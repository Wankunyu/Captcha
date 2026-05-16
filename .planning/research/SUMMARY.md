# Project Research Summary

**Project:** COGNITION Revision Experiments
**Domain:** Offline CAPTCHA/MLLM security evaluation for paper-revision evidence
**Researched:** 2026-05-15
**Confidence:** HIGH for local roadmap shape; MEDIUM for external baseline feasibility until artifacts are inspected

## Executive Summary

COGNITION is a local Python research toolkit for producing post-acceptance revision evidence for a CAPTCHA/MLLM security paper. The project should not become a production CAPTCHA service, browser automation framework, or notebook-only analysis bundle. Experts would build this kind of revision work as an offline, reproducible experiment pipeline: every claim should trace to a run manifest, immutable attempt rows, validated result schemas, statistical uncertainty, and paper-ready figure/table inputs.

The recommended approach is an additive revision layer around the existing evaluator. Keep `run_eval.py`, `run_single_experiment.py`, and current result layouts as compatibility surfaces, then add narrow root-level runners and offline artifact generators for reproducibility, confidence intervals, adaptive attacker runs, baseline comparison, defense methodology, and final paper QA. Adopt `pyproject.toml`, locked dependencies, SciPy-backed statistics, Pydantic schema validation, pytest checks, and Ruff, but avoid a broad package migration before revision evidence exists.

The main risks are clear: an adaptive attacker that is only a renamed fixed retry loop, confidence intervals that arrive too late to constrain paper claims, unfair SOTA comparisons, invalid external dataset conversion, secret leakage, provider-cost surprises, and overclaiming beyond the evidence. Mitigate these with explicit adaptive state, per-attempt logs, preflight manifests, comparability labels, dataset validation fixtures, secret-safe exports, and a final claim ledger before manuscript updates.

## Key Findings

### Recommended Stack

Keep the stack small and research-oriented. The repository already has the right base shape: Python scripts, local datasets, CSV/JSON artifacts, notebook consumers, and provider adapters for OpenAI, Anthropic, Gemini, and Fireworks-compatible models. The revision should add reproducibility and validation around this stack rather than replacing it with a service, database, experiment platform, or large framework migration.

**Core technologies:**
- Python `>=3.10`, with Python 3.11 as the first locked/tested target: matches the current framework and avoids runtime churn.
- `pyproject.toml` plus `uv.lock` or an exported lock file: gives machine-readable dependencies and reproducible installs.
- Existing `argparse` CLIs: sufficient for revision commands and lower risk than adding Typer or Click now.
- Git LFS for CAPTCHA image data: keep for existing binary datasets, but do not expand generated artifacts in git.
- SciPy: required for binomial confidence intervals, bootstrap intervals, and threshold-claim uncertainty.
- Pydantic v2: validate run manifests, attempt rows, baseline imports, and summary schemas.
- pytest: focused regression tests for scoring, schema validation, confidence calculations, CLI preflight, and dataset fixtures.
- Ruff: lightweight lint and format enforcement.

**Do not add now:**
- MLflow, W&B, DVC, Airflow, Prefect, Hydra, Poetry, databases, web frameworks, browser automation, live CAPTCHA attack tooling, or full external solver reimplementations before artifact research justifies them.

### Expected Features

The revision-critical feature set is driven by reviewer themes: adaptive attacker evidence, dataset scope and statistical significance, stronger benchmarks and baselines, retry-model validity, threshold sensitivity, defense methodology, and reproducible safe artifacts.

**Must have (table stakes):**
- Session-memory adaptive attacker runner: explicit attacker state, retry policy, attempt logs, and pass@k outputs.
- Adaptive-vs-fixed comparison outputs: fixed retry, Bernoulli prediction, and adaptive empirical results side by side.
- Hard-task robustness analysis: explains persistent failures by structural bottleneck, not just aggregate pass rates.
- Statistical confidence reporting: intervals, denominators, threshold relations, and small-n warnings for task families.
- Dataset scope and sample-size audit: included/excluded task families, counts, validity status, and statistical support.
- Baseline and larger-dataset comparison hooks: normalized schemas, task-family mappings, and comparability labels.
- Bernoulli assumption validation: prediction error and calibration checks against observed retry/adaptive outcomes.
- 40% threshold sensitivity analysis: treats the cutoff as an operational heuristic, not a security boundary.
- Defense methodology pipeline: practitioner workflow tied to measured hardness factors and evidence.
- Reproducibility/provenance manifests: code revision, dependency versions, dataset/prompt hashes, provider/model labels, seeds, and schema versions.
- Secret-safe reporting mode: no credential values, raw secret config, or unnecessary raw traces in docs or shareable artifacts.

