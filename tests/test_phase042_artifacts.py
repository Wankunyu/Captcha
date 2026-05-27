from collections.abc import Callable

import pytest
from pydantic import BaseModel, ValidationError

from cognition.phase042_artifacts import (
    PHASE042_ADAPTIVE_SUMMARY_SCHEMA_VERSION,
    PHASE042_EVIDENCE_ANALYSIS_SCHEMA_VERSION,
    PHASE042_FINAL_EVIDENCE_SCHEMA_VERSION,
    PHASE042_PREFLIGHT_MATRIX_SCHEMA_VERSION,
    PHASE042_SELECTED_MANIFEST_SCHEMA_VERSION,
    PHASE042_SELECTED_SOURCE_KINDS,
    PHASE042_STATIC_SUMMARY_SCHEMA_VERSION,
    PHASE042_VALIDATION_REPORT_SCHEMA_VERSION,
    Phase042AdaptiveSummaryRow,
    Phase042EvidenceAnalysisRow,
    Phase042FinalEvidenceRow,
    Phase042PreflightMatrixRow,
    Phase042SelectedManifestRow,
    Phase042StaticSummaryRow,
    Phase042ValidationReportRow,
)


def _selected_row(**overrides: object) -> Phase042SelectedManifestRow:
    values: dict[str, object] = {
        "selected_id": "phase042-dice-count-open-source",
        "candidate_id": "candidate-dice-count-open-source",
        "source_path": "expanded_captcha_data/phase04_2/candidates/Dice_Count",
        "candidate_image_paths": [
            "expanded_captcha_data/phase04_2/candidates/Dice_Count/sample-001.png"
        ],
        "source_kind": "open_source_dataset",
        "source_provenance_class": "preferred_real_external",
        "source_citation": "Example open-source CAPTCHA dataset",
        "source_license": "CC-BY-4.0",
        "source_provenance_notes": (
            "Real external CAPTCHA samples newly introduced relative to current "
            "captcha_data."
        ),
        "evidence_origin": "supplemented_category",
        "slice_type": "supplement_existing",
        "task_type": "Dice_Count",
        "task_family": "Counting",
        "sample_count": 1,
        "label_format": "integer",
        "metadata_alignment_notes": "source ids mapped to selected manifest rows",
        "answer_format_normalization": "integer answers normalized as strings",
        "compatibility_status": "ready_for_static_pipeline",
        "evaluation_status": "selected_for_static",
        "limitation_notes": "selective corrected sidecar slice only",
        "adaptive_eligible": True,
        "static_compatibility_notes": "offline static images with ground truth",
        "novelty_sha256": ["a" * 64],
        "novelty_hash_report_path": (
            "expanded_captcha_data/phase04_2/novelty_hash_report.json"
        ),
        "exact_captcha_data_match": False,
        "perceptual_warning_count": 0,
        "review_warnings": [],
    }
    values.update(overrides)
    return Phase042SelectedManifestRow(**values)


def _gpt_selected_row(**overrides: object) -> Phase042SelectedManifestRow:
    values: dict[str, object] = {
        "source_kind": "gpt_image_open_captchaworld_style",
        "source_provenance_class": "gpt_image_generated_fallback",
        "source_citation": "",
        "source_license": "",
        "source_provenance_notes": (
            "GPT Image generated Open CaptchaWorld-style fallback samples newly "
            "introduced relative to current captcha_data."
        ),
        "gpt_image_generation_prompt": "Generate an Open CaptchaWorld-style count task.",
        "gpt_image_model": "gpt-image-1",
        "gpt_image_generation_date": "2026-05-21",
        "open_captchaworld_style_rationale": (
            "Static image with countable objects and no live-service automation."
        ),
    }
    values.update(overrides)
    return _selected_row(**values)


def _validation_report_row(**overrides: object) -> Phase042ValidationReportRow:
    values: dict[str, object] = {
        "candidate_id": "candidate-dice-count-open-source",
        "task_type": "Dice_Count",
        "source_kind": "open_source_dataset",
        "source_path": "expanded_captcha_data/phase04_2/candidates/Dice_Count",
        "candidate_image_paths": [
            "expanded_captcha_data/phase04_2/candidates/Dice_Count/sample-001.png"
        ],
        "validation_status": "rejected",
        "selected_manifest_eligible": False,
        "rejection_reason": "missing required source image",
        "exact_captcha_data_match": False,
        "exact_captcha_data_match_paths": [],
        "novelty_sha256": [],
        "novelty_hash_report_path": (
            "expanded_captcha_data/phase04_2/novelty_hash_report.json"
        ),
        "perceptual_warning_count": 0,
        "review_warnings": [],
    }
    values.update(overrides)
    return Phase042ValidationReportRow(**values)


