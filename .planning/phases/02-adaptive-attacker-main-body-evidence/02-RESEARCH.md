# Phase 02: Adaptive Attacker Main-Body Evidence - Research

**Researched:** 2026-05-18
**Domain:** Offline adaptive CAPTCHA evaluation, explicit local memory, revision evidence artifacts
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

## Implementation Decisions

### Adaptive Feedback and Memory Semantics

- **D-01:** The adaptive attacker receives binary pass/fail feedback only after each attempt. It must not receive ground-truth labels, correct coordinates, counts, categories, instance-level corrective hints, or partial answer feedback.
- **D-02:** Persistent attacker memory is experiment-controlled state, not provider-native memory. It must be explicitly stored and replayed by the local code so it is auditable and reproducible.
- **D-03:** Persistent memory stores structured policy notes only: failed-attempt counts, tried strategy summaries, and next prompt rules. It must not persist full prompt/response transcripts, ground truth, instance answers, coordinates, counts, or local corrections.
- **D-04:** Prompt adaptation uses constrained model self-reflection. After a failed attempt, the model may see only the current prompt, its own current raw/parsed answer, and binary fail feedback, then emit a short structured policy note. Long-term memory persists only that note.

### Budget and Comparison Contract

- **D-05:** The main comparison unit is the CAPTCHA task type, matching the paper's existing evaluation unit. Structural families or bottleneck groups are explanatory groupings only, not the primary evaluation contract.
- **D-06:** Each task type gets the same attempt budget `k` for fixed retry, Bernoulli Success@k, and adaptive outcomes.
- **D-07:** Adaptive sampling uses fresh instances without replacement within each task type where possible, until the task pool is exhausted.
- **D-08:** Each task type stops on first success or when the maximum attempt budget is exhausted.
- **D-09:** Scientific wrong answers, protocol failures, and infrastructure failures must be separated. Provider/runtime failures must not be treated as structural CAPTCHA robustness evidence in main paper conclusions.

### Main-Body Evidence Outputs

- **D-10:** The primary Phase 2 output is a task-type comparison table input. Each task-type row should include Exp2 pass@1, Bernoulli Success@k, fixed retry observed outcome, adaptive observed outcome, attempts-to-success, cumulative latency, cost metadata where available, and classification change.
- **D-11:** Persistent failures are organized task-type first, with structural bottleneck tags such as spatial precision, ordering, counting, object-location binding, template diversity, and instruction sensitivity.
- **D-12:** Classification outputs use hard / borderline / broken labels with an explicit cutoff note. The 40% threshold is an operational cutoff, not a universal security boundary.

### Implementation Shape

- **D-13:** Implement the adaptive loop in a new focused module/script rather than expanding the monolithic evaluator. The planner may choose the exact file name.
- **D-14:** Reuse existing code where safe: `run_eval.build_tasks()`, `run_eval.make_provider()`, `run_eval.evaluate_pass1()`, and Phase 1 revision artifact helpers.
- **D-15:** Preserve Phase 1 artifact schema contracts. Add adaptive-specific schemas or compatibility layers instead of mutating existing `AttemptRecord` v1 semantics.
- **D-16:** Add adaptive preflight support that reports task types, attempt budget `k`, expected request count, run id, prompt/few-shot hashes, cost preview, output paths, sampling mode, feedback mode, memory mode, and stopping rule before paid calls.
- **D-17:** Validation should rely primarily on offline fake-provider tests covering memory updates, without-replacement sampling, stopping rules, attempt logs, adaptive summaries, and comparison outputs.
- **D-18:** A tiny paid provider smoke may be included only as an optional final real-provider path check. It must be gated by preflight and must not replace offline validation.

### Claude's Discretion

- The planner may choose exact module names, CLI flags, schema class names, and output filenames if they preserve the contracts above.
- The planner may choose whether adaptive-specific records extend `revision_artifacts.py` directly or live in a new adaptive artifact module, as long as Phase 1 v1 schemas remain backward-compatible.
- The planner may choose the exact hard / borderline / broken cutoff implementation and classification-change columns, provided the 40% operational-cutoff caveat is explicit.
- The planner may choose a small paid smoke shape, but it must be optional, budget-visible, and safe for secret handling.

### Deferred Ideas (OUT OF SCOPE)

