import pytest
from app.rate_limiting.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
    CircuitState,
)

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_circuit_breaker_transitions_success():
    now = 0.0

    def time_func() -> float:
        return now

    breaker = CircuitBreaker(
        failure_threshold=1, probe_interval=10, time_func=time_func
    )

    async def fail():
        raise RuntimeError("boom")

    async def success():
        return "ok"

    with pytest.raises(RuntimeError):
        await breaker.call(fail)
    assert breaker.state is CircuitState.OPEN

    with pytest.raises(CircuitBreakerOpen):
        await breaker.call(success)

    now += 11
    result = await breaker.call(success)
    assert result == "ok"
    assert breaker.state is CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_probe_failure_reopens():
    now = 0.0

    def time_func() -> float:
        return now

    breaker = CircuitBreaker(failure_threshold=1, probe_interval=5, time_func=time_func)

    async def fail():
        raise ValueError("nope")

    with pytest.raises(ValueError):
        await breaker.call(fail)
    assert breaker.state is CircuitState.OPEN

    now += 6
    with pytest.raises(ValueError):
        await breaker.call(fail)
    assert breaker.state is CircuitState.OPEN

    with pytest.raises(CircuitBreakerOpen):
        await breaker.call(fail)


@pytest.mark.asyncio
async def test_manual_open_close():
    breaker = CircuitBreaker(failure_threshold=2, probe_interval=30)

    async def success():
        return 1

    breaker.force_open()
    assert breaker.state is CircuitState.OPEN
    with pytest.raises(CircuitBreakerOpen):
        await breaker.call(success)

    breaker.force_close()
    result = await breaker.call(success)
    assert result == 1
    assert breaker.state is CircuitState.CLOSED
