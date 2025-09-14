import tempfile
from pathlib import Path

import pytest
from app.main import MAX_UPLOAD_SIZE
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def _tmp_contents() -> set[Path]:
    """Return current set of temporary files."""

    return {p for p in Path(tempfile.gettempdir()).iterdir()}


def test_import_rejects_oversized_file(client: TestClient) -> None:
    """Uploading files beyond size limit returns 413 and cleans temp files."""

    before = _tmp_contents()
    files = {"file": ("big.csv", b"x" * (MAX_UPLOAD_SIZE + 1), "text/csv")}
    headers = {"Idempotency-Key": "big"}
    response = client.post("/portfolio/holdings/import", files=files, headers=headers)
    after = _tmp_contents()
    assert response.status_code == 413
    assert before == after


def test_import_rejects_unsupported_mime(client: TestClient) -> None:
    """Non-CSV uploads return 415 and remove temporary files."""

    before = _tmp_contents()
    files = {"file": ("data.txt", b"data", "text/plain")}
    headers = {"Idempotency-Key": "mime"}
    response = client.post("/portfolio/holdings/import", files=files, headers=headers)
    after = _tmp_contents()
    assert response.status_code == 415
    assert before == after
