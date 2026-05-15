# Technology Stack: Revision Experiment Support

**Project:** COGNITION post-acceptance CAPTCHA/MLLM security revision experiments
**Research dimension:** Stack
**Researched:** 2026-05-15
**Overall confidence:** HIGH for internal stack recommendations; MEDIUM for external baseline integration details until primary artifacts for the reviewer-cited works are collected.

## Executive Recommendation

Keep the project as a local Python research framework. Do not migrate to a service stack, notebook-first workflow, or heavyweight experiment platform. The revision needs are best served by a small packaging/reproducibility layer, a modular experiment runner around the existing `run_eval.py` primitives, a first-class statistics module, and versioned artifact schemas.

The immediate implementation should preserve the existing provider coverage in `run_eval.py` and `run_single_experiment.py`: OpenAI, Anthropic, Gemini, and Fireworks-compatible models. The stack should add validated run manifests and append-only attempt records before adding adaptive attacker logic, because reviewer-facing claims need per-attempt provenance, not only final aggregate CSVs.

## Recommended Stack

### Core Runtime

| Technology | Version Policy | Purpose | Why |
|------------|----------------|---------|-----|
| Python | Keep `>=3.10`; test and lock on Python 3.11 first | Evaluation engine, provider adapters, artifact generation | Matches current README and local environment while avoiding a broad runtime migration. |
| `pyproject.toml` | Add now | Dependency declaration, tool config, package metadata | The repo currently has README-only install commands; revision artifacts need a machine-readable environment. |
| `uv.lock` plus exported locked requirements | Add after `pyproject.toml` | Reproducible install resolution | `uv.lock` gives exact resolved versions; export `requirements-lock.txt` if collaborators do not use uv. |
| Existing `argparse` CLIs | Keep | Script entry points | The current CLIs already use `argparse`; Typer/Click would add churn without solving a paper-revision blocker. |
| Git LFS | Keep for current binary datasets | Store CAPTCHA images | Already configured for `captcha_data/**`; do not expand binary artifact storage in git. |

### Existing Runtime Dependencies to Pin

| Dependency | Current Role | Recommendation |
|------------|--------------|----------------|
| `openai` | OpenAI Responses/Chat Completions and Fireworks-compatible client path | Pin the currently working major/minor version in the lockfile and add provider contract smoke tests. |
| `anthropic` | Claude Messages provider | Pin and isolate payload construction in a provider adapter module before adaptive runs. |
| `google-genai` | Gemini multimodal provider | Pin and capture SDK version in every run manifest. |
| `Pillow` | Image inspection/encoding/compression support | Pin because MIME/image behavior can affect provider payloads. |
| `PyYAML` | Prompt, few-shot, and local config loading | Keep; use only for non-secret committed config and untracked local config. |
| `numpy`, `pandas` | Result ingestion, prediction, tabular analysis | Keep; pin because CSV normalization and numeric behavior feed paper tables. |
| `matplotlib`, `seaborn`, `adjustText` | Figure generation | Keep under an `analysis` optional dependency group. |
| `tqdm` | Progress reporting | Keep; low risk. |

### New Dependencies

Add only these new dependencies unless a phase discovers a specific blocker:

| Dependency | Dependency Group | Purpose | Why |
|------------|------------------|---------|-----|
| `scipy` | `analysis` | Binomial confidence intervals, bootstrap intervals, hypothesis checks where needed | The reviewer explicitly asked for statistical confidence; SciPy provides maintained statistical primitives, including binomial interval and bootstrap APIs. |
| `pydantic>=2,<3` | core | Validate run configs, manifests, result schemas, and baseline import records | The current CSV/JSON formats are loose. Pydantic v2 can validate JSON and generate JSON Schema for documented artifacts. |
| `pytest` | `dev` | Regression tests for task scoring, result schemas, statistics, and CLIs | Existing code has no tests; reviewer-facing experiments need guardrails before refactoring. |
| `ruff` | `dev` | Lint/format checks | One tool covers formatting and basic linting with low setup cost. |

