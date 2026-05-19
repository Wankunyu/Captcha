from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import NormalDist
from typing import Any

import pandas as pd

from phase3_artifacts import (
    PASS_RATE_CONFIDENCE_SCHEMA_VERSION,
    PassRateConfidenceRow,
    write_csv,
    write_json,
)
from revision_artifacts import revision_run_dir
from visualize_results import CAPTCHAVisualizer


EXPERIMENTS = ("exp1", "exp2", "exp3", "exp4")
PASS_RATE_COLUMNS = [
    "experiment",
    "provider",
    "model",
    "provider_model",
    "task_type",
    "task_family",
    "n_attempts",
    "n_success",
    "pass_rate",
    "source_path",
]


def wilson_interval(
    n_success: int,
    n_attempts: int,
    confidence: float = 0.95,
) -> tuple[float | None, float | None]:
    if n_attempts == 0:
        return None, None
    if n_attempts < 0:
        raise ValueError("n_attempts must be non-negative")
    if n_success < 0 or n_success > n_attempts:
        raise ValueError("n_success must be between 0 and n_attempts")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")

    alpha = 1.0 - confidence
    z = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    n = float(n_attempts)
    p_hat = n_success / n
    z_squared = z**2
    denominator = 1.0 + z_squared / n
    center = (p_hat + z_squared / (2.0 * n)) / denominator
    half_width = (
        z
        * math.sqrt((p_hat * (1.0 - p_hat) + z_squared / (4.0 * n)) / n)
        / denominator
    )
    return max(0.0, center - half_width), min(1.0, center + half_width)


