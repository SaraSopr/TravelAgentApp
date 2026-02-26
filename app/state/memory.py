from datetime import UTC, datetime, timedelta


class DecisionMemory:
    def __init__(self, cooldown_seconds: int = 180) -> None:
        self._last_replan_at: dict[str, datetime] = {}
        self._cooldown_seconds = cooldown_seconds

    def in_cooldown(self, trip_id: str) -> bool:
        last = self._last_replan_at.get(trip_id)
        if not last:
            return False
        return datetime.now(UTC) - last < timedelta(seconds=self._cooldown_seconds)

    def mark_replan(self, trip_id: str) -> None:
        self._last_replan_at[trip_id] = datetime.now(UTC)
