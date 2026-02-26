import asyncio
from collections.abc import Awaitable, Callable
import logging

import orjson

from app.bus.base import EventBus, EventHandler
from app.domain.events import EventEnvelope

try:
    from nats.aio.client import Client as NATS
except ImportError:  # pragma: no cover
    NATS = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)


class NatsEventBus(EventBus):
    def __init__(self, url: str, connect_retries: int = 20, connect_delay_ms: int = 500) -> None:
        self._url = url
        self._connect_retries = connect_retries
        self._connect_delay_ms = connect_delay_ms
        self._nc = None
        self._subscriptions: list = []

    async def connect(self) -> None:
        if NATS is None:
            raise RuntimeError("nats-py is not installed. Install with: pip install .[nats]")
        self._nc = NATS()
        for attempt in range(self._connect_retries + 1):
            try:
                await self._nc.connect(servers=[self._url])
                return
            except Exception:
                if attempt >= self._connect_retries:
                    raise
                wait_seconds = (self._connect_delay_ms / 1000.0) * (attempt + 1)
                logger.warning("NATS not ready, retrying in %.2fs", wait_seconds)
                await asyncio.sleep(wait_seconds)

    async def close(self) -> None:
        if self._nc:
            for sub in self._subscriptions:
                await sub.unsubscribe()
            await self._nc.close()

    async def publish(self, topic: str, event: EventEnvelope) -> None:
        if not self._nc:
            raise RuntimeError("NATS not connected")
        payload = orjson.dumps(event.model_dump(mode="json"))
        await self._nc.publish(topic, payload)

    async def subscribe(self, topic: str, handler: EventHandler) -> None:
        if not self._nc:
            raise RuntimeError("NATS not connected")

        async def _callback(msg) -> None:
            data = orjson.loads(msg.data)
            event = EventEnvelope.model_validate(data)
            await handler(event)

        sub = await self._nc.subscribe(topic, cb=_callback)
        self._subscriptions.append(sub)
