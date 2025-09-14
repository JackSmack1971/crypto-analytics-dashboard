### /docs/INCIDENTS/PROCESS.md

# Incident Process — Crypto Analytics Dashboard (MVP)

> Local-first, single-user stack. Incidents are driven by user-journey SLOs, reliability rails (limits/breakers, **freeze on 403**), FX drift guard, disk guard, and Pack-A backups/restore drills. Runbook: `RUNBOOKS/service-name.md`.

## Severity Matrix

| Sev                  | Criteria (any)                                                                                                                                                                           | Detection Signals                                                             | Initial Actions                                                                                                                | Owner & Target                                          |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------- |
| **Sev-1 (Critical)** | API/UI hard down (`/health` failing) · UJ1/UJ2 unavailable (?50% errors 15m) · Data loss/corruption \[Unverified] · **Freeze on 403** blocks core flows >10m \[Unverified]               | `/health` !ok · Success rate << target · Breaker OPEN, no probes              | Follow **Immediate Checks** in runbook; open breakers only if safe; clamp traffic; verify last **backup**; prepare **restore** | **IC:** API owner · **MTTR:** ASAP                      |
| **Sev-2 (High)**     | Fast SLO burn (>2× budget 1h) \[Unverified] · UJ p99 > target 15m \[Unverified] · Breaker OPEN > **5m** (exceeds MTTR target) · **FX drift hold** >30m or growing queue \[Unverified]    | Trace p95/p99 over targets · `/metrics`: breaker/429 counters; FX drift queue | Reduce clamps (min 50%, step 10%); honor `Retry-After`; half-open probes; consider “**Use EOD Once**” for FX                   | **IC:** API/Worker owner · **MTTR:** ?30m \[Unverified] |
| **Sev-3 (Medium)**   | 429 spikes/oscillating clamps; cache-hit drop \[Unverified] · Low-disk guard (?**2 GB**) engaged · Nightly **backup** missing or **verify** failed · Restore **drill** missing this week | `/metrics`: budgets/429/cache/disk; backup artifacts absent                   | Triage provider budgets; stabilize clamps; free disk; run `make backup.verify`; schedule drill                                 | **IC:** Service owner                                   |
| **Sev-4 (Low)**      | Non-critical panels gated by `/capabilities` · Visual regressions · Offline banner or status card glitches \[Unverified]                                                                 | UI/Console reports; visual tests                                              | File issue; fix-forward behind flag                                                                                            | **IC:** UI owner                                        |

**Notes**

* Promote to higher **Sev** if scope expands or user-journey impact worsens.
* Demote only after SLOs stable for 30m and backlog items filed \[Unverified].

## On-call & Paging

### Roles

* **Incident Commander (IC):** owns comms/flow; may be same person as fixer (solo mode).
* **Ops (Infra):** Redis/OTel/disk guard \[Unverified].
* **Scribe/Comms:** captures timeline, artifacts, updates \[Unverified].

### Paging Triggers

* **Sev-1:** immediate page on `/health` down or UJ failure window reached.
* **Sev-2:** fast burn alert, breaker OPEN >5m, FX drift hold >30m, or UJ p99 breach 15m \[All thresholds \[Unverified]].
* **Sev-3:** disk guard crossed, backup/verify missing, cache-hit collapse \[Unverified].

### Page?Ack?Triage SLA \[Unverified]

1. **Page** (T+0): On-call receives alert (channel \[Unverified]).
2. **Ack** (?5m): IC acknowledges; posts initial severity and scope.
3. **Triage** (?15m): run Runbook **Immediate Checks**; decide mitigations (clamps, breaker toggles, FX override, disk cleanup); log trace IDs and `/metrics` snapshots.

**Runbook cross-refs (local only)**

* `docker compose ps|logs` (service/redis) · `curl 127.0.0.1:PORT/health|capabilities|metrics` · `df -h /data` · `make backup|backup.verify|restore`.

## Comms Templates

> Replace **{…}**. Keep messages terse, factual, and blameless. Include **trace IDs**, `/metrics` excerpts, and Operator Console screenshots where helpful.

