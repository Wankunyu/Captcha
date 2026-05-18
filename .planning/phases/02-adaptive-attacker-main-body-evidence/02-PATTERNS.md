# Phase 02: Adaptive Attacker Main-Body Evidence - Pattern Map

**Mapped:** 2026-05-18
**Files analyzed:** 12 planned source/test/generated files
**Analogs found:** 12 / 12

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `adaptive_artifacts.py` | model/service | append-only file-I/O, schema transform | `revision_artifacts.py` | exact |
| `adaptive_preflight.py` | utility/CLI | offline validation, request-count transform, file-I/O | `revision_preflight.py` | exact |
| `adaptive_attacker.py` | evaluator/service/CLI | request-response, explicit local memory, append-only file-I/O | `run_eval.py`, `run_until_type_correct()` | role-match |
| `adaptive_compare.py` | analysis utility/CLI | batch CSV load/merge/transform | `exp2_to_exp3_predict.py`, `visualize_results.py` | exact |
| `tests/test_adaptive_artifacts.py` | test | file-I/O, schema validation | `tests/test_revision_artifacts.py` | exact |
| `tests/test_adaptive_preflight.py` | test | offline validation | `tests/test_revision_preflight.py` | exact |
| `tests/test_adaptive_attacker.py` | test | fake-provider request-response, state validation | `tests/test_revision_run_contract.py` | exact |
| `tests/test_adaptive_compare.py` | test | CSV merge/pure transform | `tests/test_scoring_regressions.py`, `exp2_to_exp3_predict.py` | role-match |
| `results/revision/<run_id>/adaptive_preflight_report.json` | generated artifact | file-I/O | `revision_preflight.py` report writer | role-match |
| `results/revision/<run_id>/adaptive_attempts.jsonl` | generated artifact | append-only file-I/O | `revision_artifacts.py` attempts writer | exact |
| `results/revision/<run_id>/adaptive_summary.csv/json` | generated artifact | derived batch summary | `revision_artifacts.py` summary writer | exact |
| `results/revision/<run_id>/adaptive_comparison.csv/json` | generated artifact | batch merge output | `exp2_to_exp3_predict.py` prediction CSV | role-match |

## Pattern Assignments

### `adaptive_artifacts.py` (model/service, append-only file-I/O)

**Analog:** `revision_artifacts.py`

**Imports and schema constants pattern** (`revision_artifacts.py` lines 1-18):
```python
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

from pydantic import BaseModel, Field

RUN_MANIFEST_SCHEMA_VERSION = "cognition.revision.run_manifest.v1"
ATTEMPT_RECORD_SCHEMA_VERSION = "cognition.revision.attempt.v1"
SUMMARY_ROW_SCHEMA_VERSION = "cognition.revision.summary_row.v1"
```

**Model pattern** (`revision_artifacts.py` lines 45-80, 83-92):
```python
class RunManifest(BaseModel):
    schema_version: str = RUN_MANIFEST_SCHEMA_VERSION
    run_id: str
    created_at: datetime
    code_revision: dict[str, Any]
    python_version: str
    dependency_versions: dict[str, str]
    dataset_summary: dict[str, Any]
    prompt_config: PromptConfig
    provider: str
    model: str
    seed: int | None = None
    retry_policy: dict[str, Any] = Field(default_factory=dict)
    cost_control: dict[str, Any] = Field(default_factory=dict)
    output_paths: dict[str, str] = Field(default_factory=dict)
    ethics_scope: str = "offline authorized datasets only; no live service automation"

class AttemptRecord(BaseModel):
    schema_version: str = ATTEMPT_RECORD_SCHEMA_VERSION
    run_id: str
    attempt_id: str
    task_type: str
    puzzle_id: str
    attempt_index: int
    prompt_mode: str
    provider: str
    model: str
    parsed_answer: Any = None
    correct: bool
    error_category: str | None = None
    latency_ms: float | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    cost_usd: float | None = None
    timestamp: datetime
```

**Apply as:** Add adaptive-specific v1 constants and Pydantic models instead of changing Phase 1 `AttemptRecord`. Minimum models should cover `AdaptivePolicyNote`, `AdaptiveAttemptRecord`, `AdaptiveSummaryRow`, and `AdaptiveComparisonRow`. Include fields from ADAPT-03: prior failures, policy state before/after, prompt adaptation metadata, selected task, parsed answer, correctness, failure class, latency, token usage, cumulative cost, and stopping reason.

**Run directory validation pattern** (`revision_artifacts.py` lines 152-162):
```python
def revision_run_dir(output_root: str | Path, run_id: str) -> Path:
    if not _RUN_ID_RE.fullmatch(run_id):
        raise ValueError(
            "run_id must start with a letter or number and contain only letters, "
            "numbers, dot, underscore, or hyphen"
        )
    root = Path(output_root).resolve()
    run_dir = (root / run_id).resolve()
    if not run_dir.is_relative_to(root):
        raise ValueError("run_id resolves outside output_root")
    return run_dir
```

