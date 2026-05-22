---
quick_id: 260522-udm
status: complete
date: 2026-05-22
commit: pending
---

# Quick Task 260522-udm Summary

## Completed

- Added `scripts/run_phase042_adaptive_k3_dice_rotation_rerun.py`, a
  reproducible runner for the filtered GPT-5 medium adaptive rerun.
- Generated a filtered two-category evaluator slice at
  `expanded_captcha_data/phase04_2/adaptive_k3_dice_rotation_rerun_slice_20260522/`.
- Excluded prior first-attempt successes from the previous GPT-5 medium
  adaptive run:
  - `Dice_Count`: `dice12.png`, `dice9.png`
  - `Rotation_Match`: `puzzle_polarbear_direction_5.json`
- Ran five memory-isolated GPT-5 medium rounds with `attempt_budget_k=3` over
  `Dice_Count` and `Rotation_Match`.
- Wrote rerun artifacts under
  `results/revision/phase04_2_adaptive_gpt5_medium_k3_dice_rotation_rerun_20260522/`.

## Results

| Task | Filtered Samples | Rounds | Success@3 | Solve Requests | Reflection Requests | Scientific Wrong | Protocol Failures | Infra Failures |
|------|------------------|--------|-----------|----------------|---------------------|------------------|-------------------|----------------|
| `Dice_Count` | 9 | 5 | 1/5 = 0.20 | 15 | 10 | 14 | 0 | 0 |
| `Rotation_Match` | 47 | 5 | 4/5 = 0.80 | 13 | 8 | 9 | 0 | 0 |

Total solve attempts: 28. Total successes: 5. Total protocol failures: 0.
Total infrastructure failures: 0.

## Artifacts

- Filter manifest:
  `results/revision/phase04_2_adaptive_gpt5_medium_k3_dice_rotation_rerun_20260522/filter_manifest.json`
- Preflight matrix:
  `results/revision/phase04_2_adaptive_gpt5_medium_k3_dice_rotation_rerun_20260522/adaptive_k3_preflight_matrix.json`
- Aggregate summary:
  `results/revision/phase04_2_adaptive_gpt5_medium_k3_dice_rotation_rerun_20260522/adaptive_k3_aggregate_summary.json`
- Expanded adaptive summary:
  `results/revision/phase04_2_adaptive_gpt5_medium_k3_dice_rotation_rerun_20260522/expanded_adaptive_summary.json`
- Per-round append-only attempt logs:
  `results/revision/phase04_2_adaptive_gpt5_medium_k3_dice_rotation_rerun_20260522-round*/adaptive_attempts.jsonl`

## Verification

- `uv run python scripts/run_phase042_adaptive_k3_dice_rotation_rerun.py --dry-run`
- `uv run ruff check scripts/run_phase042_adaptive_k3_dice_rotation_rerun.py`
- `uv run python scripts/run_phase042_adaptive_k3_dice_rotation_rerun.py`
- `python3 -m json.tool results/revision/phase04_2_adaptive_gpt5_medium_k3_dice_rotation_rerun_20260522/adaptive_k3_aggregate_summary.json`
- `python3 -m json.tool results/revision/phase04_2_adaptive_gpt5_medium_k3_dice_rotation_rerun_20260522/expanded_adaptive_summary.json`

## Notes

- The dry-run preflight estimated at most 50 total requests and approximately
  `$0.82469`, scaled from the previous Phase 04.2 GPT-5 medium preflight.
- Runtime `cumulative_cost_usd` fields remained `0.0` in the generated summary,
  so the preflight estimate is the useful cost reference for this rerun.
- The filtered slice is generated from existing local datasets and is ignored
  rather than committed because it duplicates 41MB of image material; the runner
  can regenerate it from the append-only previous attempt logs.
