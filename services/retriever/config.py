import os


# Read configuration from environment variables in a central place.
MONGO_ATLAS_URI = os.getenv("MONGO_ATLAS_URI", "")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_USER", "")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "IranMalDB")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "tweets")
MONGO_TARGET_COLUM = os.getenv("MONGO_TARGET_COLUM", "Antisemitic")

# Build the MongoDB Connection URI.
# If a username and password are provided, build a URI with authentication (for OpenShift).
# Otherwise, build a simpler URI for local, unauthenticated development.
if MONGO_ATLAS_URI:
    MONGO_URI = MONGO_ATLAS_URI
elif MONGO_USER and MONGO_PASSWORD:
    MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
else:
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"


KAFKA_URL = os.environ.get("KAFKA_URL", "localhost")
KAFKA_PORT = int(os.environ.get("KAFKA_PORT", 9092))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_KAFKA = os.getenv("LOG_KAFKA", "ERROR").upper()
KAFKA_TOPIC_1 = os.getenv("KAFKA_TOPIC", "raw_tweets_antisemitic")
KAFKA_TOPIC_2 = os.getenv("KAFKA_TOPIC_2", "raw_tweets_not_antisemitic")
