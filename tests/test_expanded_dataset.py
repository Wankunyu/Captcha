import json
from pathlib import Path

import pytest

from expanded_dataset import (
    PHASE041_EVALUATOR_SLICE,
    PHASE041_NEW_TASK_TYPES,
    PHASE041_SIDECAR_ROOT,
    PHASE041_SUPPLEMENTED_TASK_TYPES,
    build_paper_facing_run_matrix,
    load_phase041_manifest,
    materialize_evaluator_slice,
    validate_phase041_manifest,
)


PAPER_FACING_PROVIDER_MODELS = [
    "openai/gpt-5",
    "openai/gpt-5.1_medium",
    "openai/gpt-5.1_none",
    "anthropic/claude-sonnet-4-5",
    "gemini/gemini-2.5-flash",
    "gemini/gemini-2.5-pro",
    "fireworks/accounts_fireworks_models_qwen3-vl-235b-a22b-instruct",
]

TASK_FAMILIES = {
    "Dice_Count": "Click/Coordinate",
    "Click_Order": "Click/Coordinate",
    "Patch_Select": "Grid Selection",
    "Geometry_Click": "Click/Coordinate",
    "Symbol_Count": "Counting",
    "Relation_Match": "Image Matching",
}


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_task_source(sidecar_root: Path, task_type: str, sample_name: str) -> None:
    task_root = sidecar_root / "sources" / task_type
    task_root.mkdir(parents=True, exist_ok=True)
    (task_root / sample_name).write_bytes(b"tiny offline image fixture")
    _write_json(task_root / "ground_truth.json", {sample_name: {"answer": task_type}})


def _manifest_row(task_type: str, **overrides: object) -> dict[str, object]:
    is_new = task_type in PHASE041_NEW_TASK_TYPES
    values: dict[str, object] = {
        "source_id": f"phase04_1-{task_type}",
        "source_path": str(PHASE041_SIDECAR_ROOT / "sources" / task_type),
        "materialized_path": str(PHASE041_EVALUATOR_SLICE / task_type),
        "evidence_origin": "new_category" if is_new else "supplemented_category",
        "slice_type": "new_category" if is_new else "supplement_existing",
        "task_type": task_type,
        "task_family": TASK_FAMILIES[task_type],
        "sample_count": 1,
        "label_format": "static ground_truth.json answer fields",
        "metadata_alignment_notes": "local source ids map to sidecar paths",
        "answer_format_normalization": "answers normalized before evaluator use",
        "compatibility_status": "ready_for_static_pipeline",
        "evaluation_status": "selected_for_static",
        "limitation_notes": "authorized offline sidecar fixture only",
        "adaptive_eligible": True,
        "static_compatibility_notes": "offline static image with ground truth",
    }
    values.update(overrides)
    return values


def _manifest_rows() -> list[dict[str, object]]:
    ordered_tasks = [
        "Dice_Count",
        "Click_Order",
        "Patch_Select",
        "Geometry_Click",
        "Symbol_Count",
        "Relation_Match",
    ]
    return [_manifest_row(task_type) for task_type in ordered_tasks]


def _write_manifest_fixture(tmp_path: Path) -> tuple[Path, Path]:
    sidecar_root = tmp_path / PHASE041_SIDECAR_ROOT
    for task_type in TASK_FAMILIES:
        _write_task_source(sidecar_root, task_type, f"{task_type.lower()}_sample.png")
    manifest_path = sidecar_root / "manifest.json"
    _write_json(manifest_path, {"rows": _manifest_rows()})
    return sidecar_root, manifest_path


def test_manifest_validation_accepts_phase041_required_categories(tmp_path) -> None:
    _, manifest_path = _write_manifest_fixture(tmp_path)

    rows = load_phase041_manifest(manifest_path, run_id="phase041-test")
    validate_phase041_manifest(rows)

    assert {row.task_type for row in rows} == (
        PHASE041_SUPPLEMENTED_TASK_TYPES | PHASE041_NEW_TASK_TYPES
    )
    assert {
        row.task_type for row in rows if row.evidence_origin == "supplemented_category"
    } == PHASE041_SUPPLEMENTED_TASK_TYPES
    assert {
        row.task_type for row in rows if row.evidence_origin == "new_category"
    } == PHASE041_NEW_TASK_TYPES


