# Domain Pitfalls

**Domain:** COGNITION post-acceptance CAPTCHA/MLLM security revision experiments
**Researched:** 2026-05-15
**Overall confidence:** HIGH for reviewer-driven risks and local codebase risks; MEDIUM for external baseline integration risks until artifacts are inspected in implementation phases.

## Roadmap Phase Names Used Below

The roadmap should assign these ownership buckets before implementation begins:

| Phase | Purpose |
|-------|---------|
| Phase 1: Reproducibility and Safety Foundation | Make experiment execution safe, deterministic, versioned, and secret-clean before expensive runs. |
| Phase 2: Adaptive Attacker Experiment | Implement session-memory/adaptive retry experiments and main-body-ready interpretation. |
| Phase 3: Statistical Confidence and Dataset Scope | Add uncertainty reporting, sample-size caveats, threshold justification, and dataset limitation artifacts. |
| Phase 4: Baselines and Larger Dataset Integration | Compare against SOTA solver baselines and/or larger external datasets with fair scoped methodology. |
| Phase 5: Defense Methodology Artifacts | Turn defense guidance into an actionable, reusable methodology with practitioner-facing artifacts. |
| Phase 6: Paper Artifact QA and Claim Alignment | Freeze figures/tables/appendix inputs, audit claims against outputs, and prevent overclaiming. |

## Critical Pitfalls

Mistakes that could invalidate the revision experiments, expose sensitive material, or fail to address final reviewer expectations.

### Pitfall 1: Adaptive Attacker Is Stronger in Name Only

**What goes wrong:** The "adaptive/session-memory" attacker reuses the old fixed-policy retry setup with superficial prompt changes, so reviewers still see the Bernoulli/i.i.d. criticism as unresolved.

**Why it happens:** The existing framework already supports fixed prompting, few-shot diagnostics, and until-correct retries; it is easy to bolt memory text onto the prompt without changing the attack state model, action policy, or analysis.

**Consequences:** The main reviewer request to explain robustness under a stronger attacker remains unmet. Claims that hard CAPTCHA families are structurally robust will look like artifacts of the chosen attack policy.

**Warning signs:**
- Attempts are logged independently with no per-task-type or per-instance memory state.
- The adaptive run has the same output schema as the old until-correct run with no memory fields.
- Analysis reports only aggregate Pass@k without examples of what the attacker learned and why that did or did not help.
- Borderline task gains and hard-task failures are not separated by task family.

**Prevention strategy:**
- Define an explicit attacker state model before coding: what feedback is visible, what memory persists, whether memory is per-instance or per-task-family, and what the attacker is allowed to change.
- Record per-attempt state transitions, prompt deltas, parsed answer, pass/fail, and final stopping reason in versioned JSONL or CSV.
- Compare fixed-policy, i.i.d. prediction, and adaptive empirical results side by side for the same task subsets.
- Interpret results by hardness mechanism: localization, object-location binding, counting, continuous output precision, and multi-step composition.
- Keep the implementation offline and dataset-based; do not add browser automation or live-site attack capabilities.

**Roadmap phase:** Phase 2: Adaptive Attacker Experiment.

### Pitfall 2: Bernoulli Criticism Is Treated as a Prose Limitation Instead of an Empirical Check

**What goes wrong:** The revision says the Bernoulli model is a limited approximation but does not quantify how far fixed-policy predictions diverge from observed retry or adaptive retry outcomes.

**Why it happens:** The existing Exp2-to-Exp3 analysis already implements prediction workflows, so the team may assume the current formula and validation are enough.

**Consequences:** Reviewers who questioned the i.i.d. assumption can still argue that multi-shot conclusions are formula-derived rather than validated.

**Warning signs:**
- Pass@k curves are presented without empirical confidence intervals or prediction-error summaries.
- Adaptive runs are described qualitatively but not used to bound or stress-test the Bernoulli prediction.
- Infrastructure failures, parsing failures, and true task failures are all counted as ordinary failures.
- The paper uses "expected cost" language without showing sensitivity to non-i.i.d. retry behavior.