None - discussion stayed within Phase 2 scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ADAPT-01 | Researcher can run a session-memory adaptive attacker experiment that carries explicit task-level memory across fresh CAPTCHA instances. | Use a new `adaptive_attacker.py` loop with per-task-type `AdaptivePolicyMemory` persisted locally. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][VERIFIED: run_eval.py] |
| ADAPT-02 | Adaptive attacker semantics define binary pass/fail feedback only, with no ground-truth labels, coordinates, counts, or per-instance corrective hints exposed to the attacker. | Add prompt builders and tests that assert reflection inputs contain only prompt, raw/parsed self-answer, and binary feedback. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md] |
| ADAPT-03 | Adaptive attempt records include prior failures, policy state, prompt adaptation metadata, selected task, parsed answer, correctness, latency, token usage, cumulative cost metadata, and stopping reason. | Add adaptive-specific Pydantic schemas rather than changing `AttemptRecord` v1. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][VERIFIED: revision_artifacts.py] |
| ADAPT-04 | Researcher can compare fixed retry, i.i.d. Bernoulli Success@k prediction, and adaptive session-memory outcomes under the same task-family budget. | Reuse `exp2_to_exp3_predict.py` formulas and merge Exp2, Exp3 fixed retry, and adaptive summary rows by provider/model/task type/k. [VERIFIED: exp2_to_exp3_predict.py][VERIFIED: visualize_results.py] |
| ADAPT-05 | Adaptive summaries report success rate, expected attempts, attempts-to-success, cumulative latency, cost estimates, confidence intervals where applicable, and classification changes by task family. | Emit `adaptive_summary.csv/json` and `adaptive_comparison.csv/json`; confidence intervals can be marked not applicable for one run and deferred to Phase 3 unless repeated runs exist. [CITED: .planning/REQUIREMENTS.md][VERIFIED: .planning/ROADMAP.md] |
| ADAPT-06 | Main-body adaptive attacker tables or figure-input CSVs identify robust hard families, improved borderline or instruction-sensitive families, and persistent failures grouped by structural bottleneck. | Add a task-type-first comparison artifact plus static bottleneck tags used only for explanatory grouping. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md] |
</phase_requirements>

## Summary

Phase 2 should be planned as a narrow additive workflow around the existing evaluator, not as a rewrite of `run_eval.py`. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][VERIFIED: .planning/codebase/CONCERNS.md] The safest implementation is a new adaptive loop that calls `run_eval.build_tasks()`, `run_eval.make_provider()`, `run_eval.build_json_schema()`, and `run_eval.evaluate_pass1()` while writing adaptive-specific artifacts under `results/revision/<run_id>/`. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][VERIFIED: run_eval.py][VERIFIED: revision_artifacts.py]

The main planning risk is semantic leakage: memory must be explicit local state, feedback must remain binary, and persistent notes must not contain ground truth, correct coordinates, full transcripts, or corrective hints. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md] The second risk is unfair comparison: fixed retry, Bernoulli Success@k, and adaptive outcomes must use the same task-type attempt budget `k`, while any extra reflection calls must be reported separately in request count, cost, and latency metadata. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][VERIFIED: exp2_to_exp3_predict.py]

**Primary recommendation:** Build `adaptive_artifacts.py`, `adaptive_preflight.py`, `adaptive_attacker.py`, and `adaptive_compare.py`, with offline fake-provider tests first and optional paid smoke last. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][VERIFIED: tests/test_revision_run_contract.py]

## Project Constraints (from AGENTS.md)

