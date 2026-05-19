---
phase: 04-sota-solver-and-larger-benchmark-strengthening
plan: 02
subsystem: baseline-cli
tags: [phase4, baseline, halligan, oedipus, import-validation, csv, json]

requires:
  - phase: 04-sota-solver-and-larger-benchmark-strengthening
    provides: strict Phase 4 artifact row contracts from 04-01
provides:
  - Offline coverage matrix CLI for baseline source metadata
  - Offline external import validation CLI for Halligan-first smoke rows
  - Seed metadata for Halligan, Oedipus, VTTSolver, and PhishDecloaker
  - Replacement gate requiring user confirmation before secondary smoke rows replace named systems
affects: [phase-04-paper-baseline-table, phase-06-claim-traceability]

tech-stack:
  added: []
  patterns:
    - Root-level argparse CLI with subcommands
    - revision_artifacts.revision_run_dir default output paths
    - Local JSON/CSV ingestion with strict Phase 4 row validation

key-files:
  created:
    - baseline_strengthening.py
    - baseline_sources/phase4_baseline_sources.json
    - tests/test_baseline_strengthening.py
  modified: []

key-decisions:
  - "Coverage metadata includes Halligan and Oedipus unconditionally, plus only VTTSolver and PhishDecloaker as bounded secondary systems."
  - "Halligan seed metadata contains two smoke/import labels: arkose/dice_match and OpenCaptchaWorld/Hold_Button."
  - "Secondary smoke/import rows cannot replace Halligan/Oedipus validation unless user_confirmed_replacement=true is explicit."

patterns-established:
  - "Coverage source metadata may carry selection_reason for secondary-system governance, while emitted coverage artifacts remain strict BaselineCoverageRow payloads."
  - "Import diagnostics are generated from local CSV/JSON rows and never execute external solvers or live services."
  - "CLI summaries include row counts and output paths only, avoiding secret-bearing fields."

requirements-completed: [BASE-01, BASE-02, BASE-03, BASE-04, BASE-05, BASE-06]

duration: 9 min
completed: 2026-05-19
---

# Phase 4 Plan 2: Baseline Coverage And Import Validation Summary

**Offline baseline-strengthening CLI that writes strict coverage matrices and Halligan-first import diagnostics**

## Performance

- **Duration:** 9 min
- **Started:** 2026-05-19T14:51:00Z
- **Completed:** 2026-05-19T15:00:05Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added `baseline_strengthening.py` with `coverage` and `validate-import` subcommands.
- Added source metadata for Halligan, Oedipus, VTTSolver, and PhishDecloaker, including two Halligan smoke/import labels and conservative caveats for literature-only rows.
- Implemented coverage validation for Halligan/Oedipus presence, bounded secondary systems, secondary-system selection reasons, strict audit fields, and runnable/importable license and data-use constraints.
- Implemented import diagnostics that validate required fields, metric definitions, task labels, sample counts, artifact/license/data-use fields, and comparability assumptions before writing `import_diagnostics.csv/json`.
- Added a replacement gate so secondary smoke rows cannot substitute for Halligan/Oedipus unless explicitly confirmed in the input row.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Baseline strengthening CLI tests** - `e17eed8` (test)
2. **Task 2 GREEN: Coverage and import-validation CLI** - `4ab7894` (feat)

## Files Created/Modified

- `baseline_strengthening.py` - offline Phase 4 CLI, coverage source loading, coverage validation, import row loading, import diagnostics, and subcommand parser.
- `baseline_sources/phase4_baseline_sources.json` - seed metadata for Halligan, Oedipus, VTTSolver, and PhishDecloaker with conservative status/caveat labels.
- `tests/test_baseline_strengthening.py` - fixture-based coverage, import-validation, replacement-gate, output-path, and secret-safe summary tests.

## Verification

- `uv run pytest tests/test_baseline_strengthening.py -q` - passed, 6 tests.
- `uv run pytest tests/test_phase4_artifacts.py tests/test_baseline_strengthening.py -q` - passed, 15 tests.
- `uv run python baseline_strengthening.py coverage --help` - passed.
- `uv run python baseline_strengthening.py validate-import --help` - passed.
- `uv run ruff check baseline_strengthening.py tests/test_baseline_strengthening.py` - passed.
- `uv run python baseline_strengthening.py coverage --source-metadata baseline_sources/phase4_baseline_sources.json --output-root /private/tmp/captcha-phase4-smoke --run-id seed-smoke` - passed, 5 rows.

## Decisions Made

- Used validated import rows as the first Phase 4 smoke path rather than direct Halligan/Oedipus execution.
- Kept Oedipus literature-only with artifact/license caveats until dataset/code location and terms are validated.
- Limited additional systems to VTTSolver and PhishDecloaker because they are Halligan comparison baselines.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Initial ruff check found one unused schema-version import in `baseline_strengthening.py`; removed it before committing the GREEN implementation.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None. Literature-only rows and nullable reported metrics are intentional conservative evidence states, not placeholders.

## Threat Flags

None. The CLI only reads local JSON/CSV metadata and writes local revision outputs; it does not implement direct solver execution, Docker/Pixi setup, browser automation, provider calls, live-service automation, or secret loading.

## Authentication Gates

None.

## TDD Gate Compliance

- Task 1: RED `e17eed8`.
- Task 2: GREEN `4ab7894`.

## Self-Check: PASSED

- Verified `baseline_strengthening.py`, `baseline_sources/phase4_baseline_sources.json`, and `tests/test_baseline_strengthening.py` exist.
- Verified `04-02-SUMMARY.md` exists.
- Verified task commits exist: `e17eed8`, `4ab7894`.
- Verified plan-level pytest, help, seed-smoke, and ruff checks pass.

## Next Phase Readiness

Ready for Plan 04-03. Coverage matrices and import diagnostics can now feed `build-table` and `notes` without live-service automation or direct solver reimplementation.

---
*Phase: 04-sota-solver-and-larger-benchmark-strengthening*
*Completed: 2026-05-19*