**Prevention strategy:**
- For each relevant task family, compute observed retry success, Bernoulli-predicted retry success, calibration error, and uncertainty intervals.
- Separate fixed-policy repeated attempts from adaptive attempts in filenames, schemas, tables, and figure labels.
- Report where Bernoulli is conservative, optimistic, or unsupported; do not force a single narrative.
- Treat infrastructure/provider errors as censored or separate operational failures, not as evidence of CAPTCHA hardness.
- Make the main claim independent of Bernoulli where possible: hard tasks remain hard empirically under stronger adaptive trials.

**Roadmap phase:** Phase 3: Statistical Confidence and Dataset Scope, with inputs from Phase 2.

### Pitfall 3: Statistical Confidence Is Added After Figures, Causing Claim Drift

**What goes wrong:** Confidence intervals, sample-size notes, and threshold tests are appended after the existing figures/tables are already selected, so the uncertainty analysis does not actually constrain the claims.

**Why it happens:** Existing workflows are notebook-driven and figure-oriented; there is no enforced schema that carries denominators, intervals, seeds, and filters into every artifact.

**Consequences:** The revision may still overstate conclusions from small task-family samples, especially for the 40 percent threshold, hard-vs-broken labels, and task-family rankings.

**Warning signs:**
- Tables show point estimates but omit `n`, denominator definition, retry count, and interval method.
- The 40 percent threshold is described as a security boundary instead of an operational heuristic.
- Figure captions use categorical language such as "secure", "broken", or "robust" without interval-aware caveats.
- Filtering choices remove incompatible task types without a clear appendix note.

**Prevention strategy:**
- Make statistical outputs first-class generated artifacts: per-task and per-family pass rate, denominator, interval method, confidence level, and threshold classification.
- Use interval-aware language in artifact templates before writing the paper text.
- Run sensitivity checks around the operational threshold, especially near-boundary task families.
- Include dataset-scope caveats in the same tables or appendix artifacts used by the main text, not only in a standalone limitations paragraph.
- Require Phase 6 claim audit to compare every numeric and categorical claim against generated statistical outputs.

**Roadmap phase:** Phase 3: Statistical Confidence and Dataset Scope; audited in Phase 6.

### Pitfall 4: SOTA Baselines Are Compared Unfairly or Too Literally

**What goes wrong:** The project attempts a direct score comparison against Oedipus, Halligan, or similar specialized solvers without matching task definitions, interaction assumptions, feedback channels, model versions, datasets, or allowed tools.

**Why it happens:** Reviewers asked for SOTA comparison, but these systems are not just single MLLM API calls. They may use decomposition, search, code synthesis, interaction metamodels, or larger benchmark suites.

**Consequences:** The comparison can be rejected as apples-to-oranges, or it can accidentally weaken the paper by implying COGNITION failed to implement a full external system when the revision only needed a defensible baseline methodology.

**Warning signs:**
- A baseline row says "Oedipus" or "Halligan" but actually runs only a generic MLLM prompt.
- The comparison table omits whether each solver has live interaction, multiple tool calls, coordinate actions, or CAPTCHA-specific DSL/metamodel support.
- External dataset examples are converted manually without preserving provenance or answer semantics.
- The revision claims "outperforms SOTA" when only scope/context differs.

**Prevention strategy:**
- Define baseline levels: citation/contextual comparison, artifact-compatible reproduction, adapter-based offline evaluation, and full system reproduction. Pick the strongest feasible level explicitly.
- If full reproduction is infeasible, document why and provide a fair capability matrix instead of pretending equivalence.
- Normalize by threat model: black-box API-only MLLM, agentic VLM solver, specialized CAPTCHA reasoning framework, and dataset-specific solver.
- Preserve dataset provenance, license, checksums, task mapping, and excluded-category rationale.
- Use comparison language such as "complements", "covers different threat model", or "stress-tests against agentic baseline" unless direct matched experiments justify stronger wording.

