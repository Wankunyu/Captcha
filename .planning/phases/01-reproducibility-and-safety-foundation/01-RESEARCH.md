# Phase 1: Reproducibility and Safety Foundation - Research

**Researched:** 2026-05-15
**Domain:** Python research-tooling reproducibility, offline experiment preflight, artifact schemas, import safety, and secret-safe reporting
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Packaging and Environment Scope

- **D-01:** Add `pyproject.toml` as the machine-readable dependency and tooling manifest.
- **D-02:** Use `uv` to generate and maintain a lockfile for reproducible installs.
- **D-03:** Add `pytest` and `ruff` as development tools for local validation.
- **D-04:** Do not turn Phase 1 into a broad package migration. Keep the existing script-oriented workflow usable while adding the minimum structure needed for reproducible revision work.

### Artifact Contract Shape

- **D-05:** Define a versioned revision artifact contract with `run_manifest.json`, optional `attempts.jsonl`, and derived CSV/JSON summaries.
- **D-06:** Use Pydantic schemas for run manifests, attempt rows, and summary rows.
- **D-07:** Attempt logging is controlled by a flag rather than mandatory for every new revision experiment.
- **D-08:** Write new revision artifacts under `results/revision/<run_id>/` so revision outputs do not mix into legacy `results/exp1` through `results/exp4` layouts.

### Secret Safety and Import Side Effects

- **D-09:** Phase 1 should remove or isolate all import-time side effects from `run_eval.py`. Importing `run_eval` must not read or print secrets and must not send provider API requests.
- **D-10:** Keep local `secrets.yaml` support for existing workflows, but add `secrets.example.yaml` and redacted loader/reporting behavior for shareable outputs.
- **D-11:** Do not automatically remove tracked `secrets.yaml` or rewrite repository history in Phase 1. Protect future artifacts so they never read or output credential values.
- **D-12:** Move provider smoke tests into an explicit CLI command or script that never runs by default.

### Validation and Test Coverage Boundary

- **D-13:** Cover new Phase 1 code plus high-risk legacy behavior through non-invasive tests or validators where that behavior affects revision credibility.
- **D-14:** Do not make old scoring bug fixes a Phase 1 goal. Existing scoring risks may be surfaced by validators or documented diagnostics, but Phase 1 should avoid broad scoring changes.
- **D-15:** Preflight should validate task aliases, dataset files, prompt files, output directory, and expected request counts.
- **D-16:** Provide local `pytest` and `ruff` commands and runnable tests. Do not require GitHub Actions in Phase 1.

### Claude's Discretion

- The planner may choose exact file/module names for Phase 1 helper code, as long as the existing script workflow remains usable.
- The planner may decide whether Pydantic schemas live in a root-level module, a small package directory, or a dedicated revision utility file.
- The planner may choose exact local command names for preflight, validation, provider smoke tests, and artifact schema checks.
- The planner may choose whether high-risk legacy scoring checks are implemented as pytest tests, preflight warnings, diagnostics, or documented validators, provided they do not expand into a broad scoring refactor.

### Deferred Ideas (OUT OF SCOPE)

- Adaptive/session-memory attacker implementation belongs to Phase 3.
- Statistical confidence intervals, threshold sensitivity, and Bernoulli calibration belong to Phase 2.
- Specialized solver and larger-dataset baselines belong to Phase 4.
- Defense methodology artifacts belong to Phase 5.
- Formal CI integration, broad evaluator refactor, full secret-history cleanup, and complete scoring repair are not Phase 1 goals unless later planning identifies a narrow blocker.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REPRO-01 | Researcher can install the project from a machine-readable dependency manifest instead of README-only install commands. | Add `pyproject.toml`, `uv.lock`, `pytest`, and `ruff` while preserving the flat script workflow. [VERIFIED: .planning/phases/01-reproducibility-and-safety-foundation/01-CONTEXT.md; README.md:39-49; PyPA pyproject guide] |
| REPRO-02 | Researcher can run a preflight command that validates task names, dataset paths, prompt files, output paths, and expected request counts before paid model calls. | Add an offline `revision_preflight.py`-style CLI that does not import provider clients or read secrets. [VERIFIED: run_eval.py:1797-2328; run_eval.py:1453-1486; .planning/phases/01-reproducibility-and-safety-foundation/01-PATTERNS.md] |
| REPRO-03 | Every revision experiment writes a run manifest containing schema version, code revision, dependency versions, dataset summary, prompt configuration, provider/model labels, seed, retry policy, and cost-control metadata. | Use Pydantic `RunManifest` and write `results/revision/<run_id>/run_manifest.json` before any provider call. [VERIFIED: .planning/REQUIREMENTS.md; CITED: Context7 /pydantic/pydantic] |
| REPRO-04 | Every revision experiment writes append-only per-attempt records before deriving aggregate summaries. | Define `AttemptRecord` and append JSONL rows before summary derivation; default the flag on for revision provider-call runs while keeping D-07 opt-in control for legacy or diagnostic workflows. [VERIFIED: .planning/REQUIREMENTS.md; .planning/phases/01-reproducibility-and-safety-foundation/01-CONTEXT.md] |
| REPRO-05 | Shareable reports and planning artifacts do not print, copy, or commit credential values from local secret configuration. | Remove import-time secret reads/prints, add `secrets.example.yaml`, add redaction helpers, and test fake sentinel leakage. [VERIFIED: run_eval.py:35-47; git ls-files -- secrets.yaml; .gitignore:1-15; CITED: OWASP ASVS V13.3.1] |
| REPRO-06 | Revision-critical task aliases, result schemas, and scoring helpers have focused regression tests or validators. | Add non-invasive tests/validators for import safety, alias drift, schema validation, summary-row derivation, and known crash surfaces without broad scorer migration. [VERIFIED: run_eval.py:1384-1412; run_eval.py:2348-2558; .planning/codebase/CONCERNS.md] |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- Interactive discussion with the user must stay in Chinese, while planning documents, code comments, generated reports, and project artifacts must stay in English unless explicitly requested otherwise. [VERIFIED: AGENTS.md]
- Experiments must remain offline and dataset-based; Phase 1 must not build live CAPTCHA attack automation or browser automation against real services. [VERIFIED: AGENTS.md; .planning/PROJECT.md]
- `secrets.yaml` is sensitive local configuration; do not print, quote, copy, summarize, or commit credential values. [VERIFIED: AGENTS.md]
- Prefer reproducible scripted artifacts over notebook-only manual state. [VERIFIED: AGENTS.md; .planning/PROJECT.md]
- Preserve existing experiment semantics unless a phase explicitly plans a migration. [VERIFIED: AGENTS.md; .planning/phases/01-reproducibility-and-safety-foundation/01-CONTEXT.md]
- Avoid broad refactors unless they protect experiment correctness, reproducibility, or artifact integrity. [VERIFIED: AGENTS.md; .planning/PROJECT.md]

