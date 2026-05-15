# Codebase Concerns

**Analysis Date:** 2026-05-15

## Tech Debt

**Monolithic evaluator/orchestrator:**
- Issue: Provider adapters, prompt construction, dataset loading, scoring, CSV writing, CLI parsing, and scratch execution code live in one 3,467-line module.
- Files: `run_eval.py`, `run_single_experiment.py`
- Impact: Small task changes can break unrelated provider, scoring, or CLI behavior; schema and evaluator drift is already visible in `Path_Finder` and `Connect_Icon`.
- Fix approach: Split `run_eval.py` into provider clients, task loading, task schemas, scoring, result writing, and CLI modules. Keep a thin compatibility wrapper for existing notebooks.

**Duplicate few-shot truth sources:**
- Issue: Few-shot examples are defined in both YAML and hard-coded Python data, with comments requiring manual sync after asset renames.
- Files: `few_shot_examples.yaml`, `few_shot_answers.py`, `run_eval.py` (lines 1519-1664), `prepare_few_shot_examples.py`
- Impact: Few-shot prompts can silently use stale answer data or omit examples when file names, task names, or asset extensions diverge.
- Fix approach: Use one generated manifest with image paths and normalized answers. Validate every few-shot entry against assets and `ground_truth.json` before running an experiment.

**Generated artifacts committed with source:**
- Issue: Experiment outputs, error dumps, figures, backup CSVs, temporary CSVs, and `.DS_Store` files are present in the repository.
- Files: `results/`, `error_analysis/`, `figures/`, `.gitignore`, `.gitattributes`
- Impact: Diffs mix source changes with result churn; temporary files such as `results/exp2/openai/gpt-5/results_tmp.csv` and backup files obscure canonical data.
- Fix approach: Move generated outputs to a reproducible artifact directory or external storage. Commit only curated result snapshots with explicit provenance.

**Configuration lives in README examples instead of machine-readable manifests:**
- Issue: Runtime dependencies are documented as a `pip install` command, but no `requirements.txt`, `pyproject.toml`, lockfile, or environment file is present.
- Files: `README.md`, `run_eval.py`, `visualize_results.py`, `compress_few_shot_assets.py`
- Impact: Provider SDK versions, visualization behavior, and image compression tools are not reproducible across machines.
- Fix approach: Add a pinned Python dependency manifest and document external binaries required by image compression.

## Known Bugs

**`run_eval.py` CLI cannot run correctly:**
- Symptoms: `main()` parses `--out-csv` as `args.out_csv` but calls `args.out`; direct script execution also has no `if __name__ == "__main__": main()` guard.
- Files: `run_eval.py` (lines 3214-3303)
- Trigger: Running `python run_eval.py --dataset-root ./captcha_data --types Dice_Count ...`.
- Workaround: Use `run_single_experiment.py` or call `run_eval.run_eval(...)` directly after removing import side effects.

**Importing `run_eval.py` performs live side effects:**
- Symptoms: Import reads `secrets.yaml`, prints the loaded config, and makes a Gemini test request at module scope.
- Files: `run_eval.py` (lines 35-47, 3307-3314), `run_single_experiment.py` (lines 13-22)
- Trigger: Any import of `run_eval`, including `python run_single_experiment.py ...`.
- Workaround: Move all diagnostics and API smoke tests behind explicit CLI commands or `if __name__ == "__main__"` blocks.

**Connect icon task name mismatch:**
- Symptoms: Code and prompts use `Connect_Icon`, while dataset and few-shot directories use `Connect_icon`.
- Files: `run_eval.py` (lines 1384-1406, 1596, 2266-2288), `captcha_data/Connect_icon/ground_truth.json`, `few_shot_assets/Connect_icon/`, `few_shot_examples.yaml`, `few_shot_answers.py`, `prompts_optimized.yaml`
- Trigger: Passing `Connect_icon` is skipped as unsupported; passing `Connect_Icon` looks for a non-existent `captcha_data/Connect_Icon` directory.
- Workaround: Use a task alias map until all references are normalized to one canonical spelling.

**`Path_Finder` scoring accepts wrong answers:**
- Symptoms: Task construction builds classification prompts and stores `correct_index`, but `evaluate_pass1()` treats `Path_Finder` as a multi-select task and compares missing `indices` to missing `indices_gt`.
- Files: `run_eval.py` (lines 2073-2108, 2404-2407, 2493-2530), `captcha_data/Path_Finder/ground_truth.json`
- Trigger: Evaluating the reference/options form of `Path_Finder`.
- Workaround: Add a dedicated `Path_Finder` scoring branch that checks `answer_type == "classify"` and compares `index` to `correct_index`.