**Writer and output path pattern** (`revision_artifacts.py` lines 165-210):
```python
class RevisionArtifactWriter:
    def __init__(self, output_root: str | Path, run_id: str, *, overwrite: bool = False, resume: bool = False) -> None:
        if overwrite and resume:
            raise ValueError("overwrite and resume are mutually exclusive")

        self._run_dir = revision_run_dir(output_root, run_id)
        if self._run_dir.exists() and not overwrite and not resume:
            raise FileExistsError(f"Revision run directory already exists: {self._run_dir}")
        if self._run_dir.exists() and overwrite:
            shutil.rmtree(self._run_dir)
        self._run_dir.mkdir(parents=True, exist_ok=resume)

    def output_paths(self) -> dict[str, str]:
        return {
            "run_manifest": str(self.manifest_path),
            "attempts": str(self.attempts_path),
            "summary_csv": str(self.summary_csv_path),
            "summary_json": str(self.summary_json_path),
        }
```

**Append-only attempt pattern** (`revision_artifacts.py` lines 220-236):
```python
def append_attempt(self, attempt: AttemptRecord) -> Path:
    existing_attempt_ids = {existing.attempt_id for existing in self.iter_attempts()}
    if attempt.attempt_id in existing_attempt_ids:
        raise ValueError(f"Attempt already exists in attempts.jsonl: {attempt.attempt_id}")
    with self.attempts_path.open("a", encoding="utf-8") as handle:
        handle.write(attempt.model_dump_json())
        handle.write("\n")
    return self.attempts_path

def iter_attempts(self) -> Iterator[AttemptRecord]:
    if not self.attempts_path.exists():
        return
    with self.attempts_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield AttemptRecord.model_validate_json(line)
```

**Summary derivation pattern** (`revision_artifacts.py` lines 238-280):
```python
groups: dict[tuple[str, str, str, str], dict[str, int]] = defaultdict(
    lambda: {"n_attempts": 0, "n_success": 0}
)
for attempt in self.iter_attempts():
    key = (attempt.run_id, attempt.provider, attempt.model, attempt.task_type)
    groups[key]["n_attempts"] += 1
    groups[key]["n_success"] += int(attempt.correct)

with self.summary_csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row.model_dump(mode="json"))

with self.summary_json_path.open("w", encoding="utf-8") as handle:
    json.dump({"schema_version": SUMMARY_ROW_SCHEMA_VERSION, "rows": [...]}, handle, indent=2, ensure_ascii=False)
```

**Apply as:** Derive `adaptive_summary.csv/json` from `adaptive_attempts.jsonl`, not from in-memory only state. Keep adaptive attempt IDs stable, for example `{run_id}:{task_type}:{attempt_index}:{puzzle_id}`.

---

### `adaptive_preflight.py` (utility/CLI, offline validation)

**Analog:** `revision_preflight.py`

**Imports and dependency boundary pattern** (`revision_preflight.py` lines 1-14):
```python
import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from revision_artifacts import revision_run_dir, sha256_file, sha256_text
from run_eval import DATASET_DIR_ALIASES, SUPPORTED_TYPES, TASK_ALIASES

PREFLIGHT_SCHEMA_VERSION = "cognition.revision.preflight.v1"
```

**Report model pattern** (`revision_preflight.py` lines 17-48):
```python
class PreflightTaskSummary(BaseModel):
    task_type: str
    canonical_task_type: str
    dataset_dir: str
    ground_truth_path: str
    item_count: int
    selected_count: int
    warnings: list[str] = Field(default_factory=list)

class PreflightCostPreview(BaseModel):
    expected_request_count: int
    approximate_cost_usd: float | None = None
    pricing_source: str | None = None
    unavailable_reason: str | None = None

class PreflightReport(BaseModel):
    schema_version: str = PREFLIGHT_SCHEMA_VERSION
    run_id: str
    provider: str
    model: str
    prompt_mode: str
    selected_task_types: list[str]
    expected_request_count: int
    prompt_config: dict[str, Any]
    cost_preview: PreflightCostPreview
    output_dir: str
    manifest_path: str
    attempts_path: str
    tasks: list[PreflightTaskSummary]
```

**CLI pattern** (`revision_preflight.py` lines 51-70):
```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate revision run inputs before paid calls.")
    parser.add_argument("--dataset-root", default="./captcha_data")
    parser.add_argument("--types", nargs="+", required=True)
    parser.add_argument("--prompts-file", default="./prompts_optimized.yaml")
    parser.add_argument("--few-shot-config", default=None)
    parser.add_argument("--pricing-file", default=None)
    parser.add_argument("--output-root", default="./results/revision")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--max-per-type", type=int, default=None)
    parser.add_argument("--max-attempts", type=int, default=1)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    return parser
```

**Apply as:** Add adaptive-specific CLI fields: `--attempt-budget-k`, `--sampling-mode without-replacement`, `--feedback-mode binary-pass-fail`, `--memory-mode explicit-policy-notes`, `--reflection-mode constrained`, and `--stopping-rule first-success-or-budget`.

