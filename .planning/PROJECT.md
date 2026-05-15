# COGNITION Revision Experiments

## What This Is

This project extends the existing COGNITION CAPTCHA evaluation framework to support post-acceptance USENIX Security revision experiments. The immediate goal is to turn reviewer comments into reproducible empirical artifacts: adaptive-attacker results, strengthened benchmark/baseline comparisons, statistical confidence reporting, and clearer evidence for structural CAPTCHA hardness.

The codebase is a local Python research toolkit for evaluating multimodal LLMs on CAPTCHA tasks, generating results and error analysis, and producing paper-ready visualizations. This planning cycle should preserve the paper-driven workflow: every implementation phase must map to a concrete revision need, figure, table, appendix artifact, or reviewer concern.

## Core Value

Produce credible, reproducible revision evidence that directly strengthens the paper's claims about structural CAPTCHA robustness against multimodal LLM attackers.

## Requirements

### Validated

- ✓ Existing framework evaluates CAPTCHA task families across OpenAI, Anthropic, Gemini, and Fireworks-compatible multimodal models — existing.
- ✓ Existing experiment runners support ground-truth prompting, optimized prompting, until-correct retries, and few-shot diagnostic experiments — existing.
- ✓ Existing result artifacts capture pass rates, token usage, cost summaries, latency, error analysis, and publication figures — existing.
- ✓ Existing Exp2-to-Exp3 analysis implements i.i.d. Bernoulli-style retry prediction and prediction validation workflows — existing.
- ✓ Existing codebase map documents the current stack, architecture, testing gaps, integrations, and technical concerns under `.planning/codebase/` — existing.

### Active

- [ ] Add and integrate an adaptive/session-memory attacker experiment that evaluates stronger retry behavior than the current fixed-policy or i.i.d. framing.
- [ ] Produce main-body-ready analysis showing why hard CAPTCHA tasks remain robust under the adaptive attacker, including task-family-level interpretation.
- [ ] Strengthen benchmark credibility by supporting comparisons against specialized CAPTCHA solver baselines and/or larger external benchmark datasets where feasible.
- [ ] Add statistical confidence reporting for pass rates, task-family conclusions, and threshold-based claims.
- [ ] Clarify and operationalize the defense methodology as a reusable, actionable pipeline rather than only high-level design guidelines.
- [ ] Improve reproducibility and safety of the experiment framework enough that revision results can be regenerated without fragile notebook-only steps or accidental secret exposure.

### Out of Scope

- Building a production CAPTCHA service — the project is focused on paper revision evidence and reproducible research artifacts.
- Creating browser automation for attacking live CAPTCHA deployments — the study should remain offline and dataset-based.
- Fully reimplementing external SOTA solver systems unless necessary and feasible — the initial goal is fair comparison hooks, documented methodology, and defensible baselines.
- Large-scale human-subjects usability testing — the revision may describe limitations or methodology, but the current project focuses on empirical attacker-side and benchmark evidence.
- Broad refactoring unrelated to revision evidence — cleanups are in scope only when they unblock reliable experiments or reproducibility.

## Context

The paper received reviewer requests after USENIX Security 2026 Cycle 2 review. The final requested revisions emphasize four areas:

- Adaptive attacker evidence: move session-memory attacker results into the main body and explain why hard CAPTCHA tasks remain robust against this stronger attacker.
- Dataset limitations and scope: discuss CaptchaWorld limitations, sample size, representativeness, and statistical significance.
- Benchmark strengthening: compare against state-of-the-art CAPTCHA solvers and extend evaluation to larger datasets where possible.
- Defense methodology: turn high-level design guidelines into a clearer, actionable methodology practitioners can apply.

The repository already contains a Python evaluation framework centered around `run_eval.py`, `run_single_experiment.py`, `experiments_helper.py`, `visualize_results.py`, and `exp2_to_exp3_predict.py`. Datasets and generated artifacts live under `captcha_data/`, `few_shot_assets/`, `results/`, `error_analysis/`, and `figures/`.

The current codebase has several known risks that matter for revision work: `run_eval.py` is monolithic, imports can perform side effects, secrets are tracked or printed, automated tests are absent, task aliases can drift from dataset names, and generated result artifacts are mixed with source files. These issues should be addressed when they threaten experiment correctness, reproducibility, or paper artifact integrity.

## Constraints

- **Language**: Planning documents must be written in English, while interactive discussion with the user should be in Chinese — the user explicitly requested this workflow.
- **Paper-driven scope**: Implementation should prioritize reviewer-requested evidence over general toolkit polish — revision time should produce usable paper artifacts.
- **Research ethics**: Experiments must remain offline on owned or authorized datasets and should not provide turnkey live CAPTCHA attack tooling — consistent with the disclosure and ethics framing.
- **Reproducibility**: New experiments should produce versioned CSV/JSON outputs, summaries, and figure/table inputs — revision claims must be regenerable.
- **Cost control**: Provider API experiments can be expensive — phases should include dry-run/preflight controls, small smoke runs, and explicit run manifests before full runs.
- **Security**: Secret values must not be read into docs, printed, or committed — `secrets.yaml` should be treated as sensitive local configuration.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Treat this as a brownfield research-revision project | The existing repo already implements the core CAPTCHA evaluation framework and result pipeline. | — Pending |
| Prioritize adaptive attacker evaluation first | The final reviewer comment explicitly names adaptive/session-memory results as a valuable addition that should move into the main body. | — Pending |
| Treat benchmark strengthening as baseline/dataset integration rather than a full solver rewrite by default | Reviewers asked for comparisons to SOTA solvers and larger datasets, but a scoped comparison layer is more feasible for revision than reimplementing entire external systems. | — Pending |
| Add statistical confidence reporting as a first-class output | Reviewer concerns about sample size, thresholding, and Bernoulli assumptions require quantitative uncertainty reporting, not only prose. | — Pending |
| Keep defense work methodology-focused | Reviewers want actionable guidance; code should support methodology clarity without turning the project into a production CAPTCHA platform. | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-15 after initialization*
