# Artifact Submission Guide

This repository snapshot is organized as a reproducible artifact for the
COGNITION USENIX Security 2026 experiments. It is designed for offline, dataset-based
evaluation of CAPTCHA robustness claims against multimodal LLM solvers.

## Scope

The artifact includes:

- source code for baseline, adaptive-attacker, dataset-scope, statistical, and
  visualization workflows;
- CAPTCHA datasets and `ground_truth.json` metadata used by the experiments;
- few-shot assets and prompt configuration files;
- recorded result tables and generated figures used for paper analysis;
- tests and preflight checks that validate task contracts, secret handling,
  attempt logging, manifests, and offline artifact generation.

The artifact excludes:

- local credentials and provider secrets;
- local-only planning and workflow files;
- virtual environments, caches, notebook checkpoints, and system metadata;
- generated paid-run scratch output under `results/local_runs/`.

All workflows are dataset-based. The repository does not contain automation for
attacking live CAPTCHA services.

## Clean Checkout Setup

Use Python 3.10 or newer. The dependency lockfile is managed by `uv`.

```bash
python3 -m pip install uv==0.11.14
uv sync --locked
```

Local credentials are optional for offline validation. If provider-backed runs
are needed, copy the example config and fill in local values:

```bash
cp secrets.example.yaml secrets.yaml
```

Keep `secrets.yaml` local. It is intentionally ignored and excluded from the
submission archive.

## Offline Verification

Run the default test and lint checks:

```bash
uv run pytest
uv run ruff check .
```

Run a minimal offline preflight before any paid provider call:

```bash
uv run python -m cognition.revision_preflight \
  --dataset-root ./captcha_data \
  --types Dice_Count \
  --prompts-file ./prompts_optimized.yaml \
  --output-root ./results/local_runs \
  --run-id local-preflight \
  --provider openai \
  --model gpt-5 \
  --max-per-type 2 \
  --max-attempts 1 \
  --write-report
```

This preflight validates dataset/task filters, prompt hashes, output locations,
and expected request counts without reading `secrets.yaml`.

## Submission Archive

Build a clean tarball from git-tracked files:

```bash
uv run python scripts/build_artifact_package.py
```

To inspect the files that would be included:

```bash
uv run python scripts/build_artifact_package.py --list
```

The archive builder excludes local workflow files, local credentials, caches,
virtual environments, notebook checkpoints, system metadata, and scratch
local outputs. It also writes an `artifact_manifest.json` inside the archive
with the included file list and exclusion policy. The default output path is:

```text
dist/cognition-usenixsec26-artifact.tar.gz
```

## Artifact Map

| Path | Purpose |
| --- | --- |
| `README.md` | Main project overview and experiment commands. |
| `SUBMISSION.md` | Submission-focused setup, verification, and packaging guide. |
| `pyproject.toml`, `uv.lock` | Reproducible Python dependency contract. |
| `cognition/run_eval.py` | Core provider adapters, task loading, scoring, and result writing. |
| `cognition/run_single_experiment.py` | Entrypoints for Experiments 1-4. |
| `cognition/adaptive_*.py` | Adaptive attacker preflight, execution, comparison, and artifacts. |
| `cognition/revision_*.py` | Reproducibility, manifest, preflight, and secret-safety helpers. |
| `cognition/phase*_artifacts.py` | Paper-facing evidence table and artifact generation scripts. |
| `captcha_data/` | Original CAPTCHA datasets and ground-truth metadata. |
| `expanded_captcha_data/` | Expanded evaluation slices and provenance metadata. |
| `few_shot_assets/` | Few-shot image assets grouped by task type. |
| `results/exp1/` through `results/exp4/` | Recorded outputs for the original four experiment families. |
| `results/exp5/` | Paper-facing Exp5 adaptive session-memory evidence and table-ready outputs. |
| `results/sota_baselines/` | SOTA and baseline comparison artifacts. |
| `figures/` | Generated paper figures. |
| `tests/` | Offline regression and artifact-contract tests. |
| `scripts/build_artifact_package.py` | Clean submission archive builder. |

## Claim-to-Artifact Ledger

| Paper evidence area | Primary commands or files |
| --- | --- |
| Original, optimized, retry, and few-shot evaluations | `cognition/run_single_experiment.py`, `cognition/run_eval.py`, `results/exp1/` through `results/exp4/` |
| Adaptive attacker analysis | `cognition/adaptive_preflight.py`, `cognition/adaptive_attacker.py`, `cognition/adaptive_compare.py` |
| Dataset scope and statistical confidence | `cognition/dataset_scope_audit.py`, `cognition/statistical_confidence.py`, `cognition/retry_calibration.py`, `cognition/failure_taxonomy.py`, `cognition/limitations_summary.py` |
| Expanded dataset and provenance checks / Exp5 | `cognition/expanded_dataset.py`, `cognition/expanded_dataset_phase042.py`, `expanded_captcha_data/`, `results/exp5/` |
| SOTA/baseline comparison | `cognition/baseline_strengthening.py`, `baseline_sources/`, `cognition/phase4_artifacts.py`, `results/sota_baselines/` |
| Paper figures and tables | `cognition/visualize_results.py`, `cognition/phase041_artifacts.py`, `cognition/phase042_artifacts.py`, `figures/`, curated `results/` tables |
| Reproducibility and safety contracts | `cognition/revision_preflight.py`, `cognition/revision_artifacts.py`, `cognition/revision_secrets.py`, `tests/` |

## Safety Notes

- Do not commit `secrets.yaml`, `.env`, provider keys, or local credential dumps.
- Do not publish local workflow directories such as `.planning/`,
  `AGENTS.md`, `.codex/`, or `.claude/`.
- Treat provider-backed commands as paid experiments. Run preflight first and
  inspect expected request counts before execution.
- Keep generated reports and manifests free of raw credentials. Provider/model
  labels are acceptable; key material is not.