**Roadmap phase:** Phase 4: Baselines and Larger Dataset Integration.

### Pitfall 5: Larger Dataset Integration Sacrifices Ground-Truth Validity

**What goes wrong:** Larger external benchmark data is imported quickly to satisfy scale concerns, but task labels, answer formats, interaction semantics, or image transformations are wrong.

**Why it happens:** The existing code encodes task behavior across loaders, prompts, schemas, scoring, visualization labels, and few-shot manifests. External benchmarks may use different task taxonomies, coordinate systems, UI states, or multi-step interactions.

**Consequences:** More samples produce less credible results. Wrong conversions can either inflate solver success or falsely classify hard tasks as robust.

**Warning signs:**
- Imported tasks reuse an existing evaluator branch without a task-specific validation fixture.
- Coordinate/image resizing is performed without a round-trip check.
- Excluded samples are silently skipped.
- Summary counts do not match source manifest counts.
- Manual spot checks find answer-format ambiguity.

**Prevention strategy:**
- Add a dataset validation command before large imports: manifest count, file existence, label schema, coordinate bounds, image dimensions, task alias mapping, and expected evaluator.
- Create small golden fixtures for every imported task type and run them in automated tests.
- Store source dataset citation, artifact URL, checksum, license notes, conversion script version, and excluded-sample reasons.
- Keep larger-dataset claims scoped to the subset that is faithfully represented in the offline COGNITION framework.
- Prefer fewer validated external task families over a broad but lossy import.

**Roadmap phase:** Phase 4: Baselines and Larger Dataset Integration, with foundation work in Phase 1.

### Pitfall 6: Secrets Leak Through Existing Import Side Effects and Result Logs

**What goes wrong:** API keys, provider config, raw prompts, model responses, reasoning traces, or ground truth leak into terminal logs, notebooks, committed artifacts, or paper-support bundles.

**Why it happens:** The current codebase has tracked secret configuration, import-time config printing, bottom-of-file provider snippets, and raw error-analysis artifacts. New revision runs will increase the amount of sensitive output.

**Consequences:** Credential exposure, unsafe artifact release, reviewer distrust, and possible violation of provider or institutional expectations.

**Warning signs:**
- Importing experiment modules prints provider config or runs live smoke calls.
- Result directories contain raw prompts/responses/reasoning by default.
- `secrets.yaml` or provider-specific config appears in `git status`.
- Error-analysis CSVs are copied into paper artifact folders without redaction.
- Paper artifact generation requires reading secret-bearing local files.

**Prevention strategy:**
- Remove import-time side effects before running new experiments.
- Move credentials to environment variables or an untracked local config; provide only a redacted example file.
- Add secret patterns to `.gitignore` and run secret scans before any artifact packaging.
- Make raw error-analysis output opt-in and mark it non-shareable by default.
- Generate shareable summaries through a redaction/export step that never reads or writes secret values.

**Roadmap phase:** Phase 1: Reproducibility and Safety Foundation.

### Pitfall 7: Provider Cost and Rate Limits Are Discovered Only After Spending

**What goes wrong:** Adaptive runs, larger datasets, and SOTA baseline attempts multiply provider calls and token usage, exceeding budget or producing incomplete runs due to rate limits.

**Why it happens:** Current cost control is mostly post-run accounting. Provider calls are sequential, retry/backoff is weak, and pricing data is local configuration rather than a preflight budget gate.

**Consequences:** Expensive partial outputs, inconsistent coverage across models, pressure to cherry-pick available results, and delayed revision work.

**Warning signs:**
- A full run starts without a manifest showing task count, max attempts, models, expected images per request, and estimated cost range.
- Token/cost summaries appear only after responses are collected.
- Provider exceptions are counted as task failures.
- Runs use newest/largest models by default for all smoke tests.
- Dataset expansion happens before budget caps are implemented.

