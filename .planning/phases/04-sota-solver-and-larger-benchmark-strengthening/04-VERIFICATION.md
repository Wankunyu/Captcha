---
phase: 04-sota-solver-and-larger-benchmark-strengthening
verified: 2026-05-19T15:17:27Z
status: passed
score: "12/12 must-haves verified"
overrides_applied: 0
---

# Phase 4: SOTA Solver and Larger Benchmark Strengthening Verification Report

**Phase Goal:** Researchers can make fair, labeled comparisons between local COGNITION results, Halligan, Oedipus, other specialized solver baselines, and larger external datasets when artifacts are compatible.
**Verified:** 2026-05-19T15:17:27Z
**Status:** passed
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Researcher can create a benchmark coverage matrix mapping local CAPTCHA families to Halligan, Oedipus, reviewer-cited larger datasets, and specialized solver baselines. | VERIFIED | `baseline_strengthening.py` implements `coverage`; `baseline_sources/phase4_baseline_sources.json` contains Halligan, Oedipus, VTTSolver, and PhishDecloaker rows with `external_task_label`, `mapped_local_task_type`, and `mapped_local_family`; tests assert default `coverage_matrix.csv/json` outputs and named-system presence. |
| 2 | Baseline comparison rows distinguish solver architecture, threat model, dataset scale, CAPTCHA families, reported metrics, artifact availability, latency/cost coverage, failure-mode analysis, and defense-methodology relevance. | VERIFIED | `BaselineCoverageRow` requires these fields before any coverage row can be written; `BaselineComparisonRow` preserves metric/status/class fields and source URL; seed rows populate the required coverage/provenance fields. |
| 3 | Rows are labeled as direct-run, adapter-run, literature-only, approximate, incompatible, or unavailable. | VERIFIED | `ALLOWED_PRIMARY_STATUSES` defines the six locked labels; validators reject unknown labels; tests cover all six statuses. |
| 4 | External baseline or larger-dataset imports validate fields, metric definitions, task labels, sample counts, and comparability assumptions before paper-ready outputs. | VERIFIED | `build_external_import_validation_rows` validates required fields, metric definitions, task labels, sample counts, license/data-use, and comparability; `build_baseline_comparison_rows` only normalizes and marks direct comparability when all import statuses pass. |
| 5 | Researcher can run or import at least one smoke subset for a compatible larger external benchmark or baseline comparison when artifacts are available and feasible. | VERIFIED | Validated import is the accepted Phase 4 smoke path. Tests validate two Halligan smoke labels, `arkose/dice_match` and `OpenCaptchaWorld/Hold_Button`, and the full offline CLI chain. |
| 6 | Paper-ready baseline tables separate off-the-shelf MLLM API results from specialized solver results and document dataset or threat-model differences. | VERIFIED | `system_class` is a required, validated field on coverage, comparison, and paper rows; allowed classes include `off_the_shelf_mllm_api`, `specialized_solver`, `benchmark_dataset`, and `hybrid_or_unknown`; caveat tags and comparability notes preserve dataset/threat-model differences. |
| 7 | Researchers can validate Phase 4 baseline coverage, import diagnostics, comparison, and paper-table rows before paper output is generated. | VERIFIED | `phase4_artifacts.py` defines strict Pydantic models and writer wrappers for all four artifact types; `build-table` validates through `BaselineComparisonRow` and `PaperBaselineRow` before writing outputs. |
| 8 | Every baseline row carries a primary status, system class, caveat fields, source/audit fields, and direct-comparability controls. | VERIFIED | Required schema fields include `primary_status`, `system_class`, `caveat_tags`, `checked_sources`, `missing_items`, `last_checked_date`, `directly_comparable`, and comparability note/caveat fields; validators require visible notes for non-comparable rows. |
| 9 | Unverified or non-comparable evidence cannot be silently promoted to directly comparable paper evidence. | VERIFIED | Blocking caveats, literature-only/approximate status, failed import validation, or missing diagnostics force `directly_comparable=False` and leave `normalized_success_rate=None`; tests assert literature-only and failed-sample rows remain non-comparable. |
| 10 | Coverage generation includes Halligan and Oedipus even when rows are literature-only, incompatible, or unavailable, and bounds secondary systems. | VERIFIED | `validate_coverage_rows` and `_load_baseline_coverage_artifact` require Halligan and Oedipus and cap secondary systems at two; tests reject missing Oedipus and excessive secondary systems. |
| 11 | The first smoke/import target remains Halligan or Oedipus unless the user explicitly confirms replacement. | VERIFIED | `build_external_import_validation_rows` rejects secondary smoke replacement when no named Halligan/Oedipus row validates unless `user_confirmed_replacement=true`; tests cover both rejection and explicit confirmation. |
| 12 | Concise Phase 4 notes summarize direct/adapter/literature-only rows, unavailable/incompatible rows, non-comparable rows, and approximate comparison basis. | VERIFIED | `render_baseline_notes` and `write_baseline_notes` generate `baseline_notes.md` with `Status Counts`, `Unavailable And Incompatible Evidence`, `Non-Comparable Rows`, and `Approximate Comparison Basis`; tests verify headings and secret-safe content. |

