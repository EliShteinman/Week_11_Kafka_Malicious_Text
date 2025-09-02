import logging
import time
from datetime import datetime

import config

from shared.kafka_utils import AsyncKafkaProducer
from shared.sentiment_analyzer import SentimentAnalyzer
from shared.text_processing import TextProcessing
from shared.timestamp_extractor import TimeExtractor
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
        """Initialize the enricher service."""
        self.text_cleaner = TextProcessing()
        self.kafka_producer = producer
        self._setup_topics()
        self._setup_analyzers()
        self._setup_performance_tracking()
        self._log_initialization()

    def _setup_topics(self):
        """Setup input and output topic configurations."""
        self.input_topic_antisemitic = config.KAFKA_TOPIC_IN_ANTISEMITIC
        self.input_topic_not_antisemitic = config.KAFKA_TOPIC_IN_NOT_ANTISEMITIC
        self.output_topic_antisemitic = config.KAFKA_TOPIC_OUT_ANTISEMITIC
        self.output_topic_not_antisemitic = config.KAFKA_TOPIC_OUT_NOT_ANTISEMITIC
        self.target_text_key = config.ORIGINAL_TEXT_FIELD

    def _setup_analyzers(self):
        """Setup sentiment analyzer, weapon detector and time extractor."""
        self.sentiment_analyzer = SentimentAnalyzer()
        self._setup_weapon_detector()
        self.time_extractor = TimeExtractor()

    def _setup_weapon_detector(self):
        """Load and process weapon list for detection."""
        weapons_file_path = config.WEAPONS_FILE_PATH
        raw_weapons = LoadFile.load_file(weapons_file_path)

        if not raw_weapons:
            logger.warning(f"No weapons loaded from {weapons_file_path}. Weapon detection will not function.")
            cleaned_weapons = []
        else:
            cleaned_weapons = self._clean_weapon_list(raw_weapons)

        self.weapon_detector = WeaponDetector(cleaned_weapons)

    def _clean_weapon_list(self, raw_weapons):
        """Clean weapon list using text processing."""
        cleaned_weapons = []
        for weapon in raw_weapons:
            weapon_text = weapon.split(': ', 1)[1] if ': ' in weapon else weapon
            cleaned_weapon = self.text_cleaner.clean_central(weapon_text)
            if cleaned_weapon:
                cleaned_weapons.append(cleaned_weapon)
        return cleaned_weapons

    def _setup_performance_tracking(self):
        """Initialize performance tracking variables."""
        self.processed_count = 0
        self.error_count = 0
        self.total_processing_time = 0.0
        self.start_time = time.time()

    def _log_initialization(self):
        """Log initialization information."""
        logger.info(f"EnricherService initialized with target key: '{self.target_text_key}'")
        logger.info(f"Topic mapping: {self.input_topic_antisemitic} -> {self.output_topic_antisemitic}")
        logger.info(f"Topic mapping: {self.input_topic_not_antisemitic} -> {self.output_topic_not_antisemitic}")

    async def process_and_send_tweet(self, input_topic: str, message: dict) -> dict:
        """
        Process a tweet message by enriching its data and send to appropriate output topic.

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
            processed_message = self._enrich_tweet_data(message, tweet_id)
            output_topic = self._get_output_topic(input_topic, tweet_id)

            if not output_topic:
                return self._handle_unknown_topic_error(input_topic)

            send_result = await self._send_to_kafka(output_topic, processed_message, tweet_id)
            self._update_performance_stats(process_start_time)

            return send_result

        except Exception as e:
            return self._handle_processing_error(e, tweet_id, process_start_time)

    def _enrich_tweet_data(self, message: dict, tweet_id: str) -> dict:
        """Enrich tweet data with sentiment, weapons, and timestamp."""
        processed_message = message.copy()
        original_text = processed_message.get(self.target_text_key, "")
        text_for_enrichment = processed_message.get("clean_text", original_text)

        if not text_for_enrichment:
            return self._handle_empty_text(processed_message, tweet_id)

        # Perform enrichment
        processed_message["sentiment"] = self._analyze_sentiment(text_for_enrichment, tweet_id)
        processed_message["detected_weapons"] = self._detect_weapons(text_for_enrichment, tweet_id)
        processed_message["relevant_timestamp"] = self._extract_timestamp(original_text, tweet_id)
        processed_message["enriched_at"] = datetime.now().isoformat()

        return processed_message

    def _handle_empty_text(self, processed_message: dict, tweet_id: str) -> dict:
        """Handle case where tweet has no text for enrichment."""
        logger.warning(f"Tweet {tweet_id} has no text for enrichment. Skipping.")
        processed_message.update({
            "sentiment": "neutral",
            "detected_weapons": [],
            "relevant_timestamp": "",
            "enriched_at": datetime.now().isoformat()
        })
        return processed_message

    def _analyze_sentiment(self, text: str, tweet_id: str) -> str:
        """Analyze sentiment of the text."""
        sentiment_score = self.sentiment_analyzer.get_sentiment_score(text)
        sentiment_label = self.sentiment_analyzer.convert_to_sentiment_label(
            sentiment_score,
            config.SENTIMENT_THRESHOLD_POSITIVE,
            config.SENTIMENT_THRESHOLD_NEGATIVE,
        )
        logger.debug(f"Tweet {tweet_id} - Sentiment: {sentiment_label} (Score: {sentiment_score:.3f})")
        return sentiment_label

    def _detect_weapons(self, text: str, tweet_id: str) -> list:
        """Detect weapons in the text."""
        detected_weapons = self.weapon_detector.find_weapons(text)
        weapons_list = detected_weapons if detected_weapons else []
        logger.debug(f"Tweet {tweet_id} - Detected weapons: {detected_weapons}")
        return weapons_list

    def _extract_timestamp(self, original_text: str, tweet_id: str) -> str:
        """Extract the most recent timestamp from text."""
        extracted_timestamps = self.time_extractor.date_time_extractor(original_text) or []


        if not extracted_timestamps:
            return ""

        relevant_timestamp = self._parse_latest_timestamp(extracted_timestamps, tweet_id)
        logger.debug(f"Tweet {tweet_id} - Extracted timestamp: {relevant_timestamp}")
        return relevant_timestamp

    def _parse_latest_timestamp(self, timestamps: list, tweet_id: str) -> str:
        """Parse timestamps and return the latest one."""
        parsed_dates = []

        for ts in timestamps:
            parsed_date = self._parse_single_timestamp(ts)
            if parsed_date:
                parsed_dates.append(parsed_date)

        if parsed_dates:
            return max(parsed_dates).isoformat()
        else:
            logger.warning(f"Tweet {tweet_id} - Could not parse timestamps: {timestamps}")
            return timestamps[0] if timestamps else ""

    def _parse_single_timestamp(self, timestamp_str: str):
        """Parse a single timestamp string with multiple format support."""
        formats = [
            "%Y-%m-%d",  # 2020-03-25
            "%d-%m-%Y",  # 25-03-2020
            "%Y/%m/%d",  # 2020/03/25
            "%d/%m/%Y"  # 25/03/2020
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt).date()
            except ValueError:
                continue

        return None

    def _get_output_topic(self, input_topic: str, tweet_id: str) -> str:
        """Determine the appropriate output topic based on input topic."""
        topic_mapping = {
            self.input_topic_antisemitic: self.output_topic_antisemitic,
            self.input_topic_not_antisemitic: self.output_topic_not_antisemitic
        }

        output_topic = topic_mapping.get(input_topic)

        if output_topic:
            logger.debug(f"Routing message {tweet_id} from '{input_topic}' to '{output_topic}'")
        else:
            logger.error(f"Unknown input topic '{input_topic}' for message ID: {tweet_id}")

        return output_topic

    def _handle_unknown_topic_error(self, input_topic: str) -> dict:
        """Handle unknown input topic error."""
        self.error_count += 1
        return {
            "status": "error",
            "reason": f"Unknown input topic: {input_topic}",
        }

    async def _send_to_kafka(self, output_topic: str, processed_message: dict, tweet_id: str):
        """Send enriched message to Kafka."""
        logger.debug(f"Sending enriched tweet {tweet_id} to topic '{output_topic}'")
        send_result = await self.kafka_producer.send_json(output_topic, processed_message)
        logger.info(f"Successfully sent enriched message to topic '{output_topic}' for tweet ID: {tweet_id}")
        return send_result

    def _update_performance_stats(self, process_start_time: float):
        """Update performance statistics."""
        processing_time = time.time() - process_start_time
        self.processed_count += 1
        self.total_processing_time += processing_time

        logger.info(f"Processing time: {processing_time:.3f}s")

        # Log statistics every 100 processed messages
        if self.processed_count % 100 == 0:
            self._log_performance_stats()

    def _log_performance_stats(self):
        """Log current performance statistics."""
        avg_time = self.total_processing_time / self.processed_count
        uptime = time.time() - self.start_time
        rate = self.processed_count / uptime if uptime > 0 else 0
        logger.info(
            f"Statistics: {self.processed_count} processed, {self.error_count} errors, "
            f"avg processing time: {avg_time:.3f}s, rate: {rate:.2f} msg/s"
        )

    def _handle_processing_error(self, error: Exception, tweet_id: str, process_start_time: float):
        """Handle processing errors."""
        self.error_count += 1
        processing_time = time.time() - process_start_time
        logger.error(f"Error processing tweet {tweet_id} after {processing_time:.3f}s: {str(error)}")
        raise

    def get_statistics(self) -> dict:
        """Get current processing statistics."""
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