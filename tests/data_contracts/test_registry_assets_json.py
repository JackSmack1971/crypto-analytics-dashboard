"""Validate registry assets file against schema and UUIDv7 requirements."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from tests.utils import assert_uuid7

SCHEMA_PATH = Path("DATA_CONTRACTS/schemas/asset.registry.schema.json")
REGISTRY_PATH = Path("registry/assets.json")


def test_registry_assets_json_validates_and_uuidv7() -> None:
    schema = json.loads(SCHEMA_PATH.read_text())
    data = json.loads(REGISTRY_PATH.read_text())
    Draft7Validator(schema).validate(data)
    for asset in data["assets"]:
        assert_uuid7(asset["asset_id"])


def test_invalid_uuid_rejected() -> None:
    with pytest.raises(AssertionError):
        assert_uuid7("00000000-0000-7000-8000-00000000000")
