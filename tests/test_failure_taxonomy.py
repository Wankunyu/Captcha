import csv
import json
from pathlib import Path

import pandas as pd
import pytest

from cognition.failure_taxonomy import (
    AGGREGATE_ONLY_CAVEAT,
    INFRASTRUCTURE_CAVEAT,
    PROTOCOL_CAVEAT,
    build_failure_taxonomy_rows,
    load_adaptive_summary_for_taxonomy,
    main,
    write_failure_taxonomy,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _adaptive_rows() -> list[dict[str, object]]:
    return [
        {
            "schema_version": "cognition.revision.adaptive_summary.v1",
            "run_id": "adaptive-run",
            "provider": "openai",
            "model": "gpt-5",
            "task_type": "Dice_Count",
            "attempt_budget_k": 3,
            "n_attempts": 5,
            "n_success": 2,
            "success_rate": 0.4,
            "scientific_wrong_count": 3,
            "protocol_failure_count": 0,
            "infrastructure_failure_count": 0,
        },
        {
            "schema_version": "cognition.revision.adaptive_summary.v1",
            "run_id": "adaptive-run",
            "provider": "openai",
            "model": "gpt-5",
            "task_type": "Place_Dot",
            "attempt_budget_k": 3,
            "n_attempts": 1,
            "n_success": 1,
            "success_rate": 1.0,
            "scientific_wrong_count": 0,
            "protocol_failure_count": 0,
            "infrastructure_failure_count": 0,
        },
        {
            "schema_version": "cognition.revision.adaptive_summary.v1",
            "run_id": "adaptive-run",
            "provider": "openai",
            "model": "gpt-5",
            "task_type": "Patch_Select",
            "attempt_budget_k": 3,
            "n_attempts": 4,
            "n_success": 1,
            "success_rate": 0.25,
            "scientific_wrong_count": 1,
            "protocol_failure_count": 0,
            "infrastructure_failure_count": 2,
        },
        {
            "schema_version": "cognition.revision.adaptive_summary.v1",
            "run_id": "adaptive-run",
            "provider": "openai",
            "model": "gpt-5",
            "task_type": "Image_Matching",
            "attempt_budget_k": 3,
            "n_attempts": 4,
            "n_success": 1,
            "success_rate": 0.25,
            "scientific_wrong_count": 2,
            "protocol_failure_count": 1,
            "infrastructure_failure_count": 0,
        },
    ]


def test_adaptive_rows_compute_raw_scientific_rates_and_caveats(
    tmp_path: Path,
) -> None:
    adaptive_summary = tmp_path / "adaptive_summary.csv"
    _write_csv(adaptive_summary, _adaptive_rows())

    adaptive_df = load_adaptive_summary_for_taxonomy(adaptive_summary)
    rows = build_failure_taxonomy_rows(adaptive_df, retry_df=None, run_id="run-1")
    by_key = {(row.aggregation_level, row.task_type): row for row in rows}

    dice = by_key[("task_type", "Dice_Count")]
    assert dice.success_count == 2
    assert dice.total_count == 5
    assert dice.raw_observed_rate == pytest.approx(2 / 5)
    assert dice.scientific_rate == pytest.approx(2 / (2 + 3))
    assert dice.claim_use == "scientific_claim_eligible"
    assert dice.hardness_caveat is None

    patch = by_key[("task_type", "Patch_Select")]
    assert patch.raw_observed_rate == pytest.approx(1 / 4)
    assert patch.scientific_rate == pytest.approx(1 / (1 + 1))
    assert patch.claim_use == "infrastructure_caveated"
    assert patch.hardness_caveat == INFRASTRUCTURE_CAVEAT

    image_matching = by_key[("task_type", "Image_Matching")]
    assert image_matching.raw_observed_rate == pytest.approx(1 / 4)
    assert image_matching.scientific_rate == pytest.approx(1 / (1 + 2))
    assert image_matching.claim_use == "protocol_caveated"
    assert image_matching.hardness_caveat == PROTOCOL_CAVEAT


def test_task_family_aggregation_sums_counts_and_claim_use(tmp_path: Path) -> None:
    adaptive_summary = tmp_path / "adaptive_summary.json"
    _write_json(
        adaptive_summary,
        {
            "schema_version": "cognition.revision.adaptive_summary.v1",
            "rows": _adaptive_rows(),
        },
    )

    rows = build_failure_taxonomy_rows(
        load_adaptive_summary_for_taxonomy(adaptive_summary),
        retry_df=None,
        run_id="run-1",
    )
    family_rows = [row for row in rows if row.aggregation_level == "task_family"]

    click_family = next(row for row in family_rows if row.task_family == "Click/Coordinate")
    assert click_family.task_type == "__family__"
    assert click_family.success_count == 3
    assert click_family.scientific_wrong_count == 3
    assert click_family.protocol_failure_count == 0
    assert click_family.infrastructure_failure_count == 0
    assert click_family.total_count == 6
    assert click_family.raw_observed_rate == pytest.approx(3 / 6)
    assert click_family.scientific_rate == pytest.approx(3 / (3 + 3))
    assert click_family.claim_use == "scientific_claim_eligible"
    assert click_family.hardness_caveat is None

    grid_family = next(row for row in family_rows if row.task_family == "Grid Selection")
    assert grid_family.claim_use == "infrastructure_caveated"
    assert grid_family.hardness_caveat == INFRASTRUCTURE_CAVEAT


def test_aggregate_only_rows_from_retry_calibration_are_caveated() -> None:
    retry_df = pd.DataFrame(
        [
            {
                "provider": "openai",
                "model": "gpt-5",
                "provider_model": "openai/gpt-5",
                "task_type": "Dice_Count",
                "task_family": "Click/Coordinate",
                "raw_observed_rate": 0.5,
                "scientific_rate": 0.4,
            }
        ]
    )

    rows = build_failure_taxonomy_rows(
        adaptive_df=pd.DataFrame(),
        retry_df=retry_df,
        run_id="run-1",
    )

    assert len(rows) == 1
    row = rows[0]
    assert row.aggregation_level == "aggregate_only"
    assert row.success_count == 0
    assert row.scientific_wrong_count == 0
    assert row.protocol_failure_count == 0
    assert row.infrastructure_failure_count == 0
    assert row.total_count == 0
    assert row.raw_observed_rate == pytest.approx(0.5)
    assert row.scientific_rate is None
    assert row.claim_use == "aggregate_only_caveated"
    assert row.hardness_caveat == AGGREGATE_ONLY_CAVEAT


def test_write_outputs_and_cli_defaults_use_revision_run_dir(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    adaptive_summary = tmp_path / "adaptive_summary.csv"
    _write_csv(adaptive_summary, _adaptive_rows())
    output_root = tmp_path / "revision"
    rows = build_failure_taxonomy_rows(
        load_adaptive_summary_for_taxonomy(adaptive_summary),
        retry_df=None,
        run_id="run-1",
    )

    csv_path, json_path = write_failure_taxonomy(
        rows,
        tmp_path / "manual" / "failure_taxonomy.csv",
        tmp_path / "manual" / "failure_taxonomy.json",
    )
    assert csv_path.exists()
    assert json_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "cognition.revision.failure_taxonomy.v1"

    assert main(
        [
            "--adaptive-summary",
            str(adaptive_summary),
            "--output-root",
            str(output_root),
            "--run-id",
            "safe-run",
        ]
    ) == 0
    summary = json.loads(capsys.readouterr().out)

    assert summary["row_count"] == 7
    assert summary["claim_use_counts"]["scientific_claim_eligible"] == 3
    assert summary["claim_use_counts"]["infrastructure_caveated"] == 2
    assert summary["claim_use_counts"]["protocol_caveated"] == 2
    assert (output_root / "safe-run" / "failure_taxonomy.csv").exists()
    assert (output_root / "safe-run" / "failure_taxonomy.json").exists()


@pytest.mark.parametrize("bad_run_id", ["../phase3", "bad/run"])
def test_cli_rejects_invalid_run_ids_before_writing_outputs(
    tmp_path: Path,
    bad_run_id: str,
) -> None:
    adaptive_summary = tmp_path / "adaptive_summary.csv"
    _write_csv(adaptive_summary, _adaptive_rows())
    output_root = tmp_path / "revision"

    with pytest.raises(SystemExit):
        main(
            [
                "--adaptive-summary",
                str(adaptive_summary),
                "--output-root",
                str(output_root),
                "--run-id",
                bad_run_id,
            ]
        )

    assert not output_root.exists()