- User-facing chat must stay in Chinese, while planning documents, code comments, generated reports, and project artifacts should stay in English. [VERIFIED: AGENTS.md]
- Experiments must stay offline and dataset-based; do not build live CAPTCHA attack automation or browser automation against real services. [VERIFIED: AGENTS.md]
- `secrets.yaml` is sensitive local configuration; do not print, quote, copy, summarize, or commit credential values. [VERIFIED: AGENTS.md]
- Prefer reproducible scripted artifacts over notebook-only manual state. [VERIFIED: AGENTS.md]
- Preserve existing experiment semantics unless a phase explicitly plans a migration. [VERIFIED: AGENTS.md]
- Avoid broad refactors unless they protect experiment correctness, reproducibility, or artifact integrity. [VERIFIED: AGENTS.md]
- `CLAUDE.md` was not present in the project root during this research. [VERIFIED: shell test for CLAUDE.md]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Adaptive task sampling | Local experiment orchestrator | Dataset layer | Task pools come from `build_tasks()` and must be sampled without replacement per task type. [VERIFIED: run_eval.py][CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md] |
| Binary feedback enforcement | Local experiment orchestrator | Test suite | The provider must only receive binary pass/fail feedback after scoring. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md] |
| Persistent memory | Artifact layer | Local experiment orchestrator | Memory is experiment-controlled state persisted locally, not provider-native memory. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md] |
| Scoring | Existing evaluator | Test suite | `evaluate_pass1()` is the shared correctness gate and should be reused to avoid scorer drift. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][VERIFIED: run_eval.py] |
| Provider calls | Existing provider adapter boundary | Optional paid smoke | `make_provider()` constructs OpenAI, Anthropic, Gemini, and Fireworks adapters behind one `infer()` shape. [VERIFIED: run_eval.py] |
| Comparison outputs | Analysis layer | Artifact layer | Exp2/Exp3 data are already normalized through `CAPTCHAVisualizer`, and Bernoulli predictions already live in `exp2_to_exp3_predict.py`. [VERIFIED: visualize_results.py][VERIFIED: exp2_to_exp3_predict.py] |
| Validation | Pytest test suite | Fake providers | Phase 1 tests already monkeypatch provider and task boundaries, so Phase 2 should follow that pattern. [VERIFIED: tests/test_revision_run_contract.py][VERIFIED: tests/test_revision_preflight.py] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | `>=3.10`; local `uv run python --version` reported 3.11.5 | Runtime for scripts and tests | The project declares Python `>=3.10` and current local uv runtime is Python 3.11.5. [VERIFIED: pyproject.toml][VERIFIED: uv run python --version] |
| Pydantic | 2.13.4 pinned | Versioned adaptive schema models | Phase 1 artifact and preflight schemas already use Pydantic. [VERIFIED: pyproject.toml][VERIFIED: revision_artifacts.py][VERIFIED: revision_preflight.py] |
| pytest | 9.0.3 pinned | Offline fake-provider validation | Phase 1 added pytest tests under `tests/`. [VERIFIED: pyproject.toml][VERIFIED: tests/] |
| pandas | 1.5.3 pinned | Comparison CSV loading and merging | Existing visualization and prediction tools use pandas. [VERIFIED: pyproject.toml][VERIFIED: visualize_results.py][VERIFIED: exp2_to_exp3_predict.py] |
| numpy | 1.24.3 pinned | Bernoulli formulas and numeric clipping | Existing prediction utility uses numpy for prediction and calibration helpers. [VERIFIED: pyproject.toml][VERIFIED: exp2_to_exp3_predict.py] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PyYAML | 6.0.2 pinned | Prompt/few-shot/local config loading | Reuse for preflight and prompt config handling. [VERIFIED: pyproject.toml][VERIFIED: revision_preflight.py][VERIFIED: run_eval.py] |
| openai / anthropic / google-genai | 2.6.1 / 0.72.0 / 1.39.1 pinned | Optional real-provider execution | Use only behind preflight and never in default tests. [VERIFIED: pyproject.toml][VERIFIED: run_eval.py] |
| ruff | 0.15.13 pinned | Static check | Phase 1 verification used ruff successfully. [VERIFIED: pyproject.toml][VERIFIED: .planning/phases/01-reproducibility-and-safety-foundation/01-VERIFICATION.md] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New adaptive modules | Add adaptive behavior inside `run_eval.py` | Rejected by Phase 2 D-13 and monolith risk. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][VERIFIED: .planning/codebase/CONCERNS.md] |
| Adaptive-specific schemas | Mutate `AttemptRecord` v1 | Rejected because Phase 1 schema semantics must remain backward-compatible. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][VERIFIED: revision_artifacts.py] |
| Provider-native memory | Chat/session memory in provider APIs | Rejected because memory must be explicit local state. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md] |

**Installation:**
```bash
uv sync --locked
```

**Version verification:** Package versions were verified from `pyproject.toml`; uv itself was available as `uv 0.11.14`, and an escalated `uv run python --version` returned Python 3.11.5 after the sandbox could not access the user uv cache. [VERIFIED: pyproject.toml][VERIFIED: uv --version][VERIFIED: uv run python --version]

## Architecture Patterns

### System Architecture Diagram

```text
CLI args / preflight config
        |
        v
adaptive_preflight.py
  - validate run_id, tasks, prompt hashes, output paths
  - report k, sampling mode, feedback mode, memory mode, request/cost preview
        |
        v
adaptive_attacker.py
  build task pools via run_eval.build_tasks()
        |
        v
for each task_type:
  initialize local AdaptivePolicyMemory
  shuffle fresh task pool
  while attempts < k and pool not exhausted:
    pop next fresh task
    build adapted prompt from base prompt + local policy notes
    provider.infer(...) -> raw/parsed/meta
    run_eval.evaluate_pass1(task, parsed) -> binary pass/fail
    classify failure: scientific_wrong | protocol_failure | infrastructure_failure
    if fail:
      constrained reflection input = prompt + own raw/parsed answer + binary fail only
      update local policy note
    append adaptive attempt record
    stop on first success
        |
        v
adaptive_artifacts.py
  adaptive_attempts.jsonl -> adaptive_summary.csv/json
        |
        v
adaptive_compare.py
  Exp2 pass@1 + Bernoulli Success@k + fixed retry Exp3 + adaptive summary
        |
        v
main-body table/figure-input CSV
```

### Recommended Project Structure

