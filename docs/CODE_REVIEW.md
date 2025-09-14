### /docs/CODE\_REVIEW\.md

# Code Review Guide — Crypto Analytics Dashboard (MVP)

## Purpose

Establish crisp, automatable review criteria aligned to the blueprint so changes ship safely under local-first, rate-limited, and offline constraints. Prioritize user journeys (UJ1–UJ4), public contracts (HTTP + file schemas), reliability rails (limits/breakers/FX drift), observability, and backups. &#x20;

## Reviewer SLAs

* **Code owner required on critical paths** (API/public contracts/Operator Console). *CI-enforced.*&#x20;
* **Time-to-first-review** and **merge windows** — *I cannot verify this from your inputs.* **\[Unverified]**
* **Escalation** (blocking items) — page module owner; defer nits. **\[Unverified]**

## Blocking Categories

1. **Public surface changes without spec/contract updates**
   *OpenAPI paths/components, 2xx/4xx/5xx (incl. 429 + Retry-After), examples round-trip; Data Contracts JSON Schemas; Events schemas if emitting.*  &#x20;
2. **Valuation/FX policy violations**
   *No forward fill; persist `{price_source,resolution,asof}`; drift guard & “Use EOD Once” path present.*&#x20;
3. **Rate limits/reliability regressions**
   *Ceilings/clamps (50–100% in 10% steps), cooldown 60s, hysteresis 2×, honor Retry-After, freeze on 403; breakers open/half-open/closed with probes.*&#x20;
4. **CSV ingestion contract breaches**
   *Transactions CSV v1.1 columns/enums; UUIDv7; idempotency keys; FEE normalization; transfers produce no P\&L.*&#x20;
5. **Storage/compaction safety issues**
   *Partitions `dt=YYYY-MM-DD/asset_id=…`; row-group profile; RAM watermark 0.65 (alert 0.90); disk guard at 2 GB.*&#x20;
6. **Observability gaps**
   *Span taxonomy; sampling head 10% / tail 100% on errors/>1 s; RED metrics with exemplars; logs include trace\_id.*&#x20;
7. **Security/privacy violations**
   *Bind 127.0.0.1; strict CORS; secret redaction in logs; CSV hardening (schema/size caps; formula sanitization).*&#x20;
8. **Backups/restore drills broken**
   *Nightly backup + verify artifacts; weekly drill report path/visibility preserved.*&#x20;
9. **SLO/perf budget regressions**
   *p95/p99 (API/candles/portfolio), success rate, cache hit, breaker MTTR targets tied to traces/metrics.*&#x20;
10. **Interfaces/dep policy breaches**
    *Public vs internal boundaries; deprecation/change process not followed.*&#x20;

## Nits Etiquette

* Use non-blocking comments for style/cosmetic issues; batch suggestions.
* Prefer fix-forward for nits if blocking criteria are met.
* Tie subjective UX nits to tokens/UX\_GUIDE if/when defined. **\[Unverified]**
* Require doc links for any “nit: add docs” comment (point to section being updated).&#x20;

## Checklist

> Check what applies before Approve.

* [ ] **Public surface touched?** OpenAPI updated; 2xx/4xx/5xx incl. **429 + Retry-After** documented; examples round-trip; contract tests pass.&#x20;
* [ ] **File contracts touched?** JSON Schemas (CSV v1.1, Asset Registry, Price/FX) updated; fixtures validate; N/N+1 dry-run enforced for registry.&#x20;
* [ ] **Events emitted/changed?** Subjects/schemas align to EVENTS; conformance tests green **\[Unverified transport]**.&#x20;
* [ ] **Valuation math** respects **no forward fill**; responses include `{resolution, asof, source}`; FX fallback sets `drift_bps` and gates NAV until **Use EOD Once** path.&#x20;
* [ ] **Rate-limit policy**: clamps 50–100% in 10% steps; cooldown 60s; hysteresis 2×; Retry-After honored; **freeze on 403**; breakers/state metrics wired.&#x20;
* [ ] **CSV ingestion**: UUIDv7 ids; idempotency keys; **FEE** normalization; transfers **no P\&L**; duplicates deduped.&#x20;
* [ ] **Storage/compactor**: partition path format; row-group profile (DEFAULT/LOW\_RAM); **0.65 RAM** watermark; **2 GB** disk guard behavior.&#x20;
* [ ] **Observability**: spans taxonomy present; sampling policy; RED metrics + exemplars; logs carry `trace_id/span_id`.&#x20;
* [ ] **SLOs**: trace-derived p95/p99 within targets; success rate, cache hit, MTTR budgets unaffected (or SLOs updated).&#x20;
* [ ] **Security/privacy**: localhost binding; strict CORS; secret redaction tests; CSV caps/quarantine; Gitleaks/SBOM/SCA gates unaffected.&#x20;
* [ ] **Backups & drills**: nightly backup/verify and weekly drill artifacts/links remain correct.&#x20;
* [ ] **Operator Console**: budgets edit (clamped), breaker toggle (confirm), compactor dry-run, **Use EOD Once** wired; `/capabilities` gating intact.&#x20;
* [ ] **Tests**: unit/contract/integration/E2E updated; chaos/soak scenarios covered; visual baselines updated as needed. &#x20;
* [ ] **Docs updated** (PRD/Design/Data Contracts/Interfaces/SLOs/Events as applicable).     &#x20;

---