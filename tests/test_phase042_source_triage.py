import pytest

from cognition.expanded_dataset_phase042 import (
    PHASE042_MIN_SAMPLES_PER_CATEGORY,
    build_source_triage_rows,
)


def _candidate(task_type: str, source_kind: str, **overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "task_type": task_type,
        "source_kind": source_kind,
        "source_citation": f"{source_kind} citation for {task_type}",
        "source_license": "license reviewed for offline research use",
        "source_provenance_notes": "new external candidate source for Phase 04.2",
        "fallback_reason": "",
        "style_consistency_notes": "Open CaptchaWorld-style static image",
        "candidate_path": f"expanded_captcha_data/phase04_2/candidates/{task_type}/sample.png",
    }
    values.update(overrides)
    return values


def test_source_triage_prefers_real_external_before_gpt_image() -> None:
    rows = build_source_triage_rows(
        [
            _candidate(
                "Dice_Count",
                "gpt_image_open_captchaworld_style",
                fallback_reason="Not enough usable external samples yet.",
            ),
            _candidate("Dice_Count", "open_source_dataset"),
            _candidate("Dice_Count", "peer_reviewed_paper_dataset"),
        ]
    )

    assert [row["source_kind"] for row in rows] == [
        "peer_reviewed_paper_dataset",
        "open_source_dataset",
        "gpt_image_open_captchaworld_style",
    ]
    assert all(
        row["sample_count_target"] == PHASE042_MIN_SAMPLES_PER_CATEGORY
        for row in rows
    )
    assert rows[0]["evidence_role"] == "preferred_direct_evidence"
    assert (
        rows[-1]["evidence_role"]
        == "fallback_direct_evidence_with_provenance_caveat"
    )


def test_source_triage_rejects_phase041_paths() -> None:
    with pytest.raises(ValueError, match="phase04_1"):
        build_source_triage_rows(
            [
                _candidate(
                    "Dice_Count",
                    "open_source_dataset",
                    candidate_path=(
                        "expanded_captcha_data/phase04_1/sources/Dice_Count/sample.png"
                    ),
                )
            ]
        )