**Failure description crashes on multi-select failures:**
- Symptoms: `_describe_failure()` assigns `Missing` but checks `missing`, causing `NameError` on failed `Image_Recognition`, `Select_Animal`, `Unusual_Detection`, or `Path_Finder` cases.
- Files: `run_eval.py` (lines 476-490)
- Trigger: A failed parsed multi-select response reaches error description collection.
- Workaround: Rename the variable consistently and add a regression test that forces one multi-select failure.

**Summary CSV writes only the last task row:**
- Symptoms: The `summary_csv` loop computes each row, but the `f.write(...)` call is outside the loop indentation.
- Files: `run_eval.py` (lines 2927-2934)
- Trigger: Calling `run_eval(..., summary_csv="...")`.
- Workaround: Indent the write call inside the loop and compare row count to `len(agg)`.

**Until-correct exception path can raise secondary errors:**
- Symptoms: The exception handler initializes `meta` but not `parsed` or `e2e`; token logging and reasoning collection can reference unbound locals.
- Files: `run_eval.py` (lines 3084-3125)
- Trigger: Provider inference raises while `collect_tokens` or `collect_reasoning` is enabled.
- Workaround: Initialize `parsed = None` and `e2e = 0.0` before the try block.

**OpenAI CLI default is unsupported by the OpenAI provider:**
- Symptoms: CLI default model is `gpt-4o-mini`, but `OpenAIProvider` only allows `gpt-5-chat-latest`, `gpt-5`, and `gpt-5.1`.
- Files: `run_eval.py` (lines 582-603, 3221-3223)
- Trigger: Running the `run_eval.py` CLI defaults with `--provider openai`.
- Workaround: Align defaults with supported models or make the provider support the documented default.

## Security Considerations

**Tracked secret configuration:**
- Risk: Credential material can be committed and shared because `secrets.yaml` is tracked and `.gitignore` does not exclude secret files.
- Files: `secrets.yaml`, `.gitignore`, `run_eval.py` (lines 120-131, 3225)
- Current mitigation: Not detected.
- Recommendations: Remove tracked secrets, rotate exposed credentials, add `secrets.yaml` and secret patterns to `.gitignore`, and provide a committed `secrets.example.yaml` without values.

**Hard-coded provider credential in source:**
- Risk: A provider API key is embedded directly in code.
- Files: `run_eval.py` (line 3308)
- Current mitigation: Not detected.
- Recommendations: Delete the literal credential, rotate it, and load provider credentials only from environment variables or an untracked local config file.

**Secrets printed to stdout:**
- Risk: Full secret config is printed during import, so terminal logs, notebooks, CI logs, and captured experiment output can expose credentials and pricing config.
- Files: `run_eval.py` (lines 35-47), `run_single_experiment.py` (lines 13-22)
- Current mitigation: Not detected.
- Recommendations: Remove config dumps. Log only non-sensitive provider names and validation status.

**Error analysis captures raw prompts, responses, parsed outputs, reasoning, and ground truth:**
- Risk: If the dataset or model responses include sensitive content, committed CSV/JSON artifacts preserve it.
- Files: `experiments_helper.py` (lines 41-166), `run_eval.py` (lines 2751-2808), `error_analysis/`, `results/error_analysis/`
- Current mitigation: Not detected.
- Recommendations: Treat error analysis as sensitive by default, exclude raw artifacts from git, and add a redaction/export step for shareable summaries.

**CAPTCHA-solving workflow has no use constraints in code:**
- Risk: The toolkit can be used to benchmark or improve CAPTCHA solving against real providers without in-code gating or policy reminders.
- Files: `README.md`, `run_eval.py`, `run_single_experiment.py`
- Current mitigation: The README frames the project as research.
- Recommendations: Add a usage policy, dataset provenance notes, and guardrails for running only on owned or authorized CAPTCHA datasets.

## Performance Bottlenecks

**Sequential provider calls:**
- Problem: Evaluation loops issue one API call per task and retry attempt in series.
- Files: `run_eval.py` (lines 2713-2734, 3072-3136), `run_single_experiment.py`
- Cause: No concurrency, batching, or rate-limit scheduler exists.
- Improvement path: Add a bounded async executor with provider-specific rate limits, retry budgets, and deterministic result ordering.

**Image cache stores both raw bytes and base64 strings:**
- Problem: Up to 512 image entries are cached twice, once as raw bytes and once as base64 text.
- Files: `run_eval.py` (lines 501-550)
- Cause: Cache is item-count-limited rather than memory-limited.
- Improvement path: Add a byte budget, evict by total bytes, and cache derived payloads only when the same image is reused.

**Few-shot context is rebuilt for every task:**
- Problem: Few-shot image path resolution and answer assembly run inside the per-task evaluation loop.
- Files: `run_eval.py` (lines 1519-1664, 2717-2726)
- Cause: Few-shot content is not precomputed per task type.
- Improvement path: Build few-shot payloads once per `(task_type, n_shot, assets_root)` and reuse them across tasks.