## Summary

Phase 1 should be planned as a narrow foundation layer around the existing flat Python scripts, not as a package rewrite. The current repository has no `pyproject.toml`, no lockfile, no formal test directory, and no configured linter, while the README still provides dependency installation as manual `pip install` commands. [VERIFIED: README.md:39-49; rg --files for `pyproject.toml`, `uv.lock`, tests, and ruff config]

The first implementation dependency is import safety. `run_eval.py` currently performs module-scope diagnostics, reads local secret configuration, prints the parsed config, and has an unguarded provider smoke call near the bottom of the file; `run_single_experiment.py` imports `run_eval.py` at module load. Planning must therefore sequence import-safety cleanup before tests, preflight, or wrapper CLIs rely on importing evaluator primitives. [VERIFIED: run_eval.py:35-47; run_eval.py:3307-3314; run_single_experiment.py:13-22]

The primary recommendation is to add small root-level helper modules that match the current script style: `revision_secrets.py`, `revision_artifacts.py`, `revision_preflight.py`, and `revision_provider_smoke.py`, plus focused tests under `tests/`. This preserves existing experiment entry points while creating the reproducibility, secret-safety, manifest, attempt-log, and validation contracts later phases need. [VERIFIED: .planning/phases/01-reproducibility-and-safety-foundation/01-CONTEXT.md; .planning/phases/01-reproducibility-and-safety-foundation/01-PATTERNS.md]

**Primary recommendation:** Plan Phase 1 in this order: tooling manifest and lockfile, import-safety cleanup, secret-safe loader/redaction, Pydantic artifact schemas/writer, offline preflight validators, and focused pytest/ruff verification. [VERIFIED: .planning/REQUIREMENTS.md; .planning/codebase/CONCERNS.md; CITED: Context7 /astral-sh/uv; Context7 /pydantic/pydantic; Context7 /pytest-dev/pytest; Context7 /astral-sh/ruff]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Machine-readable install and lockfile | Tooling / Local Environment | Documentation | `pyproject.toml` and `uv.lock` own reproducible dependency resolution; README should only explain commands. [VERIFIED: README.md:39-49; CITED: PyPA pyproject guide; Context7 /astral-sh/uv] |
| Import safety | Existing Evaluation Core | Test Suite | `run_eval.py` owns the unsafe module-scope behavior; pytest should prove imports are side-effect free. [VERIFIED: run_eval.py:35-47; run_eval.py:3307-3314; run_single_experiment.py:13-22] |
| Secret loading/redaction | Secret Utility Module | Existing Evaluation Core | Local config support remains, but all diagnostics and shareable outputs need one redaction path. [VERIFIED: .planning/phases/01-reproducibility-and-safety-foundation/01-CONTEXT.md; OWASP ASVS V13.3.1] |
| Preflight validation | Offline CLI / Validator | Task Data Layer | Preflight should inspect datasets, aliases, prompts, output paths, and request counts without constructing providers. [VERIFIED: run_eval.py:1797-2328; run_eval.py:1453-1486] |
| Run manifest and attempt records | Artifact Layer | Experiment Runner | Pydantic schemas should define revision artifacts under `results/revision/<run_id>/`; legacy result directories remain compatible. [VERIFIED: .planning/REQUIREMENTS.md; .planning/phases/01-reproducibility-and-safety-foundation/01-CONTEXT.md] |
| Provider smoke tests | Explicit CLI | Provider Adapter Layer | Smoke tests may use existing provider adapters, but only behind explicit commands and never during import/preflight. [VERIFIED: run_eval.py:1318-1359; run_eval.py:3307-3314] |
| Task alias/schema/scoring validators | Test Suite / Preflight | Existing Evaluation Core | Validators should detect drift like `Connect_Icon` versus `Connect_icon` and scoring/schema mismatches without forcing broad scorer fixes. [VERIFIED: task/dataset comparison command; run_eval.py:1384-1412; run_eval.py:2073-2108; run_eval.py:2404-2407; run_eval.py:2527-2530] |

## Standard Stack

### Core

