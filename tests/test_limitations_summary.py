import json
from pathlib import Path

import pytest

from limitations_summary import (
    build_artifact_index,
    load_rows,
    main,
    render_limitations_summary,
    write_limitations_summary,
)


REQUIRED_HEADINGS = [
    "# Phase 3 Dataset Scope, Statistical Confidence, And Limitations",
    "## Dataset Scope",
    "## Removed Incompatible CaptchaWorld Types",
    "## Dataset Contribution Notes",
    "## Extended Validation Slice Comparison",
    "## Statistical Confidence And Sample Support",
    "## Threshold Sensitivity",
    "## Retry Calibration",
    "## Failure Taxonomy",
    "## Generalizability Limits",
    "## Paper-Safe Claim Language",
]

REQUIRED_STRINGS = [
    "Hold_Button(Not Used)",
    "Slide_Puzzle(Not Used)",
    (
        "temporal press-and-hold interaction requires duration/hold-time behavior "
        "outside static answer schemas"
    ),
    (
        "drag/slider composition requires component-image movement and "
        "target-position tolerance outside static answer schemas"
    ),
    (
        "CaptchaWorld is treated as a curated, task-diverse benchmark for recurring "
        "structural hardness patterns, not a population-level deployment estimate."
    ),
    (
        "The 40% working CAPTCHA threshold is an operational reporting heuristic, "
        "not a universal CAPTCHA security boundary."
    ),
    "The 30%-50% review band is a revision-time caution band, not a new security tier.",
    (
        "Infrastructure and protocol failures are not counted as scientific evidence "
        "of structural robustness."
    ),
    "Original, supplemented-category, and new-category evidence are reported separately.",
    (
        "Selective validation-slice outcomes are compared against original-dataset "
        "conclusions and reported as agreement, divergence, or inconclusive evidence."
    ),
    (
        "raw_observed_rate is transparent accounting; scientific_rate is the preferred "
        "basis for model/CAPTCHA behavior claims when failure classes are available."
    ),
]


