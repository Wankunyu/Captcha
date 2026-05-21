import argparse
import hashlib
import json
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from PIL import Image
from pydantic import ValidationError

from phase042_artifacts import (
    PHASE042_GPT_IMAGE_SOURCE_KIND,
    PHASE042_REAL_EXTERNAL_SOURCE_KINDS,
    PHASE042_SELECTED_SOURCE_KINDS,
    Phase042SelectedManifestRow,
    Phase042ValidationReportRow,
    write_phase042_selected_manifest,
    write_phase042_validation_report,
)


PHASE042_SIDECAR_ROOT = Path("expanded_captcha_data/phase04_2")
PHASE042_CANDIDATES_ROOT = PHASE042_SIDECAR_ROOT / "candidates"
PHASE042_VALIDATION_REPORT_CSV = PHASE042_SIDECAR_ROOT / "phase042_validation_report.csv"
PHASE042_VALIDATION_REPORT_JSON = PHASE042_SIDECAR_ROOT / "phase042_validation_report.json"
PHASE042_SELECTED_MANIFEST_CSV = PHASE042_SIDECAR_ROOT / "phase042_selected_manifest.csv"
PHASE042_SELECTED_MANIFEST_JSON = PHASE042_SIDECAR_ROOT / "phase042_selected_manifest.json"
PHASE042_NOVELTY_HASH_REPORT_JSON = PHASE042_SIDECAR_ROOT / "novelty_hash_report.json"
PHASE042_EVALUATOR_SLICE = PHASE042_SIDECAR_ROOT / "evaluator_slice"
PHASE042_ADAPTIVE_EVALUATOR_SLICE = PHASE042_SIDECAR_ROOT / "adaptive_evaluator_slice"
PHASE042_TARGET_TASK_TYPES = (
    "Dice_Count",
    "Click_Order",
    "Patch_Select",
    "Geometry_Click",
    "Symbol_Count",
    "Relation_Match",
    "Hole_Counting",
)
PHASE042_TARGET_NEW_TASK_TYPES = {"Symbol_Count", "Relation_Match", "Hole_Counting"}
PHASE042_ORIGINAL_HARD_TASK_TYPES = (
    "Dice_Count",
    "Place_Dot",
    "Pick_Area",
    "Click_Order",
    "Patch_Select",
    "Rotation_Match",
)
PHASE042_ADAPTIVE_TASK_TYPES = (
    *PHASE042_ORIGINAL_HARD_TASK_TYPES,
    "Symbol_Count",
    "Relation_Match",
    "Hole_Counting",
)
PHASE042_MIN_SAMPLES_PER_CATEGORY = 10
PHASE042_SOURCE_PRIORITY = (
    "peer_reviewed_paper_dataset",
    "open_source_dataset",
    "gpt_image_open_captchaworld_style",
)

PHASE042_INVALID_REFERENCE_MARKERS = (
    "phase04_1",
    "synthetic_fixture",
    "Copied from existing local captcha_data",
    "Scripted local prototype",
)
IMAGE_SUFFIXES = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
PHASE042_TASK_FAMILIES = {
    "Dice_Count": "Counting",
    "Click_Order": "Ordering",
    "Patch_Select": "Spatial Selection",
    "Geometry_Click": "Spatial Precision",
    "Symbol_Count": "Counting",
    "Relation_Match": "Relational Matching",
    "Hole_Counting": "Counting",
}


def _stable_text(value: object) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    except TypeError:
        return str(value)


def assert_no_phase041_reference(value: object, *, context: str) -> None:
    text = _stable_text(value).lower()
    for marker in PHASE042_INVALID_REFERENCE_MARKERS:
        if marker.lower() in text:
            raise ValueError(
                f"{context} must not reference invalid Phase 04.1/source marker: "
                f"{marker}"
            )


def normalize_phase042_candidate_path(raw_path: str, *, context: str) -> str:
    assert_no_phase041_reference(raw_path, context=context)
    path = Path(raw_path)
    if path.is_absolute():
        raise ValueError(f"{context} must be relative to the project root")
    if ".." in path.parts:
        raise ValueError(f"{context} must not contain path traversal")
    try:
        path.relative_to(PHASE042_CANDIDATES_ROOT)
    except ValueError as exc:
        raise ValueError(
            f"{context} must resolve under {PHASE042_CANDIDATES_ROOT.as_posix()}"
        ) from exc
    return path.as_posix()


def _priority_rank(source_kind: str) -> int:
    try:
        return PHASE042_SOURCE_PRIORITY.index(source_kind)
    except ValueError as exc:
        raise ValueError(
            f"source_kind must be one of {list(PHASE042_SOURCE_PRIORITY)}"
        ) from exc


def _evidence_role(source_kind: str) -> str:
    if source_kind == "gpt_image_open_captchaworld_style":
        return "fallback_direct_evidence_with_provenance_caveat"
    return "preferred_direct_evidence"


def _default_license_status(source_kind: str) -> str:
    if source_kind == "gpt_image_open_captchaworld_style":
        return "generation_metadata_required"
    return "license_review_required_before_staging"


