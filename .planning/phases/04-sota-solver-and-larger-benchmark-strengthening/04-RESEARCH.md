# Phase 4: SOTA Solver and Larger Benchmark Strengthening - Research

**Researched:** 2026-05-19
**Domain:** Offline CAPTCHA baseline comparison, external benchmark import validation, and paper-ready comparability evidence
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

Copied verbatim from `.planning/phases/04-sota-solver-and-larger-benchmark-strengthening/04-CONTEXT.md`. [VERIFIED: 04-CONTEXT.md]

### Locked Decisions

### Baseline Coverage Policy

- **D-01:** Include all reviewer/shepherd-named systems in the coverage matrix, especially Halligan and Oedipus, even when artifacts are unavailable or incompatible.
- **D-02:** Every coverage row must have one primary status from the Phase 4 status vocabulary, such as `direct-run`, `adapter-run`, `literature-only`, `approximate`, `incompatible`, or `unavailable`.
- **D-03:** Rows may also carry multiple caveat tags, such as `metric-mismatch`, `dataset-mismatch`, `threat-model-mismatch`, `artifact-unavailable`, or `license-unclear`.
- **D-04:** `literature-only` rows may appear in the main paper-ready table and may include literature-reported metrics, but the output must make clear when those metrics are approximate and not directly comparable.
- **D-05:** `unavailable` and `incompatible` rows require auditable evidence fields before appearing in paper-ready outputs: `status_reason`, checked docs/artifacts, missing items, and last-checked date.

### Smoke Subset Priority

- **D-06:** The first smoke target should prioritize Halligan, Oedipus, or the reviewer/shepherd-named system that best answers the baseline-credibility concern.
- **D-07:** A smoke result can be either a local run, adapter run, or validated import. Direct local execution is useful but is not required for BASE-06 if import validation passes.
- **D-08:** Smoke/import validation must check required fields, metric definitions, task labels, sample counts, and comparability assumptions before the row can support paper-ready outputs.
- **D-09:** The smoke subset strategy should include at least two CAPTCHA categories with semantic or mechanism differences from the existing local 18 classes when feasible.
- **D-10:** New-category identification should prioritize semantic/mechanism differences over exact external taxonomy. Artifacts should record `external_task_label`, `mapped_local_family`, and why a row is a new category or supplemental category.
- **D-11:** For subsets that supplement local data, prioritize Phase 3 underpowered or threshold-sensitive task families.
- **D-12:** If Halligan/Oedipus artifacts cannot support smoke import or local execution, researcher/planner may propose secondary verifiable subset candidates, but execution/import should pause for user confirmation before replacing the named-system smoke target.

### Comparison Table Conservatism

- **D-13:** Use one comprehensive paper-ready comparison table with strong labels rather than separate main tables for every evidence type.
- **D-14:** The table should preserve original reported metric names and values while also providing `normalized_success_rate` when standardization is validated.
- **D-15:** If a metric cannot be standardized reliably, leave normalized fields blank and attach caveats instead of forcing false comparability.
- **D-16:** Every row must include `directly_comparable`. Rows with `directly_comparable=false` must include `comparability_caveat`, and paper outputs should expose this through symbols, notes, or footnotes.
- **D-17:** Literature-only, non-directly-comparable numbers may be discussed as approximate comparisons when the approximation basis, metric mismatch, and dataset mismatch are explicit.
- **D-18:** Every row must include `system_class`, with values such as `off_the_shelf_mllm_api`, `specialized_solver`, `benchmark_dataset`, and `hybrid_or_unknown`.

### Artifact and Schema Shape

- **D-19:** Add an independent `phase4_artifacts.py` module with strict Pydantic schemas for baseline coverage rows, comparison rows, external import validation rows, and paper-table rows.
- **D-20:** Use one central Phase 4 CLI with multiple subcommands for coverage, import/validation, comparison table generation, and notes generation. Keep schemas and helper logic outside the CLI so it does not become a new monolith.
- **D-21:** External baseline/import validator failures may enter the table with warnings/caveats, but unverified fields must not be marked directly comparable or used for strong claims.
- **D-22:** Continue writing Phase 4 outputs under `results/revision/<run_id>/`, including coverage matrix, import diagnostics, comparison table, paper-ready CSV/JSON, and short paper notes.
- **D-23:** Generate concise paper notes/prose summarizing direct/adapter/literature-only rows, unavailable/incompatible rows, non-comparable rows, and approximate comparison basis. Do not generate a full manuscript section in Phase 4.

### External System Research Scope

- **D-24:** Beyond Halligan and Oedipus, researcher may include at most two highly relevant additional systems.
- **D-25:** Prefer additional systems that Halligan or Oedipus themselves use as comparison baselines.
- **D-26:** For every runnable or importable candidate, researcher must record license, data terms, artifact availability, and data-use constraints.
- **D-27:** If license or data-use constraints are unclear, the candidate cannot be treated as `direct-run` or `adapter-run`; it must remain `literature-only` or warning/caveated.
- **D-28:** Live-service automation oriented solvers must not be run, adapted, or implemented. If public data or public results are available, Phase 4 may import those results with clear caveats.
- **D-29:** Prioritize systems and benchmarks from 2023-2026. Halligan and Oedipus are covered regardless of year. Older systems should be included only when reviewer/shepherd-named or used as comparison baselines by Halligan/Oedipus.

### Claude's Discretion

- The planner may choose exact Phase 4 schema class names and CLI subcommand names, provided the locked fields and validation semantics above are preserved.
- The planner may choose exact output filenames under `results/revision/<run_id>/`, provided outputs include machine-readable CSV/JSON and paper-facing notes where relevant.
- The researcher may propose secondary smoke candidates if named-system artifacts are not usable, but replacement requires user confirmation before execution/import.
- The planner may decide how to visually encode `directly_comparable=false` in paper-ready tables, provided it remains visible to readers.

### Deferred Ideas (OUT OF SCOPE)