def _write_json(path: Path, rows: list[dict[str, object]], schema_version: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"schema_version": schema_version, "rows": rows}, indent=2),
        encoding="utf-8",
    )
    return path


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _fixture_inputs(tmp_path: Path) -> dict[str, Path]:
    artifact_dir = tmp_path / "artifacts"
    return {
        "dataset_scope_json": _write_json(
            artifact_dir / "dataset_scope_audit.json",
            [
                {
                    "task_type": "Dice_Count",
                    "task_family": "Counting",
                    "dataset_dir": "Dice_Count",
                    "scope_status": "included",
                    "support_status": "supported",
                    "pipeline_compatibility": "compatible_static_answer",
                    "dataset_sample_count": 25,
                    "underpowered_threshold": 20,
                    "underpowered": False,
                    "reason": "supported dataset with evaluated rows",
                    "removal_decision": "kept",
                },
                {
                    "task_type": "Geometry_Click",
                    "task_family": "Click/Coordinate",
                    "dataset_dir": "Geometry_Click",
                    "scope_status": "underpowered",
                    "support_status": "supported",
                    "pipeline_compatibility": "compatible_static_answer",
                    "dataset_sample_count": 8,
                    "underpowered_threshold": 20,
                    "underpowered": True,
                    "reason": "dataset sample count 8 is below underpowered threshold 20",
                    "removal_decision": "kept",
                },
                {
                    "task_type": "Hold_Button(Not Used)",
                    "task_family": "Removed/Incompatible",
                    "dataset_dir": "Hold_Button(Not Used)",
                    "scope_status": "incompatible",
                    "support_status": "removed_not_used",
                    "pipeline_compatibility": "incompatible_temporal_hold",
                    "dataset_sample_count": 1,
                    "underpowered_threshold": 20,
                    "underpowered": True,
                    "reason": (
                        "temporal press-and-hold interaction requires duration/hold-time "
                        "behavior outside static answer schemas"
                    ),
                    "removal_decision": "removed from active evaluation",
                },
                {
                    "task_type": "Slide_Puzzle(Not Used)",
                    "task_family": "Removed/Incompatible",
                    "dataset_dir": "Slide_Puzzle(Not Used)",
                    "scope_status": "incompatible",
                    "support_status": "removed_not_used",
                    "pipeline_compatibility": "incompatible_slider_drag",
                    "dataset_sample_count": 1,
                    "underpowered_threshold": 20,
                    "underpowered": True,
                    "reason": (
                        "drag/slider composition requires component-image movement and "
                        "target-position tolerance outside static answer schemas"
                    ),
                    "removal_decision": "removed from active evaluation",
                },
            ],
            "cognition.revision.dataset_scope_audit.v1",
        ),
        "extended_manifest_json": _write_json(
            artifact_dir / "extended_dataset_manifest.json",
            [
                {
                    "source_id": "supplement-dice",
                    "evidence_origin": "supplemented_category",
                    "slice_type": "supplement_existing",
                    "task_type": "Dice_Count",
                    "task_family": "Counting",
                    "sample_count": 12,
                    "compatibility_status": "ready_for_static_pipeline",
                    "evaluation_status": "selected_for_validation",
                    "limitation_note": "selective validation slice only",
                },
                {
                    "source_id": "new-rotation",
                    "evidence_origin": "new_category",
                    "slice_type": "new_category",
                    "task_type": "Rotation_Match",
                    "task_family": "Image Matching",
                    "sample_count": 10,
                    "compatibility_status": "ready_for_static_pipeline",
                    "evaluation_status": "selected_for_validation",
                    "limitation_note": "new-category slice only",
                },
            ],
            "cognition.revision.extended_dataset_manifest.v1",
        ),
        "extended_validation_comparison_json": _write_json(
            artifact_dir / "extended_validation_comparison.json",
            [
                {
                    "source_id": "supplement-dice",
                    "evidence_origin": "supplemented_category",
                    "slice_type": "supplement_existing",
                    "task_type": "Dice_Count",
                    "task_family": "Counting",
                    "original_conclusion_label": "hard",
                    "original_rate": 0.2,
                    "validation_slice_rate": 0.2,
                    "validation_sample_count": 20,
                    "agreement_status": "supports_original",
                    "divergence_reason": "",
                    "comparison_caveat": "agreement is limited to the selective validation slice",
                    "outcome_source_path": "validation/dice.csv",
                },
                {
                    "source_id": "new-rotation",
                    "evidence_origin": "new_category",
                    "slice_type": "new_category",
                    "task_type": "Rotation_Match",
                    "task_family": "Image Matching",
                    "original_conclusion_label": "hard",
                    "original_rate": 0.25,
                    "validation_slice_rate": 0.7,
                    "validation_sample_count": 10,
                    "agreement_status": "diverges_from_original",
                    "divergence_reason": (
                        "validation slice crosses the original 40% cutoff direction"
                    ),
                    "comparison_caveat": "new-category evidence is selective",
                    "outcome_source_path": "validation/rotation.csv",
                },
                {
                    "source_id": "new-text",
                    "evidence_origin": "new_category",
                    "slice_type": "new_category",
                    "task_type": "Text_Reading",
                    "task_family": "Text Recognition",
                    "original_conclusion_label": None,
                    "original_rate": None,
                    "validation_slice_rate": None,
                    "validation_sample_count": 0,
                    "agreement_status": "inconclusive",
                    "divergence_reason": (
                        "missing original conclusion, zero sample count, or unsupported slice"
                    ),
                    "comparison_caveat": "missing validation samples keep this inconclusive",
                    "outcome_source_path": "validation/text.csv",
                },
            ],
            "cognition.revision.extended_validation_comparison.v1",
        ),
        "contribution_notes_md": _write_text(
            artifact_dir / "dataset_contribution_notes.md",
            (
                "# Dataset Contribution Notes\n\nCleaning, standardization, label "
                "alignment, and answer-format normalization were recorded offline.\n"
            ),
        ),
        "pass_rate_confidence_json": _write_json(
            artifact_dir / "pass_rate_confidence.json",
            [
                {
                    "aggregation_level": "task_type",
                    "provider": "openai",
                    "model": "gpt-5",
                    "provider_model": "openai/gpt-5",
                    "experiment": "exp2",
                    "task_type": "Geometry_Click",
                    "task_family": "Click/Coordinate",
                    "n_attempts": 8,
                    "n_success": 2,
                    "pass_rate": 0.25,
                    "ci_method": "wilson",
                    "ci_confidence": 0.95,
                    "ci_low": 0.07,
                    "ci_high": 0.59,
                    "underpowered_threshold": 20,
                    "underpowered": True,
                    "source_path": "results/exp2/results.csv",
                },
                {
                    "aggregation_level": "task_family",
                    "provider": "openai",
                    "model": "gpt-5",
                    "provider_model": "openai/gpt-5",
                    "experiment": "exp2",
                    "task_type": "__family__",
                    "task_family": "Counting",
                    "n_attempts": 25,
                    "n_success": 5,
                    "pass_rate": 0.2,
                    "ci_method": "wilson",
                    "ci_confidence": 0.95,
                    "ci_low": 0.09,
                    "ci_high": 0.39,
                    "underpowered_threshold": 20,
                    "underpowered": False,
                    "source_path": "results/exp2/results.csv",
                },
            ],
            "cognition.revision.pass_rate_confidence.v1",
        ),
        "threshold_sensitivity_json": _write_json(
            artifact_dir / "threshold_sensitivity.json",
            [
                {
                    "provider": "openai",
                    "model": "gpt-5",
                    "provider_model": "openai/gpt-5",
                    "task_type": "Geometry_Click",
                    "task_family": "Click/Coordinate",
                    "primary_experiment": "exp2",
                    "primary_rate": 0.35,
                    "max_observed_rate": 0.52,
                    "label": "borderline/near-broken",
                    "margin_to_cutoff": -0.05,
                    "cutoff": 0.4,
                    "review_band_low": 0.3,
                    "review_band_high": 0.5,
                    "in_30_50_review_band": True,
                    "ci_crosses_cutoff": True,
                    "trend_sensitive": True,
                    "trend_delta": 0.1,
                    "trend_sources": "extended_validation_slice",
                    "cutoff_note": "40% working CAPTCHA threshold",
                }
            ],
            "cognition.revision.threshold_sensitivity.v1",
        ),
        "retry_calibration_json": _write_json(
            artifact_dir / "retry_calibration.json",
            [
                {
                    "provider": "openai",
                    "model": "gpt-5",
                    "provider_model": "openai/gpt-5",
                    "task_type": "Dice_Count",
                    "task_family": "Counting",
                    "exp2_pass_at_1": 0.2,
                    "attempt_budget_k": 3,
                    "bernoulli_success_at_k": 0.49,
                    "observed_fixed_retry_success": 0.5,
                    "observed_adaptive_compatible_success": 0.33,
                    "signed_error_fixed_retry": 0.01,
                    "absolute_error_fixed_retry": 0.01,
                    "signed_error_adaptive": -0.16,
                    "absolute_error_adaptive": 0.16,
                    "sample_count": 10,
                    "scientific_wrong_count": 3,
                    "protocol_failure_count": 1,
                    "infrastructure_failure_count": 0,
                    "raw_observed_rate": 0.33,
                    "scientific_rate": 0.4,
                    "comparison_contract": "task-type-primary; same-attempt-budget",
                }
            ],
            "cognition.revision.retry_calibration.v1",
        ),
        "failure_taxonomy_json": _write_json(
            artifact_dir / "failure_taxonomy.json",
            [
                {
                    "aggregation_level": "task_type",
                    "provider": "openai",
                    "model": "gpt-5",
                    "provider_model": "openai/gpt-5",
                    "task_type": "Dice_Count",
                    "task_family": "Counting",
                    "success_count": 2,
                    "scientific_wrong_count": 3,
                    "protocol_failure_count": 0,
                    "infrastructure_failure_count": 0,
                    "total_count": 5,
                    "raw_observed_rate": 0.4,
                    "scientific_rate": 0.4,
                    "failure_taxonomy_source": "adaptive_summary",
                    "claim_use": "scientific_claim_eligible",
                    "hardness_caveat": None,
                },
                {
                    "aggregation_level": "task_type",
                    "provider": "openai",
                    "model": "gpt-5",
                    "provider_model": "openai/gpt-5",
                    "task_type": "Patch_Select",
                    "task_family": "Grid Selection",
                    "success_count": 1,
                    "scientific_wrong_count": 1,
                    "protocol_failure_count": 0,
                    "infrastructure_failure_count": 2,
                    "total_count": 4,
                    "raw_observed_rate": 0.25,
                    "scientific_rate": 0.5,
                    "failure_taxonomy_source": "adaptive_summary",
                    "claim_use": "infrastructure_caveated",
                    "hardness_caveat": "infrastructure/provider failures are visible",
                },
            ],
            "cognition.revision.failure_taxonomy.v1",
        ),
    }


