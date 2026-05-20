import argparse
import inspect
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any

from pydantic import ValidationError

import revision_preflight
import run_eval
import adaptive_attacker
import adaptive_preflight
from adaptive_artifacts import FEEDBACK_MODE, MEMORY_MODE, SAMPLING_MODE, STOPPING_RULE
from phase041_artifacts import (
    ExpandedDatasetManifestRow,
    ExpandedAdaptiveSummaryRow,
    ExpandedPreflightMatrixRow,
    ExpandedRunMatrixRow,
    ExpandedStaticSummaryRow,
    write_expanded_adaptive_summary,
    write_expanded_run_matrix,
    write_expanded_preflight_matrix,
    write_expanded_static_summary,
)
from revision_artifacts import AttemptRecord, revision_run_dir, sha256_file


PHASE041_SIDECAR_ROOT = Path("expanded_captcha_data/phase04_1")
PHASE041_EVALUATOR_SLICE = PHASE041_SIDECAR_ROOT / "evaluator_slice"
PHASE041_STATIC_SUPPLEMENTAL_RUN_ID = "phase04_1_static_supplemental"
PHASE041_ADAPTIVE_SUPPLEMENTAL_RUN_ID = "phase04_1_adaptive_supplemental"
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


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return path


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


def _validate_materialized_dataset_root(
    dataset_root: Path,
    task_types: list[str],
) -> None:
    if not dataset_root.is_dir():
        raise FileNotFoundError(f"materialized dataset root does not exist: {dataset_root}")
    for task_type in task_types:
        ground_truth_path = dataset_root / task_type / "ground_truth.json"
        ground_truth = _read_json(ground_truth_path)
        if not isinstance(ground_truth, dict) or not ground_truth:
            raise ValueError(f"{ground_truth_path} must contain a non-empty JSON object")


def _preflight_report_payload(report: object) -> dict[str, Any]:
    if hasattr(report, "model_dump"):
        return report.model_dump(mode="json")  # type: ignore[no-any-return]
    if isinstance(report, dict):
        return dict(report)
    raise TypeError("preflight report must be a pydantic model or dict")


def _adaptive_preflight_report_payload(report: object) -> dict[str, Any]:
    if hasattr(report, "model_dump"):
        return report.model_dump(mode="json")  # type: ignore[no-any-return]
    if isinstance(report, dict):
        return dict(report)
    raise TypeError("adaptive preflight report must be a pydantic model or dict")


