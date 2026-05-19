from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from exp2_to_exp3_predict import predict_A_from_exp2, predict_q_from_exp2
from phase3_artifacts import (
    RETRY_CALIBRATION_SCHEMA_VERSION,
    RetryCalibrationRow,
    write_csv,
    write_json,
)
from revision_artifacts import revision_run_dir
from visualize_results import CAPTCHAVisualizer


COMPARISON_CONTRACT = (
    "task-type-primary; same-attempt-budget; "
    "structural-bottleneck-tags-explanatory"
)
_EMPTY_BASELINE_COLUMNS = [
    "provider",
    "model",
    "provider_model",
    "task_type",
    "task_family",
    "sample_count",
    "exp2_pass_at_1",
    "source_path",
]
_EMPTY_FIXED_COLUMNS = [
    "provider",
    "model",
    "provider_model",
    "task_type",
    "observed_fixed_retry_success",
    "fixed_retry_count",
    "source_path",
]
_EMPTY_ADAPTIVE_COLUMNS = [
    "provider",
    "model",
    "provider_model",
    "task_type",
    "attempt_budget_k",
    "observed_adaptive_compatible_success",
    "n_attempts",
    "n_success",
    "scientific_wrong_count",
    "protocol_failure_count",
    "infrastructure_failure_count",
    "has_failure_counts",
]

__all__ = [
    "build_retry_calibration_family_rows",
    "build_retry_calibration_rows",
    "load_adaptive_outcomes",
    "load_exp2_baseline",
    "load_fixed_retry_observations",
    "main",
    "predict_A_from_exp2",
    "predict_q_from_exp2",
    "write_retry_calibration",
]


def load_exp2_baseline(
    results_dir: Path, provider: str | None = None, model: str | None = None
) -> pd.DataFrame:
    frames = _load_experiment_results(Path(results_dir), "exp2")
    if not frames:
        return pd.DataFrame(columns=_EMPTY_BASELINE_COLUMNS)

    df = _filter_provider_model(pd.concat(frames, ignore_index=True), provider, model)
    if df.empty:
        return pd.DataFrame(columns=_EMPTY_BASELINE_COLUMNS)
    df = _normalize_task_column(df)
    pass_column = _first_existing_column(
        df, ["exp2_pass_at_1", "pass_at_1", "pass", "p_hat"]
    )
    if pass_column is None:
        raise ValueError("Exp2 results must include pass_at_1, pass, or p_hat")
    df["exp2_pass_at_1"] = df[pass_column].map(_to_float_or_none)
    if "n" in df.columns:
        df["sample_count"] = df["n"].map(lambda value: _to_int(value, default=0))
    elif "sample_count" in df.columns:
        df["sample_count"] = df["sample_count"].map(
            lambda value: _to_int(value, default=0)
        )
    else:
        df["sample_count"] = 1
    df["task_family"] = df["task_type"].map(_task_family)

    rows: list[dict[str, Any]] = []
    group_columns = ["provider", "model", "provider_model", "task_type", "task_family"]
    for key, group in df.groupby(group_columns, dropna=False):
        sample_count = int(group["sample_count"].sum())
        rows.append(
            {
                "provider": key[0],
                "model": key[1],
                "provider_model": key[2],
                "task_type": key[3],
                "task_family": key[4],
                "sample_count": sample_count,
                "exp2_pass_at_1": _weighted_mean(
                    group["exp2_pass_at_1"], group["sample_count"]
                ),
                "source_path": ";".join(sorted(set(group["source_path"].astype(str)))),
            }
        )
    return pd.DataFrame(rows, columns=_EMPTY_BASELINE_COLUMNS).where(pd.notna, None)


