import os
import time
from typing import List

from fastapi import Depends, FastAPI, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

app = FastAPI(title="Crypto Analytics BFF", version="0.1.0")

START = time.time()


class ErrorResponse(BaseModel):
    """Structured error for 4xx/5xx responses."""

    code: str
    message: str
    trace_id: str | None = None


class Health(BaseModel):
    status: str
    versions: dict
    uptime: float


class Candle(BaseModel):
    t: int
    o: float
    h: float
    l: float
    c: float
    v: float
    resolution: str
    asof: float
    source: str


class ImportResult(BaseModel):
    imported: int


class GasPrices(BaseModel):
    safe: float
    propose: float
    fast: float


class MempoolData(BaseModel):
    txs: int
    size: int


ERROR_RESPONSES = {
    429: {"model": ErrorResponse, "description": "Too Many Requests"},
    500: {"model": ErrorResponse, "description": "Internal Server Error"},
}


def rate_limiter() -> None:  # pragma: no cover
    """Rate limiter dependency to allow override in tests."""


async def get_health_data() -> Health:  # pragma: no cover
    return Health(
        status="ok",
        versions={"app": "0.1.0", "python": os.sys.version.split()[0]},
        uptime=round(time.time() - START, 3),
    )


async def get_capabilities_data() -> dict:  # pragma: no cover
    eth_enabled = bool(os.getenv("ETHERSCAN_API_KEY"))
    btc_enabled = bool(os.getenv("MEMPOOL_SPACE_API_KEY"))
    return {
        "news": False,
        "eth_gas": {"enabled": eth_enabled},
        "btc_mempool": {"enabled": btc_enabled},
    }


async def fetch_candles(asset_id: str) -> List[Candle]:  # pragma: no cover
    return [
        Candle(
            t=0,
            o=0,
            h=0,
            l=0,
            c=0,
            v=0,
            resolution="1d",
            asof=time.time(),
            source="mock",
        )
    ]


async def process_import(file: UploadFile) -> ImportResult:  # pragma: no cover
    await file.read()
    return ImportResult(imported=1)


async def get_eth_gas_data() -> GasPrices:  # pragma: no cover
    return GasPrices(safe=1.0, propose=2.0, fast=3.0)


async def get_btc_mempool_data() -> MempoolData:  # pragma: no cover
    return MempoolData(txs=0, size=0)


async def get_metrics_data() -> str:  # pragma: no cover
    return (
        "content-type=text/plain; version=0.0.4\n"
        "app_uptime_seconds %f\n"
        "rate_limit_clamp 1.0\n"
        "breaker_open_total 0\n" % (time.time() - START)
    )


@app.get("/health", response_model=Health, responses=ERROR_RESPONSES)
async def health(
    data: Health = Depends(get_health_data),
    _: None = Depends(rate_limiter),
) -> Health:
    return data


@app.get("/capabilities", responses=ERROR_RESPONSES)
async def capabilities(
    data: dict = Depends(get_capabilities_data),
    _: None = Depends(rate_limiter),
):  # pragma: no cover
    return data


@app.get(
    "/assets/{asset_id}/candles",
    response_model=List[Candle],
    responses=ERROR_RESPONSES,
)
async def asset_candles(
    asset_id: str,
    candles: List[Candle] = Depends(fetch_candles),
    _: None = Depends(rate_limiter),
):
    return candles


@app.post(
    "/portfolio/holdings/import",
    response_model=ImportResult,
    responses=ERROR_RESPONSES,
)
async def portfolio_import(
    file: UploadFile,
    result: ImportResult = Depends(process_import),
    _: None = Depends(rate_limiter),
):
    return result


@app.get("/onchain/eth/gas", response_model=GasPrices, responses=ERROR_RESPONSES)
async def onchain_eth_gas(
    data: GasPrices = Depends(get_eth_gas_data),
    _: None = Depends(rate_limiter),
):
    return data


@app.get(
    "/onchain/btc/mempool",
    response_model=MempoolData,
    responses=ERROR_RESPONSES,
)
async def onchain_btc_mempool(
    data: MempoolData = Depends(get_btc_mempool_data),
    _: None = Depends(rate_limiter),
):
    return data


@app.get("/metrics", response_class=PlainTextResponse, responses=ERROR_RESPONSES)
async def metrics(
    data: str = Depends(get_metrics_data),
    _: None = Depends(rate_limiter),
):  # pragma: no cover
    return data
