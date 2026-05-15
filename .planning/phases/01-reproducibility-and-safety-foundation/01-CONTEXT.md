# Phase 1: Reproducibility and Safety Foundation - Context

**Gathered:** 2026-05-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 establishes the safety and reproducibility foundation for future revision experiments before paid provider calls expand. It should deliver machine-readable environment metadata, preflight validation, versioned run manifests, optional attempt logging contracts, secret-safe behavior, explicit provider smoke-test entry points, and local validation/test commands.

This phase should not implement adaptive attacker behavior, statistical confidence analysis, SOTA baseline integration, defense methodology artifacts, formal HCI studies, live CAPTCHA automation, or broad evaluator refactors. Those belong to later phases.

</domain>

<decisions>
## Implementation Decisions

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

### the agent's Discretion

- The planner may choose exact file/module names for Phase 1 helper code, as long as the existing script workflow remains usable.
- The planner may decide whether Pydantic schemas live in a root-level module, a small package directory, or a dedicated revision utility file.
- The planner may choose exact local command names for preflight, validation, provider smoke tests, and artifact schema checks.
- The planner may choose whether high-risk legacy scoring checks are implemented as pytest tests, preflight warnings, diagnostics, or documented validators, provided they do not expand into a broad scoring refactor.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and Phase Scope

- `.planning/PROJECT.md` — Overall project scope, core value, constraints, and out-of-scope boundaries.
- `.planning/REQUIREMENTS.md` — Phase 1 requirements `REPRO-01` through `REPRO-06`.
- `.planning/ROADMAP.md` — Phase 1 goal, success criteria, dependencies, and reviewer alignment.
- `.planning/STATE.md` — Current project state and phase focus.

### Research Guidance

- `.planning/research/SUMMARY.md` — Recommended stack, phase ordering, pitfalls, and Phase 1 implications.
- `.planning/research/STACK.md` — Dependency, artifact, and reproducibility recommendations.
- `.planning/research/ARCHITECTURE.md` — Additive architecture and safe integration guidance.
- `.planning/research/PITFALLS.md` — Risks around secrets, cost, schema drift, and overclaiming.

### Codebase Maps

- `.planning/codebase/STRUCTURE.md` — Existing file layout and where current evaluation, visualization, and result code lives.
- `.planning/codebase/CONVENTIONS.md` — Current Python style, CLI conventions, and import-side-effect guidance.
- `.planning/codebase/CONCERNS.md` — Known import-side-effect, secret, task-alias, scoring, result, and testing risks.
- `.planning/codebase/TESTING.md` — Current absence of automated tests and suggested testable surfaces.
- `.planning/codebase/STACK.md` — Current dependency and runtime state.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `run_eval.py` — Existing task loading, provider adapters, schema creation, scoring, token/cost accounting, and until-correct retry logic. Phase 1 should treat this as a compatibility surface and avoid broad semantic rewrites.
- `run_single_experiment.py` — Existing wrapper entry point for experiments 1-4. Useful as a reference for CLI style, but imports `run_eval.py`, so import safety matters.
- `exp2_to_exp3_predict.py` — Good example of a focused standalone analysis CLI with `argparse`, typed helpers, and dataframe outputs.
- `visualize_results.py` — Existing result loader and chart pipeline; useful reference for current result layout assumptions.
- `.planning/codebase/*` — Current codebase maps should guide planner decisions and prevent re-discovering known risks.

### Established Patterns

- The repository currently uses flat root-level Python scripts rather than a packaged `src/` layout.
- CLIs use `argparse` and keyword-heavy wrapper functions.
- Generated outputs currently live under `results/`, `error_analysis/`, and `figures/`.
- Existing task and provider code assumes the project root as the working directory.
- There is no current pytest, ruff, lockfile, or pyproject configuration.

### Integration Points

- New environment metadata should integrate at the repository root through `pyproject.toml` and `uv` lock output.
- New revision artifact helpers should write under `results/revision/<run_id>/`.
- Preflight should inspect existing task definitions, dataset directories, prompt files, output paths, and expected request counts without invoking provider APIs.
- Provider smoke tests should be explicit commands/scripts and must not run on import or by default.
- Secret-safe reporting must be enforced around any code path that reads local provider configuration or writes shareable artifacts.

</code_context>

<specifics>
## Specific Ideas

- Preserve the user's existing local `secrets.yaml` workflow, but make shareable outputs redacted and add `secrets.example.yaml`.
- Keep Phase 1 focused on foundations. Do not expand it into adaptive attacker implementation, statistical analysis, or a large package refactor.
- Interpret the testing decision as non-invasive: validators may surface legacy scoring/alias risks, but Phase 1 should not aggressively repair old scoring logic unless the planner finds a minimal blocker fix.

</specifics>

<deferred>
## Deferred Ideas

- Adaptive/session-memory attacker implementation belongs to Phase 3.
- Statistical confidence intervals, threshold sensitivity, and Bernoulli calibration belong to Phase 2.
- Specialized solver and larger-dataset baselines belong to Phase 4.
- Defense methodology artifacts belong to Phase 5.
- Formal CI integration, broad evaluator refactor, full secret-history cleanup, and complete scoring repair are not Phase 1 goals unless later planning identifies a narrow blocker.

</deferred>

---

*Phase: 01-reproducibility-and-safety-foundation*
*Context gathered: 2026-05-15*
