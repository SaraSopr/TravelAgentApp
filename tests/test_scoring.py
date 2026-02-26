from datetime import UTC, datetime, timedelta

from app.domain.models import Plan, ThreatEvent, default_activities
from app.domain.scoring import score_threat_impact


def test_score_threat_impact_in_range() -> None:
    now = datetime.now(UTC)
    plan = Plan(user_id="u1", city="Milan", activities=default_activities("Milan", now))
    threat = ThreatEvent(
        city="Milan",
        category="protest",
        severity=0.8,
        confidence=0.9,
        description="City center protest",
        location={"lat": 45.4642, "lon": 9.1900},
        starts_at=now + timedelta(minutes=20),
        ends_at=now + timedelta(hours=2),
        source="official_news",
    )
    score = score_threat_impact(plan, threat, source_trust=0.85, corroboration=0.8)
    assert 0.0 <= score <= 1.0
    assert score > 0.4
