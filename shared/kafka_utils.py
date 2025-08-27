import json
from typing import Callable, Awaitable, Sequence, Any
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer


def _default_json_serializer(obj) -> bytes:
    """Default JSON serializer with datetime support"""
    return json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")


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
    """
    def __init__(self, bootstrap_servers: str, value_serializer=None):
        self._value_serializer = value_serializer or _default_json_serializer
        self._producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            acks=1,
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

    async def send_json(self, topic: str, obj: Any) -> None:
        value = self._value_serializer(obj)
        await self._producer.send_and_wait(topic, value=value)


class AsyncKafkaConsumer:
    """
    Usage:
        c = AsyncKafkaConsumer(["topic1"], "localhost:9092", group_id="group")
        await c.start()
        await c.consume_forever(handler)
        await c.stop()
    """
    def __init__(self, topics: Sequence[str], bootstrap_servers: str, *, group_id: str):
        self._consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            auto_offset_reset="latest",
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

    async def consume_forever(self, handler: Callable[[str, Any], Awaitable[None]]) -> None:
        """
        Consume messages one by one. Calls handler(topic, msg_value) for each message,
        where topic is the topic name and msg_value is the deserialized JSON data.
        Messages are auto-committed and won't be re-consumed.
        """
        async for msg in self._consumer:
            await handler(msg.topic, msg.value)