def build_source_triage_rows(
    source_candidates: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, candidate in enumerate(source_candidates, start=1):
        assert_no_phase041_reference(candidate, context=f"source candidate {index}")
        task_type = str(candidate.get("task_type", ""))
        if task_type not in PHASE042_TARGET_TASK_TYPES:
            raise ValueError(
                f"task_type must be one of {list(PHASE042_TARGET_TASK_TYPES)}"
            )

        source_kind = str(candidate.get("source_kind", ""))
        source_priority_rank = _priority_rank(source_kind)
        candidate_path = candidate.get("candidate_path")
        row: dict[str, object] = {
            "task_type": task_type,
            "source_kind": source_kind,
            "source_priority_rank": source_priority_rank,
            "source_citation": str(candidate.get("source_citation", "")),
            "source_license": str(candidate.get("source_license", "")),
            "source_provenance_notes": str(
                candidate.get("source_provenance_notes", "")
            ),
            "sample_count_target": PHASE042_MIN_SAMPLES_PER_CATEGORY,
            "fallback_reason": str(candidate.get("fallback_reason", "")),
            "evidence_role": _evidence_role(source_kind),
            "license_status": str(
                candidate.get("license_status", _default_license_status(source_kind))
            ),
            "style_consistency_notes": str(
                candidate.get("style_consistency_notes", "")
            ),
        }
        if candidate_path is not None:
            row["candidate_path"] = normalize_phase042_candidate_path(
                str(candidate_path),
                context=f"source candidate {index} candidate_path",
            )
        rows.append(row)

    task_order = {task_type: index for index, task_type in enumerate(PHASE042_TARGET_TASK_TYPES)}
    return sorted(
        rows,
        key=lambda row: (
            task_order[str(row["task_type"])],
            int(row["source_priority_rank"]),
            str(row["source_citation"]),
            str(row.get("candidate_path", "")),
        ),
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


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
        if isinstance(puzzle_id, str) and Path(puzzle_id).suffix.lower() in IMAGE_SUFFIXES:
            referenced.add(puzzle_id)
        for value in _iter_string_values(entry):
            if Path(value).suffix.lower() in IMAGE_SUFFIXES:
                referenced.add(value)
    return sorted(referenced)


def _iter_image_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def sha256_image(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_captcha_data_hash_index(captcha_root: Path) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for path in _iter_image_files(Path(captcha_root)):
        image_hash = sha256_image(path)
        index.setdefault(image_hash, []).append(path.as_posix())
    return dict(sorted(index.items()))


def average_hash(path: Path, hash_size: int = 8) -> int:
    with Image.open(path) as image:
        gray = image.convert("L").resize((hash_size, hash_size))
        pixels = list(gray.getdata())
    threshold = sum(pixels) / len(pixels)
    bits = 0
    for index, pixel in enumerate(pixels):
        if pixel >= threshold:
            bits |= 1 << index
    return bits


def _hamming_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def _build_perceptual_index(captcha_root: Path) -> list[tuple[int, str]]:
    perceptual_index: list[tuple[int, str]] = []
    for path in _iter_image_files(Path(captcha_root)):
        try:
            perceptual_index.append((average_hash(path), path.as_posix()))
        except OSError:
            continue
    return perceptual_index


def _load_candidate_rows(candidate_manifest_path: Path) -> list[dict[str, Any]]:
    payload = _read_json(candidate_manifest_path)
    if isinstance(payload, dict):
        rows = payload.get("candidate_rows", payload.get("rows"))
    elif isinstance(payload, list):
        rows = payload
    else:
        raise ValueError("candidate manifest must be a JSON object or array")
    if not isinstance(rows, list):
        raise ValueError("candidate manifest must contain candidate_rows")
    typed_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"candidate row {index} must be a JSON object")
        typed_rows.append(dict(row))
    return typed_rows


def _resolve_candidate_image_path(raw_path: str, project_root: Path) -> Path:
    assert_no_phase041_reference(raw_path, context="candidate image path")
    path = Path(raw_path)
    if path.is_absolute():
        resolved = path.resolve()
    else:
        if ".." in path.parts:
            raise ValueError("candidate image paths must not contain path traversal")
        resolved = (project_root / path).resolve()

    candidate_root = (project_root / PHASE042_CANDIDATES_ROOT).resolve()
    captcha_root = (project_root / "captcha_data").resolve()
    if resolved == captcha_root or _is_relative_to(resolved, captcha_root):
        raise ValueError("candidate image paths must not resolve under captcha_data")
    if not _is_relative_to(resolved, candidate_root):
        raise ValueError(
            f"candidate image paths must resolve under {PHASE042_CANDIDATES_ROOT}"
        )
    return resolved


def _candidate_image_paths(row: dict[str, Any]) -> list[str]:
    raw_paths = row.get("candidate_image_paths")
    if raw_paths is None and row.get("candidate_path") is not None:
        raw_paths = [row["candidate_path"]]
    if not isinstance(raw_paths, list) or not raw_paths:
        raise ValueError("candidate_image_paths must contain at least one image path")
    paths: list[str] = []
    for value in raw_paths:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("candidate_image_paths entries must be non-empty strings")
        paths.append(value)
    return paths


def _require_candidate_text(row: dict[str, Any], field_name: str, context: str) -> None:
    value = row.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required when {context}")
    if value.strip().lower() == "pending_generation":
        raise ValueError(f"{field_name} must be final metadata, not pending_generation")


def _source_path_for_images(image_paths: list[str]) -> str:
    if not image_paths:
        return PHASE042_CANDIDATES_ROOT.as_posix()
    return Path(image_paths[0]).parent.as_posix()


def _evidence_origin(task_type: str) -> str:
    if task_type in PHASE042_TARGET_NEW_TASK_TYPES:
        return "new_category"
    return "supplemented_category"


def _slice_type(task_type: str) -> str:
    if task_type in PHASE042_TARGET_NEW_TASK_TYPES:
        return "new_category"
    return "supplement_existing"


def _selected_row_values(
    row: dict[str, Any],
    *,
    image_paths: list[str],
    exact_match_paths: list[str],
    novelty_hashes: list[str],
    novelty_hash_report_path: Path,
    perceptual_warning_count: int,
    review_warnings: list[str],
) -> dict[str, Any]:
    task_type = str(row.get("task_type", ""))
    source_kind = str(row.get("source_kind", ""))
    if source_kind == PHASE042_GPT_IMAGE_SOURCE_KIND:
        default_provenance_class = "gpt_image_generated_fallback"
    else:
        default_provenance_class = "preferred_real_external"
    return {
        "selected_id": str(row.get("selected_id") or row.get("candidate_id")),
        "candidate_id": str(row.get("candidate_id")),
        "source_path": str(row.get("source_path") or _source_path_for_images(image_paths)),
        "candidate_image_paths": image_paths,
        "source_kind": source_kind,
        "source_provenance_class": str(
            row.get("source_provenance_class") or default_provenance_class
        ),
        "source_citation": str(row.get("source_citation", "")),
        "source_license": str(row.get("source_license", "")),
        "source_provenance_notes": str(row.get("source_provenance_notes", "")),
        "evidence_origin": str(row.get("evidence_origin") or _evidence_origin(task_type)),
        "slice_type": str(row.get("slice_type") or _slice_type(task_type)),
        "task_type": task_type,
        "task_family": str(row.get("task_family") or PHASE042_TASK_FAMILIES.get(task_type, "")),
        "sample_count": len(image_paths),
        "label_format": str(row.get("label_format", "task_specific")),
        "metadata_alignment_notes": str(row.get("metadata_alignment_notes", "")),
        "answer_format_normalization": str(
            row.get("answer_format_normalization", "task-specific normalization")
        ),
        "compatibility_status": str(
            row.get("compatibility_status", "ready_for_static_pipeline")
        ),
        "evaluation_status": str(row.get("evaluation_status", "selected_for_static")),
        "limitation_notes": str(row.get("limitation_notes", "")),
        "adaptive_eligible": bool(row.get("adaptive_eligible", True)),
        "static_compatibility_notes": str(row.get("static_compatibility_notes", "")),
        "novelty_sha256": novelty_hashes,
        "novelty_hash_report_path": novelty_hash_report_path.as_posix(),
        "exact_captcha_data_match": bool(exact_match_paths),
        "perceptual_warning_count": perceptual_warning_count,
        "review_warnings": review_warnings,
        "gpt_image_generation_prompt": str(row.get("gpt_image_generation_prompt", "")),
        "gpt_image_model": str(row.get("gpt_image_model", "")),
        "gpt_image_generation_date": str(row.get("gpt_image_generation_date", "")),
        "open_captchaworld_style_rationale": str(
            row.get("open_captchaworld_style_rationale", "")
        ),
    }


def _report_row_values(
    row: dict[str, Any],
    *,
    image_paths: list[str],
    validation_status: str,
    selected_manifest_eligible: bool,
    rejection_reason: str,
    exact_match_paths: list[str],
    novelty_hashes: list[str],
    novelty_hash_report_path: Path,
    perceptual_warning_count: int,
    review_warnings: list[str],
) -> dict[str, Any]:
    return {
        "candidate_id": str(row.get("candidate_id", "")),
        "task_type": str(row.get("task_type", "")),
        "source_kind": str(row.get("source_kind", "")),
        "source_path": str(row.get("source_path") or _source_path_for_images(image_paths)),
        "candidate_image_paths": image_paths,
        "validation_status": validation_status,
        "selected_manifest_eligible": selected_manifest_eligible,
        "rejection_reason": rejection_reason,
        "exact_captcha_data_match": bool(exact_match_paths),
        "exact_captcha_data_match_paths": exact_match_paths,
        "novelty_sha256": novelty_hashes,
        "novelty_hash_report_path": novelty_hash_report_path.as_posix(),
        "perceptual_warning_count": perceptual_warning_count,
        "review_warnings": review_warnings,
    }


def _perceptual_warnings_for_paths(
    resolved_paths: list[Path],
    perceptual_index: list[tuple[int, str]],
    threshold: int,
) -> list[str]:
    warnings: list[str] = []
    if not perceptual_index:
        return warnings
    for path in resolved_paths:
        try:
            candidate_hash = average_hash(path)
        except OSError:
            continue
        for baseline_hash, baseline_path in perceptual_index:
            distance = _hamming_distance(candidate_hash, baseline_hash)
            if distance <= threshold:
                warnings.append(
                    f"perceptual near match warning: {path.as_posix()} is "
                    f"distance {distance} from {baseline_path}"
                )
                break
    return warnings


def _validate_source_specific_fields(row: dict[str, Any]) -> None:
    source_kind = str(row.get("source_kind", ""))
    if source_kind not in PHASE042_SELECTED_SOURCE_KINDS:
        raise ValueError(
            f"source_kind must be one of {sorted(PHASE042_SELECTED_SOURCE_KINDS)}"
        )
    if source_kind in PHASE042_REAL_EXTERNAL_SOURCE_KINDS:
        _require_candidate_text(row, "source_citation", "candidate is a real external row")
        _require_candidate_text(row, "source_license", "candidate is a real external row")
        _require_candidate_text(
            row,
            "source_provenance_notes",
            "candidate is a real external row",
        )
    if source_kind == PHASE042_GPT_IMAGE_SOURCE_KIND:
        _require_candidate_text(
            row,
            "source_provenance_notes",
            "candidate is a GPT Image row",
        )
        _require_candidate_text(
            row,
            "gpt_image_generation_prompt",
            "candidate is a GPT Image row",
        )
        _require_candidate_text(
            row,
            "gpt_image_model",
            "candidate is a GPT Image row",
        )
        _require_candidate_text(
            row,
            "gpt_image_generation_date",
            "candidate is a GPT Image row",
        )
        _require_candidate_text(
            row,
            "open_captchaworld_style_rationale",
            "candidate is a GPT Image row",
        )


def _validate_one_candidate(
    row: dict[str, Any],
    *,
    captcha_hash_index: dict[str, list[str]],
    perceptual_index: list[tuple[int, str]],
    novelty_hash_report_path: Path,
    project_root: Path,
    perceptual_warning_threshold: int,
) -> tuple[Phase042ValidationReportRow, Phase042SelectedManifestRow | None, list[str]]:
    image_paths: list[str] = []
    novelty_hashes: list[str] = []
    exact_match_paths: list[str] = []
    review_warnings: list[str] = []
    try:
        assert_no_phase041_reference(row, context="candidate row")
        candidate_id = row.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            raise ValueError("candidate_id is required")
        task_type = row.get("task_type")
        if task_type not in PHASE042_TARGET_TASK_TYPES:
            raise ValueError(f"task_type must be one of {list(PHASE042_TARGET_TASK_TYPES)}")
        _validate_source_specific_fields(row)
        image_paths = _candidate_image_paths(row)
        resolved_paths = [
            _resolve_candidate_image_path(raw_path, project_root)
            for raw_path in image_paths
        ]
        missing_paths = [path.as_posix() for path in resolved_paths if not path.is_file()]
        if missing_paths:
            raise FileNotFoundError(
                "missing candidate image paths: " + ", ".join(missing_paths)
            )
        for path in resolved_paths:
            image_hash = sha256_image(path)
            novelty_hashes.append(image_hash)
            exact_match_paths.extend(captcha_hash_index.get(image_hash, []))
        perceptual_warnings = _perceptual_warnings_for_paths(
            resolved_paths,
            perceptual_index,
            perceptual_warning_threshold,
        )
        review_warnings = list(perceptual_warnings)
        if exact_match_paths:
            review_warnings.insert(
                0,
                "exact SHA-256 match warning: candidate image hash already exists "
                "under current captcha_data: "
                + ", ".join(sorted(set(exact_match_paths))),
            )
        selected_row = Phase042SelectedManifestRow.model_validate(
            _selected_row_values(
                row,
                image_paths=image_paths,
                exact_match_paths=sorted(set(exact_match_paths)),
                novelty_hashes=novelty_hashes,
                novelty_hash_report_path=novelty_hash_report_path,
                perceptual_warning_count=len(perceptual_warnings),
                review_warnings=review_warnings,
            )
        )
        report_row = Phase042ValidationReportRow.model_validate(
            _report_row_values(
                row,
                image_paths=image_paths,
                validation_status="accepted",
                selected_manifest_eligible=True,
                rejection_reason="",
                exact_match_paths=sorted(set(exact_match_paths)),
                novelty_hashes=novelty_hashes,
                novelty_hash_report_path=novelty_hash_report_path,
                perceptual_warning_count=len(perceptual_warnings),
                review_warnings=review_warnings,
            )
        )
        return report_row, selected_row, review_warnings
    except (FileNotFoundError, OSError, ValueError, ValidationError) as exc:
        rejection_reason = str(exc)
        if isinstance(exc, ValidationError):
            rejection_reason = "; ".join(error["msg"] for error in exc.errors())
        if not image_paths:
            try:
                image_paths = _candidate_image_paths(row)
            except ValueError:
                image_paths = []
        report_row = Phase042ValidationReportRow.model_validate(
            _report_row_values(
                row,
                image_paths=image_paths,
                validation_status="rejected",
                selected_manifest_eligible=False,
                rejection_reason=rejection_reason,
                exact_match_paths=sorted(set(exact_match_paths)),
                novelty_hashes=novelty_hashes,
                novelty_hash_report_path=novelty_hash_report_path,
                perceptual_warning_count=len(review_warnings),
                review_warnings=review_warnings,
            )
        )
        return report_row, None, review_warnings


def validate_phase042_candidates(
    *,
    candidate_manifest_path: Path = PHASE042_SIDECAR_ROOT / "candidate_manifest.json",
    captcha_root: Path = Path("captcha_data"),
    validation_report_csv: Path = PHASE042_VALIDATION_REPORT_CSV,
    validation_report_json: Path = PHASE042_VALIDATION_REPORT_JSON,
    selected_manifest_csv: Path = PHASE042_SELECTED_MANIFEST_CSV,
    selected_manifest_json: Path = PHASE042_SELECTED_MANIFEST_JSON,
    novelty_hash_report_path: Path = PHASE042_NOVELTY_HASH_REPORT_JSON,
    perceptual_warning_threshold: int = 4,
) -> dict[str, Any]:
    project_root = Path.cwd().resolve()
    candidate_rows = _load_candidate_rows(Path(candidate_manifest_path))
    captcha_hash_index = build_captcha_data_hash_index(Path(captcha_root))
    has_existing_candidate_files = False
    for row in candidate_rows:
        try:
            raw_paths = _candidate_image_paths(row)
            resolved_paths = [
                _resolve_candidate_image_path(raw_path, project_root)
                for raw_path in raw_paths
            ]
        except ValueError:
            continue
        if any(path.is_file() for path in resolved_paths):
            has_existing_candidate_files = True
            break
    perceptual_index = (
        _build_perceptual_index(Path(captcha_root)) if has_existing_candidate_files else []
    )

    report_rows: list[Phase042ValidationReportRow] = []
    selected_rows: list[Phase042SelectedManifestRow] = []
    all_review_warnings: list[str] = []
    for row in candidate_rows:
        report_row, selected_row, review_warnings = _validate_one_candidate(
            row,
            captcha_hash_index=captcha_hash_index,
            perceptual_index=perceptual_index,
            novelty_hash_report_path=Path(novelty_hash_report_path),
            project_root=project_root,
            perceptual_warning_threshold=perceptual_warning_threshold,
        )
        report_rows.append(report_row)
        if selected_row is not None:
            selected_rows.append(selected_row)
        all_review_warnings.extend(review_warnings)

    write_phase042_validation_report(
        Path(validation_report_csv),
        Path(validation_report_json),
        report_rows,
    )
    write_phase042_selected_manifest(
        Path(selected_manifest_csv),
        Path(selected_manifest_json),
        selected_rows,
    )

    exact_match_rejection_count = sum(
        1
        for row in report_rows
        if row.exact_captcha_data_match and row.validation_status == "rejected"
    )
    exact_match_selected_count = sum(
        1
        for row in report_rows
        if row.exact_captcha_data_match and row.validation_status == "accepted"
    )
    candidate_hash_count = sum(len(row.novelty_sha256) for row in report_rows)
    review_warning_count = sum(len(row.review_warnings) for row in report_rows)
    perceptual_warning_count = sum(row.perceptual_warning_count for row in report_rows)
    novelty_payload = {
        "schema_version": "cognition.revision.phase042.novelty_hash_report.v1",
        "captcha_data_hash_index_size": len(captcha_hash_index),
        "captcha_data_image_count": sum(len(paths) for paths in captcha_hash_index.values()),
        "candidate_count": len(candidate_rows),
        "candidate_hash_count": candidate_hash_count,
        "exact_match_rejection_count": exact_match_rejection_count,
        "exact_match_selected_count": exact_match_selected_count,
        "review_warning_count": review_warning_count,
        "perceptual_near_match_warning_count": perceptual_warning_count,
        "perceptual_near_match_warnings": [
            warning
            for warning in all_review_warnings
            if warning.startswith("perceptual near match warning:")
        ],
        "review_warnings": all_review_warnings,
        "selected_count": len(selected_rows),
        "rejected_count": len(report_rows) - len(selected_rows),
        "validation_report_json": Path(validation_report_json).as_posix(),
        "selected_manifest_json": Path(selected_manifest_json).as_posix(),
    }
    _write_json(Path(novelty_hash_report_path), novelty_payload)
    return {
        "report_count": len(report_rows),
        "selected_count": len(selected_rows),
        "rejected_count": len(report_rows) - len(selected_rows),
        "validation_report_csv": Path(validation_report_csv),
        "validation_report_json": Path(validation_report_json),
        "selected_manifest_csv": Path(selected_manifest_csv),
        "selected_manifest_json": Path(selected_manifest_json),
        "novelty_hash_report": Path(novelty_hash_report_path),
    }


def _assert_selected_manifest_path(path: Path) -> None:
    normalized = path.as_posix().lower()
    if "validation_report" in normalized:
        raise ValueError("materialization must read a selected manifest, not a validation report")
    assert_no_phase041_reference(normalized, context="selected manifest path")
    if path.name not in {"phase042_selected_manifest.json", "selected_manifest.json"}:
        raise ValueError(
            "selected manifest path must be phase042_selected_manifest.json "
            "or selected_manifest.json"
        )


def load_phase042_selected_manifest(
    selected_manifest_path: str | Path = PHASE042_SELECTED_MANIFEST_JSON,
) -> list[Phase042SelectedManifestRow]:
    path = Path(selected_manifest_path)
    _assert_selected_manifest_path(path)
    payload = _read_json(path)
    assert_no_phase041_reference(payload, context="selected manifest payload")
    raw_rows = payload.get("rows") if isinstance(payload, dict) else payload
    if not isinstance(raw_rows, list):
        raise ValueError("selected manifest must contain a rows array")
    return [Phase042SelectedManifestRow.model_validate(row) for row in raw_rows]


def normalize_phase042_selected_manifest_scope(
    rows: Iterable[Phase042SelectedManifestRow | dict[str, Any]],
) -> tuple[list[Phase042SelectedManifestRow], int]:
    validated = [
        row
        if isinstance(row, Phase042SelectedManifestRow)
        else Phase042SelectedManifestRow.model_validate(row)
        for row in rows
    ]
    corrected: list[Phase042SelectedManifestRow] = []
    excluded_updated_ocw_increment_count = 0
    for row in validated:
        if row.task_type in PHASE042_TARGET_NEW_TASK_TYPES:
            corrected.append(row)
            continue
        excluded_updated_ocw_increment_count += 1

    validate_phase042_selected_manifest(corrected)
    return sorted(corrected, key=lambda row: row.task_type), excluded_updated_ocw_increment_count


def validate_phase042_selected_manifest(
    rows: Iterable[Phase042SelectedManifestRow | dict[str, Any]],
) -> list[Phase042SelectedManifestRow]:
    validated = [
        row
        if isinstance(row, Phase042SelectedManifestRow)
        else Phase042SelectedManifestRow.model_validate(row)
        for row in rows
    ]
    by_task: dict[str, list[Phase042SelectedManifestRow]] = defaultdict(list)
    for row in validated:
        assert_no_phase041_reference(row.model_dump(mode="json"), context="selected manifest row")
        if row.task_type not in PHASE042_TARGET_NEW_TASK_TYPES:
            raise ValueError(
                "corrected Phase 04.2 direct static selection is limited to "
                f"{sorted(PHASE042_TARGET_NEW_TASK_TYPES)}; got {row.task_type}"
            )
        if row.sample_count < PHASE042_MIN_SAMPLES_PER_CATEGORY:
            raise ValueError(
                f"{row.task_type} sample_count must be >= "
                f"{PHASE042_MIN_SAMPLES_PER_CATEGORY}"
            )
        by_task[row.task_type].append(row)

    task_types = set(by_task)
    if task_types != PHASE042_TARGET_NEW_TASK_TYPES:
        raise ValueError(
            "corrected Phase 04.2 selected manifest must contain exactly "
            f"{sorted(PHASE042_TARGET_NEW_TASK_TYPES)}"
        )
    duplicates = {task_type: rows for task_type, rows in by_task.items() if len(rows) != 1}
    if duplicates:
        raise ValueError(
            "corrected Phase 04.2 selected manifest requires one row per task type: "
            f"{sorted(duplicates)}"
        )
    return sorted(validated, key=lambda row: row.task_type)


def _safe_prepare_phase042_output_root(
    sidecar_root: Path,
    output_root: Path,
    *,
    overwrite: bool,
) -> Path:
    assert_no_phase041_reference(output_root.as_posix(), context="materialization output root")
    sidecar_resolved = sidecar_root.resolve()
    output_resolved = output_root.resolve()
    captcha_root = Path("captcha_data").resolve()
    if output_resolved == captcha_root or _is_relative_to(output_resolved, captcha_root):
        raise ValueError("materialization output_root must not be inside captcha_data")
    if output_resolved == sidecar_resolved:
        raise ValueError("materialization output_root must not be the sidecar root")
    if not _is_relative_to(output_resolved, sidecar_resolved):
        raise ValueError("materialization output_root must stay under Phase 04.2 sidecar root")
    if output_root.exists():
        if not overwrite:
            raise FileExistsError(f"output_root already exists: {output_root}")
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    return output_root


def _resolve_phase042_source_dir(raw_path: str, sidecar_root: Path) -> Path:
    assert_no_phase041_reference(raw_path, context="selected manifest source_path")
    path = Path(raw_path)
    if path.is_absolute():
        raise ValueError("selected manifest source_path must be relative")
    if ".." in path.parts:
        raise ValueError("selected manifest source_path must not contain path traversal")
    resolved = path.resolve()
    candidates_root = (sidecar_root / "candidates").resolve()
    if not _is_relative_to(resolved, candidates_root):
        raise ValueError("selected manifest source_path must resolve under Phase 04.2 candidates")
    return resolved


def _copy_referenced_file(source_dir: Path, output_dir: Path, relative_path: str) -> None:
    relative = Path(relative_path)
    if relative.is_absolute():
        raise ValueError(f"referenced dataset file must be relative: {relative_path}")
    if ".." in relative.parts:
        raise ValueError(
            f"referenced dataset file must not contain path traversal: {relative_path}"
        )
    source_root = source_dir.resolve()
    source_path = (source_dir / relative).resolve()
    if not _is_relative_to(source_path, source_root):
        raise ValueError(f"referenced dataset file escapes source path: {relative_path}")
    if not source_path.is_file():
        raise FileNotFoundError(str(source_path))
    output_path = output_dir / relative
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, output_path)


def _copy_task_ground_truth(
    *,
    source_dir: Path,
    task_output_root: Path,
) -> tuple[int, str]:
    source_gt_path = source_dir / "ground_truth.json"
    if not source_gt_path.is_file():
        raise FileNotFoundError(str(source_gt_path))
    ground_truth = _read_json(source_gt_path)
    if not isinstance(ground_truth, dict):
        raise ValueError(f"{source_gt_path} must contain a JSON object")
    copied_file_count = 0
    for relative_path in _referenced_files(ground_truth):
        _copy_referenced_file(source_dir, task_output_root, relative_path)
        copied_file_count += 1
    ground_truth_path = task_output_root / "ground_truth.json"
    task_output_root.mkdir(parents=True, exist_ok=True)
    with ground_truth_path.open("w", encoding="utf-8") as handle:
        json.dump(ground_truth, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return copied_file_count, ground_truth_path.as_posix()


def _write_task_materialization_metadata(
    task_output_root: Path,
    row: Phase042SelectedManifestRow,
) -> Path:
    metadata_path = task_output_root / "phase042_materialization_metadata.json"
    _write_json(
        metadata_path,
        {
            "schema_version": "cognition.revision.phase042.materialization_metadata.v1",
            "selected_id": row.selected_id,
            "candidate_id": row.candidate_id,
            "task_type": row.task_type,
            "source_kind": row.source_kind,
            "source_provenance_class": row.source_provenance_class,
            "source_citation": row.source_citation,
            "source_license": row.source_license,
            "source_provenance_notes": row.source_provenance_notes,
            "sample_count": row.sample_count,
            "selected_manifest_path": PHASE042_SELECTED_MANIFEST_JSON.as_posix(),
        },
    )
    return metadata_path


def materialize_phase042_evaluator_slice(
    rows: Iterable[Phase042SelectedManifestRow | dict[str, Any]],
    *,
    sidecar_root: str | Path = PHASE042_SIDECAR_ROOT,
    output_root: str | Path = PHASE042_EVALUATOR_SLICE,
    overwrite: bool = False,
) -> dict[str, Any]:
    sidecar = Path(sidecar_root)
    output = _safe_prepare_phase042_output_root(sidecar, Path(output_root), overwrite=overwrite)
    corrected_rows = validate_phase042_selected_manifest(rows)

    copied_file_count = 0
    ground_truth_files: list[str] = []
    metadata_files: list[str] = []
    sample_count_by_task_type: dict[str, int] = {}
    for row in corrected_rows:
        source_dir = _resolve_phase042_source_dir(row.source_path, sidecar)
        task_output_root = output / row.task_type
        copied, ground_truth_path = _copy_task_ground_truth(
            source_dir=source_dir,
            task_output_root=task_output_root,
        )
        copied_file_count += copied
        ground_truth_files.append(ground_truth_path)
        metadata_files.append(
            _write_task_materialization_metadata(task_output_root, row).as_posix()
        )
        sample_count_by_task_type[row.task_type] = row.sample_count

    return {
        "static_row_count": len(corrected_rows),
        "static_task_type_count": len(corrected_rows),
        "static_sample_count_by_task_type": dict(sorted(sample_count_by_task_type.items())),
        "copied_file_count": copied_file_count,
        "static_output_root": output.as_posix(),
        "static_ground_truth_files": sorted(ground_truth_files),
        "static_metadata_files": sorted(metadata_files),
    }


def _copy_original_hard_task(
    *,
    original_dataset_root: Path,
    task_type: str,
    adaptive_output_root: Path,
) -> tuple[int, str, int]:
    source_dir = (original_dataset_root / task_type).resolve()
    root_resolved = original_dataset_root.resolve()
    if not _is_relative_to(source_dir, root_resolved):
        raise ValueError(f"original hard task path escapes original dataset root: {task_type}")
    task_output_root = adaptive_output_root / task_type
    copied_file_count, ground_truth_path = _copy_task_ground_truth(
        source_dir=source_dir,
        task_output_root=task_output_root,
    )
    ground_truth = _read_json(task_output_root / "ground_truth.json")
    sample_count = len(ground_truth) if isinstance(ground_truth, dict) else 0
    return copied_file_count, ground_truth_path, sample_count


def materialize_phase042_adaptive_evaluator_slice(
    rows: Iterable[Phase042SelectedManifestRow | dict[str, Any]],
    *,
    sidecar_root: str | Path = PHASE042_SIDECAR_ROOT,
    output_root: str | Path = PHASE042_ADAPTIVE_EVALUATOR_SLICE,
    original_dataset_root: str | Path = "captcha_data",
    overwrite: bool = False,
) -> dict[str, Any]:
    sidecar = Path(sidecar_root)
    output = _safe_prepare_phase042_output_root(sidecar, Path(output_root), overwrite=overwrite)
    corrected_rows = validate_phase042_selected_manifest(rows)
    rows_by_task = {row.task_type: row for row in corrected_rows}

    copied_file_count = 0
    ground_truth_files: list[str] = []
    sample_count_by_task_type: dict[str, int] = {}
    original_root = Path(original_dataset_root)
    for task_type in PHASE042_ORIGINAL_HARD_TASK_TYPES:
        copied, ground_truth_path, sample_count = _copy_original_hard_task(
            original_dataset_root=original_root,
            task_type=task_type,
            adaptive_output_root=output,
        )
        copied_file_count += copied
        ground_truth_files.append(ground_truth_path)
        sample_count_by_task_type[task_type] = sample_count

    for task_type in sorted(PHASE042_TARGET_NEW_TASK_TYPES):
        row = rows_by_task[task_type]
        source_dir = _resolve_phase042_source_dir(row.source_path, sidecar)
        task_output_root = output / row.task_type
        copied, ground_truth_path = _copy_task_ground_truth(
            source_dir=source_dir,
            task_output_root=task_output_root,
        )
        copied_file_count += copied
        ground_truth_files.append(ground_truth_path)
        _write_task_materialization_metadata(task_output_root, row)
        sample_count_by_task_type[task_type] = row.sample_count

    task_types = tuple(sorted(path.name for path in output.iterdir() if path.is_dir()))
    expected = tuple(sorted(PHASE042_ADAPTIVE_TASK_TYPES))
    if task_types != expected:
        raise ValueError(f"adaptive evaluator slice must contain exactly {expected}")

    return {
        "adaptive_task_type_count": len(PHASE042_ADAPTIVE_TASK_TYPES),
        "adaptive_sample_count_by_task_type": dict(sorted(sample_count_by_task_type.items())),
        "adaptive_copied_file_count": copied_file_count,
        "adaptive_output_root": output.as_posix(),
        "adaptive_ground_truth_files": sorted(ground_truth_files),
    }


def materialize_phase042_selected(
    *,
    selected_manifest_path: str | Path = PHASE042_SELECTED_MANIFEST_JSON,
    selected_manifest_csv: str | Path = PHASE042_SELECTED_MANIFEST_CSV,
    source_download_manifest_path: str | Path = (
        PHASE042_SIDECAR_ROOT / "source_download_manifest.json"
    ),
    sidecar_root: str | Path = PHASE042_SIDECAR_ROOT,
    static_output_root: str | Path = PHASE042_EVALUATOR_SLICE,
    adaptive_output_root: str | Path = PHASE042_ADAPTIVE_EVALUATOR_SLICE,
    original_dataset_root: str | Path = "captcha_data",
    overwrite: bool = False,
) -> dict[str, Any]:
    selected_manifest_path = Path(selected_manifest_path)
    selected_manifest_hash = sha256_file(selected_manifest_path)
    rows = load_phase042_selected_manifest(selected_manifest_path)
    corrected_rows, excluded_count = normalize_phase042_selected_manifest_scope(rows)
    write_phase042_selected_manifest(
        Path(selected_manifest_csv),
        selected_manifest_path,
        corrected_rows,
    )
    corrected_hash = sha256_file(selected_manifest_path)
    static_summary = materialize_phase042_evaluator_slice(
        corrected_rows,
        sidecar_root=sidecar_root,
        output_root=static_output_root,
        overwrite=overwrite,
    )
    adaptive_summary = materialize_phase042_adaptive_evaluator_slice(
        corrected_rows,
        sidecar_root=sidecar_root,
        output_root=adaptive_output_root,
        original_dataset_root=original_dataset_root,
        overwrite=overwrite,
    )
    source_download_manifest_path = Path(source_download_manifest_path)
    summary = {
        "selected_manifest_sha256": selected_manifest_hash,
        "corrected_selected_manifest_sha256": corrected_hash,
        "source_download_manifest_sha256": (
            sha256_file(source_download_manifest_path)
            if source_download_manifest_path.is_file()
            else ""
        ),
        "selected_manifest_json": selected_manifest_path.as_posix(),
        "selected_manifest_csv": Path(selected_manifest_csv).as_posix(),
        "source_download_manifest": source_download_manifest_path.as_posix(),
        "excluded_updated_ocw_increment_count": excluded_count,
        **static_summary,
        **adaptive_summary,
    }
    summary["copied_file_count"] = int(static_summary["copied_file_count"]) + int(
        adaptive_summary["adaptive_copied_file_count"]
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Phase 04.2 corrected-provenance dataset utilities."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser(
        "validate-sources",
        help="Validate Phase 04.2 candidate sources before selected-manifest use.",
    )
    validate_parser.add_argument(
        "--candidate-manifest",
        type=Path,
        default=PHASE042_SIDECAR_ROOT / "candidate_manifest.json",
    )
    validate_parser.add_argument(
        "--captcha-root",
        type=Path,
        default=Path("captcha_data"),
    )
    validate_parser.add_argument(
        "--validation-report-csv",
        type=Path,
        default=PHASE042_VALIDATION_REPORT_CSV,
    )
    validate_parser.add_argument(
        "--validation-report-json",
        type=Path,
        default=PHASE042_VALIDATION_REPORT_JSON,
    )
    validate_parser.add_argument(
        "--selected-manifest-csv",
        type=Path,
        default=PHASE042_SELECTED_MANIFEST_CSV,
    )
    validate_parser.add_argument(
        "--selected-manifest-json",
        type=Path,
        default=PHASE042_SELECTED_MANIFEST_JSON,
    )
    validate_parser.add_argument(
        "--novelty-hash-report",
        type=Path,
        default=PHASE042_NOVELTY_HASH_REPORT_JSON,
    )
    validate_parser.add_argument(
        "--perceptual-warning-threshold",
        type=int,
        default=4,
    )
    materialize_parser = subparsers.add_parser(
        "materialize-selected",
        help="Materialize corrected Phase 04.2 static and adaptive evaluator slices.",
    )
    materialize_parser.add_argument(
        "--selected-manifest",
        type=Path,
        default=PHASE042_SELECTED_MANIFEST_JSON,
    )
    materialize_parser.add_argument(
        "--selected-manifest-csv",
        type=Path,
        default=PHASE042_SELECTED_MANIFEST_CSV,
    )
    materialize_parser.add_argument(
        "--source-download-manifest",
        type=Path,
        default=PHASE042_SIDECAR_ROOT / "source_download_manifest.json",
    )
    materialize_parser.add_argument(
        "--sidecar-root",
        type=Path,
        default=PHASE042_SIDECAR_ROOT,
    )
    materialize_parser.add_argument(
        "--static-output-root",
        type=Path,
        default=PHASE042_EVALUATOR_SLICE,
    )
    materialize_parser.add_argument(
        "--adaptive-output-root",
        type=Path,
        default=PHASE042_ADAPTIVE_EVALUATOR_SLICE,
    )
    materialize_parser.add_argument(
        "--original-dataset-root",
        type=Path,
        default=Path("captcha_data"),
    )
    materialize_parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "validate-sources":
        result = validate_phase042_candidates(
            candidate_manifest_path=args.candidate_manifest,
            captcha_root=args.captcha_root,
            validation_report_csv=args.validation_report_csv,
            validation_report_json=args.validation_report_json,
            selected_manifest_csv=args.selected_manifest_csv,
            selected_manifest_json=args.selected_manifest_json,
            novelty_hash_report_path=args.novelty_hash_report,
            perceptual_warning_threshold=args.perceptual_warning_threshold,
        )
        print(
            "Phase 04.2 validation complete: "
            f"{result['selected_count']} selected, {result['rejected_count']} rejected"
        )
        return 0
    if args.command == "materialize-selected":
        result = materialize_phase042_selected(
            selected_manifest_path=args.selected_manifest,
            selected_manifest_csv=args.selected_manifest_csv,
            source_download_manifest_path=args.source_download_manifest,
            sidecar_root=args.sidecar_root,
            static_output_root=args.static_output_root,
            adaptive_output_root=args.adaptive_output_root,
            original_dataset_root=args.original_dataset_root,
            overwrite=args.overwrite,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
