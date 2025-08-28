import os

KAFKA_URL = os.environ.get("KAFKA_URL", "localhost")
KAFKA_PORT = int(os.environ.get("KAFKA_PORT", 9092))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_KAFKA = os.getenv("LOG_KAFKA", "ERROR").upper()
KAFKA_TOPIC_IN_1 = os.getenv("KAFKA_TOPIC", "raw_tweets_antisemitic")
KAFKA_TOPIC_IN_2 = os.getenv("KAFKA_TOPIC_2", "raw_tweets_not_antisemitic")
KAFKA_TOPIC_OUT_1 = os.getenv("KAFKA_TOPIC_OUT_1", "processed_tweets_antisemitic")
KAFKA_TOPIC_OUT_2 = os.getenv("KAFKA_TOPIC_OUT_2", "processed_tweets_not_antisemitic")
TARGET_KEY = os.getenv("TARGET_KEY", "text")
KAFKA_GROUP_ID = os.environ.get("KAFKA_GROUP_ID", "preprocessor-group")