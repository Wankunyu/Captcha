# Phase 3: Dataset Scope, Statistical Confidence, and Limitations - Context

**Gathered:** 2026-05-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 produces scripted dataset-scope, statistical-confidence, threshold-sensitivity, retry-calibration, infrastructure-error, and limitations artifacts for the paper revision. It must make the CaptchaWorld scope, sample-size limits, removed/incompatible task types, confidence reporting, operational cutoff sensitivity, retry-model validity, and extended-dataset validation strategy explicit.

This phase may define and run a selective extended-dataset validation slice when it directly supports dataset generalizability and limitations claims. It should not become the full Phase 4 SOTA/larger-benchmark integration effort, should not require wholesale reruns of all historical experiments, and must remain offline and dataset-based.

</domain>

<decisions>
## Implementation Decisions

### Extended Dataset Strategy

- **D-01:** Use a selective extended-dataset strategy rather than a wholesale replacement of the original dataset.
- **D-02:** Combine two expansion routes: add samples to some existing task categories where sample size is underpowered, and add new CAPTCHA task categories to test whether conclusions extend beyond the original type set.
- **D-03:** New categories do not have to match the original CaptchaWorld taxonomy exactly. If no exact category match is available, the artifact may describe them as new CAPTCHA types using clear task-language labels.
- **D-04:** Prefer adding at least two new categories if feasible. A single new category is acceptable only if availability or timeline makes two categories impractical, and that limitation must be stated.
- **D-05:** Choose expansion targets pragmatically: prioritize categories that are feasible to collect, label, normalize, and evaluate without derailing the revision timeline.

### Experiment Rerun Scope

- **D-06:** Do not merge old and new data and rerun every experiment end-to-end by default.
- **D-07:** Run experiments on the newly added data as a selective validation slice, then compare the new-data outcomes against the original-data conclusions.
- **D-08:** The central question for the extended dataset is: do the conclusions drawn from the original dataset still hold on the new dataset slice?
- **D-09:** Selectively supplementing existing categories should be used to reduce sample-size caveats; adding new categories should be used to test broader pattern generalization.

### Adaptive Attacker on Extended Dataset

- **D-10:** Adaptive attacker evaluation may be run on the extended dataset.
- **D-11:** Adaptive-on-extended should be scoped as a validation slice, not a requirement to reproduce every historical experiment across every old and new task.
- **D-12:** If adaptive-on-extended is run, it must preserve the Phase 2 threat model: offline dataset instances, binary pass/fail feedback only, explicit local policy-memory notes, no ground-truth labels or corrective hints, and append-only adaptive attempt records.
- **D-13:** If time forces prioritization, adaptive-on-extended should focus on the most claim-relevant new or supplemented categories rather than broad coverage.

### Statistical and Claim Framing

- **D-14:** The extended dataset should strengthen credibility and generalizability language, not erase CaptchaWorld limitations or imply population-level deployment estimates.
- **D-15:** Extended-data comparisons should be framed as selective validation of recurring structural patterns, with sample counts, task-category definitions, and compatibility caveats visible in the artifact.
- **D-16:** The paper should distinguish original-dataset evidence, supplemented-category evidence, and new-category evidence rather than collapsing them into one undifferentiated dataset claim.

### Threshold Sensitivity Labels

- **D-17:** Phase 3 must produce threshold-sensitivity labels as a first-class artifact, not only prose.
- **D-18:** Carry forward Phase 2's `40%` operational cutoff and `+/- 5%` borderline margin by default unless planning finds a strong statistical reason to adjust them.
- **D-19:** Threshold outputs must report each task or family label as hard, borderline, or broken; its margin relative to the operational cutoff; and whether the conclusion is threshold-sensitive.
- **D-20:** The artifact and paper-ready prose must explicitly state that the cutoff is an operational reporting heuristic, not a universal CAPTCHA security boundary.
- **D-21:** Threshold-sensitive families should be flagged for cautious wording in the paper, especially when confidence intervals overlap the cutoff or when sample counts are underpowered.

### Retry Calibration and Failure Taxonomy