**Prevention strategy:**
- Add dry-run manifests for every expensive experiment: task counts, provider/model, attempts, prompt mode, expected token/image volume, max cost, and stop conditions.
- Require small smoke runs before full runs, including one known easy and one known hard task family.
- Enforce budget caps and resumable checkpoints at the runner level.
- Separate provider/rate-limit failures from CAPTCHA failures in output schemas.
- Use deterministic sharding so partial runs can resume without duplicating paid calls.

**Roadmap phase:** Phase 1: Reproducibility and Safety Foundation; enforced in Phases 2 and 4.

### Pitfall 8: Code Fragility Corrupts Experimental Conclusions

**What goes wrong:** Known evaluator bugs, task alias drift, summary CSV bugs, broad exception swallowing, or untested provider adapters silently change pass rates and figure inputs.

**Why it happens:** `run_eval.py` is monolithic and has no automated test suite. Task behavior is duplicated across code, YAML, datasets, notebooks, and visualization.

**Consequences:** The paper may report incorrect task-family performance, omit rows, or misclassify hard/easy tasks. Fixing this late can force reruns and invalidate already drafted claims.

**Warning signs:**
- A task type has multiple spellings across dataset directories, prompts, few-shot assets, and code.
- Summary row counts differ from task counts.
- A failed parser or malformed ground truth becomes `False`, `None`, or a warning rather than a hard error.
- Visualization code accepts loose CSV schemas without validation.
- A provider SDK update changes metadata parsing without tests failing.

**Prevention strategy:**
- Add focused automated tests before experiment changes: task registry/aliases, evaluator branches, CLI smoke behavior, provider contract stubs, and result schema validation.
- Introduce a task registry that owns canonical names, aliases, loader, schema, evaluator, prompt key, and display family.
- Fail fast on dataset/schema errors; reserve soft failures for provider infrastructure issues with explicit categories.
- Validate every generated CSV/JSON before it can be consumed by visualization or paper tables.
- Keep compatibility wrappers for notebooks while moving reusable logic into importable modules.

**Roadmap phase:** Phase 1: Reproducibility and Safety Foundation.

### Pitfall 9: Defense Methodology Remains a Restated Guideline List

**What goes wrong:** The defense revision repeats Section 5.3 observations and high-level design advice instead of producing a reusable practitioner methodology.

**Why it happens:** The project is experiment-heavy; defense work can be treated as prose rather than an artifact with inputs, steps, decision criteria, and outputs.

**Consequences:** Reviewers may still see the defense contribution as ad hoc. The paper misses the chance to convert empirical hardness factors into practical value.

**Warning signs:**
- Defense section contains verbs like "use", "avoid", and "combine" but no workflow, checklist, or decision tree.
- Select_Animal hardening is the only concrete example.
- No artifact shows how to assess a new CAPTCHA design against the methodology.
- The methodology ignores operational overhead, rotation cost, accessibility, and user friction.

**Prevention strategy:**
- Define a concrete defense pipeline: task inventory, hardness-factor scoring, recognition-only rejection, structural hardening selection, human-usability sanity check, rotation configuration, and evaluation gate.
- Produce a table/checklist artifact practitioners can apply to a new CAPTCHA family.
- Include at least one worked example from weak baseline to hardened design, with attacker-side evidence.
- State limits clearly: no formal HCI study in this milestone unless added explicitly; usability claims should be framed as design constraints or future validation needs.
- Address operational deployment concerns through config-driven template families and monitoring recommendations, not a production service implementation.

**Roadmap phase:** Phase 5: Defense Methodology Artifacts.

### Pitfall 10: Claims Overreach Beyond the Revision Evidence

**What goes wrong:** The revised paper says hard CAPTCHAs are secure, future-proof, fundamentally robust, or broadly representative when the experiments support a narrower claim.

**Why it happens:** Reviewers asked for stronger empirical grounding, and it is tempting to convert stronger artifacts into stronger language rather than more precise language.

