"""
Minimal aiokafka wrapper
"""
import json
from typing import Callable, Awaitable, Sequence, Optional, Any
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer


class AsyncKafkaProducer:
    """
    Usage:
        p = AsyncKafkaProducer("localhost:9092")
        await p.start()
        await p.send_json("topic", {"x": 1})
        await p.stop()
    """
    def __init__(self, bootstrap_servers: str, value_serializer=None):
        self._value_serializer = value_serializer or (lambda x: json.dumps(x, ensure_ascii=False, default=str).encode("utf-8"))
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

    async def send_json(self, topic: str, obj) -> None:
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
            value_deserializer=lambda b: json.loads(b.decode("utf-8")) if b else None,
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

    async def consume_forever(self, handler: Callable[[object], Awaitable[None]]) -> None:
        """
        Consume messages one by one. Calls handler(msg) for each message.
        Messages are auto-committed and won't be re-consumed.
        """
        async for msg in self._consumer:
            await handler(msg)