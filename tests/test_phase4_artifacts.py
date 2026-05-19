import csv
import json

import pytest
from pydantic import ValidationError

from phase4_artifacts import (
    BASELINE_COMPARISON_SCHEMA_VERSION,
    BASELINE_COVERAGE_SCHEMA_VERSION,
    EXTERNAL_IMPORT_VALIDATION_SCHEMA_VERSION,
    PAPER_BASELINE_TABLE_SCHEMA_VERSION,
    BaselineComparisonRow,
    BaselineCoverageRow,
    ExternalImportValidationRow,
    PaperBaselineRow,
    write_baseline_comparison,
    write_baseline_coverage,
    write_external_import_validation,
    write_paper_baseline_table,
)


def _coverage_row(**overrides: object) -> BaselineCoverageRow:
    values: dict[str, object] = {
        "run_id": "phase4-test",
        "system_name": "Halligan",
        "system_class": "specialized_solver",
        "evidence_source_type": "validated-import",
        "source_url": "https://example.test/halligan",
        "source_year": 2025,
        "solver_architecture": "agentic VLM search solver",
        "threat_model": "offline benchmark solving",
        "dataset_scale": "2600 challenges",
        "captcha_families": ["visual reasoning", "interaction"],
        "external_task_label": "arkose/dice_match",
        "mapped_local_task_type": "Dice_Count",
        "mapped_local_family": "Counting",
        "mapping_confidence": "mechanism-level",
        "new_or_supplemental_category_reason": "semantic dice matching import",
        "reported_metric_name": "success_rate",
        "reported_metric_value": 0.607,
        "reported_metric_unit": "rate",
        "artifact_availability": "public artifact",
        "license": "MIT",
        "data_use_constraints": "offline benchmark only",
        "latency_coverage": "reported",
        "cost_coverage": "reported",
        "failure_mode_analysis": "reported in paper",
        "defense_methodology_relevance": "baseline comparison",
        "primary_status": "adapter-run",
        "caveat_tags": ["dataset-mismatch"],
        "status_reason": "",
        "checked_sources": ["paper", "artifact record"],
        "missing_items": [],
        "last_checked_date": "2026-05-19",
    }
    values.update(overrides)
    return BaselineCoverageRow(**values)


def _import_validation_row(**overrides: object) -> ExternalImportValidationRow:
    values: dict[str, object] = {
        "run_id": "phase4-test",
        "system_name": "Halligan",
        "source_key": "Halligan::arkose/dice_match",
        "external_task_label": "arkose/dice_match",
        "mapped_local_task_type": "Dice_Count",
        "required_fields_status": "pass",
        "metric_definition_status": "pass",
        "task_label_status": "pass",
        "sample_count_status": "pass",
        "artifact_license_status": "pass",
        "data_use_status": "pass",
        "comparability_status": "pass",
        "validation_status": "pass",
        "sample_count": 100,
        "reported_metric_name": "success_rate",
        "reported_metric_value": 0.61,
        "reported_metric_unit": "rate",
        "normalized_success_rate": 0.61,
        "diagnostic_notes": "validated offline import row",
        "user_confirmed_replacement": False,
    }
    values.update(overrides)
    return ExternalImportValidationRow(**values)


def _comparison_row(**overrides: object) -> BaselineComparisonRow:
    values: dict[str, object] = {
        "run_id": "phase4-test",
        "system_name": "Halligan",
        "source_key": "Halligan::arkose/dice_match",
        "system_class": "specialized_solver",
        "evidence_source_type": "validated-import",
        "primary_status": "adapter-run",
        "caveat_tags": [],
        "reported_metric_name": "success_rate",
        "reported_metric_value": 0.61,
        "reported_metric_unit": "rate",
        "normalized_success_rate": 0.61,
        "metric_definition_status": "pass",
        "sample_count_status": "pass",
        "comparability_status": "pass",
        "directly_comparable": True,
        "comparability_caveat": "",
        "comparability_note": "",
        "comparison_basis": "validated Halligan import row",
        "source_url": "https://example.test/halligan",
    }
    values.update(overrides)
    return BaselineComparisonRow(**values)


