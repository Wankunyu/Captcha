# CAPTCHA Few-Shot Evaluation Toolkit

This repository collects the tooling we use to build, compress and evaluate vision CAPTCHA few-shot prompts across multiple LLM providers (OpenAI GPT‑5, Gemini, Anthropic, etc.). The codebase centres on the notebook `test.ipynb` for interactive experiments and the helper module `run_eval.py` for CLI / scripted usage.

## Project Structure

| Path | Purpose |
| --- | --- |
| `captcha_data/` | Source CAPTCHA images & `ground_truth.json` files per task. |
| `few_shot_assets/` | Optimised few-shot assets (JPEG/PNG) organised by task. |
| `few_shot_image_manifest.json` | Auto-generated manifest of all few-shot image paths. |
| `compress_few_shot_assets.py` | Script to losslessly compress images listed in the manifest. |
| `run_eval.py` | Provider implementations + experiment orchestration helpers. |
| `run_single_experiment.py` | CLI entry points for the four evaluation modes. |
| `test.ipynb` | Notebook wrapper that calls the four experiments with reusable path helpers. |
| `results/exp*/<provider>/<model>/` | Structured experiment outputs (CSV + token logs). |
| `error_analysis/exp*/<provider>/<model>/` | Structured error-analysis dumps. |

## Requirements

* Python 3.10+
* `pip install -r requirements.txt` *(if you maintain one; otherwise manually install):*
  * `openai` (Responses API + Chat Completions)
  * `anthropic`
  * `google-genai`
  * `pillow`
  * `tqdm`, `pyyaml`, `numpy`

## Configuration

Secrets live in `secrets.yaml`. Example snippet:

```yaml
providers:
  openai:
    api_key: sk-...
  anthropic:
    api_key: ...
  gemini:
    api_key: ...
```

If a provider’s key is missing, the corresponding `*Provider` raises a runtime error on first use.

## Few-Shot Asset Pipeline

1. Regenerate the manifest once assets change:
   ```bash
   python prepare_few_shot_examples.py --dataset ./captcha_data --n-shot 2 --output few_shot_examples.yaml
   ```
2. Compress all referenced images without changing dimensions:
   ```bash
   python compress_few_shot_assets.py
   ```
   A detailed report is written to `few_shot_image_compression_report.json`.

## Running Experiments

### Notebook Workflow

Open `test.ipynb`. Each experiment cell uses helpers:

```python
provider = "openai"
model = "gpt-5"               # or "gpt-5-chat-latest"

result4 = run_experiment_4(
    provider=provider,
    model=model,
    thinking=True,
    thinking_options={"effort": "high"},
    out_csv=exp_out_csv("exp4", provider, model),
    token_output_dir=exp_results_dir("exp4", provider, model),
    error_analysis_dir=exp_error_dir("exp4", provider, model),
    ...
)
```

* GPT‑5 reasoning uses the Responses API with strict JSON schema output when `strict_json_schema` is enabled (default `False`, toggle via `thinking_options`).
* GPT‑5 chat uses Chat Completions with `response_format={"type": "json_object"}`; `thinking` must remain `False` because the model does not accept reasoning controls.

All outputs funnel into `results/exp#/provider/model/` and matching error logs into `error_analysis/...`.

### CLI Workflow

```bash
python run_single_experiment.py 4 \
  --provider openai \
  --model gpt-5 \
  --types Dice_Count Click_Order Place_Dot Patch_Select \
  --few-shot-assets-root ./few_shot_assets \
  --few-shot-file ./few_shot_examples.yaml
```

Use `--thinking` and `--thinking-budget` for models that support reasoning.

## Notes on GPT‑5 Integration

* Reasoning models: set `model="gpt-5"`; adjust `thinking_options={"effort": "minimal"|"medium"|"high"}` to control depth (default `high`). Temperature is not sent because Responses API rejects it.
* Chat model: set `model="gpt-5-chat-latest"` with `thinking=False`.
* Both branches return `(raw, parsed_json, meta)` where `meta` includes `ttft_ms`, `e2e_ms`, and token counts.
* Provider timeout defaults to 120 seconds (`timeout_sec` can be overridden via experiment arguments).

## Cleaning & Organisation

Output folders are automatically created; no manual cleanup is required. Additional CSVs or ad-hoc experiments can be stored under `results/misc/` and `error_analysis/misc/`.

## Troubleshooting

* **Unsupported parameters**: GPT‑5 rejects temperature; ensure you’re on latest `run_eval.py`.
* **Missing assets**: regenerate manifest and rerun compression script.
* **Streaming exceptions**: confirm that the provider’s SDK is up to date and that your account has access to GPT‑5 features.

---
For further details, see the inline documentation in `run_eval.py` and `OpenAIProvider_Spec_v2.md`.
