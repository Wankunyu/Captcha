from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# The script is invoked by path from the repo root, so make root imports explicit.
from cognition import adaptive_attacker  # noqa: E402
from cognition.adaptive_artifacts import FEEDBACK_MODE, MEMORY_MODE, SAMPLING_MODE, STOPPING_RULE  # noqa: E402
from cognition.phase042_artifacts import (  # noqa: E402
    PHASE042_ADAPTIVE_SUMMARY_SCHEMA_VERSION,
    Phase042AdaptiveSummaryRow,
)
from cognition.revision_artifacts import revision_run_dir, sha256_file  # noqa: E402


TASK_TYPES = ("Dice_Count", "Rotation_Match")
TASK_FAMILIES = {"Dice_Count": "Counting", "Rotation_Match": "unknown"}
RUN_ID = "phase04_2_adaptive_gpt5_medium_k3_dice_rotation_rerun_20260522"
SOURCE_DATASET_ROOT = Path("expanded_captcha_data/phase04_2/adaptive_evaluator_slice")
FILTERED_DATASET_ROOT = Path(
    "expanded_captcha_data/phase04_2/adaptive_k3_dice_rotation_rerun_slice_20260522"
)
PREVIOUS_ATTEMPTS_GLOB = (
    "results/local_runs/"
    "phase04_2_adaptive_gpt5_medium_20260522-round*/adaptive_attempts.jsonl"
)
RESULTS_ROOT = Path("results/local_runs")
PROMPTS_FILE = Path("prompts_optimized.yaml")
IMAGE_SUFFIXES = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".webp"}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return path


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _iter_string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for child in value.values():
            strings.extend(_iter_string_values(child))
        return strings
    if isinstance(value, list):
        strings = []
        for child in value:
            strings.extend(_iter_string_values(child))
        return strings
    return []


def _referenced_files(ground_truth: dict[str, Any]) -> list[str]:
    referenced: set[str] = set()
    for puzzle_id, entry in ground_truth.items():
        if isinstance(puzzle_id, str) and Path(puzzle_id).suffix.lower() in IMAGE_SUFFIXES:
            referenced.add(puzzle_id)
        for value in _iter_string_values(entry):
            if Path(value).suffix.lower() in IMAGE_SUFFIXES:
                referenced.add(value)
    return sorted(referenced)


def _safe_copy(source_dir: Path, output_dir: Path, relative_path: str) -> None:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"referenced file must be relative and safe: {relative_path}")
    source_path = source_dir / relative
    if not source_path.is_file():
        raise FileNotFoundError(str(source_path))
    destination = output_dir / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination)


def discover_first_attempt_successes(
    previous_attempts_glob: str,
) -> dict[str, list[dict[str, Any]]]:
    successes: dict[str, list[dict[str, Any]]] = {task_type: [] for task_type in TASK_TYPES}
    for path in sorted(Path().glob(previous_attempts_glob)):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                attempt = json.loads(line)
                task_type = attempt.get("task_type")
                if (
                    task_type in successes
                    and int(attempt.get("attempt_index") or 0) == 1
                    and bool(attempt.get("correct"))
                ):
                    successes[task_type].append(
                        {
                            "run_id": attempt.get("run_id"),
                            "task_type": task_type,
                            "puzzle_id": attempt.get("puzzle_id"),
                            "attempt_id": attempt.get("attempt_id"),
                            "attempt_log_path": path.as_posix(),
                        }
                    )
    return {
        task_type: sorted(rows, key=lambda row: str(row["puzzle_id"]))
        for task_type, rows in successes.items()
    }


