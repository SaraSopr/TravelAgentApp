from dataclasses import dataclass
from uuid import uuid4

from app.bus.base import EventBus
from app.connectors.observer_sources import ObserverSources
from app.domain.events import EventEnvelope
from app.domain.models import ThreatEvent
from app.state.repository import PlanRepository


@dataclass
class ObserverAgent:
    bus: EventBus
    plan_repo: PlanRepository
    sources: ObserverSources

    async def ingest_threat(self, threat: ThreatEvent, correlation_id: str, trip_id: str) -> None:
        event = EventEnvelope(
            event_type="obs.event.detected",
            correlation_id=correlation_id,
            producer="observer",
            aggregate_id=trip_id,
            payload=threat.model_dump(mode="json"),
            confidence=threat.confidence,
            source_meta={"source": threat.source},
        )
        await self.bus.publish("obs.event.detected", event)

    async def poll_once(self) -> int:
        plans = await self.plan_repo.list_plans()
        total = 0
        for plan in plans:
            threats = await self.sources.collect(plan.city)
            correlation_id = str(uuid4())
            for threat in threats:
                await self.ingest_threat(threat, correlation_id=correlation_id, trip_id=plan.trip_id)
                total += 1
        return total
