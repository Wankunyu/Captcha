---
quick_id: 260522-ezj
slug: replace-unsupported-fireworks-qwen-row-w
status: in_progress
date: 2026-05-22
---

# Quick Task 260522-ezj: Replace Unsupported Fireworks Qwen Row

## Objective

Replace the Phase 04.2 Qwen supplemental experiment row that previously used
Fireworks with an OpenRouter-backed row for
`qwen/qwen3-vl-235b-a22b-instruct`, while preserving provider-free preflight,
runtime model mapping, pricing visibility, and existing offline artifact safety.

## Plan

1. Add OpenRouter as an OpenAI-compatible provider in `run_eval.py`, including
   optional OpenRouter headers and CLI/help visibility.
2. Update Phase 04.2 paper-facing model matrix, pricing lookup, historical token
   estimate fallback, and runtime mapping so the stored row is
   `openrouter/qwen_qwen3-vl-235b-a22b-instruct` and the runtime model is
   `qwen/qwen3-vl-235b-a22b-instruct`.
3. Update focused tests and docs, then verify with lint, unit tests, and a
   provider-free preflight check.

## Verification

- `uv run ruff check run_eval.py expanded_dataset_phase042.py revision_provider_smoke.py visualize_results.py tests/test_openrouter_provider.py tests/test_phase042_static_pipeline.py tests/test_phase042_adaptive_pipeline.py`
- `uv run pytest tests/test_openrouter_provider.py tests/test_phase042_static_pipeline.py tests/test_phase042_adaptive_pipeline.py -q`
- Provider-free Phase 04.2 static preflight check in `/private/tmp`.