def load_fixed_retry_observations(
    results_dir: Path,
    attempt_budget_k: int,
    provider: str | None = None,
    model: str | None = None,
) -> pd.DataFrame:
    if attempt_budget_k < 1:
        raise ValueError("attempt_budget_k must be >= 1")
    frames = _load_experiment_results(Path(results_dir), "exp3")
    if not frames:
        return pd.DataFrame(columns=_EMPTY_FIXED_COLUMNS)

    df = _filter_provider_model(pd.concat(frames, ignore_index=True), provider, model)
    if df.empty:
        return pd.DataFrame(columns=_EMPTY_FIXED_COLUMNS)
    if "kind" in df.columns:
        df = df[df["kind"] == "summary"].copy()
    if df.empty:
        return pd.DataFrame(columns=_EMPTY_FIXED_COLUMNS)
    df = _normalize_task_column(df)
    if "attempt_idx" in df.columns:
        df = df[
            df["attempt_idx"].map(lambda value: _to_int(value, default=10**9))
            <= attempt_budget_k
        ].copy()
    if df.empty:
        return pd.DataFrame(columns=_EMPTY_FIXED_COLUMNS)
    pass_column = _first_existing_column(
        df, ["observed_fixed_retry_success", "pass1", "pass"]
    )
    if pass_column is None:
        raise ValueError("Exp3 results must include pass1 or pass")
    df["observed_fixed_retry_success"] = df[pass_column].map(_to_float_or_none)

    grouped = (
        df.groupby(["provider", "model", "provider_model", "task_type"], as_index=False)
        .agg(
            observed_fixed_retry_success=("observed_fixed_retry_success", "mean"),
            fixed_retry_count=("observed_fixed_retry_success", "count"),
            source_path=("source_path", lambda values: ";".join(sorted(set(values)))),
        )
        .where(pd.notna, None)
    )
    return grouped[_EMPTY_FIXED_COLUMNS]


def load_adaptive_outcomes(
    path: Path | None,
    attempt_budget_k: int,
    provider: str | None = None,
    model: str | None = None,
) -> pd.DataFrame:
    if attempt_budget_k < 1:
        raise ValueError("attempt_budget_k must be >= 1")
    if path is None:
        return pd.DataFrame(columns=_EMPTY_ADAPTIVE_COLUMNS)

    adaptive_path = Path(path)
    if adaptive_path.suffix.lower() == ".json":
        with adaptive_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        rows = payload.get("rows", payload if isinstance(payload, list) else [])
        df = pd.DataFrame(rows)
    else:
        df = pd.read_csv(adaptive_path)
    if df.empty:
        return pd.DataFrame(columns=_EMPTY_ADAPTIVE_COLUMNS)

    failure_columns = [
        "scientific_wrong_count",
        "protocol_failure_count",
        "infrastructure_failure_count",
    ]
    has_failure_counts = all(column in df.columns for column in failure_columns)
    for column in ["n_attempts", "n_success", *failure_columns]:
        if column not in df.columns:
            df[column] = 0
        df[column] = df[column].map(lambda value: _to_int(value, default=0))
    if "success_rate" not in df.columns:
        df["success_rate"] = df.apply(
            lambda row: row["n_success"] / row["n_attempts"]
            if row["n_attempts"] > 0
            else None,
            axis=1,
        )
    df["observed_adaptive_compatible_success"] = df["success_rate"].map(
        _to_float_or_none
    )
    if "provider_model" not in df.columns:
        df["provider_model"] = df.apply(
            lambda row: f"{row.get('provider')}/{row.get('model')}", axis=1
        )
    df = _filter_provider_model(df, provider, model)
    if "attempt_budget_k" in df.columns:
        df = df[
            df["attempt_budget_k"].map(lambda value: _to_int(value, default=-1))
            == attempt_budget_k
        ].copy()
    else:
        df["attempt_budget_k"] = attempt_budget_k
    if df.empty:
        return pd.DataFrame(columns=_EMPTY_ADAPTIVE_COLUMNS)
    df["has_failure_counts"] = has_failure_counts

    grouped_rows: list[dict[str, Any]] = []
    group_columns = ["provider", "model", "provider_model", "task_type", "attempt_budget_k"]
    for key, group in df.groupby(group_columns, dropna=False):
        n_attempts = int(group["n_attempts"].sum())
        n_success = int(group["n_success"].sum())
        grouped_rows.append(
            {
                "provider": key[0],
                "model": key[1],
                "provider_model": key[2],
                "task_type": key[3],
                "attempt_budget_k": int(key[4]),
                "observed_adaptive_compatible_success": (
                    n_success / n_attempts
                    if n_attempts > 0
                    else _mean_or_none(group["observed_adaptive_compatible_success"])
                ),
                "n_attempts": n_attempts,
                "n_success": n_success,
                "scientific_wrong_count": int(group["scientific_wrong_count"].sum()),
                "protocol_failure_count": int(group["protocol_failure_count"].sum()),
                "infrastructure_failure_count": int(
                    group["infrastructure_failure_count"].sum()
                ),
                "has_failure_counts": bool(group["has_failure_counts"].all()),
            }
        )
    return pd.DataFrame(grouped_rows, columns=_EMPTY_ADAPTIVE_COLUMNS).where(
        pd.notna, None
    )


