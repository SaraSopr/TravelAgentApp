import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime

from app.bus.base import EventBus, EventHandler
from app.domain.events import EventEnvelope


logger = logging.getLogger(__name__)


class InMemoryEventBus(EventBus):
    def __init__(self, max_retries: int = 2, retry_base_ms: int = 150) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._tasks: set[asyncio.Task] = set()
        self._max_retries = max_retries
        self._retry_base_ms = retry_base_ms
        self._dlq: list[EventEnvelope] = []

    async def connect(self) -> None:
        return None

    async def close(self) -> None:
        for task in list(self._tasks):
            if not task.done():
                task.cancel()
        self._tasks.clear()

    async def publish(self, topic: str, event: EventEnvelope) -> None:
        handlers = self._subscribers.get(topic, [])
        for handler in handlers:
            task = asyncio.create_task(self._dispatch_with_retry(topic, handler, event))
            self._tasks.add(task)
            task.add_done_callback(cast_remove(self._tasks))

    async def subscribe(self, topic: str, handler: EventHandler) -> None:
        self._subscribers[topic].append(handler)

    def dlq_size(self) -> int:
        return len(self._dlq)

    def read_dlq(self) -> list[EventEnvelope]:
        return list(self._dlq)

    async def _dispatch_with_retry(self, topic: str, handler: EventHandler, event: EventEnvelope) -> None:
        for attempt in range(self._max_retries + 1):
            try:
                await handler(event)
                return
            except Exception as exc:
                if topic == "system.event.failed":
                    logger.exception("DLQ handler failed")
                    return
                if attempt >= self._max_retries:
                    logger.exception("Handler failed permanently", exc_info=exc)
                    failed_event = EventEnvelope(
                        event_type="system.event.failed",
                        correlation_id=event.correlation_id,
                        causation_id=event.event_id,
                        producer="inmemory-bus",
                        aggregate_id=event.aggregate_id,
                        occurred_at=datetime.now(UTC),
                        payload={
                            "topic": topic,
                            "error": str(exc),
                            "event": event.model_dump(mode="json"),
                            "attempts": attempt + 1,
                        },
                    )
                    self._dlq.append(failed_event)
                    await self.publish("system.event.failed", failed_event)
                    return
                await asyncio.sleep((self._retry_base_ms / 1000.0) * (2**attempt))


def cast_remove(task_set: set[asyncio.Task]) -> Callable[[asyncio.Task], None]:
    def _remove(task: asyncio.Task) -> None:
        task_set.discard(task)

    return _remove
