import json
from pathlib import Path

import pytest

import adaptive_attacker
import adaptive_preflight
import run_eval
from adaptive_preflight import (
    AdaptivePreflightCostPreview,
    AdaptivePreflightReport,
    AdaptivePreflightTaskSummary,
)
from expanded_dataset import (
    PAPER_FACING_PROVIDER_MODELS,
    PHASE041_EVALUATOR_SLICE,
    PHASE041_NEW_TASK_MIN_SAMPLE_COUNT,
    PHASE041_SIDECAR_ROOT,
    build_adaptive_preflight_matrix,
    collect_adaptive_supplemental_runs,
)
from phase041_artifacts import (
    EXPANDED_ADAPTIVE_SUMMARY_SCHEMA_VERSION,
    ExpandedPreflightMatrixRow,
    write_expanded_preflight_matrix,
)


TASK_TYPES = [
    "Click_Order",
    "Dice_Count",
    "Geometry_Click",
    "Patch_Select",
    "Relation_Match",
    "Symbol_Count",
]

SEMANTICS = {
    "sampling_mode": "without-replacement",
    "feedback_mode": "binary-pass-fail",
    "memory_mode": "explicit-policy-notes",
    "stopping_rule": "first-success-or-budget",
}


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _manifest_row(task_type: str, **overrides: object) -> dict[str, object]:
    is_new = task_type in {"Relation_Match", "Symbol_Count"}
    values: dict[str, object] = {
        "source_id": f"phase04_1-{task_type}",
        "source_path": str(PHASE041_SIDECAR_ROOT / "sources" / task_type),
        "source_kind": "open_source_dataset",
        "source_citation": "Open CaptchaWorld-compatible test fixture",
        "source_license": "test fixture license",
        "source_provenance_notes": (
            "Mirrored from an open-source CAPTCHA dataset fixture for validation."
        ),
        "materialized_path": str(PHASE041_EVALUATOR_SLICE / task_type),
        "evidence_origin": "new_category" if is_new else "supplemented_category",
        "slice_type": "new_category" if is_new else "supplement_existing",
        "task_type": task_type,
        "task_family": "Image Matching" if task_type == "Relation_Match" else "Counting",
        "sample_count": PHASE041_NEW_TASK_MIN_SAMPLE_COUNT if is_new else 2,
        "label_format": "static ground_truth.json answer fields",
        "metadata_alignment_notes": "local source ids map to sidecar paths",
        "answer_format_normalization": "answers normalized before evaluator use",
        "compatibility_status": "ready_for_static_pipeline",
        "evaluation_status": "selected_for_adaptive",
        "limitation_notes": "authorized offline sidecar fixture only",
        "adaptive_eligible": True,
        "static_compatibility_notes": "offline static image with ground truth",
    }
    values.update(overrides)
    return values


def _write_phase041_sidecar(tmp_path: Path, **row_overrides: object) -> tuple[Path, Path]:
    sidecar_root = tmp_path / PHASE041_SIDECAR_ROOT
    dataset_root = tmp_path / PHASE041_EVALUATOR_SLICE
    for task_type in TASK_TYPES:
        (sidecar_root / "sources" / task_type).mkdir(parents=True, exist_ok=True)
        task_root = dataset_root / task_type
        task_root.mkdir(parents=True, exist_ok=True)
        _write_json(
            task_root / "ground_truth.json",
            {
                f"{task_type.lower()}_1.png": {"answer": task_type},
                f"{task_type.lower()}_2.png": {"answer": task_type},
            },
        )
        _write_json(
            sidecar_root / "sources" / task_type / "ground_truth.json",
            {f"{task_type.lower()}_1.png": {"answer": task_type}},
        )

    rows = []
    for task_type in TASK_TYPES:
        overrides = row_overrides if task_type == "Relation_Match" else {}
        rows.append(_manifest_row(task_type, **overrides))
    manifest_path = sidecar_root / "manifest.json"
    _write_json(manifest_path, {"rows": rows})
    return dataset_root, manifest_path


def _write_exp2_rows(tmp_path: Path) -> Path:
    results_dir = tmp_path / "results"
    for provider_model in PAPER_FACING_PROVIDER_MODELS:
        provider, model = provider_model.split("/", 1)
        _write_json(results_dir / "exp2" / provider / model / "results.json", [])
    return results_dir


def _fake_adaptive_report(args) -> AdaptivePreflightReport:
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
        solve_request_count=len(args.types),
        reflection_request_count_max=len(args.types),
        expected_request_count_max=len(args.types) * 2,
        prompt_config={"prompts_file": args.prompts_file, "prompts_file_sha256": "f" * 64},
        cost_preview=AdaptivePreflightCostPreview(
            solve_request_count=len(args.types),
            reflection_request_count_max=len(args.types),
            expected_request_count_max=len(args.types) * 2,
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
                solve_request_count=2,
                reflection_request_count_max=1,
            )
            for task_type in args.types
        ],
    )