```text
captcha/
|-- adaptive_artifacts.py        # Pydantic schemas and adaptive writer
|-- adaptive_preflight.py        # Offline preflight for adaptive runs
|-- adaptive_attacker.py         # Main adaptive loop CLI/module
|-- adaptive_compare.py          # Comparison table builder
|-- tests/
|   |-- test_adaptive_artifacts.py
|   |-- test_adaptive_preflight.py
|   |-- test_adaptive_attacker.py
|   `-- test_adaptive_compare.py
```

This flat root-level structure matches existing project conventions. [VERIFIED: .planning/codebase/STRUCTURE.md][VERIFIED: pyproject.toml]

### Pattern 1: Adaptive Artifacts Without Mutating Phase 1 v1 Schemas

**What:** Keep `RunManifest` and helper functions from `revision_artifacts.py`, but add adaptive-specific Pydantic records in `adaptive_artifacts.py`. [VERIFIED: revision_artifacts.py][CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]

**When to use:** Use for all Phase 2 attempt, memory, summary, and comparison outputs. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]

**Recommended schemas:**
```python
ADAPTIVE_ATTEMPT_SCHEMA_VERSION = "cognition.revision.adaptive_attempt.v1"
ADAPTIVE_SUMMARY_SCHEMA_VERSION = "cognition.revision.adaptive_summary.v1"
ADAPTIVE_COMPARISON_SCHEMA_VERSION = "cognition.revision.adaptive_comparison.v1"
```

Include at minimum `run_id`, `task_type`, `puzzle_id`, `attempt_index`, `attempt_budget_k`, `sampling_mode`, `feedback_mode`, `memory_mode`, `policy_state_before`, `prompt_adaptation_metadata`, `parsed_answer`, `correct`, `failure_class`, `latency_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `cumulative_latency_ms`, `cumulative_cost_usd`, and `stopping_reason`. [CITED: .planning/REQUIREMENTS.md][CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]

### Pattern 2: Binary-Feedback-Only Reflection

**What:** Reflection prompts should be built by a single helper that accepts only `current_prompt`, `raw_answer`, `parsed_answer`, and `passed=False`; it must not receive `TaskItem.gt`. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][VERIFIED: run_eval.py]

**When to use:** Call after failed solve attempts to produce a short structured policy note. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]

**Test requirement:** Monkeypatch the provider to capture every reflection prompt and assert no sentinel ground-truth value appears. [VERIFIED: tests/test_revision_run_contract.py][CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]

### Pattern 3: Same Attempt Budget, Separate Reflection Cost

**What:** Count `k` as CAPTCHA solve attempts per task type; count reflection calls separately as `reflection_request_count`. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][ASSUMED]

**When to use:** Use this in preflight and summaries so adaptive comparisons are fair on solve budget while still cost-visible. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][ASSUMED]

### Anti-Patterns to Avoid

- **Using `run_until_type_correct()` as the adaptive loop:** It samples with `random.choice(pool_tasks)`, so it can reuse instances and does not satisfy without-replacement semantics. [VERIFIED: run_eval.py][CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]
- **Treating provider errors as robust CAPTCHA evidence:** Legacy code often turns provider errors into failed answers, but Phase 2 requires scientific/protocol/infrastructure separation. [VERIFIED: run_eval.py][CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]
- **Persisting raw transcripts in memory:** Long-term memory is limited to structured policy notes. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]
- **Adding adaptive fields to `AttemptRecord` v1:** Keep Phase 1 schemas backward-compatible. [VERIFIED: revision_artifacts.py][CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Task loading and prompt resolution | New dataset parser | `run_eval.build_tasks()` | It already handles supported types, aliases, dataset dirs, prompts, and few-shot exclusions. [VERIFIED: run_eval.py] |
| Correctness scoring | New adaptive scorer | `run_eval.evaluate_pass1()` | Reuse avoids drift from Phase 1 scoring regressions. [VERIFIED: run_eval.py][VERIFIED: tests/test_scoring_regressions.py] |
| Provider adapters | New provider clients | `run_eval.make_provider()` and provider `infer()` | Existing adapters normalize multimodal calls and token metadata. [VERIFIED: run_eval.py] |
| Bernoulli Success@k | New math implementation | `predict_q_from_exp2()` and `predict_A_from_exp2()` | Existing helper implements the current baseline formulas and optional finite-pool variant. [VERIFIED: exp2_to_exp3_predict.py] |
| Exp2/Exp3 result discovery | Ad hoc recursive CSV parsing | `CAPTCHAVisualizer` where practical | Existing loader normalizes standard and Exp3 result shapes. [VERIFIED: visualize_results.py] |
| Secret redaction | Custom regex set | `revision_secrets.redact_mapping()` and `redact_text()` | Phase 1 already centralizes redaction helpers and tests them. [VERIFIED: revision_secrets.py][VERIFIED: tests/test_revision_secrets.py] |

**Key insight:** The new work is the adaptive control policy and evidence schema, not CAPTCHA parsing, scoring, or provider client engineering. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][VERIFIED: run_eval.py]

## Common Pitfalls

### Pitfall 1: Without-Replacement Sampling Drift

**What goes wrong:** Existing fixed retry uses random task choice and can revisit instances. [VERIFIED: run_eval.py]
**Why it happens:** `run_until_type_correct()` calls `random.choice(pool_tasks)` inside the retry loop. [VERIFIED: run_eval.py]
**How to avoid:** Shuffle each task-type pool once and `pop()` a fresh task per attempt. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]
**Warning signs:** Duplicate `puzzle_id` values within one task type before pool exhaustion. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]

### Pitfall 2: Memory Leaks Ground Truth

