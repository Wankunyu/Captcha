import json
from pathlib import Path
from typing import Iterable


PHASE042_SIDECAR_ROOT = Path("expanded_captcha_data/phase04_2")
PHASE042_CANDIDATES_ROOT = PHASE042_SIDECAR_ROOT / "candidates"
PHASE042_TARGET_TASK_TYPES = (
    "Dice_Count",
    "Click_Order",
    "Patch_Select",
    "Geometry_Click",
    "Symbol_Count",
    "Relation_Match",
)
PHASE042_TARGET_NEW_TASK_TYPES = {"Symbol_Count", "Relation_Match"}
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
