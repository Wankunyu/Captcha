import csv
import json

import pytest

from revision_artifacts import (
    RUN_MANIFEST_SCHEMA_VERSION,
    AttemptRecord,
    PromptConfig,
    RevisionArtifactWriter,
    RunManifest,
    collect_code_revision,
    collect_dependency_versions,
    sha256_file,
    sha256_text,
    utc_now,
)


def _manifest(run_id: str = "run-1") -> RunManifest:
    return RunManifest(
        run_id=run_id,
        created_at=utc_now(),
        code_revision=collect_code_revision(),
        python_version="3.11",
        dependency_versions=collect_dependency_versions(["pydantic", "missing-package-for-test"]),
        dataset_summary={"Dice_Count": 1},
        prompt_config=PromptConfig(
            prompt_mode="opt",
            prompts_file="prompts.yaml",
            prompts_file_sha256="a" * 64,
            few_shot_config="few.yaml",
            few_shot_config_sha256="b" * 64,
            prompt_prefix_sha256="c" * 64,
            prompt_suffix_sha256="d" * 64,
        ),
        provider="openai",
        model="gpt-5",
        output_paths={},
    )


def _attempt(run_id: str, attempt_id: str, task_type: str, correct: bool) -> AttemptRecord:
    return AttemptRecord(
        run_id=run_id,
        attempt_id=attempt_id,
        task_type=task_type,
        puzzle_id=attempt_id,
        attempt_index=1,
        prompt_mode="opt",
        provider="openai",
        model="gpt-5",
        parsed_answer={"answer": 1},
        correct=correct,
        timestamp=utc_now(),
    )


def test_run_manifest_serializes_schema_version() -> None:
    manifest = _manifest()

    assert RUN_MANIFEST_SCHEMA_VERSION in manifest.model_dump_json()
    assert manifest.model_json_schema()["title"] == "RunManifest"


def test_writer_writes_manifest_before_summaries(tmp_path) -> None:
    writer = RevisionArtifactWriter(tmp_path, "run-1")
    manifest_path = writer.write_manifest(_manifest())

    assert manifest_path == writer.manifest_path
    assert writer.manifest_path.exists()
    assert not writer.summary_csv_path.exists()
    assert not writer.summary_json_path.exists()


def test_append_attempt_writes_one_json_object_per_line(tmp_path) -> None:
    writer = RevisionArtifactWriter(tmp_path, "run-1")

    writer.append_attempt(_attempt("run-1", "one", "Dice_Count", True))
    writer.append_attempt(_attempt("run-1", "two", "Dice_Count", False))

    lines = writer.attempts_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert [json.loads(line)["attempt_id"] for line in lines] == ["one", "two"]


def test_write_summaries_from_attempts_derives_csv_and_json(tmp_path) -> None:
    writer = RevisionArtifactWriter(tmp_path, "run-1")
    writer.append_attempt(_attempt("run-1", "one", "Dice_Count", True))
    writer.append_attempt(_attempt("run-1", "two", "Dice_Count", False))
    writer.append_attempt(_attempt("run-1", "three", "Patch_Select", True))

    csv_path, json_path = writer.write_summaries_from_attempts()

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with json_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    assert {row["task_type"] for row in rows} == {"Dice_Count", "Patch_Select"}
    dice_row = next(row for row in rows if row["task_type"] == "Dice_Count")
    assert dice_row["n_attempts"] == "2"
    assert dice_row["n_success"] == "1"
    assert float(dice_row["pass_rate"]) == 0.5
    assert len(payload["rows"]) == 2


def test_existing_run_dir_requires_overwrite_or_resume(tmp_path) -> None:
    RevisionArtifactWriter(tmp_path, "run-1")

    with pytest.raises(FileExistsError):
        RevisionArtifactWriter(tmp_path, "run-1")

    assert RevisionArtifactWriter(tmp_path, "run-1", resume=True).run_dir.exists()
    assert RevisionArtifactWriter(tmp_path, "run-1", overwrite=True).run_dir.exists()


def test_sha256_helpers_and_prompt_config_hash_keys(tmp_path) -> None:
    prompts_path = tmp_path / "prompts.yaml"
    prompts_path.write_text("types: {}\n", encoding="utf-8")

    assert sha256_file(prompts_path) == sha256_file(str(prompts_path))
    assert sha256_file(None) is None
    assert sha256_text("prefix") == sha256_text("prefix")
    assert sha256_text(None) is None

    digest = sha256_file(prompts_path)
    text_digest = sha256_text("prefix")
    assert digest is not None and len(digest) == 64 and digest == digest.lower()
    assert text_digest is not None and len(text_digest) == 64 and text_digest == text_digest.lower()

    prompt_config = PromptConfig(
        prompt_mode="opt",
        prompts_file=str(prompts_path),
        prompts_file_sha256=digest,
        few_shot_config="few.yaml",
        few_shot_config_sha256="e" * 64,
        prompt_prefix_sha256=text_digest,
        prompt_suffix_sha256=sha256_text("suffix"),
    ).model_dump()

    assert set(prompt_config) >= {
        "prompts_file_sha256",
        "few_shot_config_sha256",
        "prompt_prefix_sha256",
        "prompt_suffix_sha256",
    }
