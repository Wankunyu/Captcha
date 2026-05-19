# Phase 03: Dataset Scope, Statistical Confidence, and Limitations - Pattern Map

**Mapped:** 2026-05-19
**Files analyzed:** 13 planned new/modified implementation surfaces
**Analogs found:** 13 / 13

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `dataset_scope_audit.py` | utility / CLI analysis | file-I/O, batch transform | `revision_preflight.py` + `tests/test_task_contracts.py` | role-match |
| `statistical_confidence.py` | utility / CLI analysis | file-I/O, batch transform | `adaptive_compare.py` + `adaptive_artifacts.py` | role-match |
| `retry_calibration.py` | utility / CLI analysis | file-I/O, batch transform | `adaptive_compare.py` + `exp2_to_exp3_predict.py` | exact |
| `limitations_summary.py` | utility / prose generator | file-I/O, transform | `adaptive_compare.py` + `revision_artifacts.py` | role-match |
| `phase3_artifacts.py` | model / utility | serialization, file-I/O | `adaptive_artifacts.py` + `revision_artifacts.py` | exact |
| `adaptive_compare.py` | utility / CLI analysis | file-I/O, batch transform | `adaptive_compare.py` | exact |
| `exp2_to_exp3_predict.py` | utility / math helper CLI | file-I/O, batch transform | `exp2_to_exp3_predict.py` | exact |
| `visualize_results.py` | utility / result loader | file-I/O, batch transform | `visualize_results.py` | exact |
| `tests/test_dataset_scope_audit.py` | test | file-I/O, regression | `tests/test_revision_preflight.py` + `tests/test_task_contracts.py` | role-match |
| `tests/test_statistical_confidence.py` | test | transform, math regression | `tests/test_adaptive_compare.py` | role-match |
| `tests/test_retry_calibration.py` | test | file-I/O, join regression | `tests/test_adaptive_compare.py` | exact |
| `tests/test_limitations_summary.py` | test | file-I/O, prose regression | `tests/test_adaptive_compare.py` + `tests/test_revision_artifacts.py` | role-match |
| `tests/test_phase3_artifacts.py` | test | serialization regression | `tests/test_adaptive_artifacts.py` + `tests/test_revision_artifacts.py` | exact |

## Pattern Assignments

### `dataset_scope_audit.py` (utility / CLI analysis, file-I/O + batch transform)

**Analog:** `revision_preflight.py`, with registry checks from `tests/test_task_contracts.py` and task constants from `run_eval.py`.

**Imports pattern** (`revision_preflight.py` lines 1-11):
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
```

**Registry and alias source** (`run_eval.py` lines 1377-1402):
```python
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

**Dataset validation pattern** (`revision_preflight.py` lines 89-109):
```python
def _load_ground_truth(path: Path) -> dict[str, Any] | list[Any]:
    if not path.exists():
        raise FileNotFoundError(f"ground_truth.json does not exist: {path}")
    raw = path.read_text(encoding="utf-8")
    if raw.strip().startswith("version https://git-lfs.github.com/spec/v1"):
        raise RuntimeError(f"{path} is a Git LFS pointer; materialize dataset files first")
    payload = json.loads(raw)
    if not isinstance(payload, (dict, list)) or not payload:
        raise ValueError(f"ground_truth.json must be a non-empty list or mapping: {path}")
    return payload

def _canonical_task_type(task_type: str) -> str:
    canonical = TASK_ALIASES.get(task_type, task_type)
    if canonical not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported task type: {task_type}")
    return canonical
```

**Contract-test pattern** (`tests/test_task_contracts.py` lines 16-29, 42-67):
```python
def test_supported_types_have_dataset_directories() -> None:
    missing = []
    for task_type in sorted(SUPPORTED_TYPES):
        dataset_dir = Path("captcha_data") / DATASET_DIR_ALIASES.get(task_type, task_type)
        if not dataset_dir.is_dir():
            missing.append((task_type, str(dataset_dir)))

    assert not missing

def test_prompt_keys_are_known() -> None:
    with open("prompts_optimized.yaml", "r", encoding="utf-8") as handle:
        prompts = yaml.safe_load(handle) or {}
```

