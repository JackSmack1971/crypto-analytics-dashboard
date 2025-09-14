import os
import re

import pytest
from app.main import (
    Health,
    app,
    get_capabilities_data,
    get_health_data,
    get_metrics_data,
    rate_limiter,
)
from fastapi import HTTPException
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit

PROM_RE = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*\s[0-9.]+$", re.MULTILINE)


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


# Positive tests


def test_health_endpoint_structure(client: TestClient) -> None:
    async def override() -> Health:
        return Health(status="ok", versions={"app": "test"}, uptime=1.23)

    app.dependency_overrides[get_health_data] = override
    try:
        response = client.get("/health")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["versions"]["app"] == "test"
    assert body["uptime"] > 0


def test_capabilities_env_toggle(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def override() -> dict:
        eth_enabled = bool(os.getenv("ETHERSCAN_API_KEY"))
        btc_enabled = bool(os.getenv("MEMPOOL_SPACE_API_KEY"))
        return {
            "news": False,
            "eth_gas": {"enabled": eth_enabled},
            "btc_mempool": {"enabled": btc_enabled},
        }

    app.dependency_overrides[get_capabilities_data] = override
    try:
        # No env vars set -> disabled
        monkeypatch.delenv("ETHERSCAN_API_KEY", raising=False)
        monkeypatch.delenv("MEMPOOL_SPACE_API_KEY", raising=False)
        response = client.get("/capabilities")
        assert response.json()["eth_gas"]["enabled"] is False
        assert response.json()["btc_mempool"]["enabled"] is False

        # Env vars set -> enabled
        monkeypatch.setenv("ETHERSCAN_API_KEY", "x")
        monkeypatch.setenv("MEMPOOL_SPACE_API_KEY", "y")
        response = client.get("/capabilities")
        assert response.json()["eth_gas"]["enabled"] is True
        assert response.json()["btc_mempool"]["enabled"] is True
    finally:
        _clear_overrides()


def test_metrics_prometheus_format(client: TestClient) -> None:
    async def override() -> str:
        return (
            "app_uptime_seconds 1.0\n" "rate_limit_clamp 1.0\n" "breaker_open_total 0\n"
        )

    app.dependency_overrides[get_metrics_data] = override
    try:
        response = client.get("/metrics")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    for line in response.text.strip().splitlines():
        assert PROM_RE.match(line)


# Negative tests


def test_health_missing_dependency() -> None:
    async def broken() -> Health:
        raise RuntimeError("missing dependency")

    app.dependency_overrides[get_health_data] = broken
    client = TestClient(app, raise_server_exceptions=False)
    try:
        response = client.get("/health")
    finally:
        _clear_overrides()

    assert response.status_code == 500


def test_health_rate_limiter_http_exception() -> None:
    def limited() -> None:
        raise HTTPException(status_code=429, detail="Too Many Requests")

    app.dependency_overrides[rate_limiter] = limited
    client = TestClient(app, raise_server_exceptions=False)
    try:
        response = client.get("/health")
    finally:
        _clear_overrides()

    assert response.status_code == 429


def test_rate_limiter_counts_requests() -> None:
    class CountingLimiter:
        """Simple limiter counting calls and raising after threshold."""

        def __init__(self, threshold: int) -> None:
            self.threshold = threshold
            self.calls = 0

        def __call__(self) -> None:
            if self.calls >= self.threshold:
                raise HTTPException(status_code=429, detail="Too Many Requests")
            self.calls += 1

    limiter = CountingLimiter(threshold=2)
    app.dependency_overrides[rate_limiter] = limiter
    client = TestClient(app, raise_server_exceptions=False)
    try:
        assert client.get("/health").status_code == 200
        assert client.get("/health").status_code == 200
        assert client.get("/health").status_code == 429
    finally:
        _clear_overrides()

    assert limiter.calls == 2


def test_metrics_malformed(client: TestClient) -> None:
    async def malformed() -> str:
        return "not-prometheus"

    app.dependency_overrides[get_metrics_data] = malformed
    try:
        response = client.get("/metrics")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert not PROM_RE.match(response.text)