def build_static_preflight_matrix(
    manifest_path: str | Path = PHASE041_SIDECAR_ROOT / "manifest.json",
    dataset_root: str | Path = PHASE041_EVALUATOR_SLICE,
    results_dir: str | Path = "results",
    output_root: str | Path = "results/revision",
    run_id: str = PHASE041_STATIC_SUPPLEMENTAL_RUN_ID,
    prompts_file: str | Path = "prompts_optimized.yaml",
    prompt_mode: str = "opt",
    max_attempts: int = 1,
    resume: bool = True,
    overwrite: bool = False,
    write_reports: bool = False,
    pricing_file: str | Path | None = None,
) -> list[ExpandedPreflightMatrixRow]:
    if overwrite and resume:
        raise ValueError("overwrite and resume are mutually exclusive")
    if max_attempts != 1:
        raise ValueError("Phase 04.1 static supplemental runs require max_attempts=1")

    manifest_path = Path(manifest_path)
    dataset_root = Path(dataset_root)
    output_root = Path(output_root)
    rows = load_phase041_manifest(manifest_path, run_id=run_id)
    validate_phase041_manifest(rows)
    task_types = sorted({row.task_type for row in rows})
    _validate_materialized_dataset_root(dataset_root, task_types)

    run_matrix_rows = build_paper_facing_run_matrix(
        results_dir=Path(results_dir),
        materialized_dataset_root=dataset_root,
        output_root=output_root,
        run_id_prefix=run_id,
    )
    static_run_dir = revision_run_dir(output_root, run_id)
    preflight_reports_dir = static_run_dir / "preflight_reports"
    manifest_hash = sha256_file(manifest_path) or ""

    preflight_rows: list[ExpandedPreflightMatrixRow] = []
    for matrix_row in run_matrix_rows:
        effective_overwrite = overwrite or matrix_row.overwrite
        effective_resume = False if effective_overwrite else (resume or matrix_row.resume)
        preflight_args = argparse.Namespace(
            dataset_root=str(dataset_root),
            types=list(matrix_row.task_types),
            prompts_file=str(prompts_file),
            few_shot_config=None,
            prompt_prefix=None,
            prompt_suffix=None,
            pricing_file=str(pricing_file) if pricing_file else None,
            output_root=str(output_root),
            run_id=matrix_row.run_id,
            provider=matrix_row.provider,
            model=matrix_row.model,
            prompt_mode=prompt_mode,
            max_per_type=None,
            max_attempts=max_attempts,
            overwrite=effective_overwrite,
            resume=effective_resume,
            write_report=False,
        )
        report = revision_preflight.build_report(preflight_args)
        report_payload = _preflight_report_payload(report)
        report_path = preflight_reports_dir / f"{_slug(matrix_row.provider_model)}.json"
        if write_reports:
            _write_json(report_path, report_payload)

        preflight_rows.append(
            ExpandedPreflightMatrixRow(
                run_id=matrix_row.run_id,
                provider=matrix_row.provider,
                model=matrix_row.model,
                provider_model=matrix_row.provider_model,
                run_scope="static",
                manifest_path=str(manifest_path),
                manifest_sha256=manifest_hash,
                sidecar_dataset_root=str(manifest_path.parent),
                materialized_dataset_root=str(dataset_root),
                task_types=list(matrix_row.task_types),
                prompt_config=dict(report_payload.get("prompt_config") or {}),
                expected_request_count=int(report_payload.get("expected_request_count") or 0),
                cost_preview=dict(report_payload.get("cost_preview") or {}),
                output_dir=str(report_payload.get("output_dir") or matrix_row.output_root),
                preflight_report_path=str(report_path),
                overwrite=effective_overwrite,
                resume=effective_resume,
            )
        )

    write_expanded_preflight_matrix(
        static_run_dir / "expanded_preflight_matrix.csv",
        static_run_dir / "expanded_preflight_matrix.json",
        preflight_rows,
    )
    return preflight_rows


def _load_preflight_matrix(path: Path) -> list[ExpandedPreflightMatrixRow]:
    if not path.is_file():
        raise FileNotFoundError(f"preflight matrix does not exist: {path}")
    payload = _read_json(path)
    raw_rows = payload.get("rows") if isinstance(payload, dict) else payload
    if not isinstance(raw_rows, list):
        raise ValueError("preflight matrix must contain a rows array")
    return [ExpandedPreflightMatrixRow.model_validate(row) for row in raw_rows]


def _run_eval_with_supported_kwargs(kwargs: dict[str, object]) -> dict[str, Any]:
    signature = inspect.signature(run_eval.run_eval)
    supports_arbitrary_kwargs = any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )
    if supports_arbitrary_kwargs:
        return run_eval.run_eval(**kwargs)
    supported = {key: value for key, value in kwargs.items() if key in signature.parameters}
    return run_eval.run_eval(**supported)


def _runtime_model_kwargs(provider: str, model_label: str) -> dict[str, object]:
    if provider == "openai" and model_label.startswith("gpt-5.1_"):
        effort = model_label.rsplit("_", 1)[1]
        if effort == "none":
            return {
                "model": "gpt-5.1",
                "thinking": False,
                "thinking_options": None,
            }
        return {
            "model": "gpt-5.1",
            "thinking": True,
            "thinking_options": {"effort": effort},
        }
    return {
        "model": model_label,
        "thinking": False,
        "thinking_options": None,
    }


def _load_attempts(path: Path) -> list[AttemptRecord]:
    if not path.is_file():
        raise FileNotFoundError(f"attempt log does not exist: {path}")
    attempts = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                attempts.append(AttemptRecord.model_validate_json(line))
    return attempts


def _failure_bucket(attempt: AttemptRecord) -> str | None:
    if attempt.correct:
        return None
    category = (attempt.error_category or "").lower()
    if not category:
        return "scientific_wrong_count"
    if (
        category == "parse_error"
        and not attempt.parsed_answer
        and not attempt.tokens_in
        and not attempt.tokens_out
        and not attempt.cost_usd
    ):
        return "infrastructure_failure_count"
    if any(token in category for token in ("infra", "provider", "network", "timeout", "rate")):
        return "infrastructure_failure_count"
    return "protocol_failure_count"


