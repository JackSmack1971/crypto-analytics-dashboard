### /docs/RFCs/0001-provider-budgets-and-adaptive-rate-limits.md

# RFC-0001 — Provider Budgets & Adaptive Rate-Limit Policy (MVP)

**Status:** Draft
**Date:** 2025-09-13
**Owners:** Engineering
**Stakeholders:** Solo operator/investor; Engineering (rate-limit & reliability)&#x20;
**Related:** DESIGN\_DOC (limits/breakers, chaos/soak); SLOs (success rate, latency, MTTR) &#x20;

## Summary

Define first-class provider budgets and an adaptive rate-limit policy for CoinGecko, Etherscan, mempool.space, and FX sources; expose counters and breaker state via `/metrics`; add Operator Console controls for overrides. Defaults and adaptive behavior align to the blueprint’s “Providers & Budgets” and Operator Console requirements.&#x20;

## Motivation

PRD KPIs target p95 250 ms (API), 900 ms (candles), 1.2 s (portfolio), 24h success ?99.5%, cache hit ?70%, and breaker MTTR ?5 min. Resilience under free-tier limits/outages is a core goal; formalizing budgets + adaptive clamps is necessary to hit these KPIs and to make reliability operator-controllable.&#x20;

## Guide-level Explanation

* **What changes for users (operators):**
  *View live budgets, 429 rates, breaker state, cache TTLs; edit budgets within clamped bounds; open/close breakers with confirm; honor `Retry-After`; system freezes on 403 bans; soak/chaos behavior visible in `/metrics` and traces.*&#x20;
* **Default provider ceilings (initial):** CoinGecko `{per_min:30, per_sec:5}`; Etherscan `{per_sec:5, per_day:100000}`; mempool.space `{per_sec:1}`; FX `{per_min:10}`.&#x20;
* **Adaptive policy:** clamps min 50% / max 100% of ceilings; step 10%; cooldown 60 s; hysteresis 2×; honor `Retry-After`; freeze on 403; half-open probes gate recovery.&#x20;

## Reference-level Explanation

### A) Rate-limit primitives

* **Token buckets (Redis):** one bucket per `{provider, route}`; refill rates derive from *current clamp × default ceiling*. On Redis outage, fall back to in-process leaky-bucket (default-deny) until healthy; downgrade/upgrade events are logged.&#x20;
* **Circuit breakers:** open on sustained 429/5xx; half-open with probes; closed on success. Operator can force open/close (confirm).&#x20;

### B) Defaults & clamps

* **Defaults:** CoinGecko `{per_min:30, per_sec:5}`; Etherscan `{per_sec:5, per_day:100000}`; mempool.space `{per_sec:1}`; FX `{per_min:10}`.
* **Clamp algorithm:** start at 100%; on burn > threshold, decrement 10% steps to min 50%; recover upward by 10% after cooldown if error rate normal; apply 2× hysteresis to avoid flapping. Honor `Retry-After` window. Freeze all calls on HTTP 403.&#x20;

### C) Metrics & observability

* **/metrics** exports RED metrics plus budget/429/breaker counters with exemplars linking to traces (`trace_id`). Logs include `trace_id`/`span_id`. Sampling: head 10%; tail 100% for errors or >1 s spans. SLOs derive from `api.request` traces (p95/p99).  &#x20;

### D) Operator Console

* **Status cards:** budgets, 429 rate, breaker state, cache hit, disk guard, FX drift queue, last backup/drill.
* **Controls:** edit budgets (clamped), open/close breaker (confirm), compactor dry-run, “Use EOD Once” for FX drift.&#x20;

### E) Config keys \[Unverified]

* `PROVIDER_BUDGETS_JSON`, `ADAPTIVE_CLAMP_MIN/MAX/STEP`, `ADAPTIVE_COOLDOWN_SEC`, `ADAPTIVE_HYSTERESIS_FACTOR`, `BREAKER_PROBE_INTERVAL_SEC`.
  *I cannot verify these exact key names from your inputs.* \[Unverified]

### F) Migration plan

1. **Introduce config** with defaults above; wire token buckets + breaker; expose `/metrics` counters.
2. **Enable Operator controls** behind a feature flag; confirm dialogs in UI.
3. **Run chaos/soak** at 80% ceilings; validate MTTR \~5 min; verify burn handling; confirm no forward-fill introduced.&#x20;
4. **SLO wiring:** trace-derived p95/p99 + success rate alerts; add fast/slow burn alerts per SLOs.&#x20;

## Drawbacks

* **Throughput trade-off:** clamps reduce peak throughput under stress.
* **Operational complexity:** more controls to manage.
* **Breaking changes:** aggressive “freeze on 403” halts provider calls until manual/automatic recovery; stricter default-deny during Redis outage may degrade features temporarily.&#x20;

## Alternatives

* **Static budgets only** (no adaptive clamps): simpler but slower recovery and higher 429 risk.
* **Backoff-only strategy** (no explicit budgets): unpredictable under burst; weaker operator control.
* **Provider SDK-native limiters only:** less consistent cross-provider, weaker shared observability.

## Unresolved Questions

* **Tier-specific ceilings per account/plan:** exact paid/free provider ceilings beyond the listed defaults remain incomplete. *I cannot verify this from your inputs.* \[Unverified]&#x20;
* **Final config key names & env schema:** \[Unverified].
* **Stakeholder roster for required reviewers:** add names/roles in CODEOWNERS once defined. \[Unverified]