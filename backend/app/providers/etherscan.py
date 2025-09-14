"""Etherscan provider client for Ethereum gas prices."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx
from app.main import GasPrices


@dataclass
class EtherscanClient:
    """Minimal client to fetch gas price estimates."""

    base_url: str = "https://api.etherscan.io/api"
    transport: Optional[httpx.BaseTransport] = None

    async def get_gas_prices(self) -> GasPrices:
        """Return gas price information from Etherscan."""

        url = f"{self.base_url}/gas"
        async with httpx.AsyncClient(transport=self.transport) as client:
            response = await client.get(url, timeout=5.0)
        response.raise_for_status()
        data = response.json()
        data.setdefault("source", "etherscan")
        return GasPrices(**data)
