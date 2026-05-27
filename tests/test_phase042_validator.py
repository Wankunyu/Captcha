import json
from pathlib import Path

from PIL import Image

from cognition.expanded_dataset_phase042 import (
    build_captcha_data_hash_index,
    sha256_image,
    validate_phase042_candidates,
)


def _write_image(path: Path, color: tuple[int, int, int]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (12, 12), color).save(path)
    return path


def _write_gradient_image(path: Path, *, offset: int = 0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("L", (8, 8))
    image.putdata([min(255, value * 4 + offset) for value in range(64)])
    image.convert("RGB").save(path)
    return path


def _candidate_row(
    *,
    candidate_id: str,
    task_type: str,
    image_paths: list[str],
    source_kind: str = "open_source_dataset",
    **overrides: object,
) -> dict[str, object]:
    values: dict[str, object] = {
        "candidate_id": candidate_id,
        "task_type": task_type,
        "source_kind": source_kind,
        "source_provenance_class": "preferred_real_external",
        "candidate_image_paths": image_paths,
        "source_citation": "Example open-source CAPTCHA dataset",
        "source_license": "CC-BY-4.0",
        "source_provenance_notes": (
            "Real external CAPTCHA samples newly introduced relative to current "
            "captcha_data."
        ),
        "label_format": "integer",
        "metadata_alignment_notes": "source ids mapped to selected manifest rows",
        "answer_format_normalization": "integer answers normalized as strings",
        "compatibility_status": "ready_for_static_pipeline",
        "limitation_notes": "selective corrected sidecar slice only",
        "adaptive_eligible": True,
        "static_compatibility_notes": "offline static images with ground truth",
    }
    values.update(overrides)
    return values


def _write_manifest(path: Path, rows: list[dict[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "cognition.revision.phase042.candidate_manifest.v1",
                "candidate_rows": rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _read_rows(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["rows"]
    assert isinstance(rows, list)
    return rows


def test_exact_sha256_captcha_data_match_is_warning_not_hard_fail(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    captcha_image = _write_image(
        Path("captcha_data/Dice_Count/original.png"),
        (20, 40, 60),
    )
    candidate_image = Path(
        "expanded_captcha_data/phase04_2/candidates/Dice_Count/candidate.png"
    )
    candidate_image.parent.mkdir(parents=True, exist_ok=True)
    candidate_image.write_bytes(captcha_image.read_bytes())
    manifest_path = _write_manifest(
        Path("expanded_captcha_data/phase04_2/candidate_manifest.json"),
        [
            _candidate_row(
                candidate_id="duplicate-dice-count",
                task_type="Dice_Count",
                image_paths=[candidate_image.as_posix()],
            )
        ],
    )

    hash_index = build_captcha_data_hash_index(Path("captcha_data"))
    assert sha256_image(candidate_image) in hash_index

    result = validate_phase042_candidates(
        candidate_manifest_path=manifest_path,
        captcha_root=Path("captcha_data"),
    )

    assert result["selected_count"] == 1
    report_rows = _read_rows(
        Path("expanded_captcha_data/phase04_2/phase042_validation_report.json")
    )
    selected_rows = _read_rows(
        Path("expanded_captcha_data/phase04_2/phase042_selected_manifest.json")
    )
    assert report_rows[0]["candidate_id"] == "duplicate-dice-count"
    assert report_rows[0]["validation_status"] == "accepted"
    assert report_rows[0]["exact_captcha_data_match"] is True
    assert report_rows[0]["selected_manifest_eligible"] is True
    assert "exact SHA-256 match warning" in str(report_rows[0]["review_warnings"])
    assert selected_rows[0]["candidate_id"] == "duplicate-dice-count"
    assert selected_rows[0]["exact_captcha_data_match"] is True


def test_exact_sha256_rows_enter_selected_manifest_with_warning(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    captcha_image = _write_image(
        Path("captcha_data/Dice_Count/original.png"),
        (20, 40, 60),
    )
    candidate_image = Path(
        "expanded_captcha_data/phase04_2/candidates/Dice_Count/duplicate.png"
    )
    candidate_image.parent.mkdir(parents=True, exist_ok=True)
    candidate_image.write_bytes(captcha_image.read_bytes())
    manifest_path = _write_manifest(
        Path("expanded_captcha_data/phase04_2/candidate_manifest.json"),
        [
            _candidate_row(
                candidate_id="duplicate-dice-count",
                task_type="Dice_Count",
                image_paths=[candidate_image.as_posix()],
            )
        ],
    )

    validate_phase042_candidates(
        candidate_manifest_path=manifest_path,
        captcha_root=Path("captcha_data"),
    )

    selected_rows = _read_rows(
        Path("expanded_captcha_data/phase04_2/phase042_selected_manifest.json")
    )
    assert [row["candidate_id"] for row in selected_rows] == ["duplicate-dice-count"]
    assert selected_rows[0]["exact_captcha_data_match"] is True
    assert "exact SHA-256 match warning" in str(selected_rows[0]["review_warnings"])


def test_perceptual_near_match_is_warning_not_hard_fail(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    _write_gradient_image(Path("captcha_data/Dice_Count/original.png"), offset=0)
    candidate_image = _write_gradient_image(
        Path("expanded_captcha_data/phase04_2/candidates/Dice_Count/near.png"),
        offset=1,
    )
    manifest_path = _write_manifest(
        Path("expanded_captcha_data/phase04_2/candidate_manifest.json"),
        [
            _candidate_row(
                candidate_id="near-match-dice-count",
                task_type="Dice_Count",
                image_paths=[candidate_image.as_posix()],
            )
        ],
    )

    result = validate_phase042_candidates(
        candidate_manifest_path=manifest_path,
        captcha_root=Path("captcha_data"),
        perceptual_warning_threshold=4,
    )

    assert result["selected_count"] == 1
    report_rows = _read_rows(
        Path("expanded_captcha_data/phase04_2/phase042_validation_report.json")
    )
    selected_rows = _read_rows(
        Path("expanded_captcha_data/phase04_2/phase042_selected_manifest.json")
    )
    assert report_rows[0]["validation_status"] == "accepted"
    assert report_rows[0]["exact_captcha_data_match"] is False
    assert report_rows[0]["perceptual_warning_count"] >= 1
    assert selected_rows[0]["perceptual_warning_count"] >= 1


def test_validate_sources_writes_selected_manifest_separate_from_validation_report(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    _write_image(Path("captcha_data/Dice_Count/original.png"), (20, 40, 60))
    valid_image = _write_image(
        Path("expanded_captcha_data/phase04_2/candidates/Dice_Count/valid.png"),
        (120, 140, 160),
    )
    missing_image = Path(
        "expanded_captcha_data/phase04_2/candidates/Dice_Count/missing.png"
    )
    manifest_path = _write_manifest(
        Path("expanded_captcha_data/phase04_2/candidate_manifest.json"),
        [
            _candidate_row(
                candidate_id="valid-dice-count",
                task_type="Dice_Count",
                image_paths=[valid_image.as_posix()],
            ),
            _candidate_row(
                candidate_id="missing-dice-count",
                task_type="Dice_Count",
                image_paths=[missing_image.as_posix()],
            ),
        ],
    )

    result = validate_phase042_candidates(
        candidate_manifest_path=manifest_path,
        captcha_root=Path("captcha_data"),
    )

    validation_report = Path(
        "expanded_captcha_data/phase04_2/phase042_validation_report.json"
    )
    selected_manifest = Path(
        "expanded_captcha_data/phase04_2/phase042_selected_manifest.json"
    )
    novelty_report = Path("expanded_captcha_data/phase04_2/novelty_hash_report.json")
    assert result["report_count"] == 2
    assert validation_report.is_file()
    assert selected_manifest.is_file()
    assert novelty_report.is_file()

    report_rows = _read_rows(validation_report)
    selected_rows = _read_rows(selected_manifest)
    assert {row["candidate_id"] for row in report_rows} == {
        "valid-dice-count",
        "missing-dice-count",
    }
    assert [row["candidate_id"] for row in selected_rows] == ["valid-dice-count"]
    assert report_rows[1]["validation_status"] == "rejected"
    assert "missing candidate image" in str(report_rows[1]["rejection_reason"])
