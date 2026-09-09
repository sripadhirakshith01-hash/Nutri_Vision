"""Simple per-user request throttle (in-memory)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

_lock = Lock()
_hits: dict[int, deque[float]] = defaultdict(deque)


def check_rate_limit(user_id: int, limit_per_minute: int) -> bool:
    """Return True if the request is allowed."""
    now = time.monotonic()
    window = 60.0
    with _lock:
        bucket = _hits[user_id]
        while bucket and now - bucket[0] > window:
            bucket.popleft()
        if len(bucket) >= limit_per_minute:
            return False
        bucket.append(now)
        return True
