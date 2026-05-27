import csv
import json

import pytest
from pydantic import ValidationError

from cognition.phase3_artifacts import (
    DATASET_SCOPE_SCHEMA_VERSION,
    EXTENDED_DATASET_MANIFEST_SCHEMA_VERSION,
    EXTENDED_VALIDATION_COMPARISON_SCHEMA_VERSION,
    FAILURE_TAXONOMY_SCHEMA_VERSION,
    PASS_RATE_CONFIDENCE_SCHEMA_VERSION,
    RETRY_CALIBRATION_SCHEMA_VERSION,
    THRESHOLD_SENSITIVITY_SCHEMA_VERSION,
    DatasetScopeAuditRow,
    ExtendedDatasetManifestRow,
    ExtendedValidationComparisonRow,
    FailureTaxonomyRow,
    PassRateConfidenceRow,
    RetryCalibrationRow,
    ThresholdSensitivityRow,
    write_csv,
    write_json,
)


def _dataset_scope_row() -> DatasetScopeAuditRow:
    return DatasetScopeAuditRow(
        run_id="run-1",
        task_type="Dice_Count",
        task_family="Counting",
        dataset_dir="Dice_Count",
        scope_status="included",
        support_status="supported",
        pipeline_compatibility="compatible_static_answer",
        dataset_sample_count=25,
        evaluated_n_exp1=25,
        evaluated_n_exp2=25,
        evaluated_n_exp3=25,
        evaluated_n_exp4=0,
        underpowered_threshold=20,
        underpowered=False,
        prompt_key_status="present",
        few_shot_key_status="present",
        answer_format_notes="numeric answer",
        normalization_notes="standardized integer labels",
        removal_decision="kept",
        reason="supported and evaluated",
    )


def _extended_manifest_row() -> ExtendedDatasetManifestRow:
    return ExtendedDatasetManifestRow(
        run_id="run-1",
        source_id="supplement-dice",
        evidence_origin="supplemented_category",
        slice_type="supplement_existing",
        task_type="Dice_Count",
        task_family="Counting",
        source_path="extended/dice",
        sample_count=12,
        label_format="integer",
        metadata_alignment_notes="aligned with CaptchaWorld ids",
        answer_format_normalization="integers normalized as strings for CSV",
        task_family_grouping_notes="grouped as Counting",
        normalization_decisions="removed ambiguous samples",
        compatibility_status="ready_for_static_pipeline",
        evaluation_status="selected_for_validation",
        adaptive_eligible=True,
        adaptive_slice_priority=1,
        validation_question=(
            "do the conclusions drawn from the original dataset still hold on the new "
            "dataset slice?"
        ),
        rerun_policy="selective-validation-slice",
        limitation_note="selective slice only",
    )


def test_schema_versions_are_exact() -> None:
    assert DATASET_SCOPE_SCHEMA_VERSION == "cognition.revision.dataset_scope_audit.v1"
    assert (
        EXTENDED_DATASET_MANIFEST_SCHEMA_VERSION
        == "cognition.revision.extended_dataset_manifest.v1"
    )
    assert (
        EXTENDED_VALIDATION_COMPARISON_SCHEMA_VERSION
        == "cognition.revision.extended_validation_comparison.v1"
    )
    assert PASS_RATE_CONFIDENCE_SCHEMA_VERSION == "cognition.revision.pass_rate_confidence.v1"
    assert (
        THRESHOLD_SENSITIVITY_SCHEMA_VERSION
        == "cognition.revision.threshold_sensitivity.v1"
    )
    assert RETRY_CALIBRATION_SCHEMA_VERSION == "cognition.revision.retry_calibration.v1"
    assert FAILURE_TAXONOMY_SCHEMA_VERSION == "cognition.revision.failure_taxonomy.v1"


def test_dataset_scope_model_forbids_extra_fields_and_rejects_unknown_enums() -> None:
    row = _dataset_scope_row()

    assert row.schema_version == DATASET_SCOPE_SCHEMA_VERSION
    with pytest.raises(ValidationError):
        DatasetScopeAuditRow.model_validate({**row.model_dump(), "unexpected": "value"})
    with pytest.raises(ValidationError):
        DatasetScopeAuditRow.model_validate({**row.model_dump(), "scope_status": "maybe"})
    with pytest.raises(ValidationError):
        DatasetScopeAuditRow.model_validate(
            {**row.model_dump(), "pipeline_compatibility": "browser_required"}
        )


