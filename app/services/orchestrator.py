from dataclasses import dataclass
import asyncio
import logging

from app.agents.mind import MindAgent
from app.agents.observer import ObserverAgent
from app.agents.planner import PlannerAgent
from app.bus.base import EventBus
from app.core.config import Settings
from app.core.tracing import get_tracer
from app.state.memory import DecisionMemory
from app.state.repository import AuthAuditRepository, EventHistoryRepository, PlanRepository, RefreshTokenRepository, UserRepository

logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)


@dataclass
class SystemRuntime:
    settings: Settings
    bus: EventBus
    planner: PlannerAgent
    observer: ObserverAgent
    mind: MindAgent
    plans: PlanRepository
    events: EventHistoryRepository
    users: UserRepository
    refresh_tokens: RefreshTokenRepository
    auth_audit: AuthAuditRepository
    db: object | None = None
    observer_task: asyncio.Task | None = None

    async def start(self) -> None:
        with tracer.start_as_current_span("runtime.start"):
            await self.bus.connect()
            if self.db is not None and hasattr(self.db, "init"):
                await self.db.init()

        async def persist_all(event):
            await self.events.append(event)

        await self.bus.subscribe("trip.command.create", persist_all)
        await self.bus.subscribe("trip.event.created", persist_all)
        await self.bus.subscribe("obs.event.detected", persist_all)
        await self.bus.subscribe("mind.event.assessed", persist_all)
        await self.bus.subscribe("trip.command.replan", persist_all)
        await self.bus.subscribe("trip.event.updated", persist_all)
        await self.bus.subscribe("system.event.failed", persist_all)

        await self.bus.subscribe("trip.command.create", self.planner.handle_create_trip)
        await self.bus.subscribe("trip.event.created", self.mind.handle_plan_created)
        await self.bus.subscribe("obs.event.detected", self.mind.handle_threat_detected)
        await self.bus.subscribe("trip.command.replan", self.planner.handle_replan_trip)

        if self.settings.observer_enabled:
            self.observer_task = asyncio.create_task(self._observer_loop())

    async def stop(self) -> None:
        if self.observer_task and not self.observer_task.done():
            self.observer_task.cancel()
        await self.bus.close()
        if self.db is not None and hasattr(self.db, "close"):
            await self.db.close()

    async def _observer_loop(self) -> None:
        while True:
            try:
                with tracer.start_as_current_span("observer.poll_once"):
                    produced = await self.observer.poll_once()
                if produced:
                    logger.info("Observer emitted %s threat events", produced)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Observer polling loop failed")
            await asyncio.sleep(self.settings.observer_poll_seconds)


def build_runtime(settings: Settings, bus: EventBus) -> SystemRuntime:
    from app.connectors.observer_sources import ObserverSources

    db = None
    if settings.state_backend.lower() == "postgres":
        from app.state.postgres import (
            PostgresAuthAuditRepository,
            Database,
            PostgresEventHistoryRepository,
            PostgresPlanRepository,
            PostgresRefreshTokenRepository,
            PostgresUserRepository,
        )

        db = Database(settings.postgres_dsn)
        plan_repo = PostgresPlanRepository(db)
        event_repo = PostgresEventHistoryRepository(db)
        user_repo = PostgresUserRepository(db)
        refresh_repo = PostgresRefreshTokenRepository(db)
        auth_audit_repo = PostgresAuthAuditRepository(db)
    else:
        plan_repo = PlanRepository()
        event_repo = EventHistoryRepository()
        user_repo = UserRepository()
        refresh_repo = RefreshTokenRepository()
        auth_audit_repo = AuthAuditRepository()

    memory = DecisionMemory(settings.replan_cooldown_seconds)
    sources = ObserverSources(settings)

    planner = PlannerAgent(bus=bus, plan_repo=plan_repo)
    observer = ObserverAgent(bus=bus, plan_repo=plan_repo, sources=sources)
    mind = MindAgent(bus=bus, plan_repo=plan_repo, memory=memory, settings=settings)

    return SystemRuntime(
        settings=settings,
        bus=bus,
        planner=planner,
        observer=observer,
        mind=mind,
        plans=plan_repo,
        events=event_repo,
        users=user_repo,
        refresh_tokens=refresh_repo,
        auth_audit=auth_audit_repo,
        db=db,
    )
