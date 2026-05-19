# Phase 4: SOTA Solver and Larger Benchmark Strengthening - Pattern Map

**Mapped:** 2026-05-19
**Files analyzed:** 4
**Analogs found:** 4 / 4

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `phase4_artifacts.py` | model, utility | validation, transform, file-I/O | `phase3_artifacts.py` | exact |
| `baseline_strengthening.py` | CLI, service | batch, file-I/O, transform | `extended_dataset_manifest.py` | role-match |
| `tests/test_phase4_artifacts.py` | test | validation, file-I/O | `tests/test_phase3_artifacts.py` | exact |
| `tests/test_baseline_strengthening.py` | test | fixture-driven file-I/O, CLI request-response | `tests/test_extended_dataset_manifest.py` | role-match |

Planner note: research mentions README/reproduction concerns only as generated Phase 4 outputs and source citations. No repository README or reproduction-doc source file is plan-relevant unless execution later changes user-facing commands.

## Pattern Assignments

### `phase4_artifacts.py` (model, utility; validation, transform, file-I/O)

**Analog:** `phase3_artifacts.py`

**Imports pattern** (lines 1-7):

```python
import csv
import json
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field, field_validator
```

Apply this directly. Phase 4 should not import the Phase 3 row classes; define independent schema constants and models in `phase4_artifacts.py`.

**Schema constant and enum pattern** (lines 9-18, 19-60):

```python
DATASET_SCOPE_SCHEMA_VERSION = "cognition.revision.dataset_scope_audit.v1"
EXTENDED_DATASET_MANIFEST_SCHEMA_VERSION = "cognition.revision.extended_dataset_manifest.v1"
RETRY_CALIBRATION_SCHEMA_VERSION = "cognition.revision.retry_calibration.v1"
FAILURE_TAXONOMY_SCHEMA_VERSION = "cognition.revision.failure_taxonomy.v1"

ALLOWED_SCOPE_STATUSES = {"included", "excluded", "incompatible", "underpowered"}
ALLOWED_CLAIM_USES = {
    "scientific_claim_eligible",
    "infrastructure_caveated",
    "protocol_caveated",
    "aggregate_only_caveated",
}
```

Copy this shape with Phase 4 constants such as:

- `BASELINE_COVERAGE_SCHEMA_VERSION = "cognition.revision.baseline_coverage.v1"`
- `EXTERNAL_IMPORT_VALIDATION_SCHEMA_VERSION = "cognition.revision.external_import_validation.v1"`
- `BASELINE_COMPARISON_SCHEMA_VERSION = "cognition.revision.baseline_comparison.v1"`
- `PAPER_BASELINE_TABLE_SCHEMA_VERSION = "cognition.revision.paper_baseline_table.v1"`

Use locked status/caveat/system-class vocabularies from `04-CONTEXT.md`: `direct-run`, `adapter-run`, `literature-only`, `approximate`, `incompatible`, `unavailable`; caveats such as `metric-mismatch`, `dataset-mismatch`, `threat-model-mismatch`, `artifact-unavailable`, `license-unclear`; classes such as `off_the_shelf_mllm_api`, `specialized_solver`, `benchmark_dataset`, `hybrid_or_unknown`.

**Validation helper pattern** (lines 62-65):

```python
def _validate_allowed(value: str, allowed: set[str], field_name: str) -> str:
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {sorted(allowed)}")
    return value
```

Use this for Phase 4 enum fields rather than repeating custom validation logic in every model.

**Strict row model pattern** (lines 74-124):

```python
class DatasetScopeAuditRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = DATASET_SCOPE_SCHEMA_VERSION
    run_id: str
    task_type: str
    task_family: str
    dataset_dir: str
    scope_status: str
    support_status: str
    pipeline_compatibility: str
    dataset_sample_count: int = Field(ge=0)

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        return _validate_allowed(value, {DATASET_SCOPE_SCHEMA_VERSION}, "schema_version")

    @field_validator("scope_status")
    @classmethod
    def validate_scope_status(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_SCOPE_STATUSES, "scope_status")
```

Use `ConfigDict(extra="forbid")` on every Phase 4 row. For fields that affect paper claims, prefer explicit required strings over implicit nulls. Required Phase 4 rows should include:

- `BaselineCoverageRow`: source/system metadata, `primary_status`, caveat tags, task-family mapping, artifact/license/data-use fields, `status_reason`, checked sources, missing items, last checked date.
- `ExternalImportValidationRow`: required-field, metric-definition, task-label, sample-count, artifact/license/data-use, and comparability validation statuses.
- `BaselineComparisonRow`: source-preserving reported metric fields plus `normalized_success_rate` only when validated.
- `PaperBaselineRow`: paper-visible fields including `system_class`, `primary_status`, `directly_comparable`, `comparability_caveat`, original metric fields, normalized metric fields, and source/status notes.