None - discussion stayed within Phase 4 scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BASE-01 | Researcher can create a benchmark coverage matrix mapping local CAPTCHA families to reviewer-cited larger datasets and specialized solver baselines. | Use strict `BaselineCoverageRow` records with local `task_type`, local `task_family`, raw external labels, semantic/mechanism mapping, source URL, status, caveats, and checked-date fields. [VERIFIED: REQUIREMENTS.md; VERIFIED: 04-CONTEXT.md; VERIFIED: visualize_results.py] |
| BASE-02 | Baseline comparison rows include Halligan, Oedipus, and other relevant dedicated CAPTCHA solver or benchmark systems where available. | Include Halligan and Oedipus unconditionally; add at most two Halligan-used baselines, recommended as `VTTSolver` and `PhishDecloaker` for specialized-solver breadth, while leaving other Halligan baselines as source notes unless the user expands scope. [VERIFIED: 04-CONTEXT.md; CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf] |
| BASE-03 | Each baseline row distinguishes solver architecture, threat model, dataset scale, CAPTCHA families, reported metrics, artifact availability, latency/cost coverage, failure-mode analysis, and defense-methodology relevance. | Halligan exposes architecture, benchmark scale, baseline rows, cost/latency, and failure classes; Oedipus exposes DSL/CoT architecture, four original task types, model baselines, cost, and artifact caveats; the Phase 4 schema should require these fields or explicit `unknown` reasons. [CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf; CITED: https://arxiv.org/abs/2405.07496; CITED: https://geleideng.github.io/publication/oedipus/oedipus.pdf] |
| BASE-04 | Baseline comparisons label each row as direct-run, adapter-run, literature-only, approximate, incompatible, or unavailable. | Encode the primary status as an enum and caveat tags as a separate list/string field; status must drive whether `normalized_success_rate` and `directly_comparable` can be set. [VERIFIED: 04-CONTEXT.md] |
| BASE-05 | External baseline or larger-dataset imports validate required fields, metric definitions, task labels, sample counts, and comparability assumptions before appearing in paper-ready outputs. | Add `ExternalImportValidationRow` and fail paper-table generation if required fields are missing unless the row is explicitly caveated as non-comparable literature/context. [VERIFIED: 04-CONTEXT.md; VERIFIED: phase3_artifacts.py; VERIFIED: extended_dataset_manifest.py] |
| BASE-06 | The framework can run or import at least one smoke subset for a compatible larger external benchmark or baseline comparison when artifacts are available and feasible within the shepherding timeline. | Recommended first smoke is a validated Halligan import of at least two Table 4 categories with different mechanisms; direct Halligan offline execution requires Docker daemon and Pixi, which are not currently ready in this environment. [VERIFIED: 04-CONTEXT.md; CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf; VERIFIED: environment probe] |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- Interactive discussion with the user must stay in Chinese, while planning documents, code comments, generated reports, and project artifacts remain in English. [VERIFIED: AGENTS.md]
- Experiments must remain offline and dataset-based; do not build live CAPTCHA attack automation or browser automation against real services. [VERIFIED: AGENTS.md]
- `secrets.yaml` is sensitive local configuration and must not be read, printed, summarized, copied, or committed. [VERIFIED: AGENTS.md]
- Prefer reproducible scripted artifacts over notebook-only manual state. [VERIFIED: AGENTS.md]
- Preserve existing experiment semantics unless a phase explicitly plans a migration. [VERIFIED: AGENTS.md]
- Avoid broad refactors unless they protect experiment correctness, reproducibility, or artifact integrity. [VERIFIED: AGENTS.md]
- `CLAUDE.md` was not present in the project root during research, so there are no additional CLAUDE.md directives to include. [VERIFIED: filesystem check]
- Project-defined skills under `.claude/skills/` and `.agents/skills/` were absent. [VERIFIED: filesystem check]

## Summary

Phase 4 should be planned as an offline, auditable comparison layer, not a solver-reimplementation phase. [VERIFIED: 04-CONTEXT.md; VERIFIED: PROJECT.md] The critical planning move is to separate four evidence levels: local COGNITION API-run rows, external validated-import rows, literature-only contextual rows, and unavailable/incompatible rows with auditable reasons. [VERIFIED: 04-CONTEXT.md; VERIFIED: REQUIREMENTS.md]

Halligan is the strongest first smoke/import target because it has primary paper results, an offline benchmark artifact, implementation artifact, MIT license record, concrete benchmark scale, baseline comparisons, cost/latency numbers, and failure-mode categories. [CITED: https://www.usenix.org/conference/usenixsecurity25/presentation/teoh; CITED: https://zenodo.org/records/15709075; CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf] Oedipus must appear in the matrix, but the currently verified sources support a literature-only row first because the paper says source code is shared on request to avoid misuse and the directly downloadable dataset/code artifact URL was not found in this research pass. [CITED: https://arxiv.org/abs/2405.07496; CITED: https://geleideng.github.io/publication/oedipus/oedipus.pdf; VERIFIED: web search]

**Primary recommendation:** Build `phase4_artifacts.py` plus one `baseline_strengthening.py` CLI with subcommands `coverage`, `validate-import`, `build-table`, and `notes`; make Halligan validated import the first BASE-06 smoke path, and treat all non-matched rows as visibly non-comparable unless validation proves otherwise. [VERIFIED: 04-CONTEXT.md; VERIFIED: phase3_artifacts.py; VERIFIED: extended_dataset_manifest.py; CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| External source metadata inventory | Offline analysis CLI | Local file storage | Source records are curated/imported metadata, not model inference or provider calls. [VERIFIED: 04-CONTEXT.md; VERIFIED: AGENTS.md] |
| Baseline coverage matrix | Offline analysis CLI | Paper artifact layer | The coverage matrix maps local task families to external systems and statuses before paper tables consume it. [VERIFIED: REQUIREMENTS.md; VERIFIED: 04-CONTEXT.md] |
| Import validation | Offline analysis CLI | Pydantic schema module | Required fields, metric definitions, sample counts, and comparability assumptions must be validated before output use. [VERIFIED: BASE-05 in REQUIREMENTS.md; VERIFIED: phase3_artifacts.py] |
| Halligan/Oedipus smoke evidence | Offline import or offline local artifact runner | External artifact boundary | Direct local Halligan execution is optional; validated import satisfies the locked decision if validation passes. [VERIFIED: 04-CONTEXT.md; CITED: https://secartifacts.github.io/usenixsec2025/appendix-files/sec25cycle2ae-final17.pdf] |
| Paper-ready comparison table | Paper artifact layer | Offline analysis CLI | The table must expose source type, system class, status, caveats, and direct-comparability flags to readers. [VERIFIED: 04-CONTEXT.md] |
| Concise paper notes | Paper artifact layer | Offline analysis CLI | Notes summarize caveated evidence and should not become a full manuscript section in Phase 4. [VERIFIED: 04-CONTEXT.md] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11.5 installed; project requires `>=3.10` | Run root-level analysis scripts and tests. | Existing project is Python-only and `pyproject.toml` sets `requires-python = ">=3.10"`. [VERIFIED: environment probe; VERIFIED: pyproject.toml] |
| `pydantic` | 2.13.4 installed and pinned | Strict Phase 4 row schemas and enum validation. | Phase 3 already uses Pydantic v2 `BaseModel`, `ConfigDict(extra="forbid")`, `Field`, and `field_validator` for generated artifact contracts. [VERIFIED: environment probe; VERIFIED: pyproject.toml; VERIFIED: phase3_artifacts.py] |
| `pandas` | 1.5.3 installed and pinned | Load local result CSVs and optional table joins. | Existing result analysis and visualization already depend on pandas, but Phase 4 writers should still use explicit schema validation before table output. [VERIFIED: environment probe; VERIFIED: pyproject.toml; VERIFIED: visualize_results.py] |
| Python `csv` and `json` stdlib | Python 3.11.5 stdlib | Emit machine-readable CSV/JSON outputs. | Phase 3 artifact writers use stdlib CSV/JSON with Pydantic model dumps, which is sufficient for Phase 4. [VERIFIED: phase3_artifacts.py] |
| `revision_artifacts.revision_run_dir()` | Local module | Keep outputs under `results/revision/<run_id>/` with safe run-id validation. | Phase 1 established this helper and Phase 3 CLIs reuse it for default output paths. [VERIFIED: revision_artifacts.py; VERIFIED: dataset_scope_audit.py; VERIFIED: extended_dataset_manifest.py] |

### Supporting

| Library/Tool | Version | Purpose | When to Use |
|--------------|---------|---------|-------------|
| `pytest` | 9.0.3 installed and pinned | Offline tests for schemas, import validators, status/caveat rules, and notes output. | Use for Phase 4 unit/regression tests. [VERIFIED: environment probe; VERIFIED: pyproject.toml; VERIFIED: tests/] |
| `ruff` | 0.15.13 installed and pinned | Lint new Phase 4 modules. | Use `uv run ruff check phase4_artifacts.py baseline_strengthening.py tests/test_phase4_*.py`. [VERIFIED: environment probe; VERIFIED: pyproject.toml] |
| `uv` | 0.11.14 installed | Reproducible local commands. | Use existing project command style: `uv run pytest` and `uv run python`. [VERIFIED: environment probe; VERIFIED: TESTING.md] |
| Docker CLI | 29.1.5 installed; daemon unavailable | Optional Halligan offline benchmark direct run. | Only needed if the user approves direct Halligan artifact execution; current daemon probe failed. [VERIFIED: environment probe; CITED: https://secartifacts.github.io/usenixsec2025/appendix-files/sec25cycle2ae-final17.pdf] |
| Pixi | Not installed | Optional Halligan environment setup. | Halligan AE recommends Pixi for setup, so direct execution is blocked until installed or bypassed. [VERIFIED: environment probe; CITED: https://secartifacts.github.io/usenixsec2025/appendix-files/sec25cycle2ae-final17.pdf] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `baseline_strengthening.py` root CLI | Notebook-only baseline table | Notebook-only state would violate reproducible scripted artifact rules and make paper rows hard to validate. [VERIFIED: AGENTS.md; VERIFIED: TESTING.md] |
| Validated import first | Full Halligan or Oedipus reimplementation | Full reproduction is higher risk and not required for BASE-06 when import validation passes. [VERIFIED: 04-CONTEXT.md] |
| Strict Pydantic schemas | Loose dictionaries and ad hoc CSV columns | Loose rows risk false comparability and schema drift, which Phase 3 already avoided with strict row models. [VERIFIED: phase3_artifacts.py; VERIFIED: CONCERNS.md] |
| Halligan/Oedipus-first smoke | CAPTURE or arbitrary newer benchmark first | Locked decisions require Halligan/Oedipus priority; secondary replacement requires user confirmation. [VERIFIED: 04-CONTEXT.md; CITED: https://arxiv.org/abs/2512.11323] |

**Installation:**

No new Python package is required for the recommended Phase 4 implementation. [VERIFIED: pyproject.toml; VERIFIED: phase3_artifacts.py] If direct Halligan artifact execution is later approved, plan a separate environment step for Docker daemon readiness and Pixi installation rather than making it a default Phase 4 dependency. [VERIFIED: environment probe; CITED: https://secartifacts.github.io/usenixsec2025/appendix-files/sec25cycle2ae-final17.pdf]

```bash
uv sync
uv run pytest tests/test_phase4_artifacts.py tests/test_baseline_strengthening.py -q
```

**Version verification:** Python, `pydantic`, `pandas`, `pytest`, `ruff`, `uv`, Docker CLI, Pixi, and curl versions/availability were probed on 2026-05-19. [VERIFIED: environment probe]

## External Baseline And Benchmark Findings

### Halligan

| Field | Finding |
|-------|---------|
| Primary sources | USENIX Security 2025 page, paper PDF, USENIX artifact appendix, Zenodo artifact record. [CITED: https://www.usenix.org/conference/usenixsecurity25/presentation/teoh; CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf; CITED: https://secartifacts.github.io/usenixsec2025/appendix-files/sec25cycle2ae-final17.pdf; CITED: https://zenodo.org/records/15709075] |
| Architecture | Halligan is an agentic VLM solver that formulates visual CAPTCHA challenges as search/optimization problems with tools for interaction, ranking/comparison, and visual enhancement. [CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf] |
| Benchmark scale | The paper reports 26 visual CAPTCHA types and 2,600 benchmark challenges. [CITED: https://www.usenix.org/conference/usenixsecurity25/presentation/teoh; CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf] |
| Reported metric | Halligan reports 1,577/2,600 solved, or 60.7%, on the closed-world benchmark. [CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf] |
| Baselines used | Halligan compares against GUI Agent, WebVoyager, ShowUI, VTTSolver, GeeSolver, and PhishDecloaker. [CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf] |
| Artifact availability | Zenodo record lists `benchmark.zip` and `halligan.zip`; the record reports MIT License. [CITED: https://zenodo.org/records/15709075] |
| Direct-run feasibility | The AE appendix recommends Linux, Docker, Docker Compose, and Pixi; current local environment has Docker CLI but no daemon and no Pixi. [CITED: https://secartifacts.github.io/usenixsec2025/appendix-files/sec25cycle2ae-final17.pdf; VERIFIED: environment probe] |
| Phase 4 status | Start as `literature-only` validated import; upgrade to `direct-run` or `adapter-run` only after artifact download, checksum/license verification, and offline-only execution review. [VERIFIED: 04-CONTEXT.md; CITED: https://zenodo.org/records/15709075] |

### Oedipus

| Field | Finding |
|-------|---------|
| Primary sources | arXiv page and author-hosted CCS 2025 PDF. [CITED: https://arxiv.org/abs/2405.07496; CITED: https://geleideng.github.io/publication/oedipus/oedipus.pdf] |
| Architecture | Oedipus decomposes reasoning CAPTCHA tasks into DSL-guided sub-steps and uses Chain-of-Thought style multimodal LLM solving. [CITED: https://arxiv.org/abs/2405.07496] |
| Reported metric | arXiv reports an average success rate of 63.5%; the CCS PDF/search extract reports Claude-3.7 Oedipus average 73.8% and GPT-4V/GPT-4o/Gemini/miniGPT-4/VTT comparisons. [CITED: https://arxiv.org/abs/2405.07496; CITED: https://geleideng.github.io/publication/oedipus/oedipus.pdf] |
| Dataset scale | The CCS PDF/search extract reports four original reasoning CAPTCHA types with 100 samples each, plus later-2023 transfer tasks. [CITED: https://geleideng.github.io/publication/oedipus/oedipus.pdf] |
| Artifact availability | The CCS PDF/search extract says the complete dataset is open-sourced and source code is shared upon request to avoid misuse; this research pass did not locate a direct artifact URL. [CITED: https://geleideng.github.io/publication/oedipus/oedipus.pdf; VERIFIED: web search] |
| Phase 4 status | Include unconditionally as `literature-only` with `artifact-unavailable` or `artifact-unclear` caveat until dataset/code location and license are verified. [VERIFIED: 04-CONTEXT.md; VERIFIED: web search] |

### Recommended Additional Systems

| System | Why Include | Starting Status |
|--------|-------------|-----------------|
| VTTSolver | Halligan uses VTTSolver as a specialized visual reasoning CAPTCHA baseline, and Oedipus also uses VTT-style reasoning CAPTCHA comparison context. [CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf; CITED: https://geleideng.github.io/publication/oedipus/oedipus.pdf] | `literature-only` unless source artifact/license is separately verified. [VERIFIED: 04-CONTEXT.md] |
| PhishDecloaker | Halligan uses PhishDecloaker as a mainstream visual CAPTCHA baseline covering reCAPTCHA v2, hCaptcha, slider, and rotation-style challenges. [CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf] | `literature-only` or `incompatible` by local task family unless artifact and offline-safe data are verified. [VERIFIED: 04-CONTEXT.md] |

### Larger Benchmark Candidate

| Candidate | Finding | Phase 4 Use |
|-----------|---------|-------------|
| Halligan offline benchmark | Zenodo provides a benchmark artifact; Halligan paper reports 26 types and 2,600 challenges. [CITED: https://zenodo.org/records/15709075; CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf] | First validated-import smoke source and optional later direct-run source. [VERIFIED: 04-CONTEXT.md] |
| Upstream Open CaptchaWorld dataset | arXiv reports 20 CAPTCHA types and 225 CAPTCHAs; Hugging Face currently shows 862 rows under Apache-2.0; GitHub README reports 20 types and MIT repo license, plus update notes that the benchmark size was increased. [CITED: https://arxiv.org/abs/2505.24878; CITED: https://huggingface.co/datasets/OpenCaptchaWorld/Open_CaptchaWorld; CITED: https://github.com/MetaAgentX/OpenCaptchaWorld] | Compatible secondary smoke candidate for supplemental/new-category import after Halligan/Oedipus priority is handled; license mismatch between repo and dataset card should be caveated until resolved. [VERIFIED: 04-CONTEXT.md; CITED: https://huggingface.co/datasets/OpenCaptchaWorld/Open_CaptchaWorld; CITED: https://github.com/MetaAgentX/OpenCaptchaWorld] |
| CAPTURE | arXiv reports 4 main CAPTCHA types, 25 sub-types, and 31 vendors for LVLM CAPTCHA resolving. [CITED: https://arxiv.org/abs/2512.11323] | Do not plan as default smoke because artifact availability was not verified and D-24/D-25 prefer Halligan/Oedipus-related systems. [VERIFIED: 04-CONTEXT.md; CITED: https://arxiv.org/abs/2512.11323] |

## Architecture Patterns

### System Architecture Diagram

```text
Source metadata files / hand-curated literature rows
        |
        v
baseline_strengthening.py coverage
        |
        v
phase4_artifacts.py strict coverage rows
        |
        +--> unavailable/incompatible evidence audit
        |
        v
baseline_strengthening.py validate-import
        |
        +--> required field checks
        +--> metric definition checks
        +--> sample count checks
        +--> task/family mapping checks
        +--> license/data-use checks
        |
        v
comparison row builder
        |
        +--> if metric compatible -> normalized_success_rate allowed
        +--> if not compatible -> caveats and directly_comparable=false
        |
        v
paper table generator + notes generator
        |
        v
results/revision/<run_id>/
  coverage_matrix.csv/json
  external_import_diagnostics.csv/json
  baseline_comparison.csv/json
  paper_baseline_table.csv/json
  baseline_notes.md
```

This architecture keeps Phase 4 offline and artifact-oriented while letting later direct-run evidence enter only after validation. [VERIFIED: AGENTS.md; VERIFIED: 04-CONTEXT.md]

### Recommended Project Structure

```text
captcha/
├── phase4_artifacts.py              # strict schemas, enums, CSV/JSON writers
├── baseline_strengthening.py        # central Phase 4 CLI with subcommands
├── tests/
│   ├── test_phase4_artifacts.py
│   └── test_baseline_strengthening.py
└── results/revision/<run_id>/       # generated Phase 4 outputs
    ├── coverage_matrix.csv
    ├── coverage_matrix.json
    ├── external_import_diagnostics.csv
    ├── external_import_diagnostics.json
    ├── baseline_comparison.csv
    ├── baseline_comparison.json
    ├── paper_baseline_table.csv
    ├── paper_baseline_table.json
    └── baseline_notes.md
```

This mirrors the current flat root-level module layout and Phase 3 output convention. [VERIFIED: STRUCTURE.md; VERIFIED: CONVENTIONS.md; VERIFIED: 04-CONTEXT.md]

### Pattern 1: Strict Rows With Enums

**What:** Define schema versions, allowed status/caveat enums, and `extra="forbid"` Pydantic models for every Phase 4 row. [VERIFIED: phase3_artifacts.py]

**When to use:** Use for coverage, import diagnostics, comparison, and paper table rows before any CSV/JSON write. [VERIFIED: phase3_artifacts.py; VERIFIED: 04-CONTEXT.md]

**Example:**

```python
from pydantic import BaseModel, ConfigDict, Field, field_validator

BASELINE_COVERAGE_SCHEMA_VERSION = "cognition.revision.baseline_coverage.v1"
ALLOWED_BASELINE_STATUSES = {
    "direct-run",
    "adapter-run",
    "literature-only",
    "approximate",
    "incompatible",
    "unavailable",
}


class BaselineCoverageRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = BASELINE_COVERAGE_SCHEMA_VERSION
    run_id: str
    system_name: str
    system_class: str
    external_task_label: str
    mapped_local_family: str
    primary_status: str
    caveat_tags: list[str] = Field(default_factory=list)
    status_reason: str
    checked_sources: list[str]
    last_checked_date: str

    @field_validator("primary_status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in ALLOWED_BASELINE_STATUSES:
            raise ValueError(f"primary_status must be one of {sorted(ALLOWED_BASELINE_STATUSES)}")
        return value
```

Source pattern: `phase3_artifacts.py` uses schema constants, allowed enum sets, `ConfigDict(extra="forbid")`, and field validators. [VERIFIED: phase3_artifacts.py]

### Pattern 2: Validation Before Paper Table Inclusion

**What:** Paper rows should be generated only from validation rows that record required-field status, metric-definition status, sample-count status, mapping status, and comparability status. [VERIFIED: BASE-05 in REQUIREMENTS.md; VERIFIED: 04-CONTEXT.md]

**When to use:** Use before writing `paper_baseline_table.csv/json`; failed rows may appear only with warnings/caveats and `directly_comparable=false`. [VERIFIED: 04-CONTEXT.md]

**Example:**

```python
def paper_row_from_comparison(row: BaselineComparisonRow) -> PaperBaselineRow:
    directly_comparable = (
        row.validation_status == "passed"
        and row.metric_standardization_status == "standardized"
        and row.dataset_mapping_confidence == "high"
        and not row.blocking_caveats
    )
    return PaperBaselineRow(
        run_id=row.run_id,
        system_name=row.system_name,
        system_class=row.system_class,
        primary_status=row.primary_status,
        reported_metric_name=row.reported_metric_name,
        reported_metric_value=row.reported_metric_value,
        normalized_success_rate=(
            row.normalized_success_rate if directly_comparable else None
        ),
        directly_comparable=directly_comparable,
        comparability_caveat="" if directly_comparable else row.comparability_caveat,
    )
```

Source pattern: Phase 3 validation rows and comparison rows keep original, validation-slice, and caveat fields separate instead of collapsing evidence. [VERIFIED: extended_dataset_manifest.py; VERIFIED: phase3_artifacts.py]

### Pattern 3: Central CLI With Thin Subcommands

**What:** Put CLI parsing and subcommand routing in `baseline_strengthening.py`, while schema definitions and reusable row builders live in `phase4_artifacts.py`. [VERIFIED: 04-CONTEXT.md; VERIFIED: dataset_scope_audit.py; VERIFIED: extended_dataset_manifest.py]

**When to use:** Use for `coverage`, `validate-import`, `build-table`, and `notes`. [VERIFIED: 04-CONTEXT.md]

**Example:**

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Phase 4 baseline coverage, import validation, and paper table artifacts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    coverage = subparsers.add_parser("coverage")
    coverage.add_argument("--input-sources", required=True)
    coverage.add_argument("--output-root", default="./results/revision")
    coverage.add_argument("--run-id", required=True)
    # validate-import, build-table, and notes follow the same output-root/run-id convention.
    return parser
```

Source pattern: Existing Phase 3 CLIs define `build_parser()`, default `--output-root ./results/revision`, required `--run-id`, and JSON-safe summaries. [VERIFIED: dataset_scope_audit.py; VERIFIED: extended_dataset_manifest.py]

### Anti-Patterns to Avoid

- **Generic-prompt surrogate baseline:** Do not label a local off-the-shelf MLLM prompt as Halligan, Oedipus, VTTSolver, or PhishDecloaker. [VERIFIED: 04-CONTEXT.md; VERIFIED: PITFALLS.md]
- **Forced metric normalization:** Do not populate `normalized_success_rate` when denominator, task definition, or metric semantics are not validated. [VERIFIED: 04-CONTEXT.md]
- **Silent task mapping:** Do not map `arkose/dice_match`, `Geetest-Gobang`, or `OpenCaptchaWorld/Hold_Button` to local families without preserving the raw label and mapping rationale. [CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf; CITED: https://github.com/MetaAgentX/OpenCaptchaWorld; VERIFIED: visualize_results.py]
- **Live-service adapter work:** Do not implement adapters that target real CAPTCHA services, 2Captcha, vendor demos, or production endpoints. [VERIFIED: AGENTS.md; VERIFIED: 04-CONTEXT.md]
- **License-blind imports:** Do not mark rows `direct-run` or `adapter-run` until license and data-use terms are recorded. [VERIFIED: 04-CONTEXT.md]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Row schema validation | Ad hoc dictionaries and nullable columns everywhere | Pydantic v2 models in `phase4_artifacts.py` | Enums and required fields must be enforced before paper rows are generated. [VERIFIED: phase3_artifacts.py; VERIFIED: 04-CONTEXT.md] |
| Output directory safety | Manual string concatenation for run paths | `revision_artifacts.revision_run_dir()` | Existing helper validates run ids and root containment. [VERIFIED: revision_artifacts.py] |
| External solver reproduction | A partial local clone of Halligan/Oedipus behavior | Validated import first, direct run only after artifact/license/environment checks | Phase 4 requires fair comparison hooks, not a false reimplementation. [VERIFIED: 04-CONTEXT.md; VERIFIED: PITFALLS.md] |
| Metric conversion | Force every reported metric into a success rate | Preserve original metric plus `normalized_success_rate` only when validated | Avoids false head-to-head comparisons. [VERIFIED: 04-CONTEXT.md] |
| Dataset conversion | Manual copy/rename of external files | Manifest-driven import with raw labels, mapped labels, sample counts, exclusions, and caveats | Prevents invalid larger-dataset claims. [VERIFIED: extended_dataset_manifest.py; VERIFIED: PITFALLS.md] |
| Paper prose | Manually written table notes disconnected from generated rows | `notes` subcommand from validated CSV/JSON rows | Keeps paper-facing notes tied to auditable artifacts. [VERIFIED: limitations_summary.py; VERIFIED: 04-CONTEXT.md] |

**Key insight:** The hard part is not calculating a percentage; it is proving that two percentages mean the same thing under task, threat-model, artifact, and metric constraints. [VERIFIED: 04-CONTEXT.md; VERIFIED: PITFALLS.md]

## Common Pitfalls

### Pitfall 1: Apples-To-Oranges SOTA Claims

**What goes wrong:** A row compares COGNITION API-prompt results against Halligan or Oedipus as if architectures, datasets, interaction channels, and feedback are matched. [VERIFIED: PITFALLS.md; CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf; CITED: https://arxiv.org/abs/2405.07496]

**Why it happens:** Halligan is an agentic VLM search solver with tools and interactive benchmark conditions, while Oedipus uses a DSL/CoT decomposition for reasoning CAPTCHAs. [CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf; CITED: https://arxiv.org/abs/2405.07496]

**How to avoid:** Require `system_class`, `threat_model`, `primary_status`, `directly_comparable`, and `comparability_caveat` on every paper row. [VERIFIED: 04-CONTEXT.md]

**Warning signs:** `normalized_success_rate` is filled but `metric_definition`, `sample_count`, or `mapping_confidence` is blank. [VERIFIED: 04-CONTEXT.md]

### Pitfall 2: Treating Literature-Only Rows As Reproduced Results

**What goes wrong:** The paper table includes Halligan/Oedipus numbers without showing that they are imported from literature rather than locally reproduced. [VERIFIED: 04-CONTEXT.md]

**Why it happens:** Literature rows are useful for reviewer response, but they can look like matched experiments unless the source/status fields are visible. [VERIFIED: 04-CONTEXT.md]

**How to avoid:** Include `evidence_source_type`, `source_url`, `primary_status`, `artifact_availability`, `last_checked_date`, and `checked_sources` in rows and notes. [VERIFIED: 04-CONTEXT.md]

**Warning signs:** Paper-ready table has a single "accuracy" column with no status/caveat columns. [VERIFIED: 04-CONTEXT.md]

### Pitfall 3: Halligan Direct-Run Scope Creep

**What goes wrong:** The plan defaults to running Halligan's browser-based solver stack rather than importing validated offline benchmark results first. [CITED: https://secartifacts.github.io/usenixsec2025/appendix-files/sec25cycle2ae-final17.pdf; VERIFIED: 04-CONTEXT.md]

**Why it happens:** Halligan has an artifact package, but its AE setup includes Docker/Pixi and browser interaction against an offline benchmark. [CITED: https://secartifacts.github.io/usenixsec2025/appendix-files/sec25cycle2ae-final17.pdf]

**How to avoid:** Make validated import the Phase 4 default; make direct-run a later optional task gated by environment readiness, artifact checksum/license inspection, and offline-only confirmation. [VERIFIED: 04-CONTEXT.md; VERIFIED: environment probe]

**Warning signs:** A plan requires Pixi/Docker daemon setup before any BASE-06 evidence exists. [VERIFIED: environment probe; VERIFIED: 04-CONTEXT.md]

### Pitfall 4: Oedipus Artifact Ambiguity

**What goes wrong:** Oedipus is marked `adapter-run` even though direct code/data artifact access was not verified. [CITED: https://geleideng.github.io/publication/oedipus/oedipus.pdf; VERIFIED: web search]

**Why it happens:** The paper reports dataset/code availability language, but this research pass did not locate a direct artifact URL and source code may require author request. [CITED: https://geleideng.github.io/publication/oedipus/oedipus.pdf; VERIFIED: web search]

**How to avoid:** Start Oedipus as `literature-only` with `artifact-unavailable` or `artifact-unclear`; add `missing_items` and `last_checked_date`. [VERIFIED: 04-CONTEXT.md]

**Warning signs:** A planner proposes an Oedipus local smoke run without a source URL, license, checksum, and reproducible input manifest. [VERIFIED: 04-CONTEXT.md]

### Pitfall 5: Larger Dataset Label Drift

**What goes wrong:** Upstream Open CaptchaWorld or Halligan benchmark labels are mapped into local families without preserving differences such as temporal hold, slider/drag, or vendor-specific interaction semantics. [VERIFIED: dataset_scope_audit.py; CITED: https://github.com/MetaAgentX/OpenCaptchaWorld; CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf]

**Why it happens:** Local task behavior is encoded across dataset directories, aliases, prompts, schemas, scoring, and visualization family metadata. [VERIFIED: STRUCTURE.md; VERIFIED: CONCERNS.md; VERIFIED: visualize_results.py]

**How to avoid:** Preserve `external_task_label`, `mapped_local_task_type`, `mapped_local_family`, `mapping_confidence`, `new_or_supplemental_category_reason`, and `excluded_sample_reason`. [VERIFIED: 04-CONTEXT.md; VERIFIED: extended_dataset_manifest.py]

**Warning signs:** Row counts from source manifest and output table do not match without an exclusion report. [VERIFIED: extended_dataset_manifest.py]

## Code Examples

Verified patterns from local sources:

### CSV/JSON Writer Pattern

```python
def write_baseline_coverage(
    rows: list[BaselineCoverageRow],
    output_csv: Path,
    output_json: Path,
) -> tuple[Path, Path]:
    write_csv(output_csv, BaselineCoverageRow.model_fields, rows)
    write_json(output_json, BASELINE_COVERAGE_SCHEMA_VERSION, rows)
    return output_csv, output_json
```

Source pattern: Phase 3 writer helpers accept model fields and model rows, then emit CSV and JSON with schema version. [VERIFIED: phase3_artifacts.py]

### Default Output Path Pattern

```python
run_dir = revision_run_dir(args.output_root, args.run_id)
coverage_csv = run_dir / "coverage_matrix.csv"
coverage_json = run_dir / "coverage_matrix.json"
```

Source pattern: Phase 3 CLIs use `revision_run_dir(args.output_root, args.run_id)` and default filenames under the run directory. [VERIFIED: dataset_scope_audit.py; VERIFIED: extended_dataset_manifest.py; VERIFIED: revision_artifacts.py]

### Secret-Safe CLI Summary Pattern

```python
summary = {
    "run_id": args.run_id,
    "row_count": len(rows),
    "output_csv": str(output_csv),
    "output_json": str(output_json),
}
print(json.dumps(summary, indent=2))
```

Source pattern: Phase 3 tests assert CLI summaries avoid secret-bearing content and expose generated output paths. [VERIFIED: tests/test_dataset_scope_audit.py; VERIFIED: AGENTS.md]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single generic MLLM prompt or static image-label comparison | Agentic/search or DSL-structured solvers with explicit tools/decomposition | Halligan USENIX Security 2025 and Oedipus CCS 2025/arXiv 2024 sources establish this comparison class. [CITED: https://www.usenix.org/conference/usenixsecurity25/presentation/teoh; CITED: https://arxiv.org/abs/2405.07496; CITED: https://geleideng.github.io/publication/oedipus/oedipus.pdf] | Phase 4 must not present local off-the-shelf API rows as equivalent to specialized solver rows. [VERIFIED: 04-CONTEXT.md] |
| Static image-label-only CAPTCHA datasets | Interactive offline benchmark environments and web-agent evaluation settings | Halligan states static image-label pairs are less representative for interactive challenges; Open CaptchaWorld frames itself as web-based agent benchmark. [CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf; CITED: https://arxiv.org/abs/2505.24878] | Paper tables need dataset/threat-model caveats and cannot collapse interactive and static evidence. [VERIFIED: 04-CONTEXT.md] |
| Broad "accuracy" rows | Source-preserving metric rows with normalized fields only when valid | Locked Phase 4 decision requires original metric preservation and validated standardization. [VERIFIED: 04-CONTEXT.md] | Planner should implement metric-definition validation before paper output. [VERIFIED: REQUIREMENTS.md] |
| Unavailable systems omitted | Unavailable/incompatible systems retained with evidence fields | Locked Phase 4 decision requires Halligan/Oedipus coverage even when unavailable or incompatible. [VERIFIED: 04-CONTEXT.md] | Coverage matrix visibly answers reviewer/system mentions without overclaiming. [VERIFIED: REQUIREMENTS.md] |

**Deprecated/outdated:**

- A table that compares only local off-the-shelf MLLM API results against specialized solver headline numbers is insufficient for Phase 4 unless status, caveats, threat model, dataset scale, and direct-comparability fields are visible. [VERIFIED: 04-CONTEXT.md; VERIFIED: PITFALLS.md]
- A default direct-run plan for live-service CAPTCHA solvers is out of scope and conflicts with project ethics constraints. [VERIFIED: AGENTS.md; VERIFIED: REQUIREMENTS.md]

## Assumptions Log

All implementation-shaping claims in this research are sourced from local project artifacts, environment probes, or current primary web sources. [VERIFIED: source review]

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| None | No `[ASSUMED]` claims were intentionally introduced. | All sections | Planner can proceed without additional user confirmation except for explicit Open Questions below. |

## Open Questions

1. **Can the team locate a direct Oedipus dataset/code artifact URL and license?**
   - What we know: Oedipus reports an open-sourced dataset and source code available on request to avoid misuse. [CITED: https://geleideng.github.io/publication/oedipus/oedipus.pdf]
   - What's unclear: Direct artifact URL, license terms, checksums, and whether offline import is feasible without contacting authors were not verified. [VERIFIED: web search]
   - Recommendation: Plan Oedipus as `literature-only` first; add an explicit artifact-research task before any adapter/direct-run status. [VERIFIED: 04-CONTEXT.md]

2. **Should Halligan direct execution be attempted after validated import?**
   - What we know: Halligan artifact exists under MIT license and AE describes offline benchmark setup. [CITED: https://zenodo.org/records/15709075; CITED: https://secartifacts.github.io/usenixsec2025/appendix-files/sec25cycle2ae-final17.pdf]
   - What's unclear: Current local Docker daemon is not running and Pixi is missing; artifact contents were not unpacked or audited. [VERIFIED: environment probe]
   - Recommendation: Do not block BASE-06 on direct execution; import Halligan Table 4 first, then optionally ask the user before installing/starting direct-run dependencies. [VERIFIED: 04-CONTEXT.md]

3. **Which secondary source should be used if a named-system smoke cannot be validated?**
   - What we know: Upstream Open CaptchaWorld is closely compatible with local task names and has a current Hugging Face dataset card with 862 rows. [CITED: https://huggingface.co/datasets/OpenCaptchaWorld/Open_CaptchaWorld; VERIFIED: local captcha_data inventory]
   - What's unclear: Repo README says MIT while the dataset card says Apache-2.0, so data-use terms need resolution before adapter-run claims. [CITED: https://github.com/MetaAgentX/OpenCaptchaWorld; CITED: https://huggingface.co/datasets/OpenCaptchaWorld/Open_CaptchaWorld]
   - Recommendation: Treat as a proposed secondary candidate and pause for user confirmation before it replaces Halligan/Oedipus smoke priority. [VERIFIED: 04-CONTEXT.md]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Phase 4 scripts/tests | yes | 3.11.5 | Project supports Python `>=3.10`. [VERIFIED: environment probe; VERIFIED: pyproject.toml] |
| uv | Reproducible test/script runs | yes | 0.11.14 | Use system Python only for inspection, but project commands should use uv. [VERIFIED: environment probe; VERIFIED: TESTING.md] |
| pydantic | Strict schemas | yes | 2.13.4 | None needed. [VERIFIED: environment probe; VERIFIED: pyproject.toml] |
| pandas | CSV ingestion/joining | yes | 1.5.3 | Use stdlib `csv` for simple reads if pandas is unnecessary. [VERIFIED: environment probe; VERIFIED: pyproject.toml] |
| pytest | Offline regression tests | yes | 9.0.3 | None needed. [VERIFIED: environment probe; VERIFIED: pyproject.toml] |
| ruff | Lint new modules | yes | 0.15.13 | Manual review if not run, but tool is present. [VERIFIED: environment probe; VERIFIED: pyproject.toml] |
| Docker daemon | Optional Halligan direct-run | no | CLI 29.1.5, daemon unavailable | Use validated Halligan import first. [VERIFIED: environment probe; CITED: https://secartifacts.github.io/usenixsec2025/appendix-files/sec25cycle2ae-final17.pdf] |
| Pixi | Optional Halligan setup | no | not installed | Do not make direct Halligan execution part of required Phase 4 plan. [VERIFIED: environment probe; CITED: https://secartifacts.github.io/usenixsec2025/appendix-files/sec25cycle2ae-final17.pdf] |
| curl | Optional source/artifact retrieval | yes | 8.4.0 | Use browser/manual download if large artifacts are too slow. [VERIFIED: environment probe] |

**Missing dependencies with no fallback:**

- None for the recommended validated-import Phase 4 plan. [VERIFIED: environment probe; VERIFIED: 04-CONTEXT.md]

**Missing dependencies with fallback:**

- Docker daemon and Pixi are missing for Halligan direct-run, but validated import is a locked acceptable smoke result path. [VERIFIED: environment probe; VERIFIED: 04-CONTEXT.md]

## Sources

### Primary (HIGH confidence)

- `.planning/phases/04-sota-solver-and-larger-benchmark-strengthening/04-CONTEXT.md` - locked Phase 4 decisions and scope. [VERIFIED: file read]
- `.planning/REQUIREMENTS.md` - BASE-01 through BASE-06 requirement text. [VERIFIED: file read]
- `.planning/ROADMAP.md` - Phase 4 goal and success criteria. [VERIFIED: file read]
- `AGENTS.md` - project language, safety, secret, and offline-dataset constraints. [VERIFIED: file read]
- `phase3_artifacts.py`, `extended_dataset_manifest.py`, `dataset_scope_audit.py`, `revision_artifacts.py` - local implementation patterns. [VERIFIED: file read]
- USENIX Halligan page - primary paper metadata and headline results: https://www.usenix.org/conference/usenixsecurity25/presentation/teoh. [CITED: official page]
- Halligan paper PDF - benchmark, baselines, Table 4, failure classes, cost/latency: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf. [CITED: official PDF]
- Halligan artifact appendix - offline benchmark and setup requirements: https://secartifacts.github.io/usenixsec2025/appendix-files/sec25cycle2ae-final17.pdf. [CITED: official artifact appendix]
- Halligan Zenodo artifact - downloadable artifact and MIT license record: https://zenodo.org/records/15709075. [CITED: Zenodo]
- Oedipus arXiv page - method and 63.5% reported result: https://arxiv.org/abs/2405.07496. [CITED: arXiv]
- Oedipus author-hosted CCS PDF - DOI/license text and detailed evaluation snippets surfaced by search: https://geleideng.github.io/publication/oedipus/oedipus.pdf. [CITED: author page/PDF]
- Open CaptchaWorld arXiv page - benchmark scale and result summary: https://arxiv.org/abs/2505.24878. [CITED: arXiv]
- Open CaptchaWorld Hugging Face dataset - current row count and dataset license card: https://huggingface.co/datasets/OpenCaptchaWorld/Open_CaptchaWorld. [CITED: Hugging Face dataset card]
- Open CaptchaWorld GitHub repo - task list, code/data structure, README license, and update notes: https://github.com/MetaAgentX/OpenCaptchaWorld. [CITED: GitHub README]

### Secondary (MEDIUM confidence)

- CAPTURE arXiv page - larger LVLM CAPTCHA benchmark candidate, not selected as default due artifact uncertainty and Phase 4 scope cap: https://arxiv.org/abs/2512.11323. [CITED: arXiv]
- CoLab/ResearchGate/J-GLOBAL search results for Oedipus DOI metadata were used only to cross-check current publication status, not as primary implementation evidence. [VERIFIED: web search]

### Tertiary (LOW confidence)

- None used for implementation recommendations. [VERIFIED: source review]

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - based on installed versions, `pyproject.toml`, and Phase 3 local implementation patterns. [VERIFIED: environment probe; VERIFIED: pyproject.toml; VERIFIED: phase3_artifacts.py]
- Architecture: HIGH - locked decisions specify independent schema module, central CLI, output path, and table/notes outputs. [VERIFIED: 04-CONTEXT.md]
- External artifact feasibility: MEDIUM - Halligan has strong artifact evidence, but Oedipus direct artifact access and Open CaptchaWorld license alignment need follow-up. [CITED: https://zenodo.org/records/15709075; CITED: https://geleideng.github.io/publication/oedipus/oedipus.pdf; CITED: https://huggingface.co/datasets/OpenCaptchaWorld/Open_CaptchaWorld; CITED: https://github.com/MetaAgentX/OpenCaptchaWorld]
- Pitfalls: HIGH - grounded in locked decisions, local codebase concerns, and current primary sources. [VERIFIED: 04-CONTEXT.md; VERIFIED: CONCERNS.md; CITED: https://www.usenix.org/system/files/usenixsecurity25-teoh.pdf]

**Research date:** 2026-05-19
**Valid until:** 2026-05-26 for external artifact availability and dataset/license status; 2026-06-18 for local architecture and stack guidance. [VERIFIED: current-date context; VERIFIED: external-source volatility assessment]
