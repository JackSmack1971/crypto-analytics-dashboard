import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

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
