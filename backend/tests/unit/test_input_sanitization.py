from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


def test_asset_candles_rejects_sql_payload(client: TestClient) -> None:
    payload = quote("1 OR 1=1", safe="")
    response = client.get(f"/assets/{payload}/candles")
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "client_invalid_contract"


def test_import_rejects_xss_payload(client: TestClient) -> None:
    payload = "<script>alert('x')</script>"
    files = {"file": ("test.csv", "col\n1\n", "text/csv")}
    response = client.post(
        "/portfolio/holdings/import",
        headers={"Idempotency-Key": payload},
        files=files,
    )
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "client_invalid_contract"
