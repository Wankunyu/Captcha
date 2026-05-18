# Requirements: COGNITION Revision Experiments

**Defined:** 2026-05-15
**Revised:** 2026-05-16 after Shepherding.docx roadmap update
**Core Value:** Produce credible, reproducible revision evidence that directly strengthens the paper's claims about structural CAPTCHA robustness against multimodal LLM attackers.

## v1 Requirements

Requirements for the current shepherded revision milestone. Each requirement maps to exactly one roadmap phase.

### Reproducibility Foundation

- [x] **REPRO-01**: Researcher can install the project from a machine-readable dependency manifest instead of README-only install commands.
- [x] **REPRO-02**: Researcher can run a preflight command that validates task names, dataset paths, prompt files, output paths, expected request counts, and approximate cost visibility before paid model calls.
- [x] **REPRO-03**: Every revision experiment writes a run manifest containing schema version, code revision, dependency versions, dataset summary, prompt/few-shot configuration hashes, provider/model labels, seed, retry policy, and cost-control metadata.
- [x] **REPRO-04**: Every revision experiment writes append-only per-attempt records before deriving aggregate summaries.
- [x] **REPRO-05**: Shareable reports and planning artifacts do not print, copy, or commit credential values from local secret configuration.
- [x] **REPRO-06**: Revision-critical task aliases, result schemas, and scoring helpers have focused regression tests or validators.

### Adaptive Attacker Main-Body Evidence

- [x] **ADAPT-01**: Researcher can run a session-memory adaptive attacker experiment that carries explicit task-level memory across fresh CAPTCHA instances.
- [x] **ADAPT-02**: Adaptive attacker semantics define binary pass/fail feedback only, with no ground-truth labels, coordinates, counts, or per-instance corrective hints exposed to the attacker.
- [x] **ADAPT-03**: Adaptive attempt records include prior failures, policy state, prompt adaptation metadata, selected task, parsed answer, correctness, latency, token usage, cumulative cost metadata, and stopping reason.
- [x] **ADAPT-04**: Researcher can compare fixed retry, i.i.d. Bernoulli Success@k prediction, and adaptive session-memory outcomes under the same task-family budget.
- [x] **ADAPT-05**: Adaptive summaries report success rate, expected attempts, attempts-to-success, cumulative latency, cost estimates, confidence intervals where applicable, and classification changes by task family.
- [x] **ADAPT-06**: Main-body adaptive attacker tables or figure-input CSVs identify robust hard families, improved borderline or instruction-sensitive families, and persistent failures grouped by structural bottleneck.

### Dataset Scope, Statistical Confidence, and Limitations

- [ ] **STAT-01**: Researcher can generate a dataset scope audit that reports included, excluded, incompatible, and underpowered CAPTCHA task families with sample counts and reasons.
- [ ] **STAT-02**: Dataset documentation identifies the two removed CaptchaWorld task types and explains why they are incompatible with the evaluation pipeline.
- [ ] **STAT-03**: Dataset contribution notes cover cleaning, standardization, label and metadata alignment, answer-format normalization, removal of incompatible task types, and task-family grouping.
- [ ] **STAT-04**: Pass-rate summaries include confidence intervals by task and task family.
- [ ] **STAT-05**: Threshold-based hard/borderline/broken labels report their margin relative to the paper's operational cutoff and flag threshold-sensitive families without treating the cutoff as a universal security boundary.
- [ ] **STAT-06**: Existing Exp2-to-Exp3 retry predictions are compared against observed retry or adaptive-compatible outcomes, including prediction error by task family.
- [ ] **STAT-07**: Revision artifacts and prose distinguish scientific model failures from provider exceptions, timeouts, malformed responses, and other infrastructure errors, and state that CaptchaWorld supports structural-pattern claims rather than population-level deployment estimates.

### SOTA Solver and Larger Benchmark Strengthening