**No retry/backoff around transient provider failures:**
- Problem: Provider exceptions are converted into `__ERROR__` raw strings and counted as failed answers.
- Files: `run_eval.py` (lines 750-764, 1044-1048, 1183-1192, 1306-1311)
- Cause: API errors, rate limits, and network timeouts are not classified or retried.
- Improvement path: Add structured provider errors with exponential backoff, retryable/non-retryable classes, and separate reporting for infrastructure failures.

## Fragile Areas

**Task schema and evaluator drift:**
- Files: `run_eval.py`, `captcha_data/*/ground_truth.json`, `prompts_optimized.yaml`
- Why fragile: Every task type is encoded across supported type sets, prompt text, image loading, JSON schema, evaluator logic, visualization labels, and few-shot manifests.
- Safe modification: Change one task type through a table-driven registry that owns aliases, loader, schema, evaluator, prompt defaults, and display family.
- Test coverage: Missing.

**Broad exception swallowing hides data quality problems:**
- Files: `run_eval.py` (lines 103-108, 169-188, 2348-2477), `visualize_results.py` (lines 147-227), `prepare_few_shot_examples.py` (lines 45-76)
- Why fragile: Malformed JSON, missing files, unsupported response shapes, and plotting failures often become `None`, `False`, empty frames, or console warnings.
- Safe modification: Return structured errors with task id, provider, file path, and error category; fail fast for dataset/schema problems.
- Test coverage: Missing.

**Git LFS and tracked metadata interfere with normal repository operations:**
- Files: `.gitattributes`, `.gitignore`, `captcha_data/.DS_Store`, `captcha_data/Click_Order/.DS_Store`, `captcha_data/Image_Matching/.DS_Store`, `captcha_data/Image_Recognition/.DS_Store`, `captcha_data/Patch_Select/.DS_Store`
- Why fragile: `.gitattributes` applies LFS to `captcha_data/**`, while tracked `.DS_Store` files under `captcha_data/` pass through the LFS filter; `git status` fails when the LFS tmp directory is not writable.
- Safe modification: Remove tracked metadata files, repair LFS state, and keep `.DS_Store` ignored before it enters tracked paths.
- Test coverage: Not applicable.

**Notebook-driven workflow bypasses validation:**
- Files: `test.ipynb`, `plot.ipynb`, `test_statistic.ipynb`, `ignore_me.ipynb`, `README.md`
- Why fragile: Operational examples and analysis live in notebooks without automated execution checks.
- Safe modification: Move reusable notebook logic into importable modules and keep notebooks as thin consumers.
- Test coverage: Missing.

## Scaling Limits

**Repository stores large binary datasets in the main workspace:**
- Current capacity: `captcha_data/` is about 600 MB and `few_shot_assets/` is about 37 MB.
- Files: `captcha_data/`, `few_shot_assets/`, `.gitattributes`
- Limit: Clones, LFS pulls, status checks, and mapper runs slow down or fail as binary assets grow.
- Scaling path: Store raw datasets in versioned object storage with checksums and keep only manifests and small fixtures in git.

**Long runs have no checkpointed result stream:**
- Current capacity: `run_eval()` holds aggregate results in memory and writes final CSV output after the task loop.
- Files: `run_eval.py` (lines 2575-2955), `run_single_experiment.py`
- Limit: An interrupted run loses per-task pass/fail rows unless optional token/error logs happen to be enabled.
- Scaling path: Write append-only per-task records atomically, then derive aggregate CSV/JSON summaries after completion.

**Cost control is post-run accounting:**
- Current capacity: Token totals and estimated cost are aggregated after responses arrive.
- Files: `run_eval.py` (lines 148-166, 2659-2667, 2839-2924), `secrets.yaml`
- Limit: Expensive experiment configurations can exceed budget before totals are visible.
- Scaling path: Add preflight task counts, estimated token ranges, provider budget caps, and stop conditions.

**No provider concurrency controls:**
- Current capacity: One process runs one request at a time.
- Files: `run_eval.py` (lines 2713-2734, 3072-3136), `run_single_experiment.py`
- Limit: Full 19-type evaluations with retries scale linearly with task count and timeout.
- Scaling path: Add resumable work queues with per-provider concurrency, rate-limit, and retry policies.

## Dependencies at Risk

**Unpinned Python SDKs:**
- Risk: Provider APIs can change response shapes, streaming behavior, timeout handling, or model names.
- Files: `README.md`, `run_eval.py`
- Impact: `OpenAIProvider`, `AnthropicProvider`, `GeminiProvider`, and `FireworksProvider` can fail at runtime or silently stop collecting token metadata.
- Migration plan: Pin SDK versions, add provider contract tests, and isolate provider-specific payload builders.

