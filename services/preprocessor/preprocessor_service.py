from shared.text_processing import TextProcessing
from shared.kafka_utils import AsyncKafkaProducer
import config
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class PreprocessorService:
    """
    Service to handle text preprocessing and message routing for tweet data.
    Processes incoming tweets by cleaning text and routing to appropriate output topics.
    """

    def __init__(self, producer: AsyncKafkaProducer):
        """
        Initialize the preprocessor service.

        Args:
            producer: AsyncKafkaProducer instance for sending processed messages
        """
        self.text_cleaner = TextProcessing()
        self.kafka_producer = producer
        self.input_topic_antisemitic = config.KAFKA_TOPIC_IN_ANTISEMITIC
        self.input_topic_not_antisemitic = config.KAFKA_TOPIC_IN_NOT_ANTISEMITIC
        self.output_topic_antisemitic = config.KAFKA_TOPIC_OUT_ANTISEMITIC
        self.output_topic_not_antisemitic = config.KAFKA_TOPIC_OUT_NOT_ANTISEMITIC
        self.target_text_key = config.TARGET_KEY

        # Performance tracking
        self.processed_count = 0
        self.error_count = 0
        self.total_processing_time = 0.0
        self.start_time = time.time()

        logger.info(f"PreprocessorService initialized with target key: '{self.target_text_key}'")
        logger.info(f"Topic mapping: {self.input_topic_antisemitic} -> {self.output_topic_antisemitic}")
        logger.info(f"Topic mapping: {self.input_topic_not_antisemitic} -> {self.output_topic_not_antisemitic}")

    async def process_and_send_tweet(self, input_topic: str, message: dict) -> dict:
        """
        Process a tweet message by cleaning its text and send to appropriate output topic.

        Args:
            input_topic: The source topic name
            message: The tweet message dictionary

        Returns:
            dict: Result of the processing operation
        """
        tweet_id = message.get('_id', 'unknown')
        process_start_time = time.time()

        logger.info(f"Starting to process tweet {tweet_id} from topic '{input_topic}'")

        try:
            processed_message = message.copy()
            original_text = processed_message.get(self.target_text_key, "")

            # Handle missing text
            if not original_text:
                logger.warning(
                    f"Tweet {tweet_id} missing '{self.target_text_key}' key. Skipping text cleaning.")
                cleaned_text = ""
            else:
                # Track text processing metrics
                text_length_before = len(original_text)

                # Clean the text
                text_clean_start = time.time()
                cleaned_text = self.text_cleaner.clean_central(original_text)
                text_clean_time = time.time() - text_clean_start

                text_length_after = len(cleaned_text)
                reduction_percent = ((
                                                 text_length_before - text_length_after) / text_length_before * 100) if text_length_before > 0 else 0

                logger.debug(
                    f"Tweet {tweet_id} - Text cleaning: {text_length_before} chars -> {text_length_after} chars ({reduction_percent:.1f}% reduction) in {text_clean_time:.3f}s")
                logger.debug(f"Original: '{original_text[:100]}...' | Cleaned: '{cleaned_text[:100]}...'")

            # Add cleaned text and processing metadata
            processed_message['clean_text'] = cleaned_text
            processed_message['processed_at'] = datetime.now().isoformat()
            processed_message['original_topic'] = input_topic

            # Determine output topic
            output_topic = self._get_output_topic(input_topic, tweet_id)
            if not output_topic:
                self.error_count += 1
                return {"status": "error", "reason": f"Unknown input topic: {input_topic}"}

            # Send processed message to Kafka
            logger.debug(f"Sending tweet {tweet_id} to topic '{output_topic}'")
            send_result = await self.kafka_producer.send_json(output_topic, processed_message)

            # Update statistics
            processing_time = time.time() - process_start_time
            self.processed_count += 1
            self.total_processing_time += processing_time

            logger.info(
                f"Successfully sent processed message to topic '{output_topic}' for tweet ID: {tweet_id} (processing time: {processing_time:.3f}s)")

            # Log statistics every 100 processed messages
            if self.processed_count % 100 == 0:
                avg_time = self.total_processing_time / self.processed_count
                uptime = time.time() - self.start_time
                rate = self.processed_count / uptime if uptime > 0 else 0
                logger.info(
                    f"Statistics: {self.processed_count} processed, {self.error_count} errors, avg processing time: {avg_time:.3f}s, rate: {rate:.2f} msg/s")

            return send_result

        except Exception as e:
            self.error_count += 1
            processing_time = time.time() - process_start_time
            logger.error(f"Error processing tweet {tweet_id} after {processing_time:.3f}s: {str(e)}")
            raise

    def _get_output_topic(self, input_topic: str, tweet_id: str) -> str:
        """
        Determine the appropriate output topic based on input topic.

        Args:
            input_topic: The source topic name
            tweet_id: Tweet ID for logging purposes

        Returns:
            str: Output topic name or None if unknown input topic
        """
        if input_topic == self.input_topic_antisemitic:
            logger.debug(f"Routing message {tweet_id} from '{input_topic}' to '{self.output_topic_antisemitic}'")
            return self.output_topic_antisemitic
        elif input_topic == self.input_topic_not_antisemitic:
            logger.debug(f"Routing message {tweet_id} from '{input_topic}' to '{self.output_topic_not_antisemitic}'")
            return self.output_topic_not_antisemitic
        else:
            logger.error(
                f"Unknown input topic '{input_topic}'. Cannot determine output topic for message (ID: {tweet_id}).")
            return None

    def get_statistics(self) -> dict:
        """
        Get current processing statistics.

        Returns:
            dict: Statistics including processed count, errors, and performance metrics
        """
        uptime = time.time() - self.start_time
        avg_processing_time = self.total_processing_time / self.processed_count if self.processed_count > 0 else 0
        processing_rate = self.processed_count / uptime if uptime > 0 else 0

        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "uptime_seconds": uptime,
            "avg_processing_time": avg_processing_time,
            "processing_rate": processing_rate,
            "error_rate": self.error_count / self.processed_count if self.processed_count > 0 else 0
        }


if __name__ == "__main__":
    """
    Standalone test for TextProcessing functionality.
    This block demonstrates text cleaning without Kafka dependencies.
    """
    logger.info("Running PreprocessorService standalone test")

    examples = [
        "This is   a SAMPLE text, with Punctuation!!",
        "NLTK is a great library for text processing.",
        "Cleaning   TEXT??? is sometimes  tricky...",
        "Stopwords should be removed in this sentence.",
        "Running, runner, runs — all should be stemmed.",
        "",  # Test empty string
        "   "  # Test string with only spaces
    ]

    text_processor_standalone = TextProcessing()
    logger.info(f"Testing {len(examples)} text examples")

    for i, text in enumerate(examples, 1):
        start_time = time.time()
        cleaned = text_processor_standalone.clean_central(text)
        processing_time = time.time() - start_time

        print(f"Example {i}:")
        print(f"Original: '{text}'")
        print(f"Cleaned : '{cleaned}'")
        print(f"Time    : {processing_time:.4f}s")
        print("-" * 50)

    logger.info("Standalone test completed")