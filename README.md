# Cognition: From Evaluation to Defense against Multimodal LLM CAPTCHA Solvers

This repository contains the tooling we use to evaluate visual CAPTCHA tasks across several large language model providers (OpenAI GPT‑5, Google Gemini, Anthropic Claude, etc.). The workflow is built around four experiments that measure different prompting strategies, plus utilities for maintaining the few-shot image corpus.

## Project Structure

| Path | Purpose |
| --- | --- |
| `captcha_data/` | Raw CAPTCHA datasets with `ground_truth.json` metadata per task. |
| `few_shot_assets/` | Compressed few-shot example images grouped by task type. |
| `few_shot_image_manifest.json` | Auto-generated manifest of all few-shot image paths. |
| `compress_few_shot_assets.py` | Lossless optimiser for images listed in the manifest. |
| `run_eval.py` | Core provider implementations (OpenAI, Gemini, Anthropic) and shared evaluation logic. |
| `run_single_experiment.py` | CLI entry points for the four experiments. |
| `test.ipynb` | Notebook wrapper driving the experiments with reusable path helpers. |
| `results/exp*/<provider>/<model>/` | Structured outputs (CSV, token logs). |
| `error_analysis/exp*/<provider>/<model>/` | Structured error-analysis dumps. |

## Experiments Overview

| Experiment | Function | Description | Extra Inputs |
| --- | --- | --- | --- |
| 1. Ground Truth Prompts | `run_experiment_1` | Baseline using prompts from `ground_truth.json`. | `--max-per-type`, `--types` |
| 2. Optimised Prompts | `run_experiment_2` | Uses prompts defined in `prompts_optimized.yaml`. | `--prompts-file` |
| 3. Until Correct | `run_experiment_3` | Reattempts a task until the model succeeds or the budget is exhausted. | `--max-attempts-per-type`, `--max-pool-per-type` |
| 4. Few-shot + Optimised | `run_experiment_4` | Prepends N-shot examples drawn from `few_shot_examples.yaml` / `few_shot_assets/`. | `--few-shot-file`, `--few-shot-assets-root`, `--n-shot` |

All experiments share the same output conventions and helper utilities for notebook/CLI usage.

## Requirements

* Python 3.10+
* Recommended packages (install manually or via your own `requirements.txt`):
  * `openai`
  * `anthropic`
  * `google-genai`
  * `pillow`
  * `tqdm`
  * `pyyaml`
  * `numpy`

## Configuration

API keys are defined in `secrets.yaml`:

```yaml
providers:
  openai:
    api_key: sk-...
  anthropic:
    api_key: ...
  gemini:
    api_key: ...
```

Each provider refuses to initialise without a key, ensuring the user supplies credentials explicitly.

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

## Running Experiments in the Notebook

Open `test.ipynb`. Each cell declares `provider`, `model`, and uses three helpers to compute output paths:

```python
provider = "openai"
model = "gpt-5"  # or "gpt-5-chat-latest", "gemini-2.5-flash", etc.

result1 = run_experiment_1(
    types=ERROR_TYPES,
    max_per_type=1,
    provider=provider,
    model=model,
    thinking=True,
    thinking_options={"effort": "high"},        # applies only to reasoning models
    out_csv=exp_out_csv("exp1", provider, model),
    token_output_dir=exp_results_dir("exp1", provider, model),
    error_analysis_dir=exp_error_dir("exp1", provider, model),
    collect_tokens=True,
    collect_reasoning=True
)
```

* Experiment 2 simply switches to `run_experiment_2` and provides `prompts_file`.
* Experiment 3 adds retry-specific knobs (`max_attempts_per_type`, `max_pool_per_type`).
* Experiment 4 includes `few_shot_file`, `few_shot_assets_root`, and `n_shot`.

### Provider Notes

* **OpenAI GPT‑5 reasoning (`model="gpt-5"`):** Uses the Responses API. When `thinking=True`, `reasoning.effort` defaults to `"high"` but can be overridden via `thinking_options`. Strict JSON schema output can be toggled by setting `thinking_options["strict_json_schema"]=True`. The API rejects a `temperature` parameter, so it is omitted.
* **OpenAI GPT‑5 chat (`model="gpt-5-chat-latest"`):** Uses Chat Completions with `response_format={"type": "json_object"}`. This is a non-reasoning model, so `thinking` must remain `False`.
* **Gemini & Anthropic:** Continue to work as in previous versions; provide the appropriate provider/model pair and keys.

Each run writes results to `results/exp#/provider/model/` and error dumps to `error_analysis/exp#/provider/model/`.

## CLI Usage

The CLI mirrors the notebook helpers. Example (Experiment 4 with GPT‑5 reasoning):

```bash
python run_single_experiment.py 4 \
  --provider openai \
  --model gpt-5 \
  --types Dice_Count Click_Order Place_Dot Patch_Select \
  --few-shot-file ./few_shot_examples.yaml \
  --few-shot-assets-root ./few_shot_assets \
  --thinking \
  --thinking-budget 2048
```

Switch the leading number to run Experiments 1–3. Shared flags (`--dataset`, `--out-csv`, `--token-output-dir`, `--error-analysis`) are consistent across experiments.

## Output Organisation

* `results/exp*/provider/model/` – contains `results.csv`, token summaries, streaming logs, etc.
* `error_analysis/exp*/provider/model/` – contains `errors.csv`, `stats.json`, and token diagnostics. Miscellaneous / exploratory runs are moved under `results/misc/` and `error_analysis/misc/`.

## Troubleshooting

* **Missing strict JSON outputs** – ensure `thinking_options["strict_json_schema"] = True` (Responses API only).
* **Unsupported parameter errors** – GPT‑5 rejects `temperature`; confirm you’re using the latest `run_eval.py`.
* **Timeouts** – default OpenAI timeout is 120 seconds; override with `timeout_sec` if necessary.
* **Missing assets** – rerun `prepare_few_shot_examples.py` followed by `compress_few_shot_assets.py`.

## Further Reading

Consult the provider-specific notes in `run_eval.py`, the experiment orchestration in `run_single_experiment.py`, and the OpenAI integration requirements in `OpenAIProvider_Spec_v2.md` for deeper implementation details.