**Offline validation pattern** (`revision_preflight.py` lines 164-215):
```python
def build_report(args: argparse.Namespace) -> PreflightReport:
    if args.overwrite and args.resume:
        raise ValueError("--overwrite and --resume are mutually exclusive")
    if args.max_attempts < 1:
        raise ValueError("--max-attempts must be >= 1")

    _load_mapping(args.prompts_file, "prompts file")
    if args.few_shot_config:
        _load_mapping(args.few_shot_config, "few-shot config")

    run_dir = revision_run_dir(args.output_root, args.run_id)
    if run_dir.exists() and not args.overwrite and not args.resume:
        raise FileExistsError(
            f"Revision output directory exists; use --overwrite or --resume: {run_dir}"
        )

    tasks: list[PreflightTaskSummary] = []
    for requested_type in args.types:
        canonical = _canonical_task_type(requested_type)
        dataset_dir = Path(args.dataset_root) / _dataset_dir_name(canonical)
        ground_truth_path = dataset_dir / "ground_truth.json"
        ground_truth = _load_ground_truth(ground_truth_path)
        item_count = len(ground_truth)
        selected = _selected_count(item_count, args.max_per_type)
        ...

    expected_request_count = sum(task.selected_count for task in tasks) * args.max_attempts
```

**Report writing and CLI guard pattern** (`revision_preflight.py` lines 218-245):
```python
def _write_report(report: PreflightReport, overwrite: bool, resume: bool) -> Path:
    run_dir = Path(report.output_dir)
    if run_dir.exists() and overwrite:
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=resume)
    report_path = run_dir / "preflight_report.json"
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report.model_dump(mode="json"), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return report_path

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    ...
    print(json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

**Apply as:** Preflight must not call `load_secrets()`, `make_provider()`, or any provider `infer()` method. Count solve requests and reflection requests separately in the report while keeping solve budget `k` task-type fair.

---

### `adaptive_attacker.py` (evaluator/service/CLI, request-response with explicit memory)

**Analogs:** `run_eval.py`, especially `run_eval()` and `run_until_type_correct()`

**Provider interface pattern** (`run_eval.py` lines 549-562):
```python
class ModelProvider:
    def __init__(self, model:str, api_key:str, **kwargs):
        self.model = model
        self.api_key = api_key
        self.timeout = float(kwargs.get("timeout_sec", 120.0))
        self.thinking_enabled = bool(kwargs.get("thinking_enabled", False))
        self.thinking_options = kwargs.get("thinking_options") or {}

    def infer(self, prompt:str, images:List[str], json_schema:Dict[str, Any],
              stream:bool=True) -> Tuple[str, Optional[Dict[str,Any]], Dict[str,Any]]:
        raise NotImplementedError
```

**Provider factory pattern** (`run_eval.py` lines 1311-1352):
```python
def make_provider(name:str, model:str, secrets:dict, timeout_sec:float,
                     thinking_enabled: bool = False,
                     thinking_options: Optional[Dict[str, Any]] = None) -> ModelProvider:
    name_l = name.lower()
    prov_cfg = (secrets.get("providers") or {}).get(name_l, {})
    api_key = prov_cfg.get("api_key")
    ...
    if name_l == "openai":
        return OpenAIProvider(model=model, api_key=api_key, **common_kwargs)
    if name_l == "anthropic":
        return AnthropicProvider(model=model, api_key=api_key, **common_kwargs)
    if name_l == "gemini":
        return GeminiProvider(model=model, api_key=api_key, **common_kwargs)
    if name_l == "fireworks":
        return FireworksProvider(model=model, api_key=api_key, base_url=prov_cfg.get("base_url"), **common_kwargs)
    raise ValueError(f"Unknown provider: {name}. Supported providers: openai, anthropic, gemini, fireworks")
```

**Task item and alias pattern** (`run_eval.py` lines 1360-1402):
```python
@dataclass
class TaskItem:
    type: str
    puzzle_id: str
    prompt: str
    images: List[str]
    gt: Dict[str, Any]

SUPPORTED_TYPES = {
    "Dice_Count",
    "Geometry_Click",
    "Image_Matching",
    "Patch_Select",
    ...
    "Connect_Icon",
    "Rotation_Match",
}

TASK_ALIASES = {"Connect_icon": "Connect_Icon"}
DATASET_DIR_ALIASES = {"Connect_Icon": "Connect_icon"}
```

**Task construction pattern** (`run_eval.py` lines 1793-1836, 1837-1850):
```python
def build_tasks(
    dataset_root: str,
    types: List[str],
    max_per_type: int = None,
    prompts_cfg: dict | None = None,
    prompt_prefix: str = "",
    prompt_suffix: str = "",
    prompt_mode: str = "auto",
    exclude_examples: Optional[Dict[str, List[str]]] = None
) -> List[TaskItem]:
    prompts_cfg = prompts_cfg or {}
    exclude_examples = exclude_examples or {}
    tasks: List[TaskItem] = []
    for requested_type in types:
        t = TASK_ALIASES.get(requested_type, requested_type)
        if t not in SUPPORTED_TYPES:
            print(f"[SKIP] Type not yet supported: {requested_type}")
            continue
        type_dir = os.path.join(dataset_root, DATASET_DIR_ALIASES.get(t, t))
        gt = load_ground_truth(type_dir)
        puzzle_ids = list(gt.keys())
        ...
        if isinstance(max_per_type, int) and max_per_type > 0 and len(puzzle_ids) > max_per_type:
            puzzle_ids = random.sample(puzzle_ids, k=max_per_type)
        else:
            random.shuffle(puzzle_ids)
