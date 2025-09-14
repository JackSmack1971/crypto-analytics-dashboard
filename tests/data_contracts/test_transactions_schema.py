"""Validate transactions CSV against schema."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from jsonschema import Draft7Validator

SCHEMA_PATH = Path("DATA_CONTRACTS/schemas/transactions.v1.1.schema.json")
SAMPLE_CSV = Path("DATA_CONTRACTS/fixtures/transactions.v1.1.sample.csv")


def test_transactions_sample_csv_validates_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = Draft7Validator(schema)

    with SAMPLE_CSV.open(newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == [
            "id",
            "timestamp",
            "action",
            "asset_id",
            "quantity",
            "unit_price_usd",
            "account",
        ]
        for row in reader:
            if row["quantity"]:
                row["quantity"] = float(row["quantity"])
            if row["unit_price_usd"]:
                row["unit_price_usd"] = float(row["unit_price_usd"])
            validator.validate(row)
