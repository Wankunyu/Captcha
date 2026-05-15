# Testing Patterns

**Analysis Date:** 2026-05-15

## Test Framework

**Runner:**
- Automated runner: Not detected.
- There is no `pytest`, `unittest`, `nose`, `tox`, `nox`, or coverage configuration in the project root.
- Manual and notebook-driven workflows are the active validation pattern: `test.ipynb`, `test_statistic.ipynb`, `plot.ipynb`, `run_single_experiment.py`, and `exp2_to_exp3_predict.py`.

**Assertion Library:**
- Not detected for automated tests.
- The only source-level `assert` found is a top-level configuration check in `run_eval.py`; most validation uses explicit `raise FileNotFoundError`, `raise RuntimeError`, `raise ValueError`, or `raise SystemExit`.

**Run Commands:**
```bash
python run_single_experiment.py --help
python run_single_experiment.py 1 --types Dice_Count --max-per-type 2
python exp2_to_exp3_predict.py --results-dir ./results --output ./exp2_to_exp3_predictions.csv
python compress_few_shot_assets.py
```

## Test File Organization

**Location:**
- Automated test files are not present.
- Manual experiment smoke workflows live at repository root in `test.ipynb`.
- Statistical validation workflows live at repository root in `test_statistic.ipynb`.
- Visualization validation workflows live at repository root in `plot.ipynb`.
- Result fixtures and outputs live under `results/`, `error_analysis/`, and `figures/`.

**Naming:**
- Notebook names beginning with `test` are analysis notebooks, not automated test modules: `test.ipynb`, `test_statistic.ipynb`.
- Python source files are executable modules rather than test modules: `run_eval.py`, `run_single_experiment.py`, `visualize_results.py`, `compress_few_shot_assets.py`, `exp2_to_exp3_predict.py`.
- No `test_*.py`, `*_test.py`, `*.spec.py`, or `tests/` directory is present.

**Structure:**
```text
captcha/
├── test.ipynb                  # Manual experiment runner cells
├── test_statistic.ipynb        # Exp2 -> Exp3 prediction validation notebook
├── plot.ipynb                  # Manual chart-generation notebook
├── run_single_experiment.py    # CLI smoke entry point for experiments 1-4
├── exp2_to_exp3_predict.py     # CLI for prediction output validation
├── captcha_data/               # Dataset fixtures with ground_truth.json per task type
├── results/                    # Generated CSV/token summaries used by analysis
├── error_analysis/             # Generated error CSV/JSON summaries
└── figures/                    # Generated PDF chart outputs
```

## Test Structure

**Suite Organization:**
```python
from run_single_experiment import (
    run_experiment_1,
    run_experiment_2,
    run_experiment_3,
    run_experiment_4,
)

provider = "openai"
model = "gpt-5.1"
reasoning_effort = "medium"
storage_model = f"{model}_{reasoning_effort}"
thinking_opts = {"effort": reasoning_effort}

result = run_experiment_2(
    types=["Patch_Select"],
    prompts_file="./prompts_optimized.yaml",
    max_per_type=20,
    provider=provider,
    model=model,
    out_csv=exp_out_csv("exp2", provider, storage_model),
    collect_tokens=True,
    token_output_dir=exp_results_dir("exp2", provider, storage_model),
    timeout_sec=600,
)
```

**Patterns:**
- Configure provider/model/reasoning options at the top of the notebook or CLI invocation.
- Build output paths through helper functions such as `exp_results_dir`, `exp_out_csv`, and `exp_error_dir` in `test.ipynb`.
- Use small task subsets for manual smoke checks, such as `--types Dice_Count --max-per-type 2` from `run_single_experiment.py`.
- Persist results as CSV/JSON and inspect generated summaries instead of asserting in process.
- Use `CAPTCHAVisualizer` in `visualize_results.py` to load and normalize generated result trees before charting.

## Mocking

**Framework:** Not detected.

