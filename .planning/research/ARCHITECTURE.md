# Architecture Patterns

**Project:** COGNITION revision experiments
**Domain:** Offline multimodal LLM CAPTCHA evaluation for paper-revision evidence
**Researched:** 2026-05-15
**Overall confidence:** HIGH for codebase integration; MEDIUM for exact phase sizing until benchmark-source availability is confirmed

## Recommended Architecture

Keep the existing flat Python pipeline intact and add a narrow revision layer around it. The current evaluator is monolithic, but it already owns the highest-risk contracts: task loading, provider payloads, JSON schemas, answer scoring, token accounting, and result writing. A broad refactor during revision work would create more risk than value.

The right architecture is therefore a strangler-style extension:

```text
existing scripts/notebooks
        |
        v
revision experiment wrappers and artifact generators
        |
        v
stable compatibility calls into run_eval.py
        |
        v
captcha_data/ + prompts + provider adapters + evaluate_pass1()
        |
        v
versioned revision artifacts under results/, error_analysis/, figures/, and paper-ready tables
```

New work should be organized as root-level scripts and helper modules, matching the current repository style. Each new module should have one purpose, produce explicit CSV/JSON/Markdown artifacts, and avoid moving provider or task-scoring logic out of `run_eval.py` until after the revision deadline.

## Architectural Principles

1. Treat `run_eval.py` as the compatibility core.
2. Add new runners beside existing scripts instead of rewriting existing experiment entry points first.
3. Reuse `build_tasks()`, `build_json_schema()`, `make_provider()`, and `evaluate_pass1()` for all MLLM attacker experiments.
4. Keep statistical, baseline-comparison, and defense-methodology work offline whenever possible so those phases can run without provider credentials.
5. Make every revision claim traceable to a versioned artifact: manifest, raw attempt rows, aggregate results, confidence intervals, figure/table inputs, and prose-ready summaries.
6. Preserve existing `results/exp*/<provider>/<model>/results.csv` compatibility for `visualize_results.py` and notebooks.
7. Do not read, print, copy, or document credential values. Treat local provider configuration as a private runtime dependency only.

## Component Boundaries

| Component | Responsibility | Owns | Should Not Own | Communicates With |
|-----------|----------------|------|----------------|-------------------|
| Existing evaluation core | Task construction, provider calls, schemas, scoring, token/cost aggregation | `run_eval.py` functions and provider adapters | Revision-specific experiment policy | Revision runners |
| Existing experiment wrapper | User-facing Exp1-Exp4 compatibility | `run_single_experiment.py` CLI wrappers | New adaptive logic beyond thin dispatch | Existing core, notebooks |
| Adaptive attacker runner | Session-memory retry policy and attempt logging | New root-level script/module, likely `run_adaptive_experiment.py` | Provider payload details or task scoring | `run_eval.py`, result writer, confidence module |
| Revision result schema helper | Shared artifact naming, manifest writing, schema validation | New small helper, likely `revision_artifacts.py` | Experiment strategy | All new revision scripts |
| Statistical confidence reporter | Confidence intervals, threshold claim checks, task-family uncertainty | New offline script/module, likely `statistical_confidence.py` | Provider calls or new experiments | Existing and new result CSVs |
| Baseline and dataset comparison layer | Normalize external baseline or larger-dataset results into comparable tables | New offline-first script/module, likely `baseline_comparison.py` | Reimplementation of full SOTA solvers by default | External result files, existing visualizer |
| Defense methodology generator | Convert empirical hardness factors into practitioner-facing methodology artifacts | New offline script/module, likely `defense_methodology.py` | Production CAPTCHA service behavior | Error analysis, task-family stats, paper tables |
| Visualization bridge | Load new experiment/result types and generate paper-ready figures | Narrow changes to `visualize_results.py` or separate revision plotting script | Raw experiment execution | Result schema helper, figures |
| Notebook compatibility layer | Keep notebooks as review and exploration surfaces | Thin notebook cells that call scripts or read artifacts | Canonical business logic | Scripts and generated artifacts |

