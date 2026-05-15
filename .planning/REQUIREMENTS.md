# Requirements: COGNITION Revision Experiments

**Defined:** 2026-05-15
**Core Value:** Produce credible, reproducible revision evidence that directly strengthens the paper's claims about structural CAPTCHA robustness against multimodal LLM attackers.

## v1 Requirements

Requirements for the current revision milestone. Each requirement should map to exactly one roadmap phase.

### Reproducibility Foundation

- [ ] **REPRO-01**: Researcher can install the project from a machine-readable dependency manifest instead of README-only install commands.
- [ ] **REPRO-02**: Researcher can run a preflight command that validates task names, dataset paths, prompt files, output paths, and expected request counts before paid model calls.
- [ ] **REPRO-03**: Every revision experiment writes a run manifest containing schema version, code revision, dependency versions, dataset summary, prompt configuration, provider/model labels, seed, retry policy, and cost-control metadata.
- [ ] **REPRO-04**: Every revision experiment writes append-only per-attempt records before deriving aggregate summaries.
- [ ] **REPRO-05**: Shareable reports and planning artifacts do not print, copy, or commit credential values from local secret configuration.
- [ ] **REPRO-06**: Revision-critical task aliases, result schemas, and scoring helpers have focused regression tests or validators.

### Dataset and Statistical Evidence

- [ ] **STAT-01**: Researcher can generate a dataset scope audit that reports included, excluded, incompatible, and underpowered CAPTCHA task families with sample counts and reasons.
- [ ] **STAT-02**: Pass-rate summaries include confidence intervals by task and task family.
- [ ] **STAT-03**: Threshold-based hard/borderline/broken labels report their margin relative to the paper's operational cutoff and flag threshold-sensitive families.
- [ ] **STAT-04**: Existing Exp2-to-Exp3 retry predictions are compared against observed retry or adaptive outcomes, including prediction error by task family.
- [ ] **STAT-05**: The revision artifact set distinguishes scientific model failures from infrastructure errors such as provider exceptions, timeouts, or malformed responses.

### Adaptive Attacker Evidence

- [ ] **ADAPT-01**: Researcher can run a session-memory adaptive attacker experiment that carries explicit state across attempts within a task family.
- [ ] **ADAPT-02**: Adaptive attacker attempts record prior failures, policy state, prompt adaptation metadata, selected task, parsed answer, correctness, latency, token usage, and cumulative cost metadata.
- [ ] **ADAPT-03**: Researcher can compare fixed retry, i.i.d. Bernoulli prediction, and adaptive session-memory outcomes under the same task-family budget.
- [ ] **ADAPT-04**: Adaptive results report pass@k, attempts-to-success, cumulative latency, cost estimates, confidence intervals, and classification changes by task family.
- [ ] **ADAPT-05**: Hard-task robustness analysis groups persistent adaptive failures by structural bottleneck such as spatial localization, object-location binding, counting, continuous precision, occlusion, or multi-step state tracking.
- [ ] **ADAPT-06**: Paper-ready adaptive attacker tables or figure-input CSVs identify which hard CAPTCHA families remain robust and which borderline families improve under adaptation.

### Benchmark and Baseline Strengthening

- [ ] **BASE-01**: Researcher can create a benchmark coverage matrix mapping local CAPTCHA families to reviewer-cited larger datasets and specialized solver baselines.
- [ ] **BASE-02**: Baseline comparisons label each row as direct-run, adapter-run, literature-only, approximate, incompatible, or unavailable.
- [ ] **BASE-03**: External baseline or larger-dataset imports validate required fields, metric definitions, task labels, sample counts, and comparability assumptions before appearing in paper-ready outputs.
- [ ] **BASE-04**: The framework can run or import at least one smoke subset for an external larger-dataset or baseline comparison when artifacts are available and compatible.
- [ ] **BASE-05**: Paper-ready baseline tables separate off-the-shelf MLLM API results from specialized solver results and document dataset/threat-model differences.

### Defense Methodology

- [ ] **DEF-01**: Researcher can generate an actionable defense methodology document that converts empirical hardness factors into practitioner steps.
- [ ] **DEF-02**: Defense methodology includes a structural hardness scorecard covering recognition-only risk, spatial precision, object binding, dynamic state, counting, interaction continuity, and template diversity.
- [ ] **DEF-03**: Each defense recommendation links to measured evidence from task-family results, adaptive attacker outcomes, or failure-mode analysis.
- [ ] **DEF-04**: Defense artifacts include a lightweight template-rotation workflow that explains how to vary rendering parameters, instructions, target composition, or task structure without claiming production deployment validation.
- [ ] **DEF-05**: Defense discussion distinguishes empirically validated security effects from qualitative usability, accessibility, maintenance, and operational-overhead limitations.

