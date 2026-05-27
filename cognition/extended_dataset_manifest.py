import argparse
import csv
import json
from pathlib import Path
from typing import Any

from .dataset_scope_audit import (
    HOLD_BUTTON_REASON,
    HOLD_BUTTON_TASK,
    SLIDE_PUZZLE_REASON,
    SLIDE_PUZZLE_TASK,
)
from .phase3_artifacts import (
    EXTENDED_DATASET_MANIFEST_SCHEMA_VERSION,
    EXTENDED_VALIDATION_COMPARISON_SCHEMA_VERSION,
    ExtendedDatasetManifestRow,
    ExtendedValidationComparisonRow,
    write_csv,
    write_json,
)
from .revision_artifacts import revision_run_dir


VALIDATION_QUESTION = (
    "do the conclusions drawn from the original dataset still hold on the new dataset "
    "slice?"
)
RERUN_POLICY = "selective-validation-slice"
ADAPTIVE_RECOMMENDED_COMMAND_SCOPE = (
    "adaptive validation slice only; preserve binary pass/fail feedback and explicit "
    "local policy memory"
)
STATIC_RECOMMENDED_COMMAND_SCOPE = (
    "static validation slice only; preserve original and extended evidence separation"
)
COMPARISON_CAVEAT = (
    "This artifact is a selective validation slice and does not erase CaptchaWorld "
    "limitations or create population-level deployment estimates."
)
SLICE_TASK_FIELDS = [
    "source_id",
    "task_type",
    "task_family",
    "slice_type",
    "sample_count",
    "evaluation_status",
    "adaptive_eligible",
    "adaptive_slice_priority",
    "recommended_command_scope",
]


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


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _as_int(value: object, default: int = 0) -> int:
    if value in (None, ""):
        return default
    return int(float(str(value)))


def _as_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(str(value))


def _first_present(record: dict[str, object], *keys: str) -> object:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return None


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
    if new_category_count < 2 and not new_category_limitation.strip():
        raise ValueError(
            "new_category_limitation is required when fewer than two new_category rows exist"
        )
    for row in rows:
        if row.validation_question != VALIDATION_QUESTION:
            raise ValueError(f"{row.source_id} validation_question must be exact")
        if row.rerun_policy != RERUN_POLICY:
            raise ValueError(f"{row.source_id} rerun_policy must be {RERUN_POLICY}")
    return rows


def write_extended_dataset_manifest(
    rows: list[ExtendedDatasetManifestRow],
    output_csv: Path,
    output_json: Path,
) -> tuple[Path, Path]:
    write_csv(output_csv, ExtendedDatasetManifestRow.model_fields, rows)
    write_json(output_json, EXTENDED_DATASET_MANIFEST_SCHEMA_VERSION, rows)
    return output_csv, output_json


def write_extended_validation_slice_tasks(
    rows: list[ExtendedDatasetManifestRow],
    output_csv: Path,
) -> Path:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SLICE_TASK_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "source_id": row.source_id,
                    "task_type": row.task_type,
                    "task_family": row.task_family,
                    "slice_type": row.slice_type,
                    "sample_count": row.sample_count,
                    "evaluation_status": row.evaluation_status,
                    "adaptive_eligible": row.adaptive_eligible,
                    "adaptive_slice_priority": row.adaptive_slice_priority,
                    "recommended_command_scope": (
                        ADAPTIVE_RECOMMENDED_COMMAND_SCOPE
                        if row.adaptive_eligible
                        else STATIC_RECOMMENDED_COMMAND_SCOPE
                    ),
                }
            )
    return output_csv


def load_validation_slice_outcomes(path: Path | None) -> list[dict[str, object]]:
    return _read_table(path)


def load_original_conclusions(path: Path | None) -> list[dict[str, object]]:
    return _read_table(path)


def _validation_rate(outcome: dict[str, object]) -> tuple[int, float | None]:
    sample_count = _as_int(
        _first_present(outcome, "validation_sample_count", "n_attempts"), default=0
    )
    explicit_rate = _as_float(outcome.get("success_rate"))
    if explicit_rate is not None:
        return sample_count, explicit_rate
    success_count = _as_int(
        _first_present(outcome, "success_count", "n_success"), default=0
    )
    if sample_count <= 0:
        return sample_count, None
    return sample_count, success_count / sample_count


