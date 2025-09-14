### /docs/SECURITY\_REQUIREMENTS.md

# SECURITY\_REQUIREMENTS — Crypto Analytics Dashboard (MVP)

> Scope: CI-enforceable requirements distilled strictly from the provided blueprint and docs. Where facts are missing, items are tagged **\[Unverified]** with explicit abstention: “I cannot verify this from your inputs.”
> Anchors reference Threat Model mitigations **M-01…M-11** and other docs where applicable. &#x20;

## ASVS Mapping

> ASVS category coverage derived from local-first design, CSV hardening, rate-limit rails, logging/redaction, and supply-chain controls. Exact ASVS **version and IDs** are **\[Unverified]** — “I cannot verify this from your inputs.”

| Area                      | What we do                                                                                            | ASVS Ref (placeholder)        |
| ------------------------- | ----------------------------------------------------------------------------------------------------- | ----------------------------- |
| Architecture & Deploy     | Bind **127.0.0.1**, strict CORS; no internet exposure. (M-01)                                         | ASVS-V1 **\[Unverified]**     |
| Access Control / Auth     | Single-user, local-only; **no user accounts/sessions**. Capability gating via `/capabilities`.        | ASVS-V2/V4 **\[Unverified]**  |
| Validation / Sanitization | CSV schema enforcement, size/row caps, **formula sanitization**, quarantine; CSV fuzzer in CI. (M-02) | ASVS-V5 **\[Unverified]**     |
| API & Rate Limiting       | Token buckets, adaptive clamps, `Retry-After`, circuit breakers; **freeze on 403**. (M-03)            | ASVS-V11 **\[Unverified]**    |
| Logging & Auditing        | Structured JSON logs, **secret redaction**, trace correlation; `/metrics` with exemplars. (M-10)      | ASVS-V7 **\[Unverified]**     |
| Cryptography & Integrity  | Backup manifests with checksums; backup-at-rest encryption **\[Unverified]**. (M-07)                  | ASVS-V6 **\[Unverified]**     |
| Supply Chain              | `pip-audit`, `npm audit`, **Syft SBOM**; PR gates. (M-11)                                             | ASVS-V14 **\[Unverified]**    |

**CI rule:** Until IDs are finalized, tag each automated test with `x-asvs:"[Unverified]"` and fail the “ASVS rule tests” job if any required tag is missing.

## Auth/Session

**Policy**

1. **No accounts/sessions.** All services **MUST** bind to **127.0.0.1**; access is governed by local OS user. (M-01)&#x20;
2. **CORS:** allow only `http://localhost`/`http://127.0.0.1` origins. (M-01)&#x20;
3. **Capabilities:** When required provider keys are absent, `/capabilities` **MUST** disable dependent panels and endpoints **MUST** return `{ enabled:false }`.&#x20;

**Verification (CI/QA)**

* Static/compose check asserts all container ports are published as `127.0.0.1:PORT`. (M-01)&#x20;
* Contract tests for `/capabilities` with and without keys. **Key names \[Unverified]**. “I cannot verify this from your inputs.”&#x20;

## Crypto

**Policy**

1. **Integrity for backups:** Nightly backup **MUST** produce `manifest.json` with file checksums; verify via DB integrity check and DuckDB sample scans. **Checksum algorithm \[Unverified]**. (M-07)&#x20;
2. **At-rest encryption:** **\[Unverified]** — backup encryption and key management not specified. “I cannot verify this from your inputs.” (M-07)&#x20;
3. **Transport:** Localhost-only; TLS requirements **\[Unverified]** due to local scope. (M-01)&#x20;

**Verification (CI/QA)**

* `make backup.verify` job must pass (integrity check + DuckDB sample scans). (M-07)&#x20;
* Fails if `manifest.json` missing checksums or weekly `drill_report.json` absent. (M-07)&#x20;

## Input Validation

**Policy (CSV & API)**

1. **CSV v1.1 schema:** Enforce column set/enums; IDs **UUIDv7**; **FEE** normalization; transfers **no P\&L**; **idempotency keys** must dedupe. (M-02)&#x20;
2. **CSV hardening:** Reject files **>10 MB** or **>100k rows**; apply per-field length caps; **escape/strip formula-leading characters**; quarantine failures. (M-02)&#x20;
3. **HTTP contracts:** OpenAPI must define 2xx/4xx/5xx with **429 + `Retry-After`** where applicable.&#x20;

**Verification (CI/QA)**

* JSON-Schema validation for CSV v1.1 and fixtures; CSV fuzzer job present. (M-02)
* Contract tests assert `429` and `Retry-After` on budget exhaustion. (M-03)&#x20;

## Logging/Audit

**Policy**

1. **Structured logs (JSON):** include `ts, level, service, event_code, trace_id, span_id, message`. **Exact schema fields \[Unverified]**. (M-10)&#x20;
2. **Secrets redaction:** secrets **MUST NOT** appear in logs; enforce via redaction tests + **Gitleaks** gate. (M-04)&#x20;
3. **Metrics/Traces:** Export RED metrics (with **exemplars** linking `trace_id`); sampling = head **10%**, tail **100%** on errors/>1 s. (M-10)&#x20;
4. **Operator actions:** breaker toggles, budget edits, FX **“Use EOD Once”** **MUST** be logged and visible in the Operator Console.&#x20;
5. **Classification & Retention:** `.env` = **Secret**; CSV/Parquet = **Confidential**; telemetry TTL ? **7 days**.&#x20;

**Verification (CI/QA)**

* Redaction test scans logs for secret substrings; **Gitleaks** job required to merge. (M-04)&#x20;
* `/metrics` scrape test validates presence of budget/breaker counters and exemplars; trace correlation e2e. (M-03/M-10)&#x20;

---

**Secrets Policy (enforced)**

* **Do not** hard-code secrets; load from `.env` (classified **Secret**); prohibit logging or exporting secrets to metrics/traces. Redaction tests + **Gitleaks** CI **MUST** pass.&#x20;

---

*Reasoning Summary:* Requirements were distilled only from the provided blueprint: localhost binding & strict CORS (M-01), CSV hardening (M-02), rate-limit rails & breakers (M-03), secret redaction & Gitleaks (M-04), backup/verify/drill (M-07), observability with exemplars & sampling (M-10), and supply-chain gates (M-11). ASVS IDs, backup encryption, checksum algorithm, exact log schema fields, and env key names are **\[Unverified]** and flagged for follow-up. &#x20;

---

### /docs/\_meta/SECURITY\_REQUIREMENTS.meta.json

{
"version": "1.0",
"doc": "SECURITY\_REQUIREMENTS.md",
"status": "Draft",
"ci\_hooks": \["ASVS rule tests","Secret-scan gate"],
"quality\_checklist": \["ASVS IDs present","Secrets policy included"],
"open\_questions": \[
"Which ASVS version and concrete control IDs apply? \[Unverified]",
"Is backup-at-rest encryption required? If yes, algorithm and key management? \[Unverified]",
"What checksum algorithm is mandated for backup manifests? \[Unverified]",
"Exact log schema fields (beyond trace correlation) and retention knobs? \[Unverified]",
"Canonical environment key names for capability gating? \[Unverified]"
],
"assumptions": \[
"Local-first, single-user; no auth/session beyond localhost binding",
"No external exposure; CORS restricted to localhost",
"Telemetry retained locally \~7 days as per blueprint"
],
"sources": \["PROJECT\_BLUEPRINT.md"],
"techniques": \["Role Prompting","Decomposition","Structured Output","Eliciting Abstention","Self-Correction"]
}
