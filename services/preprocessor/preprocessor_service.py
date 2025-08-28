from shared.text_processing import TextProcessing
from shared.kafka_utils import AsyncKafkaProducer
import config
import logging

logger = logging.getLogger(__name__)


class PreprocessorService:
    def __init__(self, producer: AsyncKafkaProducer):
        self.text_cleaner = TextProcessing()
        self.kafka_producer = producer
        self.input_topic_antisemitic = config.KAFKA_TOPIC_IN_1
        self.input_topic_not_antisemitic = config.KAFKA_TOPIC_IN_2
        self.output_topic_antisemitic = config.KAFKA_TOPIC_OUT_1
        self.output_topic_not_antisemitic = config.KAFKA_TOPIC_OUT_2

        self.target_text_key = config.TARGET_KEY

    async def process_and_send_tweet(self, input_topic: str, message: dict) -> dict:
        processed_message = message.copy()

        original_text = processed_message.get(self.target_text_key, "")

        if not original_text:
            logger.warning(
                f"Tweet message (ID: {processed_message.get('_id', 'unknown')}) missing '{self.target_text_key}' key. Skipping text cleaning.")
            cleaned_text = ""
        else:
            cleaned_text = self.text_cleaner.clean_central(original_text)
            logger.debug(f"Original text: '{original_text[:50]}...' Cleaned text: '{cleaned_text[:50]}...'")

        # Add the cleaned text to the message under a new, descriptive key
        processed_message['clean_text'] = cleaned_text

        # Determine the correct output topic based on the input topic
        output_topic = None
        if input_topic == self.input_topic_antisemitic:
            output_topic = self.output_topic_antisemitic
            logger.debug(f"Routing message from '{input_topic}' to '{output_topic}'")
        elif input_topic == self.input_topic_not_antisemitic:
            output_topic = self.output_topic_not_antisemitic
            logger.debug(f"Routing message from '{input_topic}' to '{output_topic}'")
        else:
            logger.error(
                f"Unknown input topic '{input_topic}'. Cannot determine output topic for message (ID: {processed_message.get('_id', 'unknown')}).")
            # You might want to raise an exception, send to a dead-letter queue, or skip sending.
            return {"status": "error", "reason": f"Unknown input topic: {input_topic}"}

        # Send the processed message to Kafka
        send_result = await self.kafka_producer.send_json(output_topic, processed_message)
        logger.info(
            f"Successfully sent processed message to topic '{output_topic}' for tweet ID: {processed_message.get('_id', 'unknown')}")

        return send_result


if __name__ == "__main__":
    # This block is for demonstrating TextProcessing only, as Kafka producer needs to be mocked for full service test.
    examples = [
        "This is   a SAMPLE text, with Punctuation!!",
        "NLTK is a great library for text processing.",
        "Cleaning   TEXT??? is sometimes  tricky...",
        "Stopwords should be removed in this sentence.",
        "Running, runner, runs – all should be stemmed.",
        "",  # Test empty string
        "   "  # Test string with only spaces
    ]

    text_processor_standalone = TextProcessing()
    for text in examples:
        cleaned = text_processor_standalone.clean_central(text)
        print(f"Original: '{text}'")
        print(f"Cleaned : '{cleaned}'")
        print("-" * 50)


