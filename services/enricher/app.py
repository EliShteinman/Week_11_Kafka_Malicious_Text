import asyncio
import time
from shared.kafka_utils import AsyncKafkaProducer, AsyncKafkaConsumer
import config
import logging
from enricher_service import enricherservice

logging.basicConfig(level=config.LOG_LEVEL)

logger = logging.getLogger(__name__)




async def main():
    """
    Main function to start the retriever service.
    Sets up Kafka producer/consumer and starts processing loop.
    """
    logger.info("Starting retriever service...")
    logger.info("RetrieverData service initialized")

    # Initialize Kafka connections
    logger.info(f"Initializing Kafka producer - Server: {config.KAFKA_URL}:{config.KAFKA_PORT}")
    producer = AsyncKafkaProducer(bootstrap_servers=f"{config.KAFKA_URL}:{config.KAFKA_PORT}")
    consumer = AsyncKafkaConsumer(
        [config.KAFKA_TOPIC_IN_1, config.KAFKA_TOPIC_IN_2],
        bootstrap_servers=f"{config.KAFKA_URL}:{config.KAFKA_PORT}",
        group_id=config.KAFKA_GROUP_ID
    )
    preprocessor = enricherservice(producer)

    try:
        await producer.start()
        await consumer.start()
        logger.info("Kafka producer and consumer started successfully")
    except Exception as e:
        logger.error(f"Failed to start Kafka: {e}")
        return

    logger.info(f"Starting to consume from topics: {config.KAFKA_TOPIC_IN_1}, {config.KAFKA_TOPIC_IN_2}")
    logger.info("Starting main processing loop...")

    # Performance tracking variables
    message_count = 0
    start_time = time.time()
    processed_in_batch = 0
    last_stats_time = time.time()

    while True:
        try:
            async for topic, tweet in consumer.consume():
                message_count += 1
                processed_in_batch += 1
                tweet_id = tweet.get('_id', 'unknown_id')

                logger.debug(f"Processing message #{message_count} from topic '{topic}' - Tweet ID: {tweet_id}")

                # Track processing time for each message
                process_start_time = time.time()
                result = await preprocessor.process_and_send_tweet(topic, tweet)
                processing_time = time.time() - process_start_time

                logger.info(f"Processed tweet {tweet_id} in {processing_time:.3f}s")

                # Print statistics every 60 seconds
                current_time = time.time()
                if current_time - last_stats_time > 60:
                    rate = processed_in_batch / 60
                    logger.info(f"Processing rate: {rate:.2f} messages/second | Total processed: {message_count}")
                    last_stats_time = current_time
                    processed_in_batch = 0

                # Log every 100 messages for general tracking
                if message_count % 100 == 0:
                    logger.info(f"Milestone: Processed {message_count} total messages")

        except Exception as e:
            logger.error(f"Error consuming messages from Kafka: {e}")

        # Sleep between batches to prevent overwhelming the system
        await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        logger.info("Application startup initiated")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Retriever service stopped by user")
    except Exception as e:
        logger.critical(f"Critical error in main: {e}")
        raise
    finally:
        logger.info("Application shutdown complete")