## Recommended Data Flow

### 1. Current Evaluator Flow

```text
captcha_data/<TaskType>/ground_truth.json
        |
        v
run_eval.build_tasks()
        |
        v
TaskItem(type, puzzle_id, prompt, images, gt)
        |
        v
run_eval.make_provider() + provider.infer()
        |
        v
run_eval.extract_json() + run_eval.evaluate_pass1()
        |
        v
results/expN/<provider>/<model>/results.csv
error_analysis/...
token summaries
figures/...
```

This flow should remain the foundation for MLLM-based experiments. New experiments should call into it or reuse its primitives so scoring stays consistent across original, optimized, few-shot, until-correct, and adaptive-attacker results.

### 2. Adaptive Attacker Flow

```text
adaptive run config
        |
        v
build_tasks() per task type
        |
        v
AdaptiveSession(task_type, attempt history, observed failures, strategy state)
        |
        v
prompt mutation / memory summary / next-item policy
        |
        v
provider.infer() through existing ModelProvider
        |
        v
evaluate_pass1() through existing scorer
        |
        v
attempt rows + per-type summary + run manifest
        |
        v
confidence reporter + main-body figure/table inputs
```

The adaptive attacker should be implemented as a new runner, not as a modification to `run_until_type_correct()` first. `run_until_type_correct()` is useful as a baseline policy, but the adaptive policy needs durable attempt rows, explicit session state, and comparable Pass@k/cost summaries. The runner can still reuse the same provider and scoring functions.

Recommended adaptive artifacts:

| Artifact | Purpose |
|----------|---------|
| `attempts.csv` | One row per attempt with task type, puzzle id, attempt index, policy label, pass/fail, latency, token counts, and non-sensitive strategy metadata |
| `results.csv` | Visualizer-compatible per-task-type summary with provider, model, task type, n, pass rate, latency, tokens, and cost |
| `adaptive_summary.json` | Per-task and task-family Pass@k, first-hit attempt distribution, cost, and hard-task interpretation inputs |
| `run_manifest.json` | Dataset path, task list, prompt mode, max attempts, seed, code revision when available, provider/model labels, and artifact schema version |

Do not store full credential config, secret values, or unnecessary raw provider payloads in these artifacts.

### 3. Baseline and Dataset Comparison Flow

```text
external baseline or larger-dataset outputs
        |
        v
source-specific adapter
        |
        v
canonical comparison schema
        |
        v
task-family mapping + metric normalization
        |
        v
baseline_comparison.csv + limitations notes
        |
        v
paper table and appendix artifact
```

The baseline layer should start with result ingestion, not solver reimplementation. Reviewers asked for comparison against specialized solvers and larger datasets, but the lowest-risk first step is to normalize available published or reproduced outputs into an explicit comparison schema. Reimplementing an entire SOTA solver should only happen after the artifact gap is clear and the implementation cost is justified.

Recommended canonical comparison columns:

| Column | Meaning |
|--------|---------|
| `source` | Existing COGNITION run, external paper, reproduced baseline, or larger dataset |
| `solver_type` | Off-the-shelf MLLM, adaptive MLLM, specialized solver, or dataset-only reference |
| `dataset` | CaptchaWorld, larger external dataset, or curated subset |
| `task_type` | Local task identifier when mappable |
| `task_family` | Coarser family used for fair comparison when exact task types differ |
| `n` | Number of evaluated samples |
| `success_rate` | Comparable pass/success metric |
| `metric_definition` | Pass@1, Pass@k, solver success, or paper-reported metric |
| `comparability` | High, medium, or low depending on metric and dataset alignment |
| `notes` | Limitations, mapping assumptions, or missing details |

This component should explicitly separate "apples-to-apples local runs" from "contextual literature comparisons." Mixing them in one chart without comparability labels would weaken the response.

