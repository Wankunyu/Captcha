# Cognition: From Evaluation to Defense against Multimodal LLM CAPTCHA Solvers
LAST UPDATED: May 27, 2026

A comprehensive framework for evaluating visual CAPTCHA tasks across multiple large language model providers (OpenAI GPT-5/5.1, Google Gemini 2.5, Anthropic Claude, Fireworks Qwen). The paper evaluates four main CaptchaWorld experiment families on 18 task types, plus Exp5 adaptive session-memory evidence and three supplemental external categories.

This repository is prepared as a public artifact snapshot: default verification
paths are offline and dataset-based, local credentials are excluded, and
local planning workflow files are not part of the submission surface. See
`SUBMISSION.md` for clean-checkout setup, verification, and archive packaging.

Code is provided for non-commercial research and reproducibility purposes. Data,
documentation, and result artifacts are licensed under CC-BY-NC-4.0.

## Project Structure

| Path | Purpose |
| --- | --- |
| `SUBMISSION.md` | Submission-focused setup, verification, safety, and archive packaging guide. |
| `captcha_data/` | CaptchaWorld task directories with `ground_truth.json` metadata; the paper's main benchmark uses 18 cleaned task types. |
| `few_shot_assets/` | Compressed few-shot example images grouped by task type. |
| `few_shot_image_manifest.json` | Auto-generated manifest of all few-shot image paths. |
| `cognition/compress_few_shot_assets.py` | Lossless optimizer for images listed in the manifest. |
| `cognition/run_eval.py` | Core provider implementations (OpenAI, Gemini, Anthropic, Fireworks) and evaluation logic. |
| `cognition/run_single_experiment.py` | CLI entry points for Exp1-Exp4. |
| `cognition/experiments_helper.py` | Error analysis utilities with automatic error description generation. |
| `cognition/visualize_results.py` | Comprehensive visualization module with 9+ chart types. |
| `notebooks/plot.ipynb` | Interactive notebook for generating publication-quality PDF charts. |
| `notebooks/test_statistic.ipynb` | Statistical analysis and Exp2→Exp3 prediction validation. |
| `cognition/exp2_to_exp3_predict.py` | Practical implementation of baseline prediction formulas. |
| `notebooks/test.ipynb` | Notebook wrapper for running experiments with reusable path helpers. |
| `results/exp*/<provider>/<model>/` | Structured outputs for Exp1-Exp4 (CSV, token logs, cost summaries). |
| `results/exp5/` | Paper-facing Exp5 static/adaptive session-memory evidence, analysis rows, and table-ready outputs. |
| `results/sota_baselines/` | SOTA and baseline comparison artifacts. |
| `error_analysis/exp*/<provider>/<model>/` | Structured error dumps with detailed failure analysis. |
| `figures/` | Generated visualization outputs (PDF format). |

## Experiments Overview

| Experiment | Function | Description | Key Parameters |
| --- | --- | --- | --- |
| **Exp1: Direct Prompts** | `run_experiment_1` | Original human-facing task instructions from `ground_truth.json`. | `--max-per-type`, `--types` |
| **Exp2: Optimized Prompts** | `run_experiment_2` | Enhanced prompts from `prompts_optimized.yaml`. | `--prompts-file`, `--prompt-mode` |
| **Exp3: Until-Correct** | `run_experiment_3` | Retry strategy until success or budget exhaustion. | `--max-attempts-per-type`, `--max-pool-per-type` |
| **Exp4: Few-shot Learning** | `run_experiment_4` | N-shot examples from `few_shot_examples.yaml`. | `--few-shot-file`, `--n-shot` |
| **Exp5: Adaptive Session-Memory** | `cognition.expanded_dataset_phase042` | Static expanded-dataset evidence and adaptive session-memory comparison. | `evidence-analysis`, `final-outputs` |

Exp1-Exp4 share the main CaptchaWorld benchmark and differ by prompting or retry
strategy. Exp5 is the paper-facing adaptive session-memory evidence on hard or
near-hard main-benchmark tasks plus supplemental external categories.

## Paper-To-Artifact Map