**Apply to Phase 3:**
- Build rows from `captcha_data/*/ground_truth.json`, `SUPPORTED_TYPES`, `TASK_ALIASES`, `DATASET_DIR_ALIASES`, prompt keys, few-shot keys, and result coverage.
- Treat `Hold_Button(Not Used)` and `Slide_Puzzle(Not Used)` as excluded/incompatible dataset directories, not supported task types.
- Include separate fields for `dataset_sample_count`, `evaluated_n_by_experiment`, `support_status`, `underpowered`, `pipeline_compatibility`, and `reason`.
- Do not import provider constructors or read `secrets.yaml`.

---

### `statistical_confidence.py` (utility / CLI analysis, file-I/O + batch transform)

**Analog:** `adaptive_compare.py` for result loading, threshold labels, CLI shape, and writers; `adaptive_artifacts.py` for Pydantic row schemas.

**Imports and local dependencies** (`adaptive_compare.py` lines 1-18):
```python
from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from adaptive_artifacts import (
    ADAPTIVE_COMPARISON_SCHEMA_VERSION,
    AdaptiveComparisonRow,
)
from exp2_to_exp3_predict import predict_A_from_exp2, predict_q_from_exp2
from visualize_results import CAPTCHAVisualizer
```

**Threshold label pattern** (`adaptive_compare.py` lines 104-116):
```python
def classify_rate(
    rate: float | None, *, cutoff: float = 0.40, margin: float = 0.0
) -> str | None:
    if rate is None:
        return None
    if margin < 0:
        raise ValueError("margin must be non-negative")
    epsilon = 1e-12
    if rate < cutoff - margin - epsilon:
        return "hard"
    if rate <= cutoff + margin + epsilon:
        return "borderline"
    return "broken"
```

**Result normalization pattern** (`adaptive_compare.py` lines 405-416):
```python
def _normalize_exp2(df: pd.DataFrame) -> pd.DataFrame:
    exp2 = df[df["experiment"] == "exp2"].copy()
    if exp2.empty:
        return pd.DataFrame(columns=_LEGACY_COLUMNS[:6])
    if "n" not in exp2.columns:
        exp2["n"] = 1
    return exp2.groupby(
        ["provider", "model", "provider_model", "task_type"], as_index=False
    ).agg(
        exp2_n=("n", "max"),
        exp2_pass_at_1=("pass", "mean"),
    )
```

**Schema pattern** (`adaptive_artifacts.py` lines 169-197):
```python
class AdaptiveSummaryRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = ADAPTIVE_SUMMARY_SCHEMA_VERSION
    run_id: str
    provider: str
    model: str
    task_type: str
    attempt_budget_k: int = Field(ge=1)
    n_attempts: int = Field(ge=0)
    n_success: int = Field(ge=0)
    success_rate: float = Field(ge=0, le=1)
    scientific_wrong_count: int = Field(ge=0)
    protocol_failure_count: int = Field(ge=0)
    infrastructure_failure_count: int = Field(ge=0)
    confidence_interval_low: float | None = Field(default=None, ge=0, le=1)
    confidence_interval_high: float | None = Field(default=None, ge=0, le=1)
```

**Apply to Phase 3:**
- Add a local Wilson interval helper using `math.sqrt` and `statistics.NormalDist`; avoid new SciPy/statsmodels dependency.
- Emit both task-level and family-level rows.
- Preserve `classify_rate()` semantics but add Phase 3 fields: `margin_to_cutoff`, `in_30_50_review_band`, `ci_crosses_cutoff`, `trend_sensitive`, and `cutoff_note`.
- Default paper-facing output should foreground sample counts, underpowered flags, margins, and review-band flags; CI columns are appendix/backup evidence.

---

### `retry_calibration.py` (utility / CLI analysis, file-I/O + batch transform)

**Analog:** `adaptive_compare.py` and `exp2_to_exp3_predict.py`.

