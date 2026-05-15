# Phase 1: Reproducibility and Safety Foundation - Pattern Map

**Mapped:** 2026-05-15
**Files analyzed:** 21 planned source/config/test/generated files
**Analogs found:** 13 / 21

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `pyproject.toml` | config | dependency/tooling | None | no-analog |
| `uv.lock` | lockfile | dependency/tooling | None | no-analog |
| `secrets.example.yaml` | config | file-I/O | `README.md`, `run_eval.py` | role-match |
| `revision_secrets.py` | utility | file-I/O, transform | `run_eval.py` | role-match |
| `revision_artifacts.py` | model/service | file-I/O, append-only | `experiments_helper.py`, `run_eval.py` | role-match |
| `revision_preflight.py` | utility/CLI | request-count transform, file-I/O | `exp2_to_exp3_predict.py`, `compress_few_shot_assets.py`, `run_eval.py` | role-match |
| `revision_provider_smoke.py` | utility/CLI | explicit provider request-response | `exp2_to_exp3_predict.py`, `run_single_experiment.py`, `run_eval.py` | role-match |
| `run_eval.py` | evaluator/service | request-response, file-I/O | existing `run_eval.py` plus CLI guards from small scripts | exact |
| `run_single_experiment.py` | route/CLI wrapper | request-response orchestration | existing `run_single_experiment.py` | exact |
| `.gitignore` | config | file filtering | existing `.gitignore` | exact |
| `README.md` | documentation | install/run workflow | existing `README.md` | exact |
| `tests/test_import_safety.py` | test | subprocess, import validation | None | no-analog |
| `tests/test_revision_secrets.py` | test | file-I/O, redaction validation | None | no-analog |
| `tests/test_revision_artifacts.py` | test | file-I/O, schema validation | None | no-analog |
| `tests/test_revision_preflight.py` | test | offline validation | None | no-analog |
| `tests/test_task_contracts.py` | test | dataset/schema transform | None | no-analog |
| `tests/test_scoring_regressions.py` | test | pure transform | None | no-analog |
| `results/revision/<run_id>/run_manifest.json` | generated artifact | file-I/O | `experiments_helper.py` stats JSON | role-match |
| `results/revision/<run_id>/attempts.jsonl` | generated artifact | append-only file-I/O | `run_eval.py` token rows | partial |
| `results/revision/<run_id>/summary.csv` | generated artifact | derived CSV | `run_eval.py` results CSV | exact |
| `results/revision/<run_id>/summary.json` | generated artifact | derived JSON | `run_eval.py` token summary JSON | exact |

## Pattern Assignments

### `revision_secrets.py` (utility, file-I/O/transform)

**Analog:** `run_eval.py`

**Imports and loader pattern** (`run_eval.py` lines 7-13, 120-131):
```python
import os, re, io, json, time, base64, argparse, random, pathlib, mimetypes
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional

import yaml

def load_secrets(path: str) -> dict:
    if not path:
        return {}
    if not os.path.exists(path):
        raise FileNotFoundError(f"Secrets file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        if path.endswith(".json"):
            return json.load(f)
        return yaml.safe_load(f) or {}
```

**Pattern to copy:** Keep YAML/JSON support and explicit missing-file errors, but make the new module side-effect free. Add redaction helpers in this module and use them from diagnostics, manifests, and tests.

**Sensitive anti-pattern to avoid** (`run_eval.py` lines 35-47): module-scope diagnostics currently read `./secrets.yaml` and dump the parsed config during import. Do not copy this behavior; Phase 1 should remove or isolate it behind explicit commands without printing raw config.

**Pricing metadata pattern** (`run_eval.py` lines 148-164):
```python
def estimate_cost(provider: str, model: str, tokens_in: Optional[int], tokens_out: Optional[int], secrets: dict) -> Optional[float]:
    try:
        pricing = (secrets.get("pricing") or {}).get(provider, {})
        p = pricing.get(model) or pricing.get(model.lower())
        if not p:
            print(f"[WARNING] No pricing found for provider='{provider}', model='{model}'")
            return None
        return round(_cost(tokens_in, p.get("in_per_1k")) + _cost(tokens_out, p.get("out_per_1k")), 6)
    except Exception as e:
        print(f"[ERROR] estimate_cost failed: provider={provider}, model={model}, error={e}")
        return None
```