def _build_static_summary_rows(
    matrix_rows: list[ExpandedPreflightMatrixRow],
    manifest_rows: list[ExpandedDatasetManifestRow],
) -> list[ExpandedStaticSummaryRow]:
    manifest_by_task = {row.task_type: row for row in manifest_rows}
    summary_rows: list[ExpandedStaticSummaryRow] = []
    for matrix_row in matrix_rows:
        run_dir = Path(matrix_row.output_dir)
        attempts = _load_attempts(run_dir / "attempts.jsonl")
        counts_by_task: dict[str, dict[str, int]] = defaultdict(
            lambda: {
                "attempt_count": 0,
                "success_count": 0,
                "scientific_wrong_count": 0,
                "protocol_failure_count": 0,
                "infrastructure_failure_count": 0,
            }
        )
        for attempt in attempts:
            counts = counts_by_task[attempt.task_type]
            counts["attempt_count"] += 1
            counts["success_count"] += int(attempt.correct)
            bucket = _failure_bucket(attempt)
            if bucket:
                counts[bucket] += 1

        for task_type, counts in sorted(counts_by_task.items()):
            manifest_row = manifest_by_task.get(task_type)
            summary_rows.append(
                ExpandedStaticSummaryRow(
                    run_id=matrix_row.run_id,
                    provider=matrix_row.provider,
                    model=matrix_row.model,
                    provider_model=matrix_row.provider_model,
                    task_type=task_type,
                    task_family=manifest_row.task_family if manifest_row else "unknown",
                    evidence_origin=(
                        manifest_row.evidence_origin if manifest_row else "supplemented_category"
                    ),
                    slice_type=manifest_row.slice_type if manifest_row else "supplement_existing",
                    sample_count=manifest_row.sample_count if manifest_row else 0,
                    attempt_count=counts["attempt_count"],
                    success_count=counts["success_count"],
                    scientific_wrong_count=counts["scientific_wrong_count"],
                    protocol_failure_count=counts["protocol_failure_count"],
                    infrastructure_failure_count=counts["infrastructure_failure_count"],
                    pass_rate=(
                        counts["success_count"] / counts["attempt_count"]
                        if counts["attempt_count"]
                        else None
                    ),
                    run_manifest_path=str(run_dir / "run_manifest.json"),
                    attempt_log_path=str(run_dir / "attempts.jsonl"),
                    summary_source_path=str(run_dir / "summary.json"),
                    claim_use="main_body_direct_evidence",
                )
            )
    return summary_rows


def collect_static_supplemental_runs(
    preflight_matrix_path: str | Path,
    output_root: str | Path = "results/revision",
    manifest_path: str | Path | None = None,
    *,
    resume: bool = True,
    overwrite: bool = False,
    secrets_file: str | Path = "secrets.yaml",
    stream: bool = True,
    timeout_sec: float = 600.0,
    seed: int = 1234,
) -> dict[str, object]:
    if overwrite and resume:
        raise ValueError("overwrite and resume are mutually exclusive")

    preflight_matrix_path = Path(preflight_matrix_path)
    output_root = Path(output_root)
    matrix_rows = _load_preflight_matrix(preflight_matrix_path)
    if not matrix_rows:
        raise ValueError("preflight matrix must contain at least one row")

    resolved_manifest_path = Path(manifest_path or matrix_rows[0].manifest_path)
    manifest_rows = load_phase041_manifest(
        resolved_manifest_path,
        run_id=PHASE041_STATIC_SUPPLEMENTAL_RUN_ID,
    )
    validate_phase041_manifest(manifest_rows)

    run_results: list[dict[str, Any]] = []
    for matrix_row in matrix_rows:
        prompts_file = matrix_row.prompt_config.get("prompts_file") or "prompts_optimized.yaml"
        runtime_model = _runtime_model_kwargs(matrix_row.provider, matrix_row.model)
        run_kwargs: dict[str, object] = {
            "dataset_root": matrix_row.materialized_dataset_root,
            "types": list(matrix_row.task_types),
            "provider": matrix_row.provider,
            "model": runtime_model["model"],
            "max_per_type": None,
            "out_csv": str(Path(matrix_row.output_dir) / "results.csv"),
            "secrets_file": str(secrets_file),
            "stream": stream,
            "timeout_sec": timeout_sec,
            "seed": seed,
            "prompts_file": str(prompts_file),
            "prompt_mode": "opt",
            "revision_run_id": matrix_row.run_id,
            "revision_output_root": str(output_root),
            "write_attempts": True,
            "overwrite_revision_output": overwrite,
            "resume_revision_output": resume,
            "max_attempts": 1,
            "thinking": runtime_model["thinking"],
            "thinking_options": runtime_model["thinking_options"],
        }
        run_results.append(_run_eval_with_supported_kwargs(run_kwargs))

    summary_rows = _build_static_summary_rows(matrix_rows, manifest_rows)
    summary_dir = preflight_matrix_path.parent
    summary_csv = summary_dir / "expanded_static_summary.csv"
    summary_json = summary_dir / "expanded_static_summary.json"
    write_expanded_static_summary(summary_csv, summary_json, summary_rows)
    return {
        "run_count": len(matrix_rows),
        "run_result_count": len(run_results),
        "static_summary_row_count": len(summary_rows),
        "static_summary_csv": str(summary_csv),
        "static_summary_json": str(summary_json),
    }


