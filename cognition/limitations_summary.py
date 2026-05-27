from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from .revision_artifacts import revision_run_dir


PHASE3_ARTIFACT_INDEX_SCHEMA_VERSION = "cognition.revision.phase3_artifact_index.v1"

DATASET_SCOPE_CAVEAT = (
    "CaptchaWorld is treated as a curated, task-diverse benchmark for recurring "
    "structural hardness patterns, not a population-level deployment estimate."
)
THRESHOLD_CAVEAT = (
    "The 40% working CAPTCHA threshold is an operational reporting heuristic, "
    "not a universal CAPTCHA security boundary."
)
REVIEW_BAND_CAVEAT = (
    "The 30%-50% review band is a revision-time caution band, "
    "not a new security tier."
)
FAILURE_TAXONOMY_CAVEAT = "Infrastructure and protocol failures are not counted as scientific evidence of structural robustness."  # noqa: E501
EVIDENCE_SEPARATION_CAVEAT = (
    "Original, supplemented-category, and new-category evidence are reported separately."
)
VALIDATION_SLICE_CAVEAT = (
    "Selective validation-slice outcomes are compared against original-dataset "
    "conclusions and reported as agreement, divergence, or inconclusive evidence."
)
RAW_SCIENTIFIC_RATE_CAVEAT = (
    "raw_observed_rate is transparent accounting; scientific_rate is the preferred "
    "basis for model/CAPTCHA behavior claims when failure classes are available."
)

REQUIRED_INPUT_KEYS = {
    "dataset_scope_json": "dataset_scope_audit.json",
    "extended_manifest_json": "extended_dataset_manifest.json",
    "extended_validation_comparison_json": "extended_validation_comparison.json",
    "contribution_notes_md": "dataset_contribution_notes.md",
    "pass_rate_confidence_json": "pass_rate_confidence.json",
    "threshold_sensitivity_json": "threshold_sensitivity.json",
    "retry_calibration_json": "retry_calibration.json",
    "failure_taxonomy_json": "failure_taxonomy.json",
}

CLAIM_BOUNDARIES = {
    "dataset_scope": DATASET_SCOPE_CAVEAT,
    "extended_validation_slice": VALIDATION_SLICE_CAVEAT,
    "threshold_cutoff": f"{THRESHOLD_CAVEAT} {REVIEW_BAND_CAVEAT}",
    "failure_taxonomy": (
        f"{FAILURE_TAXONOMY_CAVEAT} {RAW_SCIENTIFIC_RATE_CAVEAT}"
    ),
    "live_service_automation": (
        "Phase 3 artifacts are offline and dataset-based; they do not require "
        "browser automation against live CAPTCHA services."
    ),
}


