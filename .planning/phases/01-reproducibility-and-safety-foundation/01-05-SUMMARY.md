---
phase: 01-reproducibility-and-safety-foundation
plan: "05"
subsystem: evaluator
tags: [revision-mode, run-manifest, attempts-jsonl, scoring-regression, cli]
requires:
  - phase: 01-02
    provides: import-safe evaluator and secret-safe boundary
  - phase: 01-03
    provides: revision artifact writer and schemas
  - phase: 01-04
    provides: preflight-compatible prompt hash and output path semantics
provides:
  - Explicit run_eval revision mode with manifest and attempt writing
  - CLI flags for revision artifacts and attempt logging
  - Focused scoring and summary regression coverage
affects: [phase-01, evaluator, revision-runs, paper-evidence]
tech-stack:
  added: []
  patterns:
    - Revision mode is opt-in through revision_run_id and write_attempts
    - Manifest and output-directory checks happen before provider construction
key-files:
  created:
    - tests/test_revision_run_contract.py
    - tests/test_scoring_regressions.py
  modified:
    - run_eval.py
key-decisions:
  - "Legacy run_eval calls without revision_run_id keep writing the existing result CSV shape."
  - "Revision-mode runs require write_attempts=True so manifests and attempts stay linked."
patterns-established:
  - "run_eval writes run_manifest.json before provider construction in explicit revision mode."
  - "AttemptRecord rows are appended before derived revision summary files are written."
requirements-completed: [REPRO-03, REPRO-04, REPRO-06]
duration: 22min
completed: 2026-05-16
---

# Phase 01: Reproducibility and Safety Foundation - Plan 05 Summary

**Explicit evaluator revision mode with pre-provider manifests, append-only attempts, and narrow scoring regressions**

## Performance

- **Duration:** 22 min
- **Started:** 2026-05-16T03:36:00Z
- **Completed:** 2026-05-16T03:57:37Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added explicit `run_eval()` revision-mode parameters: `revision_run_id`, `revision_output_root`, `write_attempts`, `overwrite_revision_output`, and `resume_revision_output`.
- Wrote revision manifests after task/prompt validation and before provider construction.
- Appended one `AttemptRecord` per evaluated task and derived revision summaries from `attempts.jsonl`.
- Added CLI flags for revision artifact mode and fixed direct CLI `args.out_csv` usage plus the missing `main()` guard.
- Added focused regression tests for `Path_Finder` classify scoring, multi-select failure descriptions, and summary CSV row writing.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Revision run contract tests** - `46b8586` (`test(01-05): add failing revision run contract`)
2. **Task 1 GREEN: Evaluator revision artifact wiring** - `1a09f02` (`feat(01-05): wire revision artifacts into evaluator`)
3. **Task 2 RED: Scoring regression tests** - `185fd5a` (`test(01-05): add failing scoring regressions`)
4. **Task 2 GREEN: Scoring regression fixes** - `3f404d0` (`fix(01-05): cover revision scoring regressions`)

## Files Created/Modified

- `run_eval.py` - Adds revision-mode writer integration, manifest/attempt creation, CLI flags, direct CLI guard, and narrow scoring fixes.
- `tests/test_revision_run_contract.py` - Verifies revision-mode output policy, manifest ordering, attempts, summaries, hashes, and cost-control metadata.
- `tests/test_scoring_regressions.py` - Verifies `Path_Finder`, multi-select failure descriptions, and summary CSV row counts.

## Decisions Made

- `revision_run_id` without `write_attempts=True` raises before local config loading or provider construction.
- Revision `cost_control` records expected request count and either pre-call per-request estimate metadata or an explicit unavailable reason.
- The legacy aggregate CSV remains in place for existing callers; revision summaries are additional artifacts under `results/revision/<run_id>/`.

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope change.

## Issues Encountered

- The summary CSV writer indentation bug was fixed while wiring revision mode and then covered by the Task 2 regression test.

## Verification

- `uv run pytest tests/test_revision_run_contract.py tests/test_scoring_regressions.py -q` passed.
- `uv run python -c "import run_eval; import inspect; assert 'revision_run_id' in str(inspect.signature(run_eval.run_eval))"` passed.
- `rg` acceptance checks verified revision-mode flags, prompt/few-shot hash fields, cost-control metadata, `RevisionArtifactWriter`, absence of `args.out`, and `Path_Finder` scoring coverage.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 1 now has install, preflight, manifest, attempt-log, secret-safety, and validator contracts needed before paid provider runs or adaptive-attacker evidence.

## Self-Check: PASSED

All key files exist on disk, acceptance checks passed, and required commits are present.

---
*Phase: 01-reproducibility-and-safety-foundation*
*Completed: 2026-05-16*