**Consequences:** The final revision can trigger renewed objections about rapid MLLM progress, limited datasets, user studies, economic volatility, or attacker sophistication.

**Warning signs:**
- The manuscript uses "fundamental" without linking to a measured structural failure mode.
- Cost comparisons use current API pricing as if it is stable.
- Dataset language implies comprehensive coverage of the CAPTCHA ecosystem.
- Human usability is asserted without user-study data.
- Specialized solvers are dismissed because they are outside the black-box API threat model.

**Prevention strategy:**
- Maintain a claim ledger mapping every main-body claim to generated evidence, source artifact, confidence level, and limitation.
- Use bounded language: "under the evaluated black-box/API and adaptive-session settings", "representative benchmark", "current model snapshot", and "structural failure modes observed across tested models".
- Separate empirical findings, interpretation, and future-work speculation.
- For cost and latency, state the date/model/provider assumptions and include volatility caveats.
- Use Phase 6 to remove or soften any claim without a direct artifact link.

**Roadmap phase:** Phase 6: Paper Artifact QA and Claim Alignment.

## Moderate Pitfalls

### Pitfall 11: Reviewer Expectation Mismatch on "Main Body" Integration

**What goes wrong:** Adaptive results, dataset limitations, SOTA discussion, and defense methodology are added to appendix material, footnotes, or scattered paragraphs rather than being made visible in the main paper.

**Warning signs:**
- The main body still centers old figures while new revision evidence appears only in appendix tables.
- The introduction/contributions do not mention the strengthened adaptive or defense methodology work.
- Captions do not explain why hard tasks remain robust under the stronger attacker.

**Prevention strategy:**
- Reserve main-body figure/table slots early for adaptive attacker results and defense methodology.
- Treat appendix material as support for main claims, not the primary location for required revisions.
- Write a reviewer-response traceability table: final request -> paper location -> artifact path.

**Roadmap phase:** Phase 6: Paper Artifact QA and Claim Alignment.

### Pitfall 12: External Baseline Artifacts Create Safety or Ethics Drift

**What goes wrong:** Importing or running external CAPTCHA solver artifacts introduces live-site automation, MITM workflows, browser driving, or instructions that conflict with the project's offline, authorized-dataset scope.

**Warning signs:**
- A baseline requires real CAPTCHA provider endpoints or live browser sessions.
- Scripts include credentialed CAPTCHA-farm, proxy, or account automation flows.
- The comparison needs interaction traces that are not available in the local offline datasets.

**Prevention strategy:**
- Review external artifacts in a read-only, offline mode first.
- Integrate only dataset-compatible, offline components, or cite the external results with a capability matrix.
- Add a baseline safety checklist: no live service attack, no credentialed farm use, no turnkey browser automation, no release of operational abuse scripts.

**Roadmap phase:** Phase 4: Baselines and Larger Dataset Integration.

### Pitfall 13: Reproducibility Metadata Is Missing From New Artifacts

**What goes wrong:** New CSVs, figures, and JSON summaries cannot be traced back to code version, dataset version, prompt file, provider SDK versions, model IDs, run parameters, or random seeds.

**Warning signs:**
- Output directories are named only by experiment/provider/model.
- Figures are regenerated from notebooks with hidden cell state.
- Prompt or dataset edits happen after results are generated with no manifest diff.

**Prevention strategy:**
- Write a run manifest before every experiment and copy it next to every result directory.
- Include code commit, dirty-worktree flag, dataset checksums, prompt hash, dependency versions, provider/model identifiers, runner command, and timestamp.
- Move notebook logic into scripts that consume manifests and result schemas.

**Roadmap phase:** Phase 1: Reproducibility and Safety Foundation.

### Pitfall 14: Threshold and Taxonomy Choices Look Arbitrary

**What goes wrong:** The 40 percent cutoff, hard/broken taxonomy, and task-family grouping are preserved but not defended with sensitivity analysis or uncertainty-aware rationale.

