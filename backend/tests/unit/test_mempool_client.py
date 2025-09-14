import httpx
import pytest
from app.providers import MempoolSpaceClient

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_parses_mempool(load_provider_fixture):
    fixture = load_provider_fixture("mempool_space.json")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=fixture)

    transport = httpx.MockTransport(handler)
    client = MempoolSpaceClient(base_url="https://btc.local", transport=transport)
    data = await client.get_mempool()

    assert data.source == "mempool.space"
    assert data.txs == fixture["txs"]
