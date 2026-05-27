import argparse
import csv
import json
from pathlib import Path
from typing import Any

import yaml

from .phase3_artifacts import (
    DATASET_SCOPE_SCHEMA_VERSION,
    DatasetScopeAuditRow,
    write_csv,
    write_json,
)
from .revision_artifacts import revision_run_dir
from .run_eval import DATASET_DIR_ALIASES, SUPPORTED_TYPES, TASK_ALIASES
from .visualize_results import CAPTCHAVisualizer


EXPERIMENTS = ("exp1", "exp2", "exp3", "exp4")
HOLD_BUTTON_TASK = "Hold_Button(Not Used)"
SLIDE_PUZZLE_TASK = "Slide_Puzzle(Not Used)"
REMOVED_TASK_TYPES = [HOLD_BUTTON_TASK, SLIDE_PUZZLE_TASK]
HOLD_BUTTON_REASON = (
    "temporal press-and-hold interaction requires duration/hold-time behavior outside "
    "static answer schemas"
)
SLIDE_PUZZLE_REASON = (
    "drag/slider composition requires component-image movement and target-position "
    "tolerance outside static answer schemas"
)


def load_ground_truth_count(path: Path) -> int:
    raw = path.read_text(encoding="utf-8")
    if raw.strip().startswith("version https://git-lfs.github.com/spec/v1"):
        raise RuntimeError(f"{path} is a Git LFS pointer; materialize dataset files first")
    payload = json.loads(raw)
    if isinstance(payload, dict | list):
        return len(payload)
    raise ValueError(f"ground_truth.json must be a mapping or list: {path}")


def _canonical_task_type(task_type: str) -> str:
    return TASK_ALIASES.get(task_type, task_type)


def _task_family(task_type: str) -> str:
    return CAPTCHAVisualizer.TASK_FAMILY.get(task_type, "Unmapped")


def _row_count(record: dict[str, str]) -> int:
    value = record.get("n")
    if value not in (None, ""):
        try:
            return max(int(float(value)), 0)
        except ValueError:
            return 1
    return 1


def collect_evaluated_counts(results_dir: Path) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = {}
    for experiment in EXPERIMENTS:
        experiment_dir = results_dir / experiment
        if not experiment_dir.exists():
            continue
        for csv_file in experiment_dir.rglob("results.csv"):
            with csv_file.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                for record in reader:
                    raw_task_type = record.get("task_type") or record.get("type")
                    if not raw_task_type:
                        continue
                    task_type = _canonical_task_type(str(raw_task_type))
                    key = (experiment, task_type)
                    counts[key] = counts.get(key, 0) + _row_count(record)
    return counts


def _load_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _prompt_keys(path: Path = Path("prompts_optimized.yaml")) -> set[str] | None:
    payload = _load_yaml(path)
    if payload is None:
        return None
    raw_types = payload.get("types") if isinstance(payload, dict) else {}
    if isinstance(raw_types, dict):
        return {_canonical_task_type(str(task_type)) for task_type in raw_types}
    return set()


def _few_shot_keys(path: Path = Path("few_shot_examples.yaml")) -> set[str] | None:
    payload = _load_yaml(path)
    if payload is None:
        return None
    if isinstance(payload, dict):
        return {_canonical_task_type(str(task_type)) for task_type in payload}
    return set()


def _key_status(task_type: str, keys: set[str] | None) -> str:
    if keys is None:
        return "not_applicable"
    return "present" if task_type in keys else "missing"


def _experiment_count_fields(
    counts: dict[tuple[str, str], int],
    task_type: str,
) -> dict[str, int]:
    return {
        f"evaluated_n_{experiment}": counts.get((experiment, task_type), 0)
        for experiment in EXPERIMENTS
    }


def _supported_row(
    *,
    run_id: str,
    task_type: str,
    dataset_dir: str,
    dataset_sample_count: int,
    evaluated_counts: dict[tuple[str, str], int],
    underpowered_n: int,
    prompt_keys: set[str] | None,
    few_shot_keys: set[str] | None,
) -> DatasetScopeAuditRow:
    count_fields = _experiment_count_fields(evaluated_counts, task_type)
    total_evaluated = sum(count_fields.values())
    underpowered = dataset_sample_count < underpowered_n
    if underpowered:
        scope_status = "underpowered"
        reason = (
            f"dataset sample count {dataset_sample_count} is below underpowered "
            f"threshold {underpowered_n}"
        )
    elif total_evaluated > 0:
        scope_status = "included"
        reason = "supported dataset with evaluated rows in selected result files"
    else:
        scope_status = "excluded"
        reason = "dataset-supported but absent from selected result files"

    support_status = (
        "dataset_supported_not_evaluated"
        if scope_status == "excluded"
        else "supported"
    )
    return DatasetScopeAuditRow(
        run_id=run_id,
        task_type=task_type,
        task_family=_task_family(task_type),
        dataset_dir=dataset_dir,
        scope_status=scope_status,
        support_status=support_status,
        pipeline_compatibility="compatible_static_answer",
        dataset_sample_count=dataset_sample_count,
        underpowered_threshold=underpowered_n,
        underpowered=underpowered,
        prompt_key_status=_key_status(task_type, prompt_keys),
        few_shot_key_status=_key_status(task_type, few_shot_keys),
        answer_format_notes="static answer schema from ground_truth.json",
        normalization_notes="task name canonicalized through TASK_ALIASES where needed",
        removal_decision="kept",
        reason=reason,
        **count_fields,
    )


