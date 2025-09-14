import httpx
import pytest
from app.providers.fx import CircuitBreakerOpen, FXClient
from freezegun import freeze_time

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_circuit_breaker_transitions_success():
    calls = 0

    async def failing_handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500)

    client = FXClient(
        base_url="https://fx.local",
        timeout=0.01,
        retries=1,
        breaker_threshold=1,
        reset_timeout=60,
        transport=httpx.MockTransport(failing_handler),
    )

    with freeze_time("2024-01-01") as frozen:
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_rate("USD", "EUR")
        assert calls == 1

        with pytest.raises(CircuitBreakerOpen):
            await client.get_rate("USD", "EUR")
        assert calls == 1

        frozen.tick(61)

        async def success_handler(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            return httpx.Response(200, json={"rates": {"EUR": 0.9}})

        client.transport = httpx.MockTransport(success_handler)
        rate = await client.get_rate("USD", "EUR")
        assert rate == pytest.approx(0.9)
        assert calls == 2


@pytest.mark.asyncio
async def test_circuit_breaker_reopens_after_half_open_failure():
    calls = 0

    async def failing_handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500)

    client = FXClient(
        base_url="https://fx.local",
        timeout=0.01,
        retries=1,
        breaker_threshold=1,
        reset_timeout=60,
        transport=httpx.MockTransport(failing_handler),
    )

    with freeze_time("2024-01-01") as frozen:
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_rate("USD", "EUR")
        assert calls == 1

        frozen.tick(61)

        async def failing_again(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            return httpx.Response(500)

        client.transport = httpx.MockTransport(failing_again)
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_rate("USD", "EUR")
        assert calls == 2

        with pytest.raises(CircuitBreakerOpen):
            await client.get_rate("USD", "EUR")
        assert calls == 2