**What goes wrong:** Reflection helpers accidentally receive `task.gt`, failure descriptions, coordinates, counts, or correct labels. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]
**Why it happens:** `TaskItem` carries ground truth beside prompt/images, and scorer code has access to it. [VERIFIED: run_eval.py]
**How to avoid:** Build reflection inputs from a restricted dataclass that cannot hold `gt`, and test with sentinel ground-truth values. [VERIFIED: tests/test_revision_run_contract.py][ASSUMED]
**Warning signs:** Adaptive memory contains numeric answers, coordinate pairs, correct indices, or raw prompt/response transcripts. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]

### Pitfall 3: Request Count Underestimates Adaptive Cost

**What goes wrong:** Preflight reports only solve attempts and omits reflection calls. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][ASSUMED]
**Why it happens:** Phase 1 preflight uses `sum(selected_count) * max_attempts`, which matches single-pass/retry counting but not reflection overhead. [VERIFIED: revision_preflight.py]
**How to avoid:** Adaptive preflight should report `solve_request_count`, `reflection_request_count_max`, and `expected_request_count_max`. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][ASSUMED]
**Warning signs:** Cost preview equals `n_types * k` even when model self-reflection is enabled. [ASSUMED]

### Pitfall 4: Provider/Protocol Failures Pollute Robustness Claims

**What goes wrong:** Timeout, SDK, parse, or schema failures are counted as CAPTCHA hardness. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]
**Why it happens:** Existing provider adapters often return `__ERROR__` strings, and legacy loops can treat them as failed answers. [VERIFIED: run_eval.py]
**How to avoid:** Record `failure_class` as `scientific_wrong`, `protocol_failure`, or `infrastructure_failure`, and exclude infrastructure failures from main structural conclusions. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]
**Warning signs:** Main-body persistent-hard rows include attempts with `raw` beginning `__ERROR__`. [VERIFIED: run_eval.py][CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]

### Pitfall 5: Optional Paid Smoke Uses the Broken Smoke Interface

**What goes wrong:** `revision_provider_smoke.py` calls `provider.infer(..., image_paths=[])`, while provider `infer()` signatures use `images`. [VERIFIED: revision_provider_smoke.py][VERIFIED: run_eval.py]
**Why it happens:** Phase 1 tests only verify smoke import/help safety, not live smoke execution. [VERIFIED: tests/test_import_safety.py]
**How to avoid:** If Phase 2 includes paid smoke, fix or bypass this interface and cover it with a fake-provider argument-shape test before any real call. [VERIFIED: revision_provider_smoke.py][ASSUMED]
**Warning signs:** Optional smoke raises `TypeError: infer() got an unexpected keyword argument 'image_paths'`. [VERIFIED: revision_provider_smoke.py][VERIFIED: run_eval.py]

## Code Examples

### Adaptive Loop Skeleton

```python
tasks_by_type = group_by_type(build_tasks(...))
for task_type, pool in tasks_by_type.items():
    rng.shuffle(pool)
    memory = AdaptivePolicyMemory(task_type=task_type)
    for attempt_index in range(1, k + 1):
        if not pool:
            stop_reason = "pool_exhausted"
            break
        task = pool.pop()
        adapted_prompt = build_adapted_prompt(task.prompt, memory)
        raw, parsed, meta = provider.infer(
            prompt=adapted_prompt,
            images=task.images,
            json_schema=build_json_schema(task.type),
            stream=False,
        )
        correct = evaluate_pass1(task, parsed)
        failure_class = classify_failure(raw, parsed, correct)
        if not correct and failure_class == "scientific_wrong":
            note = reflect_with_binary_feedback(
                current_prompt=adapted_prompt,
                raw_answer=raw,
                parsed_answer=parsed,
                passed=False,
            )
            memory = memory.apply(note)
        writer.append_adaptive_attempt(...)
        if correct:
            stop_reason = "first_success"
            break
```

Source surfaces: `build_tasks`, `build_json_schema`, `make_provider`, and `evaluate_pass1` exist in `run_eval.py`; adaptive memory/reflection helpers do not exist yet and must be added. [VERIFIED: run_eval.py]

### Comparison Merge Skeleton

```python
exp2 = load_exp2_pass1(results_dir, provider, model)
pred = exp2.assign(
    bernoulli_success_at_k=lambda df: df.p_hat.map(lambda p: predict_q_from_exp2(p, n=1, k=k)),
    bernoulli_expected_attempts=lambda df: df.p_hat.map(lambda p: predict_A_from_exp2(p, n=1, k=k)),
)
fixed = load_fixed_retry_exp3(results_dir, provider, model, k)
adaptive = load_adaptive_summary(adaptive_run_dir)
comparison = pred.merge(fixed, on=keys, how="left").merge(adaptive, on=keys, how="left")
```

Source surfaces: `predict_q_from_exp2()` and `predict_A_from_exp2()` exist; adaptive summary loading must be added. [VERIFIED: exp2_to_exp3_predict.py]

