### /docs/SUPPLY\_CHAIN.md

# SUPPLY\_CHAIN — Crypto Analytics Dashboard (MVP)

> Scope: CI-enforceable supply-chain controls derived strictly from provided inputs. Any missing facts are tagged **\[Unverified]** with explicit abstention: “I cannot verify this from your inputs.”

## SLSA Targets

* **Objective:** Ensure verifiable build provenance and artifact integrity for every merge and tagged release.
* **Target level:** **\[Unverified]** — *I cannot verify an intended SLSA level from your inputs.*
* **Controls already mandated by the blueprint/docs (mapped to SLSA intent):**

  * **SBOM generation (Syft) + SCA gates (`pip-audit`, `npm audit`).** &#x20;
  * **Secret-scan gate (Gitleaks).**&#x20;
  * **Releases cut from signed SemVer tags; CI-protected default branch.**&#x20;
  * **Contract validation gates (OpenAPI / JSON Schemas / event conformance) to prevent drift.**&#x20;
* **CI hook (required):** `SLSA attest verify on CI` (job must fail the build if provenance is missing or invalid). \[Policy hook from filetype]

## Provenance

* **Source provenance (code):**

  * **Signed tag + commit SHA** captured for each release. **Builder identity / runner trust** — **\[Unverified]**.&#x20;
* **Artifact provenance (data & backups):**

  * **Backups** package Parquet and emit `manifest.json` with file checksums; weekly **restore drill** produces a report artifact.&#x20;
  * **Asset Registry** is semver’ed with **checksum**; **N/N+1 dry-run** fails on breaking diffs without a major bump. &#x20;
* **Publication & retention:** *SBOM on tag; store scan reports (SCA, Gitleaks) as CI artifacts.* **\[Unverified storage location/tools]**.&#x20;

## Hermetic Builds

> Goal: deterministic, reproducible builds with controlled inputs.

* **Dependency pinning / lockfiles present and verified in CI** — **\[Unverified]** (“I cannot verify this from your inputs”).
* **No network during build (allowlist only) & vendored caches** — **\[Unverified]**.
* **Base images/toolchains pinned by digest** — **\[Unverified]**.
* **Reproducibility checks (rebuild ? byte-identical)** — **\[Unverified]**.
* **Note:** current inputs only mandate SCA/SBOM/secret-scan and signed-tag releases; hermeticity specifics are not defined.  &#x20;

## Attestations

* **To emit (artifacts)**

  * **SLSA provenance attestation** for each build/release — **\[Unverified format/tool]**.
  * **SBOM (Syft)** attached on tag; **diff across releases** — **\[Unverified diff job]**.&#x20;
  * **SCA reports:** `pip-audit`, `npm audit`.&#x20;
  * **Secret-scan report:** **Gitleaks**.&#x20;
  * **Contract conformance:** OpenAPI validation, JSON-Schema validation (CSV v1.1 / Registry / Price-FX), Events conformance (if emitting).&#x20;
  * **Backup integrity artifacts:** `manifest.json` checksums, `drill_report.json`.&#x20;
* **Verification steps (CI)**

  1. **Run `SLSA attest verify`** ? fail build on missing/invalid provenance. \[Required hook]
  2. **Generate SBOM (Syft)** ? upload as artifact; **optional diff vs previous tag** — **\[Unverified job]**.&#x20;
  3. **Execute SCA gates** (`pip-audit`, `npm audit`) ? block on severity thresholds **\[Unverified thresholds]**.&#x20;
  4. **Run Gitleaks secret-scan** ? block on any finding.&#x20;
  5. **Validate public contracts** (OpenAPI / JSON Schemas / Events) ? block on drift.&#x20;
  6. **Backup verify job** (`make backup.verify`) ? assert checksums + sample scans; ensure latest **restore drill** artifact exists.&#x20;

---

*Reasoning Summary:* Built a CI-ready supply-chain policy strictly from the blueprint: SBOM via Syft, SCA (`pip-audit`, `npm audit`), Gitleaks, signed-tag releases, contract validation gates, and backup integrity artifacts. SLSA level, hermetic-build specifics, and attestation formats/tools are **\[Unverified]** by inputs and explicitly abstained.

---

### /docs/\_meta/SUPPLY\_CHAIN.meta.json

{
"version": "1.0",
"doc": "SUPPLY\_CHAIN.md",
"status": "Draft",
"ci\_hooks": \["SLSA attest verify on CI"],
"quality\_checklist": \["Build provenance documented", "Artifact verification steps"],
"open\_questions": \[
"Which SLSA level is targeted and by when? \[Unverified]",
"What attestation format/tooling is mandated (e.g., predicate type, signer)? \[Unverified]",
"Are hermetic-build requirements (lockfiles, network policy, base image digests) in scope for MVP? \[Unverified]",
"Where are SBOM/SCA/Gitleaks artifacts stored and how long are they retained? \[Unverified]"
],
"assumptions": \[],
"sources": \["PROJECT\_BLUEPRINT.md"],
"techniques": \["Role Prompting","Decomposition","Structured Output","Eliciting Abstention","Self-Correction"]
}
