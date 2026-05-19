---
phase: 03-dataset-scope-statistical-confidence-and-limitations
plan: 01
subsystem: testing
tags: [phase3, dataset-scope, statistics, manifest, csv, json, pydantic]

requires:
  - phase: 02-adaptive-attacker-main-body-evidence
    provides: adaptive artifact contracts, comparison inputs, and failure taxonomy semantics
provides:
  - Strict Phase 3 row schemas and CSV/JSON writers
  - Offline dataset scope audit CLI with removed-task and underpowered-status rows
  - Extended dataset manifest CLI with validation-slice tasks, comparison outputs, and contribution notes
affects: [phase-03-statistical-confidence, phase-04-benchmark-strengthening, paper-claim-ledger]

tech-stack:
  added: []
  patterns:
    - Pydantic ConfigDict(extra="forbid") row contracts
    - revision_artifacts.revision_run_dir default output paths
    - Offline argparse CLIs writing CSV/JSON/Markdown under results/revision/<run_id>/

key-files:
  created:
    - phase3_artifacts.py
    - dataset_scope_audit.py
    - extended_dataset_manifest.py
    - tests/test_phase3_artifacts.py
    - tests/test_dataset_scope_audit.py
    - tests/test_extended_dataset_manifest.py
  modified: []

key-decisions:
  - "Phase 3 schemas live in phase3_artifacts.py so Phase 1 and Phase 2 artifact contracts remain unchanged."
  - "Dataset scope audit counts evaluated evidence only from results/exp1 through results/exp4, excluding error_analysis result files."
  - "Extended-data evidence remains split into original, supplemented-category, and new-category rows with selective validation-slice comparison outputs."

patterns-established:
  - "Phase 3 artifact rows are strict Pydantic models with explicit enum-like validators."
  - "Dataset and manifest CLIs are offline artifact generators and do not construct providers or read local secrets."
  - "Optional validation-slice outcomes can be absent while still producing empty comparison CSV/JSON files with schema metadata."

requirements-completed: [STAT-01, STAT-02, STAT-03]

duration: 11 min
completed: 2026-05-19
---

# Phase 3 Plan 1: Dataset Scope and Extended Manifest Foundation Summary

**Strict Phase 3 artifact schemas plus offline dataset-scope and extended-validation-slice CLIs for reviewer-facing dataset limitation evidence**

## Performance

- **Duration:** 11 min
- **Started:** 2026-05-19T00:44:11Z
- **Completed:** 2026-05-19T00:55:09Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Added strict reusable Phase 3 row schemas for dataset scope, extended manifest, validation comparison, pass-rate confidence, threshold sensitivity, retry calibration, and failure taxonomy.
- Added `dataset_scope_audit.py`, an offline CLI that classifies supported, excluded, incompatible, and underpowered task rows while documenting `Hold_Button(Not Used)` and `Slide_Puzzle(Not Used)` with exact static-pipeline incompatibility reasons.
- Added `extended_dataset_manifest.py`, an offline manifest validator and generator for extended dataset rows, validation-slice task scopes, optional original-vs-slice comparison rows, and contribution notes.
- Added focused pytest coverage for schema strictness, enum rejection, output shape, explicit result filtering, removed-task reasons, new-category limitation rules, comparison statuses, and CLI help.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Phase 3 schema tests** - `109683e` (test)
2. **Task 1 GREEN: Phase 3 artifact schemas** - `1227750` (feat)
3. **Task 2 RED: Dataset scope audit tests** - `edfb185` (test)
4. **Task 2 GREEN: Dataset scope audit CLI** - `edc4fa7` (feat)
5. **Task 3 RED: Extended dataset manifest tests** - `e89a1c7` (test)
6. **Task 3 GREEN: Extended dataset manifest CLI** - `65282a2` (feat)
7. **Task 3 REFACTOR: Lint-safe manifest formatting** - `aa91a79` (refactor)

## Files Created/Modified

