---
phase: 03-dataset-scope-statistical-confidence-and-limitations
plan: 03
subsystem: statistical-evidence
tags: [phase3, retry-calibration, failure-taxonomy, statistics, csv, json]

requires:
  - phase: 02-adaptive-attacker-main-body-evidence
    provides: adaptive summary fields, retry comparison contracts, and failure-class counts
  - phase: 03-dataset-scope-statistical-confidence-and-limitations
    provides: Phase 3 strict row schemas and statistical artifact writer patterns
provides:
  - Offline retry calibration CLI comparing Exp2 Bernoulli Success@k predictions to fixed-retry and adaptive-compatible outcomes
  - Task-family retry calibration summaries with signed/absolute errors and preserved failure counts
  - Offline failure taxonomy CLI separating scientific, protocol, infrastructure, and aggregate-only evidence
  - Raw observed rates, scientific rates, and claim-use caveats for adaptive and retry-derived artifacts
affects: [phase-03-limitations-prose, phase-06-claim-ledger, paper-structural-hardness-claims]

tech-stack:
  added: []
  patterns:
    - Offline argparse CLIs with revision_artifacts.revision_run_dir default output paths
    - Phase 3 strict Pydantic row contracts written through shared CSV/JSON helpers
    - Task-type-primary joins with optional family-level interpretive summaries

key-files:
  created:
    - retry_calibration.py
    - failure_taxonomy.py
    - tests/test_retry_calibration.py
    - tests/test_failure_taxonomy.py
  modified:
    - phase3_artifacts.py

key-decisions:
  - "Retry calibration keeps task type as the primary comparison unit and emits family rows only as interpretive summaries under the same attempt budget."
  - "Failure taxonomy treats adaptive failure-class counts as claim-eligible evidence and marks retry-only legacy rows as aggregate_only_caveated."
  - "Scientific-claim-eligible failure taxonomy rows carry hardness_caveat=None instead of an empty string."

patterns-established:
  - "Phase 3 loaders explicitly read local CSV/JSON artifacts and avoid provider construction, prompt transcripts, and secret configuration."
  - "Infrastructure/provider and protocol failures remain visible counts but are caveated out of structural-hardness evidence."
  - "Default CLI output paths are resolved through revision_run_dir before any output file is created."

requirements-completed: [STAT-06, STAT-07]

duration: 11 min
completed: 2026-05-19
---

# Phase 3 Plan 3: Retry Calibration and Failure Taxonomy Summary

**Retry-calibration and failure-taxonomy artifacts that separate Bernoulli prediction error from scientific, protocol, infrastructure, and aggregate-only evidence**

## Performance

- **Duration:** 11 min
- **Started:** 2026-05-19T01:10:51Z
- **Completed:** 2026-05-19T01:22:03Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added `retry_calibration.py`, an offline CLI that loads only `results/exp2/**/results.csv`, `results/exp3/**/results.csv`, and optional adaptive summary CSV/JSON inputs; it writes task-type and task-family calibration CSV/JSON outputs.
- Added `failure_taxonomy.py`, an offline CLI that emits task-type, task-family, and aggregate-only taxonomy rows with raw observed rates, scientific rates, claim-use labels, and exact caveat strings.
- Added focused pytest coverage for Bernoulli formula reuse, same-k filtering, nullable observations, failure count preservation, raw/scientific rate separation, claim caveats, family aggregation, and run-id path safety.
- Adjusted `FailureTaxonomyRow.hardness_caveat` to allow `None` for scientific-claim-eligible rows, matching the plan's caveat contract.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Retry calibration tests** - `5d86c40` (test)
2. **Task 1 GREEN: Retry calibration artifacts** - `dd87b30` (feat)
3. **Task 2 RED: Failure taxonomy tests** - `ed53abe` (test)
4. **Task 2 GREEN: Failure taxonomy artifacts** - `68dcd46` (feat)

## Files Created/Modified

