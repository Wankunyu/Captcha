# Codebase Structure

**Analysis Date:** 2026-05-15

## Directory Layout

```text
captcha/
|-- run_eval.py                    # Core evaluation engine, provider adapters, schemas, scoring, and direct CLI
|-- run_single_experiment.py       # Primary experiment wrapper CLI for Exp1, Exp2, Exp3, and Exp4
|-- experiments_helper.py          # Error collection, stats summaries, and legacy task loading helper
|-- visualize_results.py           # Result loader and PDF chart generation
|-- exp2_to_exp3_predict.py        # Exp2 pass@1 to Exp3 prediction utility
|-- phase3_artifacts.py            # Phase 3 strict artifact schemas and CSV/JSON writers
|-- dataset_scope_audit.py         # Phase 3 offline dataset scope audit CLI
|-- extended_dataset_manifest.py   # Phase 3 extended-data manifest and validation-slice CLI
|-- retry_calibration.py           # Phase 3 Bernoulli retry calibration CLI
|-- failure_taxonomy.py            # Phase 3 scientific/protocol/infrastructure failure taxonomy CLI
|-- prepare_few_shot_examples.py   # Few-shot YAML generation from dataset metadata
|-- compress_few_shot_assets.py    # Few-shot image compression utility
|-- few_shot_answers.py            # Hard-coded few-shot answer lookup table
|-- prompts_optimized.yaml         # Optimized prompt rules keyed by CAPTCHA task type
|-- few_shot_examples.yaml         # Few-shot sample manifest keyed by CAPTCHA task type
|-- few_shot_image_manifest.json   # Few-shot image manifest consumed by compression tooling
|-- secrets.yaml                   # Provider credentials and pricing config; values must not be copied into docs
|-- README.md                      # Project overview, usage, and output conventions
|-- captcha_data/                  # Raw CAPTCHA datasets and ground_truth.json metadata
|-- few_shot_assets/               # Compressed few-shot example image assets
|-- results/                       # Experiment CSVs, token logs, and token summaries
|-- error_analysis/                # Error reports and failure diagnostics
|-- figures/                       # Generated PDF visualizations
|-- tests/                         # Focused offline pytest regression tests
|-- plot.ipynb                     # Interactive visualization notebook
|-- test_statistic.ipynb           # Statistical analysis notebook
|-- test.ipynb                     # Interactive experiment notebook
|-- ignore_me.ipynb                # Ignored notebook workspace file
|-- .planning/codebase/            # GSD codebase maps
|-- .gitattributes                 # Git LFS tracking for captcha_data/**
|-- .gitignore                     # Ignore rules for caches, notebooks, logs, and local envs
|-- __pycache__/                   # Generated Python bytecode cache
`-- .ipynb_checkpoints/            # Generated notebook checkpoints
```

## Directory Purposes

**Root Python Modules:**
- Purpose: Hold all executable and importable Python code in a flat root-level script layout.
- Contains: `run_eval.py`, `run_single_experiment.py`, `experiments_helper.py`, `visualize_results.py`, `exp2_to_exp3_predict.py`, `phase3_artifacts.py`, `dataset_scope_audit.py`, `extended_dataset_manifest.py`, `retry_calibration.py`, `failure_taxonomy.py`, `prepare_few_shot_examples.py`, `compress_few_shot_assets.py`, and `few_shot_answers.py`.
- Key files: `run_eval.py` for core behavior, `run_single_experiment.py` for the primary CLI, and `visualize_results.py` for chart generation.

**`captcha_data/`:**
- Purpose: Store raw evaluation datasets grouped by CAPTCHA task type.
- Contains: directories such as `captcha_data/Dice_Count/`, `captcha_data/Click_Order/`, `captcha_data/Image_Recognition/`, `captcha_data/Path_Finder/`, and `captcha_data/Rotation_Match/`.
- Key files: each active task directory uses `captcha_data/<TaskType>/ground_truth.json`; `.gitattributes` tracks `captcha_data/**` with Git LFS.

**`few_shot_assets/`:**
- Purpose: Store few-shot example image assets referenced during Exp4.
- Contains: directories parallel to task types, such as `few_shot_assets/Dice_Count/`, `few_shot_assets/Image_Recognition/`, and `few_shot_assets/Patch_Select/`.
- Key files: asset paths are indexed in `few_shot_image_manifest.json` and referenced by `run_eval.build_few_shot_content()`.

**`results/`:**
- Purpose: Store experiment outputs in a structured results tree.
- Contains: `results/exp1/`, `results/exp2/`, `results/exp3/`, `results/exp4/`, and `results/error_analysis/`.
- Key files: `results/exp1/openai/gpt-5/results.csv`, `results/exp2/gemini/gemini-2.5-pro/results.csv`, `results/exp3/openai/gpt-5/results.csv`, and provider/model token summaries.

**`error_analysis/`:**
- Purpose: Store detailed failed-prediction analysis for runs that enable error collection.
- Contains: nested experiment/provider/model directories such as `error_analysis/exp4/openai/gpt-5/exp4_fewshot/`.
- Key files: `error_analysis/exp4/openai/gpt-5/exp4_fewshot/errors.csv`, `error_analysis/exp4/openai/gpt-5/exp4_fewshot/stats.json`, and `error_analysis/exp4/openai/gpt-5/exp4_fewshot/token_summary.json`.

**`figures/`:**
- Purpose: Store generated publication charts.
- Contains: PDF outputs such as `figures/heatmap_exp1.pdf`, `figures/heatmap_exp2.pdf`, and `figures/comparison_bars_openai_gpt-5.pdf`.
- Key files: generated by `visualize_results.py` and notebook workflows in `plot.ipynb`.

**`.planning/codebase/`:**
- Purpose: Store GSD codebase mapping documents.
- Contains: `ARCHITECTURE.md`, `STRUCTURE.md`, and other mapper-owned docs.
- Key files: `.planning/codebase/ARCHITECTURE.md` and `.planning/codebase/STRUCTURE.md`.

**Generated/Local Cache Directories:**
- Purpose: Hold interpreter and notebook generated state.
- Contains: `__pycache__/` and `.ipynb_checkpoints/`.
- Key files: generated `.pyc` files under `__pycache__/`; do not add source logic here.

## Key File Locations

**Entry Points:**
- `run_single_experiment.py`: Use this as the primary CLI and import surface for experiments 1 through 4.
- `run_eval.py`: Use this for lower-level direct evaluation, provider adapter changes, task construction, schemas, and scoring.
- `visualize_results.py`: Use this for batch chart generation and results loading.
- `prepare_few_shot_examples.py`: Use this to regenerate `few_shot_examples.yaml`.
- `compress_few_shot_assets.py`: Use this to optimize images listed in `few_shot_image_manifest.json`.
- `exp2_to_exp3_predict.py`: Use this to generate Exp2-to-Exp3 prediction CSVs.
- `dataset_scope_audit.py`: Use this to generate Phase 3 dataset scope CSV/JSON rows under `results/revision/<run_id>/`.
- `extended_dataset_manifest.py`: Use this to validate extended-data manifests, write validation-slice task CSVs, optional comparison CSV/JSON files, and dataset contribution notes.
- `retry_calibration.py`: Use this to compare Exp2 Bernoulli Success@k predictions with fixed-retry and adaptive-compatible outcomes by task type and family.
- `failure_taxonomy.py`: Use this to separate scientific model failures from protocol, infrastructure, and aggregate-only evidence for paper-safe claims.
- `phase3_artifacts.py`: Use this for strict Phase 3 row schemas and shared CSV/JSON writers.

**Configuration:**
- `secrets.yaml`: Provider API credentials and pricing configuration; note existence only and do not copy values.
- `prompts_optimized.yaml`: Optimized prompt rules for task types consumed by `run_eval._load_prompts_yaml()`.
- `few_shot_examples.yaml`: Few-shot example list consumed by `run_eval.load_few_shot_examples()`.
- `few_shot_image_manifest.json`: Asset manifest consumed by `compress_few_shot_assets.py`.
- `.gitattributes`: Git LFS rule for `captcha_data/**`.
- `.gitignore`: Ignore rules for cache directories, local environments, logs, checkpoints, and local notebooks.

**Core Logic:**
- `run_eval.py`: Provider adapters, data loading, task building, prompt resolution, JSON schema building, answer scoring, run aggregation, token accounting, and direct CLI.
- `run_single_experiment.py`: Experiment-specific wrappers and CLI branching.
- `experiments_helper.py`: Error case dataclass, error collector, comparison printer, and legacy ground-truth loader.
- `few_shot_answers.py`: Hard-coded answer table for few-shot examples.

**Analysis and Visualization:**
- `visualize_results.py`: `CAPTCHAVisualizer`, result normalization, task family metadata, and chart methods.
- `exp2_to_exp3_predict.py`: Truncated-geometric and finite-pool prediction helpers.
- `plot.ipynb`: Interactive plotting workflow.
- `test_statistic.ipynb`: Statistical validation workflow.

**Data:**
- `captcha_data/<TaskType>/ground_truth.json`: Metadata source for `run_eval.build_tasks()`.
- `captcha_data/<TaskType>/*.{png,jpg,jpeg,JPG}`: Raw CAPTCHA image assets used by tasks.
- `few_shot_assets/<TaskType>/`: Few-shot images used by Exp4.

**Outputs:**
- `results/exp*/<provider>/<model>/results.csv`: Aggregated experiment results.
- `results/exp*/<provider>/<model>/*_tokens.csv`: Per-question or per-attempt token logs.
- `results/exp*/<provider>/<model>/*_token_summary.json`: Aggregated token and cost summaries.
- `error_analysis/exp*/<provider>/<model>/<variant>/errors.csv`: Failed examples with parsed output and error descriptions.
- `figures/*.pdf`: Publication-ready visualizations.

**Testing:**
- Focused offline pytest tests live under `tests/`.
- Revision-critical schema, preflight, adaptive, Phase 3 dataset-scope, and manifest contracts are validated with `uv run pytest`.

## Naming Conventions

**Files:**
- Use `snake_case.py` for Python modules: `run_eval.py`, `run_single_experiment.py`, `experiments_helper.py`, and `visualize_results.py`.
- Use descriptive YAML/JSON filenames for configuration and manifests: `prompts_optimized.yaml`, `few_shot_examples.yaml`, and `few_shot_image_manifest.json`.
- Use notebook filenames for interactive work: `plot.ipynb`, `test_statistic.ipynb`, and `test.ipynb`.

**Directories:**
- Use task-type directory names with underscores and leading capitals under `captcha_data/` and `few_shot_assets/`: `captcha_data/Dice_Count/`, `captcha_data/Patch_Select/`, and `few_shot_assets/Rotation_Match/`.
- Treat task names as API identifiers; keep names aligned among `captcha_data/<TaskType>/`, `run_eval.SUPPORTED_TYPES`, `prompts_optimized.yaml`, `few_shot_examples.yaml`, and `visualize_results.CAPTCHAVisualizer.TASK_FAMILY`.
- Use `results/expN/<provider>/<model>/` for experiment outputs: `results/exp2/openai/gpt-5.1_medium/`.
- Use `error_analysis/expN/<provider>/<model>/<variant>/` for detailed failure exports: `error_analysis/exp4/openai/gpt-5/exp4_fewshot/`.

**Functions:**
- Use `snake_case` functions throughout root modules: `build_tasks()`, `evaluate_pass1()`, `run_experiment_1()`, `quick_visualize()`, and `extract_few_shot_examples()`.
- Use leading underscores for internal helpers: `_choose_prompt()`, `_load_prompts_yaml()`, `_normalize_points()`, `_collect_image_paths()`, and `_get_accuracy_pivot()`.

**Classes and Dataclasses:**
- Use `PascalCase` for classes: `TaskItem`, `ImageCache`, `ModelProvider`, `OpenAIProvider`, `SimpleErrorCollector`, and `CAPTCHAVisualizer`.
- Use dataclasses for lightweight records: `TaskItem` in `run_eval.py`, `ErrorCase` in `experiments_helper.py`, and `CompressionResult` in `compress_few_shot_assets.py`.

**Result Files:**
- Use `results.csv` as the standard per-provider/model aggregate output filename.
- Use experiment-prefixed token logs: `exp1_gt_openai_gpt-5_tokens.csv`, `exp2_opt_openai_gpt-5_tokens.csv`, and `exp4_fewshot_openai_gpt-5_tokens.csv`.
- Use matching token summary names ending in `_token_summary.json`.

## Where to Add New Code

**New Provider:**
- Primary code: add a `ModelProvider` subclass in `run_eval.py`.
- Factory wiring: add provider selection to `run_eval.make_provider()`.
- Configuration: add provider config keys to `secrets.yaml` without documenting values.
- Output path: results should continue using `results/exp*/<provider>/<model>/`.

**New CAPTCHA Task Type:**
- Data: add `captcha_data/<TaskType>/ground_truth.json` and image assets under `captcha_data/<TaskType>/`.
- Supported type list: add the task name to `SUPPORTED_TYPES` in `run_eval.py`.
- Task construction: add a branch in `run_eval.build_tasks()` that resolves images, prompt defaults, and normalized ground truth.
- Schema: add expected response shape to `run_eval.build_json_schema()`.
- Scoring: add correctness logic to `run_eval.evaluate_pass1()`.
- Prompts: add task rules to `prompts_optimized.yaml`.
- Few-shot: add optional entries to `few_shot_examples.yaml`, `few_shot_answers.py`, and `few_shot_assets/<TaskType>/`.
- Visualization: add task family metadata to `visualize_results.CAPTCHAVisualizer.TASK_FAMILY`.

**New Experiment Wrapper:**
- Primary code: add a `run_experiment_N()` wrapper in `run_single_experiment.py`.
- CLI wiring: add argument handling and dispatch in `run_single_experiment.main()`.
- Core behavior: reuse `run_eval.run_eval()` or `run_eval.run_until_type_correct()` unless the experiment needs a new core loop in `run_eval.py`.
- Output path: use `results/expN/<provider>/<model>/` for consistency with `visualize_results.CAPTCHAVisualizer._load_all_data()`.

**New Result Visualization:**
- Primary code: add a method on `CAPTCHAVisualizer` in `visualize_results.py`.
- Batch generation: call the new method from `CAPTCHAVisualizer.plot_all()` when it belongs in full chart generation.
- Output path: write PDFs to `figures/` or a caller-provided output directory.

**New Statistical Utility:**
- Primary code: add a root-level script only if it is a standalone workflow like `exp2_to_exp3_predict.py`.
- Shared loading: prefer `visualize_results.CAPTCHAVisualizer` to read `results/` rather than duplicating recursive CSV loading.

**New Few-Shot Asset Workflow:**
- Manifest generation: use or extend `prepare_few_shot_examples.py`.
- Answer data: keep few-shot answer payloads in `few_shot_answers.py` when asset filenames drift from raw dataset filenames.
- Compression: keep lossless optimization behavior in `compress_few_shot_assets.py`.

**Utilities:**
- Shared evaluation utilities belong in `run_eval.py` when they are tied to task construction, provider calls, schemas, or scoring.
- Error-reporting utilities belong in `experiments_helper.py`.
- Plotting helpers belong in `visualize_results.py`.

## Special Directories

**`captcha_data/`:**
- Purpose: Raw CAPTCHA dataset and ground truth.
- Generated: No
- Committed: Yes, with Git LFS via `.gitattributes`.

**`few_shot_assets/`:**
- Purpose: Compressed few-shot example images.
- Generated: Partly, through asset preparation and compression workflows.
- Committed: Yes

**`results/`:**
- Purpose: Experiment results, token logs, and token summaries.
- Generated: Yes
- Committed: Present in the repository tree.

**`error_analysis/`:**
- Purpose: Failure analysis exports.
- Generated: Yes
- Committed: Present in the repository tree.

**`figures/`:**
- Purpose: Generated PDF charts.
- Generated: Yes
- Committed: Present in the repository tree.

**`__pycache__/`:**
- Purpose: Python bytecode cache.
- Generated: Yes
- Committed: No target for source edits.

**`.ipynb_checkpoints/`:**
- Purpose: Jupyter checkpoint state.
- Generated: Yes
- Committed: No target for source edits.

**`.planning/codebase/`:**
- Purpose: GSD architecture, structure, quality, stack, integration, and concern docs.
- Generated: Yes
- Committed: Managed by GSD workflow.

---

*Structure analysis: 2026-05-15*