- [ ] **BASE-01**: Researcher can create a benchmark coverage matrix mapping local CAPTCHA families to reviewer-cited larger datasets and specialized solver baselines.
- [ ] **BASE-02**: Baseline comparison rows include Halligan, Oedipus, and other relevant dedicated CAPTCHA solver or benchmark systems where available.
- [ ] **BASE-03**: Each baseline row distinguishes solver architecture, threat model, dataset scale, CAPTCHA families, reported metrics, artifact availability, latency/cost coverage, failure-mode analysis, and defense-methodology relevance.
- [ ] **BASE-04**: Baseline comparisons label each row as direct-run, adapter-run, literature-only, approximate, incompatible, or unavailable.
- [ ] **BASE-05**: External baseline or larger-dataset imports validate required fields, metric definitions, task labels, sample counts, and comparability assumptions before appearing in paper-ready outputs.
- [ ] **BASE-06**: The framework can run or import at least one smoke subset for a compatible larger external benchmark or baseline comparison when artifacts are available and feasible within the shepherding timeline.

### Defense Methodology and HCI Scope

- [ ] **DEF-01**: Researcher can generate an actionable defense methodology document that converts empirical hardness factors into practitioner steps.
- [ ] **DEF-02**: The methodology includes a structural hardness scorecard covering recognition-only risk, spatial precision, object-location binding, counting, ordering, interaction continuity, template diversity, and instruction sensitivity.
- [ ] **DEF-03**: The methodology presents a hardening pipeline: diagnose vulnerable pattern, apply structural hardening transformations, preserve human clarity, red-team the hardened design, and address deployment overhead.
- [ ] **DEF-04**: The methodology includes a transformation table mapping vulnerable pattern to hardening transformation, targeted MLLM failure mode, human-clarity constraint, and deployment knob, grounded in the hardened `Select_Animal` case study where applicable.
- [ ] **DEF-05**: Defense artifacts include a lightweight template-family workflow for varying object categories, layouts, rendering styles, instruction phrasing, target counts, distractors, and tolerance parameters without claiming production deployment validation.
- [ ] **DEF-06**: Defense discussion separates empirically validated security effects from qualitative usability, accessibility, maintenance, deployment-overhead, and formal HCI limitations.

### Ethics, Artifact Availability, and Paper Claim Alignment

- [ ] **PAPER-01**: Researcher can generate a reviewer-request traceability table mapping each final requested revision to implementation artifacts, result files, and manuscript sections.
- [ ] **PAPER-02**: Researcher can generate a claim ledger tying each main-body empirical claim to sample counts, confidence intervals, model/provider scope, dataset scope, and artifact paths.
- [ ] **PAPER-03**: Paper-ready figure and table inputs are regenerated from scripted artifacts rather than notebook-only manual state.
- [ ] **PAPER-04**: Final revision outputs include a redacted artifact manifest suitable for coauthors, shepherds, reviewers, and artifact availability verification.
- [ ] **PAPER-05**: The final artifact package includes the evaluation framework, prompt templates, dataset preprocessing and cleaning scripts, task metadata, result-processing scripts, and reproduction documentation.
- [ ] **PAPER-06**: Ethics and disclosure artifacts list stakeholder categories, contacted organizations, dates, channels where available, and response status, including Google VRP closure by January 26, 2026 and January 30, 2026 outreach to OpenAI, Anthropic, hCaptcha, Cloudflare, and Alibaba.
- [ ] **PAPER-07**: Final prose reiterates that evaluation was conducted offline on Open CaptchaWorld, not through high-volume attacks against live production registration flows or protected endpoints, and that the artifact does not release turnkey live-service automation tooling.
- [ ] **PAPER-08**: The final paper package supports May 28 AoE submission expectations: revised paper, color-coded diff, point-by-point change description, and final artifact package.

## v2 Requirements

Deferred to future release. Tracked but not in the current roadmap.

### Longitudinal Robustness

- **LONG-01**: Repeat the benchmark across future model releases over time.
- **LONG-02**: Track model, SDK, API-pricing, and latency drift across longitudinal runs.

### Formal Human Factors