## State of the Art

| Old Approach | Current Phase 2 Approach | When Changed | Impact |
|--------------|--------------------------|--------------|--------|
| Exp3 fixed retry with no memory | Session-memory adaptive attacker with explicit local policy notes | Phase 2 context, 2026-05-18 | Addresses reviewer concern that robustness may be fixed-prompt/i.i.d.-only. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][VERIFIED: .planning/ROADMAP.md] |
| Random retry sampling can repeat instances | Fresh instances without replacement where possible | Phase 2 context, 2026-05-18 | Makes adaptive evidence cleaner under the task-type budget. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][VERIFIED: run_eval.py] |
| Single-pass `AttemptRecord` v1 | Adaptive-specific attempt schema | Phase 2 context, 2026-05-18 | Preserves Phase 1 compatibility while covering ADAPT-03 fields. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][VERIFIED: revision_artifacts.py] |
| Main outputs under legacy `results/exp*` | Revision outputs under `results/revision/<run_id>/` | Phase 1 completed 2026-05-16 | Keeps new evidence reproducible, manifest-backed, and path-scoped. [VERIFIED: .planning/phases/01-reproducibility-and-safety-foundation/01-VERIFICATION.md][VERIFIED: revision_artifacts.py] |

**Deprecated/outdated:**
- Treating `.planning/codebase/TESTING.md` as current is outdated because Phase 1 added `tests/` and `pyproject.toml` test config after that map was written. [VERIFIED: .planning/codebase/TESTING.md][VERIFIED: tests/][VERIFIED: pyproject.toml]
- Using provider-native memory is out of scope for Phase 2. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]

## Comparison Contract

The comparison artifact should be task-type primary, with one row per provider/model/task_type/k/adaptive_run_id. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md] Recommended columns are:

| Column Group | Columns |
|--------------|---------|
| Identity | `run_id`, `provider`, `model`, `task_type`, `attempt_budget_k`, `prompt_mode` |
| Exp2 | `exp2_n`, `exp2_pass_at_1`, `exp2_source_path` |
| Bernoulli | `bernoulli_success_at_k`, `bernoulli_expected_attempts`, `bernoulli_formula_note` |
| Fixed retry | `fixed_retry_observed_success`, `fixed_retry_attempts_to_success`, `fixed_retry_cumulative_latency_ms`, `fixed_retry_source_path` |
| Adaptive | `adaptive_observed_success`, `adaptive_attempts_to_success`, `adaptive_cumulative_latency_ms`, `adaptive_solve_request_count`, `adaptive_reflection_request_count`, `adaptive_cumulative_cost_usd`, `adaptive_stop_reason` |
| Failure separation | `scientific_wrong_count`, `protocol_failure_count`, `infrastructure_failure_count` |
| Classification | `baseline_label`, `adaptive_label`, `classification_change`, `cutoff_note` |
| Explanation | `structural_bottleneck_tags`, `persistent_failure_note` |

Use `hard` below 0.40, `borderline` within a small configured margin around 0.40, and `broken` above the margin; the margin should be explicit in the artifact metadata. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][VERIFIED: visualize_results.py][ASSUMED]

## Structural Bottleneck Tags

Use these tags only as explanatory groupings, not as the primary evaluation unit. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]

| Tag | Likely Task Types | Confidence |
|-----|-------------------|------------|
| Spatial precision | `Geometry_Click`, `Place_Dot`, `Pick_Area`, `Misleading_Click`, `Click_Order` | MEDIUM - inferred from task schemas and prompts. [VERIFIED: run_eval.py][ASSUMED] |
| Ordering | `Click_Order`, `Bingo` | MEDIUM - inferred from task schemas and prompts. [VERIFIED: run_eval.py][ASSUMED] |
| Counting | `Dice_Count`, `Dart_Count` | MEDIUM - inferred from task names and schemas. [VERIFIED: run_eval.py][ASSUMED] |
| Object-location binding | `Patch_Select`, `Select_Animal`, `Select_Animal_Optimized`, `Image_Recognition`, `Unusual_Detection` | MEDIUM - inferred from task schemas and prompts. [VERIFIED: run_eval.py][ASSUMED] |
| Template diversity | `Image_Matching`, `Object_Match`, `Path_Finder`, `Connect_Icon`, `Rotation_Match` | LOW - needs author confirmation before locked paper wording. [VERIFIED: run_eval.py][ASSUMED] |
| Instruction sensitivity | Any task whose Exp2/Exp3/adaptive label changes materially | MEDIUM - should be derived from comparison deltas, not assigned by name only. [VERIFIED: visualize_results.py][ASSUMED] |

## Test Strategy

Phase 2 should be test-first because paid runs are optional and must not be the validation backbone. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]

