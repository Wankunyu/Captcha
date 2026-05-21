import json
from pathlib import Path

import pytest

from expanded_dataset_phase042 import (
    PHASE042_ADAPTIVE_TASK_TYPES,
    PHASE042_TARGET_NEW_TASK_TYPES,
    load_phase042_selected_manifest,
    materialize_phase042_adaptive_evaluator_slice,
    materialize_phase042_evaluator_slice,
    materialize_phase042_selected,
    normalize_phase042_selected_manifest_scope,
    validate_phase042_selected_manifest,
)


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write_task_source(task_type: str, count: int = 10) -> Path:
    source_dir = Path("expanded_captcha_data/phase04_2/candidates") / task_type
    source_dir.mkdir(parents=True, exist_ok=True)
    ground_truth: dict[str, dict[str, object]] = {}
    for index in range(count):
        image_name = f"{task_type.lower()}_{index:03d}.png"
        (source_dir / image_name).write_bytes(f"{task_type}-{index}".encode())
        ground_truth[image_name] = {
            "image": image_name,
            "answer": index,
            "source_kind": "open_source_dataset",
        }
    _write_json(source_dir / "ground_truth.json", ground_truth)
    return source_dir


def _write_original_hard_tasks() -> None:
    for task_type in [
        "Dice_Count",
        "Place_Dot",
        "Pick_Area",
        "Click_Order",
        "Patch_Select",
        "Rotation_Match",
    ]:
        task_dir = Path("captcha_data") / task_type
        task_dir.mkdir(parents=True, exist_ok=True)
        image_name = f"{task_type.lower()}_sample.png"
        (task_dir / image_name).write_bytes(task_type.encode())
        _write_json(task_dir / "ground_truth.json", {image_name: {"answer": task_type}})


def _selected_row(task_type: str, *, sample_count: int = 10) -> dict[str, object]:
    source_dir = _write_task_source(task_type, count=sample_count)
    return {
        "selected_id": f"phase042-{task_type.lower()}",
        "candidate_id": f"candidate-{task_type.lower()}",
        "source_path": source_dir.as_posix(),
        "candidate_image_paths": [
            (source_dir / f"{task_type.lower()}_{index:03d}.png").as_posix()
            for index in range(sample_count)
        ],
        "source_kind": "open_source_dataset",
        "source_provenance_class": "preferred_real_external",
        "source_citation": "Example open-source CAPTCHA dataset",
        "source_license": "CC-BY-4.0",
        "source_provenance_notes": "Real external CAPTCHA samples for Phase 04.2.",
        "evidence_origin": "new_category",
        "slice_type": "new_category",
        "task_type": task_type,
        "task_family": "Counting",
        "sample_count": sample_count,
        "label_format": "ground_truth.json",
        "metadata_alignment_notes": "source ids mapped to selected rows",
        "answer_format_normalization": "answers normalized for evaluator use",
        "compatibility_status": "ready_for_static_pipeline",
        "evaluation_status": "selected_for_static",
        "limitation_notes": "offline corrected Phase 04.2 sidecar",
        "adaptive_eligible": True,
        "static_compatibility_notes": "offline images with ground truth",
        "novelty_sha256": ["a" * 64 for _ in range(sample_count)],
        "novelty_hash_report_path": (
            "expanded_captcha_data/phase04_2/novelty_hash_report.json"
        ),
        "exact_captcha_data_match": False,
        "perceptual_warning_count": 0,
        "review_warnings": [],
    }


def _ocw_increment_row(task_type: str) -> dict[str, object]:
    row = _selected_row(task_type, sample_count=1)
    row.update(
        {
            "selected_id": f"phase042-ocw-{task_type.lower()}-latest-additions",
            "candidate_id": f"phase042-ocw-{task_type.lower()}-latest-additions",
            "evidence_origin": "supplemented_category",
            "slice_type": "supplement_existing",
            "source_provenance_notes": "Updated local OpenCaptchaWorld hard-type increment.",
        }
    )
    return row


def _write_selected_manifest(path: Path, rows: list[dict[str, object]]) -> Path:
    return _write_json(
        path,
        {
            "schema_version": "cognition.revision.phase042.selected_manifest.v1",
            "rows": rows,
        },
    )


def _three_category_rows() -> list[dict[str, object]]:
    return [
        _selected_row("Symbol_Count"),
        _selected_row("Relation_Match"),
        _selected_row("Hole_Counting"),
    ]


def test_materialization_uses_selected_manifest_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    selected_manifest = _write_selected_manifest(
        Path("expanded_captcha_data/phase04_2/selected_manifest.json"),
        _three_category_rows(),
    )
    validation_report = _write_json(
        Path("expanded_captcha_data/phase04_2/phase042_validation_report.json"),
        {"rows": []},
    )

    assert len(load_phase042_selected_manifest(selected_manifest)) == 3
    with pytest.raises(ValueError, match="selected manifest"):
        load_phase042_selected_manifest(validation_report)


