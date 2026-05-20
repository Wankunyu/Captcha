import csv
import json
from collections.abc import Callable
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from phase041_artifacts import (
    ALLOWED_EVIDENCE_ORIGINS,
    ALLOWED_SLICE_TYPES,
    EXPANDED_ADAPTIVE_SUMMARY_SCHEMA_VERSION,
    EXPANDED_CLAIM_BOUNDARY_SCHEMA_VERSION,
    EXPANDED_DATASET_MANIFEST_SCHEMA_VERSION,
    EXPANDED_PAPER_EVIDENCE_SCHEMA_VERSION,
    EXPANDED_PREFLIGHT_MATRIX_SCHEMA_VERSION,
    EXPANDED_RUN_MATRIX_SCHEMA_VERSION,
    EXPANDED_STATIC_SUMMARY_SCHEMA_VERSION,
    ExpandedAdaptiveSummaryRow,
    ExpandedClaimBoundaryNoteRow,
    ExpandedDatasetManifestRow,
    ExpandedPaperEvidenceRow,
    ExpandedPreflightMatrixRow,
    ExpandedRunMatrixRow,
    ExpandedStaticSummaryRow,
    write_expanded_adaptive_summary,
    write_expanded_claim_boundaries,
    write_expanded_dataset_manifest,
    write_expanded_paper_evidence,
    write_expanded_preflight_matrix,
    write_expanded_run_matrix,
    write_expanded_static_summary,
)


PAPER_FACING_PROVIDER_MODELS = (
    "openai/gpt-5",
    "openai/gpt-5.1_medium",
    "openai/gpt-5.1_none",
    "anthropic/claude-sonnet-4-5",
    "gemini/gemini-2.5-flash",
    "gemini/gemini-2.5-pro",
    "fireworks/accounts_fireworks_models_qwen3-vl-235b-a22b-instruct",
)


def _manifest_row(**overrides: object) -> ExpandedDatasetManifestRow:
    values: dict[str, object] = {
        "run_id": "phase041-test",
        "source_id": "supplement-dice-count",
        "source_path": "expanded_captcha_data/phase04_1/sources/dice",
        "evidence_origin": "supplemented_category",
        "slice_type": "supplement_existing",
        "task_type": "Dice_Count",
        "task_family": "Counting",
        "sample_count": 12,
        "label_format": "integer",
        "metadata_alignment_notes": "source ids mapped to sidecar manifest rows",
        "answer_format_normalization": "integer answers normalized as strings",
        "compatibility_status": "ready_for_static_pipeline",
        "evaluation_status": "selected_for_static",
        "limitation_notes": "selective supplemental slice only",
        "adaptive_eligible": True,
        "static_compatibility_notes": "offline static images with ground truth",
    }
    values.update(overrides)
    return ExpandedDatasetManifestRow(**values)


def _run_matrix_row(**overrides: object) -> ExpandedRunMatrixRow:
    values: dict[str, object] = {
        "matrix_id": "static-openai-gpt5",
        "paper_facing_model_row": True,
        "provider": "openai",
        "model": "gpt-5",
        "provider_model": "openai/gpt-5",
        "run_scope": "static",
        "run_id": "phase041-static-openai-gpt5",
        "task_types": ["Dice_Count", "Click_Order"],
        "materialized_dataset_root": "expanded_captcha_data/phase04_1/evaluator_slice",
        "output_root": "results/revision/phase041-static-openai-gpt5",
        "overwrite": False,
        "resume": True,
    }
    values.update(overrides)
    return ExpandedRunMatrixRow(**values)


def _preflight_row(**overrides: object) -> ExpandedPreflightMatrixRow:
    values: dict[str, object] = {
        "run_id": "phase041-static-openai-gpt5",
        "provider": "openai",
        "model": "gpt-5",
        "provider_model": "openai/gpt-5",
        "run_scope": "static",
        "manifest_sha256": "a" * 64,
        "prompt_config": "prompts_optimized.yaml#phase041-static",
        "expected_request_count": 24,
        "cost_preview": "estimated from non-secret pricing metadata",
        "output_dir": "results/revision/phase041-static-openai-gpt5",
        "preflight_report_path": (
            "results/revision/phase041-static-openai-gpt5/preflight.json"
        ),
    }
    values.update(overrides)
    return ExpandedPreflightMatrixRow(**values)


