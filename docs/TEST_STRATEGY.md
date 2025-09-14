### /docs/TEST\_STRATEGY.md

# TEST\_STRATEGY — Crypto Analytics Dashboard (MVP)

## Pyramid (Unit/Contract/Integration/E2E)

**Unit**

* **Worker (valuation & lots):** bucket-close logic per 5m/1h/1d, DST edges; lots FIFO/LIFO and “transfers produce no P\&L”. Assert persisted `{resolution,asof,source}` and FX rules.
* **Compactor:** profiles DEFAULT/LOW\_RAM, watermark 0.65 RAM with spill behavior.
* **Limiters/Breakers:** adaptive clamps (50–100%), cooldown 60s, hysteresis 2×; honor `Retry-After`; freeze on 403.
* **UI utilities:** indicators (MA/RSI/MACD) formatting and state transforms.

**Contract**

* **HTTP API:** contract tests for `/health`, `/capabilities`, `/assets/{asset_id}/candles`, `/portfolio/holdings/import`, `/onchain/eth/gas`, `/onchain/btc/mempool`, `/assets/{asset_id}/metrics`, `/metrics`; include 2xx and documented 429 with `Retry-After` where applicable.
* **File contracts:** JSON Schema validation for Transactions CSV v1.1, Asset Registry, Price/FX annotation; enforce UUIDv7, idempotency, FEE normalization, no forward-fill.

**Integration**

* **End-to-end data path:** CSV v1.1 ? normalize ? Parquet ? DuckDB views; verify idempotent upsert and fee handling.
* **Valuation determinism:** resolution/asof correctness incl. DST boundaries.
* **Rate limits & outages:** generate synthetic 429/5xx; observe breakers (open/half-open) and clamps; verify `/metrics` counters & exemplars.
* **FX drift guard:** trigger fallback and assert `drift_bps > 25` holds NAV until override (“Use EOD Once”).
* **Backups & restore drills:** exercise `backup|backup.verify|restore` flow and presence of weekly drill artifact.

**E2E (Playwright)**

* **Critical journeys (SLO UJ1–UJ4):** Watchlist/Asset candles, Portfolio, CSV import, Operator Console (budgets, breakers, compactor dry-run, “Use EOD Once”). Include visual baselines.
* **Perf assertions:** p95/p99 per PRD/SLOs for API, candles, portfolio derived from `api.request` traces.

## Coverage Targets

* **Unit:** Python/TS code coverage (statements/branches/functions/lines) ? **\[Unverified]**. “I cannot verify this from your inputs.”
* **Contract (HTTP):** **Path coverage 100% \[Unverified]** across listed routes with 2xx + documented 429; `/metrics` text validated.
* **Contract (Files):** **Schema coverage 100%** for Transactions v1.1, Asset Registry, Price/FX annotations (fixtures round-trip).
* **Integration:** **Scenario checklist 100%** for valuation determinism (incl. DST), clamps/breakers, FX drift, backups/restore.
* **E2E:** **UJ1–UJ4 = 100%** scripted with visual baselines. **Perf**: assert PRD/SLO p95/p99 targets.

## Flaky Policy

* **Detection:** CI marks a test *flaky* after **\[Unverified]** intermittent failures within last N runs; auto-open issue with logs/artifacts. **\[Unverified]**
* **Quarantine:** Move to a quarantined bucket so it runs but does not block merge; create owner-tagged ticket; annotate test with `@flaky` and link issue. **\[Unverified]**
* **Deflake SLA:** Owner triages root cause (timing, network, async, data). Require **2 consecutive green runs** post-fix before removal from quarantine. **\[Unverified]**
* **Visual tests:** On baseline drift, require human review and explicit baseline update PR.
* **Chaos/soak:** Flakiness discovered during 3-hour soak at 80% ceilings is tracked under the same workflow.

## Test Data Management

* **Fixtures (authoritative):**

  * `DATA_CONTRACTS/fixtures/transactions.v1.1.sample.csv` — happy path + FEE + transfers (validates v1.1 schema). **\[Unverified content]**
  * `DATA_CONTRACTS/fixtures/asset.registry.sample.json` — semver + checksum. **\[Unverified content]**
  * `DATA_CONTRACTS/fixtures/candles.sample.parquet` — partitioned by `dt/asset_id`. **\[Unverified content]**
* **Classification:** CSV inputs & Parquet analytics are **Confidential**; ensure secret redaction in logs is validated by integration tests.
* **Synthetic conditions:**

  * **429/5xx** responses for providers to test clamps/breakers/`Retry-After`.
  * **FX fallback** episodes to assert `drift_bps` guards and operator override.
  * **Backups/drills**: generate artifacts under `/data/backups/%Y-%m-%d/` and verify integrity + sample scans.
* **Schema evolution:** Apply **N/N+1** dry-run for registry changes; fail on breaking diffs without a major bump.

---

*Reasoning Summary:* Built the CI-ready test strategy strictly from the provided blueprint/PRD/SLOs/Data Contracts. Where numeric coverage/flaky thresholds weren’t specified, I marked them **\[Unverified]** per guardrails. Mapped tests directly to public surfaces, SLO journeys, rate-limit/FX policies, backups, and operator controls.

---