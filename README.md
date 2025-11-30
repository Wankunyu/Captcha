# Cognition: From Evaluation to Defense against Multimodal LLM CAPTCHA Solvers

A comprehensive framework for evaluating visual CAPTCHA tasks across multiple large language model providers (OpenAI GPT-5/5.1, Google Gemini 2.5, Anthropic Claude, Fireworks Qwen). Features 4 experimental paradigms testing 18 distinct task types with advanced visualization and statistical analysis capabilities.

## Project Structure

| Path | Purpose |
| --- | --- |
| `captcha_data/` | Raw CAPTCHA datasets with `ground_truth.json` metadata (18 task types). |
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
    gpt-5:
      in_per_1k: 0.0020
      out_per_1k: 0.0080
    gpt-5.1-medium:
      in_per_1k: 0.0025
      out_per_1k: 0.0100
    gpt-5.1-none:
      in_per_1k: 0.0015
      out_per_1k: 0.0060
  gemini:
    gemini-2.5-flash:
      in_per_1k: 0.0003
      out_per_1k: 0.0025
    gemini-2.5-pro:
      in_per_1k: 0.0010
      out_per_1k: 0.0050
  anthropic:
    claude-sonnet-4-5:
      in_per_1k: 0.003
      out_per_1k: 0.015
```

Each provider requires valid credentials before initialization.

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
7. **Custom Analysis**: Complete pipeline from Pass@1 → Success@3 → Expected cost per solve

All charts export to **PDF format** for publication quality.

**Note**: The visualization system focuses on the core 6 chart types used in the paper. Additional analysis tools are available through the `CAPTCHAVisualizer` class methods.

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
model = "gpt-5.1-medium"

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
  --model gpt-5.1-medium \
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

* **GPT-5 (Reasoning)**: Uses Responses API with `reasoning.effort` ("medium" by default), **no temperature parameter**
* **GPT-5.1 Medium/None**: Variants with different reasoning effort levels, uses Responses API
* **GPT-5-Chat-Latest**: Uses Chat Completions, non-reasoning model (`thinking=False`)

#### Anthropic

* **Claude Sonnet 4.5**, Claude 3.5 Sonnet
* Extended thinking modes: structured/freeform with `thinking_budget_tokens`
* Supports up to 64K thinking tokens for complex reasoning

#### Gemini

* **Gemini 2.5 Flash**, **Gemini 2.5 Pro**
* Thinking budget: -1=dynamic, 0=disabled, N=token limit
* Raw bytes image format (no base64 encoding)
* Supports multimodal reasoning with visual inputs

#### Fireworks

* **Qwen3-VL-235B-A22B-Instruct** and other vision-language models
* OpenAI-compatible API with extended vision capabilities
* Supports up to 30 images per request

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
* **Automatic Error Analysis**: Auto-generated error descriptions with detailed failure categorization
* **Token Tracking**: Per-question and aggregated cost calculations across all providers
* **Exp3 Format Handling**: Automatic conversion of Until-Correct CSV format with attempt tracking
* **Statistical Prediction Tools**: Baseline formulas for Exp2→Exp3 predictions (q = 1-(1-p)^k, A = [1-(1-p)^k]/p)
* **Display Name Mapping**: Professional model/experiment names for publication-quality outputs
* **Missing Data Tolerance**: Gracefully handles incomplete experiments with partial results

## Task Types

The toolkit evaluates 18 CAPTCHA task types across 4 categories:

1. **Click/Coordinate Tasks** (6 types): Dice_Count, Click_Order, Place_Dot, Geometry_Click, Pick_Area, Misleading_Click
2. **Grid Selection Tasks** (4 types): Patch_Select, Select_Animal, Image_Recognition, Unusual_Detection
3. **Image Matching Tasks** (4 types): Image_Matching, Object_Match, Path_Finder, Rotation_Match
4. **Logic/Reasoning Tasks** (4 types): Bingo, Dart_Count, Coordinates, Connect_Icon

## Recent Updates

* **GPT-5 and GPT-5.1 Support**: Full integration with OpenAI's latest reasoning models
* **Enhanced Statistical Analysis**: Exp2→Exp3 prediction tools with calibration diagnostics
* **Comprehensive Results**: Full evaluation across 6 major models (GPT-5, GPT-5.1 variants, Gemini 2.5 Flash/Pro, Claude Sonnet 4.5, Qwen3-VL)
* **Improved Visualization**: 11 generated figures with optimization resistance and cost-performance analysis
* **Dataset Expansion**: Extended samples across multiple task types for robust evaluation

## Further Reading

* [run_eval.py](run_eval.py): Provider implementations and evaluation logic
* [run_single_experiment.py](run_single_experiment.py): Experiment orchestration and CLI interface
* [visualize_results.py](visualize_results.py): Visualization system with 9+ chart types
* [exp2_to_exp3_predict.py](exp2_to_exp3_predict.py): Statistical prediction tools (baseline formulas: q = 1-(1-p)^k, A = [1-(1-p)^k]/p)
* [test_statistic.ipynb](test_statistic.ipynb): Prediction validation with calibration diagnostics
* [prompts_optimized.yaml](prompts_optimized.yaml): Task-specific optimized prompts

## Citation

If you use this toolkit in your research, please cite:

```bibtex
@software{captcha_eval_toolkit,
  title = {CAPTCHA Evaluation Toolkit},
  author = {Research Team},
  year = {2024},
  url = {https://github.com/yourusername/captcha}
}
```

---

**Version**: 2.1 (GPT-5/5.1 integration with statistical analysis)
**Last Updated**: November 30, 2024
