### /docs/RELEASE\_PROCESS.md

# RELEASE\_PROCESS — Crypto Analytics Dashboard (MVP)

## Branch Strategy

* **Model:** Short-lived feature branches ? PR to the default branch; default branch is protected by CI and code-owner rules. *I cannot verify the default branch name from your inputs.* **\[Unverified]**&#x20;
* **PR requirements (must be green to merge):** OpenAPI validation + contract tests; JSON Schema validation (CSV v1.1, asset registry, price/FX) with **N/N+1 dry-run** for registry; events conformance (if emitting); unit/integration/E2E (Playwright) incl. chaos/soak; SCA/SBOM/Gitleaks; docs lint; backup-verify job; `/metrics` text parse. Code owner required on critical paths.&#x20;
* **Versioning & tags:** Use **SemVer** tags (`vX.Y.Z`) on the default branch; create a release from a signed tag. *Tooling (e.g., semantic-release) is not specified.* **\[Unverified]**&#x20;
* **Hotfixes:** Branch from the last release tag, apply fix, bump **patch**, tag and release after CI passes. **\[Unverified]** (no explicit hotfix policy in inputs).
* **Documentation updates on change to Public surfaces:** PR must update **OpenAPI**, **Data Contracts** (and run registry dry-run), **Interfaces**, **SLOs**, and **EVENTS** (if used).&#x20;

## Feature Flags

* **Types & sources**

  * **Capability flags** (environment-key gated): ETH gas / BTC mempool panels exposed only when keys are present and `/capabilities` reports them **enabled**.&#x20;
  * **Operator toggles** (runtime controls): breaker **open/close**, budget clamps (min/max enforced), **compactor dry-run**, **“Use EOD Once”** for FX.&#x20;
  * **Policy rails** (always-on safety): adaptive clamps (50–100% in 10% steps, 60s cooldown, 2× hysteresis), honor `Retry-After`, **freeze on 403**; breakers with half-open probes.&#x20;
* **Lifecycle**

  * **Introduce** behind a flag with owner and removal criteria; default **off** for risky paths (UI pages, new providers). **\[Unverified]**
  * **Test matrix** must include *flag on/off* across UJ1–UJ4 journeys and chaos/soak scenarios before enabling by default.&#x20;
  * **Retire** flags promptly after stabilization; delete dead code and update docs. **\[Unverified]**
* **Visibility:** Flag state and operator actions MUST surface in the Operator Console status cards/logs with `trace_id` correlation.&#x20;

## Cut Criteria

A release can be **cut** only when all of the below are satisfied:

* **Acceptance & Public Contracts**

  * PRD “User Stories & Acceptance” satisfied (CSV v1.1 ingest/idempotency/FEE; candles+indicators; portfolio NAV/TWR/DD; outage operations; nightly backup+verify & weekly restore drill).&#x20;
  * OpenAPI paths/components updated; **2xx/4xx/5xx** (incl. **429 + `Retry-After`**) documented with round-trip examples; contract tests pass.&#x20;
  * JSON Schemas validate fixtures; **registry N/N+1 dry-run** shows no breaking diffs without a major bump.&#x20;
* **Reliability & SLOs**

  * Trace-derived **p95/p99** within targets (API 250/600 ms; candles 900/1.8 s; portfolio 1.2/2.5 s). Success ? **99.5%/24h**, cache-hit ? **70%**, breaker **MTTR ? 5 min**.&#x20;
  * Rate-limit rails active (clamps, cooldown, hysteresis, `Retry-After`, **freeze on 403**); breaker state visible; `/metrics` exports counters with exemplars.&#x20;
* **Backups & Restore**

  * Last nightly **backup + verify** succeeded; weekly **restore drill** produced `drill_report.json` and is visible in the Operator Console.&#x20;
* **Observability & Security**

  * Span taxonomy + sampling (head 10%, tail 100% for errors/>1s); logs include `trace_id/span_id`; Prometheus `/metrics` text scrapes cleanly.&#x20;
  * Local-only binding (127.0.0.1), strict CORS, secret redaction tests, CSV hardening gates pass.&#x20;
* **E2E & Visual**

  * Playwright UJ1–UJ4 pass with updated baselines; chaos/soak at 80% ceilings green.&#x20;
* **Changelog**

  * Changelog prepared; on tag, CI **auto-generates** and publishes release notes. *Exact tooling is not specified.* **\[Unverified]**&#x20;

## Rollback Plan

* **P0 mitigate (no redeploy):**

  * **Disable feature flags** / set Operator Console toggles to safe settings (e.g., tighten clamps; open/close breakers as needed; revoke **“Use EOD Once”** if FX drift persists).&#x20;
* **Code rollback:**

  1. Checkout previous **SemVer tag**; 2) redeploy containers/services locally; 3) verify `/health` and key UJ endpoints. **\[Unverified exact commands]**&#x20;
* **Data rollback (if corruption/regression suspected):**

  * Run `make restore` to recover from the last nightly backup; confirm via integrity check and DuckDB sample scans; attach the latest **restore drill** report to the incident notes.&#x20;
* **Post-rollback checks:**

  * Validate SLO probes (trace p95/p99, success rate, cache-hit, breaker MTTR) and `/metrics` counters; confirm Operator Console status cards healthy.&#x20;
* **Follow-ups:** File incident & postmortem; revert flags permanently or re-enable behind **capability gating** until fixed. **\[Unverified process owners/timelines]**&#x20;

### /docs/\_meta/RELEASE\_PROCESS.meta.json

{
"version": "1.0",
"doc": "RELEASE\_PROCESS.md",
"status": "Draft",
"ci\_hooks": \["Release checklist gate", "Automated changelog on tag"],
"quality\_checklist": \["Rollback documented & tested", "Flag lifecycles clear"],
"open\_questions": \["What is the canonical default branch name for protected releases?", "Which tool generates the changelog on tag (e.g., semantic-release)?"],
"assumptions": \["Releases are cut from signed SemVer tags on the default branch"],
"sources": \["PROJECT\_BLUEPRINT.md"],
"techniques": \["Role Prompting","Decomposition","Structured Output","Eliciting Abstention","Self-Correction"]
}