def load_experiment_pass_rates(results_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    root = Path(results_dir)
    for experiment in EXPERIMENTS:
        for csv_file in sorted((root / experiment).glob("**/results.csv")):
            df = pd.read_csv(csv_file)
            rows.extend(_normalize_result_file(df, csv_file, root, experiment))
    if not rows:
        return pd.DataFrame(columns=PASS_RATE_COLUMNS)
    return pd.DataFrame(rows, columns=PASS_RATE_COLUMNS).where(pd.notna(pd.DataFrame(rows)), None)


def build_pass_rate_confidence_rows(
    df: pd.DataFrame,
    run_id: str,
    underpowered_n: int = 20,
    confidence: float = 0.95,
) -> list[PassRateConfidenceRow]:
    if underpowered_n < 0:
        raise ValueError("underpowered_n must be non-negative")
    if df.empty:
        return []

    rows: list[PassRateConfidenceRow] = []
    task_groups = _aggregate_pass_rates(
        df,
        [
            "provider",
            "model",
            "provider_model",
            "experiment",
            "task_type",
            "task_family",
        ],
    )
    for record in task_groups:
        rows.append(
            _confidence_row(
                record,
                run_id=run_id,
                aggregation_level="task_type",
                underpowered_n=underpowered_n,
                confidence=confidence,
            )
        )

    family_groups = _aggregate_pass_rates(
        df,
        ["provider", "model", "provider_model", "experiment", "task_family"],
    )
    for record in family_groups:
        record["task_type"] = "__family__"
        rows.append(
            _confidence_row(
                record,
                run_id=run_id,
                aggregation_level="task_family",
                underpowered_n=underpowered_n,
                confidence=confidence,
            )
        )
    return rows


def write_pass_rate_outputs(
    rows: list[PassRateConfidenceRow],
    output_csv: Path,
    output_json: Path,
) -> tuple[Path, Path]:
    validated_rows = [
        row if isinstance(row, PassRateConfidenceRow) else PassRateConfidenceRow.model_validate(row)
        for row in rows
    ]
    csv_path = Path(output_csv)
    json_path = Path(output_json)
    write_csv(csv_path, PassRateConfidenceRow.model_fields, validated_rows)
    write_json(json_path, PASS_RATE_CONFIDENCE_SCHEMA_VERSION, validated_rows)
    return csv_path, json_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Phase 3 pass-rate confidence and threshold-sensitivity artifacts."
    )
    parser.add_argument("--results-dir", default="./results")
    parser.add_argument("--output-root", default="./results/revision")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--underpowered-n", type=int, default=20)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument(
        "--pass-rate-csv",
        default=None,
        help="Default: results/revision/<run_id>/pass_rate_confidence.csv",
    )
    parser.add_argument(
        "--pass-rate-json",
        default=None,
        help="Default: results/revision/<run_id>/pass_rate_confidence.json",
    )
    parser.add_argument(
        "--threshold-csv",
        default=None,
        help="Default: results/revision/<run_id>/threshold_sensitivity.csv",
    )
    parser.add_argument(
        "--threshold-json",
        default=None,
        help="Default: results/revision/<run_id>/threshold_sensitivity.json",
    )
    parser.add_argument("--adaptive-summary", default=None)
    parser.add_argument("--adaptive-comparison", default=None)
    parser.add_argument("--extended-validation-comparison", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        run_dir = revision_run_dir(args.output_root, args.run_id)
        pass_rate_csv = (
            Path(args.pass_rate_csv)
            if args.pass_rate_csv is not None
            else run_dir / "pass_rate_confidence.csv"
        )
        pass_rate_json = (
            Path(args.pass_rate_json)
            if args.pass_rate_json is not None
            else run_dir / "pass_rate_confidence.json"
        )
        df = load_experiment_pass_rates(Path(args.results_dir))
        rows = build_pass_rate_confidence_rows(
            df,
            run_id=args.run_id,
            underpowered_n=args.underpowered_n,
            confidence=args.confidence,
        )
        output_csv, output_json = write_pass_rate_outputs(
            rows,
            pass_rate_csv,
            pass_rate_json,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    print(
        json.dumps(
            {
                "pass_rate_row_count": len(rows),
                "pass_rate_csv": str(output_csv),
                "pass_rate_json": str(output_json),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _normalize_result_file(
    df: pd.DataFrame,
    csv_file: Path,
    results_dir: Path,
    experiment: str,
) -> list[dict[str, Any]]:
    provider, model = _provider_model_from_path(csv_file, results_dir, experiment)
    if experiment == "exp3":
        return _normalize_exp3(df, csv_file, experiment, provider, model)
    return _normalize_aggregate(df, csv_file, experiment, provider, model)


def _normalize_aggregate(
    df: pd.DataFrame,
    csv_file: Path,
    experiment: str,
    provider_from_path: str,
    model_from_path: str,
) -> list[dict[str, Any]]:
    required = {"n", "pass_at_1"}
    task_column = "task_type" if "task_type" in df.columns else "type"
    if task_column not in df.columns or not required.issubset(df.columns):
        raise ValueError(f"Unsupported {experiment} result schema: {csv_file}")

    rows: list[dict[str, Any]] = []
    for record in df.to_dict(orient="records"):
        provider = str(record.get("provider") or provider_from_path)
        model = str(record.get("model") or model_from_path)
        task_type = str(record[task_column])
        n_attempts = _to_int(record["n"])
        pass_rate = _to_float(record["pass_at_1"])
        n_success = int(round(pass_rate * n_attempts))
        rows.append(
            _pass_rate_record(
                experiment=experiment,
                provider=provider,
                model=model,
                task_type=task_type,
                n_attempts=n_attempts,
                n_success=n_success,
                pass_rate=pass_rate,
                source_path=csv_file,
            )
        )
    return rows


def _normalize_exp3(
    df: pd.DataFrame,
    csv_file: Path,
    experiment: str,
    provider_from_path: str,
    model_from_path: str,
) -> list[dict[str, Any]]:
    required = {"kind", "pass1"}
    task_column = "task_type" if "task_type" in df.columns else "type"
    if task_column not in df.columns or not required.issubset(df.columns):
        raise ValueError(f"Unsupported exp3 result schema: {csv_file}")

    summary = df[df["kind"] == "summary"].copy()
    if summary.empty:
        return []
    if "provider" not in summary.columns:
        summary["provider"] = provider_from_path
    if "model" not in summary.columns:
        summary["model"] = model_from_path

    grouped = (
        summary.groupby(["provider", "model", task_column], as_index=False)
        .agg(n_attempts=("pass1", "count"), n_success=("pass1", "sum"))
        .to_dict(orient="records")
    )
    rows: list[dict[str, Any]] = []
    for record in grouped:
        n_attempts = _to_int(record["n_attempts"])
        n_success = _to_int(record["n_success"])
        pass_rate = n_success / n_attempts if n_attempts else 0.0
        rows.append(
            _pass_rate_record(
                experiment=experiment,
                provider=str(record["provider"]),
                model=str(record["model"]),
                task_type=str(record[task_column]),
                n_attempts=n_attempts,
                n_success=n_success,
                pass_rate=pass_rate,
                source_path=csv_file,
            )
        )
    return rows


def _pass_rate_record(
    *,
    experiment: str,
    provider: str,
    model: str,
    task_type: str,
    n_attempts: int,
    n_success: int,
    pass_rate: float,
    source_path: Path,
) -> dict[str, Any]:
    return {
        "experiment": experiment,
        "provider": provider,
        "model": model,
        "provider_model": f"{provider}/{model}",
        "task_type": task_type,
        "task_family": CAPTCHAVisualizer.TASK_FAMILY.get(task_type, "Unmapped"),
        "n_attempts": n_attempts,
        "n_success": n_success,
        "pass_rate": pass_rate,
        "source_path": str(source_path),
    }


def _aggregate_pass_rates(df: pd.DataFrame, keys: list[str]) -> list[dict[str, Any]]:
    grouped: list[dict[str, Any]] = []
    for key_values, group in df.groupby(keys, dropna=False, sort=True):
        if not isinstance(key_values, tuple):
            key_values = (key_values,)
        record = dict(zip(keys, key_values))
        n_attempts = int(group["n_attempts"].astype(int).sum())
        n_success = int(group["n_success"].astype(int).sum())
        record["n_attempts"] = n_attempts
        record["n_success"] = n_success
        record["pass_rate"] = n_success / n_attempts if n_attempts else 0.0
        record["source_path"] = ";".join(sorted({str(path) for path in group["source_path"]}))
        grouped.append(record)
    return grouped


def _confidence_row(
    record: dict[str, Any],
    *,
    run_id: str,
    aggregation_level: str,
    underpowered_n: int,
    confidence: float,
) -> PassRateConfidenceRow:
    n_attempts = int(record["n_attempts"])
    n_success = int(record["n_success"])
    ci_low, ci_high = wilson_interval(n_success, n_attempts, confidence)
    return PassRateConfidenceRow(
        run_id=run_id,
        aggregation_level=aggregation_level,
        provider=str(record["provider"]),
        model=str(record["model"]),
        provider_model=str(record["provider_model"]),
        experiment=str(record["experiment"]),
        task_type=str(record["task_type"]),
        task_family=str(record["task_family"]),
        n_attempts=n_attempts,
        n_success=n_success,
        pass_rate=float(record["pass_rate"]),
        ci_method="wilson",
        ci_confidence=confidence,
        ci_low=ci_low,
        ci_high=ci_high,
        underpowered_threshold=underpowered_n,
        underpowered=n_attempts < underpowered_n,
        source_path=str(record["source_path"]),
    )


def _provider_model_from_path(
    csv_file: Path,
    results_dir: Path,
    experiment: str,
) -> tuple[str, str]:
    try:
        parts = csv_file.relative_to(results_dir).parts
    except ValueError:
        parts = csv_file.parts
    if len(parts) >= 3 and parts[0] == experiment:
        return parts[1], parts[2]
    return "", ""


def _to_float(value: object) -> float:
    return float(value)


def _to_int(value: object) -> int:
    return int(round(float(value)))


if __name__ == "__main__":
    raise SystemExit(main())
