"""Default provider rate limit budgets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class ProviderBudget:
    """Ceiling definitions for a provider."""

    per_sec: Optional[float] = None
    per_min: Optional[float] = None
    per_day: Optional[float] = None


DEFAULT_BUDGETS: Dict[str, ProviderBudget] = {
    "coingecko": ProviderBudget(per_sec=5, per_min=30),
    "etherscan": ProviderBudget(per_sec=5, per_day=100_000),
    "mempool_space": ProviderBudget(per_sec=1),
    "fx": ProviderBudget(per_min=10),
}
"""Default provider budgets used when none supplied."""