def load_rows(path: Path) -> list[dict[str, object]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        rows = payload.get("rows", [])
    elif isinstance(payload, list):
        rows = payload
    else:
        raise ValueError(f"Expected a JSON object or array in {path}")
    if not isinstance(rows, list):
        raise ValueError(f"Expected rows array in {path}")
    return [dict(row) for row in rows if isinstance(row, dict)]


def build_artifact_index(
    inputs: dict[str, Path],
    output_md: Path,
    run_id: str,
    artifact_index_json: Path | None = None,
) -> dict[str, object]:
    missing = sorted(set(REQUIRED_INPUT_KEYS) - set(inputs))
    if missing:
        raise ValueError(f"missing required input artifacts: {', '.join(missing)}")
    index_path = artifact_index_json or Path(output_md).with_name(
        "phase3_artifact_index.json"
    )
    return {
        "schema_version": PHASE3_ARTIFACT_INDEX_SCHEMA_VERSION,
        "run_id": run_id,
        "input_artifacts": {
            key: str(Path(inputs[key])) for key in REQUIRED_INPUT_KEYS
        },
        "output_artifacts": {
            "limitations_summary_md": str(Path(output_md)),
            "phase3_artifact_index_json": str(index_path),
        },
        "claim_boundaries": CLAIM_BOUNDARIES,
    }


def render_limitations_summary(
    *,
    dataset_scope_rows: list[dict[str, object]],
    extended_manifest_rows: list[dict[str, object]],
    extended_validation_rows: list[dict[str, object]],
    contribution_notes_md: str,
    pass_rate_rows: list[dict[str, object]],
    threshold_rows: list[dict[str, object]],
    retry_rows: list[dict[str, object]],
    failure_rows: list[dict[str, object]],
) -> str:
    scope_counts = _counts_by(dataset_scope_rows, "scope_status")
    removed_rows = [
        row
        for row in dataset_scope_rows
        if row.get("scope_status") == "incompatible"
        or row.get("support_status") == "removed_not_used"
    ]
    validation_counts = _counts_by(extended_validation_rows, "agreement_status")
    divergent_rows = [
        row
        for row in extended_validation_rows
        if row.get("agreement_status") == "diverges_from_original"
    ]
    inconclusive_rows = [
        row
        for row in extended_validation_rows
        if row.get("agreement_status") == "inconclusive"
    ]
    underpowered_rows = [
        row
        for row in [*dataset_scope_rows, *pass_rate_rows]
        if _as_bool(row.get("underpowered"))
    ]
    review_band_count = sum(
        1 for row in threshold_rows if _as_bool(row.get("in_30_50_review_band"))
    )
    trend_sensitive_count = sum(
        1 for row in threshold_rows if _as_bool(row.get("trend_sensitive"))
    )

    lines = [
        "# Phase 3 Dataset Scope, Statistical Confidence, And Limitations",
        "",
        "## Dataset Scope",
        DATASET_SCOPE_CAVEAT,
        _format_counts("Scope-status counts", scope_counts),
        (
            "Dataset sample counts, support status, prompt/few-shot availability, "
            "and underpowered flags are interpreted as benchmark coverage metadata."
        ),
        "",
        "## Removed Incompatible CaptchaWorld Types",
        *_removed_task_lines(removed_rows),
        "",
        "## Dataset Contribution Notes",
        EVIDENCE_SEPARATION_CAVEAT,
        _manifest_origin_summary(extended_manifest_rows),
        _contribution_note_excerpt(contribution_notes_md),
        "",
        "## Extended Validation Slice Comparison",
        VALIDATION_SLICE_CAVEAT,
        _format_counts("Agreement-status counts", validation_counts),
        _divergent_summary(divergent_rows),
        _inconclusive_summary(inconclusive_rows),
        "",
        "## Statistical Confidence And Sample Support",
        _confidence_summary(pass_rate_rows),
        _underpowered_summary(underpowered_rows),
        "",
        "## Threshold Sensitivity",
        THRESHOLD_CAVEAT,
        REVIEW_BAND_CAVEAT,
        f"30%-50% review band rows: {review_band_count}",
        f"trend-sensitive rows: {trend_sensitive_count}",
        _threshold_task_summary(threshold_rows),
        "",
        "## Retry Calibration",
        _retry_calibration_summary(retry_rows),
        "",
        "## Failure Taxonomy",
        FAILURE_TAXONOMY_CAVEAT,
        RAW_SCIENTIFIC_RATE_CAVEAT,
        _format_counts("Claim-use row counts", _counts_by(failure_rows, "claim_use")),
        "",
        "## Generalizability Limits",
        (
            "These artifacts support recurring structural-hardness claims within a "
            "curated benchmark and selective validation slices. They do not convert "
            "CaptchaWorld into a deployment-population sample, and they keep original "
            "dataset, supplemented-category, and new-category evidence separate."
        ),
        "",
        "## Paper-Safe Claim Language",
        DATASET_SCOPE_CAVEAT,
        THRESHOLD_CAVEAT,
        REVIEW_BAND_CAVEAT,
        FAILURE_TAXONOMY_CAVEAT,
        EVIDENCE_SEPARATION_CAVEAT,
        VALIDATION_SLICE_CAVEAT,
        RAW_SCIENTIFIC_RATE_CAVEAT,
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_limitations_summary(
    *,
    inputs: dict[str, Path],
    output_md: Path,
    artifact_index_json: Path,
    run_id: str,
) -> tuple[Path, Path]:
    rows = {key: load_rows(path) for key, path in inputs.items() if key != "contribution_notes_md"}
    contribution_notes = Path(inputs["contribution_notes_md"]).read_text(encoding="utf-8")
    output_md = Path(output_md)
    artifact_index_json = Path(artifact_index_json)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    artifact_index_json.parent.mkdir(parents=True, exist_ok=True)

    text = render_limitations_summary(
        dataset_scope_rows=rows["dataset_scope_json"],
        extended_manifest_rows=rows["extended_manifest_json"],
        extended_validation_rows=rows["extended_validation_comparison_json"],
        contribution_notes_md=contribution_notes,
        pass_rate_rows=rows["pass_rate_confidence_json"],
        threshold_rows=rows["threshold_sensitivity_json"],
        retry_rows=rows["retry_calibration_json"],
        failure_rows=rows["failure_taxonomy_json"],
    )
    output_md.write_text(text, encoding="utf-8")

    index = build_artifact_index(inputs, output_md, run_id, artifact_index_json)
    with artifact_index_json.open("w", encoding="utf-8") as handle:
        json.dump(index, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return output_md, artifact_index_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate paper-safe Phase 3 limitations prose and artifact index "
            "from offline revision artifacts."
        )
    )
    parser.add_argument("--dataset-scope-json", required=True)
    parser.add_argument("--extended-manifest-json", required=True)
    parser.add_argument("--extended-validation-comparison-json", required=True)
    parser.add_argument("--contribution-notes-md", required=True)
    parser.add_argument("--pass-rate-confidence-json", required=True)
    parser.add_argument("--threshold-sensitivity-json", required=True)
    parser.add_argument("--retry-calibration-json", required=True)
    parser.add_argument("--failure-taxonomy-json", required=True)
    parser.add_argument("--output-root", default="./results/local_runs")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-md", default=None)
    parser.add_argument("--artifact-index-json", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        run_dir = revision_run_dir(args.output_root, args.run_id)
        output_md = (
            Path(args.output_md)
            if args.output_md is not None
            else run_dir / "limitations_summary.md"
        )
        artifact_index_json = (
            Path(args.artifact_index_json)
            if args.artifact_index_json is not None
            else run_dir / "phase3_artifact_index.json"
        )
        inputs = {
            "dataset_scope_json": Path(args.dataset_scope_json),
            "extended_manifest_json": Path(args.extended_manifest_json),
            "extended_validation_comparison_json": Path(
                args.extended_validation_comparison_json
            ),
            "contribution_notes_md": Path(args.contribution_notes_md),
            "pass_rate_confidence_json": Path(args.pass_rate_confidence_json),
            "threshold_sensitivity_json": Path(args.threshold_sensitivity_json),
            "retry_calibration_json": Path(args.retry_calibration_json),
            "failure_taxonomy_json": Path(args.failure_taxonomy_json),
        }
        output_md, artifact_index_json = write_limitations_summary(
            inputs=inputs,
            output_md=output_md,
            artifact_index_json=artifact_index_json,
            run_id=args.run_id,
        )
        row_counts = {
            key: len(load_rows(path))
            for key, path in inputs.items()
            if key != "contribution_notes_md"
        }
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    print(
        json.dumps(
            {
                "output_md": str(output_md),
                "artifact_index_json": str(artifact_index_json),
                "row_counts": row_counts,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _counts_by(rows: list[dict[str, object]], field_name: str) -> Counter[str]:
    return Counter(
        str(row.get(field_name))
        for row in rows
        if row.get(field_name) not in (None, "")
    )


def _format_counts(title: str, counts: Counter[str]) -> str:
    if not counts:
        return f"{title}: none"
    rendered = ", ".join(f"{key}: {counts[key]}" for key in sorted(counts))
    return f"{title}: {rendered}"


def _removed_task_lines(rows: list[dict[str, object]]) -> list[str]:
    if not rows:
        return ["No incompatible CaptchaWorld task rows were present in the audit."]
    return [
        f"- {row.get('task_type')}: {row.get('reason')}"
        for row in sorted(rows, key=lambda record: str(record.get("task_type")))
    ]


def _manifest_origin_summary(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "Extended manifest origin counts: none"
    counts = _counts_by(rows, "evidence_origin")
    return _format_counts("Extended manifest origin counts", counts)


def _contribution_note_excerpt(text: str) -> str:
    stripped = " ".join(line.strip() for line in text.splitlines() if line.strip())
    if not stripped:
        return "Dataset contribution notes were empty."
    return f"Contribution-note source summary: {stripped[:400]}"


def _divergent_summary(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "Divergent validation-slice rows: none"
    names = [
        f"{row.get('task_type')} ({row.get('task_family')}): "
        f"{row.get('divergence_reason')}"
        for row in rows
    ]
    return "Divergent validation-slice rows: " + "; ".join(names)


def _inconclusive_summary(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "Inconclusive validation-slice caveats: none"
    names = [
        f"{row.get('task_type')} ({row.get('task_family')}): "
        f"{row.get('comparison_caveat')}"
        for row in rows
    ]
    return "Inconclusive validation-slice caveats: " + "; ".join(names)


def _confidence_summary(rows: list[dict[str, object]]) -> str:
    methods = sorted(
        {
            str(row.get("ci_method"))
            for row in rows
            if row.get("ci_method") not in (None, "")
        }
    )
    confidence_levels = sorted(
        {
            _format_confidence(_as_float(row.get("ci_confidence")))
            for row in rows
            if _as_float(row.get("ci_confidence")) is not None
        }
    )
    methods_text = ", ".join(methods) if methods else "not reported"
    confidence_text = ", ".join(confidence_levels) if confidence_levels else "not reported"
    return (
        f"Confidence interval method: {methods_text}; confidence level: "
        f"{confidence_text}."
    )


def _underpowered_summary(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "Underpowered task or family rows: none"
    thresholds = sorted(
        {
            str(row.get("underpowered_threshold"))
            for row in rows
            if row.get("underpowered_threshold") not in (None, "")
        }
    )
    names = sorted(
        {
            _task_or_family_name(row)
            for row in rows
            if _task_or_family_name(row) not in ("", "__family__")
        }
    )
    threshold_text = ", ".join(thresholds) if thresholds else "not reported"
    return (
        f"Underpowered threshold(s): {threshold_text}. "
        f"Underpowered task/family names: {', '.join(names)}."
    )


def _threshold_task_summary(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "Threshold-sensitive task rows: none"
    names = [
        str(row.get("task_type"))
        for row in rows
        if _as_bool(row.get("in_30_50_review_band"))
        or _as_bool(row.get("trend_sensitive"))
    ]
    if not names:
        return "Threshold-sensitive task rows: none"
    return "Threshold-sensitive task rows: " + ", ".join(sorted(set(names)))


def _retry_calibration_summary(rows: list[dict[str, object]]) -> str:
    grouped: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"fixed_retry": [], "adaptive": []}
    )
    for row in rows:
        family = str(row.get("task_family") or "Unmapped")
        fixed = _as_float(row.get("absolute_error_fixed_retry"))
        adaptive = _as_float(row.get("absolute_error_adaptive"))
        if fixed is not None:
            grouped[family]["fixed_retry"].append(fixed)
        if adaptive is not None:
            grouped[family]["adaptive"].append(adaptive)
    if not grouped:
        return "Mean absolute retry-calibration error by task family: none"
    rendered = []
    for family in sorted(grouped):
        fixed_text = _mean_text(grouped[family]["fixed_retry"])
        adaptive_text = _mean_text(grouped[family]["adaptive"])
        rendered.append(f"{family}: fixed_retry={fixed_text}, adaptive={adaptive_text}")
    return "Mean absolute retry-calibration error by task family: " + "; ".join(rendered)


def _mean_text(values: list[float]) -> str:
    if not values:
        return "n/a"
    return f"{sum(values) / len(values):.3f}"


def _task_or_family_name(row: dict[str, object]) -> str:
    task_type = str(row.get("task_type") or "")
    if task_type and task_type != "__family__":
        return task_type
    return str(row.get("task_family") or "")


def _format_confidence(value: float | None) -> str:
    if value is None:
        return "not reported"
    return f"{value * 100:.0f}%"


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _as_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    raise SystemExit(main())
