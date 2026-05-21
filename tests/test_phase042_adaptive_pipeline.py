import json
from pathlib import Path

import pytest

import adaptive_attacker
import adaptive_preflight
from adaptive_preflight import (
    AdaptivePreflightCostPreview,
    AdaptivePreflightReport,
    AdaptivePreflightTaskSummary,
)
from expanded_dataset_phase042 import (
    PHASE042_ADAPTIVE_ATTEMPT_BUDGET_K,
    PHASE042_ADAPTIVE_EVALUATOR_SLICE,
    PHASE042_ADAPTIVE_INTERMEDIATE_BUDGET_K,
    PHASE042_ADAPTIVE_ROUND_COUNT,
    PHASE042_ADAPTIVE_SUPPLEMENTAL_RUN_ID,
    PHASE042_ADAPTIVE_TASK_TYPES,
    PHASE042_PAPER_FACING_PROVIDER_MODELS,
    build_phase042_adaptive_preflight_matrix,
    collect_phase042_adaptive_runs,
)
from phase042_artifacts import PHASE042_ADAPTIVE_SUMMARY_SCHEMA_VERSION


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _selected_row(task_type: str, sample_count: int = 10) -> dict[str, object]:
    return {
        "selected_id": f"phase042-{task_type.lower()}",
        "candidate_id": f"candidate-{task_type.lower()}",
        "source_path": f"expanded_captcha_data/phase04_2/candidates/{task_type}",
        "candidate_image_paths": [
            f"expanded_captcha_data/phase04_2/candidates/{task_type}/{index}.png"
            for index in range(sample_count)
        ],
        "source_kind": "open_source_dataset",
        "source_provenance_class": "preferred_real_external",
        "source_citation": "Example open-source CAPTCHA dataset",
        "source_license": "CC-BY-4.0",
        "source_provenance_notes": "Real external CAPTCHA samples for Phase 04.2.",
        "evidence_origin": "new_category",
        "slice_type": "new_category",
        "task_type": task_type,
        "task_family": "Counting",
        "sample_count": sample_count,
        "label_format": "ground_truth.json",
        "metadata_alignment_notes": "source ids mapped to selected rows",
        "answer_format_normalization": "answers normalized for evaluator use",
        "compatibility_status": "ready_for_static_pipeline",
        "evaluation_status": "selected_for_static",
        "limitation_notes": "offline corrected Phase 04.2 sidecar",
        "adaptive_eligible": True,
        "static_compatibility_notes": "offline images with ground truth",
        "novelty_sha256": ["b" * 64 for _ in range(sample_count)],
        "novelty_hash_report_path": (
            "expanded_captcha_data/phase04_2/novelty_hash_report.json"
        ),
        "exact_captcha_data_match": False,
        "perceptual_warning_count": 0,
        "review_warnings": [],
    }


def _write_phase042_adaptive_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    selected_manifest = tmp_path / "expanded_captcha_data/phase04_2/phase042_selected_manifest.json"
    _write_json(
        selected_manifest,
        {
            "schema_version": "cognition.revision.phase042.selected_manifest.v1",
            "rows": [
                _selected_row("Symbol_Count", 10),
                _selected_row("Relation_Match", 10),
                _selected_row("Hole_Counting", 10),
            ],
        },
    )
    dataset_root = tmp_path / PHASE042_ADAPTIVE_EVALUATOR_SLICE
    for task_type in PHASE042_ADAPTIVE_TASK_TYPES:
        task_root = dataset_root / task_type
        task_root.mkdir(parents=True, exist_ok=True)
        _write_json(
            task_root / "ground_truth.json",
            {
                f"{task_type.lower()}_1.png": {"answer": task_type},
                f"{task_type.lower()}_2.png": {"answer": task_type},
            },
        )
    results_dir = tmp_path / "results"
    for provider_model in PHASE042_PAPER_FACING_PROVIDER_MODELS:
        provider, model = provider_model.split("/", 1)
        _write_json(results_dir / "exp2" / provider / model / "results.json", [])
    return selected_manifest, dataset_root, results_dir


