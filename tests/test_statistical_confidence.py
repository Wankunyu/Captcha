import csv
import json
from pathlib import Path

import pytest

from phase3_artifacts import PASS_RATE_CONFIDENCE_SCHEMA_VERSION
from statistical_confidence import (
    build_pass_rate_confidence_rows,
    load_experiment_pass_rates,
    main,
    wilson_interval,
    write_pass_rate_outputs,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


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