**Patterns:**
```python
class ModelProvider:
    def infer(self, prompt, images, json_schema, stream=True):
        raise NotImplementedError
```

**What to Mock:**
- Provider boundaries exposed through `ModelProvider.infer` in `run_eval.py`.
- File-system inputs such as `captcha_data/<Task>/ground_truth.json`, `few_shot_examples.yaml`, and `few_shot_image_manifest.json`.
- CSV/JSON result files consumed by `CAPTCHAVisualizer` and `exp2_to_exp3_predict.py`.

**What NOT to Mock:**
- Pure evaluators and math helpers can run directly with in-memory data: `evaluate_pass1`, `build_json_schema`, `_clean_indices`, `_match_points`, `predict_q_from_exp2`, `predict_A_from_exp2`, `apply_calibration`.
- Small normalization helpers can run against literal dictionaries and lists: `_normalize_ground_truth`, `_resolve_prompt_cfg`, `_render_template`, `extract_answer`.

## Fixtures and Factories

**Test Data:**
```python
tasks = load_tasks_from_ground_truth(
    dataset_root="./captcha_data",
    task_types=["Dice_Count", "Patch_Select"],
    max_per_type=15,
)
```

**Location:**
- Ground-truth fixtures are per-task JSON files under `captcha_data/<Task>/ground_truth.json`.
- Image fixtures are grouped with each task under `captcha_data/<Task>/`.
- Few-shot image fixtures are grouped under `few_shot_assets/<Task>/`.
- Few-shot metadata fixtures live in `few_shot_examples.yaml`, `few_shot_image_manifest.json`, and hard-coded `FEW_SHOT_ANSWERS` in `few_shot_answers.py`.
- Generated result fixtures live under `results/exp*/<provider>/<model>/`.
- Generated error-analysis fixtures live under `error_analysis/exp*/<provider>/<model>/`.

## Coverage

**Requirements:** None enforced.

**View Coverage:**
```bash
# Not detected: no coverage command is defined by this repository.
```

## Test Types

**Unit Tests:**
- Not present as automated files.
- Unit-testable surfaces include `extract_json`, `guess_mime`, `_is_rect_hit`, `_point_dist`, `_normalize_points`, `_clean_indices`, `evaluate_pass1`, `build_json_schema`, `compress_images`, and prediction helpers in `exp2_to_exp3_predict.py`.

**Integration Tests:**
- Manual integration checks run through `run_single_experiment.py` and `test.ipynb`.
- Integration inputs are real dataset images from `captcha_data/`, prompts from `prompts_optimized.yaml`, examples from `few_shot_examples.yaml`, and credentials/config from `secrets.yaml`.
- Integration outputs are CSV and token/error summaries in `results/` and `error_analysis/`.

**E2E Tests:**
- No automated E2E framework is present.
- E2E behavior is exercised by live provider calls through `OpenAIProvider`, `AnthropicProvider`, `GeminiProvider`, and `FireworksProvider` in `run_eval.py`.
- The full E2E path is dataset load -> prompt/schema build -> provider inference -> JSON extraction -> `evaluate_pass1` -> CSV/token/error summary write.

## Common Patterns

**Async Testing:**
```python
# Not detected. Provider calls are synchronous and return (raw, parsed, meta).
raw, parsed, meta = provider.infer(
    prompt=task.prompt,
    images=task.images,
    json_schema=build_json_schema(task.type),
    stream=False,
)
```

**Error Testing:**
```python
try:
    gt = load_ground_truth(type_dir)
except Exception as e:
    print(f"[SKIP] Failed to read GT {task_type}: {e}")
    continue
```

**Result Validation:**
```python
viz = CAPTCHAVisualizer(results_dir="./results")
if viz.data.empty:
    raise RuntimeError("No results found under RESULTS_DIR")

df = viz.data.copy()
exp2 = df[df["experiment"] == "exp2"].copy()
if exp2.empty:
    raise RuntimeError("Exp2 results not found in current selection")
```

---

*Testing analysis: 2026-05-15*
