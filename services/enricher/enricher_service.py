import logging
import time
from datetime import datetime

import config

from shared.kafka_utils import AsyncKafkaProducer
from shared.sentiment_analyzer import SentimentAnalyzer
from shared.text_processing import TextProcessing
from shared.timestamp_extractor import Time_extractor
from shared.weapon_detector import WeaponDetector

logger = logging.getLogger(__name__)


class LoadFile:
    @staticmethod
    def load_file(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:

                return [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return []
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            return []


class EnricherService:
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

        self.target_text_key = config.TARGET_ORIGINAL
        self.sentiment_analyzer = SentimentAnalyzer()

        weapons_file_path = config.WEAPONS_FILE_PATH
        self.weapons_list = LoadFile.load_file(weapons_file_path)
        if not self.weapons_list:
            logger.warning(
                f"No weapons loaded from {weapons_file_path}. Weapon detection will not function."
            )
        self.weapon_detector = WeaponDetector(self.weapons_list)

        self.time_extractor = Time_extractor()

        # Performance tracking
        self.processed_count = 0
        self.error_count = 0
        self.total_processing_time = 0.0
        self.start_time = time.time()

        logger.info(
            f"PreprocessorService initialized with target key: '{self.target_text_key}'"
        )
        logger.info(
            f"Topic mapping: {self.input_topic_antisemitic} -> {self.output_topic_antisemitic}"
        )
        logger.info(
            f"Topic mapping: {self.input_topic_not_antisemitic} -> {self.output_topic_not_antisemitic}"
        )

    async def process_and_send_tweet(self, input_topic: str, message: dict) -> dict:
        """
        Process a tweet message by cleaning its text and send to appropriate output topic.

        Args:
            input_topic: The source topic name
            message: The tweet message dictionary

        Returns:
            dict: Result of the processing operation
        """
        tweet_id = message.get("_id", "unknown")

        process_start_time = time.time()

        logger.info(f"Starting to process tweet {tweet_id} from topic '{input_topic}'")

        try:
            processed_message = message.copy()
            original_text = processed_message.get(self.target_text_key, "")

            # Use the already cleaned text from the previous stage, if available
            # Otherwise, clean the original text
            text_for_enrichment = processed_message.get("clean_text", original_text)

            # If no text is available, log and skip enrichment
            if not text_for_enrichment:
                logger.warning(
                    f"Tweet {tweet_id} has no text for enrichment. Skipping."
                )
                processed_message["sentiment"] = "neutral"
                processed_message["weapons_detected"] = []
                processed_message["relevant_timestamp"] = None
            else:
                # 1. Sentiment Analysis
                sentiment_score = self.sentiment_analyzer.get_sentiment_score(
                    text_for_enrichment
                )
                sentiment_label = self.sentiment_analyzer.convert_to_sentiment_label(
                    sentiment_score,
                    config.SENTIMENT_THRESHOLD_POSITIVE,
                    config.SENTIMENT_THRESHOLD_NEGATIVE,
                )
                processed_message["sentiment"] = sentiment_label
                logger.debug(
                    f"Tweet {tweet_id} - Sentiment: {sentiment_label} (Score: {sentiment_score:.3f})"
                )

                # 2. Weapon Detection (on cleaned text for better accuracy)
                detected_weapons = self.weapon_detector.find_weapons(
                    text_for_enrichment
                )
                processed_message["weapons_detected"] = (
                    detected_weapons if detected_weapons else []
                )
                logger.debug(f"Tweet {tweet_id} - Detected weapons: {detected_weapons}")

                # 3. Timestamp Extraction (on original text for full context)
                # The requirement states "within the content of the text (date only, no time)"
                # Assuming Time_extractor.DateTimeExtractor returns a list of detected dates.
                # We need to pick the latest one if multiple are found.
                extracted_timestamps = self.time_extractor.DateTimeExtractor(
                    original_text
                )
                relevant_timestamp = None
                if extracted_timestamps:
                    try:
                        # Try to parse and find the latest date
                        parsed_dates = [
                            datetime.strptime(ts, "%Y-%m-%d").date()
                            for ts in extracted_timestamps
                        ]
                        relevant_timestamp = max(parsed_dates).isoformat()
                    except ValueError:
                        logger.warning(
                            f"Tweet {tweet_id} - Could not parse all extracted timestamps: {extracted_timestamps}"
                        )
                        # Fallback to just taking the first one if parsing fails, or keep None
                        relevant_timestamp = extracted_timestamps[0]

                processed_message["relevant_timestamp"] = relevant_timestamp
                logger.debug(
                    f"Tweet {tweet_id} - Extracted timestamp: {relevant_timestamp}"
                )

            processed_message["enriched_at"] = datetime.now().isoformat()

            # Determine output topic
            output_topic = self._get_output_topic(input_topic, tweet_id)
            if not output_topic:
                self.error_count += 1
                return {
                    "status": "error",
                    "reason": f"Unknown input topic: {input_topic}",
                }

            # Send enriched message to Kafka
            logger.debug(f"Sending enriched tweet {tweet_id} to topic '{output_topic}'")
            send_result = await self.kafka_producer.send_json(
                output_topic, processed_message
            )

            # Update statistics
            processing_time = time.time() - process_start_time
            self.processed_count += 1
            self.total_processing_time += processing_time

            logger.info(
                f"Successfully sent enriched message to topic '{output_topic}' for tweet ID: {tweet_id} (processing time: {processing_time:.3f}s)"
            )

            # Log statistics every 100 processed messages
            if self.processed_count % 100 == 0:
                avg_time = self.total_processing_time / self.processed_count
                uptime = time.time() - self.start_time
                rate = self.processed_count / uptime if uptime > 0 else 0
                logger.info(
                    f"Statistics: {self.processed_count} processed, {self.error_count} errors, avg processing time: {avg_time:.3f}s, rate: {rate:.2f} msg/s"
                )

            return send_result

        except Exception as e:
            self.error_count += 1
            processing_time = time.time() - process_start_time
            logger.error(
                f"Error processing tweet {tweet_id} after {processing_time:.3f}s: {str(e)}"
            )
            # Consider if you want to re-raise or just log and continue
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
            logger.debug(
                f"Routing message {tweet_id} from '{input_topic}' to '{self.output_topic_antisemitic}'"
            )
            return self.output_topic_antisemitic
        elif input_topic == self.input_topic_not_antisemitic:
            logger.debug(
                f"Routing message {tweet_id} from '{input_topic}' to '{self.output_topic_not_antisemitic}'"
            )
            return self.output_topic_not_antisemitic
        else:
            logger.error(
                f"Unknown input topic '{input_topic}'. Cannot determine output topic for message (ID: {tweet_id})."
            )
            return None

    def get_statistics(self) -> dict:
        """
        Get current processing statistics.

        Returns:
            dict: Statistics including processed count, errors, and performance metrics
        """
        uptime = time.time() - self.start_time
        avg_processing_time = (
            self.total_processing_time / self.processed_count
            if self.processed_count > 0
            else 0
        )
        processing_rate = self.processed_count / uptime if uptime > 0 else 0

        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "uptime_seconds": uptime,
            "avg_processing_time": avg_processing_time,
            "processing_rate": processing_rate,
            "error_rate": (
                self.error_count / self.processed_count
                if self.processed_count > 0
                else 0
            ),
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
        "",
        "   ",
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
