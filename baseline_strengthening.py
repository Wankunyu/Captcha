import argparse
import csv
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from phase4_artifacts import (
    BaselineCoverageRow,
    ExternalImportValidationRow,
    write_baseline_coverage,
    write_external_import_validation,
)
from revision_artifacts import revision_run_dir


NAMED_BASELINE_SYSTEMS = {"Halligan", "Oedipus"}
MAX_SECONDARY_SYSTEMS = 2
DEFAULT_SOURCE_METADATA = Path("baseline_sources/phase4_baseline_sources.json")


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


def _as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    raw = str(value).strip()
    if not raw:
        return []
    if raw.startswith("[") and raw.endswith("]"):
        try:
            payload = json.loads(raw)
            if isinstance(payload, list):
                return [str(item) for item in payload if str(item).strip()]
        except json.JSONDecodeError:
            pass
    return [part.strip() for part in raw.replace("|", ",").split(",") if part.strip()]


def _source_key(system_name: str, external_task_label: str) -> str:
    return f"{system_name}::{external_task_label}"


def _coverage_model_payload(raw_row: dict[str, object], run_id: str) -> dict[str, object]:
    payload = dict(raw_row)
    payload.pop("selection_reason", None)
    payload["run_id"] = run_id
    for field_name in ("captcha_families", "caveat_tags", "checked_sources", "missing_items"):
        payload[field_name] = _as_list(payload.get(field_name))
    payload["source_year"] = _as_int(payload.get("source_year"))
    payload["reported_metric_value"] = _as_float(payload.get("reported_metric_value"))
    return payload


def _secondary_systems(raw_rows: list[dict[str, object]]) -> set[str]:
    return {
        str(row.get("system_name") or "")
        for row in raw_rows
        if str(row.get("system_name") or "") not in NAMED_BASELINE_SYSTEMS
    }


def _validate_secondary_systems(raw_rows: list[dict[str, object]]) -> None:
    secondary_systems = _secondary_systems(raw_rows)
    if len(secondary_systems) > MAX_SECONDARY_SYSTEMS:
        raise ValueError("coverage metadata may include at most two additional systems")
    for row in raw_rows:
        system_name = str(row.get("system_name") or "")
        if system_name in NAMED_BASELINE_SYSTEMS:
            continue
        selection_reason = str(row.get("selection_reason") or "")
        if not any(named in selection_reason for named in NAMED_BASELINE_SYSTEMS):
            raise ValueError(
                f"{system_name} selection_reason must tie the row to Halligan or Oedipus"
            )


def validate_coverage_rows(
    rows: list[BaselineCoverageRow | dict[str, object]],
    run_id: str,
) -> list[BaselineCoverageRow]:
    raw_rows = [
        row.model_dump(mode="json") if isinstance(row, BaselineCoverageRow) else dict(row)
        for row in rows
    ]
    system_names = {str(row.get("system_name") or "") for row in raw_rows}
    if not NAMED_BASELINE_SYSTEMS <= system_names:
        raise ValueError("coverage metadata must include Halligan and Oedipus")
    _validate_secondary_systems(raw_rows)
    return [
        BaselineCoverageRow.model_validate(_coverage_model_payload(row, run_id))
        for row in raw_rows
    ]


def load_baseline_coverage_sources(path: Path, run_id: str) -> list[BaselineCoverageRow]:
    return validate_coverage_rows(_read_table(path), run_id=run_id)


def _load_baseline_coverage_artifact(path: Path, run_id: str) -> list[BaselineCoverageRow]:
    rows = _read_table(path)
    return [
        BaselineCoverageRow.model_validate(_coverage_model_payload(row, run_id))
        for row in rows
    ]


def load_external_import_rows(path: Path) -> list[dict[str, object]]:
    return _read_table(path)


def _validation_status(condition: bool) -> str:
    return "pass" if condition else "fail"


def _coverage_index(
    rows: list[BaselineCoverageRow],
) -> dict[str, BaselineCoverageRow]:
    return {
        _source_key(row.system_name, row.external_task_label): row
        for row in rows
    }


