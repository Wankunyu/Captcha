import csv
import json
from pathlib import Path

import pytest

from adaptive_compare import (
    CUTOFF_NOTE,
    build_comparison_rows,
    classify_rate,
    load_adaptive_summary,
    load_legacy_results,
    write_comparison,
)
from exp2_to_exp3_predict import predict_A_from_exp2, predict_q_from_exp2


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_legacy_results(results_dir: Path) -> None:
    _write_csv(
        results_dir / "exp2" / "openai" / "gpt-5" / "results.csv",
        [
            {"type": "Dice_Count", "n": 4, "pass_at_1": 0.25},
            {"type": "Patch_Select", "n": 5, "pass_at_1": 0.10},
            {"type": "Click_Order", "n": 5, "pass_at_1": 0.50},
            {"type": "Image_Matching", "n": 5, "pass_at_1": 0.10},
        ],
    )
    _write_csv(
        results_dir / "exp3" / "openai" / "gpt-5" / "results.csv",
        [
            {
                "kind": "summary",
                "type": "Dice_Count",
                "pass1": 1,
                "attempt_idx": 2,
                "cumulative_ms": 2500.0,
            }
        ],
    )


def _write_adaptive_summary(path: Path) -> None:
    _write_csv(
        path,
        [
            {
                "schema_version": "cognition.revision.adaptive_summary.v1",
                "run_id": "adaptive-run",
                "provider": "openai",
                "model": "gpt-5",
                "task_type": "Dice_Count",
                "attempt_budget_k": 3,
                "sampling_mode": "without-replacement",
                "feedback_mode": "binary-pass-fail",
                "memory_mode": "explicit-policy-notes",
                "solve_request_count": 2,
                "reflection_request_count": 1,
                "n_attempts": 2,
                "n_success": 1,
                "success_rate": 0.5,
                "expected_attempts": 2.0,
                "attempts_to_success": 2,
                "cumulative_latency_ms": 3000.0,
                "cumulative_cost_usd": 0.012,
                "scientific_wrong_count": 1,
                "protocol_failure_count": 0,
                "infrastructure_failure_count": 0,
                "stopping_reason": "first_success",
                "confidence_interval_low": "",
                "confidence_interval_high": "",
                "confidence_interval_not_applicable_reason": (
                    "single adaptive session; repeated-run CI deferred to Phase 3"
                ),
            },
            {
                "schema_version": "cognition.revision.adaptive_summary.v1",
                "run_id": "adaptive-run",
                "provider": "openai",
                "model": "gpt-5",
                "task_type": "Patch_Select",
                "attempt_budget_k": 3,
                "sampling_mode": "without-replacement",
                "feedback_mode": "binary-pass-fail",
                "memory_mode": "explicit-policy-notes",
                "solve_request_count": 3,
                "reflection_request_count": 2,
                "n_attempts": 3,
                "n_success": 0,
                "success_rate": 0.0,
                "expected_attempts": "",
                "attempts_to_success": "",
                "cumulative_latency_ms": 4200.0,
                "cumulative_cost_usd": 0.015,
                "scientific_wrong_count": 3,
                "protocol_failure_count": 0,
                "infrastructure_failure_count": 0,
                "stopping_reason": "budget_exhausted",
                "confidence_interval_low": "",
                "confidence_interval_high": "",
                "confidence_interval_not_applicable_reason": (
                    "single adaptive session; repeated-run CI deferred to Phase 3"
                ),
            },
            {
                "schema_version": "cognition.revision.adaptive_summary.v1",
                "run_id": "adaptive-run",
                "provider": "openai",
                "model": "gpt-5",
                "task_type": "Click_Order",
                "attempt_budget_k": 3,
                "sampling_mode": "without-replacement",
                "feedback_mode": "binary-pass-fail",
                "memory_mode": "explicit-policy-notes",
                "solve_request_count": 2,
                "reflection_request_count": 1,
                "n_attempts": 2,
                "n_success": 1,
                "success_rate": 0.40,
                "expected_attempts": 2.0,
                "attempts_to_success": 2,
                "cumulative_latency_ms": 2800.0,
                "cumulative_cost_usd": 0.010,
                "scientific_wrong_count": 1,
                "protocol_failure_count": 0,
                "infrastructure_failure_count": 0,
                "stopping_reason": "first_success",
                "confidence_interval_low": "",
                "confidence_interval_high": "",
                "confidence_interval_not_applicable_reason": "",
            },
            {
                "schema_version": "cognition.revision.adaptive_summary.v1",
                "run_id": "adaptive-run",
                "provider": "openai",
                "model": "gpt-5",
                "task_type": "Image_Matching",
                "attempt_budget_k": 3,
                "sampling_mode": "without-replacement",
                "feedback_mode": "binary-pass-fail",
                "memory_mode": "explicit-policy-notes",
                "solve_request_count": 2,
                "reflection_request_count": 0,
                "n_attempts": 2,
                "n_success": 0,
                "success_rate": 0.0,
                "expected_attempts": "",
                "attempts_to_success": "",
                "cumulative_latency_ms": 3100.0,
                "cumulative_cost_usd": 0.011,
                "scientific_wrong_count": 0,
                "protocol_failure_count": 2,
                "infrastructure_failure_count": 1,
                "stopping_reason": "budget_exhausted",
                "confidence_interval_low": "",
                "confidence_interval_high": "",
                "confidence_interval_not_applicable_reason": "",
            },
        ],
    )


