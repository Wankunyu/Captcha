# Architecture

**Analysis Date:** 2026-05-15

## Pattern Overview

**Overall:** Flat, script-oriented Python research pipeline with data-driven task construction and provider-adapter inference.

**Key Characteristics:**
- Core execution lives in a root-level module, `run_eval.py`, instead of a packaged `src/` layout.
- CAPTCHA tasks are driven by filesystem data under `captcha_data/<TaskType>/ground_truth.json`, with task-specific prompt, image, schema, and scoring logic in `run_eval.py`.
- Model calls are normalized through provider classes in `run_eval.py`: `OpenAIProvider`, `AnthropicProvider`, `GeminiProvider`, and `FireworksProvider`.
- Experiment entry points are thin wrappers in `run_single_experiment.py` around `run_eval.run_eval()` and `run_eval.run_until_type_correct()`.
- Analysis and publication outputs are separate modules: `experiments_helper.py`, `visualize_results.py`, and `exp2_to_exp3_predict.py`.
- Project-specific agent skills are not detected: `.claude/skills/` and `.agents/skills/` are absent.

## Layers

**Experiment Orchestration:**
- Purpose: Provide user-facing functions and CLI routing for experiments 1 through 4.
- Location: `run_single_experiment.py`
- Contains: `run_experiment_1()`, `run_experiment_2()`, `run_experiment_3()`, `run_experiment_4()`, `_collect_error_analysis()`, and `main()`.
- Depends on: `run_eval.py` for evaluation primitives and `experiments_helper.py` for optional error collection.
- Used by: CLI calls such as `python run_single_experiment.py 1 --types Dice_Count`, notebooks such as `test.ipynb`, and README examples in `README.md`.

**Core Evaluation Engine:**
- Purpose: Load data, build tasks, call model providers, parse JSON, score predictions, aggregate metrics, and write outputs.
- Location: `run_eval.py`
- Contains: `TaskItem`, `SUPPORTED_TYPES`, `build_tasks()`, `build_json_schema()`, `evaluate_pass1()`, `run_eval()`, and `run_until_type_correct()`.
- Depends on: `captcha_data/`, `prompts_optimized.yaml`, `few_shot_examples.yaml`, `few_shot_answers.py`, `secrets.yaml`, and provider SDKs.
- Used by: `run_single_experiment.py`, direct CLI use of `run_eval.py`, notebooks, and ad hoc experiment helpers embedded in `run_eval.py`.

**Provider Adapter Layer:**
- Purpose: Hide provider-specific image formatting, structured output, timing, token accounting, and API call mechanics behind a shared `infer()` shape.
- Location: `run_eval.py`
- Contains: `ModelProvider`, `OpenAIProvider`, `AnthropicProvider`, `GeminiProvider`, `FireworksProvider`, and `make_provider()`.
- Depends on: `openai`, `anthropic`, `google.genai`, provider config in `secrets.yaml`, and image bytes from `ImageCache`.
- Used by: `run_eval.run_eval()` and `run_eval.run_until_type_correct()`.

**Task Data Layer:**
- Purpose: Store raw CAPTCHA images and per-task ground truth metadata.
- Location: `captcha_data/`
- Contains: task directories such as `captcha_data/Dice_Count/`, `captcha_data/Geometry_Click/`, `captcha_data/Image_Recognition/`, and `captcha_data/Rotation_Match/`, each with `ground_truth.json`.
- Depends on: Git LFS tracking in `.gitattributes`.
- Used by: `run_eval.load_ground_truth()`, `run_eval.build_tasks()`, and `experiments_helper.load_tasks_from_ground_truth()`.

**Prompt and Few-Shot Configuration:**
- Purpose: Configure optimized prompt rules, sample few-shot examples, and resolved few-shot answer payloads.
- Location: `prompts_optimized.yaml`, `few_shot_examples.yaml`, `few_shot_answers.py`, `few_shot_image_manifest.json`, and `few_shot_assets/`.
- Contains: prompt rules keyed by task type, few-shot sample manifests, hard-coded sample answers, and compressed example image paths.
- Depends on: `prepare_few_shot_examples.py` for manifest generation and `compress_few_shot_assets.py` for asset optimization.
- Used by: `run_eval._load_prompts_yaml()`, `run_eval._choose_prompt()`, `run_eval.load_few_shot_examples()`, and `run_eval.build_few_shot_content()`.

