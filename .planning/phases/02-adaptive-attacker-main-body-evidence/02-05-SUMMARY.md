---
phase: 02-adaptive-attacker-main-body-evidence
plan: "05"
subsystem: validation
tags: [adaptive-attacker, end-to-end, fake-provider, README, offline-validation]
requires:
  - phase: 02-01
    provides: adaptive artifact schemas and writer contracts
  - phase: 02-02
    provides: adaptive preflight request-count and semantics report
  - phase: 02-03
    provides: adaptive attacker loop with explicit local policy memory
  - phase: 02-04
    provides: adaptive comparison table builder
provides:
  - Offline fake-provider end-to-end validation for Phase 2 adaptive workflow
  - README reproduction commands for adaptive preflight, run, comparison, and default validation
  - Optional paid-smoke documentation gated by preflight request counts and explicit budget decision
affects: [phase-02, phase-03-statistics, paper-table-inputs, artifact-reproduction]
tech-stack:
  added: []
  patterns:
    - End-to-end adaptive tests use temp datasets, monkeypatching, and fake providers only
    - Paid smoke documentation stays non-default and budget-gated
key-files:
  created:
    - tests/test_adaptive_end_to_end.py
  modified:
    - README.md
key-decisions:
  - "The complete Phase 2 adaptive workflow is validated with an offline fake-provider E2E test before any optional paid provider run."
  - "README makes offline pytest/ruff validation the default path and marks paid smoke as explicitly non-default."
  - "Optional paid smoke requires adaptive preflight and inspection of expected_request_count_max before a budget decision."
patterns-established:
  - "E2E adaptive validation creates temp CaptchaWorld-like inputs and never depends on local credentials."
  - "Sentinel ground-truth leakage checks cover adaptive attempts, summaries, provider prompts, and comparison outputs."
requirements-completed: [ADAPT-01, ADAPT-02, ADAPT-03, ADAPT-04, ADAPT-05, ADAPT-06]
duration: 4min
completed: 2026-05-18
---

# Phase 02 Plan 05: Offline Adaptive Workflow Validation Summary

**Offline fake-provider validation and reproduction documentation for the full adaptive attacker evidence workflow**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-18T04:02:25Z
- **Completed:** 2026-05-18T04:06:23Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Added `tests/test_adaptive_end_to_end.py`, covering adaptive preflight, fake-provider adaptive execution, summary artifacts, and comparison output generation.
- Verified the test uses temp datasets and monkeypatched provider/task seams only, with no real provider calls or local credential loading.
- Added README Phase 2 reproduction notes for adaptive preflight, default offline validation, adaptive execution, comparison-table generation, and optional paid smoke.
- Ran full Phase 2 offline pytest and ruff validation successfully.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add offline end-to-end adaptive validation test** - `0ff808e` (`test`)
2. **Task 2: Document Phase 2 offline reproduction and optional gated paid smoke** - `1e7c1e9` (`docs`)
3. **Task 3: Run full Phase 2 offline verification** - `86fe730` (`test`, empty verification marker commit)

## Files Created/Modified

- `tests/test_adaptive_end_to_end.py` - Offline integration-style pytest for preflight, adaptive run, artifact leakage checks, and comparison outputs.
- `README.md` - Adds Phase 2 adaptive workflow commands and default offline validation guidance.

## Decisions Made

- Kept the E2E test fully offline by monkeypatching `run_eval.build_tasks()` and `run_eval.make_provider()`.
- Used a fake provider that fails once, emits a constrained policy note, and succeeds on the second solve attempt.
- Documented paid smoke as a separate, optional path gated by preflight `expected_request_count_max`.

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope change.

## Issues Encountered

- The Task 1 TDD RED check passed immediately because Plans 02-01 through 02-04 already implemented the behavior that the new E2E test validates. No production-code GREEN change was required.
- Task 3 produced no file changes; an empty verification marker commit records the successful full offline validation task.

## Verification

- `uv run pytest tests/test_adaptive_end_to_end.py -q` passed.
- `uv run python -c "from pathlib import Path; text=Path('README.md').read_text(); assert 'Phase 2 Adaptive Attacker Workflow' in text and 'Optional paid smoke is not part of default verification.' in text"` passed.
- `uv run pytest tests/test_adaptive_artifacts.py tests/test_adaptive_preflight.py tests/test_adaptive_attacker.py tests/test_adaptive_compare.py tests/test_adaptive_end_to_end.py -q` passed with 36 tests.
- `uv run ruff check adaptive_artifacts.py adaptive_preflight.py adaptive_attacker.py adaptive_compare.py tests` passed.
- Acceptance `rg` checks passed for E2E imports, adaptive semantics literals, README headings, request-count fields, `results/revision/<run_id>/`, and secret-file boundaries.

## TDD Gate Compliance

- RED-style test commit present: `0ff808e`
- GREEN implementation commit: Not applicable; the existing Phase 2 implementation already satisfied the new E2E test.
- Warning: the RED run did not fail before commit because this plan added validation coverage over existing behavior rather than introducing a new production feature.

## Known Stubs

None. Stub-pattern scan found only test-local empty lists and an empty `secrets_file=""` argument used to prevent local credential loading; these are intentional test fixtures, not product stubs.

## Threat Flags

None. The plan added no new network endpoint, auth path, file-access trust boundary, or schema change beyond offline test fixtures and README reproduction commands.

## User Setup Required

None for default validation. Optional paid smoke remains separate and requires a researcher budget decision after adaptive preflight.

## Next Phase Readiness

Phase 2 is now validated end to end offline. Phase 3 can consume the adaptive summary and comparison contracts for statistical confidence, threshold sensitivity, and dataset-scope interpretation without relying on paid-provider smoke as a validation gate.

## Self-Check: PASSED

All key files exist on disk, required task commits are present in git history, and automated offline verification passed.

---
*Phase: 02-adaptive-attacker-main-body-evidence*
*Completed: 2026-05-18*