**Score:** 12/12 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `phase4_artifacts.py` | Strict Pydantic schemas and CSV/JSON writer wrappers for Phase 4 artifacts | VERIFIED | Exists, 413 lines, defines four schema constants, allowed vocabularies, four row models, list-safe CSV serialization, JSON writers, and strict `extra="forbid"` validation. |
| `baseline_strengthening.py` | Central offline CLI with coverage, validate-import, build-table, and notes subcommands | VERIFIED | Exists, 748 lines, imports Phase 4 row models/writers, uses `revision_run_dir`, validates coverage/import artifacts, rejects duplicate import source keys, and writes expected outputs. |
| `baseline_sources/phase4_baseline_sources.json` | Offline seed metadata for Halligan, Oedipus, VTTSolver, and PhishDecloaker | VERIFIED | Contains five rows: two Halligan smoke/import labels, Oedipus literature-only row, and two Halligan-tied secondary systems. No credential fields were found. |
| `tests/test_phase4_artifacts.py` | Offline schema, enum, caveat, writer, and serialization tests | VERIFIED | Exists, 328 lines. Tests schema versions, extra-field rejection, vocabularies, audit/license constraints, visible non-comparability notes, metric preservation, and JSON-serialized CSV list fields. |
| `tests/test_baseline_strengthening.py` | Offline CLI and full-chain regression tests | VERIFIED | Exists, 577 lines. Tests coverage, import validation, replacement gate, paper table generation, notes, full CLI chain, stale coverage rejection, duplicate source-key rejection, and secret-safe summaries. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `phase4_artifacts.py` | `tests/test_phase4_artifacts.py` | Pydantic model validation and writer wrappers | VERIFIED | `gsd-sdk query verify.key-links` passed for Plan 04-01; tests import all row models and writer wrappers. |
| `baseline_strengthening.py` | `phase4_artifacts.py` | Imports row models and writer wrappers | VERIFIED | `baseline_strengthening.py` imports `BaselineCoverageRow`, `ExternalImportValidationRow`, `BaselineComparisonRow`, `PaperBaselineRow`, and all writer wrappers. |
| `baseline_sources/phase4_baseline_sources.json` | `baseline_strengthening.py coverage` | `--source-metadata` and default source path | VERIFIED | Manual check confirms `DEFAULT_SOURCE_METADATA = Path("baseline_sources/phase4_baseline_sources.json")`, `coverage --source-metadata`, and tests using metadata fixtures. |
| `coverage_matrix.json` | `baseline_comparison.json` | `build-table` | VERIFIED | `_run_build_table` loads coverage JSON through `_load_baseline_coverage_artifact`, validates rows, builds comparison rows, and writes `baseline_comparison.csv/json`; full-chain test verifies output files. |
| `baseline_comparison.json` | `paper_baseline_table.json` | `PaperBaselineRow` validation | VERIFIED | `build_paper_baseline_rows` converts validated comparison rows into `PaperBaselineRow` objects before `write_paper_baseline_table`; full-chain test verifies required paper fields. |
| `paper_baseline_table.json` | `baseline_notes.md` | `notes` | VERIFIED | `_run_notes` loads `PaperBaselineRow` payloads and calls `write_baseline_notes`; tests verify `baseline_notes.md` headings and non-comparable row content. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `baseline_strengthening.py coverage` | `rows` / `coverage_rows` | Local JSON/CSV source metadata via `_read_table`, defaulting to `baseline_sources/phase4_baseline_sources.json` | Yes - validates five seed metadata rows and writes coverage CSV/JSON | VERIFIED |
| `baseline_strengthening.py validate-import` | `import_rows` / diagnostics rows | Local CSV/JSON import rows plus validated coverage artifact | Yes - builds `ExternalImportValidationRow` diagnostics and records pass/fail statuses | VERIFIED |
| `baseline_strengthening.py build-table` | `comparison_rows` / `paper_rows` | Validated coverage JSON and import diagnostics JSON | Yes - joins by stable source key, rejects duplicates, preserves metrics, and writes comparison/paper table artifacts | VERIFIED |
| `baseline_strengthening.py notes` | `paper_rows` / `import_rows` | Validated paper table JSON and optional import diagnostics JSON | Yes - renders status counts, non-comparable rows, unavailable/incompatible evidence, and approximate basis | VERIFIED |
| `phase4_artifacts.py` writers | Validated row models | Pydantic model instances or dict rows | Yes - validates rows before writing schema-versioned CSV/JSON payloads | VERIFIED |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Focused Phase 4 regression tests | `uv run pytest tests/test_phase4_artifacts.py tests/test_baseline_strengthening.py -q` | 21 tests passed | PASS |
| Full local test suite | `uv run pytest -q` | 150 tests passed; only existing matplotlib/pyparsing deprecation warnings | PASS |
| Lint changed Phase 4 files | `uv run ruff check phase4_artifacts.py baseline_strengthening.py tests/test_phase4_artifacts.py tests/test_baseline_strengthening.py` | All checks passed | PASS |
| Schema drift validation | `gsd-sdk query verify.schema-drift 04` | `valid: true`, `issues: []`, `checked: 3` | PASS |
| CLI help surfaces | `uv run python baseline_strengthening.py coverage --help`; `validate-import --help`; `build-table --help`; `notes --help` | All four help commands exited successfully | PASS |
| Review-warning closure commit | `git show --stat --oneline fb50097` | Commit `fb50097 fix(04-03): resolve baseline review warnings` changed `baseline_strengthening.py`, `phase4_artifacts.py`, and tests | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| BASE-01 | 04-01, 04-02 | Researcher can create a benchmark coverage matrix mapping local CAPTCHA families to reviewer-cited larger datasets and specialized solver baselines. | SATISFIED | Coverage rows include external labels, mapped local task/family fields, Halligan/Oedipus/secondary systems, and default `coverage_matrix.csv/json` outputs. |
| BASE-02 | 04-02, 04-03 | Baseline comparison rows include Halligan, Oedipus, and other relevant dedicated CAPTCHA solver or benchmark systems where available. | SATISFIED | Seed metadata includes Halligan, Oedipus, VTTSolver, and PhishDecloaker; validation requires Halligan/Oedipus and caps secondary systems at two. |
| BASE-03 | 04-01, 04-02, 04-03 | Each baseline row distinguishes architecture, threat model, dataset scale, families, metrics, artifacts, latency/cost, failures, and defense relevance. | SATISFIED | `BaselineCoverageRow` requires all listed fields and seed rows populate them with source/audit values. |
| BASE-04 | 04-01, 04-02, 04-03 | Baseline comparisons label each row as direct-run, adapter-run, literature-only, approximate, incompatible, or unavailable. | SATISFIED | Locked `ALLOWED_PRIMARY_STATUSES` and tests enforce the six labels. |
| BASE-05 | 04-01, 04-02, 04-03 | External baseline or larger-dataset imports validate required fields, metric definitions, task labels, sample counts, and comparability assumptions before paper-ready outputs. | SATISFIED | Import diagnostics validate those fields; comparison rows only use normalized rates and direct-comparability when all statuses pass. |
| BASE-06 | 04-02, 04-03 | Framework can run or import at least one smoke subset for a compatible larger external benchmark or baseline comparison when feasible. | SATISFIED | Validated import path accepts Halligan smoke rows for `arkose/dice_match` and `OpenCaptchaWorld/Hold_Button`; direct Halligan execution remains intentionally out of scope without Docker/Pixi/user approval. |

