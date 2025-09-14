import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


def test_cors_allows_local_origin(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "http://127.0.0.1:3000"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"


def test_cors_blocks_external_origin(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "http://evil.com"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