```

**Apply as:** Group returned `TaskItem` objects by `task.type`. For Phase 2, sample fresh instances without replacement by shuffling once per task type and consuming with `pop()` or an index. Do not copy the fixed retry `random.choice(pool_tasks)` behavior from `run_until_type_correct()`.

**Scoring boundary pattern** (`run_eval.py` lines 2345-2480):
```python
def evaluate_pass1(task:TaskItem, parsed:Optional[Dict[str,Any]])->bool:
    if parsed is None:
        return False
    t = task.type
    gt = task.gt
    try:
        if t == "Dice_Count":
            return parsed.get("answer_type")=="number" and int(parsed.get("value")) == int(gt["sum"])
        if task.type == "Geometry_Click":
            ...
        if t == "Patch_Select":
            pred = sorted(set(int(i) for i in parsed.get("indices", [])))
            gold = sorted(set(int(i) for i in gt.get("correct_patches",[])))
            return pred == gold
        ...
    except Exception:
        return False
    return False
```

**JSON schema pattern** (`run_eval.py` lines 2496-2530, 2531-2571):
```python
def build_json_schema(task_type:str, *, include_reasoning: bool = False)->Dict[str,Any]:
    if task_type == "Dice_Count":
        return _with_reasoning({"type":"object","properties":{"answer_type":{"type":"string","enum":["number"]},
                                              "value":{"type":"integer"}},
                "required":["answer_type","value"]}, include_reasoning=include_reasoning)
    if task_type in ("Geometry_Click","Place_Dot"):
        return _with_reasoning({"type":"object","properties":{"answer_type":{"type":"string","enum":["single_point"]},
                                              "point":{"type":"object",
                                                       "properties":{"x":{"type":"number"},"y":{"type":"number"}},
                                                       "required":["x","y"]}},
                "required":["answer_type","point"]}, include_reasoning=include_reasoning)
    ...
    return _with_reasoning({"type":"object"}, include_reasoning=include_reasoning)
```

**Revision manifest-before-provider pattern** (`run_eval.py` lines 2676-2780, 2781-2792):
```python
if revision_run_id and not write_attempts:
    raise ValueError("revision runs require write_attempts=True")

secrets = load_secrets(secrets_file)
random.seed(seed)
prompts_cfg = _load_prompts_yaml(prompts_file) if prompts_file else {}
tasks = build_tasks(dataset_root, types, max_per_type, prompts_cfg=prompts_cfg, ...)

if revision_run_id:
    revision_writer = RevisionArtifactWriter(...)
    manifest = RunManifest(
        run_id=revision_run_id,
        created_at=utc_now(),
        code_revision=collect_code_revision(),
        python_version=platform.python_version(),
        dependency_versions=_revision_dependency_versions(),
        dataset_summary=_revision_dataset_summary(dataset_root, tasks),
        retry_policy={"mode": "single_pass", "max_attempts": 1},
        cost_control=_revision_cost_control(...),
        output_paths=revision_writer.output_paths(),
    )
    revision_writer.write_manifest(manifest)

if tasks_to_evaluate:
    prov = make_provider(provider, model, secrets, timeout_sec, ...)
```

**Apply as:** Adaptive runs should write the manifest before provider construction, with `retry_policy` or adaptive policy metadata set to `mode=session_memory_adaptive`, `attempt_budget_k`, `sampling_mode=without_replacement`, `feedback_mode=binary_pass_fail`, and `memory_mode=explicit_policy_notes`.

**Per-attempt scoring and append pattern** (`run_eval.py` lines 2839-2923):
```python
for task in tqdm(tasks_to_evaluate, desc="Evaluating", ncols=0):
    schema = build_json_schema(task.type, include_reasoning=collect_reasoning)
    raw, parsed, meta = prov.infer(
        prompt=task.prompt,
        images=task.images,
        json_schema=schema,
        stream=stream_flag,
        few_shot_examples=few_shot_content
    )

    if isinstance(raw, str) and raw.startswith("__ERROR__"):
        parsed = None
        errors += 1

    passed = evaluate_pass1(task, parsed)
    ...
    if revision_writer is not None and write_attempts:
        revision_writer.append_attempt(
            AttemptRecord(
                run_id=revision_run_id,
                attempt_id=revision_attempt_id,
                task_type=task.type,
                puzzle_id=task.puzzle_id,
                attempt_index=1,
                parsed_answer=parsed,
                correct=passed,
                error_category="parse_error" if parsed is None else None,
                latency_ms=e2e,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost_usd=task_cost_usd,
                timestamp=utc_now(),
            )
        )