**Apply as:** Manifests may include provider/model labels and non-sensitive pricing metadata only. Redact keys by field name and by credential-like value shape before any print, JSON dump, or assertion message.

---

### `secrets.example.yaml` (config, file-I/O)

**Analogs:** `README.md` config section; `run_eval.load_secrets()`

**Config shape pattern** (`README.md` lines 52-84, values intentionally redacted here):
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

pricing:
  openai:
    gpt-5:
      in_per_1k: 0.0
      out_per_1k: 0.0
```

**Apply as:** Commit placeholders only. Do not copy local `secrets.yaml`. Keep enough provider/pricing structure for `load_secrets()` and `estimate_cost()` callers to validate keys without requiring credentials.

---

### `revision_artifacts.py` (model/service, file-I/O/append-only)

**Analogs:** `experiments_helper.py`, `compress_few_shot_assets.py`, `run_eval.py`

**Data carrier pattern** (`experiments_helper.py` lines 16-30; `compress_few_shot_assets.py` lines 29-48):
```python
@dataclass
class ErrorCase:
    task_type: str
    puzzle_id: str
    prompt: str
    gt: Dict[str, Any]
    raw: str
    parsed: Optional[Dict[str, Any]]
    pass1: bool
    e2e_ms: float
```

**Apply as:** Use Pydantic models instead of dataclasses per phase decision D-06, but keep the local convention of typed, explicit record fields and small model classes. Recommended models: `RunManifest`, `AttemptRecord`, `SummaryRow`, and a small writer class.

**CSV/JSON writer pattern** (`experiments_helper.py` lines 75-166):
```python
def save_summary(self, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    errors_file = os.path.join(output_dir, "errors.csv")
    with open(errors_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["type", "puzzle_id", "raw_response", "parsed", "ground_truth"])
        for err in self.errors:
            writer.writerow([...])

    stats_file = os.path.join(output_dir, "stats.json")
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats_data, f, indent=2, ensure_ascii=False)
```

**Token/result output pattern** (`run_eval.py` lines 2675-2681, 2775-2785, 2895-2920):
```python
if collect_tokens and token_log_path:
    os.makedirs(os.path.dirname(token_log_path) or ".", exist_ok=True)
    token_log_file = open(token_log_path, "w", encoding="utf-8", newline="")
    token_log_writer = csv.writer(token_log_file)
    token_log_writer.writerow(["provider", "model", "type", "puzzle_id", "tokens_in", "tokens_out"])

if token_log_writer:
    token_log_writer.writerow([provider, model, task.type, task.puzzle_id, tokens_in, tokens_out])