**Bernoulli formula source** (`exp2_to_exp3_predict.py` lines 105-155):
```python
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

def predict_A_from_exp2(
    p_hat: float,
    n: int,
    k: int,
    N_pool: Optional[int] = None,
    alpha0: float = 1.0,
    beta0: float = 1.0,
) -> float:
    p = float(np.clip(p_hat, 1e-9, 1.0 - 1e-9))
    if N_pool is not None:
        return expected_attempts_hypergeom(p, k, N_pool)
    if p <= 0:
        return float(k)
    return float((1.0 - (1.0 - p) ** k) / p)
```

**Legacy/adaptive join pattern** (`adaptive_compare.py` lines 147-168, 170-198):
```python
merged = legacy.merge(
    adaptive,
    on=["provider", "model", "task_type"],
    how="inner",
    suffixes=("", "_adaptive"),
)
if merged.empty:
    raise ValueError("No overlapping Exp2 and adaptive rows after filtering")

for record in merged.to_dict(orient="records"):
    exp2_n = _to_int(record.get("exp2_n"), default=0)
    exp2_pass_at_1 = _to_float_or_none(record.get("exp2_pass_at_1"))
    if exp2_pass_at_1 is not None:
        bernoulli_success = predict_q_from_exp2(exp2_pass_at_1, exp2_n, attempt_budget_k)
        bernoulli_attempts = predict_A_from_exp2(exp2_pass_at_1, exp2_n, attempt_budget_k)
```

**CSV/JSON writer pattern** (`adaptive_compare.py` lines 320-337, 507-533):
```python
def write_comparison(
    rows: list[AdaptiveComparisonRow],
    output_csv: str | Path,
    output_json: str | Path,
) -> tuple[Path, Path]:
    validated_rows = [
        row if isinstance(row, AdaptiveComparisonRow) else AdaptiveComparisonRow.model_validate(row)
        for row in rows
    ]
    csv_path = Path(output_csv)
    json_path = Path(output_json)
    _write_csv(csv_path, AdaptiveComparisonRow.model_fields, validated_rows)
    _write_json(
        json_path,
        ADAPTIVE_COMPARISON_SCHEMA_VERSION,
        [row.model_dump(mode="json") for row in validated_rows],
    )
    return csv_path, json_path
```

**Apply to Phase 3:**
- Join by `(provider, model, provider_model, task_type, attempt_budget_k)` where available; keep task type as primary unit.
- Add `task_family` from `CAPTCHAVisualizer.TASK_FAMILY`.
- Required fields: Exp2 `Pass@1`, `attempt_budget_k`, Bernoulli `Success@k`, observed fixed-retry success, observed adaptive-compatible success, signed error, absolute error, sample count, and failure counts.
- Include `raw_observed_rate` and `scientific_rate`; only compute `scientific_rate` when failure taxonomy fields are present.

---

### `limitations_summary.py` (utility / prose generator, file-I/O + transform)

**Analog:** `adaptive_compare.py` for cutoff caveat and machine-readable CLI summaries; `revision_artifacts.py` for revision-safe output directories.

**Cutoff caveat source** (`adaptive_compare.py` lines 21-25):
```python
CUTOFF_NOTE = (
    "40% working CAPTCHA threshold; not a universal security boundary. "
    "Threshold-sensitivity review is handled in Phase 3."
)
CI_NOT_APPLICABLE_REASON = "single adaptive session; repeated-run CI deferred to Phase 3"
```

**CLI summary pattern** (`adaptive_compare.py` lines 369-402):
```python
def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        rows = build_comparison_rows(...)
    except ValueError as exc:
        parser.error(str(exc))

    output_csv, output_json = write_comparison(...)
    print(
        json.dumps(
            {
                "row_count": len(rows),
                "output_csv": str(output_csv),
                "output_json": str(output_json),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0
```

**Run-dir safety pattern** (`revision_artifacts.py` lines 152-162):
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

