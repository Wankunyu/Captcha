---
phase: 03-dataset-scope-statistical-confidence-and-limitations
plan: 02
subsystem: statistics
tags: [phase3, statistical-confidence, wilson, threshold-sensitivity, pandas, csv, json]

requires:
  - phase: 03-dataset-scope-statistical-confidence-and-limitations
    provides: Phase 3 artifact schemas and dataset-scope output contracts from Plan 03-01
provides:
  - Offline pass-rate confidence CLI and CSV/JSON artifacts
  - Wilson confidence intervals for task-type and task-family pass rates
  - Threshold-sensitivity labels with cutoff margins, review-band flags, and trend sources
affects: [phase-03-retry-calibration, paper-statistical-limitations, threshold-sensitivity-artifacts]

tech-stack:
  added: []
  patterns:
    - stdlib NormalDist Wilson interval implementation
    - explicit exp1-exp4 result filtering instead of recursive all-results loading
    - revision_artifacts.revision_run_dir default output paths

key-files:
  created:
    - statistical_confidence.py
    - tests/test_statistical_confidence.py
  modified: []

key-decisions:
  - "Pass-rate loading explicitly scans results/exp1 through results/exp4 and excludes error_analysis outputs."
  - "Wilson confidence intervals use stdlib statistics.NormalDist and math.sqrt to avoid adding SciPy or statsmodels."
  - "Adaptive and extended-validation rates are threshold trend sources only, not merged old-plus-new evidence."

patterns-established:
  - "Statistical CLIs write pass_rate_confidence and threshold_sensitivity CSV/JSON under revision-safe run directories."
  - "Threshold rows preserve the 40% operational cutoff caveat and expose the 30%-50% review band as caution metadata."
  - "Task-family confidence rows aggregate sample counts before computing Wilson intervals."

requirements-completed: [STAT-04, STAT-05]

duration: 7 min
completed: 2026-05-19
---

# Phase 3 Plan 2: Statistical Confidence and Threshold Sensitivity Summary

**Wilson pass-rate confidence intervals plus cutoff-margin threshold-sensitivity artifacts for Phase 3 statistical caveats**

## Performance

- **Duration:** 7 min
- **Started:** 2026-05-19T01:00:49Z
- **Completed:** 2026-05-19T01:07:50Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `statistical_confidence.py`, an offline argparse CLI that writes `pass_rate_confidence.csv/json` and `threshold_sensitivity.csv/json` under `results/revision/<run_id>/` by default.
- Implemented Wilson confidence intervals for explicit Exp1-Exp4 result inputs, with task-type and task-family aggregation, sample counts, source paths, and underpowered flags.
- Implemented threshold-sensitivity labels with the 40% operational cutoff, margin-to-cutoff, 30%-50% review-band membership, CI crossing, trend sensitivity, and explicit trend sources from Exp1-Exp4, adaptive summary/comparison, and extended validation slices.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Confidence interval tests** - `9cc22cf` (test)
2. **Task 1 GREEN: Pass-rate confidence artifacts** - `2f865e1` (feat)
3. **Task 2 RED: Threshold sensitivity tests** - `049eb8a` (test)
4. **Task 2 GREEN: Threshold sensitivity artifacts** - `4dc1277` (feat)

## Files Created/Modified

- `statistical_confidence.py` - offline pass-rate confidence and threshold-sensitivity CLI, result loaders, Wilson interval helper, trend loaders, and CSV/JSON writers.
- `tests/test_statistical_confidence.py` - focused tests for Wilson intervals, explicit result filtering, Exp2/Exp3 normalization, family aggregation, output path safety, threshold labels, trend sources, adaptive/extended inputs, and CLI outputs.

## Verification

- `uv run pytest tests/test_statistical_confidence.py -q` - passed, 12 tests.
- `uv run ruff check statistical_confidence.py tests/test_statistical_confidence.py` - passed.
- `uv run python statistical_confidence.py --help` - passed.
- Acceptance `rg` checks for Wilson interval implementation, output flags, run-id safety, explicit Exp1-Exp4 filtering, threshold helpers, trend sources, cutoff caveat text, and absence of the disallowed margin phrase all passed.

## Decisions Made

- Result ingestion is explicit to `results/exp1`, `results/exp2`, `results/exp3`, and `results/exp4` so recursive `results/error_analysis/**/results.csv` files cannot become statistical evidence.
- Exp2 is the preferred primary threshold row when present; otherwise the row's own experiment is used as primary evidence.
- Adaptive summary/comparison and extended validation rows only contribute to trend-sensitive interpretation and `max_observed_rate`; they are not merged into the primary pass-rate denominator.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `uv run pytest tests/test_statistical_confidence.py -q` passes with pre-existing matplotlib/pyparsing deprecation warnings caused by importing the existing visualization module for task-family metadata.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None. Nullable trend rates are intentional for ambiguous adaptive labels, and empty optional trend inputs produce schema-valid empty trend frames.

## Threat Flags

None. The new CLI reads local result CSV/JSON artifacts and writes local revision outputs only; no live-service automation, browser automation, provider construction, or secret-reading path was introduced.

## Authentication Gates

None.

## TDD Gate Compliance

- Task 1: RED `9cc22cf` followed by GREEN `2f865e1`.
- Task 2: RED `049eb8a` followed by GREEN `4dc1277`.

## Self-Check: PASSED

- Verified `statistical_confidence.py`, `tests/test_statistical_confidence.py`, and `03-02-SUMMARY.md` exist.
- Verified all task commits exist: `9cc22cf`, `2f865e1`, `049eb8a`, `4dc1277`.

## Next Phase Readiness

Ready for Plan 03-03. Pass-rate confidence and threshold-sensitivity artifacts now provide the statistical and cutoff-framing inputs needed by retry calibration and limitations summary work.

---
*Phase: 03-dataset-scope-statistical-confidence-and-limitations*
*Completed: 2026-05-19*
