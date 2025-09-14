### /docs/ADRs/0001-uuidv7-ids.md

# ADR-0001 — UUIDv7 for Internal IDs

**Status:** Accepted.
**Decided:** \[Unverified]
**Related:** \[ADR-0002 — Valuation Policy \[Unverified]]\(../ADRs/0002-valuation-policy.md), [ADR-0003 — Backups & Tracing (Pack A)](../ADRs/0003-backups-tracing-pack-a.md)&#x20;

## Context

The project is a local-first, single-user crypto analytics dashboard (Next.js UI, FastAPI BFF, Python worker). IDs are specified as **UUIDv7** in the executive summary and in Identity & Data Contracts. &#x20;

## Decision

Adopt **UUIDv7** as the global ID scheme:

* **API:** hyphenated UUID strings
* **DB:** 16-byte UUID/BLOB
* **Files:** may prefix `YYYY-MM-DD/` in paths where appropriate
  Marked **ADR-0001: ACCEPTED** in the blueprint.&#x20;

## Consequences

* **Uniformity across interfaces:** API, DB, and file conventions align with the blueprint’s data contracts.&#x20;
* **CSV contract parity:** Transactions CSV v1.1 uses `id(uuidv7)`, keeping ingestion/idempotency consistent with the system’s ID policy.&#x20;
* **Documentation & tests:** ADR presence (0001/0002/0003) is part of MVP acceptance, so this ADR must ship and stay in sync with schemas and fixtures.&#x20;

---