**Apply to Phase 3:**
- Read generated Phase 3 CSV/JSON artifacts, do not recompute unsupported science from aggregate-only sources.
- Output `limitations_summary.md` under `results/revision/<run_id>/`.
- Required prose boundaries: original vs supplemented vs new-category evidence; sample-size/underpowered caveats; incompatible removed task types; `40%` operational heuristic; failure taxonomy caveat; no population-level deployment estimate.
- Keep generated artifact text in English.

---

### `phase3_artifacts.py` (model / utility, serialization + file-I/O)

**Analog:** `adaptive_artifacts.py` for strict Pydantic schemas and CSV/JSON writers; `revision_artifacts.py` for simple revision run writers.

**Strict schema and validators pattern** (`adaptive_artifacts.py` lines 91-107, 154-159):
```python
class AdaptivePolicyState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = ADAPTIVE_POLICY_STATE_SCHEMA_VERSION
    task_type: str
    failed_attempt_count: int = Field(ge=0)
    tried_strategy_summaries: list[str] = Field(default_factory=list)
    next_prompt_rules: list[str] = Field(default_factory=list)
    updated_at: datetime

@field_validator("failure_class")
@classmethod
def validate_failure_class(cls, value: str) -> str:
    if value not in ALLOWED_FAILURE_CLASSES:
        raise ValueError(f"failure_class must be one of {sorted(ALLOWED_FAILURE_CLASSES)}")
    return value
```

**Generic writer pattern** (`adaptive_artifacts.py` lines 459-485):
```python
def _write_csv(
    path: Path,
    field_map: dict[str, Any],
    rows: Iterable[BaseModel],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(field_map)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.model_dump(mode="json"))

def _write_json(path: Path, schema_version: str, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump({"schema_version": schema_version, "rows": rows}, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
```

**Apply to Phase 3:**
- If shared schemas are useful, create Phase 3 row models here instead of expanding Phase 2 `AdaptiveComparisonRow`.
- Use `ConfigDict(extra="forbid")` for Phase 3 artifacts that become contract files.
- Recommended schemas: `DatasetScopeAuditRow`, `PassRateConfidenceRow`, `ThresholdSensitivityRow`, `RetryCalibrationRow`, `FailureTaxonomyRow`, and `ExtendedDatasetManifestRow`.

---

### `adaptive_compare.py` (existing utility / CLI analysis, file-I/O + batch transform)

**Analog:** self.

**Current comparison row construction** (`adaptive_compare.py` lines 170-269):
```python
n_success = _to_int(record.get("n_success"), default=0)
success_rate = _to_float_or_none(record.get("success_rate"))
adaptive_observed_success = n_success > 0 or bool(
    success_rate is not None and success_rate > 0
)
adaptive_success_at_k = 1.0 if adaptive_observed_success else 0.0
baseline_label = classify_rate(exp2_pass_at_1, cutoff=cutoff, margin=borderline_margin)
adaptive_label = classify_rate(adaptive_success_at_k, cutoff=cutoff, margin=borderline_margin)
...
scientific_wrong_count = _to_int(record.get("scientific_wrong_count"), default=0)
protocol_failure_count = _to_int(record.get("protocol_failure_count"), default=0)
infrastructure_failure_count = _to_int(record.get("infrastructure_failure_count"), default=0)
```

**Persistent-failure guard** (`adaptive_compare.py` lines 287-309):
```python
def _persistent_failure_note(
    *,
    adaptive_label: str | None,
    adaptive_observed_success: bool,
    scientific_wrong_count: int,
    protocol_failure_count: int,
    infrastructure_failure_count: int,
) -> str | None:
    if (
        adaptive_label == "hard"
        and adaptive_observed_success is False
        and scientific_wrong_count > 0
        and protocol_failure_count == 0
        and infrastructure_failure_count == 0
    ):
        return PERSISTENT_FAILURE_NOTE
```

**Apply to Phase 3:**
- Prefer complementing this file with `statistical_confidence.py` or `retry_calibration.py` rather than mutating verified Phase 2 schemas.
- If modifying this file, keep existing `classify_rate()` defaults and tests stable; add Phase 3 review-band logic as new helpers, not as a changed default label rule.

