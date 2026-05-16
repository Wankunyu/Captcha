---
phase: 01-reproducibility-and-safety-foundation
plan: "01"
subsystem: tooling
tags: [uv, pyproject, pytest, ruff, reproducibility]
requires: []
provides:
  - Machine-readable dependency and tool manifest for the existing flat-script workflow
  - Locked uv dependency resolution for local reproduction
  - README install, validation, preflight, and revision artifact layout guidance
affects: [phase-01, reproducibility, local-validation]
tech-stack:
  added: [uv, pytest, ruff, pydantic]
  patterns:
    - Flat script project configured with tool.uv.package=false
    - Local validation standardized through uv run pytest and uv run ruff check .
key-files:
  created:
    - pyproject.toml
    - uv.lock
  modified:
    - README.md
key-decisions:
  - "Kept the project as root-level scripts and used [tool.uv] package=false instead of adding a src/ package."
  - "Documented credential setup by filename and placeholder only, without copying local secret values."
patterns-established:
  - "Dependency pins live in pyproject.toml and are resolved by uv.lock."
  - "Phase 1 validation commands are documented before paid provider runs."
requirements-completed: [REPRO-01]
duration: 15min
completed: 2026-05-16
---

# Phase 01: Reproducibility and Safety Foundation - Plan 01 Summary

**uv-backed dependency manifest, lockfile, and README validation workflow for the existing flat experiment scripts**

## Performance

- **Duration:** 15 min
- **Started:** 2026-05-16T03:25:31Z
- **Completed:** 2026-05-16T03:38:57Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added `pyproject.toml` with pinned runtime dependencies, dev tools, pytest settings, and ruff settings.
- Generated `uv.lock` from the manifest with `uv lock`.
- Updated `README.md` with reproducible install commands, local validation commands, offline preflight guidance, revision artifact layout, and secret-safe configuration guidance.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add the uv project manifest and lockfile** - `9005e63` (`build(01-01): add uv project manifest`)
2. **Task 2: Document reproducible install and validation commands** - `a1b55c6` (`docs(01-01): document reproducible validation workflow`)

## Files Created/Modified

- `pyproject.toml` - Declares pinned dependencies, `uv` flat-project behavior, pytest config, and ruff config.
- `uv.lock` - Locks the dependency graph generated from `pyproject.toml`.
- `README.md` - Documents `uv sync --locked`, `uv run pytest`, `uv run ruff check .`, offline preflight, revision artifact paths, and credential file guidance.

## Decisions Made

- Used `tool.uv.package = false` to preserve the current root-level script workflow.
- Kept provider SDK versions pinned to the researched working versions rather than upgrading them during the reproducibility foundation step.
- Replaced credential-shaped README examples with placeholder-only guidance tied to `secrets.example.yaml` and local `secrets.yaml`.

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope change.

## Issues Encountered

- `uv` was not installed in the active shell, so `uv==0.11.14` was installed before generating `uv.lock`.
- `uv lock` and `uv run` required access to the user-level uv cache outside the sandbox; both commands completed successfully after approval.

## Verification

- `python3 -c "import pathlib, tomllib; ..."` verified manifest structure, required pins, and lockfile presence.
- `uv lock --check` verified the lockfile matches `pyproject.toml`.
- `uv run python -c "import pathlib, tomllib; ..."` verified `tool.uv.package` through the locked environment.
- `rg` acceptance checks verified README and manifest content.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 02 can rely on `uv run pytest` and the locked dependency environment while removing import-time side effects and adding secret-safety tests.

## Self-Check: PASSED

All key files exist on disk, acceptance checks passed, and required commits are present.

---
*Phase: 01-reproducibility-and-safety-foundation*
*Completed: 2026-05-16*
