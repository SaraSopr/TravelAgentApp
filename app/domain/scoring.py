from datetime import UTC, datetime

from app.domain.models import Plan, ThreatEvent


def recency_score(starts_at: datetime, now: datetime | None = None) -> float:
    now = now or datetime.now(UTC)
    delta_minutes = max((starts_at - now).total_seconds() / 60.0, 0.0)
    if delta_minutes <= 30:
        return 1.0
    if delta_minutes <= 120:
        return 0.7
    if delta_minutes <= 360:
        return 0.4
    return 0.2


def geo_overlap_score(plan: Plan, threat: ThreatEvent) -> float:
    for activity in plan.activities:
        lat_distance = abs(activity.location.lat - threat.location.lat)
        lon_distance = abs(activity.location.lon - threat.location.lon)
        if lat_distance <= 0.02 and lon_distance <= 0.02:
            return 1.0
    return 0.3


def score_threat_impact(
    plan: Plan,
    threat: ThreatEvent,
    source_trust: float,
    corroboration: float,
    wt: float = 0.30,
    wr: float = 0.25,
    wc: float = 0.20,
    wg: float = 0.25,
) -> float:
    recency = recency_score(threat.starts_at)
    geo = geo_overlap_score(plan, threat)
    raw_score = wt * source_trust + wr * recency + wc * corroboration + wg * geo
    weighted_severity = raw_score * threat.severity * threat.confidence
    return min(max(weighted_severity, 0.0), 1.0)