def _preflight_row(**overrides: object) -> Phase042PreflightMatrixRow:
    values: dict[str, object] = {
        "run_id": "phase04_2_static_supplemental_openai_gpt5",
        "provider": "openai",
        "model": "gpt-5",
        "provider_model": "openai/gpt-5",
        "run_scope": "static",
        "selected_manifest_path": (
            "expanded_captcha_data/phase04_2/phase042_selected_manifest.json"
        ),
        "selected_manifest_sha256": "b" * 64,
        "materialized_dataset_root": "expanded_captcha_data/phase04_2/evaluator_slice",
        "task_types": ["Dice_Count"],
        "prompt_config": {"prompts_file": "prompts_optimized.yaml"},
        "expected_request_count": 1,
        "cost_preview": {"unavailable_reason": "pricing metadata not provided"},
        "output_dir": "results/local_runs/phase04_2_static_supplemental",
        "preflight_report_path": (
            "results/local_runs/phase04_2_static_supplemental/preflight.json"
        ),
        "overwrite": False,
        "resume": True,
    }
    values.update(overrides)
    return Phase042PreflightMatrixRow(**values)


def _static_summary_row(**overrides: object) -> Phase042StaticSummaryRow:
    values: dict[str, object] = {
        "run_id": "phase04_2_static_supplemental_openai_gpt5",
        "provider": "openai",
        "model": "gpt-5",
        "provider_model": "openai/gpt-5",
        "task_type": "Dice_Count",
        "task_family": "Counting",
        "evidence_origin": "supplemented_category",
        "sample_count": 1,
        "attempt_count": 1,
        "success_count": 0,
        "scientific_wrong_count": 1,
        "protocol_failure_count": 0,
        "infrastructure_failure_count": 0,
        "pass_rate": 0.0,
        "run_manifest_path": "results/local_runs/phase04_2_static/run_manifest.json",
        "attempt_log_path": "results/local_runs/phase04_2_static/attempts.jsonl",
        "summary_source_path": "results/local_runs/phase04_2_static/summary.csv",
        "selected_manifest_path": (
            "expanded_captcha_data/phase04_2/phase042_selected_manifest.json"
        ),
        "claim_use": "main_body_direct_evidence",
    }
    values.update(overrides)
    return Phase042StaticSummaryRow(**values)


def _adaptive_summary_row(**overrides: object) -> Phase042AdaptiveSummaryRow:
    values: dict[str, object] = {
        "run_id": "phase04_2_adaptive_supplemental_openai_gpt5",
        "provider": "openai",
        "model": "gpt-5",
        "provider_model": "openai/gpt-5",
        "task_type": "Dice_Count",
        "task_family": "Counting",
        "evidence_origin": "supplemented_category",
        "sample_count": 1,
        "session_count": 1,
        "attempt_budget_k": 6,
        "success_count": 0,
        "scientific_wrong_count": 6,
        "protocol_failure_count": 0,
        "infrastructure_failure_count": 0,
        "adaptive_success_rate": 0.0,
        "feedback_mode": "binary-pass-fail",
        "memory_mode": "explicit-policy-notes",
        "stopping_rule": "first-success-or-budget",
        "run_manifest_path": "results/local_runs/phase04_2_adaptive/manifest.json",
        "adaptive_attempt_log_path": (
            "results/local_runs/phase04_2_adaptive/adaptive_attempts.jsonl"
        ),
        "adaptive_summary_source_path": (
            "results/local_runs/phase04_2_adaptive/adaptive_summary.csv"
        ),
        "selected_manifest_path": (
            "expanded_captcha_data/phase04_2/phase042_selected_manifest.json"
        ),
        "claim_use": "main_body_caveated",
    }
    values.update(overrides)
    return Phase042AdaptiveSummaryRow(**values)


def _evidence_analysis_row(**overrides: object) -> Phase042EvidenceAnalysisRow:
    values: dict[str, object] = {
        "analysis_id": "dice-count-openai-gpt5",
        "task_type": "Dice_Count",
        "task_family": "Counting",
        "provider_model": "openai/gpt-5",
        "sample_count": 1,
        "original_rate": 0.2,
        "corrected_static_rate": 0.0,
        "corrected_adaptive_rate": 0.0,
        "agreement_status": "supports_original",
        "divergence_reason": "",
        "scientific_wrong_count": 1,
        "protocol_failure_count": 0,
        "infrastructure_failure_count": 0,
        "selected_manifest_path": (
            "expanded_captcha_data/phase04_2/phase042_selected_manifest.json"
        ),
        "claim_boundary_note": "corrected sidecar evidence only",
    }
    values.update(overrides)
    return Phase042EvidenceAnalysisRow(**values)


