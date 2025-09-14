### /docs/EVENTS.md

# Events Catalog — Crypto Analytics Dashboard (MVP)

> Scope: event envelope, subjects, idempotency, retention/DLQ, and minimal schemas to enable CI conformance checks. Items tagged **\[Unverified]** are not confirmed by provided inputs.

## Event Names & Subjects

**Subject format:** `domain.entity.action` (lowercase, dot-separated). **Producer:** `api|worker|compactor|scheduler|operator_console`. **ID:** `event_id` is **UUIDv7** (global policy).&#x20;

**Catalog (provisional)**

* **ingest.csv.accepted** — CSV v1.1 file accepted for processing (pre-normalize). Dedupe via CSV idempotency keys. **Producer:** api.&#x20;
* **ingest.csv.normalized** — rows normalized/upserted. **Producer:** worker.&#x20;
* **ingest.csv.failed** — ingestion failure with reasons. **Producer:** api|worker. \[Unverified]
* **valuation.snapshot.created** — 5m/1h/1d snapshot materialized (no forward fill), includes price/FX annotation. **Producer:** worker.&#x20;
* **compactor.run.completed** — compaction finished (RAM watermark respected), outputs row-group stats. **Producer:** compactor.&#x20;
* **backup.completed** — nightly backup artifacts written. **Producer:** scheduler.&#x20;
* **backup.verified** — PRAGMA/DuckDB sample scans passed. **Producer:** scheduler.&#x20;
* **restore.drill.completed** — weekly drill produced `drill_report`. **Producer:** scheduler.&#x20;
* **rate\_limit.breaker.opened** — breaker opened for a provider/route (429/5xx). **Producer:** api.
* **rate\_limit.breaker.closed** — breaker recovered/closed. **Producer:** api.&#x20;
* **provider.budget.updated** — operator changed clamp/ceilings (min/max enforced). **Producer:** operator\_console.
* **fx.drift.flagged** — fallback FX drift exceeded threshold; NAV held. **Producer:** worker.&#x20;
* **fx.drift.override\_used** — operator invoked “Use EOD Once”. **Producer:** operator\_console.&#x20;
* **disk.guard.threshold\_crossed** — low-disk guard engaged (ingest cadence reduced). **Producer:** worker|api.&#x20;

> Note: Subjects beyond those implied by the blueprint are **\[Unverified]** and may be adjusted once the transport is chosen.&#x20;

## Versioning Policy

* **Envelope `version`:** semver string. **Minor** = additive fields; **Major** = breaking/rename/semantic change; **Patch** = non-breaking clarifications. Aligns with registry semver discipline. \[Unverified]&#x20;
* **Subject stability:** changing the **subject** requires a **major** for that event family. \[Unverified]
* **Deprecation:** add `deprecated_in` + successor subject; emit both during transition (N/N+1). \[Unverified]&#x20;

## Ordering & Idempotency

* **Global ID:** `event_id` = UUIDv7; consumers must **dedupe** on `(subject, idempotency_key)` when present, else on `event_id`.&#x20;
* **Per-event idempotency keys (derived):**

  * `ingest.csv.*` ? CSV v1.1 keys: `(account, tx_hash)` | `external_id` | `id`.&#x20;
  * `valuation.snapshot.created` ? `(asset_id, resolution, asof)`. \[Unverified]&#x20;
  * `compactor.run.completed` ? `run_id`. \[Unverified]
  * `backup.*`/`restore.drill.completed` ? `backup_date`/`drill_id`. \[Unverified]
  * `rate_limit.breaker.*` ? `(provider, route) + window`. \[Unverified]&#x20;
  * `provider.budget.updated` ? `(provider, route) + updated_at`. \[Unverified]
  * `fx.drift.*` ? `(asof, base, quote)`. \[Unverified]&#x20;
* **Ordering:** no global ordering; consumers should enforce **per-key** ordering (e.g., by `asset_id` or CSV keys). \[Unverified]

## Retention & DLQs

* **Retention:** event transport retention/window **\[Unverified]**. Recommend ?7 days to align with telemetry/ops workflows. \[Unverified]&#x20;
* **DLQ:** route non-conforming events to `file:///data/dlq/events.ndjson` with hourly reprocessor. \[Unverified]
* **Backpressure:** on DLQ growth, raise `disk.guard.threshold_crossed`. \[Unverified]&#x20;

## Schemas

