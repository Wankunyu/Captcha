---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Completed 03-02-PLAN.md
last_updated: "2026-05-19T01:08:51.744Z"
last_activity: 2026-05-19
progress:
  total_phases: 6
  completed_phases: 2
  total_plans: 14
  completed_plans: 12
  percent: 86
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-16)

**Core value:** Produce credible, reproducible revision evidence that directly strengthens the paper's claims about structural CAPTCHA robustness against multimodal LLM attackers.
**Current focus:** Phase 3 - Dataset Scope, Statistical Confidence, and Limitations

## Current Position

Phase: 3 (Dataset Scope, Statistical Confidence, and Limitations) - EXECUTING
Plan: 3 of 4
Status: Ready to execute
Last activity: 2026-05-19

Progress: [█████████░] 86%

## Performance Metrics

**Velocity:**

- Total plans completed: 12
- Average duration: N/A
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 5 | - | - |
| 02 | 5 | - | - |

**Recent Trend:**

- Last 5 plans: N/A
- Trend: N/A

*Updated after each plan completion*
| Phase 02 P01 | 18min | 2 tasks | 2 files |
| Phase 02 P02 | 4min | 2 tasks | 2 files |
| Phase 02 P03 | 8min | 2 tasks | 2 files |
| Phase 02 P04 | 10min | 3 tasks | 2 files |
| Phase 02 P05 | 4min | 3 tasks | 2 files |
| Phase 03 P01 | 11min | 3 tasks | 6 files |
| Phase 03 P02 | 7 min | 2 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Use six shepherding-aligned phases: reproducibility foundation, adaptive attacker main-body evidence, dataset/statistical limitations, SOTA/larger benchmark strengthening, defense/HCI methodology, and ethics/artifact/paper alignment.
- [Roadmap]: Keep the work paper-driven; broad refactoring is only in scope when it protects experiment correctness, reproducibility, or artifact integrity.
- [Roadmap]: Treat external baseline feasibility as uncertain until primary artifacts, licenses, datasets, metrics, and schemas are inspected.
- [Roadmap]: Preserve Phase 1 plans, but execute future phases in the latest shepherding-response order from Shepherding.docx.
- [Deadline]: The current revision package targets May 28 AoE for revised paper, color-coded diff, point-by-point changes, and final artifact package.
- Adaptive artifacts live in a separate module so Phase 1 AttemptRecord v1 remains unchanged.
- Adaptive summaries separate scientific_wrong, protocol_failure, and infrastructure_failure counts.
- Confidence interval fields are nullable in Phase 2 and carry an explicit repeated-run deferral reason.
- Adaptive preflight reports solve_request_count, reflection_request_count_max, and expected_request_count_max separately.
- Pricing preview reads only explicit non-secret pricing metadata, never local secret configuration.
- Prompt/few-shot inputs and prompt prefix/suffix values are recorded as hashes, not raw prompt text.
- Adaptive output directories fail closed unless --overwrite or --resume is explicit.
- Adaptive execution samples each task-type pool without replacement using a local seeded random generator.
- Adaptive resume skips provider construction when selected task types already have terminal adaptive attempts.
- Adaptive run manifests are written before local config loading and provider construction.
- Adaptive reflection is hard-coded to Feedback: FAIL and only used after scientific wrong answers when another solve attempt remains.
- Comparison rows remain task-type primary under the same attempt_budget_k for Bernoulli, fixed retry, and adaptive outcomes.
- Provider/runtime/protocol failures remain visible as counts but never create persistent hard-family notes without scientific_wrong_count > 0.
- Structural bottleneck tags preserve the AdaptiveComparisonRow list schema from 02-01 while staying explanatory, not the primary evaluation unit.
- The complete Phase 2 adaptive workflow is validated with an offline fake-provider E2E test before any optional paid provider run.
- Optional paid smoke requires adaptive preflight and inspection of expected_request_count_max before a budget decision.
- README makes offline pytest/ruff validation the default path and marks paid smoke as explicitly non-default.
- Phase 3 schemas live in phase3_artifacts.py so Phase 1 and Phase 2 artifact contracts remain unchanged.
- Dataset scope audit counts evaluated evidence only from results/exp1 through results/exp4, excluding error_analysis result files.
- Extended-data evidence remains split into original, supplemented-category, and new-category rows with selective validation-slice comparison outputs.
- Pass-rate loading explicitly scans results/exp1 through results/exp4 and excludes error_analysis outputs.
- Wilson confidence intervals use stdlib statistics.NormalDist and math.sqrt to avoid adding SciPy or statsmodels.
- Adaptive and extended-validation rates are threshold trend sources only, not merged old-plus-new evidence.

### Pending Todos

None yet.

### Blockers/Concerns

- [Resolved in Phase 1]: Secret-safe import, redaction, preflight, manifest, attempt-log, and validator contracts are now in place before new paid provider runs.
- [Resolved in Phase 2]: Adaptive schemas, preflight, offline loop, comparison builder, and offline end-to-end validation are complete; optional paid smoke remains separate and budget-gated.
- [Phase 3]: Dataset-scope, confidence-interval, threshold-sensitivity, retry-calibration, and infrastructure-vs-scientific failure artifacts are planned and ready to execute.
- [Phase 4]: External solver and larger-dataset comparisons require comparability labels to avoid apples-to-oranges claims.
- [Phase 6]: Ethics/disclosure details and artifact availability need scripted traceability so final claims do not exceed generated evidence.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260515-v59 | Update revision roadmap from Shepherding.docx | 2026-05-16 | docs-only | [.planning/quick/260515-v59-update-revision-roadmap-from-shepherding/](./quick/260515-v59-update-revision-roadmap-from-shepherding/) |
| 260519-al4 | Align Phase 2 adaptive comparison cutoff semantics with the paper-facing 40% threshold and Phase 3 sensitivity framing | 2026-05-18 | 5638e17 | [.planning/quick/260519-al4-align-phase-2-adaptive-comparison-cutoff/](./quick/260519-al4-align-phase-2-adaptive-comparison-cutoff/) |

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Longitudinal robustness | Repeat benchmark across future model releases | Deferred to v2 | Requirements definition |
| Human factors | Formal human-subjects usability and accessibility study | Deferred to v2 | Requirements definition |
| Advanced attackers | Fine-tuned, distilled, or custom-trained attacker models | Deferred to v2 | Requirements definition |
| Production defense | Production CAPTCHA service or live dynamic-template deployment | Deferred to v2 | Requirements definition |

## Session Continuity

Last session: Completed 03-02-PLAN.md
Stopped at: Completed 03-02-PLAN.md
Resume file: None

**Next Phase:** 03 (Dataset Scope, Statistical Confidence, and Limitations) — ready to execute

**Planned Phase:** 3 (Dataset Scope, Statistical Confidence, and Limitations) — 4 plans — 2026-05-19T00:20:25.541Z
