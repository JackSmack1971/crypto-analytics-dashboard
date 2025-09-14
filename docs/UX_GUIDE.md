### /docs/UX\_GUIDE.md

# UX\_GUIDE — Crypto Analytics Dashboard (MVP)

> Scope: UI conventions for this local-first app. Content is derived strictly from the provided blueprint and docs. Visual identity values (palette, typography) are not defined in your inputs and are tagged **\[Unverified]**. Operator Console requirements, capabilities gating, offline banner, FX drift guard, rate-limit/breaker controls, compactor/disk guard, and backup/drill status all come from the blueprint.

## Tokens

> Authoritative token keys (values **\[Unverified]**). Keep a single JSON at `ui/tokens.json`; CI checks **key parity** with this section.

```json
{
  "color": {
    "brand": { "primary": "[Unverified]", "surface": "[Unverified]" },
    "text": { "primary": "[Unverified]", "secondary": "[Unverified]", "inverse": "[Unverified]" },
    "bg": { "default": "[Unverified]", "muted": "[Unverified]", "elevated": "[Unverified]" },
    "border": { "default": "[Unverified]" },
    "status": {
      "ok": "[Unverified]",
      "warn": "[Unverified]",
      "critical": "[Unverified]",
      "info": "[Unverified]"
    }
  },
  "space": { "0": 0, "1": "[Unverified]", "2": "[Unverified]", "3": "[Unverified]", "4": "[Unverified]" },
  "radii": { "sm": "[Unverified]", "md": "[Unverified]", "lg": "[Unverified]", "xl": "[Unverified]" },
  "shadow": { "card": "[Unverified]", "overlay": "[Unverified]" },
  "typography": {
    "font": { "base": "[Unverified]", "mono": "[Unverified]" },
    "size": { "xs": "[Unverified]", "sm": "[Unverified]", "base": "[Unverified]", "lg": "[Unverified]", "xl": "[Unverified]" },
    "weight": { "regular": "[Unverified]", "medium": "[Unverified]", "bold": "[Unverified]" }
  },
  "icon": { "size": { "sm": "[Unverified]", "md": "[Unverified]", "lg": "[Unverified]" } },
  "z": { "nav": 10, "dropdown": 20, "modal": 40, "toast": 50 },
  "motion": {
    "duration": { "fast": "[Unverified]", "base": "[Unverified]", "slow": "[Unverified]" },
    "easing": { "standard": "[Unverified]", "decelerate": "[Unverified]", "accelerate": "[Unverified]" }
  }
}
```

**Notes**

* Use `color.status.*` across Operator Console status cards (budgets/429, breakers, cache, disk guard, FX drift queue, backups/drill). \[Unverified values]
* Respect data classification visually only (no PII/secret badges needed); see Security docs for classification.

## Components

> Core inventory with props, required behaviors, and test anchors. All user-facing timeseries must **not forward-fill**; show `{resolution, asof, source}` provenance where applicable.

1. **Banner.Offline**
   Props: `visible:boolean`, `last_asof?:ISO-8601`
   Behavior: shows when SW reports offline; render last `asof` for user context; disappears on reconnect.
   Test id: `data-testid="banner-offline"`

2. **Banner.FXDriftHold**
   Props: `drift_bps:number`, `override_enabled:boolean`
   Behavior: if `drift_bps > 25`, show hold state and CTA “Use EOD Once” (time-boxed).
   Test id: `data-testid="banner-fx-drift"`
   Source: FX drift guard and override flow.

3. **Banner.DiskGuard**
   Props: `free_gb:number`
   Behavior: warn when low-disk threshold (\~2 GB) is crossed; advise reduced ingest cadence.
   Test id: `data-testid="banner-disk-guard"`

4. **Card.Status (Operator Console)**
   Variants: `providerBudgets`, `breakerState`, `cacheTtl`, `diskUsage`, `fxDriftQueue`, `backupDrill`
   Content rules:

* Budgets: show current clamp % and ceilings; honor min 50% / max 100% / step 10% semantics.
* Breakers: OPEN / HALF\_OPEN / CLOSED with timestamps; link to traces via `trace_id` when present.
* Backup drill: show last `drill_report` status.
  Test id: `data-testid="card-status-<variant>"`

5. **Dialog.BreakerConfirm**
   Props: `provider:string`, `route:string`, `desired:"OPEN"|"CLOSED"`
   Behavior: confirm irreversible action; annotate with current error/429 context; log action with `trace_id`.
   Test id: `data-testid="dialog-breaker-confirm"`

6. **Form.BudgetEditor**
   Props: `provider:string`, `route:string`, `ceilings:{per_sec?:n, per_min?:n, per_day?:n}`, `clamp:number`
   Behavior: clamp edits **must** respect bounds (50–100%) and cooldown/hysteresis notes; reject values outside bounds.
   Test id: `data-testid="form-budget-editor"`

