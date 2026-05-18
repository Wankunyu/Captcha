# Phase 2: Adaptive Attacker Main-Body Evidence - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-05-18
**Phase:** 2-Adaptive Attacker Main-Body Evidence
**Areas discussed:** Adaptive feedback and memory semantics, budget and comparison contract, main-body evidence outputs, implementation shape

---

## Adaptive Feedback and Memory Semantics

| Option | Description | Selected |
|--------|-------------|----------|
| Binary only | Only pass/fail feedback; no labels, coordinates, counts, categories, partial hints, or corrections. | yes |
| Binary + error type | Include parse/format/wrong-answer category in feedback. | |
| Binary + coarse family hint | Include high-level structural hints such as spatial/counting/order. | |

**User's choice:** Binary pass/fail only.
**Notes:** This locks ADAPT-02 and keeps the attacker from receiving ground-truth or local corrective information.

| Option | Description | Selected |
|--------|-------------|----------|
| Policy notes only | Persist failed-attempt counts, tried strategy summaries, and next prompt rules. | yes |
| Full transcript | Persist prompts, raw responses, parsed answers, and history. | |
| Minimal counters | Persist only success/failure counters and attempt index. | |

**User's choice:** Policy notes only.
**Notes:** The user asked whether persistent memory meant provider-native API memory. We clarified that Phase 2 memory must be explicit experiment-controlled state, not hidden provider memory.

| Option | Description | Selected |
|--------|-------------|----------|
| Rule-based policy | Fixed strategy templates update from feedback. | |
| Model self-reflection | Model writes its next strategy after a failure. | yes |
| Hybrid policy | Fixed template plus model-generated reflection fields. | |

**User's choice:** Model self-reflection, constrained.
**Notes:** The final decision constrains self-reflection: after each failure, the model may see only the current prompt, its own current raw/parsed answer, and binary fail feedback, then emit a short structured policy note. Long-term memory persists only the note, not a full transcript.

---

## Budget and Comparison Contract

| Option | Description | Selected |
|--------|-------------|----------|
| Task-family budget | Same attempt budget per structural family. | |
| Per-task-type budget | Same attempt budget per concrete CAPTCHA task type. | yes |
| Global budget | One shared budget across all tasks. | |

**User's choice:** Per-task-type budget.
**Notes:** The user corrected that the paper evaluates per task type, not per family. Structural family/bottleneck grouping remains explanatory only.

| Option | Description | Selected |
|--------|-------------|----------|
| Without replacement per task type | Sample fresh instances within each task type where possible. | yes |
| With replacement | Allow repeated instances, matching the older until-correct loop more closely. | |
| Fixed curated subset | Use a fixed small subset for stability. | |

**User's choice:** Without replacement per task type.
**Notes:** Supports the fresh CAPTCHA instance assumption.

| Option | Description | Selected |
|--------|-------------|----------|
| Stop on first success or max budget | Stop each task type after first success or budget exhaustion. | yes |
| Always exhaust budget | Continue after success to estimate adaptive pass rate. | |
| Stop after policy convergence | Stop once the policy note no longer changes. | |

**User's choice:** Stop on first success or max budget.
**Notes:** Aligns with Exp3 and Success@k comparison.

| Option | Description | Selected |
|--------|-------------|----------|
| Separate infra/protocol failures | Separate wrong answers, parse/format failures, and provider/runtime failures. | yes |
| Count all as failures | Treat every non-success as CAPTCHA-solving failure. | |
| Retry infra once then fail | Retry provider/runtime failures once before counting. | |

**User's choice:** Separate infra/protocol failures.
**Notes:** We discussed scientific wrong answers versus format/parse failures and provider/timeouts. Main paper claims should not treat provider/runtime infrastructure failures as structural CAPTCHA robustness evidence.

---

## Evidence Outputs for Main-Body Figures/Tables

| Option | Description | Selected |
|--------|-------------|----------|
| Task-type comparison table | One row per task type with Exp2 pass@1, Bernoulli Success@k, fixed retry, adaptive outcome, attempts-to-success, cost/latency, and classification change. | yes |
| Family summary table | One row per structural family. | |
| Both equal priority | Produce both as primary outputs. | |

**User's choice:** Task-type comparison table.
**Notes:** Matches the paper's evaluation unit.

| Option | Description | Selected |
|--------|-------------|----------|
| Task-type first + structural bottleneck tag | Keep task type as primary key and annotate bottleneck. | yes |
| Structural bottleneck first | Group primarily by failure mechanism. | |
| Raw failure list only | Preserve raw failure cases without paper-ready grouping. | |

**User's choice:** Task-type first with structural bottleneck tags.
**Notes:** Supports persistent-failure narrative without changing the primary evaluation unit.

| Option | Description | Selected |
|--------|-------------|----------|
| Hard / borderline / broken with cutoff note | Use labels while stating the cutoff is operational, not universal. | yes |
| Improved / unchanged / regressed only | Focus on adaptive impact without security labels. | |
| No labels, numbers only | Avoid categorical labels. | |

**User's choice:** Hard / borderline / broken with cutoff note.
**Notes:** The 40% threshold must be described as an operational cutoff.

---

## Implementation Shape Inside the Existing Codebase

| Option | Description | Selected |
|--------|-------------|----------|
| New focused module/script | Add adaptive logic outside the monolithic evaluator while reusing task/provider/scoring helpers. | yes |
| Extend `run_until_type_correct()` | Reuse the old Exp3 loop. | |
| Put inside `run_eval.py` as new function | Keep entry point centralized. | |

**User's choice:** New focused module/script.
**Notes:** Avoids expanding the most fragile file while preserving existing experiment semantics.

| Option | Description | Selected |
|--------|-------------|----------|
| Add adaptive-specific schemas while preserving v1 | Keep Phase 1 artifact contracts stable. | yes |
| Mutate existing `AttemptRecord` v1 | Change the existing attempt schema. | |
| Use loose JSON only | Avoid schema work. | |

**User's choice:** Add adaptive-specific schemas while preserving v1.
**Notes:** Downstream planner should avoid breaking Phase 1 revision artifact contracts.

| Option | Description | Selected |
|--------|-------------|----------|
| Adaptive preflight mode | Add adaptive-specific preflight fields and request-count preview. | yes |
| Reuse existing preflight manually | No adaptive-specific mode. | |
| No preflight for adaptive smoke | Run adaptive smoke without preflight. | |

**User's choice:** Adaptive preflight mode.
**Notes:** Required to keep Phase 2 behind the Phase 1 safety gate.

| Option | Description | Selected |
|--------|-------------|----------|
| Tiny paid smoke as final check, plus offline fake-provider tests | Use offline tests for contracts and optional small paid smoke for the live path. | yes |
| Tiny paid smoke only | Rely mainly on real API smoke. | |
| No paid smoke in Phase 2 | Keep validation fully offline. | |

**User's choice:** Offline fake-provider tests plus optional tiny paid smoke.
**Notes:** The user initially selected tiny paid smoke only, then clarified the intended decision is fake-provider validation as the main gate with paid smoke as an optional final real-provider check.

---

## the agent's Discretion

- Exact module/script names for adaptive logic.
- Exact adaptive schema class names and output filenames.
- Exact CLI flags for adaptive preflight and optional paid smoke.
- Exact structural bottleneck tag vocabulary, provided it remains task-type-first and paper-readable.

## Deferred Ideas

None.
