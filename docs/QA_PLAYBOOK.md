### /docs/QA\_PLAYBOOK.md

# QA Playbook — Crypto Analytics Dashboard (MVP)

> Scope: concrete test charters, a11y checks, numeric perf budgets, and a pragmatic browser/device grid. All items derive strictly from provided docs; gaps are tagged **\[Unverified]**.

## Exploratory Charters

**Format:** *Goal ? Tours ? Oracles ? Exit Artifacts*

* **CSV Import & Idempotency**

  * *Goal:* Normalize CSV v1.1, enforce UUIDv7, FEE normalization, transfer?P\&L.
  * *Tours:* happy-path; duplicate rows (idempotency keys); oversize/invalid schema; FEE & transfers.
  * *Oracles:* rows in SQLite; FEE rows materialized; transfers preserve acquisition dates.
  * *Artifacts:* test run log; normalized sample dump; schema validation report.

* **Valuation Granularity & Bucket Boundaries**

  * *Goal:* Correct 5m/1h/1d bucket-close with **no forward fill**.
  * *Tours:* edges at interval boundaries; DST transitions; sparse history.
  * *Oracles:* responses include `{resolution, asof, source}`; boundary math matches spec.
  * *Artifacts:* trace set (api.request); comparison notebook or diff.

* **FX Fallback & Drift Guard**

  * *Goal:* Safe behavior when primary FX fails.
  * *Tours:* trigger fallback; induce large `drift_bps`; invoke **“Use EOD Once”**.
  * *Oracles:* `drift_bps > 25` flags `DELAYED_FX`; NAV held until override.
  * *Artifacts:* `/metrics` snapshot; operator action log.

* **Rate Limits, Breakers & Adaptive Clamps**

  * *Goal:* Resilience under 429/5xx and bans.
  * *Tours:* burst past ceilings; honor `Retry-After`; simulate 403.
  * *Oracles:* clamps move 100%?50% in 10% steps; breaker open/half-open/closed; freeze on 403.
  * *Artifacts:* `/metrics` counters with exemplars; traces linking to spikes.

* **Operator Console Controls**

  * *Goal:* Safe, observable operations.
  * *Tours:* edit budgets (clamped bounds); breaker toggle with confirm; **compactor dry-run**; **Use EOD Once**.
  * *Oracles:* status cards reflect actions; logs carry `trace_id`.
  * *Artifacts:* e2e screenshots; audit log excerpt.

* **Backups, Verify & Weekly Restore Drill**

  * *Goal:* Pack A backup SLOs.
  * *Tours:* nightly artifact presence; integrity\_check; DuckDB sample scans; restore to temp workspace.
  * *Oracles:* backup artifacts under `/data/backups/%Y-%m-%d/`; `drill_report.json` produced; Operator shows last drill status.
  * *Artifacts:* manifest + verify logs; drill report.

* **Compactor Profiles & Disk Guard**

  * *Goal:* DEFAULT vs LOW\_RAM profiles under RAM watermark **0.65**, alert at **0.90**, disk guard at **2 GB**.
  * *Tours:* high-cardinality partitions; memory pressure; low disk.
  * *Oracles:* row-groups \~128 MB (DEFAULT) / \~32 MB (LOW\_RAM); ingest cadence reduces on disk guard.
  * *Artifacts:* compactor stats; alert records.

* **Service Worker Offline & SWR**

  * *Goal:* Offline banner + last `asof`; stale-while-revalidate.
  * *Tours:* go offline ? interact ? back online; cache bust.
  * *Oracles:* banner visible; data consistency after revalidate.
  * *Artifacts:* network log; screenshots.

* **On-Chain Panels & Capabilities Gating**

  * *Goal:* ETH gas / BTC mempool panels respect missing keys via `/capabilities`.
  * *Tours:* keys present vs missing.
  * *Oracles:* endpoints return values or `{enabled:false}`; UI gates features accordingly.
  * *Artifacts:* capability matrix; UI capture.

* **Observability: Traces, Metrics, Logs**

  * *Goal:* Trace sampling (head 10%, tail 100% errors/>1s) + RED metrics with exemplars.
  * *Tours:* induce error paths; long spans; correlate logs.
  * *Oracles:* `/metrics` export contains counters; logs include `trace_id/span_id`.
  * *Artifacts:* Prometheus scrape; trace screenshots.

## Accessibility Checks

* **Keyboard & Focus:** Tab order across pages, dialogs (budget edit, breaker confirm), focus traps, visible focus states.
* **Charts:** Provide accessible names/labels and textual summaries for candles/indicators **\[Unverified]**.
* **Forms & Controls:** Labels/ARIA for inputs, toggles; error text tied to fields.
* **Live Regions:** Announce operator actions and async updates **\[Unverified]**.
* **Color/Contrast/Zoom:** Verify contrast and 200% zoom usability **\[Unverified]**.
* **Reference:** *WCAG 2.2 mapping* — see **A11Y\_CHECKLIST.md** **\[Unverified]**.

## Perf Budgets

> Measured from **api.request** traces and `/metrics` where applicable.

| Area                    | Metric              |                         Budget | Source/Measure                          |
| ----------------------- | ------------------- | -----------------------------: | --------------------------------------- |
| API baseline            | p95 latency         |                     **250 ms** | Trace p95                               |
| API baseline            | p99 latency         |                     **600 ms** | Trace p99                               |
| Asset candles           | p95 latency         |                     **900 ms** | Trace p95                               |
| Asset candles           | p99 latency         |                      **1.8 s** | Trace p99                               |
| Portfolio view          | p95 latency         |                      **1.2 s** | Trace p95                               |
| Portfolio view          | p99 latency         |                      **2.5 s** | Trace p99                               |
| Success rate (24h)      | Availability        |                    **? 99.5%** | `/metrics`                              |
| Cache effectiveness     | Cache hit rate      |                      **? 70%** | `/metrics`                              |
| Incident recovery       | Breaker MTTR        |                    **? 5 min** | `/metrics`                              |
| Compaction safety       | RAM watermark       | **? 0.65 of RAM** (alert 0.90) | compactor logs                          |
| Storage guardrail       | Low-disk trigger    |                       **2 GB** | `/metrics`/alerts                       |
| Lighthouse page budgets | LCP/INP/CLS targets |              **\[Unverified]** | `web-lh-budgets.json` **\[Unverified]** |

*CI notes:* perf assertions derive from traces; Lighthouse budgets required by CI job **\[Unverified]**.

## Cross-browser/device Grid

* **Playwright projects**

  * **chromium — Required**
  * **firefox — Optional \[Unverified]**
  * **webkit — Optional \[Unverified]**
* **Viewports**

  * **Desktop:** 1280×800, 1920×1080 **\[Unverified]**
  * **Mobile:** 390×844 (iPhone 12/13 class) **\[Unverified]**
* **OS**

  * Windows/macOS for desktop; iOS/Android emulation via Playwright **\[Unverified]**

---

*Reasoning Summary:* Charters map directly to CSV v1.1 ingestion, valuation/FX policies, rate-limit controls, Operator Console, backups/restore, compactor watermarks, offline behavior, and observability from the blueprint/PRD/SLOs. Perf budgets use the provided p95/p99/API targets plus numeric reliability guards; Lighthouse and some a11y/browser specifics are flagged **\[Unverified]** pending dedicated docs.

---