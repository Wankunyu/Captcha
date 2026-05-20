import json
from pathlib import Path

import pytest

import revision_preflight
import run_eval
from expanded_dataset import (
    PAPER_FACING_PROVIDER_MODELS,
    PHASE041_EVALUATOR_SLICE,
    PHASE041_NEW_TASK_MIN_SAMPLE_COUNT,
    PHASE041_SIDECAR_ROOT,
    build_static_preflight_matrix,
    collect_static_supplemental_runs,
)
from phase041_artifacts import (
    EXPANDED_STATIC_SUMMARY_SCHEMA_VERSION,
    ExpandedPreflightMatrixRow,
    write_expanded_preflight_matrix,
)
from revision_preflight import PreflightCostPreview, PreflightReport, PreflightTaskSummary


PAPER_FACING_PROVIDER_MODELS_LITERAL = [
    "openai/gpt-5",
    "openai/gpt-5.1_medium",
    "openai/gpt-5.1_none",
    "anthropic/claude-sonnet-4-5",
    "gemini/gemini-2.5-flash",
    "gemini/gemini-2.5-pro",
    "fireworks/accounts_fireworks_models_qwen3-vl-235b-a22b-instruct",
]

TASK_TYPES = [
    "Click_Order",
    "Dice_Count",
    "Geometry_Click",
    "Patch_Select",
    "Relation_Match",
    "Symbol_Count",
]


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _manifest_row(task_type: str) -> dict[str, object]:
    is_new = task_type in {"Relation_Match", "Symbol_Count"}
    return {
        "source_id": f"phase04_1-{task_type}",
        "source_path": str(PHASE041_SIDECAR_ROOT / "sources" / task_type),
        "materialized_path": str(PHASE041_EVALUATOR_SLICE / task_type),
        "evidence_origin": "new_category" if is_new else "supplemented_category",
        "slice_type": "new_category" if is_new else "supplement_existing",
        "task_type": task_type,
        "task_family": "Image Matching" if task_type == "Relation_Match" else "Counting",
        "sample_count": PHASE041_NEW_TASK_MIN_SAMPLE_COUNT if is_new else 1,
        "label_format": "static ground_truth.json answer fields",
        "metadata_alignment_notes": "local source ids map to sidecar paths",
        "answer_format_normalization": "answers normalized before evaluator use",
        "compatibility_status": "ready_for_static_pipeline",
        "evaluation_status": "selected_for_static",
        "limitation_notes": "authorized offline sidecar fixture only",
        "adaptive_eligible": True,
        "static_compatibility_notes": "offline static image with ground truth",
    }


def _write_phase041_sidecar(tmp_path: Path) -> tuple[Path, Path, Path]:
    sidecar_root = tmp_path / PHASE041_SIDECAR_ROOT
    dataset_root = tmp_path / PHASE041_EVALUATOR_SLICE
    for task_type in TASK_TYPES:
        source_root = sidecar_root / "sources" / task_type
        materialized_root = dataset_root / task_type
        source_root.mkdir(parents=True, exist_ok=True)
        materialized_root.mkdir(parents=True, exist_ok=True)
        (source_root / f"{task_type.lower()}_sample.png").write_bytes(b"fixture")
        (materialized_root / f"{task_type.lower()}_sample.png").write_bytes(b"fixture")
        ground_truth = {f"{task_type.lower()}_sample.png": {"answer": task_type}}
        _write_json(source_root / "ground_truth.json", ground_truth)
        _write_json(materialized_root / "ground_truth.json", ground_truth)

    manifest_path = sidecar_root / "manifest.json"
    _write_json(manifest_path, {"rows": [_manifest_row(task_type) for task_type in TASK_TYPES]})
    return sidecar_root, dataset_root, manifest_path


