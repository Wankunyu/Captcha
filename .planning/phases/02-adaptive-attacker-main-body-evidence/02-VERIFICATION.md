---
phase: 02-adaptive-attacker-main-body-evidence
verified: 2026-05-18T04:33:35Z
status: passed
score: "5/5 must-haves verified"
overrides_applied: 0
human_verification_required: false
re_verification: false
requirements:
  ADAPT-01: passed
  ADAPT-02: passed
  ADAPT-03: passed
  ADAPT-04: passed
  ADAPT-05: passed
  ADAPT-06: passed
automated_checks:
  uv_lock_check: passed
  pytest_all: passed
  pytest_adaptive_focused: passed
  ruff_check: passed
  adaptive_preflight_spot_check: passed
  adaptive_compare_help: passed
  schema_drift: passed
  code_review: clean
---

# Phase 2: Adaptive Attacker Main-Body Evidence Verification Report

**Phase Goal:** Researchers can evaluate the session-memory adaptive attacker and produce main-body-ready evidence explaining which hard CAPTCHA families remain robust.
**Verified:** 2026-05-18T04:33:35Z
**Status:** passed
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Researcher can run a session-memory adaptive attacker that carries task-level memory across fresh CAPTCHA instances. | VERIFIED | `adaptive_attacker.py` groups tasks by task type, shuffles deterministic without-replacement pools, removes used puzzle IDs on resume, carries `policy_state` per task type, and appends updated state to each attempt (`adaptive_attacker.py:34`, `adaptive_attacker.py:466`, `adaptive_attacker.py:559`, `adaptive_attacker.py:566`, `adaptive_attacker.py:740`). Tests assert no duplicate puzzle IDs and correct budget/first-success/pool stop behavior (`tests/test_adaptive_attacker.py:329`, `tests/test_adaptive_attacker.py:348`, `tests/test_adaptive_attacker.py:360`). |
| 2 | Adaptive attacker semantics explicitly state binary pass/fail feedback only, with no ground-truth labels, coordinates, counts, or corrective hints. | VERIFIED | Constants lock `feedback_mode` to `binary-pass-fail` and `memory_mode` to `explicit-policy-notes` (`adaptive_artifacts.py:18`). Reflection prompt uses `Feedback: FAIL` and explicitly forbids attempted answers, counts, coordinates, ground truth, corrective hints, and transcripts from memory (`adaptive_attacker.py:72`, `adaptive_attacker.py:95`). Policy-state validators reject ground-truth, raw-response, coordinate, count, selected, picked, image-name, and numeric answer details (`adaptive_artifacts.py:36`, `adaptive_artifacts.py:47`). Tests cover banned text and sentinel non-leakage (`tests/test_adaptive_artifacts.py:191`, `tests/test_adaptive_attacker.py:501`, `tests/test_adaptive_end_to_end.py:157`). |
| 3 | Adaptive attempt records capture prior failures, policy state, prompt adaptation metadata, parsed answer, correctness, latency, token usage, cumulative cost, and stopping reason. | VERIFIED | `AdaptiveAttemptRecord` defines all required fields (`adaptive_artifacts.py:107`). The run loop populates `prior_failures`, `policy_state_before/after`, `prompt_adaptation_metadata`, `parsed_answer`, `correct`, latency, tokens, cost, cumulative cost/latency, and `stopping_reason` before append-only write (`adaptive_attacker.py:702`, `adaptive_attacker.py:711`). `AdaptiveArtifactWriter.append_attempt()` persists one JSONL row and rejects duplicate IDs (`adaptive_artifacts.py:329`). |
| 4 | Fixed retry, Bernoulli Success@k, and adaptive outcomes are compared under the same task-family budget. | VERIFIED | `adaptive_compare.build_comparison_rows()` requires one `attempt_budget_k`, filters adaptive summaries to the same `attempt_budget_k`, uses the same k for Bernoulli `predict_q_from_exp2()` and `predict_A_from_exp2()`, and emits the same k on every comparison row (`adaptive_compare.py:114`, `adaptive_compare.py:131`, `adaptive_compare.py:158`, `adaptive_compare.py:214`, `adaptive_compare.py:468`). Tests assert Exp2 pass@1, Bernoulli Success@k, fixed retry, and adaptive fields are merged under `attempt_budget_k=3` (`tests/test_adaptive_compare.py:211`). |
| 5 | Main-body adaptive tables or figure-input CSVs report success rate, expected attempts, cost/latency where available, task-family changes, and persistent hard-family failures grouped by structural bottleneck. | VERIFIED | `AdaptiveSummaryRow` includes success rate, expected attempts, attempts-to-success, latency, cost, failure-class counts, and CI fields (`adaptive_artifacts.py:169`). `AdaptiveComparisonRow` includes Exp2, Bernoulli, fixed retry, adaptive outcome, classification change, cutoff note, bottleneck tags, and persistent failure notes (`adaptive_artifacts.py:221`). `adaptive_compare.py` writes CSV/JSON, classifies hard/borderline/broken labels, adds structural bottleneck tags, and only emits persistent failure notes for scientific hard failures (`adaptive_compare.py:21`, `adaptive_compare.py:26`, `adaptive_compare.py:282`, `adaptive_compare.py:315`). Tests cover labels, tags, persistent-failure gating, and comparison output fields (`tests/test_adaptive_compare.py:292`, `tests/test_adaptive_compare.py:332`, `tests/test_adaptive_end_to_end.py:199`). |

