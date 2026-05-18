# Phase 3: Dataset Scope, Statistical Confidence, and Limitations - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-05-19
**Phase:** 3 - Dataset Scope, Statistical Confidence, and Limitations
**Areas discussed:** Extended dataset strategy, adaptive attacker on extended dataset

---

## Extended Dataset Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Supplement existing categories only | Add samples to current task categories to increase per-category sample counts. | |
| Add new categories only | Treat the extended dataset as separate new CAPTCHA categories. | |
| Combine both routes | Add samples to some existing categories and add new categories where feasible. | yes |

**User's choice:** Combine both routes.

**Notes:** The advisor discussion concluded that selective supplementation is preferable to overextending the revision work. Existing categories can be supplemented where sample counts are thin, and new categories can be added to test whether the old conclusions still hold beyond the original dataset. At least two new categories are preferred if feasible; if exact matches are unavailable, the new additions can be described as new CAPTCHA types.

---

## Experiment Rerun Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Merge and rerun everything | Combine old and new data and rerun all experiments. | |
| Run only new data and compare | Evaluate the new data slice and compare it with original conclusions. | yes |
| Defer all new-data runs | Produce only a plan for future expansion. | |

**User's choice:** Run only new data and compare.

**Notes:** The advisor discussion rejected exhaustive reruns as unnecessary for the revision timeline. The intended comparison is whether the conclusions from the original dataset remain valid on the new dataset slice.

---

## Adaptive Attacker on Extended Dataset

| Option | Description | Selected |
|--------|-------------|----------|
| Do not run adaptive on extended data | Keep adaptive evidence only on the original Phase 2 dataset. | |
| Optional if time allows | Treat adaptive-on-extended as nonessential and run only if schedule permits. | |
| Include adaptive-on-extended as a validation slice | Plan for adaptive attacker evaluation on the extended dataset, scoped to claim-relevant categories. | yes |

**User's choice:** Include adaptive-on-extended as a validation slice.

**Notes:** The advisor originally said adaptive on extended data was not mandatory, but the user decided it can be run. The context records this as allowed and desirable within scope, provided it remains a selective validation slice and preserves Phase 2 binary-feedback explicit-memory semantics.

---

## the agent's Discretion

- Exact artifact names, CLI flags, and minimum underpowered-sample thresholds may be chosen during planning.
- Confidence interval method may be selected during planning if documented and suitable for small sample counts.

## Deferred Ideas

- Full external benchmark/SOTA solver integration remains Phase 4.
- Full reruns across every old and new task are not required for Phase 3 by default.