def materialize_filtered_slice(
    *,
    source_dataset_root: Path,
    output_dataset_root: Path,
    exclusions: dict[str, list[dict[str, Any]]],
    previous_attempts_glob: str,
) -> dict[str, Any]:
    sample_count_by_task: dict[str, int] = {}
    excluded_ids_by_task = {
        task_type: {str(row["puzzle_id"]) for row in rows}
        for task_type, rows in exclusions.items()
    }
    ground_truth_files: list[str] = []
    copied_file_count = 0
    output_dataset_root.mkdir(parents=True, exist_ok=True)

    for task_type in TASK_TYPES:
        source_dir = source_dataset_root / task_type
        output_dir = output_dataset_root / task_type
        ground_truth = _read_json(source_dir / "ground_truth.json")
        if not isinstance(ground_truth, dict):
            raise ValueError(f"ground_truth.json must contain an object for {task_type}")
        filtered_ground_truth = {
            puzzle_id: entry
            for puzzle_id, entry in ground_truth.items()
            if puzzle_id not in excluded_ids_by_task[task_type]
        }
        if len(filtered_ground_truth) < 3:
            raise ValueError(f"{task_type} has fewer than three remaining samples")
        output_dir.mkdir(parents=True, exist_ok=True)
        for relative_path in _referenced_files(filtered_ground_truth):
            _safe_copy(source_dir, output_dir, relative_path)
            copied_file_count += 1
        ground_truth_path = output_dir / "ground_truth.json"
        _write_json(ground_truth_path, filtered_ground_truth)
        ground_truth_files.append(ground_truth_path.as_posix())
        sample_count_by_task[task_type] = len(filtered_ground_truth)

    manifest = {
        "schema_version": "cognition.revision.phase042.adaptive_k3_filter_manifest.v1",
        "created_at": _utc_now(),
        "source_dataset_root": source_dataset_root.as_posix(),
        "filtered_dataset_root": output_dataset_root.as_posix(),
        "previous_attempts_glob": previous_attempts_glob,
        "task_types": list(TASK_TYPES),
        "exclusion_rule": "exclude previous GPT-5 medium samples solved on attempt_index=1",
        "excluded_first_attempt_successes": exclusions,
        "excluded_count_by_task": {
            task_type: len(rows) for task_type, rows in exclusions.items()
        },
        "sample_count_by_task": sample_count_by_task,
        "copied_file_count": copied_file_count,
        "ground_truth_files": ground_truth_files,
    }
    _write_json(output_dataset_root / "filter_manifest.json", manifest)
    return manifest


def _previous_cost_preview(expected_request_count_max: int) -> dict[str, Any]:
    previous_matrix_path = (
        RESULTS_ROOT
        / "phase04_2_adaptive_gpt5_medium_20260522"
        / "expanded_adaptive_preflight_matrix.json"
    )
    if not previous_matrix_path.is_file():
        return {
            "expected_request_count_max": expected_request_count_max,
            "approximate_cost_usd": None,
            "pricing_basis": "previous Phase 04.2 GPT-5 medium matrix unavailable",
        }
    payload = _read_json(previous_matrix_path)
    rows = payload.get("rows") if isinstance(payload, dict) else payload
    first = rows[0] if isinstance(rows, list) and rows else {}
    previous = first.get("cost_preview") if isinstance(first, dict) else {}
    previous_requests = float(previous.get("expected_request_count_max") or 0)
    previous_cost = previous.get("approximate_cost_usd")
    if previous_requests <= 0 or previous_cost is None:
        approximate_cost = None
    else:
        approximate_cost = round(
            float(previous_cost) / previous_requests * expected_request_count_max,
            6,
        )
    return {
        "solve_request_count": len(TASK_TYPES) * 3,
        "reflection_request_count_max": len(TASK_TYPES) * 2,
        "expected_request_count_max": expected_request_count_max,
        "approximate_cost_usd": approximate_cost,
        "pricing_source": previous.get("pricing_source"),
        "pricing_model": previous.get("pricing_model"),
        "pricing_basis": (
            "Scaled from the previous Phase 04.2 GPT-5 medium adaptive preflight "
            "average request estimate; runtime uses reasoning effort medium."
        ),
    }


