# Cognition: From Evaluation to Defense against Multimodal LLM CAPTCHA Solvers
LAST UPDATED: Jan. 23, 2026

A comprehensive framework for evaluating visual CAPTCHA tasks across multiple large language model providers (OpenAI GPT-5/5.1, Google Gemini 2.5, Anthropic Claude, Fireworks Qwen). Features 4 experimental paradigms testing 19 distinct task types with advanced visualization and statistical analysis capabilities.

## Project Structure

| Path | Purpose |
| --- | --- |
| `captcha_data/` | Raw CAPTCHA datasets with `ground_truth.json` metadata (19 task types). |
| `few_shot_assets/` | Compressed few-shot example images grouped by task type. |
| `few_shot_image_manifest.json` | Auto-generated manifest of all few-shot image paths. |
| `compress_few_shot_assets.py` | Lossless optimizer for images listed in the manifest. |
| `run_eval.py` | Core provider implementations (OpenAI, Gemini, Anthropic, Fireworks) and evaluation logic. |
| `run_single_experiment.py` | CLI entry points for the four experiments. |
| `experiments_helper.py` | Error analysis utilities with automatic error description generation. |
| `visualize_results.py` | Comprehensive visualization module with 9+ chart types. |
| `plot.ipynb` | Interactive notebook for generating publication-quality PDF charts. |
| `test_statistic.ipynb` | Statistical analysis and Exp2→Exp3 prediction validation. |
| `exp2_to_exp3_predict.py` | Practical implementation of baseline prediction formulas. |
| `test.ipynb` | Notebook wrapper for running experiments with reusable path helpers. |
| `results/exp*/<provider>/<model>/` | Structured outputs (CSV, token logs, cost summaries). |
| `error_analysis/exp*/<provider>/<model>/` | Structured error dumps with detailed failure analysis. |
| `figures/` | Generated visualization outputs (PDF format). |

## Experiments Overview

| Experiment | Function | Description | Key Parameters |
| --- | --- | --- | --- |
| **Exp1: Ground Truth** | `run_experiment_1` | Baseline using prompts from `ground_truth.json`. | `--max-per-type`, `--types` |
| **Exp2: Optimized Prompts** | `run_experiment_2` | Enhanced prompts from `prompts_optimized.yaml`. | `--prompts-file`, `--prompt-mode` |
| **Exp3: Until-Correct** | `run_experiment_3` | Retry strategy until success or budget exhaustion. | `--max-attempts-per-type`, `--max-pool-per-type` |
| **Exp4: Few-shot Learning** | `run_experiment_4` | N-shot examples from `few_shot_examples.yaml`. | `--few-shot-file`, `--n-shot` |

All experiments support token tracking, cost analysis, and reasoning collection.

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

## Configuration

Copy `secrets.example.yaml` to a local `secrets.yaml` and fill in provider credentials on
your machine. Keep `secrets.yaml` local; do not commit it or paste credential values into
reports, logs, notebooks, or planning artifacts.

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
```

Each provider requires valid credentials before initialization.

## Phase 1 Validation

Run the offline preflight before any paid provider run:

```bash
uv run python revision_preflight.py --dataset-root ./captcha_data --types Dice_Count --prompts-file ./prompts_optimized.yaml --output-root ./results/revision --run-id local-preflight --provider openai --model gpt-5 --max-per-type 2 --max-attempts 1
uv run pytest
uv run ruff check .
```

Revision artifacts are written under a run-specific directory:

```text
results/revision/<run_id>/
  run_manifest.json
  attempts.jsonl
  summary.csv
  summary.json
  preflight_report.json