**Nullable metric pattern** (lines 182-199, 286-312):

```python
class ExtendedValidationComparisonRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original_rate: float | None = Field(default=None, ge=0, le=1)
    validation_slice_rate: float | None = Field(default=None, ge=0, le=1)
    validation_sample_count: int = Field(ge=0)
    agreement_status: str
    divergence_reason: str
    comparison_caveat: str
    outcome_source_path: str
```

```python
class RetryCalibrationRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exp2_pass_at_1: float | None = Field(default=None, ge=0, le=1)
    bernoulli_success_at_k: float | None = Field(default=None, ge=0, le=1)
    observed_fixed_retry_success: float | None = Field(default=None, ge=0, le=1)
    observed_adaptive_compatible_success: float | None = Field(default=None, ge=0, le=1)
    raw_observed_rate: float | None = Field(default=None, ge=0, le=1)
    scientific_rate: float | None = Field(default=None, ge=0, le=1)
```

Use this for Phase 4 reported and normalized metric fields. Do not force `normalized_success_rate` when standardization is unvalidated.

**CSV/JSON writer pattern** (lines 68-71, 352-382):

```python
def _row_to_json_dict(row: BaseModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(row, BaseModel):
        return row.model_dump(mode="json")
    return row


def write_csv(
    path: Path,
    field_map: dict[str, Any],
    rows: Iterable[BaseModel | dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(field_map)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(_row_to_json_dict(row))


def write_json(
    path: Path,
    schema_version: str,
    rows: Iterable[BaseModel | dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "schema_version": schema_version,
                "rows": [_row_to_json_dict(row) for row in rows],
            },
            handle,
            indent=2,
            ensure_ascii=False,
        )
        handle.write("\n")
```

Copy these helpers or keep equivalent local helpers in `phase4_artifacts.py`. Add thin `write_baseline_coverage`, `write_external_import_validation`, `write_baseline_comparison`, and `write_paper_baseline_table` wrappers that pass the right model fields and schema version.

---

### `baseline_strengthening.py` (CLI, service; batch, file-I/O, transform)

**Primary analog:** `extended_dataset_manifest.py`

**Secondary analogs:** `dataset_scope_audit.py`, `retry_calibration.py`, `failure_taxonomy.py`, `limitations_summary.py`, `revision_artifacts.py`

**Imports pattern** (extended_dataset_manifest.py lines 1-21):

```python
import argparse
import csv
import json
from pathlib import Path
from typing import Any

from phase3_artifacts import (
    EXTENDED_DATASET_MANIFEST_SCHEMA_VERSION,
    EXTENDED_VALIDATION_COMPARISON_SCHEMA_VERSION,
    ExtendedDatasetManifestRow,
    ExtendedValidationComparisonRow,
    write_csv,
    write_json,
)
from revision_artifacts import revision_run_dir
```

For Phase 4, import `phase4_artifacts` row classes and writer wrappers, and always reuse `revision_run_dir`.

**Input table loader pattern** (extended_dataset_manifest.py lines 53-71):

```python
def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_table(path: Path | None) -> list[dict[str, object]]:
    if path is None:
        return []
    if path.suffix.lower() == ".json":
        payload = _read_json(path)
        if isinstance(payload, dict):
            rows = payload.get("rows", [])
        else:
            rows = payload
        if not isinstance(rows, list):
            raise ValueError(f"Expected rows array in {path}")
        return [dict(row) for row in rows if isinstance(row, dict)]
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]
```

Use this for curated baseline metadata, imported Halligan/Oedipus/literature rows, and comparison inputs. Do not read `secrets.yaml`.

**Manifest validation pattern** (extended_dataset_manifest.py lines 102-137):

```python
def load_extended_dataset_manifest(
    path: Path,
    run_id: str,
) -> list[ExtendedDatasetManifestRow]:
    payload = _read_json(path)
    if isinstance(payload, list):
        raw_rows = payload
        new_category_limitation = ""
    elif isinstance(payload, dict):
        raw_rows = payload.get("rows")
        new_category_limitation = str(payload.get("new_category_limitation") or "")
    else:
        raise ValueError("input manifest must be a JSON object or array")
    if not isinstance(raw_rows, list):
        raise ValueError("input manifest must contain a rows array")

    rows = [
        ExtendedDatasetManifestRow.model_validate({**dict(row), "run_id": run_id})
        for row in raw_rows
        if isinstance(row, dict)
    ]
    if not any(row.slice_type == "supplement_existing" for row in rows):
        raise ValueError("manifest must include at least one supplement_existing row")
    new_category_count = sum(row.slice_type == "new_category" for row in rows)
    if new_category_count < 1:
        raise ValueError("manifest must include at least one new_category row")
```

Apply this to `load_baseline_coverage_sources` and `load_external_import_rows`. Phase 4-specific validations should enforce:

