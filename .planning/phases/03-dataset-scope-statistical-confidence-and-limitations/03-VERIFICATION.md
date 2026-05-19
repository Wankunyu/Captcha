---
phase: 03-dataset-scope-statistical-confidence-and-limitations
verified: 2026-05-19T01:53:51Z
status: passed
score: "10/10 must-haves verified"
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: "9/10"
  gaps_closed:
    - "Selective validation-slice outcomes can be ingested from offline artifacts and compared against original-dataset conclusions with agreement, divergence, and caveats."
  gaps_remaining: []
  regressions: []
residual_risks:
  - id: WR-02
    severity: warning
    source: "03-REVIEW.md"
    summary: "retry_calibration.py family rows use unweighted mean rates while summing counts; non-blocking for STAT-06 because task-family prediction-error rows exist, but interpretation should stay caveated."
  - id: WR-03
    severity: warning
    source: "03-REVIEW.md"
    summary: "Explicit Phase 3 CLI output path overrides can bypass the default revision_run_dir traceability contract; defaults remain safe and tested."
  - id: IN-01
    severity: info
    source: "03-REVIEW.md"
    summary: "wilson_interval(1, 0) would return an empty-sample interval before impossible-count validation; current loaders/tests do not produce this case."
---

# Phase 3: Dataset Scope, Statistical Confidence, and Limitations Verification Report

**Phase Goal:** Researchers can quantify uncertainty, dataset support, removed/incompatible task types, threshold sensitivity, retry-model validity, infrastructure-vs-scientific failures, and benchmark generalizability limits.
**Verified:** 2026-05-19T01:53:51Z
**Status:** passed
**Re-verification:** Yes - after gap closure commit `186f138 fix(03): classify near-broken validation labels as borderline`

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Researchers can generate a dataset scope audit with included, excluded, incompatible, and underpowered CAPTCHA families with counts and reasons. | VERIFIED | `dataset_scope_audit.py` remains substantive and wired to local dataset/result inputs; focused Phase 3 suite passes. |
| 2 | The artifact set identifies the two removed CaptchaWorld task types and explains static-pipeline incompatibility. | VERIFIED | `Hold_Button(Not Used)` and `Slide_Puzzle(Not Used)` reasons remain asserted in source and tests. |
| 3 | Dataset contribution notes cover cleaning, standardization, label/metadata alignment, answer-format normalization, task-family grouping, and removal decisions. | VERIFIED | `extended_dataset_manifest.py` and tests retain all required contribution-note headings and phrases. |
| 4 | Extended evidence remains separated as original, supplemented-category, or new-category rows. | VERIFIED | Manifest schemas and tests preserve `evidence_origin` and `slice_type` separation. |
| 5 | Selective validation-slice outcomes can be ingested and compared against original conclusions with agreement, divergence, and caveats. | VERIFIED | Previous gap closed: `_direction()` now checks `borderline`/`near` before `broken`; direct behavior check passed and new regression asserts `borderline/near-broken` yields `supports_original`. |
| 6 | Pass-rate summaries report Wilson confidence intervals by task and task family. | VERIFIED | `statistical_confidence.py` retains Wilson interval implementation, task and family aggregation, and passing focused tests. |
| 7 | Hard, borderline, and broken labels show margin relative to the 40 percent operational cutoff and flag threshold-sensitive families. | VERIFIED | Threshold code still emits `margin_to_cutoff`, 30-50 review-band flags, trend sensitivity, and operational-cutoff caveat. |
| 8 | Retry predictions are compared against observed retry or adaptive-compatible outcomes with prediction error by task family. | VERIFIED | `retry_calibration.py` retains Exp2 formula imports, signed/absolute errors, and family output coverage. |
| 9 | Scientific, protocol, and infrastructure failures remain separate, and infrastructure/protocol failures are not counted as structural-hardness evidence. | VERIFIED | `failure_taxonomy.py` retains raw/scientific rate separation and claim-use caveats. |
| 10 | Limitations prose and README avoid population-level overclaiming and keep Phase 3 offline, dataset-based, and secret-safe. | VERIFIED | `limitations_summary.py` and README retain exact claim-boundary language and offline/no-browser/no-secret Phase 3 guidance. |

