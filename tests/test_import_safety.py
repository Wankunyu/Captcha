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
    result = _run_imports("import cognition.run_eval; import cognition.run_single_experiment")
    output = _combined_output(result)

    assert result.returncode == 0, "import subprocess failed"
    for marker in UNSAFE_OUTPUT_MARKERS:
        if marker in output:
            raise AssertionError(f"unsafe marker emitted during import: {marker!r}")


def test_revision_provider_smoke_import_does_not_construct_provider() -> None:
    result = _run_imports(
        "import cognition.run_eval as run_eval\n"
        "def fail(*args, **kwargs):\n"
        "    raise AssertionError('make_provider should not be called on import')\n"
        "run_eval.make_provider = fail\n"
        "import cognition.revision_provider_smoke\n"
    )
    output = _combined_output(result)

    assert result.returncode == 0, "revision_provider_smoke import subprocess failed"
    for marker in UNSAFE_OUTPUT_MARKERS:
        if marker in output:
            raise AssertionError(f"unsafe marker emitted during smoke import: {marker!r}")


def test_revision_provider_smoke_help_does_not_read_secrets() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "cognition.revision_provider_smoke", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    output = _combined_output(result)

    assert result.returncode == 0, "revision_provider_smoke --help failed"
    if "secrets.yaml exists?" in output:
        raise AssertionError("help emitted import-time secrets diagnostic")
    if "api_key" in output:
        raise AssertionError("help emitted credential field name")
