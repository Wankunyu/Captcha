---
phase: 02-adaptive-attacker-main-body-evidence
reviewed: 2026-05-18T04:12:17Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - adaptive_artifacts.py
  - adaptive_preflight.py
  - adaptive_attacker.py
  - adaptive_compare.py
  - tests/test_adaptive_artifacts.py
  - tests/test_adaptive_preflight.py
  - tests/test_adaptive_attacker.py
  - tests/test_adaptive_compare.py
  - tests/test_adaptive_end_to_end.py
  - README.md
findings:
  critical: 0
  warning: 7
  info: 0
  total: 7
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-05-18T04:12:17Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Reviewed the Phase 2 adaptive artifact, preflight, attacker, comparison, test, and README changes against the adaptive-attacker contracts. The offline validation suite currently passes (`36` adaptive tests), and `ruff` passes, but several semantic gaps remain around protocol/scientific failure separation, reflection robustness, adaptive labeling, persistent-failure gating, resume safety, and reproducibility.

## Warnings

### WR-01: Schema-Invalid Provider Outputs Are Counted as Scientific Failures

**File:** `adaptive_attacker.py:151-153`

**Issue:** `classify_failure()` treats any parsed dictionary as `scientific_wrong` when it is not correct. A provider response such as `{"answer_type": "number"}` for `Dice_Count` is parseable JSON but does not satisfy the required answer schema, so it should be a protocol failure rather than structural CAPTCHA evidence. Because reflection is gated on `failure_class == "scientific_wrong"` at `adaptive_attacker.py:482`, malformed schema outputs can also trigger adaptive reflection and persistent policy updates.

**Fix:**
```python
def classify_failure(
    raw: str,
    parsed: Any,
    correct: bool,
    *,
    schema_valid: bool,
    provider_exception: Exception | None = None,
) -> str:
    if correct:
        return "none"
    if provider_exception is not None or (isinstance(raw, str) and raw.startswith("__ERROR__")):
        return "infrastructure_failure"
    if parsed is None or not isinstance(parsed, dict) or not schema_valid:
        return "protocol_failure"
    return "scientific_wrong"
```

Validate `parsed` against `run_eval.build_json_schema(task.type)` before calling `classify_failure()`, and reflect only after a schema-valid scientific miss.

### WR-02: Reflection Failures Can Abort the Run Before the Attempt Is Persisted

**File:** `adaptive_attacker.py:489-530`

**Issue:** The solve provider call is protected, but the reflection provider call and policy-state validation are not. If the reflection call raises, returns invalid metadata, or returns a policy note that trips the `AdaptivePolicyState` banned-token validator, the exception exits the loop before `AdaptiveAttemptRecord` is written. That violates the append-before-summary evidence contract and loses the failed solve attempt that triggered reflection.

**Fix:**
```python
reflection_request_count = 0
reflection_meta = {}
parsed_note = None
if failure_class == "scientific_wrong" and another_solve_remains:
    reflection_request_count = 1
    try:
        reflection_raw, reflection_parsed, reflection_call_meta = model_provider.infer(
            prompt=reflection_prompt,
            images=[],
            json_schema=reflection_json_schema(),
            stream=stream,
        )
        if isinstance(reflection_parsed, dict):
            parsed_note = reflection_parsed
        # accumulate reflection latency/cost/tokens here
    except Exception as exc:
        reflection_meta = {
            "reflection_requested": True,
            "reflection_failed": True,
            "reflection_error_type": type(exc).__name__,
        }

try:
    policy_state_after = (
        policy_state_before
        if correct
        else parse_policy_state(task.type, policy_state_before, parsed_note)
    )
except ValueError:
    reflection_meta["reflection_note_rejected"] = True
    policy_state_after = parse_policy_state(task.type, policy_state_before, None)
```

Persist the solve attempt regardless of reflection outcome, and record only non-secret reflection failure metadata.

### WR-03: Policy-Note Validation Does Not Prevent Instance Answer Details from Becoming Memory

**File:** `adaptive_artifacts.py:35-67`

**Issue:** The adaptive memory validator rejects a short banned-token list, but it still allows instance-specific details from the model's own answer, such as `"I answered value 0"`, `"avoid index 2"`, or `"the point was x=10 y=20"`. Phase 2 memory is supposed to store reusable policy notes only, not instance answers, counts, coordinates, or local corrections. Because `parse_policy_state()` appends raw reflection strings at `adaptive_attacker.py:126-129`, a compliant-looking reflection can persist details that should remain confined to the current failed attempt.