| Test File | Coverage |
|-----------|----------|
| `tests/test_adaptive_artifacts.py` | Schema versions, JSONL append order, duplicate attempt IDs, summary derivation, comparison row serialization. [VERIFIED: tests/test_revision_artifacts.py] |
| `tests/test_adaptive_preflight.py` | Task aliases, output dir overwrite/resume, run-id validation, prompt/few-shot hashes, k, sampling mode, feedback mode, memory mode, request/cost preview. [VERIFIED: tests/test_revision_preflight.py] |
| `tests/test_adaptive_attacker.py` | Fake-provider loop, memory update, no ground-truth leakage, without-replacement sampling, stop on first success, stop on budget, stop on pool exhaustion, failure-class separation. [VERIFIED: tests/test_revision_run_contract.py][CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md] |
| `tests/test_adaptive_compare.py` | Exp2/Bernoulli/fixed/adaptive merge, missing fixed retry handling, classification labels, cutoff note, bottleneck tags. [VERIFIED: exp2_to_exp3_predict.py][VERIFIED: visualize_results.py] |

Recommended quick checks:

```bash
uv run pytest tests/test_adaptive_artifacts.py tests/test_adaptive_preflight.py tests/test_adaptive_attacker.py tests/test_adaptive_compare.py -q
uv run ruff check adaptive_artifacts.py adaptive_preflight.py adaptive_attacker.py adaptive_compare.py tests
```

These commands match the Phase 1 validation style. [VERIFIED: .planning/phases/01-reproducibility-and-safety-foundation/01-VERIFICATION.md][VERIFIED: pyproject.toml]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| `uv` | Install/test execution | Yes | 0.11.14 | Use project Python only for read-only inspection; use uv for real validation. [VERIFIED: uv --version] |
| Python via `uv run` | Runtime | Yes after approval outside sandbox | 3.11.5 | Direct system Python is not recommended for final validation. [VERIFIED: uv run python --version][VERIFIED: pyproject.toml] |
| Provider credentials | Optional paid smoke | Local config exists but values were not inspected | Unknown | Fake providers for all required validation. [VERIFIED: AGENTS.md][VERIFIED: tests/test_revision_run_contract.py] |

**Missing dependencies with no fallback:** None identified for offline planning and tests. [VERIFIED: pyproject.toml][VERIFIED: tests/]

**Missing dependencies with fallback:** Paid provider availability is intentionally optional; fake-provider validation is the required path. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | No for app users | No user auth is in scope; provider credentials stay in local config. [VERIFIED: AGENTS.md][VERIFIED: run_eval.py] |
| V3 Session Management | Yes for experiment memory semantics | Do not use provider-native hidden sessions; persist explicit local memory only. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md] |
| V4 Access Control | Limited | Keep outputs under validated `results/revision/<run_id>/` paths and reject unsafe run IDs. [VERIFIED: revision_artifacts.py][VERIFIED: tests/test_revision_artifacts.py] |
| V5 Input Validation | Yes | Use Pydantic schemas and preflight validation for adaptive configs and artifacts. [VERIFIED: revision_preflight.py][VERIFIED: revision_artifacts.py] |
| V6 Cryptography | Yes for hashes only | Use existing SHA-256 helpers for prompt/few-shot hashes; do not implement custom crypto. [VERIFIED: revision_artifacts.py] |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Secret leakage through logs or artifacts | Information Disclosure | Reuse redaction helpers and never print/copy `secrets.yaml` values. [VERIFIED: AGENTS.md][VERIFIED: revision_secrets.py] |
| Ground-truth leakage into adaptive memory | Information Disclosure / Tampering | Restrict reflection inputs and test with sentinel ground-truth values. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][ASSUMED] |
| Path traversal in run IDs | Tampering | Reuse `revision_run_dir()` validation. [VERIFIED: revision_artifacts.py][VERIFIED: tests/test_revision_artifacts.py] |
| Infrastructure failures misrepresented as robustness | Repudiation / Integrity | Store `failure_class` and exclude infrastructure failures from structural conclusions. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md] |

## Plan Split Recommendations

