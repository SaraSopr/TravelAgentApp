from dataclasses import dataclass

from app.bus.base import EventBus
from app.domain.events import EventEnvelope
from app.domain.models import CreateTripRequest, Plan, ThreatEvent, default_activities
from app.state.repository import PlanRepository


@dataclass
class PlannerAgent:
    bus: EventBus
    plan_repo: PlanRepository

    async def handle_create_trip(self, event: EventEnvelope) -> None:
        request = CreateTripRequest.model_validate(event.payload)
        plan = Plan(
            user_id=request.user_id,
            city=request.city,
            activities=default_activities(request.city, request.start_time, request.interests),
            risk_level=0.1,
            budget_level=request.budget_level,
            mobility_mode=request.mobility_mode,
            interests=request.interests,
            status="stable",
        )
        await self.plan_repo.save_plan(plan)

        created_event = EventEnvelope(
            event_type="trip.event.created",
            correlation_id=event.correlation_id,
            causation_id=event.event_id,
            producer="planner",
            aggregate_id=plan.trip_id,
            sequence=1,
            payload=plan.model_dump(mode="json"),
        )
        await self.bus.publish("trip.event.created", created_event)

    async def handle_replan_trip(self, event: EventEnvelope) -> None:
        trip_id = event.aggregate_id
        plan = await self.plan_repo.get_plan(trip_id)
        if not plan:
            return

        threat = ThreatEvent.model_validate(event.payload["threat"])
        filtered_activities = [
            act
            for act in plan.activities
            if not (
                abs(act.location.lat - threat.location.lat) <= 0.02
                and abs(act.location.lon - threat.location.lon) <= 0.02
                and act.starts_at <= threat.ends_at
                and act.ends_at >= threat.starts_at
            )
        ]
        if not filtered_activities:
            fallback = default_activities(plan.city, plan.created_at, plan.interests)
            filtered_activities = fallback[:1]
        plan.activities = filtered_activities
        plan.version += 1
        plan.risk_level = max(plan.risk_level, 0.6)
        plan.status = "replanned"
        await self.plan_repo.save_plan(plan)

        updated_event = EventEnvelope(
            event_type="trip.event.updated",
            correlation_id=event.correlation_id,
            causation_id=event.event_id,
            producer="planner",
            aggregate_id=plan.trip_id,
            sequence=plan.version,
            payload=plan.model_dump(mode="json"),
        )
        await self.bus.publish("trip.event.updated", updated_event)