def test_load_rows_accepts_phase3_json_payload(tmp_path: Path) -> None:
    path = _write_json(
        tmp_path / "dataset_scope_audit.json",
        [{"task_type": "Dice_Count"}],
        "cognition.revision.dataset_scope_audit.v1",
    )

    assert load_rows(path) == [{"task_type": "Dice_Count"}]


def test_render_limitations_summary_contains_required_language_and_rollups(
    tmp_path: Path,
) -> None:
    inputs = _fixture_inputs(tmp_path)

    text = render_limitations_summary(
        dataset_scope_rows=load_rows(inputs["dataset_scope_json"]),
        extended_manifest_rows=load_rows(inputs["extended_manifest_json"]),
        extended_validation_rows=load_rows(inputs["extended_validation_comparison_json"]),
        contribution_notes_md=inputs["contribution_notes_md"].read_text(encoding="utf-8"),
        pass_rate_rows=load_rows(inputs["pass_rate_confidence_json"]),
        threshold_rows=load_rows(inputs["threshold_sensitivity_json"]),
        retry_rows=load_rows(inputs["retry_calibration_json"]),
        failure_rows=load_rows(inputs["failure_taxonomy_json"]),
    )

    for heading in REQUIRED_HEADINGS:
        assert heading in text
    for required in REQUIRED_STRINGS:
        assert required in text
    assert "included: 1" in text
    assert "underpowered: 1" in text
    assert "incompatible: 2" in text
    assert "supports_original: 1" in text
    assert "diverges_from_original: 1" in text
    assert "inconclusive: 1" in text
    assert "Rotation_Match" in text
    assert "Image Matching" in text
    assert "missing validation samples keep this inconclusive" in text
    assert "Geometry_Click" in text
    assert "wilson" in text
    assert "95%" in text
    assert "30%-50% review band rows: 1" in text
    assert "trend-sensitive rows: 1" in text
    assert "Counting: fixed_retry=0.010, adaptive=0.160" in text
    assert "scientific_claim_eligible: 1" in text
    assert "infrastructure_caveated: 1" in text
    assert "not a population-level deployment estimate" in text
    assert " not a population-level deployment estimate" in text


