from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import pandas as pd

from phase3_artifacts import (
    FAILURE_TAXONOMY_SCHEMA_VERSION,
    FailureTaxonomyRow,
    write_csv,
    write_json,
)
from revision_artifacts import revision_run_dir
from visualize_results import CAPTCHAVisualizer


INFRASTRUCTURE_CAVEAT = (
    "infrastructure/provider failures are visible and are not counted as "
    "scientific evidence of structural robustness"
)
PROTOCOL_CAVEAT = (
    "protocol failures are visible and are not counted as scientific model failures"
)
AGGREGATE_ONLY_CAVEAT = (
    "aggregate-only source lacks failure classes; use for rate context, not "
    "failure-taxonomy claims"
)

_EMPTY_ADAPTIVE_COLUMNS = [
    "provider",
    "model",
    "provider_model",
    "task_type",
    "task_family",
    "n_success",
    "scientific_wrong_count",
    "protocol_failure_count",
    "infrastructure_failure_count",
]
_EMPTY_RETRY_COLUMNS = [
    "provider",
    "model",
    "provider_model",
    "task_type",
    "task_family",
    "raw_observed_rate",
]


def load_adaptive_summary_for_taxonomy(path: Path | None) -> pd.DataFrame:
    if path is None:
        return pd.DataFrame(columns=_EMPTY_ADAPTIVE_COLUMNS)
    df = _read_table(Path(path))
    if df.empty:
        return pd.DataFrame(columns=_EMPTY_ADAPTIVE_COLUMNS)
    if "provider_model" not in df.columns:
        df["provider_model"] = df.apply(
            lambda row: f"{row.get('provider')}/{row.get('model')}", axis=1
        )
    if "task_family" not in df.columns:
        df["task_family"] = df["task_type"].map(_task_family)
    for column in [
        "n_success",
        "scientific_wrong_count",
        "protocol_failure_count",
        "infrastructure_failure_count",
    ]:
        if column not in df.columns:
            raise ValueError(f"adaptive summary missing required field: {column}")
        df[column] = df[column].map(lambda value: _to_int(value, default=0))
    return df[_EMPTY_ADAPTIVE_COLUMNS].where(pd.notna, None)


def build_failure_taxonomy_rows(
    adaptive_df: pd.DataFrame,
    retry_df: pd.DataFrame | None,
    run_id: str,
) -> list[FailureTaxonomyRow]:
    if not adaptive_df.empty:
        task_rows = _adaptive_rows_by_level(
            adaptive_df,
            run_id=run_id,
            aggregation_level="task_type",
            group_columns=["provider", "model", "provider_model", "task_type", "task_family"],
        )
        family_rows = _adaptive_rows_by_level(
            adaptive_df,
            run_id=run_id,
            aggregation_level="task_family",
            group_columns=["provider", "model", "provider_model", "task_family"],
        )
        return task_rows + family_rows

    if retry_df is not None and not retry_df.empty:
        return _aggregate_only_rows(retry_df, run_id=run_id)

    return []