| Paper item | Primary artifact paths |
| --- | --- |
| Table 1, evaluated models | `results/exp1/` through `results/exp4/`, provider notes below |
| Figures 2-5, Exp1/Exp2 pass-rate analysis | `results/exp1/`, `results/exp2/`, `figures/heatmap_exp1.pdf`, `figures/heatmap_exp2.pdf`, `figures/stability_exp1.pdf`, `figures/stability_exp2.pdf`, `figures/comparison_bars_openai_gpt-5.pdf` |
| Figures 6-8, finite-retry and cost/latency analysis | `cognition/exp2_to_exp3_predict.py`, `notebooks/test_statistic.ipynb`, `figures/exp3_mapping_pass_to_success_openai_gpt-5.pdf`, `figures/exp3_mapping_expected_calls_openai_gpt-5.pdf`, `figures/cost_performance_frontier_openai_gpt-5.pdf`, `figures/time_performance_scatter_openai_gpt-5.pdf` |
| Table 2, Exp4 few-shot results | `results/exp4/`, `few_shot_examples.yaml`, `few_shot_assets/` |
| Table 3, supplemental external evaluation | `expanded_captcha_data/phase04_2/evaluator_slice/`, `results/exp5/static_final_evidence_20260522/` |
| Table 4, GPT-5 static/adaptive comparison | `expanded_captcha_data/phase04_2/adaptive_evaluator_slice/`, `results/exp5/adaptive_final_evidence_20260522/`, `results/exp5/evidence_analysis/`, `results/exp5/final_outputs_20260522/` |
| Table 5, hardened Select_Animal defense validation | `captcha_data/Select_Animal_Optimized/`, `cognition/run_eval.py` |
| Table 7, task definitions and supplemental categories | `captcha_data/`, `expanded_captcha_data/phase04_2/`, task list below |
| Table 8, contextual SOTA/baseline comparison | `results/sota_baselines/`, `baseline_sources/`, `cognition/baseline_strengthening.py` |

## Requirements

* Python 3.10+
* `uv` 0.11.14 for reproducible dependency resolution:

  ```bash
  python3 -m pip install uv==0.11.14
  uv sync --locked
  ```

* Local validation commands:

  ```bash
  uv run pytest
  uv run ruff check .
  ```

The dependency contract is declared in `pyproject.toml` and locked in `uv.lock`; use
`uv sync --locked` to reproduce the local environment.

Build a clean submission archive from tracked files:

```bash
uv run python scripts/build_artifact_package.py
```

The archive builder excludes local secrets, local workflow files, caches, virtual
environments, notebook checkpoints, system metadata, and scratch local outputs.

## Configuration

Copy `secrets.example.yaml` to a local `secrets.yaml` and fill in provider credentials on
your machine. Keep `secrets.yaml` local; do not commit it or paste credential values into
reports, logs, notebooks, or generated artifacts.

```yaml
providers:
  openai:
    api_key: "<OPENAI_API_KEY>"
  anthropic:
    api_key: "<ANTHROPIC_API_KEY>"
  gemini:
    api_key: "<GEMINI_API_KEY>"
  fireworks:
    api_key: "<FIREWORKS_API_KEY>"
  openrouter:
    api_key: "<OPENROUTER_API_KEY>"
    base_url: "https://openrouter.ai/api/v1"
```

Each provider requires valid credentials before initialization.

## Offline Validation

Run the offline preflight before any paid provider run:

```bash
uv run python -m cognition.revision_preflight --dataset-root ./captcha_data --types Dice_Count --prompts-file ./prompts_optimized.yaml --output-root ./results/local_runs --run-id local-preflight --provider openai --model gpt-5 --max-per-type 2 --max-attempts 1
uv run pytest
uv run ruff check .
```

Local run artifacts are written under a run-specific directory:

```text
results/local_runs/<run_id>/
  run_manifest.json
  attempts.jsonl
  summary.csv
  summary.json
  preflight_report.json
```

## Adaptive Attacker Workflow

Adaptive attacker artifacts are written under `results/local_runs/<run_id>/` and use
binary pass/fail feedback, fresh-instance sampling without replacement,
experiment-controlled policy notes, and first-success-or-budget stopping.

### Offline adaptive preflight

```bash
uv run python -m cognition.adaptive_preflight --dataset-root ./captcha_data --types Dice_Count Patch_Select --prompts-file ./prompts_optimized.yaml --output-root ./results/local_runs --run-id local-adaptive-preflight --provider openai --model gpt-5 --prompt-mode opt --max-per-type 2 --attempt-budget-k 6 --write-report
```

