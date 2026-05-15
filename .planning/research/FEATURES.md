# Feature Landscape

**Project:** COGNITION Revision Experiments
**Domain:** CAPTCHA/MLLM security revision evidence for USENIX Security reviewer comments
**Researched:** 2026-05-15
**Scope:** Features dimension only. This document is based on `.planning/PROJECT.md`, codebase architecture/testing/concerns maps, and the USENIX reviewer-comment file provided by the user.
**Overall confidence:** HIGH for reviewer-comment mapping; MEDIUM for feasibility of external solver and larger-dataset integrations until artifact availability is checked.

## Reviewer Theme Keys

Use these keys in requirements and phase plans so every feature traces back to reviewer demand.

| Key | Reviewer-Comment Theme | Must Satisfy |
|-----|------------------------|--------------|
| A1.1 | Adaptive/session-memory attacker integration | Move adaptive results into the main body and explain why hard tasks remain robust. |
| A1.2 | Dataset limitations and scope | Clarify CaptchaWorld limitations, sample size, representativeness, removed task types, and statistical significance. |
| A1.3 | Benchmark strengthening and baselines | Compare against specialized CAPTCHA solvers and extend to larger datasets where feasible. |
| A1.4 | Defense methodology clarification | Convert high-level hardening guidelines into an actionable practitioner methodology. |
| C/D-Bernoulli | Retry-model validity | Address i.i.d. Bernoulli assumptions and adaptive, non-i.i.d. retry behavior. |
| C-Threshold | Threshold justification | Explain the 40% cutoff as an operational heuristic with uncertainty, not a universal security boundary. |
| A/D-Lifetime | Future capability and arms-race limits | Acknowledge that current MLLM limitations may change and frame results as structural evidence, not permanent guarantees. |
| D-HCI/Ops | Usability and deployment overhead | Clarify what is validated now versus what requires future user studies or production deployment work. |

## Table Stakes

Features missing from the revision would leave direct reviewer comments under-addressed.

