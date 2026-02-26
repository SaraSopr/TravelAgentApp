from collections import defaultdict
from datetime import UTC, datetime
from dataclasses import dataclass

from app.domain.auth_models import User
from app.domain.events import EventEnvelope
from app.domain.models import Plan
from app.security.auth import hash_token


class PlanRepository:
    def __init__(self) -> None:
        self._plans: dict[str, Plan] = {}

    async def save_plan(self, plan: Plan) -> None:
        self._plans[plan.trip_id] = plan

    async def get_plan(self, trip_id: str) -> Plan | None:
        return self._plans.get(trip_id)

    async def list_plans(self) -> list[Plan]:
        return list(self._plans.values())


class EventHistoryRepository:
    def __init__(self) -> None:
        self._events_by_trip: dict[str, list[EventEnvelope]] = defaultdict(list)
        self._seen_event_ids: set[str] = set()

    async def append(self, event: EventEnvelope) -> bool:
        if event.event_id in self._seen_event_ids:
            return False
        self._seen_event_ids.add(event.event_id)
        self._events_by_trip[event.aggregate_id].append(event)
        return True

    async def by_trip(self, trip_id: str) -> list[EventEnvelope]:
        return self._events_by_trip.get(trip_id, [])

    async def all_events(self) -> list[EventEnvelope]:
        events: list[EventEnvelope] = []
        for trip_events in self._events_by_trip.values():
            events.extend(trip_events)
        events.sort(key=lambda event: event.occurred_at)
        return events


class UserRepository:
    def __init__(self) -> None:
        self._users_by_id: dict[str, User] = {}
        self._users_by_username: dict[str, User] = {}

    async def create_user(self, user: User) -> None:
        self._users_by_id[user.user_id] = user
        self._users_by_username[user.username.lower()] = user

    async def get_by_username(self, username: str) -> User | None:
        return self._users_by_username.get(username.lower())

    async def get_by_id(self, user_id: str) -> User | None:
        return self._users_by_id.get(user_id)


@dataclass
class RefreshTokenRecord:
    user_id: str
    expires_at: datetime
    revoked: bool = False


class RefreshTokenRepository:
    def __init__(self) -> None:
        self._by_hash: dict[str, RefreshTokenRecord] = {}

    async def save(self, token: str, user_id: str, expires_at: datetime) -> None:
        token_hash = hash_token(token)
        self._by_hash[token_hash] = RefreshTokenRecord(user_id=user_id, expires_at=expires_at, revoked=False)

    async def get_user_id(self, token: str) -> str | None:
        token_hash = hash_token(token)
        record = self._by_hash.get(token_hash)
        if not record or record.revoked:
            return None
        if record.expires_at < datetime.now(UTC):
            return None
        return record.user_id

    async def revoke(self, token: str) -> None:
        token_hash = hash_token(token)
        record = self._by_hash.get(token_hash)
        if record:
            record.revoked = True

    async def revoke_for_user(self, user_id: str) -> None:
        for record in self._by_hash.values():
            if record.user_id == user_id:
                record.revoked = True


@dataclass
class AuthAuditRecord:
    created_at: datetime
    event_type: str
    username: str
    user_id: str | None
    client_ip: str
    detail: str


class AuthAuditRepository:
    def __init__(self) -> None:
        self._records: list[AuthAuditRecord] = []

    async def append(
        self,
        event_type: str,
        username: str,
        user_id: str | None,
        client_ip: str,
        detail: str,
    ) -> None:
        self._records.append(
            AuthAuditRecord(
                created_at=datetime.now(UTC),
                event_type=event_type,
                username=username,
                user_id=user_id,
                client_ip=client_ip,
                detail=detail,
            )
        )

    async def list_recent(self, limit: int = 100) -> list[dict]:
        items = self._records[-limit:]
        return [
            {
                "created_at": item.created_at,
                "event_type": item.event_type,
                "username": item.username,
                "user_id": item.user_id,
                "client_ip": item.client_ip,
                "detail": item.detail,
            }
            for item in reversed(items)
        ]