The report includes `solve_request_count`, `reflection_request_count_max`,
`expected_request_count_max`, prompt/few-shot hashes, output paths,
`sampling_mode=without-replacement`, `feedback_mode=binary-pass-fail`,
`memory_mode=explicit-policy-notes`, and
`stopping_rule=first-success-or-budget`.

### Required offline validation

```bash
uv run pytest tests/test_adaptive_artifacts.py tests/test_adaptive_preflight.py tests/test_adaptive_attacker.py tests/test_adaptive_compare.py tests/test_adaptive_end_to_end.py -q
uv run ruff check cognition/adaptive_artifacts.py cognition/adaptive_preflight.py cognition/adaptive_attacker.py cognition/adaptive_compare.py tests
```

This is the default verification path and does not run paid provider calls.

### Adaptive run

```bash
uv run python -m cognition.adaptive_attacker --dataset-root ./captcha_data --types Dice_Count Patch_Select --prompts-file ./prompts_optimized.yaml --output-root ./results/local_runs --run-id adaptive-mainbody-local --provider openai --model gpt-5 --prompt-mode opt --max-per-type 20 --attempt-budget-k 6
```

This command is dataset-based and offline with respect to CAPTCHA services, but
it may make provider API calls if real credentials are configured locally.

### Comparison table input

```bash
uv run python -m cognition.adaptive_compare --results-dir ./results --adaptive-summary ./results/local_runs/adaptive-mainbody-local/adaptive_summary.csv --output-csv ./results/local_runs/adaptive-mainbody-local/adaptive_comparison.csv --output-json ./results/local_runs/adaptive-mainbody-local/adaptive_comparison.json --run-id adaptive-mainbody-local --provider openai --model gpt-5 --attempt-budget-k 6
```

### Optional paid smoke

Optional paid smoke is not part of default verification. First run adaptive
preflight and inspect `expected_request_count_max`; proceed only after an
explicit budget decision.

```bash
uv run python -m cognition.adaptive_preflight --dataset-root ./captcha_data --types Dice_Count --prompts-file ./prompts_optimized.yaml --output-root ./results/local_runs --run-id local-paid-smoke --provider openai --model gpt-5 --prompt-mode opt --max-per-type 1 --attempt-budget-k 2 --write-report
uv run python -m cognition.adaptive_attacker --dataset-root ./captcha_data --types Dice_Count --prompts-file ./prompts_optimized.yaml --output-root ./results/local_runs --run-id local-paid-smoke --provider openai --model gpt-5 --prompt-mode opt --max-per-type 1 --attempt-budget-k 2
```

## Dataset And Statistical Artifacts

Dataset and statistical artifact generation is offline and dataset-based. These commands do not perform browser automation against live services.
These commands do not read or print `secrets.yaml`.
Provider/model evidence should come from existing result CSV/JSON artifacts or
separately budget-gated, preflighted runs.

```bash
uv run python -m cognition.dataset_scope_audit --run-id phase3-local --output-root results/local_runs
uv run python -m cognition.extended_dataset_manifest --input-manifest path/to/extended_manifest.json --validation-outcomes path/to/validation_slice_outcomes.json --original-conclusions results/local_runs/phase3-local/threshold_sensitivity.json --run-id phase3-local --output-root results/local_runs
uv run python -m cognition.statistical_confidence --results-dir results --adaptive-summary results/local_runs/<adaptive_run_id>/adaptive_summary.csv --adaptive-comparison results/local_runs/<adaptive_run_id>/adaptive_comparison.csv --extended-validation-comparison results/local_runs/phase3-local/extended_validation_comparison.json --run-id phase3-local --output-root results/local_runs
uv run python -m cognition.retry_calibration --results-dir results --adaptive-summary results/local_runs/<adaptive_run_id>/adaptive_summary.csv --run-id phase3-local --output-root results/local_runs --attempt-budget-k 10
uv run python -m cognition.failure_taxonomy --adaptive-summary results/local_runs/<adaptive_run_id>/adaptive_summary.csv --retry-calibration results/local_runs/phase3-local/retry_calibration.csv --run-id phase3-local --output-root results/local_runs
uv run python -m cognition.limitations_summary --dataset-scope-json results/local_runs/phase3-local/dataset_scope_audit.json \
  --extended-manifest-json results/local_runs/phase3-local/extended_dataset_manifest.json \
  --extended-validation-comparison-json results/local_runs/phase3-local/extended_validation_comparison.json \
  --contribution-notes-md results/local_runs/phase3-local/dataset_contribution_notes.md \
  --pass-rate-confidence-json results/local_runs/phase3-local/pass_rate_confidence.json \
  --threshold-sensitivity-json results/local_runs/phase3-local/threshold_sensitivity.json \
  --retry-calibration-json results/local_runs/phase3-local/retry_calibration.json \
  --failure-taxonomy-json results/local_runs/phase3-local/failure_taxonomy.json \
  --run-id phase3-local \
  --output-root results/local_runs
```

