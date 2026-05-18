---
status: complete
quick_id: 260519-al4
slug: align-phase-2-adaptive-comparison-cutoff
completed: 2026-05-18
commit: 5638e17
---

# Quick Task 260519-al4 Summary

## Result

Aligned Phase 2 adaptive comparison semantics with the submitted paper's 40% working CAPTCHA threshold and the Phase 3 threshold-sensitivity framing.

## Changes

- Updated `adaptive_compare.py` so default classification uses `cutoff=0.40` with `borderline_margin=0.0`.
- Updated the default cutoff note to stop claiming a `+/- 5%` borderline margin.
- Kept `--borderline-margin` as an explicit optional analysis setting for compatibility and future sensitivity checks.
- Added tests for the paper-facing default, explicit nonzero-margin behavior, and negative-margin validation.
- Updated Phase 2 planning/research artifacts that described the old margin default.

## Verification

- `uv run pytest tests/test_adaptive_compare.py -q` - passed.
- `uv run ruff check adaptive_compare.py tests/test_adaptive_compare.py` - passed.
- `uv run python adaptive_compare.py --help` - passed.
- `rg -n '\+/- 5|borderline margin|default=0\.05|margin `0\.05`' adaptive_compare.py tests/test_adaptive_compare.py .planning/phases/02-adaptive-attacker-main-body-evidence` - no matches.

## Notes

The only remaining `0.05` references in the checked scope are explicit test calls using `margin=0.05`, which prove that nonzero-margin sensitivity analysis still works when deliberately requested. Phase 3 remains responsible for the manuscript-facing `30%-50%` review band and broader threshold-sensitivity analysis.