def _original_rate(record: dict[str, object] | None) -> float | None:
    if record is None:
        return None
    return _as_float(_first_present(record, "original_rate", "primary_rate"))


def _original_label(record: dict[str, object] | None) -> str | None:
    if record is None:
        return None
    value = _first_present(record, "original_conclusion_label", "label")
    return None if value in (None, "") else str(value)


def _direction(label: str | None, rate: float | None, cutoff: float = 0.40) -> str | None:
    if label:
        lowered = label.lower()
        if "borderline" in lowered or "near" in lowered:
            return "borderline"
        if "hard" in lowered:
            return "hard"
        if "broken" in lowered:
            return "broken"
    if rate is None:
        return None
    if rate < cutoff:
        return "hard"
    if abs(rate - cutoff) <= 1e-12:
        return "borderline"
    return "broken"


def _manifest_by_source(
    rows: list[ExtendedDatasetManifestRow],
) -> dict[str, ExtendedDatasetManifestRow]:
    return {row.source_id: row for row in rows}


def _original_indexes(
    rows: list[dict[str, object]],
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    by_task = {
        str(row["task_type"]): row
        for row in rows
        if row.get("task_type") not in (None, "")
    }
    by_family = {
        str(row["task_family"]): row
        for row in rows
        if row.get("task_family") not in (None, "")
    }
    return by_task, by_family


def _find_original_conclusion(
    task_type: str,
    task_family: str,
    by_task: dict[str, dict[str, object]],
    by_family: dict[str, dict[str, object]],
) -> dict[str, object] | None:
    return by_task.get(task_type) or by_family.get(task_family)


def _comparison_status(
    *,
    manifest_row: ExtendedDatasetManifestRow,
    validation_sample_count: int,
    original_direction: str | None,
    validation_direction: str | None,
) -> tuple[str, str]:
    if (
        validation_sample_count <= 0
        or original_direction is None
        or validation_direction is None
        or manifest_row.compatibility_status != "ready_for_static_pipeline"
        or manifest_row.evaluation_status not in {"selected_for_validation", "evaluated"}
    ):
        reason = "missing original conclusion, zero sample count, or unsupported slice"
        return "inconclusive", reason
    if original_direction == validation_direction:
        return "supports_original", ""
    return (
        "diverges_from_original",
        "validation slice crosses the original 40% cutoff direction",
    )


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
            task_type = str(outcome.get("task_type") or "")
            task_family = str(outcome.get("task_family") or "")
            matches = [
                row
                for row in manifest_rows
                if row.task_type == task_type or row.task_family == task_family
            ]
            manifest_row = matches[0] if matches else None
        if manifest_row is None:
            continue

        validation_sample_count, validation_slice_rate = _validation_rate(outcome)
        original = _find_original_conclusion(
            manifest_row.task_type,
            manifest_row.task_family,
            original_by_task,
            original_by_family,
        )
        original_rate = _original_rate(original)
        original_label = _original_label(original)
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
                original_conclusion_label=original_label,
                original_rate=original_rate,
                validation_slice_rate=validation_slice_rate,
                validation_sample_count=validation_sample_count,
                agreement_status=status,
                divergence_reason=reason,
                comparison_caveat=COMPARISON_CAVEAT,
                outcome_source_path=str(outcome.get("outcome_source_path") or ""),
            )
        )
    return rows


