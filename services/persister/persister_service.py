# services/persister/persister_service.py (גרסה מתוקנת)
import logging
from typing import Any, Dict
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)


class TweetDAL:
    def __init__(self, collection: Collection):
        self.collection = collection
        logger.debug(f"TweetDAL initialized for collection: {collection.name}")

    def _format_tweet_for_storage(self, enriched_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforms the enriched data into the final, precise format required by the exam.
        This includes renaming fields, selecting specific fields, and ensuring correct structure.
        """
        # Note: The 'createdate' and 'antisemietic' fields in the exam's output spec have typos.
        # We will follow the output specification exactly as written.
        final_doc = {
            "_id": enriched_data.get("_id"),
            "createdate": enriched_data.get("CreateDate"),
            "antisemietic": enriched_data.get("Antisemitic", 0),
            "original_text": enriched_data.get("text", ""),
            "clean_text": enriched_data.get("clean_text", ""),
            "sentiment": enriched_data.get("sentiment", "neutral"),
            # Rename 'detected_weapons' to 'weapons_detected' as per spec
            "weapons_detected": enriched_data.get("detected_weapons", []),
            "relevant_timestamp": enriched_data.get("relevant_timestamp", "")
        }
        return final_doc

    async def insert_tweet(self, tweet_data: Dict[str, Any]) -> str:
        """
        Formats the tweet data to the final schema and inserts it into the collection.
        """
        try:
            # 1. Format the data just before insertion
            formatted_tweet = self._format_tweet_for_storage(tweet_data)

            logger.debug(f"Inserting formatted tweet with original ID: {formatted_tweet['_id']}")

            # 2. Insert the cleaned, formatted document
            result = await self.collection.insert_one(formatted_tweet)

            tweet_id = str(result.inserted_id)
            logger.info(f"Tweet inserted successfully with ID: {tweet_id}")
            return tweet_id

        except PyMongoError as e:
            logger.error(f"MongoDB error inserting tweet: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error inserting tweet: {e}")
            raise