| Library / Tool | Version | Purpose | Why Standard |
|----------------|---------|---------|--------------|
| Python | `>=3.10`; local interpreter is 3.11.5 | Runtime for existing scripts and new helper modules | README requires Python 3.10+ and current code uses Python 3.10+ syntax such as `str | None`. [VERIFIED: README.md:39; python3 --version; .planning/codebase/STACK.md] |
| `pyproject.toml` | Project manifest, not package migration | Dependencies plus pytest/ruff/uv config | PyPA documents `pyproject.toml` as the standard configuration file for package metadata and tool tables. [CITED: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/] |
| `uv` | Latest PyPI 0.11.14, published 2026-05-12 | Lockfile generation and local sync | Context7 documents `uv lock`, `uv sync`, and `uv sync --locked`; Phase 1 locked D-02 to uv. [VERIFIED: PyPI JSON API; CITED: Context7 /astral-sh/uv] |
| `pydantic` | Latest PyPI 2.13.4, published 2026-05-06 | Manifest, attempt, and summary schemas | Pydantic v2 provides `BaseModel`, `model_validate`, `model_validate_json`, and `model_json_schema` for runtime validation and JSON Schema generation. [VERIFIED: PyPI JSON API; CITED: Context7 /pydantic/pydantic] |
| `pytest` | Latest PyPI 9.0.3, published 2026-04-07 | Focused tests for Phase 1 and high-risk legacy behavior | pytest supports project configuration in `pyproject.toml` and has a stable fixture/subprocess-friendly model for import/output tests. [VERIFIED: PyPI JSON API; CITED: Context7 /pytest-dev/pytest] |
| `ruff` | Latest PyPI 0.15.13, published 2026-05-14 | Lightweight lint and format checks | Ruff supports `ruff check`, `ruff format`, and `pyproject.toml` rule configuration. [VERIFIED: PyPI JSON API; CITED: Context7 /astral-sh/ruff] |

### Existing Runtime Dependencies to Declare and Lock

| Dependency | Local Installed Version | Latest Verified Version | Phase 1 Guidance |
|------------|-------------------------|-------------------------|------------------|
| `openai` | 2.6.1 | 2.36.0, published 2026-05-07 | Declare and lock the currently working version first; defer provider SDK upgrades until provider contract tests exist. [VERIFIED: importlib.metadata; PyPI JSON API; .planning/codebase/CONCERNS.md] |
| `anthropic` | 0.72.0 | 0.102.0, published 2026-05-13 | Lock the current baseline first because provider payload and metadata parsing are high-risk surfaces. [VERIFIED: importlib.metadata; PyPI JSON API; .planning/codebase/CONCERNS.md] |
| `google-genai` | 1.39.1 | 2.2.0, published 2026-05-12 | Do not silently cross a major version during Phase 1; provider smoke tests must be explicit. [VERIFIED: importlib.metadata; PyPI JSON API; run_eval.py:3307-3314] |
| `Pillow` | 10.0.1 | 12.2.0, published 2026-04-01 | Lock current image behavior first; image encoding affects provider payloads. [VERIFIED: importlib.metadata; PyPI JSON API; .planning/codebase/STACK.md] |
| `PyYAML` | 6.0.2 | 6.0.3, published 2025-09-25 | Keep for prompt/few-shot/local config parsing; do not use it to dump secrets into logs. [VERIFIED: importlib.metadata; PyPI JSON API; run_eval.py:120-131; run_eval.py:1453-1486] |
| `tqdm` | 4.65.0 | 4.67.3, published 2026-02-03 | Keep for progress bars in existing evaluation loops. [VERIFIED: importlib.metadata; PyPI JSON API; run_eval.py:14-18] |
| `numpy`, `pandas`, `matplotlib`, `seaborn`, `adjustText` | numpy 1.24.3, pandas 1.5.3, matplotlib 3.7.1, seaborn 0.12.2, adjustText 1.3.0 | Latest versions verified via PyPI JSON API | Declare these for existing analysis/visualization compatibility; broad analysis upgrades belong outside Phase 1 unless tests force them. [VERIFIED: importlib.metadata; PyPI JSON API; .planning/codebase/STACK.md] |

### Supporting

| Library / Tool | Version | Purpose | When to Use |
|----------------|---------|---------|-------------|
| Git | local 2.51.2 | Code revision capture in manifests | Required for `code_revision` and dirty-state metadata. [VERIFIED: git --version] |
| Git LFS | local 3.7.1 | Materialized dataset files under `captcha_data/**` | Preflight should detect LFS pointer files before model calls. [VERIFIED: git lfs version; .gitattributes; run_eval.py load_ground_truth pattern in 01-PATTERNS.md] |
| `argparse` | Python stdlib | CLI commands | Existing CLIs use `argparse`; adding Typer/Click is unnecessary churn for Phase 1. [VERIFIED: run_single_experiment.py:495-618; exp2_to_exp3_predict.py pattern in 01-PATTERNS.md] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Root-level helper modules | Full `src/` package migration | A package migration could clean boundaries but conflicts with D-04 and increases risk before import-safety/tests exist. [VERIFIED: .planning/phases/01-reproducibility-and-safety-foundation/01-CONTEXT.md] |
| `uv` | pip-only `requirements.txt` | pip-only installs are simpler but do not satisfy D-02's uv lockfile decision. [VERIFIED: .planning/phases/01-reproducibility-and-safety-foundation/01-CONTEXT.md] |
| Pydantic | Ad hoc dict validation | Hand-written validators are easy to drift and do not provide JSON Schema for artifact contracts. [CITED: Context7 /pydantic/pydantic] |
| pytest + ruff | GitHub Actions first | D-16 explicitly says Phase 1 should not require GitHub Actions; local commands are enough. [VERIFIED: .planning/phases/01-reproducibility-and-safety-foundation/01-CONTEXT.md] |