def write_extended_validation_comparison(
    rows: list[ExtendedValidationComparisonRow],
    output_csv: Path,
    output_json: Path,
) -> tuple[Path, Path]:
    write_csv(output_csv, ExtendedValidationComparisonRow.model_fields, rows)
    write_json(output_json, EXTENDED_VALIDATION_COMPARISON_SCHEMA_VERSION, rows)
    return output_csv, output_json


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
        "",
        "## Label And Metadata Alignment",
        "Manifest rows preserve label format, metadata alignment notes, source paths, and",
        (
            "task-family grouping so original, supplemented-category, and "
            "new-category evidence remain separate."
        ),
        "",
        "## Answer-Format Normalization",
        "Answer formats are normalized into static JSON-compatible fields before any",
        "offline evaluation consumes the slice.",
        "",
        "## Removal Decisions",
        f"- `{HOLD_BUTTON_TASK}`: {HOLD_BUTTON_REASON}.",
        f"- `{SLIDE_PUZZLE_TASK}`: {SLIDE_PUZZLE_REASON}.",
    ]
    if dataset_scope_json is not None:
        content_lines.extend(["", f"Dataset scope audit source: `{dataset_scope_json}`."])
    content_lines.extend(
        [
            "",
            "## Task-Family Grouping",
            "Task-family grouping is recorded per row and is not collapsed across original,",
            "supplemented-category, or new-category evidence.",
            "",
            "## Extended Validation Slice",
            "The extended-data rows define a selective validation slice. The slice asks",
            "whether conclusions drawn from the original dataset still hold on the new",
            "dataset slice, while retaining the limitation that CaptchaWorld and",
            "extensions do not provide population-level deployment estimates.",
        ]
    )
    content = "\n".join(content_lines) + "\n"
    output_md.write_text(content, encoding="utf-8")
    return output_md


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate an extended dataset manifest and write Phase 3 artifacts."
    )
    parser.add_argument("--input-manifest", required=True)
    parser.add_argument("--dataset-scope-json", default=None)
    parser.add_argument("--output-root", default="./results/local_runs")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-csv", default=None)
    parser.add_argument("--output-json", default=None)
    parser.add_argument("--slice-tasks-csv", default=None)
    parser.add_argument("--validation-outcomes", default=None)
    parser.add_argument("--original-conclusions", default=None)
    parser.add_argument("--comparison-csv", default=None)
    parser.add_argument("--comparison-json", default=None)
    parser.add_argument("--notes-md", default=None)
    return parser


def _path_or_default(raw_path: str | None, default_path: Path) -> Path:
    return Path(raw_path) if raw_path else default_path


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
        slice_tasks_csv = _path_or_default(
            args.slice_tasks_csv, run_dir / "extended_validation_slice_tasks.csv"
        )
        comparison_csv = _path_or_default(
            args.comparison_csv, run_dir / "extended_validation_comparison.csv"
        )
        comparison_json = _path_or_default(
            args.comparison_json, run_dir / "extended_validation_comparison.json"
        )
        notes_md = _path_or_default(args.notes_md, run_dir / "dataset_contribution_notes.md")
        manifest_rows = load_extended_dataset_manifest(
            Path(args.input_manifest), run_id=args.run_id
        )
        output_csv, output_json = write_extended_dataset_manifest(
            manifest_rows, output_csv, output_json
        )
        slice_tasks_csv = write_extended_validation_slice_tasks(
            manifest_rows, slice_tasks_csv
        )
        validation_outcomes = load_validation_slice_outcomes(
            Path(args.validation_outcomes) if args.validation_outcomes else None
        )
        original_conclusions = load_original_conclusions(
            Path(args.original_conclusions) if args.original_conclusions else None
        )
        comparison_rows = build_extended_validation_comparison_rows(
            manifest_rows=manifest_rows,
            validation_outcomes=validation_outcomes,
            original_conclusions=original_conclusions,
            run_id=args.run_id,
        )
        comparison_csv, comparison_json = write_extended_validation_comparison(
            comparison_rows, comparison_csv, comparison_json
        )
        notes_md = write_dataset_contribution_notes(
            manifest_rows,
            notes_md,
            Path(args.dataset_scope_json) if args.dataset_scope_json else None,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    print(
        json.dumps(
            {
                "row_count": len(manifest_rows),
                "slice_task_count": len(manifest_rows),
                "comparison_row_count": len(comparison_rows),
                "output_csv": str(output_csv),
                "output_json": str(output_json),
                "slice_tasks_csv": str(slice_tasks_csv),
                "comparison_csv": str(comparison_csv),
                "comparison_json": str(comparison_json),
                "notes_md": str(notes_md),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
