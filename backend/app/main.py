import os
import time

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Crypto Analytics BFF", version="0.1.0")

START = time.time()


class Health(BaseModel):
    status: str
    versions: dict
    uptime: float


@app.get("/health", response_model=Health)
def health():
    return Health(
        status="ok",
        versions={"app": "0.1.0", "python": os.sys.version.split()[0]},
        uptime=round(time.time() - START, 3),
    )


@app.get("/capabilities")
def capabilities():  # pragma: no cover
    # [Unverified] exact env var names for gating
    eth_enabled = bool(os.getenv("ETHERSCAN_API_KEY"))
    btc_enabled = bool(os.getenv("MEMPOOL_SPACE_API_KEY"))
    return {
        "news": False,  # optional/unspecified
        "eth_gas": {"enabled": eth_enabled},
        "btc_mempool": {"enabled": btc_enabled},
    }


@app.get("/metrics")
def metrics():  # pragma: no cover
    # Minimal Prometheus-like text. Replace with real counters and exemplars.
    return (
        "content-type=text/plain; version=0.0.4\n"
        "app_uptime_seconds %f\n"
        "rate_limit_clamp 1.0\n"
        "breaker_open_total 0\n" % (time.time() - START)
    )
