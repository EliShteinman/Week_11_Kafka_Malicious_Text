"""
Minimal aiokafka wrapper
"""
import json
from typing import Callable, Awaitable, Sequence, Optional
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer


class AsyncKafkaProducer:
    def __init__(self, bootstrap_servers: str):
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
        value = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        await self._producer.send_and_wait(topic, value=value)


class AsyncKafkaConsumer:
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
        async for msg in self._consumer:
            await handler(msg)