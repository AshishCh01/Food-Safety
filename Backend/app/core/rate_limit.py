"""In-memory request-rate limiting for abuse-prone public endpoints
(docs/SECURITY_AND_RBAC.md section 11, docs/API_ARCHITECTURE.md section 18:
"Rate-limit public complaint creation and authentication endpoints").

This is a single-process sliding-window limiter keyed by client IP. It is
intentionally dependency-free (no Redis/slowapi) since the current
deployment target is a single backend process - see
docs/DEVELOPMENT_ROADMAP.md Phase 13. A multi-worker/multi-instance
production deployment would need a shared store (e.g. Redis) instead of
this in-process dict; that is a documented known limitation, not a bug.
"""

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request

from app.utils.exceptions import RateLimitExceededError


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._buckets[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                raise RateLimitExceededError()
            bucket.append(now)

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()

    def __call__(self, request: Request) -> None:
        client_host = request.client.host if request.client else "unknown"
        self.check(client_host)


# One bucket set per protected endpoint so hammering one doesn't exhaust the
# quota for another. Limits are deliberately generous enough not to bother a
# real user retyping a password, tight enough to blunt scripted abuse.
login_rate_limiter = InMemoryRateLimiter(max_requests=10, window_seconds=60)
register_rate_limiter = InMemoryRateLimiter(max_requests=5, window_seconds=60)
refresh_rate_limiter = InMemoryRateLimiter(max_requests=30, window_seconds=60)
complaint_creation_rate_limiter = InMemoryRateLimiter(max_requests=20, window_seconds=60)

ALL_RATE_LIMITERS = (
    login_rate_limiter,
    register_rate_limiter,
    refresh_rate_limiter,
    complaint_creation_rate_limiter,
)


def reset_all_rate_limiters() -> None:
    """Test-only helper - see app/tests/conftest.py."""
    for limiter in ALL_RATE_LIMITERS:
        limiter.reset()