**Installation:**

```bash
python3 -m pip install uv==0.11.14
uv sync
uv run pytest
uv run ruff check .
```

`uv` is not currently installed in the active shell, so planning must include either a documented uv bootstrap step or an executor prerequisite. [VERIFIED: `command -v uv` returned no path; PyPI JSON API verified uv 0.11.14]

**Recommended pyproject shape:**

```toml
[project]
name = "cognition-revision-experiments"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
  "openai==2.6.1",
  "anthropic==0.72.0",
  "google-genai==1.39.1",
  "Pillow==10.0.1",
  "PyYAML==6.0.2",
  "tqdm==4.65.0",
  "numpy==1.24.3",
  "pandas==1.5.3",
  "matplotlib==3.7.1",
  "seaborn==0.12.2",
  "adjustText==1.3.0",
  "pydantic==2.13.4",
]

[dependency-groups]
dev = [
  "pytest==9.0.3",
  "ruff==0.15.13",
]

[tool.uv]
package = false

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra -q"

[tool.ruff]
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F"]
```

Use `tool.uv.package = false` if Phase 1 keeps the project as flat scripts without installing the project package itself; uv documents this setting for flat/script-style projects that do not need package installation. [CITED: https://docs.astral.sh/uv/concepts/projects/config/]

## Architecture Patterns

### System Architecture Diagram

```text
Developer CLI input
  |
  v
revision_preflight.py -- offline validation only
  |-- task aliases + dataset paths + prompt/few-shot config
  |-- output directory safety + expected request counts
  |-- manifest preview without provider clients or secrets
  v
results/revision/<run_id>/run_manifest.json
  |
  v
Existing experiment wrapper / future revision runner
  |
  |-- explicit provider smoke command only when requested
  |-- existing run_eval primitives after import-safety cleanup
  v
Provider call boundary
  |
  v
append attempts.jsonl row before aggregate summary
  |
  v
derive summary.csv + summary.json from attempt records
  |
  v
later phases consume versioned artifacts for stats, adaptive runs, baselines, and paper QA
```

This data flow keeps preflight offline, keeps provider calls explicit, and makes append-only attempt records the source of truth for revision summaries. [VERIFIED: .planning/REQUIREMENTS.md; .planning/phases/01-reproducibility-and-safety-foundation/01-CONTEXT.md]

### Recommended Project Structure

```text
.
|-- pyproject.toml
|-- uv.lock
|-- secrets.example.yaml
|-- revision_secrets.py
|-- revision_artifacts.py
|-- revision_preflight.py
|-- revision_provider_smoke.py
|-- run_eval.py
|-- run_single_experiment.py
|-- tests/
|   |-- test_import_safety.py
|   |-- test_revision_secrets.py
|   |-- test_revision_artifacts.py
|   |-- test_revision_preflight.py
|   |-- test_task_contracts.py
|   `-- test_scoring_regressions.py
`-- results/
    `-- revision/
        `-- <run_id>/
            |-- run_manifest.json
            |-- attempts.jsonl
            |-- summary.csv
            `-- summary.json
```

This structure follows the pattern mapper's closest analogs: secret utilities mirror `run_eval.load_secrets()` without side effects, artifact writing mirrors `experiments_helper.py` and token/result writers, preflight mirrors standalone `argparse` utilities, and generated revision artifacts stay out of legacy `results/exp*` layouts. [VERIFIED: .planning/phases/01-reproducibility-and-safety-foundation/01-PATTERNS.md]

### Pattern 1: Import-Safe Compatibility Core

**What:** Move module-scope diagnostics and provider smoke calls from `run_eval.py` into explicit functions or guarded CLIs. [VERIFIED: run_eval.py:35-47; run_eval.py:3307-3314]

**When to use:** This must be first or near-first in Phase 1, because tests and preflight need to import evaluator constants/helpers safely. [VERIFIED: run_single_experiment.py:13-22]

**Example:**

```python
def run_provider_smoke(provider: str, model: str, secrets_file: str) -> int:
    # Source: local pattern from run_eval.make_provider(), but explicit and opt-in.
    secrets = load_secrets(secrets_file)
    client = make_provider(provider, model, secrets, timeout_sec=30.0)
    raw, parsed, meta = client.infer(
        prompt="Return JSON only.",
        images=[],
        json_schema={"type": "object", "properties": {}, "required": []},
        stream=False,
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

Do not include any real credential value in this script or in its tests. [VERIFIED: AGENTS.md; OWASP ASVS V13.3.1]

### Pattern 2: Pydantic Artifact Schemas

**What:** Define `RunManifest`, `AttemptRecord`, and `SummaryRow` as Pydantic models, then use `model_validate`, `model_validate_json`, and `model_json_schema` for validation and schema export. [CITED: Context7 /pydantic/pydantic]

**When to use:** Use for every revision artifact under `results/revision/<run_id>/`. [VERIFIED: .planning/REQUIREMENTS.md]

**Example:**

```python
from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel, Field


class RunManifest(BaseModel):
    schema_version: str = "cognition.revision.run_manifest.v1"
    run_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    code_revision: dict[str, str | bool]
    dependency_versions: dict[str, str]
    dataset_summary: dict[str, object]
    prompt_config: dict[str, object]
    provider: str
    model: str
    seed: int | None = None
    retry_policy: dict[str, object] = Field(default_factory=dict)
    cost_control: dict[str, object] = Field(default_factory=dict)


def write_manifest(path: Path, manifest: RunManifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
```

### Pattern 3: Offline Preflight Before Provider Construction

**What:** Validate selected tasks, dataset files, prompt/few-shot config, output path safety, and expected request counts without calling `load_secrets()` or `make_provider()`. [VERIFIED: run_eval.py:120-131; run_eval.py:1318-1359; run_eval.py:1797-2328]

**When to use:** Use before any paid provider run, including future adaptive and baseline smoke subsets. [VERIFIED: AGENTS.md; .planning/ROADMAP.md]

**Expected request count formula:** single-pass revision runs should estimate selected task count after `max_per_type` and exclusions; until-correct or retry policies should estimate `selected_task_or_type_count * max_attempts` unless the policy has a stricter stop condition. [VERIFIED: run_eval.py:2575-2945; run_eval.py:2967-3210]

### Pattern 4: One Secret Redaction Path

**What:** Provide `load_local_config()` and `redact_mapping()` in `revision_secrets.py`, and ensure diagnostics/artifacts call redaction before printing or writing. [VERIFIED: run_eval.py:120-131; run_eval.py:35-47]

**When to use:** Any code path that touches local provider config, diagnostics, manifests, or shareable reports. [VERIFIED: AGENTS.md; OWASP ASVS V13.3.1]

**Example:**

```python
SECRET_KEYS = {"api_key", "access_token", "secret", "password", "token"}


def redact_mapping(value):
    if isinstance(value, dict):
        return {
            key: "<redacted>" if key.lower() in SECRET_KEYS else redact_mapping(child)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [redact_mapping(item) for item in value]
    return value
```

## Pattern Map Integration

The pattern mapper found direct or role-match analogs for 13 of 21 planned files/artifacts. [VERIFIED: .planning/phases/01-reproducibility-and-safety-foundation/01-PATTERNS.md]

Use these assignments in planning:

| New/Modified Surface | Pattern to Reuse | Planning Note |
|----------------------|------------------|---------------|
| `revision_secrets.py` | `run_eval.load_secrets()` for YAML/JSON loading | Copy the input shape, not the module-scope secret printing. [VERIFIED: 01-PATTERNS.md; run_eval.py:120-131; run_eval.py:35-47] |
| `revision_artifacts.py` | `experiments_helper.py` dataclass/writer shape and `run_eval.py` token/result writers | Use Pydantic per D-06, but keep small typed records and explicit file writers. [VERIFIED: 01-PATTERNS.md] |
| `revision_preflight.py` | `exp2_to_exp3_predict.py` and `compress_few_shot_assets.py` CLI/manifest patterns | Keep CLI standalone, deterministic, and offline. [VERIFIED: 01-PATTERNS.md] |
| `revision_provider_smoke.py` | `run_single_experiment.py` CLI guard and `run_eval.make_provider()` | Create provider clients only after the user explicitly asks for smoke testing. [VERIFIED: 01-PATTERNS.md; run_eval.py:1318-1359] |
| `tests/*` | No existing test analogs | Plan Wave 0 test infrastructure because automated tests are absent. [VERIFIED: .planning/codebase/TESTING.md; 01-PATTERNS.md] |

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dependency resolution | Custom pinned text files maintained manually | `pyproject.toml` plus `uv.lock` | uv provides lock/sync commands and Phase 1 has a locked uv decision. [CITED: Context7 /astral-sh/uv; VERIFIED: 01-CONTEXT.md] |
| Artifact validation | Manual nested dict checks everywhere | Pydantic v2 models | Pydantic validates Python objects/JSON and can emit JSON Schema. [CITED: Context7 /pydantic/pydantic] |
| Local test runner | Bespoke validation script as the only test layer | pytest | pytest is already available locally and supports project config in pyproject. [VERIFIED: pytest --version; CITED: Context7 /pytest-dev/pytest] |
| Lint/format checks | A custom style checker | Ruff | Ruff handles `check`, `format`, and pyproject rule selection. [CITED: Context7 /astral-sh/ruff] |
| Secret-safety reporting | Scattered ad hoc redaction | One redaction helper used by diagnostics/manifests/tests | Current module-scope config printing proves scattered handling is unsafe. [VERIFIED: run_eval.py:35-47; OWASP ASVS V13.3.1] |
| Task alias validation | Repeated string comparisons in each runner | Canonical alias map owned by preflight/task contract tests | The repo already has `Connect_Icon` in code and `Connect_icon` on disk/few-shot config. [VERIFIED: task/dataset comparison command; run_eval.py:1384-1405] |

**Key insight:** The risky parts of Phase 1 are not algorithmically novel; they are contract and boundary problems. Use established tooling for environment, schema, test, and lint work so planning effort goes into sequencing and preserving experiment semantics. [VERIFIED: .planning/codebase/CONCERNS.md; CITED: PyPA, uv, Pydantic, pytest, Ruff docs]

## Common Pitfalls

### Pitfall 1: Preflight Imports Unsafe Code Too Early

**What goes wrong:** A preflight command imports `run_eval.py` before import-safety cleanup and accidentally reads/prints local config or runs provider smoke code. [VERIFIED: run_eval.py:35-47; run_eval.py:3307-3314]

**Why it happens:** `run_eval.py` contains constants and helpers the preflight wants, but it is not currently side-effect free. [VERIFIED: run_eval.py:1384-1412; run_eval.py:1797-2328]

**How to avoid:** Plan import-safety cleanup before preflight imports, or implement the first preflight pass by parsing static data and only importing after tests prove safety. [VERIFIED: run_single_experiment.py:13-22]

**Warning signs:** `python -c "import run_eval"` prints diagnostics, touches `secrets.yaml`, or sends any provider request. [VERIFIED: run_eval.py:35-47; run_eval.py:3307-3314]

### Pitfall 2: Secret Redaction Is Added Only to New Code

**What goes wrong:** New revision artifacts are safe, but legacy import paths still print local config or raw error analysis captures shareable-sensitive details. [VERIFIED: run_eval.py:35-47; run_eval.py:2751-2808; experiments_helper.py:75-166]

**Why it happens:** Existing code already has multiple output paths, and `secrets.yaml` is tracked while `.gitignore` does not ignore it. [VERIFIED: git ls-files -- secrets.yaml; .gitignore:1-15]

**How to avoid:** Add one redaction helper, update import-time behavior, add sentinel tests, and document that Phase 1 does not rewrite secret history. [VERIFIED: 01-CONTEXT.md; OWASP ASVS V13.3.1]

**Warning signs:** Test logs or generated JSON contain fake sentinel values from a temporary secrets fixture. [VERIFIED: AGENTS.md]

### Pitfall 3: Attempt Logging Conflicts With D-07

**What goes wrong:** The planner either makes attempt logging mandatory everywhere, breaking legacy workflows, or leaves it off for revision runs, failing REPRO-04. [VERIFIED: .planning/REQUIREMENTS.md; 01-CONTEXT.md]

**Why it happens:** REPRO-04 says every revision experiment writes append-only records, while D-07 says attempt logging is flag-controlled. [VERIFIED: .planning/REQUIREMENTS.md; 01-CONTEXT.md]

**How to avoid:** Default attempt logging on for `results/revision/<run_id>/` provider-call runs, keep the flag for legacy/diagnostic code paths, and make preflight report whether attempts will be written. [VERIFIED: 01-CONTEXT.md]

**Warning signs:** A revision run can produce `summary.csv` without `attempts.jsonl`, or an old Exp1-Exp4 wrapper changes output shape unexpectedly. [VERIFIED: run_eval.py:2841-2873; run_eval.py:2967-3210]

### Pitfall 4: Alias Drift Is Fixed Broadly Instead of Surfaced Safely

**What goes wrong:** Phase 1 turns into task taxonomy migration and changes experiment semantics. [VERIFIED: 01-CONTEXT.md D-04, D-14]

**Why it happens:** The repo has real drift: code supports `Connect_Icon`, dataset/few-shot paths include `Connect_icon`, and some not-used dataset directories have ground truth. [VERIFIED: task/dataset comparison command]

**How to avoid:** Add a canonical alias map and tests/validators first. Only perform the narrow fix required for selected tasks to resolve predictably. [VERIFIED: run_eval.py:1384-1412; 01-CONTEXT.md D-13, D-14]

**Warning signs:** The plan modifies many scoring branches or renames dataset directories instead of adding compatibility aliases and validation. [VERIFIED: .planning/codebase/CONCERNS.md]

### Pitfall 5: Provider SDK Locking Silently Upgrades Behavior

**What goes wrong:** A new `uv.lock` resolves latest provider SDKs and changes payload, streaming, token metadata, or model behavior before provider contract tests exist. [VERIFIED: PyPI JSON API version comparison; .planning/codebase/CONCERNS.md]

**Why it happens:** Several installed SDKs are behind latest PyPI versions, and `google-genai` has crossed a major version. [VERIFIED: importlib.metadata; PyPI JSON API]

**How to avoid:** Pin the current working provider SDK versions for the first lockfile, then treat upgrades as a later explicit task with smoke tests. [VERIFIED: .planning/codebase/CONCERNS.md]

**Warning signs:** `uv lock` changes OpenAI/Anthropic/Gemini SDK versions without a matching provider smoke-test and contract-test plan. [VERIFIED: PyPI JSON API; run_eval.py provider classes]

## Code Examples

### Preflight Result Shape

```python
from pydantic import BaseModel, Field


class PreflightTaskSummary(BaseModel):
    task_type: str
    canonical_task_type: str
    dataset_dir: str
    item_count: int
    warnings: list[str] = Field(default_factory=list)


class PreflightReport(BaseModel):
    schema_version: str = "cognition.revision.preflight.v1"
    selected_task_types: list[str]
    expected_request_count: int
    output_dir: str
    manifest_path: str
    tasks: list[PreflightTaskSummary]
```

Source: Pydantic model pattern verified by Context7; fields derived from REPRO-02 and D-15. [CITED: Context7 /pydantic/pydantic; VERIFIED: .planning/REQUIREMENTS.md; 01-CONTEXT.md]

### Append-Only Attempt Writer

```python
import json
from pathlib import Path


def append_attempt(path: Path, attempt: "AttemptRecord") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(attempt.model_dump_json())
        handle.write("\n")
        handle.flush()
```

Source: Local writer pattern mirrors existing CSV/JSON writers while changing the source of truth to JSONL. [VERIFIED: run_eval.py:2675-2681; run_eval.py:2895-2920; experiments_helper.py:75-166]

### Import Safety Test

```python
import subprocess
import sys


def test_run_eval_import_is_offline_and_quiet():
    result = subprocess.run(
        [sys.executable, "-c", "import run_eval; import run_single_experiment"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    combined = result.stdout + result.stderr
    assert "secrets.yaml exists?" not in combined
    assert "TEXT OK:" not in combined
```

Source: Test targets current unsafe outputs from `run_eval.py`. [VERIFIED: run_eval.py:35-47; run_eval.py:3314]

## State of the Art

| Old Approach | Current Approach | When Changed / Verified | Impact |
|--------------|------------------|-------------------------|--------|
| README-only install commands | `pyproject.toml` plus lockfile-managed sync | Verified 2026-05-15 via PyPA and uv docs | Satisfies REPRO-01 and makes dependency state machine-readable. [CITED: PyPA pyproject guide; Context7 /astral-sh/uv] |
| Manual dict artifact contracts | Pydantic v2 models with JSON validation/schema export | Verified 2026-05-15 via Context7 | Gives planners explicit manifest/attempt/summary contracts. [CITED: Context7 /pydantic/pydantic] |
| Notebook/manual validation only | pytest focused tests plus ruff checks | Verified 2026-05-15 via Context7 and local tool probes | Gives Phase 1 local gates without requiring CI. [VERIFIED: pytest --version; ruff missing locally; CITED: Context7 /pytest-dev/pytest; Context7 /astral-sh/ruff] |
| Import-time provider smoke snippets | Explicit smoke-test CLI | Required by D-12 and current code audit | Prevents accidental paid calls from imports, preflight, or tests. [VERIFIED: 01-CONTEXT.md; run_eval.py:3307-3314] |

**Deprecated/outdated for Phase 1:**

- Module-scope config dumps in importable modules are incompatible with REPRO-05 and D-09. [VERIFIED: run_eval.py:35-47]
- Aggregate-only revision outputs are insufficient for REPRO-04; summaries must be derived from attempt rows for revision runs. [VERIFIED: .planning/REQUIREMENTS.md]
- Broad evaluator splitting before tests is not recommended because it risks changing accepted-paper experiment semantics. [VERIFIED: .planning/PROJECT.md; 01-CONTEXT.md]

## Assumptions Log

All claims in this research were verified against local files, local command output, Context7/official docs, OWASP ASVS, or PyPI metadata during this session. No `[ASSUMED]` claims are intentionally present.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| - | None | - | - |

## Open Questions (RESOLVED)

1. **Should Phase 1 pin current provider SDK versions exactly or allow compatible minor upgrades?**
   - What we know: local installed versions are older than PyPI latest for OpenAI, Anthropic, and Google Gen AI. [VERIFIED: importlib.metadata; PyPI JSON API]
   - RESOLVED: Phase 1 pins the exact locally installed provider SDK versions in `pyproject.toml` and `uv.lock`: `openai==2.6.1`, `anthropic==0.72.0`, and `google-genai==1.39.1`. Compatible/minor SDK upgrades are intentionally out of scope until explicit provider contract or smoke tests exist. [VERIFIED: .planning/codebase/CONCERNS.md]

2. **How far should Phase 1 go on scoring regressions?**
   - What we know: `Path_Finder` has classification schema/build behavior but `evaluate_pass1()` treats it with multi-select logic in one branch; there are other known scoring/summary crash surfaces. [VERIFIED: run_eval.py:2073-2108; run_eval.py:2404-2407; run_eval.py:2527-2530; run_eval.py:2927-2934]
   - RESOLVED: Phase 1 adds focused regression tests/validators for revision-critical scoring and summary risks, and only permits the smallest code fixes needed for those tests to pass. Broad scoring repair, taxonomy migration, and evaluator refactors remain out of scope per D-14. [VERIFIED: 01-CONTEXT.md D-13, D-14]

3. **Should `revision_preflight.py` import `run_eval` after import safety, or maintain an independent task registry?**
   - What we know: importing `run_eval` is currently unsafe, but duplicating task logic can drift. [VERIFIED: run_eval.py:35-47; run_eval.py:1797-2328]
   - RESOLVED: Plan 02 makes `run_eval` import-safe first. Plan 04 may then import the cleaned `run_eval.SUPPORTED_TYPES` constant surface, while keeping preflight offline and forbidden from calling `load_secrets()`, `make_provider()`, provider SDK classes, or any `infer()` method. [VERIFIED: 01-PATTERNS.md]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | All Phase 1 code | yes | 3.11.5 | None needed. [VERIFIED: python3 --version] |
| pip | uv bootstrap fallback | yes | 26.0.1 | None needed. [VERIFIED: python3 -m pip --version] |
| uv | Lockfile and sync | no | latest 0.11.14 on PyPI | Install/bootstrap uv before generating `uv.lock`; pip fallback does not satisfy D-02. [VERIFIED: command -v uv; PyPI JSON API; 01-CONTEXT.md] |
| pytest | Tests | yes | 7.4.0 installed; 9.0.3 latest | Use `uv sync` to install locked dev version. [VERIFIED: pytest --version; PyPI JSON API] |
| ruff | Lint/format | no | latest 0.15.13 on PyPI | Use `uv sync` to install locked dev version. [VERIFIED: command -v ruff; PyPI JSON API] |
| Git | Manifest code revision | yes | 2.51.2 | None. [VERIFIED: git --version] |
| Git LFS | Dataset materialization checks | yes | 3.7.1 | Preflight should fail if required dataset files are pointers. [VERIFIED: git lfs version; .gitattributes] |
| Provider SDKs | Existing evaluator compatibility | yes | openai 2.6.1, anthropic 0.72.0, google-genai 1.39.1 | Lock current versions first. [VERIFIED: importlib.metadata] |

**Missing dependencies with no fallback:**

- `uv` for D-02 lockfile generation until installed. [VERIFIED: command -v uv; 01-CONTEXT.md]

**Missing dependencies with fallback:**

- `ruff` is missing locally, but will be provided by the new dev dependency group once `uv sync` is available. [VERIFIED: command -v ruff; PyPI JSON API]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | This is a local offline research toolkit, not an authenticated service. [VERIFIED: .planning/PROJECT.md] |
| V3 Session Management | no | No web sessions are part of Phase 1. [VERIFIED: .planning/PROJECT.md] |
| V4 Access Control | partial | Keep local secret files out of generated/shareable artifacts; no multi-user authorization layer is planned. [VERIFIED: AGENTS.md; 01-CONTEXT.md] |
| V5 Input Validation | yes | Pydantic schemas plus explicit path/task/prompt validation in preflight. [CITED: Context7 /pydantic/pydantic; VERIFIED: REPRO-02, REPRO-03, REPRO-06] |
| V6 Cryptography | no custom crypto | Do not hand-roll cryptography; provider SDKs and local secret storage remain external/local concerns. [VERIFIED: .planning/PROJECT.md] |
| V13 Configuration / Secret Management | yes | Secrets must not be included in source/build artifacts, and Phase 1 must prevent printing/copying credential values. [CITED: OWASP ASVS V13.3.1; VERIFIED: AGENTS.md; run_eval.py:35-47] |

### Known Threat Patterns for Phase 1

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Credential disclosure through import logs | Information Disclosure | Remove module-scope secret reads/prints, add redaction helper, test sentinel leakage. [VERIFIED: run_eval.py:35-47; OWASP ASVS V13.3.1] |
| Accidental paid provider calls during import/preflight/tests | Denial of wallet / Safety boundary breach | Move smoke tests to explicit CLI and assert imports/preflight do not construct providers. [VERIFIED: run_eval.py:3307-3314; 01-CONTEXT.md D-12] |
| Result overwrite or mixed legacy/revision outputs | Tampering / Repudiation | Write revision artifacts under `results/revision/<run_id>/`, require unique or resumable output policy in preflight. [VERIFIED: 01-CONTEXT.md D-08, D-15] |
| Schema drift between attempts and summaries | Tampering / Repudiation | Validate attempts/summaries with Pydantic and derive summaries from attempts. [VERIFIED: REPRO-03, REPRO-04; CITED: Context7 /pydantic/pydantic] |
| Task alias drift silently skipping data | Tampering / Scientific validity risk | Canonical alias map plus preflight/test failure on unresolved aliases. [VERIFIED: task/dataset comparison command; run_eval.py:1384-1412] |

## Sources

### Primary (HIGH confidence)

- `.planning/phases/01-reproducibility-and-safety-foundation/01-CONTEXT.md` - locked user decisions D-01 through D-16, discretion, and deferred ideas.
- `.planning/REQUIREMENTS.md` - REPRO-01 through REPRO-06.
- `.planning/ROADMAP.md` - Phase 1 goal and success criteria.
- `.planning/PROJECT.md` and `AGENTS.md` - scope, language, offline/safety, reproducibility, and secret-handling constraints.
- `.planning/codebase/STRUCTURE.md`, `CONVENTIONS.md`, `CONCERNS.md`, `TESTING.md`, `STACK.md`, `ARCHITECTURE.md` - codebase shape, risks, testing gap, stack, and integration guidance.
- `.planning/research/SUMMARY.md`, `STACK.md`, `ARCHITECTURE.md`, `PITFALLS.md` - roadmap-level research and Phase 1 implications.
- `.planning/phases/01-reproducibility-and-safety-foundation/01-PATTERNS.md` - local pattern map for planned files/artifacts.
- `run_eval.py`, `run_single_experiment.py`, `README.md`, `.gitignore`, `.gitattributes`, `prompts_optimized.yaml`, `few_shot_examples.yaml`, `captcha_data/*/ground_truth.json` - local code/config evidence.
- Context7 `/astral-sh/uv` - uv lock/sync/dependency group guidance.
- Context7 `/pydantic/pydantic` - Pydantic v2 validation and schema methods.
- Context7 `/pytest-dev/pytest` - pytest pyproject configuration.
- Context7 `/astral-sh/ruff` - Ruff check/format and pyproject configuration.
- PyPI JSON API - current package versions, publish timestamps, and Python requirements for uv, Pydantic, pytest, Ruff, and existing runtime dependencies.
- Python Packaging User Guide - `pyproject.toml` metadata/dependency/tooling guidance: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
- uv project configuration docs - flat/script project package behavior and `tool.uv.package`: https://docs.astral.sh/uv/concepts/projects/config/
- OWASP ASVS 5.0 V13.3.1 secret management: https://cornucopia.owasp.org/taxonomy/asvs-5.0/13-configuration/03-secret-management

### Secondary (MEDIUM confidence)

- None required for the Phase 1 implementation choices; external baseline and statistical methodology sources belong to later phases. [VERIFIED: 01-CONTEXT.md deferred ideas]

### Tertiary (LOW confidence)

- None.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - Verified against local stack/docs, PyPI JSON API, PyPA, uv, Pydantic, pytest, and Ruff sources.
- Architecture: HIGH - Grounded in locked decisions, pattern map, and local codebase shape.
- Pitfalls: HIGH - Grounded in direct code audit and existing codebase concern documents.
- Security: HIGH - Grounded in AGENTS.md constraints, direct import-side-effect evidence, and OWASP ASVS secret-management guidance.

**Research date:** 2026-05-15
**Valid until:** 2026-06-14 for Phase 1 architecture and local code constraints; package latest-version recommendations should be rechecked after 2026-05-22 because uv, Ruff, provider SDKs, and Pydantic are moving quickly.