def _paper_row(**overrides: object) -> PaperBaselineRow:
    values: dict[str, object] = {
        "run_id": "phase4-test",
        "system_name": "Halligan",
        "system_class": "specialized_solver",
        "primary_status": "adapter-run",
        "reported_metric_display": "61% success rate",
        "reported_metric_name": "success_rate",
        "reported_metric_value": 0.61,
        "reported_metric_unit": "rate",
        "normalized_success_rate": 0.61,
        "directly_comparable": True,
        "comparability_caveat": "",
        "comparability_note": "",
        "caveat_tags": [],
        "source_note": "validated import",
        "paper_table_note": "directly comparable imported subset",
    }
    values.update(overrides)
    return PaperBaselineRow(**values)


def test_schema_versions_are_exact() -> None:
    assert BASELINE_COVERAGE_SCHEMA_VERSION == "cognition.revision.baseline_coverage.v1"
    assert (
        EXTERNAL_IMPORT_VALIDATION_SCHEMA_VERSION
        == "cognition.revision.external_import_validation.v1"
    )
    assert BASELINE_COMPARISON_SCHEMA_VERSION == "cognition.revision.baseline_comparison.v1"
    assert PAPER_BASELINE_TABLE_SCHEMA_VERSION == "cognition.revision.paper_baseline_table.v1"


def test_phase4_models_forbid_extra_fields() -> None:
    rows = [
        _coverage_row(),
        _import_validation_row(),
        _comparison_row(),
        _paper_row(),
    ]

    for row in rows:
        with pytest.raises(ValidationError):
            row.__class__.model_validate({**row.model_dump(), "unexpected": "value"})


def test_unknown_vocabularies_raise_validation_errors() -> None:
    with pytest.raises(ValidationError):
        _coverage_row(primary_status="maybe-direct")
    with pytest.raises(ValidationError):
        _coverage_row(caveat_tags=["metric-mismatch", "secret-unverified"])
    with pytest.raises(ValidationError):
        _coverage_row(system_class="browser_automation_solver")
    with pytest.raises(ValidationError):
        _import_validation_row(validation_status="unknown")


def test_phase4_status_and_system_class_vocabularies_allow_locked_values() -> None:
    for status in (
        "direct-run",
        "adapter-run",
        "literature-only",
        "approximate",
        "incompatible",
        "unavailable",
    ):
        row = _coverage_row(
            primary_status=status,
            license="MIT" if status in {"direct-run", "adapter-run"} else "",
            data_use_constraints=(
                "offline benchmark only" if status in {"direct-run", "adapter-run"} else ""
            ),
            status_reason=(
                "audited unavailable or incompatible evidence"
                if status in {"incompatible", "unavailable"}
                else ""
            ),
            checked_sources=["paper"],
            missing_items=(
                ["direct artifact URL"] if status in {"incompatible", "unavailable"} else []
            ),
            last_checked_date="2026-05-19",
        )
        assert row.primary_status == status

    for system_class in (
        "off_the_shelf_mllm_api",
        "specialized_solver",
        "benchmark_dataset",
        "hybrid_or_unknown",
    ):
        assert _coverage_row(system_class=system_class).system_class == system_class


def test_coverage_rows_enforce_audit_fields_for_unavailable_and_incompatible() -> None:
    for status in ("unavailable", "incompatible"):
        valid = _coverage_row(
            system_name="Oedipus",
            primary_status=status,
            caveat_tags=["artifact-unavailable", "license-unclear"],
            status_reason="artifact could not be validated before the deadline",
            checked_sources=["paper", "project page"],
            missing_items=["direct artifact URL", "license"],
            last_checked_date="2026-05-19",
            license="",
            data_use_constraints="",
        )
        assert valid.primary_status == status

        with pytest.raises(ValidationError):
            _coverage_row(
                primary_status=status,
                status_reason="",
                checked_sources=[],
                missing_items=[],
                last_checked_date="",
            )


