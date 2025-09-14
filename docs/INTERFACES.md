### /docs/INTERFACES.md

# INTERFACES — Crypto Analytics Dashboard (MVP)

> Scope: declare module boundaries and the public vs. internal surfaces, assign stability levels, and codify deprecation/change rules used by CI to guard breaking changes. All content is derived from the provided blueprint and docs. Items marked **\[Unverified]** could not be confirmed from your inputs.

## Module Boundaries

**System topology (authoritative):**
UI (Next.js App Router) ? API (FastAPI BFF) ? Data (SQLite/Redis) and Worker (Python ? Parquet/DuckDB). Nightly backups; Operator Console lives in UI. All services bind to 127.0.0.1.&#x20;

**Interfaces by module**

* **UI ? API (HTTP, localhost):**
  `/health`, `/capabilities`, `/assets/{asset_id}/candles`, `/portfolio/holdings/import`, `/onchain/eth/gas`, `/onchain/btc/mempool`, `/assets/{asset_id}/metrics`, `/metrics` (Prometheus text).&#x20;
* **Worker ? Data:**
  Reads SQLite + writes Parquet snapshots (5m/1h/1d), compacts with RAM watermark; DuckDB reads Parquet via views.&#x20;
* **Operator ? System (Operator Console + CLI):**
  Status/controls for budgets, breakers, FX drift override, compactor dry-run; `make backup|backup.verify|restore` artifacts and weekly restore drill.&#x20;
* **Contracts (file/API):**
  Transactions CSV v1.1 (ingest), Asset Registry `registry/assets.json` (seed), Price/FX annotations persisted with valuations.&#x20;

**Public vs. internal**

* **Public (to app consumers within the repo):** HTTP API listed above; Transactions CSV v1.1; Asset Registry format; Prometheus `/metrics`.
* **Internal:** SQLite schema, Parquet physical layout, compactor internals, Redis limiter keys, DuckDB view definitions.&#x20;

## Stability Levels

Use three tiers to drive CI policy and change control.

| Surface        | Elements                                                                                               | Stability                      | Notes                                                      |
| -------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------ | ---------------------------------------------------------- |
| HTTP API       | `/health`, `/capabilities`                                                                             | **Stable**                     | Must not break in MVP without deprecation window.          |
| HTTP API       | `/assets/{asset_id}/candles`, `/portfolio/holdings/import`, `/onchain/*`, `/assets/{asset_id}/metrics` | **Stable**                     | Document 429 + `Retry-After` behavior where applicable.    |
| Ops API        | `/metrics` (Prometheus text)                                                                           | **Stable**                     | Format must remain Prometheus-compatible.                  |
| File Contracts | Transactions CSV v1.1; Asset Registry; Price/FX annotation                                             | **Stable**                     | Enforced by JSON Schemas & migration SOP (N/N+1 dry-run).  |
| Events         | Catalog in `EVENTS.md`                                                                                 | **Experimental \[Unverified]** | Transport/retention not locked; schemas provisional.       |
| Internal       | SQLite/Parquet/DuckDB/Redis keys                                                                       | **Unstable (Internal)**        | May change freely; covered by internal tests only.         |

## Deprecation Policy

* **Versioning:**
  Public HTTP and file contracts follow **SemVer** at the repo level; breaking changes require **major**; additive fields = **minor**; clarifications = **patch**. **\[Unverified]** (no explicit version cadence provided). *I cannot verify this from your inputs.*&#x20;
* **N/N+1 window:**
  For breaking renames/semantics in **events** and **registry**, dual-emit or dual-accept for one adjacent version; fails closed if a major bump is missing in dry-run migration.
* **EOL timeline:**
  Define removal after at least one release cycle **\[Unverified]**; publish in CHANGELOG and docs before removal. *I cannot verify exact timelines from your inputs.* \[Unverified]

## Change Process

**Applies to any change touching Public surfaces.**

1. **Propose & Record**

   * If irreversible/architectural ? add/update **ADR**; if broad policy (e.g., rate limits) ? **RFC** with migration plan.&#x20;
2. **Update Specs/Contracts**

   * **OpenAPI** paths/components updated; examples round-trip; 2xx/4xx/5xx defined. CI: OpenAPI validation + contract tests.&#x20;
   * **Data Contracts** (CSV/Registry/Annotations): update JSON Schemas; run **N/N+1 dry-run** migration; CI validation jobs must pass.&#x20;
   * **Events**: update envelope/subjects/schemas; CI drift detector + conformance tests.
3. **SLO/Observability Alignment**

   * Reassess p95/p99 targets, success rate, MTTR; ensure `/metrics` counters and trace exemplars still map to SLOs.
4. **Operator Impact**

   * Reflect toggles/controls in the Operator Console (budgets, breakers, FX override) and update docs.&#x20;
5. **CI Gates (required to merge)**

   * **Breaking-change detector** over public API surface (Interface doc CI hook).
   * OpenAPI validation + contract tests; JSON Schema validation; events conformance; docs lint present.

*Reasoning Summary:* Interfaces are enumerated strictly from the blueprint/API section, data contracts index, and events catalog; stability tiers reflect MVP guarantees; deprecation mirrors the registry/event SOP with N/N+1; CI gates bind to provided hooks and spec validators.

---