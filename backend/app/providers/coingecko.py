"""CoinGecko provider client with simple JSON parsing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import httpx
from app.main import Candle


@dataclass
class CoinGeckoClient:
    """Minimal CoinGecko HTTP client.

    Parameters
    ----------
    base_url:
        Base URL for the CoinGecko API.
    transport:
        Optional custom transport for testing/mocking.
    """

    base_url: str = "https://api.coingecko.com/api/v3"
    transport: Optional[httpx.BaseTransport] = None

    async def get_candles(self, asset_id: str) -> List[Candle]:
        """Fetch OHLCV candles for the given asset.

        Notes
        -----
        This implementation assumes the upstream response JSON already matches the
        ``Candle`` schema except for the missing ``source`` field which is
        injected for provenance tracking.
        """

        url = f"{self.base_url}/candles/{asset_id}"
        async with httpx.AsyncClient(transport=self.transport) as client:
            response = await client.get(url, timeout=5.0)
        response.raise_for_status()
        data = response.json()
        candles: List[Candle] = []
        for item in data:
            item.setdefault("source", "coingecko")  # ensure provider provenance
            candles.append(Candle(**item))
        return candles
