import argparse
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from phase041_artifacts import (
    ExpandedDatasetManifestRow,
    ExpandedRunMatrixRow,
    write_expanded_run_matrix,
)
from revision_artifacts import revision_run_dir


PHASE041_SIDECAR_ROOT = Path("expanded_captcha_data/phase04_1")
PHASE041_EVALUATOR_SLICE = PHASE041_SIDECAR_ROOT / "evaluator_slice"
PHASE041_SUPPLEMENTED_TASK_TYPES = {"Dice_Count", "Click_Order", "Patch_Select", "Geometry_Click"}
PHASE041_NEW_TASK_TYPES = {"Symbol_Count", "Relation_Match"}

PAPER_FACING_PROVIDER_MODELS = [
    "openai/gpt-5",
    "openai/gpt-5.1_medium",
    "openai/gpt-5.1_none",
    "anthropic/claude-sonnet-4-5",
    "gemini/gemini-2.5-flash",
    "gemini/gemini-2.5-pro",
    "fireworks/accounts_fireworks_models_qwen3-vl-235b-a22b-instruct",
]

IMAGE_SUFFIXES = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
BANNED_STATIC_COMPATIBILITY_TERMS = (
    "live service",
    "browser automation",
    "temporal hold",
    "press-and-hold",
    "drag/slider",
    "drag",
    "slider",
    "production endpoint",
    "http://",
    "https://",
)


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _resolve_sidecar_relative(raw_path: str, sidecar_root: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path.resolve()
    try:
        suffix = path.relative_to(PHASE041_SIDECAR_ROOT)
    except ValueError:
        suffix = path
    return (sidecar_root / suffix).resolve()


def _validate_materialized_path(raw_path: str, sidecar_root: Path) -> None:
    resolved = _resolve_sidecar_relative(raw_path, sidecar_root)
    evaluator_root = (sidecar_root / "evaluator_slice").resolve()
    if not _is_relative_to(resolved, evaluator_root):
        raise ValueError(
            "materialized_path must resolve under "
            f"{PHASE041_EVALUATOR_SLICE.as_posix()}"
        )


def _validate_source_path(row: ExpandedDatasetManifestRow, sidecar_root: Path) -> None:
    resolved = _resolve_sidecar_relative(row.source_path, sidecar_root)
    sources_root = (sidecar_root / "sources").resolve()
    if not _is_relative_to(resolved, sources_root):
        raise ValueError(
            f"{row.source_id} source_path must resolve under "
            f"{(PHASE041_SIDECAR_ROOT / 'sources').as_posix()}"
        )


def load_phase041_manifest(
    path: Path,
    run_id: str,
) -> list[ExpandedDatasetManifestRow]:
    payload = _read_json(path)
    if isinstance(payload, list):
        raw_rows = payload
    elif isinstance(payload, dict):
        raw_rows = payload.get("rows")
    else:
        raise ValueError("input manifest must be a JSON object or array")
    if not isinstance(raw_rows, list):
        raise ValueError("input manifest must contain a rows array")

    sidecar_root = path.parent
    rows: list[ExpandedDatasetManifestRow] = []
    for index, raw_row in enumerate(raw_rows, start=1):
        if not isinstance(raw_row, dict):
            raise ValueError(f"manifest row {index} must be a JSON object")
        values = dict(raw_row)
        materialized_path = values.pop("materialized_path", None)
        try:
            row = ExpandedDatasetManifestRow.model_validate({**values, "run_id": run_id})
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc
        if materialized_path not in (None, ""):
            _validate_materialized_path(str(materialized_path), sidecar_root)
        _validate_source_path(row, sidecar_root)
        rows.append(row)
    return rows


def _row_static_text(row: ExpandedDatasetManifestRow) -> str:
    fields = [
        row.source_id,
        row.source_path,
        row.task_type,
        row.task_family,
        row.label_format,
        row.metadata_alignment_notes,
        row.answer_format_normalization,
        row.limitation_notes,
        row.static_compatibility_notes,
    ]
    return "\n".join(fields).lower()


def validate_phase041_manifest(rows: list[ExpandedDatasetManifestRow]) -> None:
    if not rows:
        raise ValueError("manifest must contain at least one row")

    new_category_types = {
        row.task_type
        for row in rows
        if row.evidence_origin == "new_category" or row.slice_type == "new_category"
    }
    unsupported_new_types = new_category_types - PHASE041_NEW_TASK_TYPES
    if unsupported_new_types:
        raise ValueError(
            "only accepted new-category task types are "
            f"{sorted(PHASE041_NEW_TASK_TYPES)}; got {sorted(unsupported_new_types)}"
        )
    if new_category_types != PHASE041_NEW_TASK_TYPES:
        raise ValueError(
            "manifest must include exactly two distinct new_category task types: "
            f"{sorted(PHASE041_NEW_TASK_TYPES)}"
        )

    supplemented_types = {
        row.task_type
        for row in rows
        if row.evidence_origin == "supplemented_category"
        or row.slice_type == "supplement_existing"
    }
    missing_supplemented = PHASE041_SUPPLEMENTED_TASK_TYPES - supplemented_types
    if missing_supplemented:
        raise ValueError(
            "manifest must include supplemented rows for "
            f"{sorted(PHASE041_SUPPLEMENTED_TASK_TYPES)}; missing "
            f"{sorted(missing_supplemented)}"
        )

    for row in rows:
        if row.sample_count <= 0:
            raise ValueError(f"{row.source_id} sample_count must be greater than zero")
        if row.compatibility_status != "ready_for_static_pipeline":
            raise ValueError(
                f"{row.source_id} compatibility_status must be ready_for_static_pipeline"
            )
        row_text = _row_static_text(row)
        banned_matches = [
            term for term in BANNED_STATIC_COMPATIBILITY_TERMS if term in row_text
        ]
        if banned_matches:
            raise ValueError(
                f"{row.source_id} is not static-compatible: {sorted(banned_matches)}"
            )


def _iter_string_values(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for child in value.values():
            strings.extend(_iter_string_values(child))
        return strings
    if isinstance(value, list):
        strings = []
        for child in value:
            strings.extend(_iter_string_values(child))
        return strings
    return []


def _referenced_files(ground_truth: dict[str, object]) -> list[str]:
    referenced: set[str] = set()
    for puzzle_id, entry in ground_truth.items():
        if isinstance(puzzle_id, str):
            referenced.add(puzzle_id)
        for value in _iter_string_values(entry):
            suffix = Path(value).suffix.lower()
            if suffix in IMAGE_SUFFIXES:
                referenced.add(value)
    return sorted(referenced)


def _copy_referenced_file(source_dir: Path, output_dir: Path, relative_path: str) -> None:
    relative = Path(relative_path)
    if relative.is_absolute():
        raise ValueError(f"referenced dataset file must be relative: {relative_path}")
    source_root = source_dir.resolve()
    source_path = (source_dir / relative).resolve()
    if not _is_relative_to(source_path, source_root):
        raise ValueError(f"referenced dataset file escapes source_path: {relative_path}")
    if not source_path.is_file():
        raise FileNotFoundError(str(source_path))
    output_path = output_dir / relative
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, output_path)


def _safe_prepare_output_root(
    sidecar_root: Path,
    output_root: Path,
    *,
    overwrite: bool,
) -> Path:
    sidecar_resolved = sidecar_root.resolve()
    output_resolved = output_root.resolve()
    captcha_root = Path("captcha_data").resolve()
    if output_resolved == captcha_root or _is_relative_to(output_resolved, captcha_root):
        raise ValueError("materialization output_root must not be captcha_data")
    if output_resolved == sidecar_resolved:
        raise ValueError("materialization output_root must not be the sidecar root")
    if not _is_relative_to(output_resolved, sidecar_resolved):
        raise ValueError("materialization output_root must stay under sidecar_root")
    if output_root.exists():
        if not overwrite:
            raise FileExistsError(f"output_root already exists: {output_root}")
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    return output_root


def materialize_evaluator_slice(
    rows: list[ExpandedDatasetManifestRow],
    sidecar_root: Path,
    output_root: Path,
    overwrite: bool = False,
) -> dict[str, object]:
    validate_phase041_manifest(rows)
    output_root = _safe_prepare_output_root(
        Path(sidecar_root),
        Path(output_root),
        overwrite=overwrite,
    )
    sidecar_root = Path(sidecar_root)

    rows_by_task: dict[str, list[ExpandedDatasetManifestRow]] = defaultdict(list)
    for row in rows:
        rows_by_task[row.task_type].append(row)

    ground_truth_paths: list[str] = []
    copied_file_count = 0
    for task_type, task_rows in sorted(rows_by_task.items()):
        task_output_root = output_root / task_type
        task_output_root.mkdir(parents=True, exist_ok=True)
        combined_ground_truth: dict[str, object] = {}

        for row in task_rows:
            source_dir = _resolve_sidecar_relative(row.source_path, sidecar_root)
            source_gt_path = source_dir / "ground_truth.json"
            if not source_gt_path.is_file():
                raise FileNotFoundError(str(source_gt_path))
            source_ground_truth = _read_json(source_gt_path)
            if not isinstance(source_ground_truth, dict):
                raise ValueError(f"{source_gt_path} must contain a JSON object")
            duplicate_ids = set(combined_ground_truth).intersection(source_ground_truth)
            if duplicate_ids:
                raise ValueError(
                    f"{row.source_id} duplicates puzzle ids: {sorted(duplicate_ids)}"
                )
            for relative_path in _referenced_files(source_ground_truth):
                _copy_referenced_file(source_dir, task_output_root, relative_path)
                copied_file_count += 1
            combined_ground_truth.update(source_ground_truth)

        ground_truth_path = task_output_root / "ground_truth.json"
        with ground_truth_path.open("w", encoding="utf-8") as handle:
            json.dump(combined_ground_truth, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        ground_truth_paths.append(str(ground_truth_path))

    return {
        "row_count": len(rows),
        "task_type_count": len(rows_by_task),
        "copied_file_count": copied_file_count,
        "output_root": str(output_root),
        "ground_truth_files": ground_truth_paths,
    }


def _exp2_root(results_dir: Path) -> Path:
    return results_dir / "exp2" if (results_dir / "exp2").is_dir() else results_dir


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")


def _discover_exp2_provider_models(results_dir: Path) -> set[str]:
    root = _exp2_root(results_dir)
    provider_models: set[str] = set()
    if not root.is_dir():
        return provider_models
    for provider_dir in root.iterdir():
        if not provider_dir.is_dir():
            continue
        for model_dir in provider_dir.iterdir():
            if model_dir.is_dir():
                provider_models.add(f"{provider_dir.name}/{model_dir.name}")
    return provider_models


def build_paper_facing_run_matrix(
    results_dir: Path,
    materialized_dataset_root: Path,
    output_root: Path,
    run_id_prefix: str,
) -> list[ExpandedRunMatrixRow]:
    discovered = _discover_exp2_provider_models(Path(results_dir))
    missing = [
        provider_model
        for provider_model in PAPER_FACING_PROVIDER_MODELS
        if provider_model not in discovered
    ]
    if missing:
        raise ValueError(f"results/exp2 is missing paper-facing model rows: {missing}")

    task_types = sorted(PHASE041_SUPPLEMENTED_TASK_TYPES | PHASE041_NEW_TASK_TYPES)
    rows: list[ExpandedRunMatrixRow] = []
    for provider_model in PAPER_FACING_PROVIDER_MODELS:
        provider, model = provider_model.split("/", 1)
        run_id = f"{run_id_prefix}-{_slug(provider)}-{_slug(model)}"
        rows.append(
            ExpandedRunMatrixRow(
                matrix_id=run_id,
                paper_facing_model_row=True,
                provider=provider,
                model=model,
                provider_model=provider_model,
                run_scope="static",
                run_id=run_id,
                task_types=task_types,
                materialized_dataset_root=str(materialized_dataset_root),
                output_root=str(revision_run_dir(output_root, run_id)),
                overwrite=False,
                resume=True,
            )
        )
    return rows


def _run_manifest(args: argparse.Namespace) -> dict[str, object]:
    rows = load_phase041_manifest(Path(args.manifest), run_id=args.run_id)
    validate_phase041_manifest(rows)
    return {
        "row_count": len(rows),
        "task_type_count": len({row.task_type for row in rows}),
        "manifest": str(Path(args.manifest)),
    }


def _run_materialize(args: argparse.Namespace) -> dict[str, object]:
    rows = load_phase041_manifest(Path(args.manifest), run_id=args.run_id)
    return materialize_evaluator_slice(
        rows,
        sidecar_root=Path(args.sidecar_root),
        output_root=Path(args.output_root),
        overwrite=args.overwrite,
    )


def _run_matrix(args: argparse.Namespace) -> dict[str, object]:
    rows = build_paper_facing_run_matrix(
        results_dir=Path(args.results_dir),
        materialized_dataset_root=Path(args.materialized_dataset_root),
        output_root=Path(args.output_root),
        run_id_prefix=args.run_id_prefix,
    )
    run_dir = revision_run_dir(args.output_root, args.run_id_prefix)
    output_csv = Path(args.output_csv) if args.output_csv else run_dir / "expanded_run_matrix.csv"
    output_json = (
        Path(args.output_json) if args.output_json else run_dir / "expanded_run_matrix.json"
    )
    write_expanded_run_matrix(output_csv, output_json, rows)
    return {
        "row_count": len(rows),
        "output_csv": str(output_csv),
        "output_json": str(output_json),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and materialize Phase 04.1 expanded sidecar datasets."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest = subparsers.add_parser(
        "manifest",
        help="Validate a Phase 04.1 expanded sidecar manifest.",
    )
    manifest.add_argument("--manifest", default=str(PHASE041_SIDECAR_ROOT / "manifest.json"))
    manifest.add_argument("--run-id", required=True)

    materialize = subparsers.add_parser(
        "materialize",
        help="Materialize an evaluator-compatible Phase 04.1 sidecar root.",
    )
    materialize.add_argument("--manifest", default=str(PHASE041_SIDECAR_ROOT / "manifest.json"))
    materialize.add_argument("--run-id", required=True)
    materialize.add_argument("--sidecar-root", default=str(PHASE041_SIDECAR_ROOT))
    materialize.add_argument("--output-root", default=str(PHASE041_EVALUATOR_SLICE))
    materialize.add_argument("--overwrite", action="store_true")

    run_matrix = subparsers.add_parser(
        "run-matrix",
        help="Generate the paper-facing Phase 04.1 provider/model run matrix.",
    )
    run_matrix.add_argument("--results-dir", default="results/exp2")
    run_matrix.add_argument(
        "--materialized-dataset-root",
        default=str(PHASE041_EVALUATOR_SLICE),
    )
    run_matrix.add_argument("--output-root", default="results/revision")
    run_matrix.add_argument("--run-id-prefix", required=True)
    run_matrix.add_argument("--output-csv", default=None)
    run_matrix.add_argument("--output-json", default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "manifest":
            summary = _run_manifest(args)
        elif args.command == "materialize":
            summary = _run_materialize(args)
        elif args.command == "run-matrix":
            summary = _run_matrix(args)
        else:
            parser.error(f"unknown command: {args.command}")
    except (OSError, ValueError, ValidationError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
