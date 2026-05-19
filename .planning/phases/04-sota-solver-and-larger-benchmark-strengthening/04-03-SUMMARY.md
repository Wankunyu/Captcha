---
phase: 04-sota-solver-and-larger-benchmark-strengthening
plan: 03
subsystem: paper-baseline-artifacts
tags: [phase4, baseline-table, notes, comparability, paper-output]

requires:
  - phase: 04-sota-solver-and-larger-benchmark-strengthening
    provides: strict Phase 4 schemas plus coverage/import diagnostics from 04-01 and 04-02
provides:
  - Baseline comparison row builder
  - Paper baseline table row builder
  - build-table CLI subcommand
  - notes CLI subcommand with concise paper-facing Markdown notes
affects: [phase-05-defense-methodology, phase-06-artifact-availability, reviewer-response]

tech-stack:
  added: []
  patterns:
    - Stable source-key join from coverage rows to import diagnostics
    - Direct-comparability gate derived from status, caveats, and validation statuses
    - Concise generated Markdown notes from machine-readable paper table rows

key-files:
  created: []
  modified:
    - baseline_strengthening.py
    - tests/test_baseline_strengthening.py

key-decisions:
  - "Paper rows set directly_comparable=false unless metric, sample, task, license/data-use, and comparability validation all pass and no blocking caveat tags are present."
  - "Literature-only and approximate rows preserve reported metrics while leaving normalized_success_rate empty."
  - "Baseline notes summarize counts and caveats without generating a full manuscript section."

patterns-established:
  - "Full Phase 4 chain can run offline: coverage -> validate-import -> build-table -> notes."
  - "Baseline table generation keeps non-comparable systems visible instead of filtering them out."
  - "Notes expose unavailable/incompatible, non-comparable, and approximate-comparison basis sections."

requirements-completed: [BASE-02, BASE-03, BASE-04, BASE-05, BASE-06]

duration: 6 min
completed: 2026-05-19
---

# Phase 4 Plan 3: Paper Baseline Table And Notes Summary

**Offline comparison-table and notes generation with visible status, metric provenance, and direct-comparability labels**

## Performance

- **Duration:** 6 min
- **Started:** 2026-05-19T15:00:00Z
- **Completed:** 2026-05-19T15:05:59Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Extended `baseline_strengthening.py` with `build-table` and `notes` subcommands.
- Added `build_baseline_comparison_rows`, `build_paper_baseline_rows`, `render_baseline_notes`, and `write_baseline_notes`.
- Joined coverage rows to import diagnostics by stable source keys and preserved every coverage row in downstream comparison and paper-table outputs.
- Populated `normalized_success_rate` only for directly comparable rows whose import diagnostics fully pass and whose coverage caveats do not block parity.
- Generated concise Phase 4 notes with status counts, unavailable/incompatible evidence, non-comparable rows, and approximate comparison basis.
- Added offline tests for row builders, notes, and the full coverage -> validate-import -> build-table -> notes chain.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Baseline table and notes tests** - `084ef44` (test)
2. **Task 2 GREEN: build-table and notes CLI** - `79aa469` (feat)

## Files Created/Modified

- `baseline_strengthening.py` - added comparison/table builders, notes renderer/writer, `build-table` parser branch, and `notes` parser branch.
- `tests/test_baseline_strengthening.py` - added paper-table, normalization, notes, and full offline chain tests.

## Verification

- `uv run pytest tests/test_baseline_strengthening.py -q` - passed, 10 tests.
- `uv run pytest tests/test_phase4_artifacts.py tests/test_baseline_strengthening.py -q` - passed, 19 tests.
- `uv run python baseline_strengthening.py build-table --help` - passed.
- `uv run python baseline_strengthening.py notes --help` - passed.
- `uv run ruff check phase4_artifacts.py baseline_strengthening.py tests/test_phase4_artifacts.py tests/test_baseline_strengthening.py` - passed.

## Decisions Made

- Direct comparability requires no blocking caveat tags and all import validation statuses set to `pass`.
- Paper rows keep `comparability_note` empty only when a row is directly comparable; non-comparable rows receive visible notes.
- Notes remain concise and generated from structured rows rather than becoming manuscript prose.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None. Empty normalized rates on literature-only, approximate, and non-comparable rows are intentional claim-boundary signals.

## Threat Flags

None. The final Phase 4 chain remains offline and local-file based; it adds no live-service adapters, browser automation, provider calls, Docker/Pixi execution, or secret-reading paths.

## Authentication Gates

None.

## TDD Gate Compliance

- Task 1: RED `084ef44`.
- Task 2: GREEN `79aa469`.

## Self-Check: PASSED

- Verified `baseline_strengthening.py` contains `build-table`, `notes`, `build_baseline_comparison_rows`, `build_paper_baseline_rows`, `render_baseline_notes`, and `write_baseline_notes`.
- Verified `tests/test_baseline_strengthening.py` contains the required paper-table, normalization, notes, and full-chain tests.
- Verified `04-03-SUMMARY.md` exists.
- Verified task commits exist: `084ef44`, `79aa469`.
- Verified plan-level pytest, help, and ruff checks pass.

## Next Phase Readiness

Phase 4 implementation is ready for code review, regression checks, and phase-level verification. Phase 5 can consume the baseline notes and caveated comparison rows when shaping defense methodology.

---
*Phase: 04-sota-solver-and-larger-benchmark-strengthening*
*Completed: 2026-05-19*