def _fake_adaptive_report(args) -> AdaptivePreflightReport:
    solve_request_count = len(args.types) * PHASE042_ADAPTIVE_ATTEMPT_BUDGET_K
    reflection_request_count = len(args.types) * (PHASE042_ADAPTIVE_ATTEMPT_BUDGET_K - 1)
    expected_request_count = solve_request_count + reflection_request_count
    return AdaptivePreflightReport(
        run_id=args.run_id,
        provider=args.provider,
        model=args.model,
        prompt_mode=args.prompt_mode,
        selected_task_types=list(args.types),
        attempt_budget_k=args.attempt_budget_k,
        sampling_mode=args.sampling_mode,
        feedback_mode=args.feedback_mode,
        memory_mode=args.memory_mode,
        stopping_rule=args.stopping_rule,
        solve_request_count=solve_request_count,
        reflection_request_count_max=reflection_request_count,
        expected_request_count_max=expected_request_count,
        prompt_config={"prompts_file": args.prompts_file, "prompts_file_sha256": "f" * 64},
        cost_preview=AdaptivePreflightCostPreview(
            solve_request_count=solve_request_count,
            reflection_request_count_max=reflection_request_count,
            expected_request_count_max=expected_request_count,
            unavailable_reason="pricing metadata not provided",
        ),
        output_dir=str(Path(args.output_root) / args.run_id),
        output_paths={
            "run_manifest": str(Path(args.output_root) / args.run_id / "run_manifest.json"),
            "adaptive_attempts": str(
                Path(args.output_root) / args.run_id / "adaptive_attempts.jsonl"
            ),
            "adaptive_summary_json": str(
                Path(args.output_root) / args.run_id / "adaptive_summary.json"
            ),
        },
        tasks=[
            AdaptivePreflightTaskSummary(
                task_type=task_type,
                canonical_task_type=task_type,
                dataset_dir=str(Path(args.dataset_root) / task_type),
                ground_truth_path=str(Path(args.dataset_root) / task_type / "ground_truth.json"),
                item_count=2,
                selected_count=2,
                solve_request_count=PHASE042_ADAPTIVE_ATTEMPT_BUDGET_K,
                reflection_request_count_max=PHASE042_ADAPTIVE_ATTEMPT_BUDGET_K - 1,
            )
            for task_type in args.types
        ],
    )


def _build_preflight(tmp_path: Path, monkeypatch) -> tuple[Path, list[object], Path]:
    selected_manifest, dataset_root, results_dir = _write_phase042_adaptive_fixture(tmp_path)
    output_root = tmp_path / "results/revision"
    monkeypatch.setattr(adaptive_preflight, "build_report", _fake_adaptive_report)
    rows = build_phase042_adaptive_preflight_matrix(
        selected_manifest_path=selected_manifest,
        dataset_root=dataset_root,
        results_dir=results_dir,
        output_root=output_root,
        write_reports=True,
    )
    matrix_path = (
        output_root
        / PHASE042_ADAPTIVE_SUPPLEMENTAL_RUN_ID
        / "expanded_adaptive_preflight_matrix.json"
    )
    return matrix_path, rows, selected_manifest