def test_materialization_uses_phase042_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    rows = validate_phase042_selected_manifest(_three_category_rows())
    summary = materialize_phase042_evaluator_slice(rows, overwrite=True)

    assert summary["static_output_root"] == "expanded_captcha_data/phase04_2/evaluator_slice"
    assert {
        path.parent.name for path in Path(summary["static_output_root"]).glob("*/ground_truth.json")
    } == PHASE042_TARGET_NEW_TASK_TYPES


def test_materialization_rejects_validation_report_input(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    validation_report = _write_json(
        Path("expanded_captcha_data/phase04_2/phase042_validation_report.json"),
        {"rows": _three_category_rows()},
    )

    with pytest.raises(ValueError, match="validation report"):
        load_phase042_selected_manifest(validation_report)


def test_materialization_rejects_phase041_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    rows = _three_category_rows()
    rows[0]["source_path"] = "expanded_captcha_data/phase04_1/sources/Symbol_Count"

    with pytest.raises(ValueError, match="Phase 04.1"):
        validate_phase042_selected_manifest(rows)


def test_materialization_never_writes_to_captcha_data(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    rows = validate_phase042_selected_manifest(_three_category_rows())

    with pytest.raises(ValueError, match="captcha_data"):
        materialize_phase042_evaluator_slice(
            rows,
            output_root=Path("captcha_data/phase04_2_bad"),
            overwrite=True,
        )


def test_static_materialization_uses_only_three_new_categories(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    rows = validate_phase042_selected_manifest(_three_category_rows())
    materialize_phase042_evaluator_slice(rows, overwrite=True)

    task_dirs = {
        path.name for path in Path("expanded_captcha_data/phase04_2/evaluator_slice").iterdir()
    }
    assert task_dirs == {"Symbol_Count", "Relation_Match", "Hole_Counting"}
    metadata = json.loads(
        Path(
            "expanded_captcha_data/phase04_2/evaluator_slice/Symbol_Count/"
            "phase042_materialization_metadata.json"
        ).read_text(encoding="utf-8")
    )
    assert metadata["source_kind"] == "open_source_dataset"
    assert metadata["source_provenance_class"] == "preferred_real_external"


def test_selected_manifest_normalization_excludes_ocw_hard_type_increments(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    rows = [
        _ocw_increment_row("Dice_Count"),
        _ocw_increment_row("Click_Order"),
        _ocw_increment_row("Patch_Select"),
        _ocw_increment_row("Geometry_Click"),
        *_three_category_rows(),
    ]

    corrected, excluded_count = normalize_phase042_selected_manifest_scope(rows)

    assert excluded_count == 4
    assert {row.task_type for row in corrected} == {
        "Symbol_Count",
        "Relation_Match",
        "Hole_Counting",
    }


def test_adaptive_materialization_combines_original_hard_tasks_with_three_new_categories(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    _write_original_hard_tasks()
    rows = validate_phase042_selected_manifest(_three_category_rows())

    summary = materialize_phase042_adaptive_evaluator_slice(rows, overwrite=True)

    task_dirs = {
        path.name
        for path in Path("expanded_captcha_data/phase04_2/adaptive_evaluator_slice").iterdir()
    }
    assert task_dirs == set(PHASE042_ADAPTIVE_TASK_TYPES)
    assert summary["adaptive_task_type_count"] == 9
    assert set(summary["adaptive_sample_count_by_task_type"]) == set(PHASE042_ADAPTIVE_TASK_TYPES)


def test_materialization_excludes_updated_ocw_hard_type_increments(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    _write_original_hard_tasks()
    selected_manifest = _write_selected_manifest(
        Path("expanded_captcha_data/phase04_2/phase042_selected_manifest.json"),
        [
            _ocw_increment_row("Dice_Count"),
            _ocw_increment_row("Click_Order"),
            _ocw_increment_row("Patch_Select"),
            _ocw_increment_row("Geometry_Click"),
            *_three_category_rows(),
        ],
    )
    _write_json(Path("expanded_captcha_data/phase04_2/source_download_manifest.json"), {})

    summary = materialize_phase042_selected(
        selected_manifest_path=selected_manifest,
        overwrite=True,
    )

    assert summary["excluded_updated_ocw_increment_count"] == 4
    static_task_dirs = {
        path.name for path in Path("expanded_captcha_data/phase04_2/evaluator_slice").iterdir()
    }
    assert static_task_dirs == {"Symbol_Count", "Relation_Match", "Hole_Counting"}
    corrected_rows = json.loads(selected_manifest.read_text(encoding="utf-8"))["rows"]
    assert {row["task_type"] for row in corrected_rows} == static_task_dirs
