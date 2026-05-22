---
quick_id: 260522-ezj
status: complete
date: 2026-05-22
commit: deferred
---

# Quick Task 260522-ezj Summary

## Completed

- Added an OpenRouter provider path in `run_eval.py` using the OpenAI-compatible
  API default `https://openrouter.ai/api/v1`, optional OpenRouter headers, and
  the same normalized inference interface as other providers.
- Replaced the Phase 04.2 Qwen paper-facing row with
  `openrouter/qwen_qwen3-vl-235b-a22b-instruct`, while mapping runtime calls to
  `qwen/qwen3-vl-235b-a22b-instruct`.
- Updated Phase 04.2 pricing metadata to OpenRouter's published
  `0.00020/0.00088` USD per 1K input/output tokens and preserved historical
  Fireworks token summaries as a token-count fallback only.
- Updated focused tests, visualization display names, provider smoke wiring, and
  README configuration placeholders.

## Verification

- `uv run pytest tests/test_openrouter_provider.py tests/test_phase042_static_pipeline.py tests/test_phase042_adaptive_pipeline.py -q`
- `uv run ruff check run_eval.py expanded_dataset_phase042.py revision_provider_smoke.py visualize_results.py tests/test_openrouter_provider.py tests/test_phase042_static_pipeline.py tests/test_phase042_adaptive_pipeline.py`
- Provider-free static preflight check wrote
  `/private/tmp/captcha_openrouter_preflight_check/phase04_2_static_openrouter_preflight_check_20260522/expanded_static_preflight_matrix.json`.
- Paid static remediation completed after `providers.openrouter.api_key` was added
  to local `secrets.yaml`: `results/revision/phase04_2_static_openrouter_qwen_infra_remediation_20260522/expanded_static_summary.json`.

## Notes

- The temporary preflight check produced seven rows with one OpenRouter Qwen row
  and zero Fireworks rows.
- The OpenRouter Qwen remediation replaced the unsupported Fireworks 80/80
  infrastructure-failure row with 80 completed OpenRouter attempts, 3 successes,
  and 0 infrastructure failures.
- Final git commit was deferred while the GPT-5 medium adaptive run had existing
  manifests that validated `code_revision` on resume.
