"""Test utilities for fixtures and state simulation."""

from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

FIXTURE_ROOT = Path(__file__).resolve().parent.parent / "fixtures"


def read_fixture(relative_path: str, mode: str = "r") -> Any:
    """Read a fixture file relative to the fixture root.

    Args:
        relative_path: Path to file within fixtures directory.
        mode: File mode; use 'rb' for binary.

    Returns:
        Parsed JSON for .json files or raw content for others.
    """
    path = FIXTURE_ROOT / relative_path
    if path.suffix == ".b64":
        with open(path, "rb") as fh:
            encoded = fh.read()
        return base64.b64decode(encoded)
    if "b" in mode:
        with open(path, mode) as fh:
            return fh.read()
    with open(path, mode, encoding="utf-8") as fh:
        if path.suffix == ".json":
            return json.load(fh)
        return fh.read()


def generate_uuid7() -> str:
    """Generate a UUIDv7 identifier.

    Uses Unix time in milliseconds for sortable IDs.
    """
    unix_ms = int(time.time() * 1000)
    ts_hex = f"{unix_ms:015x}"
    time_high = ts_hex[:8]
    time_mid = ts_hex[8:12]
    time_low = ts_hex[12:15]
    rand_hex = os.urandom(10).hex()
    variant = "8"
    return f"{time_high}-{time_mid}-7{time_low}-{variant}{rand_hex[:3]}-{rand_hex[3:]}"


def simulate_redis_state(initial: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Create a simple in-memory Redis-like state."""
    return dict(initial or {})


def simulate_db_state(initial: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a simple in-memory database state."""
    return dict(initial or {})
