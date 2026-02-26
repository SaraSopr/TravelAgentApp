from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.agents.observer import ObserverAgent
from app.bus.in_memory import InMemoryEventBus
from app.core.config import get_settings
from app.domain.auth_models import AuthResponse, LoginRequest, RefreshRequest, RegisterRequest, User
from app.domain.events import EventEnvelope
from app.domain.models import CreateTripRequest, ThreatEvent
from app.security.auth import create_access_token, create_refresh_token, decode_access_token, hash_password, verify_password
from app.security.rate_limit import LoginRateLimiter
from app.services.orchestrator import SystemRuntime

router = APIRouter(prefix="/api", tags=["travel-agent"])
settings = get_settings()
login_limiter = LoginRateLimiter(
    max_attempts=settings.auth_login_max_attempts,
    window_seconds=settings.auth_login_window_seconds,
    lock_seconds=settings.auth_login_lock_seconds,
)


def get_runtime() -> SystemRuntime:
    from app.main import runtime

    return runtime


async def get_current_user(
    rt: SystemRuntime = Depends(get_runtime),
    authorization: str | None = Header(default=None),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    settings = get_settings()
    payload = decode_access_token(token, settings.auth_secret)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = str(payload.get("sub", ""))
    user = await rt.users.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/auth/register", response_model=AuthResponse)
async def register_user(request: RegisterRequest, rt: SystemRuntime = Depends(get_runtime)) -> AuthResponse:
    existing = await rt.users.get_by_username(request.username)
    if existing:
        await rt.auth_audit.append("register_failed", request.username, None, "n/a", "username_already_registered")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")

    user = User(username=request.username, password_hash=hash_password(request.password))
    await rt.users.create_user(user)
    await rt.auth_audit.append("register_success", request.username, user.user_id, "n/a", "user_created")

    access = create_access_token(user.user_id, user.username, settings.auth_secret, settings.auth_token_ttl_minutes)
    refresh = create_refresh_token()
    refresh_exp = datetime.now(UTC) + timedelta(days=7)
    await rt.refresh_tokens.save(refresh, user.user_id, refresh_exp)
    return AuthResponse(access_token=access, refresh_token=refresh, user_id=user.user_id, username=user.username)


@router.post("/auth/login", response_model=AuthResponse)
async def login_user(
    request: LoginRequest,
    raw_request: Request,
    rt: SystemRuntime = Depends(get_runtime),
) -> AuthResponse:
    client_host = raw_request.client.host if raw_request.client else "unknown"
    key = f"{request.username.lower()}::{client_host}"
    if not login_limiter.is_allowed(key):
        await rt.auth_audit.append("login_blocked", request.username, None, client_host, "temporary_lockout")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many login attempts")

    user = await rt.users.get_by_username(request.username)
    if not user or not verify_password(request.password, user.password_hash):
        login_limiter.register_failure(key)
        await rt.auth_audit.append("login_failed", request.username, None, client_host, "invalid_credentials")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    login_limiter.reset(key)
    await rt.auth_audit.append("login_success", request.username, user.user_id, client_host, "authenticated")
    access = create_access_token(user.user_id, user.username, settings.auth_secret, settings.auth_token_ttl_minutes)
    refresh = create_refresh_token()
    refresh_exp = datetime.now(UTC) + timedelta(days=7)
    await rt.refresh_tokens.save(refresh, user.user_id, refresh_exp)
    return AuthResponse(access_token=access, refresh_token=refresh, user_id=user.user_id, username=user.username)


@router.post("/auth/refresh", response_model=AuthResponse)
async def refresh_auth(request: RefreshRequest, rt: SystemRuntime = Depends(get_runtime)) -> AuthResponse:
    user_id = await rt.refresh_tokens.get_user_id(request.refresh_token)
    if not user_id:
        await rt.auth_audit.append("refresh_failed", "unknown", None, "n/a", "invalid_refresh_token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = await rt.users.get_by_id(user_id)
    if not user:
        await rt.auth_audit.append("refresh_failed", "unknown", user_id, "n/a", "user_not_found")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    await rt.refresh_tokens.revoke(request.refresh_token)

    settings = get_settings()
    access = create_access_token(user.user_id, user.username, settings.auth_secret, settings.auth_token_ttl_minutes)
    new_refresh = create_refresh_token()
    refresh_exp = datetime.now(UTC) + timedelta(days=7)
    await rt.refresh_tokens.save(new_refresh, user.user_id, refresh_exp)
    await rt.auth_audit.append("refresh_success", user.username, user.user_id, "n/a", "token_rotated")
    return AuthResponse(access_token=access, refresh_token=new_refresh, user_id=user.user_id, username=user.username)


@router.post("/auth/logout")
async def logout_user(
    request: RefreshRequest | None = None,
    rt: SystemRuntime = Depends(get_runtime),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    if request and request.refresh_token:
        await rt.refresh_tokens.revoke(request.refresh_token)
    await rt.refresh_tokens.revoke_for_user(current_user.user_id)
    await rt.auth_audit.append("logout", current_user.username, current_user.user_id, "n/a", "session_revoked")
    return {"status": "logged_out"}


@router.post("/trips")
async def create_trip(
    request: CreateTripRequest,
    rt: SystemRuntime = Depends(get_runtime),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    correlation_id = str(uuid4())
    payload = request.model_dump(mode="json")
    payload["user_id"] = current_user.user_id
    event = EventEnvelope(
        event_type="trip.command.create",
        correlation_id=correlation_id,
        producer="api",
        aggregate_id=f"trip-request-{uuid4()}",
        payload=payload,
    )
    await rt.bus.publish("trip.command.create", event)
    return {"status": "accepted", "correlation_id": correlation_id}


@router.get("/trips")
async def list_user_trips(
    rt: SystemRuntime = Depends(get_runtime),
    current_user: User = Depends(get_current_user),
) -> dict[str, list[dict]]:
    plans = await rt.plans.list_plans()
    user_plans = [plan for plan in plans if plan.user_id == current_user.user_id]
    return {"plans": [plan.model_dump(mode="json") for plan in user_plans]}


@router.get("/trips/{trip_id}")
async def get_trip(
    trip_id: str,
    rt: SystemRuntime = Depends(get_runtime),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    plan = await rt.plans.get_plan(trip_id)
    if not plan or plan.user_id != current_user.user_id:
        return {"found": False, "trip": None}
    return {"found": True, "trip": plan.model_dump(mode="json")}


@router.get("/trips/{trip_id}/alerts")
async def get_trip_alerts(
    trip_id: str,
    rt: SystemRuntime = Depends(get_runtime),
    current_user: User = Depends(get_current_user),
) -> dict[str, list[dict]]:
    plan = await rt.plans.get_plan(trip_id)
    if not plan or plan.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    events = await rt.events.by_trip(trip_id)
    alerts: list[dict] = []
    for event in events:
        if event.event_type == "obs.event.detected":
            alerts.append(
                {
                    "type": "threat",
                    "at": event.occurred_at,
                    "confidence": event.confidence,
                    "description": event.payload.get("description", "Threat detected"),
                    "source": event.payload.get("source", "unknown"),
                }
            )
        if event.event_type == "mind.event.assessed":
            alerts.append(
                {
                    "type": "assessment",
                    "at": event.occurred_at,
                    "confidence": event.confidence,
                    "description": event.payload.get("rationale", "Impact assessed"),
                    "action": event.payload.get("action", "monitor"),
                }
            )
        if event.event_type == "trip.event.updated":
            alerts.append(
                {
                    "type": "replan",
                    "at": event.occurred_at,
                    "confidence": event.confidence,
                    "description": "Itinerary updated after disruption",
                    "action": "updated",
                }
            )
    alerts.sort(key=lambda item: item["at"], reverse=True)
    return {"alerts": alerts[:30]}


@router.post("/threats/simulate")
async def simulate_threat(
    correlation_id: str,
    trip_id: str,
    rt: SystemRuntime = Depends(get_runtime),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    plan = await rt.plans.get_plan(trip_id)
    if not plan or plan.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    observer: ObserverAgent = rt.observer
    now = datetime.now(UTC)
    threat = ThreatEvent(
        city=plan.city,
        category="transit_disruption",
        severity=0.9,
        confidence=0.8,
        description="Metro line interruption due to strike",
        location={"lat": 45.4670, "lon": 9.1820},
        starts_at=now + timedelta(minutes=15),
        ends_at=now + timedelta(hours=3),
        source="transit",
    )
    await observer.ingest_threat(threat, correlation_id, trip_id)
    return {"status": "published"}


@router.get("/ops/plans")
async def list_plans(rt: SystemRuntime = Depends(get_runtime)) -> dict[str, list[dict]]:
    plans = await rt.plans.list_plans()
    return {"plans": [plan.model_dump(mode="json") for plan in plans]}


@router.get("/ops/events")
async def get_events(trip_id: str | None = None, rt: SystemRuntime = Depends(get_runtime)) -> dict[str, list[dict]]:
    if trip_id:
        events = await rt.events.by_trip(trip_id)
    else:
        events = await rt.events.all_events()
    return {"events": [event.model_dump(mode="json") for event in events]}


@router.get("/ops/dlq")
async def get_dlq(rt: SystemRuntime = Depends(get_runtime)) -> dict[str, object]:
    bus = rt.bus
    if not isinstance(bus, InMemoryEventBus):
        return {"backend": "non-inmemory", "dlq_size": None, "events": []}
    events = [event.model_dump(mode="json") for event in bus.read_dlq()]
    return {"backend": "inmemory", "dlq_size": bus.dlq_size(), "events": events}


@router.get("/ops/auth-audit")
async def get_auth_audit(rt: SystemRuntime = Depends(get_runtime), limit: int = 100) -> dict[str, list[dict]]:
    records = await rt.auth_audit.list_recent(limit=max(1, min(limit, 500)))
    return {"records": records}
