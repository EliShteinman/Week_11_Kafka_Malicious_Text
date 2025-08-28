"""
Configuration module for the tweet preprocessing service.
Contains all environment variable definitions and default values.
"""
import os

# Kafka connection settings
KAFKA_URL = os.environ.get("KAFKA_URL", "localhost")
KAFKA_PORT = int(os.environ.get("KAFKA_PORT", 9092))

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_KAFKA = os.getenv("LOG_KAFKA", "ERROR").upper()

# Input topics - where raw tweets are consumed from
KAFKA_TOPIC_IN_ANTISEMITIC = os.getenv("KAFKA_TOPIC_IN_ANTISEMITIC", "raw_tweets_antisemitic")
KAFKA_TOPIC_IN_NOT_ANTISEMITIC = os.getenv("KAFKA_TOPIC_IN_NOT_ANTISEMITIC", "raw_tweets_not_antisemitic")

# Output topics - where processed tweets are sent to
KAFKA_TOPIC_OUT_ANTISEMITIC = os.getenv("KAFKA_TOPIC_OUT_ANTISEMITIC", "preprocessed_tweets_antisemitic")
KAFKA_TOPIC_OUT_NOT_ANTISEMITIC = os.getenv("KAFKA_TOPIC_OUT_NOT_ANTISEMITIC", "preprocessed_tweets_not_antisemitic")

# Processing configuration
TARGET_KEY = os.getenv("TARGET_KEY", "text")  # Key name for text content in tweet messages

# Kafka consumer group settings
KAFKA_GROUP_ID = os.environ.get("KAFKA_GROUP_ID", "preprocessor-group")