- Halligan and Oedipus appear in coverage rows.
- Every coverage row has one `primary_status`.
- `unavailable` and `incompatible` rows include `status_reason`, checked docs/artifacts, missing items, and last-checked date.
- Direct/adapter rows require license and data-use terms.
- Literature-only rows preserve source URL and reported metric provenance.

**Coverage/incompatibility row construction pattern** (dataset_scope_audit.py lines 176-212, 215-243):

```python
def _removed_row(
    *,
    run_id: str,
    task_type: str,
    dataset_sample_count: int,
    underpowered_n: int,
) -> DatasetScopeAuditRow:
    if task_type == HOLD_BUTTON_TASK:
        compatibility = "incompatible_temporal_hold"
        reason = HOLD_BUTTON_REASON
    elif task_type == SLIDE_PUZZLE_TASK:
        compatibility = "incompatible_slider_drag"
        reason = SLIDE_PUZZLE_REASON
    else:
        raise ValueError(f"Unknown removed task type: {task_type}")
    return DatasetScopeAuditRow(
        run_id=run_id,
        task_type=task_type,
        task_family="Removed/Incompatible",
        scope_status="incompatible",
        support_status="removed_not_used",
        pipeline_compatibility=compatibility,
        reason=reason,
    )
```

```python
def _unsupported_row(
    *,
    run_id: str,
    task_type: str,
    dataset_sample_count: int,
    underpowered_n: int,
) -> DatasetScopeAuditRow:
    return DatasetScopeAuditRow(
        run_id=run_id,
        task_type=task_type,
        task_family="Unmapped",
        scope_status="excluded",
        support_status="unsupported",
        pipeline_compatibility="unknown",
        reason="unsupported dataset directory is not part of SUPPORTED_TYPES",
    )
```

Use this style for `unavailable`, `incompatible`, and `literature-only` baseline coverage rows. Keep the raw external label and status reason rather than silently dropping incompatible systems.

**Comparison row builder pattern** (extended_dataset_manifest.py lines 288-347):

```python
def build_extended_validation_comparison_rows(
    manifest_rows: list[ExtendedDatasetManifestRow],
    validation_outcomes: list[dict[str, object]],
    original_conclusions: list[dict[str, object]],
    run_id: str,
) -> list[ExtendedValidationComparisonRow]:
    if not validation_outcomes:
        return []
    manifest_by_source = _manifest_by_source(manifest_rows)
    original_by_task, original_by_family = _original_indexes(original_conclusions)
    rows: list[ExtendedValidationComparisonRow] = []
    for outcome in validation_outcomes:
        source_id = str(outcome.get("source_id") or "")
        manifest_row = manifest_by_source.get(source_id)
        if manifest_row is None:
            continue

        validation_sample_count, validation_slice_rate = _validation_rate(outcome)
        original = _find_original_conclusion(
            manifest_row.task_type,
            manifest_row.task_family,
            original_by_task,
            original_by_family,
        )
        status, reason = _comparison_status(
            manifest_row=manifest_row,
            validation_sample_count=validation_sample_count,
            original_direction=_direction(original_label, original_rate),
            validation_direction=_direction(None, validation_slice_rate),
        )
        rows.append(
            ExtendedValidationComparisonRow(
                run_id=run_id,
                source_id=manifest_row.source_id,
                evidence_origin=manifest_row.evidence_origin,
                slice_type=manifest_row.slice_type,
                task_type=manifest_row.task_type,
                task_family=manifest_row.task_family,
                agreement_status=status,
                divergence_reason=reason,
                comparison_caveat=COMPARISON_CAVEAT,
                outcome_source_path=str(outcome.get("outcome_source_path") or ""),
            )
        )
    return rows
```

Phase 4 should build comparison rows by joining coverage rows, import validation rows, optional local result rows, and literature metrics. The builder must preserve source labels and set `directly_comparable=false` unless metric definition, task mapping, sample count, artifact/license, and threat-model comparability pass validation.

**Metric and rate comparison pattern** (retry_calibration.py lines 256-354):

