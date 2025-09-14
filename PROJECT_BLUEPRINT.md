# PROJECT\_BLUEPRINT.md

# Crypto Analytics Dashboard — **MVP Blueprint (Pack A Locked)**

## 0) Executive Summary

Local-first, single-user crypto analytics dashboard. Next.js App Router UI ? FastAPI BFF ? Python worker. Transactions CSV (opaque `asset_id`) is the source of truth; worker derives end-of-interval snapshots, resolves prices/FX with **provider-aware bucket-close**, and writes Parquet read via **DuckDB views**. IDs are **UUIDv7**. **Pack A** is locked: nightly backups + verification + weekly restore drills, tracing MVP with sampling & exemplars, autoscaler clamps/cooldowns/hysteresis, compactor watermark 0.65 RAM (alert 0.90), CSV hardening, and a minimal Operator Console.

---

## 1) Goals, KPIs, SLOs, Constraints

**Goals**

* Fast local charts (candles + MA/RSI/MACD), portfolio NAV/TWR/drawdown, ETH gas & BTC mempool panels.
* Deterministic valuation/backfill aligned to provider granularity.
* Resilient under rate limits/outages; observable and operator-controllable.

**KPIs**

* p95: API ? **250 ms**, candles ? **900 ms**, portfolio ? **1.2 s**.
* p99: API ? **600 ms**, candles ? **1.8 s**, portfolio ? **2.5 s**.
* 24h success **?99.5%**; cache hit rate **?70%**; breaker MTTR **?5 min**.

**Constraints**

* Free-tier APIs; bind **127.0.0.1**; offline-friendly SW cache; local OTel collector.

---

## 2) Architecture

```mermaid
flowchart LR
  subgraph UI[Next.js App Router]
    A1[Watchlist]
    A2[Asset Detail (MA/RSI/MACD)]
    A3[Portfolio (NAV/TWR/DD)]
    A4[ETH Gas / BTC Mempool]
    A5[CSV Import (v1.1)]
    A6[Operator Console]
  end
  subgraph API[FastAPI BFF]
    B1[/health]
    B2[/capabilities]
    B3[/assets/{asset_id}/candles]
    B4[/portfolio/holdings + import]
    B5[/onchain/eth/gas]
    B6[/onchain/btc/mempool]
    B7[/assets/{asset_id}/metrics]
    B8[/metrics]
  end
  subgraph Worker[Python]
    W1[Import & Normalize]
    W2[Valuation (bucket-close)]
    W3[Lots FIFO/LIFO]
    W4[Snapshots 5m/1h/1d]
    W5[Parquet Writer + Compactor]
  end
  subgraph Data
    D1[(SQLite)]
    D2[(Redis)]
    D3[(Parquet)]
    D4[(DuckDB Views)]
    D5[[registry/assets.json]]
    D6[[/data/backups/…]]
  end
  UI<-->API
  API<-->D1 & D2
  Worker<-->D1 & D3
  D4<-->D3
  D1<--seed--->D5
  D6-. nightly .->D1 & D3
```

Profiles: `default(frontend,api,redis)`, `worker(worker)`, `ops(otel-collector)`. All services bind **127.0.0.1**.

---

## 3) Identity & Data Contracts

### 3.1 UUIDv7 IDs

* API: hyphenated UUID; DB: 16-byte UUID/BLOB; files may prefix `YYYY-MM-DD/`. **ADR-0001: ACCEPTED.**

### 3.2 Asset Registry (JSON-first, authoritative)

* `registry/assets.json` (semver + checksum) ? seed SQLite on boot; **no runtime mutation**.
* Entities: `chains`, `assets`, `asset_contracts`, `asset_provider_ids`, `asset_aliases`.
* Make: `validate-assets`, `checksum-assets`, `diff-assets`, `seed-assets`.

**Semver & Migration SOP**

* **Patch:** Non-breaking metadata (aliases, provider\_ids).
* **Minor:** New assets/contracts/fields (back-compatible).
* **Major:** Breaking identity shifts (e.g., decimals, chain remap).
* Rows include: `introduced_in`, `deprecated_in`, `deprecation_status`, `superseded_by`.
* **N/N+1 dry-run seed** prints a migration plan (SQL + alias rewrites) and fails on breaking diffs without a major bump.

### 3.3 Transactions CSV v1.1