def build_retry_calibration_rows(
    exp2_df: pd.DataFrame,
    fixed_retry_df: pd.DataFrame,
    adaptive_df: pd.DataFrame,
    *,
    run_id: str,
    attempt_budget_k: int,
) -> list[RetryCalibrationRow]:
    if attempt_budget_k < 1:
        raise ValueError("attempt_budget_k must be >= 1")
    if exp2_df.empty:
        return []

    merged = exp2_df.merge(
        fixed_retry_df,
        on=["provider", "model", "provider_model", "task_type"],
        how="left",
        suffixes=("", "_fixed"),
    )
    merged = merged.merge(
        adaptive_df,
        on=["provider", "model", "provider_model", "task_type"],
        how="left",
        suffixes=("", "_adaptive"),
    )

    rows: list[RetryCalibrationRow] = []
    for record in merged.to_dict(orient="records"):
        sample_count = _to_int(record.get("sample_count"), default=0)
        exp2_pass_at_1 = _to_float_or_none(record.get("exp2_pass_at_1"))
        bernoulli_success_at_k = (
            predict_q_from_exp2(exp2_pass_at_1, sample_count, attempt_budget_k)
            if exp2_pass_at_1 is not None
            else None
        )
        observed_fixed = _to_float_or_none(
            record.get("observed_fixed_retry_success")
        )
        observed_adaptive = _to_float_or_none(
            record.get("observed_adaptive_compatible_success")
        )
        n_success = _to_int(record.get("n_success"), default=0)
        scientific_wrong_count = _to_int(
            record.get("scientific_wrong_count"), default=0
        )
        protocol_failure_count = _to_int(
            record.get("protocol_failure_count"), default=0
        )
        infrastructure_failure_count = _to_int(
            record.get("infrastructure_failure_count"), default=0
        )
        has_failure_counts = bool(record.get("has_failure_counts") is True)
        rows.append(
            RetryCalibrationRow(
                run_id=run_id,
                provider=str(record["provider"]),
                model=str(record["model"]),
                provider_model=str(record["provider_model"]),
                task_type=str(record["task_type"]),
                task_family=str(record.get("task_family") or _task_family(record["task_type"])),
                exp2_pass_at_1=exp2_pass_at_1,
                attempt_budget_k=attempt_budget_k,
                bernoulli_success_at_k=bernoulli_success_at_k,
                observed_fixed_retry_success=observed_fixed,
                observed_adaptive_compatible_success=observed_adaptive,
                signed_error_fixed_retry=_signed_error(
                    observed_fixed, bernoulli_success_at_k
                ),
                absolute_error_fixed_retry=_absolute_error(
                    observed_fixed, bernoulli_success_at_k
                ),
                signed_error_adaptive=_signed_error(
                    observed_adaptive, bernoulli_success_at_k
                ),
                absolute_error_adaptive=_absolute_error(
                    observed_adaptive, bernoulli_success_at_k
                ),
                sample_count=sample_count,
                scientific_wrong_count=scientific_wrong_count,
                protocol_failure_count=protocol_failure_count,
                infrastructure_failure_count=infrastructure_failure_count,
                raw_observed_rate=_raw_observed_rate(
                    has_failure_counts=has_failure_counts,
                    n_success=n_success,
                    scientific_wrong_count=scientific_wrong_count,
                    protocol_failure_count=protocol_failure_count,
                    infrastructure_failure_count=infrastructure_failure_count,
                    observed_adaptive=observed_adaptive,
                    observed_fixed=observed_fixed,
                ),
                scientific_rate=_scientific_rate(
                    has_failure_counts=has_failure_counts,
                    n_success=n_success,
                    scientific_wrong_count=scientific_wrong_count,
                ),
                comparison_contract=COMPARISON_CONTRACT,
            )
        )
    return rows


