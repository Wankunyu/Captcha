# Cognition: From Evaluation to Defense against Multimodal LLM CAPTCHA Solvers

A comprehensive framework for evaluating visual CAPTCHA tasks across multiple large language model providers (OpenAI GPT-5, Google Gemini, Anthropic Claude, Fireworks Qwen). Features 4 experimental paradigms, 20 task types, and advanced visualization capabilities.

## Project Structure

| Path | Purpose |
| --- | --- |
| `captcha_data/` | Raw CAPTCHA datasets with `ground_truth.json` metadata (20 task types). |
| `few_shot_assets/` | Compressed few-shot example images grouped by task type. |
| `few_shot_image_manifest.json` | Auto-generated manifest of all few-shot image paths. |
| `compress_few_shot_assets.py` | Lossless optimizer for images listed in the manifest. |
| `run_eval.py` | Core provider implementations (OpenAI, Gemini, Anthropic, Fireworks) and evaluation logic. |
| `run_single_experiment.py` | CLI entry points for the four experiments. |
| `experiments_helper.py` | Error analysis utilities with automatic error description generation. |
| `visualize_results.py` | **NEW** Comprehensive visualization module with 9+ chart types. |
| `plot.ipynb` | **NEW** Interactive notebook for generating publication-quality PDF charts. |
| `test.ipynb` | Notebook wrapper for running experiments with reusable path helpers. |
| `results/exp*/<provider>/<model>/` | Structured outputs (CSV, token logs, cost summaries). |
| `error_analysis/exp*/<provider>/<model>/` | Structured error dumps with detailed failure analysis. |
| `figures/` | **NEW** Generated visualization outputs (PDF format). |

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
* Core dependencies:

  ```bash
  pip install openai anthropic google-genai pillow tqdm pyyaml numpy pandas matplotlib seaborn
  ```

* Optional for enhanced visualizations:

  ```bash
  pip install adjustText  # Automatic label positioning in scatter plots
  ```

## Configuration

API keys and pricing are defined in `secrets.yaml`:

```yaml
providers:
  openai:
    api_key: sk-...
  anthropic:
    api_key: sk-ant-...
  gemini:
    api_key: ...
  fireworks:
    api_key: ...

pricing:
  openai:
    gpt-5-chat-latest:
      in_per_1k: 0.0025
      out_per_1k: 0.010
  gemini:
    gemini-2.5-flash:
      in_per_1k: 0.0003
      out_per_1k: 0.0025
```

Each provider requires valid credentials before initialization.

## Visualization System (NEW)

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

**Mode A: Quick Generation** - Run a single cell to generate all charts

**Mode B: Custom Control** - Configure experiment, model, and display names:

```python
# Configure preferences
SELECTED_EXPERIMENT = 'exp2'
SELECTED_MODEL = "openai/gpt-5-chat-latest"
EXPERIMENTS_TO_COMPARE = ['exp1', 'exp2', 'exp4']

# Custom display names for publication
CUSTOM_MODEL_NAMES = {
    'openai/gpt-5': 'GPT-5 (Reasoning)',
    'openai/gpt-5-chat-latest': 'GPT-5 Chat',
    'gemini/gemini-2.5-flash': 'Gemini 2.5 Flash',
}

# Initialize with custom names
viz = CAPTCHAVisualizer(
    results_dir="./results",
    model_names=CUSTOM_MODEL_NAMES,
    exp_names={'exp1': 'Baseline', 'exp2': 'Optimized'}
)

# Generate specific charts
viz.plot_heatmap(experiment=SELECTED_EXPERIMENT)
viz.plot_exp3_analysis(model_filter=SELECTED_MODEL)
```

### Available Chart Types

1. **Heatmap**: Task difficulty overview across models
2. **Grouped Bar Chart**: Multi-experiment comparison
3. **Scatter Plot**: Optimization resistance analysis (Exp1 vs Exp2)
4. **Box Plot**: Cross-model stability analysis
5. **Exp3 Analysis**: 4-panel Until-Correct comprehensive analysis
6. **Cost-Performance Frontier**: Cost vs Pass@1 trade-offs
7. **Time-Performance Scatter**: Latency vs accuracy
8. **Slope Chart**: Per-task improvement visualization
9. **Radar Chart**: Task family performance (Click/Grid/Matching/Logic)

All charts export to **PDF format** for publication quality.

## Few-shot Asset Pipeline

1. Regenerate examples if the dataset changes:

   ```bash
   python prepare_few_shot_examples.py --dataset ./captcha_data --n-shot 2 --output few_shot_examples.yaml
   ```

2. Compress all example images without resizing:

   ```bash
   python compress_few_shot_assets.py
   ```

   The script creates `few_shot_image_compression_report.json` summarising byte savings.

## Running Experiments

### Notebook Usage (test.ipynb)

```python
provider = "openai"
model = "gpt-5-chat-latest"

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

### CLI Usage

```bash
# Experiment 1: Baseline
python run_single_experiment.py 1 \
  --provider openai \
  --model gpt-5-chat-latest \
  --max-per-type 10

# Experiment 3: Until-Correct
python run_single_experiment.py 3 \
  --provider anthropic \
  --model claude-sonnet-4-5 \
  --max-attempts-per-type 5

# Experiment 4: Few-Shot with Reasoning
python run_single_experiment.py 4 \
  --provider openai \
  --model gpt-5 \
  --n-shot 2 \
  --thinking \
  --thinking-budget 2048
```

### Provider-Specific Notes

#### OpenAI

* **GPT-5 (Reasoning)**: Uses Responses API, supports `reasoning.effort` ("low"/"medium"/"high"), **no temperature parameter**
* **GPT-5-Chat**: Uses Chat Completions, non-reasoning model (`thinking=False`)

#### Anthropic

* Claude Sonnet 4.5, Claude 3.5 Sonnet
* Thinking modes: structured/freeform with `thinking_budget_tokens`

#### Gemini

* gemini-2.5-flash, gemini-2.5-pro
* Thinking budget: -1=dynamic, 0=disabled, N=token limit
* Raw bytes image format (no base64)

#### Fireworks

* Qwen3-VL-235B and others
* OpenAI-compatible API
* Up to 30 images per request

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
| Missing adjustText | Install with `pip install adjustText` |
| Scatter plot label overlap | Enable `use_adjust_text=True` (default) |

## Key Features

* **Zero-Conversion Image Pipeline**: Images loaded as raw bytes, no resizing/format conversion
* **Automatic Error Analysis**: Auto-generated error descriptions for all failures
* **Token Tracking**: Per-question and aggregated cost calculations
* **Exp3 Format Handling**: Automatic conversion of Until-Correct CSV format
* **Display Name Mapping**: Professional model/experiment names for publication
* **Missing Data Tolerance**: Gracefully handles incomplete experiments

## Further Reading

* `CLAUDE.md`: Detailed project overview and development guidelines
* `run_eval.py`: Provider implementations and evaluation logic
* `run_single_experiment.py`: Experiment orchestration
* `visualize_results.py`: Visualization system documentation
* `STATISTICAL_LINK_EXP2_EXP3.md`: Theoretical link between Exp2 (Pass@1) and Exp3 (until-correct) under the baseline truncated-geometric model
* `exp2_to_exp3_predict.py` + `test_statistic.ipynb`: Practical implementation of Exp2 → Exp3 predictions using the baseline formulas \(q = 1 - (1-p)^k\), \(A = [1 - (1-p)^k]/p\), with optional finite-pool and calibration diagnostics
* `prompts_optimized.yaml`: Task-specific optimized prompts

---

**Version**: 2.0 (with visualization system)
**Last Updated**: November 2024
