import asyncio
import datetime
import json
import logging
from typing import Any, AsyncIterator, Awaitable, Callable, Optional, Sequence, Tuple


from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

logger = logging.getLogger(__name__)


def _json_default_handler(obj):
    if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _default_json_serializer(obj) -> bytes:
    """Default JSON serializer with datetime support"""
    return json.dumps(obj, ensure_ascii=False, default=_json_default_handler).encode(
        "utf-8"
    )


def _kafka_json_deserializer(data: bytes):
    """Default JSON deserializer"""
    return json.loads(data.decode("utf-8")) if data else None


class AsyncKafkaProducer:
    """
    Usage:
        p = AsyncKafkaProducer("localhost:9092")
        await p.start()
        await p.send_json("topic", {"x": 1})
        await p.stop()
    Args:
        bootstrap_servers (str): Kafka bootstrap servers.
        value_serializer (callable, optional): Serializer for message values. Defaults to JSON.
        acks (int or str, optional): The number of acknowledgments the producer requires the leader to have received before considering a request complete.
            Accepts 0, 1, or 'all'. Default is 1 (moderate durability). Use 'all' for stronger durability guarantees.
    """

    def __init__(self, bootstrap_servers: str, value_serializer=None, acks=1):
        self._value_serializer = value_serializer or _default_json_serializer
        self._producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            acks=acks,
        )
        self._started = False
        logger.info(
            f"Kafka producer initialized - Bootstrap servers: {bootstrap_servers}, ACKs: {acks}"
        )


    async def start(self) -> None:
        if not self._started:
            try:
                logger.info("Starting Kafka producer...")
                await self._producer.start()
                self._started = True
                logger.info("Kafka producer started successfully")
            except Exception as e:
                logger.error(f"Failed to start Kafka producer: {e}")
                raise

    async def stop(self) -> None:
        if self._started:
            try:
                logger.info("Stopping Kafka producer...")
                await self._producer.stop()
                self._started = False
                logger.info("Kafka producer stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping Kafka producer: {e}")
                raise

    async def send_json(self, topic: str, obj: Any):
        """
        Send a JSON-serializable object to the given topic.
        Returns:
            RecordMetadata: Metadata about the sent record (topic, partition, offset, etc.).
        """
        if not self._started:
            logger.error("Kafka producer is not started")
            raise RuntimeError("Kafka producer is not started")

        try:
            value = self._value_serializer(obj)
            logger.debug(
                f"Sending message to topic '{topic}' - Size: {len(value)} bytes"
            )

            result = await self._producer.send_and_wait(topic, value=value)

            logger.debug(
                f"Message sent successfully - Topic: {result.topic}, "
                f"Partition: {result.partition}, Offset: {result.offset}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to send message to topic '{topic}': {e}")
            logger.debug(f"Message object type: {type(obj)}")
            raise


class AsyncKafkaConsumer:
    """
    Usage:
        c = AsyncKafkaConsumer(["topic1"], "localhost:9092", group_id="group")
        await c.start()
        await c.consume_forever(handler)
        await c.stop()
    """

    def __init__(
            self,
            topics: Sequence[str],
            bootstrap_servers: str,
            *,
            group_id: str,
            auto_offset_reset: str = "earliest",
            enable_auto_commit: bool = True,
    ):
        """
        Args:
            topics: List of topic names to subscribe to.
            bootstrap_servers: Kafka bootstrap servers.
            group_id: Consumer group id.
            auto_offset_reset: Where to start if no offset is committed ("earliest" or "latest"). Defaults to "earliest".
            enable_auto_commit: Whether to auto-commit offsets. Defaults to True. Set to False to manually control offset commits.
        """
        self._consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=enable_auto_commit,
            value_deserializer=_kafka_json_deserializer,
        )
        self._started = False
        logger.info(
            f"Kafka consumer initialized - Topics: {list(topics)}, "
            f"Bootstrap servers: {bootstrap_servers}, Group ID: {group_id}"
        )

    async def start(self) -> None:
        if not self._started:
            try:
                logger.info("Starting Kafka consumer...")
                await self._consumer.start()
                self._started = True
                logger.info("Kafka consumer started successfully")
            except Exception as e:
                logger.error(f"Failed to start Kafka consumer: {e}")
                raise

    async def stop(self) -> None:
        if self._started:
            try:
                logger.info("Stopping Kafka consumer...")
                await self._consumer.stop()
                self._started = False
                logger.info("Kafka consumer stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping Kafka consumer: {e}")
                raise

    async def consume_forever(
            self,
            handler: Callable[[str, Any], Awaitable[None]],
            cancel_event: Optional[asyncio.Event] = None,
    ) -> None:
        """
        Consume messages one by one. Calls handler(topic, msg_value) for each message,
        where topic is the topic name and msg_value is the deserialized JSON data.
        Messages are auto-committed and won't be re-consumed.
        Args:
            handler: Callable to process each message.
            cancel_event: Optional asyncio.Event. If set, the consumption loop will exit gracefully.
        """
        if not self._started:
            logger.error("Kafka consumer is not started")
            raise RuntimeError("Kafka consumer is not started")

        logger.info("Starting message consumption loop...")
        message_count = 0

        try:
            async for msg in self._consumer:
                if cancel_event is not None and cancel_event.is_set():
                    logger.info("Cancel event received, stopping consumption")
                    break

                message_count += 1
                logger.debug(
                    f"Received message #{message_count} from topic '{msg.topic}' "
                    f"(Partition: {msg.partition}, Offset: {msg.offset})"
                )

                try:
                    await handler(msg.topic, msg.value)
                    logger.debug(f"Message #{message_count} processed successfully")
                except Exception as e:
                    logger.exception(
                        f"Error processing message #{message_count} from topic {msg.topic}: {e}"
                    )
                    logger.debug(f"Message value: {msg.value}")

        except Exception as e:
            logger.error(f"Error in consumption loop: {e}")
            raise
        finally:
            logger.info(
                f"Message consumption ended. Total messages processed: {message_count}"
            )

    async def consume(
        self, cancel_event: Optional[asyncio.Event] = None
    ) -> AsyncIterator[Tuple[str, Any]]:
        """
        Consume messages as an async iterator.

        Args:
            cancel_event: Optional asyncio.Event. If set, the consumption will stop gracefully.

        Yields:
            Tuple[str, Any]: (topic_name, message_value) for each received message
        """
        if not self._started:
            logger.error("Kafka consumer is not started")
            raise RuntimeError("Kafka consumer is not started")

        logger.info("Starting message consumption loop...")
        message_count = 0

        try:
            async for msg in self._consumer:
                if cancel_event is not None and cancel_event.is_set():
                    logger.info("Cancel event received, stopping consumption")
                    break

                message_count += 1
                logger.debug(
                    f"Received message #{message_count} from topic '{msg.topic}' "
                    f"(Partition: {msg.partition}, Offset: {msg.offset})"
                )

                yield msg.topic, msg.value
                logger.debug(f"Message #{message_count} yielded successfully")

        except Exception as e:
            logger.error(f"Error in consumption loop: {e}")
            raise
        finally:
            logger.info(
                f"Message consumption ended. Total messages processed: {message_count}"
            )