def _adaptive_eligible_task_types(
    rows: list[ExpandedDatasetManifestRow],
    requested_task_types: list[str] | None = None,
) -> list[str]:
    eligible = {row.task_type for row in rows if row.adaptive_eligible}
    if requested_task_types:
        requested = set(requested_task_types)
        ineligible = requested - eligible
        if ineligible:
            raise ValueError(
                "requested adaptive task types must have adaptive_eligible=true: "
                f"{sorted(ineligible)}"
            )
        return sorted(requested)
    return sorted(eligible)


def build_adaptive_preflight_matrix(
    manifest_path: str | Path = PHASE041_SIDECAR_ROOT / "manifest.json",
    dataset_root: str | Path = PHASE041_EVALUATOR_SLICE,
    results_dir: str | Path = "results",
    output_root: str | Path = "results/revision",
    run_id: str = PHASE041_ADAPTIVE_SUPPLEMENTAL_RUN_ID,
    prompts_file: str | Path = "prompts_optimized.yaml",
    prompt_mode: str = "opt",
    attempt_budget_k: int = 6,
    seed: int = 1234,
    resume: bool = True,
    overwrite: bool = False,
    write_reports: bool = False,
    pricing_file: str | Path | None = None,
    requested_task_types: list[str] | None = None,
) -> list[ExpandedPreflightMatrixRow]:
    del seed
    if overwrite and resume:
        raise ValueError("overwrite and resume are mutually exclusive")
    if attempt_budget_k != 6:
        raise ValueError("Phase 04.1 adaptive supplemental runs require attempt_budget_k=6")

    manifest_path = Path(manifest_path)
    dataset_root = Path(dataset_root)
    output_root = Path(output_root)
    rows = load_phase041_manifest(manifest_path, run_id=run_id)
    validate_phase041_manifest(rows)
    task_types = _adaptive_eligible_task_types(rows, requested_task_types)
    _validate_materialized_dataset_root(dataset_root, task_types)

    run_matrix_rows = build_paper_facing_run_matrix(
        results_dir=Path(results_dir),
        materialized_dataset_root=dataset_root,
        output_root=output_root,
        run_id_prefix=run_id,
    )
    adaptive_run_dir = revision_run_dir(output_root, run_id)
    reports_dir = adaptive_run_dir / "adaptive_preflight_reports"
    manifest_hash = sha256_file(manifest_path) or ""

    preflight_rows: list[ExpandedPreflightMatrixRow] = []
    for matrix_row in run_matrix_rows:
        effective_overwrite = overwrite or matrix_row.overwrite
        effective_resume = False if effective_overwrite else (resume or matrix_row.resume)
        preflight_args = argparse.Namespace(
            dataset_root=str(dataset_root),
            types=task_types,
            prompts_file=str(prompts_file),
            few_shot_config=None,
            prompt_prefix=None,
            prompt_suffix=None,
            pricing_file=str(pricing_file) if pricing_file else None,
            output_root=str(output_root),
            run_id=matrix_row.run_id,
            provider=matrix_row.provider,
            model=matrix_row.model,
            prompt_mode=prompt_mode,
            max_per_type=None,
            attempt_budget_k=attempt_budget_k,
            sampling_mode=SAMPLING_MODE,
            feedback_mode=FEEDBACK_MODE,
            memory_mode=MEMORY_MODE,
            stopping_rule=STOPPING_RULE,
            overwrite=effective_overwrite,
            resume=effective_resume,
            write_report=False,
        )
        report = adaptive_preflight.build_report(preflight_args)
        report_payload = _adaptive_preflight_report_payload(report)
        report_path = reports_dir / f"{_slug(matrix_row.provider_model)}.json"
        if write_reports:
            _write_json(report_path, report_payload)

        preflight_rows.append(
            ExpandedPreflightMatrixRow(
                run_id=matrix_row.run_id,
                provider=matrix_row.provider,
                model=matrix_row.model,
                provider_model=matrix_row.provider_model,
                run_scope="adaptive",
                manifest_path=str(manifest_path),
                manifest_sha256=manifest_hash,
                sidecar_dataset_root=str(manifest_path.parent),
                materialized_dataset_root=str(dataset_root),
                task_types=task_types,
                prompt_config=dict(report_payload.get("prompt_config") or {}),
                expected_request_count=int(
                    report_payload.get("expected_request_count_max")
                    or report_payload.get("expected_request_count")
                    or 0
                ),
                cost_preview=dict(report_payload.get("cost_preview") or {}),
                output_dir=str(report_payload.get("output_dir") or matrix_row.output_root),
                preflight_report_path=str(report_path),
                overwrite=effective_overwrite,
                resume=effective_resume,
                attempt_budget_k=attempt_budget_k,
                sampling_mode=str(report_payload.get("sampling_mode") or SAMPLING_MODE),
                feedback_mode=str(report_payload.get("feedback_mode") or FEEDBACK_MODE),
                memory_mode=str(report_payload.get("memory_mode") or MEMORY_MODE),
                stopping_rule=str(report_payload.get("stopping_rule") or STOPPING_RULE),
                solve_request_count=int(report_payload.get("solve_request_count") or 0),
                reflection_request_count_max=int(
                    report_payload.get("reflection_request_count_max") or 0
                ),
                expected_request_count_max=int(
                    report_payload.get("expected_request_count_max") or 0
                ),
            )
        )

    write_expanded_preflight_matrix(
        adaptive_run_dir / "expanded_adaptive_preflight_matrix.csv",
        adaptive_run_dir / "expanded_adaptive_preflight_matrix.json",
        preflight_rows,
    )
    return preflight_rows


