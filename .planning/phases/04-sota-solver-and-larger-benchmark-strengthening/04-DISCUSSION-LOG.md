# Phase 4: SOTA Solver and Larger Benchmark Strengthening - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md; this log preserves the alternatives considered.

**Date:** 2026-05-19
**Phase:** 04 - SOTA Solver and Larger Benchmark Strengthening
**Areas discussed:** Baseline coverage policy, Smoke subset priority, Comparison table conservatism, Phase 4 artifact/schema shape, External system research scope

---

## Baseline Coverage Policy

| Question | Option | Description | Selected |
|---|---|---|---|
| Coverage inclusion rule | Include all named systems with strong labels | Include every reviewer/shepherd-named system and use comparability/status labels. | Yes |
| Coverage inclusion rule | Only include artifact-verifiable items | Include only systems with verifiable papers, code, data, metrics, or licenses. | No |
| Coverage inclusion rule | Use two-tier inclusion | Put artifact-verifiable systems in the main table and unavailable/incompatible systems in appendix or JSON. | No |

**User's choice:** Include all reviewer/shepherd-named systems, with strong comparability/status labels.
**Notes:** Halligan and Oedipus should not disappear from the matrix even if they are unavailable, incompatible, or literature-only.

| Question | Option | Description | Selected |
|---|---|---|---|
| Literature-only table inclusion | Include in main table but do not mix into numeric comparison | Show architecture, threat model, dataset scale, task families, artifacts, and comparable metrics only when valid. | No |
| Literature-only table inclusion | Only include in appendix/coverage matrix | Keep main text limited to direct-run, adapter-run, and import-validated rows. | No |
| Literature-only table inclusion | Include in main table with literature-reported metrics | Include reported metrics with footnotes and comparability caveats. | Yes |

**User's choice:** Include literature-only rows in the main table and fill literature-reported metrics with footnotes and comparability caveats.
**Notes:** These values can support reviewer response and context but require clear metric and comparability documentation.

| Question | Option | Description | Selected |
|---|---|---|---|
| Row label shape | Primary status plus caveat tags | One primary status plus multiple caveat tags. | Yes |
| Row label shape | Single status only | Keep only one status and put details in notes. | No |
| Row label shape | Multiple status labels without split | Let a row have multiple statuses without separating primary/caveat. | No |

**User's choice:** Use one primary status plus multiple caveat tags.
**Notes:** This keeps paper tables readable while preserving machine-readable caveats.

| Question | Option | Description | Selected |
|---|---|---|---|
| Evidence for unavailable/incompatible rows | Require documented basis | Require `status_reason`, checked artifacts/docs, missing items, and last-checked date. | Yes |
| Evidence for unavailable/incompatible rows | Use short notes only | Faster but less auditable. | No |
| Evidence for unavailable/incompatible rows | Strict evidence only for named systems | Require full evidence for Halligan/Oedipus, simplify other rows. | No |

**User's choice:** Require documented basis for unavailable/incompatible rows before paper-ready inclusion.
**Notes:** This prevents unsupported availability or incompatibility claims.

---

## Smoke Subset Priority

| Question | Option | Description | Selected |
|---|---|---|---|
| Smoke target priority | Artifact verifiability first | Choose the clearest data/code/metric/license subset. | No |
| Smoke target priority | Task-family similarity first | Choose the subset most mappable to local CAPTCHA families. | No |
| Smoke target priority | Reviewer attention first | Choose Halligan/Oedipus or the named system that best answers criticism. | Yes |
| Smoke target priority | Sample scale first | Choose the largest subset to answer larger-benchmark concerns. | No |

**User's choice:** Prioritize Halligan/Oedipus or the named system that best answers the criticism.
**Notes:** Within that priority, select at least two semantically different new CAPTCHA categories and some subsets that map to local task families, carrying forward Phase 3's dataset-extension goal.

| Question | Option | Description | Selected |
|---|---|---|---|
| Smoke success standard | Run or import count if validated | Local run, adapter run, or import can count if validation passes. | Yes |
| Smoke success standard | Must direct-run or adapter-run at least one subset | Stronger but riskier if named artifacts are not usable. | No |
| Smoke success standard | Use dual-track import plus separate direct-run | Most complete but largest scope. | No |

**User's choice:** Run or import both count, but validation is mandatory.
**Notes:** Validation must cover required fields, metrics, task labels, sample counts, and comparability assumptions.

| Question | Option | Description | Selected |
|---|---|---|---|
| New-category definition | Semantic/mechanism difference first | New types need clear task/visual-structure differences, not exact taxonomy matches. | Yes |
| New-category definition | External taxonomy first | Preserve the external benchmark's original category structure. | No |
| New-category definition | Local taxonomy first | Prefer mapping into local families unless impossible. | No |