7. **Action.UseEODOnce**
   Behavior: triggers single-use EOD FX override and exposes TTL countdown; disabled if queue empty.
   Test id: `data-testid="action-use-eod-once"`

8. **Uploader.CSV (Transactions v1.1)**
   Behavior: enforce schema/size limits; normalize FEE; transfers keep acquisition dates; show dedupe results.
   States below.
   Test id: `data-testid="uploader-csv"`

9. **Chart.Candles** (+ Indicators MA/RSI/MACD)
   Behavior: never forward-fill; show `{resolution, asof, source}`; respond to 429 by showing a rate-limit state.
   Test id: `data-testid="chart-candles"`

10. **Panel.Portfolio** (NAV/TWR/DD)
    Behavior: provenance and determinism rules mirrored; no P\&L on transfers.
    Test id: `data-testid="panel-portfolio"`

11. **Panel.OnChain.EthGas / BtcMempool**
    Behavior: **capabilities-gated** — if disabled, render informative empty state.
    Test id: `data-testid="panel-eth-gas" | "panel-btc-mempool"`

12. **Logs.Table (Operator Console)**
    Behavior: structured rows with `trace_id` correlation; secret-safe.
    Test id: `data-testid="table-logs"`

## Motion

* Honor `prefers-reduced-motion`; disable non-essential transitions when set. **\[Unverified exact durations/easings]**
* Use **opacity/transform** only; avoid layout-thrashing animations on charts or tables.
* Dialogs and banners may fade/scale subtly; **no continuous or looping** animations in data views.
* Live counters (budgets/429) update discretely; do not animate number ticks.
* Any animation **must not** mask state transitions (e.g., breaker OPEN). Tie announcements to ARIA live regions where applicable **\[Unverified]**.

## States (Empty/Error/Loading)

> Required for key surfaces. Copy is illustrative and can be adjusted without changing logic.

| Surface                     | Empty                                     | Loading (skeleton)                | Error / Exceptional                                                               |
| --------------------------- | ----------------------------------------- | --------------------------------- | --------------------------------------------------------------------------------- |
| Watchlist                   | “No assets yet.” CTA: “Add to watchlist.” | Rows + mini-candles placeholders  | “Couldn’t load watchlist.” Retry.                                                 |
| Asset Detail (Candles)      | “No price history for this interval.”     | Candle grid & axis placeholders   | 429: “Rate limited. Retry after {Retry-After}s.” Breaker OPEN: “Provider paused.” |
| Portfolio                   | “Import a CSV to see NAV/TWR/DD.”         | Metric cards & chart placeholders | “Portfolio unavailable.” Link to logs with `trace_id`.                            |
| Uploader.CSV                | “Drop CSV v1.1 here.”                     | Parse/progress bar                | Schema/size cap: show validation list; quarantine message; dedupe summary.        |
| OnChain.EthGas/BtcMempool   | “Disabled — add keys in env.”             | Gauges/spark placeholders         | `{enabled:false}`: keep disabled state; other errors show retry.                  |
| Operator Console — Budgets  | “No data yet.”                            | Status card placeholders          | “Metrics unavailable.” Show `/metrics` fetch hint.                                |
| Operator Console — Breakers | “All providers healthy.”                  | Status card placeholders          | OPEN: red card with action to **Close** (confirm) or wait for half-open probes.   |
| FX Drift Hold Banner        | —                                         | —                                 | `drift_bps > 25`: show HOLD with **Use EOD Once**; disable button post-use TTL.   |
| Disk Guard Banner           | —                                         | —                                 | Free space < \~2 GB: warn + link “Reduce ingest cadence” info.                    |
| Backups/Drill Status        | “No report yet.”                          | —                                 | Missing nightly backup or weekly drill: show red status with resolution steps.    |
| Offline Banner              | “You’re offline. Showing data as of {t}.” | —                                 | —                                                                                 |

**Accessibility hooks (high level \[Unverified])**

* Banners and breaker changes should announce via ARIA live regions.
* Dialogs trap focus correctly and restore on close.
* Charts provide accessible titles and short textual summaries for screen readers.

---

*Reasoning Summary:* Tokens are enumerated (values **\[Unverified]**). Components and states map 1:1 to the blueprint’s UI and Operator Console requirements: no forward-fill with provenance fields; capabilities gating for on-chain panels; FX drift guard with “Use EOD Once”; rate-limit clamps and breakers; disk guard; backups and weekly restore drill visibility.

### /docs/\_meta/UX\_GUIDE.meta.json

{
"version": "1.0",
"doc": "UX\_GUIDE.md",
"status": "Draft",
"ci\_hooks": \["Design tokens JSON parity check"],
"quality\_checklist": \["Tokens enumerated","States illustrated"],
"open\_questions": \[],
"assumptions": \[],
"sources": \["PROJECT\_BLUEPRINT.md"],
"techniques": \["Role Prompting","Decomposition","Structured Output","Eliciting Abstention","Self-Correction"]
}
