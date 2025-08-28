import os

# MongoDB Configuration
MONGO_ATLAS_URI = os.getenv("MONGO_ATLAS_URI", "")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "IranMalDB")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_USER", "")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")
MONGO_COLLECTION_RAW_TWEETS = os.getenv("MONGO_COLLECTION_RAW_TWEETS", "tweets")
MONGO_CLASSIFICATION_FIELD = os.getenv("MONGO_CLASSIFICATION_FIELD", "Antisemitic")

# Build MongoDB URI
if MONGO_ATLAS_URI:
    MONGO_URI = MONGO_ATLAS_URI
elif MONGO_USER and MONGO_PASSWORD:
    MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
else:
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"

# Kafka Configuration
KAFKA_URL = os.environ.get("KAFKA_URL", "localhost")
KAFKA_PORT = int(os.environ.get("KAFKA_PORT", 9092))

# Kafka Output Topics - where retriever sends data
KAFKA_TOPIC_OUT_ANTISEMITIC = os.getenv("KAFKA_TOPIC_OUT_ANTISEMITIC", "raw_tweets_antisemitic")
KAFKA_TOPIC_OUT_NOT_ANTISEMITIC = os.getenv("KAFKA_TOPIC_OUT_NOT_ANTISEMITIC", "raw_tweets_not_antisemitic")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_KAFKA = os.getenv("LOG_KAFKA", "ERROR").upper()
LOG_MONGO = os.getenv("LOG_MONGO", "ERROR").upper()