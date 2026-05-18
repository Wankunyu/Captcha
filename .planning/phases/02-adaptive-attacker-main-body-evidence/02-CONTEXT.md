# Phase 2: Adaptive Attacker Main-Body Evidence - Context

**Gathered:** 2026-05-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 delivers an offline, dataset-based session-memory adaptive attacker experiment and the paper-ready evidence needed to move adaptive-attacker results into the main body. The phase must let researchers compare fixed retry, Bernoulli Success@k predictions, and adaptive session-memory outcomes under the same per-task-type budget.

This phase should implement explicit adaptive attacker semantics, adaptive preflight, attempt/state logging, comparison outputs, and validation. It should not build live CAPTCHA automation, browser automation against real services, a production CAPTCHA platform, a broad evaluator rewrite, or a provider-hidden memory workflow.

</domain>

<decisions>
## Implementation Decisions

### Adaptive Feedback and Memory Semantics

- **D-01:** The adaptive attacker receives binary pass/fail feedback only after each attempt. It must not receive ground-truth labels, correct coordinates, counts, categories, instance-level corrective hints, or partial answer feedback.
- **D-02:** Persistent attacker memory is experiment-controlled state, not provider-native memory. It must be explicitly stored and replayed by the local code so it is auditable and reproducible.
- **D-03:** Persistent memory stores structured policy notes only: failed-attempt counts, tried strategy summaries, and next prompt rules. It must not persist full prompt/response transcripts, ground truth, instance answers, coordinates, counts, or local corrections.
- **D-04:** Prompt adaptation uses constrained model self-reflection. After a failed attempt, the model may see only the current prompt, its own current raw/parsed answer, and binary fail feedback, then emit a short structured policy note. Long-term memory persists only that note.

### Budget and Comparison Contract

- **D-05:** The main comparison unit is the CAPTCHA task type, matching the paper's existing evaluation unit. Structural families or bottleneck groups are explanatory groupings only, not the primary evaluation contract.
- **D-06:** Each task type gets the same attempt budget `k` for fixed retry, Bernoulli Success@k, and adaptive outcomes.
- **D-07:** Adaptive sampling uses fresh instances without replacement within each task type where possible, until the task pool is exhausted.
- **D-08:** Each task type stops on first success or when the maximum attempt budget is exhausted.
- **D-09:** Scientific wrong answers, protocol failures, and infrastructure failures must be separated. Provider/runtime failures must not be treated as structural CAPTCHA robustness evidence in main paper conclusions.

### Main-Body Evidence Outputs

- **D-10:** The primary Phase 2 output is a task-type comparison table input. Each task-type row should include Exp2 pass@1, Bernoulli Success@k, fixed retry observed outcome, adaptive observed outcome, attempts-to-success, cumulative latency, cost metadata where available, and classification change.
- **D-11:** Persistent failures are organized task-type first, with structural bottleneck tags such as spatial precision, ordering, counting, object-location binding, template diversity, and instruction sensitivity.
- **D-12:** Classification outputs use hard / borderline / broken labels with an explicit cutoff note. The 40% threshold is an operational cutoff, not a universal security boundary.

### Implementation Shape

- **D-13:** Implement the adaptive loop in a new focused module/script rather than expanding the monolithic evaluator. The planner may choose the exact file name.
- **D-14:** Reuse existing code where safe: `run_eval.build_tasks()`, `run_eval.make_provider()`, `run_eval.evaluate_pass1()`, and Phase 1 revision artifact helpers.
- **D-15:** Preserve Phase 1 artifact schema contracts. Add adaptive-specific schemas or compatibility layers instead of mutating existing `AttemptRecord` v1 semantics.
- **D-16:** Add adaptive preflight support that reports task types, attempt budget `k`, expected request count, run id, prompt/few-shot hashes, cost preview, output paths, sampling mode, feedback mode, memory mode, and stopping rule before paid calls.
- **D-17:** Validation should rely primarily on offline fake-provider tests covering memory updates, without-replacement sampling, stopping rules, attempt logs, adaptive summaries, and comparison outputs.
- **D-18:** A tiny paid provider smoke may be included only as an optional final real-provider path check. It must be gated by preflight and must not replace offline validation.

### the agent's Discretion

- The planner may choose exact module names, CLI flags, schema class names, and output filenames if they preserve the contracts above.
- The planner may choose whether adaptive-specific records extend `revision_artifacts.py` directly or live in a new adaptive artifact module, as long as Phase 1 v1 schemas remain backward-compatible.
- The planner may choose the exact hard / borderline / broken cutoff implementation and classification-change columns, provided the 40% operational-cutoff caveat is explicit.
- The planner may choose a small paid smoke shape, but it must be optional, budget-visible, and safe for secret handling.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and Phase Scope

- `.planning/PROJECT.md` - Project goals, paper-revision constraints, ethics boundaries, and active adaptive-attacker requirement.
- `.planning/REQUIREMENTS.md` - Phase 2 requirements `ADAPT-01` through `ADAPT-06`.
- `.planning/ROADMAP.md` - Phase 2 goal, success criteria, dependency on Phase 1, and reviewer alignment.
- `.planning/STATE.md` - Current project state and Phase 2 focus.

