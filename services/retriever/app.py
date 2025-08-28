import asyncio
from shared.mongo_utils import SingletonMongoClient
from shared.kafka_utils import AsyncKafkaProducer
from retriever_service import RetrieverData
import config
import logging

logging.basicConfig(level=config.LOG_LEVEL)
logging.getLogger("pymongo").setLevel(level=config.LOG_MONGO)
logging.getLogger("kafka").setLevel(level=config.LOG_KAFKA)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting retriever service...")

    db_client = SingletonMongoClient(
        uri=config.MONGO_URI,
        db_name=config.MONGO_DB_NAME,
        collection_name=config.MONGO_COLLECTION_RAW_TWEETS,
    )
    try:
        await db_client.connect_and_verify()
        logger.info("MongoDB client initialized and connected.")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB client: {e}")
        return

    collection = db_client.get_collection()
    retriever = RetrieverData(collection)
    logger.info(f"RetrieverData service initialized")

    logger.info(f"Initializing Kafka producer - Server: {config.KAFKA_URL}:{config.KAFKA_PORT}")
    producer = AsyncKafkaProducer(bootstrap_servers=f"{config.KAFKA_URL}:{config.KAFKA_PORT}")
    try:
        await producer.start()
        logger.info("Kafka producer started successfully")
    except Exception as e:
        logger.error(f"Failed to start Kafka producer: {e}")
        return

    logger.info("Starting main processing loop...")
    poll_count = 0

    while True:
        try:
            poll_count += 1
            logger.debug(f"Polling iteration #{poll_count}")

            tweets = await retriever.receive_messages_from()

            if tweets:
                logger.info(f"Retrieved {len(tweets)} tweets from MongoDB")

                antisemitic_count = 0
                not_antisemitic_count = 0

                for tweet in tweets:
                    try:
                        if tweet.get(config.MONGO_CLASSIFICATION_FIELD):
                            await producer.send_json(config.KAFKA_TOPIC_OUT_ANTISEMITIC, tweet)
                            antisemitic_count += 1
                            logger.debug(f"Sent antisemitic tweet to {config.KAFKA_TOPIC_OUT_ANTISEMITIC}")
                        else:
                            await producer.send_json(config.KAFKA_TOPIC_OUT_NOT_ANTISEMITIC, tweet)
                            not_antisemitic_count += 1
                            logger.debug(f"Sent non-antisemitic tweet to {config.KAFKA_TOPIC_OUT_NOT_ANTISEMITIC}")
                    except Exception as e:
                        logger.error(f"Failed to send tweet to Kafka: {e}")
                        logger.debug(f"Tweet data: {tweet.get('_id', 'unknown_id')}")

                logger.info(
                    f"Processing complete - Antisemitic: {antisemitic_count}, Not antisemitic: {not_antisemitic_count}")
            else:
                logger.debug("No new tweets found in this poll")

        except Exception as e:
            logger.error(f"Error in main processing loop: {e}")
            logger.debug("Continuing with next iteration after error...")

        logger.debug("Waiting 60 seconds before next poll...")
        await asyncio.sleep(60)  # Poll every minute


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Retriever service stopped by user")
    except Exception as e:
        logger.critical(f"Critical error in main: {e}")
        raise