def _load_adaptive_summary_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"adaptive summary does not exist: {path}")
    payload = _read_json(path)
    rows = payload.get("rows") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError(f"adaptive summary must contain rows: {path}")
    return [row for row in rows if isinstance(row, dict)]


def _build_expanded_adaptive_summary_rows(
    matrix_rows: list[ExpandedPreflightMatrixRow],
    manifest_rows: list[ExpandedDatasetManifestRow],
) -> list[ExpandedAdaptiveSummaryRow]:
    manifest_by_task = {row.task_type: row for row in manifest_rows}
    expanded_rows: list[ExpandedAdaptiveSummaryRow] = []
    for matrix_row in matrix_rows:
        run_dir = Path(matrix_row.output_dir)
        source_summary_path = run_dir / "adaptive_summary.json"
        for row in _load_adaptive_summary_rows(source_summary_path):
            task_type = str(row.get("task_type") or "")
            manifest_row = manifest_by_task.get(task_type)
            expanded_rows.append(
                ExpandedAdaptiveSummaryRow(
                    run_id=matrix_row.run_id,
                    provider=matrix_row.provider,
                    model=matrix_row.model,
                    provider_model=matrix_row.provider_model,
                    task_type=task_type,
                    task_family=manifest_row.task_family if manifest_row else "unknown",
                    evidence_origin=(
                        manifest_row.evidence_origin if manifest_row else "supplemented_category"
                    ),
                    slice_type=manifest_row.slice_type if manifest_row else "supplement_existing",
                    sample_count=manifest_row.sample_count if manifest_row else 0,
                    session_count=1,
                    attempt_budget_k=int(row.get("attempt_budget_k") or 0),
                    success_count=int(row.get("n_success") or 0),
                    scientific_wrong_count=int(row.get("scientific_wrong_count") or 0),
                    protocol_failure_count=int(row.get("protocol_failure_count") or 0),
                    infrastructure_failure_count=int(
                        row.get("infrastructure_failure_count") or 0
                    ),
                    adaptive_success_rate=float(row.get("success_rate") or 0.0),
                    feedback_mode=str(row.get("feedback_mode") or FEEDBACK_MODE),
                    memory_mode=str(row.get("memory_mode") or MEMORY_MODE),
                    stopping_rule=str(row.get("stopping_reason") or STOPPING_RULE),
                    run_manifest_path=str(run_dir / "run_manifest.json"),
                    adaptive_attempt_log_path=str(run_dir / "adaptive_attempts.jsonl"),
                    adaptive_summary_source_path=str(source_summary_path),
                    claim_use="main_body_caveated",
                )
            )
    return expanded_rows