The `--validation-outcomes` file may point to already-produced offline
selective validation outputs. Supplying this file is what creates
`extended_validation_comparison.json`, the original-vs-new comparison artifact;
These statistical commands do not mandate paid provider execution.

## Running Experiments

### Notebook Usage (notebooks/test.ipynb)

```python
provider = "openai"
model = "gpt-5.1"
reasoning_effort = "medium"

result = run_experiment_1(
    types=["Dice_Count", "Click_Order", "Patch_Select"],
    max_per_type=10,
    provider=provider,
    model=model,
    out_csv=exp_out_csv("exp1", provider, model),
    token_output_dir=exp_results_dir("exp1", provider, model),
    error_analysis_dir=exp_error_dir("exp1", provider, model),
    collect_tokens=True,
    collect_reasoning=False  # Set True for reasoning traces
)
```

### Provider-Specific Notes

#### OpenAI

* **GPT-5 (Reasoning)**: Uses Responses API with `reasoning.effort` ("medium" by default), **no temperature parameter**
* **GPT-5.1 (Reasoning)**: Uses Responses API with `reasoning.effort` ("medium"/"none"), **no temperature parameter**

#### Anthropic

* **Claude Sonnet 4.5**

#### Gemini

* **Gemini 2.5 Flash**, **Gemini 2.5 Pro**
* Thinking budget: -1=dynamic, 0=disabled, N=token limit

#### Fireworks

* **Qwen3-VL-235B-A22B-Instruct** and other vision-language models
* OpenAI-compatible API with extended vision capabilities
* Supports up to 30 images per request

## Visualization System

### Quick Start

Generate all charts automatically:

```python
from cognition.visualize_results import quick_visualize

viz = quick_visualize(
    results_dir="./results",
    output_dir="./figures",
    show=False
)
```

### Interactive Notebook (notebooks/plot.ipynb)

**Mode A: Quick Generation** - Run `quick_visualize()` to auto-generate all charts

**Mode B: Custom Control** - Fine-grained control with customizable parameters:

```python
# Step 1: Configure preferences
SELECTED_EXPERIMENT = 'exp2'
SELECTED_MODEL = "openai/gpt-5"
EXPERIMENTS_TO_COMPARE = ['exp1', 'exp2']

# Custom display names for publication
CUSTOM_MODEL_NAMES = {
    'openai/gpt-5': 'GPT-5 (Medium)',
    'openai/gpt-5.1_medium': 'GPT-5.1 (Medium)',
    'gemini/gemini-2.5-flash': 'Gemini 2.5 Flash',
}

# Step 2: Initialize with custom names
viz = CAPTCHAVisualizer(
    results_dir="./results",
    model_names=CUSTOM_MODEL_NAMES,
    exp_names={'exp1': 'Exp1 (Original Prompts)', 'exp2': 'Exp2 (Optimized Prompts)'}
)

# Step 3: Generate specific charts
viz.plot_heatmap(experiment=SELECTED_EXPERIMENT, save_path='./figures/heatmap_exp2.pdf')
viz.plot_comparison_bars(experiments=EXPERIMENTS_TO_COMPARE, model_filter=SELECTED_MODEL)
viz.plot_optimization_resistance(base_exp='exp1', opt_exp='exp2', model_filter=SELECTED_MODEL)
```

**Available chart methods:**

* `plot_heatmap()` - Task difficulty heatmap
* `plot_comparison_bars()` - Multi-experiment bar chart
* `plot_optimization_resistance()` - Exp1 vs Exp2 scatter plot
* `plot_cross_model_stability()` - Box plot analysis
* `plot_cost_performance_frontier()` - Cost-performance trade-offs
* `plot_time_performance_scatter()` - Latency-accuracy relationship

### Available Chart Types