### A) Event Envelope (JSON Schema, v1.0) \[Unverified]

```json
{
  "$id": "EVENTS/envelope.v1.schema.json",
  "type": "object",
  "required": ["event_id","subject","version","time","producer","data"],
  "properties": {
    "event_id": { "type": "string", "format": "uuid", "description": "UUIDv7" },
    "subject": { "type": "string", "pattern": "^[a-z]+(\\.[a-z]+){1,}$" },
    "version": { "type": "string" },
    "time": { "type": "string", "format": "date-time" },
    "producer": { "type": "string", "enum": ["api","worker","compactor","scheduler","operator_console"] },
    "trace_id": { "type": ["string","null"] },
    "idempotency_key": { "type": ["string","null"] },
    "data": { "type": "object" }
  }
}
```

### B) `ingest.csv.normalized` — Data (reuses CSV v1.1 row) \[Unverified]

```json
{
  "$id": "EVENTS/ingest.csv.normalized.v1.schema.json",
  "allOf": [
    { "$ref": "DATA_CONTRACTS/schemas/transactions.v1.1.schema.json" }
  ]
}
```

*Rationale:* Mirrors ingestion contract; leverages existing idempotency keys.&#x20;

### C) `valuation.snapshot.created` — Data (candle/snapshot + price/FX) \[Unverified]

```json
{
  "$id": "EVENTS/valuation.snapshot.created.v1.schema.json",
  "type": "object",
  "required": ["asset_id","resolution","asof","row"],
  "properties": {
    "asset_id": { "type": "string" },
    "resolution": { "type": "string", "enum": ["5m","1h","1d"] },
    "asof": { "type": "string", "format": "date-time" },
    "row": {
      "allOf": [
        { "$ref": "DATA_CONTRACTS/schemas/candle.row.schema.json" },
        { "$ref": "DATA_CONTRACTS/schemas/price_fx.annotation.schema.json" }
      ]
    }
  }
}
```

*Rationale:* Emits snapshot with no forward fill; includes FX annotation and drift flags.

### D) `compactor.run.completed` — Data \[Unverified]

```json
{
  "$id": "EVENTS/compactor.run.completed.v1.schema.json",
  "type": "object",
  "required": ["run_id","profile","watermark_ram","partitions","row_groups_out"],
  "properties": {
    "run_id": { "type": "string", "format": "uuid" },
    "profile": { "type": "string", "enum": ["DEFAULT","LOW_RAM"] },
    "watermark_ram": { "type": "number" },
    "partitions": { "type": "integer" },
    "row_groups_out": { "type": "integer" }
  }
}
```

*Rationale:* Confirms 0.65 RAM watermark behavior and output stats.&#x20;

### E) `backup.completed` / `backup.verified` / `restore.drill.completed` — Data \[Unverified]

```json
{
  "$id": "EVENTS/backup.restore.v1.schema.json",
  "type": "object",
  "required": ["run_id","started_at","ended_at","status"],
  "properties": {
    "run_id": { "type": "string", "format": "uuid" },
    "started_at": { "type": "string", "format": "date-time" },
    "ended_at": { "type": "string", "format": "date-time" },
    "status": { "type": "string", "enum": ["SUCCESS","FAILURE"] },
    "manifest_path": { "type": ["string","null"] },
    "report_path": { "type": ["string","null"] }
  }
}
```

*Rationale:* Matches nightly backup + verify and weekly drill artifacts.&#x20;

### F) `rate_limit.breaker.*` / `provider.budget.updated` — Data \[Unverified]

```json
{
  "$id": "EVENTS/rate_limit.v1.schema.json",
  "type": "object",
  "required": ["provider","route","state"],
  "properties": {
    "provider": { "type": "string" },
    "route": { "type": "string" },
    "state": { "type": "string", "enum": ["OPEN","CLOSED","HALF_OPEN","UPDATED"] },
    "clamp": { "type": ["number","null"] },
    "retry_after_sec": { "type": ["integer","null"] }
  }
}
```

*Rationale:* Reflects budgets/clamps, breaker states, and Retry-After handling.&#x20;

---

*Reasoning Summary:* Derived an events scaffold strictly from the blueprint: ingestion (CSV v1.1), valuation snapshots without forward fill, compactor/backups/drills, and rate-limit/budget/FX drift/operator actions. Where the blueprint did not define transports or exact payloads, subjects/schemas are marked **\[Unverified]** and shaped to enable CI linting against current data contracts.