from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta


class LoginRateLimiter:
    def __init__(self, max_attempts: int = 8, window_seconds: int = 60, lock_seconds: int = 120) -> None:
        self._max_attempts = max_attempts
        self._window_seconds = window_seconds
        self._lock_seconds = lock_seconds
        self._attempts: dict[str, deque[datetime]] = defaultdict(deque)
        self._locked_until: dict[str, datetime] = {}

    def is_allowed(self, key: str) -> bool:
        now = datetime.now(UTC)
        locked_until = self._locked_until.get(key)
        if locked_until and now < locked_until:
            return False

        window_start = now - timedelta(seconds=self._window_seconds)
        queue = self._attempts[key]
        while queue and queue[0] < window_start:
            queue.popleft()
        if len(queue) >= self._max_attempts:
            self._locked_until[key] = now + timedelta(seconds=self._lock_seconds)
            return False
        return True

    def register_failure(self, key: str) -> None:
        now = datetime.now(UTC)
        window_start = now - timedelta(seconds=self._window_seconds)
        queue = self._attempts[key]
        while queue and queue[0] < window_start:
            queue.popleft()
        queue.append(now)
        if len(queue) >= self._max_attempts:
            self._locked_until[key] = now + timedelta(seconds=self._lock_seconds)

    def reset(self, key: str) -> None:
        self._attempts.pop(key, None)
        self._locked_until.pop(key, None)