def test_write_limitations_summary_writes_markdown_and_artifact_index(
    tmp_path: Path,
) -> None:
    inputs = _fixture_inputs(tmp_path)
    output_md = tmp_path / "revision" / "phase3-local" / "limitations_summary.md"
    index_json = tmp_path / "revision" / "phase3-local" / "phase3_artifact_index.json"

    written_md, written_index = write_limitations_summary(
        inputs=inputs,
        output_md=output_md,
        artifact_index_json=index_json,
        run_id="phase3-local",
    )

    assert written_md == output_md
    assert written_index == index_json
    assert output_md.exists()
    assert index_json.exists()
    payload = json.loads(index_json.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "cognition.revision.phase3_artifact_index.v1"
    assert payload["run_id"] == "phase3-local"
    assert set(payload["input_artifacts"]) == set(inputs)
    assert payload["output_artifacts"]["limitations_summary_md"] == str(output_md)
    assert payload["output_artifacts"]["phase3_artifact_index_json"] == str(index_json)
    assert set(payload["claim_boundaries"]) == {
        "dataset_scope",
        "extended_validation_slice",
        "threshold_cutoff",
        "failure_taxonomy",
        "live_service_automation",
    }
    assert all(str(path) in payload["input_artifacts"].values() for path in inputs.values())

    index = build_artifact_index(inputs, output_md, "phase3-local")
    assert index["output_artifacts"]["limitations_summary_md"] == str(output_md)


@pytest.mark.parametrize("bad_run_id", ["../phase3", "bad/run"])
def test_cli_rejects_invalid_run_ids_before_writing_outputs(
    tmp_path: Path,
    bad_run_id: str,
) -> None:
    inputs = _fixture_inputs(tmp_path)
    output_root = tmp_path / "revision"

    argv = [
        "--dataset-scope-json",
        str(inputs["dataset_scope_json"]),
        "--extended-manifest-json",
        str(inputs["extended_manifest_json"]),
        "--extended-validation-comparison-json",
        str(inputs["extended_validation_comparison_json"]),
        "--contribution-notes-md",
        str(inputs["contribution_notes_md"]),
        "--pass-rate-confidence-json",
        str(inputs["pass_rate_confidence_json"]),
        "--threshold-sensitivity-json",
        str(inputs["threshold_sensitivity_json"]),
        "--retry-calibration-json",
        str(inputs["retry_calibration_json"]),
        "--failure-taxonomy-json",
        str(inputs["failure_taxonomy_json"]),
        "--output-root",
        str(output_root),
        "--run-id",
        bad_run_id,
    ]
    with pytest.raises(SystemExit):
        main(argv)

    assert not output_root.exists()


def test_cli_writes_default_revision_outputs(tmp_path: Path, capsys) -> None:
    inputs = _fixture_inputs(tmp_path)
    output_root = tmp_path / "revision"

    exit_code = main(
        [
            "--dataset-scope-json",
            str(inputs["dataset_scope_json"]),
            "--extended-manifest-json",
            str(inputs["extended_manifest_json"]),
            "--extended-validation-comparison-json",
            str(inputs["extended_validation_comparison_json"]),
            "--contribution-notes-md",
            str(inputs["contribution_notes_md"]),
            "--pass-rate-confidence-json",
            str(inputs["pass_rate_confidence_json"]),
            "--threshold-sensitivity-json",
            str(inputs["threshold_sensitivity_json"]),
            "--retry-calibration-json",
            str(inputs["retry_calibration_json"]),
            "--failure-taxonomy-json",
            str(inputs["failure_taxonomy_json"]),
            "--output-root",
            str(output_root),
            "--run-id",
            "phase3-local",
        ]
    )

    summary = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert summary["output_md"].endswith("phase3-local/limitations_summary.md")
    assert summary["artifact_index_json"].endswith(
        "phase3-local/phase3_artifact_index.json"
    )
    assert (output_root / "phase3-local" / "limitations_summary.md").exists()
    assert (output_root / "phase3-local" / "phase3_artifact_index.json").exists()
