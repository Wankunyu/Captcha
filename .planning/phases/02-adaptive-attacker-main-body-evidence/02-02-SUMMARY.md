---
phase: 02-adaptive-attacker-main-body-evidence
plan: "02"
subsystem: validation
tags: [adaptive-preflight, request-counts, hashes, pricing-preview, output-safety]
requires:
  - phase: 02-01
    provides: adaptive schema constants, output filenames, and revision run directory safety
provides:
  - Provider-free adaptive preflight CLI for offline run previews
  - Adaptive request-count preview separating solve and reflection overhead
  - Prompt/few-shot hash reporting and non-secret pricing metadata preview
  - Output directory safety checks for adaptive revision run ids
affects: [phase-02, adaptive-attacker, adaptive-artifacts, revision-runs]
tech-stack:
  added: []
  patterns:
    - Argparse CLI prints Pydantic report JSON and writes only when explicitly requested
    - Adaptive preflight imports semantics constants from adaptive_artifacts.py
key-files:
  created:
    - adaptive_preflight.py
    - tests/test_adaptive_preflight.py
  modified: []
key-decisions:
  - "Adaptive preflight reports solve_request_count, reflection_request_count_max, and expected_request_count_max separately."
  - "Pricing preview reads only explicit non-secret pricing metadata, never local secret configuration."
  - "Prompt/few-shot inputs and prompt prefix/suffix values are recorded as hashes, not raw prompt text."
  - "Adaptive output directories fail closed unless --overwrite or --resume is explicit."
patterns-established:
  - "Adaptive preflight output_paths include run_manifest and all Phase 2 adaptive artifact filenames under results/revision/<run_id>/."
  - "Adaptive preflight can validate aliases and budgets without constructing providers or reading secrets."
requirements-completed: [ADAPT-01, ADAPT-02, ADAPT-03]
duration: 4min
completed: 2026-05-18
---

# Phase 02: Adaptive Attacker Main-Body Evidence - Plan 02 Summary

**Provider-free adaptive preflight with solve/reflection request counts, prompt hashes, cost preview metadata, and output-directory guards**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-18T03:31:09Z
- **Completed:** 2026-05-18T03:35:21Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `adaptive_preflight.py` with import-safe Pydantic report models and an offline argparse CLI.
- Added adaptive semantics to preflight reports: `without-replacement`, `binary-pass-fail`, `explicit-policy-notes`, and `first-success-or-budget`.
- Added offline validation for task aliases, dataset directories, Git LFS ground-truth pointers, non-empty ground truth, prompt/few-shot mappings, run ids, existing output directories, and adaptive request counts.
- Added prompt/few-shot/prefix/suffix hash reporting, adaptive output path reporting, and non-secret pricing metadata preview.
- Added focused tests covering schema defaults, CLI output, report writing, provider-free behavior, request counts, hashes, aliases, unsafe run ids, existing directory rejection, pricing metadata, and secret-like text exclusion.

## Task Commits

Each TDD task was committed atomically:

1. **Task 1 RED: Adaptive preflight schema and CLI tests** - `14556c9` (`test(02-02): add failing adaptive preflight schema tests`)
2. **Task 1 GREEN: Adaptive preflight schema CLI** - `7cf0075` (`feat(02-02): add adaptive preflight schema CLI`)
3. **Task 2 RED: Adaptive preflight validation tests** - `08f6eb5` (`test(02-02): add failing adaptive preflight validation tests`)
4. **Task 2 GREEN: Adaptive preflight validation** - `3e6b204` (`feat(02-02): implement adaptive preflight validation`)

## Files Created/Modified

- `adaptive_preflight.py` - Implements the provider-free adaptive preflight schema, CLI, validation, output paths, request counts, hashes, and cost preview.
- `tests/test_adaptive_preflight.py` - Verifies adaptive preflight schema, CLI behavior, safety guards, aliases, request counts, hashes, pricing metadata, report writing, and provider-boundary safety.

## Decisions Made

- Adaptive preflight treats solve attempts as the fair task-type budget and reports reflection calls separately as maximum overhead.
- Pricing preview accepts only an explicit `--pricing-file` metadata document and never reads local secret configuration.
- Prompt prefix and suffix are hashed with SHA-256 and never written to the report as raw text.
- Output directory existence is checked even without `--write-report`, so paid execution can fail early before provider construction.

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope change.

## Issues Encountered

None.

## Verification

- `uv run pytest tests/test_adaptive_preflight.py -q` passed.
- `uv run ruff check adaptive_preflight.py tests/test_adaptive_preflight.py` passed.
- `uv run python adaptive_preflight.py --dataset-root ./captcha_data --types Dice_Count --prompts-file ./prompts_optimized.yaml --output-root ./results/revision --run-id local-adaptive-preflight --provider openai --model gpt-5 --max-per-type 1 --attempt-budget-k 2` exited 0 and printed adaptive semantics, request counts, hashes, cost preview, and output paths.
- Plan acceptance `rg` checks passed for schema constants, model classes, adaptive literals, output filenames, request-count fields, hash fields, pricing unavailable reasons, and absence of provider-boundary calls in `adaptive_preflight.py`.

## TDD Gate Compliance

- RED commits present: `14556c9`, `08f6eb5`
- GREEN commits present after RED commits: `7cf0075`, `3e6b204`
- Refactor commit: Not needed.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 02-03 can gate adaptive attacker execution behind `adaptive_preflight.py` and rely on validated `results/revision/<run_id>/` output paths, prompt/few-shot hashes, request-count previews, and explicit adaptive semantics before constructing providers.

## Self-Check: PASSED

All key files exist on disk, required task commits are present, and automated verification passed.

---
*Phase: 02-adaptive-attacker-main-body-evidence*
*Completed: 2026-05-18*
