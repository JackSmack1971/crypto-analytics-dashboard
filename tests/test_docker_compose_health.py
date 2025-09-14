"""Tests for docker compose service health parsing."""

from __future__ import annotations

from typing import Iterable

import pytest

from tests.utils import read_fixture

REQUIRED_SERVICES = {"frontend", "api", "redis"}


def _load_ps_fixture(name: str) -> list[dict[str, str]]:
    """Load simulated ``docker compose ps --format json`` output."""
    data = read_fixture(f"docker/{name}")
    assert isinstance(data, list)
    return data


def _assert_services_healthy(data: Iterable[dict[str, str]]) -> None:
    """Assert required services exist and report ``healthy`` status."""
    services = {entry["Service"]: entry.get("Health") for entry in data}
    missing = REQUIRED_SERVICES - services.keys()
    unhealthy = {
        svc
        for svc, health in services.items()
        if svc in REQUIRED_SERVICES and health != "healthy"
    }
    if missing or unhealthy:
        raise AssertionError(f"missing={sorted(missing)} unhealthy={sorted(unhealthy)}")


def test_required_services_healthy() -> None:
    data = _load_ps_fixture("ps_all_healthy.json")
    _assert_services_healthy(data)


@pytest.mark.parametrize("fixture", ["ps_missing_service.json", "ps_unhealthy.json"])
def test_missing_or_unhealthy_services_fail(fixture: str) -> None:
    data = _load_ps_fixture(fixture)
    with pytest.raises(AssertionError):
        _assert_services_healthy(data)