**Fix:**
```python
_BANNED_POLICY_PATTERNS = (
    re.compile(r"\b(answer|value|index|indices|point)\b", re.I),
    re.compile(r"\b[xy]\s*[:=]\s*-?\d+(\.\d+)?\b", re.I),
    re.compile(r"\(\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*\)"),
)

def _validate_policy_note_texts(values: list[str]) -> list[str]:
    for value in values:
        banned = _contains_banned_token(value)
        if banned is not None or any(pattern.search(value) for pattern in _BANNED_POLICY_PATTERNS):
            raise ValueError("adaptive policy state contains instance-specific answer detail")
    return values
```

Also strengthen the reflection prompt to explicitly forbid storing attempted answers, coordinates, counts, indices, puzzle IDs, or corrective hints.

### WR-04: Adaptive Classification Uses a Censored Per-Attempt Rate Instead of Budget-Level Outcome

**File:** `adaptive_compare.py:166-174`

**Issue:** `adaptive_label` is derived from `success_rate`, which is written as `n_success / n_attempts` in `adaptive_artifacts.py:368`. Because the adaptive loop stops on first success, this rate is censored by stopping time rather than being an observed Success@k outcome. A task solved on attempt 6 becomes `1/6` and can be labeled `hard`, while a task solved on attempt 2 becomes `1/2` and can be labeled `broken`; the label is driven by attempts-to-success, not the under-budget adaptive outcome.

**Fix:**
```python
adaptive_success_at_k = 1.0 if adaptive_observed_success else 0.0
adaptive_label = classify_rate(
    adaptive_success_at_k,
    cutoff=cutoff,
    margin=borderline_margin,
)
```

Alternatively, add a dedicated `adaptive_success_at_k` column and reserve the current per-attempt `success_rate` for descriptive run diagnostics.

### WR-05: Persistent Failure Notes Can Still Be Added to Mixed Failure Rows

**File:** `adaptive_compare.py:289-294`

**Issue:** `_persistent_failure_note()` adds the structural robustness note when `scientific_wrong_count > 0`, even if the same row also contains protocol or infrastructure failures. That can overstate persistent CAPTCHA hardness for a contaminated run where provider/runtime or response-format failures consumed part of the budget.

**Fix:**
```python
if (
    adaptive_label == "hard"
    and adaptive_observed_success is False
    and scientific_wrong_count > 0
    and protocol_failure_count == 0
    and infrastructure_failure_count == 0
):
    return PERSISTENT_FAILURE_NOTE
```

For mixed rows, emit no persistent-failure note or use a separate limitation note that explicitly says the row is not clean structural evidence.

### WR-06: Resume Mode Does Not Validate Existing Run Configuration

**File:** `adaptive_attacker.py:358-360`

**Issue:** `resume=True` loads any existing attempts in the run directory and uses their terminal stopping reasons to skip provider construction. It does not verify that the existing manifest or attempt rows match the current provider, model, prompt mode, task set, seed, or `attempt_budget_k`. Reusing a `run_id` with changed CLI flags can silently mix or skip evidence from a different adaptive configuration.

**Fix:**
```python
def _validate_resume_attempts(
    attempts: list[AdaptiveAttemptRecord],
    *,
    provider: str,
    model: str,
    prompt_mode: str,
    attempt_budget_k: int,
) -> None:
    for attempt in attempts:
        if (
            attempt.provider != provider
            or attempt.model != model
            or attempt.prompt_mode != prompt_mode
            or attempt.attempt_budget_k != attempt_budget_k
        ):
            raise ValueError("existing adaptive attempts do not match resume configuration")
```

Also compare the existing `run_manifest.json` retry policy and prompt/dataset hashes before skipping any task type.

### WR-07: `--max-per-type` Sampling Is Not Controlled by the Adaptive Seed

**File:** `adaptive_attacker.py:337-350`

**Issue:** `run_adaptive_experiment()` passes `max_per_type` into `run_eval.build_tasks()` before creating the local seeded RNG. `build_tasks()` uses the global `random` module for `random.sample()` / `random.shuffle()`, so the selected task instances are not reproducible from the adaptive run seed when `--max-per-type` caps the dataset.

**Fix:**
```python
tasks = run_eval.build_tasks(
    dataset_root,
    types,
    max_per_type=None,
    prompts_cfg=prompts_cfg,
    prompt_prefix=prompt_prefix,
    prompt_suffix=prompt_suffix,
    prompt_mode=prompt_mode,
)
task_pools = group_tasks_by_type(tasks)
rng = random.Random(seed)
for task_type, pool in task_pools.items():
    rng.shuffle(pool)
    if max_per_type is not None and max_per_type > 0:
        task_pools[task_type] = pool[:max_per_type]
```

Keep all adaptive sampling and truncation under the local `random.Random(seed)` instance so manifests can reproduce the exact selected instances.

---

_Reviewed: 2026-05-18T04:12:17Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