| Feature | Reviewer Themes | Why Expected | Complexity | Testable Acceptance |
|---------|-----------------|--------------|------------|---------------------|
| Session-memory adaptive attacker runner | A1.1, C/D-Bernoulli | The final comment explicitly calls the adaptive attacker a valuable addition and asks for main-body analysis. | High | A command or wrapper runs a retry attacker that carries structured session memory across attempts within a task family, records every attempt, and emits versioned CSV/JSON summaries with pass@k, attempts-to-success, cost, latency, seed, model, prompt mode, task type, and run manifest. |
| Adaptive-vs-fixed comparison outputs | A1.1, C/D-Bernoulli | Reviewers need evidence that the stronger attacker changes or does not change conclusions. | Medium | For each evaluated task family, outputs include fixed-policy pass@1 or predicted retry baseline, adaptive pass@k, absolute/relative lift, confidence intervals, and a flag for hard/borderline/broken classification change. |
| Hard-task robustness analysis | A1.1, A/D-Lifetime | The paper must explain why hard tasks remain robust under a stronger attacker, not merely report numbers. | Medium | A generated analysis table groups adaptive failures by structural bottleneck such as spatial localization, object-location binding, counting, continuous precision, occlusion, or multi-step state tracking, with per-family examples and no long raw-response dumps. |
| Main-body artifact package for adaptive attacker | A1.1 | The final comment asks that results move from appendix to main body. | Medium | Produces paper-ready table/figure inputs and a concise narrative summary naming which hard families remain below the chosen operational threshold under adaptive retries. |
| Statistical confidence reporting | A1.2, C-Threshold, C/D-Bernoulli | Dataset scale and threshold concerns require uncertainty, not only point estimates. | Medium | Pass-rate summaries include binomial confidence intervals or an explicitly justified alternative; threshold claims report margin relative to 40%; small-n groups are flagged as underpowered instead of overclaimed. |
| Dataset scope and sample-size audit | A1.2 | Reviewers asked for limitations around CaptchaWorld, scale, representativeness, and removed task types. | Medium | A dataset audit reports source, task family, sample count, included/excluded status, incompatibility reason, ground-truth validity status, and whether each family supports statistical claims. |
| Larger-dataset integration path | A1.2, A1.3 | The final comment asks for extension to larger datasets like prior work. | High | A manifest format or adapter can ingest at least one larger external benchmark subset, map tasks to COGNITION family labels, validate ground truth/images, and run or mark feasibility with documented blockers. |
| Specialized solver baseline comparison | A1.3 | Reviewer C specifically requested comparison beyond simple MLLM API calls. | High | The revision includes either runnable baseline results or a normalized literature/result comparison against specialized solvers named by reviewers, with task coverage, dataset differences, threat-model differences, and clear non-comparable cases. |
| Benchmark coverage matrix | A1.2, A1.3 | Larger datasets and SOTA solvers will not perfectly align with local task families; the gap must be explicit. | Medium | A table maps each local task family to CaptchaWorld coverage, external dataset coverage, specialized solver coverage, and comparison status: direct, approximate, literature-only, or unavailable. |
| Bernoulli assumption validation | C/D-Bernoulli | Reviewers challenged the independent retry formula. | Medium | The analysis compares Exp2-to-Exp3 predictions against observed retry or adaptive results, reports calibration error by task family, and states where the Bernoulli model is only a first-order approximation. |
| 40% threshold sensitivity analysis | C-Threshold | The threshold was called arbitrary and needs empirical framing. | Low | Outputs show conclusions under adjacent cutoffs or confidence-adjusted classifications and identify which task families are sensitive to the cutoff. |
| Defense methodology pipeline | A1.4, D-HCI/Ops | Reviewers asked for actionable methodology, not just design guidelines. | Medium | A step-by-step pipeline turns empirical hardness factors into practitioner actions: diagnose weak task, choose structural hardening factor, generate variant, validate human-visible clarity qualitatively, run MLLM evaluation, rotate templates, monitor drift. |
| Defense evidence mapping | A1.4, A1.1 | The methodology must be grounded in experiments rather than disconnected advice. | Medium | Each defense recommendation links to one or more measured failure modes and to at least one task-family result showing reduced attacker success or persistent hardness. |
| Reproducibility and provenance manifest | A1.2, A1.3 | Revision evidence must be regenerable and comparable across datasets/models. | Medium | Every experiment output records code revision if available, dataset manifest checksum, prompt config, model/provider, seed, retry policy, sample counts, date, and result schema version. |
| Secret-safe reporting mode | A1.2, A1.3 | The codebase concerns show secrets and raw artifacts can leak; revision docs must avoid secret exposure. | Medium | Logs and generated docs report provider/model labels and artifact paths without printing credential values, raw secret config, or unnecessary raw model traces. |

## Differentiators

These features are not strictly required for acceptance, but would make the revision stronger and more defensible if time allows.

| Feature | Reviewer Themes | Value Proposition | Complexity | Testable Acceptance |
|---------|-----------------|-------------------|------------|---------------------|
| Adaptive memory ablation suite | A1.1, C/D-Bernoulli | Shows whether gains come from remembering failed answers, changing strategy, using task-family hints, or simply more attempts. | Medium | Runs multiple retry policies with the same budget: fixed retry, failed-answer exclusion, strategy-reflection memory, and oracle-free task-family memory. |
| Classification stability dashboard | A1.1, A1.2, C-Threshold | Makes hard/borderline/broken labels less brittle under uncertainty. | Medium | Produces a table that labels each task family as stable hard, stable broken, or threshold-sensitive across adaptive policy and confidence interval variants. |
| External benchmark smoke subset first | A1.3 | Reduces risk before expensive full larger-dataset runs. | Low | A small validated subset from an external dataset runs end-to-end and produces comparable schema output before scaling. |
| Literature-to-experiment reconciliation appendix | A1.3 | Prevents unfair claims when prior specialized solvers use different datasets or threat models. | Medium | For each cited baseline, documents solver type, model backbone, dataset, CAPTCHA categories, interaction assumptions, success metric, and whether direct numeric comparison is valid. |
| Structural hardness scorecard | A1.4, A/D-Lifetime | Converts Section 5.3-style insights into a reusable design checklist. | Medium | Each CAPTCHA candidate receives binary or ordinal scores for recognition-only risk, spatial precision, object binding, dynamic state, counting, interaction continuity, and template diversity. |
| Cost/latency volatility annotation | A/D-Lifetime | Responds to concerns that API pricing and model capability are snapshots. | Low | Tables distinguish stable structural findings from volatile cost/latency/model-market findings and include date-stamped cost assumptions. |
| Human-usability proxy checklist | D-HCI/Ops | Acknowledges HCI concerns without overclaiming a full user study. | Low | Defense methodology includes a checklist for readability, motor precision, visual accessibility, and expected completion burden, marked as qualitative unless measured. |
| Result schema validator | A1.2, A1.3 | Reduces risk that charts or comparisons are built from malformed CSVs. | Medium | A validation command rejects missing columns, unsupported task aliases, duplicate task ids, and inconsistent sample counts before figures are generated. |
| Paper-ready change log | All themes | Helps revision writing by tying each artifact to a reviewer concern. | Low | A generated or curated table lists feature, artifact path, manuscript section, reviewer theme, and status. |

