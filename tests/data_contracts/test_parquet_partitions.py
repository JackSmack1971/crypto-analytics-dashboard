"""Ensure Parquet datasets use dt/asset_id partition layout."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def test_parquet_partition_layout(tmp_path: Path) -> None:
    table = pa.table(
        {
            "t": [0],
            "o": [1.0],
            "h": [1.0],
            "l": [1.0],
            "c": [1.0],
            "v": [1.0],
            "dt": ["2024-01-01"],
            "asset_id": ["btc"],
        }
    )
    root = tmp_path / "dataset"
    pq.write_to_dataset(table, root_path=root, partition_cols=["dt", "asset_id"])

    files = list(root.rglob("*.parquet"))
    assert files, "No Parquet files written"
    for file in files:
        parts = file.relative_to(root).parts
        assert parts[0].startswith("dt=")
        assert parts[1].startswith("asset_id=")
