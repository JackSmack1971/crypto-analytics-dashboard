import json
import sqlite3
import sys
from pathlib import Path

import fakeredis
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
from app.main import app, rate_limiter  # noqa: E402

FIXTURES_PATH = Path(__file__).parent / "fixtures"
PROVIDER_FIXTURES_PATH = FIXTURES_PATH / "providers"


@pytest.fixture
def client() -> TestClient:  # pragma: no cover
    """FastAPI test client."""
    with TestClient(app) as test_client:
        app.dependency_overrides[rate_limiter] = lambda request: None
        try:
            yield test_client
        finally:
            app.dependency_overrides.clear()


@pytest.fixture
def sqlite_conn():  # pragma: no cover
    """In-memory SQLite connection for isolated tests."""
    conn = sqlite3.connect(":memory:")
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def fake_redis():  # pragma: no cover
    """In-memory Redis replacement using fakeredis."""
    redis = fakeredis.FakeRedis()
    try:
        yield redis
    finally:
        redis.close()


@pytest.fixture
def load_fixture():  # pragma: no cover
    """Load JSON fixture from tests/fixtures directory."""

    def _loader(name: str):
        path = FIXTURES_PATH / name
        with path.open() as fh:
            return json.load(fh)

    return _loader


@pytest.fixture
def load_provider_fixture():  # pragma: no cover
    """Load provider mock from tests/fixtures/providers."""

    def _loader(name: str):
        path = PROVIDER_FIXTURES_PATH / name
        with path.open() as fh:
            return json.load(fh)

    return _loader


@pytest.fixture
def coingecko_candles(load_provider_fixture):  # pragma: no cover
    return load_provider_fixture("coingecko_candles.json")


@pytest.fixture
def etherscan_gas(load_provider_fixture):  # pragma: no cover
    return load_provider_fixture("etherscan_gas.json")


@pytest.fixture
def mempool_space(load_provider_fixture):  # pragma: no cover
    return load_provider_fixture("mempool_space.json")


def pytest_configure(config: pytest.Config) -> None:  # pragma: no cover
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "contract: HTTP contract tests")
    config.addinivalue_line("markers", "integration: integration tests")
