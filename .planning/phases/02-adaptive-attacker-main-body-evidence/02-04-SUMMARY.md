---
phase: 02-adaptive-attacker-main-body-evidence
plan: "04"
subsystem: analysis
tags: [adaptive-comparison, bernoulli, fixed-retry, task-type, csv, json]
requires:
  - phase: 02-01
    provides: adaptive comparison schema and adaptive summary artifact contract
  - phase: 02-03
    provides: adaptive_summary.csv/json emitted from adaptive attacker attempts
provides:
  - Task-type comparison builder for Exp2 pass@1, Bernoulli Success@k, fixed retry, and adaptive outcomes
  - Adaptive comparison CSV/JSON writer with Pydantic row validation
  - Hard/borderline/broken labels with operational cutoff note and structural bottleneck tags
affects: [phase-02, adaptive-comparison, paper-table-inputs, phase-03-statistics]
tech-stack:
  added: []
  patterns:
    - CAPTCHAVisualizer-backed legacy result loading with quiet CLI output
    - Task-type comparison rows validated through AdaptiveComparisonRow before writing
    - Argparse CLI emits machine-readable JSON summary with row counts and output paths
key-files:
  created:
    - adaptive_compare.py
    - tests/test_adaptive_compare.py
  modified: []
key-decisions:
  - "Comparison rows remain task-type primary under the same attempt_budget_k for Bernoulli, fixed retry, and adaptive outcomes."
  - "Provider/runtime/protocol failures remain visible as counts but never create persistent hard-family notes without scientific_wrong_count > 0."
  - "Structural bottleneck tags preserve the AdaptiveComparisonRow list schema from 02-01 while staying explanatory, not the primary evaluation unit."
patterns-established:
  - "Comparison CLIs should print clean JSON summaries while suppressing visualizer scan logs."
  - "Persistent hard-family notes require adaptive_label == hard, adaptive_observed_success == false, and scientific_wrong_count > 0."
requirements-completed: [ADAPT-04, ADAPT-05, ADAPT-06]
duration: 10min
completed: 2026-05-18
---

# Phase 02 Plan 04: Adaptive Comparison Table Builder Summary

**Task-type comparison table inputs merging Exp2 pass@1, Bernoulli Success@k, fixed retry observations, and adaptive session-memory outcomes**

## Performance

- **Duration:** 10 min
- **Started:** 2026-05-18T03:48:44Z
- **Completed:** 2026-05-18T03:58:42Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Added `adaptive_compare.py` with pure loaders for legacy Exp2/Exp3 results and adaptive summary CSV/JSON artifacts.
- Added `build_comparison_rows()` to merge task-type rows by provider, model, task type, and `attempt_budget_k`, with missing fixed retry observations preserved as `None`.
- Added Bernoulli `Success@k` and expected-attempt fields using `predict_q_from_exp2()` and `predict_A_from_exp2()`.
- Added hard/borderline/broken labels, the required operational cutoff note, structural bottleneck tags, instruction-sensitivity tagging, nullable CI fields, and persistent hard-family notes gated on scientific failures only.
- Added an argparse CLI that writes parent directories for comparison CSV/JSON outputs and prints a clean JSON summary with `row_count`, `output_csv`, and `output_json`.

## Task Commits

Each TDD task was committed atomically:

1. **Task 1 RED: Adaptive comparison merge tests** - `4ba2289` (`test(02-04): add failing adaptive comparison merge tests`)
2. **Task 1 GREEN: Adaptive comparison merge implementation** - `ef573d6` (`feat(02-04): merge adaptive comparison inputs`)
3. **Task 2 RED: Classification and failure-note tests** - `6721d4e` (`test(02-04): add failing adaptive classification tests`)
4. **Task 2 GREEN: Classification labels and bottleneck tags** - `40caeb8` (`feat(02-04): add adaptive classification labels`)
5. **Task 3 RED: CLI behavior tests** - `d002f0b` (`test(02-04): add failing adaptive comparison CLI tests`)
6. **Task 3 GREEN: CLI implementation** - `31bd7d4` (`feat(02-04): add adaptive comparison CLI`)

## Files Created/Modified

- `adaptive_compare.py` - Loads legacy/adaptive inputs, builds validated comparison rows, classifies rates, adds bottleneck and persistent-failure annotations, writes CSV/JSON, and exposes the CLI.
- `tests/test_adaptive_compare.py` - Verifies merge behavior, Bernoulli formulas, nullable fixed retry fields, labels, cutoff note, bottleneck tags, persistent-failure gating, CI deferral, CLI output, and error exits.

## Decisions Made

- Kept `attempt_budget_k` as the shared comparison budget across Exp2-derived Bernoulli predictions, fixed retry observations, and adaptive outcomes.
- Used `CAPTCHAVisualizer` for legacy result discovery but suppressed its scan logs inside `load_legacy_results()` so the CLI can print valid JSON.
- Preserved the 02-01 `AdaptiveComparisonRow.structural_bottleneck_tags` list schema instead of changing the schema type during this plan.
- Treated infrastructure-only and protocol-only adaptive failures as limitation/error-separation evidence only; they do not receive persistent robustness notes.

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope change.

## Issues Encountered

- `CAPTCHAVisualizer` imports trigger matplotlib pyparsing deprecation warnings during tests. The warnings are pre-existing dependency noise and do not affect comparison behavior.

## Verification

- `uv run pytest tests/test_adaptive_compare.py -q` passed.
- `uv run ruff check adaptive_compare.py tests/test_adaptive_compare.py` passed.
- `uv run python adaptive_compare.py --help` exited 0.
- Plan acceptance `rg` checks passed for loaders, Bernoulli helpers, `CAPTCHAVisualizer`, D-10 comparison fields, cutoff note, labels, bottleneck tags, persistent-failure gating, nullable CI reason, CLI flags, output filenames, and `row_count`.

## TDD Gate Compliance

- RED commits present: `4ba2289`, `6721d4e`, `d002f0b`
- GREEN commits present after RED commits: `ef573d6`, `40caeb8`, `31bd7d4`
- Refactor commit: Not needed.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 02-05 can run offline end-to-end validation by generating adaptive summaries and passing them through `adaptive_compare.py` to produce `adaptive_comparison.csv` and `adaptive_comparison.json` for main-body table inputs.

## Self-Check: PASSED

All key files exist on disk, required task commits are present, and automated verification passed after summary creation.

---
*Phase: 02-adaptive-attacker-main-body-evidence*
*Completed: 2026-05-18*
