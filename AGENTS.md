# Agent Guide: COGNITION Revision Experiments

## Project

This repository supports the COGNITION paper revision work: reproducible CAPTCHA/MLLM security experiments, statistical evidence, adaptive-attacker analysis, benchmark/baseline comparisons, defense-methodology artifacts, and paper-ready figures/tables.

The current GSD project context lives in:

- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/codebase/`
- `.planning/research/`

## Core Value

Produce credible, reproducible revision evidence that directly strengthens the paper's claims about structural CAPTCHA robustness against multimodal LLM attackers.

## Current Focus

Phase 1: Reproducibility and Safety Foundation.

The next planning step is:

```bash
/gsd-discuss-phase 1
```

Phase 1 should establish install, preflight, manifest, attempt-log, secret-safety, and validator contracts before expensive provider runs.

## Working Rules

- Keep interactive discussion with the user in Chinese.
- Keep planning documents, code comments, generated reports, and project artifacts in English unless the user explicitly asks otherwise.
- Keep experiments offline and dataset-based. Do not build live CAPTCHA attack automation or browser automation against real services.
- Treat `secrets.yaml` as sensitive local configuration. Do not print, quote, copy, summarize, or commit credential values.
- Prefer reproducible scripted artifacts over notebook-only manual state.
- Preserve existing experiment semantics unless a phase explicitly plans a migration.
- Avoid broad refactors unless they protect experiment correctness, reproducibility, or artifact integrity.

## Existing Codebase Shape

Primary files:

- `run_eval.py`: monolithic evaluation engine, provider adapters, task loading, scoring, and result writing.
- `run_single_experiment.py`: wrappers for experiments 1-4.
- `exp2_to_exp3_predict.py`: retry prediction and Exp2-to-Exp3 analysis.
- `visualize_results.py`: result loading and figure generation.
- `experiments_helper.py`: error analysis utilities.

Primary artifact directories:

- `captcha_data/`: CAPTCHA datasets and `ground_truth.json` files.
- `few_shot_assets/`: few-shot image assets.
- `results/`: generated result CSV/JSON artifacts.
- `error_analysis/`: generated error reports.
- `figures/`: generated paper figures.

## Known Risks

- `run_eval.py` has import-time side effects and is monolithic.
- Secrets may be tracked or printed by existing code paths; fix this before shareable artifact generation.
- Automated tests are currently absent.
- Task aliases and scorer behavior can drift from dataset names and ground truth.
- Generated outputs are mixed with source and curated artifacts.
- Git LFS and tracked metadata files can interfere with broad `git status`; use path-scoped status checks when possible.

## Roadmap Summary

1. Reproducibility and Safety Foundation
2. Statistical Confidence and Dataset Scope
3. Adaptive Attacker Evidence
4. Benchmark and Baseline Strengthening
5. Defense Methodology Artifacts
6. Paper Artifact QA and Claim Alignment

Each implementation phase should map back to `.planning/REQUIREMENTS.md` and update traceability when complete.

## Before Running Costly Experiments

Confirm:

- Dataset/task filters are validated.
- Prompt and few-shot configuration hashes are recorded.
- Provider/model labels are recorded without secrets.
- Expected request counts and approximate cost are visible.
- Output directory is unique or resumable.
- Per-attempt records will be written before aggregate summaries.

---
*Generated for Codex/GSD project guidance on 2026-05-15.*
