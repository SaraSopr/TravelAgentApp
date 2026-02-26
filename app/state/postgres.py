from datetime import UTC, datetime
import json

from sqlalchemy import DateTime, Float, Integer, String, Text, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.domain.auth_models import User
from app.domain.events import EventEnvelope
from app.domain.models import Plan


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class PlanRow(Base):
    __tablename__ = "plans"

    trip_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    city: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer)
    risk_level: Mapped[float] = mapped_column(Float)
    budget_level: Mapped[str] = mapped_column(String(32))
    mobility_mode: Mapped[str] = mapped_column(String(64))
    interests: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(32))
    activities: Mapped[dict] = mapped_column(JSONB)


class EventRow(Base):
    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    aggregate_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(128), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    raw: Mapped[dict] = mapped_column(JSONB)


class RefreshTokenRow(Base):
    __tablename__ = "refresh_tokens"

    token_hash: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked: Mapped[bool] = mapped_column(default=False)


class AuthAuditRow(Base):
    __tablename__ = "auth_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=lambda: datetime.now(UTC))
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    username: Mapped[str] = mapped_column(String(128), index=True)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    client_ip: Mapped[str] = mapped_column(String(64))
    detail: Mapped[str] = mapped_column(Text)


class Database:
    def __init__(self, dsn: str) -> None:
        self.engine = create_async_engine(dsn, future=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def init(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        await self.engine.dispose()


class PostgresUserRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def create_user(self, user: User) -> None:
        async with self._db.session_factory() as session:
            session.add(
                UserRow(
                    user_id=user.user_id,
                    username=user.username,
                    password_hash=user.password_hash,
                    created_at=user.created_at,
                )
            )
            await session.commit()

    async def get_by_username(self, username: str) -> User | None:
        async with self._db.session_factory() as session:
            row = (await session.execute(select(UserRow).where(UserRow.username == username))).scalar_one_or_none()
            if not row:
                return None
            return User(user_id=row.user_id, username=row.username, password_hash=row.password_hash, created_at=row.created_at)

    async def get_by_id(self, user_id: str) -> User | None:
        async with self._db.session_factory() as session:
            row = (await session.execute(select(UserRow).where(UserRow.user_id == user_id))).scalar_one_or_none()
            if not row:
                return None
            return User(user_id=row.user_id, username=row.username, password_hash=row.password_hash, created_at=row.created_at)


class PostgresPlanRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def save_plan(self, plan: Plan) -> None:
        async with self._db.session_factory() as session:
            existing = await session.get(PlanRow, plan.trip_id)
            payload = plan.model_dump(mode="json")
            if existing:
                existing.user_id = plan.user_id
                existing.city = plan.city
                existing.created_at = plan.created_at
                existing.version = plan.version
                existing.risk_level = plan.risk_level
                existing.budget_level = plan.budget_level
                existing.mobility_mode = plan.mobility_mode
                existing.interests = payload.get("interests", [])
                existing.status = plan.status
                existing.activities = payload.get("activities", [])
            else:
                session.add(
                    PlanRow(
                        trip_id=plan.trip_id,
                        user_id=plan.user_id,
                        city=plan.city,
                        created_at=plan.created_at,
                        version=plan.version,
                        risk_level=plan.risk_level,
                        budget_level=plan.budget_level,
                        mobility_mode=plan.mobility_mode,
                        interests=payload.get("interests", []),
                        status=plan.status,
                        activities=payload.get("activities", []),
                    )
                )
            await session.commit()

    async def get_plan(self, trip_id: str) -> Plan | None:
        async with self._db.session_factory() as session:
            row = await session.get(PlanRow, trip_id)
            if not row:
                return None
            return Plan(
                trip_id=row.trip_id,
                user_id=row.user_id,
                city=row.city,
                created_at=row.created_at,
                version=row.version,
                risk_level=row.risk_level,
                budget_level=row.budget_level,
                mobility_mode=row.mobility_mode,
                interests=list(row.interests or []),
                status=row.status,
                activities=row.activities,
            )

    async def list_plans(self) -> list[Plan]:
        async with self._db.session_factory() as session:
            rows = (await session.execute(select(PlanRow).order_by(PlanRow.created_at.desc()))).scalars().all()
            return [
                Plan(
                    trip_id=row.trip_id,
                    user_id=row.user_id,
                    city=row.city,
                    created_at=row.created_at,
                    version=row.version,
                    risk_level=row.risk_level,
                    budget_level=row.budget_level,
                    mobility_mode=row.mobility_mode,
                    interests=list(row.interests or []),
                    status=row.status,
                    activities=row.activities,
                )
                for row in rows
            ]


class PostgresEventHistoryRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def append(self, event: EventEnvelope) -> bool:
        async with self._db.session_factory() as session:
            existing = await session.get(EventRow, event.event_id)
            if existing:
                return False
            session.add(
                EventRow(
                    event_id=event.event_id,
                    aggregate_id=event.aggregate_id,
                    event_type=event.event_type,
                    occurred_at=event.occurred_at,
                    raw=json.loads(event.model_dump_json()),
                )
            )
            await session.commit()
            return True

    async def by_trip(self, trip_id: str) -> list[EventEnvelope]:
        async with self._db.session_factory() as session:
            rows = (
                await session.execute(select(EventRow).where(EventRow.aggregate_id == trip_id).order_by(EventRow.occurred_at))
            ).scalars().all()
            return [EventEnvelope.model_validate(row.raw) for row in rows]

    async def all_events(self) -> list[EventEnvelope]:
        async with self._db.session_factory() as session:
            rows = (await session.execute(select(EventRow).order_by(EventRow.occurred_at))).scalars().all()
            return [EventEnvelope.model_validate(row.raw) for row in rows]


class PostgresRefreshTokenRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def save(self, token: str, user_id: str, expires_at: datetime) -> None:
        from app.security.auth import hash_token

        token_hash = hash_token(token)
        async with self._db.session_factory() as session:
            existing = await session.get(RefreshTokenRow, token_hash)
            if existing:
                existing.user_id = user_id
                existing.expires_at = expires_at
                existing.revoked = False
            else:
                session.add(
                    RefreshTokenRow(
                        token_hash=token_hash,
                        user_id=user_id,
                        expires_at=expires_at,
                        revoked=False,
                    )
                )
            await session.commit()

    async def get_user_id(self, token: str) -> str | None:
        from app.security.auth import hash_token

        token_hash = hash_token(token)
        async with self._db.session_factory() as session:
            row = await session.get(RefreshTokenRow, token_hash)
            if not row or row.revoked:
                return None
            if row.expires_at < datetime.now(UTC):
                return None
            return row.user_id

    async def revoke(self, token: str) -> None:
        from app.security.auth import hash_token

        token_hash = hash_token(token)
        async with self._db.session_factory() as session:
            row = await session.get(RefreshTokenRow, token_hash)
            if row:
                row.revoked = True
                await session.commit()

    async def revoke_for_user(self, user_id: str) -> None:
        async with self._db.session_factory() as session:
            rows = (await session.execute(select(RefreshTokenRow).where(RefreshTokenRow.user_id == user_id))).scalars().all()
            for row in rows:
                row.revoked = True
            await session.commit()


class PostgresAuthAuditRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def append(
        self,
        event_type: str,
        username: str,
        user_id: str | None,
        client_ip: str,
        detail: str,
    ) -> None:
        async with self._db.session_factory() as session:
            session.add(
                AuthAuditRow(
                    created_at=datetime.now(UTC),
                    event_type=event_type,
                    username=username,
                    user_id=user_id,
                    client_ip=client_ip,
                    detail=detail,
                )
            )
            await session.commit()

    async def list_recent(self, limit: int = 100) -> list[dict]:
        async with self._db.session_factory() as session:
            rows = (
                await session.execute(select(AuthAuditRow).order_by(AuthAuditRow.created_at.desc()).limit(limit))
            ).scalars().all()
            return [
                {
                    "created_at": row.created_at,
                    "event_type": row.event_type,
                    "username": row.username,
                    "user_id": row.user_id,
                    "client_ip": row.client_ip,
                    "detail": row.detail,
                }
                for row in rows
            ]