---

### `exp2_to_exp3_predict.py` (existing math helper CLI, file-I/O + batch transform)

**Analog:** self.

**CLI and result loading pattern** (`exp2_to_exp3_predict.py` lines 182-209):
```python
def main():
    ap = argparse.ArgumentParser(description="Predict Exp3 from Exp2 with bias corrections")
    ap.add_argument("--results-dir", default="./results", help="Root results directory")
    ap.add_argument("--output", default="./exp2_to_exp3_predictions.csv", help="Output CSV path")
    ap.add_argument("--k", type=int, default=10, help="Max attempts per type in Exp3")
    ...
    args = ap.parse_args()

    viz = CAPTCHAVisualizer(results_dir=args.results_dir)
    if viz.data.empty:
        raise SystemExit("No results found under --results-dir")
```

**Output pattern** (`exp2_to_exp3_predict.py` lines 319-322):
```python
out_path = Path(args.output)
out_path.parent.mkdir(parents=True, exist_ok=True)
pred_df.to_csv(out_path, index=False)
print(f"[SAVED] Predictions -> {out_path}")
```

**Apply to Phase 3:**
- Reuse formulas directly from this file.
- If keeping this script unchanged, import formulas into `retry_calibration.py`.
- If extending it, avoid changing existing output column names without preserving backwards compatibility.

---

### `visualize_results.py` (existing result loader and family metadata, file-I/O + batch transform)

**Analog:** self.

**Family map source** (`visualize_results.py` lines 46-68):
```python
TASK_FAMILY = {
    'Dice_Count': 'Click/Coordinate',
    'Click_Order': 'Click/Coordinate',
    'Place_Dot': 'Click/Coordinate',
    'Geometry_Click': 'Click/Coordinate',
    'Pick_Area': 'Click/Coordinate',
    'Misleading_Click': 'Click/Coordinate',
    ...
    'Coordinates': 'Logic/Reasoning',
    'Connect_Icon': 'Logic/Reasoning',
}
```

**Result loader pattern** (`visualize_results.py` lines 147-234):
```python
def _load_all_data(self) -> pd.DataFrame:
    all_results = []
    for csv_file in self.results_dir.rglob("results.csv"):
        try:
            parts = csv_file.relative_to(self.results_dir).parts
            if len(parts) >= 3:
                experiment = parts[0]
                provider = parts[1]
                model = parts[2]
                df = pd.read_csv(csv_file)
                ...
                df['provider_model'] = f"{provider}/{model}"
                all_results.append(df)
        except Exception as e:
            print(f"[SKIP] File {csv_file}: {e}")
```

**40 percent legacy figure convention** (`visualize_results.py` lines 898-943):
```python
def generate_captcha_recommendation(self, experiment: str = 'exp2',
                                   threshold: float = 40.0,
                                   top_n: int = 8) -> pd.DataFrame:
    ...
    stats = df.groupby('task_type').agg({
        'pass': ['mean', 'std', 'count']
    }).round(4)
    stats.columns = ['avg_pass@1', 'std_pass@1', 'n_models']
    ...
    difficult_tasks = stats[stats['avg_pass@1'] < threshold].copy()
```

**Apply to Phase 3:**
- Use `CAPTCHAVisualizer.TASK_FAMILY` as seed family metadata.
- Phase 3 loaders should explicitly filter `exp1`, `exp2`, `exp3`, `exp4`, and revision-run artifacts; do not blindly treat every nested `results.csv` as a scientific experiment.
- Do not overwrite existing figure semantics while adding threshold-sensitivity tables.

## Test Pattern Assignments

### `tests/test_dataset_scope_audit.py`

**Analogs:** `tests/test_revision_preflight.py` and `tests/test_task_contracts.py`.

