from pymongo.collection import Collection
from pymongo.errors import PyMongoError
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TweetDAL:
    def __init__(self, collection: Collection):
        self.collection = collection
        logger.debug(f"TweetDAL initialized for collection: {collection.name}")

    async def insert_tweet(self, tweet_data: Dict[str, Any]) -> str:
        try:
            logger.debug(f"Inserting tweet with keys: {list(tweet_data.keys())}")
            result = await self.collection.insert_one(tweet_data)
            tweet_id = str(result.inserted_id)
            logger.info(f"Tweet inserted successfully with ID: {tweet_id}")
            return tweet_id

        except PyMongoError as e:
            logger.error(f"MongoDB error inserting tweet: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error inserting tweet: {e}")
            raise