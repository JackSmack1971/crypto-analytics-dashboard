import logging
import os

import pytest

from app.config_env import load
from app.logging_utils import configure_logging

pytestmark = pytest.mark.unit


def test_logging_redacts_secrets(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Secret env vars are not exposed in logs."""
    monkeypatch.setenv("API_KEY", "supersecret")
    monkeypatch.setenv("SERVICE_TOKEN", "tok123")
    logger = configure_logging(logging.getLogger("test_logger"))

    with caplog.at_level(logging.INFO):
        logger.info(
            "API_KEY=%s SERVICE_TOKEN=%s",
            os.getenv("API_KEY"),
            os.getenv("SERVICE_TOKEN"),
        )

    output = caplog.text
    assert "supersecret" not in output
    assert "tok123" not in output
    assert "API_KEY=[REDACTED]" in output
    assert "SERVICE_TOKEN=[REDACTED]" in output


def test_load_rejects_non_local_host(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-local API_HOST values are rejected."""
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    monkeypatch.setenv("API_HOST", "0.0.0.0")
    with pytest.raises(RuntimeError):
        load()