def build_preflight_matrix(
    *,
    run_id: str,
    output_root: Path,
    dataset_root: Path,
    sample_count_by_task: dict[str, int],
    exclusions: dict[str, list[dict[str, Any]]],
    round_count: int,
    seed: int,
    resume: bool,
    overwrite: bool,
) -> dict[str, Any]:
    solve_request_count = sum(min(sample_count_by_task[task_type], 3) for task_type in TASK_TYPES)
    reflection_request_count_max = sum(
        max(0, min(sample_count_by_task[task_type], 3) - 1) for task_type in TASK_TYPES
    )
    expected_request_count_max = solve_request_count + reflection_request_count_max
    rows: list[dict[str, Any]] = []
    for round_index in range(1, round_count + 1):
        round_run_id = f"{run_id}-round{round_index:02d}-openai-gpt-5-medium"
        row = {
            "run_id": round_run_id,
            "provider": "openai",
            "model": "gpt-5_medium",
            "runtime_model": "gpt-5",
            "reasoning_effort": "medium",
            "provider_model": "openai/gpt-5_medium",
            "run_scope": "adaptive_k3_filtered_rerun",
            "task_types": list(TASK_TYPES),
            "materialized_dataset_root": dataset_root.as_posix(),
            "sample_count_by_task": sample_count_by_task,
            "excluded_first_attempt_successes": exclusions,
            "prompt_config": {
                "prompt_mode": "opt",
                "prompts_file": PROMPTS_FILE.as_posix(),
                "prompts_file_sha256": sha256_file(PROMPTS_FILE),
            },
            "attempt_budget_k": 3,
            "sampling_mode": SAMPLING_MODE,
            "feedback_mode": FEEDBACK_MODE,
            "memory_mode": MEMORY_MODE,
            "stopping_rule": STOPPING_RULE,
            "solve_request_count": solve_request_count,
            "reflection_request_count_max": reflection_request_count_max,
            "expected_request_count_max": expected_request_count_max,
            "cost_preview": _previous_cost_preview(expected_request_count_max),
            "output_dir": str(revision_run_dir(output_root, round_run_id).resolve()),
            "overwrite": overwrite,
            "resume": resume,
            "round_id": f"round{round_index:02d}",
            "round_index": round_index,
            "round_count": round_count,
            "seed": seed + (round_index - 1) * 1000,
        }
        rows.append(row)

    matrix_dir = revision_run_dir(output_root, run_id)
    csv_rows = [
        {
            key: json.dumps(value, ensure_ascii=False, sort_keys=True)
            if isinstance(value, (dict, list))
            else value
            for key, value in row.items()
        }
        for row in rows
    ]
    _write_csv(matrix_dir / "adaptive_k3_preflight_matrix.csv", csv_rows)
    _write_json(
        matrix_dir / "adaptive_k3_preflight_matrix.json",
        {
            "schema_version": "cognition.revision.phase042.adaptive_k3_preflight_matrix.v1",
            "rows": rows,
        },
    )
    return {
        "matrix_dir": matrix_dir,
        "rows": rows,
        "expected_request_count_max_per_round": expected_request_count_max,
        "expected_request_count_max_total": expected_request_count_max * round_count,
        "approximate_cost_usd_total": round(
            sum(float(row["cost_preview"].get("approximate_cost_usd") or 0.0) for row in rows),
            6,
        ),
    }


def _attempts_for_task(path: Path, task_type: str) -> list[dict[str, Any]]:
    attempts = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            attempt = json.loads(line)
            if attempt.get("task_type") == task_type:
                attempts.append(attempt)
    return attempts


def _first_success(attempts: list[dict[str, Any]], k: int) -> int | None:
    success_indices = [
        int(attempt.get("attempt_index") or 0)
        for attempt in attempts
        if bool(attempt.get("correct")) and int(attempt.get("attempt_index") or 0) <= k
    ]
    return min(success_indices) if success_indices else None