### Paper Artifact QA

- [ ] **PAPER-01**: Researcher can generate a reviewer-request traceability table mapping each final requested revision to implementation artifacts, result files, and manuscript sections.
- [ ] **PAPER-02**: Researcher can generate a claim ledger that ties each main-body empirical claim to sample counts, confidence intervals, model/provider scope, dataset scope, and artifact paths.
- [ ] **PAPER-03**: Paper-ready figure and table inputs are regenerated from scripted artifacts rather than notebook-only manual state.
- [ ] **PAPER-04**: Final revision outputs include a redacted artifact manifest suitable for sharing with coauthors or reviewers.

## v2 Requirements

Deferred to future release. Tracked but not in the current roadmap.

### Longitudinal Robustness

- **LONG-01**: Repeat the benchmark across future model releases over time.
- **LONG-02**: Track model, SDK, API-pricing, and latency drift across longitudinal runs.

### Human Factors

- **HCI-01**: Conduct a formal human-subjects usability and accessibility study for hardened CAPTCHA variants.
- **HCI-02**: Measure human completion time, error rate, frustration, and accessibility effects under approved study protocols.

### Advanced Attackers

- **ADV-01**: Evaluate fine-tuned, distilled, or custom-trained attacker models.
- **ADV-02**: Reproduce full specialized solver systems when official artifacts and licenses make this feasible.

### Production Defense

- **PROD-01**: Build a production CAPTCHA service or dynamic-template deployment system.
- **PROD-02**: Integrate live monitoring, abuse telemetry, and template rotation into a high-traffic service.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Live CAPTCHA attack automation | Inconsistent with the offline research-ethics framing and unnecessary for reviewer-requested evidence. |
| Browser automation against real services | The project should remain dataset-based and authorized, not turnkey abuse tooling. |
| Full production CAPTCHA platform | Reviewers asked for methodology clarification, not a deployed service. |
| Formal human-subjects study in this milestone | Valuable but too large for the current paper-revision scope and likely requires separate protocol work. |
| Full rewrite of the monolithic evaluator before evidence generation | Broad refactoring risks changing experiment semantics and delaying revision artifacts. |
| Treating the 40% threshold as a universal security boundary | The cutoff must be framed as an operational heuristic with sensitivity analysis. |
| Claiming permanent CAPTCHA security | Results should be dated, scoped to evaluated models/datasets, and framed as structural evidence under current capabilities. |
| Printing or committing secret values | Credential exposure is unrelated to the paper and creates avoidable risk. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| REPRO-01 | TBD | Pending |
| REPRO-02 | TBD | Pending |
| REPRO-03 | TBD | Pending |
| REPRO-04 | TBD | Pending |
| REPRO-05 | TBD | Pending |
| REPRO-06 | TBD | Pending |
| STAT-01 | TBD | Pending |
| STAT-02 | TBD | Pending |
| STAT-03 | TBD | Pending |
| STAT-04 | TBD | Pending |
| STAT-05 | TBD | Pending |
| ADAPT-01 | TBD | Pending |
| ADAPT-02 | TBD | Pending |
| ADAPT-03 | TBD | Pending |
| ADAPT-04 | TBD | Pending |
| ADAPT-05 | TBD | Pending |
| ADAPT-06 | TBD | Pending |
| BASE-01 | TBD | Pending |
| BASE-02 | TBD | Pending |
| BASE-03 | TBD | Pending |
| BASE-04 | TBD | Pending |
| BASE-05 | TBD | Pending |
| DEF-01 | TBD | Pending |
| DEF-02 | TBD | Pending |
| DEF-03 | TBD | Pending |
| DEF-04 | TBD | Pending |
| DEF-05 | TBD | Pending |
| PAPER-01 | TBD | Pending |
| PAPER-02 | TBD | Pending |
| PAPER-03 | TBD | Pending |
| PAPER-04 | TBD | Pending |

**Coverage:**
- v1 requirements: 31 total
- Mapped to phases: 0
- Unmapped: 31

---
*Requirements defined: 2026-05-15*
*Last updated: 2026-05-15 after initial definition*