**Should have (strengthens revision):**
- Adaptive memory ablations: isolate failed-answer memory, strategy memory, and task-family reminders.
- Classification stability table: stable hard, stable broken, or threshold-sensitive labels under uncertainty.
- External benchmark smoke subset: validate mapping and schema before expensive full imports.
- Literature-to-experiment reconciliation appendix: solver type, dataset, metric, threat model, and comparability.
- Structural hardness scorecard: reusable factor matrix for CAPTCHA design evaluation.
- Cost/latency volatility annotations: date-stamped assumptions for model/provider snapshots.
- Human-usability proxy checklist: readability, motor precision, visual accessibility, and completion burden as constraints.
- Result schema validator and paper-ready change log.

**Defer (v2+ or future work):**
- Live CAPTCHA attack automation.
- Full production CAPTCHA service or dynamic-template deployment system.
- Formal human-subjects usability study.
- Longitudinal model-drift benchmark.
- Fine-tuned or distilled attacker models.
- Complete package refactor or broad CI expansion unrelated to revision evidence.

### Architecture Approach

Use a strangler-style architecture: add revision wrappers and artifact generators around the existing evaluator, and keep notebooks as consumers. The current evaluator owns important contracts for task loading, provider payloads, JSON schemas, scoring, token accounting, and result writing. A broad refactor before evidence generation would risk changing the experimental surface and making old and new results incomparable.

**Major components:**
1. Existing evaluation core: `run_eval.py` primitives for task construction, provider calls, schema creation, scoring, and token/cost aggregation.
2. Adaptive attacker runner: new runner for session-memory policy, prompt mutation, attempt logging, and pass@k summaries.
3. Revision artifact helper: manifests, schema versions, result directory conventions, atomic writes, and validation.
4. Statistical confidence reporter: offline intervals, task-family aggregation, threshold sensitivity, and Bernoulli calibration.
5. Baseline/dataset comparison layer: import external results, normalize metrics, map task families, and label comparability.
6. Defense methodology generator: hardness-factor matrix, practitioner checklist, evidence map, and template-rotation example.
7. Visualization and notebook bridge: paper figure/table inputs generated from scripts, with notebooks used only for inspection.
8. Paper artifact QA layer: claim ledger, reviewer-response traceability, and final figure/table validation.

### Critical Pitfalls

1. **Adaptive attacker is stronger in name only**: define attacker state, visible feedback, memory persistence, allowed prompt changes, and stopping rules before coding; record state transitions per attempt.
2. **Bernoulli criticism is handled only in prose**: compute observed retry success, predicted retry success, calibration error, and uncertainty by task family.
3. **Statistical confidence is added after figures**: generate interval-aware tables before selecting main claims, and make captions/prose consume those outputs.
4. **SOTA baselines are compared unfairly**: separate citation-only, artifact-compatible, adapter-based, and full-reproduction comparison levels; require metric definitions and comparability labels.
5. **Larger dataset imports break ground-truth validity**: validate manifests, labels, coordinate bounds, image dimensions, conversions, excluded samples, and golden fixtures before scale.
6. **Secrets leak through imports or logs**: remove import-time side effects, avoid printing config values, keep credentials untracked, and generate shareable artifacts through redacted exports.
7. **Cost and rate limits appear after spending**: require dry-run manifests, budget caps, small smoke runs, checkpoints, and infrastructure-error categories.
8. **Code fragility corrupts conclusions**: add focused tests for task aliases, evaluator branches, result schemas, confidence calculations, and provider metadata stubs.
9. **Defense methodology stays abstract**: produce a concrete pipeline, factor matrix, checklist, and worked example tied to experiment evidence.
10. **Claims overreach**: maintain a claim ledger and use bounded language tied to evaluated models, datasets, assumptions, and confidence intervals.

## Implications for Roadmap

Based on the combined research and the later shepherding plan, the roadmap should start with evidence contracts before expensive model calls, then prioritize the adaptive attacker as the first headline empirical addition. Dataset/statistical limitations follow immediately after the adaptive evidence so the main-body claims can be bounded before baseline, defense, and final paper packaging work.

### Phase 1: Reproducibility and Safety Foundation

