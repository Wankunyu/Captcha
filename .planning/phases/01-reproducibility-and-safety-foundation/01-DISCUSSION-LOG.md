# Phase 1: Reproducibility and Safety Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `01-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-05-15
**Phase:** 1 - Reproducibility and Safety Foundation
**Areas discussed:** Packaging & Environment Scope, Artifact Contract Shape, Secret Safety & Import Side Effects, Validation/Test Coverage Boundary

---

## Packaging & Environment Scope

| Option | Description | Selected |
|--------|-------------|----------|
| `pyproject.toml` + lockfile | Strongest reproducibility for reviewer-facing experiments. | ✓ |
| `pyproject.toml` only | Lighter change, but version drift remains. | |
| `requirements.txt` only | Simplest, but weaker dependency grouping and maintenance. | |

**User's choice:** `pyproject.toml` plus lockfile.
**Notes:** User selected `1A`.

| Option | Description | Selected |
|--------|-------------|----------|
| `uv` lockfile | Fast modern lock workflow for Python research environments. | ✓ |
| `pip-tools` / `requirements-lock.txt` | More conservative and familiar to some collaborators. | |
| Do not lock versions | Fastest, but weak reproducibility. | |

**User's choice:** Use `uv`.
**Notes:** User selected `2A`.

| Option | Description | Selected |
|--------|-------------|----------|
| `pytest` + `ruff` | Minimal correctness and lint/format foundation. | ✓ |
| `pytest` only | Correctness-focused, no lint/format tool. | |
| No dev tools yet | Least change, but weak REPRO-06 support. | |

**User's choice:** Add `pytest` and `ruff`.
**Notes:** User selected `3A`.

---

## Artifact Contract Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Versioned manifest + attempts JSONL + summaries | Strong provenance, resumability, and reviewer-facing traceability. | ✓ |
| Standardize existing CSV/JSON only | Less change, weaker per-attempt provenance. | |
| Document format in README only | Fastest, but hard for downstream agents to enforce. | |

**User's choice:** Versioned `run_manifest.json`, `attempts.jsonl`, and derived CSV/JSON summaries.
**Notes:** User selected `1A`.

| Option | Description | Selected |
|--------|-------------|----------|
| Pydantic schema | Strong validation for manifests, attempt rows, and summaries. | ✓ |
| Manual dict validation | Fewer dependencies, easier to drift. | |
| No schema validation yet | Fastest, but weak artifact contracts. | |

**User's choice:** Use Pydantic schemas.
**Notes:** User selected `2A`.

| Option | Description | Selected |
|--------|-------------|----------|
| Always write attempts JSONL | Maximum traceability for every revision experiment. | |
| Only adaptive attacker writes attempt logs | Narrower and lighter. | |
| Attempt log controlled by flag | Flexible; requires planner to make defaults explicit. | ✓ |

**User's choice:** Attempt logging should be flag-controlled.
**Notes:** User selected `3C`.

| Option | Description | Selected |
|--------|-------------|----------|
| `results/revision/<run_id>/` | Separates revision artifacts from legacy experiment layouts. | ✓ |
| Existing `results/expN/...` layout | More compatible with current visualizer, but mixes old and revision artifacts. | |
| Top-level `revision_results/` | Strong isolation, but adds another result root. | |

**User's choice:** Use `results/revision/<run_id>/`.
**Notes:** User selected `4A`.

---

## Secret Safety & Import Side Effects

| Option | Description | Selected |
|--------|-------------|----------|
| Remove/isolate all import-time side effects | Importing `run_eval` should not read/print secrets or send API requests. | ✓ |
| Only remove hard-coded smoke call | Lower change, but secret printing risk remains. | |
| Do not change import side effects yet | Fastest, unsafe for tests and preflight. | |

**User's choice:** Remove or isolate all import-time side effects.
**Notes:** User selected `1A`.