def _removed_row(
    *,
    run_id: str,
    task_type: str,
    dataset_sample_count: int,
    underpowered_n: int,
) -> DatasetScopeAuditRow:
    if task_type == HOLD_BUTTON_TASK:
        compatibility = "incompatible_temporal_hold"
        reason = HOLD_BUTTON_REASON
    elif task_type == SLIDE_PUZZLE_TASK:
        compatibility = "incompatible_slider_drag"
        reason = SLIDE_PUZZLE_REASON
    else:
        raise ValueError(f"Unknown removed task type: {task_type}")
    return DatasetScopeAuditRow(
        run_id=run_id,
        task_type=task_type,
        task_family="Removed/Incompatible",
        dataset_dir=task_type,
        scope_status="incompatible",
        support_status="removed_not_used",
        pipeline_compatibility=compatibility,
        dataset_sample_count=dataset_sample_count,
        evaluated_n_exp1=0,
        evaluated_n_exp2=0,
        evaluated_n_exp3=0,
        evaluated_n_exp4=0,
        underpowered_threshold=underpowered_n,
        underpowered=dataset_sample_count < underpowered_n,
        prompt_key_status="not_applicable",
        few_shot_key_status="not_applicable",
        answer_format_notes="outside current static answer schema",
        normalization_notes="not normalized into the active static pipeline",
        removal_decision="removed from active evaluation",
        reason=reason,
    )


def _unsupported_row(
    *,
    run_id: str,
    task_type: str,
    dataset_sample_count: int,
    underpowered_n: int,
) -> DatasetScopeAuditRow:
    return DatasetScopeAuditRow(
        run_id=run_id,
        task_type=task_type,
        task_family="Unmapped",
        dataset_dir=task_type,
        scope_status="excluded",
        support_status="unsupported",
        pipeline_compatibility="unknown",
        dataset_sample_count=dataset_sample_count,
        evaluated_n_exp1=0,
        evaluated_n_exp2=0,
        evaluated_n_exp3=0,
        evaluated_n_exp4=0,
        underpowered_threshold=underpowered_n,
        underpowered=dataset_sample_count < underpowered_n,
        prompt_key_status="not_applicable",
        few_shot_key_status="not_applicable",
        answer_format_notes="unsupported dataset directory",
        normalization_notes="no active task alias or scorer contract",
        removal_decision="excluded from active evaluation",
        reason="unsupported dataset directory is not part of SUPPORTED_TYPES",
    )


def build_dataset_scope_rows(
    dataset_root: Path,
    results_dir: Path,
    run_id: str,
    underpowered_n: int = 20,
) -> list[DatasetScopeAuditRow]:
    evaluated_counts = collect_evaluated_counts(results_dir)
    prompt_keys = _prompt_keys()
    few_shot_keys = _few_shot_keys()
    rows: list[DatasetScopeAuditRow] = []

    for ground_truth_path in sorted(dataset_root.glob("*/ground_truth.json")):
        dataset_dir_name = ground_truth_path.parent.name
        task_type = _canonical_task_type(dataset_dir_name)
        dataset_sample_count = load_ground_truth_count(ground_truth_path)
        if dataset_dir_name in REMOVED_TASK_TYPES:
            rows.append(
                _removed_row(
                    run_id=run_id,
                    task_type=dataset_dir_name,
                    dataset_sample_count=dataset_sample_count,
                    underpowered_n=underpowered_n,
                )
            )
            continue
        if task_type in SUPPORTED_TYPES:
            dataset_dir = DATASET_DIR_ALIASES.get(task_type, dataset_dir_name)
            rows.append(
                _supported_row(
                    run_id=run_id,
                    task_type=task_type,
                    dataset_dir=dataset_dir,
                    dataset_sample_count=dataset_sample_count,
                    evaluated_counts=evaluated_counts,
                    underpowered_n=underpowered_n,
                    prompt_keys=prompt_keys,
                    few_shot_keys=few_shot_keys,
                )
            )
            continue
        rows.append(
            _unsupported_row(
                run_id=run_id,
                task_type=dataset_dir_name,
                dataset_sample_count=dataset_sample_count,
                underpowered_n=underpowered_n,
            )
        )
    return rows


def write_dataset_scope_audit(
    rows: list[DatasetScopeAuditRow],
    output_csv: Path,
    output_json: Path,
) -> tuple[Path, Path]:
    write_csv(output_csv, DatasetScopeAuditRow.model_fields, rows)
    write_json(output_json, DATASET_SCOPE_SCHEMA_VERSION, rows)
    return output_csv, output_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an offline dataset scope audit for revision artifacts."
    )
    parser.add_argument("--dataset-root", default="./captcha_data")
    parser.add_argument("--results-dir", default="./results")
    parser.add_argument("--output-root", default="./results/local_runs")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--underpowered-n", type=int, default=20)
    parser.add_argument("--output-csv", default=None)
    parser.add_argument("--output-json", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        run_dir = revision_run_dir(args.output_root, args.run_id)
        output_csv = (
            Path(args.output_csv)
            if args.output_csv
            else run_dir / "dataset_scope_audit.csv"
        )
        output_json = (
            Path(args.output_json)
            if args.output_json
            else run_dir / "dataset_scope_audit.json"
        )
        rows = build_dataset_scope_rows(
            dataset_root=Path(args.dataset_root),
            results_dir=Path(args.results_dir),
            run_id=args.run_id,
            underpowered_n=args.underpowered_n,
        )
        csv_path, json_path = write_dataset_scope_audit(rows, output_csv, output_json)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    print(
        json.dumps(
            {
                "row_count": len(rows),
                "output_csv": str(csv_path),
                "output_json": str(json_path),
                "underpowered_threshold": args.underpowered_n,
                "removed_task_types": REMOVED_TASK_TYPES,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
