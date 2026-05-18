from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from adaptive_artifacts import (
    ADAPTIVE_COMPARISON_SCHEMA_VERSION,
    AdaptiveComparisonRow,
)
from exp2_to_exp3_predict import predict_A_from_exp2, predict_q_from_exp2
from visualize_results import CAPTCHAVisualizer


_LEGACY_COLUMNS = [
    "provider",
    "model",
    "provider_model",
    "task_type",
    "exp2_n",
    "exp2_pass_at_1",
    "fixed_retry_observed_success",
    "fixed_retry_attempts_to_success",
    "fixed_retry_cumulative_latency_ms",
]


def load_legacy_results(
    results_dir: str, provider: str | None = None, model: str | None = None
) -> pd.DataFrame:
    viz = CAPTCHAVisualizer(results_dir=results_dir)
    if viz.data.empty:
        return pd.DataFrame(columns=_LEGACY_COLUMNS)

    df = viz.data.copy()
    df = _filter_provider_model(df, provider=provider, model=model)
    exp2 = _normalize_exp2(df)
    fixed = _normalize_fixed_retry(df)
    if exp2.empty:
        return pd.DataFrame(columns=_LEGACY_COLUMNS)
    if fixed.empty:
        for column in (
            "fixed_retry_observed_success",
            "fixed_retry_attempts_to_success",
            "fixed_retry_cumulative_latency_ms",
        ):
            exp2[column] = None
        return exp2[_LEGACY_COLUMNS]

    merged = exp2.merge(
        fixed,
        on=["provider", "model", "provider_model", "task_type"],
        how="left",
    )
    return merged[_LEGACY_COLUMNS].where(pd.notna(merged), None)


def load_adaptive_summary(path: str | Path) -> pd.DataFrame:
    summary_path = Path(path)
    if summary_path.suffix.lower() == ".json":
        with summary_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        rows = payload.get("rows", payload if isinstance(payload, list) else [])
        return pd.DataFrame(rows)
    return pd.read_csv(summary_path).where(pd.notna(pd.read_csv(summary_path)), None)


def build_comparison_rows(
    *,
    results_dir: str,
    adaptive_summary_path: str | Path,
    run_id: str,
    provider: str | None = None,
    model: str | None = None,
    attempt_budget_k: int,
    cutoff: float = 0.40,
    borderline_margin: float = 0.05,
) -> list[AdaptiveComparisonRow]:
    if attempt_budget_k < 1:
        raise ValueError("attempt_budget_k must be >= 1")
    legacy = load_legacy_results(results_dir, provider=provider, model=model)
    if legacy.empty:
        raise ValueError("Exp2 results not found after filtering")

    adaptive = load_adaptive_summary(adaptive_summary_path)
    adaptive = _filter_adaptive_summary(
        adaptive,
        run_id=run_id,
        provider=provider,
        model=model,
        attempt_budget_k=attempt_budget_k,
    )
    if adaptive.empty:
        raise ValueError("Adaptive summary rows not found after filtering")

    merged = legacy.merge(
        adaptive,
        on=["provider", "model", "task_type"],
        how="inner",
        suffixes=("", "_adaptive"),
    )
    if merged.empty:
        raise ValueError("No overlapping Exp2 and adaptive rows after filtering")

    rows: list[AdaptiveComparisonRow] = []
    for record in merged.to_dict(orient="records"):
        exp2_n = _to_int(record.get("exp2_n"), default=0)
        exp2_pass_at_1 = _to_float_or_none(record.get("exp2_pass_at_1"))
        bernoulli_success = None
        bernoulli_attempts = None
        if exp2_pass_at_1 is not None:
            bernoulli_success = predict_q_from_exp2(
                exp2_pass_at_1, exp2_n, attempt_budget_k
            )
            bernoulli_attempts = predict_A_from_exp2(
                exp2_pass_at_1, exp2_n, attempt_budget_k
            )

        n_success = _to_int(record.get("n_success"), default=0)
        success_rate = _to_float_or_none(record.get("success_rate"))
        adaptive_observed_success = n_success > 0 or bool(
            success_rate is not None and success_rate > 0
        )
        rows.append(
            AdaptiveComparisonRow(
                run_id=run_id,
                provider=str(record["provider"]),
                model=str(record["model"]),
                provider_model=str(record.get("provider_model") or ""),
                task_type=str(record["task_type"]),
                attempt_budget_k=attempt_budget_k,
                exp2_n=exp2_n,
                exp2_pass_at_1=exp2_pass_at_1,
                bernoulli_success_at_k=bernoulli_success,
                bernoulli_expected_attempts=bernoulli_attempts,
                fixed_retry_observed_success=_to_bool_or_none(
                    record.get("fixed_retry_observed_success")
                ),
                fixed_retry_attempts_to_success=_to_int_or_none(
                    record.get("fixed_retry_attempts_to_success")
                ),
                fixed_retry_cumulative_latency_ms=_to_float_or_none(
                    record.get("fixed_retry_cumulative_latency_ms")
                ),
                adaptive_observed_success=adaptive_observed_success,
                adaptive_attempts_to_success=_to_int_or_none(
                    record.get("attempts_to_success")
                ),
                adaptive_cumulative_latency_ms=_to_float(
                    record.get("cumulative_latency_ms")
                ),
                adaptive_solve_request_count=_to_int(
                    record.get("solve_request_count"), default=0
                ),
                adaptive_reflection_request_count=_to_int(
                    record.get("reflection_request_count"), default=0
                ),
                adaptive_cumulative_cost_usd=_to_float(
                    record.get("cumulative_cost_usd")
                ),
                scientific_wrong_count=_to_int(
                    record.get("scientific_wrong_count"), default=0
                ),
                protocol_failure_count=_to_int(
                    record.get("protocol_failure_count"), default=0
                ),
                infrastructure_failure_count=_to_int(
                    record.get("infrastructure_failure_count"), default=0
                ),
                baseline_label="",
                adaptive_label="",
                classification_change="",
                cutoff_note="",
                structural_bottleneck_tags=[],
                confidence_interval_low=_to_float_or_none(
                    record.get("confidence_interval_low")
                ),
                confidence_interval_high=_to_float_or_none(
                    record.get("confidence_interval_high")
                ),
                confidence_interval_not_applicable_reason=_to_str_or_none(
                    record.get("confidence_interval_not_applicable_reason")
                ),
            )
        )
    return rows


