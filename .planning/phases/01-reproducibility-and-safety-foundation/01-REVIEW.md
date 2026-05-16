---
phase: 01-reproducibility-and-safety-foundation
reviewed: 2026-05-16T04:03:34Z
depth: standard
files_reviewed: 17
files_reviewed_list:
  - .gitignore
  - README.md
  - pyproject.toml
  - revision_artifacts.py
  - revision_preflight.py
  - revision_provider_smoke.py
  - revision_secrets.py
  - run_eval.py
  - secrets.example.yaml
  - tests/conftest.py
  - tests/test_import_safety.py
  - tests/test_revision_artifacts.py
  - tests/test_revision_preflight.py
  - tests/test_revision_run_contract.py
  - tests/test_revision_secrets.py
  - tests/test_scoring_regressions.py
  - tests/test_task_contracts.py
findings:
  critical: 1
  warning: 3
  info: 0
  total: 4
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-05-16T04:03:34Z
**Depth:** standard
**Files Reviewed:** 17
**Status:** issues_found

## Summary

Reviewed the Phase 1 reproducibility, preflight, secret-safety, revision artifact, run-contract, and regression-test changes. The main safety issue is that run IDs are treated as filesystem paths before destructive overwrite operations. The main correctness issues are task alias drift between preflight and evaluation, incomplete dirty-tree capture in run manifests, and resume mode double-counting attempts.

Validation observed during review: `python -m pytest` passed (`31 passed`). `python -m ruff check ...` could not run because `ruff` is not installed in the active Python environment.

## Critical Issues

### CR-01: Run IDs Can Escape The Output Root And Be Deleted On Overwrite

**File:** `/Users/ukun/Desktop/captcha/revision_artifacts.py:150`
**Also Affected:** `/Users/ukun/Desktop/captcha/revision_artifacts.py:166`, `/Users/ukun/Desktop/captcha/revision_artifacts.py:170`, `/Users/ukun/Desktop/captcha/revision_preflight.py:176`, `/Users/ukun/Desktop/captcha/revision_preflight.py:222`

**Issue:** `revision_run_dir()` returns `Path(output_root) / run_id` without rejecting absolute paths, `..` segments, path separators, or empty/special names. In `RevisionArtifactWriter`, `overwrite=True` then calls `shutil.rmtree(self._run_dir)`. In preflight, `_write_report()` performs the same overwrite deletion. A malformed run ID can therefore write artifacts outside `output_root`; with overwrite enabled it can delete arbitrary reachable directories.

**Fix:**
```python
import re

_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def revision_run_dir(output_root: str | Path, run_id: str) -> Path:
    if not _RUN_ID_RE.fullmatch(run_id):
        raise ValueError("run_id must contain only letters, numbers, dot, underscore, or hyphen")
    root = Path(output_root).resolve()
    run_dir = (root / run_id).resolve()
    if not run_dir.is_relative_to(root):
        raise ValueError("run_id resolves outside output_root")
    return run_dir
```

Use this single helper in both `RevisionArtifactWriter` and `revision_preflight`, and add tests for absolute paths, `..`, slash-containing IDs, `overwrite=True`, and `resume=True`.

## Warnings

### WR-01: Preflight Accepts A Task Alias That The Evaluator Rejects

**File:** `/Users/ukun/Desktop/captcha/revision_preflight.py:15`
**Also Affected:** `/Users/ukun/Desktop/captcha/revision_preflight.py:16`, `/Users/ukun/Desktop/captcha/run_eval.py:1803`, `/Users/ukun/Desktop/captcha/run_eval.py:1807`

**Issue:** `revision_preflight` accepts `Connect_icon` and reports the canonical task type as `Connect_Icon`, with an explicit dataset directory alias. `run_eval.build_tasks()` does not apply the same alias map; it checks the raw type against `SUPPORTED_TYPES` and builds the dataset path directly from the type string. As a result, a type accepted by preflight can be skipped by the actual evaluator, and canonical `Connect_Icon` relies on case-insensitive filesystems instead of the explicit `Connect_icon` dataset directory.

**Fix:** Move task canonicalization and dataset-directory mapping into a shared helper used by both preflight and evaluation.
```python
canonical = TASK_ALIASES.get(requested_type, requested_type)
if canonical not in SUPPORTED_TYPES:
    raise ValueError(f"Unsupported task type: {requested_type}")
type_dir = os.path.join(dataset_root, DATASET_DIR_ALIASES.get(canonical, canonical))
```

Add regression tests that call `build_tasks(..., ["Connect_icon"])` and `build_tasks(..., ["Connect_Icon"])` and assert both produce tasks using the same dataset directory.

### WR-02: Run Manifests Can Report Clean Code With Untracked Source Files

**File:** `/Users/ukun/Desktop/captcha/revision_artifacts.py:111`

**Issue:** `collect_code_revision()` calls `git status --short --untracked-files=no`, so a new untracked source or test file under the reviewed source paths is ignored. The manifest can record `"dirty": false` even though the run depends on uncommitted code that cannot be reconstructed from the recorded commit.

**Fix:** Include untracked files for the source-scoped paths while continuing to exclude generated outputs and local secret config.
```python
dirty_output = _run_git(
    ["status", "--short", "--untracked-files=normal", "--", *_DIRTY_CHECK_PATHS]
)
```

Add a unit test that creates an untracked source file in a temporary git repository and verifies `collect_code_revision()["dirty"]` is true.

### WR-03: Resume Mode Re-Appends Duplicate Attempt Records

**File:** `/Users/ukun/Desktop/captcha/revision_artifacts.py:171`
**Also Affected:** `/Users/ukun/Desktop/captcha/revision_artifacts.py:209`, `/Users/ukun/Desktop/captcha/revision_artifacts.py:228`, `/Users/ukun/Desktop/captcha/run_eval.py:2879`

**Issue:** `resume=True` only allows reusing an existing run directory. It does not load completed attempt IDs or prevent duplicate appends. `run_eval()` always emits attempt IDs ending in `:1`, so rerunning the same revision run with resume appends duplicate attempts and `write_summaries_from_attempts()` double-counts them.

**Fix:** Either reject duplicate attempt IDs when appending, or implement actual resume behavior by loading existing `attempt_id`s before the loop and skipping completed tasks.
```python
existing_attempt_ids = {attempt.attempt_id for attempt in revision_writer.iter_attempts()}
attempt_id = f"{revision_run_id}:{task.type}:{task.puzzle_id}:1"
if attempt_id in existing_attempt_ids:
    continue
revision_writer.append_attempt(AttemptRecord(attempt_id=attempt_id, ...))
```

Add a test that writes a partial `attempts.jsonl`, reruns with `resume_revision_output=True`, and asserts summaries count each attempt ID once.

---

_Reviewed: 2026-05-16T04:03:34Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