Do not add `mlflow`, `wandb`, `dvc`, Airflow, Prefect, Hydra, Poetry, a database, or a web service framework for this milestone. They would increase migration and artifact-management work without directly answering reviewer requests.

## Recommended Module Boundaries

Create a small package alongside the existing scripts and migrate incrementally. Keep `run_eval.py` and `run_single_experiment.py` as compatibility wrappers until notebooks and README examples are updated.

```text
cognition/
  artifacts/
    schemas.py          # Pydantic models for manifests, attempts, summaries, statistics
    writer.py           # atomic JSON/CSV/JSONL writers and schema_version stamping
  baselines/
    ingest.py           # import external solver or dataset comparison results
    normalize.py        # map external task/dataset labels to COGNITION task families
  experiments/
    runner.py           # common run loop shared by Exp1/Exp2/Exp4/adaptive
    adaptive.py         # session-memory attacker policies and prompt updates
    replay.py           # resume/replay from manifest + attempt log
  providers/
    base.py             # ModelProvider protocol and structured provider errors
    openai.py
    anthropic.py
    gemini.py
    fireworks.py
  stats/
    confidence.py       # binomial CIs, bootstrap CIs, threshold uncertainty
    retry_models.py     # i.i.d., finite-pool, and adaptive comparison summaries
  tasks/
    registry.py         # canonical task names, aliases, families, display labels
    load.py             # dataset and few-shot manifest loading
    schema.py           # response schemas by task
    score.py            # evaluate_pass1 branches by task
  cli/
    revision_runner.py  # revision-focused subcommands using argparse
```

This layout addresses current codebase risks directly:

| Current Risk | Boundary That Fixes It |
|--------------|------------------------|
| `run_eval.py` mixes provider calls, loading, scoring, writing, and CLI behavior | Split provider, task, experiment, and artifact modules while preserving wrappers. |
| Task aliases drift, especially `Connect_Icon` vs `Connect_icon` | `tasks/registry.py` owns canonical names and aliases. |
| `Path_Finder` scorer drift can invalidate results | `tasks/score.py` gets focused tests per task type. |
| Exp3 only writes task-level summary rows unless attempt logging is enabled | `artifacts/writer.py` always writes append-only attempt records. |
| Provider failures are counted like wrong answers | `providers/base.py` defines structured `infrastructure_error` vs `model_wrong` outcome fields. |
| Result files lack provenance | `artifacts/schemas.py` requires `run_manifest.json` for every run. |

## Experiment Runner Structure

Add one revision runner CLI rather than extending the legacy scripts with many flags:

```bash
python -m cognition.cli.revision_runner preflight --config configs/revision/adaptive_gpt5.yaml
python -m cognition.cli.revision_runner run --config configs/revision/adaptive_gpt5.yaml
python -m cognition.cli.revision_runner summarize --run-id 2026-05-15_adaptive_openai_gpt-5
python -m cognition.cli.revision_runner compare --manifest configs/revision/baseline_comparison.yaml
```

Runner responsibilities:

| Step | Required Behavior |
|------|-------------------|
| `preflight` | Validate task names, dataset files, few-shot exclusions, prompt files, provider names, output paths, cost cap, and expected call count without reading or printing secret values. |
| `run` | Write `run_manifest.json` first, append one `attempts.jsonl` record per API call, update checkpoint state after each attempt, and derive summaries only after the attempt stream is complete. |
| `resume` | Continue from `attempts.jsonl` and `checkpoint.json`; never overwrite completed attempt records. |
| `summarize` | Generate task-family CSVs, confidence intervals, adaptive-vs-i.i.d. comparison tables, and paper-ready figure inputs from immutable attempt logs. |
| `compare` | Import baseline/dataset comparison records and normalize them into the same task-family table shape used by COGNITION results. |

The adaptive attacker should be a policy plugged into the shared runner, not a separate custom loop. Minimum policy interface:

