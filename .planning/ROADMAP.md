# Roadmap: COGNITION Revision Experiments

## Overview

This roadmap turns the USENIX Security revision requests into reproducible research artifacts. The work starts by making experiment execution safe and traceable, then adds offline statistical and dataset-scope evidence before running the headline adaptive attacker study. External baseline strengthening, defense methodology, and final paper QA follow after the local evidence contracts are stable, so manuscript claims can stay tied to versioned artifacts instead of notebook-only state.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Reproducibility and Safety Foundation** - Establish install, preflight, manifest, attempt-log, secret-safety, and validator contracts for all revision experiments.
- [ ] **Phase 2: Statistical Confidence and Dataset Scope** - Produce offline confidence, threshold-sensitivity, dataset audit, retry-calibration, and infrastructure-error reporting.
- [ ] **Phase 3: Adaptive Attacker Evidence** - Run and analyze the session-memory adaptive attacker against fixed retry and Bernoulli baselines.
- [ ] **Phase 4: Benchmark and Baseline Strengthening** - Add fair comparison hooks for specialized CAPTCHA solvers and larger external datasets where compatible.
- [ ] **Phase 5: Defense Methodology Artifacts** - Convert measured structural hardness evidence into an actionable practitioner methodology.
- [ ] **Phase 6: Paper Artifact QA and Claim Alignment** - Tie every reviewer request and manuscript claim to regenerated, redacted, shareable artifacts.

## Phase Details

### Phase 1: Reproducibility and Safety Foundation
**Goal**: Researchers can run revision experiments through safe, validated, reproducible contracts before spending provider budget.
**Depends on**: Nothing (first phase)
**Requirements**: REPRO-01, REPRO-02, REPRO-03, REPRO-04, REPRO-05, REPRO-06
**Reviewer alignment**: Supports reviewer concerns about reproducibility, dataset validity, cost-controlled reruns, and safe shareable artifacts.
**Success Criteria** (what must be TRUE):
  1. Researcher can install the project from a machine-readable dependency manifest instead of README-only commands.
  2. Researcher can run a preflight command that validates task aliases, dataset paths, prompts, output paths, and expected request counts before paid model calls.
  3. Every revision experiment writes a versioned run manifest and append-only per-attempt records before aggregate summaries are derived.
  4. Shareable reports and planning artifacts never print, copy, or commit credential values from local secret configuration.
  5. Revision-critical task aliases, result schemas, and scoring helpers are covered by focused regression tests or validators.
**Plans**: 5 plans
Plans:
- [ ] 01-01-PLAN.md - Add uv dependency manifest, lockfile, and local validation documentation.
- [ ] 01-02-PLAN.md - Remove import-time side effects and establish secret-safe provider smoke boundaries.
- [ ] 01-03-PLAN.md - Define versioned revision artifact schemas and append-only writer.
- [ ] 01-04-PLAN.md - Add offline preflight validation for task aliases, datasets, prompts, outputs, and request counts.
- [ ] 01-05-PLAN.md - Wire explicit revision artifact mode into the evaluator and add focused regression tests.

### Phase 2: Statistical Confidence and Dataset Scope
**Goal**: Researchers can quantify uncertainty, sample support, threshold sensitivity, retry-model validity, and infrastructure-vs-scientific failures for existing and future results.
**Depends on**: Phase 1
**Requirements**: STAT-01, STAT-02, STAT-03, STAT-04, STAT-05
**Reviewer alignment**: Addresses reviewer comments about CaptchaWorld limitations, sample size, statistical significance, the 40% threshold, and Bernoulli retry assumptions.
**Success Criteria** (what must be TRUE):
  1. Researcher can generate a dataset scope audit listing included, excluded, incompatible, and underpowered CAPTCHA families with sample counts and reasons.
  2. Pass-rate summaries report confidence intervals by task and task family.
  3. Hard, borderline, and broken labels show their margin relative to the operational cutoff and flag threshold-sensitive families.
  4. Existing Exp2-to-Exp3 retry predictions are compared against observed retry or adaptive-compatible outcomes with prediction error by task family.
  5. Revision artifacts distinguish scientific model failures from provider exceptions, timeouts, malformed responses, and other infrastructure errors.
**Plans**: TBD

