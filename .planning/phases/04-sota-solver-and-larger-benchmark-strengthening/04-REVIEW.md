---
phase: 04-sota-solver-and-larger-benchmark-strengthening
reviewed: 2026-05-19T15:10:07Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - phase4_artifacts.py
  - baseline_strengthening.py
  - baseline_sources/phase4_baseline_sources.json
  - tests/test_phase4_artifacts.py
  - tests/test_baseline_strengthening.py
findings:
  critical: 0
  warning: 3
  info: 0
  total: 3
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-05-19T15:10:07Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Reviewed the Phase 4 baseline artifact models, baseline-strengthening CLI, curated source metadata, and the focused unit tests. Automated checks passed:

- `uv run ruff check phase4_artifacts.py baseline_strengthening.py tests/test_phase4_artifacts.py tests/test_baseline_strengthening.py`
- `uv run pytest tests/test_phase4_artifacts.py tests/test_baseline_strengthening.py`

No critical security issues were found. The warnings below are data-integrity and reproducibility risks in artifact serialization and validation paths.

## Warnings

### WR-01: CSV artifacts do not round-trip list fields

**File:** `phase4_artifacts.py:340`
**Issue:** `write_csv` passes model payloads directly to `csv.DictWriter.writerow`. Python lists are serialized with Python `repr` syntax such as `['dataset-mismatch']`, but the CSV readers in `baseline_strengthening._as_list` only parse JSON arrays or delimited strings. A generated coverage CSV can therefore fail when reused as a coverage artifact because `caveat_tags`, `captcha_families`, `checked_sources`, and `missing_items` are read back with stray brackets/quotes.
**Fix:**
```python
def _row_to_csv_dict(row: BaseModel | dict[str, Any]) -> dict[str, Any]:
    payload = _row_to_json_dict(row)
    return {
        key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
        for key, value in payload.items()
    }


def write_csv(
    path: Path,
    field_map: dict[str, Any],
    rows: Iterable[BaseModel | dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(field_map)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(_row_to_csv_dict(row))
```

### WR-02: Downstream coverage-artifact loads bypass source coverage invariants

**File:** `baseline_strengthening.py:155`
**Issue:** `_load_baseline_coverage_artifact` only validates each row against `BaselineCoverageRow`. It does not re-enforce the coverage-level invariants from `validate_coverage_rows`, including required Halligan/Oedipus presence and the maximum secondary-system cap. A hand-edited or stale coverage artifact missing Oedipus can still proceed into `validate-import` or `build-table`. This is harder to fix downstream because `selection_reason` is removed before artifact writing at `baseline_strengthening.py:101`, so secondary-system rationale is not preserved for later audit.
**Fix:**
```python
def _validate_coverage_artifact_rows(
    rows: list[dict[str, object]],
    run_id: str,
) -> list[BaselineCoverageRow]:
    system_names = {str(row.get("system_name") or "") for row in rows}
    if not NAMED_BASELINE_SYSTEMS <= system_names:
        raise ValueError("coverage artifact must include Halligan and Oedipus")
    if len(_secondary_systems(rows)) > MAX_SECONDARY_SYSTEMS:
        raise ValueError("coverage artifact may include at most two additional systems")
    return [
        BaselineCoverageRow.model_validate(_coverage_model_payload(row, run_id))
        for row in rows
    ]


def _load_baseline_coverage_artifact(path: Path, run_id: str) -> list[BaselineCoverageRow]:
    return _validate_coverage_artifact_rows(_read_table(path), run_id)
```

If secondary selection rationale is intended to remain auditable after the coverage stage, add a `selection_reason` or `secondary_selection_reason` field to `BaselineCoverageRow` instead of popping it before writing artifacts.

### WR-03: Duplicate import source keys are silently overwritten

**File:** `baseline_strengthening.py:372`
**Issue:** `build_baseline_comparison_rows` indexes import validation rows with `{row.source_key: row for row in import_validation_rows}`. If an import diagnostics file contains duplicate `source_key` values with conflicting pass/fail status or metric values, the last row silently wins and the comparison output becomes order-dependent.
**Fix:**
```python
def _unique_import_index(
    rows: list[ExternalImportValidationRow],
) -> dict[str, ExternalImportValidationRow]:
    indexed: dict[str, ExternalImportValidationRow] = {}
    for row in rows:
        if row.source_key in indexed:
            raise ValueError(f"duplicate import validation source_key: {row.source_key}")
        indexed[row.source_key] = row
    return indexed


def build_baseline_comparison_rows(
    coverage_rows: list[BaselineCoverageRow],
    import_validation_rows: list[ExternalImportValidationRow],
    run_id: str,
) -> list[BaselineComparisonRow]:
    import_by_key = _unique_import_index(import_validation_rows)
    ...
```

---

_Reviewed: 2026-05-19T15:10:07Z_
_Reviewer: Codex (gsd-code-reviewer)_
_Depth: standard_
