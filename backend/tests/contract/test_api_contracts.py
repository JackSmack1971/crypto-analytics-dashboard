import json
from pathlib import Path

import jsonschema
import pytest
from app.main import (Candle, ErrorResponse, GasPrices, Health, ImportResult,
                      MempoolData, app, fetch_candles, get_btc_mempool_data,
                      get_eth_gas_data, rate_limiter)
from fastapi import HTTPException

OPENAPI = json.loads(Path("backend/openapi.json").read_text())


def resolve_schema(schema: dict) -> dict:
    """Resolve JSON schema $ref pointers using loaded OpenAPI spec."""

    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        return resolve_schema(OPENAPI["components"]["schemas"][ref_name])
    if "items" in schema:
        schema = {**schema, "items": resolve_schema(schema["items"])}
    if "properties" in schema:
        schema = {
            **schema,
            "properties": {
                k: resolve_schema(v) for k, v in schema["properties"].items()
            },
        }
    return schema


def clean_schema(schema: dict) -> dict:
    """Remove non-structural fields for comparison."""

    cleaned = {}
    for key, value in schema.items():
        if key in {"title", "description", "default"}:
            continue
        if isinstance(value, dict):
            cleaned[key] = clean_schema(value)
        elif isinstance(value, list):
            cleaned[key] = [
                clean_schema(v) if isinstance(v, dict) else v for v in value
            ]
        else:
            cleaned[key] = value
    return cleaned


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
    "model",
    [ErrorResponse, Health, Candle, ImportResult, GasPrices, MempoolData],
)
def test_component_schemas(model):
    spec_schema = clean_schema(OPENAPI["components"]["schemas"][model.__name__])
    assert spec_schema == clean_schema(model.model_json_schema())


@pytest.mark.contract
@pytest.mark.parametrize(
    "method,path,spec_path,model,is_array,content_type,kwargs",
    [
        ("get", "/health", "/health", Health, False, "application/json", {}),
        ("get", "/capabilities", "/capabilities", None, False, "application/json", {}),
        (
            "get",
            "/assets/btc/candles",
            "/assets/{asset_id}/candles",
            Candle,
            True,
            "application/json",
            {},
        ),
        (
            "post",
            "/portfolio/holdings/import",
            "/portfolio/holdings/import",
            ImportResult,
            False,
            "application/json",
            {
                "files": {"file": ("data.csv", b"date,asset\n", "text/csv")},
                "headers": {"Idempotency-Key": "contract"},
            },
        ),
        (
            "get",
            "/onchain/eth/gas",
            "/onchain/eth/gas",
            GasPrices,
            False,
            "application/json",
            {},
        ),
        (
            "get",
            "/onchain/btc/mempool",
            "/onchain/btc/mempool",
            MempoolData,
            False,
            "application/json",
            {},
        ),
        (
            "get",
            "/metrics",
            "/metrics",
            None,
            False,
            "text/plain",
            {},
        ),
    ],
)
def test_success_contract(
    client,
    method,
    path,
    spec_path,
    model,
    is_array,
    content_type,
    kwargs,
):
    resp = getattr(client, method)(path, **kwargs)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith(content_type)
    spec_resp = OPENAPI["paths"][spec_path][method]["responses"]["200"]
    assert content_type in spec_resp["content"]
    spec_schema = clean_schema(
        resolve_schema(spec_resp["content"][content_type]["schema"])
    )
    if model:
        expected_schema = (
            {"type": "array", "items": clean_schema(model.model_json_schema())}
            if is_array
            else clean_schema(model.model_json_schema())
        )
        assert spec_schema == expected_schema
        data = resp.json()
        jsonschema.validate(data, spec_schema)
    else:
        data = resp.json() if content_type == "application/json" else resp.text
        jsonschema.validate(data, spec_schema)


@pytest.mark.contract
@pytest.mark.parametrize(
    "method,path,spec_path,kwargs",
    [
        ("get", "/health", "/health", {}),
        ("get", "/capabilities", "/capabilities", {}),
        ("get", "/assets/btc/candles", "/assets/{asset_id}/candles", {}),
        (
            "post",
            "/portfolio/holdings/import",
            "/portfolio/holdings/import",
            {"files": {"file": ("data.csv", b"date,asset\n", "text/csv")}},
        ),
        ("get", "/onchain/eth/gas", "/onchain/eth/gas", {}),
        ("get", "/onchain/btc/mempool", "/onchain/btc/mempool", {}),
        ("get", "/metrics", "/metrics", {}),
    ],
)
def test_rate_limited(client, method, path, spec_path, kwargs):
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
    spec_resp = OPENAPI["paths"][spec_path][method]["responses"]["429"]
    schema = clean_schema(
        resolve_schema(next(iter(spec_resp["content"].values()))["schema"])
    )
    assert schema == clean_schema(ErrorResponse.model_json_schema())
    data = (
        resp.json()["detail"]
        if resp.headers["content-type"].startswith("application/json")
        else json.loads(resp.text)["detail"]
    )
    jsonschema.validate(data, schema)
    assert data["code"] == "provider_throttled"
    app.dependency_overrides.pop(rate_limiter, None)
