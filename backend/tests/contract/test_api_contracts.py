import pytest
from fastapi import HTTPException

from app.main import (
    Candle,
    ErrorResponse,
    GasPrices,
    MempoolData,
    app,
    fetch_candles,
    get_btc_mempool_data,
    get_eth_gas_data,
    rate_limiter,
)


@pytest.fixture(autouse=True)
def provider_overrides(coingecko_candles, etherscan_gas, mempool_space):
    app.dependency_overrides[fetch_candles] = lambda asset_id: [
        Candle(**c) for c in coingecko_candles
    ]
    app.dependency_overrides[get_eth_gas_data] = lambda: GasPrices(**etherscan_gas)
    app.dependency_overrides[get_btc_mempool_data] = lambda: MempoolData(
        **mempool_space
    )
    yield
    app.dependency_overrides.clear()


@pytest.mark.contract
@pytest.mark.parametrize(
    "method,path,kwargs",
    [
        ("get", "/health", {}),
        ("get", "/capabilities", {}),
        ("get", "/assets/btc/candles", {}),
        (
            "post",
            "/portfolio/holdings/import",
            {"files": {"file": ("data.csv", b"date,asset\n", "text/csv")}},
        ),
        ("get", "/onchain/eth/gas", {}),
        ("get", "/onchain/btc/mempool", {}),
        ("get", "/metrics", {}),
    ],
)
def test_success_contract(client, method, path, kwargs):
    resp = getattr(client, method)(path, **kwargs)
    assert 200 <= resp.status_code < 300


@pytest.mark.contract
@pytest.mark.parametrize(
    "method,path,kwargs",
    [
        ("get", "/health", {}),
        ("get", "/capabilities", {}),
        ("get", "/assets/btc/candles", {}),
        (
            "post",
            "/portfolio/holdings/import",
            {"files": {"file": ("data.csv", b"date,asset\n", "text/csv")}},
        ),
        ("get", "/onchain/eth/gas", {}),
        ("get", "/onchain/btc/mempool", {}),
        ("get", "/metrics", {}),
    ],
)
def test_rate_limited(client, method, path, kwargs):
    def limiter():
        raise HTTPException(
            status_code=429,
            headers={"Retry-After": "1"},
            detail=ErrorResponse(
                code="provider_throttled", message="slow down", trace_id="test"
            ).model_dump(),
        )

    app.dependency_overrides[rate_limiter] = limiter
    if "files" in kwargs:
        kwargs = {
            **kwargs,
            "files": {"file": ("data.csv", b"date,asset\n", "text/csv")},
        }
    resp = getattr(client, method)(path, **kwargs)
    assert resp.status_code == 429
    assert resp.headers["Retry-After"] == "1"
    data = resp.json()["detail"]
    assert data["code"] == "provider_throttled"
    app.dependency_overrides.pop(rate_limiter, None)
