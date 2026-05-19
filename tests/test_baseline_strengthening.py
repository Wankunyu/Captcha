import csv
import json
from pathlib import Path

import pytest

from baseline_strengthening import (
    build_baseline_comparison_rows,
    build_external_import_validation_rows,
    build_paper_baseline_rows,
    load_baseline_coverage_sources,
    load_external_import_rows,
    main,
    render_baseline_notes,
    validate_coverage_rows,
)
from phase4_artifacts import (
    BASELINE_COMPARISON_SCHEMA_VERSION,
    BASELINE_COVERAGE_SCHEMA_VERSION,
    EXTERNAL_IMPORT_VALIDATION_SCHEMA_VERSION,
    PAPER_BASELINE_TABLE_SCHEMA_VERSION,
)


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


def _coverage_row(
    *,
    system_name: str,
    external_task_label: str,
    primary_status: str,
    selection_reason: str = "",
    caveat_tags: list[str] | None = None,
    system_class: str = "specialized_solver",
    mapped_local_task_type: str = "Dice_Count",
    mapped_local_family: str = "Counting",
    source_year: int = 2025,
    reported_metric_value: float | None = 0.61,
) -> dict[str, object]:
    runnable = primary_status in {"direct-run", "adapter-run"}
    audit_required = primary_status in {"unavailable", "incompatible"}
    return {
        "run_id": "fixture-run",
        "system_name": system_name,
        "system_class": system_class,
        "evidence_source_type": "validated-import",
        "source_url": f"https://example.test/{system_name.lower()}",
        "source_year": source_year,
        "solver_architecture": "offline literature or artifact baseline",
        "threat_model": "offline benchmark solving",
        "dataset_scale": "reported by source paper",
        "captcha_families": ["visual reasoning", "interaction"],
        "external_task_label": external_task_label,
        "mapped_local_task_type": mapped_local_task_type,
        "mapped_local_family": mapped_local_family,
        "mapping_confidence": "mechanism-level",
        "new_or_supplemental_category_reason": "semantic/mechanism mapping",
        "reported_metric_name": "success_rate",
        "reported_metric_value": reported_metric_value,
        "reported_metric_unit": "rate",
        "artifact_availability": "public artifact" if runnable else "literature only",
        "license": "MIT" if runnable else "",
        "data_use_constraints": "offline benchmark only" if runnable else "",
        "latency_coverage": "reported",
        "cost_coverage": "reported",
        "failure_mode_analysis": "reported",
        "defense_methodology_relevance": "baseline comparison",
        "primary_status": primary_status,
        "caveat_tags": caveat_tags or [],
        "status_reason": "artifact unavailable or incompatible" if audit_required else "",
        "checked_sources": ["paper", "artifact record"],
        "missing_items": ["validated local runner"] if audit_required else [],
        "last_checked_date": "2026-05-19",
        "selection_reason": selection_reason,
    }


def _coverage_rows() -> list[dict[str, object]]:
    return [
        _coverage_row(
            system_name="Halligan",
            external_task_label="arkose/dice_match",
            primary_status="adapter-run",
        ),
        _coverage_row(
            system_name="Halligan",
            external_task_label="OpenCaptchaWorld/Hold_Button",
            primary_status="adapter-run",
            mapped_local_task_type="Hold_Button(Not Used)",
            mapped_local_family="Interaction",
        ),
        _coverage_row(
            system_name="Oedipus",
            external_task_label="Oedipus/reasoning_captcha",
            primary_status="literature-only",
            caveat_tags=["artifact-unavailable", "license-unclear", "metric-mismatch"],
            reported_metric_value=0.635,
        ),
        _coverage_row(
            system_name="VTTSolver",
            external_task_label="VTTSolver/visual_reasoning",
            primary_status="literature-only",
            selection_reason="Halligan comparison baseline for specialized solvers",
            caveat_tags=["dataset-mismatch"],
        ),
        _coverage_row(
            system_name="PhishDecloaker",
            external_task_label="PhishDecloaker/visual_captcha",
            primary_status="literature-only",
            selection_reason="Halligan comparison baseline for visual CAPTCHA solvers",
            caveat_tags=["threat-model-mismatch"],
        ),
    ]