- **HCI-01**: Conduct a formal human-subjects usability and accessibility study for hardened CAPTCHA variants.
- **HCI-02**: Measure human completion time, error rate, frustration, and accessibility effects under approved study protocols, including users with motor or visual impairments.

### Advanced Attackers

- **ADV-01**: Evaluate fine-tuned, distilled, custom-trained, or agentic CAPTCHA-specific attacker models.
- **ADV-02**: Reproduce full specialized solver systems when official artifacts and licenses make this feasible.

### Production Defense

- **PROD-01**: Build a production CAPTCHA service or dynamic-template deployment system.
- **PROD-02**: Integrate live monitoring, abuse telemetry, and template rotation into a high-traffic service.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Live CAPTCHA attack automation | Inconsistent with the offline research-ethics framing and unnecessary for shepherd-requested evidence. |
| Browser automation against real services | The project should remain dataset-based and authorized, not turnkey abuse tooling. |
| Full production CAPTCHA platform | Shepherding asks for methodology clarification and artifact availability, not a deployed service. |
| Formal human-subjects study in this milestone | Valuable but too large for the May 28 AoE revision package and likely requires separate protocol work. |
| Full rewrite of the monolithic evaluator before evidence generation | Broad refactoring risks changing experiment semantics and delaying revision artifacts. |
| Treating the 40% threshold as a universal security boundary | The cutoff must be framed as an operational heuristic with sensitivity analysis. |
| Claiming permanent CAPTCHA security | Results should be dated, scoped to evaluated models/datasets, and framed as structural evidence under current black-box and adaptive MLLM-based attackers. |
| Printing or committing secret values | Credential exposure is unrelated to the paper and creates avoidable risk. |

## Traceability

Which phases cover which requirements. Updated during roadmap revision from `Shepherding.docx`.

| Requirement | Phase | Status |
|-------------|-------|--------|
| REPRO-01 | Phase 1 | Complete |
| REPRO-02 | Phase 1 | Complete |
| REPRO-03 | Phase 1 | Complete |
| REPRO-04 | Phase 1 | Complete |
| REPRO-05 | Phase 1 | Complete |
| REPRO-06 | Phase 1 | Complete |
| ADAPT-01 | Phase 2 | Complete |
| ADAPT-02 | Phase 2 | Complete |
| ADAPT-03 | Phase 2 | Complete |
| ADAPT-04 | Phase 2 | Complete |
| ADAPT-05 | Phase 2 | Complete |
| ADAPT-06 | Phase 2 | Complete |
| STAT-01 | Phase 3 | Pending |
| STAT-02 | Phase 3 | Pending |
| STAT-03 | Phase 3 | Pending |
| STAT-04 | Phase 3 | Pending |
| STAT-05 | Phase 3 | Pending |
| STAT-06 | Phase 3 | Pending |
| STAT-07 | Phase 3 | Pending |
| BASE-01 | Phase 4 | Pending |
| BASE-02 | Phase 4 | Pending |
| BASE-03 | Phase 4 | Pending |
| BASE-04 | Phase 4 | Pending |
| BASE-05 | Phase 4 | Pending |
| BASE-06 | Phase 4 | Pending |
| DEF-01 | Phase 5 | Pending |
| DEF-02 | Phase 5 | Pending |
| DEF-03 | Phase 5 | Pending |
| DEF-04 | Phase 5 | Pending |
| DEF-05 | Phase 5 | Pending |
| DEF-06 | Phase 5 | Pending |
| PAPER-01 | Phase 6 | Pending |
| PAPER-02 | Phase 6 | Pending |
| PAPER-03 | Phase 6 | Pending |
| PAPER-04 | Phase 6 | Pending |
| PAPER-05 | Phase 6 | Pending |
| PAPER-06 | Phase 6 | Pending |
| PAPER-07 | Phase 6 | Pending |
| PAPER-08 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 39 total
- Mapped to phases: 39
- Unmapped: 0

---
*Requirements revised: 2026-05-16 from Shepherding.docx*
