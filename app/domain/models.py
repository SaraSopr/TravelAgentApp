from datetime import UTC, datetime, timedelta
from uuid import uuid4

from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    lat: float
    lon: float


class Activity(BaseModel):
    name: str
    category: str
    location: Coordinates
    address: str
    starts_at: datetime
    ends_at: datetime
    transport_mode: str = "walk"
    estimated_cost_eur: float = 0.0
    notes: str = ""


class Plan(BaseModel):
    trip_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    city: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    version: int = 1
    activities: list[Activity]
    risk_level: float = 0.0
    budget_level: str = "medium"
    mobility_mode: str = "public_transport"
    interests: list[str] = Field(default_factory=list)
    status: str = "stable"


class CreateTripRequest(BaseModel):
    user_id: str = ""
    city: str
    intent: str
    start_time: datetime | None = None
    budget_level: str = "medium"
    mobility_mode: str = "public_transport"
    interests: list[str] = Field(default_factory=list)


class ThreatEvent(BaseModel):
    threat_id: str = Field(default_factory=lambda: str(uuid4()))
    city: str
    category: str
    severity: float
    confidence: float
    description: str
    location: Coordinates
    starts_at: datetime
    ends_at: datetime
    source: str


class ImpactAssessment(BaseModel):
    trip_id: str
    threat_id: str
    impact_score: float
    action: str
    rationale: str


def default_activities(city: str, start_time: datetime | None, interests: list[str] | None = None) -> list[Activity]:
    base = start_time or datetime.now(UTC)
    normalized_city = city.strip().lower()
    selected = [interest.lower() for interest in (interests or [])]

    if normalized_city == "rome":
        templates = [
            ("Colosseum District Walk", "sightseeing", 41.8902, 12.4922, "Colosseo, Roma", 35, 120),
            ("Vatican Museums", "culture", 41.9065, 12.4536, "Viale Vaticano, Roma", 160, 260),
            ("Trastevere Dinner", "food", 41.8897, 12.4694, "Trastevere, Roma", 310, 430),
        ]
    elif normalized_city == "paris":
        templates = [
            ("Seine Riverside Walk", "sightseeing", 48.8584, 2.2945, "Champ de Mars, Paris", 30, 120),
            ("Louvre Visit", "culture", 48.8606, 2.3376, "Rue de Rivoli, Paris", 160, 260),
            ("Le Marais Food Tour", "food", 48.8579, 2.3622, "Le Marais, Paris", 320, 420),
        ]
    else:
        templates = [
            ("City Center Walk", "sightseeing", 45.4642, 9.1900, f"Centro {city}", 30, 120),
            ("Museum Visit", "culture", 45.4670, 9.1820, f"Museo {city}", 160, 250),
            ("Dinner District", "food", 45.4700, 9.2000, f"Ristorante {city}", 300, 420),
        ]

    activities: list[Activity] = []
    for name, category, lat, lon, address, start_offset, end_offset in templates:
        activities.append(
            Activity(
                name=f"{name} - {city}",
                category=category,
                location=Coordinates(lat=lat, lon=lon),
                address=address,
                starts_at=base + timedelta(minutes=start_offset),
                ends_at=base + timedelta(minutes=end_offset),
                transport_mode="walk" if category == "sightseeing" else "metro",
                estimated_cost_eur=0.0 if category == "sightseeing" else 18.0,
                notes="Optimized for your profile",
            )
        )

    if "shopping" in selected:
        activities.append(
            Activity(
                name=f"Local Shopping Session - {city}",
                category="shopping",
                location=Coordinates(lat=activities[-1].location.lat + 0.01, lon=activities[-1].location.lon + 0.01),
                address=f"Shopping District {city}",
                starts_at=base + timedelta(minutes=440),
                ends_at=base + timedelta(minutes=520),
                transport_mode="walk",
                estimated_cost_eur=25.0,
                notes="Based on shopping interest",
            )
        )

    return activities