def test_adaptive_preflight_rejects_manifest_ineligible_types(tmp_path) -> None:
    dataset_root, manifest_path = _write_phase041_sidecar(
        tmp_path,
        adaptive_eligible=False,
    )
    _write_exp2_rows(tmp_path)

    with pytest.raises(ValueError, match="adaptive_eligible"):
        build_adaptive_preflight_matrix(
            manifest_path=manifest_path,
            dataset_root=dataset_root,
            results_dir=tmp_path / "results",
            output_root=tmp_path / "results" / "revision",
            run_id="phase04_1_adaptive_supplemental",
            requested_task_types=["Relation_Match"],
        )


def test_adaptive_preflight_matrix_keeps_phase2_semantics_and_no_provider(
    tmp_path,
    monkeypatch,
) -> None:
    sentinel = "SECRET_GT_DO_NOT_LEAK"
    dataset_root, manifest_path = _write_phase041_sidecar(tmp_path)
    results_dir = _write_exp2_rows(tmp_path)
    output_root = tmp_path / "results" / "revision"
    calls = []

    def fail_provider(*args, **kwargs):
        raise AssertionError("adaptive preflight must not construct providers")

    def record_report(args):
        calls.append(args)
        return _fake_adaptive_report(args)

    monkeypatch.setattr(run_eval, "make_provider", fail_provider)
    monkeypatch.setattr(adaptive_preflight, "build_report", record_report)

    rows = build_adaptive_preflight_matrix(
        manifest_path=manifest_path,
        dataset_root=dataset_root,
        results_dir=results_dir,
        output_root=output_root,
        run_id="phase04_1_adaptive_supplemental",
        prompts_file=tmp_path / "prompts_optimized.yaml",
        prompt_mode="opt",
        attempt_budget_k=6,
        seed=1234,
        resume=True,
        write_reports=True,
    )

    assert [row.provider_model for row in rows] == PAPER_FACING_PROVIDER_MODELS
    assert len(calls) == 7
    first = rows[0]
    assert first.task_types == TASK_TYPES
    assert first.attempt_budget_k == 6
    assert first.sampling_mode == SEMANTICS["sampling_mode"]
    assert first.feedback_mode == SEMANTICS["feedback_mode"]
    assert first.memory_mode == SEMANTICS["memory_mode"]
    assert first.stopping_rule == SEMANTICS["stopping_rule"]
    assert first.solve_request_count == 6
    assert first.reflection_request_count_max == 6
    assert first.expected_request_count_max == 12
    matrix_path = (
        output_root
        / "phase04_1_adaptive_supplemental"
        / "expanded_adaptive_preflight_matrix.json"
    )
    assert matrix_path.exists()
    assert sentinel not in matrix_path.read_text(encoding="utf-8")


def _adaptive_preflight_rows(
    tmp_path: Path,
    manifest_path: Path,
    dataset_root: Path,
) -> list[ExpandedPreflightMatrixRow]:
    output_root = tmp_path / "results" / "revision"
    rows = []
    for provider_model in PAPER_FACING_PROVIDER_MODELS:
        provider, model = provider_model.split("/", 1)
        run_id = f"phase04_1_adaptive_supplemental-{provider}-{model.replace('/', '-')}"
        rows.append(
            ExpandedPreflightMatrixRow(
                run_id=run_id,
                provider=provider,
                model=model,
                provider_model=provider_model,
                run_scope="adaptive",
                manifest_path=str(manifest_path),
                manifest_sha256="a" * 64,
                sidecar_dataset_root=str(manifest_path.parent),
                materialized_dataset_root=str(dataset_root),
                task_types=TASK_TYPES,
                prompt_config={"prompts_file": "prompts_optimized.yaml"},
                expected_request_count=12,
                cost_preview={"unavailable_reason": "pricing metadata not provided"},
                output_dir=str(output_root / run_id),
                preflight_report_path=str(
                    output_root
                    / "phase04_1_adaptive_supplemental"
                    / "adaptive_preflight_reports"
                    / f"{run_id}.json"
                ),
                overwrite=False,
                resume=True,
                attempt_budget_k=6,
                sampling_mode=SEMANTICS["sampling_mode"],
                feedback_mode=SEMANTICS["feedback_mode"],
                memory_mode=SEMANTICS["memory_mode"],
                stopping_rule=SEMANTICS["stopping_rule"],
                solve_request_count=6,
                reflection_request_count_max=6,
                expected_request_count_max=12,
            )
        )
    return rows