1. **Heatmap**: Task difficulty overview across models with weighted Overall row
2. **Grouped Bar Chart**: Multi-experiment side-by-side comparison
3. **Scatter Plot**: Optimization resistance analysis (Exp1 vs Exp2)
4. **Box Plot**: Cross-model stability and variance analysis
5. **Cost-Performance Frontier**: API cost vs Pass@1 trade-offs with Pareto frontier
6. **Time-Performance Scatter**: Response latency vs accuracy relationship

All charts export to **PDF format** for publication quality.

## Output Organization

```text
results/
  exp1/<provider>/<model>/
    results.csv                                      # Performance by task type
    exp1_gt_<provider>_<model>_tokens.csv           # Per-question tokens
    exp1_gt_<provider>_<model>_token_summary.json   # Aggregated stats with cost
  exp2/...
  exp3/...  # Special format with attempt_idx and cumulative_ms
  exp4/...
  exp5/
    static_final_evidence_20260522/                 # Table 3/4 static evidence inputs
    adaptive_final_evidence_20260522/               # Table 4 adaptive evidence inputs
    evidence_analysis/                              # Exp5 analysis rows and divergence report
    final_outputs_20260522/                         # Table-ready rows and paper notes
  sota_baselines/                                   # Contextual SOTA/baseline comparison

error_analysis/
  exp1/<provider>/<model>/<variant>/
    errors.csv         # Detailed failures with auto-generated descriptions
    stats.json         # Performance statistics by task type
    token_summary.json # Token consumption summary

figures/
  heatmap_exp1.pdf
  comparison_bars.pdf
  exp3_analysis_<model>.pdf
  frontier_<model>.pdf
  radar_<experiment>_<model>.pdf
  ...
```

## Troubleshooting

| Issue | Solution |
| --- | --- |
| Missing API keys | Add keys to `secrets.yaml` |
| Timeout errors | Increase `timeout_sec` parameter (default: 120s) |
| JSON parsing failures | Check `raw_response` in `errors.csv` |
| GPT-5 parameter errors | Remove `temperature` parameter |
| Exp3 visualization errors | Ensure `avg_attempts` and `avg_e2e_ms` columns exist |

## Task Types

The paper's main CaptchaWorld benchmark contains 18 cleaned task types across
four families:

1. **Counting and aggregation** (2 types): Dice_Count, Dart_Count
2. **Pointing and path-based localization** (6 types): Place_Dot, Geometry_Click, Pick_Area, Misleading_Click, Click_Order, Path_Finder
3. **Grid selection and matching** (7 types): Bingo, Patch_Select, Image_Recognition, Select_Animal, Unusual_Detection, Object_Match, Image_Matching
4. **Relational and transformation puzzles** (3 types): Coordinates, Connect_Icon, Rotation_Match

Exp5 adds three supplemental external categories under
`expanded_captcha_data/phase04_2/`: Hole_Counting, Relation_Match, and
Symbol_Count. The repository also retains upstream or auxiliary directories
such as `Hold_Button(Not Used)`, `Slide_Puzzle(Not Used)`, and
`Select_Animal_Optimized`; these are not counted as the 18-task main benchmark.

## Recent Updates

* **GPT-5 and GPT-5.1 Support**: Full integration with OpenAI's latest reasoning models
* **Enhanced Statistical Analysis**: Exp2→Exp3 prediction tools with calibration diagnostics
* **Comprehensive Results**: Full evaluation across seven model configurations (GPT-5, GPT-5.1 variants, Gemini 2.5 Flash/Pro, Claude Sonnet 4.5, Qwen3-VL-235B-A22B-Instruct)
* **Improved Visualization**: 11 generated figures with optimization resistance and cost-performance analysis
* **Exp5 Evidence**: Supplemental external categories and adaptive session-memory evidence aligned with the paper's Table 3 and Table 4

## Further Reading

* [cognition/run_eval.py](cognition/run_eval.py): Provider implementations and evaluation logic
* [cognition/run_single_experiment.py](cognition/run_single_experiment.py): Experiment orchestration and CLI interface
* [cognition/visualize_results.py](cognition/visualize_results.py): Visualization system with 9+ chart types
* [cognition/exp2_to_exp3_predict.py](cognition/exp2_to_exp3_predict.py): Statistical prediction tools (baseline formulas: q = 1-(1-p)^k, A = [1-(1-p)^k]/p)
* [notebooks/test_statistic.ipynb](notebooks/test_statistic.ipynb): Prediction validation with calibration diagnostics
* [prompts_optimized.yaml](prompts_optimized.yaml): Task-specific optimized prompts
