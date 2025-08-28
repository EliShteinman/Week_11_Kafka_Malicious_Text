from shared.kafka_utils import AsyncKafkaConsumer
from shared.mongo_utils import SingletonMongoClient
import config
from persister_service import TweetDAL
import logging
import asyncio

logging.basicConfig(level=config.LOG_LEVEL)
logging.getLogger("pymongo").setLevel(level=config.LOG_MONGO)
logging.getLogger("kafka").setLevel(level=config.LOG_KAFKA)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting persister service")

    # Initialize MongoDB client
    client = SingletonMongoClient(config.MONGO_URI, config.MONGO_DB_NAME)
    await client.connect_and_verify()
    logger.info("MongoDB client connected successfully")

    # Initialize collections
    antisemitic_collection = client.get_collection(collection_name=config.MONGO_COLLECTION_ANTISEMITIC)
    normal_collection = client.get_collection(collection_name=config.MONGO_COLLECTION_NOT_ANTISEMITIC)
    logger.info(f"Collections initialized: {config.MONGO_COLLECTION_ANTISEMITIC}, {config.MONGO_COLLECTION_NOT_ANTISEMITIC}")

    # Initialize DAL objects
    antisemitic_dal = TweetDAL(antisemitic_collection)
    normal_dal = TweetDAL(normal_collection)

    # Initialize Kafka consumer
    consumer = AsyncKafkaConsumer(
        [config.KAFKA_TOPIC_ANTISEMITIC, config.KAFKA_TOPIC_NOT_ANTISEMITIC],
        bootstrap_servers=f"{config.KAFKA_URL}:{config.KAFKA_PORT}",
        group_id=config.KAFKA_GROUP_ID
    )

    try:
        await consumer.start()
        logger.info("Kafka consumer started successfully")
    except Exception as e:
        logger.error(f"Failed to start Kafka consumer: {e}")
        return

    logger.info("Starting main processing loop")

    try:
        while True:
            try:
                async for topic, tweet in consumer.consume():
                    try:
                        if topic == config.KAFKA_TOPIC_ANTISEMITIC:
                            tweet_id = await antisemitic_dal.insert_tweet(tweet)
                            logger.debug(f"Inserted antisemitic tweet: {tweet_id}")
                        elif topic == config.KAFKA_TOPIC_NOT_ANTISEMITIC:
                            tweet_id = await normal_dal.insert_tweet(tweet)
                            logger.debug(f"Inserted normal tweet: {tweet_id}")
                        else:
                            logger.warning(f"Unknown topic '{topic}', skipping message")
                            continue

                    except Exception as e:
                        logger.error(f"Failed to insert tweet from topic {topic}: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error in consumer loop: {e}")
                logger.info("Attempting to reconnect in 5 seconds")
                await asyncio.sleep(5)

    except KeyboardInterrupt:
        logger.info("Shutting down persister service by user request")
    finally:
        try:
            await consumer.stop()
            logger.info("Kafka consumer stopped")
        except Exception as e:
            logger.error(f"Error stopping Kafka consumer: {e}")

        logger.info("Persister service stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Critical error in main: {e}")
        raise