```

**Fixed retry loop pattern to adapt carefully** (`run_eval.py` lines 3203-3219, 3231-3251, 3286-3298):
```python
for t in types:
    effective_max = None if use_full_dataset_pool else max_pool_per_type
    pool_tasks = build_tasks(
        dataset_root=dataset_root,
        types=[t],
        max_per_type=effective_max,
        prompts_cfg=prompts_cfg,
        prompt_prefix=prompt_prefix,
        prompt_suffix=prompt_suffix,
        prompt_mode=prompt_mode
    )
    random.shuffle(pool_tasks)

    while attempt < max_attempt_per_type:
        task = random.choice(pool_tasks)
        attempt += 1
        schema = build_json_schema(task.type)
        raw, parsed, meta = prov.infer(
            prompt=pr, images=task.images, json_schema=schema, stream=stream
        )
        ok = evaluate_pass1(task, parsed)
        ...
        if log_attempt_rows:
            csv_rows.append(f"attempt,{provider},{model},{t},{task.puzzle_id},{attempt},{cumulative:.1f},{int(ok)},{last_err}")
        if ok:
            success = 1
            first_success_pid = task.puzzle_id
            break
    csv_rows.append(f"summary,{provider},{model},{t},{first_success_pid},{attempt},{cumulative:.1f},{success},{last_err}")
```

**Apply as:** Reuse the per-task-type stopping shape, cumulative latency accounting, and first-success summary. Change sampling to without replacement. Add explicit memory state and reflection calls only after scientific wrong answers. Reflection input must contain only current prompt, the model's own raw/parsed answer, and binary `passed=False`; it must not receive `task.gt`, correct coordinates, counts, categories, instance labels, or corrective hints.

---

### `adaptive_compare.py` (analysis utility/CLI, batch CSV merge)

**Analogs:** `exp2_to_exp3_predict.py`, `visualize_results.py`

**Bernoulli baseline formulas** (`exp2_to_exp3_predict.py` lines 40-60, 105-155):
```python
def g_q(p: float, k: int) -> float:
    return 1.0 - (1.0 - p) ** max(k, 0)

def predict_q_from_exp2(
    p_hat: float,
    n: int,
    k: int,
    N_pool: Optional[int] = None,
    alpha0: float = 1.0,
    beta0: float = 1.0,
) -> float:
    p = float(np.clip(p_hat, 1e-9, 1.0 - 1e-9))
    q = g_q(p, k)
    if N_pool is not None:
        return predict_exp3_hypergeom(p, k, N_pool)
    return q

def predict_A_from_exp2(...):
    p = float(np.clip(p_hat, 1e-9, 1.0 - 1e-9))
    if N_pool is not None:
        return expected_attempts_hypergeom(p, k, N_pool)
    return float((1.0 - (1.0 - p) ** k) / p)
```

**Legacy result loading and grouping pattern** (`exp2_to_exp3_predict.py` lines 207-251, 253-266):
```python
viz = CAPTCHAVisualizer(results_dir=args.results_dir)
if viz.data.empty:
    raise SystemExit("No results found under --results-dir")

df = viz.data.copy()
...
exp2 = df[df['experiment'] == 'exp2'].copy()
if exp2.empty:
    raise SystemExit("Exp2 results not found; cannot predict")

exp2_grp = exp2.groupby(['provider','model','provider_model','task_type'], as_index=False).agg(
    n=('n','max'),
    p_hat=('pass','mean')
)

exp3 = df[df['experiment'] == 'exp3'].copy()
if not exp3.empty:
    exp3_obs = exp3.groupby(['provider','model','provider_model','task_type'], as_index=False).agg(
        q_obs=('pass','mean'),
        A_obs=('avg_attempts','mean')
    )
```

**Prediction row and output pattern** (`exp2_to_exp3_predict.py` lines 268-322):
```python
rows = []
for _, r in exp2_grp.iterrows():
    prov = r['provider']
    model = r['model']
    pm = r['provider_model']
    t = r['task_type']
    n = int(r.get('n', 1) or 1)
    p_hat = float(r['p_hat'])
    q_pred = predict_q_from_exp2(p_hat, n, args.k, args.pool_size, args.alpha0, args.beta0)
    A_pred = predict_A_from_exp2(p_hat, n, args.k, args.pool_size, args.alpha0, args.beta0)
    rows.append([prov, model, pm, t, n, p_hat, q_pred, A_pred])

pred_df = pd.DataFrame(rows, columns=['provider', 'model', 'provider_model', 'task_type', 'n', 'p_hat', 'q_pred', 'A_pred'])
...
out_path = Path(args.output)
out_path.parent.mkdir(parents=True, exist_ok=True)
pred_df.to_csv(out_path, index=False)
```

**Task family and hard-task metadata** (`visualize_results.py` lines 46-73):
```python
TASK_FAMILY = {
    'Dice_Count': 'Click/Coordinate',
    'Click_Order': 'Click/Coordinate',
    'Place_Dot': 'Click/Coordinate',
    'Geometry_Click': 'Click/Coordinate',
    'Pick_Area': 'Click/Coordinate',
    'Misleading_Click': 'Click/Coordinate',
    'Patch_Select': 'Grid Selection',
    'Select_Animal': 'Grid Selection',
    'Image_Recognition': 'Grid Selection',
    'Unusual_Detection': 'Grid Selection',
    'Image_Matching': 'Image Matching',
    'Object_Match': 'Image Matching',
    'Path_Finder': 'Image Matching',
    'Rotation_Match': 'Image Matching',
    'Bingo': 'Logic/Reasoning',
    'Dart_Count': 'Logic/Reasoning',
    'Coordinates': 'Logic/Reasoning',
    'Connect_Icon': 'Logic/Reasoning',
}

