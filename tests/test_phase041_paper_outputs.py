import json
from pathlib import Path

from expanded_dataset import (
    PHASE041_EVALUATOR_SLICE,
    PHASE041_NEW_TASK_MIN_SAMPLE_COUNT,
    PHASE041_SIDECAR_ROOT,
    write_phase041_paper_outputs,
)


TASK_TYPES = [
    "Click_Order",
    "Dice_Count",
    "Geometry_Click",
    "Patch_Select",
    "Relation_Match",
    "Symbol_Count",
]


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _manifest_row(task_type: str) -> dict[str, object]:
    is_new = task_type in {"Relation_Match", "Symbol_Count"}
    return {
        "source_id": f"phase04_1-{task_type}",
        "source_path": str(PHASE041_SIDECAR_ROOT / "sources" / task_type),
        "source_kind": "open_source_dataset",
        "source_citation": "Open CaptchaWorld-compatible test fixture",
        "source_license": "test fixture license",
        "source_provenance_notes": (
            "Mirrored from an open-source CAPTCHA dataset fixture for validation."
        ),
        "materialized_path": str(PHASE041_EVALUATOR_SLICE / task_type),
        "evidence_origin": "new_category" if is_new else "supplemented_category",
        "slice_type": "new_category" if is_new else "supplement_existing",
        "task_type": task_type,
        "task_family": "Spatial Reasoning" if task_type == "Relation_Match" else "Counting",
        "sample_count": PHASE041_NEW_TASK_MIN_SAMPLE_COUNT if is_new else 10,
        "label_format": "static ground_truth.json answer fields",
        "metadata_alignment_notes": "local source ids map to sidecar paths",
        "answer_format_normalization": "answers normalized before evaluator use",
        "compatibility_status": "ready_for_static_pipeline",
        "evaluation_status": "selected_for_static",
        "limitation_notes": "authorized offline sidecar fixture only",
        "adaptive_eligible": True,
        "static_compatibility_notes": "offline static image with ground truth",
    }


def _write_manifest(tmp_path: Path) -> Path:
    manifest_path = tmp_path / PHASE041_SIDECAR_ROOT / "manifest.json"
    _write_json(manifest_path, {"rows": [_manifest_row(task) for task in TASK_TYPES]})
    return manifest_path


def _summary_row(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "run_id": "phase04_1_static_supplemental",
        "provider": "openai",
        "model": "gpt-5",
        "provider_model": "openai/gpt-5",
        "task_type": "Dice_Count",
        "task_family": "Counting",
        "evidence_origin": "supplemented_category",
        "slice_type": "supplement_existing",
        "sample_count": 10,
        "scientific_wrong_count": 4,
        "protocol_failure_count": 1,
        "infrastructure_failure_count": 0,
        "claim_use": "main_body_caveated",
    }
    values.update(overrides)
    return values


def _write_phase4_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    phase4_table_path = tmp_path / "results" / "revision" / "phase4-paper" / "table.json"
    phase4_notes_path = tmp_path / "results" / "revision" / "phase4-paper" / "notes.md"
    _write_json(
        phase4_table_path,
        {
            "rows": [
                {
                    "system_name": "Oedipus",
                    "reported_metric_value": 0.635,
                    "source_artifact_path": "phase4-baseline-fixture",
                }
            ]
        },
    )
    phase4_notes_path.parent.mkdir(parents=True, exist_ok=True)
    phase4_notes_path.write_text("Phase 4 baseline context fixture.\n", encoding="utf-8")
    return phase4_table_path, phase4_notes_path


def test_paper_outputs_preserve_divergence(tmp_path) -> None:
    manifest_path = _write_manifest(tmp_path)
    results_dir = tmp_path / "results"
    exp2_path = results_dir / "exp2" / "openai" / "gpt-5" / "results.csv"
    exp2_path.parent.mkdir(parents=True, exist_ok=True)
    exp2_path.write_text("type,pass_at_1\nDice_Count,0.1\n", encoding="utf-8")

    static_summary_path = tmp_path / "static_summary.json"
    adaptive_summary_path = tmp_path / "adaptive_summary.json"
    _write_json(
        static_summary_path,
        {
            "rows": [
                _summary_row(
                    attempt_count=10,
                    success_count=6,
                    pass_rate=0.6,
                    summary_source_path="static-summary-fixture",
                )
            ]
        },
    )
    _write_json(
        adaptive_summary_path,
        {
            "rows": [
                _summary_row(
                    run_id="phase04_1_adaptive_supplemental",
                    session_count=1,
                    attempt_budget_k=6,
                    success_count=5,
                    scientific_wrong_count=3,
                    protocol_failure_count=0,
                    infrastructure_failure_count=2,
                    adaptive_success_rate=0.5,
                    adaptive_summary_source_path="adaptive-summary-fixture",
                )
            ]
        },
    )
    phase4_table_path, phase4_notes_path = _write_phase4_artifacts(tmp_path)

    summary = write_phase041_paper_outputs(
        manifest_path=manifest_path,
        static_summary_path=static_summary_path,
        adaptive_summary_path=adaptive_summary_path,
        phase4_paper_table_path=phase4_table_path,
        phase4_notes_path=phase4_notes_path,
        results_dir=results_dir,
        output_root=tmp_path / "results" / "revision",
        run_id="phase04_1_paper_outputs",
    )

    output_dir = tmp_path / "results" / "revision" / "phase04_1_paper_outputs"
    validation_payload = json.loads(
        (output_dir / "expanded_dataset_validation_analysis.json").read_text(
            encoding="utf-8"
        )
    )
    paper_payload = json.loads(
        (output_dir / "expanded_main_body_table.json").read_text(encoding="utf-8")
    )
    notes = (output_dir / "expanded_claim_boundary_notes.md").read_text(
        encoding="utf-8"
    )

    direct_row = next(
        row for row in paper_payload["rows"] if row["provider_model"] == "openai/gpt-5"
    )
    contextual_row = next(
        row for row in paper_payload["rows"] if row["contextual_sota_only"]
    )
    validation_row = validation_payload["rows"][0]

    assert summary["validation_row_count"] == 1
    assert validation_row["diverges_from_original"] is True
    assert direct_row["agreement_status"] == "diverges_from_original"
    assert direct_row["divergence_reason"]
    assert direct_row["claim_boundary_note"]
    assert direct_row["direct_evidence"] is True
    assert direct_row["contextual_sota_only"] is False
    assert direct_row["scientific_wrong_count"] == 7
    assert direct_row["protocol_failure_count"] == 1
    assert direct_row["infrastructure_failure_count"] == 2
    assert contextual_row["direct_evidence"] is False
    assert contextual_row["contextual_sota_only"] is True
    assert "infrastructure failures must not be counted as structural hardness" in (
        direct_row["claim_boundary_note"]
    )
    assert "Directly evaluated expanded-dataset evidence" in notes
    assert "Divergence handling" in notes
    assert "Contextual external SOTA triangulation" in notes
    assert "Scope limits" in notes
    assert "population-level deployment estimate" in notes
    assert "CaptchaWorld limitations" in notes