- `phase3_artifacts.py` - strict Phase 3 schema constants, row models, enum validators, and shared CSV/JSON writers.
- `dataset_scope_audit.py` - offline dataset audit CLI using `SUPPORTED_TYPES`, `TASK_ALIASES`, `DATASET_DIR_ALIASES`, and `CAPTCHAVisualizer.TASK_FAMILY`.
- `extended_dataset_manifest.py` - offline manifest validator, validation-slice task writer, optional comparison ingestion, and contribution-note generator.
- `tests/test_phase3_artifacts.py` - schema strictness, enum validation, nullable statistical fields, and writer output tests.
- `tests/test_dataset_scope_audit.py` - dataset classification, removed-task reason, result-filtering, output, and CLI tests.
- `tests/test_extended_dataset_manifest.py` - manifest validation, contribution notes, slice tasks, empty comparison, and agreement/divergence tests.

## Verification

- `uv run pytest tests/test_phase3_artifacts.py tests/test_dataset_scope_audit.py tests/test_extended_dataset_manifest.py -q` - passed, 15 tests.
- `uv run ruff check phase3_artifacts.py dataset_scope_audit.py extended_dataset_manifest.py tests/test_phase3_artifacts.py tests/test_dataset_scope_audit.py tests/test_extended_dataset_manifest.py` - passed.
- `uv run python dataset_scope_audit.py --help` - passed.
- `uv run python extended_dataset_manifest.py --help` - passed.

## Decisions Made

- Phase 3 schemas are separated from `adaptive_artifacts.py` to avoid mutating verified Phase 2 adaptive contracts.
- Dataset scope evidence is counted only from explicit experiment directories `exp1`, `exp2`, `exp3`, and `exp4`; recursive `results/error_analysis/**/results.csv` files are intentionally excluded from evaluated evidence.
- Extended dataset rows are validated as selective validation slices and keep original, supplemented-category, and new-category evidence separate.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Robust CSV fallback for sparse optional outcome columns**
- **Found during:** Task 3 (Build extended dataset manifest and contribution-note generator)
- **Issue:** `csv.DictReader` represents missing optional fields as empty strings when a union of outcome columns is present, so `n_attempts` / `n_success` fallback fields were not used for rows that lacked `validation_sample_count` / `success_count`.
- **Fix:** Added a `_first_present()` helper and used it for validation outcome sample/success counts and original conclusion label/rate fallback.
- **Files modified:** `extended_dataset_manifest.py`
- **Verification:** `uv run pytest tests/test_extended_dataset_manifest.py -q`
- **Committed in:** `65282a2`

---

**Total deviations:** 1 auto-fixed (1 bug).
**Impact on plan:** The fix preserves the planned CSV/JSON ingestion contract and improves compatibility with sparse offline outcome files.

## Issues Encountered

- Plan-level pytest passed with pre-existing third-party matplotlib/pyparsing deprecation warnings from importing existing visualization code.
- Initial ruff check found long generated-note source lines; fixed in `aa91a79` without changing behavior.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None. Nullable fields and empty comparison outputs are intentional schema states for absent optional evidence, not placeholder data.

## Threat Flags

None. The new CLIs only read local dataset, manifest, prompt/few-shot, and result artifacts and write local revision outputs; no live-service automation, browser automation, or secret-reading path was introduced.

## Authentication Gates

None.

## TDD Gate Compliance

- Task 1: RED `109683e` followed by GREEN `1227750`.
- Task 2: RED `edfb185` followed by GREEN `edc4fa7`.
- Task 3: RED `e89a1c7` followed by GREEN `65282a2` and REFACTOR `aa91a79`.

## Self-Check: PASSED

- Verified all created source and test files exist.
- Verified `03-01-SUMMARY.md` exists.
- Verified all task commits exist: `109683e`, `1227750`, `edfb185`, `edc4fa7`, `e89a1c7`, `65282a2`, `aa91a79`.

## Next Phase Readiness

Ready for Plan 03-02. The Phase 3 schema module now provides the confidence and threshold-sensitivity row contracts that 03-02 can populate without modifying Phase 1 or Phase 2 artifact schemas.

---
*Phase: 03-dataset-scope-statistical-confidence-and-limitations*
*Completed: 2026-05-19*
