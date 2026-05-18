import argparse
import json
from pathlib import Path

import pytest
import yaml

from adaptive_preflight import (
    ADAPTIVE_PREFLIGHT_SCHEMA_VERSION,
    AdaptivePreflightCostPreview,
    AdaptivePreflightReport,
    AdaptivePreflightTaskSummary,
    build_parser,
    main,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_yaml(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")


def _dataset_root(tmp_path: Path) -> Path:
    root = tmp_path / "captcha_data"
    _write_json(
        root / "Dice_Count" / "ground_truth.json",
        {
            "dice1.png": {"sum": 3},
            "dice2.png": {"sum": 4},
            "dice3.png": {"sum": 5},
        },
    )
    return root


def _prompts_file(tmp_path: Path) -> Path:
    path = tmp_path / "prompts.yaml"
    _write_yaml(path, {"types": {"Dice_Count": "count dice"}})
    return path


def _base_args(tmp_path: Path, run_id: str = "adaptive-run") -> list[str]:
    return [
        "--dataset-root",
        str(_dataset_root(tmp_path)),
        "--types",
        "Dice_Count",
        "--prompts-file",
        str(_prompts_file(tmp_path)),
        "--output-root",
        str(tmp_path / "results" / "revision"),
        "--run-id",
        run_id,
        "--provider",
        "openai",
        "--model",
        "gpt-5",
        "--max-per-type",
        "1",
        "--attempt-budget-k",
        "2",
    ]


def test_schema_constant_and_models_expose_adaptive_semantics() -> None:
    assert ADAPTIVE_PREFLIGHT_SCHEMA_VERSION == "cognition.revision.adaptive_preflight.v1"

    task = AdaptivePreflightTaskSummary(
        task_type="Dice_Count",
        canonical_task_type="Dice_Count",
        dataset_dir="captcha_data/Dice_Count",
        ground_truth_path="captcha_data/Dice_Count/ground_truth.json",
        item_count=3,
        selected_count=1,
        solve_request_count=1,
        reflection_request_count_max=0,
    )
    cost_preview = AdaptivePreflightCostPreview(
        solve_request_count=1,
        reflection_request_count_max=0,
        expected_request_count_max=1,
        unavailable_reason="pricing metadata not provided",
    )
    report = AdaptivePreflightReport(
        run_id="adaptive-run",
        provider="openai",
        model="gpt-5",
        prompt_mode="opt",
        selected_task_types=["Dice_Count"],
        attempt_budget_k=2,
        sampling_mode="without-replacement",
        feedback_mode="binary-pass-fail",
        memory_mode="explicit-policy-notes",
        stopping_rule="first-success-or-budget",
        solve_request_count=1,
        reflection_request_count_max=0,
        expected_request_count_max=1,
        prompt_config={},
        cost_preview=cost_preview,
        output_dir="results/revision/adaptive-run",
        output_paths={"adaptive_preflight_report": "adaptive_preflight_report.json"},
        tasks=[task],
    )

    payload = report.model_dump(mode="json")
    assert payload["schema_version"] == ADAPTIVE_PREFLIGHT_SCHEMA_VERSION
    assert payload["sampling_mode"] == "without-replacement"
    assert payload["feedback_mode"] == "binary-pass-fail"
    assert payload["memory_mode"] == "explicit-policy-notes"
    assert payload["stopping_rule"] == "first-success-or-budget"


def test_parser_declares_required_adaptive_flags() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--types",
            "Dice_Count",
            "--run-id",
            "adaptive-run",
            "--provider",
            "openai",
            "--model",
            "gpt-5",
        ]
    )

    assert isinstance(args, argparse.Namespace)
    assert args.attempt_budget_k == 6
    assert args.sampling_mode == "without-replacement"
    assert args.feedback_mode == "binary-pass-fail"
    assert args.memory_mode == "explicit-policy-notes"
    assert args.stopping_rule == "first-success-or-budget"
    assert args.prompt_mode == "opt"


def test_cli_prints_report_and_writes_only_when_requested(tmp_path, capsys) -> None:
    exit_code = main(_base_args(tmp_path))
    report = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert report["schema_version"] == ADAPTIVE_PREFLIGHT_SCHEMA_VERSION
    assert report["selected_task_types"] == ["Dice_Count"]
    assert report["attempt_budget_k"] == 2
    assert report["sampling_mode"] == "without-replacement"
    assert report["feedback_mode"] == "binary-pass-fail"
    assert report["memory_mode"] == "explicit-policy-notes"
    assert report["stopping_rule"] == "first-success-or-budget"
    assert not (tmp_path / "results" / "revision" / "adaptive-run").exists()

    main([*_base_args(tmp_path, run_id="written-run"), "--write-report"])
    assert (
        tmp_path
        / "results"
        / "revision"
        / "written-run"
        / "adaptive_preflight_report.json"
    ).exists()


def test_preflight_does_not_construct_provider(tmp_path, monkeypatch, capsys) -> None:
    import run_eval

    def fail(*args, **kwargs):
        raise AssertionError("adaptive preflight must not construct providers")

    monkeypatch.setattr(run_eval, "make_provider", fail)

    main(_base_args(tmp_path, run_id="provider-free"))
    report = json.loads(capsys.readouterr().out)

    assert report["provider"] == "openai"
    assert report["model"] == "gpt-5"
