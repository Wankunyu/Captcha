# Coding Conventions

**Analysis Date:** 2026-05-15

## Naming Patterns

**Files:**
- Use top-level `snake_case.py` scripts for importable tools and CLIs, as in `run_eval.py`, `run_single_experiment.py`, `experiments_helper.py`, `visualize_results.py`, `compress_few_shot_assets.py`, `exp2_to_exp3_predict.py`, and `prepare_few_shot_examples.py`.
- Use descriptive notebook names for manual analysis workflows, as in `test.ipynb`, `test_statistic.ipynb`, and `plot.ipynb`.
- Use task-type directory names with capitalized words separated by underscores, matching dataset keys and result rows: `captcha_data/Dice_Count`, `captcha_data/Patch_Select`, `captcha_data/Image_Recognition`, `few_shot_assets/Click_Order`.
- Use generated-output paths grouped by experiment/provider/model: `results/exp2/openai/gpt-5.1_medium/results.csv`, `error_analysis/exp4/openai/gpt-5/exp4_fewshot/errors.csv`.

**Functions:**
- Use `snake_case` for functions: `load_secrets`, `load_prompts`, `build_tasks`, `evaluate_pass1`, `run_eval`, `quick_visualize`, `compress_images`.
- Prefix private helpers with `_`: `_list_images_in_dir`, `_maybe_parse_json`, `_choose_prompt`, `_normalize_points`, `_collect_error_analysis`, `_normalize_multi`.
- Use experiment entry-point names with numeric suffixes for the four experiment families: `run_experiment_1`, `run_experiment_2`, `run_experiment_3`, `run_experiment_4` in `run_single_experiment.py`.
- Keep mathematical helpers compact and lowercase when they mirror formula notation: `g_q`, `g2_q`, `_logit` in `exp2_to_exp3_predict.py`.

**Variables:**
- Use `lower_snake_case` for local variables and parameters: `dataset_root`, `max_per_type`, `token_output_dir`, `few_shot_config`, `provider_model`.
- Use short names only inside tight mathematical or coordinate scopes: `p`, `k`, `n`, `x`, `y`, `gt`, `df` in `exp2_to_exp3_predict.py`, `run_eval.py`, and `visualize_results.py`.
- Use uppercase constants for shared task/model/static settings: `IMG_EXTS`, `IMAGE_EXTENSIONS`, `SUPPORTED_TYPES`, `TYPE_REQUIRE_PER_ITEM`, `DEFAULT_MODEL_NAMES`, `TASK_FAMILY`, `HARD_TASKS`, `PNG_EXTS`, `JPEG_EXTS`.
- Preserve provider/model identifiers as strings and sanitize path segments with `model.replace("/", "_")`, matching `run_single_experiment.py` and `test.ipynb`.

**Types:**
- Use `PascalCase` for classes and dataclasses: `ImageCache`, `ModelProvider`, `OpenAIProvider`, `AnthropicProvider`, `GeminiProvider`, `FireworksProvider`, `TaskItem`, `ErrorCase`, `SimpleErrorCollector`, `CAPTCHAVisualizer`, `CompressionResult`.
- Use `@dataclass` for simple data carriers with typed fields: `TaskItem` in `run_eval.py`, `ErrorCase` in `experiments_helper.py`, and `CompressionResult` in `compress_few_shot_assets.py`.
- Use standard typing imports where they already exist: `Dict`, `Any`, `List`, `Tuple`, `Optional` in `run_eval.py` and `experiments_helper.py`; built-in generics and unions also appear in `exp2_to_exp3_predict.py`.

## Code Style

**Formatting:**
- Tooling: Not detected. There is no `pyproject.toml`, `setup.cfg`, `tox.ini`, `ruff.toml`, `.flake8`, `pytest.ini`, or formatter config in the project root.
- Use Python 3.10+ compatible syntax. The README lists Python 3.10+, notebooks record Python 3.10.13, and source uses annotations such as `str | None` in `run_eval.py` and `exp2_to_exp3_predict.py`.
- Prefer the cleaner four-space, type-annotated style in `compress_few_shot_assets.py`, `exp2_to_exp3_predict.py`, and `experiments_helper.py` for new code.
- Keep long CLI argument lists vertically aligned as in `run_single_experiment.py` and `exp2_to_exp3_predict.py`.
- Avoid expanding the notebook-derived formatting style in `run_eval.py`; it contains large blank gaps, mixed spacing, top-level debug cells, and broad inline snippets.

**Linting:**
- Tooling: Not detected.
- No lint rules are enforced by repository config.
- Keep imports and unused code clean manually. Several modules use optional imports guarded by `try`/`except`, such as `adjustText` in `visualize_results.py` and `experiments_helper` in `run_eval.py`.

## Import Organization

