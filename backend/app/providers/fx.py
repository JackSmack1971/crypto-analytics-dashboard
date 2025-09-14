"""FX rate client with timeout, retry, and circuit breaker logic."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Optional

import httpx


class CircuitBreakerOpen(Exception):
    """Raised when the circuit breaker is open and calls are blocked."""


@dataclass
class FXClient:
    """Simple FX client enforcing timeout, retries, and circuit breaker.

    Parameters
    ----------
    base_url: str
        Base URL for the FX service.
    timeout: float
        Request timeout in seconds.
    retries: int
        Number of retry attempts for failed requests.
    breaker_threshold: int
        Consecutive failures to open the circuit breaker.
    reset_timeout: float
        Seconds after which an open breaker resets.
    transport: Optional[httpx.BaseTransport]
        Optional custom transport for testing/mocking.
    """

    base_url: str
    timeout: float = 5.0
    retries: int = 3
    breaker_threshold: int = 5
    reset_timeout: float = 60.0
    transport: Optional[httpx.BaseTransport] = None

    _failures: int = 0
    _opened_at: Optional[float] = None

    def _breaker_open(self) -> bool:
        """Return True if breaker is currently open."""
        if self._opened_at is None:
            return False
        if time.time() - self._opened_at > self.reset_timeout:
            self._failures = 0
            self._opened_at = None
            return False
        return True

    async def get_rate(self, base: str, quote: str) -> float:
        """Fetch FX rate from base to quote.

        Raises
        ------
        CircuitBreakerOpen
            If the circuit breaker is open.
        httpx.RequestError
            On network-related errors.
        httpx.HTTPStatusError
            If the response status is not 200.
        KeyError
            If the expected rate field is missing.
        """

        if self._breaker_open():
            raise CircuitBreakerOpen("circuit breaker open")

        url = f"{self.base_url}/latest?base={base}&symbols={quote}"
        last_exc: Exception | None = None

        for _ in range(self.retries):
            try:
                async with httpx.AsyncClient(transport=self.transport) as client:
                    response = await client.get(url, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                rate = float(data["rates"][quote])
                # Reset failure count on success
                self._failures = 0
                self._opened_at = None
                return rate
            except (httpx.RequestError, httpx.HTTPStatusError, KeyError) as exc:
                last_exc = exc
                # Yield control to allow cooperative multitasking
                await asyncio.sleep(0)

        # All retries exhausted -> record failure
        self._failures += 1
        if self._failures >= self.breaker_threshold:
            self._opened_at = time.time()
        assert last_exc is not None
        raise last_exc
