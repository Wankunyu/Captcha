import importlib.util
from pathlib import Path


def _load_packager():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "build_artifact_package.py"
    spec = importlib.util.spec_from_file_location("build_artifact_package", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_submission_package_excludes_local_workflow_and_secret_paths() -> None:
    packager = _load_packager()

    excluded_paths = [
        ".planning/ROADMAP.md",
        "AGENTS.md",
        ".codex/state.json",
        ".claude/settings.json",
        "secrets.yaml",
        "secrets.local.yaml",
        ".env",
        ".venv/lib/python.py",
        "__pycache__/run_eval.pyc",
        "tests/__pycache__/test.pyc",
        "captcha_data/.DS_Store",
        "results/local_runs/local-run/attempts.jsonl",
        "results/local_runs/phase04_2_static_openai/run-static.sh",
        "results/local_runs/phase04_2_static_openai/collect-static.background.log",
        "dist/cognition.tar.gz",
    ]

    for path in excluded_paths:
        assert packager.is_excluded(path), path


def test_submission_package_keeps_core_artifact_paths() -> None:
    packager = _load_packager()

    included_paths = [
        "README.md",
        "SUBMISSION.md",
        "pyproject.toml",
        "uv.lock",
        "cognition/run_eval.py",
        "cognition/revision_preflight.py",
        "secrets.example.yaml",
        "captcha_data/Dice_Count/ground_truth.json",
        "few_shot_assets/Dice_Count/dice1.jpg",
        "results/exp1/openai/gpt-5/results.csv",
        "results/exp5/final_outputs_20260522/corrected_expanded_table_rows.csv",
        "figures/heatmap_exp1.pdf",
        "tests/test_revision_preflight.py",
    ]

    for path in included_paths:
        assert not packager.is_excluded(path), path
