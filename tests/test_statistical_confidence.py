import csv
import json
from pathlib import Path

import pytest
import pandas as pd

from cognition.phase3_artifacts import (
    PASS_RATE_CONFIDENCE_SCHEMA_VERSION,
    THRESHOLD_SENSITIVITY_SCHEMA_VERSION,
)
from cognition.statistical_confidence import (
    CUTOFF_NOTE,
    build_pass_rate_confidence_rows,
    build_threshold_sensitivity_rows,
    classify_threshold_label,
    load_adaptive_trend_rates,
    load_experiment_pass_rates,
    load_extended_validation_trend_rates,
    main,
    wilson_interval,
    write_pass_rate_outputs,
    write_threshold_outputs,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_wilson_interval_known_case_and_empty_sample() -> None:
    low, high = wilson_interval(3, 10)

    assert low == pytest.approx(0.1078, abs=1e-4)
    assert high == pytest.approx(0.6032, abs=1e-4)
    assert wilson_interval(0, 0) == (None, None)


def test_load_experiment_pass_rates_filters_exp2_and_error_analysis(
    tmp_path: Path,
) -> None:
    results_dir = tmp_path / "results"
    _write_csv(
        results_dir / "exp2" / "openai" / "gpt-5" / "results.csv",
        [
            {
                "provider": "openai",
                "model": "gpt-5",
                "type": "Dice_Count",
                "n": 4,
                "pass_at_1": 0.25,
            },
            {
                "provider": "openai",
                "model": "gpt-5",
                "type": "Place_Dot",
                "n": 40,
                "pass_at_1": 0.45,
            },
        ],
    )
    _write_csv(
        results_dir / "error_analysis" / "openai" / "gpt-5" / "results.csv",
        [
            {
                "provider": "openai",
                "model": "gpt-5",
                "type": "Dice_Count",
                "n": 99,
                "pass_at_1": 1.0,
            }
        ],
    )
    _write_csv(
        results_dir / "exp5" / "openai" / "gpt-5" / "results.csv",
        [
            {
                "provider": "openai",
                "model": "gpt-5",
                "type": "Dice_Count",
                "n": 99,
                "pass_at_1": 1.0,
            }
        ],
    )

    loaded = load_experiment_pass_rates(results_dir)

    assert set(loaded["experiment"]) == {"exp2"}
    assert set(loaded["task_type"]) == {"Dice_Count", "Place_Dot"}
    dice = loaded[loaded["task_type"] == "Dice_Count"].iloc[0]
    assert dice["n_attempts"] == 4
    assert dice["n_success"] == 1
    assert dice["pass_rate"] == pytest.approx(0.25)
    assert dice["provider_model"] == "openai/gpt-5"
    assert dice["task_family"] == "Click/Coordinate"
    assert "error_analysis" not in ";".join(loaded["source_path"].astype(str))


def test_load_experiment_pass_rates_normalizes_exp3_summary_rows(
    tmp_path: Path,
) -> None:
    results_dir = tmp_path / "results"
    _write_csv(
        results_dir / "exp3" / "openai" / "gpt-5" / "results.csv",
        [
            {
                "kind": "summary",
                "provider": "openai",
                "model": "gpt-5",
                "type": "Dice_Count",
                "puzzle_id": "one",
                "attempt_idx": 1,
                "cumulative_ms": 100.0,
                "pass1": 1,
            },
            {
                "kind": "summary",
                "provider": "openai",
                "model": "gpt-5",
                "type": "Dice_Count",
                "puzzle_id": "two",
                "attempt_idx": 2,
                "cumulative_ms": 200.0,
                "pass1": 0,
            },
            {
                "kind": "attempt",
                "provider": "openai",
                "model": "gpt-5",
                "type": "Dice_Count",
                "puzzle_id": "ignored",
                "attempt_idx": 3,
                "cumulative_ms": 300.0,
                "pass1": 1,
            },
        ],
    )

    loaded = load_experiment_pass_rates(results_dir)

    assert len(loaded) == 1
    row = loaded.iloc[0]
    assert row["experiment"] == "exp3"
    assert row["task_type"] == "Dice_Count"
    assert row["n_attempts"] == 2
    assert row["n_success"] == 1
    assert row["pass_rate"] == pytest.approx(0.5)


def test_build_pass_rate_confidence_rows_adds_task_and_family_rows(
    tmp_path: Path,
) -> None:
    results_dir = tmp_path / "results"
    _write_csv(
        results_dir / "exp2" / "openai" / "gpt-5" / "results.csv",
        [
            {
                "provider": "openai",
                "model": "gpt-5",
                "type": "Dice_Count",
                "n": 4,
                "pass_at_1": 0.25,
            },
            {
                "provider": "openai",
                "model": "gpt-5",
                "type": "Place_Dot",
                "n": 40,
                "pass_at_1": 0.45,
            },
        ],
    )
    df = load_experiment_pass_rates(results_dir)

    rows = build_pass_rate_confidence_rows(
        df,
        run_id="run-1",
        underpowered_n=20,
    )

    by_key = {(row.aggregation_level, row.task_type): row for row in rows}
    dice = by_key[("task_type", "Dice_Count")]
    family = by_key[("task_family", "__family__")]

    assert dice.ci_method == "wilson"
    assert dice.ci_confidence == pytest.approx(0.95)
    assert dice.underpowered is True
    assert dice.underpowered_threshold == 20
    assert dice.source_path.endswith("results.csv")
    assert family.task_family == "Click/Coordinate"
    assert family.n_attempts == 44
    assert family.n_success == 19
    assert family.pass_rate == pytest.approx(19 / 44)
    assert family.underpowered is False


def test_write_pass_rate_outputs_emit_csv_and_json(tmp_path: Path) -> None:
    rows = build_pass_rate_confidence_rows(
        load_experiment_pass_rates(tmp_path / "missing-results"),
        run_id="run-1",
    )
    assert rows == []

    csv_path, json_path = write_pass_rate_outputs(
        [
            build_pass_rate_confidence_rows(
                load_experiment_pass_rates(_fixture_results(tmp_path)),
                run_id="run-1",
            )[0]
        ],
        tmp_path / "nested" / "pass_rate_confidence.csv",
        tmp_path / "nested" / "pass_rate_confidence.json",
    )

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert csv_rows[0]["schema_version"] == PASS_RATE_CONFIDENCE_SCHEMA_VERSION
    assert payload["schema_version"] == PASS_RATE_CONFIDENCE_SCHEMA_VERSION
    assert payload["rows"][0]["aggregation_level"] == "task_type"


def test_cli_uses_revision_run_dir_defaults_and_rejects_bad_run_ids(
    tmp_path: Path,
) -> None:
    results_dir = _fixture_results(tmp_path)
    output_root = tmp_path / "revision"

    exit_code = main(
        [
            "--results-dir",
            str(results_dir),
            "--output-root",
            str(output_root),
            "--run-id",
            "phase3-run",
        ]
    )

    assert exit_code == 0
    assert (output_root / "phase3-run" / "pass_rate_confidence.csv").exists()
    assert (output_root / "phase3-run" / "pass_rate_confidence.json").exists()

    for bad_run_id in ("../phase3", "bad/run"):
        bad_root = tmp_path / f"bad-{bad_run_id.replace('/', '-')}"
        with pytest.raises(SystemExit) as exc_info:
            main(
                [
                    "--results-dir",
                    str(results_dir),
                    "--output-root",
                    str(bad_root),
                    "--run-id",
                    bad_run_id,
                ]
            )
        assert exc_info.value.code != 0
        assert not any(bad_root.glob("**/*"))


def _fixture_results(tmp_path: Path) -> Path:
    results_dir = tmp_path / "fixture-results"
    _write_csv(
        results_dir / "exp2" / "openai" / "gpt-5" / "results.csv",
        [
            {
                "provider": "openai",
                "model": "gpt-5",
                "type": "Dice_Count",
                "n": 4,
                "pass_at_1": 0.25,
            }
        ],
    )
    return results_dir


def test_threshold_label_rules_and_cutoff_note_text() -> None:
    assert classify_threshold_label(None) is None
    assert classify_threshold_label(0.29) == "hard"
    assert classify_threshold_label(0.30) == "borderline/near-broken"
    assert classify_threshold_label(0.40) == "borderline/near-broken"
    assert classify_threshold_label(0.50) == "borderline/near-broken"
    assert classify_threshold_label(0.51) == "broken"
    assert classify_threshold_label(0.20, ci_crosses_cutoff=True) == "borderline/near-broken"
    assert classify_threshold_label(0.20, trend_sensitive=True) == "borderline/near-broken"
    assert (
        CUTOFF_NOTE
        == "40% working CAPTCHA threshold; operational reporting heuristic, not a universal "
        "CAPTCHA security boundary. 30%-50% is a revision-time caution band, not a new "
        "security tier."
    )
    disallowed_margin_text = "+" + "/- 5%"
    assert disallowed_margin_text not in Path("cognition/statistical_confidence.py").read_text(
        encoding="utf-8"
    )


def test_build_threshold_rows_prefers_exp2_and_flags_exp3_trend(
    tmp_path: Path,
) -> None:
    results_dir = tmp_path / "results"
    _write_csv(
        results_dir / "exp2" / "openai" / "gpt-5" / "results.csv",
        [
            {
                "provider": "openai",
                "model": "gpt-5",
                "type": "Dice_Count",
                "n": 100,
                "pass_at_1": 0.20,
            }
        ],
    )
    _write_csv(
        results_dir / "exp3" / "openai" / "gpt-5" / "results.csv",
        [
            {
                "kind": "summary",
                "provider": "openai",
                "model": "gpt-5",
                "type": "Dice_Count",
                "puzzle_id": f"puzzle-{idx}",
                "attempt_idx": 1,
                "cumulative_ms": 100.0,
                "pass1": 1 if idx < 4 else 0,
            }
            for idx in range(10)
        ],
    )
    confidence_rows = build_pass_rate_confidence_rows(
        load_experiment_pass_rates(results_dir),
        run_id="run-1",
    )

    rows = build_threshold_sensitivity_rows(confidence_rows, run_id="run-1")

    assert len(rows) == 1
    row = rows[0]
    assert row.primary_experiment == "exp2"
    assert row.primary_rate == pytest.approx(0.20)
    assert row.max_observed_rate == pytest.approx(0.40)
    assert row.margin_to_cutoff == pytest.approx(-0.20)
    assert row.in_30_50_review_band is False
    assert row.trend_sensitive is True
    assert row.trend_sources == "exp3"
    assert row.label == "borderline/near-broken"
    assert row.cutoff_note == CUTOFF_NOTE


def test_adaptive_and_extended_trend_sources_are_exact(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    _write_csv(
        results_dir / "exp2" / "openai" / "gpt-5" / "results.csv",
        [
            {
                "provider": "openai",
                "model": "gpt-5",
                "type": "Patch_Select",
                "n": 100,
                "pass_at_1": 0.20,
            }
        ],
    )
    adaptive_summary = tmp_path / "adaptive_summary.csv"
    _write_csv(
        adaptive_summary,
        [
            {
                "provider": "openai",
                "model": "gpt-5",
                "task_type": "Patch_Select",
                "attempt_budget_k": 3,
                "success_rate": 0.35,
            }
        ],
    )
    adaptive_comparison = tmp_path / "adaptive_comparison.json"
    _write_json(
        adaptive_comparison,
        {
            "schema_version": "cognition.revision.adaptive_comparison.v1",
            "rows": [
                {
                    "provider": "openai",
                    "model": "gpt-5",
                    "provider_model": "openai/gpt-5",
                    "task_type": "Patch_Select",
                    "adaptive_success_at_k": 0.45,
                }
            ],
        },
    )
    extended_comparison = tmp_path / "extended_validation_comparison.csv"
    _write_csv(
        extended_comparison,
        [
            {
                "run_id": "extended-run",
                "source_id": "patch-slice",
                "evidence_origin": "supplemented_category",
                "slice_type": "supplement_existing",
                "task_type": "Patch_Select",
                "task_family": "Grid Selection",
                "original_conclusion_label": "hard",
                "original_rate": 0.2,
                "validation_slice_rate": 0.55,
                "validation_sample_count": 20,
                "agreement_status": "diverges_from_original",
                "divergence_reason": "higher validation-slice rate",
                "comparison_caveat": "selective validation slice",
                "outcome_source_path": "slice.csv",
                "provider": "openai",
                "model": "gpt-5",
            }
        ],
    )
    confidence_rows = build_pass_rate_confidence_rows(
        load_experiment_pass_rates(results_dir),
        run_id="run-1",
    )

    rows = build_threshold_sensitivity_rows(
        confidence_rows,
        run_id="run-1",
        adaptive_trend_rates=load_adaptive_trend_rates(
            adaptive_summary,
            adaptive_comparison,
        ),
        extended_validation_trend_rates=load_extended_validation_trend_rates(
            extended_comparison
        ),
    )

    row = rows[0]
    assert row.max_observed_rate == pytest.approx(0.55)
    assert row.trend_sensitive is True
    assert (
        row.trend_sources
        == "adaptive_summary;adaptive_comparison;extended_validation_slice"
    )
    assert row.label == "borderline/near-broken"


def test_adaptive_and_extended_loaders_accept_rates_and_labels(tmp_path: Path) -> None:
    adaptive_summary = tmp_path / "adaptive_summary.json"
    _write_json(
        adaptive_summary,
        {
            "rows": [
                {
                    "provider": "openai",
                    "model": "gpt-5",
                    "task_type": "Dice_Count",
                    "success_rate": 0.42,
                }
            ]
        },
    )
    adaptive_comparison = tmp_path / "adaptive_comparison.csv"
    _write_csv(
        adaptive_comparison,
        [
            {
                "provider": "openai",
                "model": "gpt-5",
                "task_type": "Image_Matching",
                "adaptive_success_at_k": "",
                "adaptive_label": "broken",
            },
            {
                "provider": "openai",
                "model": "gpt-5",
                "task_type": "Patch_Select",
                "adaptive_success_at_k": "",
                "adaptive_label": "hard",
            },
            {
                "provider": "openai",
                "model": "gpt-5",
                "task_type": "Click_Order",
                "adaptive_success_at_k": "",
                "adaptive_label": "borderline",
            },
        ],
    )
    extended_comparison = tmp_path / "extended_validation_comparison.json"
    _write_json(
        extended_comparison,
        {
            "rows": [
                {
                    "provider": "openai",
                    "model": "gpt-5",
                    "task_type": "Object_Match",
                    "validation_slice_rate": 0.31,
                }
            ]
        },
    )

    adaptive = load_adaptive_trend_rates(adaptive_summary, adaptive_comparison)
    extended = load_extended_validation_trend_rates(extended_comparison)

    by_task = {row["task_type"]: row for row in adaptive.to_dict(orient="records")}
    assert by_task["Dice_Count"]["pass_rate"] == pytest.approx(0.42)
    assert by_task["Dice_Count"]["source"] == "adaptive_summary"
    assert by_task["Image_Matching"]["pass_rate"] == pytest.approx(1.0)
    assert by_task["Patch_Select"]["pass_rate"] == pytest.approx(0.0)
    assert pd.isna(by_task["Click_Order"]["pass_rate"])
    assert extended.iloc[0]["pass_rate"] == pytest.approx(0.31)
    assert extended.iloc[0]["source"] == "extended_validation_slice"


def test_write_threshold_outputs_and_cli_defaults(tmp_path: Path) -> None:
    results_dir = _fixture_results(tmp_path)
    output_root = tmp_path / "revision"

    exit_code = main(
        [
            "--results-dir",
            str(results_dir),
            "--output-root",
            str(output_root),
            "--run-id",
            "threshold-run",
        ]
    )

    assert exit_code == 0
    threshold_csv = output_root / "threshold-run" / "threshold_sensitivity.csv"
    threshold_json = output_root / "threshold-run" / "threshold_sensitivity.json"
    assert threshold_csv.exists()
    assert threshold_json.exists()

    with threshold_csv.open("r", encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    payload = json.loads(threshold_json.read_text(encoding="utf-8"))

    assert csv_rows[0]["schema_version"] == THRESHOLD_SENSITIVITY_SCHEMA_VERSION
    assert payload["schema_version"] == THRESHOLD_SENSITIVITY_SCHEMA_VERSION
    assert payload["rows"][0]["margin_to_cutoff"] == pytest.approx(-0.15)

    for bad_run_id in ("../phase3", "bad/run"):
        bad_root = tmp_path / f"threshold-bad-{bad_run_id.replace('/', '-')}"
        with pytest.raises(SystemExit) as exc_info:
            main(
                [
                    "--results-dir",
                    str(results_dir),
                    "--output-root",
                    str(bad_root),
                    "--run-id",
                    bad_run_id,
                ]
            )
        assert exc_info.value.code != 0
        assert not any(bad_root.glob("**/*"))


def test_write_threshold_outputs_helper(tmp_path: Path) -> None:
    confidence_rows = build_pass_rate_confidence_rows(
        load_experiment_pass_rates(_fixture_results(tmp_path)),
        run_id="run-1",
    )
    rows = build_threshold_sensitivity_rows(confidence_rows, run_id="run-1")

    csv_path, json_path = write_threshold_outputs(
        rows,
        tmp_path / "nested" / "threshold_sensitivity.csv",
        tmp_path / "nested" / "threshold_sensitivity.json",
    )

    assert csv_path.exists()
    assert json_path.exists()