**Error Analysis Layer:**
- Purpose: Capture failed predictions, per-type summary stats, and token usage for diagnosis.
- Location: `experiments_helper.py`, `error_analysis/`, and `results/error_analysis/`.
- Contains: `ErrorCase`, `SimpleErrorCollector`, `compare_experiments()`, and `load_tasks_from_ground_truth()`.
- Depends on: `run_eval.run_eval()` passing raw responses, parsed JSON, ground truth, timing, and tokens.
- Used by: `run_eval.run_eval()` when `collect_errors=True` and by `run_single_experiment._collect_error_analysis()`.

**Visualization and Statistical Analysis:**
- Purpose: Load structured result directories, normalize experiment formats, generate charts, and compute Exp2-to-Exp3 predictions.
- Location: `visualize_results.py`, `exp2_to_exp3_predict.py`, `plot.ipynb`, and `test_statistic.ipynb`.
- Contains: `CAPTCHAVisualizer`, `quick_visualize()`, chart methods, and truncated-geometric prediction helpers.
- Depends on: CSV and JSON outputs in `results/`, optional error data in `error_analysis/`, and output directory `figures/`.
- Used by: notebook workflows and direct scripts for PDF/chart generation.

**Generated Output Layer:**
- Purpose: Persist experiment summaries, token logs, error reports, and figures.
- Location: `results/`, `error_analysis/`, and `figures/`.
- Contains: `results/exp1/<provider>/<model>/results.csv`, `results/exp2/<provider>/<model>/results.csv`, `results/exp3/<provider>/<model>/results.csv`, token CSVs, token summaries, error CSVs, and PDF figures.
- Depends on: write calls from `run_eval.py`, `experiments_helper.py`, `visualize_results.py`, and `exp2_to_exp3_predict.py`.
- Used by: `visualize_results.CAPTCHAVisualizer`, README examples, and notebooks.

## Data Flow

**Single-Pass Experiments (Exp1, Exp2, Exp4):**

1. `run_single_experiment.py` parses CLI arguments in `main()` or exposes `run_experiment_1()`, `run_experiment_2()`, and `run_experiment_4()` for imports.
2. The wrapper calls `run_eval.run_eval()` with `dataset_root`, `types`, provider/model settings, output paths, prompt mode, token collection flags, and optional few-shot configuration.
3. `run_eval.run_eval()` loads provider config from `secrets.yaml` with `load_secrets()` and prompt rules from `prompts_optimized.yaml` with `_load_prompts_yaml()`.
4. `run_eval.build_tasks()` reads `captcha_data/<TaskType>/ground_truth.json`, resolves image paths, chooses a prompt via `_choose_prompt()`, normalizes ground truth, and returns `TaskItem` objects.
5. `run_eval.make_provider()` creates a provider adapter from `OpenAIProvider`, `AnthropicProvider`, `GeminiProvider`, or `FireworksProvider`.
6. For each `TaskItem`, `run_eval.build_json_schema()` creates the expected JSON output schema and provider `infer()` sends images and prompt content to the API.
7. `run_eval.extract_json()` parses model output and `run_eval.evaluate_pass1()` compares the parsed response against `TaskItem.gt`.
8. `run_eval.run_eval()` aggregates pass@1, latency, tokens, and cost, then writes `results/exp*/<provider>/<model>/results.csv`, token logs, token summaries, and optional error reports.

**Until-Correct Experiment (Exp3):**

1. `run_single_experiment.run_experiment_3()` delegates to `run_eval.run_until_type_correct()`.
2. `run_eval.run_until_type_correct()` builds a candidate pool per task type using `build_tasks()`.
3. The loop randomly samples tasks, appends an optional cache-busting nonce to the prompt, calls provider `infer()`, and evaluates with `evaluate_pass1()`.
4. The loop stops per type on first success or after `max_attempt_per_type`.
5. Summary rows are written to `results/exp3/<provider>/<model>/results.csv`; token summaries use the same provider/model output convention.