def _import_rows() -> list[dict[str, object]]:
    return [
        {
            "system_name": "Halligan",
            "source_key": "Halligan::arkose/dice_match",
            "external_task_label": "arkose/dice_match",
            "mapped_local_task_type": "Dice_Count",
            "sample_count": 100,
            "reported_metric_name": "success_rate",
            "reported_metric_value": 0.61,
            "reported_metric_unit": "rate",
            "metric_definition": "success_count/sample_count",
            "artifact_license": "MIT",
            "data_use_constraints": "offline benchmark only",
            "comparability_assumptions": "static mapped task with binary success metric",
        },
        {
            "system_name": "Halligan",
            "source_key": "Halligan::OpenCaptchaWorld/Hold_Button",
            "external_task_label": "OpenCaptchaWorld/Hold_Button",
            "mapped_local_task_type": "Hold_Button(Not Used)",
            "sample_count": 100,
            "reported_metric_name": "success_rate",
            "reported_metric_value": 0.58,
            "reported_metric_unit": "rate",
            "metric_definition": "success_count/sample_count",
            "artifact_license": "MIT",
            "data_use_constraints": "offline benchmark only",
            "comparability_assumptions": "mechanism-different smoke import row",
        },
    ]


def test_coverage_writes_default_revision_outputs_and_secret_safe_summary(
    tmp_path, capsys
) -> None:
    metadata_path = tmp_path / "phase4_baseline_sources.json"
    _write_json(metadata_path, {"rows": _coverage_rows()})

    exit_code = main(
        [
            "coverage",
            "--source-metadata",
            str(metadata_path),
            "--output-root",
            str(tmp_path / "results" / "revision"),
            "--run-id",
            "coverage-test",
        ]
    )

    summary = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert summary["row_count"] == 5
    assert summary["output_csv"].endswith("coverage-test/coverage_matrix.csv")
    assert summary["output_json"].endswith("coverage-test/coverage_matrix.json")
    assert "secret" not in json.dumps(summary).lower()

    payload = json.loads(Path(summary["output_json"]).read_text(encoding="utf-8"))
    assert payload["schema_version"] == BASELINE_COVERAGE_SCHEMA_VERSION
    assert {"Halligan", "Oedipus"} <= {row["system_name"] for row in payload["rows"]}


def test_coverage_requires_halligan_and_oedipus(tmp_path) -> None:
    metadata_path = tmp_path / "missing-oedipus.json"
    _write_json(
        metadata_path,
        {"rows": [row for row in _coverage_rows() if row["system_name"] != "Oedipus"]},
    )

    with pytest.raises(ValueError, match="Halligan and Oedipus"):
        load_baseline_coverage_sources(metadata_path, run_id="coverage-test")


def test_coverage_rejects_too_many_secondary_systems() -> None:
    rows = [
        *_coverage_rows(),
        _coverage_row(
            system_name="ExtraSolver",
            external_task_label="ExtraSolver/task",
            primary_status="literature-only",
            selection_reason="interesting but not tied to named baselines",
        ),
    ]

    with pytest.raises(ValueError, match="at most two additional systems"):
        validate_coverage_rows(rows, run_id="coverage-test")


def test_coverage_rejects_missing_audit_and_license_fields() -> None:
    unavailable = _coverage_row(
        system_name="Oedipus",
        external_task_label="Oedipus/reasoning_captcha",
        primary_status="unavailable",
    )
    unavailable["status_reason"] = ""
    unavailable["checked_sources"] = []
    unavailable["missing_items"] = []
    unavailable["last_checked_date"] = ""

    with pytest.raises(ValueError):
        validate_coverage_rows(
            [
                _coverage_rows()[0],
                unavailable,
                *_coverage_rows()[3:],
            ],
            run_id="coverage-test",
        )

    direct = _coverage_row(
        system_name="Halligan",
        external_task_label="arkose/dice_match",
        primary_status="direct-run",
    )
    direct["license"] = ""
    direct["data_use_constraints"] = ""
    with pytest.raises(ValueError):
        validate_coverage_rows([direct, *_coverage_rows()[1:]], run_id="coverage-test")