**User's choice:** Prioritize semantic/mechanism differences over exact external taxonomy.
**Notes:** Artifacts should record `external_task_label`, `mapped_local_family`, and the new/supplemental rationale.

| Question | Option | Description | Selected |
|---|---|---|---|
| Local family supplementation | Underpowered / threshold-sensitive families | Supplement Phase 3 underpowered or threshold-sensitive families first. | Yes |
| Local family supplementation | Hardest families | Add evidence for already-robust families. | No |
| Local family supplementation | Borderline families | Add evidence for families most vulnerable to reviewer skepticism. | No |
| Local family supplementation | Artifact availability | Let availability decide first. | No |

**User's choice:** Prioritize Phase 3 underpowered and threshold-sensitive families.
**Notes:** This makes external data strengthen the most claim-sensitive local evidence.

| Question | Option | Description | Selected |
|---|---|---|---|
| Substitute if named artifacts fail | Automatically choose secondary verifiable subset | Avoids blocking BASE-06 but changes direction automatically. | No |
| Substitute if named artifacts fail | Do not substitute | Keep named systems as the only smoke target. | No |
| Substitute if named artifacts fail | Ask user to confirm substitute | Researcher proposes candidates, user confirms before replacement. | Yes |

**User's choice:** Ask user to confirm substitute.
**Notes:** Planner/researcher may propose secondary candidates but must not auto-replace Halligan/Oedipus smoke targets.

---

## Comparison Table Conservatism

| Question | Option | Description | Selected |
|---|---|---|---|
| Paper-ready table structure | Layered main table | Separate evidence classes into sections. | No |
| Paper-ready table structure | One comprehensive table plus strong labels | Keep one table with primary status and caveat tags. | Yes |
| Paper-ready table structure | Compact main table with full appendix/artifacts | Keep the main text lean, push full matrix elsewhere. | No |

**User's choice:** Use one comprehensive table plus strong labels.
**Notes:** Strong labels must prevent readers from treating the table as a simple ranking.

| Question | Option | Description | Selected |
|---|---|---|---|
| Numeric metric presentation | Original reported value plus normalized fields | Preserve raw reported metrics and add normalized success rate when validated. | Yes |
| Numeric metric presentation | Original reported value only | Avoids standardization risk but reduces comparison utility. | No |
| Numeric metric presentation | Standardized success rate only | Clean table but risks overcompressing metric differences. | No |

**User's choice:** Show original reported metric name/value alongside validated `normalized_success_rate`.
**Notes:** Leave normalized fields blank with caveats when standardization is unreliable.

| Question | Option | Description | Selected |
|---|---|---|---|
| Direct comparability field | Require directly_comparable | Every row has a boolean; false requires caveat. | Yes |
| Direct comparability field | Use caveat tags only | Comparability inferred from tags. | No |
| Direct comparability field | Machine artifact only | Keep the field out of the paper table. | No |

**User's choice:** Require `directly_comparable`.
**Notes:** Paper tables should expose false rows through symbols, notes, or footnotes.

| Question | Option | Description | Selected |
|---|---|---|---|
| Main-text phrasing for non-comparable literature metrics | Contextual reference, not head-to-head | Most conservative language. | No |
| Main-text phrasing for non-comparable literature metrics | Approximate comparison | Stronger comparison language with explicit caveats. | Yes |
| Main-text phrasing for non-comparable literature metrics | Not compared numerically | Show values but do not discuss differences. | No |

**User's choice:** Use approximate comparison language when caveats are explicit.
**Notes:** Artifacts should record approximation basis, metric mismatch, and dataset mismatch.

| Question | Option | Description | Selected |
|---|---|---|---|
| System class distinction | Require explicit system_class | Add classes such as off-the-shelf MLLM API and specialized solver. | Yes |
| System class distinction | Use threat model fields only | Less direct. | No |
| System class distinction | Separate in paper table only | Human-readable but weaker traceability. | No |

**User's choice:** Require explicit `system_class`.
**Notes:** This satisfies the roadmap requirement to separate off-the-shelf MLLM API results from specialized solver results.

---

## Phase 4 Artifact/Schema Shape

| Question | Option | Description | Selected |
|---|---|---|---|
| Strict schema module | Add phase4_artifacts.py | New Pydantic schemas for baseline coverage, comparison, import validation, and paper rows. | Yes |
| Strict schema module | Extend phase3_artifacts.py | Reuse file but mix baseline semantics into Phase 3 schemas. | No |
| Strict schema module | Use lightweight dataclasses/CSV writers | Faster but less strict. | No |

**User's choice:** Add `phase4_artifacts.py`.
**Notes:** Keep Phase 4 SOTA/baseline semantics separate from Phase 3 dataset/statistical schemas.

