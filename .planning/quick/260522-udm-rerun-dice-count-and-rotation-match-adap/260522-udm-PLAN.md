---
quick_id: 260522-udm
slug: rerun-dice-count-and-rotation-match-adap
status: complete
date: 2026-05-22
---

# Quick Task 260522-udm: Rerun Dice_Count and Rotation_Match Adaptive Attacker

## Objective

Rerun the Phase 04.2 GPT-5 medium adaptive attacker experiment for only
`Dice_Count` and `Rotation_Match`, with `attempt_budget_k=3`, five
memory-isolated rounds, and samples solved on the first attempt in the previous
GPT-5 medium adaptive run excluded from the rerun slice.

## Plan

1. Add a reproducible rerun helper script that discovers prior first-attempt
   successes from append-only adaptive attempt logs, materializes the filtered
   two-category evaluator slice, and writes a visible k=3 preflight matrix.
2. Run the helper in dry-run mode to confirm excluded samples, sample counts,
   request counts, and cost preview before any provider call.
3. Execute five GPT-5 medium adaptive rounds with `k=3`, preserving append-only
   per-round artifacts, then write expanded and aggregate rerun summaries.

## Verification

- `uv run python scripts/run_phase042_adaptive_k3_dice_rotation_rerun.py --dry-run`
- `uv run python scripts/run_phase042_adaptive_k3_dice_rotation_rerun.py`
- Validate generated summary counts from
  `results/revision/phase04_2_adaptive_gpt5_medium_k3_dice_rotation_rerun_20260522/`.