def collect_adaptive_supplemental_runs(
    preflight_matrix_path: str | Path,
    output_root: str | Path = "results/revision",
    manifest_path: str | Path | None = None,
    *,
    resume: bool = True,
    overwrite: bool = False,
    secrets_file: str | Path = "secrets.yaml",
    stream: bool = False,
    timeout_sec: float = 600.0,
    seed: int = 1234,
) -> dict[str, object]:
    if overwrite and resume:
        raise ValueError("overwrite and resume are mutually exclusive")

    preflight_matrix_path = Path(preflight_matrix_path)
    output_root = Path(output_root)
    matrix_rows = _load_preflight_matrix(preflight_matrix_path)
    if not matrix_rows:
        raise ValueError("preflight matrix must contain at least one row")

    resolved_manifest_path = Path(manifest_path or matrix_rows[0].manifest_path)
    manifest_rows = load_phase041_manifest(
        resolved_manifest_path,
        run_id=PHASE041_ADAPTIVE_SUPPLEMENTAL_RUN_ID,
    )
    validate_phase041_manifest(manifest_rows)

    run_results: list[dict[str, Any]] = []
    for matrix_row in matrix_rows:
        if matrix_row.run_scope != "adaptive":
            raise ValueError(f"preflight row is not adaptive: {matrix_row.run_id}")
        if matrix_row.attempt_budget_k != 6:
            raise ValueError(f"adaptive row must have attempt_budget_k=6: {matrix_row.run_id}")
        runtime_model = _runtime_model_kwargs(matrix_row.provider, matrix_row.model)
        prompts_file = matrix_row.prompt_config.get("prompts_file") or "prompts_optimized.yaml"
        run_results.append(
            adaptive_attacker.run_adaptive_experiment(
                dataset_root=matrix_row.materialized_dataset_root,
                types=list(matrix_row.task_types),
                provider=matrix_row.provider,
                model=str(runtime_model["model"]),
                run_id=matrix_row.run_id,
                output_root=str(output_root),
                attempt_budget_k=6,
                max_per_type=None,
                prompts_file=str(prompts_file),
                prompt_mode="opt",
                secrets_file=str(secrets_file),
                timeout_sec=timeout_sec,
                seed=seed,
                stream=stream,
                overwrite=overwrite,
                resume=resume,
                thinking=bool(runtime_model["thinking"]),
                thinking_options=runtime_model["thinking_options"],
            )
        )

    summary_rows = _build_expanded_adaptive_summary_rows(matrix_rows, manifest_rows)
    summary_dir = preflight_matrix_path.parent
    summary_csv = summary_dir / "expanded_adaptive_summary.csv"
    summary_json = summary_dir / "expanded_adaptive_summary.json"
    write_expanded_adaptive_summary(summary_csv, summary_json, summary_rows)
    return {
        "run_count": len(matrix_rows),
        "run_result_count": len(run_results),
        "adaptive_summary_row_count": len(summary_rows),
        "adaptive_summary_csv": str(summary_csv),
        "adaptive_summary_json": str(summary_json),
    }