HARD_TASKS = {
    'Patch_Select', 'Rotation_Match', 'Click_Order',
    'Pick_Area', 'Place_Dot', 'Dice_Count'
}
```

**40 percent threshold pattern** (`visualize_results.py` lines 375-379, 771-775, 898-943):
```python
for i, (task, row) in enumerate(pivot.iterrows()):
    if row['Average'] < 40:
        ax.add_patch(plt.Rectangle((len(pivot.columns)-1, i), 1, 1,
                                  fill=False, edgecolor='red', lw=3))

ax.axhline(y=40, color='red', linestyle='--', linewidth=2, alpha=0.5)
ax.axvline(x=40, color='red', linestyle='--', linewidth=2, alpha=0.5)
ax.fill_between([0, 40], 0, 40, alpha=0.1, color='red',
               label='Recommended CAPTCHA Zone')

def generate_captcha_recommendation(self, experiment: str = 'exp2',
                                   threshold: float = 40.0,
                                   top_n: int = 8) -> pd.DataFrame:
    ...
    difficult_tasks = stats[stats['avg_pass@1'] < threshold].copy()
```

**Apply as:** Produce one row per `run_id/provider/model/task_type/attempt_budget_k`. Merge Exp2 pass@1, Bernoulli `success_at_k`, fixed retry observed Exp3, and adaptive summary. Use `hard`, `borderline`, and `broken` labels with an explicit `cutoff_note` stating the 40 percent cutoff is operational, not a universal security boundary.

---

### `tests/test_adaptive_artifacts.py` (test, schema/file-I/O validation)

**Analog:** `tests/test_revision_artifacts.py`

**Fixture helper pattern** (`tests/test_revision_artifacts.py` lines 22-58):
```python
def _manifest(run_id: str = "run-1") -> RunManifest:
    return RunManifest(
        run_id=run_id,
        created_at=utc_now(),
        code_revision=collect_code_revision(),
        python_version="3.11",
        dependency_versions=collect_dependency_versions(["pydantic", "missing-package-for-test"]),
        dataset_summary={"Dice_Count": 1},
        prompt_config=PromptConfig(...),
        provider="openai",
        model="gpt-5",
        output_paths={},
    )

def _attempt(run_id: str, attempt_id: str, task_type: str, correct: bool) -> AttemptRecord:
    return AttemptRecord(
        run_id=run_id,
        attempt_id=attempt_id,
        task_type=task_type,
        puzzle_id=attempt_id,
        attempt_index=1,
        prompt_mode="opt",
        provider="openai",
        model="gpt-5",
        parsed_answer={"answer": 1},
        correct=correct,
        timestamp=utc_now(),
    )
```

**Append and summary assertions** (`tests/test_revision_artifacts.py` lines 78-108, 129-136):
```python
writer.append_attempt(_attempt("run-1", "one", "Dice_Count", True))
writer.append_attempt(_attempt("run-1", "two", "Dice_Count", False))

lines = writer.attempts_path.read_text(encoding="utf-8").splitlines()
assert len(lines) == 2
assert [json.loads(line)["attempt_id"] for line in lines] == ["one", "two"]

csv_path, json_path = writer.write_summaries_from_attempts()
with csv_path.open("r", encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle))
with json_path.open("r", encoding="utf-8") as handle:
    payload = json.load(handle)

with pytest.raises(ValueError, match="Attempt already exists"):
    writer.append_attempt(attempt)
```

**Apply as:** Add tests for adaptive schema versions, append order, duplicate adaptive attempt IDs, memory note serialization, summary derivation, cumulative latency/cost fields, and a negative assertion that policy notes cannot contain raw transcripts or ground-truth-like fields.

---

### `tests/test_adaptive_preflight.py` (test, offline validation)

**Analog:** `tests/test_revision_preflight.py`

**Temp dataset and CLI fixture pattern** (`tests/test_revision_preflight.py` lines 11-24, 39-59):
```python
def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")

def _dataset_root(tmp_path: Path) -> Path:
    root = tmp_path / "captcha_data"
    _write_json(root / "Dice_Count" / "ground_truth.json", {"dice1.png": {"answer": 3}})
    _write_json(root / "Connect_icon" / "ground_truth.json", {"puzzle1.json": {"choice": 0}})
    return root

def _base_args(tmp_path: Path, run_id: str = "run-1") -> list[str]:
    return [
        "--dataset-root", str(_dataset_root(tmp_path)),
        "--types", "Dice_Count",
        "--prompts-file", str(_prompts_file(tmp_path)),
        "--output-root", str(tmp_path / "results" / "revision"),
        "--run-id", run_id,
        "--provider", "openai",
        "--model", "gpt-5",
        "--max-per-type", "1",
        "--max-attempts", "1",
    ]