**Few-Shot Flow:**

1. `prepare_few_shot_examples.py` samples examples from `captcha_data/` and writes `few_shot_examples.yaml`.
2. `few_shot_answers.py` supplies hard-coded answer payloads through `get_all_examples()` for examples listed in `few_shot_examples.yaml`.
3. `compress_few_shot_assets.py` reads `few_shot_image_manifest.json`, compresses images in `few_shot_assets/`, and writes `few_shot_image_compression_report.json`.
4. `run_eval.run_eval()` enables few-shot mode through `few_shot_config`, excludes selected examples from evaluation pools, and passes `build_few_shot_content()` output into provider `infer()`.

**Visualization Flow:**

1. `visualize_results.CAPTCHAVisualizer` recursively scans `results/**/results.csv`.
2. `_load_all_data()` normalizes standard Exp1/Exp2/Exp4 outputs and special Exp3 `kind=summary` rows into a shared dataframe.
3. Chart methods such as `plot_heatmap()`, `plot_comparison_bars()`, and `plot_cost_performance_frontier()` write PDFs to `figures/`.
4. `exp2_to_exp3_predict.py` imports `CAPTCHAVisualizer`, reads Exp2 and optional Exp3 rows, and writes `exp2_to_exp3_predictions.csv`.

**State Management:**
- Use `TaskItem` instances in `run_eval.py` as the in-memory task state passed through prompt, image, schema, inference, and scoring steps.
- Use the module-level `IMG_CACHE` in `run_eval.py` for LRU caching of raw image bytes and base64 strings.
- Use `random.seed(seed)` in `run_eval.run_eval()` for reproducible sampling when `max_per_type` triggers random selection.
- Persist durable state to `results/`, `error_analysis/`, `figures/`, `few_shot_examples.yaml`, and `few_shot_image_manifest.json`.

## Key Abstractions

**TaskItem:**
- Purpose: Represents one CAPTCHA evaluation item after data normalization.
- Examples: `run_eval.py`
- Pattern: `@dataclass` with `type`, `puzzle_id`, `prompt`, `images`, and `gt`.

**ModelProvider:**
- Purpose: Defines the common provider contract for multimodal inference.
- Examples: `run_eval.py`
- Pattern: Abstract base class with provider-specific subclasses that return `(raw, parsed, meta)`.

**ImageCache:**
- Purpose: Avoid repeated disk reads and base64 encodes for images passed to providers.
- Examples: `run_eval.py`
- Pattern: Small in-process LRU cache keyed by image path.

**Task Schema Builders:**
- Purpose: Encode expected answer shape for each CAPTCHA type.
- Examples: `run_eval.build_json_schema()` in `run_eval.py`
- Pattern: Task-type switch returning JSON Schema dictionaries, optionally augmented with a `reasoning` string.

**Task Scorers:**
- Purpose: Convert parsed provider output into pass/fail metrics against normalized ground truth.
- Examples: `run_eval.evaluate_pass1()` in `run_eval.py`
- Pattern: Task-type switch with specialized comparisons for numeric, classification, multi-select, point, ordered-point, swap, rotation, and safe-click tasks.

**Prompt Resolver:**
- Purpose: Merge per-item ground truth prompts, optimized prompt rules, templates, prefixes, suffixes, and task-specific defaults.
- Examples: `_load_prompts_yaml()`, `_resolve_prompt_cfg()`, `_choose_prompt()`, and `_render_template()` in `run_eval.py`
- Pattern: Config-first prompt selection with `gt`, `opt`, and `auto` modes.

**Error Collector:**
- Purpose: Persist failed cases and token summaries outside the main results CSV.
- Examples: `experiments_helper.ErrorCase` and `experiments_helper.SimpleErrorCollector`
- Pattern: Dataclass records plus CSV/JSON summary writers.

**Visualizer:**
- Purpose: Normalize result files and generate publication-ready charts.
- Examples: `visualize_results.CAPTCHAVisualizer`
- Pattern: Stateful analysis class with loaded dataframe, display-name maps, task family metadata, and plotting methods.

## Entry Points

