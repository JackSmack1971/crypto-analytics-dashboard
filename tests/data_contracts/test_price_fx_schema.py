"""Validate price/FX annotation schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, ValidationError

SCHEMA_PATH = Path("DATA_CONTRACTS/schemas/price_fx.annotation.schema.json")


def test_price_fx_annotation_structure() -> None:
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = Draft7Validator(schema)

    good = {
        "price_source": "manual",
        "resolution": "1d",
        "asof": "2024-01-01T00:00:00Z",
    }
    validator.validate(good)

    bad = {"price_source": "manual"}
    with pytest.raises(ValidationError):
        validator.validate(bad)