### 4. Statistical Confidence Flow

```text
existing results.csv / adaptive attempts.csv / baseline comparison rows
        |
        v
canonical result loader
        |
        v
binomial intervals + task-family aggregation + threshold checks
        |
        v
confidence_report.csv
confidence_summary.md
figure/table inputs
```

Confidence reporting should be an offline artifact generator that can run over existing results before any new model calls. This gives immediate value and creates a reusable check for all later phases.

Recommended outputs:

| Artifact | Purpose |
|----------|---------|
| `confidence_report.csv` | Row-level estimates with `n`, successes, point estimate, interval lower/upper, method, and threshold relation |
| `confidence_by_family.csv` | Aggregated uncertainty by task family and hardness group |
| `threshold_sensitivity.csv` | Results under several thresholds around the current 40 percent cutoff |
| `confidence_summary.md` | Paper-ready prose bullets explaining what is statistically supported and what remains limited |

The reporter should not depend on notebooks. Notebooks may read these artifacts to inspect plots, but the canonical interval calculations should live in a script.

### 5. Defense Methodology Flow

```text
task-family pass rates
        |
        v
error analysis and hard-task factors
        |
        v
hardness-factor matrix
        |
        v
methodology checklist + template-rotation artifact
        |
        v
paper Section 6 revision and practitioner appendix
```

The defense component should not become a production CAPTCHA service. It should produce an actionable methodology artifact that operationalizes the paper's evidence:

1. Identify whether a CAPTCHA is pure recognition, grid selection, coordinate precision, ordering, path reasoning, rotation, or compositional logic.
2. Score the design against observed hardness factors: continuous-space output, object-location binding, spatial precision, multi-step state, distractor resistance, and template diversity.
3. Flag weak designs that rely mainly on recognition or text/image classification.
4. Recommend structural hardening changes that preserve human clarity while adding model-hard interactions.
5. Define a lightweight rotation plan over template parameters, target composition, and instruction phrasing.
6. Emit a practitioner-facing checklist and a machine-readable factor matrix.

Recommended artifacts:

| Artifact | Purpose |
|----------|---------|
| `hardness_factor_matrix.csv` | Task types versus structural factors and empirical support |
| `defense_methodology.md` | Paper-ready methodology and practitioner checklist |
| `template_rotation_plan.json` | Non-production example of configurable defense dimensions |
| `defense_evidence_map.csv` | Links methodology claims to experiments, figures, and error-analysis evidence |

## Patterns to Follow

### Pattern 1: Additive Experiment Runner

**What:** Add new root-level runners that reuse `run_eval.py` primitives.

**When:** Adaptive attacker experiments, dataset extension runs, or targeted model comparisons.

**Shape:**

```python
from run_eval import build_tasks, build_json_schema, evaluate_pass1, load_secrets, make_provider

def run_revision_experiment(config):
    tasks = build_tasks(...)
    provider = make_provider(...)
    for attempt in policy.iter_attempts(tasks):
        raw, parsed, meta = provider.infer(...)
        ok = evaluate_pass1(attempt.task, parsed)
        writer.record_attempt(attempt, ok, meta)
    writer.write_summary()
```

**Why:** This keeps scoring and provider behavior consistent while avoiding a high-risk split of `run_eval.py`.

### Pattern 2: Offline Artifact Generator

**What:** Add scripts that read existing result files and emit paper-ready artifacts without provider calls.

**When:** Confidence intervals, threshold sensitivity, baseline comparison, defense methodology, and figure/table inputs.

**Why:** Offline scripts are cheap to test, reproducible, and safe to run repeatedly during manuscript editing.

### Pattern 3: Versioned Result Schemas

**What:** Every new result directory should include a small manifest and stable columns.

**When:** Any artifact intended to support a paper claim.

**Minimum manifest fields:**

