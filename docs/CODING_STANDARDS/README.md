### /docs/CODING\_STANDARDS/README.md

# Coding Standards — Crypto Analytics Dashboard (MVP)

> Scope: standards derived strictly from the provided blueprint & repo docs. When specifics are not present in inputs, the item is tagged **\[Unverified]** and must be finalized during implementation.

## Language Guides

### TypeScript (Next.js App Router — UI)

* **Boundary rule:** UI calls **only** the FastAPI BFF; no direct provider SDK calls from the browser. Enforce all data access via `/health`, `/capabilities`, `/assets/{id}/candles`, `/portfolio/…`, `/onchain/*`, `/metrics`. &#x20;
* **Operator Console:** implement guarded controls (budget edit with clamps, breaker toggle with confirm, compactor dry-run, **“Use EOD Once”**). Reflect status cards for budgets/429/breakers/FX drift/disk guard/backup drill.&#x20;
* **Indicators:** keep MA/RSI/MACD utilities pure/deterministic; do not forward-fill series.&#x20;
* **Capabilities gating:** ETH gas/BTC mempool panels must respect `/capabilities` when keys are missing.&#x20;

### Python (FastAPI BFF)

* **HTTP contracts:** implement paths listed in Architecture/API; document **2xx/4xx/5xx** and **429 with `Retry-After`**.&#x20;
* **Rate-limit semantics:** honor adaptive clamps, cooldown, hysteresis; **freeze on 403**; expose counters via `/metrics`.&#x20;
* **CSV import:** enforce Transactions CSV v1.1 schema, UUIDv7 IDs, idempotency keys; normalize **FEE**; transfers **no P\&L**. &#x20;
* **Valuation responses:** persist/return `{price_source,resolution,asof}`; no forward fill; FX fallback sets `drift_bps` and flags `DELAYED_FX` when guarded.&#x20;

### Python (Worker)

* **Snapshots:** materialize 5m/1h/1d with provider-aware bucket-close; persist price/FX annotations; never forward-fill.&#x20;
* **Lots:** implement FIFO/LIFO as specified; transfers move lots and preserve acquisition dates.&#x20;
* **Compactor:** respect profiles (DEFAULT?128 MB, LOW\_RAM?32 MB), **RAM watermark 0.65** (alert 0.90), and partition path `dt=YYYY-MM-DD/asset_id=…`.&#x20;

### DuckDB/Parquet

* **Partitioning & profiles:** write Parquet under `dt=YYYY-MM-DD/asset_id=…`; use configured row-group size per profile.&#x20;
* **Views:** query via DuckDB **views** over Parquet; treat view definitions as internal and changeable.&#x20;

## Lint/Format Rules

* **Required in CI:** lint & format must pass to merge (**CI gate**).&#x20;
* **Configs:** repository-wide lint/format configs must live at the root and be referenced by CI **\[Unverified]**.
* **TypeScript:** project-wide strict typing & ESLint/Prettier enforcement **\[Unverified]**.
* **Python:** static checks + formatter (e.g., ruff/flake8 + black) **\[Unverified]**.
* **Docs/specs:** OpenAPI and JSON Schemas validated by existing CI jobs; no unchecked drift of public contracts.&#x20;

## Error Handling

> Define canonical, testable error categories; map to HTTP or operator-visible states.

| Code (canonical)          | Layer  | Behavior / Mapping                                                                                                      |
| ------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------- |
| `client_invalid_contract` | API    | CSV/schema/idempotency violation ? **4xx** with machine-readable detail; quarantine oversize files **\[Unverified]**.   |
| `provider_throttled`      | API    | Upstream limits ? **429** with **`Retry-After`**; counters exported; clamps adjust (50–100% in 10% steps).              |
| `provider_banned`         | API    | Upstream **403** ? **freeze** provider calls until recovery/operator action; breaker state visible.                     |
| `provider_outage`         | API    | Upstream **5xx** ? breaker **open**, half-open probes, metrics/traces linked; operator can force close/open.            |
| `fx_drift_hold`           | Worker | FX fallback drift `>25 bps` ? flag `DELAYED_FX`, **hold NAV** until operator uses **“Use EOD Once”**.                   |
| `disk_guard_low_space`    | Worker | At **2 GB** threshold reduce ingest cadence; surface alert in Operator Console.                                         |

**General rules**

* Propagate **canonical codes** in problem details (API) and in logs/metrics tags (all layers). **\[Unverified]**
* Never forward-fill time series; always include `{resolution,asof,source}` in valuation responses.&#x20;
* CSV normalization must always emit FEE rows and keep transfer acquisition dates.&#x20;

## Logging

* **Structured logs:** JSON with at minimum `ts, level, service, module, event_code, trace_id, span_id, message`. Include canonical codes above for searchability **\[Unverified]**; **logs must include `trace_id/span_id`**. &#x20;
* **Redaction:** secrets must never appear in logs; CI includes redaction tests + Gitleaks gate.&#x20;
* **Observability linkage:** export RED metrics; attach **exemplars** with `trace_id` to key counters; sampling = head **10%**, tail **100%** for errors/>1 s spans.&#x20;
* **Classification:** respect data classification (Internal/Confidential/Secret) in log fields and avoid logging Confidential payloads.&#x20;
* **Levels:** `ERROR` (user-impacting, opens breakers/guards), `WARN` (recoverable/transient), `INFO` (state changes: budgets updated, breaker toggles), `DEBUG` (development). **\[Unverified]**

---

*Reasoning Summary:* Standards are scoped to the documented architecture, contracts, reliability/FX policies, observability, and operator flows. Tool-specific lint/format choices are marked **\[Unverified]** pending repo configuration.

---