**Warning signs:**
- Near-threshold families flip classification under confidence intervals.
- The paper calls the threshold a "security" threshold rather than an analysis heuristic.
- Figures hide uncertainty around grouped task-family labels.

**Prevention strategy:**
- Report threshold sensitivity and avoid overinterpreting near-boundary families.
- Tie task-family groupings to measured failure modes and evaluator semantics.
- Use the threshold as a descriptive operational cutoff, not a universal security boundary.

**Roadmap phase:** Phase 3: Statistical Confidence and Dataset Scope.

### Pitfall 15: Model Snapshot Becomes Obsolete Before the Revision Lands

**What goes wrong:** The paper leans on specific model rankings or API costs that change quickly, weakening long-term value.

**Warning signs:**
- Main conclusions depend on one model version being weak.
- Cost tables lack dates or provider assumptions.
- The discussion does not distinguish structural failure modes from current model capability gaps.

**Prevention strategy:**
- Center conclusions on task properties and failure modes that recur across evaluated models.
- Date-stamp model IDs, provider settings, pricing assumptions, and latency measurements.
- Add a limitations note that newer models may change point estimates while the methodology remains reusable.

**Roadmap phase:** Phase 6: Paper Artifact QA and Claim Alignment.

### Pitfall 16: Few-Shot and Prompt Diagnostics Are Misread as Attack Strength

**What goes wrong:** Few-shot prompting results are presented as a realistic adaptive attack or as proof of structural hardness without distinguishing diagnostic purpose from attacker capability.

**Warning signs:**
- Few-shot and adaptive/session-memory are grouped in the same table without method distinctions.
- The paper says few-shot "failed" without explaining what that diagnoses.
- Prompt examples can drift from current assets or answers.

**Prevention strategy:**
- Label few-shot runs as diagnostics for instruction sensitivity unless the threat model explicitly allows them as attacker knowledge.
- Use a single generated few-shot manifest validated against assets and ground truth.
- Compare few-shot, fixed retry, and adaptive memory as separate attack dimensions.

**Roadmap phase:** Phase 2: Adaptive Attacker Experiment; manifest validation in Phase 1.

## Minor Pitfalls

### Pitfall 17: Artifact Directory Churn Obscures Canonical Results

**What goes wrong:** Temporary CSVs, backup files, figures, and rerun outputs remain mixed with source and curated results.

**Warning signs:**
- Multiple files appear to be the same result with names like `tmp`, `backup`, or timestamp-only variants.
- Figure scripts auto-discover result trees and pick up stale runs.

**Prevention strategy:**
- Define canonical artifact directories per phase and require manifests.
- Exclude scratch outputs from git and from figure discovery.
- Use explicit input manifests for paper figure generation.

**Roadmap phase:** Phase 1: Reproducibility and Safety Foundation; final cleanup in Phase 6.

### Pitfall 18: Accessibility and HCI Limits Are Ignored in Defense Claims

**What goes wrong:** The defense methodology implies human usability without measuring completion time, error rate, accessibility, or frustration.

**Warning signs:**
- Hardened designs increase precision or interaction burden but the text calls them user-friendly.
- Accessibility is mentioned only in future work or not at all.

**Prevention strategy:**
- Frame usability as a constraint and limitation unless formal user data is collected.
- Include a practitioner checklist item for accessibility and human effort.
- Avoid claiming empirical HCI validation in this revision.

**Roadmap phase:** Phase 5: Defense Methodology Artifacts; claim audit in Phase 6.

### Pitfall 19: Provider SDK Drift Breaks Token, Cost, or Parsing Metadata

**What goes wrong:** Unpinned dependencies or provider API changes alter response shape, token metadata, model availability, or JSON parsing behavior.

**Warning signs:**
- Token summaries disappear for one provider after a package update.
- Model aliases differ between README, CLI defaults, and provider allowlists.
- JSON extraction errors increase after SDK changes.

**Prevention strategy:**
- Pin dependencies and record versions in run manifests.
- Add provider contract tests with mocked responses for metadata extraction and error classification.
- Align CLI defaults with supported model IDs before smoke runs.

