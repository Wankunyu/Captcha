# Phase 3: Dataset Scope, Statistical Confidence, and Limitations - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-05-19
**Phase:** 3 - Dataset Scope, Statistical Confidence, and Limitations
**Areas discussed:** Extended dataset strategy, adaptive attacker on extended dataset, threshold sensitivity labels, retry calibration and failure taxonomy

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

## Threshold Sensitivity Labels

| Option | Description | Selected |
|--------|-------------|----------|
| Leave as prose only | Mention the 40% cutoff limitation in text without producing structured labels. | |
| Carry Phase 2 labels forward unchanged | Reuse hard/borderline/broken without additional sensitivity diagnostics. | |
| Produce structured threshold-sensitivity labels | Report hard/borderline/broken, margin to cutoff, threshold-sensitive flags, and caveat wording. | yes |

**User's choice:** Produce structured threshold-sensitivity labels.

**Notes:** The user identified this as a Phase 3 completion requirement. After checking the submitted paper, the locked direction is to keep the paper's existing 40% working threshold, use a 30%-50% review band for threshold-sensitive cases, and treat that band as a caution mechanism rather than a new security tier. CI material is only contingency or appendix-ready backup for possible reviewer follow-up; the main manuscript emphasis should be dataset imbalance, sample counts, underpowered categories, and threshold/trend sensitivity.

---

## Retry Calibration and Failure Taxonomy

| Option | Description | Selected |
|--------|-------------|----------|
| Keep existing Bernoulli predictions only | Reuse `Success@k` predictions without observed-vs-predicted diagnostics. | |
| Add retry calibration only | Compare predictions to observed retry/adaptive-compatible outcomes but leave failure classes separate. | |
| Add retry calibration plus failure taxonomy | Produce prediction-error outputs and paper-ready scientific/protocol/infrastructure failure summaries. | yes |

**User's choice:** Add retry calibration plus failure taxonomy.

**Notes:** The user identified this as a Phase 3 completion requirement and accepted the recommended lock. Bernoulli `Success@k` predictions should be aligned with observed retry or adaptive-compatible outcomes. Prediction errors should be task-type primary with optional family summaries. Summaries should report both `raw_observed_rate` and `scientific_rate`, with main paper claims preferring `scientific_rate` and treating infrastructure/protocol failures as reliability or limitation evidence rather than CAPTCHA robustness evidence.

---

## the agent's Discretion

- Exact artifact names, CLI flags, and minimum underpowered-sample thresholds may be chosen during planning.
- Confidence interval method and placement may be selected during planning, but CI should remain contingency or appendix-ready backup rather than the main manuscript thread.
- Exact threshold-sensitive flag logic may be refined during planning if it preserves margin-to-cutoff reporting.
- Exact retry-calibration table layout may be chosen during planning if it includes prediction-error and failure-taxonomy fields.

## Deferred Ideas

- Full external benchmark/SOTA solver integration remains Phase 4.
- Full reruns across every old and new task are not required for Phase 3 by default.
