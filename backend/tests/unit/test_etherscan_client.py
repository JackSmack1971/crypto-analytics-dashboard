import httpx
import pytest
from app.providers import EtherscanClient

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_parses_gas_prices(load_provider_fixture):
    fixture = load_provider_fixture("etherscan_gas.json")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=fixture)

    transport = httpx.MockTransport(handler)
    client = EtherscanClient(base_url="https://eth.local", transport=transport)
    gas = await client.get_gas_prices()

    assert gas.source == "etherscan"
    assert gas.fast == pytest.approx(fixture["fast"])