**Score:** 5/5 truths verified

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `adaptive_artifacts.py` | Adaptive schemas, policy validators, append-only writer, summary/comparison serialization | VERIFIED | 485 lines; defines schema constants, Pydantic models, policy-state leakage validators, `AdaptiveArtifactWriter`, JSONL append, summary derivation, and comparison writer. |
| `adaptive_preflight.py` | Provider-free preflight CLI with counts, hashes, output paths, semantics, and path safety | VERIFIED | 312 lines; imports adaptive constants, uses `revision_run_dir()`, reports solve/reflection/max request counts, hashes prompt/few-shot/prefix/suffix inputs, and does not construct providers. |
| `adaptive_attacker.py` | Dataset-based adaptive run loop with explicit task-level memory | VERIFIED | 819 lines; writes manifest before provider construction, samples without replacement, reuses `run_eval` task/provider/scoring seams, records append-only adaptive attempts, and derives summaries. |
| `adaptive_compare.py` | Table/figure-input comparison builder | VERIFIED | 569 lines; loads legacy Exp2/Exp3 and adaptive summaries, computes Bernoulli Success@k, merges fixed retry/adaptive outcomes, classifies changes, and writes CSV/JSON. |
| `tests/test_adaptive_*.py` | Offline validation for Phase 2 workflow | VERIFIED | 2,023 lines across five focused test files; focused suite passed with 43 tests and third-party warnings only. |
| `README.md` | Reproduction notes and optional paid-smoke boundary | VERIFIED | Documents adaptive preflight, required offline validation, adaptive run, comparison table input, `results/revision/<run_id>/`, and optional paid smoke as non-default and budget-gated (`README.md:98`). |

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `adaptive_preflight.py` | `adaptive_artifacts.py` constants | Imports `FEEDBACK_MODE`, `MEMORY_MODE`, `SAMPLING_MODE`, `STOPPING_RULE` | WIRED | CLI choices and report fields use the imported constants (`adaptive_preflight.py:10`, `adaptive_preflight.py:80`, `adaptive_preflight.py:254`). |
| `adaptive_preflight.py` | `revision_artifacts.revision_run_dir()` | Output path validation | WIRED | Preflight validates run IDs and output directory state before any paid run path (`adaptive_preflight.py:11`, `adaptive_preflight.py:215`). |
| `adaptive_attacker.py` | `run_eval` task/provider/scorer seams | `build_tasks()`, `make_provider()`, `build_json_schema()`, `evaluate_pass1()` | WIRED | Adaptive loop reuses existing dataset construction and scoring semantics rather than duplicating them (`adaptive_attacker.py:456`, `adaptive_attacker.py:547`, `adaptive_attacker.py:588`, `adaptive_attacker.py:603`). |
| `adaptive_attacker.py` | `AdaptiveArtifactWriter` | Append attempts and derive summaries | WIRED | Writer is constructed before provider setup, attempts are appended as `AdaptiveAttemptRecord`, and summaries are derived from persisted attempts (`adaptive_attacker.py:477`, `adaptive_attacker.py:737`, `adaptive_attacker.py:753`). |
| `adaptive_compare.py` | Exp2/Bernoulli/fixed/adaptive inputs | `CAPTCHAVisualizer`, `predict_q_from_exp2()`, `predict_A_from_exp2()`, adaptive summary loading | WIRED | Comparison builder merges legacy results and adaptive summaries into validated `AdaptiveComparisonRow` outputs (`adaptive_compare.py:13`, `adaptive_compare.py:17`, `adaptive_compare.py:59`, `adaptive_compare.py:90`, `adaptive_compare.py:207`). |
| `tests/test_adaptive_end_to_end.py` | Full Phase 2 workflow | Preflight -> adaptive run -> summary -> comparison | WIRED | E2E test uses temp datasets and fake providers only, asserts no sentinel ground-truth leakage, and verifies comparison CSV/JSON fields (`tests/test_adaptive_end_to_end.py:63`). |

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `adaptive_preflight.py` | `AdaptivePreflightReport` | Dataset `ground_truth.json`, prompt/few-shot hashes, CLI budget/provider/model args | Yes | FLOWING - spot-check produced one selected `Dice_Count` item, request counts, prompt hash, semantics, and output paths with no warnings. |
| `adaptive_attacker.py` | `AdaptiveAttemptRecord` rows | `run_eval.build_tasks()` selected tasks, provider `infer()`, `run_eval.evaluate_pass1()`, policy-state update | Yes | FLOWING - attempts are built from selected task instances and provider outputs, then persisted before summaries. |
| `adaptive_artifacts.py` | `AdaptiveSummaryRow` rows | `adaptive_attempts.jsonl` via `iter_attempts()` | Yes | FLOWING - `write_summary_from_attempts()` groups persisted attempts and computes success, reflection, latency, cost, and failure counts (`adaptive_artifacts.py:351`). |
| `adaptive_compare.py` | `AdaptiveComparisonRow` rows | Legacy Exp2/Exp3 outputs plus adaptive summary CSV/JSON | Yes | FLOWING - builder filters by provider/model/run/k, computes Bernoulli fields, merges adaptive outcome, and validates rows through Pydantic. |

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Focused adaptive suite passes | `uv run pytest tests/test_adaptive_artifacts.py tests/test_adaptive_preflight.py tests/test_adaptive_attacker.py tests/test_adaptive_compare.py tests/test_adaptive_end_to_end.py -q` | 43 passed; third-party matplotlib/pyparsing deprecation warnings only | PASS |
| Full suite passes | `uv run pytest -q` | Passed; third-party matplotlib/pyparsing deprecation warnings only | PASS |
| Lint passes | `uv run ruff check .` | All checks passed | PASS |
| Dependency lock is current | `uv lock --check` | Resolved 56 packages; lock check passed | PASS |
| Adaptive preflight is provider-free and budget-visible | `uv run python adaptive_preflight.py --dataset-root ./captcha_data --types Dice_Count --prompts-file ./prompts_optimized.yaml --output-root /tmp/captcha-phase2-verification-preflight --run-id verifier-preflight-02 --provider openai --model gpt-5 --max-per-type 1 --attempt-budget-k 1` | Exited 0 with `expected_request_count_max=1`, no warnings, adaptive semantics, prompt hash, and output paths | PASS |
| Comparison CLI is runnable | `uv run python adaptive_compare.py --help` | Exited 0 and showed required adaptive summary/output/k flags | PASS |
| Schema drift check passes | `gsd-sdk query verify.schema-drift 02` | `valid: true`, `issues: []`, `checked: 5` | PASS |

## Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|-------------|----------------|-------------|--------|----------|
| ADAPT-01 | 02-02, 02-03, 02-05 | Researcher can run a session-memory adaptive attacker experiment that carries explicit task-level memory across fresh CAPTCHA instances. | SATISFIED | `adaptive_attacker.py` implements `run_adaptive_experiment()` with per-task-type policy state, without-replacement pools, resume handling, and CLI; E2E fake-provider test exercises the full path. |
| ADAPT-02 | 02-01, 02-02, 02-03, 02-05 | Binary pass/fail feedback only; no ground-truth labels, coordinates, counts, or corrective hints exposed to the attacker. | SATISFIED | Constants, manifest/preflight fields, reflection prompt text, policy validators, and sentinel leakage tests enforce the contract. |
| ADAPT-03 | 02-01, 02-02, 02-03, 02-05 | Adaptive attempts include prior failures, policy state, prompt metadata, selected task, parsed answer, correctness, latency, tokens, cumulative cost, and stopping reason. | SATISFIED | `AdaptiveAttemptRecord` fields and run-loop construction include every required field; writer appends JSONL before summaries. |
| ADAPT-04 | 02-04, 02-05 | Researcher can compare fixed retry, Bernoulli Success@k, and adaptive session-memory outcomes under the same task-family budget. | SATISFIED | `adaptive_compare.py` requires `attempt_budget_k`, filters adaptive rows by it, uses it for Bernoulli predictions, and emits fixed retry/adaptive fields. |
| ADAPT-05 | 02-01, 02-04, 02-05 | Adaptive summaries report success rate, expected attempts, attempts-to-success, latency, cost, confidence intervals where applicable, and classification changes by task family. | SATISFIED | Summary and comparison schemas include the fields; Phase 2 single-run CI fields are nullable with explicit repeated-run deferral to Phase 3. |
| ADAPT-06 | 02-04, 02-05 | Main-body adaptive tables or figure-input CSVs identify hard families, improved/borderline/instruction-sensitive families, and persistent failures grouped by structural bottleneck. | SATISFIED | `adaptive_compare.py` emits hard/borderline/broken labels, classification changes, structural bottleneck tags, instruction-sensitivity tags, and persistent hard-family notes gated on scientific failures. |

All six ADAPT requirements appear in Phase 2 PLAN frontmatter and in `.planning/REQUIREMENTS.md`; no orphaned ADAPT requirements were found.

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | - | - | - | No TODO/FIXME/placeholder markers, product stubs, or blocking hardcoded-empty data paths were found in Phase 2 implementation files. The only empty-list/empty-dict matches are normal optional defaults or test fixtures. |

## Human Verification Required

None. Phase 2 produces offline scripts, schemas, CSV/JSON evidence inputs, and documentation, all covered by automated checks and fake-provider E2E validation. Optional paid smoke remains documented as non-default and budget-gated; it is not required for Phase 2 goal verification.

## Gaps Summary

No gaps found. The codebase contains substantive, wired, and tested artifacts for the adaptive preflight, session-memory adaptive attacker, attempt/summary artifacts, comparison table inputs, and README reproduction workflow. Phase 2 goal is achieved.

---

_Verified: 2026-05-18T04:33:35Z_
_Verifier: Claude (gsd-verifier)_
