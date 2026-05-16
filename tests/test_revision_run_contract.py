import json
from pathlib import Path

import pytest
import yaml

import run_eval
from revision_artifacts import RevisionArtifactWriter, sha256_file


class FakeProvider:
    def __init__(self, events: list[str] | None = None) -> None:
        self.events = events

    def infer(self, **kwargs):
        return (
            '{"answer_type":"number","value":3}',
            {"answer_type": "number", "value": 3},
            {"e2e_ms": 12.0, "ttft_ms": 3.0, "tokens_in": 10, "tokens_out": 5},
        )


def _write_config(path: Path) -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "pricing": {
                    "openai": {
                        "gpt-5": {
                            "in_per_1k": 0.001,
                            "out_per_1k": 0.002,
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )


def _write_yaml(path: Path, payload: object) -> None:
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")


def _patch_single_task(monkeypatch) -> None:
    task = run_eval.TaskItem(
        type="Dice_Count",
        puzzle_id="dice1.png",
        prompt="Count the dice.",
        images=[],
        gt={"sum": 3},
    )
    monkeypatch.setattr(run_eval, "build_tasks", lambda *args, **kwargs: [task])


def _run_revision_eval(
    tmp_path: Path,
    monkeypatch,
    *,
    run_id: str = "run-1",
    events: list[str] | None = None,
    few_shot_config: dict | None = None,
    few_shot_file: Path | None = None,
) -> dict:
    _patch_single_task(monkeypatch)
    secrets_file = tmp_path / "local-config.yaml"
    prompts_file = tmp_path / "prompts.yaml"
    _write_config(secrets_file)
    _write_yaml(prompts_file, {"types": {"Dice_Count": "count dice"}})

    def fake_make_provider(*args, **kwargs):
        if events is not None:
            events.append("provider")
        return FakeProvider(events)

    monkeypatch.setattr(run_eval, "make_provider", fake_make_provider)

    return run_eval.run_eval(
        dataset_root=str(tmp_path / "captcha_data"),
        types=["Dice_Count"],
        provider="openai",
        model="gpt-5",
        max_per_type=1,
        out_csv=str(tmp_path / "legacy.csv"),
        secrets_file=str(secrets_file),
        stream=False,
        prompts_file=str(prompts_file),
        prompt_mode="opt",
        few_shot_config=few_shot_config,
        few_shot_file=str(few_shot_file) if few_shot_file else "./few_shot_examples.yaml",
        revision_run_id=run_id,
        revision_output_root=str(tmp_path / "results" / "revision"),
        write_attempts=True,
    )


def test_revision_run_requires_write_attempts_before_loading_secrets(tmp_path, monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError("load_secrets should not run")

    monkeypatch.setattr(run_eval, "load_secrets", fail)

    with pytest.raises(ValueError, match="revision runs require write_attempts=True"):
        run_eval.run_eval(
            dataset_root=str(tmp_path / "captcha_data"),
            types=["Dice_Count"],
            revision_run_id="run-1",
            write_attempts=False,
        )


def test_existing_revision_output_requires_overwrite_or_resume(tmp_path, monkeypatch) -> None:
    _patch_single_task(monkeypatch)
    secrets_file = tmp_path / "local-config.yaml"
    _write_config(secrets_file)
    (tmp_path / "results" / "revision" / "dupe").mkdir(parents=True)

    with pytest.raises(FileExistsError):
        run_eval.run_eval(
            dataset_root=str(tmp_path / "captcha_data"),
            types=["Dice_Count"],
            out_csv=str(tmp_path / "legacy.csv"),
            secrets_file=str(secrets_file),
            revision_run_id="dupe",
            revision_output_root=str(tmp_path / "results" / "revision"),
            write_attempts=True,
        )


def test_revision_mode_writes_manifest_attempts_and_summaries(tmp_path, monkeypatch) -> None:
    _run_revision_eval(tmp_path, monkeypatch)

    run_dir = tmp_path / "results" / "revision" / "run-1"
    assert (run_dir / "run_manifest.json").exists()
    assert (run_dir / "attempts.jsonl").exists()
    assert (run_dir / "summary.csv").exists()
    assert (run_dir / "summary.json").exists()
    assert len((run_dir / "attempts.jsonl").read_text(encoding="utf-8").splitlines()) == 1


def test_manifest_attempt_summary_order(tmp_path, monkeypatch) -> None:
    events: list[str] = []
    original_manifest = RevisionArtifactWriter.write_manifest
    original_attempt = RevisionArtifactWriter.append_attempt
    original_summary = RevisionArtifactWriter.write_summaries_from_attempts

    def record_manifest(self, manifest):
        events.append("manifest")
        assert manifest.cost_control["expected_request_count"] == 1
        assert "unavailable_reason" in manifest.cost_control
        return original_manifest(self, manifest)

    def record_attempt(self, attempt):
        events.append("attempt")
        return original_attempt(self, attempt)

    def record_summary(self):
        events.append("summary")
        return original_summary(self)

    monkeypatch.setattr(RevisionArtifactWriter, "write_manifest", record_manifest)
    monkeypatch.setattr(RevisionArtifactWriter, "append_attempt", record_attempt)
    monkeypatch.setattr(RevisionArtifactWriter, "write_summaries_from_attempts", record_summary)

    _run_revision_eval(tmp_path, monkeypatch, events=events)

    assert events == ["manifest", "provider", "attempt", "summary"]


def test_manifest_records_few_shot_file_digest(tmp_path, monkeypatch) -> None:
    few_shot_file = tmp_path / "few-shot.yaml"
    _write_yaml(few_shot_file, {"Dice_Count": {"examples": []}})

    _run_revision_eval(
        tmp_path,
        monkeypatch,
        run_id="few-shot-run",
        few_shot_config={"enabled": True, "n_shot": 1},
        few_shot_file=few_shot_file,
    )

    manifest = json.loads(
        (tmp_path / "results" / "revision" / "few-shot-run" / "run_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    prompt_config = manifest["prompt_config"]
    assert prompt_config["few_shot_config"] == str(few_shot_file)
    assert prompt_config["few_shot_config_sha256"] == sha256_file(few_shot_file)


def test_manifest_cost_control_is_available_before_provider(tmp_path, monkeypatch) -> None:
    _run_revision_eval(tmp_path, monkeypatch, run_id="cost-run")

    manifest = json.loads(
        (tmp_path / "results" / "revision" / "cost-run" / "run_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    cost_control = manifest["cost_control"]
    assert cost_control["expected_request_count"] == 1
    assert "approximate_cost_usd" in cost_control or "unavailable_reason" in cost_control


def test_resume_revision_output_does_not_duplicate_attempts(tmp_path, monkeypatch) -> None:
    _run_revision_eval(tmp_path, monkeypatch, run_id="resume-run")

    def fail_provider(*args, **kwargs):
        raise AssertionError("resume should skip completed attempts before provider construction")

    monkeypatch.setattr(run_eval, "make_provider", fail_provider)
    run_eval.run_eval(
        dataset_root=str(tmp_path / "captcha_data"),
        types=["Dice_Count"],
        provider="openai",
        model="gpt-5",
        max_per_type=1,
        out_csv=str(tmp_path / "legacy-resume.csv"),
        secrets_file=str(tmp_path / "local-config.yaml"),
        stream=False,
        prompts_file=str(tmp_path / "prompts.yaml"),
        prompt_mode="opt",
        revision_run_id="resume-run",
        revision_output_root=str(tmp_path / "results" / "revision"),
        write_attempts=True,
        resume_revision_output=True,
    )

    run_dir = tmp_path / "results" / "revision" / "resume-run"
    attempts = (run_dir / "attempts.jsonl").read_text(encoding="utf-8").splitlines()
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))

    assert len(attempts) == 1
    assert summary["rows"][0]["n_attempts"] == 1