- **D-22:** Phase 3 must produce retry-calibration artifacts that align Bernoulli `Success@k` predictions with observed retry outcomes and adaptive-compatible outcomes where available.
- **D-23:** Prediction-error outputs should be task-type primary, with optional family-level summaries for interpretation. At minimum, include predicted `Success@k`, observed success, absolute error, signed error, sample count, attempt budget `k`, provider, model, and task type.
- **D-24:** Adaptive-compatible calibration should preserve Phase 2's comparison contract: task type is the primary unit, adaptive runs use the same attempt budget when compared, and structural bottleneck tags remain explanatory rather than the primary evaluation unit.
- **D-25:** Paper-ready summaries must separate scientific model failures from protocol failures and infrastructure failures. Infrastructure or provider/runtime errors must not be counted as evidence of structural CAPTCHA robustness.
- **D-26:** Failure-taxonomy summaries should expose counts and rates for `scientific_wrong`, `protocol_failure`, and `infrastructure_failure`, and should state how each class affects inclusion in pass-rate, retry-calibration, threshold, and limitation claims.

### the agent's Discretion

- The planner may choose exact artifact filenames and CLI flag names for the dataset audit, extended-data manifest, comparison table, and limitations prose generator.
- The planner may choose the exact confidence-interval method, provided the method is documented and appropriate for small sample counts.
- The planner may choose the exact minimum sample-count threshold for "underpowered" task families, provided the threshold is explicit and surfaced in outputs.
- The planner may choose which existing Phase 2 adaptive comparison utilities to reuse or extend, provided Phase 2 schemas and threat-model semantics remain intact.
- The planner may refine the exact threshold-sensitive flag logic, provided it preserves margin-to-cutoff reporting and does not turn the cutoff into a universal security claim.
- The planner may choose the exact retry-calibration table layout, provided the required prediction-error and failure-taxonomy fields are present.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and Phase Scope

- `.planning/PROJECT.md` - Project goals, paper-revision constraints, ethics boundaries, and the active dataset/statistical requirement.
- `.planning/REQUIREMENTS.md` - Phase 3 requirements `STAT-01` through `STAT-07`.
- `.planning/ROADMAP.md` - Phase 3 goal, success criteria, dependency on Phase 2, and reviewer alignment.
- `.planning/STATE.md` - Current project state and Phase 3 focus.

### Prior Phase Contracts

- `.planning/phases/01-reproducibility-and-safety-foundation/01-CONTEXT.md` - Locked decisions on revision artifact layout, manifests, attempt logs, preflight, validators, and secret-safe reporting.
- `.planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md` - Locked adaptive attacker threat model, comparison unit, failure taxonomy, operational cutoff framing, and adaptive output contracts.
- `.planning/phases/02-adaptive-attacker-main-body-evidence/02-VERIFICATION.md` - Verified Phase 2 adaptive workflow and residual constraints.

### Codebase Maps

- `.planning/codebase/ARCHITECTURE.md` - Existing evaluation, result, visualization, and statistical-analysis architecture.
- `.planning/codebase/STRUCTURE.md` - File layout and recommended locations for statistical utilities and revision artifacts.
- `.planning/codebase/CONVENTIONS.md` - Python style, CLI conventions, import-safety guidance, and artifact-writing patterns.
- `.planning/codebase/CONCERNS.md` - Dataset/schema drift, generated artifact, provider failure, and statistical overclaiming risks.
- `.planning/codebase/TESTING.md` - Current automated test patterns and testable seams.

### Implementation Surfaces

