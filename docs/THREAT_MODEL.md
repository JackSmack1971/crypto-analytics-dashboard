### /docs/THREAT\_MODEL.md

# THREAT\_MODEL — Crypto Analytics Dashboard (MVP)

> Scope: STRIDE-lite threat model grounded strictly in the provided blueprint. Local-first, single-user; all services bind to 127.0.0.1. No speculative controls beyond inputs; gaps are tagged **\[Unverified]**.&#x20;

## Data Flows

```mermaid
flowchart TD
  subgraph UI[UI (Next.js, Operator Console)]
  end
  subgraph API[API (FastAPI BFF)]
  end
  subgraph WORKER[Worker (Python)]
  end
  subgraph STORES[Data Stores]
    SQL[(SQLite)]
    R[(Redis)]
    PQ[(Parquet)]
    DDB[(DuckDB Views)]
    BK[/ /data/backups/%Y-%m-%d/ /]
  end
  subgraph EXT[External Providers]
    CG[CoinGecko]
    ES[Etherscan]
    MS[mempool.space]
    FX[FX (exchangerate.host / ECB)]
  end

  UI <--> API
  API --> SQL
  API <--> R
  WORKER <--> SQL
  WORKER --> PQ
  DDB <--> PQ
  API --> CG & ES & MS & FX
  BK -. nightly .- SQL
  BK -. nightly .- PQ
```

**Key flows**

* **F1** UI ? API (local HTTP). Operator Console actions (budgets, breakers, compactor dry-run, “Use EOD Once”).&#x20;
* **F2** CSV v1.1 upload ? API ? Worker normalize/upsert. No forward fill; FEE normalization; transfers produce no P\&L.&#x20;
* **F3** API ? SQLite; **F4** Worker ? SQLite/Parquet; **F5** DuckDB Views ? Parquet.&#x20;
* **F6** API ? Providers (CoinGecko, Etherscan, mempool.space, FX). Limits/breakers/adaptive clamps; honor Retry-After; freeze on 403.&#x20;
* **F7** Telemetry: traces (OTel), Prometheus `/metrics` (RED + budgets/breakers with exemplars).&#x20;
* **F8** Backups: nightly 02:30 local; verify; weekly restore drill artifacts.&#x20;

## Assets & Trust Boundaries

### Assets (with sensitivity)

| Asset                                        | Location     | Classification                       |
| -------------------------------------------- | ------------ | ------------------------------------ |
| Source code & configs                        | Repo / local | Code (Internal); `.env` = **Secret** |
| Transactions CSV v1.1                        | User import  | **Confidential**                     |
| Parquet analytics, snapshots                 | Local FS     | **Confidential**                     |
| SQLite DB                                    | Local FS     | **Confidential**                     |
| DuckDB views                                 | Local FS     | Internal                             |
| Redis (limits/cache)                         | Local        | Internal                             |
| Telemetry (logs/metrics/traces)              | Local        | Internal; TTL 7d                     |
| Backup artifacts (`/data/backups/%Y-%m-%d/`) | Local FS     | **Confidential**                     |
| Provider responses (HTTP)                    | Network      | Internal (transient)                 |

(Bound to **127.0.0.1** with strict CORS; classification per blueprint.)&#x20;

### Trust boundaries

* **TB1** Browser ? API (localhost HTTP, strict CORS).&#x20;
* **TB2** API ? External providers (internet, rate-limited).&#x20;
* **TB3** Processes ? Filesystem (SQLite/Parquet/Backups).&#x20;
* **TB4** Processes ? Redis (downgrade to in-process leaky bucket on outage).&#x20;
* **TB5** Metrics/Traces exposure (Prometheus text; OTel sampling).&#x20;
* **TB6** CSV file ingress (user-supplied content).&#x20;

## STRIDE Findings (per flow)

> Abbrev: S=Spoofing, T=Tampering, R=Repudiation, I=Information Disclosure, D=Denial of Service, E=Elevation of Privilege.

### F2 — CSV upload ? normalize/upsert

* **T/I:** Malicious CSV (formula injection), schema abuse, oversize rows/files. ? **M-02 CSV hardening** (strict schema, per-field length caps, **max 10 MB / 100k rows**, escape/strip formula-leading chars), quarantine failed files; CSV fuzzer in CI.&#x20;
* **D:** Oversize/invalid inputs to exhaust worker/API. ? **M-02** (caps/quarantine).&#x20;
* **R:** Duplicate rows. ? Idempotency keys in CSV v1.1; normalized FEE rows; transfers no P\&L. **M-02**.&#x20;

### F1 — UI ? API (local)

* **S/E:** Cross-origin abuse minimized via localhost bind + strict CORS. ? **M-01 Localhost-only + CORS**.&#x20;
* **I:** Leaking secrets in responses/logs. ? **M-04 Log redaction + Gitleaks CI**.&#x20;

### F6 — API ? Providers

* **D:** Upstream 429/5xx/403; client-side bursts. ? **M-03 Rate-limiters + adaptive clamps (50–100%/10% steps), 60s cooldown, 2× hysteresis; honor Retry-After; breakers open/half-open/closed; freeze on 403**. Metrics exported with exemplars.&#x20;
* **R:** Provider outages masked. ? Breakers + `/metrics` + traces surface state (**M-03/M-10**).&#x20;

### F4/F5 — Worker/Views ? Parquet; valuation rules

