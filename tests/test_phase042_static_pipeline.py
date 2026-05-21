import json
from pathlib import Path

import pytest

import revision_preflight
import run_eval
from expanded_dataset_phase042 import (
    PHASE042_EVALUATOR_SLICE,
    PHASE042_PAPER_FACING_PROVIDER_MODELS,
    PHASE042_STATIC_SUPPLEMENTAL_RUN_ID,
    PHASE042_STATIC_TASK_TYPES,
    build_phase042_static_preflight_matrix,
    collect_phase042_static_runs,
)
from phase042_artifacts import PHASE042_STATIC_SUMMARY_SCHEMA_VERSION
from revision_preflight import PreflightCostPreview, PreflightReport, PreflightTaskSummary


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write_phase042_pricing(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "pricing:",
                "  openai:",
                "    gpt-5: {in_per_1k: 0.00125, out_per_1k: 0.0100}",
                "    gpt-5.1: {in_per_1k: 0.00125, out_per_1k: 0.0100}",
                "  anthropic:",
                "    claude-sonnet-4-5: {in_per_1k: 0.003, out_per_1k: 0.015}",
                "  gemini:",
                "    gemini-2.5-flash: {in_per_1k: 0.00030, out_per_1k: 0.0025}",
                "    gemini-2.5-pro: {in_per_1k: 0.00125, out_per_1k: 0.0100}",
                "  fireworks:",
                "    accounts/fireworks/models/qwen3-vl-235b-a22b-instruct: "
                "{in_per_1k: 0.00022, out_per_1k: 0.00088}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _write_exp2_token_summaries(results_dir: Path) -> None:
    for provider_model in PHASE042_PAPER_FACING_PROVIDER_MODELS:
        provider, model = provider_model.split("/", 1)
        summary_model = (
            "accounts/fireworks/models/qwen3-vl-235b-a22b-instruct"
            if provider == "fireworks"
            else ("gpt-5.1" if model.startswith("gpt-5.1_") else model)
        )
        _write_json(
            (
                results_dir
                / "exp2"
                / provider
                / model
                / f"exp2_opt_{provider}_{model}_token_summary.json"
            ),
            {
                "experiment": "exp2_opt",
                "provider": provider,
                "model": summary_model,
                "overall": {
                    "total_questions": 10,
                    "total_tokens_in": 10000,
                    "total_tokens_out": 1000,
                    "total_tokens": 11000,
                },
            },
        )


def _selected_row(task_type: str, sample_count: int = 10) -> dict[str, object]:
    return {
        "selected_id": f"phase042-{task_type.lower()}",
        "candidate_id": f"candidate-{task_type.lower()}",
        "source_path": f"expanded_captcha_data/phase04_2/candidates/{task_type}",
        "candidate_image_paths": [
            f"expanded_captcha_data/phase04_2/candidates/{task_type}/{task_type.lower()}_{index}.png"
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


def _write_phase042_static_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    selected_manifest = tmp_path / "expanded_captcha_data/phase04_2/phase042_selected_manifest.json"
    rows = [
        _selected_row("Symbol_Count", 2),
        _selected_row("Relation_Match", 2),
        _selected_row("Hole_Counting", 2),
    ]
    for row in rows:
        row["sample_count"] = 10
    _write_json(
        selected_manifest,
        {
            "schema_version": "cognition.revision.phase042.selected_manifest.v1",
            "rows": rows,
        },
    )
    dataset_root = tmp_path / PHASE042_EVALUATOR_SLICE
    for task_type in PHASE042_STATIC_TASK_TYPES:
        task_root = dataset_root / task_type
        task_root.mkdir(parents=True, exist_ok=True)
        image_name = f"{task_type.lower()}_sample.png"
        (task_root / image_name).write_bytes(b"fixture")
        _write_json(task_root / "ground_truth.json", {image_name: {"answer": task_type}})
    results_dir = tmp_path / "results"
    for provider_model in PHASE042_PAPER_FACING_PROVIDER_MODELS:
        provider, model = provider_model.split("/", 1)
        _write_json(results_dir / "exp2" / provider / model / "results.json", [])
    return selected_manifest, dataset_root, results_dir


def _fake_preflight_report(args) -> PreflightReport:
    return PreflightReport(
        run_id=args.run_id,
        provider=args.provider,
        model=args.model,
        prompt_mode=args.prompt_mode,
        selected_task_types=list(args.types),
        expected_request_count=len(args.types),
        prompt_config={
            "prompts_file": args.prompts_file,
            "prompts_file_sha256": "f" * 64,
            "few_shot_config": None,
            "few_shot_config_sha256": None,
            "prompt_prefix_sha256": None,
            "prompt_suffix_sha256": None,
        },
        cost_preview=PreflightCostPreview(
            expected_request_count=len(args.types),
            unavailable_reason="pricing metadata not provided",
        ),
        output_dir=str(Path(args.output_root) / args.run_id),
        manifest_path=str(Path(args.output_root) / args.run_id / "run_manifest.json"),
        attempts_path=str(Path(args.output_root) / args.run_id / "attempts.jsonl"),
        tasks=[
            PreflightTaskSummary(
                task_type=task_type,
                canonical_task_type=task_type,
                dataset_dir=str(Path(args.dataset_root) / task_type),
                ground_truth_path=str(Path(args.dataset_root) / task_type / "ground_truth.json"),
                item_count=1,
                selected_count=1,
            )
            for task_type in args.types
        ],
    )


def test_static_preflight_uses_full_paper_facing_matrix(tmp_path: Path, monkeypatch) -> None:
    selected_manifest, dataset_root, results_dir = _write_phase042_static_fixture(tmp_path)
    output_root = tmp_path / "results/revision"
    calls = []

    def record_report(args):
        calls.append(args)
        return _fake_preflight_report(args)

    monkeypatch.setattr(revision_preflight, "build_report", record_report)

    rows = build_phase042_static_preflight_matrix(
        selected_manifest_path=selected_manifest,
        dataset_root=dataset_root,
        results_dir=results_dir,
        output_root=output_root,
        write_reports=True,
    )

    assert [row.provider_model for row in rows] == PHASE042_PAPER_FACING_PROVIDER_MODELS
    assert [f"{call.provider}/{call.model}" for call in calls] == (
        PHASE042_PAPER_FACING_PROVIDER_MODELS
    )
    assert (output_root / PHASE042_STATIC_SUPPLEMENTAL_RUN_ID / "preflight_reports").is_dir()
    assert (
        output_root
        / PHASE042_STATIC_SUPPLEMENTAL_RUN_ID
        / "expanded_static_preflight_matrix.json"
    ).is_file()


def test_static_preflight_uses_only_three_new_categories(tmp_path: Path, monkeypatch) -> None:
    selected_manifest, dataset_root, results_dir = _write_phase042_static_fixture(tmp_path)
    monkeypatch.setattr(revision_preflight, "build_report", _fake_preflight_report)

    rows = build_phase042_static_preflight_matrix(
        selected_manifest_path=selected_manifest,
        dataset_root=dataset_root,
        results_dir=results_dir,
        output_root=tmp_path / "results/revision",
    )

    assert {tuple(row.task_types) for row in rows} == {PHASE042_STATIC_TASK_TYPES}
    assert "Dice_Count" not in rows[0].task_types
    assert "Geometry_Click" not in rows[0].task_types


def test_static_preflight_estimates_cost_from_token_pricing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    selected_manifest, dataset_root, results_dir = _write_phase042_static_fixture(tmp_path)
    pricing_file = _write_phase042_pricing(tmp_path / "pricing.phase04_2.yaml")
    _write_exp2_token_summaries(results_dir)
    monkeypatch.setattr(revision_preflight, "build_report", _fake_preflight_report)

    rows = build_phase042_static_preflight_matrix(
        selected_manifest_path=selected_manifest,
        dataset_root=dataset_root,
        results_dir=results_dir,
        output_root=tmp_path / "results/revision",
        pricing_file=pricing_file,
        write_reports=True,
    )

    assert all(row.cost_preview["approximate_cost_usd"] > 0 for row in rows)
    assert all(row.cost_preview["pricing_source"] == str(pricing_file) for row in rows)
    assert rows[0].cost_preview["pricing_model"] == "gpt-5"
    medium = next(row for row in rows if row.model == "gpt-5.1_medium")
    fireworks = next(row for row in rows if row.provider == "fireworks")
    assert medium.cost_preview["pricing_model"] == "gpt-5.1"
    assert fireworks.cost_preview["pricing_model"] == (
        "accounts/fireworks/models/qwen3-vl-235b-a22b-instruct"
    )
    assert "unavailable_reason" not in fireworks.cost_preview
    report_payload = json.loads(Path(fireworks.preflight_report_path).read_text(encoding="utf-8"))
    assert report_payload["cost_preview"]["approximate_cost_usd"] > 0


def test_static_preflight_never_constructs_providers(tmp_path: Path, monkeypatch) -> None:
    selected_manifest, dataset_root, results_dir = _write_phase042_static_fixture(tmp_path)

    def fail_provider(*args, **kwargs):
        raise AssertionError("static-preflight-matrix must not construct providers")

    monkeypatch.setattr(run_eval, "make_provider", fail_provider)
    monkeypatch.setattr(revision_preflight, "build_report", _fake_preflight_report)

    build_phase042_static_preflight_matrix(
        selected_manifest_path=selected_manifest,
        dataset_root=dataset_root,
        results_dir=results_dir,
        output_root=tmp_path / "results/revision",
    )


def test_collect_static_invokes_phase042_revision_contract(
    tmp_path: Path,
    monkeypatch,
) -> None:
    selected_manifest, dataset_root, results_dir = _write_phase042_static_fixture(tmp_path)
    output_root = tmp_path / "results/revision"
    monkeypatch.setattr(revision_preflight, "build_report", _fake_preflight_report)
    build_phase042_static_preflight_matrix(
        selected_manifest_path=selected_manifest,
        dataset_root=dataset_root,
        results_dir=results_dir,
        output_root=output_root,
    )
    matrix_path = (
        output_root
        / PHASE042_STATIC_SUPPLEMENTAL_RUN_ID
        / "expanded_static_preflight_matrix.json"
    )
    calls = []

    def fake_run_eval(**kwargs):
        calls.append(kwargs)
        run_dir = Path(kwargs["revision_output_root"]) / kwargs["revision_run_id"]
        run_dir.mkdir(parents=True, exist_ok=True)
        _write_json(run_dir / "run_manifest.json", {"run_id": kwargs["revision_run_id"]})
        attempt = {
            "schema_version": "cognition.revision.attempt.v1",
            "run_id": kwargs["revision_run_id"],
            "attempt_id": f"{kwargs['revision_run_id']}:Symbol_Count:symbol.png:1",
            "task_type": "Symbol_Count",
            "puzzle_id": "symbol.png",
            "attempt_index": 1,
            "prompt_mode": "opt",
            "provider": kwargs["provider"],
            "model": kwargs["model"],
            "parsed_answer": {"answer_type": "number", "value": 1},
            "correct": False,
            "error_category": None,
            "latency_ms": 1.0,
            "tokens_in": 1,
            "tokens_out": 1,
            "cost_usd": 0.0,
            "timestamp": "2026-05-21T00:00:00Z",
        }
        (run_dir / "attempts.jsonl").write_text(json.dumps(attempt) + "\n", encoding="utf-8")
        _write_json(run_dir / "summary.json", {"rows": []})
        return {"n": 1, "pass1": 0.0}

    monkeypatch.setattr(run_eval, "run_eval", fake_run_eval)

    summary = collect_phase042_static_runs(
        preflight_matrix_path=matrix_path,
        output_root=output_root,
        selected_manifest_path=selected_manifest,
    )

    assert summary["run_count"] == 7
    first_call = calls[0]
    assert first_call["dataset_root"] == str(dataset_root)
    assert first_call["types"] == list(PHASE042_STATIC_TASK_TYPES)
    assert first_call["revision_run_id"].startswith(PHASE042_STATIC_SUPPLEMENTAL_RUN_ID)
    assert first_call["revision_output_root"] == str(output_root)
    assert first_call["write_attempts"] is True
    assert first_call["prompt_mode"] == "opt"
    assert first_call["max_attempts"] == 1
    assert first_call["resume_revision_output"] is True
    medium_call = next(call for call in calls if call["revision_run_id"].endswith("gpt-5.1_medium"))
    none_call = next(call for call in calls if call["revision_run_id"].endswith("gpt-5.1_none"))
    fireworks_call = next(call for call in calls if call["provider"] == "fireworks")
    assert medium_call["model"] == "gpt-5.1"
    assert medium_call["thinking"] is True
    assert medium_call["thinking_options"] == {"effort": "medium"}
    assert none_call["model"] == "gpt-5.1"
    assert none_call["thinking"] is False
    assert fireworks_call["model"] == (
        "accounts/fireworks/models/qwen3-vl-235b-a22b-instruct"
    )
    assert fireworks_call["thinking"] is False
    assert fireworks_call["thinking_options"] is None
    payload = json.loads(
        (
            output_root
            / PHASE042_STATIC_SUPPLEMENTAL_RUN_ID
            / "expanded_static_summary.json"
        ).read_text(encoding="utf-8")
    )
    assert payload["schema_version"] == PHASE042_STATIC_SUMMARY_SCHEMA_VERSION
    assert payload["rows"][0]["scientific_wrong_count"] == 1


def test_static_pipeline_rejects_phase041_inputs(tmp_path: Path) -> None:
    selected_manifest, dataset_root, results_dir = _write_phase042_static_fixture(tmp_path)

    with pytest.raises(ValueError, match="Phase 04.1"):
        build_phase042_static_preflight_matrix(
            selected_manifest_path=Path("expanded_captcha_data/phase04_1/manifest.json"),
            dataset_root=dataset_root,
            results_dir=results_dir,
            output_root=tmp_path / "results/revision",
        )

    with pytest.raises(ValueError, match="Phase 04.1"):
        build_phase042_static_preflight_matrix(
            selected_manifest_path=selected_manifest,
            dataset_root=dataset_root,
            results_dir=results_dir,
            output_root=tmp_path / "results/revision",
            run_id="phase04_1_static_supplemental",
        )
