### /docs/SLOs.md

# SLOs — Crypto Analytics Dashboard (MVP)

## User Journeys

* **UJ1:** Load Watchlist / Asset Detail (candles + MA/RSI/MACD).
* **UJ2:** Load Portfolio (NAV/TWR/DD).
* **UJ3:** Import CSV v1.1 and see updated analytics.
* **UJ4:** Operator inspects/acts during provider limits/outages (Console + `/metrics`).

## SLIs

* **Latency (p95/p99)** per route from `api.request` traces (watchlist, asset candles, portfolio). *(RED: Duration)*
* **Request success rate (24h)** exclude 4xx client errors; include 429s. *(RED: Errors)*
* **Cache hit rate** for provider calls (Redis). *\[Unverified RED/USE mapping]*
* **Breaker MTTR** measured from open?closed duration. *(Ops MTTR)*
* **FX drift events** count and queue age. *(Quality signal)*

## Targets & Error Budgets

* **Latency targets (p95/p99):** API **250/600 ms**; candles **900/1.8 s**; portfolio **1.2/2.5 s**. *(Breach if >5% of requests violate target in rolling 1h) \[Unverified threshold]*
* **Availability:** **?99.5%** successful requests per 24h ? **error budget 0.5%**.
* **Cache hit:** **?70%** daily.
* **Breaker MTTR:** **?5 min** median.

## Alerting

* **Burn-rate (availability):**

  * **Fast burn:** >2× budget over 1h. *\[Unverified]*
  * **Slow burn:** >1× budget over 6–12h. *\[Unverified]*
* **Latency:** Page when any UJ **p99** exceeds target for **15 min**. *\[Unverified]*
* **FX drift:** Warn if `drift_bps > 25` persists **>30 min** or queue length **>N**. *\[Unverified]*
* **Disk guard:** Warn when **2 GB** low-disk threshold crossed; system reduces ingest cadence automatically.

> Items marked **\[Unverified]** could not be confirmed from provided inputs and should be finalized during ops bring-up.

---

### /docs/\_meta/SLOs.meta.json

{
"version": "1.0",
"doc": "SLOs.md",
"status": "Draft",
"ci\_hooks": \["SLO config lint", "Budget burn pre-deploy check"],
"quality\_checklist": \["RED/USE metrics mapped", "Burn alerts defined"],
"open\_questions": \[],
"assumptions": \[],
"sources": \["PROJECT\_BLUEPRINT.md"],
"techniques": \["Role Prompting","Decomposition","Structured Output","Eliciting Abstention","Self-Correction"]
}
