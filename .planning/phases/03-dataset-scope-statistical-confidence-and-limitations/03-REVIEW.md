---
phase: 03-dataset-scope-statistical-confidence-and-limitations
reviewed: 2026-05-19T01:41:19Z
depth: standard
files_reviewed: 15
files_reviewed_list:
  - dataset_scope_audit.py
  - extended_dataset_manifest.py
  - failure_taxonomy.py
  - limitations_summary.py
  - phase3_artifacts.py
  - retry_calibration.py
  - statistical_confidence.py
  - tests/test_dataset_scope_audit.py
  - tests/test_extended_dataset_manifest.py
  - tests/test_failure_taxonomy.py
  - tests/test_limitations_summary.py
  - tests/test_phase3_artifacts.py
  - tests/test_retry_calibration.py
  - tests/test_statistical_confidence.py
  - README.md
findings:
  critical: 0
  warning: 3
  info: 1
  total: 4
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-05-19T01:41:19Z
**Depth:** standard
**Files Reviewed:** 15
**Status:** issues_found

## Summary

Reviewed the Phase 3 offline dataset/statistical artifact scripts, their tests, and README guidance. The implementation stays dataset-based and does not introduce live CAPTCHA/browser automation or direct `secrets.yaml` reads/prints in the Phase 3 commands. Default run-id directories use `revision_artifacts.revision_run_dir()`, and the 40% threshold language is correctly framed as an operational heuristic rather than a universal security boundary.

The main issues are data-correctness and path-safety risks: one label parser misclassifies `borderline/near-broken`, retry family summaries use unweighted means for aggregate-looking rows, and explicit output path overrides bypass the run-directory safety/traceability contract.

## Warnings

### WR-01: `borderline/near-broken` Labels Are Parsed As `broken`

**File:** `extended_dataset_manifest.py:215`

**Issue:** `_direction()` checks `"broken"` before `"borderline"`/`"near"`. The threshold artifact emits labels such as `borderline/near-broken`, so an original conclusion with that label is classified as `broken` instead of `borderline`. Extended validation comparisons can therefore report false divergences or false support when the original result was intended to remain in the caution band.

**Fix:**

```python
def _direction(label: str | None, rate: float | None, cutoff: float = 0.40) -> str | None:
    if label:
        lowered = label.lower()
        if "borderline" in lowered or "near" in lowered:
            return "borderline"
        if "hard" in lowered:
            return "hard"
        if "broken" in lowered:
            return "broken"
    ...
```

Add a regression test where `original_conclusion_label == "borderline/near-broken"` and validation stays borderline, expecting `supports_original`.

### WR-02: Retry Family Rows Report Unweighted Mean Rates As Family Aggregates

**File:** `retry_calibration.py:388`

**Issue:** `build_retry_calibration_family_rows()` sums `sample_count`, `scientific_wrong_count`, `protocol_failure_count`, and `infrastructure_failure_count`, but computes `exp2_pass_at_1`, predicted success, observed success, errors, `raw_observed_rate`, and `scientific_rate` with plain `_row_mean()`. For task families with uneven task sample sizes or failure denominators, the family row can materially misstate calibration and scientific-rate evidence while looking like an aggregate row.

**Fix:** Compute family-level rates from summed numerators/denominators, or rename these fields as task-mean metrics and add separate weighted aggregate fields. A safer aggregate pattern is:

```python
total_sample_count = sum(row.sample_count for row in group_rows)
exp2_pass_at_1 = _weighted_row_mean(group_rows, "exp2_pass_at_1", "sample_count")
bernoulli_success_at_k = _weighted_row_mean(group_rows, "bernoulli_success_at_k", "sample_count")
```

For `raw_observed_rate` and `scientific_rate`, preserve enough adaptive outcome counts to recompute from summed successes and failure-class denominators instead of averaging task-level ratios.

### WR-03: Explicit Output Path Overrides Bypass Run-Directory Path Safety

**Files:** `dataset_scope_audit.py:326`, `extended_dataset_manifest.py:447`, `failure_taxonomy.py:315`, `limitations_summary.py:267`, `retry_calibration.py:520`, `statistical_confidence.py:365`

**Issue:** Default output paths are anchored under `revision_run_dir(output_root, run_id)`, but every Phase 3 CLI accepts explicit output path overrides and converts them directly with `Path(args.output_...)`. A typo or path traversal such as `--output-json ../../artifact.json` can write outside the run directory, weakening reproducibility and artifact traceability. This is not a live-service security issue, but it is a path-safety and experiment-integrity risk for generated revision artifacts.

**Fix:** Resolve explicit overrides relative to the run directory and reject paths outside it, unless the CLI deliberately exposes an opt-in escape hatch.

```python
def _output_path(raw_path: str | None, default_path: Path, run_dir: Path) -> Path:
    candidate = (run_dir / raw_path).resolve() if raw_path else default_path.resolve()
    if not candidate.is_relative_to(run_dir.resolve()):
        raise ValueError("output paths must stay inside the revision run directory")
    return candidate
```

Add tests for each CLI covering `--output-* ../outside.csv` and absolute outside paths.

## Info

### IN-01: Wilson Interval Accepts Impossible Zero-Attempt Success Counts

**File:** `statistical_confidence.py:67`

**Issue:** `wilson_interval()` returns `(None, None)` when `n_attempts == 0` before validating that `n_success` is also zero. A direct call like `wilson_interval(1, 0)` silently treats impossible data as an empty sample.

**Fix:** Validate `n_attempts >= 0` and `0 <= n_success <= n_attempts` before the zero-attempt fast path.

---

## Verification

Ran:

```bash
uv run pytest tests/test_dataset_scope_audit.py tests/test_extended_dataset_manifest.py tests/test_failure_taxonomy.py tests/test_limitations_summary.py tests/test_phase3_artifacts.py tests/test_retry_calibration.py tests/test_statistical_confidence.py -q
```

Result: 46 passed; only third-party deprecation warnings from matplotlib/pyparsing.

_Reviewed: 2026-05-19T01:41:19Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