```python
def build_retry_calibration_rows(
    exp2_df: pd.DataFrame,
    fixed_retry_df: pd.DataFrame,
    adaptive_df: pd.DataFrame,
    *,
    run_id: str,
    attempt_budget_k: int,
) -> list[RetryCalibrationRow]:
    if attempt_budget_k < 1:
        raise ValueError("attempt_budget_k must be >= 1")
    if exp2_df.empty:
        return []

    merged = exp2_df.merge(
        fixed_retry_df,
        on=["provider", "model", "provider_model", "task_type"],
        how="left",
        suffixes=("", "_fixed"),
    )
    merged = merged.merge(
        adaptive_df,
        on=["provider", "model", "provider_model", "task_type"],
        how="left",
        suffixes=("", "_adaptive"),
    )

    rows: list[RetryCalibrationRow] = []
    for record in merged.to_dict(orient="records"):
        exp2_pass_at_1 = _to_float_or_none(record.get("exp2_pass_at_1"))
        observed_fixed = _to_float_or_none(record.get("observed_fixed_retry_success"))
        observed_adaptive = _to_float_or_none(
            record.get("observed_adaptive_compatible_success")
        )
        rows.append(
            RetryCalibrationRow(
                run_id=run_id,
                provider=str(record["provider"]),
                model=str(record["model"]),
                task_type=str(record["task_type"]),
                exp2_pass_at_1=exp2_pass_at_1,
                observed_fixed_retry_success=observed_fixed,
                observed_adaptive_compatible_success=observed_adaptive,
                comparison_contract=COMPARISON_CONTRACT,
            )
        )
    return rows
```

Use the same merge-first, then row-validate pattern for Phase 4 table generation. Do not calculate direct comparability from a single field.

**Caveat/claim-use pattern** (failure_taxonomy.py lines 20-30, 252-312):

```python
INFRASTRUCTURE_CAVEAT = (
    "infrastructure/provider failures are visible and are not counted as "
    "scientific evidence of structural robustness"
)
PROTOCOL_CAVEAT = (
    "protocol failures are visible and are not counted as scientific model failures"
)
AGGREGATE_ONLY_CAVEAT = (
    "aggregate-only source lacks failure classes; use for rate context, not "
    "failure-taxonomy claims"
)
```

```python
def _claim_use_and_caveat(
    *,
    protocol_failure_count: int,
    infrastructure_failure_count: int,
) -> tuple[str, str | None]:
    if infrastructure_failure_count > 0:
        return "infrastructure_caveated", INFRASTRUCTURE_CAVEAT
    if protocol_failure_count > 0:
        return "protocol_caveated", PROTOCOL_CAVEAT
    return "scientific_claim_eligible", None
```

Phase 4 equivalent should map validation and comparability outcomes into caveat fields, not into hidden planner prose. Paper rows must expose caveats.

**Paper notes generation pattern** (extended_dataset_manifest.py lines 360-416; limitations_summary.py lines 103-205):

```python
def write_dataset_contribution_notes(
    rows: list[ExtendedDatasetManifestRow],
    output_md: Path,
    dataset_scope_json: Path | None = None,
) -> Path:
    output_md.parent.mkdir(parents=True, exist_ok=True)
    row_lines = "\n".join(
        f"- `{row.source_id}` ({row.slice_type}, {row.task_type}): "
        f"{row.normalization_decisions}"
        for row in rows
    )
    content_lines = [
        "# Dataset Contribution Notes",
        "",
        "## Cleaning",
        "Ambiguous, incomplete, or non-static samples are excluded before validation-slice use.",
        row_lines,
        "",
        "## Standardization",
        "Rows are standardized into local manifest records with source ids, task types,",
        "task families, sample counts, source paths, compatibility status, and",
        "evaluation status.",
    ]
    content = "\n".join(content_lines) + "\n"
    output_md.write_text(content, encoding="utf-8")
    return output_md
```

```python
def render_limitations_summary(
    *,
    dataset_scope_rows: list[dict[str, object]],
    extended_manifest_rows: list[dict[str, object]],
    extended_validation_rows: list[dict[str, object]],
    contribution_notes_md: str,
    pass_rate_rows: list[dict[str, object]],
    threshold_rows: list[dict[str, object]],
    retry_rows: list[dict[str, object]],
    failure_rows: list[dict[str, object]],
) -> str:
    scope_counts = _counts_by(dataset_scope_rows, "scope_status")
    validation_counts = _counts_by(extended_validation_rows, "agreement_status")
    lines = [
        "# Phase 3 Dataset Scope, Statistical Confidence, And Limitations",
        "",
        "## Dataset Scope",
        DATASET_SCOPE_CAVEAT,
        _format_counts("Scope-status counts", scope_counts),
        "",
        "## Extended Validation Slice Comparison",
        VALIDATION_SLICE_CAVEAT,
        _format_counts("Agreement-status counts", validation_counts),
    ]
    return "\n".join(lines).rstrip() + "\n"
```

Use this for the `notes` subcommand. Phase 4 notes should summarize direct/adapter/literature-only rows, unavailable/incompatible rows, non-comparable rows, and approximate comparison basis. Keep it concise and generated from validated rows.

**CLI parser/main pattern** (extended_dataset_manifest.py lines 419-516; dataset_scope_audit.py lines 307-363):

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate an extended dataset manifest and write Phase 3 artifacts."
    )
    parser.add_argument("--input-manifest", required=True)
    parser.add_argument("--dataset-scope-json", default=None)
    parser.add_argument("--output-root", default="./results/revision")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-csv", default=None)
    parser.add_argument("--output-json", default=None)
    parser.add_argument("--notes-md", default=None)
    return parser
