import httpx
import pytest
from app.providers import CoinGeckoClient

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_parses_candles(load_provider_fixture):
    fixture = load_provider_fixture("coingecko_candles.json")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=fixture)

    transport = httpx.MockTransport(handler)
    client = CoinGeckoClient(base_url="https://cg.local", transport=transport)
    candles = await client.get_candles("btc")

    assert len(candles) == len(fixture)
    assert all(c.source == "coingecko" for c in candles)