```

**Report assertion pattern** (`tests/test_revision_preflight.py` lines 62-70, 100-112, 115-137):
```python
exit_code = main([*_base_args(tmp_path), "--write-report"])
report = json.loads(capsys.readouterr().out)

assert exit_code == 0
assert report["expected_request_count"] == 1
assert report["tasks"][0]["canonical_task_type"] == "Dice_Count"
assert report["cost_preview"]["expected_request_count"] == 1
assert (tmp_path / "results" / "revision" / "run-1" / "preflight_report.json").exists()

monkeypatch.setattr(run_eval, "make_provider", fail)
main(_base_args(tmp_path, run_id="offline-only"))
assert report["provider"] == "openai"
assert report["model"] == "gpt-5"

assert prompt_config["prompts_file_sha256"] == sha256_file(prompts)
assert report["cost_preview"]["approximate_cost_usd"] is None
assert report["cost_preview"]["unavailable_reason"] == "pricing metadata not provided"
```

**Apply as:** Add assertions for `attempt_budget_k`, solve request count, reflection request count, selected task types, output paths, sampling mode, feedback mode, memory mode, stopping rule, prompt/few-shot hashes, unsafe run IDs, existing output dirs, and provider factory not being called.

---

### `tests/test_adaptive_attacker.py` (test, fake-provider request-response/state validation)

**Analog:** `tests/test_revision_run_contract.py`

**Fake provider pattern** (`tests/test_revision_run_contract.py` lines 11-20):
```python
class FakeProvider:
    def __init__(self, events: list[str] | None = None) -> None:
        self.events = events

    def infer(self, **kwargs):
        return (
            '{"answer_type":"number","value":3}',
            {"answer_type": "number", "value": 3},
            {"e2e_ms": 12.0, "ttft_ms": 3.0, "tokens_in": 10, "tokens_out": 5},
        )
```

**Task monkeypatch pattern** (`tests/test_revision_run_contract.py` lines 45-54, 71-77):
```python
def _patch_single_task(monkeypatch) -> None:
    task = run_eval.TaskItem(
        type="Dice_Count",
        puzzle_id="dice1.png",
        prompt="Count the dice.",
        images=[],
        gt={"sum": 3},
    )
    monkeypatch.setattr(run_eval, "build_tasks", lambda *args, **kwargs: [task])

def fake_make_provider(*args, **kwargs):
    if events is not None:
        events.append("provider")
    return FakeProvider(events)

monkeypatch.setattr(run_eval, "make_provider", fake_make_provider)
```

**Ordering pattern** (`tests/test_revision_run_contract.py` lines 141-167):
```python
events: list[str] = []
original_manifest = RevisionArtifactWriter.write_manifest
original_attempt = RevisionArtifactWriter.append_attempt
original_summary = RevisionArtifactWriter.write_summaries_from_attempts

def record_manifest(self, manifest):
    events.append("manifest")
    assert manifest.cost_control["expected_request_count"] == 1
    return original_manifest(self, manifest)

def record_attempt(self, attempt):
    events.append("attempt")
    return original_attempt(self, attempt)

def record_summary(self):
    events.append("summary")
    return original_summary(self)

assert events == ["manifest", "provider", "attempt", "summary"]
```

**Resume/skip pattern** (`tests/test_revision_run_contract.py` lines 205-234):
```python
def fail_provider(*args, **kwargs):
    raise AssertionError("resume should skip completed attempts before provider construction")

monkeypatch.setattr(run_eval, "make_provider", fail_provider)
run_eval.run_eval(..., resume_revision_output=True)

attempts = (run_dir / "attempts.jsonl").read_text(encoding="utf-8").splitlines()
summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))

assert len(attempts) == 1
assert summary["rows"][0]["n_attempts"] == 1
```

**Apply as:** Cover memory update after failed attempts, no ground-truth leakage into reflection prompts, without-replacement sampling, stop on first success, stop on budget, stop on pool exhaustion, infrastructure/protocol/scientific failure separation, append-before-summary ordering, and resume behavior.

---

### `tests/test_adaptive_compare.py` (test, CSV merge/pure transform)

**Analogs:** `exp2_to_exp3_predict.py`, `tests/test_scoring_regressions.py`

**Pure assertion pattern** (`tests/test_scoring_regressions.py` lines 28-39):
```python
task = run_eval.TaskItem(
    type="Path_Finder",
    puzzle_id="path1.json",
    prompt="choose the path",
    images=[],
    gt={"correct_index": 2},
)

assert run_eval.evaluate_pass1(task, {"answer_type": "classify", "index": 2})
assert not run_eval.evaluate_pass1(task, {"answer_type": "classify", "index": 1})
```

**Temp CSV assertion pattern** (`tests/test_scoring_regressions.py` lines 60-94):
```python
summary_csv = tmp_path / "summary.csv"
run_eval.run_eval(..., summary_csv=str(summary_csv))

