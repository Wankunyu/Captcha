import subprocess
import sys


UNSAFE_OUTPUT_MARKERS = (
    "secrets.yaml exists?",
    "TEXT OK:",
    "providers",
    "api_key",
)


def _run_imports(statement: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", statement],
        capture_output=True,
        text=True,
        check=False,
    )


def _combined_output(result: subprocess.CompletedProcess[str]) -> str:
    return f"{result.stdout}\n{result.stderr}"


def test_run_eval_and_wrapper_imports_are_quiet() -> None:
    result = _run_imports("import run_eval; import run_single_experiment")
    output = _combined_output(result)

    assert result.returncode == 0, output
    for marker in UNSAFE_OUTPUT_MARKERS:
        assert marker not in output


def test_revision_provider_smoke_import_does_not_construct_provider() -> None:
    result = _run_imports(
        "import run_eval\n"
        "def fail(*args, **kwargs):\n"
        "    raise AssertionError('make_provider should not be called on import')\n"
        "run_eval.make_provider = fail\n"
        "import revision_provider_smoke\n"
    )
    output = _combined_output(result)

    assert result.returncode == 0, output
    for marker in UNSAFE_OUTPUT_MARKERS:
        assert marker not in output


def test_revision_provider_smoke_help_does_not_read_secrets() -> None:
    result = subprocess.run(
        [sys.executable, "revision_provider_smoke.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    output = _combined_output(result)

    assert result.returncode == 0, output
    assert "secrets.yaml exists?" not in output
    assert "api_key" not in output