**Fixture/write helpers** (`tests/test_revision_preflight.py` lines 11-24):
```python
def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")

def _dataset_root(tmp_path: Path) -> Path:
    root = tmp_path / "captcha_data"
    _write_json(root / "Dice_Count" / "ground_truth.json", {"dice1.png": {"answer": 3}})
    _write_json(root / "Connect_icon" / "ground_truth.json", {"puzzle1.json": {"choice": 0}})
    return root
```

**Coverage target:** dataset directory status, alias canonicalization, not-used incompatible rows, underpowered flag threshold, prompt/few-shot unknown-key checks, and no provider construction.

### `tests/test_statistical_confidence.py`

**Analog:** `tests/test_adaptive_compare.py`.

**Threshold tests** (`tests/test_adaptive_compare.py` lines 283-299):
```python
def test_classify_rate_uses_paper_cutoff_by_default() -> None:
    assert classify_rate(None) is None
    assert classify_rate(0.39) == "hard"
    assert classify_rate(0.40) == "borderline"
    assert classify_rate(0.41) == "broken"

def test_classify_rate_allows_explicit_margin_for_sensitivity_checks() -> None:
    assert classify_rate(0.34, margin=0.05) == "hard"
    assert classify_rate(0.35, margin=0.05) == "borderline"
```

**Coverage target:** Wilson interval edge cases (`n=0`, `successes=0`, `successes=n`), review band `0.30 <= rate <= 0.50`, margin-to-cutoff signs, CI-crosses-cutoff, family aggregation, and trend-sensitive flag inputs.

### `tests/test_retry_calibration.py`

**Analog:** `tests/test_adaptive_compare.py`.

**Synthetic CSV setup** (`tests/test_adaptive_compare.py` lines 20-50, 53-85):
```python
def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def _write_legacy_results(results_dir: Path) -> None:
    _write_csv(
        results_dir / "exp2" / "openai" / "gpt-5" / "results.csv",
        [{"type": "Dice_Count", "n": 4, "pass_at_1": 0.25}],
    )
```

**Coverage target:** Exp2 formula reuse, Exp3 observed joins, adaptive-compatible observed joins, signed/absolute error, task family inclusion, aggregate-only failure taxonomy caveats, CLI writes both CSV and JSON.

### `tests/test_limitations_summary.py`

**Analogs:** `tests/test_adaptive_compare.py` CLI tests and `tests/test_revision_artifacts.py` JSON/CSV checks.

**CLI output check** (`tests/test_adaptive_compare.py` lines 395-448):
```python
exit_code = main([...])

summary = json.loads(capsys.readouterr().out)
assert exit_code == 0
assert summary["row_count"] == 5
assert summary["output_csv"].endswith("adaptive_comparison.csv")
assert output_csv.exists()
assert output_json.exists()
```

**Coverage target:** generated Markdown contains required caveats and excludes unsupported claims. Check for artifact paths and key phrases, not brittle full-prose equality.

### `tests/test_phase3_artifacts.py`

**Analogs:** `tests/test_adaptive_artifacts.py` and `tests/test_revision_artifacts.py`.

**Schema/write checks** (`tests/test_adaptive_artifacts.py` lines 90-188, 334-361):
```python
def test_adaptive_models_expose_schema_versions_and_modes() -> None:
    ...
    assert before.schema_version == ADAPTIVE_POLICY_STATE_SCHEMA_VERSION
    assert attempt.schema_version == ADAPTIVE_ATTEMPT_SCHEMA_VERSION
    assert summary.schema_version == ADAPTIVE_SUMMARY_SCHEMA_VERSION
    assert comparison.schema_version == ADAPTIVE_COMPARISON_SCHEMA_VERSION

csv_path, json_path = writer.write_summary_from_attempts()
assert csv_path.name == "adaptive_summary.csv"
assert json_path.name == "adaptive_summary.json"
```

**Coverage target:** Phase 3 schema versions, `extra="forbid"`, field bounds, CSV/JSON row parity, output path creation, and secret-safe fields only.

## Shared Patterns

### Offline and Secret-Safe Execution

**Source:** `tests/test_revision_preflight.py` lines 100-112.