| Field | Purpose |
|-------|---------|
| `schema_version` | Allows future loaders to handle format changes |
| `experiment_kind` | Original, optimized, few-shot, until-correct, adaptive, confidence, baseline, or defense |
| `created_at` | Run timestamp |
| `dataset_root` | Dataset location label, not secret material |
| `task_types` | Evaluated task identifiers |
| `provider` and `model` | Public model labels |
| `prompt_mode` | Ground-truth, optimized, auto, or adaptive |
| `seed` | Reproducibility |
| `max_attempts` | Retry/adaptive budget when relevant |
| `notes` | Known limitations |

### Pattern 4: Notebook as Consumer

**What:** Move reusable calculations from notebooks into scripts, then let notebooks import or display generated artifacts.

**When:** Migrating `plot.ipynb`, `test_statistic.ipynb`, or ad hoc revision analysis.

**Why:** Reviewer-facing claims need regeneration commands, not hidden notebook state.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Splitting `run_eval.py` Before Revision Evidence Exists

**What goes wrong:** Provider, scoring, schema, and task-loading behavior can change while experiments are being added.

**Consequence:** New revision results may become incomparable to accepted-paper results.

**Instead:** Add wrappers and helper modules first. Refactor `run_eval.py` only after smoke tests and result-schema checks exist.

### Anti-Pattern 2: Adaptive Logic Embedded as Prompt Strings Only

**What goes wrong:** The experiment becomes hard to audit because session memory, policy changes, and retry decisions are not explicit.

**Consequence:** Reviewers cannot tell whether gains came from memory, prompt mutation, sampling, or chance.

**Instead:** Represent adaptive policy state as structured rows and summaries, then derive prompts from that state.

### Anti-Pattern 3: Baseline Comparison Without Comparability Labels

**What goes wrong:** Specialized solvers, larger datasets, and local MLLM runs can have different task definitions and success metrics.

**Consequence:** Tables can overclaim fairness or understate limitations.

**Instead:** Normalize metrics where possible and label comparability level for every row.

### Anti-Pattern 4: Statistical Claims Only in Notebook Outputs

**What goes wrong:** Confidence intervals and threshold sensitivity become hard to regenerate.

**Consequence:** Paper text can drift from computed numbers.

**Instead:** Generate CSV and Markdown summaries from a script, then let notebooks render optional plots.

### Anti-Pattern 5: Defense Artifact Becomes a Production System

**What goes wrong:** Scope expands into service design, live deployment, browser automation, or human-study tooling.

**Consequence:** Revision work misses the reviewer request for a clear methodology.

**Instead:** Produce methodology, factor matrix, template-rotation plan, and evidence map only.

## Compatibility With Existing Scripts and Notebooks

Existing workflows should keep working:

| Existing Surface | Compatibility Plan |
|------------------|--------------------|
| `python run_single_experiment.py 1 ...` | Leave unchanged |
| `python run_single_experiment.py 2 ...` | Leave unchanged |
| `python run_single_experiment.py 3 ...` | Treat as fixed-policy until-correct baseline |
| `python run_single_experiment.py 4 ...` | Leave unchanged |
| `visualize_results.CAPTCHAVisualizer` | Add only narrow support for new `experiment_kind` or keep revision plots separate |
| `exp2_to_exp3_predict.py` | Preserve as Bernoulli baseline and compare against empirical adaptive results |
| `plot.ipynb` | Convert to reader of generated figure/table inputs |
| `test_statistic.ipynb` | Convert to reader of `confidence_report.csv` and `threshold_sensitivity.csv` |

For the new adaptive attacker, prefer a separate command first:

```bash
python run_adaptive_experiment.py --dataset-root ./captcha_data --provider openai --model gpt-5 --types Dice_Count Rotation_Match --max-attempts 10 --out-dir ./results/exp_adaptive/openai/gpt-5
```

After the command stabilizes, `run_single_experiment.py` can optionally receive a thin `run_experiment_5()` wrapper that delegates to it.