### Phase 3: Adaptive Attacker Evidence
**Goal**: Researchers can evaluate a stronger session-memory attacker and explain which hard CAPTCHA families remain robust under adaptive retries.
**Depends on**: Phase 2
**Requirements**: ADAPT-01, ADAPT-02, ADAPT-03, ADAPT-04, ADAPT-05, ADAPT-06
**Reviewer alignment**: Directly answers the request to move adaptive/session-memory attacker results into the main body and explain persistent hard-task robustness.
**Success Criteria** (what must be TRUE):
  1. Researcher can run a session-memory adaptive attacker experiment that carries explicit state across attempts within a task family.
  2. Adaptive attempt records include prior failures, policy state, prompt adaptation metadata, selected task, parsed answer, correctness, latency, token usage, and cumulative cost metadata.
  3. Researcher can compare fixed retry, i.i.d. Bernoulli prediction, and adaptive session-memory outcomes under the same task-family budget.
  4. Adaptive summaries report pass@k, attempts-to-success, cumulative latency, cost estimates, confidence intervals, and classification changes by task family.
  5. Paper-ready adaptive tables or figure-input CSVs identify robust hard families, improved borderline families, and persistent failures grouped by structural bottleneck.
**Plans**: TBD

### Phase 4: Benchmark and Baseline Strengthening
**Goal**: Researchers can make fair, labeled comparisons between local COGNITION results, specialized solver baselines, and larger external datasets when artifacts are compatible.
**Depends on**: Phase 3
**Requirements**: BASE-01, BASE-02, BASE-03, BASE-04, BASE-05
**Reviewer alignment**: Addresses requests for comparison against specialized CAPTCHA solvers and larger benchmark datasets without overstating incompatible evidence.
**Success Criteria** (what must be TRUE):
  1. Researcher can create a benchmark coverage matrix mapping local CAPTCHA families to reviewer-cited larger datasets and specialized solver baselines.
  2. Baseline comparison rows are labeled as direct-run, adapter-run, literature-only, approximate, incompatible, or unavailable.
  3. External baseline or larger-dataset imports validate required fields, metric definitions, task labels, sample counts, and comparability assumptions before appearing in paper-ready outputs.
  4. Researcher can run or import at least one smoke subset for a compatible external larger-dataset or baseline comparison when artifacts are available.
  5. Paper-ready baseline tables separate off-the-shelf MLLM API results from specialized solver results and document dataset or threat-model differences.
**Plans**: TBD

### Phase 5: Defense Methodology Artifacts
**Goal**: Researchers can generate actionable defense methodology artifacts grounded in measured structural hardness evidence.
**Depends on**: Phase 4
**Requirements**: DEF-01, DEF-02, DEF-03, DEF-04, DEF-05
**Reviewer alignment**: Converts high-level defense guidelines into a reusable methodology while preserving limits around usability and production deployment claims.
**Success Criteria** (what must be TRUE):
  1. Researcher can generate an actionable defense methodology document that turns empirical hardness factors into practitioner steps.
  2. The methodology includes a structural hardness scorecard for recognition-only risk, spatial precision, object binding, dynamic state, counting, interaction continuity, and template diversity.
  3. Each defense recommendation links to measured evidence from task-family results, adaptive attacker outcomes, or failure-mode analysis.
  4. Defense artifacts include a lightweight template-rotation workflow for varying rendering parameters, instructions, target composition, or task structure without claiming production validation.
  5. Defense discussion separates empirically validated security effects from qualitative usability, accessibility, maintenance, and operational-overhead limitations.
**Plans**: TBD

### Phase 6: Paper Artifact QA and Claim Alignment
**Goal**: Researchers can verify that manuscript claims, reviewer responses, figures, tables, and shareable artifacts are regenerated, traceable, and appropriately scoped.
**Depends on**: Phase 5
**Requirements**: PAPER-01, PAPER-02, PAPER-03, PAPER-04
**Reviewer alignment**: Ensures final revision text visibly answers each requested change and does not exceed the generated evidence.
**Success Criteria** (what must be TRUE):
  1. Researcher can generate a reviewer-request traceability table mapping each final requested revision to implementation artifacts, result files, and manuscript sections.
  2. Researcher can generate a claim ledger tying each main-body empirical claim to sample counts, confidence intervals, model/provider scope, dataset scope, and artifact paths.
  3. Paper-ready figure and table inputs are regenerated from scripted artifacts rather than notebook-only manual state.
  4. Final revision outputs include a redacted artifact manifest suitable for sharing with coauthors or reviewers.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Reproducibility and Safety Foundation | 0/TBD | Not started | - |
| 2. Statistical Confidence and Dataset Scope | 0/TBD | Not started | - |
| 3. Adaptive Attacker Evidence | 0/TBD | Not started | - |
| 4. Benchmark and Baseline Strengthening | 0/TBD | Not started | - |
| 5. Defense Methodology Artifacts | 0/TBD | Not started | - |
| 6. Paper Artifact QA and Claim Alignment | 0/TBD | Not started | - |
