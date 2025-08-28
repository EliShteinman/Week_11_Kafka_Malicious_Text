import logging
from datetime import datetime
from typing import Any, Dict, List

from bson import ObjectId

from shared.mongo_utils import SingletonMongoClient

logger = logging.getLogger(__name__)


class TweetRepository:
    """
    Data Access Layer for tweet retrieval operations
    """

    def __init__(self, mongo_client: SingletonMongoClient):
        self.mongo_client = mongo_client
        logger.info("TweetRepository initialized")

    async def get_tweets_from_collection(
        self, collection_name: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all tweets from specified collection with proper data conversion
        """
        try:
            collection = self.mongo_client.get_collection(
                collection_name=collection_name
            )
            tweets = []

            async for tweet in collection.find():
                # Convert ObjectId to string for JSON serialization
                if isinstance(tweet.get("_id"), ObjectId):
                    tweet["_id"] = str(tweet["_id"])

                # Convert datetime objects to ISO format strings
                for key, value in tweet.items():
                    if isinstance(value, datetime):
                        tweet[key] = value.isoformat()

                tweets.append(tweet)

            logger.info(
                f"Retrieved {len(tweets)} tweets from collection '{collection_name}'"
            )
            return tweets

        except Exception as e:
            logger.error(
                f"Error retrieving tweets from collection '{collection_name}': {e}"
            )
            raise