```

```python
def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        run_dir = revision_run_dir(args.output_root, args.run_id)
        output_csv = _path_or_default(
            args.output_csv, run_dir / "extended_dataset_manifest.csv"
        )
        output_json = _path_or_default(
            args.output_json, run_dir / "extended_dataset_manifest.json"
        )
        manifest_rows = load_extended_dataset_manifest(
            Path(args.input_manifest), run_id=args.run_id
        )
        output_csv, output_json = write_extended_dataset_manifest(
            manifest_rows, output_csv, output_json
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    print(
        json.dumps(
            {
                "row_count": len(manifest_rows),
                "output_csv": str(output_csv),
                "output_json": str(output_json),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0
```

No existing repo script uses `argparse.add_subparsers`, so Phase 4's central multi-command CLI has no exact subcommand analog. Use this thin parser/main/error-summary style, but implement stdlib subcommands:

- `coverage`
- `validate-import`
- `build-table`
- `notes`

Each subcommand should share `--output-root ./results/revision`, required `--run-id`, optional output overrides, and JSON stdout summaries.

**Run directory safety pattern** (revision_artifacts.py lines 152-162):

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

Always resolve default output files through this helper before writing. Tests should assert invalid run ids do not create output roots.

---

### `tests/test_phase4_artifacts.py` (test; validation, file-I/O)

**Analog:** `tests/test_phase3_artifacts.py`

**Imports and row factory pattern** (lines 1-24, 27-77):

```python
import csv
import json

import pytest
from pydantic import ValidationError

from phase3_artifacts import (
    DATASET_SCOPE_SCHEMA_VERSION,
    EXTENDED_DATASET_MANIFEST_SCHEMA_VERSION,
    DatasetScopeAuditRow,
    ExtendedDatasetManifestRow,
    write_csv,
    write_json,
)
```

```python
def _dataset_scope_row() -> DatasetScopeAuditRow:
    return DatasetScopeAuditRow(
        run_id="run-1",
        task_type="Dice_Count",
        task_family="Counting",
        dataset_dir="Dice_Count",
        scope_status="included",
        support_status="supported",
        pipeline_compatibility="compatible_static_answer",
        dataset_sample_count=25,
        reason="supported and evaluated",
    )
```

Create one valid fixture per Phase 4 row model: coverage, import validation, baseline comparison, paper baseline table.

**Schema version and enum tests** (lines 80-110, 113-141):

```python
def test_schema_versions_are_exact() -> None:
    assert DATASET_SCOPE_SCHEMA_VERSION == "cognition.revision.dataset_scope_audit.v1"
    assert (
        EXTENDED_DATASET_MANIFEST_SCHEMA_VERSION
        == "cognition.revision.extended_dataset_manifest.v1"
    )


def test_dataset_scope_model_forbids_extra_fields_and_rejects_unknown_enums() -> None:
    row = _dataset_scope_row()

    assert row.schema_version == DATASET_SCOPE_SCHEMA_VERSION
    with pytest.raises(ValidationError):
        DatasetScopeAuditRow.model_validate({**row.model_dump(), "unexpected": "value"})
    with pytest.raises(ValidationError):
        DatasetScopeAuditRow.model_validate({**row.model_dump(), "scope_status": "maybe"})
```

Phase 4 tests should reject unknown statuses, caveat tags, system classes, validation statuses, and extra fields.

**Nullable metric and caveat tests** (lines 144-237):

```python
def test_downstream_statistical_rows_allow_nullable_ci_and_optional_observed_fields() -> None:
    retry = RetryCalibrationRow(
        run_id="run-1",
        provider="openai",
        model="gpt-5",
        provider_model="openai/gpt-5",
        task_type="Dice_Count",
        task_family="Counting",
        exp2_pass_at_1=0.2,
        observed_fixed_retry_success=None,
        observed_adaptive_compatible_success=None,
        raw_observed_rate=0.2,
        scientific_rate=0.2,
        comparison_contract="task type primary, same attempt budget",
    )

    assert retry.observed_fixed_retry_success is None
    with pytest.raises(ValidationError):
        FailureTaxonomyRow.model_validate({**taxonomy.model_dump(), "claim_use": "unsafe"})
```

Use equivalent tests for Phase 4: literature-only rows may have reported metrics but no normalized success rate; non-comparable rows must require a comparability caveat.

**Writer tests** (lines 240-256):

```python
def test_writers_create_parent_dirs_and_emit_schema_payload(tmp_path) -> None:
    row = _dataset_scope_row()
    csv_path = tmp_path / "nested" / "dataset_scope_audit.csv"
    json_path = tmp_path / "nested" / "dataset_scope_audit.json"

    write_csv(csv_path, DatasetScopeAuditRow.model_fields, [row])
    write_json(json_path, DATASET_SCOPE_SCHEMA_VERSION, [row])

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    with json_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    assert csv_rows[0]["schema_version"] == DATASET_SCOPE_SCHEMA_VERSION
    assert payload["schema_version"] == DATASET_SCOPE_SCHEMA_VERSION
    assert payload["rows"][0]["task_type"] == "Dice_Count"
```

Repeat this for each Phase 4 writer wrapper or at least cover the shared writers plus one wrapper per schema.

---

### `tests/test_baseline_strengthening.py` (test; fixture-driven file-I/O, CLI request-response)

**Primary analog:** `tests/test_extended_dataset_manifest.py`

**Secondary analogs:** `tests/test_dataset_scope_audit.py`, `tests/test_retry_calibration.py`, `tests/test_failure_taxonomy.py`, `tests/test_limitations_summary.py`

**Test helper pattern** (tests/test_extended_dataset_manifest.py lines 19-31):

```python
def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({field for row in rows for field in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
```

Use local fixture writers and temporary directories. Do not depend on real external artifacts or network.

**Manifest fixture pattern** (tests/test_extended_dataset_manifest.py lines 33-83):

```python
def _manifest_rows() -> list[dict[str, object]]:
    common = {
        "label_format": "integer or categorical label",
        "metadata_alignment_notes": "aligned local ids and source paths",
        "answer_format_normalization": "normalized answers into static JSON-compatible fields",
        "task_family_grouping_notes": "mapped to reviewer-facing task family",
        "normalization_decisions": "removed ambiguous or incomplete samples",
        "compatibility_status": "ready_for_static_pipeline",
        "evaluation_status": "selected_for_validation",
        "validation_question": VALIDATION_QUESTION,
        "rerun_policy": "selective-validation-slice",
        "limitation_note": "selective validation slice only",
    }
    return [
        {
            **common,
            "source_id": "supplement-dice",
            "evidence_origin": "supplemented_category",
            "slice_type": "supplement_existing",
            "task_type": "Dice_Count",
            "task_family": "Counting",
            "sample_count": 12,
            "adaptive_eligible": True,
            "adaptive_slice_priority": 1,
        },
    ]
```

Phase 4 fixture should include Halligan and Oedipus rows, plus one unavailable or incompatible row and one non-directly-comparable literature-only metric.

**Validation behavior test pattern** (tests/test_extended_dataset_manifest.py lines 86-110):

```python
def test_manifest_validation_requires_supplement_and_new_category_rows(tmp_path) -> None:
    valid_manifest = tmp_path / "manifest.json"
    _write_json(valid_manifest, {"rows": _manifest_rows()})

    rows = load_extended_dataset_manifest(valid_manifest, run_id="manifest-test")

    assert len(rows) == 3
    assert {row.slice_type for row in rows} == {"supplement_existing", "new_category"}
    assert all(row.validation_question == VALIDATION_QUESTION for row in rows)

    invalid_manifest = tmp_path / "one-new-category.json"
    _write_json(invalid_manifest, {"rows": _manifest_rows()[:2]})
    with pytest.raises(ValueError, match="new_category_limitation"):
        load_extended_dataset_manifest(invalid_manifest, run_id="manifest-test")
```

Phase 4 tests should assert missing Halligan/Oedipus rows fail coverage validation, direct/adapter rows without license/data-use terms fail validation, and incompatible/unavailable rows without audit fields fail validation.

**CLI default output and notes pattern** (tests/test_extended_dataset_manifest.py lines 113-169):

```python
def test_cli_writes_manifest_slice_tasks_empty_comparison_and_notes(tmp_path, capsys) -> None:
    manifest_path = tmp_path / "manifest.json"
    _write_json(manifest_path, {"rows": _manifest_rows()})

    exit_code = main(
        [
            "--input-manifest",
            str(manifest_path),
            "--output-root",
            str(tmp_path / "results" / "revision"),
            "--run-id",
            "manifest-test",
        ]
    )

    summary = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert summary["row_count"] == 3
    assert summary["comparison_row_count"] == 0

    manifest_json = Path(summary["output_json"])
    comparison_json = Path(summary["comparison_json"])
    notes_md = Path(summary["notes_md"])
    assert manifest_json.exists()
    assert comparison_json.exists()
    assert notes_md.exists()

    notes = notes_md.read_text(encoding="utf-8")
    for heading in (
        "## Cleaning",
        "## Standardization",
        "## Label And Metadata Alignment",
        "## Answer-Format Normalization",
        "## Removal Decisions",
        "## Task-Family Grouping",
        "## Extended Validation Slice",
    ):
        assert heading in notes
```

Adapt this to subcommands. Test each Phase 4 subcommand writes default files under `results/revision/<run_id>/` and prints a JSON summary with no secret-bearing content.

**Comparison outcome test pattern** (tests/test_extended_dataset_manifest.py lines 171-244):

```python
def test_validation_slice_comparison_agreement_divergence_and_inconclusive(
    tmp_path,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    outcomes_path = tmp_path / "validation_outcomes.csv"
    conclusions_path = tmp_path / "original_conclusions.csv"
    _write_json(manifest_path, {"rows": _manifest_rows()})
    _write_csv(
        outcomes_path,
        [
            {
                "source_id": "supplement-dice",
                "task_type": "Dice_Count",
                "task_family": "Counting",
                "n_attempts": 20,
                "n_success": 4,
            },
        ],
    )
    rows = build_extended_validation_comparison_rows(
        manifest_rows=load_extended_dataset_manifest(manifest_path, run_id="manifest-test"),
        validation_outcomes=load_validation_slice_outcomes(outcomes_path),
        original_conclusions=load_original_conclusions(conclusions_path),
        run_id="manifest-test",
    )

    by_source = {row.source_id: row for row in rows}
    assert by_source["supplement-dice"].agreement_status == "supports_original"
    assert all("selective validation slice" in row.comparison_caveat for row in rows)
```

Phase 4 equivalent should assert:

- standardized metrics populate `normalized_success_rate`;
- metric-mismatch or dataset-mismatch rows leave normalized fields blank;
- `directly_comparable=false` rows include `comparability_caveat`;
- literature-only rows remain visible but caveated.

**Secret-safe CLI summary pattern** (tests/test_dataset_scope_audit.py lines 177-212):

```python
def test_cli_writes_default_revision_outputs_and_prints_secret_safe_summary(
    tmp_path, monkeypatch, capsys
) -> None:
    exit_code = main(
        [
            "--dataset-root",
            str(dataset_root),
            "--results-dir",
            str(results_dir),
            "--output-root",
            str(tmp_path / "results" / "revision"),
            "--run-id",
            "scope-test",
            "--underpowered-n",
            "20",
        ]
    )

    summary = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert summary["output_csv"].endswith("scope-test/dataset_scope_audit.csv")
    assert "secret" not in json.dumps(summary).lower()
    assert Path(summary["output_csv"]).exists()
```

Use this assertion on all Phase 4 CLI summaries.

**Invalid run id pattern** (tests/test_retry_calibration.py lines 280-306; tests/test_failure_taxonomy.py lines 236-257):

```python
@pytest.mark.parametrize("bad_run_id", ["../phase3", "bad/run"])
def test_cli_rejects_invalid_run_ids_before_writing_outputs(
    tmp_path: Path,
    bad_run_id: str,
) -> None:
    output_root = tmp_path / "revision"

    with pytest.raises(SystemExit):
        main(
            [
                "--results-dir",
                str(results_dir),
                "--adaptive-summary",
                str(adaptive_summary),
                "--output-root",
                str(output_root),
                "--run-id",
                bad_run_id,
                "--attempt-budget-k",
                "3",
            ]
        )

    assert not output_root.exists()
```

Add this for at least one subcommand that resolves output paths through `revision_run_dir`; ideally parameterize over all subcommands.

**Generated prose regression pattern** (tests/test_limitations_summary.py lines 392-430, 552-588):

```python
def test_render_limitations_summary_contains_required_language_and_rollups(
    tmp_path: Path,
) -> None:
    inputs = _fixture_inputs(tmp_path)

    text = render_limitations_summary(
        dataset_scope_rows=load_rows(inputs["dataset_scope_json"]),
        extended_manifest_rows=load_rows(inputs["extended_manifest_json"]),
        extended_validation_rows=load_rows(inputs["extended_validation_comparison_json"]),
        contribution_notes_md=inputs["contribution_notes_md"].read_text(encoding="utf-8"),
        pass_rate_rows=load_rows(inputs["pass_rate_confidence_json"]),
        threshold_rows=load_rows(inputs["threshold_sensitivity_json"]),
        retry_rows=load_rows(inputs["retry_calibration_json"]),
        failure_rows=load_rows(inputs["failure_taxonomy_json"]),
    )

    for heading in REQUIRED_HEADINGS:
        assert heading in text
    for required in REQUIRED_STRINGS:
        assert required in text
    assert "supports_original: 1" in text
    assert "diverges_from_original: 1" in text
    assert "inconclusive: 1" in text
```

For Phase 4 notes, assert required headings and language for direct/adapter/literature-only status counts, unavailable/incompatible evidence, non-comparable rows, and approximate comparison basis.

## Shared Patterns

### Output Root And Run ID Safety

**Source:** `revision_artifacts.py` lines 152-162  
**Apply to:** `baseline_strengthening.py` all write subcommands

```python
root = Path(output_root).resolve()
run_dir = (root / run_id).resolve()
if not run_dir.is_relative_to(root):
    raise ValueError("run_id resolves outside output_root")
return run_dir
```

All default Phase 4 outputs should be `revision_run_dir(args.output_root, args.run_id) / <filename>`.

### Strict Schema Before Write

**Source:** `retry_calibration.py` lines 421-441 and `failure_taxonomy.py` lines 103-118  
**Apply to:** all Phase 4 writers

```python
validated_rows = [
    row if isinstance(row, RetryCalibrationRow) else RetryCalibrationRow.model_validate(row)
    for row in rows
]
write_csv(Path(output_csv), RetryCalibrationRow.model_fields, validated_rows)
write_json(Path(output_json), RETRY_CALIBRATION_SCHEMA_VERSION, validated_rows)
```

Validate dict rows into Pydantic models before writing. Do not write ad hoc dictionaries directly to paper-ready artifacts.

### Task Family Mapping And Raw Label Preservation

**Source:** `dataset_scope_audit.py` lines 44-50; `retry_calibration.py` lines 588-590  
**Apply to:** coverage matrix and external subset mapping

```python
def _canonical_task_type(task_type: str) -> str:
    return TASK_ALIASES.get(task_type, task_type)


def _task_family(task_type: str) -> str:
    return CAPTCHAVisualizer.TASK_FAMILY.get(task_type, "Unmapped")
```

Use local family metadata where possible, but preserve `external_task_label`, `mapped_local_task_type`, `mapped_local_family`, mapping confidence, and rationale.

### Comparison Conservatism

**Source:** `adaptive_compare.py` lines 119-271; `retry_calibration.py` lines 256-354  
**Apply to:** `build-table` subcommand

```python
baseline_label = classify_rate(
    exp2_pass_at_1, cutoff=cutoff, margin=borderline_margin
)
adaptive_label = classify_rate(
    adaptive_success_at_k, cutoff=cutoff, margin=borderline_margin
)
classification_change = (
    f"{baseline_label}->{adaptive_label}"
    if baseline_label is not None and adaptive_label is not None
    else ""
)
```

This project labels comparisons explicitly and carries cutoff/contract notes. Phase 4 should similarly carry `comparison_contract`, `metric_standardization_status`, `dataset_mapping_confidence`, `directly_comparable`, and `comparability_caveat`.

### Caveat-First Claim Use

**Source:** `failure_taxonomy.py` lines 303-312; `limitations_summary.py` lines 49-60  
**Apply to:** paper table and notes

```python
def _claim_use_and_caveat(
    *,
    protocol_failure_count: int,
    infrastructure_failure_count: int,
) -> tuple[str, str | None]:
    if infrastructure_failure_count > 0:
        return "infrastructure_caveated", INFRASTRUCTURE_CAVEAT
    if protocol_failure_count > 0:
        return "protocol_caveated", PROTOCOL_CAVEAT
    return "scientific_claim_eligible", None
```

Do not encode caveats only in prose. They must appear in rows and be summarized in notes.

### Secret Safety

**Source:** `tests/test_dataset_scope_audit.py` lines 177-212  
**Apply to:** all Phase 4 CLI summaries and diagnostics

```python
summary = json.loads(capsys.readouterr().out)
assert "secret" not in json.dumps(summary).lower()
```

Do not read, print, copy, summarize, or commit `secrets.yaml` values. Phase 4 is offline and dataset-based.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `baseline_strengthening.py` subcommand dispatcher | CLI | request-response | Existing root CLIs use `argparse` but no file currently uses `add_subparsers`; implement stdlib subparsers while preserving local parser/main/error-summary style. |

No standalone README/reproduction source document was classified because the research output only requires generated `baseline_notes.md` under `results/revision/<run_id>/`.

## Metadata

**Analog search scope:** root-level Python modules, `tests/`, `.planning/codebase/`, and Phase 4 context/research docs.

**Files scanned/read:** 19 targeted files plus `rg` scans over root Python modules and tests:

- `.planning/phases/04-sota-solver-and-larger-benchmark-strengthening/04-CONTEXT.md`
- `.planning/phases/04-sota-solver-and-larger-benchmark-strengthening/04-RESEARCH.md`
- `.planning/codebase/STRUCTURE.md`
- `.planning/codebase/CONVENTIONS.md`
- `phase3_artifacts.py`
- `extended_dataset_manifest.py`
- `dataset_scope_audit.py`
- `retry_calibration.py`
- `failure_taxonomy.py`
- `revision_artifacts.py`
- `adaptive_compare.py`
- `limitations_summary.py`
- `tests/test_phase3_artifacts.py`
- `tests/test_extended_dataset_manifest.py`
- `tests/test_dataset_scope_audit.py`
- `tests/test_retry_calibration.py`
- `tests/test_failure_taxonomy.py`
- `tests/test_limitations_summary.py`
- `tests/conftest.py`

**Pattern extraction date:** 2026-05-19
