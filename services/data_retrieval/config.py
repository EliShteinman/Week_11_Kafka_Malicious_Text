import os

# MongoDB Configuration - Local MongoDB (not Atlas)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "processed_tweets")

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
