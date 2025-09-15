"""Generic circuit breaker implementation.

This module provides a reusable circuit breaker with the classic CLOSED →
OPEN → HALF_OPEN transitions. It supports a probe interval, manual operator
controls, and raises :class:`CircuitBreakerOpen` when the breaker blocks calls.
"""

from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Awaitable, Callable, Generic, Optional, TypeVar


class CircuitBreakerOpen(Exception):
    """Raised when the circuit breaker is open and calls are blocked."""


class CircuitState(str, Enum):
    """Possible circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


T = TypeVar("T")


class CircuitBreaker(Generic[T]):
    """Circuit breaker controlling calls to unreliable services.

    Parameters
    ----------
    failure_threshold:
        Consecutive failures required to open the circuit.
    probe_interval:
        Seconds to wait before allowing a probe call after opening.
    time_func:
        Optional time provider for tests; defaults to :func:`time.monotonic`.
    """

    def __init__(
        self,
        failure_threshold: int,
        probe_interval: float,
        *,
        time_func: Callable[[], float] | None = None,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.probe_interval = probe_interval
        self.time = time_func or time.monotonic
        self._failures = 0
        self._state: CircuitState = CircuitState.CLOSED
        self._opened_at: Optional[float] = None
        self._frozen = False
        self._log = logging.getLogger("app.circuit_breaker")

    @property
    def state(self) -> CircuitState:
        """Return the current state."""

        return self._state

    # Hooks for Operator Console
    def force_open(self) -> None:
        """Manually open the circuit via operator control."""

        self._state = CircuitState.OPEN
        self._opened_at = self.time()
        self._frozen = False

    def reset(self, *, trace_id: str | None = None) -> None:
        """Manually close the circuit and clear freeze state."""

        self._state = CircuitState.CLOSED
        self._failures = 0
        self._opened_at = None
        self._frozen = False
        self._log.info("breaker reset", extra={"trace_id": trace_id})

    # Backwards compatibility
    force_close = reset

    async def call(
        self, func: Callable[[], Awaitable[T]], *, trace_id: str | None = None
    ) -> T:
        """Execute ``func`` respecting circuit breaker state.

        Raises
        ------
        CircuitBreakerOpen
            If the circuit breaker is open or probing interval has not elapsed.
        Exception
            Propagates errors from ``func``.
        """

        now = self.time()
        if self._state is CircuitState.OPEN:
            if not self._frozen and (
                self._opened_at is not None
                and now - self._opened_at >= self.probe_interval
            ):
                self._state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpen("circuit breaker open")

        try:
            result = await func()
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            self._failures += 1
            if status == 403:
                self._state = CircuitState.OPEN
                self._opened_at = now
                self._frozen = True
                self._log.info("breaker frozen", extra={"trace_id": trace_id})
            elif (
                self._state is CircuitState.HALF_OPEN
                or self._failures >= self.failure_threshold
            ):
                self._state = CircuitState.OPEN
                self._opened_at = now
            raise
        else:
            self._failures = 0
            self._state = CircuitState.CLOSED
            self._opened_at = None
            return result


# Security: no secrets stored; manual controls allow Operator Console oversight.
__all__ = [
    "CircuitBreaker",
    "CircuitBreakerOpen",
    "CircuitState",
]
