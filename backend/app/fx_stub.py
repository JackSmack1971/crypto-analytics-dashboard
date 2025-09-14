"""Deterministic FX rate stub for testing.

Provides stable exchange rates based on currency pairs to avoid external
network calls during development and tests.
"""

from __future__ import annotations

import hashlib


def deterministic_rate(base: str, quote: str) -> float:
    """Return a deterministic FX rate for the currency pair.

    Parameters
    ----------
    base: str
        Base currency code (e.g., ``'USD'``).
    quote: str
        Quote currency code (e.g., ``'EUR'``).

    Returns
    -------
    float
        Pseudo exchange rate in the range ``[0.5, 1.5)`` derived from a
        SHA-256 hash of the pair. The rate is deterministic for the same
        inputs to ensure reproducible calculations in tests.
    """

    digest = hashlib.sha256(f"{base}:{quote}".encode()).digest()
    value = int.from_bytes(digest[:8], "big")
    return round(0.5 + (value % 1000) / 1000, 6)