def _run_preflight_matrix(args: argparse.Namespace) -> dict[str, object]:
    rows = build_static_preflight_matrix(
        manifest_path=Path(args.manifest),
        dataset_root=Path(args.dataset_root),
        results_dir=Path(args.results_dir),
        output_root=Path(args.output_root),
        run_id=args.run_id,
        prompts_file=Path(args.prompts_file),
        prompt_mode=args.prompt_mode,
        max_attempts=args.max_attempts,
        resume=args.resume,
        overwrite=args.overwrite,
        write_reports=args.write_reports,
        pricing_file=Path(args.pricing_file) if args.pricing_file else None,
    )
    run_dir = revision_run_dir(args.output_root, args.run_id)
    return {
        "row_count": len(rows),
        "output_csv": str(run_dir / "expanded_preflight_matrix.csv"),
        "output_json": str(run_dir / "expanded_preflight_matrix.json"),
        "preflight_reports_dir": str(run_dir / "preflight_reports"),
    }


def _run_collect_static(args: argparse.Namespace) -> dict[str, object]:
    return collect_static_supplemental_runs(
        preflight_matrix_path=Path(args.preflight_matrix),
        output_root=Path(args.output_root),
        manifest_path=Path(args.manifest) if args.manifest else None,
        resume=args.resume,
        overwrite=args.overwrite,
        secrets_file=Path(args.secrets_file),
        stream=not args.no_stream,
        timeout_sec=args.timeout_sec,
        seed=args.seed,
    )


def _run_adaptive_preflight_matrix(args: argparse.Namespace) -> dict[str, object]:
    requested_task_types = args.types if args.types else None
    rows = build_adaptive_preflight_matrix(
        manifest_path=Path(args.manifest),
        dataset_root=Path(args.dataset_root),
        results_dir=Path(args.results_dir),
        output_root=Path(args.output_root),
        run_id=args.run_id,
        prompts_file=Path(args.prompts_file),
        prompt_mode=args.prompt_mode,
        attempt_budget_k=args.attempt_budget_k,
        seed=args.seed,
        resume=args.resume,
        overwrite=args.overwrite,
        write_reports=args.write_reports,
        pricing_file=Path(args.pricing_file) if args.pricing_file else None,
        requested_task_types=requested_task_types,
    )
    run_dir = revision_run_dir(args.output_root, args.run_id)
    return {
        "row_count": len(rows),
        "output_csv": str(run_dir / "expanded_adaptive_preflight_matrix.csv"),
        "output_json": str(run_dir / "expanded_adaptive_preflight_matrix.json"),
        "adaptive_preflight_reports_dir": str(run_dir / "adaptive_preflight_reports"),
    }