## Safe Migration From Manual Workflows

1. Inventory the current notebook-only claims and map each to a desired artifact file.
2. Add offline result loaders and schema checks before changing experiment behavior.
3. Create `statistical_confidence.py` over existing CSVs first, because it can validate the current evidence without new API cost.
4. Create the adaptive runner with a dry-run mode that builds tasks and writes a manifest without provider calls.
5. Run small smoke experiments on one or two task types before full provider/model sweeps.
6. Add baseline comparison ingestion using local CSV fixtures or manually curated literature rows before attempting external solver reproduction.
7. Generate defense methodology artifacts from existing evidence, then update them after adaptive and baseline results land.
8. Keep notebooks as optional visualization/review layers only.

## Suggested Build Order

### Phase 1: Reproducibility and Artifact Contracts

Build first because every later result depends on traceability.

Deliver:
- Shared artifact schema helper.
- Run manifest writer.
- Result directory conventions for revision experiments.
- Minimal schema validation for existing `results.csv` formats.
- Dry-run/preflight command that reports task counts, prompt mode, provider/model labels, and estimated run shape without provider calls.

Dependencies:
- Reads existing result layout and codebase conventions.
- Does not require new model calls.

### Phase 2: Statistical Confidence Reporting

Build second because it directly addresses reviewer concerns and can run on existing data.

Deliver:
- Confidence intervals by task type.
- Task-family aggregation.
- Threshold sensitivity around the 40 percent cutoff.
- Paper-ready confidence summary.

Dependencies:
- Phase 1 result schema helper.
- Existing Exp1/Exp2/Exp3/Exp4 CSVs.

### Phase 3: Adaptive Attacker Evaluation

Build third because it is the strongest new empirical requirement and uses the same schema and confidence machinery.

Deliver:
- Adaptive session runner.
- Attempt-level rows and per-type summaries.
- Comparison against fixed-policy Exp3 and Bernoulli prediction.
- Main-body figure/table inputs for hard-task robustness.

Dependencies:
- Phase 1 manifest/schema helper.
- Phase 2 confidence reporter.
- Existing `run_eval.py` provider and scoring primitives.

### Phase 4: Baseline and Dataset Comparison

Build fourth because it depends on knowing what local result schema and confidence labels look like.

Deliver:
- Baseline comparison schema.
- Source-specific adapters for available SOTA/larger-dataset artifacts.
- Comparability labels and limitation notes.
- Appendix-ready comparison table.

Dependencies:
- Phase 1 schema helper.
- Phase 2 confidence reporter for local and comparable rows.
- External result availability or manually curated literature metrics.

### Phase 5: Defense Methodology and HCI Scope

Build fifth because the methodology should cite the final evidence from confidence, adaptive attacker, and baseline phases.

Deliver:
- Hardness-factor matrix.
- Defense methodology Markdown.
- Template-rotation plan artifact.
- Evidence map from methodology claims to experiment outputs.

Dependencies:
- Existing error analysis and task-family mappings.
- Phase 2 confidence outputs.
- Phase 3 adaptive hard-task analysis.
- Phase 4 baseline/dataset comparison where available.

### Phase 6: Ethics, Artifact Availability, and Paper Claim Alignment

Build last because figures and notebooks should consume stable artifacts.

Deliver:
- Narrow visualizer support for adaptive and confidence artifacts, or a revision-only plotting script.
- Updated notebooks that read generated CSV/JSON rather than recomputing canonical logic.
- Final paper figure/table inputs.

Dependencies:
- Stable outputs from Phases 2 through 5.

## Component Dependency Map

```text
Artifact contracts
        |
        +--> Statistical confidence
        |           |
        |           +--> Adaptive result interpretation
        |           +--> Baseline comparison uncertainty labels
        |
        +--> Adaptive attacker runner
        |           |
        |           +--> Defense evidence map
        |
        +--> Baseline comparison layer
        |           |
        |           +--> Defense methodology limitations
        |
        +--> Defense methodology artifacts
                    |
                    +--> Final visualization and notebook cleanup
```