def test_adaptive_preflight_uses_six_hard_tasks_plus_three_new_categories(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _matrix_path, rows, _selected_manifest = _build_preflight(tmp_path, monkeypatch)

    assert len(rows) == len(PHASE042_PAPER_FACING_PROVIDER_MODELS) * PHASE042_ADAPTIVE_ROUND_COUNT
    assert {tuple(row.task_types) for row in rows} == {PHASE042_ADAPTIVE_TASK_TYPES}
    assert "Image_Recognition" not in rows[0].task_types
    assert "Geometry_Click" not in rows[0].task_types
    assert all(row.run_scope == "adaptive" for row in rows)
    assert all("ceiling-effect" in row.adaptive_scope_rationale for row in rows)


def test_adaptive_preflight_records_five_memory_isolated_rounds(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _matrix_path, rows, _selected_manifest = _build_preflight(tmp_path, monkeypatch)

    assert {row.round_count for row in rows} == {PHASE042_ADAPTIVE_ROUND_COUNT}
    assert {row.round_index for row in rows} == set(range(1, PHASE042_ADAPTIVE_ROUND_COUNT + 1))
    assert len({row.run_id for row in rows}) == len(rows)
    assert len({row.output_dir for row in rows}) == len(rows)
    assert len({row.seed for row in rows}) == len(rows)
    assert {row.attempt_budget_k for row in rows} == {PHASE042_ADAPTIVE_ATTEMPT_BUDGET_K}
    assert {row.intermediate_budget_k for row in rows} == {
        PHASE042_ADAPTIVE_INTERMEDIATE_BUDGET_K
    }
    assert {row.sampling_mode for row in rows} == {"without-replacement"}
    assert {row.feedback_mode for row in rows} == {"binary-pass-fail"}
    assert {row.memory_mode for row in rows} == {"explicit-policy-notes"}
    assert {row.stopping_rule for row in rows} == {"first-success-or-budget"}
    assert all(row.expected_request_count_max for row in rows)


def test_collect_adaptive_requires_confirmation(tmp_path: Path, monkeypatch) -> None:
    matrix_path, _rows, selected_manifest = _build_preflight(tmp_path, monkeypatch)

    def fail_run(**kwargs):
        raise AssertionError("collect-adaptive must require confirmation before providers")

    monkeypatch.setattr(adaptive_attacker, "run_adaptive_experiment", fail_run)
    with pytest.raises(ValueError, match="confirmed-adaptive-cost"):
        collect_phase042_adaptive_runs(
            preflight_matrix_path=matrix_path,
            output_root=tmp_path / "results/revision",
            selected_manifest_path=selected_manifest,
        )


def test_adaptive_summary_derives_success_at_3_and_success_at_5(
    tmp_path: Path,
    monkeypatch,
) -> None:
    matrix_path, _rows, selected_manifest = _build_preflight(tmp_path, monkeypatch)
    output_root = tmp_path / "results/revision"
    calls = []

    def fake_run_adaptive_experiment(**kwargs):
        calls.append(kwargs)
        run_dir = Path(kwargs["output_root"]) / kwargs["run_id"]
        run_dir.mkdir(parents=True, exist_ok=True)
        _write_json(run_dir / "run_manifest.json", {"run_id": kwargs["run_id"]})
        attempts = [
            {
                "schema_version": "cognition.revision.adaptive_attempt.v1",
                "run_id": kwargs["run_id"],
                "attempt_id": f"{kwargs['run_id']}:Dice_Count:{index}",
                "provider": kwargs["provider"],
                "model": kwargs["model"],
                "prompt_mode": "opt",
                "task_type": "Dice_Count",
                "puzzle_id": f"dice-{index}.png",
                "attempt_index": index,
                "attempt_budget_k": PHASE042_ADAPTIVE_ATTEMPT_BUDGET_K,
                "sampling_mode": "without-replacement",
                "feedback_mode": "binary-pass-fail",
                "memory_mode": "explicit-policy-notes",
                "correct": index == 4,
                "failure_class": "none" if index == 4 else "scientific_wrong",
                "stopping_reason": "first_success" if index == 4 else "continue",
            }
            for index in range(1, 5)
        ]
        (run_dir / "adaptive_attempts.jsonl").write_text(
            "\n".join(json.dumps(attempt) for attempt in attempts) + "\n",
            encoding="utf-8",
        )
        _write_json(
            run_dir / "adaptive_summary.json",
            {
                "schema_version": "cognition.revision.adaptive_summary.v1",
                "rows": [
                    {
                        "run_id": kwargs["run_id"],
                        "provider": kwargs["provider"],
                        "model": kwargs["model"],
                        "task_type": "Dice_Count",
                        "attempt_budget_k": PHASE042_ADAPTIVE_ATTEMPT_BUDGET_K,
                        "sampling_mode": "without-replacement",
                        "feedback_mode": "binary-pass-fail",
                        "memory_mode": "explicit-policy-notes",
                        "n_attempts": 4,
                        "n_success": 1,
                        "success_rate": 1.0,
                        "scientific_wrong_count": 3,
                        "protocol_failure_count": 0,
                        "infrastructure_failure_count": 0,
                        "stopping_reason": "first_success",
                    }
                ],
            },
        )
        return {"run_id": kwargs["run_id"]}

    monkeypatch.setattr(adaptive_attacker, "run_adaptive_experiment", fake_run_adaptive_experiment)

    summary = collect_phase042_adaptive_runs(
        preflight_matrix_path=matrix_path,
        output_root=output_root,
        selected_manifest_path=selected_manifest,
        confirmed_adaptive_cost=True,
    )

    assert summary["run_count"] == len(PHASE042_PAPER_FACING_PROVIDER_MODELS) * 5
    assert len(calls) == summary["run_count"]
    assert len({call["run_id"] for call in calls}) == len(calls)
    assert len({call["seed"] for call in calls}) == len(calls)
    assert calls[0]["attempt_budget_k"] == PHASE042_ADAPTIVE_ATTEMPT_BUDGET_K
    fireworks_call = next(call for call in calls if call["provider"] == "fireworks")
    assert fireworks_call["model"] == "accounts/fireworks/models/qwen3-vl-235b-a22b-instruct"
    medium_call = next(call for call in calls if call["run_id"].endswith("gpt-5.1_medium"))
    assert medium_call["model"] == "gpt-5.1"
    assert medium_call["thinking_options"] == {"effort": "medium"}
    payload = json.loads(
        (
            output_root
            / PHASE042_ADAPTIVE_SUPPLEMENTAL_RUN_ID
            / "expanded_adaptive_summary.json"
        ).read_text(encoding="utf-8")
    )
    assert payload["schema_version"] == PHASE042_ADAPTIVE_SUMMARY_SCHEMA_VERSION
    first_row = payload["rows"][0]
    assert first_row["success_at_3"] is False
    assert first_row["success_at_5"] is True
    assert first_row["attempts_to_success_at_3"] is None
    assert first_row["attempts_to_success_at_5"] == 4
    assert first_row["round_count"] == PHASE042_ADAPTIVE_ROUND_COUNT
    assert first_row["intermediate_budget_k"] == PHASE042_ADAPTIVE_INTERMEDIATE_BUDGET_K


def test_adaptive_pipeline_rejects_phase041_inputs(tmp_path: Path, monkeypatch) -> None:
    selected_manifest, dataset_root, results_dir = _write_phase042_adaptive_fixture(tmp_path)
    monkeypatch.setattr(adaptive_preflight, "build_report", _fake_adaptive_report)

    with pytest.raises(ValueError, match="Phase 04.1"):
        build_phase042_adaptive_preflight_matrix(
            selected_manifest_path=Path("expanded_captcha_data/phase04_1/manifest.json"),
            dataset_root=dataset_root,
            results_dir=results_dir,
            output_root=tmp_path / "results/revision",
        )

    with pytest.raises(ValueError, match="Phase 04.1"):
        build_phase042_adaptive_preflight_matrix(
            selected_manifest_path=selected_manifest,
            dataset_root=dataset_root,
            results_dir=results_dir,
            output_root=tmp_path / "results/revision",
            run_id="phase04_1_adaptive_supplemental",
        )