def _write_exp2_rows(tmp_path: Path) -> Path:
    results_dir = tmp_path / "results"
    assert PAPER_FACING_PROVIDER_MODELS_LITERAL == PAPER_FACING_PROVIDER_MODELS
    for provider_model in PAPER_FACING_PROVIDER_MODELS_LITERAL:
        provider, model = provider_model.split("/", 1)
        _write_json(results_dir / "exp2" / provider / model / "results.json", [])
    return results_dir


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


def test_preflight_matrix_never_constructs_providers(tmp_path, monkeypatch) -> None:
    sentinel_credential = "REDACTED_OPENAI_API_KEY"
    _, dataset_root, manifest_path = _write_phase041_sidecar(tmp_path)
    results_dir = _write_exp2_rows(tmp_path)
    output_root = tmp_path / "results" / "revision"
    calls = []

    def fail_provider(*args, **kwargs):
        raise AssertionError("preflight-matrix must not construct providers")

    def record_report(args):
        calls.append(args)
        return _fake_preflight_report(args)

    monkeypatch.setattr(run_eval, "make_provider", fail_provider)
    monkeypatch.setattr(revision_preflight, "build_report", record_report)

    rows = build_static_preflight_matrix(
        manifest_path=manifest_path,
        dataset_root=dataset_root,
        results_dir=results_dir,
        output_root=output_root,
        run_id="phase04_1_static_supplemental",
        prompts_file=tmp_path / "prompts_optimized.yaml",
        prompt_mode="opt",
        max_attempts=1,
        resume=True,
        write_reports=True,
    )

    assert [row.provider_model for row in rows] == PAPER_FACING_PROVIDER_MODELS
    assert [f"{call.provider}/{call.model}" for call in calls] == PAPER_FACING_PROVIDER_MODELS
    reports_dir = output_root / "phase04_1_static_supplemental" / "preflight_reports"
    assert len(list(reports_dir.glob("*.json"))) == 7
    first = rows[0]
    assert first.manifest_sha256
    assert first.sidecar_dataset_root == str(manifest_path.parent)
    assert first.materialized_dataset_root == str(dataset_root)
    assert first.task_types == TASK_TYPES
    assert first.prompt_config["prompts_file"] == str(tmp_path / "prompts_optimized.yaml")
    assert first.cost_preview["unavailable_reason"] == "pricing metadata not provided"
    matrix_path = output_root / "phase04_1_static_supplemental" / "expanded_preflight_matrix.json"
    assert matrix_path.exists()
    assert sentinel_credential not in matrix_path.read_text(encoding="utf-8")


def _preflight_rows(
    tmp_path: Path,
    manifest_path: Path,
    dataset_root: Path,
) -> list[ExpandedPreflightMatrixRow]:
    output_root = tmp_path / "results" / "revision"
    rows = []
    for provider_model in PAPER_FACING_PROVIDER_MODELS:
        provider, model = provider_model.split("/", 1)
        run_id = f"phase04_1_static_supplemental-{provider}-{model.replace('/', '-')}"
        rows.append(
            ExpandedPreflightMatrixRow(
                run_id=run_id,
                provider=provider,
                model=model,
                provider_model=provider_model,
                run_scope="static",
                manifest_path=str(manifest_path),
                manifest_sha256="a" * 64,
                sidecar_dataset_root=str(manifest_path.parent),
                materialized_dataset_root=str(dataset_root),
                task_types=TASK_TYPES,
                prompt_config={"prompts_file": "prompts_optimized.yaml"},
                expected_request_count=len(TASK_TYPES),
                cost_preview={"unavailable_reason": "pricing metadata not provided"},
                output_dir=str(output_root / run_id),
                preflight_report_path=str(
                    output_root
                    / "phase04_1_static_supplemental"
                    / "preflight_reports"
                    / f"{run_id}.json"
                ),
                overwrite=False,
                resume=True,
            )
        )
    return rows