**Primary Experiment CLI:**
- Location: `run_single_experiment.py`
- Triggers: `python run_single_experiment.py <experiment> [options]`
- Responsibilities: Select experiment 1, 2, 3, or 4; build wrapper arguments; route to `run_eval.py`.

**Core Evaluation CLI:**
- Location: `run_eval.py`
- Triggers: `python run_eval.py --dataset-root ./captcha_data --types ...`
- Responsibilities: Run direct single-pass evaluation or until-correct mode through `main()`.
- Note: Keep import-time use of `run_eval.py` guarded carefully because the file contains module-level diagnostic and experimental code outside function bodies.

**Few-Shot Manifest Generator:**
- Location: `prepare_few_shot_examples.py`
- Triggers: `python prepare_few_shot_examples.py --dataset ./captcha_data --n-shot 2 --output ./few_shot_examples.yaml`
- Responsibilities: Read task ground truth and write a few-shot example YAML manifest.

**Few-Shot Asset Compressor:**
- Location: `compress_few_shot_assets.py`
- Triggers: `python compress_few_shot_assets.py`
- Responsibilities: Read `few_shot_image_manifest.json`, run lossless PNG/JPEG optimization, and emit a compression report.

**Visualization Script:**
- Location: `visualize_results.py`
- Triggers: `python visualize_results.py`
- Responsibilities: Load `results/`, generate all supported charts, and write PDFs under `figures/`.

**Exp2-to-Exp3 Predictor:**
- Location: `exp2_to_exp3_predict.py`
- Triggers: `python exp2_to_exp3_predict.py --results-dir ./results --output ./exp2_to_exp3_predictions.csv`
- Responsibilities: Map Exp2 pass@1 into Exp3 expected success and attempts, with optional finite-pool and calibration options.

**Notebook Entrypoints:**
- Location: `test.ipynb`, `plot.ipynb`, and `test_statistic.ipynb`
- Triggers: Jupyter execution.
- Responsibilities: Interactive experiment running, plotting, and statistical validation.

## Error Handling

**Strategy:** Print-and-continue for data issues, provider-level error capture for API failures, and structured failure recording when error analysis is enabled.

**Patterns:**
- Use skip messages in `run_eval.build_tasks()` for malformed or missing data such as missing image files or invalid `ground_truth.json` fields.
- Use `__ERROR__: <type>: <message>` strings from provider `infer()` methods in `run_eval.py` instead of propagating most provider exceptions through the evaluation loop.
- Use `extract_json()` in `run_eval.py` as a lenient parser that strips code fences and falls back to outer-brace extraction.
- Use `evaluate_pass1()` in `run_eval.py` as the main correctness gate; exceptions inside scoring return `False`.
- Use `SimpleErrorCollector.save_summary()` in `experiments_helper.py` to write `errors.csv`, `stats.json`, and `token_summary.json`.
- Use `visualize_results.CAPTCHAVisualizer._load_all_data()` to skip unreadable result files while continuing to load the rest of `results/`.

## Cross-Cutting Concerns

**Logging:** Uses `print()` and `tqdm` progress output in `run_eval.py`, `run_single_experiment.py`, `experiments_helper.py`, `visualize_results.py`, `prepare_few_shot_examples.py`, and `compress_few_shot_assets.py`.

**Validation:** Uses task-specific validation in `run_eval.build_tasks()`, response schemas from `run_eval.build_json_schema()`, and answer checks in `run_eval.evaluate_pass1()`.

**Authentication:** Uses provider credentials from `secrets.yaml`; do not document, print, or commit values from this file.

**Image Handling:** Uses raw bytes and base64 from `run_eval.ImageCache`; provider adapters format the same images differently for OpenAI, Anthropic, Gemini, and Fireworks.

**Serialization:** Uses CSV for experiment summaries and token logs in `results/`, JSON for token/error summaries, YAML for prompts and few-shot examples, and PDF for figures.

**Path Conventions:** Uses relative paths rooted at the project directory, including `./captcha_data`, `./results`, `./error_analysis`, `./figures`, `./prompts_optimized.yaml`, and `./few_shot_examples.yaml`.

---

*Architecture analysis: 2026-05-15*