def test_validate_import_accepts_halligan_smoke_rows(tmp_path, capsys) -> None:
    metadata_path = tmp_path / "phase4_baseline_sources.json"
    import_path = tmp_path / "halligan_import_rows.csv"
    _write_json(metadata_path, {"rows": _coverage_rows()})
    _write_csv(import_path, _import_rows())

    coverage_rows = load_baseline_coverage_sources(metadata_path, run_id="import-test")
    import_rows = load_external_import_rows(import_path)
    diagnostics = build_external_import_validation_rows(
        coverage_rows,
        import_rows,
        run_id="import-test",
    )

    assert {row.external_task_label for row in diagnostics} == {
        "arkose/dice_match",
        "OpenCaptchaWorld/Hold_Button",
    }
    assert all(row.validation_status == "pass" for row in diagnostics)

    coverage_json = tmp_path / "results" / "revision" / "import-test" / "coverage_matrix.json"
    _write_json(
        coverage_json,
        {
            "schema_version": BASELINE_COVERAGE_SCHEMA_VERSION,
            "rows": [row.model_dump(mode="json") for row in coverage_rows],
        },
    )
    exit_code = main(
        [
            "validate-import",
            "--coverage-json",
            str(coverage_json),
            "--import-rows",
            str(import_path),
            "--output-root",
            str(tmp_path / "results" / "revision"),
            "--run-id",
            "import-test",
        ]
    )

    summary = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert summary["row_count"] == 2
    assert summary["output_csv"].endswith("import-test/import_diagnostics.csv")
    assert summary["output_json"].endswith("import-test/import_diagnostics.json")
    assert "secret" not in json.dumps(summary).lower()
    payload = json.loads(Path(summary["output_json"]).read_text(encoding="utf-8"))
    assert payload["schema_version"] == EXTERNAL_IMPORT_VALIDATION_SCHEMA_VERSION


def test_secondary_smoke_replacement_requires_user_confirmation(tmp_path) -> None:
    metadata_path = tmp_path / "phase4_baseline_sources.json"
    _write_json(metadata_path, {"rows": _coverage_rows()})
    coverage_rows = load_baseline_coverage_sources(metadata_path, run_id="replacement-test")
    secondary_row = {
        **_import_rows()[0],
        "system_name": "VTTSolver",
        "source_key": "VTTSolver::visual_reasoning",
        "external_task_label": "VTTSolver/visual_reasoning",
        "user_confirmed_replacement": False,
    }

    with pytest.raises(ValueError, match="user confirmation"):
        build_external_import_validation_rows(
            coverage_rows,
            [secondary_row],
            run_id="replacement-test",
        )

    confirmed = build_external_import_validation_rows(
        coverage_rows,
        [{**secondary_row, "user_confirmed_replacement": True}],
        run_id="replacement-test",
    )
    assert confirmed[0].user_confirmed_replacement is True


def test_build_table_preserves_non_comparable_literature_rows(tmp_path) -> None:
    metadata_path = tmp_path / "phase4_baseline_sources.json"
    _write_json(metadata_path, {"rows": _coverage_rows()})
    coverage_rows = load_baseline_coverage_sources(metadata_path, run_id="table-test")
    import_rows = build_external_import_validation_rows(
        coverage_rows,
        _import_rows(),
        run_id="table-test",
    )

    comparison_rows = build_baseline_comparison_rows(
        coverage_rows,
        import_rows,
        run_id="table-test",
    )
    paper_rows = build_paper_baseline_rows(comparison_rows, run_id="table-test")

    oedipus_comparison = next(row for row in comparison_rows if row.system_name == "Oedipus")
    oedipus_paper = next(row for row in paper_rows if row.system_name == "Oedipus")

    assert oedipus_comparison.primary_status == "literature-only"
    assert oedipus_comparison.reported_metric_name == "success_rate"
    assert oedipus_comparison.reported_metric_value == 0.635
    assert oedipus_comparison.reported_metric_unit == "rate"
    assert oedipus_comparison.normalized_success_rate is None
    assert oedipus_comparison.directly_comparable is False
    assert "literature-only" in oedipus_comparison.comparability_caveat
    assert oedipus_paper.directly_comparable is False
    assert oedipus_paper.comparability_note


