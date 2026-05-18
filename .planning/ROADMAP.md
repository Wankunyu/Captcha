# Roadmap: COGNITION Shepherded Revision Experiments

## Overview

This roadmap turns the latest shepherding plan into reproducible paper and artifact deliverables for the May 28 AoE revision deadline. The work still starts with a safety/reproducibility foundation before any additional costly provider runs, but the downstream order now follows the shepherding-response flow: adaptive attacker evidence first, dataset/statistical limitations second, SOTA/larger-benchmark strengthening third, defense methodology fourth, and final ethics/artifact/paper alignment last.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Reproducibility and Safety Foundation** - Establish install, preflight, manifest, attempt-log, secret-safety, prompt/few-shot hash, cost-preview, and validator contracts before additional provider runs. Completed 2026-05-16.
- [ ] **Phase 2: Adaptive Attacker Main-Body Evidence** - Run, analyze, and package session-memory adaptive attacker evidence for the main paper body.
- [ ] **Phase 3: Dataset Scope, Statistical Confidence, and Limitations** - Produce dataset-scope, statistical-confidence, retry-calibration, infrastructure-error, and limitations artifacts.
- [ ] **Phase 4: SOTA Solver and Larger Benchmark Strengthening** - Add fair comparison hooks for Halligan, Oedipus, specialized CAPTCHA solvers, and compatible larger external benchmark subsets.
- [ ] **Phase 5: Defense Methodology and HCI Scope** - Convert measured structural hardness evidence into an actionable practitioner methodology with explicit human-clarity and HCI limitations.
- [ ] **Phase 6: Ethics, Artifact Availability, and Paper Claim Alignment** - Tie reviewer requests, disclosure details, artifact availability, figures/tables, and manuscript claims to regenerated, redacted, shareable artifacts.

## Phase Details

### Phase 1: Reproducibility and Safety Foundation
**Goal**: Researchers can run revision experiments through safe, validated, reproducible contracts before spending provider budget.
**Depends on**: Nothing (first phase)
**Requirements**: REPRO-01, REPRO-02, REPRO-03, REPRO-04, REPRO-05, REPRO-06
**Reviewer alignment**: Supports shepherd concerns about reproducibility, dataset validity, cost-controlled reruns, prompt/few-shot provenance, and safe shareable artifacts.
**Success Criteria** (what must be TRUE):
  1. Researcher can install the project from a machine-readable dependency manifest instead of README-only commands.
  2. Researcher can run a preflight command that validates task aliases, dataset paths, prompts, output paths, expected request counts, and approximate cost visibility before paid model calls.
  3. Every revision experiment writes a versioned run manifest and append-only per-attempt records before aggregate summaries are derived.
  4. Shareable reports and planning artifacts never print, copy, or commit credential values from local secret configuration.
  5. Revision-critical task aliases, result schemas, and scoring helpers are covered by focused regression tests or validators.
**Plans**: 5 plans
Plans:
- [x] 01-01-PLAN.md - Add uv dependency manifest, lockfile, and local validation documentation.
- [x] 01-02-PLAN.md - Remove import-time side effects and establish secret-safe provider smoke boundaries.
- [x] 01-03-PLAN.md - Define versioned revision artifact schemas and append-only writer.
- [x] 01-04-PLAN.md - Add offline preflight validation for task aliases, datasets, prompts, outputs, request counts, and cost preview.
- [x] 01-05-PLAN.md - Wire explicit revision artifact mode into the evaluator and add focused regression tests.

### Phase 2: Adaptive Attacker Main-Body Evidence
**Goal**: Researchers can evaluate the session-memory adaptive attacker and produce main-body-ready evidence explaining which hard CAPTCHA families remain robust.
**Depends on**: Phase 1
**Requirements**: ADAPT-01, ADAPT-02, ADAPT-03, ADAPT-04, ADAPT-05, ADAPT-06
**Reviewer alignment**: Directly answers the shepherding request to move adaptive/session-memory attacker results from appendix to main body and clarify why robustness is not only a fixed-prompt or i.i.d. artifact.
**Success Criteria** (what must be TRUE):
  1. Researcher can run a session-memory adaptive attacker that carries task-level memory across fresh CAPTCHA instances.
  2. Adaptive attacker semantics explicitly state binary pass/fail feedback only, with no ground-truth labels, coordinates, counts, or corrective hints.
  3. Adaptive attempt records capture prior failures, policy state, prompt adaptation metadata, parsed answer, correctness, latency, token usage, cumulative cost, and stopping reason.
  4. Fixed retry, Bernoulli Success@k, and adaptive outcomes are compared under the same task-family budget.
  5. Main-body adaptive tables or figure-input CSVs report success rate, expected attempts, cost/latency where available, task-family changes, and persistent hard-family failures grouped by structural bottleneck.