def test_loads_and_merges_task_type_comparison_rows(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    adaptive_summary = tmp_path / "adaptive_summary.csv"
    _write_legacy_results(results_dir)
    _write_adaptive_summary(adaptive_summary)

    legacy = load_legacy_results(str(results_dir), provider="openai", model="gpt-5")
    loaded_adaptive = load_adaptive_summary(adaptive_summary)
    assert {"provider", "model", "provider_model", "task_type"}.issubset(legacy.columns)
    assert set(loaded_adaptive["task_type"]) == {"Dice_Count", "Patch_Select"}

    rows = build_comparison_rows(
        results_dir=str(results_dir),
        adaptive_summary_path=adaptive_summary,
        run_id="adaptive-run",
        provider="openai",
        model="gpt-5",
        attempt_budget_k=3,
    )

    by_task = {row.task_type: row for row in rows}
    dice = by_task["Dice_Count"]
    patch = by_task["Patch_Select"]

    assert dice.exp2_n == 4
    assert dice.exp2_pass_at_1 == pytest.approx(0.25)
    assert dice.bernoulli_success_at_k == pytest.approx(
        predict_q_from_exp2(0.25, 4, 3)
    )
    assert dice.bernoulli_expected_attempts == pytest.approx(
        predict_A_from_exp2(0.25, 4, 3)
    )
    assert dice.fixed_retry_observed_success is True
    assert dice.fixed_retry_attempts_to_success == 2
    assert dice.fixed_retry_cumulative_latency_ms == pytest.approx(2500.0)
    assert dice.adaptive_observed_success is True
    assert dice.adaptive_attempts_to_success == 2
    assert dice.adaptive_cumulative_cost_usd == pytest.approx(0.012)

    assert patch.fixed_retry_observed_success is None
    assert patch.fixed_retry_attempts_to_success is None
    assert patch.fixed_retry_cumulative_latency_ms is None
    assert patch.adaptive_observed_success is False
    assert patch.scientific_wrong_count == 3


def test_write_comparison_outputs_primary_key_fields(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    adaptive_summary = tmp_path / "adaptive_summary.csv"
    _write_legacy_results(results_dir)
    _write_adaptive_summary(adaptive_summary)
    rows = build_comparison_rows(
        results_dir=str(results_dir),
        adaptive_summary_path=adaptive_summary,
        run_id="adaptive-run",
        provider="openai",
        model="gpt-5",
        attempt_budget_k=3,
    )

    csv_path, json_path = write_comparison(
        rows,
        tmp_path / "nested" / "adaptive_comparison.csv",
        tmp_path / "nested" / "adaptive_comparison.json",
    )

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    primary_key = {
        "run_id",
        "provider",
        "model",
        "provider_model",
        "task_type",
        "attempt_budget_k",
    }
    assert primary_key.issubset(csv_rows[0])
    assert primary_key.issubset(payload["rows"][0])
    assert payload["rows"][0]["run_id"] == "adaptive-run"


def test_classify_rate_uses_cutoff_margin_labels() -> None:
    assert classify_rate(None) is None
    assert classify_rate(0.34) == "hard"
    assert classify_rate(0.35) == "borderline"
    assert classify_rate(0.40) == "borderline"
    assert classify_rate(0.45) == "borderline"
    assert classify_rate(0.46) == "broken"


def test_comparison_rows_add_labels_cutoff_note_and_bottleneck_tags(
    tmp_path: Path,
) -> None:
    results_dir = tmp_path / "results"
    adaptive_summary = tmp_path / "adaptive_summary.csv"
    _write_legacy_results(results_dir)
    _write_adaptive_summary(adaptive_summary)

    rows = build_comparison_rows(
        results_dir=str(results_dir),
        adaptive_summary_path=adaptive_summary,
        run_id="adaptive-run",
        provider="openai",
        model="gpt-5",
        attempt_budget_k=3,
    )
    by_task = {row.task_type: row for row in rows}

    dice = by_task["Dice_Count"]
    assert dice.baseline_label == "hard"
    assert dice.adaptive_label == "broken"
    assert dice.classification_change == "hard->broken"
    assert dice.cutoff_note == CUTOFF_NOTE
    assert "counting" in dice.structural_bottleneck_tags
    assert "instruction sensitivity" in dice.structural_bottleneck_tags

    click_order = by_task["Click_Order"]
    assert click_order.baseline_label == "broken"
    assert click_order.adaptive_label == "borderline"
    assert "spatial precision" in click_order.structural_bottleneck_tags
    assert "ordering" in click_order.structural_bottleneck_tags
    assert "instruction sensitivity" in click_order.structural_bottleneck_tags

    patch = by_task["Patch_Select"]
    assert patch.baseline_label == "hard"
    assert patch.adaptive_label == "hard"
    assert patch.classification_change == "hard->hard"
    assert "object-location binding" in patch.structural_bottleneck_tags


def test_persistent_failure_note_excludes_infrastructure_only_or_protocol_only(
    tmp_path: Path,
) -> None:
    results_dir = tmp_path / "results"
    adaptive_summary = tmp_path / "adaptive_summary.csv"
    _write_legacy_results(results_dir)
    _write_adaptive_summary(adaptive_summary)

    rows = build_comparison_rows(
        results_dir=str(results_dir),
        adaptive_summary_path=adaptive_summary,
        run_id="adaptive-run",
        provider="openai",
        model="gpt-5",
        attempt_budget_k=3,
    )
    by_task = {row.task_type: row for row in rows}

    patch = by_task["Patch_Select"]
    assert patch.adaptive_label == "hard"
    assert patch.adaptive_observed_success is False
    assert patch.scientific_wrong_count > 0
    assert (
        patch.persistent_failure_note
        == "adaptive remained hard under binary-feedback explicit-memory budget"
    )

    # Infrastructure-only or protocol-only rows are limitations/error-separation
    # evidence, not structural CAPTCHA robustness evidence.
    infra_or_protocol = by_task["Image_Matching"]
    assert infra_or_protocol.adaptive_label == "hard"
    assert infra_or_protocol.adaptive_observed_success is False
    assert infra_or_protocol.scientific_wrong_count == 0
    assert infra_or_protocol.protocol_failure_count > 0
    assert infra_or_protocol.infrastructure_failure_count > 0
    assert infra_or_protocol.persistent_failure_note is None
    assert infra_or_protocol.confidence_interval_low is None
    assert infra_or_protocol.confidence_interval_high is None
    assert (
        infra_or_protocol.confidence_interval_not_applicable_reason
        == "single adaptive session; repeated-run CI deferred to Phase 3"
    )
