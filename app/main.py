from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.bus.base import EventBus
from app.bus.in_memory import InMemoryEventBus
from app.bus.nats_bus import NatsEventBus
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.tracing import configure_tracing
from app.services.orchestrator import SystemRuntime, build_runtime
from app.web.routes import router as web_router

settings = get_settings()
configure_logging(settings.log_level)
configure_tracing(enabled=settings.otel_enabled, service_name=settings.otel_service_name)


def build_bus() -> EventBus:
    if settings.bus_backend.lower() == "nats":
        return NatsEventBus(
            settings.nats_url,
            connect_retries=settings.nats_connect_retries,
            connect_delay_ms=settings.nats_connect_delay_ms,
        )
    return InMemoryEventBus(max_retries=settings.bus_max_retries, retry_base_ms=settings.bus_retry_base_ms)


runtime: SystemRuntime = build_runtime(settings, build_bus())


@asynccontextmanager
async def lifespan(_: FastAPI):
    await runtime.start()
    try:
        yield
    finally:
        await runtime.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(router)
app.include_router(web_router)