No Phase 4 requirement IDs were orphaned: the union of PLAN frontmatter requirements is BASE-01 through BASE-06, matching `.planning/REQUIREMENTS.md`.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | - | No blocking TODO/FIXME/placeholders, stub returns, provider calls, browser automation, Docker/Pixi execution, or secret-reading path found in Phase 4 files. | None | Phase 4 remains offline and local-file based. |

Safety-boundary scan notes:

- `secrets.yaml`, environment-variable credential access, provider construction, `requests`/`httpx`/network clients, Selenium/Playwright/browser automation, Docker/Pixi execution, and subprocess execution were not introduced in the reviewed files.
- Literal `secret` hits are negative test assertions or invalid-vocabulary fixtures, not secret reads or outputs.
- Literal `live service automation` appears only in `data_use_constraints` text prohibiting live-service automation.
- `baseline_strengthening.py` has benign parser fallbacks returning empty lists for optional inputs; these do not flow to paper evidence without validation.

### Human Verification Required

None. This phase produces offline schemas, CLIs, CSV/JSON artifacts, and Markdown notes. There is no UI, live service, external provider integration, browser automation, or performance behavior requiring human testing for goal achievement.

### Gaps Summary

No blocking gaps found. All roadmap success criteria, PLAN must-haves, required artifacts, wiring, data flow, requirements coverage, review-warning fixes, and safety constraints are verified.

Non-blocking note: `gsd-sdk query roadmap.analyze --raw` reports Phase 4 `disk_status: complete` but `roadmap_complete: false`; the roadmap phase detail lists all three Phase 4 plans complete. This is project-progress metadata lag, not a Phase 4 goal-achievement gap.

---

_Verified: 2026-05-19T15:17:27Z_
_Verifier: Codex (gsd-verifier)_