def test_collect_adaptive_invokes_runner_and_writes_expanded_summary(
    tmp_path,
    monkeypatch,
) -> None:
    sentinel = "CORRECT_ANSWER_SENTINEL"
    dataset_root, manifest_path = _write_phase041_sidecar(tmp_path)
    output_root = tmp_path / "results" / "revision"
    matrix_path = (
        output_root
        / "phase04_1_adaptive_supplemental"
        / "expanded_adaptive_preflight_matrix.json"
    )
    write_expanded_preflight_matrix(
        output_root
        / "phase04_1_adaptive_supplemental"
        / "expanded_adaptive_preflight_matrix.csv",
        matrix_path,
        _adaptive_preflight_rows(tmp_path, manifest_path, dataset_root),
    )
    captured_calls = []

    def fake_run_adaptive_experiment(**kwargs):
        captured_calls.append(kwargs)
        run_id = kwargs["run_id"]
        run_dir = Path(kwargs["output_root"]) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        _write_json(run_dir / "run_manifest.json", {"run_id": run_id})
        attempt = {
            "schema_version": "cognition.revision.adaptive_attempt.v1",
            "run_id": run_id,
            "provider": kwargs["provider"],
            "model": kwargs["model"],
            "prompt_mode": "opt",
            "task_type": "Dice_Count",
            "puzzle_id": "dice.png",
            "attempt_index": 1,
            "attempt_budget_k": 6,
            "sampling_mode": SEMANTICS["sampling_mode"],
            "feedback_mode": SEMANTICS["feedback_mode"],
            "memory_mode": SEMANTICS["memory_mode"],
            "correct": False,
            "failure_class": "scientific_wrong",
            "stopping_reason": "budget_exhausted",
        }
        (run_dir / "adaptive_attempts.jsonl").write_text(
            json.dumps(attempt) + "\n",
            encoding="utf-8",
        )
        _write_json(
            run_dir / "adaptive_summary.json",
            {
                "schema_version": "cognition.revision.adaptive_summary.v1",
                "rows": [
                    {
                        "run_id": run_id,
                        "provider": kwargs["provider"],
                        "model": kwargs["model"],
                        "task_type": "Dice_Count",
                        "attempt_budget_k": 6,
                        "sampling_mode": SEMANTICS["sampling_mode"],
                        "feedback_mode": SEMANTICS["feedback_mode"],
                        "memory_mode": SEMANTICS["memory_mode"],
                        "solve_request_count": 1,
                        "reflection_request_count": 0,
                        "n_attempts": 1,
                        "n_success": 0,
                        "success_rate": 0.0,
                        "expected_attempts": None,
                        "attempts_to_success": None,
                        "cumulative_latency_ms": 1.0,
                        "cumulative_cost_usd": 0.0,
                        "scientific_wrong_count": 1,
                        "protocol_failure_count": 0,
                        "infrastructure_failure_count": 0,
                        "stopping_reason": "budget_exhausted",
                        "confidence_interval_low": None,
                        "confidence_interval_high": None,
                        "confidence_interval_not_applicable_reason": "test fixture",
                    }
                ],
            },
        )
        return {"run_id": run_id, "adaptive_summary_json": str(run_dir / "adaptive_summary.json")}

    monkeypatch.setattr(adaptive_attacker, "run_adaptive_experiment", fake_run_adaptive_experiment)

    summary = collect_adaptive_supplemental_runs(
        preflight_matrix_path=matrix_path,
        output_root=output_root,
        manifest_path=manifest_path,
        resume=True,
    )

    assert summary["run_count"] == 7
    assert len(captured_calls) == 7
    first_call = captured_calls[0]
    assert first_call["dataset_root"] == str(dataset_root)
    assert first_call["types"] == TASK_TYPES
    assert first_call["attempt_budget_k"] == 6
    assert first_call["prompt_mode"] == "opt"
    assert first_call["seed"] == 1234
    assert first_call["resume"] is True
    medium_call = next(
        call
        for call in captured_calls
        if call["run_id"].endswith("gpt-5.1_medium")
    )
    assert medium_call["model"] == "gpt-5.1"
    assert medium_call["thinking"] is True
    assert medium_call["thinking_options"] == {"effort": "medium"}
    adaptive_summary_path = (
        output_root
        / "phase04_1_adaptive_supplemental"
        / "expanded_adaptive_summary.json"
    )
    payload = json.loads(adaptive_summary_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == EXPANDED_ADAPTIVE_SUMMARY_SCHEMA_VERSION
    assert payload["rows"][0]["feedback_mode"] == SEMANTICS["feedback_mode"]
    assert payload["rows"][0]["memory_mode"] == SEMANTICS["memory_mode"]
    assert payload["rows"][0]["stopping_rule"] == SEMANTICS["stopping_rule"]
    assert sentinel not in adaptive_summary_path.read_text(encoding="utf-8")


def test_collect_adaptive_refuses_missing_preflight_matrix(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="preflight matrix"):
        collect_adaptive_supplemental_runs(
            preflight_matrix_path=tmp_path / "missing.json",
            output_root=tmp_path / "results" / "revision",
        )