def _static_summary_row(**overrides: object) -> ExpandedStaticSummaryRow:
    values: dict[str, object] = {
        "run_id": "phase041-static-openai-gpt5",
        "provider": "openai",
        "model": "gpt-5",
        "provider_model": "openai/gpt-5",
        "task_type": "Dice_Count",
        "task_family": "Counting",
        "evidence_origin": "supplemented_category",
        "slice_type": "supplement_existing",
        "sample_count": 12,
        "attempt_count": 12,
        "success_count": 2,
        "scientific_wrong_count": 10,
        "protocol_failure_count": 0,
        "infrastructure_failure_count": 0,
        "pass_rate": 0.1667,
        "run_manifest_path": (
            "results/revision/phase041-static-openai-gpt5/run_manifest.json"
        ),
        "attempt_log_path": "results/revision/phase041-static-openai-gpt5/attempts.jsonl",
        "summary_source_path": "results/revision/phase041-static-openai-gpt5/summary.csv",
        "claim_use": "main_body_direct_evidence",
    }
    values.update(overrides)
    return ExpandedStaticSummaryRow(**values)


def _adaptive_summary_row(**overrides: object) -> ExpandedAdaptiveSummaryRow:
    values: dict[str, object] = {
        "run_id": "phase041-adaptive-openai-gpt5",
        "provider": "openai",
        "model": "gpt-5",
        "provider_model": "openai/gpt-5",
        "task_type": "Dice_Count",
        "task_family": "Counting",
        "evidence_origin": "supplemented_category",
        "slice_type": "supplement_existing",
        "sample_count": 12,
        "session_count": 4,
        "attempt_budget_k": 3,
        "success_count": 1,
        "scientific_wrong_count": 11,
        "protocol_failure_count": 0,
        "infrastructure_failure_count": 0,
        "adaptive_success_rate": 0.25,
        "feedback_mode": "binary-pass-fail",
        "memory_mode": "explicit-policy-notes",
        "stopping_rule": "first-success-or-budget",
        "run_manifest_path": (
            "results/revision/phase041-adaptive-openai-gpt5/adaptive_manifest.json"
        ),
        "adaptive_attempt_log_path": (
            "results/revision/phase041-adaptive-openai-gpt5/adaptive_attempts.jsonl"
        ),
        "adaptive_summary_source_path": (
            "results/revision/phase041-adaptive-openai-gpt5/adaptive_summary.csv"
        ),
        "claim_use": "main_body_caveated",
    }
    values.update(overrides)
    return ExpandedAdaptiveSummaryRow(**values)


def _paper_evidence_row(**overrides: object) -> ExpandedPaperEvidenceRow:
    values: dict[str, object] = {
        "run_id": "phase041-paper",
        "evidence_row_id": "dice-count-openai-gpt5",
        "provider": "openai",
        "model": "gpt-5",
        "provider_model": "openai/gpt-5",
        "task_type": "Dice_Count",
        "task_family": "Counting",
        "evidence_origin": "supplemented_category",
        "slice_type": "supplement_existing",
        "sample_count": 12,
        "original_rate": 0.2,
        "expanded_static_rate": 0.1667,
        "expanded_adaptive_rate": 0.25,
        "agreement_status": "supports_original",
        "divergence_reason": "",
        "claim_boundary_note": "expanded slice supports the original hard-family claim",
        "direct_evidence": True,
        "contextual_sota_only": False,
        "claim_use": "main_body_direct_evidence",
        "source_artifact_path": "results/revision/phase041-paper/evidence.csv",
    }
    values.update(overrides)
    return ExpandedPaperEvidenceRow(**values)


