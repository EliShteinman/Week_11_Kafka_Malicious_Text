import os


# Collections created by Persister service
MONGO_COLLECTION_ANTISEMITIC = os.getenv(
    "MONGO_COLLECTION_ANTISEMITIC", "tweets_antisemitic"
)
MONGO_COLLECTION_NOT_ANTISEMITIC = os.getenv(
    "MONGO_COLLECTION_NOT_ANTISEMITIC", "tweets_not_antisemitic"
)

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8082))


# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_MONGO = os.getenv("LOG_MONGO", "ERROR").upper()



# MongoDB Configuration
MONGO_ATLAS_URI = os.getenv("MONGO_ATLAS_URI", "")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "processed_tweets")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_USER", "")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")
MONGO_COLLECTION_RAW_TWEETS = os.getenv("MONGO_COLLECTION_RAW_TWEETS", "tweets")
MONGO_CLASSIFICATION_FIELD = os.getenv("MONGO_CLASSIFICATION_FIELD", "Antisemitic")


if MONGO_ATLAS_URI:
    MONGO_URI = MONGO_ATLAS_URI
elif MONGO_USER and MONGO_PASSWORD:
    MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
else:
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"