"""Validate asset registry sample against schema and checksum rules."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft7Validator
from packaging.version import Version

SCHEMA_PATH = Path("DATA_CONTRACTS/schemas/asset.registry.schema.json")
SAMPLE_JSON = Path("DATA_CONTRACTS/fixtures/asset.registry.sample.json")


def test_asset_registry_sample_validates_and_checks_checksum() -> None:
    schema = json.loads(SCHEMA_PATH.read_text())
    data = json.loads(SAMPLE_JSON.read_text())

    Draft7Validator(schema).validate(data)
    Version(data["version"])

    payload = {key: data[key] for key in ["chains", "assets"]}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    checksum = hashlib.sha256(canonical).hexdigest()
    assert data["checksum"] == checksum