```text
AdaptivePolicy.observe(attempt_record) -> None
AdaptivePolicy.next_prompt(task, base_prompt, session_state) -> prompt
AdaptivePolicy.session_summary() -> JSON-serializable state without secrets
```

Recommended first policy:

| Policy | Behavior | Why |
|--------|----------|-----|
| `session_memory_v1` | Retain prior failed parsed answers, failure categories, and task-family reminders within the same task type; adapt instruction wording and avoid repeated wrong coordinates/options where applicable. | Directly answers the reviewer request for a stronger non-i.i.d. retry attacker while staying offline and dataset-based. |

Do not implement browser automation, live CAPTCHA probing, CAPTCHA farm integration, or turnkey attack deployment tooling.

## Result Formats

Use versioned artifacts under a new revision namespace:

```text
results/revision/<run_id>/
  run_manifest.json
  checkpoint.json
  attempts.jsonl
  per_item.csv
  summary_by_task.csv
  summary_by_family.csv
  statistics.json
  adaptive_trace_summary.json
  token_summary.json
  baseline_comparisons.csv
  figure_inputs/
    main_adaptive_results.csv
    confidence_intervals.csv
    baseline_comparison.csv
```

### `run_manifest.json`

Required fields:

| Field | Meaning |
|-------|---------|
| `schema_version` | Use `cognition.revision.run_manifest.v1`. |
| `run_id` | Timestamped stable identifier, not provider secret material. |
| `experiment_kind` | `single_pass`, `until_correct_iid`, `adaptive_session_memory`, `baseline_import`, or `dataset_comparison`. |
| `code_revision` | Git commit hash and dirty-worktree flag. |
| `python_version` | Runtime version. |
| `dependency_versions` | Provider SDKs, SciPy, pandas, numpy, Pillow, pydantic. |
| `dataset_manifest` | Dataset root, task names, item counts, ground-truth file hashes, image-count summary. |
| `prompt_manifest` | Prompt file hash, prompt mode, few-shot file hash if used. |
| `provider_config` | Provider name, model name, reasoning/thinking options, timeout, retry settings; no API keys. |
| `sampling_config` | Seed, max items, max attempts, replacement policy, task filters. |
| `cost_controls` | Estimated request count, optional budget cap, dry-run status. |
| `ethics_scope` | Offline owned/authorized datasets only; no live service automation. |

### `attempts.jsonl`

One JSON object per provider call:

| Field | Meaning |
|-------|---------|
| `schema_version` | `cognition.revision.attempt.v1`. |
| `run_id`, `attempt_id` | Stable identifiers. |
| `experiment_kind`, `policy_name`, `session_id` | Distinguish i.i.d. retries from adaptive session-memory attempts. |
| `provider`, `model` | Provider metadata. |
| `task_type`, `task_family`, `puzzle_id` | Canonical task metadata. |
| `attempt_idx`, `max_attempts` | Retry position. |
| `prompt_hash`, `image_hashes`, `ground_truth_hash` | Provenance without dumping sensitive or bulky content. |
| `parsed_response` | Normalized model output after JSON extraction. |
| `passed` | Boolean correctness. |
| `failure_category` | `wrong_count`, `wrong_coordinate`, `wrong_option`, `schema_error`, `parse_error`, `provider_error`, etc. |
| `tokens_in`, `tokens_out`, `e2e_ms`, `ttft_ms`, `cost_usd` | Operational metrics. |
| `infrastructure_error` | Separate provider/network/rate-limit failures from wrong answers. |
| `session_memory_delta` | Compact description of what the adaptive policy learned; no raw secrets. |

### Summary Tables

Keep CSV for paper tables and plots because the current analysis stack already expects CSV. Required summary columns:

```text
run_id,experiment_kind,policy_name,provider,model,task_type,task_family,
n_items,n_attempts,n_success,pass_rate,
ci_method,ci_level,ci_low,ci_high,
threshold,threshold_claim,threshold_claim_supported,
tokens_in,tokens_out,cost_usd,avg_e2e_ms,
dataset_name,dataset_version,notes
```

