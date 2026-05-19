import csv
import json
from pathlib import Path

import pytest

from dataset_scope_audit import (
    HOLD_BUTTON_REASON,
    SLIDE_PUZZLE_REASON,
    build_dataset_scope_rows,
    collect_evaluated_counts,
    load_ground_truth_count,
    main,
    write_dataset_scope_audit,
)
from phase3_artifacts import DATASET_SCOPE_SCHEMA_VERSION


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _dataset_root(tmp_path: Path) -> Path:
    root = tmp_path / "captcha_data"
    _write_json(
        root / "Dice_Count" / "ground_truth.json",
        {f"dice-{idx}.png": {"answer": idx % 6} for idx in range(25)},
    )
    _write_json(
        root / "Geometry_Click" / "ground_truth.json",
        {f"geom-{idx}.png": {"x": idx, "y": idx} for idx in range(15)},
    )
    _write_json(
        root / "Hold_Button(Not Used)" / "ground_truth.json",
        {"hold-1.png": {"hold_time": 2.5, "completed": True}},
    )
    _write_json(
        root / "Slide_Puzzle(Not Used)" / "ground_truth.json",
        {"slide-1.png": {"target_position": 40, "tolerance": 3}},
    )
    return root


def _results_dir(tmp_path: Path) -> Path:
    results = tmp_path / "results"
    _write_csv(
        results / "exp2" / "openai" / "gpt-5" / "results.csv",
        [
            {"type": "Dice_Count", "pass": 1},
            {"type": "Dice_Count", "pass": 0},
            {"task_type": "Connect_icon", "pass": 1},
        ],
    )
    _write_csv(
        results / "error_analysis" / "openai" / "gpt-5" / "results.csv",
        [{"type": "Geometry_Click", "pass": 1}],
    )
    return results


def _write_prompt_configs(tmp_path: Path) -> None:
    (tmp_path / "prompts_optimized.yaml").write_text(
        "types:\n  Dice_Count: Count the objects.\n",
        encoding="utf-8",
    )
    (tmp_path / "few_shot_examples.yaml").write_text(
        "Dice_Count:\n  examples: []\n",
        encoding="utf-8",
    )


def test_load_ground_truth_count_supports_mapping_and_list(tmp_path) -> None:
    mapping_path = tmp_path / "mapping.json"
    list_path = tmp_path / "list.json"
    _write_json(mapping_path, {"one.png": {"answer": 1}, "two.png": {"answer": 2}})
    _write_json(list_path, [{"id": "one"}, {"id": "two"}, {"id": "three"}])

    assert load_ground_truth_count(mapping_path) == 2
    assert load_ground_truth_count(list_path) == 3


def test_collect_evaluated_counts_filters_to_exp1_through_exp4(tmp_path) -> None:
    results = _results_dir(tmp_path)

    counts = collect_evaluated_counts(results)

    assert counts[("exp2", "Dice_Count")] == 2
    assert counts[("exp2", "Connect_Icon")] == 1
    assert not any(experiment == "error_analysis" for experiment, _ in counts)
    assert ("error_analysis", "Geometry_Click") not in counts


def test_build_dataset_scope_rows_classifies_supported_underpowered_and_removed_tasks(
    tmp_path, monkeypatch
) -> None:
    dataset_root = _dataset_root(tmp_path)
    results_dir = _results_dir(tmp_path)
    _write_prompt_configs(tmp_path)
    monkeypatch.chdir(tmp_path)

    rows = build_dataset_scope_rows(
        dataset_root=dataset_root,
        results_dir=results_dir,
        run_id="scope-test",
        underpowered_n=20,
    )
    by_task = {row.task_type: row for row in rows}

    dice = by_task["Dice_Count"]
    assert dice.schema_version == DATASET_SCOPE_SCHEMA_VERSION
    assert dice.scope_status == "included"
    assert dice.support_status == "supported"
    assert dice.pipeline_compatibility == "compatible_static_answer"
    assert dice.dataset_sample_count == 25
    assert dice.evaluated_n_exp2 == 2
    assert dice.underpowered_threshold == 20
    assert dice.underpowered is False
    assert dice.prompt_key_status == "present"
    assert dice.few_shot_key_status == "present"

    geometry = by_task["Geometry_Click"]
    assert geometry.scope_status == "underpowered"
    assert geometry.support_status == "supported"
    assert geometry.dataset_sample_count == 15
    assert geometry.evaluated_n_exp2 == 0
    assert geometry.underpowered is True
    assert "underpowered" in geometry.reason

    hold = by_task["Hold_Button(Not Used)"]
    assert hold.scope_status == "incompatible"
    assert hold.support_status == "removed_not_used"
    assert hold.pipeline_compatibility == "incompatible_temporal_hold"
    assert hold.reason == HOLD_BUTTON_REASON

    slide = by_task["Slide_Puzzle(Not Used)"]
    assert slide.scope_status == "incompatible"
    assert slide.support_status == "removed_not_used"
    assert slide.pipeline_compatibility == "incompatible_slider_drag"
    assert slide.reason == SLIDE_PUZZLE_REASON


def test_write_dataset_scope_audit_emits_csv_and_json(tmp_path, monkeypatch) -> None:
    dataset_root = _dataset_root(tmp_path)
    results_dir = _results_dir(tmp_path)
    _write_prompt_configs(tmp_path)
    monkeypatch.chdir(tmp_path)
    rows = build_dataset_scope_rows(dataset_root, results_dir, "scope-test", 20)

    output_csv = tmp_path / "out" / "dataset_scope_audit.csv"
    output_json = tmp_path / "out" / "dataset_scope_audit.json"
    csv_path, json_path = write_dataset_scope_audit(rows, output_csv, output_json)

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert csv_rows[0]["schema_version"] == DATASET_SCOPE_SCHEMA_VERSION
    assert payload["schema_version"] == DATASET_SCOPE_SCHEMA_VERSION
    assert {row["task_type"] for row in payload["rows"]} >= {
        "Dice_Count",
        "Geometry_Click",
        "Hold_Button(Not Used)",
        "Slide_Puzzle(Not Used)",
    }


def test_cli_writes_default_revision_outputs_and_prints_secret_safe_summary(
    tmp_path, monkeypatch, capsys
) -> None:
    dataset_root = _dataset_root(tmp_path)
    results_dir = _results_dir(tmp_path)
    _write_prompt_configs(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "--dataset-root",
            str(dataset_root),
            "--results-dir",
            str(results_dir),
            "--output-root",
            str(tmp_path / "results" / "revision"),
            "--run-id",
            "scope-test",
            "--underpowered-n",
            "20",
        ]
    )

    summary = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert summary["underpowered_threshold"] == 20
    assert summary["removed_task_types"] == [
        "Hold_Button(Not Used)",
        "Slide_Puzzle(Not Used)",
    ]
    assert summary["output_csv"].endswith("scope-test/dataset_scope_audit.csv")
    assert summary["output_json"].endswith("scope-test/dataset_scope_audit.json")
    assert "secret" not in json.dumps(summary).lower()
    assert Path(summary["output_csv"]).exists()
    assert Path(summary["output_json"]).exists()


def test_cli_help_exits_cleanly(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    assert "--underpowered-n" in capsys.readouterr().out