def write_expanded_summary(
    *,
    matrix_dir: Path,
    matrix_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    expanded_rows: list[Phase042AdaptiveSummaryRow] = []
    aggregate_by_task: dict[str, dict[str, Any]] = {
        task_type: {
            "task_type": task_type,
            "round_count": 0,
            "success_at_3_count": 0,
            "scientific_wrong_count": 0,
            "protocol_failure_count": 0,
            "infrastructure_failure_count": 0,
            "solve_request_count": 0,
            "reflection_request_count": 0,
            "cumulative_cost_usd": 0.0,
        }
        for task_type in TASK_TYPES
    }
    for row in matrix_rows:
        run_dir = Path(row["output_dir"])
        summary_payload = _read_json(run_dir / "adaptive_summary.json")
        summary_rows = summary_payload.get("rows") if isinstance(summary_payload, dict) else []
        for summary_row in summary_rows:
            task_type = str(summary_row.get("task_type") or "")
            if task_type not in TASK_TYPES:
                continue
            attempts = _attempts_for_task(run_dir / "adaptive_attempts.jsonl", task_type)
            first_success_at_3 = _first_success(attempts, 3)
            expanded = Phase042AdaptiveSummaryRow(
                run_id=str(row["run_id"]),
                provider="openai",
                model="gpt-5_medium",
                provider_model="openai/gpt-5_medium",
                task_type=task_type,
                task_family=TASK_FAMILIES[task_type],
                evidence_origin="supplemented_category",
                sample_count=int(row["sample_count_by_task"][task_type]),
                session_count=1,
                round_id=str(row["round_id"]),
                round_index=int(row["round_index"]),
                round_count=int(row["round_count"]),
                attempt_budget_k=3,
                intermediate_budget_k=3,
                success_count=int(summary_row.get("n_success") or 0),
                success_at_3=first_success_at_3 is not None,
                success_at_5=None,
                attempts_to_success_at_3=first_success_at_3,
                attempts_to_success_at_5=None,
                scientific_wrong_count=int(summary_row.get("scientific_wrong_count") or 0),
                protocol_failure_count=int(summary_row.get("protocol_failure_count") or 0),
                infrastructure_failure_count=int(
                    summary_row.get("infrastructure_failure_count") or 0
                ),
                adaptive_success_rate=float(summary_row.get("success_rate") or 0.0),
                feedback_mode=str(summary_row.get("feedback_mode") or FEEDBACK_MODE),
                memory_mode=str(summary_row.get("memory_mode") or MEMORY_MODE),
                stopping_rule=STOPPING_RULE,
                run_manifest_path=str(run_dir / "run_manifest.json"),
                adaptive_attempt_log_path=str(run_dir / "adaptive_attempts.jsonl"),
                adaptive_summary_source_path=str(run_dir / "adaptive_summary.json"),
                selected_manifest_path=str(matrix_dir / "filter_manifest.json"),
                claim_use="appendix_context",
            )
            expanded_rows.append(expanded)
            aggregate = aggregate_by_task[task_type]
            aggregate["round_count"] += 1
            aggregate["success_at_3_count"] += int(first_success_at_3 is not None)
            aggregate["scientific_wrong_count"] += expanded.scientific_wrong_count
            aggregate["protocol_failure_count"] += expanded.protocol_failure_count
            aggregate["infrastructure_failure_count"] += expanded.infrastructure_failure_count
            aggregate["solve_request_count"] += int(summary_row.get("solve_request_count") or 0)
            aggregate["reflection_request_count"] += int(
                summary_row.get("reflection_request_count") or 0
            )
            aggregate["cumulative_cost_usd"] += float(
                summary_row.get("cumulative_cost_usd") or 0.0
            )

    output_rows = [row.model_dump(mode="json") for row in expanded_rows]
    _write_json(
        matrix_dir / "expanded_adaptive_summary.json",
        {
            "schema_version": PHASE042_ADAPTIVE_SUMMARY_SCHEMA_VERSION,
            "rows": output_rows,
        },
    )
    _write_csv(
        matrix_dir / "expanded_adaptive_summary.csv",
        [
            {
                key: json.dumps(value, ensure_ascii=False, sort_keys=True)
                if isinstance(value, (dict, list))
                else value
                for key, value in row.items()
            }
            for row in output_rows
        ],
    )
    aggregate_rows = []
    for task_type, aggregate in aggregate_by_task.items():
        round_count = int(aggregate["round_count"])
        aggregate_rows.append(
            {
                **aggregate,
                "success_at_3_rate": (
                    aggregate["success_at_3_count"] / round_count if round_count else None
                ),
                "cumulative_cost_usd": round(float(aggregate["cumulative_cost_usd"]), 6),
            }
        )
    aggregate_summary = {
        "schema_version": "cognition.revision.phase042.adaptive_k3_aggregate_summary.v1",
        "rows": aggregate_rows,
        "expanded_adaptive_summary_json": str(matrix_dir / "expanded_adaptive_summary.json"),
        "expanded_adaptive_summary_csv": str(matrix_dir / "expanded_adaptive_summary.csv"),
    }
    _write_json(matrix_dir / "adaptive_k3_aggregate_summary.json", aggregate_summary)
    return aggregate_summary


def run_rounds(
    *,
    matrix_rows: list[dict[str, Any]],
    output_root: Path,
    dataset_root: Path,
    secrets_file: str,
    timeout_sec: float,
    stream: bool,
) -> list[dict[str, Any]]:
    results = []
    for row in matrix_rows:
        results.append(
            adaptive_attacker.run_adaptive_experiment(
                dataset_root=dataset_root.as_posix(),
                types=list(TASK_TYPES),
                provider="openai",
                model="gpt-5",
                run_id=str(row["run_id"]),
                output_root=output_root.as_posix(),
                attempt_budget_k=3,
                max_per_type=None,
                prompts_file=PROMPTS_FILE.as_posix(),
                prompt_mode="opt",
                secrets_file=secrets_file,
                timeout_sec=timeout_sec,
                seed=int(row["seed"]),
                stream=stream,
                overwrite=bool(row["overwrite"]),
                resume=bool(row["resume"]),
                thinking=True,
                thinking_options={"effort": "medium"},
            )
        )
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Phase 04.2 GPT-5 medium k=3 adaptive rerun for Dice_Count "
            "and Rotation_Match, excluding prior first-attempt successes."
        )
    )
    parser.add_argument(
        "--task-types",
        nargs="+",
        choices=sorted(TASK_FAMILIES),
        default=list(TASK_TYPES),
    )
    parser.add_argument("--run-id", default=RUN_ID)
    parser.add_argument("--source-dataset-root", type=Path, default=SOURCE_DATASET_ROOT)
    parser.add_argument("--output-dataset-root", type=Path, default=FILTERED_DATASET_ROOT)
    parser.add_argument("--previous-attempts-glob", default=PREVIOUS_ATTEMPTS_GLOB)
    parser.add_argument("--output-root", type=Path, default=RESULTS_ROOT)
    parser.add_argument("--round-count", type=int, default=5)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--secrets-file", default="secrets.yaml")
    parser.add_argument("--timeout-sec", type=float, default=600.0)
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--resume", action="store_true", default=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    global TASK_TYPES
    TASK_TYPES = tuple(args.task_types)
    if args.round_count != 5:
        raise ValueError("This rerun is defined for exactly five rounds.")
    if args.overwrite and args.resume:
        raise ValueError("--overwrite and --resume are mutually exclusive")

    exclusions = discover_first_attempt_successes(args.previous_attempts_glob)
    filter_manifest = materialize_filtered_slice(
        source_dataset_root=args.source_dataset_root,
        output_dataset_root=args.output_dataset_root,
        exclusions=exclusions,
        previous_attempts_glob=args.previous_attempts_glob,
    )
    matrix = build_preflight_matrix(
        run_id=args.run_id,
        output_root=args.output_root,
        dataset_root=args.output_dataset_root,
        sample_count_by_task=filter_manifest["sample_count_by_task"],
        exclusions=exclusions,
        round_count=args.round_count,
        seed=args.seed,
        resume=args.resume,
        overwrite=args.overwrite,
    )
    matrix_dir = matrix["matrix_dir"]
    _write_json(matrix_dir / "filter_manifest.json", filter_manifest)

    if args.dry_run:
        result = {
            "dry_run": True,
            "run_id": args.run_id,
            "matrix_dir": matrix_dir.as_posix(),
            "filtered_dataset_root": args.output_dataset_root.as_posix(),
            "excluded_count_by_task": filter_manifest["excluded_count_by_task"],
            "sample_count_by_task": filter_manifest["sample_count_by_task"],
            "expected_request_count_max_total": matrix["expected_request_count_max_total"],
            "approximate_cost_usd_total": matrix["approximate_cost_usd_total"],
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    run_results = run_rounds(
        matrix_rows=matrix["rows"],
        output_root=args.output_root,
        dataset_root=args.output_dataset_root,
        secrets_file=args.secrets_file,
        timeout_sec=args.timeout_sec,
        stream=args.stream,
    )
    aggregate_summary = write_expanded_summary(
        matrix_dir=matrix_dir,
        matrix_rows=matrix["rows"],
    )
    result = {
        "dry_run": False,
        "run_id": args.run_id,
        "run_count": len(run_results),
        "matrix_dir": matrix_dir.as_posix(),
        "filtered_dataset_root": args.output_dataset_root.as_posix(),
        "excluded_count_by_task": filter_manifest["excluded_count_by_task"],
        "sample_count_by_task": filter_manifest["sample_count_by_task"],
        "expected_request_count_max_total": matrix["expected_request_count_max_total"],
        "approximate_cost_usd_total": matrix["approximate_cost_usd_total"],
        "aggregate_summary_json": str(matrix_dir / "adaptive_k3_aggregate_summary.json"),
        "expanded_adaptive_summary_json": aggregate_summary["expanded_adaptive_summary_json"],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
