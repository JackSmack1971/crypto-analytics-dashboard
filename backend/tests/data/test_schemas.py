"""CSV schema validation tests for sample data contracts."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

EXPECTED_COLUMNS = [
    "id",
    "timestamp",
    "action",
    "asset_id",
    "quantity",
    "unit_price_usd",
    "account",
]

NUMERIC_COLUMNS = ["quantity", "unit_price_usd"]


def validate_transactions_csv(source: Path) -> int:
    """Validate Transactions CSV v1.1 schema.

    Ensures required columns exist, numeric fields parse as floats,
    and returns the number of data rows. Raises ``ValueError`` on
    schema or type violations.
    """

    with source.open(newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError("CSV columns mismatch")

        row_count = 0
        for row in reader:
            row_count += 1
            for field in NUMERIC_COLUMNS:
                try:
                    float(row[field])
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"Invalid numeric value for '{field}'") from exc
        return row_count


@pytest.mark.unit
def test_transactions_sample_schema_valid() -> None:
    """Sample transactions CSV adheres to required schema."""
    root = Path(__file__).resolve().parents[3]
    csv_path = root / "DATA_CONTRACTS" / "fixtures" / "transactions.v1.1.sample.csv"
    row_count = validate_transactions_csv(csv_path)
    assert row_count == 0


@pytest.mark.unit
def test_transactions_invalid_schema(tmp_path: Path) -> None:
    """Missing columns raise ``ValueError`` during validation."""
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text(
        "id,timestamp,action,asset_id,unit_price_usd,account\n"
        "1,2024-01-01T00:00:00Z,buy,BTC,50000,acc1\n"
    )
    with pytest.raises(ValueError):
        validate_transactions_csv(bad_csv)
