# Phase 4: SOTA Solver and Larger Benchmark Strengthening - Context

**Gathered:** 2026-05-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 delivers a fair, auditable baseline and larger-benchmark comparison layer for the COGNITION revision. It should map local CAPTCHA task families to Halligan, Oedipus, other specialized solver baselines, and compatible larger external benchmark subsets; validate external/imported evidence; and generate paper-ready comparison tables, diagnostics, and concise notes.

This phase should not fully reimplement external solver systems by default, should not build live CAPTCHA attack automation, and should not run browser automation or adapters against real services. Evidence should remain offline, dataset-based, and clearly labeled by comparability, artifact availability, threat model, metric definition, and data-use constraints.

</domain>

<decisions>
## Implementation Decisions

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

### the agent's Discretion

- The planner may choose exact Phase 4 schema class names and CLI subcommand names, provided the locked fields and validation semantics above are preserved.
- The planner may choose exact output filenames under `results/revision/<run_id>/`, provided outputs include machine-readable CSV/JSON and paper-facing notes where relevant.
- The researcher may propose secondary smoke candidates if named-system artifacts are not usable, but replacement requires user confirmation before execution/import.
- The planner may decide how to visually encode `directly_comparable=false` in paper-ready tables, provided it remains visible to readers.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and Phase Scope

- `.planning/PROJECT.md` - Project goals, paper-revision constraints, ethics boundaries, and active benchmark-strengthening requirement.
- `.planning/REQUIREMENTS.md` - Phase 4 requirements `BASE-01` through `BASE-06`.
- `.planning/ROADMAP.md` - Phase 4 goal, success criteria, dependency on Phase 3, and reviewer alignment.
- `.planning/STATE.md` - Current project state and Phase 4 focus.

### Prior Phase Contracts

- `.planning/phases/01-reproducibility-and-safety-foundation/01-CONTEXT.md` - Locked decisions on `results/revision/<run_id>/`, manifests, preflight, append-only records, secret-safe reporting, and validators.
- `.planning/phases/02-adaptive-attacker-main-body-evidence/02-CONTEXT.md` - Locked adaptive threat model, task-type-primary comparison unit, binary feedback boundary, and failure-type separation.
- `.planning/phases/03-dataset-scope-statistical-confidence-and-limitations/03-CONTEXT.md` - Locked dataset-scope, extended-slice, threshold-sensitivity, retry-calibration, and failure-taxonomy framing.

### Codebase Maps

- `.planning/codebase/ARCHITECTURE.md` - Existing evaluation, provider, task, visualization, and generated-output architecture.
- `.planning/codebase/STRUCTURE.md` - File layout and current Phase 3 artifact modules.
- `.planning/codebase/CONVENTIONS.md` - Python style, CLI conventions, import-safety guidance, and artifact-writing patterns.
- `.planning/codebase/CONCERNS.md` - Generated artifact, task/schema drift, provider failure, and overclaiming risks.
- `.planning/codebase/TESTING.md` - Current pytest patterns and offline validation surfaces.

### Implementation Surfaces

- `revision_artifacts.py` - Revision run directory helpers and shared artifact-writing precedent.
- `phase3_artifacts.py` - Strict Pydantic schema and CSV/JSON writer pattern to mirror in `phase4_artifacts.py`.
- `dataset_scope_audit.py` - Dataset/task-family audit patterns and removed/incompatible task documentation style.
- `extended_dataset_manifest.py` - Extended dataset manifest, validation-slice, and original-vs-new evidence separation pattern.
- `retry_calibration.py` - Task-type-primary calibration and metric-comparison patterns.
- `failure_taxonomy.py` - Scientific/protocol/infrastructure failure separation pattern.
- `adaptive_compare.py` - Operational cutoff labels, comparison rows, and structural bottleneck tags.
- `visualize_results.py` - Existing task-family metadata and result-loading conventions.
- `tests/` - Offline pytest style for schema, importer, validator, and paper-output regressions.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `phase3_artifacts.py` already provides the strict Pydantic schema plus `write_csv`/`write_json` style that Phase 4 should mirror in a new `phase4_artifacts.py`.
- `extended_dataset_manifest.py` already validates selective external/extended evidence slices and records original, supplemented, and new-category evidence separately.
- `dataset_scope_audit.py` already documents incompatible task types with explicit reasons, which is the closest precedent for `unavailable` and `incompatible` baseline rows.
- `retry_calibration.py` and `adaptive_compare.py` already preserve task-type-primary comparisons and avoid overinterpreting non-equivalent evidence.
- `failure_taxonomy.py` already separates scientific evidence from protocol and infrastructure caveats, a pattern Phase 4 should reuse for comparability caveats.
- `revision_artifacts.revision_run_dir()` should be reused for `results/revision/<run_id>/` output placement.

### Established Patterns

- New revision-critical outputs should live under `results/revision/<run_id>/`.
- New standalone workflows use root-level Python modules and `argparse`.
- Tests should be offline and fixture-based; live provider calls and live-service automation are not default validation paths.
- Generated paper artifacts should remain machine-readable and reproducible through CSV/JSON, with prose generated only as supporting notes.
- Secret values and local credentials must not appear in reports, diagnostics, or planning artifacts.

### Integration Points

- The Phase 4 CLI should likely consume hand-authored or researcher-produced metadata about external systems, validate it into strict rows, and then generate the comprehensive comparison table.
- External import validation should explicitly check required fields, reported metric definitions, task labels, sample counts, artifact availability, license/use constraints, and comparability assumptions.
- Baseline outputs should feed later Phase 6 traceability and claim-ledger work without claiming direct comparability where only approximate or literature-only evidence exists.
- Task-family mapping for external subsets should use existing family metadata where possible but allow new semantic/mechanism categories when external evidence differs from the current 18 local classes.

</code_context>

<specifics>
## Specific Ideas

- Halligan and Oedipus are the priority named systems for Phase 4.
- Extra systems, if any, should come from the comparison baselines used by Halligan/Oedipus and should be limited to at most two.
- The smoke subset should support both reviewer response and dataset strengthening: at least two semantically different new CAPTCHA categories when feasible, plus supplemental data for Phase 3 underpowered or threshold-sensitive local families.
- A single comprehensive table is preferred over separate layered tables, as long as `system_class`, primary status, caveat tags, `directly_comparable`, and metric provenance are explicit.
- Literature-only metrics may be shown in the main table and discussed as approximate comparisons, but they must not be presented as direct head-to-head results unless comparability is validated.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within Phase 4 scope.

</deferred>

---

*Phase: 04-sota-solver-and-larger-benchmark-strengthening*
*Context gathered: 2026-05-19*