**Score:** 10/10 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `phase3_artifacts.py` | Strict Phase 3 schemas and writers | VERIFIED | 382 lines; row schemas and writer helpers remain present. |
| `dataset_scope_audit.py` | Dataset scope audit CLI | VERIFIED | 363 lines; imports task aliases, supported types, dataset aliases, family metadata, and `revision_run_dir`. |
| `extended_dataset_manifest.py` | Extended manifest, validation comparison, slice task, and notes CLI | VERIFIED | 516 lines; `_direction()` fix verified and regression test added. |
| `statistical_confidence.py` | Confidence and threshold-sensitivity CLI | VERIFIED | 813 lines; Wilson, threshold, trend, and output helpers remain present. |
| `retry_calibration.py` | Retry calibration task and family artifacts | VERIFIED | 679 lines; Exp2 prediction formulas and retry error fields remain present. |
| `failure_taxonomy.py` | Failure taxonomy artifacts | VERIFIED | 363 lines; failure-class rates and caveats remain present. |
| `limitations_summary.py` | Limitations summary and artifact index | VERIFIED | 498 lines; consumes all Phase 3 artifacts and emits paper-safe prose/index. |
| `README.md` | Offline Phase 3 reproduction commands | VERIFIED | Phase 3 section documents offline dataset-based commands and safety boundaries. |
| `tests/test_extended_dataset_manifest.py` | Regression coverage for fixed gap | VERIFIED | New near-broken regression is present and passes. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `dataset_scope_audit.py` | `run_eval.py` task contracts | Imports `SUPPORTED_TYPES`, `TASK_ALIASES`, `DATASET_DIR_ALIASES` | VERIFIED | Required imports are present. |
| `dataset_scope_audit.py` | `visualize_results.py` family metadata | `CAPTCHAVisualizer.TASK_FAMILY` | VERIFIED | Required import and usage remain present. |
| Phase 3 CLIs | revision-safe default outputs | `revision_artifacts.revision_run_dir(output_root, run_id)` | VERIFIED | Required default-output path hook remains present across CLIs; explicit override path safety remains WR-03 warning. |
| `statistical_confidence.py` | Phase 3 schemas and trend evidence | Row models plus adaptive/extended inputs | VERIFIED | Confidence, threshold, adaptive trend, and extended validation hooks remain present. |
| `retry_calibration.py` | Exp2 Bernoulli formulas | `predict_q_from_exp2`, `predict_A_from_exp2` | VERIFIED | Required imports and formula coverage remain present. |
| `failure_taxonomy.py` | Adaptive/failure evidence | CSV/JSON loaders and claim-use fields | VERIFIED | Failure counts, raw/scientific rates, and claim-use caveats remain present. |
| `limitations_summary.py` | All Phase 3 artifact inputs | Required CLI paths and row loaders | VERIFIED | Integrated test covers all expected artifact filenames in the index. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `dataset_scope_audit.py` | `rows` | Local dataset directories and `results/exp1`-`exp4` | Yes | FLOWING |
| `extended_dataset_manifest.py` | `comparison_rows` | Local manifest, validation outcomes, original conclusions | Yes - near-broken/borderline path now classifies correctly | FLOWING |
| `statistical_confidence.py` | `rows`, `threshold_rows` | Result CSVs plus optional adaptive/extended artifacts | Yes | FLOWING |
| `retry_calibration.py` | `rows`, `family_rows` | Exp2, Exp3, and optional adaptive summary artifacts | Yes | FLOWING |
| `failure_taxonomy.py` | `rows` | Adaptive summary or retry calibration CSV/JSON | Yes | FLOWING |
| `limitations_summary.py` | rendered markdown and index | Explicit Phase 3 artifact paths | Yes | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Previous gap direct behavior | `uv run python -c "from extended_dataset_manifest import _direction; assert _direction('borderline/near-broken', None) == 'borderline'; assert _direction('near-broken', None) == 'borderline'; assert _direction('broken', None) == 'broken'"` | Printed `direction parsing ok` | PASS |
| Extended manifest focused tests | `uv run pytest tests/test_extended_dataset_manifest.py -q` | Passed; third-party matplotlib/pyparsing deprecation warnings only | PASS |
| Full focused Phase 3 tests | `uv run pytest tests/test_phase3_artifacts.py tests/test_dataset_scope_audit.py tests/test_extended_dataset_manifest.py tests/test_statistical_confidence.py tests/test_retry_calibration.py tests/test_failure_taxonomy.py tests/test_limitations_summary.py -q` | 47 passed; third-party matplotlib/pyparsing deprecation warnings only | PASS |
| Focused Phase 3 lint | `uv run ruff check phase3_artifacts.py dataset_scope_audit.py extended_dataset_manifest.py statistical_confidence.py retry_calibration.py failure_taxonomy.py limitations_summary.py tests/test_phase3_artifacts.py tests/test_dataset_scope_audit.py tests/test_extended_dataset_manifest.py tests/test_statistical_confidence.py tests/test_retry_calibration.py tests/test_failure_taxonomy.py tests/test_limitations_summary.py` | All checks passed | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| STAT-01 | 03-01, 03-04 | Dataset scope audit reports included, excluded, incompatible, underpowered families, counts, and reasons. | SATISFIED | `dataset_scope_audit.py` and tests retain status/reason coverage. |
| STAT-02 | 03-01, 03-04 | Removed CaptchaWorld task types are identified with incompatibility reasons. | SATISFIED | Removed-task constants, reasons, tests, and limitations prose remain present. |
| STAT-03 | 03-01, 03-04 | Dataset contribution notes cover cleaning, standardization, alignment, answer normalization, removal, grouping. | SATISFIED | Contribution-note headings and exact separation phrase remain tested. |
| STAT-04 | 03-02, 03-04 | Confidence intervals by task and task family. | SATISFIED | Wilson interval and aggregation code remain present; focused tests pass. |
| STAT-05 | 03-02, 03-04 | Threshold labels report margin and threshold-sensitive families without universalizing cutoff. | SATISFIED | Threshold fields and exact caveat text remain present; focused tests pass. |
| STAT-06 | 03-03, 03-04 | Retry predictions are compared to observed retry/adaptive outcomes with family prediction error. | SATISFIED WITH RESIDUAL RISK | Task/family prediction-error artifacts remain covered; WR-02 notes unweighted family means are a warning, not a blocker. |
| STAT-07 | 03-03, 03-04 | Scientific failures are separated from provider/protocol/infrastructure errors and CaptchaWorld scope is bounded. | SATISFIED | Failure taxonomy and limitations/README caveats remain present; focused tests pass. |