| Option | Description | Selected |
|--------|-------------|----------|
| `secrets.yaml` support + `secrets.example.yaml` + redacted behavior | Compatible with existing workflow and safer for sharing. | ✓ |
| Environment variables as primary config | Safer but more disruptive to existing notebooks/scripts. | |
| Documentation warning only | Lightest, but weak protection. | |

**User's choice:** Keep `secrets.yaml` support, add `secrets.example.yaml`, and use redacted shareable behavior.
**Notes:** User selected `2A`.

| Option | Description | Selected |
|--------|-------------|----------|
| Do not auto-remove; protect future artifacts | Avoids destructive history/tracking changes in Phase 1. | ✓ |
| Remove `secrets.yaml` from git tracking and add to `.gitignore` | Cleaner future state, more disruptive. | |
| Keep current behavior | Least change, highest risk. | |

**User's choice:** Do not automatically remove tracked `secrets.yaml` or rewrite history in Phase 1.
**Notes:** User selected `3A`.

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit CLI command/script | Provider smoke tests never run by default. | ✓ |
| pytest skip unless env flag | More integrated but more complex. | |
| Manual notebook workflow | Closest to current habits but less reproducible. | |

**User's choice:** Move provider smoke tests to explicit CLI command or script.
**Notes:** User selected `4A`.

---

## Validation/Test Coverage Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| New code + known high-risk legacy logic | Covers artifact schemas, preflight, secret-safe import, and task alias/scoring smoke. | ✓ |
| New code only | Lower change, but old risks may continue to pollute experiments. | |
| Validators only, no pytest | Simpler, weaker regression protection. | |

**User's choice:** Cover new Phase 1 code plus high-risk legacy behavior through non-invasive tests or validators.
**Notes:** User selected `1A`.

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal regression tests/validators, no broad scoring repair | Surfaces risk without making Phase 1 a scoring refactor. | |
| Fix all known scoring bugs in Phase 1 | More thorough, but may balloon scope. | |
| Do not touch old scoring | Fastest; legacy scoring changes are not a Phase 1 goal. | ✓ |

**User's choice:** Do not make old scoring fixes a Phase 1 goal.
**Notes:** User asked for clarification, then selected `2C`. Interpreted together with `1A`: Phase 1 may surface legacy scoring risks non-invasively, but should avoid broad scoring changes.

| Option | Description | Selected |
|--------|-------------|----------|
| Task aliases + dataset files + prompt files + output dir + request count | Directly supports Phase 1 success criteria. | ✓ |
| Task and dataset only | Lighter, but cost/output/prompt issues may appear late. | |
| Dry-run summary only, do not fail | Weakest guardrail. | |

**User's choice:** Preflight validates aliases, dataset files, prompt files, output directory, and expected request count.
**Notes:** User selected `3A`.

| Option | Description | Selected |
|--------|-------------|----------|
| Local commands only, no mandatory CI | Adds runnable checks without LFS/secrets/CI complications. | ✓ |
| Add GitHub Actions | More standard, but likely to collide with secrets and large datasets. | |
| No unified test/lint commands | Fastest, but weak downstream verification. | |

**User's choice:** Provide local pytest/ruff commands and tests; do not require GitHub Actions in Phase 1.
**Notes:** User selected `4A`.

---

## the agent's Discretion

- Exact module/file names for Phase 1 helper code.
- Exact Pydantic schema organization.
- Exact CLI command names for preflight, provider smoke tests, and validation.
- Whether high-risk legacy checks are pytest tests, preflight warnings, diagnostics, or documented validators, as long as Phase 1 does not become a broad scoring repair.

## Deferred Ideas

- Adaptive attacker implementation belongs to Phase 3.
- Statistical confidence reporting belongs to Phase 2.
- External baselines and larger datasets belong to Phase 4.
- Defense methodology belongs to Phase 5.
- Broad evaluator refactor, full secret history cleanup, mandatory CI, and comprehensive scoring repairs are not Phase 1 goals.
