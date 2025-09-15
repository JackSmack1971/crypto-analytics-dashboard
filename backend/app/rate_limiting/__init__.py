"""Rate limiting utilities exposing high-level APIs."""

from __future__ import annotations

from typing import Callable, Optional

from redis import Redis

from .adaptive_clamps import AdaptiveClamp
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpen, CircuitState
from .token_bucket import TokenBucket

__all__ = [
    "AdaptiveClamp",
    "CircuitBreaker",
    "CircuitBreakerOpen",
    "CircuitState",
    "TokenBucket",
    "init",
    "acquire",
    "adjust_clamp",
]

_bucket: Optional[TokenBucket] = None
_clamp = AdaptiveClamp()


def init(
    redis_client: Redis,
    capacity: int,
    refill_rate: float,
    *,
    time_func: Callable[[], float] | None = None,
) -> None:
    """Initialize token bucket with Redis client.

    Parameters
    ----------
    redis_client:
        Redis connection used for token storage.
    capacity:
        Maximum number of tokens in each bucket.
    refill_rate:
        Tokens added per second.
    time_func:
        Optional time provider for tests.
    """

    global _bucket
    _bucket = TokenBucket(redis_client, capacity, refill_rate, time_func=time_func)


# Security: Public API to acquire tokens. Relies on prior :func:`init` call.
def acquire(provider: str, route: str, tokens: int = 1) -> bool:
    """Acquire tokens for ``provider`` and ``route``.

    Returns ``True`` if the call is allowed, ``False`` otherwise.
    """

    if _bucket is None:  # pragma: no cover - defensive
        raise RuntimeError("token bucket not initialized")
    key = f"{provider}:{route}"
    return _bucket.acquire(key, tokens)


def adjust_clamp(provider: str, success: bool) -> float:
    """Adjust and return the clamp for ``provider``."""

    return _clamp.adjust(provider, success)