def _claim_boundary_row(**overrides: object) -> ExpandedClaimBoundaryNoteRow:
    values: dict[str, object] = {
        "run_id": "phase041-paper",
        "note_id": "dice-count-boundary",
        "claim_key": "structural-hardness-boundary",
        "task_type": "Dice_Count",
        "task_family": "Counting",
        "evidence_origin": "supplemented_category",
        "agreement_status": "supports_original",
        "divergence_reason": "",
        "claim_use": "main_body_direct_evidence",
        "direct_evidence": True,
        "contextual_sota_only": False,
        "claim_boundary_note": "direct expanded-dataset evidence, not population estimate",
        "limitation_notes": "sidecar supplemental slice only",
        "source_artifact_path": "results/revision/phase041-paper/claim_boundaries.csv",
        "visible_in_main_body": True,
    }
    values.update(overrides)
    return ExpandedClaimBoundaryNoteRow(**values)


def test_phase041_schema_versions_are_exact() -> None:
    assert (
        EXPANDED_DATASET_MANIFEST_SCHEMA_VERSION
        == "cognition.revision.phase041.expanded_dataset_manifest.v1"
    )
    assert EXPANDED_RUN_MATRIX_SCHEMA_VERSION == "cognition.revision.phase041.run_matrix.v1"
    assert (
        EXPANDED_PREFLIGHT_MATRIX_SCHEMA_VERSION
        == "cognition.revision.phase041.preflight_matrix.v1"
    )
    assert (
        EXPANDED_STATIC_SUMMARY_SCHEMA_VERSION
        == "cognition.revision.phase041.static_summary.v1"
    )
    assert (
        EXPANDED_ADAPTIVE_SUMMARY_SCHEMA_VERSION
        == "cognition.revision.phase041.adaptive_summary.v1"
    )
    assert (
        EXPANDED_PAPER_EVIDENCE_SCHEMA_VERSION
        == "cognition.revision.phase041.paper_evidence.v1"
    )
    assert (
        EXPANDED_CLAIM_BOUNDARY_SCHEMA_VERSION
        == "cognition.revision.phase041.claim_boundary.v1"
    )


def test_phase041_models_forbid_extra_fields() -> None:
    rows = [
        _manifest_row(),
        _run_matrix_row(),
        _preflight_row(),
        _static_summary_row(),
        _adaptive_summary_row(),
        _paper_evidence_row(),
        _claim_boundary_row(),
    ]

    for row in rows:
        with pytest.raises(ValidationError):
            row.__class__.model_validate({**row.model_dump(), "unexpected": "value"})


def test_manifest_requires_d08_provenance_fields() -> None:
    required_fields = (
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
    )
    row = _manifest_row().model_dump()

    for field in required_fields:
        payload = dict(row)
        payload.pop(field)
        with pytest.raises(ValidationError):
            ExpandedDatasetManifestRow.model_validate(payload)


def test_manifest_vocabularies_and_new_category_caveat() -> None:
    assert {
        "original_captchaworld",
        "supplemented_category",
        "new_category",
    }.issubset(ALLOWED_EVIDENCE_ORIGINS)
    assert {"original", "supplement_existing", "new_category"}.issubset(
        ALLOWED_SLICE_TYPES
    )

    for evidence_origin in (
        "original_captchaworld",
        "supplemented_category",
        "new_category",
    ):
        row = _manifest_row(
            evidence_origin=evidence_origin,
            slice_type="new_category"
            if evidence_origin == "new_category"
            else "supplement_existing",
            static_compatibility_notes=(
                "new static-compatible offline category"
                if evidence_origin == "new_category"
                else "offline static images with ground truth"
            ),
        )
        assert row.evidence_origin == evidence_origin

    with pytest.raises(ValidationError):
        _manifest_row(
            evidence_origin="new_category",
            slice_type="new_category",
            static_compatibility_notes="",
        )