with summary_csv.open("r", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))
assert [row["type"] for row in rows] == ["Dice_Count", "Patch_Select"]
```

**Apply as:** Build minimal legacy `results/exp2/<provider>/<model>/results.csv`, `results/exp3/<provider>/<model>/results.csv`, and adaptive summary fixtures under `tmp_path`. Assert Bernoulli `success_at_k` equals `predict_q_from_exp2()`, missing fixed retry rows remain nullable, classification labels honor cutoff/margin, bottleneck tags are task-type-first, and CSV/JSON outputs contain the explicit cutoff note.

## Shared Patterns

### Import Safety and CLI Guards

**Sources:** `revision_preflight.py` lines 230-245; `exp2_to_exp3_predict.py` lines 319-326.

**Apply to:** `adaptive_preflight.py`, `adaptive_attacker.py`, `adaptive_compare.py`, all tests.

All new modules should define functions/classes at import time only. Provider construction, local config loading, paid calls, and writes belong inside explicit functions or `if __name__ == "__main__":` guarded CLI entry points.

### Secret Safety

**Source:** `revision_secrets.py` lines 9-17, 46-68.
```python
SECRET_KEY_FRAGMENTS = ("api_key", "access_token", "secret", "password", "token")
REDACTED = "<redacted>"

def redact_mapping(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[Any, Any] = {}
        for key, child in value.items():
            redacted[key] = REDACTED if _is_secret_key(key) else redact_mapping(child)
        return redacted
    if isinstance(value, list):
        return [redact_mapping(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value
```

**Apply to:** Manifest metadata, preflight reports, adaptive attempts, adaptive summaries, comparison outputs, logs, and tests. Never read, print, quote, summarize, or persist credential values from `secrets.yaml`.

### Offline Dataset Boundary

**Sources:** `AGENTS.md` lines 32-40; `02-CONTEXT.md` lines 9-11.

**Apply to:** Entire Phase 2. Keep the adaptive attacker offline and dataset-based. Do not add browser automation, live service automation, provider-native memory, or hidden sessions.

### Binary Feedback and Memory Semantics

**Sources:** `02-CONTEXT.md` lines 18-24; `02-RESEARCH.md` lines 210-217.

**Apply to:** `adaptive_attacker.py`, `adaptive_artifacts.py`, `tests/test_adaptive_attacker.py`.

Persistent memory stores structured policy notes only: failed-attempt counts, tried strategy summaries, and next prompt rules. It must not store full prompt/response transcripts, ground truth, instance answers, coordinates, counts, categories, or corrective hints. Reflection inputs are limited to current prompt, own raw/parsed answer, and binary fail feedback.

### Failure Class Separation

**Sources:** `02-CONTEXT.md` lines 25-32; `run_eval.py` lines 2868-2872; `run_eval.py` lines 3252-3256.

**Apply to:** Adaptive attempts, summaries, comparison rows, tests.

Use separate classes such as `scientific_wrong`, `protocol_failure`, and `infrastructure_failure`. Provider/runtime failures must be visible in artifacts but excluded from main structural robustness conclusions.

### Same Budget Comparison

**Sources:** `02-CONTEXT.md` lines 25-36; `exp2_to_exp3_predict.py` lines 105-155.

**Apply to:** `adaptive_preflight.py`, `adaptive_attacker.py`, `adaptive_compare.py`.

The primary comparison unit is task type. Fixed retry, Bernoulli Success@k, and adaptive observed outcomes use the same solve attempt budget `k`. Reflection calls should be counted separately in request/cost/latency metadata.

### File I/O

**Sources:** `revision_artifacts.py` lines 212-227, 263-280; `exp2_to_exp3_predict.py` lines 319-322.

**Apply to:** All adaptive artifact writers and comparison outputs.

Create parent directories before writing, use UTF-8, use `newline=""` for CSV, write machine-readable JSON with indentation and a final newline, and append attempt records before derived summaries.

## No Analog Found

No file-level analog gaps were found. The following subpatterns have no exact existing implementation and need direct test coverage:

| Subpattern | Planned Location | Reason |
|------------|------------------|--------|
| Explicit adaptive policy memory | `adaptive_artifacts.py`, `adaptive_attacker.py` | Existing retry logic is stateless. |
| Binary-feedback-only self-reflection helper | `adaptive_attacker.py` | Existing provider calls solve CAPTCHA tasks only. |
| Without-replacement adaptive session sampling | `adaptive_attacker.py` | `run_until_type_correct()` samples with `random.choice()`. |
| Hard/borderline/broken adaptive classification change | `adaptive_compare.py` | Existing visualizer uses a 40 percent threshold but not Phase 2 labels. |

## Metadata

**Analog search scope:** Root-level Python scripts, `tests/`, prior Phase 1 pattern map, Phase 2 context/research docs, and project instructions.

**Files scanned:** `AGENTS.md`, `02-CONTEXT.md`, `02-RESEARCH.md`, `01-PATTERNS.md`, `revision_artifacts.py`, `revision_preflight.py`, `revision_secrets.py`, `run_eval.py`, `exp2_to_exp3_predict.py`, `visualize_results.py`, `tests/test_revision_artifacts.py`, `tests/test_revision_preflight.py`, `tests/test_revision_run_contract.py`, `tests/test_scoring_regressions.py`.

**Pattern extraction date:** 2026-05-18

**Sensitive-source handling:** Did not read or quote `secrets.yaml`. Did not include credential values. Pattern map preserves the project rule that generated planning docs remain English.