with open(summary_path, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
```

**Apply as:** New revision writer should create `results/revision/<run_id>/`, write `run_manifest.json` before evaluation, append each `AttemptRecord` to `attempts.jsonl` before derived summaries, then derive `summary.csv` and `summary.json` from attempts. Keep generated artifacts out of legacy `results/exp1` through `results/exp4` layouts.

---

### `revision_preflight.py` (utility/CLI, offline validation)

**Analogs:** `exp2_to_exp3_predict.py`, `compress_few_shot_assets.py`, `run_eval.py`, `visualize_results.py`

**CLI pattern** (`exp2_to_exp3_predict.py` lines 182-205):
```python
def main():
    ap = argparse.ArgumentParser(description="Predict Exp3 from Exp2 with bias corrections")
    ap.add_argument("--results-dir", default="./results", help="Root results directory")
    ap.add_argument("--output", default="./exp2_to_exp3_predictions.csv", help="Output CSV path")
    ap.add_argument("--provider", dest="providers", action="append", default=None)
    args = ap.parse_args()
```

**Manifest/file validation pattern** (`compress_few_shot_assets.py` lines 111-118):
```python
def load_manifest(manifest_path: Path) -> List[Path]:
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    images = manifest.get("images", [])
    if not images:
        raise ValueError("Manifest does not contain an 'images' list.")
    return [Path(p) for p in images]
```

**Dataset validation pattern** (`run_eval.py` lines 1435-1449):
```python
def load_ground_truth(type_dir: str) -> Dict[str, Any]:
    gt_path = os.path.join(type_dir, "ground_truth.json")
    if not os.path.exists(gt_path):
        raise FileNotFoundError(f"ground_truth.json does not exist: {gt_path}")
    with open(gt_path, "r", encoding="utf-8") as f:
        raw = f.read()
    if _is_git_lfs_pointer(raw):
        raise RuntimeError(f"{gt_path} is a Git LFS pointer. Please ensure you have pulled the actual JSON file.")
    return json.loads(raw)
```

**Prompt/few-shot config pattern** (`run_eval.py` lines 1453-1486, 1519-1556):
```python
def _load_prompts_yaml(path: Optional[str]) -> dict:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if data and "types" not in data and "default" not in data and "by_id" not in data:
        data = {"version": 0, "types": data}
    data.setdefault("default", {})
    data.setdefault("types", {})
    data.setdefault("templates", {})
    data.setdefault("by_id", {})
    return data
```

**Task registry pattern** (`run_eval.py` lines 1384-1412; `visualize_results.py` lines 45-68):
```python
SUPPORTED_TYPES = {
    "Dice_Count",
    "Geometry_Click",
    "Image_Matching",
    "Patch_Select",
    "Path_Finder",
    "Connect_Icon",
    "Rotation_Match",
}

TASK_FAMILY = {
    'Dice_Count': 'Click/Coordinate',
    'Patch_Select': 'Grid Selection',
    'Path_Finder': 'Image Matching',
}
```

**Apply as:** Preflight should normalize aliases, validate dataset directories, validate prompt/few-shot keys, compute expected request counts, and report output paths. It must not call `load_secrets()`, `make_provider()`, or any provider `infer()` method.

---

### `revision_provider_smoke.py` (utility/CLI, explicit provider request-response)

**Analogs:** `exp2_to_exp3_predict.py`, `run_single_experiment.py`, `run_eval.py`

**Explicit CLI guard pattern** (`exp2_to_exp3_predict.py` lines 319-325; `run_single_experiment.py` lines 618-620):
```python
out_path = Path(args.output)
out_path.parent.mkdir(parents=True, exist_ok=True)
pred_df.to_csv(out_path, index=False)
print(f"[SAVED] Predictions -> {out_path}")

if __name__ == "__main__":
    main()
```

**Provider factory pattern** (`run_eval.py` lines 1318-1359):
```python
def make_provider(name: str, model: str, secrets: dict, timeout_sec: float, thinking_enabled: bool = False,
                  thinking_options: Optional[Dict[str, Any]] = None) -> ModelProvider:
    name_l = name.lower()
    prov_cfg = (secrets.get("providers") or {}).get(name_l, {})
    api_key = prov_cfg.get("api_key")
    if name_l == "openai":
        return OpenAIProvider(model=model, api_key=api_key, **common_kwargs)
    if name_l == "gemini":
        return GeminiProvider(model=model, api_key=api_key, **common_kwargs)
    raise ValueError(f"Unknown provider: {name}. Supported providers: openai, anthropic, gemini, fireworks")
```

**Apply as:** The smoke script may load secrets and instantiate a provider only inside `main()` after explicit user invocation. Do not import or call it from preflight, tests, or module import paths. Print only provider/model labels and redacted status.

---

### `run_eval.py` (evaluator/service, request-response/file-I/O)

**Analog:** existing `run_eval.py`, with safe CLI guard patterns from smaller scripts

**Primary import-safety target** (`run_eval.py` lines 35-47): remove or move module-scope cwd/dataset/secrets diagnostics and full config dumping behind an explicit command. Do not quote or copy credential-bearing literals from later smoke-test code; isolate that code into `revision_provider_smoke.py` or delete it after replacement.

**Lazy runtime configuration pattern** (`run_eval.py` lines 2575-2667):
```python
def run_eval(..., secrets_file: str = "./secrets.yaml", ...):
    secrets = load_secrets(secrets_file)
    random.seed(seed)
    prompts_cfg = _load_prompts_yaml(prompts_file) if prompts_file else {}
    tasks = build_tasks(dataset_root, types, max_per_type, prompts_cfg=prompts_cfg)
    prov = make_provider(provider, model, secrets, timeout_sec, thinking_enabled=thinking)
```

**Apply as:** Keep secret loading and provider creation inside explicit evaluation or smoke functions, never at import. Add optional revision artifact hooks with defaults off so legacy experiments still write their current outputs.

**Per-attempt-before-summary pattern** (`run_eval.py` lines 2713-2785, 2837-2920):
```python
for task in tqdm(tasks, desc="Evaluating", ncols=0):
    schema = build_json_schema(task.type, include_reasoning=collect_reasoning)
    raw, parsed, meta = prov.infer(prompt=task.prompt, images=task.images, json_schema=schema, stream=stream_flag)
    passed = evaluate_pass1(task, parsed)
    if token_log_writer:
        token_log_writer.writerow([provider, model, task.type, task.puzzle_id, tokens_in, tokens_out])

with open(out_csv, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["provider", "model", "type", "n", "pass_at_1"])
```

**Apply as:** For revision runs, the attempt writer should append before aggregate CSV/JSON is generated. Existing `summary_csv` indentation risk at `run_eval.py` lines 2927-2934 should be covered by a regression test if touched.

**Scoring/schema patterns** (`run_eval.py` lines 2348-2477, 2493-2530):
```python
def evaluate_pass1(task: TaskItem, parsed: Optional[Dict[str, Any]]) -> bool:
    if parsed is None:
        return False
    if task.type == "Dice_Count":
        return parsed.get("answer_type") == "number" and int(parsed.get("value")) == int(gt["sum"])
    if task.type == "Patch_Select":
        pred = sorted(set(int(i) for i in parsed.get("indices", [])))
        gold = sorted(set(int(i) for i in gt.get("correct_patches", [])))
        return pred == gold

def build_json_schema(task_type: str, *, include_reasoning: bool = False) -> Dict[str, Any]:
    if task_type == "Dice_Count":
        return _with_reasoning({"type": "object", "properties": {...}}, include_reasoning=include_reasoning)
```

**Apply as:** Tests can target these pure helpers directly. Phase 1 should avoid broad scoring rewrites, but can add narrow tests for known crash surfaces and validator visibility.

---

### `run_single_experiment.py` (route/CLI wrapper, request-response orchestration)

**Analog:** existing `run_single_experiment.py`

**Import and wrapper pattern** (`run_single_experiment.py` lines 8-22, 33-117):
```python
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_eval import (
    run_eval,
    run_until_type_correct,
    SUPPORTED_TYPES,
    make_provider,
    build_json_schema,
    evaluate_pass1,
    load_secrets,
    build_tasks
)

def run_experiment_1(...):
    if types is None:
        types = sorted(list(SUPPORTED_TYPES))
    result = run_eval(..., collect_tokens=collect_tokens, ...)
    return result
```

**CLI dispatch pattern** (`run_single_experiment.py` lines 495-620):
```python
def main():
    parser = argparse.ArgumentParser(description="Run individual CAPTCHA experiment")
    parser.add_argument("experiment", type=int, choices=[1, 2, 3, 4])
    parser.add_argument("--dataset", default="./captcha_data")
    parser.add_argument("--types", nargs="+", default=None)
    parser.add_argument("--out-csv", default=None)
    args = parser.parse_args()

    if args.experiment == 1:
        run_experiment_1(...)
    elif args.experiment == 2:
        run_experiment_2(...)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
```

**Apply as:** If Phase 1 exposes revision-run or preflight flags here, keep them optional and default-compatible. Importing this module must become safe once `run_eval.py` import side effects are removed.

---

### `.gitignore` (config, file filtering)

**Analog:** existing `.gitignore`

**Current pattern** (`.gitignore` lines 1-15):
```gitignore
__pycache__/
.ipynb_checkpoints/
.claude/
CLAUDE.md
ignore_me.ipynb
*.pyc
.venv/
env/
*.log
wandb/
*.ckpt
*.pt
*.npy
.DS_Store
Draft/
```

**Apply as:** Extend this list narrowly for Phase 1 safety: local secret files (`secrets.yaml`, alternate secret/env files) and generated revision run directories (`results/revision/`) unless a curated artifact is intentionally committed. Do not rewrite history or remove tracked secrets in this phase.

---

### `README.md` (documentation, install/preflight workflow)

**Analog:** existing `README.md`

**Dependency documentation pattern** (`README.md` lines 37-49):
````markdown
## Requirements

* Python 3.10+
* Core dependencies:

  ```bash
  pip install openai anthropic google-genai pillow tqdm pyyaml numpy pandas matplotlib seaborn
  ```
````

**Output layout pattern** (`README.md` lines 198-223):
````markdown
## Output Organization

```text
results/
  exp1/<provider>/<model>/
    results.csv
    exp1_gt_<provider>_<model>_tokens.csv
    exp1_gt_<provider>_<model>_token_summary.json
```
````

**Apply as:** Add `uv` install/lock commands, preflight command, import-safety command, pytest/ruff commands, and the new `results/revision/<run_id>/` artifact contract. Replace credential examples with `secrets.example.yaml` references and placeholders only.

---

### `pyproject.toml` and `uv.lock` (config/lockfile, dependency/tooling)

**Analog:** None in repository. Use current README dependency list and Research recommendations.

**Source dependency reference:** `README.md` lines 37-49 lists the current unpinned runtime dependencies. Phase 1 should move these into `pyproject.toml` and add dev tooling (`pytest`, `ruff`) plus Pydantic for artifact schemas.

**Apply as:** Keep configuration minimal and script-friendly. Do not introduce a `src/` package migration. `uv.lock` should be generated from `pyproject.toml`, not hand-authored.

---

### `tests/*.py` (test, subprocess/file-I/O/pure transform)

**Analog:** No automated test files exist. Use source-under-test patterns and the research test plan.

**Import-safety targets:**
- `run_eval.py` lines 35-47 are import side effects to remove and then guard with subprocess tests.
- `run_single_experiment.py` lines 13-22 imports `run_eval` immediately, so it is a dependent import-safety target.

**Secret-redaction targets:**
- `revision_secrets.py` should own redaction.
- `run_eval.load_secrets()` pattern at lines 120-131 shows current parsing behavior.
- Tests should use sentinel fake values in temporary files and assert those values never appear in stdout/stderr or generated artifacts.

**Artifact tests:**
- Use `experiments_helper.save_summary()` lines 75-166 and `run_eval` token/result writing lines 2675-2920 as behavior analogs.
- Assert attempts are written before summaries are derived.

**Preflight/task tests:**
- Validate `SUPPORTED_TYPES` (`run_eval.py` lines 1384-1412), `load_ground_truth()` (`run_eval.py` lines 1435-1449), prompt config (`run_eval.py` lines 1453-1468), and task construction skip behavior (`run_eval.py` lines 1797-1855).
- Include known alias drift as validator output rather than broad evaluator migration.

**Scoring tests:**
- Target pure helper behavior in `evaluate_pass1()` and `build_json_schema()` (`run_eval.py` lines 2348-2530).
- Keep fixes narrow and focused on revision-critical crash surfaces.

---

## Generated Artifact Contracts

### `results/revision/<run_id>/run_manifest.json`

**Analog:** `run_eval.py` token summary JSON (`run_eval.py` lines 2895-2920) and `experiments_helper.py` stats JSON (`experiments_helper.py` lines 110-166).

**Apply as:** Write a Pydantic-validated manifest with `schema_version`, `run_id`, `created_at`, code/dependency metadata, dataset summary, task types, prompt/few-shot config hashes, provider/model labels, retry policy, cost control, and output paths. Redact all credential-like values before writing.

### `results/revision/<run_id>/attempts.jsonl`

**Analog:** `run_eval.py` token row writing (`run_eval.py` lines 2675-2785) and `run_until_type_correct()` attempt rows (`run_eval.py` lines 3127-3128).

**Apply as:** Append one JSON object per provider attempt before aggregate summaries. Use stable fields from the research contract: `schema_version`, `run_id`, `attempt_id`, `task_type`, `puzzle_id`, `attempt_index`, `prompt_mode`, `provider`, `model`, `parsed_answer`, `correct`, `error_category`, latency, token, cost, and timestamp fields.

### `results/revision/<run_id>/summary.csv` and `summary.json`

**Analog:** `run_eval.py` aggregate CSV and summary JSON (`run_eval.py` lines 2837-2920).

**Apply as:** Derive both summaries from `attempts.jsonl`, not from in-memory aggregate-only state. Keep legacy `results/exp*/.../results.csv` behavior unchanged unless revision mode is explicitly enabled.

## Shared Patterns

### Import Safety

**Source:** `run_eval.py` lines 35-47 are anti-patterns; `exp2_to_exp3_predict.py` lines 319-325 and `run_single_experiment.py` lines 618-620 are safe CLI guard patterns.

**Apply to:** `run_eval.py`, `run_single_experiment.py`, `revision_provider_smoke.py`, tests.

All importable modules should define functions/classes only at import time. No secret reads, provider client construction, provider requests, result writes, or raw config prints should happen outside explicit function calls or `if __name__ == "__main__":` guarded CLI entry points.

### Secret Safety

**Source:** `run_eval.load_secrets()` lines 120-131; `.gitignore` lines 1-15; README config section lines 52-84.

**Apply to:** `revision_secrets.py`, `secrets.example.yaml`, `run_eval.py`, `README.md`, tests.

Preserve local `secrets.yaml` support for existing workflows, but never print raw config and never include credential values in manifests, summaries, logs, or docs. `secrets.example.yaml` should contain placeholders only.

### Offline Preflight

**Source:** `run_eval.load_ground_truth()` lines 1435-1449, `_load_prompts_yaml()` lines 1453-1468, `build_tasks()` lines 1797-1855, `visualize_results.TASK_FAMILY` lines 45-68.

**Apply to:** `revision_preflight.py`, `tests/test_revision_preflight.py`, `tests/test_task_contracts.py`.

Preflight should inspect files and compute counts without constructing providers. Report selected task types, item counts, expected provider request count, output directory, manifest path, and warnings/errors for unsupported aliases or schema drift.

### CLI Style

**Source:** `exp2_to_exp3_predict.py` lines 182-205 and `run_single_experiment.py` lines 495-620.

**Apply to:** `revision_preflight.py`, `revision_provider_smoke.py`, README command examples.

Use root-level script CLIs with `argparse`, keyword-heavy options, defaults matching repository paths, and `if __name__ == "__main__": main()` guards.

### File I/O and Result Writing

**Source:** `experiments_helper.py` lines 75-166, `run_eval.py` lines 2675-2920, `compress_few_shot_assets.py` lines 231-269.

**Apply to:** `revision_artifacts.py`, revision tests, generated artifact files.

Create parent directories before writing, use UTF-8, use `newline=""` for CSV, write machine-readable JSON with indentation for summaries/manifests, and make attempt logging append-only.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `pyproject.toml` | config | dependency/tooling | No Python project metadata exists. Use README dependencies and Research guidance. |
| `uv.lock` | lockfile | dependency/tooling | No lockfile exists. Generate with `uv lock`. |
| `tests/test_import_safety.py` | test | subprocess/import validation | No automated test suite exists. Use pytest conventions from Research. |
| `tests/test_revision_secrets.py` | test | file-I/O/redaction validation | No automated test suite exists. |
| `tests/test_revision_artifacts.py` | test | schema/file-I/O validation | No automated test suite exists. |
| `tests/test_revision_preflight.py` | test | offline validation | No automated test suite exists. |
| `tests/test_task_contracts.py` | test | dataset/schema transform | No automated test suite exists. |
| `tests/test_scoring_regressions.py` | test | pure transform | No automated test suite exists. |

## Metadata

**Analog search scope:** root Python scripts, `.gitignore`, `README.md`, `.planning/codebase/*`, Phase 1 context/research docs.

**Files scanned:** `run_eval.py`, `run_single_experiment.py`, `experiments_helper.py`, `exp2_to_exp3_predict.py`, `compress_few_shot_assets.py`, `visualize_results.py`, `.gitignore`, `README.md`, and required planning/codebase docs.

**Pattern extraction date:** 2026-05-15

**Sensitive-source handling:** Did not read or quote `secrets.yaml`. Did not quote the hard-coded credential-bearing smoke-test line reported in codebase concerns; referenced it only as a generic import/smoke-test hazard.