```python
def test_preflight_never_calls_provider_factory(tmp_path, monkeypatch, capsys) -> None:
    import run_eval

    def fail(*args, **kwargs):
        raise AssertionError("preflight must not construct providers")

    monkeypatch.setattr(run_eval, "make_provider", fail)

    main(_base_args(tmp_path, run_id="offline-only"))
```

**Apply to:** all Phase 3 CLIs and tests.

Never read, print, copy, summarize, or validate values from `secrets.yaml`. Phase 3 scripts should consume local datasets and generated results only.

### Revision Output Paths

**Source:** `revision_artifacts.py` lines 165-218.

```python
class RevisionArtifactWriter:
    def __init__(..., overwrite: bool = False, resume: bool = False) -> None:
        if overwrite and resume:
            raise ValueError("overwrite and resume are mutually exclusive")
        self._run_dir = revision_run_dir(output_root, run_id)
        if self._run_dir.exists() and not overwrite and not resume:
            raise FileExistsError(f"Revision run directory already exists: {self._run_dir}")
        ...

    def write_manifest(self, manifest: RunManifest) -> Path:
        payload = manifest.model_dump(mode="json")
        payload["output_paths"] = payload.get("output_paths") or self.output_paths()
```

**Apply to:** `phase3_artifacts.py`, `dataset_scope_audit.py`, `statistical_confidence.py`, `retry_calibration.py`, and `limitations_summary.py`.

### Failure Taxonomy

**Source:** `adaptive_artifacts.py` lines 22-27, 107-159, 390-398.

```python
ALLOWED_FAILURE_CLASSES = {
    "scientific_wrong",
    "protocol_failure",
    "infrastructure_failure",
    "none",
}

class AdaptiveAttemptRecord(BaseModel):
    ...
    correct: bool
    failure_class: str

@field_validator("failure_class")
@classmethod
def validate_failure_class(cls, value: str) -> str:
    if value not in ALLOWED_FAILURE_CLASSES:
        raise ValueError(f"failure_class must be one of {sorted(ALLOWED_FAILURE_CLASSES)}")
    return value
```

**Apply to:** `retry_calibration.py`, `statistical_confidence.py`, `limitations_summary.py`, and related tests.

When failure classes are unavailable in legacy aggregate CSVs, mark them as aggregate-only/unknown rather than inventing scientific/protocol/infrastructure counts.

### Result Family Metadata

**Source:** `visualize_results.py` lines 46-68.

Use `CAPTCHAVisualizer.TASK_FAMILY` as the default family map. Any Phase 3 refinements for extended categories must be written into output metadata so the paper can distinguish original, supplemented, and new-category evidence.

### CLI Error Handling

**Source:** `adaptive_compare.py` lines 369-384 and `revision_preflight.py` lines 230-241.

Use `parser.error(str(exc))` for user-correctable CLI validation errors when the script has an `argparse` parser, and use `SystemExit(str(exc))` only for simpler CLIs that already follow that style.

## No Analog Found

No planned Phase 3 file lacks a usable analog. `limitations_summary.py` has no exact Markdown prose-generator analog, but `adaptive_compare.py` and `revision_artifacts.py` provide the relevant CLI, caveat, output-path, and writer patterns.

## Metadata

**Analog search scope:** root-level Python modules, `tests/`, and `.planning/codebase/` maps. `secrets.yaml` was not read.

**Files scanned:** 29 Python/test files via `rg --files`; 11 analog/source files read for concrete patterns.

**Primary analog files read:**
- `revision_artifacts.py`
- `revision_preflight.py`
- `adaptive_artifacts.py`
- `adaptive_compare.py`
- `exp2_to_exp3_predict.py`
- `visualize_results.py`
- targeted non-overlapping ranges from `run_eval.py`
- `tests/test_revision_preflight.py`
- `tests/test_task_contracts.py`
- `tests/test_adaptive_compare.py`
- `tests/test_adaptive_artifacts.py`
- `tests/test_revision_artifacts.py`

**Pattern extraction date:** 2026-05-19