## Anti-Features

Do not build these for this milestone unless the user explicitly changes scope.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Live CAPTCHA attack automation | Out of scope and inconsistent with the research-ethics framing; reviewers care about offline evidence, not turnkey abuse tooling. | Keep experiments dataset-based with owned or authorized images and no browser automation against live deployments. |
| Full reimplementation of every specialized solver | Too expensive for revision scope and likely to introduce unfair, unvalidated clones of prior work. | Prefer official artifacts if available, direct runnable subsets where feasible, and transparent literature comparisons where not. |
| Claiming permanent CAPTCHA security | Reviewers explicitly raised MLLM capability drift and arms-race concerns. | Frame robust tasks as current structural bottlenecks with dated model coverage and future-work caveats. |
| Treating the 40% threshold as a universal boundary | Reviewer C challenged the cutoff. | Present it as an operational heuristic, include sensitivity analysis, and avoid binary overclaims near the threshold. |
| Notebook-only revision evidence | The codebase already relies heavily on notebooks, which weakens reproducibility. | Move reusable analysis into scripts or modules that emit versioned artifacts consumed by notebooks or figures. |
| Raw reasoning-trace dumps in paper artifacts | Raw model outputs can be noisy, sensitive, and hard to review. | Use curated failure categories, aggregate counts, and short sanitized examples only when needed. |
| Broad refactor before evidence generation | The evaluator is monolithic, but reviewer deadlines prioritize empirical artifacts. | Refactor only the pieces needed for adaptive attacker, dataset validation, statistical reporting, and safe reproducibility. |
| Production CAPTCHA service or template generator | Reviewers asked for methodology clarification, not a deployable service. | Provide a practitioner pipeline and proof-of-concept parameterized variants without production infrastructure. |
| Formal human-subjects usability study in this milestone | Valuable but likely too large for revision timing and not part of the final required comments. | Add limitations and a concrete proposed evaluation framework; include lightweight qualitative proxy checks only. |
| Secret/config migration as a standalone security project | Important but secondary to the revision unless it blocks safe execution. | Add secret-safe reporting and avoid reading or printing credential values while generating revision artifacts. |

## Deferrals

These should be documented as limitations or future work rather than forced into the revision feature set.

| Deferred Feature | Defer Until | Reason | Reviewer Theme Handling Now |
|------------------|-------------|--------|------------------------------|
| Formal accessibility and usability study with human participants | Post-revision or separate IRB-scoped work | Requires participant recruitment, protocols, and accessibility-specific metrics. | Address D-HCI/Ops with limitations plus a proposed study methodology. |
| Longitudinal model-drift benchmark over months | Later benchmark maintenance cycle | Requires repeated paid runs across future model releases and stable archived prompts/datasets. | Address A/D-Lifetime with dated results, structural reasoning, and reproducibility manifests. |
| Fine-tuned or distilled attacker models | Later threat-model expansion | Reviewers asked mainly for stronger adaptive retry and specialized solver comparison; custom training is a larger study. | Discuss as out-of-scope attacker sophistication while comparing to available specialized solvers. |
| Full production dynamic-template rotation system | Later applied-systems project | Needs service integration, monitoring, abuse telemetry, and operational ownership. | Provide an actionable design pipeline and proof-of-concept artifact, not production code. |
| Complete migration from script-oriented layout to package architecture | Later maintainability milestone | Important for long-term health but not necessary for immediate revision evidence. | Add only minimal structure needed for reliable experiments and artifact generation. |
| Comprehensive CI and provider contract test suite | Follow-up reproducibility phase | Useful but broad; live provider tests are costly and brittle. | Add targeted smoke tests/validators around new revision-critical outputs. |