### 1) Initial Ack (T+?5m)

```
Incident {INCIDENT_ID} — Ack
Sev: {SEV} | Services: {api|worker|frontend}
Impact: {UJ1/UJ2/UJ3/UJ4} affected — signal {success rate/latency/breaker/FX drift}
Last healthy: {ISO8601}
Next update: T+{30}m
IC: {name}  Scribe: {name [Unverified]}
```

### 2) Status Update (T+?30m)

```
Incident {INCIDENT_ID} — Status
Current state: {breaker OPEN|clamps @60%|FX drift hold|disk guard}
Actions: {reduced clamps to 50%|honoring Retry-After|opened half-open probes|queued Use-EOD-Once}
Metrics: p95/p99 {values}, success {value}%, cache-hit {value}%
ETA next update: T+{30}m
```

### 3) Mitigated/Resolved

```
Incident {INCIDENT_ID} — Resolved
Root cause (provisional): {cause hypothesis}
Fix: {action taken}
Time to mitigate: {min}  Time to resolve: {min}
Follow-ups: {issue IDs} (owner, due {date})
Artifacts: {/metrics snapshot path, trace links, drill_report path}
```

### 4) Customer/Internal Summary (post-incident) \[Unverified channel]

```
Summary for {date}
What happened: {one-liner}
User impact: {UJ + duration}
Why it happened: {brief, blameless}
What we’re doing: {top 3 corrective/preventive actions}
```

## Blameless Postmortems

**Policy**

* **Required:** **Sev ? 2** (CI gate).
* **Optional:** Sev-3 with SLO breach or repeat pattern \[Unverified].
* **Due:** Draft in **48h**, finalized in **5 business days** \[Unverified].

**Template (copy to `/docs/incidents/{YYYY-MM-DD}-{slug}.md`)**

1. **Summary:** one-paragraph plain-language overview.
2. **Impact:** UJs affected, start/end, % errors, latency deltas; screenshots/links to traces and `/metrics`.
3. **Timeline:** T-0 detection ? key actions (UTC ISO with actor).
4. **Root Cause:** technical chain; include breaker/clamp behavior, FX drift, disk guard, backups.
5. **Contributing Factors:** caching gaps, config drift, missing tests, capacity \[Unverified].
6. **Detection & Response:** how detected; page path; where detection can improve.
7. **What Worked / What Didn’t:** specific playbook steps, tooling, comms.
8. **Corrective Actions:**

   * **Immediate Mitigations** (done)
   * **Corrective** (code/config/tests/docs)
   * **Preventive** (alerts, runbooks, drills, budgets)
   * Each with **owner**, **issue ID**, **due date**.
9. **Attachments:** `/metrics` snapshots, trace IDs, Operator Console screenshots, backup `manifest.json`, `drill_report.json`.
10. **Sign-off:** IC + owners \[Unverified].

**CI Rules**

* For **Sev ? 2**, a postmortem file with sections **1–10** must exist before closing the incident.
* Each corrective/preventive action must reference an issue ID and owner.

---

*Reasoning Summary:* Built a minimal, CI-ready incident process from the provided blueprint: SLO targets & MTTR, reliability rails (limits/breakers, `Retry-After`, freeze on 403), FX drift guard with “Use EOD Once,” disk guard threshold, and Pack-A backups/weekly restore drills. Contacts/channels/threshold cadences are **\[Unverified]** where not present in inputs.

---

### /docs/\_meta/PROCESS.meta.json

{
"version": "1.0",
"doc": "INCIDENTS/PROCESS.md",
"status": "Draft",
"ci\_hooks": \["Postmortem required on Sev?2"],
"quality\_checklist": \["Sev definitions testable","Postmortem template ready"],
"open\_questions": \[],
"assumptions": \[],
"sources": \["PROJECT\_BLUEPRINT.md"],
"techniques": \["Role Prompting","Decomposition","Structured Output","Eliciting Abstention","Self-Correction"]
}