def write_failure_taxonomy(
    rows: list[FailureTaxonomyRow],
    output_csv: Path,
    output_json: Path,
) -> tuple[Path, Path]:
    validated_rows = [
        row
        if isinstance(row, FailureTaxonomyRow)
        else FailureTaxonomyRow.model_validate(row)
        for row in rows
    ]
    csv_path = Path(output_csv)
    json_path = Path(output_json)
    write_csv(csv_path, FailureTaxonomyRow.model_fields, validated_rows)
    write_json(json_path, FAILURE_TAXONOMY_SCHEMA_VERSION, validated_rows)
    return csv_path, json_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build failure taxonomy artifacts separating scientific, protocol, "
            "infrastructure, and aggregate-only evidence."
        )
    )
    parser.add_argument("--adaptive-summary", default=None)
    parser.add_argument("--retry-calibration", default=None)
    parser.add_argument("--output-root", default="./results/revision")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-csv", default=None)
    parser.add_argument("--output-json", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.adaptive_summary is None and args.retry_calibration is None:
        parser.error("--adaptive-summary or --retry-calibration is required")
    try:
        output_csv, output_json = _resolve_output_paths(args)
        adaptive_df = load_adaptive_summary_for_taxonomy(
            Path(args.adaptive_summary) if args.adaptive_summary else None
        )
        retry_df = _load_retry_calibration(
            Path(args.retry_calibration) if args.retry_calibration else None
        )
        rows = build_failure_taxonomy_rows(adaptive_df, retry_df, run_id=args.run_id)
        if not rows:
            raise ValueError("No failure taxonomy rows found after loading inputs")
    except ValueError as exc:
        parser.error(str(exc))

    paths = write_failure_taxonomy(rows, output_csv, output_json)
    claim_counts = Counter(row.claim_use for row in rows)
    print(
        json.dumps(
            {
                "row_count": len(rows),
                "output_csv": str(paths[0]),
                "output_json": str(paths[1]),
                "claim_use_counts": dict(sorted(claim_counts.items())),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _adaptive_rows_by_level(
    df: pd.DataFrame,
    *,
    run_id: str,
    aggregation_level: str,
    group_columns: list[str],
) -> list[FailureTaxonomyRow]:
    rows: list[FailureTaxonomyRow] = []
    for key, group in df.groupby(group_columns, dropna=False):
        key_values = dict(zip(group_columns, key, strict=False))
        success_count = int(group["n_success"].sum())
        scientific_wrong_count = int(group["scientific_wrong_count"].sum())
        protocol_failure_count = int(group["protocol_failure_count"].sum())
        infrastructure_failure_count = int(group["infrastructure_failure_count"].sum())
        task_family = str(key_values["task_family"])
        task_type = (
            "__family__"
            if aggregation_level == "task_family"
            else str(key_values["task_type"])
        )
        rows.append(
            _build_row(
                run_id=run_id,
                aggregation_level=aggregation_level,
                provider=str(key_values["provider"]),
                model=str(key_values["model"]),
                provider_model=str(key_values["provider_model"]),
                task_type=task_type,
                task_family=task_family,
                success_count=success_count,
                scientific_wrong_count=scientific_wrong_count,
                protocol_failure_count=protocol_failure_count,
                infrastructure_failure_count=infrastructure_failure_count,
                failure_taxonomy_source="adaptive_summary",
            )
        )
    return rows


def _aggregate_only_rows(
    retry_df: pd.DataFrame,
    *,
    run_id: str,
) -> list[FailureTaxonomyRow]:
    rows: list[FailureTaxonomyRow] = []
    normalized = retry_df.copy()
    if "provider_model" not in normalized.columns:
        normalized["provider_model"] = normalized.apply(
            lambda row: f"{row.get('provider')}/{row.get('model')}", axis=1
        )
    if "task_family" not in normalized.columns:
        normalized["task_family"] = normalized["task_type"].map(_task_family)
    if "raw_observed_rate" not in normalized.columns:
        normalized["raw_observed_rate"] = None
    for record in normalized.to_dict(orient="records"):
        rows.append(
            FailureTaxonomyRow(
                run_id=run_id,
                aggregation_level="aggregate_only",
                provider=str(record["provider"]),
                model=str(record["model"]),
                provider_model=str(record["provider_model"]),
                task_type=str(record["task_type"]),
                task_family=str(record["task_family"]),
                success_count=0,
                scientific_wrong_count=0,
                protocol_failure_count=0,
                infrastructure_failure_count=0,
                total_count=0,
                raw_observed_rate=_to_float_or_none(record.get("raw_observed_rate")),
                scientific_rate=None,
                failure_taxonomy_source="retry_calibration_aggregate_only",
                claim_use="aggregate_only_caveated",
                hardness_caveat=AGGREGATE_ONLY_CAVEAT,
            )
        )
    return rows


def _build_row(
    *,
    run_id: str,
    aggregation_level: str,
    provider: str,
    model: str,
    provider_model: str,
    task_type: str,
    task_family: str,
    success_count: int,
    scientific_wrong_count: int,
    protocol_failure_count: int,
    infrastructure_failure_count: int,
    failure_taxonomy_source: str,
) -> FailureTaxonomyRow:
    total_count = (
        success_count
        + scientific_wrong_count
        + protocol_failure_count
        + infrastructure_failure_count
    )
    scientific_denominator = success_count + scientific_wrong_count
    claim_use, caveat = _claim_use_and_caveat(
        protocol_failure_count=protocol_failure_count,
        infrastructure_failure_count=infrastructure_failure_count,
    )
    return FailureTaxonomyRow(
        run_id=run_id,
        aggregation_level=aggregation_level,
        provider=provider,
        model=model,
        provider_model=provider_model,
        task_type=task_type,
        task_family=task_family,
        success_count=success_count,
        scientific_wrong_count=scientific_wrong_count,
        protocol_failure_count=protocol_failure_count,
        infrastructure_failure_count=infrastructure_failure_count,
        total_count=total_count,
        raw_observed_rate=success_count / total_count if total_count > 0 else None,
        scientific_rate=(
            success_count / scientific_denominator
            if scientific_denominator > 0
            else None
        ),
        failure_taxonomy_source=failure_taxonomy_source,
        claim_use=claim_use,
        hardness_caveat=caveat,
    )


def _claim_use_and_caveat(
    *,
    protocol_failure_count: int,
    infrastructure_failure_count: int,
) -> tuple[str, str | None]:
    if infrastructure_failure_count > 0:
        return "infrastructure_caveated", INFRASTRUCTURE_CAVEAT
    if protocol_failure_count > 0:
        return "protocol_caveated", PROTOCOL_CAVEAT
    return "scientific_claim_eligible", None


def _resolve_output_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    run_dir = revision_run_dir(args.output_root, args.run_id)
    return (
        Path(args.output_csv) if args.output_csv else run_dir / "failure_taxonomy.csv",
        Path(args.output_json) if args.output_json else run_dir / "failure_taxonomy.json",
    )


def _load_retry_calibration(path: Path | None) -> pd.DataFrame:
    if path is None:
        return pd.DataFrame(columns=_EMPTY_RETRY_COLUMNS)
    df = _read_table(path)
    if df.empty:
        return pd.DataFrame(columns=_EMPTY_RETRY_COLUMNS)
    return df.where(pd.notna, None)


def _read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        rows = payload.get("rows", payload if isinstance(payload, list) else [])
        return pd.DataFrame(rows)
    return pd.read_csv(path).where(pd.notna, None)


def _task_family(task_type: object) -> str:
    return CAPTCHAVisualizer.TASK_FAMILY.get(str(task_type), "Unmapped")


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
