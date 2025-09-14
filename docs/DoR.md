### /docs/DoR.md

# Definition of Ready — Crypto Analytics Dashboard (MVP)

## Entry Criteria

* [ ] **User value stated** (maps to Solo operator/investor job-to-be-done).&#x20;
* [ ] **Scope slices named** (UI, API, Worker, Data) with concrete endpoints/files touched (e.g., `/assets/{asset_id}/candles`, CSV v1.1 import, snapshots/Parquet).&#x20;
* [ ] **Acceptance slices listed** per PRD “User Stories & Acceptance” (copy minimal Given/When/Then).&#x20;
* [ ] **Performance/SLO hooks**: declare expected p95/p99 for impacted routes and how measured from `api.request` traces.&#x20;
* [ ] **Local-first & safety constraints honored**: bind 127.0.0.1, free-tier providers, offline SW cache, strict CORS.&#x20;
* [ ] **Data contracts pinned**: Transactions **CSV v1.1** (UUIDv7, idempotency keys, FEE normalization, transfer=no P\&L), **Asset Registry** (semver + checksum, seed-only), **Price/FX annotation** (no forward fill; drift guard).&#x20;
* [ ] **Observability**: spans taxonomy present; `/metrics` counters to expose RED + budgets/breakers with exemplars; logs carry `trace_id`.&#x20;
* [ ] **Reliability rails**: rate-limit policy acknowledges 429 + `Retry-After`; breakers/half-open; adaptive clamps; freeze on 403.
* [ ] **Backups/restore drills** impact assessed if data written; artifacts/verify steps referenced.&#x20;
* [ ] **Operator Console touchpoints** enumerated (budgets edit, breaker toggle, compactor dry-run, FX “Use EOD Once”).&#x20;
* [ ] **Security & classification**: localhost-only, secret redaction in logs, CSV hardening; data tagged Confidential where applicable.&#x20;

## Backlog Hygiene

* [ ] **Linked docs**: PRD, DESIGN\_DOC, DATA\_CONTRACTS, INTERFACES, (EVENTS if emitting) attached/PR-referenced.
* [ ] **Public vs Internal** surfaces labeled; changes to Public require OpenAPI/contract updates + CI gates.&#x20;
* [ ] **SLOs impact note**: list affected SLIs (latency, success rate, cache hit, MTTR) and alerting changes if any.&#x20;
* [ ] **Out-of-scope callouts kept** (no internet exposure; news optional/unspecified \[Unverified]).&#x20;
* [ ] **Test strategy pointer** to PRD/Design acceptance & chaos/perf where applicable.&#x20;

## Dependency Checks

* [ ] **Provider ceilings** for CoinGecko/Etherscan/mempool.space/FX confirmed *or* tracked as \[Unverified]; clamp bounds recorded.
* [ ] **Env keys & feature gating**: `/capabilities` behavior defined for missing keys (e.g., ETH gas).&#x20;
* [ ] **Redis available** (token buckets) or fallback plan (in-process leaky bucket default-deny) acknowledged.&#x20;
* [ ] **OTel collector running** locally with sampling policy (head 10%, tail 100% errors/>1s).&#x20;
* [ ] **Storage & compactor**: partitioning `dt=YYYY-MM-DD/asset_id=…`, row-group profile (DEFAULT/LOW\_RAM), RAM watermark 0.65; disk guard thresholds.&#x20;
* [ ] **OpenAPI surfaces** touched enumerated; shapes known or flagged \[Unverified] (see OpenAPI meta open questions).&#x20;
* [ ] **Events transport/retention** if emitting events flagged \[Unverified] and aligned to EVENTS scaffold.&#x20;

---

*(Copy this checklist into the ticket. If any box is unchecked, the item is **Not Ready** and must be tracked as a dependency or split.)*