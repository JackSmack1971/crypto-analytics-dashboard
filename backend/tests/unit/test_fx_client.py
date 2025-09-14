import httpx
import pytest

from app.providers.fx import CircuitBreakerOpen, FXClient

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_retries_and_timeout():
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("timeout", request=request)

    transport = httpx.MockTransport(handler)
    client = FXClient(
        base_url="https://fx.local",
        timeout=0.01,
        retries=3,
        breaker_threshold=5,
        transport=transport,
    )

    with pytest.raises(httpx.ReadTimeout):
        await client.get_rate("USD", "EUR")

    assert calls == 3  # retries honoured
    assert client.timeout == 0.01


@pytest.mark.asyncio
async def test_circuit_breaker_opens():
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500)

    transport = httpx.MockTransport(handler)
    client = FXClient(
        base_url="https://fx.local",
        timeout=0.01,
        retries=1,
        breaker_threshold=1,
        transport=transport,
    )

    # First call fails and opens breaker
    with pytest.raises(httpx.HTTPStatusError):
        await client.get_rate("USD", "EUR")
    assert calls == 1

    # Subsequent call is blocked by breaker (no additional HTTP call)
    with pytest.raises(CircuitBreakerOpen):
        await client.get_rate("USD", "EUR")
    assert calls == 1


@pytest.mark.asyncio
async def test_success_path():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"rates": {"EUR": 0.9}})

    transport = httpx.MockTransport(handler)
    client = FXClient(
        base_url="https://fx.local",
        transport=transport,
    )

    rate = await client.get_rate("USD", "EUR")
    assert rate == pytest.approx(0.9)