def build_retry_calibration_family_rows(
    rows: list[RetryCalibrationRow],
) -> list[RetryCalibrationRow]:
    groups: dict[tuple[str, str, str, str, int, str], list[RetryCalibrationRow]] = {}
    for row in rows:
        key = (
            row.provider,
            row.model,
            row.provider_model,
            row.task_family,
            row.attempt_budget_k,
            row.run_id,
        )
        groups.setdefault(key, []).append(row)

    family_rows: list[RetryCalibrationRow] = []
    for key, group_rows in sorted(groups.items()):
        provider, model, provider_model, task_family, attempt_budget_k, run_id = key
        scientific_wrong_count = sum(row.scientific_wrong_count for row in group_rows)
        protocol_failure_count = sum(row.protocol_failure_count for row in group_rows)
        infrastructure_failure_count = sum(
            row.infrastructure_failure_count for row in group_rows
        )
        family_rows.append(
            RetryCalibrationRow(
                run_id=run_id,
                provider=provider,
                model=model,
                provider_model=provider_model,
                task_type="__family__",
                task_family=task_family,
                exp2_pass_at_1=_row_mean(group_rows, "exp2_pass_at_1"),
                attempt_budget_k=attempt_budget_k,
                bernoulli_success_at_k=_row_mean(
                    group_rows, "bernoulli_success_at_k"
                ),
                observed_fixed_retry_success=_row_mean(
                    group_rows, "observed_fixed_retry_success"
                ),
                observed_adaptive_compatible_success=_row_mean(
                    group_rows, "observed_adaptive_compatible_success"
                ),
                signed_error_fixed_retry=_row_mean(
                    group_rows, "signed_error_fixed_retry"
                ),
                absolute_error_fixed_retry=_row_mean(
                    group_rows, "absolute_error_fixed_retry"
                ),
                signed_error_adaptive=_row_mean(group_rows, "signed_error_adaptive"),
                absolute_error_adaptive=_row_mean(
                    group_rows, "absolute_error_adaptive"
                ),
                sample_count=sum(row.sample_count for row in group_rows),
                scientific_wrong_count=scientific_wrong_count,
                protocol_failure_count=protocol_failure_count,
                infrastructure_failure_count=infrastructure_failure_count,
                raw_observed_rate=_row_mean(group_rows, "raw_observed_rate"),
                scientific_rate=_row_mean(group_rows, "scientific_rate"),
                comparison_contract=COMPARISON_CONTRACT,
            )
        )
    return family_rows


