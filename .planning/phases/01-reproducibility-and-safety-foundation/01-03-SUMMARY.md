---
phase: 01-reproducibility-and-safety-foundation
plan: "03"
subsystem: artifacts
tags: [pydantic, jsonl, manifest, summary, provenance]
requires:
  - phase: 01-01
    provides: uv-backed pytest execution and locked dependencies
provides:
  - Versioned RunManifest, AttemptRecord, and SummaryRow schemas
  - Append-only RevisionArtifactWriter under results/revision/<run_id>/
  - Deterministic prompt and few-shot hash helpers for run provenance
affects: [phase-01, preflight, evaluator, revision-results]
tech-stack:
  added: [pydantic]
  patterns:
    - Pydantic v2 models define revision artifact schemas
    - Summary CSV/JSON files are derived from attempts.jsonl
key-files:
  created:
    - revision_artifacts.py
    - tests/test_revision_artifacts.py
  modified: []
key-decisions:
  - "Revision summaries are derived from persisted attempts.jsonl instead of in-memory aggregate state."
  - "Code revision dirty checks are source-scoped and do not inspect local secret configuration."
patterns-established:
  - "Artifact paths are centralized through RevisionArtifactWriter properties."
  - "Prompt and few-shot provenance uses SHA-256 digests instead of raw inline prompt text."
requirements-completed: [REPRO-03, REPRO-04, REPRO-06]
duration: 12min
completed: 2026-05-16
---

# Phase 01: Reproducibility and Safety Foundation - Plan 03 Summary

**Versioned revision artifact schemas with append-only attempt logging and derived summaries**

## Performance

- **Duration:** 12 min
- **Started:** 2026-05-16T03:35:00Z
- **Completed:** 2026-05-16T03:46:47Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments

- Added Pydantic v2 schemas for `PromptConfig`, `RunManifest`, `AttemptRecord`, and `SummaryRow`.
- Added `RevisionArtifactWriter` for `run_manifest.json`, append-only `attempts.jsonl`, derived `summary.csv`, and derived `summary.json`.
- Added SHA-256 helpers for files and inline text, plus dependency and code revision metadata helpers.
- Added focused tests for schema serialization, manifest ordering, JSONL append behavior, derived summaries, output directory guards, and prompt/few-shot hash fields.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Revision artifact contract tests** - `b746af1` (`test(01-03): add failing revision artifact contract`)
2. **Task 1 GREEN: Revision artifact writer** - `48ea2d6` (`feat(01-03): add revision artifact writer`)

## Files Created/Modified

- `revision_artifacts.py` - Defines schema constants, Pydantic models, provenance helpers, hash helpers, and the artifact writer.
- `tests/test_revision_artifacts.py` - Verifies schema, append-only behavior, summary derivation, hash fields, and output directory safety.

## Decisions Made

- `RevisionArtifactWriter` refuses existing run directories unless `overwrite=True` or `resume=True`.
- `write_summaries_from_attempts()` reads `attempts.jsonl` and derives both CSV and JSON summaries from persisted rows.
- `collect_code_revision()` records commit and dirty status without reading local secret config.

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope change.

## Issues Encountered

None.

## Verification

- `uv run pytest tests/test_revision_artifacts.py -q` passed.
- `uv run python -c "from revision_artifacts import RunManifest, AttemptRecord, SummaryRow, RevisionArtifactWriter; print(RunManifest.model_json_schema()['title'])"` printed `RunManifest`.
- `rg` acceptance checks verified schema constants, model classes, writer methods, dependency/hash helpers, and prompt/few-shot hash fields.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 04 can import `revision_artifacts.py` for offline preflight reports, output path calculation, and deterministic prompt/few-shot hashes.

## Self-Check: PASSED

All key files exist on disk, acceptance checks passed, and required commits are present.

---
*Phase: 01-reproducibility-and-safety-foundation*
*Completed: 2026-05-16*
