import logging
from typing import List
from bson import ObjectId
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)


class RetrieverData:

    def __init__(self, collection):
        self.collection = collection
        self.latest_message_time = None
        logger.info("RetrieverData initialized")

    async def receive_messages_from(self) -> List:
        if self.collection is None:
            logger.error("Database connection is not available")
            raise RuntimeError("Database connection is not available.")

        if self.latest_message_time is None:
            query = {}
            logger.info("First run - retrieving all messages")
        else:
            query = {"CreateDate": {"$gt": self.latest_message_time}}
            logger.info(f"Retrieving messages created after: {self.latest_message_time}")

        try:
            logger.debug(f"Executing MongoDB query: {query}")
            cursor = self.collection.find(query).sort("CreateDate", 1).limit(100)

            items: List = []
            processed_count = 0

            async for message in cursor:
                processed_count += 1

                # Convert ObjectId to string for JSON serialization
                if isinstance(message.get("_id"), ObjectId):
                    message["_id"] = str(message["_id"])

                # Update latest_message_time to track progress
                if "CreateDate" in message:
                    self.latest_message_time = message["CreateDate"]

                items.append(message)

                # Log every 10th message to avoid spam
                if processed_count % 10 == 0:
                    logger.debug(f"Processed {processed_count} messages so far...")

            if items:
                logger.info(f"Successfully retrieved {len(items)} messages from MongoDB")
                logger.debug(f"Latest message time updated to: {self.latest_message_time}")
            else:
                logger.debug("No messages found matching the query")

            return items

        except PyMongoError as e:
            logger.error(f"PyMongo error retrieving data since {self.latest_message_time}: {e}")
            raise RuntimeError(f"Database operation failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in receive_messages_from: {e}")
            raise RuntimeError(f"Unexpected database error: {e}")