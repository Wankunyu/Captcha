---
phase: 01-reproducibility-and-safety-foundation
plan: "04"
subsystem: validation
tags: [preflight, dataset-validation, task-aliases, cost-preview, hashes]
requires:
  - phase: 01-02
    provides: import-safe evaluator modules and secret-safe config boundary
  - phase: 01-03
    provides: revision artifact path and hash helpers
provides:
  - Offline revision preflight CLI with request-count and output-directory safety checks
  - Task alias and dataset directory drift tests
  - Prompt/few-shot hash reporting and non-secret cost preview metadata
affects: [phase-01, evaluator, revision-runs, task-contracts]
tech-stack:
  added: [pydantic, argparse]
  patterns:
    - Preflight validates filesystem and metadata before provider boundaries
    - Task alias drift is covered by focused pytest contracts
key-files:
  created:
    - revision_preflight.py
    - tests/test_revision_preflight.py
    - tests/test_task_contracts.py
  modified: []
key-decisions:
  - "Preflight imports only SUPPORTED_TYPES from run_eval and never constructs provider clients."
  - "Few-shot sections explicitly marked '(Not Used)' are ignored by active task contract checks."
patterns-established:
  - "Preflight reports selected task counts, prompt hashes, output paths, and cost-preview availability as JSON."
  - "Connect_icon remains a dataset directory alias for canonical Connect_Icon."
requirements-completed: [REPRO-02, REPRO-06]
duration: 16min
completed: 2026-05-16
---

# Phase 01: Reproducibility and Safety Foundation - Plan 04 Summary

**Offline preflight CLI for task, dataset, prompt, output, request-count, and cost-preview validation**

## Performance

- **Duration:** 16 min
- **Started:** 2026-05-16T03:36:00Z
- **Completed:** 2026-05-16T03:51:37Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added `revision_preflight.py` with Pydantic report models, task alias normalization, dataset validation, prompt/few-shot hash reporting, output directory guards, expected request counts, and cost preview metadata.
- Added tests proving the preflight stays offline, handles `Connect_icon`, writes `preflight_report.json`, refuses accidental output reuse, and reports hash/cost metadata.
- Added task contract tests for supported dataset directories, prompt keys, few-shot keys, and the `Connect_icon` alias.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Preflight coverage** - `351f9aa` (`test(01-04): add failing preflight coverage`)
2. **Task 1 GREEN: Offline preflight CLI** - `a518284` (`feat(01-04): add offline revision preflight`)
3. **Task 2: Task contract drift tests** - `f3a9ede` (`test(01-04): cover task contract drift`)

## Files Created/Modified

- `revision_preflight.py` - Implements the offline preflight CLI and report schema.
- `tests/test_revision_preflight.py` - Covers offline report generation, aliasing, output directory safety, provider-boundary safety, hashes, and missing pricing metadata.
- `tests/test_task_contracts.py` - Covers task/dataset/prompt/few-shot drift checks.

## Decisions Made

- Preflight reports `unavailable_reason` when pricing metadata is absent instead of reading local secret configuration.
- The output directory existence check runs even when `--write-report` is not used, so paid runs can fail early before provider construction.
- Task contract tests ignore only few-shot sections explicitly named as not used.

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope change.

## Issues Encountered

- No code changes were needed for Task 2 after adding drift tests; active dataset, prompt, and few-shot keys already matched the alias contract.

## Verification

- `uv run pytest tests/test_revision_preflight.py tests/test_task_contracts.py -q` passed.
- `uv run python revision_preflight.py --dataset-root ./captcha_data --types Dice_Count --prompts-file ./prompts_optimized.yaml --output-root ./results/revision --run-id local-preflight --provider openai --model gpt-5 --max-per-type 1 --max-attempts 1` exited 0 and printed `expected_request_count`, `prompt_config`, and `cost_preview`.
- `rg` acceptance checks verified schema constants, cost preview fields, hash fields, alias maps, CLI entry point, and absence of provider-boundary calls.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 05 can wire `RevisionArtifactWriter` into explicit evaluator revision mode and rely on preflight-compatible prompt hash and output path semantics.

## Self-Check: PASSED

All key files exist on disk, acceptance checks passed, and required commits are present.

---
*Phase: 01-reproducibility-and-safety-foundation*
*Completed: 2026-05-16*