def test_direct_and_adapter_rows_require_license_and_data_use_constraints() -> None:
    for status in ("direct-run", "adapter-run"):
        assert _coverage_row(primary_status=status).primary_status == status
        with pytest.raises(ValidationError):
            _coverage_row(
                primary_status=status,
                license="",
                data_use_constraints="",
            )


def test_paper_rows_require_visible_notes_when_not_directly_comparable() -> None:
    with pytest.raises(ValidationError):
        _paper_row(
            system_name="Oedipus",
            primary_status="literature-only",
            directly_comparable=False,
            comparability_caveat="",
            comparability_note="",
            normalized_success_rate=None,
            caveat_tags=["metric-mismatch", "artifact-unavailable"],
        )

    row = _paper_row(
        system_name="Oedipus",
        primary_status="literature-only",
        directly_comparable=False,
        comparability_caveat="literature-only metric uses a different benchmark",
        normalized_success_rate=None,
        caveat_tags=["metric-mismatch", "artifact-unavailable"],
    )
    assert row.directly_comparable is False


def test_literature_only_rows_preserve_reported_metrics_without_normalization() -> None:
    comparison = _comparison_row(
        system_name="Oedipus",
        primary_status="literature-only",
        caveat_tags=["metric-mismatch", "dataset-mismatch", "artifact-unavailable"],
        reported_metric_name="average_success_rate",
        reported_metric_value=0.635,
        reported_metric_unit="rate",
        normalized_success_rate=None,
        metric_definition_status="warning",
        sample_count_status="warning",
        comparability_status="warning",
        directly_comparable=False,
        comparability_caveat="reported on Oedipus reasoning CAPTCHA tasks",
        comparison_basis="literature-only approximate context",
    )

    assert comparison.reported_metric_name == "average_success_rate"
    assert comparison.reported_metric_value == 0.635
    assert comparison.normalized_success_rate is None


def test_writers_create_parent_dirs_and_emit_schema_payloads(tmp_path) -> None:
    coverage_path = tmp_path / "nested" / "coverage.csv"
    coverage_json = tmp_path / "nested" / "coverage.json"
    import_path = tmp_path / "nested" / "import.csv"
    import_json = tmp_path / "nested" / "import.json"
    comparison_path = tmp_path / "nested" / "comparison.csv"
    comparison_json = tmp_path / "nested" / "comparison.json"
    paper_path = tmp_path / "nested" / "paper.csv"
    paper_json = tmp_path / "nested" / "paper.json"

    write_baseline_coverage(coverage_path, coverage_json, [_coverage_row()])
    write_external_import_validation(
        import_path,
        import_json,
        [_import_validation_row()],
    )
    write_baseline_comparison(comparison_path, comparison_json, [_comparison_row()])
    write_paper_baseline_table(paper_path, paper_json, [_paper_row()])

    with coverage_path.open("r", encoding="utf-8", newline="") as handle:
        coverage_rows = list(csv.DictReader(handle))
    with coverage_json.open("r", encoding="utf-8") as handle:
        coverage_payload = json.load(handle)
    with import_json.open("r", encoding="utf-8") as handle:
        import_payload = json.load(handle)
    with comparison_json.open("r", encoding="utf-8") as handle:
        comparison_payload = json.load(handle)
    with paper_json.open("r", encoding="utf-8") as handle:
        paper_payload = json.load(handle)

    assert coverage_rows[0]["schema_version"] == BASELINE_COVERAGE_SCHEMA_VERSION
    assert json.loads(coverage_rows[0]["caveat_tags"]) == ["dataset-mismatch"]
    assert json.loads(coverage_rows[0]["captcha_families"]) == [
        "visual reasoning",
        "interaction",
    ]
    assert coverage_payload["schema_version"] == BASELINE_COVERAGE_SCHEMA_VERSION
    assert import_payload["schema_version"] == EXTERNAL_IMPORT_VALIDATION_SCHEMA_VERSION
    assert comparison_payload["schema_version"] == BASELINE_COMPARISON_SCHEMA_VERSION
    assert paper_payload["schema_version"] == PAPER_BASELINE_TABLE_SCHEMA_VERSION
    assert coverage_payload["rows"][0]["system_name"] == "Halligan"
