# External Integrations

**Analysis Date:** 2026-05-15

## APIs & External Services

**LLM Inference Providers:**
- OpenAI - evaluates CAPTCHA tasks with GPT-5/GPT-5.1 reasoning models and `gpt-5-chat-latest`.
  - SDK/Client: `openai.OpenAI` in `run_eval.py`.
  - Auth: `providers.openai.api_key` in `secrets.yaml`.
  - Request shape: Responses API for `gpt-5`/`gpt-5.1`, Chat Completions for `gpt-5-chat-latest`, with inline base64 image data and JSON output parsing in `OpenAIProvider`.
- Anthropic - evaluates CAPTCHA tasks with Claude models.
  - SDK/Client: `anthropic.Anthropic` in `run_eval.py`.
  - Auth: `providers.anthropic.api_key` in `secrets.yaml`.
  - Request shape: `messages.create` with image blocks, tool schema `submit_answer`, optional thinking budget, and JSON tool input parsing in `AnthropicProvider`.
- Google Gemini - evaluates CAPTCHA tasks with Gemini 2.5 models.
  - SDK/Client: `google.genai.Client` and `google.genai.types` in `run_eval.py`.
  - Auth: `providers.gemini.api_key` in `secrets.yaml`.
  - Request shape: `models.generate_content` with inline raw image bytes, `response_mime_type="application/json"`, response schema configuration, and optional thinking budget in `GeminiProvider`.
- Fireworks AI - evaluates CAPTCHA tasks with OpenAI-compatible vision-language models such as Qwen3-VL.
  - SDK/Client: `openai.OpenAI` with a Fireworks base URL in `run_eval.py`.
  - Auth: `providers.fireworks.api_key` in `secrets.yaml`.
  - Endpoint: default `https://api.fireworks.ai/inference/v1`, overridable through `providers.fireworks.base_url` in `secrets.yaml`.
  - Request shape: Chat Completions with inline base64 image URLs and strict JSON schema in `FireworksProvider`.

**Provider Routing:**
- `make_provider()` in `run_eval.py` centralizes provider selection, credential lookup, timeout configuration, and thinking-option merging.
- `run_eval()` and `run_until_type_correct()` in `run_eval.py` call the selected provider for Exp1/Exp2/Exp4 and Exp3-style retry evaluation.
- `run_single_experiment.py` exposes user-facing experiment wrappers that pass provider/model/secrets settings into `run_eval.py`.

**Cost and Usage Metadata:**
- Token usage is collected from provider SDK responses in `OpenAIProvider`, `AnthropicProvider`, `GeminiProvider`, and `FireworksProvider` in `run_eval.py`.
- Cost estimates use the `pricing` section in `secrets.yaml` through `estimate_cost()` in `run_eval.py`.
- Token logs and summaries are written to local files under `results/` and `error_analysis/` by `run_eval.py`, `run_single_experiment.py`, and `experiments_helper.py`.

## Data Storage

**Databases:**
- Not detected. No SQLite, Postgres, MySQL, MongoDB, Supabase, ORM, or database migration tooling is present.
  - Connection: Not applicable.
  - Client: Not applicable.

**File Storage:**
- Local filesystem only.
- CAPTCHA inputs and ground truth live under `captcha_data/*/ground_truth.json` plus task image files; `captcha_data/**` is Git LFS-managed in `.gitattributes`.
- Few-shot assets live under `few_shot_assets/`, with manifests/configuration in `few_shot_image_manifest.json`, `few_shot_examples.yaml`, and `few_shot_answers.py`.
- Experiment outputs live under `results/exp*/<provider>/<model>/`, with CSV results and token summary JSON files documented in `README.md` and consumed by `visualize_results.py`.
- Error-analysis outputs live under `error_analysis/` and `results/error_analysis/`, written by `experiments_helper.py` and `run_eval.py`.
- Generated publication figures live under `figures/`, written by `visualize_results.py` and notebooks.

**Caching:**
- In-process image cache only. `ImageCache` in `run_eval.py` caches raw image bytes and base64 strings with a max size of 512 items.
- No Redis, Memcached, disk cache service, or remote cache detected.

## Authentication & Identity

**Auth Provider:**
- API-key based provider authentication.
  - Implementation: `load_secrets()` in `run_eval.py` reads local YAML/JSON config, then `make_provider()` injects `api_key` values into provider clients.
  - Credential file: `secrets.yaml` is present at repo root and must be treated as secret configuration. Contents were not included in this map.
  - Environment variables: provider API keys are not read directly from environment variables in the main provider path.

## Monitoring & Observability

**Error Tracking:**
- No external error tracking service detected.
- Local error collection is implemented by `SimpleErrorCollector` in `experiments_helper.py`, which writes `errors.csv`, `stats.json`, and `token_summary.json` under error-analysis directories.

**Logs:**
- Console logging through `print()` statements in `run_eval.py`, `run_single_experiment.py`, `experiments_helper.py`, `prepare_few_shot_examples.py`, and `visualize_results.py`.
- Structured local outputs include result CSVs, token logs, token summaries, error CSVs, and stats JSON files under `results/` and `error_analysis/`.

## CI/CD & Deployment

**Hosting:**
- Not detected. The project is run locally from scripts and notebooks.

**CI Pipeline:**
- None detected. No `.github/`, `.gitlab/`, `.circleci/`, or workflow config is present.

## Environment Configuration

**Required env vars:**
- None detected for provider credentials in the main execution path.
- Optional: `FEW_SHOT_ASSETS_ROOT` can override the default `./few_shot_assets` root in `run_eval.py`.

**Required local config keys:**
- `providers.openai.api_key` for OpenAI experiments.
- `providers.anthropic.api_key` for Anthropic experiments.
- `providers.gemini.api_key` for Gemini experiments.
- `providers.fireworks.api_key` for Fireworks experiments.
- `providers.fireworks.base_url` is optional; `run_eval.py` falls back to the Fireworks inference endpoint.
- `pricing.<provider>.<model>.in_per_1k` and `pricing.<provider>.<model>.out_per_1k` are used by `estimate_cost()` for cost summaries.

**Secrets location:**
- Local `secrets.yaml` at repo root. The file exists and is referenced by `README.md`, `run_eval.py`, and `run_single_experiment.py`.
- `run_eval.py` also contains exploratory bottom-of-file provider snippets; use the `load_secrets()` and `make_provider()` path for new integrations rather than ad hoc client setup.

## Webhooks & Callbacks

**Incoming:**
- None detected. There is no web server, HTTP route layer, webhook endpoint, or callback handler.

**Outgoing:**
- Outbound HTTPS API calls are made through SDK clients for OpenAI, Anthropic, Google Gemini, and Fireworks in `run_eval.py`.
- No project-defined outgoing webhooks or callback registrations detected.

---

*Integration audit: 2026-05-15*
