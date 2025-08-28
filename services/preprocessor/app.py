import asyncio
from shared.kafka_utils import AsyncKafkaProducer, AsyncKafkaConsumer
import config
import logging
from preprocessor_service import PreprocessorService

logging.basicConfig(level=config.LOG_LEVEL)

logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting retriever service...")
    logger.info(f"RetrieverData service initialized")

    logger.info(f"Initializing Kafka producer - Server: {config.KAFKA_URL}:{config.KAFKA_PORT}")
    producer = AsyncKafkaProducer(bootstrap_servers=f"{config.KAFKA_URL}:{config.KAFKA_PORT}")
    consumer = AsyncKafkaConsumer(
        [config.KAFKA_TOPIC_IN_1, config.KAFKA_TOPIC_IN_2],
        bootstrap_servers=f"{config.KAFKA_URL}:{config.KAFKA_PORT}",
        group_id=config.KAFKA_GROUP_ID
    )
    preprocessor = PreprocessorService(producer)
    try:
        await producer.start()
        await consumer.start()
        logger.info("Kafka producer started successfully")
    except Exception as e:
        logger.error(f"Failed to start Kafka: {e}")
        return

    logger.info("Starting main processing loop...")

    while True:
        try:
            async for topic, tweet in consumer.consume():
                logger.debug(f"Consumed tweet from Kafka: {tweet.get('_id', 'unknown_id')}")
                await preprocessor.process_and_send_tweet(topic, tweet)
        except Exception as e:
            logger.error(f"Error consuming messages from Kafka: {e}")
        await asyncio.sleep(5)



if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Retriever service stopped by user")
    except Exception as e:
        logger.critical(f"Critical error in main: {e}")
        raise