def test_build_table_normalizes_only_validated_metrics(tmp_path) -> None:
    metadata_path = tmp_path / "phase4_baseline_sources.json"
    _write_json(metadata_path, {"rows": _coverage_rows()})
    coverage_rows = load_baseline_coverage_sources(metadata_path, run_id="normalize-test")
    import_fixture = _import_rows()
    import_fixture[1]["sample_count"] = 0
    import_rows = build_external_import_validation_rows(
        coverage_rows,
        import_fixture,
        run_id="normalize-test",
    )

    comparison_rows = build_baseline_comparison_rows(
        coverage_rows,
        import_rows,
        run_id="normalize-test",
    )
    by_key = {row.source_key: row for row in comparison_rows}

    assert by_key["Halligan::arkose/dice_match"].normalized_success_rate == 0.61
    assert (
        by_key["Halligan::OpenCaptchaWorld/Hold_Button"].normalized_success_rate
        is None
    )
    assert by_key["Halligan::OpenCaptchaWorld/Hold_Button"].directly_comparable is False
    assert "metric-mismatch" in by_key["Oedipus::Oedipus/reasoning_captcha"].caveat_tags
    assert by_key["Oedipus::Oedipus/reasoning_captcha"].normalized_success_rate is None


def test_notes_summarize_status_and_comparability_counts(tmp_path) -> None:
    metadata_path = tmp_path / "phase4_baseline_sources.json"
    _write_json(metadata_path, {"rows": _coverage_rows()})
    coverage_rows = load_baseline_coverage_sources(metadata_path, run_id="notes-test")
    import_rows = build_external_import_validation_rows(
        coverage_rows,
        _import_rows(),
        run_id="notes-test",
    )
    comparison_rows = build_baseline_comparison_rows(
        coverage_rows,
        import_rows,
        run_id="notes-test",
    )
    paper_rows = build_paper_baseline_rows(comparison_rows, run_id="notes-test")

    notes = render_baseline_notes(paper_rows, import_rows)

    for heading in (
        "## Status Counts",
        "## Unavailable And Incompatible Evidence",
        "## Non-Comparable Rows",
        "## Approximate Comparison Basis",
    ):
        assert heading in notes
    assert "literature-only" in notes
    assert "Oedipus" in notes
    assert "Non-comparable rows:" in notes
    assert "Approximate comparisons preserve reported metrics" in notes
    assert "secret" not in notes.lower()