def test_manifest_requires_exact_phase041_new_categories(tmp_path) -> None:
    sidecar_root, manifest_path = _write_manifest_fixture(tmp_path)

    one_new_category = [
        row for row in _manifest_rows() if row["task_type"] != "Relation_Match"
    ]
    _write_json(manifest_path, {"rows": one_new_category})
    with pytest.raises(ValueError, match="exactly"):
        validate_phase041_manifest(
            load_phase041_manifest(manifest_path, run_id="phase041-test")
        )

    too_many_new_categories = [
        *_manifest_rows(),
        _manifest_row(
            "Symbol_Count",
            source_id="phase04_1-extra-symbol",
        ),
    ]
    too_many_new_categories[-1]["task_type"] = "Extra_Static_Category"
    _write_task_source(sidecar_root, "Extra_Static_Category", "extra.png")
    too_many_new_categories[-1]["source_path"] = str(
        PHASE041_SIDECAR_ROOT / "sources" / "Extra_Static_Category"
    )
    too_many_new_categories[-1]["materialized_path"] = str(
        PHASE041_EVALUATOR_SLICE / "Extra_Static_Category"
    )
    _write_json(manifest_path, {"rows": too_many_new_categories})
    expected_new_categories = "Symbol_Count.*Relation_Match|Relation_Match.*Symbol_Count"
    with pytest.raises(ValueError, match=expected_new_categories):
        validate_phase041_manifest(
            load_phase041_manifest(manifest_path, run_id="phase041-test")
        )

    unsupported_new_category = [
        _manifest_row(
            row["task_type"],
            evidence_origin="new_category",
            slice_type="new_category",
        )
        if row["task_type"] == "Dice_Count"
        else row
        for row in _manifest_rows()
    ]
    _write_json(manifest_path, {"rows": unsupported_new_category})
    with pytest.raises(ValueError, match="only accepted new-category task types"):
        validate_phase041_manifest(
            load_phase041_manifest(manifest_path, run_id="phase041-test")
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "source_id",
        "source_path",
        "task_type",
        "task_family",
        "sample_count",
        "label_format",
        "metadata_alignment_notes",
        "answer_format_normalization",
        "compatibility_status",
        "evaluation_status",
        "limitation_notes",
        "adaptive_eligible",
    ],
)
def test_manifest_requires_every_d08_field(tmp_path, field_name) -> None:
    _, manifest_path = _write_manifest_fixture(tmp_path)
    rows = _manifest_rows()
    rows[0].pop(field_name)
    _write_json(manifest_path, {"rows": rows})

    with pytest.raises(ValueError, match=field_name):
        load_phase041_manifest(manifest_path, run_id="phase041-test")


def test_manifest_source_path_must_resolve_under_sidecar_sources(tmp_path) -> None:
    _, manifest_path = _write_manifest_fixture(tmp_path)
    rows = _manifest_rows()
    rows[0]["source_path"] = "captcha_data/Dice_Count"
    _write_json(manifest_path, {"rows": rows})

    with pytest.raises(ValueError, match="source_path"):
        load_phase041_manifest(manifest_path, run_id="phase041-test")


def test_materialize_evaluator_slice_writes_layout_without_touching_captcha_data(
    tmp_path,
) -> None:
    sidecar_root, manifest_path = _write_manifest_fixture(tmp_path)
    rows = load_phase041_manifest(manifest_path, run_id="phase041-test")
    output_root = sidecar_root / "evaluator_slice"

    summary = materialize_evaluator_slice(
        rows,
        sidecar_root=sidecar_root,
        output_root=output_root,
        overwrite=True,
    )

    assert summary["output_root"] == str(output_root)
    assert summary["task_type_count"] == 6
    for task_type in TASK_FAMILIES:
        task_root = output_root / task_type
        ground_truth_path = task_root / "ground_truth.json"
        assert ground_truth_path.exists()
        ground_truth = json.loads(ground_truth_path.read_text(encoding="utf-8"))
        assert len(ground_truth) == 1
        sample_name = next(iter(ground_truth))
        assert (task_root / sample_name).exists()
    assert not (tmp_path / "captcha_data").exists()


def test_materialize_evaluator_slice_rejects_missing_referenced_files(tmp_path) -> None:
    sidecar_root, manifest_path = _write_manifest_fixture(tmp_path)
    (sidecar_root / "sources" / "Dice_Count" / "dice_count_sample.png").unlink()
    rows = load_phase041_manifest(manifest_path, run_id="phase041-test")

    with pytest.raises(FileNotFoundError, match="dice_count_sample.png"):
        materialize_evaluator_slice(
            rows,
            sidecar_root=sidecar_root,
            output_root=sidecar_root / "evaluator_slice",
            overwrite=True,
        )


def test_build_paper_facing_run_matrix_uses_existing_exp2_models(tmp_path) -> None:
    exp2_root = tmp_path / "results" / "exp2"
    for provider_model in [*PAPER_FACING_PROVIDER_MODELS, "openai/gpt-5-chat-latest"]:
        provider, model = provider_model.split("/", 1)
        _write_json(exp2_root / provider / model / "results.csv", [])

    rows = build_paper_facing_run_matrix(
        results_dir=exp2_root,
        materialized_dataset_root=tmp_path / PHASE041_EVALUATOR_SLICE,
        output_root=tmp_path / "results" / "revision",
        run_id_prefix="phase04_1_static",
    )

    assert [row.provider_model for row in rows] == PAPER_FACING_PROVIDER_MODELS
    assert all(row.paper_facing_model_row for row in rows)
    assert all(row.run_scope == "static" for row in rows)
    assert all(
        set(row.task_types)
        == PHASE041_SUPPLEMENTED_TASK_TYPES | PHASE041_NEW_TASK_TYPES
        for row in rows
    )
    assert rows[0].materialized_dataset_root.endswith(
        "expanded_captcha_data/phase04_1/evaluator_slice"
    )


def test_gitattributes_contains_expanded_dataset_lfs_rule() -> None:
    assert "expanded_captcha_data/** filter=lfs diff=lfs merge=lfs -text" in Path(
        ".gitattributes"
    ).read_text(encoding="utf-8")
