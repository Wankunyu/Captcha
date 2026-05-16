---
phase: 01-reproducibility-and-safety-foundation
plan: "02"
subsystem: security
tags: [import-safety, secrets, redaction, provider-smoke, pytest]
requires:
  - phase: 01-01
    provides: uv-backed pytest execution and locked dependencies
provides:
  - Import-safe evaluator modules with provider smoke moved to an explicit CLI
  - Shared secret-safe local config loader and redaction helpers
  - Placeholder-only secret example config and ignore rules for local secret/output files
affects: [phase-01, preflight, revision-artifacts, evaluator]
tech-stack:
  added: [pytest]
  patterns:
    - Provider smoke behavior is reachable only through main() in revision_provider_smoke.py
    - Secret-like values are redacted through revision_secrets.py before output
key-files:
  created:
    - revision_provider_smoke.py
    - revision_secrets.py
    - secrets.example.yaml
    - tests/conftest.py
    - tests/test_import_safety.py
    - tests/test_revision_secrets.py
  modified:
    - run_eval.py
    - .gitignore
key-decisions:
  - "Removed import-time diagnostics and provider smoke code from run_eval.py instead of preserving it behind module-scope guards."
  - "Kept local secrets.yaml support but committed only placeholder values in secrets.example.yaml."
patterns-established:
  - "Import-safety tests use subprocesses and assert that unsafe output markers are absent."
  - "Tests use fake sentinel values only and never read the real local secrets.yaml."
requirements-completed: [REPRO-05, REPRO-06]
duration: 18min
completed: 2026-05-16
---

# Phase 01: Reproducibility and Safety Foundation - Plan 02 Summary

**Import-safe evaluator modules with explicit provider smoke execution and a unified secret redaction boundary**

## Performance

- **Duration:** 18 min
- **Started:** 2026-05-16T03:26:00Z
- **Completed:** 2026-05-16T03:44:04Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Removed `run_eval.py` import-time filesystem diagnostics, local config printing, and provider smoke request code.
- Added `revision_provider_smoke.py` as an explicit CLI that constructs providers only inside `main()`.
- Added `revision_secrets.py` with YAML/JSON local config loading plus recursive mapping/text redaction.
- Added `secrets.example.yaml` and `.gitignore` entries for local secret files and `results/revision/`.
- Added focused import-safety and redaction tests using fake sentinel values only.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Import safety tests** - `c073f71` (`test(01-02): add failing import safety coverage`)
2. **Task 1 GREEN: Import-safe evaluator and explicit smoke CLI** - `45a4f28` (`feat(01-02): isolate provider smoke from imports`)
3. **Task 2 RED: Secret redaction tests** - `73a2e74` (`test(01-02): add failing secret redaction coverage`)
4. **Task 2 GREEN: Secret redaction boundary** - `a9949a7` (`feat(01-02): add secret redaction boundary`)

## Files Created/Modified

- `run_eval.py` - Removed import-time secret/config diagnostics and provider smoke request code.
- `revision_provider_smoke.py` - Adds explicit provider smoke CLI with provider construction inside `main()`.
- `revision_secrets.py` - Adds local YAML/JSON config loader and redaction helpers.
- `secrets.example.yaml` - Provides placeholder-only provider/pricing structure.
- `.gitignore` - Ignores local secret files and generated revision output directories.
- `tests/test_import_safety.py` - Verifies evaluator and smoke imports are quiet and offline.
- `tests/test_revision_secrets.py` - Verifies config loading and fake sentinel redaction.
- `tests/conftest.py` - Adds repo root to pytest import path for flat-script modules.

## Decisions Made

- Provider smoke remains available but must be requested through `revision_provider_smoke.py`.
- Redaction is centralized in `revision_secrets.py` so future artifacts can share one safe output path.
- Added a minimal pytest import-path shim instead of migrating scripts into a package.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added pytest import-path shim**
- **Found during:** Task 2 (secret redaction tests)
- **Issue:** `uv run python` could import root-level modules, but pytest collection did not reliably include the repository root for new flat-script helper modules.
- **Fix:** Added `tests/conftest.py` to insert the repository root into `sys.path`.
- **Files modified:** `tests/conftest.py`
- **Verification:** `uv run pytest tests/test_revision_secrets.py -q` and the combined Plan 02 pytest command passed.
- **Committed in:** `a9949a7`

---

**Total deviations:** 1 auto-fixed (1 blocking).
**Impact on plan:** Preserves the planned flat-script workflow without introducing a package migration.

## Issues Encountered

- The initial RED import-safety test exposed the expected unsafe import-time output and missing smoke CLI.
- No provider requests, real secret reads, or live CAPTCHA automation were introduced.

## Verification

- `uv run pytest tests/test_import_safety.py tests/test_revision_secrets.py -q` passed.
- `uv run python -c "import run_eval; import run_single_experiment; import revision_provider_smoke; import revision_secrets"` exited 0 with no output.
- `rg` acceptance checks verified removed unsafe markers, smoke `main()` guard, redaction exports, placeholder example tokens, and ignore entries.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 03 can define revision artifacts without risking import-time credential output or accidental provider calls.

## Self-Check: PASSED

All key files exist on disk, acceptance checks passed, and required commits are present.

---
*Phase: 01-reproducibility-and-safety-foundation*
*Completed: 2026-05-16*