def _validation_row_from_import(
    raw_row: dict[str, object],
    coverage_by_key: dict[str, BaselineCoverageRow],
    run_id: str,
) -> ExternalImportValidationRow:
    system_name = str(raw_row.get("system_name") or "")
    external_task_label = str(raw_row.get("external_task_label") or "")
    source_key = str(raw_row.get("source_key") or "") or _source_key(
        system_name, external_task_label
    )
    coverage_row = coverage_by_key.get(source_key)
    mapped_local_task_type = str(raw_row.get("mapped_local_task_type") or "")
    sample_count = _as_int(raw_row.get("sample_count"))
    reported_metric_name = str(raw_row.get("reported_metric_name") or "")
    reported_metric_value = _as_float(raw_row.get("reported_metric_value"))
    reported_metric_unit = str(raw_row.get("reported_metric_unit") or "")
    metric_definition = str(raw_row.get("metric_definition") or "")
    artifact_license = str(raw_row.get("artifact_license") or raw_row.get("license") or "")
    data_use_constraints = str(raw_row.get("data_use_constraints") or "")
    assumptions = str(raw_row.get("comparability_assumptions") or "")

    required_fields_ok = all(
        [
            system_name,
            source_key,
            external_task_label,
            mapped_local_task_type,
            reported_metric_name,
            reported_metric_unit,
        ]
    )
    metric_ok = bool(metric_definition and reported_metric_name and reported_metric_unit)
    task_label_ok = (
        coverage_row is not None
        and coverage_row.external_task_label == external_task_label
        and coverage_row.mapped_local_task_type == mapped_local_task_type
    )
    sample_count_ok = sample_count > 0
    artifact_license_ok = bool(artifact_license.strip())
    data_use_ok = bool(data_use_constraints.strip())
    comparability_ok = all(
        [
            assumptions.strip(),
            metric_ok,
            task_label_ok,
            sample_count_ok,
            artifact_license_ok,
            data_use_ok,
        ]
    )
    validation_ok = all(
        [
            required_fields_ok,
            metric_ok,
            task_label_ok,
            sample_count_ok,
            artifact_license_ok,
            data_use_ok,
            comparability_ok,
        ]
    )
    normalized_success_rate = (
        reported_metric_value
        if validation_ok
        and reported_metric_name == "success_rate"
        and reported_metric_unit == "rate"
        else None
    )
    notes = []
    if coverage_row is None:
        notes.append("no matching coverage row")
    if not validation_ok:
        notes.append("one or more import validation checks failed")
    if not notes:
        notes.append("validated offline import row")

    return ExternalImportValidationRow(
        run_id=run_id,
        system_name=system_name,
        source_key=source_key,
        external_task_label=external_task_label,
        mapped_local_task_type=mapped_local_task_type,
        required_fields_status=_validation_status(required_fields_ok),
        metric_definition_status=_validation_status(metric_ok),
        task_label_status=_validation_status(task_label_ok),
        sample_count_status=_validation_status(sample_count_ok),
        artifact_license_status=_validation_status(artifact_license_ok),
        data_use_status=_validation_status(data_use_ok),
        comparability_status=_validation_status(comparability_ok),
        validation_status=_validation_status(validation_ok),
        sample_count=sample_count,
        reported_metric_name=reported_metric_name,
        reported_metric_value=reported_metric_value,
        reported_metric_unit=reported_metric_unit,
        normalized_success_rate=normalized_success_rate,
        diagnostic_notes="; ".join(notes),
        user_confirmed_replacement=_as_bool(raw_row.get("user_confirmed_replacement")),
    )


def build_external_import_validation_rows(
    coverage_rows: list[BaselineCoverageRow],
    import_rows: list[dict[str, object]],
    run_id: str,
) -> list[ExternalImportValidationRow]:
    coverage_by_key = _coverage_index(coverage_rows)
    rows = [
        _validation_row_from_import(raw_row, coverage_by_key, run_id)
        for raw_row in import_rows
    ]
    named_pass = any(
        row.system_name in NAMED_BASELINE_SYSTEMS and row.validation_status == "pass"
        for row in rows
    )
    secondary_rows = [row for row in rows if row.system_name not in NAMED_BASELINE_SYSTEMS]
    if secondary_rows and not named_pass:
        unconfirmed = [row for row in secondary_rows if not row.user_confirmed_replacement]
        if unconfirmed:
            raise ValueError(
                "secondary smoke replacement requires user confirmation when no "
                "Halligan/Oedipus import row validates"
            )
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Phase 4 baseline coverage and import-validation artifacts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    coverage = subparsers.add_parser(
        "coverage",
        help="Validate baseline source metadata and write a coverage matrix.",
    )
    coverage.add_argument("--source-metadata", default=str(DEFAULT_SOURCE_METADATA))
    coverage.add_argument("--output-root", default="./results/revision")
    coverage.add_argument("--run-id", required=True)
    coverage.add_argument("--output-csv", default=None)
    coverage.add_argument("--output-json", default=None)

    validate_import = subparsers.add_parser(
        "validate-import",
        help="Validate external/imported baseline smoke rows.",
    )
    validate_import.add_argument("--coverage-json", required=True)
    validate_import.add_argument("--import-rows", required=True)
    validate_import.add_argument("--output-root", default="./results/revision")
    validate_import.add_argument("--run-id", required=True)
    validate_import.add_argument("--output-csv", default=None)
    validate_import.add_argument("--output-json", default=None)
    return parser


def _path_or_default(raw_path: str | None, default_path: Path) -> Path:
    return Path(raw_path) if raw_path else default_path


def _run_coverage(args: argparse.Namespace) -> dict[str, object]:
    run_dir = revision_run_dir(args.output_root, args.run_id)
    output_csv = _path_or_default(args.output_csv, run_dir / "coverage_matrix.csv")
    output_json = _path_or_default(args.output_json, run_dir / "coverage_matrix.json")
    rows = load_baseline_coverage_sources(Path(args.source_metadata), run_id=args.run_id)
    write_baseline_coverage(output_csv, output_json, rows)
    return {
        "row_count": len(rows),
        "output_csv": str(output_csv),
        "output_json": str(output_json),
    }


def _run_validate_import(args: argparse.Namespace) -> dict[str, object]:
    run_dir = revision_run_dir(args.output_root, args.run_id)
    output_csv = _path_or_default(args.output_csv, run_dir / "import_diagnostics.csv")
    output_json = _path_or_default(args.output_json, run_dir / "import_diagnostics.json")
    coverage_rows = _load_baseline_coverage_artifact(
        Path(args.coverage_json),
        run_id=args.run_id,
    )
    import_rows = load_external_import_rows(Path(args.import_rows))
    rows = build_external_import_validation_rows(
        coverage_rows,
        import_rows,
        run_id=args.run_id,
    )
    write_external_import_validation(output_csv, output_json, rows)
    return {
        "row_count": len(rows),
        "output_csv": str(output_csv),
        "output_json": str(output_json),
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "coverage":
            summary = _run_coverage(args)
        elif args.command == "validate-import":
            summary = _run_validate_import(args)
        else:
            parser.error(f"unknown command: {args.command}")
    except (OSError, ValueError, ValidationError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