### Prior Phase Contracts

- `.planning/phases/01-reproducibility-and-safety-foundation/01-CONTEXT.md` - Locked Phase 1 decisions on `results/revision/<run_id>/`, manifests, attempts, secret safety, preflight, and validators.
- `.planning/phases/01-reproducibility-and-safety-foundation/01-VERIFICATION.md` - Verified Phase 1 artifacts and residual risks.
- `.planning/phases/01-reproducibility-and-safety-foundation/01-05-SUMMARY.md` - Explicit evaluator revision mode, manifest ordering, append-only attempts, CLI flags, and tests.

### Codebase Maps

- `.planning/codebase/ARCHITECTURE.md` - Existing evaluation, provider, task, visualization, and generated-output architecture.
- `.planning/codebase/STRUCTURE.md` - File layout and recommended locations for new experiment wrappers, statistical utilities, and artifacts.
- `.planning/codebase/CONVENTIONS.md` - Python style, CLI conventions, import side-effect guidance, and logging patterns.
- `.planning/codebase/CONCERNS.md` - Monolithic evaluator risks, until-correct weaknesses, generated artifact risks, and provider failure concerns.
- `.planning/codebase/TESTING.md` - Current testing patterns and testable seams.

### Implementation Surfaces

- `revision_artifacts.py` - Phase 1 run manifest, attempt record, summary row, writer, run-id validation, and hash helpers.
- `revision_preflight.py` - Existing offline preflight command to extend or complement for adaptive runs.
- `run_eval.py` - Task loading, provider factory, scoring, existing revision-mode run support, and legacy until-correct loop.
- `run_single_experiment.py` - Existing experiment wrapper style.
- `exp2_to_exp3_predict.py` - Bernoulli Success@k and expected-attempt prediction logic.
- `visualize_results.py` - Existing result loading, task family metadata, hard-task labels, and figure pipeline.
- `tests/` - Phase 1 automated test suite patterns for offline validators and fake/provider-boundary tests.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `revision_artifacts.py` already provides `RunManifest`, `AttemptRecord`, `SummaryRow`, `RevisionArtifactWriter`, `revision_run_dir()`, `sha256_file()`, and `sha256_text()`. Phase 2 should build on these without breaking v1 schemas.
- `revision_preflight.py` already validates task aliases, dataset paths, prompts, expected request counts, run ids, output paths, and cost preview availability. Adaptive preflight should reuse this foundation while adding adaptive-specific fields.
- `run_eval.build_tasks()` already resolves task aliases, dataset directories, prompts, few-shot exclusions, and normalized `TaskItem` instances.
- `run_eval.make_provider()` and provider adapters provide the live multimodal inference boundary.
- `run_eval.evaluate_pass1()` is the shared correctness gate and should be reused to avoid scorer drift.
- `exp2_to_exp3_predict.py` already implements the Bernoulli Success@k baseline and expected-attempt formulas needed for the comparison table.
- `visualize_results.CAPTCHAVisualizer` already normalizes legacy Exp2/Exp3 results and contains task family metadata and hard-task display conventions.

### Established Patterns

- The repository uses flat root-level Python scripts rather than a packaged `src/` layout.
- CLIs use `argparse` and path defaults rooted at the repository.
- Phase 1 introduced `uv`, `pytest`, `ruff`, Pydantic schemas, `results/revision/<run_id>/`, and focused tests.
- Existing legacy result directories remain under `results/exp1` through `results/exp4`; revision-critical outputs should use `results/revision/<run_id>/`.
- Provider calls are synchronous and should remain explicit, cost-visible, and gated by preflight.

### Integration Points

- New adaptive logic should likely live in a focused script/module and call into `run_eval` for task construction, provider creation, and scoring.
- Adaptive attempts should be append-only and written before derived summaries.
- Comparison outputs should combine adaptive run artifacts, Exp2 pass@1 inputs, Bernoulli Success@k predictions, and observed fixed retry results where available.
- Tests should use fake providers or monkeypatch provider boundaries rather than live credentials.
- Optional paid smoke should be a separate command/path that is not run by default.

</code_context>

<specifics>
## Specific Ideas

- Do not use provider-native hidden memory. All attacker state must be explicit in local artifacts and prompt inputs.
- Keep the paper's primary evaluation unit as task type. Use structural bottleneck tags only for interpretation and persistent-failure narrative.
- Treat the stale Phase 1 context note that placed adaptive work in a later phase as superseded by the current ROADMAP and STATE, which make adaptive attacker evidence Phase 2.
- Keep the adaptive threat model strong enough to address fixed-prompt/i.i.d. concerns, but constrained enough that reviewers can audit exactly what feedback and memory were available.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within Phase 2 scope.

</deferred>

---

*Phase: 02-adaptive-attacker-main-body-evidence*
*Context gathered: 2026-05-18*