def write_comparison(
    rows: list[AdaptiveComparisonRow],
    output_csv: str | Path,
    output_json: str | Path,
) -> tuple[Path, Path]:
    validated_rows = [
        row if isinstance(row, AdaptiveComparisonRow) else AdaptiveComparisonRow.model_validate(row)
        for row in rows
    ]
    csv_path = Path(output_csv)
    json_path = Path(output_json)
    _write_csv(csv_path, AdaptiveComparisonRow.model_fields, validated_rows)
    _write_json(
        json_path,
        ADAPTIVE_COMPARISON_SCHEMA_VERSION,
        [row.model_dump(mode="json") for row in validated_rows],
    )
    return csv_path, json_path


def _normalize_exp2(df: pd.DataFrame) -> pd.DataFrame:
    exp2 = df[df["experiment"] == "exp2"].copy()
    if exp2.empty:
        return pd.DataFrame(columns=_LEGACY_COLUMNS[:6])
    if "n" not in exp2.columns:
        exp2["n"] = 1
    return exp2.groupby(
        ["provider", "model", "provider_model", "task_type"], as_index=False
    ).agg(
        exp2_n=("n", "max"),
        exp2_pass_at_1=("pass", "mean"),
    )


def _normalize_fixed_retry(df: pd.DataFrame) -> pd.DataFrame:
    exp3 = df[df["experiment"] == "exp3"].copy()
    if exp3.empty:
        return pd.DataFrame(
            columns=[
                "provider",
                "model",
                "provider_model",
                "task_type",
                "fixed_retry_observed_success",
                "fixed_retry_attempts_to_success",
                "fixed_retry_cumulative_latency_ms",
            ]
        )
    if "avg_attempts" not in exp3.columns:
        exp3["avg_attempts"] = None
    if "cum_e2e_ms" not in exp3.columns:
        exp3["cum_e2e_ms"] = None
    grouped = exp3.groupby(
        ["provider", "model", "provider_model", "task_type"], as_index=False
    ).agg(
        fixed_retry_success_rate=("pass", "mean"),
        fixed_retry_attempts_avg=("avg_attempts", "mean"),
        fixed_retry_cumulative_latency_ms=("cum_e2e_ms", "mean"),
    )
    grouped["fixed_retry_observed_success"] = grouped["fixed_retry_success_rate"].map(
        lambda value: None if _is_null(value) else bool(float(value) > 0)
    )
    grouped["fixed_retry_attempts_to_success"] = grouped.apply(
        lambda row: _to_int_or_none(row["fixed_retry_attempts_avg"])
        if row["fixed_retry_observed_success"] is True
        else None,
        axis=1,
    )
    return grouped[
        [
            "provider",
            "model",
            "provider_model",
            "task_type",
            "fixed_retry_observed_success",
            "fixed_retry_attempts_to_success",
            "fixed_retry_cumulative_latency_ms",
        ]
    ]


def _filter_provider_model(
    df: pd.DataFrame, *, provider: str | None, model: str | None
) -> pd.DataFrame:
    filtered = df
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


def _filter_adaptive_summary(
    df: pd.DataFrame,
    *,
    run_id: str,
    provider: str | None,
    model: str | None,
    attempt_budget_k: int,
) -> pd.DataFrame:
    if df.empty:
        return df
    filtered = df.copy()
    if "run_id" in filtered.columns:
        filtered = filtered[filtered["run_id"] == run_id]
    if provider is not None and "provider" in filtered.columns:
        filtered = filtered[filtered["provider"] == provider]
    if model is not None and "model" in filtered.columns:
        filtered = filtered[filtered["model"] == model]
    if "attempt_budget_k" in filtered.columns:
        filtered = filtered[
            filtered["attempt_budget_k"].map(lambda value: _to_int(value, default=-1))
            == attempt_budget_k
        ]
    return filtered.where(pd.notna(filtered), None)


def _write_csv(
    path: Path,
    field_map: dict[str, Any],
    rows: Iterable[AdaptiveComparisonRow],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(field_map)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.model_dump(mode="json"))


def _write_json(path: Path, schema_version: str, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "schema_version": schema_version,
                "rows": rows,
            },
            handle,
            indent=2,
            ensure_ascii=False,
        )
        handle.write("\n")


def _is_null(value: object) -> bool:
    return value is None or (isinstance(value, float) and pd.isna(value)) or value == ""


def _to_float_or_none(value: object) -> float | None:
    if _is_null(value):
        return None
    return float(value)


def _to_float(value: object) -> float:
    maybe_float = _to_float_or_none(value)
    return 0.0 if maybe_float is None else maybe_float


def _to_int_or_none(value: object) -> int | None:
    if _is_null(value):
        return None
    return int(round(float(value)))


def _to_int(value: object, *, default: int) -> int:
    maybe_int = _to_int_or_none(value)
    return default if maybe_int is None else maybe_int


def _to_bool_or_none(value: object) -> bool | None:
    if _is_null(value):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().casefold()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return bool(value)


def _to_str_or_none(value: object) -> str | None:
    if _is_null(value):
        return None
    return str(value)
