import os

# MongoDB Configuration
MONGO_ATLAS_URI = os.getenv("MONGO_ATLAS_URI", "")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_USER", "")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "IranMalDB")

# MongoDB Collections - matching the data flow
MONGO_COLLECTION_ANTISEMITIC = os.getenv(
    "MONGO_COLLECTION_ANTISEMITIC", "tweets_antisemitic"
)
MONGO_COLLECTION_NOT_ANTISEMITIC = os.getenv(
    "MONGO_COLLECTION_NOT_ANTISEMITIC", "tweets_not_antisemitic"
)
MONGO_TARGET_COLUMN = os.getenv("MONGO_TARGET_COLUMN", "Antisemitic")

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

# Kafka Topics - matching the data flow
KAFKA_TOPIC_ANTISEMITIC = os.getenv(
    "KAFKA_TOPIC_ANTISEMITIC", "enriched_preprocessed_tweets_antisemitic"
)
KAFKA_TOPIC_NOT_ANTISEMITIC = os.getenv(
    "KAFKA_TOPIC_NOT_ANTISEMITIC", "enriched_preprocessed_tweets_not_antisemitic"
)

# Kafka Consumer
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "persister_service")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_KAFKA = os.getenv("LOG_KAFKA", "ERROR").upper()
LOG_MONGO = os.getenv("LOG_MONGO", "ERROR").upper()