**External image compression binaries are implicit:**
- Risk: `zopflipng` and `jpegtran` are required by the compression script but are not listed in README requirements.
- Files: `compress_few_shot_assets.py`, `README.md`
- Impact: `compress_few_shot_assets.py` fails on machines without those binaries.
- Migration plan: Document binary dependencies, detect missing tools before processing, and provide a no-op/report-only mode.

**Visualization depends on optional libraries and loose CSV schemas:**
- Risk: `adjustText` is optional and result CSV columns vary across experiments.
- Files: `visualize_results.py`, `results/`, `exp2_to_exp3_predict.py`
- Impact: Charts can silently omit labels or normalize data incorrectly when schemas shift.
- Migration plan: Define versioned result schemas and validate each CSV before plotting.

**No locked execution environment:**
- Risk: Python, Pillow, pandas, provider SDKs, and matplotlib versions are unconstrained.
- Files: `README.md`, `run_eval.py`, `visualize_results.py`, `compress_few_shot_assets.py`
- Impact: Image MIME handling, CSV parsing, plotting output, and API clients vary across machines.
- Migration plan: Add `pyproject.toml` plus a lockfile and a minimal CI environment.

## Missing Critical Features

**Dataset validation command:**
- Problem: No command validates task directories, aliases, `ground_truth.json`, image references, prompt keys, few-shot assets, and evaluator/schema alignment.
- Files: `captcha_data/`, `few_shot_assets/`, `run_eval.py`, `prompts_optimized.yaml`, `few_shot_examples.yaml`
- Blocks: Reliable full-dataset runs and safe addition of new CAPTCHA task types.

**Automated test suite:**
- Problem: No `test_*.py`, `*_test.py`, or `*.test.*` files are present.
- Files: `run_eval.py`, `run_single_experiment.py`, `visualize_results.py`, `experiments_helper.py`
- Blocks: Refactoring `run_eval.py`, changing provider payloads, and fixing task scoring with confidence.

**Secret-management template:**
- Problem: The repository has tracked `secrets.yaml` but no safe example config or environment-variable loader.
- Files: `secrets.yaml`, `.gitignore`, `run_eval.py`
- Blocks: Secure onboarding and safe CI usage.

**Resume and provenance tracking:**
- Problem: Experiment outputs do not consistently record code revision, dataset revision, prompt revision, seed, SDK versions, or run configuration.
- Files: `run_eval.py`, `run_single_experiment.py`, `results/`, `error_analysis/`
- Blocks: Reproducing published results and resuming interrupted evaluations.

**CI/static checks:**
- Problem: No lint, format, type-check, or smoke-test command is configured.
- Files: `README.md`, `run_eval.py`, `run_single_experiment.py`
- Blocks: Catching CLI argument errors, import side effects, task alias drift, and syntax/runtime regressions before experiments run.

## Test Coverage Gaps

**Task loaders and evaluators:**
- What's not tested: Each supported task type's image loading, prompt construction, JSON schema, and `evaluate_pass1()` behavior.
- Files: `run_eval.py`, `captcha_data/*/ground_truth.json`
- Risk: Invalid scoring can mark wrong answers correct or skip task types entirely.
- Priority: High

**CLI entry points:**
- What's not tested: Argument parsing, output path handling, experiment selection, and import behavior.
- Files: `run_eval.py`, `run_single_experiment.py`
- Risk: Users hit runtime crashes or unintended API calls before experiments start.
- Priority: High

**Provider adapter contracts:**
- What's not tested: Payload shape, image encoding, JSON extraction, token metadata parsing, streaming/non-streaming behavior, and error classification.
- Files: `run_eval.py`
- Risk: SDK changes and model-specific response formats silently corrupt results.
- Priority: High

**Security-sensitive logging and artifacts:**
- What's not tested: Secrets are not printed, raw artifacts are not committed by default, and redaction is applied before sharing.
- Files: `run_eval.py`, `experiments_helper.py`, `results/`, `error_analysis/`
- Risk: Credentials, prompts, model responses, and reasoning traces leak into logs or git.
- Priority: High

**Visualization ingestion:**
- What's not tested: Result CSV schema compatibility across Exp1-Exp4, missing-column handling, and chart generation on a minimal fixture set.
- Files: `visualize_results.py`, `exp2_to_exp3_predict.py`, `results/`
- Risk: Figures can be generated from inconsistent or partially malformed data.
- Priority: Medium

**Few-shot asset integrity:**
- What's not tested: YAML examples, hard-coded answers, compressed assets, and dataset exclusions refer to the same canonical examples.
- Files: `few_shot_examples.yaml`, `few_shot_answers.py`, `few_shot_assets/`, `run_eval.py`
- Risk: Few-shot experiments compare against contaminated or incomplete test pools.
- Priority: Medium

---

*Concerns audit: 2026-05-15*