`statistics.json` should also include model-family and task-family aggregates with explicit methods:

| Statistic | Method |
|-----------|--------|
| Pass-rate confidence intervals | Wilson or exact binomial interval via SciPy; record method and confidence level. |
| Adaptive-vs-i.i.d. delta | Difference in pass rate with interval; bootstrap over task items when item-level records exist. |
| Threshold claims such as 40% | Report whether the confidence interval is fully below, crosses, or is fully above the threshold. |
| Exp2-to-Exp3 comparison | Keep the existing i.i.d. formula as a baseline model and report observed adaptive results separately. |
| Multiple task-family summaries | Prefer descriptive intervals over p-value-heavy reporting unless a specific manuscript claim requires a test. |

## Baseline and Dataset Comparison Format

Do not reimplement reviewer-cited systems first. Add an ingestion layer that can compare against published or locally reproduced outputs once primary artifacts are available.

Reviewer-grounded external works:

| Work Mentioned in Review Text | How to Treat in Stack |
|--------------------------------|------------------------|
| "Oedipus: LLM-enchanced Reasoning CAPTCHA Solver", CCS 2025 | Create a baseline-import adapter only after locating the primary paper/artifact. Unknown solver details require follow-up research. |
| "Are CAPTCHAs Still Bot-hard? Generalized Visual CAPTCHA Solving with Agentic Vision Language Model", USENIX 2025 | Create a dataset/baseline comparison adapter only after locating the primary paper/artifact. Unknown dataset schema and metrics require follow-up research. |

Baseline import schema:

```text
baseline_name,source_title,source_url,artifact_hash,dataset_name,
task_label_raw,task_type_mapped,task_family_mapped,
n_items,n_success,metric_name,metric_value,
ci_low,ci_high,notes,mapping_confidence
```

Rules:

| Rule | Rationale |
|------|-----------|
| Store raw external labels and mapped COGNITION labels. | Prevent silent overclaiming when task definitions differ. |
| Require `mapping_confidence` as `high`, `medium`, or `low`. | Reviewer comparisons may be partial rather than one-to-one. |
| Keep external baseline rows separate from native API-run attempts. | Imported claims may not have item-level attempt records. |
| Mark unknown solver mechanics as follow-up research. | The review text names works but does not provide enough implementation detail. |

## Reproducibility Practices

Implement these before full adaptive runs:

1. Add `pyproject.toml` with core, `analysis`, and `dev` dependency groups.
2. Generate and commit `uv.lock` or an exported locked requirements file.
3. Move secret-bearing local config to an ignored file and commit only an example template.
4. Add `configs/revision/*.yaml` experiment configs for adaptive, i.i.d., and baseline-import runs.
5. Write `run_manifest.json` before the first provider call.
6. Hash prompt files, ground-truth files, and image files in dataset manifests.
7. Capture SDK versions and model identifiers at runtime.
8. Use append-only `attempts.jsonl` for every run.
9. Derive all CSV summaries and figure inputs from the immutable attempt log.
10. Add `pytest` tests for task scoring, artifact schema validation, confidence interval calculations, and CLI preflight.

Security-specific requirements:

| Requirement | Implementation Guidance |
|-------------|-------------------------|
| Do not read or quote secret values in docs. | Treat `secrets.yaml` as local sensitive config; do not include values in manifests. |
| Do not print full config. | Log provider/model names and validation status only. |
| Keep raw reasoning/error dumps out of shareable artifacts by default. | Write redacted summaries for paper artifacts. |
| Separate provider errors from model failures. | Statistical pass-rate denominators should be explicit about excluded infrastructure failures. |

## What Not to Add