```

## Phase 2 Adaptive Attacker Workflow

Phase 2 adaptive artifacts are written under `results/revision/<run_id>/` and use
binary pass/fail feedback, fresh-instance sampling without replacement,
experiment-controlled policy notes, and first-success-or-budget stopping.

### Offline adaptive preflight

```bash
uv run python adaptive_preflight.py --dataset-root ./captcha_data --types Dice_Count Patch_Select --prompts-file ./prompts_optimized.yaml --output-root ./results/revision --run-id local-adaptive-preflight --provider openai --model gpt-5 --prompt-mode opt --max-per-type 2 --attempt-budget-k 6 --write-report
```

The report includes `solve_request_count`, `reflection_request_count_max`,
`expected_request_count_max`, prompt/few-shot hashes, output paths,
`sampling_mode=without-replacement`, `feedback_mode=binary-pass-fail`,
`memory_mode=explicit-policy-notes`, and
`stopping_rule=first-success-or-budget`.

### Required offline validation

```bash
uv run pytest tests/test_adaptive_artifacts.py tests/test_adaptive_preflight.py tests/test_adaptive_attacker.py tests/test_adaptive_compare.py tests/test_adaptive_end_to_end.py -q
uv run ruff check adaptive_artifacts.py adaptive_preflight.py adaptive_attacker.py adaptive_compare.py tests
```

This is the default verification path and does not run paid provider calls.

### Adaptive run

```bash
uv run python adaptive_attacker.py --dataset-root ./captcha_data --types Dice_Count Patch_Select --prompts-file ./prompts_optimized.yaml --output-root ./results/revision --run-id adaptive-mainbody-local --provider openai --model gpt-5 --prompt-mode opt --max-per-type 20 --attempt-budget-k 6
```

This command is dataset-based and offline with respect to CAPTCHA services, but
it may make provider API calls if real credentials are configured locally.

### Comparison table input

```bash
uv run python adaptive_compare.py --results-dir ./results --adaptive-summary ./results/revision/adaptive-mainbody-local/adaptive_summary.csv --output-csv ./results/revision/adaptive-mainbody-local/adaptive_comparison.csv --output-json ./results/revision/adaptive-mainbody-local/adaptive_comparison.json --run-id adaptive-mainbody-local --provider openai --model gpt-5 --attempt-budget-k 6
```

### Optional paid smoke

Optional paid smoke is not part of default verification. First run adaptive
preflight and inspect `expected_request_count_max`; proceed only after an
explicit budget decision.

```bash
uv run python adaptive_preflight.py --dataset-root ./captcha_data --types Dice_Count --prompts-file ./prompts_optimized.yaml --output-root ./results/revision --run-id local-paid-smoke --provider openai --model gpt-5 --prompt-mode opt --max-per-type 1 --attempt-budget-k 2 --write-report
uv run python adaptive_attacker.py --dataset-root ./captcha_data --types Dice_Count --prompts-file ./prompts_optimized.yaml --output-root ./results/revision --run-id local-paid-smoke --provider openai --model gpt-5 --prompt-mode opt --max-per-type 1 --attempt-budget-k 2
```

## Running Experiments

### Notebook Usage (test.ipynb)

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
from visualize_results import quick_visualize

viz = quick_visualize(
    results_dir="./results",
    output_dir="./figures",
    show=False
)
```

### Interactive Notebook (plot.ipynb)

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

The toolkit evaluates 19 CAPTCHA task types across 4 categories:

1. **Click/Coordinate Tasks** (7 types): Dice_Count, Click_Order, Place_Dot, Geometry_Click, Pick_Area, Misleading_Click, Select_Animal_Optimized
2. **Grid Selection Tasks** (4 types): Patch_Select, Select_Animal, Image_Recognition, Unusual_Detection
3. **Image Matching Tasks** (4 types): Image_Matching, Object_Match, Path_Finder, Rotation_Match
4. **Logic/Reasoning Tasks** (4 types): Bingo, Dart_Count, Coordinates, Connect_Icon

## Recent Updates

* **GPT-5 and GPT-5.1 Support**: Full integration with OpenAI's latest reasoning models
* **Enhanced Statistical Analysis**: Exp2→Exp3 prediction tools with calibration diagnostics
* **Comprehensive Results**: Full evaluation across 6 major models (GPT-5, GPT-5.1 variants, Gemini 2.5 Flash/Pro, Claude Sonnet 4.5, Qwen3-VL-235B-A22B-Instruct)
* **Improved Visualization**: 11 generated figures with optimization resistance and cost-performance analysis
* **Dataset Expansion**: Extended samples across multiple task types for robust evaluation

## Further Reading

* [run_eval.py](run_eval.py): Provider implementations and evaluation logic
* [run_single_experiment.py](run_single_experiment.py): Experiment orchestration and CLI interface
* [visualize_results.py](visualize_results.py): Visualization system with 9+ chart types
* [exp2_to_exp3_predict.py](exp2_to_exp3_predict.py): Statistical prediction tools (baseline formulas: q = 1-(1-p)^k, A = [1-(1-p)^k]/p)
* [test_statistic.ipynb](test_statistic.ipynb): Prediction validation with calibration diagnostics
* [prompts_optimized.yaml](prompts_optimized.yaml): Task-specific optimized prompts