## Scalability Considerations

| Concern | Near Term Revision Runs | Larger Follow-Up Study | Long-Term Toolkit |
|---------|-------------------------|------------------------|-------------------|
| Provider cost | Dry-run manifests, small smoke runs, explicit max attempts | Budget caps and resumable queues | Bounded concurrency and provider retry policies |
| Result volume | CSV/JSON artifacts under existing result tree | Artifact schema versions and append-only attempt logs | External artifact store with checksums |
| Dataset scale | Reuse `captcha_data/` and adapters for external summaries | Dataset manifests and task-family mappings | Object storage and fixture-only git data |
| Code risk | Additive wrappers, no large evaluator split | Extract low-risk utilities after tests exist | Package layout with provider/task/scoring modules |
| Statistical claims | Binomial intervals and threshold sensitivity | Hierarchical or bootstrap task-family models | Full experiment registry and reproducibility dashboard |

## Risk Controls

| Risk | Mitigation |
|------|------------|
| Existing `run_eval.py` import side effects | Avoid importing it in docs-generation scripts that do not need provider/scoring behavior; when imported, never print or copy secret config |
| Task alias drift | Add schema/preflight checks for task names before full runs |
| Incomparable baseline metrics | Require `metric_definition` and `comparability` columns |
| Adaptive attacker overclaiming | Preserve fixed-policy, Bernoulli, and adaptive results side by side |
| Notebook drift | Make scripts authoritative and notebooks read-only consumers |
| Accidental secret exposure | Keep manifests limited to public labels and paths; exclude full local config values |
| Generated artifact churn | Use dedicated revision output directories and stable filenames |

## Source Basis

- `.planning/PROJECT.md`: revision goals, constraints, and reviewer-driven requirements.
- `.planning/codebase/ARCHITECTURE.md`: current pipeline layers, data flow, abstractions, and entry points.
- `.planning/codebase/STRUCTURE.md`: repository layout and recommended locations for new code.
- `.planning/codebase/CONVENTIONS.md`: root-level script style, naming conventions, and import patterns.
- `.planning/codebase/CONCERNS.md`: monolithic evaluator risk, import side effects, task alias drift, missing tests, generated artifact issues, and secret-handling concerns.
- Reviewer-comment file: adaptive attacker, statistical confidence, baseline/dataset comparison, and defense-methodology revision needs.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Existing pipeline integration | HIGH | Current evaluator, wrappers, result layout, and visualizer behavior are documented and confirmed from source signatures |
| Adaptive attacker boundary | HIGH | Can reuse existing task/provider/scoring primitives while isolating policy and state in a new runner |
| Statistical confidence architecture | HIGH | Can run offline over existing CSV outputs before new experiments |
| Baseline/dataset comparison | MEDIUM | Architecture is clear, but feasibility depends on accessible external artifacts and metric compatibility |
| Defense methodology artifacts | HIGH | Can be generated from existing task-family evidence and updated after adaptive/baseline phases |
| Safe migration plan | HIGH | Additive script-first migration minimizes risky refactors and preserves notebooks |

## Roadmap Implications

The roadmap should not start with a general cleanup of `run_eval.py`. Start with artifact contracts and offline analysis, then add adaptive experiments, then comparison and methodology artifacts. This order creates reproducible outputs early, constrains provider cost, and gives each later phase a stable evidence format.

Suggested sequence:

1. Reproducibility and artifact contracts.
2. Statistical confidence reporting.
3. Adaptive attacker evaluation.
4. Baseline and larger-dataset comparison.
5. Defense methodology artifacts.
6. Visualization and notebook cleanup.

The only phase that likely requires expensive provider calls is adaptive attacker evaluation. The statistical, comparison, defense, and visualization phases should be designed to run offline once their inputs exist.