def test_collect_static_invokes_revision_run_contract_and_writes_summary(
    tmp_path,
    monkeypatch,
) -> None:
    sentinel_credential = "REDACTED_OPENAI_API_KEY"
    _, dataset_root, manifest_path = _write_phase041_sidecar(tmp_path)
    output_root = tmp_path / "results" / "revision"
    matrix_path = output_root / "phase04_1_static_supplemental" / "expanded_preflight_matrix.json"
    write_expanded_preflight_matrix(
        output_root / "phase04_1_static_supplemental" / "expanded_preflight_matrix.csv",
        matrix_path,
        _preflight_rows(tmp_path, manifest_path, dataset_root),
    )
    captured_calls = []

    def fake_run_eval(**kwargs):
        captured_calls.append(kwargs)
        run_id = kwargs["revision_run_id"]
        run_dir = Path(kwargs["revision_output_root"]) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        _write_json(run_dir / "run_manifest.json", {"run_id": run_id})
        is_infrastructure_failure = kwargs["provider"] == "fireworks"
        attempt = {
            "schema_version": "cognition.revision.attempt.v1",
            "run_id": run_id,
            "attempt_id": f"{run_id}:Dice_Count:dice.png:1",
            "task_type": "Dice_Count",
            "puzzle_id": "dice.png",
            "attempt_index": 1,
            "prompt_mode": "opt",
            "provider": kwargs["provider"],
            "model": kwargs["model"],
            "parsed_answer": None
            if is_infrastructure_failure
            else {"answer_type": "number", "value": 2},
            "correct": False,
            "error_category": "parse_error" if is_infrastructure_failure else None,
            "latency_ms": 1.0,
            "tokens_in": 0,
            "tokens_out": 0,
            "cost_usd": None if is_infrastructure_failure else 0.0,
            "timestamp": "2026-05-20T00:00:00Z",
        }
        (run_dir / "attempts.jsonl").write_text(json.dumps(attempt) + "\n", encoding="utf-8")
        _write_json(run_dir / "summary.json", {"schema_version": "summary", "rows": []})
        return {"n": 1, "pass1": 0.0}

    monkeypatch.setattr(run_eval, "run_eval", fake_run_eval)

    summary = collect_static_supplemental_runs(
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
    assert first_call["revision_output_root"] == str(output_root)
    assert first_call["write_attempts"] is True
    assert first_call["prompt_mode"] == "opt"
    assert first_call["max_attempts"] == 1
    assert first_call["resume_revision_output"] is True
    medium_call = next(
        call
        for call in captured_calls
        if call["revision_run_id"].endswith("gpt-5.1_medium")
    )
    none_call = next(
        call for call in captured_calls if call["revision_run_id"].endswith("gpt-5.1_none")
    )
    assert medium_call["model"] == "gpt-5.1"
    assert medium_call["thinking"] is True
    assert medium_call["thinking_options"] == {"effort": "medium"}
    assert none_call["model"] == "gpt-5.1"
    assert none_call["thinking"] is False
    assert none_call["thinking_options"] is None
    static_summary_path = (
        output_root / "phase04_1_static_supplemental" / "expanded_static_summary.json"
    )
    payload = json.loads(static_summary_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == EXPANDED_STATIC_SUMMARY_SCHEMA_VERSION
    assert payload["rows"][0]["scientific_wrong_count"] == 1
    assert payload["rows"][0]["protocol_failure_count"] == 0
    assert payload["rows"][0]["infrastructure_failure_count"] == 0
    fireworks_row = next(
        row for row in payload["rows"] if row["provider_model"].startswith("fireworks/")
    )
    assert fireworks_row["scientific_wrong_count"] == 0
    assert fireworks_row["protocol_failure_count"] == 0
    assert fireworks_row["infrastructure_failure_count"] == 1
    assert sentinel_credential not in static_summary_path.read_text(encoding="utf-8")


def test_collect_static_refuses_missing_preflight_matrix(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="preflight matrix"):
        collect_static_supplemental_runs(
            preflight_matrix_path=tmp_path / "missing.json",
            output_root=tmp_path / "results" / "revision",
        )
