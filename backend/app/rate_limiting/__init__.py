"""Rate limiting utilities exposing high-level APIs."""

from __future__ import annotations

from typing import Callable, Dict, Optional

from redis import Redis

from .adaptive_clamps import AdaptiveClamp
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpen, CircuitState
from .token_bucket import TokenBucket
from .provider_budgets import DEFAULT_BUDGETS, ProviderBudget

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

_buckets: Dict[tuple[str, str], TokenBucket] = {}
_budgets: Dict[str, ProviderBudget] = DEFAULT_BUDGETS.copy()
_clamp = AdaptiveClamp()


def init(
    redis_client: Redis,
    budgets: Dict[str, ProviderBudget] | None = None,
    *,
    time_func: Callable[[], float] | None = None,
) -> None:
    """Initialize token buckets for all providers.

    ``budgets`` may override the default :data:`DEFAULT_BUDGETS` mapping.
    """

    global _buckets, _budgets
    _buckets = {}
    _budgets = budgets or DEFAULT_BUDGETS
    for provider, budget in _budgets.items():
        if budget.per_sec:
            _buckets[(provider, "per_sec")] = TokenBucket(
                redis_client,
                capacity=float(budget.per_sec),
                refill_rate=float(budget.per_sec),
                time_func=time_func,
            )
        if budget.per_min:
            _buckets[(provider, "per_min")] = TokenBucket(
                redis_client,
                capacity=float(budget.per_min),
                refill_rate=float(budget.per_min) / 60.0,
                time_func=time_func,
            )
        if budget.per_day:
            _buckets[(provider, "per_day")] = TokenBucket(
                redis_client,
                capacity=float(budget.per_day),
                refill_rate=float(budget.per_day) / 86400.0,
                time_func=time_func,
            )


# Security: Public API to acquire tokens. Relies on prior :func:`init` call.
def acquire(provider: str, route: str, tokens: float = 1.0) -> tuple[bool, float]:
    """Acquire tokens for ``provider``.

    Returns tuple of ``(allowed, retry_after_seconds)``.
    """

    if not _buckets:  # pragma: no cover - defensive
        raise RuntimeError("token buckets not initialized")

    clamp = _clamp.get(provider)
    cost = tokens / clamp if clamp > 0 else float("inf")
    retry_after = 0.0
    allowed = True
    for (prov, period), bucket in _buckets.items():
        if prov != provider:
            continue
        key = f"{provider}:{period}"
        ok, wait = bucket.acquire(key, cost)
        if not ok:
            allowed = False
            retry_after = max(retry_after, wait)
    return allowed, retry_after


def adjust_clamp(provider: str, success: bool) -> float:
    """Adjust and return the clamp for ``provider``."""

    return _clamp.adjust(provider, success)