No Phase 3 requirement IDs are orphaned. STAT-01 through STAT-07 appear in Phase 3 plan frontmatter and are covered above.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `retry_calibration.py` | 388-414 | Family rows combine summed counts with unweighted mean rates | Warning | Preserved from 03-REVIEW WR-02; interpretation risk only, not a goal blocker. |
| Phase 3 CLIs | multiple | Explicit output path overrides use raw `Path(args.output_*)` | Warning | Preserved from 03-REVIEW WR-03; defaults are safe and tested. |
| `statistical_confidence.py` | 67 | `wilson_interval(1, 0)` returns `(None, None)` before impossible-count validation | Info | Preserved from 03-REVIEW IN-01; current loaders/tests do not produce impossible counts. |

### Human Verification Required

None. Phase 3 produces offline scripts and machine-readable/text artifacts that were verified programmatically. No visual, live-service, or browser behavior is required for this phase.

### Gaps Summary

No blocking gaps remain. The previous gap is closed by commit `186f138`: labels containing `borderline` or `near` are classified as borderline before checking for `broken`, and the new regression test confirms `original_conclusion_label="borderline/near-broken"` with a 0.40 validation rate reports `supports_original`.

Later roadmap phases cover baseline comparisons, defense methodology, and final claim packaging; none are needed to close Phase 3 goal achievement.

---

_Verified: 2026-05-19T01:53:51Z_
_Verifier: Codex (gsd-verifier role)_