| Do Not Add | Reason |
|------------|--------|
| Web server, API backend, or production CAPTCHA service | Out of scope; paper revision needs offline evidence. |
| Browser automation or live CAPTCHA attack tooling | Conflicts with the offline/authorized-dataset scope. |
| MLflow/W&B/DVC | Too much artifact-platform migration for the revision timeline. |
| A relational database | Local append-only JSONL/CSV is sufficient and easier to audit. |
| A full Poetry migration | `pyproject.toml` plus uv/pip-compatible lock output is lower churn. |
| Custom statistical formulas where SciPy already provides maintained implementations | Reduces risk of math or edge-case mistakes. |
| Large external solver reimplementations before artifact research | Reviewers asked for comparisons; imports and documented scope are the first defensible step. |

## Recommended Phase Ordering for Roadmap

1. **Reproducible Runner Foundation**
   - Add `pyproject.toml`, lockfile, artifact schemas, preflight, attempt logging, and manifest writing.
   - Fix import-time side effects and secret printing before any new provider run.

2. **Task Registry and Scoring Hardening**
   - Add canonical task registry, alias handling, scorer tests, and schema validation.
   - Fix `Connect_Icon` alias drift and `Path_Finder` scoring before paper claims rely on those families.

3. **Statistical Confidence Reporting**
   - Add SciPy-backed confidence intervals and threshold-claim classification.
   - Recompute existing Exp1/Exp2/Exp3 summaries from current results where possible.

4. **Adaptive Session-Memory Attacker**
   - Implement `session_memory_v1` as a runner policy.
   - Output main-body figure inputs: adaptive success, i.i.d. baseline prediction, observed gap, cost, and task-family interpretation.

5. **Baseline and Dataset Comparison Hooks**
   - Add baseline import schemas and mapping tables.
   - Conduct separate primary-source research for Oedipus and the USENIX 2025 agentic VLM CAPTCHA paper before importing or reproducing any claims.

6. **Paper Artifact Export**
   - Generate curated CSVs/PDF inputs and a `paper_artifact_manifest.json` tying figures/tables to run IDs.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Core stack | HIGH | Existing repo is a Python script-oriented research framework; preserving it minimizes risk. |
| Dependency additions | HIGH | SciPy, Pydantic, pytest, and Ruff directly address stated gaps without imposing platform migration. |
| Result formats | HIGH | Versioned JSON manifests, JSONL attempts, and CSV summaries match current local-file workflow and reproducibility needs. |
| Adaptive runner structure | HIGH | The reviewer request maps cleanly to a policy-based retry runner with session memory. |
| External baseline details | MEDIUM | Review text names two works, but implementation details require primary paper/artifact research before claims. |

## Sources

- Internal: `.planning/PROJECT.md`, `.planning/codebase/STACK.md`, `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/CONCERNS.md`, `README.md`, `run_eval.py`, `run_single_experiment.py`, `experiments_helper.py`, `exp2_to_exp3_predict.py`.
- Reviewer context: `/Users/ukun/Desktop/USENIX Sec.txt`; external works are referenced only by the titles and venues included in the review text.
- Python Packaging User Guide: `pyproject.toml` is the standard place for project metadata, dependencies, and tool configuration. https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
- uv documentation: `uv.lock` captures exact resolved package versions and should be checked into version control for reproducible environments. https://docs.astral.sh/uv/concepts/projects/layout/
- SciPy documentation: `scipy.stats.binomtest(...).proportion_ci(...)` supports exact and Wilson binomial confidence intervals; `scipy.stats.bootstrap` supports bootstrap confidence intervals. https://scipy.github.io/devdocs/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html and https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html
- Pydantic documentation: Pydantic v2 models can validate data and produce JSON Schema via `model_json_schema()`. https://pydantic.dev/docs/validation/2.0/usage/json_schema/
- pytest documentation: pytest provides fixtures such as `tmp_path` and assertion helpers useful for file-oriented regression tests. https://docs.pytest.org/en/stable/getting-started.html
- Ruff documentation: Ruff provides both linting (`ruff check`) and formatting (`ruff format`) through one tool. https://docs.astral.sh/ruff/linter/ and https://docs.astral.sh/ruff/formatter/
