import asyncio
from uuid import uuid4

import pytest

from app.bus.in_memory import InMemoryEventBus
from app.domain.events import EventEnvelope


@pytest.mark.asyncio
async def test_inmemory_bus_retries_then_dlq() -> None:
    bus = InMemoryEventBus(max_retries=1, retry_base_ms=1)
    await bus.connect()

    async def always_fail(_: EventEnvelope) -> None:
        raise RuntimeError("boom")

    await bus.subscribe("x.topic", always_fail)
    event = EventEnvelope(
        event_type="x.topic",
        correlation_id=str(uuid4()),
        producer="test",
        aggregate_id="trip-1",
        payload={"x": 1},
    )
    await bus.publish("x.topic", event)

    await asyncio.sleep(0.05)

    assert bus.dlq_size() == 1
    failed = bus.read_dlq()[0]
    assert failed.event_type == "system.event.failed"
    assert failed.payload["topic"] == "x.topic"

    await bus.close()