- `run_eval.py` - Supported task types, task aliases, task loading, scoring, and provider-boundary behavior.
- `revision_preflight.py` - Existing dataset/task validation and cost-visible preflight patterns.
- `revision_artifacts.py` - Phase 1 manifest, attempt, summary, hashing, and revision output helpers.
- `adaptive_artifacts.py` - Adaptive attempt, summary, comparison schemas, and failure-class fields.
- `adaptive_compare.py` - Phase 2 comparison table builder, operational cutoff labels, structural bottleneck tags, and current CI deferral fields.
- `exp2_to_exp3_predict.py` - Bernoulli Success@k and expected-attempt prediction formulas.
- `visualize_results.py` - Legacy result loader, task-family metadata, and existing 40% threshold chart conventions.
- `tests/` - Existing offline validator and regression-test patterns.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `run_eval.SUPPORTED_TYPES`, `TASK_ALIASES`, and `DATASET_DIR_ALIASES` already encode active task types and the `Connect_icon` / `Connect_Icon` alias boundary.
- `captcha_data/` contains active task directories plus `Hold_Button(Not Used)` and `Slide_Puzzle(Not Used)`, which are the current visible candidates for incompatible or removed task-type documentation.
- `revision_preflight.py` already validates dataset paths, task aliases, prompt/few-shot hashes, run ids, output paths, and expected request counts.
- `adaptive_compare.py` already provides hard / borderline / broken labels around the 40% operational cutoff and separates infrastructure/protocol/scientific failure counts in comparison rows.
- `adaptive_artifacts.py` already stores adaptive confidence interval fields as nullable with a Phase 3 deferral reason.
- `exp2_to_exp3_predict.py` already implements the Bernoulli retry prediction baseline needed for calibration diagnostics.
- `visualize_results.CAPTCHAVisualizer.TASK_FAMILY` already groups current task types into coarse families that Phase 3 can audit and refine.

### Established Patterns

- Keep new revision-critical outputs under `results/revision/<run_id>/` rather than legacy `results/exp1` through `results/exp4` directories.
- Use flat root-level Python scripts with `argparse` for standalone analysis utilities.
- Keep provider calls explicit, preflighted, and budget-visible.
- Use offline fake-provider tests where possible; live paid runs must be optional and gated.
- Do not print or copy local secret values into generated reports.

### Integration Points

- Dataset scope audit should inspect `captcha_data/<TaskType>/ground_truth.json`, `SUPPORTED_TYPES`, task aliases, prompt keys, few-shot keys, and not-used task directories.
- Extended dataset validation should use a manifest that records source, category mapping, sample counts, normalization decisions, prompt/few-shot hashes, and whether each row supplements an existing category or defines a new category.
- Adaptive-on-extended should reuse Phase 2 adaptive runner and comparison schemas where possible, adding only the dataset-slice metadata needed to distinguish original, supplemented, and new-category evidence.
- Threshold-sensitivity outputs should extend or complement `adaptive_compare.py` so Phase 2 classification labels remain consistent with Phase 3's statistical caveats.
- Retry-calibration outputs should reuse `exp2_to_exp3_predict.py` formulas where possible and add observed-vs-predicted diagnostics rather than duplicating model logic.
- Failure-taxonomy outputs should consume existing Phase 2 adaptive fields and any legacy provider-error indicators in a way that keeps scientific, protocol, and infrastructure failures visibly separate.
- Statistical summaries should feed paper-ready CSV/JSON tables and limitations prose rather than notebook-only state.

</code_context>

<specifics>
## Specific Ideas

- From the advisor discussion: adaptive attacker does not have to run on the extended dataset by default, but the user now wants it to be allowed and planned as a feasible validation slice.
- From the advisor discussion: do not exhaustively rerun everything after dataset expansion. Run new data and compare against old conclusions.
- From the advisor discussion: choose data additions pragmatically; supplement the categories that are easiest and most useful, and add at least two new categories if feasible.
- From the advisor discussion: if exact category matches cannot be found, describe the additions as new CAPTCHA types in clear prose.
- The comparison should answer whether old conclusions remain valid on new data, not pretend the extended dataset fully solves representativeness limitations.
- The user explicitly promoted threshold sensitivity labels and retry calibration/failure taxonomy from discussion gray areas into Phase 3 completion requirements.

</specifics>

<deferred>
## Deferred Ideas

- Full SOTA/larger-benchmark integration with Halligan, Oedipus, specialized solvers, or larger external benchmark adapters belongs to Phase 4.
- Full reruns of every historical experiment across a merged old-plus-new dataset are not required for Phase 3 unless planning identifies a narrow, claim-critical reason.
- Formal human-subjects usability validation remains out of scope for this milestone.

</deferred>

---

*Phase: 03-dataset-scope-statistical-confidence-and-limitations*
*Context gathered: 2026-05-19*