def write_retry_calibration(
    rows: list[RetryCalibrationRow],
    family_rows: list[RetryCalibrationRow],
    output_csv: Path,
    output_json: Path,
    family_csv: Path,
    family_json: Path,
) -> tuple[Path, Path, Path, Path]:
    validated_rows = [
        row if isinstance(row, RetryCalibrationRow) else RetryCalibrationRow.model_validate(row)
        for row in rows
    ]
    validated_family_rows = [
        row if isinstance(row, RetryCalibrationRow) else RetryCalibrationRow.model_validate(row)
        for row in family_rows
    ]
    write_csv(Path(output_csv), RetryCalibrationRow.model_fields, validated_rows)
    write_json(Path(output_json), RETRY_CALIBRATION_SCHEMA_VERSION, validated_rows)
    write_csv(Path(family_csv), RetryCalibrationRow.model_fields, validated_family_rows)
    write_json(Path(family_json), RETRY_CALIBRATION_SCHEMA_VERSION, validated_family_rows)
    return Path(output_csv), Path(output_json), Path(family_csv), Path(family_json)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build retry calibration artifacts comparing Bernoulli Success@k "
            "against fixed-retry and adaptive-compatible observations."
        )
    )
    parser.add_argument("--results-dir", default="./results")
    parser.add_argument("--adaptive-summary", default=None)
    parser.add_argument("--output-root", default="./results/revision")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--attempt-budget-k", type=int, required=True)
    parser.add_argument("--provider", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--output-csv", default=None)
    parser.add_argument("--output-json", default=None)
    parser.add_argument("--family-csv", default=None)
    parser.add_argument("--family-json", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.attempt_budget_k < 1:
        parser.error("attempt_budget_k must be >= 1")
    try:
        output_csv, output_json, family_csv, family_json = _resolve_output_paths(args)
        exp2 = load_exp2_baseline(
            Path(args.results_dir), provider=args.provider, model=args.model
        )
        fixed = load_fixed_retry_observations(
            Path(args.results_dir),
            attempt_budget_k=args.attempt_budget_k,
            provider=args.provider,
            model=args.model,
        )
        adaptive = load_adaptive_outcomes(
            Path(args.adaptive_summary) if args.adaptive_summary else None,
            attempt_budget_k=args.attempt_budget_k,
            provider=args.provider,
            model=args.model,
        )
        rows = build_retry_calibration_rows(
            exp2,
            fixed,
            adaptive,
            run_id=args.run_id,
            attempt_budget_k=args.attempt_budget_k,
        )
        if not rows:
            raise ValueError("Exp2 baseline rows not found after filtering")
        family_rows = build_retry_calibration_family_rows(rows)
    except ValueError as exc:
        parser.error(str(exc))

    paths = write_retry_calibration(
        rows, family_rows, output_csv, output_json, family_csv, family_json
    )
    print(
        json.dumps(
            {
                "row_count": len(rows),
                "family_row_count": len(family_rows),
                "output_csv": str(paths[0]),
                "output_json": str(paths[1]),
                "family_csv": str(paths[2]),
                "family_json": str(paths[3]),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _resolve_output_paths(args: argparse.Namespace) -> tuple[Path, Path, Path, Path]:
    run_dir = revision_run_dir(args.output_root, args.run_id)
    return (
        Path(args.output_csv) if args.output_csv else run_dir / "retry_calibration.csv",
        Path(args.output_json) if args.output_json else run_dir / "retry_calibration.json",
        Path(args.family_csv)
        if args.family_csv
        else run_dir / "retry_calibration_by_family.csv",
        Path(args.family_json)
        if args.family_json
        else run_dir / "retry_calibration_by_family.json",
    )


def _load_experiment_results(results_dir: Path, experiment: str) -> list[pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    for csv_path in sorted((results_dir / experiment).glob("**/results.csv")):
        parts = csv_path.relative_to(results_dir).parts
        provider = parts[1] if len(parts) > 1 else ""
        model = parts[2] if len(parts) > 2 else ""
        df = pd.read_csv(csv_path)
        if df.empty:
            continue
        if "provider" not in df.columns:
            df["provider"] = provider
        if "model" not in df.columns:
            df["model"] = model
        if "provider_model" not in df.columns:
            df["provider_model"] = df.apply(
                lambda row: f"{row.get('provider')}/{row.get('model')}", axis=1
            )
        df["source_path"] = str(csv_path)
        frames.append(df)
    return frames


def _normalize_task_column(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    if "task_type" not in normalized.columns and "type" in normalized.columns:
        normalized = normalized.rename(columns={"type": "task_type"})
    if "task_type" not in normalized.columns:
        raise ValueError("results must include task_type or type")
    return normalized


def _filter_provider_model(
    df: pd.DataFrame, provider: str | None, model: str | None
) -> pd.DataFrame:
    filtered = df.copy()
    if provider is not None and "provider" in filtered.columns:
        filtered = filtered[filtered["provider"] == provider]
    if model is not None:
        if "provider_model" in filtered.columns:
            filtered = filtered[
                (filtered["model"] == model) | (filtered["provider_model"] == model)
            ]
        elif "model" in filtered.columns:
            filtered = filtered[filtered["model"] == model]
    return filtered.copy()


def _first_existing_column(df: pd.DataFrame, columns: list[str]) -> str | None:
    for column in columns:
        if column in df.columns:
            return column
    return None


def _task_family(task_type: object) -> str:
    return CAPTCHAVisualizer.TASK_FAMILY.get(str(task_type), "Unmapped")


def _weighted_mean(values: Iterable[object], weights: Iterable[object]) -> float | None:
    pairs = [
        (_to_float_or_none(value), _to_int(weight, default=0))
        for value, weight in zip(values, weights, strict=False)
    ]
    weighted_pairs = [(value, weight) for value, weight in pairs if value is not None]
    total_weight = sum(weight for _, weight in weighted_pairs)
    if total_weight > 0:
        return sum(value * weight for value, weight in weighted_pairs) / total_weight
    return _mean_or_none(value for value, _ in weighted_pairs)


def _mean_or_none(values: Iterable[object]) -> float | None:
    numeric = [_to_float_or_none(value) for value in values]
    numeric = [value for value in numeric if value is not None]
    if not numeric:
        return None
    return sum(numeric) / len(numeric)


def _row_mean(rows: list[RetryCalibrationRow], field_name: str) -> float | None:
    return _mean_or_none(getattr(row, field_name) for row in rows)


def _signed_error(observed: float | None, predicted: float | None) -> float | None:
    if observed is None or predicted is None:
        return None
    return observed - predicted


def _absolute_error(observed: float | None, predicted: float | None) -> float | None:
    signed = _signed_error(observed, predicted)
    return None if signed is None else abs(signed)


def _raw_observed_rate(
    *,
    has_failure_counts: bool,
    n_success: int,
    scientific_wrong_count: int,
    protocol_failure_count: int,
    infrastructure_failure_count: int,
    observed_adaptive: float | None,
    observed_fixed: float | None,
) -> float | None:
    if observed_adaptive is not None:
        if has_failure_counts:
            total = (
                n_success
                + scientific_wrong_count
                + protocol_failure_count
                + infrastructure_failure_count
            )
            return n_success / total if total > 0 else None
        return observed_adaptive
    return observed_fixed


def _scientific_rate(
    *, has_failure_counts: bool, n_success: int, scientific_wrong_count: int
) -> float | None:
    if not has_failure_counts:
        return None
    denominator = n_success + scientific_wrong_count
    if denominator <= 0:
        return None
    return n_success / denominator


def _is_null(value: object) -> bool:
    return value is None or value == "" or (isinstance(value, float) and pd.isna(value))


def _to_float_or_none(value: object) -> float | None:
    if _is_null(value) or pd.isna(value):
        return None
    return float(value)


def _to_int(value: object, *, default: int) -> int:
    maybe_float = _to_float_or_none(value)
    if maybe_float is None:
        return default
    return int(round(maybe_float))


if __name__ == "__main__":
    raise SystemExit(main())
