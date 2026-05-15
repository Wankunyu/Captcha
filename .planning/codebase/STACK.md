# Technology Stack

**Analysis Date:** 2026-05-15

## Languages

**Primary:**
- Python 3.10+ - evaluation engine, provider clients, CLIs, visualizations, and utility scripts in `run_eval.py`, `run_single_experiment.py`, `visualize_results.py`, `experiments_helper.py`, `exp2_to_exp3_predict.py`, `prepare_few_shot_examples.py`, and `compress_few_shot_assets.py`.

**Secondary:**
- Jupyter Notebook - interactive experiment and plotting workflows in `test.ipynb`, `plot.ipynb`, and `test_statistic.ipynb`.
- YAML - prompts, few-shot examples, and local secrets/pricing configuration in `prompts_optimized.yaml`, `few_shot_examples.yaml`, and `secrets.yaml`.
- JSON/CSV/PDF artifacts - CAPTCHA ground truth and output data in `captcha_data/*/ground_truth.json`, `results/`, `error_analysis/`, and `figures/`.

## Runtime

**Environment:**
- CPython - README requires Python 3.10+ in `README.md`; the active shell reports Python 3.11.5.
- Python notebook kernel - notebooks use `python3` kernels in `test.ipynb`, `plot.ipynb`, and `test_statistic.ipynb`.
- Git LFS - dataset files under `captcha_data/**` are marked as LFS-managed in `.gitattributes`; `run_eval.py` rejects Git LFS pointer text when loading `ground_truth.json`.

**Package Manager:**
- pip - README installs dependencies with `pip install` commands in `README.md`.
- Lockfile: missing. No `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`, `poetry.lock`, or `environment.yml` is present.
- Current interpreter packages detected: `openai` 2.6.1, `anthropic` 0.72.0, `google-genai` 1.39.1, `Pillow` 10.0.1, `tqdm` 4.65.0, `PyYAML` 6.0.2, `numpy` 1.24.3, `pandas` 1.5.3, `matplotlib` 3.7.1, `seaborn` 0.12.2, and optional `adjustText` 1.3.0.

## Frameworks

**Core:**
- Custom Python evaluation framework - `run_eval.py` defines `ModelProvider`, `OpenAIProvider`, `AnthropicProvider`, `GeminiProvider`, `FireworksProvider`, task loading, JSON-schema construction, Pass@1 scoring, token tracking, and cost estimation.
- Experiment orchestration CLI - `run_single_experiment.py` wraps four experiment modes with `argparse` entry points: ground-truth prompts, optimized prompts, until-correct retries, and few-shot learning.
- OpenAI Python SDK - `run_eval.py` uses `openai.OpenAI` for OpenAI Responses/Chat Completions and for Fireworks' OpenAI-compatible API.
- Anthropic Python SDK - `run_eval.py` uses `anthropic.Anthropic` for Claude Messages with tool-based JSON-schema output.
- Google Gen AI SDK - `run_eval.py` uses `google.genai.Client` and `google.genai.types` for Gemini multimodal JSON responses.

**Testing:**
- No dedicated automated test framework detected. There is no `pytest`, `unittest`, `tox`, `nox`, `jest`, or CI test config.
- Exploratory validation lives in notebooks and analysis scripts: `test.ipynb`, `test_statistic.ipynb`, `plot.ipynb`, and `exp2_to_exp3_predict.py`.

**Build/Dev:**
- `argparse` CLIs - `run_eval.py`, `run_single_experiment.py`, `exp2_to_exp3_predict.py`, `prepare_few_shot_examples.py`, and `compress_few_shot_assets.py` expose command-line workflows.
- Jupyter - notebooks drive interactive experiment execution, statistical checks, and publication chart generation.
- `matplotlib`/`seaborn` - `visualize_results.py` produces PDF visualizations and summary charts from `results/`.
- `zopflipng` and `jpegtran` - `compress_few_shot_assets.py` calls these external binaries for lossless PNG/JPEG optimization.

## Key Dependencies

**Critical:**
- `openai` - OpenAI GPT-5/GPT-5.1 integration and Fireworks OpenAI-compatible client usage in `run_eval.py`.
- `anthropic` - Claude Sonnet/Opus provider support in `run_eval.py`.
- `google-genai` - Gemini 2.5 Flash/Pro provider support in `run_eval.py`.
- `PyYAML` - loads `secrets.yaml`, `prompts_optimized.yaml`, and `few_shot_examples.yaml` in `run_eval.py` and `prepare_few_shot_examples.py`.
- `Pillow` - image inspection/compression support in `compress_few_shot_assets.py` and Anthropic image-size handling in `run_eval.py`.
- `tqdm` - progress reporting during evaluation loops in `run_eval.py`.

**Infrastructure:**
- `numpy` and `pandas` - result loading, statistical prediction, and dataframe processing in `visualize_results.py` and `exp2_to_exp3_predict.py`.
- `matplotlib` and `seaborn` - chart generation in `visualize_results.py`.
- `adjustText` - optional label-placement enhancement in `visualize_results.py`.
- Git LFS - required for actual CAPTCHA dataset content under `captcha_data/`, configured by `.gitattributes`.
- Local filesystem - stores datasets, prompts, few-shot assets, experiment outputs, error analysis, and generated figures in `captcha_data/`, `few_shot_assets/`, `results/`, `error_analysis/`, and `figures/`.

## Configuration

**Environment:**
- Provider credentials and pricing are configured in local `secrets.yaml`; `README.md`, `run_eval.py`, and `run_single_experiment.py` all default to `./secrets.yaml`.
- Optional `FEW_SHOT_ASSETS_ROOT` can override the default few-shot image root in `run_eval.py`; otherwise the code uses `./few_shot_assets`.
- Prompt overrides are configured through `prompts_optimized.yaml`, with structured sections consumed by `_load_prompts_yaml()` and `_resolve_prompt_cfg()` in `run_eval.py`.
- Few-shot examples are configured through `few_shot_examples.yaml` and answer data in `few_shot_answers.py`.
- Do not read or emit values from `secrets.yaml`; it is present and contains local environment configuration.

**Build:**
- No packaging/build configuration detected.
- No linting/formatting configuration detected.
- No CI configuration detected under `.github/`, `.gitlab/`, or `.circleci/`.
- Git LFS configuration exists in `.gitattributes`.

## Platform Requirements

**Development:**
- Python 3.10+ with the README dependency set installed.
- Valid provider API credentials in `secrets.yaml` for the selected provider.
- Git LFS materialized for `captcha_data/**` before running evaluations.
- Optional system binaries `zopflipng` and `jpegtran` for `compress_few_shot_assets.py`.
- Local dataset and asset directories: `captcha_data/`, `few_shot_assets/`, `few_shot_image_manifest.json`, `prompts_optimized.yaml`, and `few_shot_examples.yaml`.

**Production:**
- Not detected as a deployed service. The project is a local research/evaluation toolkit run from Python scripts and notebooks.
- Output persistence is local file-based storage under `results/`, `error_analysis/`, and `figures/`.

---

*Stack analysis: 2026-05-15*
