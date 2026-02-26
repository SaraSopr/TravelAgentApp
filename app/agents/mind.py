from dataclasses import dataclass

from app.bus.base import EventBus
from app.core.config import Settings
from app.domain.events import EventEnvelope
from app.domain.models import ImpactAssessment, Plan, ThreatEvent
from app.domain.scoring import score_threat_impact
from app.state.memory import DecisionMemory
from app.state.repository import PlanRepository

SOURCE_TRUST = {
    "transit": 0.95,
    "official_news": 0.85,
    "social": 0.60,
}


@dataclass
class MindAgent:
    bus: EventBus
    plan_repo: PlanRepository
    memory: DecisionMemory
    settings: Settings

    async def handle_threat_detected(self, event: EventEnvelope) -> None:
        trip_id = event.aggregate_id
        plan = await self.plan_repo.get_plan(trip_id)
        if not plan:
            return

        threat = ThreatEvent.model_validate(event.payload)
        source_trust = SOURCE_TRUST.get(threat.source, 0.5)
        corroboration = min(1.0, max(event.confidence, 0.3))
        impact = score_threat_impact(plan, threat, source_trust, corroboration)

        action = "monitor"
        if impact >= self.settings.threat_impact_threshold and not self.memory.in_cooldown(trip_id):
            action = "replan"

        assessment = ImpactAssessment(
            trip_id=trip_id,
            threat_id=threat.threat_id,
            impact_score=impact,
            action=action,
            rationale=f"impact={impact:.3f}, source={threat.source}, severity={threat.severity:.2f}",
        )

        assessed_event = EventEnvelope(
            event_type="mind.event.assessed",
            correlation_id=event.correlation_id,
            causation_id=event.event_id,
            producer="mind",
            aggregate_id=trip_id,
            payload=assessment.model_dump(mode="json"),
            confidence=impact,
        )
        await self.bus.publish("mind.event.assessed", assessed_event)

        if action == "replan":
            self.memory.mark_replan(trip_id)
            replan_event = EventEnvelope(
                event_type="trip.command.replan",
                correlation_id=event.correlation_id,
                causation_id=event.event_id,
                producer="mind",
                aggregate_id=trip_id,
                payload={"threat": threat.model_dump(mode="json"), "assessment": assessment.model_dump(mode="json")},
            )
            await self.bus.publish("trip.command.replan", replan_event)

    async def handle_plan_created(self, event: EventEnvelope) -> None:
        plan = Plan.model_validate(event.payload)
        await self.plan_repo.save_plan(plan)