* **T:** Forward-fill or FX misuse corrupts analytics. ? **M-06 No forward fill; persist `{price_source,resolution,asof}`; FX fallback w/ `drift_bps` guard; “Use EOD Once” override**.&#x20;
* **D:** Compaction memory spikes. ? **M-08 Compactor watermark 0.65 RAM (alert 0.90)**; LOW\_RAM profile.&#x20;

### F3 — API ? SQLite

* **I/T:** DB/file corruption. ? **M-07 Nightly backup + verify; weekly restore drill**; integrity check + DuckDB sample scans.&#x20;

### F7 — Telemetry (logs/metrics/traces)

* **I:** Secrets in logs/metrics. ? **M-04 Redaction tests + Gitleaks CI**; metrics expose budgets/breakers but not secrets.&#x20;
* **D:** High-cardinality/volume. ? **M-10 OTel sampling (head 10%, tail 100% on errors or >1s)**; exemplars link traces to RED metrics.&#x20;

### F8 — Backups (`/data/backups/%Y-%m-%d/`)

* **I:** Backup artifact exposure. ? Local-only design + classification; verify on write; weekly drills (**M-07**). **Encryption policy \[Unverified].**&#x20;
* **R:** Missing/failed backups. ? Verify step; drill report surfaced in Operator Console (**M-07**).&#x20;

### Shared/Infra

* **D:** Redis outage ? limiter failure. ? **M-05 In-process leaky-bucket fallback (default-deny) with downgrade/upgrade logs**.&#x20;
* **D:** Low disk. ? **M-09 Disk guard @ 2 GB** reduces ingest cadence + alert.&#x20;
* **S/T/I:** Supply-chain risk. ? **M-11 SCA (pip-audit/npm audit) + Syft SBOM; PR gates**.&#x20;

## Mitigations

> Canonical IDs (M-##) are used above and in CI checks.

* **M-01 Localhost-only + strict CORS** (network binding 127.0.0.1).&#x20;
* **M-02 CSV hardening** (schema, caps **10 MB/100k rows**, formula-sanitization, quarantine; fuzzer in CI; idempotency; FEE/transfer rules).&#x20;
* **M-03 Provider budgets + adaptive rate limits + breakers** (clamps 50–100%, 10% steps; 60s cooldown; 2× hysteresis; honor Retry-After; **freeze on 403**).&#x20;
* **M-04 Secrets redaction + Gitleaks** (CI gate).&#x20;
* **M-05 Redis outage fallback** (in-process leaky-bucket default-deny; log downgrade/upgrade).&#x20;
* **M-06 Valuation guardrails** (no forward fill; persist `{price_source,resolution,asof}`; FX fallback + `drift_bps`>25 holds NAV; **“Use EOD Once”** override).&#x20;
* **M-07 Backups/verify/restore drills** (nightly 02:30, 7-day retention; integrity\_check + DuckDB sample scans; weekly drill report).&#x20;
* **M-08 Compactor RAM watermark 0.65 (alert 0.90)**; LOW\_RAM profile option.&#x20;
* **M-09 Disk guard @ 2 GB** (reduce ingest cadence + Operator alert).&#x20;
* **M-10 Observability** (OTel span taxonomy; head 10% / tail 100% sampling; RED metrics with exemplars; logs carry trace\_id/span\_id).&#x20;
* **M-11 Supply-chain checks** (pip-audit, npm audit, **Syft SBOM**; PR gates).&#x20;

### Tracker mapping (issues)

| Mitigation | Issue/Ticket                                                 |
| ---------- | ------------------------------------------------------------ |
| M-01…M-11  | **\[Unverified]** — “I cannot verify this from your inputs.” |

### Verification hooks (CI/QA bindings)

* CSV fuzzer + schema validation (**M-02**); OpenAPI/contract tests; events (if any) **\[Unverified transport]**.&#x20;
* `/metrics` scrape & exemplar linkage (**M-03/M-10**); chaos/soak at 80% ceilings.&#x20;
* Backup verify & weekly restore drill artifact presence (**M-07**).&#x20;
* SBOM/SCA/Gitleaks gates (**M-04/M-11**).&#x20;

---

*Reasoning Summary:* Data flows, assets, and mitigations were extracted verbatim from the blueprint’s architecture, reliability rails (limits/breakers, Redis fallback, disk guard), valuation/FX policy, telemetry, backups, and security/classification sections. Gaps like backup encryption and issue IDs are marked **\[Unverified]** per guardrails.&#x20;

### /docs/\_meta/THREAT\_MODEL.meta.json

{
"version": "1.0",
"doc": "THREAT\_MODEL.md",
"status": "Draft",
"ci\_hooks": \["Dfd diagram presence check","Mitigation linkage lint"],
"quality\_checklist": \["STRIDE per flow","Mitigations mapped to issues"],
"open\_questions": \[
"Backup-at-rest encryption policy and key management \[Unverified]",
"Canonical issue IDs for mitigation mapping \[Unverified]"
],
"assumptions": \[
"Local-first, single-user; all services bind to 127.0.0.1",
"No cloud exposure; free-tier providers with adaptive limits and breakers"
],
"sources": \["PROJECT\_BLUEPRINT.md"],
"techniques": \["Role Prompting","Decomposition","Structured Output","Eliciting Abstention","Self-Correction"]
}