**Plans**: 5 plans
Plans:
- [x] 02-01-PLAN.md - Define adaptive schemas, policy-memory safety validators, and append-only adaptive artifact writer.
- [x] 02-02-PLAN.md - Add provider-free adaptive preflight with request counts, hashes, output paths, and adaptive semantics.
- [x] 02-03-PLAN.md - Implement the offline dataset-based adaptive attacker loop with explicit local memory.
- [ ] 02-04-PLAN.md - Build task-type comparison table inputs for Exp2, Bernoulli Success@k, fixed retry, and adaptive outcomes.
- [ ] 02-05-PLAN.md - Add offline end-to-end validation and adaptive reproduction notes with optional gated paid-smoke documentation.

### Phase 3: Dataset Scope, Statistical Confidence, and Limitations
**Goal**: Researchers can quantify uncertainty, dataset support, removed/incompatible task types, threshold sensitivity, retry-model validity, infrastructure-vs-scientific failures, and benchmark generalizability limits.
**Depends on**: Phase 2
**Requirements**: STAT-01, STAT-02, STAT-03, STAT-04, STAT-05, STAT-06, STAT-07
**Reviewer alignment**: Addresses shepherd concerns about CaptchaWorld limitations, sample size, representativeness, statistical significance, the 40% threshold, and Bernoulli retry assumptions.
**Success Criteria** (what must be TRUE):
  1. Researcher can generate a dataset scope audit listing included, excluded, incompatible, and underpowered CAPTCHA families with sample counts and reasons.
  2. The artifact set identifies the two removed CaptchaWorld task types and explains pipeline incompatibility.
  3. Dataset contribution notes cover cleaning, standardization, label/metadata alignment, answer-format normalization, task-family grouping, and removal decisions.
  4. Pass-rate summaries report confidence intervals by task and task family.
  5. Hard, borderline, and broken labels show margin relative to the operational cutoff and flag threshold-sensitive families.
  6. Retry predictions are compared against observed retry or adaptive-compatible outcomes with prediction error by task family.
  7. Limitations prose avoids population-level overclaiming and frames CaptchaWorld as a curated, task-diverse benchmark for recurring structural hardness patterns.
**Plans**: TBD

### Phase 4: SOTA Solver and Larger Benchmark Strengthening
**Goal**: Researchers can make fair, labeled comparisons between local COGNITION results, Halligan, Oedipus, other specialized solver baselines, and larger external datasets when artifacts are compatible.
**Depends on**: Phase 3
**Requirements**: BASE-01, BASE-02, BASE-03, BASE-04, BASE-05, BASE-06
**Reviewer alignment**: Addresses shepherd requests for comparison against SOTA CAPTCHA solvers and larger benchmark datasets without overstating incompatible evidence.
**Success Criteria** (what must be TRUE):
  1. Researcher can create a benchmark coverage matrix mapping local CAPTCHA families to Halligan, Oedipus, reviewer-cited larger datasets, and specialized solver baselines.
  2. Baseline comparison rows distinguish solver architecture, threat model, dataset scale, CAPTCHA families, reported metrics, artifact availability, latency/cost coverage, failure-mode analysis, and defense-methodology relevance.
  3. Rows are labeled as direct-run, adapter-run, literature-only, approximate, incompatible, or unavailable.
  4. External baseline or larger-dataset imports validate fields, metric definitions, task labels, sample counts, and comparability assumptions before appearing in paper-ready outputs.
  5. Researcher can run or import at least one smoke subset for a compatible larger external benchmark or baseline comparison when artifacts are available and feasible within the shepherding timeline.
  6. Paper-ready baseline tables separate off-the-shelf MLLM API results from specialized solver results and document dataset or threat-model differences.