**Roadmap phase:** Phase 1: Reproducibility and Safety Foundation.

### Pitfall 20: Paper Tables Mix Operational and Scientific Failures

**What goes wrong:** Rate limits, timeouts, malformed responses, parsing bugs, and missing files are treated as model failures in pass-rate statistics.

**Warning signs:**
- A result row has raw value `__ERROR__` but still contributes to CAPTCHA hardness.
- Error categories are not shown in appendix tables.
- Rerunning the same subset changes pass rates due to transient provider failures.

**Prevention strategy:**
- Add explicit outcome categories: correct, incorrect, parse_failure, provider_failure, dataset_error, skipped.
- Exclude or separately report operational failures according to a predeclared rule.
- Include failure-category counts in appendix artifacts.

**Roadmap phase:** Phase 3: Statistical Confidence and Dataset Scope, supported by Phase 1 schema work.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|----------------|------------|
| Reproducibility and safety | Existing import side effects leak secrets or trigger live calls during tests. | Remove side effects, add secret-safe config template, scan outputs before artifact packaging. |
| Adaptive attacker | Memory attacker does not materially differ from fixed retries. | Define attacker state, feedback, memory persistence, and allowed prompt/action changes before implementation. |
| Statistical confidence | Intervals are added but do not constrain claims. | Generate interval-aware tables first and make paper language consume those outputs. |
| Dataset scope | Larger dataset import increases sample count while lowering label validity. | Validate conversion with manifests, checksums, golden fixtures, and excluded-sample accounting. |
| SOTA baselines | Specialized solvers are reduced to generic prompt baselines. | Use capability matrix and matched experiments only where artifacts and assumptions align. |
| Defense methodology | Guidance remains abstract and repetitive. | Produce a workflow/checklist plus a worked example tied to empirical hardness factors. |
| Paper artifact QA | Main-body revisions do not visibly answer final reviewer asks. | Maintain request-to-artifact traceability and audit every claim against outputs. |

## Sources And Confidence

| Source | Confidence | Notes |
|--------|------------|-------|
| `.planning/PROJECT.md` | HIGH | Defines revision scope, active requirements, constraints, and key decisions. |
| `.planning/codebase/CONCERNS.md` | HIGH | Documents local bugs, security concerns, fragility, scaling limits, and missing critical features. |
| `.planning/codebase/TESTING.md` | HIGH | Confirms lack of automated tests and notebook/manual validation pattern. |
| `.planning/codebase/INTEGRATIONS.md` | HIGH | Confirms provider integrations, local file storage, credential location, and lack of CI/monitoring. |
| `/Users/ukun/Desktop/USENIX Sec.txt` | HIGH | Contains reviewer concerns and author-response commitments driving this revision. Secret values were not read or quoted. |
| USENIX Security 2025 Halligan page | HIGH | Primary source confirming Halligan as a generalized visual CAPTCHA solver and benchmark context: https://www.usenix.org/conference/usenixsecurity25/presentation/teoh |
| Zenodo Halligan artifact record | HIGH | Primary artifact source confirming downloadable offline benchmark and implementation artifacts: https://zenodo.org/records/15709075 |
| arXiv Oedipus record | MEDIUM | Primary preprint source for Oedipus method and reported success; final ACM page should be checked during baseline implementation: https://arxiv.org/abs/2405.07496 |

## What Might Be Missed

- Final ACM artifact details for Oedipus could change the feasible comparison level; Phase 4 should inspect the final DOI/artifact package before committing to reproduction.
- The current repo may contain additional unpublished adaptive-attacker scripts or draft results not covered by the codebase maps; Phase 2 should inventory existing result directories before writing new runners.
- Human-usability evidence is outside the current implementation scope. The revision should not imply a formal user study unless such data is explicitly added.
- Provider pricing and model availability are volatile. Any cost/latency claim should be date-stamped and treated as a snapshot.