1. **Plan 02-01 - Adaptive schemas and writer:** Add `adaptive_artifacts.py`, schema constants, writer paths, JSONL append, summary derivation, and tests. [VERIFIED: revision_artifacts.py][VERIFIED: tests/test_revision_artifacts.py]
2. **Plan 02-02 - Adaptive preflight:** Add `adaptive_preflight.py` with k, expected solve/reflection request counts, hashes, output paths, sampling/feedback/memory/stopping metadata, and tests. [VERIFIED: revision_preflight.py][CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]
3. **Plan 02-03 - Offline adaptive loop:** Add `adaptive_attacker.py` with fake-provider tests for memory, binary feedback, without-replacement sampling, stopping rules, and failure separation. [VERIFIED: run_eval.py][VERIFIED: tests/test_revision_run_contract.py]
4. **Plan 02-04 - Comparison table builder:** Add `adaptive_compare.py` to merge Exp2 pass@1, Bernoulli Success@k, fixed retry observed results, adaptive summaries, classification labels, and bottleneck tags. [VERIFIED: exp2_to_exp3_predict.py][VERIFIED: visualize_results.py]
5. **Plan 02-05 - End-to-end offline validation and optional smoke:** Run focused pytest/ruff, an offline fake adaptive run, comparison artifact generation, and only then an optional tiny paid smoke if explicitly requested. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md][VERIFIED: .planning/phases/01-reproducibility-and-safety-foundation/01-VERIFICATION.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Reflection calls should count separately from solve-attempt budget `k`, while still appearing in request/cost/latency metadata. | Architecture Patterns, Common Pitfalls | Cost preview or fairness wording may need adjustment if the paper treats reflection as part of the same request budget. |
| A2 | Hard/borderline/broken should use 40% plus an explicit margin for borderline labels. | Comparison Contract | Classification-change rows may need different thresholds if authors already have a fixed cutoff policy. |
| A3 | Structural bottleneck tags can be initialized from task schemas/names and refined from adaptive outcomes. | Structural Bottleneck Tags | Paper wording could overstate tags unless authors confirm the mapping. |
| A4 | Sentinel-based prompt tests are sufficient to catch ground-truth leakage in offline tests. | Test Strategy, Security Domain | More static checks may be needed if prompt construction grows complex. |

## Open Questions (RESOLVED)

1. **Should model self-reflection be a separate provider call or folded into the next solve prompt?**
   - What we know: D-04 allows constrained model self-reflection after failure. [CITED: .planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md]
   - RESOLVED: Treat reflection as separately accounted adaptive overhead, not as a solve attempt in the task-type budget `k`. Adaptive preflight and summaries must report `solve_request_count`, `reflection_request_count`, `reflection_request_count_max`, and `expected_request_count_max` so the main comparison remains fair on solve budget while cost and latency remain conservative and visible. [RESOLVED: 02-01 through 02-05 plans]

2. **Which provider/model pair is the canonical Phase 2 paid run target?**
   - What we know: Existing results include multiple providers/models under `results/exp1`, `results/exp2`, and `results/exp3`. [VERIFIED: results/]
   - RESOLVED: Do not hard-code a canonical paid provider/model in planning. Implement provider/model CLI filters, validate offline first, and choose any paid target at execution/preflight time with budget-visible preflight output. Optional paid smoke remains non-default and explicitly gated. [RESOLVED: 02-02, 02-03, 02-05 plans]

3. **Should confidence intervals appear in Phase 2 or Phase 3?**
   - What we know: ADAPT-05 requests confidence intervals where applicable, while Phase 3 owns broader statistical confidence work. [VERIFIED: .planning/REQUIREMENTS.md][VERIFIED: .planning/ROADMAP.md]
   - RESOLVED: Phase 2 comparison outputs include nullable CI fields plus an explicit `ci_not_applicable_reason` when repeated adaptive sessions are unavailable. Full statistical confidence, threshold sensitivity, and interval expansion are deferred to Phase 3. [RESOLVED: 02-04 and 02-05 plans]

## Sources

### Primary (HIGH confidence)
- `AGENTS.md` - project constraints, ethics boundary, secret-safety rules.
- `.planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md` - locked Phase 2 decisions.
- `.planning/REQUIREMENTS.md` - ADAPT-01 through ADAPT-06.
- `.planning/ROADMAP.md` - Phase 2 goal and success criteria.
- `.planning/STATE.md` - current project state.
- `.planning/phases/01-reproducibility-and-safety-foundation/01-VERIFICATION.md` - verified Phase 1 contracts.
- `.planning/phases/01-reproducibility-and-safety-foundation/01-05-SUMMARY.md` - evaluator revision-mode details.
- `revision_artifacts.py` - Phase 1 schemas, run-dir validation, writer, hash helpers.
- `revision_preflight.py` - existing preflight model.
- `run_eval.py` - task building, provider boundary, scoring, legacy retry loop.
- `exp2_to_exp3_predict.py` - Bernoulli Success@k and expected-attempt formulas.
- `visualize_results.py` - result normalization and 40% threshold use.
- `tests/` - Phase 1 pytest/fake-provider patterns.
- `pyproject.toml` - pinned stack and test/lint config.

### Secondary (MEDIUM confidence)
- `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md`, `.planning/codebase/CONVENTIONS.md`, `.planning/codebase/CONCERNS.md`, `.planning/codebase/TESTING.md` - useful maps, but `TESTING.md` predates Phase 1 tests.

### Tertiary (LOW confidence)
- Structural bottleneck task mappings in this research are inferred from task names, prompts, schemas, and Phase 2 allowed tag names; confirm before final paper prose.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - versions and tooling are pinned in `pyproject.toml`, with uv/Python availability checked locally.
- Architecture: HIGH - Phase 2 decisions and Phase 1 contracts are explicit, and implementation seams were verified in code.
- Pitfalls: HIGH for sampling/error/schema risks verified in code; MEDIUM for reflection request accounting because it needs a final execution decision.

**Research date:** 2026-05-18
**Valid until:** 2026-06-17 for local codebase architecture; re-check provider SDK behavior before any paid run.
