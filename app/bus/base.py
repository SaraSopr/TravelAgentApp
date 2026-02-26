from collections.abc import Awaitable, Callable

from app.domain.events import EventEnvelope

EventHandler = Callable[[EventEnvelope], Awaitable[None]]


class EventBus:
    async def connect(self) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError

    async def publish(self, topic: str, event: EventEnvelope) -> None:
        raise NotImplementedError

    async def subscribe(self, topic: str, handler: EventHandler) -> None:
        raise NotImplementedError