`id(uuidv7)`, `timestamp(UTC ISO)`, `action{BUY|SELL|TRANSFER_IN|TRANSFER_OUT|FEE|STAKING_REWARD|AIRDROP|INCOME}`, `asset_id`, `quantity`, `unit_price_usd?`, `fee_asset?`, `fee_amount?`, `account`, `wallet?`, `venue?`, `tx_hash?`, `external_id?`, `notes?`.
Fees ? normalized **FEE** row (negative qty of `fee_asset`) included in cost basis.
Idempotency: `UNIQUE(account, tx_hash)` or `UNIQUE(external_id)`; else rely on `id`.
Transfers: move lots; **no P\&L**; acquisition dates preserved.

---

## 4) Valuation & FX Policy (Provider-Aware + Drift Guard)

* **Granularity:** ?1 day **5m** (backward tolerance ?2 m), 1–90 d **1h**, >90 d **1d**; **no forward fill**.
* Persist: `price_source`, `resolution`, `asof`, and if applicable `fx_source`, `fx_rate`.
* **FX:** primary **exchangerate.host**; fallback **Frankfurter (ECB EOD)**.
* **Drift guard:** when fallback used, compute **drift\_bps** vs latest intraday USD; if `>25 bps`, flag `[DELAYED_FX]`, hold NAV; Operator Console offers **“Use EOD Once”** (TTL default 30 min).

---

## 5) Providers & Budgets (Adaptive Limits ? Redis Buckets)

* **Static ceilings (defaults):** CoinGecko `{ per_min: 30, per_sec: 5 }`; Etherscan `{ per_sec: 5, per_day: 100000 }`; mempool.space `{ per_sec: 1 }`; FX `{ per_min: 10 }`.
* **Adaptive policy (clamped):** min **50%**, max **100%**, step **10%**, cooldown **60 s**, hysteresis **2×**; honor `Retry-After`; **freeze on 403**.
* **Outages:** circuit breakers open on sustained 5xx/429; **half-open** probes gate recovery.
* **/metrics:** exposes rate-limit counters, breaker state, cache TTLs, FX drift occurrences; exemplars link to traces.

---

## 6) Storage, Retention, Compaction & Backups

* **Partitions:** `dt=YYYY-MM-DD/asset_id=…` (date-first).
* **Profiles:** `DEFAULT` **128 MB** row groups (\~100k–1M rows); `LOW_RAM` **32 MB** (\~25k–250k rows) via `STORAGE_PROFILE`.
* **Watermarks:** compactor caps in-flight memory at **?0.65 RAM**; alert at **0.90**; spills to smaller groups when near cap.
* **Retention:** OHLC raw 30 d?daily; 1h 1 y; 1d 3 y; snapshots 1 y; on-chain 90 d; telemetry 7 d.
* **Disk guard:** **2 GB** triggers reduced ingest cadence and Operator alert.

**Backups (Pack A) — ADR-0003: ACCEPTED**

* Nightly **02:30 local** to `/data/backups/%Y-%m-%d/`:

  * `sqlite/backup.sqlite3` via `PRAGMA wal_checkpoint; .backup`
  * `parquet/…` packaged as `parquet.tar.gz` + `manifest.json` (file list + checksums)
* **Retention:** 7 days.
* **Verify:** `PRAGMA integrity_check=’ok’`; DuckDB sample scans (random 1–5 files/partition).
* **Restore drill:** weekly to a temp workspace; produce `drill_report.json` artifact; Operator Console shows last drill status.

---

## 7) Reliability, Operability & Operator Console

* **Limiters:** Redis token buckets; exponential backoff + jitter; circuit breakers (open/half-open/closed).
* **Redis outage:** switch to **in-process leaky-bucket** (default-deny) until Redis healthy; log downgrade/upgrade events.
* **Service Worker:** stale-while-revalidate; offline banner with last `asof`.
* **Operator Console**

  * **Status cards:** provider budgets, 429 rate, breaker state, cache TTLs, disk usage/guard, FX drift queue, last backup/drill.
  * **Controls:** open/close breaker (confirm), edit budgets (min/max clamped), trigger **compactor dry-run**, **Use EOD Once** for FX.
  * **Logs:** structured logs with secret redaction; filter WARN/ERROR; logs carry `trace_id`.

---

## 8) Security & Privacy (DPIA-lite & Classification)

* **Networking:** bind **127.0.0.1**; strict CORS (localhost).
* **Classification:** Code (Internal), Config/.env (Secret), CSV inputs (Confidential), Parquet analytics (Confidential), Telemetry (Internal; TTL 7 d).
* **Threat model (STRIDE-lite):**

  * CSV ingestion: spoofing/trojan formulas ? **sanitize on export**, size/row caps, quarantine, schema validation.
  * Provider abuse: DoS/ban ? **limiters + breakers + clamps + cooldown**.
  * Secrets: leakage in logs ? **redaction tests** + Gitleaks CI.
