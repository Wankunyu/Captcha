---
phase: 02-adaptive-attacker-main-body-evidence
plan: "03"
subsystem: adaptive-attacker
tags: [adaptive-attacker, binary-feedback, explicit-memory, jsonl, cli]
requires:
  - phase: 02-01
    provides: adaptive policy-state, attempt, summary schemas, and append-only writer
  - phase: 02-02
    provides: adaptive preflight semantics, output paths, and request-count contract
  - phase: 01-05
    provides: revision manifest pattern and evaluator task/provider/scoring seams
provides:
  - Offline dataset-based adaptive attacker loop with explicit task-type policy memory
  - Binary-fail self-reflection helper constrained to current prompt and own answer
  - Adaptive CLI that writes run manifests before provider construction
  - Append-only adaptive attempts and derived adaptive summaries
affects: [phase-02, adaptive-preflight, adaptive-comparison, revision-runs]
tech-stack:
  added: []
  patterns:
    - TDD RED/GREEN commits for adaptive helper and loop behavior
    - Adaptive run loop reuses run_eval task construction, provider factory, JSON schema, and scoring
    - Reflection calls are counted separately from solve attempts
key-files:
  created:
    - adaptive_attacker.py
    - tests/test_adaptive_attacker.py
  modified: []
key-decisions:
  - "Adaptive execution samples each task-type pool without replacement using a local seeded random generator."
  - "The run manifest is written before local config loading and provider construction."
  - "Reflection prompt output is hard-coded to Feedback: FAIL and is only used for scientific wrong answers with another solve attempt available."
  - "Resume mode skips provider construction when existing adaptive attempts already contain a terminal stopping reason for every selected task type."
patterns-established:
  - "Attempt IDs use run_id:task_type:attempt_index:puzzle_id for stable resume detection."
  - "AdaptiveAttemptRecord stores parsed solve output and policy state, but not raw transcripts or instance-level corrective hints."
requirements-completed: [ADAPT-01, ADAPT-02, ADAPT-03]
duration: 8min
completed: 2026-05-18
---

# Phase 02: Adaptive Attacker Main-Body Evidence - Plan 03 Summary

**Offline adaptive attacker loop with explicit local policy memory, binary-fail reflection, without-replacement sampling, and append-only adaptive evidence artifacts**

## Performance

- **Duration:** 8 min
- **Started:** 2026-05-18T03:38:11Z
- **Completed:** 2026-05-18T03:45:49Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `adaptive_attacker.py` helper primitives for grouping tasks, adapting prompts from explicit policy notes, building constrained reflection prompts, validating reflection JSON, updating policy state, and classifying failure classes.
- Implemented `run_adaptive_experiment()` with manifest-before-provider ordering, local seeded without-replacement task pools, first-success/budget/pool stopping, resume skip behavior, and adaptive summaries derived from persisted attempts.
- Added an argparse CLI for offline adaptive runs with flags matching the execution contract.
- Added fake-provider tests covering helper signatures, sentinel non-leakage, failure classification, manifest ordering, no duplicate puzzle IDs, stop rules, reflection gating, and resume behavior.

## Task Commits

Each TDD task was committed atomically:

1. **Task 1 RED: Adaptive helper tests** - `a91c574` (`test(02-03): add failing adaptive helper tests`)
2. **Task 1 GREEN: Adaptive helper primitives** - `3bff17c` (`feat(02-03): add adaptive helper primitives`)
3. **Task 2 RED: Adaptive loop tests** - `3bbd795` (`test(02-03): add failing adaptive loop tests`)
4. **Task 2 GREEN: Adaptive loop and CLI** - `a86d8cf` (`feat(02-03): implement adaptive attacker loop`)

## Files Created/Modified

- `adaptive_attacker.py` - Implements binary-feedback helper functions, explicit policy-state prompt adaptation, adaptive run manifest writing, without-replacement solve loop, reflection gating, append-only attempt writing, summary derivation, resume skip behavior, and CLI.
- `tests/test_adaptive_attacker.py` - Verifies helper contracts, no sentinel leakage, policy-state validation, failure classes, adaptive run ordering, sampling, stopping, reflection behavior, and resume semantics with fake providers.

## Decisions Made

- Wrote the adaptive run manifest before loading local config or constructing the provider, so output and retry semantics are visible before any paid/provider boundary.
- Counted reflection latency, tokens, and cost into the attempt that triggered the reflection while also recording `reflection_request_count` separately in metadata.
- Incremented failed-attempt count for all failed solve attempts, but added new strategy/rule notes only when constrained scientific-wrong reflection produced a valid note.
- Kept provider/runtime and protocol failures in the attempt stream while suppressing reflection for those classes.

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope change.

## Issues Encountered

None.

## Verification

- `uv run pytest tests/test_adaptive_attacker.py -q` passed.
- `uv run ruff check adaptive_attacker.py tests/test_adaptive_attacker.py` passed.
- `uv run python -c "import adaptive_attacker; assert hasattr(adaptive_attacker, 'run_adaptive_experiment')"` passed.
- `uv run pytest tests/test_adaptive_artifacts.py tests/test_adaptive_preflight.py tests/test_revision_run_contract.py tests/test_adaptive_attacker.py -q` passed.
- Plan acceptance `rg` checks passed for helper functions, CLI entry point, run_eval integration calls, adaptive semantics literals, failure classes, no `random.choice`, no sentinel in `adaptive_attacker.py`, and no prohibited leakage patterns in `adaptive_attacker.py`.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required for offline fake-provider validation. Real provider runs still require local config supplied through `--secrets-file`.

## Next Phase Readiness

Plan 02-04 can consume `adaptive_summary.csv/json` and `adaptive_attempts.jsonl` under `results/revision/<run_id>/` to compare adaptive outcomes against Exp2 pass@1, Bernoulli Success@k, and fixed retry outcomes under the same task-type solve budget.

## Self-Check: PASSED

All key files exist on disk, required task commits are present, and automated verification passed after summary creation.

---
*Phase: 02-adaptive-attacker-main-body-evidence*
*Completed: 2026-05-18*