**Order:**
1. Shebang, encoding marker, and module docstring when the file is a CLI or standalone script: `run_single_experiment.py`, `compress_few_shot_assets.py`, `exp2_to_exp3_predict.py`, `prepare_few_shot_examples.py`.
2. `from __future__ import annotations` when used: `compress_few_shot_assets.py`, `exp2_to_exp3_predict.py`.
3. Standard library imports: `argparse`, `json`, `os`, `pathlib`, `subprocess`, `tempfile`, `dataclasses`, `typing`.
4. Third-party imports: `yaml`, `tqdm`, `openai`, `anthropic`, `google.genai`, `PIL.Image`, `numpy`, `pandas`, `matplotlib`, `seaborn`.
5. Local imports: `from run_eval import ...`, `from visualize_results import CAPTCHAVisualizer`, `from few_shot_answers import get_all_examples`, `from experiments_helper import SimpleErrorCollector`.

**Path Aliases:**
- No package path aliases are configured.
- Imports assume the repository root is the working directory.
- `run_single_experiment.py` inserts its own directory into `sys.path` before importing `run_eval.py`.
- Notebooks import top-level modules directly: `from run_single_experiment import ...` in `test.ipynb`, `from exp2_to_exp3_predict import ...` in `test_statistic.ipynb`.

## Error Handling

**Patterns:**
- Raise explicit exceptions for missing required files and invalid arguments: `load_secrets`, `load_prompts`, `load_ground_truth`, `load_manifest`, and `ensure_dimensions`.
- Return `None` or empty containers for optional parsing/config failures where callers can continue: `_maybe_parse_json`, `extract_json`, `load_few_shot_examples`, `_collect_image_paths`.
- Skip bad dataset items with console prefixes rather than aborting the full experiment: `build_tasks` prints `[SKIP]` messages in `run_eval.py`.
- Convert malformed CLI JSON into process termination with a clear message: `raise SystemExit(...)` in `run_eval.py` and `exp2_to_exp3_predict.py`.
- Keep provider initialization failures explicit and provider-specific: `OpenAIProvider`, `AnthropicProvider`, `GeminiProvider`, and `FireworksProvider` raise runtime errors when required credentials are absent.
- Broad `except Exception` is common in legacy and exploratory paths. Use it only around optional dependencies, data best-effort loading, provider calls, or per-task loops where one failure must not stop an entire run.

## Logging

**Framework:** console output with `print`; no `logging` configuration is present.

**Patterns:**
- Use bracketed status prefixes for machine-readable progress: `[INFO]`, `[WARNING]`, `[WARN]`, `[ERROR]`, `[SKIP]`, `[LOADED]`, `[SAVED]`, `[DONE]`, `[SUMMARY]`.
- Use progress bars through `tqdm` in `run_eval.py` when iterating evaluation tasks.
- Use human-readable section dividers in CLI wrappers, as in `run_single_experiment.py` and `experiments_helper.py`.
- Use `warnings.filterwarnings("ignore")` only in visualization code where noisy plotting/library warnings are intentionally suppressed: `visualize_results.py`.
- Do not print secret file contents. `secrets.yaml` exists and is referenced by `run_eval.py`, `run_single_experiment.py`, and `README.md`, but its values are not part of the codebase map.

## Comments

**When to Comment:**
- Use module docstrings to explain standalone script purpose and workflow: `compress_few_shot_assets.py`, `exp2_to_exp3_predict.py`, `experiments_helper.py`.
- Use function docstrings for public helpers, CLI entry points, provider abstractions, and non-obvious evaluation formulas.
- Use short inline comments for schema differences, experiment-specific result normalization, and chart-generation blocks, as in `visualize_results.py`.
- Keep comments tied to behavior. Notebook-style banners and scratch comments are common in `plot.ipynb` and `run_eval.py`, but new importable code should stay compact.

**JSDoc/TSDoc:**
- Not applicable. This repository is Python-only for source code.
- Python docstrings are the active documentation style.

## Function Design

**Size:** Keep new helpers small and single-purpose. Existing focused examples include `compress_png`, `compress_jpeg`, `load_manifest`, `predict_q_from_exp2`, and `apply_calibration`. `run_eval.py` contains large orchestration functions and should be extended through helpers where practical.

**Parameters:** Public functions use keyword-friendly defaults for paths, providers, models, and experiment options. Follow patterns in `run_experiment_1`, `run_experiment_2`, `run_eval`, `quick_visualize`, and `extract_few_shot_examples`.

**Return Values:** Return structured values rather than printing only. Examples include dictionaries from `run_eval`, lists of `CompressionResult` from `compress_images`, `pandas.DataFrame` objects inside `CAPTCHAVisualizer`, and config dictionaries from `load_few_shot_examples`.

## Module Design

**Exports:** There are no `__all__` declarations or barrel modules. Import concrete functions/classes directly from their files: `run_eval.py`, `run_single_experiment.py`, `visualize_results.py`, `exp2_to_exp3_predict.py`, `experiments_helper.py`.

**Barrel Files:** Not used.

**CLI Guards:** Use `if __name__ == "__main__":` for executable scripts. This pattern is present in `run_single_experiment.py`, `visualize_results.py`, `compress_few_shot_assets.py`, `exp2_to_exp3_predict.py`, `prepare_few_shot_examples.py`, and `experiments_helper.py`.

**Side Effects:** Importable modules should keep side effects behind functions or CLI guards. `run_eval.py` currently contains top-level environment/debug code and embedded scratch/demo calls, so avoid using that pattern for new code.

---

*Convention analysis: 2026-05-15*
