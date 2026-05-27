import csv
import json
from pathlib import Path

import pytest

from cognition.extended_dataset_manifest import (
    ADAPTIVE_RECOMMENDED_COMMAND_SCOPE,
    VALIDATION_QUESTION,
    build_extended_validation_comparison_rows,
    load_extended_dataset_manifest,
    load_original_conclusions,
    load_validation_slice_outcomes,
    main,
)
from cognition.phase3_artifacts import EXTENDED_VALIDATION_COMPARISON_SCHEMA_VERSION


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
            "source_path": "extended/dice",
            "sample_count": 12,
            "adaptive_eligible": True,
            "adaptive_slice_priority": 1,
        },
        {
            **common,
            "source_id": "new-rotation",
            "evidence_origin": "new_category",
            "slice_type": "new_category",
            "task_type": "Rotation_Match",
            "task_family": "Image Matching",
            "source_path": "extended/rotation",
            "sample_count": 16,
            "adaptive_eligible": False,
            "adaptive_slice_priority": 0,
        },
        {
            **common,
            "source_id": "new-text",
            "evidence_origin": "new_category",
            "slice_type": "new_category",
            "task_type": "Text_Reading",
            "task_family": "Text Recognition",
            "source_path": "extended/text",
            "sample_count": 8,
            "adaptive_eligible": True,
            "adaptive_slice_priority": 2,
        },
    ]


def test_manifest_validation_requires_supplement_and_new_category_rows(tmp_path) -> None:
    valid_manifest = tmp_path / "manifest.json"
    _write_json(valid_manifest, {"rows": _manifest_rows()})

    rows = load_extended_dataset_manifest(valid_manifest, run_id="manifest-test")

    assert len(rows) == 3
    assert {row.slice_type for row in rows} == {"supplement_existing", "new_category"}
    assert all(row.validation_question == VALIDATION_QUESTION for row in rows)
    assert all(row.rerun_policy == "selective-validation-slice" for row in rows)

    invalid_manifest = tmp_path / "one-new-category.json"
    _write_json(invalid_manifest, {"rows": _manifest_rows()[:2]})
    with pytest.raises(ValueError, match="new_category_limitation"):
        load_extended_dataset_manifest(invalid_manifest, run_id="manifest-test")

    limited_manifest = tmp_path / "one-new-category-limited.json"
    _write_json(
        limited_manifest,
        {
            "new_category_limitation": "Only one new category was available before the deadline.",
            "rows": _manifest_rows()[:2],
        },
    )
    assert len(load_extended_dataset_manifest(limited_manifest, run_id="manifest-test")) == 2


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
    assert summary["slice_task_count"] == 3
    assert summary["comparison_row_count"] == 0

    manifest_json = Path(summary["output_json"])
    comparison_json = Path(summary["comparison_json"])
    notes_md = Path(summary["notes_md"])
    slice_tasks_csv = Path(summary["slice_tasks_csv"])
    assert manifest_json.exists()
    assert comparison_json.exists()
    assert notes_md.exists()
    assert slice_tasks_csv.exists()

    comparison_payload = json.loads(comparison_json.read_text(encoding="utf-8"))
    assert comparison_payload["schema_version"] == EXTENDED_VALIDATION_COMPARISON_SCHEMA_VERSION
    assert comparison_payload["rows"] == []

    with slice_tasks_csv.open("r", encoding="utf-8", newline="") as handle:
        slice_rows = list(csv.DictReader(handle))
    adaptive_row = next(row for row in slice_rows if row["source_id"] == "supplement-dice")
    assert adaptive_row["recommended_command_scope"] == ADAPTIVE_RECOMMENDED_COMMAND_SCOPE

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
    assert "Hold_Button(Not Used)" in notes
    assert "Slide_Puzzle(Not Used)" in notes
    assert "temporal press-and-hold interaction requires duration/hold-time behavior" in notes
    assert "drag/slider composition requires component-image movement" in notes
    assert "selective validation slice" in notes
    assert "original, supplemented-category, and new-category evidence remain separate" in notes


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
                "slice_type": "supplement_existing",
                "n_attempts": 20,
                "n_success": 4,
                "outcome_source_path": "validation/dice.csv",
            },
            {
                "source_id": "new-rotation",
                "task_type": "Rotation_Match",
                "task_family": "Image Matching",
                "slice_type": "new_category",
                "validation_sample_count": 10,
                "success_count": 7,
                "outcome_source_path": "validation/rotation.csv",
            },
            {
                "source_id": "new-text",
                "task_type": "Text_Reading",
                "task_family": "Text Recognition",
                "slice_type": "new_category",
                "validation_sample_count": 0,
                "success_count": 0,
                "outcome_source_path": "validation/text.csv",
            },
        ],
    )
    _write_csv(
        conclusions_path,
        [
            {
                "task_type": "Dice_Count",
                "task_family": "Counting",
                "label": "hard",
                "primary_rate": 0.2,
            },
            {
                "task_type": "Rotation_Match",
                "task_family": "Image Matching",
                "original_conclusion_label": "hard",
                "original_rate": 0.25,
            },
        ],
    )
    manifest_rows = load_extended_dataset_manifest(manifest_path, run_id="manifest-test")
    outcomes = load_validation_slice_outcomes(outcomes_path)
    conclusions = load_original_conclusions(conclusions_path)

    rows = build_extended_validation_comparison_rows(
        manifest_rows=manifest_rows,
        validation_outcomes=outcomes,
        original_conclusions=conclusions,
        run_id="manifest-test",
    )
    by_source = {row.source_id: row for row in rows}

    assert by_source["supplement-dice"].validation_slice_rate == 0.2
    assert by_source["supplement-dice"].agreement_status == "supports_original"
    assert by_source["new-rotation"].agreement_status == "diverges_from_original"
    assert "crosses" in by_source["new-rotation"].divergence_reason
    assert by_source["new-text"].agreement_status == "inconclusive"
    assert all("selective validation slice" in row.comparison_caveat for row in rows)


def test_validation_slice_comparison_treats_near_broken_as_borderline(
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
                "slice_type": "supplement_existing",
                "n_attempts": 10,
                "n_success": 4,
                "outcome_source_path": "validation/dice.csv",
            }
        ],
    )
    _write_csv(
        conclusions_path,
        [
            {
                "task_type": "Dice_Count",
                "task_family": "Counting",
                "original_conclusion_label": "borderline/near-broken",
                "original_rate": 0.39,
            }
        ],
    )

    rows = build_extended_validation_comparison_rows(
        manifest_rows=load_extended_dataset_manifest(manifest_path, run_id="manifest-test"),
        validation_outcomes=load_validation_slice_outcomes(outcomes_path),
        original_conclusions=load_original_conclusions(conclusions_path),
        run_id="manifest-test",
    )

    assert len(rows) == 1
    assert rows[0].original_conclusion_label == "borderline/near-broken"
    assert rows[0].validation_slice_rate == 0.4
    assert rows[0].agreement_status == "supports_original"


def test_cli_help_exits_cleanly(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    assert "--validation-outcomes" in capsys.readouterr().out