def test_full_phase4_cli_chain_with_halligan_smoke_fixture(tmp_path, capsys) -> None:
    metadata_path = tmp_path / "phase4_baseline_sources.json"
    import_path = tmp_path / "halligan_import_rows.csv"
    output_root = tmp_path / "results" / "revision"
    _write_json(metadata_path, {"rows": _coverage_rows()})
    _write_csv(import_path, _import_rows())

    assert main(
        [
            "coverage",
            "--source-metadata",
            str(metadata_path),
            "--output-root",
            str(output_root),
            "--run-id",
            "chain-test",
        ]
    ) == 0
    coverage_summary = json.loads(capsys.readouterr().out)
    assert "secret" not in json.dumps(coverage_summary).lower()

    assert main(
        [
            "validate-import",
            "--coverage-json",
            coverage_summary["output_json"],
            "--import-rows",
            str(import_path),
            "--output-root",
            str(output_root),
            "--run-id",
            "chain-test",
        ]
    ) == 0
    import_summary = json.loads(capsys.readouterr().out)
    assert "secret" not in json.dumps(import_summary).lower()

    assert main(
        [
            "build-table",
            "--coverage-json",
            coverage_summary["output_json"],
            "--import-validation-json",
            import_summary["output_json"],
            "--output-root",
            str(output_root),
            "--run-id",
            "chain-test",
        ]
    ) == 0
    table_summary = json.loads(capsys.readouterr().out)
    assert table_summary["comparison_json"].endswith(
        "chain-test/baseline_comparison.json"
    )
    assert table_summary["paper_table_json"].endswith(
        "chain-test/paper_baseline_table.json"
    )
    assert Path(table_summary["comparison_csv"]).exists()
    assert Path(table_summary["paper_table_csv"]).exists()
    assert "secret" not in json.dumps(table_summary).lower()

    paper_payload = json.loads(
        Path(table_summary["paper_table_json"]).read_text(encoding="utf-8")
    )
    assert paper_payload["schema_version"] == PAPER_BASELINE_TABLE_SCHEMA_VERSION
    first_paper_row = paper_payload["rows"][0]
    for field in (
        "system_class",
        "primary_status",
        "directly_comparable",
        "comparability_note",
        "reported_metric_display",
        "normalized_success_rate",
    ):
        assert field in first_paper_row

    comparison_payload = json.loads(
        Path(table_summary["comparison_json"]).read_text(encoding="utf-8")
    )
    assert comparison_payload["schema_version"] == BASELINE_COMPARISON_SCHEMA_VERSION
    assert comparison_payload["rows"][0]["reported_metric_name"]
    assert "reported_metric_value" in comparison_payload["rows"][0]
    assert comparison_payload["rows"][0]["reported_metric_unit"]

    assert main(
        [
            "notes",
            "--paper-table-json",
            table_summary["paper_table_json"],
            "--import-validation-json",
            import_summary["output_json"],
            "--output-root",
            str(output_root),
            "--run-id",
            "chain-test",
        ]
    ) == 0
    notes_summary = json.loads(capsys.readouterr().out)
    assert notes_summary["output_md"].endswith("chain-test/baseline_notes.md")
    notes = Path(notes_summary["output_md"]).read_text(encoding="utf-8")
    assert "## Non-Comparable Rows" in notes
    assert "secret" not in notes.lower()


def test_build_table_rejects_stale_coverage_artifact_missing_named_system(
    tmp_path,
) -> None:
    coverage_json = tmp_path / "coverage_matrix.json"
    import_json = tmp_path / "import_diagnostics.json"
    rows = [
        row
        for row in validate_coverage_rows(_coverage_rows(), run_id="stale-test")
        if row.system_name != "Oedipus"
    ]
    _write_json(
        coverage_json,
        {
            "schema_version": BASELINE_COVERAGE_SCHEMA_VERSION,
            "rows": [row.model_dump(mode="json") for row in rows],
        },
    )
    _write_json(
        import_json,
        {
            "schema_version": EXTERNAL_IMPORT_VALIDATION_SCHEMA_VERSION,
            "rows": [],
        },
    )

    with pytest.raises(SystemExit):
        main(
            [
                "build-table",
                "--coverage-json",
                str(coverage_json),
                "--import-validation-json",
                str(import_json),
                "--output-root",
                str(tmp_path / "results" / "revision"),
                "--run-id",
                "stale-test",
            ]
        )


def test_build_table_rejects_duplicate_import_source_keys(tmp_path) -> None:
    metadata_path = tmp_path / "phase4_baseline_sources.json"
    _write_json(metadata_path, {"rows": _coverage_rows()})
    coverage_rows = load_baseline_coverage_sources(metadata_path, run_id="dupe-test")
    import_fixture = [*_import_rows(), _import_rows()[0]]
    import_rows = build_external_import_validation_rows(
        coverage_rows,
        import_fixture,
        run_id="dupe-test",
    )

    with pytest.raises(ValueError, match="duplicate import validation source_key"):
        build_baseline_comparison_rows(coverage_rows, import_rows, run_id="dupe-test")
