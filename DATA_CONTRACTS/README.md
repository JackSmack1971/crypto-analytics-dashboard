### /docs/DATA\_CONTRACTS/README.md

# Data Contracts — Crypto Analytics Dashboard (MVP)

## Schema Index

* **Asset Registry** — `registry/assets.json` (JSON; authoritative; semver + checksum). **Owner:** Engineering. **Version:** semver \[Unverified]. **Notes:** seeds SQLite; no runtime mutation.&#x20;
* **Transactions CSV v1.1** — `DATA_CONTRACTS/schemas/transactions.v1.1.schema.json` (JSON Schema for CSV rows). **Owner:** Engineering. **Version:** 1.1. **Notes:** UUIDv7 ids; idempotency keys; FEE normalization.&#x20;
* **Price/FX Annotation** — `DATA_CONTRACTS/schemas/price_fx.annotation.schema.json` (JSON). **Owner:** Engineering. **Version:** 1.0 \[Unverified]. **Notes:** persist `price_source,resolution,asof,fx_source,fx_rate`; drift guard flags.&#x20;
* **Candles/Snapshots** — `DATA_CONTRACTS/schemas/candle.row.schema.json` and `snapshot.row.schema.json` (Parquet row JSON Schema). **Owner:** Engineering. **Version:** 1.0 \[Unverified]. **Notes:** partitions `dt=YYYY-MM-DD/asset_id=…`.&#x20;

> ID policy across contracts: **UUIDv7**. API uses hyphenated strings; DB uses 16-byte UUID/BLOB.&#x20;

---

## Entity Schemas

### A) Asset Registry (`registry/assets.json`)

Authoritative, JSON-first registry used to seed the DB at boot; immutable at runtime. Entities: `chains`, `assets`, `asset_contracts`, `asset_provider_ids`, `asset_aliases`. Semver + checksum required.&#x20;

```json
{
  "$id": "DATA_CONTRACTS/schemas/asset.registry.schema.json",
  "type": "object",
  "required": ["version", "checksum", "chains", "assets"],
  "properties": {
    "version": { "type": "string", "description": "semver (x.y.z) [Unverified exact]" },
    "checksum": { "type": "string" },
    "introduced_in": { "type": "string" },
    "deprecated_in": { "type": "string" },
    "chains": { "type": "array", "items": { "type": "object" } },
    "assets": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["asset_id"],
        "properties": {
          "asset_id": { "type": "string", "description": "opaque id used across system" },
          "aliases": { "type": "array", "items": { "type": "string" } },
          "provider_ids": { "type": "object" },
          "contracts": { "type": "array", "items": { "type": "object" } },
          "introduced_in": { "type": "string" },
          "deprecated_in": { "type": "string" },
          "deprecation_status": { "type": "string" },
          "superseded_by": { "type": "string" }
        }
      }
    }
  }
}
```

*Migration SOP (N/N+1 dry-run; fail on breaking diffs without a major bump) is mandatory.*&#x20;

### B) Transactions CSV v1.1 (row schema)

Columns and semantics are fixed by v1.1; FEE rows are normalized; transfers move lots and produce **no P\&L**; idempotency via declared keys.&#x20;

```json
{
  "$id": "DATA_CONTRACTS/schemas/transactions.v1.1.schema.json",
  "type": "object",
  "required": ["id","timestamp","action","asset_id","quantity","account"],
  "properties": {
    "id": { "type": "string", "format": "uuid", "description": "UUIDv7" },
    "timestamp": { "type": "string", "format": "date-time", "description": "UTC ISO" },
    "action": { "type": "string", "enum": ["BUY","SELL","TRANSFER_IN","TRANSFER_OUT","FEE","STAKING_REWARD","AIRDROP","INCOME"] },
    "asset_id": { "type": "string" },
    "quantity": { "type": "number" },
    "unit_price_usd": { "type": ["number","null"] },
    "fee_asset": { "type": ["string","null"] },
    "fee_amount": { "type": ["number","null"] },
    "account": { "type": "string" },
    "wallet": { "type": ["string","null"] },
    "venue": { "type": ["string","null"] },
    "tx_hash": { "type": ["string","null"] },
    "external_id": { "type": ["string","null"] },
    "notes": { "type": ["string","null"] }
  },
  "x-idempotency": {
    "oneOf": [
      { "required": ["account","tx_hash"] },
      { "required": ["external_id"] },
      { "required": ["id"] }
    ]
  }
}
```

*Operational rule:* include a negative-qty **FEE** row for fees and preserve acquisition dates on transfers.&#x20;

### C) Price/FX Annotation

Persist alongside valuations and snapshots.&#x20;

```json
{
  "$id": "DATA_CONTRACTS/schemas/price_fx.annotation.schema.json",
  "type": "object",
  "required": ["price_source","resolution","asof"],
  "properties": {
    "price_source": { "type": "string" },
    "resolution": { "type": "string", "enum": ["5m","1h","1d"] },
    "asof": { "type": "string", "format": "date-time" },
    "fx_source": { "type": ["string","null"] },
    "fx_rate": { "type": ["number","null"] },
    "drift_bps": { "type": ["number","null"] },
    "flags": { "type": "array", "items": { "type": "string", "enum": ["DELAYED_FX"] } }
  }
}
```

*Granularity policy (no forward fill) and drift guard apply.*&#x20;

### D) Candle/Snapshot Rows (Parquet)

Partitioned path convention: `dt=YYYY-MM-DD/asset_id=…`; row-group targets set via profile; compactor respects RAM watermarks. **Schema fields:** `t,o,h,l,c,v,resolution,asof`. \[Unverified exact Parquet field types]&#x20;

---

## Events Schemas

No domain events are defined in provided inputs. *I cannot verify any event subjects or payloads from your inputs.* **\[Unverified]**

---

## Fixtures

* `DATA_CONTRACTS/fixtures/transactions.v1.1.sample.csv` — minimal happy-path + FEE + transfers **\[Unverified content]**. (Validates against row schema above.)&#x20;
* `DATA_CONTRACTS/fixtures/asset.registry.sample.json` — small chain/asset set with semver/checksum **\[Unverified content]**.&#x20;
* `DATA_CONTRACTS/fixtures/candles.sample.parquet` — partitioned by `dt/asset_id` **\[Unverified content]**.&#x20;

---

## Validation Rules

1. **Registry Semver & Dry-Run:** `N/N+1` dry-run must emit a migration plan (SQL + alias rewrites) and **fail on breaking diffs without a major bump**.&#x20;
2. **Transactions v1.1:** enforce column set & enums; timestamp must be UTC ISO; ids **UUIDv7**; apply idempotency keys; **FEE** rows normalized; **transfers do not affect P\&L**.&#x20;
3. **Price/FX:** persist `{price_source,resolution,asof}` and `{fx_source,fx_rate}` when used; if `drift_bps > 25` from fallback vs latest intraday USD, flag `DELAYED_FX` and hold NAV until operator override (“Use EOD Once”).&#x20;
4. **Partitions:** Parquet paths must follow `dt=YYYY-MM-DD/asset_id=…`; profiles control row-group size; compactor caps in-flight memory and spills when near cap.&#x20;
5. **Classification/PII:** CSV inputs and Parquet analytics are **Confidential**; no PII fields expected; tag PII explicitly if later introduced.&#x20;

---

*Reasoning Summary:* Built a CI-ready contracts index and minimal schemas strictly from the blueprint: asset registry (JSON, semver), transactions CSV v1.1 (UUIDv7, idempotency, FEE/transfer rules), price/FX annotations (drift guard), and Parquet partitioning. Events are not defined ? marked **\[Unverified]**.

---