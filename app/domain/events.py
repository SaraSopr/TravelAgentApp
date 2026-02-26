from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str
    causation_id: str | None = None
    producer: str
    schema_version: str = "1.0"
    aggregate_id: str
    sequence: int = 0
    confidence: float = 1.0
    payload: dict[str, Any]
    source_meta: dict[str, Any] = Field(default_factory=dict)