def _run_collect_adaptive(args: argparse.Namespace) -> dict[str, object]:
    return collect_adaptive_supplemental_runs(
        preflight_matrix_path=Path(args.preflight_matrix),
        output_root=Path(args.output_root),
        manifest_path=Path(args.manifest) if args.manifest else None,
        resume=args.resume,
        overwrite=args.overwrite,
        secrets_file=Path(args.secrets_file),
        stream=not args.no_stream,
        timeout_sec=args.timeout_sec,
        seed=args.seed,
    )


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

    preflight_matrix = subparsers.add_parser(
        "preflight-matrix",
        help="Build static supplemental preflight reports for all paper-facing rows.",
    )
    preflight_matrix.add_argument(
        "--manifest",
        default=str(PHASE041_SIDECAR_ROOT / "manifest.json"),
    )
    preflight_matrix.add_argument("--dataset-root", default=str(PHASE041_EVALUATOR_SLICE))
    preflight_matrix.add_argument("--results-dir", default="./results")
    preflight_matrix.add_argument("--output-root", default="./results/revision")
    preflight_matrix.add_argument("--run-id", default=PHASE041_STATIC_SUPPLEMENTAL_RUN_ID)
    preflight_matrix.add_argument("--prompts-file", default="./prompts_optimized.yaml")
    preflight_matrix.add_argument(
        "--prompt-mode",
        choices=["auto", "gt", "opt"],
        default="opt",
    )
    preflight_matrix.add_argument("--pricing-file", default=None)
    preflight_matrix.add_argument("--max-attempts", type=int, default=1)
    preflight_matrix.add_argument("--overwrite", action="store_true")
    preflight_matrix.add_argument("--resume", action="store_true")
    preflight_matrix.add_argument("--write-reports", action="store_true")

    collect_static = subparsers.add_parser(
        "collect-static",
        help="Run static supplemental revision evaluations from a preflight matrix.",
    )
    collect_static.add_argument(
        "--preflight-matrix",
        default=str(
            Path("results/revision")
            / PHASE041_STATIC_SUPPLEMENTAL_RUN_ID
            / "expanded_preflight_matrix.json"
        ),
    )
    collect_static.add_argument("--output-root", default="./results/revision")
    collect_static.add_argument("--manifest", default=None)
    collect_static.add_argument("--secrets-file", default="./secrets.yaml")
    collect_static.add_argument("--resume", action="store_true")
    collect_static.add_argument("--overwrite", action="store_true")
    collect_static.add_argument("--no-stream", action="store_true")
    collect_static.add_argument("--timeout-sec", type=float, default=600.0)
    collect_static.add_argument("--seed", type=int, default=1234)

    adaptive_preflight_matrix = subparsers.add_parser(
        "adaptive-preflight-matrix",
        help="Build adaptive supplemental preflight reports for all paper-facing rows.",
    )
    adaptive_preflight_matrix.add_argument(
        "--manifest",
        default=str(PHASE041_SIDECAR_ROOT / "manifest.json"),
    )
    adaptive_preflight_matrix.add_argument("--dataset-root", default=str(PHASE041_EVALUATOR_SLICE))
    adaptive_preflight_matrix.add_argument("--results-dir", default="./results")
    adaptive_preflight_matrix.add_argument("--output-root", default="./results/revision")
    adaptive_preflight_matrix.add_argument(
        "--run-id",
        default=PHASE041_ADAPTIVE_SUPPLEMENTAL_RUN_ID,
    )
    adaptive_preflight_matrix.add_argument("--prompts-file", default="./prompts_optimized.yaml")
    adaptive_preflight_matrix.add_argument(
        "--prompt-mode",
        choices=["auto", "gt", "opt"],
        default="opt",
    )
    adaptive_preflight_matrix.add_argument("--pricing-file", default=None)
    adaptive_preflight_matrix.add_argument("--attempt-budget-k", type=int, default=6)
    adaptive_preflight_matrix.add_argument("--seed", type=int, default=1234)
    adaptive_preflight_matrix.add_argument("--overwrite", action="store_true")
    adaptive_preflight_matrix.add_argument("--resume", action="store_true")
    adaptive_preflight_matrix.add_argument("--write-reports", action="store_true")
    adaptive_preflight_matrix.add_argument("--types", nargs="*", default=None)

    collect_adaptive = subparsers.add_parser(
        "collect-adaptive",
        help="Run adaptive supplemental revision evaluations from a preflight matrix.",
    )
    collect_adaptive.add_argument(
        "--preflight-matrix",
        default=str(
            Path("results/revision")
            / PHASE041_ADAPTIVE_SUPPLEMENTAL_RUN_ID
            / "expanded_adaptive_preflight_matrix.json"
        ),
    )
    collect_adaptive.add_argument("--output-root", default="./results/revision")
    collect_adaptive.add_argument("--manifest", default=None)
    collect_adaptive.add_argument("--secrets-file", default="./secrets.yaml")
    collect_adaptive.add_argument("--resume", action="store_true")
    collect_adaptive.add_argument("--overwrite", action="store_true")
    collect_adaptive.add_argument("--no-stream", action="store_true")
    collect_adaptive.add_argument("--timeout-sec", type=float, default=600.0)
    collect_adaptive.add_argument("--seed", type=int, default=1234)

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
        elif args.command == "preflight-matrix":
            summary = _run_preflight_matrix(args)
        elif args.command == "collect-static":
            summary = _run_collect_static(args)
        elif args.command == "adaptive-preflight-matrix":
            summary = _run_adaptive_preflight_matrix(args)
        elif args.command == "collect-adaptive":
            summary = _run_collect_adaptive(args)
        else:
            parser.error(f"unknown command: {args.command}")
    except (
        OSError,
        TypeError,
        ValueError,
        ValidationError,
        json.JSONDecodeError,
    ) as exc:
        parser.error(str(exc))

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