**Rationale:** Every later artifact depends on traceability, safe execution, and correct task/result schemas. This phase reduces the chance of reruns, secret exposure, and corrupted claims before provider calls multiply cost.

**Delivers:** `pyproject.toml`, lock file, secret-safe config template, artifact schema helper, run manifest writer, result directory conventions, CLI dry-run/preflight, task alias validation, basic scoring/schema tests, and import-side-effect cleanup where needed.

**Addresses:** Reproducibility manifests, secret-safe reporting, dataset preflight, result schema validation, cost controls.

**Avoids:** Secret leakage, provider-cost surprises, task alias drift, provider SDK drift, generated artifact churn, code fragility.

### Phase 2: Adaptive Attacker Main-Body Evidence

**Rationale:** This is the most visible shepherd-requested empirical addition and should move from appendix to main body as soon as Phase 1 safety and artifact contracts exist.

**Delivers:** Adaptive session-memory runner, attempt-level logs, structured attacker state summaries, adaptive-vs-fixed comparison tables, pass@k and attempts-to-success outputs, hard-task robustness interpretation, and main-body figure/table inputs.

**Addresses:** Adaptive attacker integration, non-i.i.d. retry behavior, hard-task robustness analysis, main-body adaptive artifact package.

**Avoids:** Superficial prompt-only adaptation, untraceable memory behavior, unsupported claims that hard tasks remain robust.

### Phase 3: Dataset Scope, Statistical Confidence, and Limitations

**Rationale:** This can run mostly offline over existing and adaptive results, and should constrain paper language before baseline and final packaging work.

**Delivers:** Confidence intervals by task and family, denominator definitions, threshold sensitivity around 40%, small-n/underpowered flags, dataset scope audit, removed/incompatible CaptchaWorld task rationale, Bernoulli prediction calibration, and paper-ready limitations summaries.

**Addresses:** Statistical confidence reporting, dataset limitations, threshold justification, Bernoulli assumption validation, and generalizability boundaries.

**Avoids:** Claim drift, arbitrary hard/broken labels, prose-only treatment of retry assumptions, operational failures mixed with scientific failures, and population-level overclaims.

### Phase 4: SOTA Solver and Larger Benchmark Strengthening

**Rationale:** SOTA solver and larger-dataset comparisons have the highest external uncertainty. This phase should start with primary artifact inspection and scoped ingestion, not full solver rewrites.

**Delivers:** Baseline comparison schema, Halligan/Oedipus and dedicated-solver coverage matrix, task-family mapping, comparability labels, external benchmark smoke subset if feasible, literature/reproduction distinction, and appendix-ready comparison table.

**Addresses:** Specialized solver baseline comparison, larger-dataset integration path, benchmark coverage matrix, literature-to-experiment reconciliation.

**Avoids:** Apples-to-oranges SOTA tables, invalid dataset conversions, unsafe external solver workflows, overclaiming beyond matched evidence.

### Phase 5: Defense Methodology and HCI Scope

**Rationale:** Defense guidance should consume final empirical evidence from adaptive, confidence, and baseline work. This phase should produce actionable methodology, not a production defense system or formal HCI claim.

**Delivers:** Hardness-factor matrix, defense methodology Markdown, practitioner checklist, template-family/rotation example, human-clarity constraints, deployment-monitoring knobs, defense evidence map, and at least one worked weak-to-hardened example where evidence supports it.

**Addresses:** Defense methodology clarification, defense evidence mapping, structural hardness scorecard, usability/HCI scoping, and deployment-overhead discussion.

**Avoids:** Restated guideline lists, unsupported usability claims, formal HCI overclaiming, production-service scope creep.

### Phase 6: Ethics, Artifact Availability, and Paper Claim Alignment

**Rationale:** The revision succeeds only if generated artifacts visibly answer shepherd asks, disclosure details are documented, artifact availability is ready, and manuscript claims stay within the evidence.

**Delivers:** Claim ledger, reviewer-request-to-artifact traceability table, ethics/disclosure record, paper artifact manifest, final figure/table inputs, confidence-aware captions, notebook cleanup or read-only notebook consumers, color-coded diff support, point-by-point change support, and shareable redacted artifact bundle.

**Addresses:** Main-body integration, paper-ready change log, visualization cleanup, ethics/disclosure requirements, and final artifact availability package.

**Avoids:** New evidence hidden in appendix only, stale notebook computations, threshold overclaims, model-snapshot overgeneralization.

### Phase Ordering Rationale

