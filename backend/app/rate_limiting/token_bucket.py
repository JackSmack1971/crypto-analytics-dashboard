"""Token bucket rate limiter with Redis backend and local fallback.

This module implements a simple token bucket algorithm. Tokens are stored in
Redis for cross-process coordination. When Redis is unavailable, an
in-process dictionary is used as a fallback to avoid unlimited requests.
"""

from __future__ import annotations

import json
import time
from typing import Callable, Dict, Tuple

from redis import Redis
from redis.exceptions import RedisError


class TokenBucket:
    """Redis-backed token bucket with in-process fallback.

    Parameters
    ----------
    redis_client:
        Redis connection used for shared token storage.
    capacity:
        Maximum number of tokens that can be stored in the bucket.
    refill_rate:
        Number of tokens added per second.
    time_func:
        Optional time provider for testing; defaults to :func:`time.time`.
    """

    def __init__(
        self,
        redis_client: Redis,
        capacity: int,
        refill_rate: float,
        *,
        time_func: Callable[[], float] | None = None,
    ) -> None:
        self.redis = redis_client
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.time = time_func or time.time
        self.local_buckets: Dict[str, Tuple[float, float]] = {}

    # Security: No secrets stored; fallback prevents unlimited calls on Redis outage.
    def acquire(self, key: str, tokens: int = 1) -> bool:
        """Attempt to take tokens from the bucket.

        Returns ``True`` if enough tokens were available, ``False`` otherwise.
        On Redis errors the function falls back to a process-local bucket.
        """

        now = self.time()
        try:
            data = self.redis.get(key)
            if data is None:
                available = self.capacity
                last = now
            else:
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                available, last = json.loads(data)
            available = float(available)
            last = float(last)

            delta = max(0.0, now - last) * self.refill_rate
            available = min(self.capacity, available + delta)
            allowed = available >= tokens
            if allowed:
                available -= tokens
            self.redis.set(key, json.dumps([available, now]))
            return allowed
        except RedisError:
            # Fallback to in-process bucket on Redis failure
            return self._acquire_local(key, now, tokens)

    def _acquire_local(self, key: str, now: float, tokens: int) -> bool:
        """Local in-memory bucket used when Redis is unavailable."""

        available, last = self.local_buckets.get(key, (self.capacity, now))
        delta = max(0.0, now - last) * self.refill_rate
        available = min(self.capacity, available + delta)
        allowed = available >= tokens
        if allowed:
            available -= tokens
        self.local_buckets[key] = (available, now)
        return allowed