| Question | Option | Description | Selected |
|---|---|---|---|
| CLI/module split | Multiple small scripts | Each script has one responsibility. | No |
| CLI/module split | One CLI with subcommands | Central entry point for coverage/import/table/notes. | Yes |
| CLI/module split | One script first, split later | Fastest but less planned. | No |

**User's choice:** Use one central CLI with subcommands.
**Notes:** Schemas and helper logic should stay outside the CLI to avoid a new monolith.

| Question | Option | Description | Selected |
|---|---|---|---|
| Validator failure handling | Fail closed | Invalid rows cannot enter paper-ready tables. | No |
| Validator failure handling | Allow with warning | Rows can enter with warning/caveat. | Yes |
| Validator failure handling | Different rules by status | Strict for direct/import rows, looser for literature-only rows. | No |

**User's choice:** Allow with warning/caveat.
**Notes:** Unverified fields must not be marked directly comparable or support strong claims.

| Question | Option | Description | Selected |
|---|---|---|---|
| Output path convention | Continue results/revision/<run_id>/ | Keep Phase 1-3 revision artifact convention. | Yes |
| Output path convention | Add results/baselines/<run_id>/ | More semantic but less consistent. | No |
| Output path convention | Only output to paper_artifacts or figures | Paper-adjacent but weaker provenance. | No |

**User's choice:** Continue using `results/revision/<run_id>/`.
**Notes:** Coverage matrix, diagnostics, comparison table, and notes should all live there.

| Question | Option | Description | Selected |
|---|---|---|---|
| Prose generation | Generate short paper notes | Produce concise notes/prose for table interpretation. | Yes |
| Prose generation | Only generate CSV/JSON tables | Keep manuscript writing manual. | No |
| Prose generation | Generate full manuscript section | Saves writing but overlaps Phase 6. | No |

**User's choice:** Generate short paper notes/prose.
**Notes:** Do not write a full manuscript section in Phase 4.

---

## External System Research Scope

| Question | Option | Description | Selected |
|---|---|---|---|
| Additional system search | Proactively find a few high-relevance systems | Add a small number of relevant external systems. | Yes |
| Additional system search | Strictly cover named systems only | Avoid scope expansion. | No |
| Additional system search | Broadly scan then filter | Best coverage but deadline risk. | No |

**User's choice:** Proactively include a small number of highly relevant systems.
**Notes:** Prefer systems that Halligan/Oedipus use as comparison baselines.

| Question | Option | Description | Selected |
|---|---|---|---|
| Extra-system upper bound | At most 2 | Tight, deadline-friendly scope. | Yes |
| Extra-system upper bound | At most 4 | Broader but more work. | No |
| Extra-system upper bound | No fixed number | Flexible but risks scope creep. | No |

**User's choice:** At most two extra systems.
**Notes:** Prioritize systems actually compared in Halligan/Oedipus.

| Question | Option | Description | Selected |
|---|---|---|---|
| License/use constraints | Must validate license/use constraints | Required for runnable/importable candidates. | Yes |
| License/use constraints | Only validate direct-run candidates | Less work but weaker artifact readiness. | No |
| License/use constraints | Not a Phase 4 focus | Fastest but risky. | No |

**User's choice:** Must validate license and data-use constraints.
**Notes:** Unclear license/use terms prevent `direct-run` or `adapter-run` status.

| Question | Option | Description | Selected |
|---|---|---|---|
| Live-service automation oriented systems | Exclude running; ethics-caveated literature row only | Do not run or adapt, only document. | No |
| Live-service automation oriented systems | Import public results if available | Do not run, but allow public-result import with caveats. | Yes |
| Live-service automation oriented systems | Completely exclude | Safest but incomplete. | No |

**User's choice:** Import public data/results if available, with clear caveats.
**Notes:** Do not run or implement adapters for live-service automation oriented systems.

| Question | Option | Description | Selected |
|---|---|---|---|
| External research recency | Recent work first; older only if named/referenced | Prioritize 2023-2026 and include older only if named or used as comparisons. | Yes |
| External research recency | No year limit | Relevance and comparability only. | No |
| External research recency | Only 2024 onward | Very modern but may miss important baselines. | No |

**User's choice:** Prioritize 2023-2026 systems and benchmarks.
**Notes:** Halligan/Oedipus are covered regardless of year; older systems only if named or used as comparison baselines by them.

---

## the agent's Discretion

- Choose exact schema class names and CLI subcommand names.
- Choose exact output filenames under `results/revision/<run_id>/`.
- Decide table footnote/symbol formatting for `directly_comparable=false`.
- Propose secondary smoke candidates if named-system artifacts are unusable, but pause for user confirmation before substitution.

## Deferred Ideas

None.