- Start with reproducibility and safety because all later runs require manifests, schema versions, task validation, budget preflight, and secret-safe logging.
- Run adaptive experiments immediately after the foundation because the shepherding plan explicitly moves session-memory evidence into the main body.
- Run dataset scope and statistical confidence after adaptive evidence so limitations and uncertainty can bound both existing and new results.
- Put SOTA solvers and larger datasets after local schemas stabilize because external comparisons require explicit mapping and comparability controls.
- Build defense methodology after empirical evidence lands so it is grounded in measured hardness factors rather than repeated prose.
- Finish with ethics, artifact availability, and claim alignment because the last risk is not missing code; it is manuscript language, disclosure detail, or artifact packaging falling out of sync with generated evidence.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3:** Adaptive attacker policy design needs a precise state/feedback model before implementation.
- **Phase 4:** Oedipus, Halligan/USENIX 2025, and any larger benchmark artifacts need primary-source and license/schema inspection before committing to reproduction.
- **Phase 5:** If the roadmap requires stronger usability claims than a proxy checklist, human-study methodology needs separate research and likely remains out of current scope.

Phases with standard patterns where research-phase can usually be skipped:
- **Phase 1:** Python packaging, lock files, Pydantic validation, pytest fixtures, and secret-safe config templates are established engineering patterns.
- **Phase 2:** Binomial confidence intervals, threshold sensitivity tables, and CSV/Markdown report generation are standard offline analysis work.
- **Phase 6:** Artifact manifests, claim ledgers, and reviewer traceability tables are straightforward documentation/QA patterns once inputs exist.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Existing repo is a Python local research framework; recommended additions directly address reproducibility, statistics, validation, and tests without platform migration. |
| Features | HIGH | Must-have features map directly to reviewer-request themes and active project requirements. External dataset/baseline features are MEDIUM feasibility until artifacts are checked. |
| Architecture | HIGH | Additive wrappers and offline generators preserve existing evaluator contracts and minimize result-comparability risk. |
| Pitfalls | HIGH | Risks are grounded in reviewer concerns and documented local codebase issues; external solver risks remain MEDIUM until source artifacts are inspected. |

**Overall confidence:** HIGH for the six-phase roadmap and internal implementation direction; MEDIUM for exact Phase 4 scope.

### Gaps to Address

- External baseline feasibility: inspect primary Oedipus and Halligan/USENIX 2025 artifacts, licenses, datasets, threat models, and metrics before choosing comparison level.
- Larger dataset compatibility: validate task labels, answer semantics, coordinate systems, image transforms, checksums, and excluded-sample accounting before claiming scale.
- Adaptive attacker semantics: define what feedback the attacker sees, whether memory is per-instance or per-family, and what prompt/action changes are allowed.
- Existing adaptive drafts: inventory current result directories and any unpublished scripts before writing a new runner.
- Human usability: keep claims qualitative unless a separate user study is explicitly added.
- Provider volatility: date-stamp model IDs, SDK versions, pricing assumptions, latency, and cost results.

## Sources

### Primary Research Inputs

- `.planning/PROJECT.md`: project scope, active requirements, constraints, decisions, and revision context.
- `.planning/research/STACK.md`: stack recommendations, dependencies, result schemas, reproducibility practices, and stack confidence.
- `.planning/research/FEATURES.md`: table-stakes features, differentiators, anti-features, deferrals, and feature dependencies.
- `.planning/research/ARCHITECTURE.md`: additive architecture, component boundaries, data flow, patterns, anti-patterns, and build order.
- `.planning/research/PITFALLS.md`: critical/moderate/minor risks, phase warnings, and mitigation strategies.

### Source Types Cited By Research Docs

- Local codebase maps under `.planning/codebase/`: current architecture, structure, concerns, testing gaps, integrations, and conventions.
- Local framework files referenced by research docs: `run_eval.py`, `run_single_experiment.py`, `experiments_helper.py`, `visualize_results.py`, and `exp2_to_exp3_predict.py`.
- Reviewer context summarized in the research docs: adaptive attacker, dataset scope, statistical significance, SOTA comparison, threshold, Bernoulli retry, defense methodology, and HCI/operations concerns.
- External technical references cited by research docs: Python Packaging User Guide, uv documentation, SciPy statistics APIs, Pydantic v2 documentation, pytest documentation, Ruff documentation, USENIX Security 2025 Halligan page, Zenodo Halligan artifact record, and arXiv Oedipus record.

---
*Research completed: 2026-05-15*
*Ready for roadmap: yes*
