import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "env, expected_eth, expected_btc",
    [
        ({"ETHERSCAN_API_KEY": "x", "MEMPOOL_SPACE_API_KEY": "y"}, True, True),
        ({"ETHERSCAN_API_KEY": "x"}, True, False),
        ({"MEMPOOL_SPACE_API_KEY": "y"}, False, True),
        ({}, False, False),
    ],
)
def test_capabilities_flags_reflect_env(
    client: TestClient, env: dict[str, str], expected_eth: bool, expected_btc: bool
) -> None:
    """Ensure capability flags mirror presence of provider API keys."""
    with patch.dict(os.environ, env, clear=True):
        response = client.get("/capabilities")
        body = response.json()
        assert body["eth_gas"]["enabled"] is expected_eth
        assert body["btc_mempool"]["enabled"] is expected_btc


def test_health_ok_when_redis_ping_succeeds(client: TestClient) -> None:
    """Health endpoint returns ok status when Redis ping succeeds."""

    mock_redis = MagicMock()
    mock_redis.ping.return_value = True
    with patch("app.main.get_redis_client", return_value=mock_redis), patch.dict(
        os.environ, {"REDIS_URL": "redis://127.0.0.1:6379/0"}, clear=True
    ):
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_degraded_when_redis_ping_fails(client: TestClient) -> None:
    """Health endpoint degrades when Redis ping raises an exception."""

    mock_redis = MagicMock()
    mock_redis.ping.side_effect = ConnectionError("boom")
    with patch("app.main.get_redis_client", return_value=mock_redis), patch.dict(
        os.environ, {"REDIS_URL": "redis://127.0.0.1:6379/0"}, clear=True
    ):
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
