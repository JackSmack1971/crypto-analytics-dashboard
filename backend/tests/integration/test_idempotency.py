import pytest
from app.main import IDEMPOTENCY_CACHE, ImportResult, app, get_process_import
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    """Ensure idempotency cache is empty before each test."""
    IDEMPOTENCY_CACHE.clear()


@pytest.mark.parametrize(
    "method,path,kwargs",
    [
        ("GET", "/health", {}),
        ("GET", "/capabilities", {}),
        ("GET", "/assets/eth/candles", {}),
        ("GET", "/onchain/eth/gas", {}),
        ("GET", "/onchain/btc/mempool", {}),
        ("GET", "/metrics", {}),
        (
            "POST",
            "/portfolio/holdings/import",
            {"files": {"file": ("import.csv", b"x", "text/csv")}},
        ),
    ],
)
def test_endpoints_accept_idempotency_key(
    client: TestClient, method: str, path: str, kwargs: dict
) -> None:
    """All endpoints should accept the Idempotency-Key header."""
    headers = {"Idempotency-Key": "testkey"}
    response = client.request(method, path, headers=headers, **kwargs)
    assert response.status_code == 200


def test_portfolio_import_idempotent(client: TestClient) -> None:
    """Repeated requests with the same key return cached result without reprocessing."""
    calls = {"count": 0}

    async def fake_process(file):
        calls["count"] += 1
        await file.read()
        return ImportResult(imported=1)

    app.dependency_overrides[get_process_import] = lambda: fake_process
    try:
        files = {"file": ("import.csv", b"data", "text/csv")}
        headers = {"Idempotency-Key": "abc123"}

        first = client.post("/portfolio/holdings/import", files=files, headers=headers)
        second = client.post("/portfolio/holdings/import", files=files, headers=headers)

        assert first.status_code == second.status_code == 200
        assert first.json() == second.json() == {"imported": 1}
        assert calls["count"] == 1
    finally:
        app.dependency_overrides.pop(get_process_import, None)


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Idempotency-Key": "bad key"},
    ],
)
def test_portfolio_import_requires_valid_key(
    client: TestClient, headers: dict[str, str]
) -> None:
    """Missing or malformed keys should be rejected with 400."""
    files = {"file": ("import.csv", b"data", "text/csv")}
    response = client.post("/portfolio/holdings/import", files=files, headers=headers)
    assert response.status_code == 400
