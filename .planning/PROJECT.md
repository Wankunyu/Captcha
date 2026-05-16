# COGNITION Revision Experiments

## What This Is

This project extends the existing COGNITION CAPTCHA evaluation framework to support the shepherded USENIX Security revision due May 28 AoE. The immediate goal is to turn the shepherding plan into reproducible paper and artifact evidence: main-body adaptive-attacker results, dataset/statistical limitations, SOTA-solver and larger-benchmark comparisons, actionable defense methodology, ethics/disclosure updates, and a final availability-ready artifact package.

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

- [ ] Establish safe, reproducible experiment contracts before any new costly provider runs: install metadata, preflight, manifests, attempt logs, prompt/few-shot hashes, cost preview, and secret-safe reporting.
- [ ] Move the session-memory adaptive attacker into the main-body evidence flow, including explicit feedback/memory assumptions and comparison to fixed-policy Bernoulli Success@k estimates.
- [ ] Revise dataset scope and statistical interpretation: CaptchaWorld limitations, removed incompatible task types, sample-size caveats, confidence reporting, and boundaries on population-level claims.
- [ ] Strengthen benchmark credibility through a structured comparison against Halligan, Oedipus, specialized CAPTCHA solvers, and a feasible larger external benchmark subset where artifacts are compatible.
- [ ] Convert defense guidance into a reusable practitioner methodology with structural hardening transformations, red-team evaluation, deployment-monitoring knobs, and clear HCI/usability limits.
- [ ] Produce final paper and artifact-delivery evidence: ethics/disclosure details, stakeholder contacts, reviewer-request traceability, claim ledger, color-coded diff support, and an availability-ready artifact package by May 28 AoE.

### Out of Scope

- Building a production CAPTCHA service — the project is focused on paper revision evidence and reproducible research artifacts.
- Creating browser automation for attacking live CAPTCHA deployments — the study should remain offline and dataset-based.
- Fully reimplementing external SOTA solver systems unless necessary and feasible — the initial goal is fair comparison hooks, documented methodology, and defensible baselines.
- Large-scale human-subjects usability testing — the revision may describe limitations or methodology, but the current project focuses on empirical attacker-side and benchmark evidence.
- Broad refactoring unrelated to revision evidence — cleanups are in scope only when they unblock reliable experiments or reproducibility.

## Context

The paper received a conditional acceptance with shepherding requirements after USENIX Security 2026 Cycle 2 review. The current revision plan, captured in `/Users/ukun/Desktop/Shepherding.docx`, commits to submit the revised paper, color-coded diff, point-by-point changes, and final artifact package by May 28 AoE. The latest shepherding scope emphasizes seven areas:

- Adaptive attacker evidence: move session-memory attacker results into the main body, define binary pass/fail feedback and task-level memory over fresh CAPTCHA instances, and explain why hard tasks remain robust.
- Dataset limitations and scope: discuss CaptchaWorld size, representativeness, removed incompatible task types, cleaning/standardization, answer-format normalization, and statistical significance limits.
- Benchmark strengthening: compare against state-of-the-art solver and benchmark systems such as Halligan and Oedipus, and attempt a compatible larger external benchmark subset where feasible.
- Defense methodology: turn high-level guidelines into a practical hardening pipeline with transformations, human-clarity constraints, red-team evaluation, and deployment-monitoring knobs.
- Limitations and HCI scope: clarify long-term validity limits, evolving MLLMs, custom-trained/agentic attackers, API cost/latency volatility, and the absence of formal human-subject usability validation.
- Ethics and disclosure: document stakeholder categories, disclosure dates and response status, including Google VRP closure by January 26, 2026 and January 30, 2026 contacts to OpenAI, Anthropic, hCaptcha, Cloudflare, and Alibaba.
- Artifact availability: package the evaluation framework, prompts, dataset preprocessing/cleaning scripts, task metadata, result-processing scripts, and reproduction documentation without turning the artifact into operational CAPTCHA-bypass tooling.

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
| Keep Phase 1 as the safety/reproducibility gate before additional provider runs | The shepherding deadline is tight, and every later claim needs preflight, prompt/few-shot hashes, cost visibility, secret safety, and append-only attempt records. | Phase 1 planned |
| Prioritize adaptive attacker main-body evidence immediately after the foundation | The shepherding plan explicitly moves session-memory adaptive results from appendix to main body and uses them to address fixed-prompt/i.i.d. concerns. | Roadmap updated |
| Treat benchmark strengthening as baseline/dataset integration rather than a full solver rewrite by default | Reviewers asked for comparisons to SOTA solvers and larger datasets, but a scoped comparison layer is more feasible for revision than reimplementing entire external systems. | — Pending |
| Add statistical confidence reporting as a first-class output | Reviewer concerns about sample size, thresholding, and Bernoulli assumptions require quantitative uncertainty reporting, not only prose. | — Pending |
| Keep defense work methodology-focused and HCI-scoped | Shepherding asks for actionable guidance, but the revision must avoid claiming formal usability validation without a human-subjects study. | Roadmap updated |
| Treat ethics, disclosure, and artifact availability as implementation deliverables | The final package must include traceability, disclosure details, and availability-ready artifacts, not just prose edits. | Roadmap updated |

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
*Last updated: 2026-05-16 after shepherding-plan roadmap update*
