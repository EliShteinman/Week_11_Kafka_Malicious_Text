import asyncio
import datetime
import json
import logging
from typing import Any, Awaitable, Callable, Optional, Sequence

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

    async def start(self) -> None:
        if not self._started:
            await self._producer.start()
            self._started = True

    async def stop(self) -> None:
        if self._started:
            await self._producer.stop()
            self._started = False

    async def send_json(self, topic: str, obj: Any):
        """
        Send a JSON-serializable object to the given topic.
        Returns:
            RecordMetadata: Metadata about the sent record (topic, partition, offset, etc.).
        """
        value = self._value_serializer(obj)
        return await self._producer.send_and_wait(topic, value=value)


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
    ):
        """
        Args:
            topics: List of topic names to subscribe to.
            bootstrap_servers: Kafka bootstrap servers.
            group_id: Consumer group id.
            auto_offset_reset: Where to start if no offset is committed ("earliest" or "latest"). Defaults to "earliest".
        """
        self._consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=True,
            value_deserializer=_kafka_json_deserializer,
        )
        self._started = False

    async def start(self) -> None:
        if not self._started:
            await self._consumer.start()
            self._started = True

    async def stop(self) -> None:
        if self._started:
            await self._consumer.stop()
            self._started = False

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
        async for msg in self._consumer:
            if cancel_event is not None and cancel_event.is_set():
                break
            try:
                await handler(msg.topic, msg.value)
            except Exception as e:
                logger.exception(
                    f"Error processing message from topic {msg.topic}: {e}"
                )
