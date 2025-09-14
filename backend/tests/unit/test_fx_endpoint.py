import httpx
import pytest
from app.fx_stub import deterministic_rate
from app.main import app

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_fx_endpoint_returns_deterministic_rate_and_conversions() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp_eur = await client.get("/fx/USD/EUR")
        resp_jpy = await client.get("/fx/USD/JPY")

    data_eur = resp_eur.json()
    data_jpy = resp_jpy.json()

    expected_eur = deterministic_rate("USD", "EUR")
    expected_jpy = deterministic_rate("USD", "JPY")

    assert data_eur["rate"] == pytest.approx(expected_eur)
    assert data_jpy["rate"] == pytest.approx(expected_jpy)

    usd_amount = 10.0
    eur_converted = usd_amount * data_eur["rate"]
    jpy_converted = usd_amount * data_jpy["rate"]

    assert eur_converted == pytest.approx(usd_amount * expected_eur)
    assert jpy_converted == pytest.approx(usd_amount * expected_jpy)
    assert eur_converted != pytest.approx(jpy_converted)
