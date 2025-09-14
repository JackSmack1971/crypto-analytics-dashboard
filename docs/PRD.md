### /docs/PRD.md

# PRD — Crypto Analytics Dashboard (MVP)

## Problem

Local-first, single-user crypto analytics needs fast, deterministic valuation (candles, NAV/TWR/DD) that stays resilient under free-tier rate limits, works offline, and is operator-controllable. UI: Next.js; API: FastAPI BFF; worker derives snapshots from Transactions CSV v1.1 into Parquet/DuckDB. IDs are UUIDv7. Nightly backups, tracing MVP, compactor watermarks, and CSV hardening are in scope (Pack A).&#x20;

## Users & Jobs

* **Solo operator/investor** — import CSVs, view watchlist/asset detail, analyze portfolio NAV/TWR/DD, inspect ETH gas & BTC mempool, and operate controls during provider outages/limits.&#x20;

## Scope / Out-of-Scope

**In scope**

* CSV v1.1 import with idempotency; valuation with provider-aware bucket-close and FX fallback/drift guard; charts (candles + MA/RSI/MACD); portfolio metrics; ETH gas & BTC mempool panels; Operator Console (status/controls); local OTel collector; nightly backups + weekly restore drill; Parquet/DuckDB views; Redis rate limiting/circuit breakers.&#x20;
  **Out of scope**
* Multi-user/cloud deployment; external exposure (bind must remain 127.0.0.1); forward-fill pricing; news integration (optional/unspecified) \[Unverified].&#x20;

## User Stories & Acceptance

1. **Import transactions CSV**

   * *As an operator*, I upload CSV v1.1 to normalize and upsert.
   * **Acceptance:** rows appear in SQLite; FEE rows normalized; idempotency via keys; `/capabilities` reflects key-gated features.&#x20;

2. **View asset candles & indicators**

   * *As a user*, I open Asset Detail to see candles with MA/RSI/MACD.
   * **Acceptance:** `GET /assets/{asset_id}/candles` returns `{t,o,h,l,c,v,resolution,asof}`; 429 documented with `Retry-After`; valuation includes `{resolution,asof,source}`.&#x20;

3. **Analyze portfolio NAV/TWR/DD**

   * *As a user*, I open Portfolio to see NAV/TWR/DD with deterministic backfill.
   * **Acceptance:** Lots engine computes P\&L; transfers have no P\&L; DuckDB views query Parquet successfully.&#x20;

4. **Operate during outages/limits**

   * *As an operator*, I inspect budgets/429/breakers/FX drift and toggle controls.
   * **Acceptance:** Operator Console shows status cards and allows breaker open/close (confirm), budget edits (clamped), compactor dry-run, and “Use EOD Once” for FX; `/metrics` exposes RED + budgets + breaker counters with exemplars.&#x20;

5. **Reliability & backups**

   * *As an operator*, I rely on auto backups and drills.
   * **Acceptance:** Nightly 02:30 local backup artifacts, verification via integrity\_check + DuckDB sample scans; weekly restore drill report visible.&#x20;

## Constraints & KPIs

**Constraints:** free-tier providers; localhost binding; offline-friendly SW cache; local OTel; partitioning/compaction profiles; compactor RAM watermarks; disk guard.&#x20;
**KPIs (targets):**

* p95: API 250 ms; candles 900 ms; portfolio 1.2 s.
* p99: API 600 ms; candles 1.8 s; portfolio 2.5 s.
* 24h success ?99.5%; cache hit ?70%; breaker MTTR ?5 min.&#x20;

## Risks / Open Questions

* Provider ceilings per plan/tier are incomplete **\[Unverified]** (“I cannot verify this from your inputs”).&#x20;
* Visual identity tokens not defined **\[Unverified]**.&#x20;
* Optional news/FX policies beyond listed providers **\[Unverified]**.&#x20;
* CSV ingestion threats (formula injection/oversize) — mitigated via caps/sanitization/quarantine. **Owner:** Engineering.&#x20;
* Provider DoS/bans — mitigated via limiters/breakers/adaptive clamps. **Owner:** Engineering.&#x20;

---