def test_run_matrix_requires_paper_facing_model_rows_and_runtime_fields() -> None:
    required_fields = (
        "paper_facing_model_row",
        "provider",
        "model",
        "provider_model",
        "run_scope",
        "run_id",
        "task_types",
        "materialized_dataset_root",
        "output_root",
        "overwrite",
        "resume",
    )
    row = _run_matrix_row().model_dump()

    for provider_model in PAPER_FACING_PROVIDER_MODELS:
        provider, model = provider_model.split("/", 1)
        assert (
            _run_matrix_row(
                matrix_id=f"static-{provider}-{model}",
                provider=provider,
                model=model,
                provider_model=provider_model,
            ).provider_model
            == provider_model
        )

    for field in required_fields:
        payload = dict(row)
        payload.pop(field)
        with pytest.raises(ValidationError):
            ExpandedRunMatrixRow.model_validate(payload)

    with pytest.raises(ValidationError):
        _run_matrix_row(paper_facing_model_row=False)
    with pytest.raises(ValidationError):
        _run_matrix_row(run_scope="live-browser")


def test_preflight_matrix_requires_hash_cost_and_output_fields() -> None:
    required_fields = (
        "manifest_sha256",
        "prompt_config",
        "expected_request_count",
        "cost_preview",
        "output_dir",
        "preflight_report_path",
    )
    row = _preflight_row().model_dump()

    for field in required_fields:
        payload = dict(row)
        payload.pop(field)
        with pytest.raises(ValidationError):
            ExpandedPreflightMatrixRow.model_validate(payload)


def test_paper_evidence_requires_visible_caveats_and_direct_evidence_flags() -> None:
    required_fields = (
        "agreement_status",
        "divergence_reason",
        "claim_boundary_note",
        "direct_evidence",
        "contextual_sota_only",
    )
    row = _paper_evidence_row().model_dump()

    for field in required_fields:
        payload = dict(row)
        payload.pop(field)
        with pytest.raises(ValidationError):
            ExpandedPaperEvidenceRow.model_validate(payload)

    with pytest.raises(ValidationError):
        _paper_evidence_row(direct_evidence=False, claim_boundary_note="")
    with pytest.raises(ValidationError):
        _paper_evidence_row(contextual_sota_only=True, direct_evidence=True)
    with pytest.raises(ValidationError):
        _paper_evidence_row(agreement_status="diverges_from_original", divergence_reason="")


def test_writers_create_parent_dirs_and_emit_schema_payloads(tmp_path: Path) -> None:
    writer_cases: tuple[
        tuple[
            Callable[[Path, Path, list[BaseModel]], tuple[Path, Path]],
            str,
            BaseModel,
            str,
        ],
        ...,
    ] = (
        (
            write_expanded_dataset_manifest,
            EXPANDED_DATASET_MANIFEST_SCHEMA_VERSION,
            _manifest_row(),
            "expanded_dataset_manifest",
        ),
        (
            write_expanded_run_matrix,
            EXPANDED_RUN_MATRIX_SCHEMA_VERSION,
            _run_matrix_row(),
            "expanded_run_matrix",
        ),
        (
            write_expanded_preflight_matrix,
            EXPANDED_PREFLIGHT_MATRIX_SCHEMA_VERSION,
            _preflight_row(),
            "expanded_preflight_matrix",
        ),
        (
            write_expanded_static_summary,
            EXPANDED_STATIC_SUMMARY_SCHEMA_VERSION,
            _static_summary_row(),
            "expanded_static_summary",
        ),
        (
            write_expanded_adaptive_summary,
            EXPANDED_ADAPTIVE_SUMMARY_SCHEMA_VERSION,
            _adaptive_summary_row(),
            "expanded_adaptive_summary",
        ),
        (
            write_expanded_paper_evidence,
            EXPANDED_PAPER_EVIDENCE_SCHEMA_VERSION,
            _paper_evidence_row(),
            "expanded_paper_evidence",
        ),
        (
            write_expanded_claim_boundaries,
            EXPANDED_CLAIM_BOUNDARY_SCHEMA_VERSION,
            _claim_boundary_row(),
            "expanded_claim_boundary",
        ),
    )

    for writer, schema_version, row, stem in writer_cases:
        csv_path = tmp_path / stem / "nested" / f"{stem}.csv"
        json_path = tmp_path / stem / "nested" / f"{stem}.json"

        writer(csv_path, json_path, [row])

        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            csv_rows = list(csv.DictReader(handle))
        with json_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        assert csv_rows[0]["schema_version"] == schema_version
        assert payload["schema_version"] == schema_version
        assert payload["rows"][0]["schema_version"] == schema_version