* **Supply chain:** `pip-audit`, `npm audit`, **Syft SBOM**; PR gates.

---

## 9) Tracing MVP (OTel)

* **Span taxonomy:** `api.request`, `provider.http`, `worker.job`, `compactor.run`.
* **Sampling:** **head 10%**; **tail 100%** for errors or spans **>1 s**.
* **Metrics exemplars:** RED metrics attach exemplars with `trace_id`.
* **Logs:** include `trace_id`/`span_id` for correlation.
* **Trace-based SLOs:** p95/p99 derived from `api.request` spans; alerts on burn rate.

---

## 10) API Surface (OpenAPI 3.1 excerpts)

* `GET /health` ? `{ status, versions, uptime }`
* `GET /capabilities` ? `{ news:boolean, eth_gas:{enabled:boolean}, … }`
* `GET /assets/{asset_id}/candles?interval=5m|1h|1d&start&end` ? `{ t,o,h,l,c,v,resolution,asof }[]` (documents **429** + `Retry-After`)
* `POST /portfolio/holdings/import` ? CSV v1.1 normalize; idempotent upsert
* `GET /onchain/eth/gas` ? values or `{ enabled:false }` if key missing
* `GET /onchain/btc/mempool` ? mempool size & fee buckets
* `GET /assets/{asset_id}/metrics` ? NAV share, drawdown, RSI/MACD inputs
* `GET /metrics` ? Prometheus text (RED + rate-limit + breaker counters, with exemplars)

---

## 11) Testing & QA

* **Functional:** importer normalization (incl. FEE rows); FIFO/LIFO lots; valuation bucket boundaries; FX conversions; `/capabilities` with/without keys.
* **Determinism:** valuation per `resolution/asof`; DST boundary tests.
* **Performance:** p95/p99 for API/candles/portfolio; compactor throughput; **LOW\_RAM** compaction on 2-GB VM.
* **Chaos & Soak:** 3-hour soak at **80% ceilings**; synthetic 429/5xx; **MTTR ?5 min**; alert fire/clear verified.
* **FX drift:** fail when `drift_bps > 25`; banner/override flow tested.
* **Backups:** `make backup|backup.verify|restore` CI checks; **weekly restore drill** artifact exists.
* **Secrets & redaction:** integration test scans logs for secret substrings.
* **Operator Console e2e:** breaker toggle, compactor dry-run, FX Use-EOD-Once.
* **Visual regression:** Playwright baselines.

---

## 12) Delivery Plan & Timeline (solo)

1. **Days 1–2:** repo/compose/env; `/health`; Next.js shell; assets.json schema + seed; Operator Console stub.
2. **Days 3–4:** CSV importer + idempotency; valuation (+FX + drift guard); `/metrics`; limiters/breakers (static).
3. **Day 5:** snapshots ? Parquet; DuckDB views; compactor (DEFAULT/LOW\_RAM, watermark 0.65).
4. **Day 6:** UI charts; ETH gas / BTC mempool panels; adaptive budgets (clamped).
5. **Day 7:** Tracing MVP (spans, sampling, exemplars); backups + verify; restore script.
6. **Days 8–9:** Chaos/soak; perf; Operator Console controls; secrets/redaction tests.
7. **Day 10:** README + runbooks + ADR-0003; docs lint.
   **Stabilization buffer:** +2 days.

---

## 13) Acceptance (MVP)

* `docker compose up` ? all healthchecks pass on **127.0.0.1**.
* Import sample CSV ? rows in SQLite; normalized **FEE** rows emitted.
* Valuation returns `{resolution, asof, source}`; FX fallback flagged with `drift_bps`; Operator can **Use EOD Once**.
* Lots engine computes P\&L; transfers **no P\&L**.
* Parquet written; DuckDB **views** query successfully.
* Compactor runs @ **02:00 ET**; **DEFAULT** row groups ?128 MB; **LOW\_RAM** succeeds on 2-GB VM under 0.65 RAM cap.
* **/metrics** exposes RED + budgets + breakers with exemplars; **chaos/soak** suites pass; **MTTR ?5 min** observed.
* Nightly **backup + verify** artifacts present; **weekly restore drill** succeeds with report in Operator Console.
* CI gates green: SCA, SBOM, Gitleaks, unit/integration, visual baselines; log redaction tests pass.
* ADRs present: **0001 UUIDv7**, **0002 Valuation**, **0003 Backups & Tracing (Pack A)**.