def _final_evidence_row(**overrides: object) -> Phase042FinalEvidenceRow:
    values: dict[str, object] = {
        "run_id": "exp5_final_outputs_20260522",
        "evidence_row_id": "dice-count-openai-gpt5",
        "provider": "openai",
        "model": "gpt-5",
        "provider_model": "openai/gpt-5",
        "task_type": "Dice_Count",
        "task_family": "Counting",
        "evidence_origin": "supplemented_category",
        "sample_count": 1,
        "original_rate": 0.2,
        "corrected_static_rate": 0.0,
        "corrected_adaptive_rate": 0.0,
        "agreement_status": "supports_original",
        "divergence_reason": "",
        "scientific_wrong_count": 1,
        "protocol_failure_count": 0,
        "infrastructure_failure_count": 0,
        "claim_boundary_note": "direct corrected expanded evidence only",
        "direct_evidence": True,
        "contextual_sota_only": False,
        "claim_use": "main_body_direct_evidence",
        "source_artifact_path": "results/exp5/final_outputs_20260522/evidence.csv",
        "selected_manifest_path": (
            "expanded_captcha_data/phase04_2/phase042_selected_manifest.json"
        ),
    }
    values.update(overrides)
    return Phase042FinalEvidenceRow(**values)


def test_phase042_schema_versions_are_exact() -> None:
    assert (
        PHASE042_SELECTED_MANIFEST_SCHEMA_VERSION
        == "cognition.revision.phase042.selected_manifest.v1"
    )
    assert (
        PHASE042_VALIDATION_REPORT_SCHEMA_VERSION
        == "cognition.revision.phase042.validation_report.v1"
    )
    assert (
        PHASE042_PREFLIGHT_MATRIX_SCHEMA_VERSION
        == "cognition.revision.phase042.preflight_matrix.v1"
    )
    assert (
        PHASE042_STATIC_SUMMARY_SCHEMA_VERSION
        == "cognition.revision.phase042.static_summary.v1"
    )
    assert (
        PHASE042_ADAPTIVE_SUMMARY_SCHEMA_VERSION
        == "cognition.revision.phase042.adaptive_summary.v1"
    )
    assert (
        PHASE042_EVIDENCE_ANALYSIS_SCHEMA_VERSION
        == "cognition.revision.phase042.evidence_analysis.v1"
    )
    assert (
        PHASE042_FINAL_EVIDENCE_SCHEMA_VERSION
        == "cognition.revision.phase042.final_evidence.v1"
    )


def test_phase042_selected_source_kinds_are_exact() -> None:
    assert PHASE042_SELECTED_SOURCE_KINDS == {
        "peer_reviewed_paper_dataset",
        "open_source_dataset",
        "gpt_image_open_captchaworld_style",
    }


def test_selected_rows_require_novelty_hash_report_path() -> None:
    with pytest.raises(ValidationError, match="novelty_hash_report_path"):
        _selected_row(novelty_hash_report_path="")


def test_selected_rows_reject_synthetic_fixture_source_kind() -> None:
    with pytest.raises(ValidationError, match="source_kind"):
        _selected_row(source_kind="synthetic_fixture")


def test_selected_rows_require_warning_for_exact_captcha_data_matches() -> None:
    with pytest.raises(ValidationError, match="review warning"):
        _selected_row(exact_captcha_data_match=True)


def test_selected_rows_allow_exact_captcha_data_matches_with_warning() -> None:
    row = _selected_row(
        exact_captcha_data_match=True,
        review_warnings=[
            "exact SHA-256 match warning: candidate image hash already exists "
            "under current captcha_data: captcha_data/Dice_Count/original.png"
        ],
    )

    assert row.exact_captcha_data_match is True


def test_selected_rows_reject_phase041_references() -> None:
    with pytest.raises(ValidationError, match="Phase 04.1"):
        _selected_row(source_path="expanded_captcha_data/phase04_1/sources/dice")


def test_real_external_rows_require_source_citation_license_and_notes() -> None:
    for field_name in (
        "source_citation",
        "source_license",
        "source_provenance_notes",
    ):
        with pytest.raises(ValidationError, match=field_name):
            _selected_row(**{field_name: ""})


def test_gpt_image_rows_require_generation_metadata() -> None:
    for field_name in (
        "gpt_image_generation_prompt",
        "gpt_image_model",
        "gpt_image_generation_date",
        "open_captchaworld_style_rationale",
    ):
        with pytest.raises(ValidationError, match=field_name):
            _gpt_selected_row(**{field_name: ""})


def test_validation_report_rejected_rows_require_rejection_reason() -> None:
    with pytest.raises(ValidationError, match="rejection_reason"):
        _validation_report_row(rejection_reason="")


def test_phase042_models_forbid_extra_fields() -> None:
    builders: list[tuple[type[BaseModel], Callable[[], BaseModel]]] = [
        (Phase042SelectedManifestRow, _selected_row),
        (Phase042ValidationReportRow, _validation_report_row),
        (Phase042PreflightMatrixRow, _preflight_row),
        (Phase042StaticSummaryRow, _static_summary_row),
        (Phase042AdaptiveSummaryRow, _adaptive_summary_row),
        (Phase042EvidenceAnalysisRow, _evidence_analysis_row),
        (Phase042FinalEvidenceRow, _final_evidence_row),
    ]
    for model, builder in builders:
        assert model.model_config["extra"] == "forbid"
        values = builder().model_dump()
        values["unexpected_field"] = "not allowed"
        with pytest.raises(ValidationError, match="unexpected_field"):
            model.model_validate(values)
