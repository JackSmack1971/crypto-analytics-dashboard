"""mempool.space provider client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx
from app.main import MempoolData


@dataclass
class MempoolSpaceClient:
    """Fetch Bitcoin mempool statistics."""

    base_url: str = "https://mempool.space/api"
    transport: Optional[httpx.BaseTransport] = None

    async def get_mempool(self) -> MempoolData:
        """Return mempool statistics from mempool.space."""

        url = f"{self.base_url}/mempool"
        async with httpx.AsyncClient(transport=self.transport) as client:
            response = await client.get(url, timeout=5.0)
        response.raise_for_status()
        data = response.json()
        data.setdefault("source", "mempool.space")
        return MempoolData(**data)