**Plans**: TBD

### Phase 5: Defense Methodology and HCI Scope
**Goal**: Researchers can generate an actionable defense methodology grounded in measured structural hardness evidence while clearly scoping human-clarity and formal HCI claims.
**Depends on**: Phase 4
**Requirements**: DEF-01, DEF-02, DEF-03, DEF-04, DEF-05, DEF-06
**Reviewer alignment**: Converts high-level defense guidelines into a reusable practitioner methodology while preserving limits around usability, accessibility, maintenance, and production deployment claims.
**Success Criteria** (what must be TRUE):
  1. Researcher can generate an actionable defense methodology document that turns empirical hardness factors into practitioner steps.
  2. The methodology includes a structural hardness scorecard for recognition-only risk, spatial precision, object-location binding, counting, ordering, interaction continuity, template diversity, and instruction sensitivity.
  3. The methodology presents a hardening pipeline: diagnose vulnerable pattern, apply structural hardening transformations, preserve human clarity, red-team the hardened design, and address deployment overhead.
  4. A transformation table maps vulnerable pattern to hardening transformation, targeted MLLM failure mode, human-clarity constraint, and deployment knob.
  5. Defense artifacts include a lightweight template-family workflow for varying object categories, layouts, rendering styles, instruction phrasing, target counts, distractors, and tolerance parameters.
  6. Defense discussion separates empirically validated security effects from qualitative usability, accessibility, maintenance, deployment-overhead, and formal HCI limitations.
**Plans**: TBD

### Phase 6: Ethics, Artifact Availability, and Paper Claim Alignment
**Goal**: Researchers can verify that manuscript claims, reviewer responses, disclosure details, figures, tables, and availability artifacts are regenerated, traceable, redacted, and appropriately scoped for May 28 AoE submission.
**Depends on**: Phase 5
**Requirements**: PAPER-01, PAPER-02, PAPER-03, PAPER-04, PAPER-05, PAPER-06, PAPER-07, PAPER-08
**Reviewer alignment**: Ensures final revision text visibly answers each shepherded requirement, documents ethics/disclosure scope, provides an availability-ready artifact package, and does not exceed the generated evidence.
**Success Criteria** (what must be TRUE):
  1. Researcher can generate a reviewer-request traceability table mapping each requested revision to implementation artifacts, result files, and manuscript sections.
  2. Researcher can generate a claim ledger tying each main-body empirical claim to sample counts, confidence intervals, model/provider scope, dataset scope, and artifact paths.
  3. Paper-ready figure and table inputs are regenerated from scripted artifacts rather than notebook-only manual state.
  4. Final revision outputs include a redacted artifact manifest suitable for coauthors, shepherds, reviewers, and artifact availability verification.
  5. Artifact package includes the evaluation framework, prompt templates, dataset preprocessing and cleaning scripts, task metadata, result-processing scripts, and reproduction documentation.
  6. Ethics/disclosure artifacts list stakeholder categories, contacted organizations, dates, channels where available, and response status, including Google VRP closure by January 26, 2026 and January 30, 2026 outreach to OpenAI, Anthropic, hCaptcha, Cloudflare, and Alibaba.
  7. Final prose reiterates offline Open CaptchaWorld evaluation, no high-volume live production attacks, and no turnkey live-service automation tooling.
  8. Final paper package supports May 28 AoE submission expectations: revised paper, color-coded diff, point-by-point change description, and final artifact package.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Reproducibility and Safety Foundation | 5/5 | Complete | 2026-05-16 |
| 2. Adaptive Attacker Main-Body Evidence | 3/5 | Executing | - |
| 3. Dataset Scope, Statistical Confidence, and Limitations | 0/TBD | Not started | - |
| 4. SOTA Solver and Larger Benchmark Strengthening | 0/TBD | Not started | - |
| 5. Defense Methodology and HCI Scope | 0/TBD | Not started | - |
| 6. Ethics, Artifact Availability, and Paper Claim Alignment | 0/TBD | Not started | - |

---
*Roadmap revised: 2026-05-16 from Shepherding.docx*
