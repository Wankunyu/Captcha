import csv
import json
from pathlib import Path

import pytest

from cognition.exp2_to_exp3_predict import predict_A_from_exp2, predict_q_from_exp2
from cognition.retry_calibration import (
    build_retry_calibration_family_rows,
    build_retry_calibration_rows,
    load_adaptive_outcomes,
    load_exp2_baseline,
    load_fixed_retry_observations,
    main,
    write_retry_calibration,
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


def _write_retry_inputs(results_dir: Path, adaptive_summary: Path) -> None:
    _write_csv(
        results_dir / "exp2" / "openai" / "gpt-5" / "results.csv",
        [
            {"type": "Dice_Count", "n": 10, "pass_at_1": 0.20},
            {"type": "Place_Dot", "n": 20, "pass_at_1": 0.50},
            {"type": "Patch_Select", "n": 12, "pass_at_1": 0.10},
        ],
    )
    _write_csv(
        results_dir / "exp4" / "openai" / "gpt-5" / "results.csv",
        [{"type": "Dice_Count", "n": 99, "pass_at_1": 1.0}],
    )
    _write_csv(
        results_dir / "exp3" / "openai" / "gpt-5" / "results.csv",
        [
            {
                "kind": "summary",
                "type": "Dice_Count",
                "puzzle_id": "one",
                "attempt_idx": 1,
                "pass1": 1,
            },
            {
                "kind": "summary",
                "type": "Dice_Count",
                "puzzle_id": "two",
                "attempt_idx": 3,
                "pass1": 0,
            },
            {
                "kind": "summary",
                "type": "Place_Dot",
                "puzzle_id": "filtered-by-k",
                "attempt_idx": 5,
                "pass1": 1,
            },
            {
                "kind": "attempt",
                "type": "Dice_Count",
                "puzzle_id": "ignored-kind",
                "attempt_idx": 1,
                "pass1": 0,
            },
        ],
    )
    _write_csv(
        adaptive_summary,
        [
            {
                "schema_version": "cognition.revision.adaptive_summary.v1",
                "run_id": "adaptive-run",
                "provider": "openai",
                "model": "gpt-5",
                "task_type": "Dice_Count",
                "attempt_budget_k": 3,
                "n_attempts": 6,
                "n_success": 2,
                "success_rate": 0.3333333333,
                "scientific_wrong_count": 3,
                "protocol_failure_count": 1,
                "infrastructure_failure_count": 0,
            },
            {
                "schema_version": "cognition.revision.adaptive_summary.v1",
                "run_id": "adaptive-run",
                "provider": "openai",
                "model": "gpt-5",
                "task_type": "Place_Dot",
                "attempt_budget_k": 4,
                "n_attempts": 4,
                "n_success": 4,
                "success_rate": 1.0,
                "scientific_wrong_count": 0,
                "protocol_failure_count": 0,
                "infrastructure_failure_count": 0,
            },
        ],
    )


def test_loads_exp2_exp3_and_adaptive_inputs_with_same_k_filtering(
    tmp_path: Path,
) -> None:
    results_dir = tmp_path / "results"
    adaptive_summary = tmp_path / "adaptive_summary.csv"
    _write_retry_inputs(results_dir, adaptive_summary)

    exp2 = load_exp2_baseline(results_dir, provider="openai", model="gpt-5")
    fixed = load_fixed_retry_observations(
        results_dir,
        attempt_budget_k=3,
        provider="openai",
        model="gpt-5",
    )
    adaptive = load_adaptive_outcomes(
        adaptive_summary,
        attempt_budget_k=3,
        provider="openai",
        model="gpt-5",
    )

    assert set(exp2["task_type"]) == {"Dice_Count", "Patch_Select", "Place_Dot"}
    assert "exp4" not in ";".join(exp2["source_path"].astype(str))
    assert set(fixed["task_type"]) == {"Dice_Count"}
    assert fixed.iloc[0]["observed_fixed_retry_success"] == pytest.approx(0.5)
    assert set(adaptive["task_type"]) == {"Dice_Count"}
    assert adaptive.iloc[0]["observed_adaptive_compatible_success"] == pytest.approx(
        0.3333333333
    )


def test_build_retry_calibration_rows_preserves_failure_counts_and_nulls(
    tmp_path: Path,
) -> None:
    results_dir = tmp_path / "results"
    adaptive_summary = tmp_path / "adaptive_summary.csv"
    _write_retry_inputs(results_dir, adaptive_summary)

    rows = build_retry_calibration_rows(
        load_exp2_baseline(results_dir),
        load_fixed_retry_observations(results_dir, attempt_budget_k=3),
        load_adaptive_outcomes(adaptive_summary, attempt_budget_k=3),
        run_id="run-1",
        attempt_budget_k=3,
    )

    by_task = {row.task_type: row for row in rows}
    dice = by_task["Dice_Count"]
    patch = by_task["Patch_Select"]
    place_dot = by_task["Place_Dot"]

    assert dice.bernoulli_success_at_k == pytest.approx(
        predict_q_from_exp2(0.20, 10, 3)
    )
    assert predict_A_from_exp2(0.20, 10, 3) > 0
    assert dice.observed_fixed_retry_success == pytest.approx(0.5)
    assert dice.observed_adaptive_compatible_success == pytest.approx(0.3333333333)
    assert dice.signed_error_fixed_retry == pytest.approx(
        0.5 - predict_q_from_exp2(0.20, 10, 3)
    )
    assert dice.absolute_error_fixed_retry == pytest.approx(
        abs(0.5 - predict_q_from_exp2(0.20, 10, 3))
    )
    assert dice.signed_error_adaptive == pytest.approx(
        0.3333333333 - predict_q_from_exp2(0.20, 10, 3)
    )
    assert dice.absolute_error_adaptive == pytest.approx(
        abs(0.3333333333 - predict_q_from_exp2(0.20, 10, 3))
    )
    assert dice.raw_observed_rate == pytest.approx(2 / (2 + 3 + 1 + 0))
    assert dice.scientific_rate == pytest.approx(2 / (2 + 3))
    assert dice.scientific_wrong_count == 3
    assert dice.protocol_failure_count == 1
    assert dice.infrastructure_failure_count == 0
    assert dice.comparison_contract == (
        "task-type-primary; same-attempt-budget; "
        "structural-bottleneck-tags-explanatory"
    )

    assert patch.observed_fixed_retry_success is None
    assert patch.observed_adaptive_compatible_success is None
    assert patch.raw_observed_rate is None
    assert patch.scientific_rate is None

    assert place_dot.observed_fixed_retry_success is None
    assert place_dot.observed_adaptive_compatible_success is None


def test_family_rows_average_predictions_and_sum_counts(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    adaptive_summary = tmp_path / "adaptive_summary.csv"
    _write_retry_inputs(results_dir, adaptive_summary)
    rows = build_retry_calibration_rows(
        load_exp2_baseline(results_dir),
        load_fixed_retry_observations(results_dir, attempt_budget_k=3),
        load_adaptive_outcomes(adaptive_summary, attempt_budget_k=3),
        run_id="run-1",
        attempt_budget_k=3,
    )

    family_rows = build_retry_calibration_family_rows(rows)

    click_family = next(row for row in family_rows if row.task_family == "Click/Coordinate")
    assert click_family.task_type == "__family__"
    assert click_family.sample_count == 30
    assert click_family.scientific_wrong_count == 3
    assert click_family.protocol_failure_count == 1
    assert click_family.infrastructure_failure_count == 0
    assert click_family.raw_observed_rate == pytest.approx(2 / (2 + 3 + 1 + 0))
    assert click_family.scientific_rate == pytest.approx(2 / (2 + 3))
    assert click_family.bernoulli_success_at_k == pytest.approx(
        (
            predict_q_from_exp2(0.20, 10, 3)
            + predict_q_from_exp2(0.50, 20, 3)
        )
        / 2
    )


def test_write_outputs_and_cli_defaults_use_revision_run_dir(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    adaptive_summary = tmp_path / "adaptive_summary.csv"
    _write_retry_inputs(results_dir, adaptive_summary)

    rows = build_retry_calibration_rows(
        load_exp2_baseline(results_dir),
        load_fixed_retry_observations(results_dir, attempt_budget_k=3),
        load_adaptive_outcomes(adaptive_summary, attempt_budget_k=3),
        run_id="run-1",
        attempt_budget_k=3,
    )
    family_rows = build_retry_calibration_family_rows(rows)
    paths = write_retry_calibration(
        rows,
        family_rows,
        tmp_path / "manual" / "retry_calibration.csv",
        tmp_path / "manual" / "retry_calibration.json",
        tmp_path / "manual" / "retry_calibration_by_family.csv",
        tmp_path / "manual" / "retry_calibration_by_family.json",
    )
    assert all(path.exists() for path in paths)
    payload = json.loads(paths[1].read_text(encoding="utf-8"))
    assert payload["schema_version"] == "cognition.revision.retry_calibration.v1"
    assert payload["rows"][0]["attempt_budget_k"] == 3

    output_root = tmp_path / "revision"
    assert main(
        [
            "--results-dir",
            str(results_dir),
            "--adaptive-summary",
            str(adaptive_summary),
            "--output-root",
            str(output_root),
            "--run-id",
            "safe-run",
            "--attempt-budget-k",
            "3",
        ]
    ) == 0

    assert (output_root / "safe-run" / "retry_calibration.csv").exists()
    assert (output_root / "safe-run" / "retry_calibration.json").exists()
    assert (output_root / "safe-run" / "retry_calibration_by_family.csv").exists()
    assert (output_root / "safe-run" / "retry_calibration_by_family.json").exists()


@pytest.mark.parametrize("bad_run_id", ["../phase3", "bad/run"])
def test_cli_rejects_invalid_run_ids_before_writing_outputs(
    tmp_path: Path,
    bad_run_id: str,
) -> None:
    results_dir = tmp_path / "results"
    adaptive_summary = tmp_path / "adaptive_summary.csv"
    _write_retry_inputs(results_dir, adaptive_summary)
    output_root = tmp_path / "revision"

    with pytest.raises(SystemExit):
        main(
            [
                "--results-dir",
                str(results_dir),
                "--adaptive-summary",
                str(adaptive_summary),
                "--output-root",
                str(output_root),
                "--run-id",
                bad_run_id,
                "--attempt-budget-k",
                "3",
            ]
        )

    assert not output_root.exists()