- `retry_calibration.py` - Loads Exp2, Exp3 fixed-retry, and adaptive-compatible outcomes; computes Bernoulli Success@k, signed/absolute errors, raw/scientific rates, and task-family summaries.
- `failure_taxonomy.py` - Aggregates adaptive summary failure counts into claim-use taxonomy rows and emits aggregate-only caveated retry rows when failure classes are unavailable.
- `tests/test_retry_calibration.py` - Covers retry calibration formulas, joins, nullable observations, counts, family rows, output writing, CLI defaults, and invalid run IDs.
- `tests/test_failure_taxonomy.py` - Covers raw/scientific rates, task-family aggregation, caveat strings, aggregate-only rows, CLI output summaries, and invalid run IDs.
- `phase3_artifacts.py` - Allows `FailureTaxonomyRow.hardness_caveat` to be nullable for scientific-claim-eligible rows.

## Verification

- `uv run pytest tests/test_retry_calibration.py tests/test_failure_taxonomy.py -q` - passed, 12 tests; existing third-party matplotlib/pyparsing deprecation warnings only.
- `uv run ruff check retry_calibration.py failure_taxonomy.py tests/test_retry_calibration.py tests/test_failure_taxonomy.py` - passed.
- `uv run python retry_calibration.py --help` - passed.
- `uv run python failure_taxonomy.py --help` - passed.
- Task-level acceptance `rg` checks for formula reuse, path safety, prediction errors, raw/scientific rates, caveat strings, and claim-use labels all passed.

## Decisions Made

- Retry calibration does not mutate `AdaptiveSummaryRow` or `AdaptiveComparisonRow`; it consumes their fields and writes Phase 3 rows.
- Adaptive-compatible calibration uses the same `attempt_budget_k` as the Bernoulli prediction and exposes fixed/adaptive observations as nullable when matching rows are absent.
- Failure taxonomy gives infrastructure caveats precedence when both infrastructure and protocol failures are present, matching the plan's `infrastructure_failure_count > 0` rule.
- Retry-only rows without failure-class fields are labeled `aggregate_only_caveated` and keep `scientific_rate=None`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Allowed null caveats for scientific-eligible taxonomy rows**
- **Found during:** Task 2 (Aggregate failure taxonomy and claim-use caveats)
- **Issue:** The existing `FailureTaxonomyRow` schema required `hardness_caveat: str`, but the plan requires `hardness_caveat=None` for `scientific_claim_eligible` rows.
- **Fix:** Changed `hardness_caveat` to `str | None = None` in `phase3_artifacts.py` and covered the nullable behavior in `tests/test_failure_taxonomy.py`.
- **Files modified:** `phase3_artifacts.py`, `tests/test_failure_taxonomy.py`
- **Verification:** `uv run pytest tests/test_failure_taxonomy.py -q`
- **Committed in:** `68dcd46`

---

**Total deviations:** 1 auto-fixed (1 bug).
**Impact on plan:** The fix aligns the shared schema with the planned failure-taxonomy contract and does not alter Phase 1 or Phase 2 adaptive schemas.

## Issues Encountered

- `uv run ruff check failure_taxonomy.py phase3_artifacts.py tests/test_failure_taxonomy.py` initially found one unused import in `failure_taxonomy.py`; removed it before the Task 2 GREEN commit.
- Focused pytest commands continue to surface pre-existing third-party matplotlib/pyparsing deprecation warnings from importing existing visualization metadata.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None. Nullable observations, nullable `scientific_rate`, and nullable `hardness_caveat` are intentional evidence states, not placeholders.

## Threat Flags

None. The new CLIs read local CSV/JSON result artifacts only and write local revision outputs; they add no provider calls, browser automation, live-service interaction, auth paths, network endpoints, or secret-reading paths.

## Authentication Gates

None.

## TDD Gate Compliance

- Task 1: RED `5d86c40` followed by GREEN `dd87b30`.
- Task 2: RED `ed53abe` followed by GREEN `68dcd46`.

## Self-Check: PASSED

- Verified all created source and test files exist.
- Verified `03-03-SUMMARY.md` exists.
- Verified all task commits exist: `5d86c40`, `dd87b30`, `ed53abe`, `68dcd46`.

## Next Phase Readiness

Ready for Plan 03-04. Retry-calibration and failure-taxonomy artifacts now provide the machine-readable inputs needed for paper-safe limitations prose, artifact indexing, and claim-ledger work.

---
*Phase: 03-dataset-scope-statistical-confidence-and-limitations*
*Completed: 2026-05-19*