## Feature Dependencies

```text
Dataset scope audit -> Statistical confidence reporting
Dataset scope audit -> Larger-dataset integration path
Dataset scope audit -> Benchmark coverage matrix

Session-memory adaptive attacker runner -> Adaptive-vs-fixed comparison outputs
Session-memory adaptive attacker runner -> Hard-task robustness analysis
Adaptive-vs-fixed comparison outputs -> Main-body adaptive artifact package
Statistical confidence reporting -> 40% threshold sensitivity analysis
Bernoulli assumption validation -> Main-body adaptive artifact package

Specialized solver baseline comparison -> Benchmark coverage matrix
Larger-dataset integration path -> Benchmark coverage matrix
Benchmark coverage matrix -> Revision benchmark narrative

Hard-task robustness analysis -> Defense evidence mapping
Defense evidence mapping -> Defense methodology pipeline
Structural hardness scorecard -> Defense methodology pipeline
```

## MVP Recommendation

Prioritize these features for the revision-critical path:

1. Session-memory adaptive attacker runner.
2. Adaptive-vs-fixed comparison outputs.
3. Hard-task robustness analysis.
4. Statistical confidence reporting.
5. Dataset scope and sample-size audit.
6. Specialized solver baseline comparison.
7. Defense methodology pipeline.

Defer full external-dataset scaling until the dataset audit and smoke subset prove that task mapping, ground truth, and metrics are compatible. If larger-dataset integration is blocked by artifact availability or incompatible labels, the roadmap should still produce a transparent benchmark coverage matrix and literature comparison rather than silently dropping A1.3.

## Roadmap-Friendly Phase Shape

| Phase Candidate | Feature Bundle | Primary Reviewer Themes | Success Signal |
|-----------------|----------------|--------------------------|----------------|
| Adaptive Attacker Evidence | Session-memory runner, adaptive-vs-fixed outputs, Bernoulli validation, main-body artifact package | A1.1, C/D-Bernoulli | Paper-ready adaptive results show whether hard tasks remain robust and where adaptive retries help. |
| Statistical Benchmark Audit | Dataset audit, confidence intervals, threshold sensitivity, provenance manifest | A1.2, C-Threshold | Every pass-rate and threshold claim has sample counts, uncertainty, and scope limits. |
| Baseline and Larger-Dataset Strengthening | Specialized solver comparison, external dataset smoke subset, coverage matrix | A1.3 | The paper can state what was directly compared, what was literature-only, and why any gaps remain. |
| Defense Methodology Clarification | Defense pipeline, evidence mapping, structural hardness scorecard, usability proxy checklist | A1.4, D-HCI/Ops | Section 6.2 becomes an actionable procedure tied to empirical findings. |
| Reproducibility Hardening | Secret-safe reporting, schema validator, paper-ready change log | All themes | Revision artifacts can be regenerated without notebook-only or secret-exposure risks. |

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Adaptive attacker feature need | HIGH | Directly requested in final reviewer comment A1.1 and already listed as active project scope. |
| Statistical confidence feature need | HIGH | Directly requested in comments about dataset size, statistical significance, Bernoulli retries, and threshold justification. |
| Defense methodology feature need | HIGH | Directly requested by reviewers B, C, D, and final comment A1.4. |
| Specialized solver comparison feasibility | MEDIUM | Reviewer demand is clear, but implementation depends on available artifacts, licenses, and comparable task coverage. |
| Larger-dataset integration feasibility | MEDIUM | The need is clear, but direct compatibility with local task schemas and ground truth formats must be validated. |
| HCI/user-study feature priority | MEDIUM | Reviewers raised it, but final requested revisions focus on methodology clarification rather than a formal user study. |

## Sources

- `.planning/PROJECT.md` for revision scope, active requirements, constraints, and key decisions.
- `.planning/codebase/ARCHITECTURE.md` for current evaluator/data/result architecture.
- `.planning/codebase/TESTING.md` for validation gaps and existing manual workflow patterns.
- `.planning/codebase/CONCERNS.md` for reproducibility, security, scoring, and artifact risks.
- `/Users/ukun/Desktop/USENIX Sec.txt` for reviewer-comment themes and final requested revisions.