def test_extended_manifest_and_comparison_enums() -> None:
    manifest_row = _extended_manifest_row()
    comparison_row = ExtendedValidationComparisonRow(
        run_id="run-1",
        source_id="supplement-dice",
        evidence_origin="supplemented_category",
        slice_type="supplement_existing",
        task_type="Dice_Count",
        task_family="Counting",
        original_conclusion_label="hard",
        original_rate=0.2,
        validation_slice_rate=0.25,
        validation_sample_count=12,
        agreement_status="supports_original",
        divergence_reason="",
        comparison_caveat="selective validation slice",
        outcome_source_path="validation.csv",
    )

    assert manifest_row.schema_version == EXTENDED_DATASET_MANIFEST_SCHEMA_VERSION
    assert comparison_row.schema_version == EXTENDED_VALIDATION_COMPARISON_SCHEMA_VERSION
    with pytest.raises(ValidationError):
        ExtendedDatasetManifestRow.model_validate(
            {**manifest_row.model_dump(), "evidence_origin": "merged_dataset"}
        )
    with pytest.raises(ValidationError):
        ExtendedValidationComparisonRow.model_validate(
            {**comparison_row.model_dump(), "agreement_status": "ambiguous"}
        )


def test_downstream_statistical_rows_allow_nullable_ci_and_optional_observed_fields() -> None:
    confidence = PassRateConfidenceRow(
        run_id="run-1",
        aggregation_level="task_type",
        provider="openai",
        model="gpt-5",
        provider_model="openai/gpt-5",
        experiment="exp2",
        task_type="Dice_Count",
        task_family="Counting",
        n_attempts=0,
        n_success=0,
        pass_rate=0.0,
        ci_method="wilson",
        ci_confidence=0.95,
        ci_low=None,
        ci_high=None,
        underpowered_threshold=20,
        underpowered=True,
        source_path="results/exp2/openai/gpt-5/results.csv",
    )
    threshold = ThresholdSensitivityRow(
        run_id="run-1",
        provider="openai",
        model="gpt-5",
        provider_model="openai/gpt-5",
        task_type="Geometry_Click",
        task_family="Spatial",
        primary_experiment="exp2",
        primary_rate=0.35,
        max_observed_rate=0.45,
        label="hard",
        margin_to_cutoff=-0.05,
        cutoff=0.4,
        review_band_low=0.3,
        review_band_high=0.5,
        in_30_50_review_band=True,
        ci_crosses_cutoff=True,
        trend_sensitive=True,
        trend_delta=0.1,
        trend_sources="exp2,adaptive",
        cutoff_note="40 percent cutoff is operational, not universal.",
    )
    retry = RetryCalibrationRow(
        run_id="run-1",
        provider="openai",
        model="gpt-5",
        provider_model="openai/gpt-5",
        task_type="Dice_Count",
        task_family="Counting",
        exp2_pass_at_1=0.2,
        attempt_budget_k=3,
        bernoulli_success_at_k=0.488,
        observed_fixed_retry_success=None,
        observed_adaptive_compatible_success=None,
        signed_error_fixed_retry=None,
        absolute_error_fixed_retry=None,
        signed_error_adaptive=None,
        absolute_error_adaptive=None,
        sample_count=10,
        scientific_wrong_count=8,
        protocol_failure_count=0,
        infrastructure_failure_count=0,
        raw_observed_rate=0.2,
        scientific_rate=0.2,
        comparison_contract="task type primary, same attempt budget",
    )
    taxonomy = FailureTaxonomyRow(
        run_id="run-1",
        aggregation_level="task_type",
        provider="openai",
        model="gpt-5",
        provider_model="openai/gpt-5",
        task_type="Dice_Count",
        task_family="Counting",
        success_count=2,
        scientific_wrong_count=8,
        protocol_failure_count=0,
        infrastructure_failure_count=0,
        total_count=10,
        raw_observed_rate=0.2,
        scientific_rate=0.2,
        failure_taxonomy_source="adaptive_summary",
        claim_use="scientific_claim_eligible",
        hardness_caveat="none",
    )

    assert confidence.ci_low is None
    assert confidence.ci_high is None
    assert threshold.in_30_50_review_band is True
    assert retry.observed_fixed_retry_success is None
    assert taxonomy.claim_use == "scientific_claim_eligible"
    with pytest.raises(ValidationError):
        FailureTaxonomyRow.model_validate({**taxonomy.model_dump(), "claim_use": "unsafe"})


def test_writers_create_parent_dirs_and_emit_schema_payload(tmp_path) -> None:
    row = _dataset_scope_row()
    csv_path = tmp_path / "nested" / "dataset_scope_audit.csv"
    json_path = tmp_path / "nested" / "dataset_scope_audit.json"

    write_csv(csv_path, DatasetScopeAuditRow.model_fields, [row])
    write_json(json_path, DATASET_SCOPE_SCHEMA_VERSION, [row])

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    with json_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    assert csv_rows[0]["schema_version"] == DATASET_SCOPE_SCHEMA_VERSION
    assert csv_rows[0]["task_type"] == "Dice_Count"
    assert payload["schema_version"] == DATASET_SCOPE_SCHEMA_VERSION
    assert payload["rows"][0]["task_type"] == "Dice_Count"
