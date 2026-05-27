import csv
import json
from pathlib import Path
from typing import Any, Iterable, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


EXPANDED_DATASET_MANIFEST_SCHEMA_VERSION = (
    "cognition.revision.phase041.expanded_dataset_manifest.v1"
)
EXPANDED_RUN_MATRIX_SCHEMA_VERSION = "cognition.revision.phase041.run_matrix.v1"
EXPANDED_PREFLIGHT_MATRIX_SCHEMA_VERSION = "cognition.revision.phase041.preflight_matrix.v1"
EXPANDED_STATIC_SUMMARY_SCHEMA_VERSION = "cognition.revision.phase041.static_summary.v1"
EXPANDED_ADAPTIVE_SUMMARY_SCHEMA_VERSION = (
    "cognition.revision.phase041.adaptive_summary.v1"
)
EXPANDED_FINAL_EVIDENCE_SCHEMA_VERSION = (
    "cognition.revision.phase041.final_evidence.v1"
)
EXPANDED_CLAIM_BOUNDARY_SCHEMA_VERSION = "cognition.revision.phase041.claim_boundary.v1"

ALLOWED_EVIDENCE_ORIGINS = {
    "original_captchaworld",
    "supplemented_category",
    "new_category",
}
ALLOWED_SLICE_TYPES = {"original", "supplement_existing", "new_category"}
ALLOWED_COMPATIBILITY_STATUSES = {
    "ready_for_static_pipeline",
    "needs_normalization",
    "incompatible_static_pipeline",
}
ALLOWED_EVALUATION_STATUSES = {
    "selected_for_static",
    "selected_for_adaptive",
    "evaluated_static",
    "evaluated_adaptive",
    "excluded_with_reason",
}
ALLOWED_RUN_SCOPES = {"static", "adaptive"}
ALLOWED_AGREEMENT_STATUSES = {
    "supports_original",
    "diverges_from_original",
    "inconclusive",
}
ALLOWED_CLAIM_USES = {
    "main_body_direct_evidence",
    "main_body_caveated",
    "appendix_context",
    "excluded_from_claim",
}
ALLOWED_SOURCE_KINDS = {
    "peer_reviewed_paper_dataset",
    "open_source_dataset",
    "gpt_image_open_captchaworld_style",
    "synthetic_fixture",
}
REAL_WORLD_SOURCE_KINDS = {
    "peer_reviewed_paper_dataset",
    "open_source_dataset",
}
PAPER_ELIGIBLE_SOURCE_KINDS = REAL_WORLD_SOURCE_KINDS | {
    "gpt_image_open_captchaworld_style"
}
GENERATED_SOURCE_MARKERS = (
    "deterministic offline generated",
    "offline generated",
    "synthetic",
    "manual fixture",
    "toy fixture",
    "pil generated",
)
ORIGINAL_DATASET_REUSE_MARKERS = (
    "copied from existing local captcha_data",
    "copied from captcha_data",
    "reused from existing captcha_data",
    "from existing local captcha_data",
    "local dataset snapshot in captcha_data",
)
EXPANDED_NOVELTY_MARKERS = (
    "new to current captcha_data",
    "not present in current captcha_data",
    "not in existing captcha_data",
    "not copied from existing captcha_data",
    "new external sample",
)

RowModel = TypeVar("RowModel", bound=BaseModel)


def _validate_allowed(value: str, allowed: set[str], field_name: str) -> str:
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {sorted(allowed)}")
    return value


def _require_text(value: str, field_name: str, context: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} is required when {context}")


def _require_items(values: list[str], field_name: str, context: str) -> None:
    if not values:
        raise ValueError(f"{field_name} is required when {context}")
    if any(not value.strip() for value in values):
        raise ValueError(f"{field_name} cannot contain blank items")


def _row_to_json_dict(row: BaseModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(row, BaseModel):
        return row.model_dump(mode="json")
    return row


def _row_to_csv_dict(row: BaseModel | dict[str, Any]) -> dict[str, Any]:
    payload = _row_to_json_dict(row)
    return {
        key: json.dumps(value, ensure_ascii=False)
        if isinstance(value, (list, dict))
        else value
        for key, value in payload.items()
    }


def _validated_rows(
    model: type[RowModel],
    rows: Iterable[RowModel | dict[str, Any]],
) -> list[RowModel]:
    return [row if isinstance(row, model) else model.model_validate(row) for row in rows]


class ExpandedDatasetManifestRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = EXPANDED_DATASET_MANIFEST_SCHEMA_VERSION
    run_id: str
    source_id: str
    source_path: str
    source_kind: str
    source_citation: str
    source_license: str
    source_provenance_notes: str
    evidence_origin: str
    slice_type: str
    task_type: str
    task_family: str
    sample_count: int = Field(ge=0)
    label_format: str
    metadata_alignment_notes: str
    answer_format_normalization: str
    compatibility_status: str
    evaluation_status: str
    limitation_notes: str
    adaptive_eligible: bool
    static_compatibility_notes: str

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        return _validate_allowed(
            value,
            {EXPANDED_DATASET_MANIFEST_SCHEMA_VERSION},
            "schema_version",
        )

    @field_validator("evidence_origin")
    @classmethod
    def validate_evidence_origin(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_EVIDENCE_ORIGINS, "evidence_origin")

    @field_validator("source_kind")
    @classmethod
    def validate_source_kind(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_SOURCE_KINDS, "source_kind")

    @field_validator("slice_type")
    @classmethod
    def validate_slice_type(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_SLICE_TYPES, "slice_type")

    @field_validator("compatibility_status")
    @classmethod
    def validate_compatibility_status(cls, value: str) -> str:
        return _validate_allowed(
            value,
            ALLOWED_COMPATIBILITY_STATUSES,
            "compatibility_status",
        )

    @field_validator("evaluation_status")
    @classmethod
    def validate_evaluation_status(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_EVALUATION_STATUSES, "evaluation_status")

    @model_validator(mode="after")
    def validate_manifest_caveats(self) -> "ExpandedDatasetManifestRow":
        selected_or_evaluated = self.evaluation_status != "excluded_with_reason"
        if selected_or_evaluated:
            if self.source_kind not in PAPER_ELIGIBLE_SOURCE_KINDS:
                raise ValueError(
                    "selected expanded sidecar rows must come from real-world "
                    "paper datasets, open-source CAPTCHA datasets, or GPT Image "
                    "Open CaptchaWorld-style generated samples"
                )
            _require_text(
                self.source_citation,
                "source_citation",
                "row is selected for expanded sidecar evaluation",
            )
            _require_text(
                self.source_license,
                "source_license",
                "row is selected for expanded sidecar evaluation",
            )
            _require_text(
                self.source_provenance_notes,
                "source_provenance_notes",
                "row is selected for expanded sidecar evaluation",
            )
            provenance_text = " ".join(
                [
                    self.source_citation,
                    self.metadata_alignment_notes,
                    self.limitation_notes,
                    self.static_compatibility_notes,
                    self.source_provenance_notes,
                ]
            ).lower()
            reuse_matches = [
                marker
                for marker in ORIGINAL_DATASET_REUSE_MARKERS
                if marker in provenance_text
            ]
            if reuse_matches:
                raise ValueError(
                    "expanded sidecar rows must be new relative to existing "
                    f"captcha_data; reuse markers found: {sorted(reuse_matches)}"
                )
            if not any(marker in provenance_text for marker in EXPANDED_NOVELTY_MARKERS):
                raise ValueError(
                    "source_provenance_notes must state that selected expanded "
                    "sidecar samples are new relative to current captcha_data"
                )
            if self.source_kind in REAL_WORLD_SOURCE_KINDS:
                generated_matches = [
                    marker
                    for marker in GENERATED_SOURCE_MARKERS
                    if marker in provenance_text
                ]
                if generated_matches:
                    raise ValueError(
                        "real-world expanded sidecar rows must not describe generated "
                        f"samples; generated source markers found: {sorted(generated_matches)}"
                    )
            if self.source_kind == "gpt_image_open_captchaworld_style":
                if "gpt image" not in provenance_text or "open captchaworld" not in provenance_text:
                    raise ValueError(
                        "GPT Image expanded sidecar rows must state GPT Image and "
                        "Open CaptchaWorld-style provenance"
                    )
        if self.evidence_origin == "new_category":
            _require_text(
                self.static_compatibility_notes,
                "static_compatibility_notes",
                "evidence_origin is new_category",
            )
        if self.compatibility_status == "incompatible_static_pipeline":
            _require_text(
                self.limitation_notes,
                "limitation_notes",
                "compatibility_status is incompatible_static_pipeline",
            )
        return self


class ExpandedRunMatrixRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = EXPANDED_RUN_MATRIX_SCHEMA_VERSION
    matrix_id: str
    paper_facing_model_row: bool
    provider: str
    model: str
    provider_model: str
    run_scope: str
    run_id: str
    task_types: list[str]
    materialized_dataset_root: str
    output_root: str
    overwrite: bool
    resume: bool

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        return _validate_allowed(value, {EXPANDED_RUN_MATRIX_SCHEMA_VERSION}, "schema_version")

    @field_validator("run_scope")
    @classmethod
    def validate_run_scope(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_RUN_SCOPES, "run_scope")

    @field_validator("task_types")
    @classmethod
    def validate_task_types(cls, values: list[str]) -> list[str]:
        _require_items(values, "task_types", "building an expanded run matrix row")
        return values

    @model_validator(mode="after")
    def validate_paper_facing_model_row(self) -> "ExpandedRunMatrixRow":
        if not self.paper_facing_model_row:
            raise ValueError("paper_facing_model_row must be true")
        return self


class ExpandedPreflightMatrixRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = EXPANDED_PREFLIGHT_MATRIX_SCHEMA_VERSION
    run_id: str
    provider: str
    model: str
    provider_model: str
    run_scope: str
    manifest_path: str
    manifest_sha256: str
    sidecar_dataset_root: str
    materialized_dataset_root: str
    task_types: list[str]
    prompt_config: dict[str, Any]
    expected_request_count: int = Field(ge=0)
    cost_preview: dict[str, Any]
    output_dir: str
    preflight_report_path: str
    overwrite: bool
    resume: bool
    attempt_budget_k: int | None = Field(default=None, ge=1)
    sampling_mode: str | None = None
    feedback_mode: str | None = None
    memory_mode: str | None = None
    stopping_rule: str | None = None
    solve_request_count: int | None = Field(default=None, ge=0)
    reflection_request_count_max: int | None = Field(default=None, ge=0)
    expected_request_count_max: int | None = Field(default=None, ge=0)

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        return _validate_allowed(
            value,
            {EXPANDED_PREFLIGHT_MATRIX_SCHEMA_VERSION},
            "schema_version",
        )

    @field_validator("run_scope")
    @classmethod
    def validate_run_scope(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_RUN_SCOPES, "run_scope")

    @field_validator("task_types")
    @classmethod
    def validate_task_types(cls, values: list[str]) -> list[str]:
        _require_items(values, "task_types", "building an expanded preflight matrix row")
        return values


class ExpandedStaticSummaryRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = EXPANDED_STATIC_SUMMARY_SCHEMA_VERSION
    run_id: str
    provider: str
    model: str
    provider_model: str
    task_type: str
    task_family: str
    evidence_origin: str
    slice_type: str
    sample_count: int = Field(ge=0)
    attempt_count: int = Field(ge=0)
    success_count: int = Field(ge=0)
    scientific_wrong_count: int = Field(ge=0)
    protocol_failure_count: int = Field(ge=0)
    infrastructure_failure_count: int = Field(ge=0)
    pass_rate: float | None = Field(default=None, ge=0, le=1)
    run_manifest_path: str
    attempt_log_path: str
    summary_source_path: str
    claim_use: str

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        return _validate_allowed(
            value,
            {EXPANDED_STATIC_SUMMARY_SCHEMA_VERSION},
            "schema_version",
        )

    @field_validator("evidence_origin")
    @classmethod
    def validate_evidence_origin(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_EVIDENCE_ORIGINS, "evidence_origin")

    @field_validator("slice_type")
    @classmethod
    def validate_slice_type(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_SLICE_TYPES, "slice_type")

    @field_validator("claim_use")
    @classmethod
    def validate_claim_use(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_CLAIM_USES, "claim_use")


class ExpandedAdaptiveSummaryRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = EXPANDED_ADAPTIVE_SUMMARY_SCHEMA_VERSION
    run_id: str
    provider: str
    model: str
    provider_model: str
    task_type: str
    task_family: str
    evidence_origin: str
    slice_type: str
    sample_count: int = Field(ge=0)
    session_count: int = Field(ge=0)
    attempt_budget_k: int = Field(ge=0)
    success_count: int = Field(ge=0)
    scientific_wrong_count: int = Field(ge=0)
    protocol_failure_count: int = Field(ge=0)
    infrastructure_failure_count: int = Field(ge=0)
    adaptive_success_rate: float | None = Field(default=None, ge=0, le=1)
    feedback_mode: str
    memory_mode: str
    stopping_rule: str
    run_manifest_path: str
    adaptive_attempt_log_path: str
    adaptive_summary_source_path: str
    claim_use: str

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        return _validate_allowed(
            value,
            {EXPANDED_ADAPTIVE_SUMMARY_SCHEMA_VERSION},
            "schema_version",
        )

    @field_validator("evidence_origin")
    @classmethod
    def validate_evidence_origin(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_EVIDENCE_ORIGINS, "evidence_origin")

    @field_validator("slice_type")
    @classmethod
    def validate_slice_type(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_SLICE_TYPES, "slice_type")

    @field_validator("claim_use")
    @classmethod
    def validate_claim_use(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_CLAIM_USES, "claim_use")


class ExpandedFinalEvidenceRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = EXPANDED_FINAL_EVIDENCE_SCHEMA_VERSION
    run_id: str
    evidence_row_id: str
    provider: str
    model: str
    provider_model: str
    task_type: str
    task_family: str
    evidence_origin: str
    slice_type: str
    sample_count: int = Field(ge=0)
    original_rate: float | None = Field(default=None, ge=0, le=1)
    expanded_static_rate: float | None = Field(default=None, ge=0, le=1)
    expanded_adaptive_rate: float | None = Field(default=None, ge=0, le=1)
    agreement_status: str
    diverges_from_original: bool = False
    divergence_reason: str
    scientific_wrong_count: int = Field(default=0, ge=0)
    protocol_failure_count: int = Field(default=0, ge=0)
    infrastructure_failure_count: int = Field(default=0, ge=0)
    claim_boundary_note: str
    direct_evidence: bool
    contextual_sota_only: bool
    claim_use: str
    source_artifact_path: str

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        return _validate_allowed(
            value,
            {EXPANDED_FINAL_EVIDENCE_SCHEMA_VERSION},
            "schema_version",
        )

    @field_validator("evidence_origin")
    @classmethod
    def validate_evidence_origin(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_EVIDENCE_ORIGINS, "evidence_origin")

    @field_validator("slice_type")
    @classmethod
    def validate_slice_type(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_SLICE_TYPES, "slice_type")

    @field_validator("agreement_status")
    @classmethod
    def validate_agreement_status(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_AGREEMENT_STATUSES, "agreement_status")

    @field_validator("claim_use")
    @classmethod
    def validate_claim_use(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_CLAIM_USES, "claim_use")

    @model_validator(mode="after")
    def validate_visible_claim_boundaries(self) -> "ExpandedFinalEvidenceRow":
        if self.agreement_status == "diverges_from_original":
            _require_text(
                self.divergence_reason,
                "divergence_reason",
                "agreement_status is diverges_from_original",
            )
        if not self.direct_evidence:
            _require_text(
                self.claim_boundary_note,
                "claim_boundary_note",
                "direct_evidence is false",
            )
        if self.contextual_sota_only:
            if self.direct_evidence:
                raise ValueError(
                    "contextual_sota_only rows cannot set direct_evidence to true"
                )
            _require_text(
                self.claim_boundary_note,
                "claim_boundary_note",
                "contextual_sota_only is true",
            )
        return self


class ExpandedClaimBoundaryNoteRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = EXPANDED_CLAIM_BOUNDARY_SCHEMA_VERSION
    run_id: str
    note_id: str
    claim_key: str
    task_type: str
    task_family: str
    evidence_origin: str
    agreement_status: str
    divergence_reason: str
    claim_use: str
    direct_evidence: bool
    contextual_sota_only: bool
    claim_boundary_note: str
    limitation_notes: str
    source_artifact_path: str
    visible_in_main_body: bool

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        return _validate_allowed(
            value,
            {EXPANDED_CLAIM_BOUNDARY_SCHEMA_VERSION},
            "schema_version",
        )

    @field_validator("evidence_origin")
    @classmethod
    def validate_evidence_origin(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_EVIDENCE_ORIGINS, "evidence_origin")

    @field_validator("agreement_status")
    @classmethod
    def validate_agreement_status(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_AGREEMENT_STATUSES, "agreement_status")

    @field_validator("claim_use")
    @classmethod
    def validate_claim_use(cls, value: str) -> str:
        return _validate_allowed(value, ALLOWED_CLAIM_USES, "claim_use")

    @model_validator(mode="after")
    def validate_claim_boundary_contract(self) -> "ExpandedClaimBoundaryNoteRow":
        if self.agreement_status == "diverges_from_original":
            _require_text(
                self.divergence_reason,
                "divergence_reason",
                "agreement_status is diverges_from_original",
            )
        if not self.direct_evidence:
            _require_text(
                self.claim_boundary_note,
                "claim_boundary_note",
                "direct_evidence is false",
            )
        if self.contextual_sota_only:
            if self.direct_evidence:
                raise ValueError(
                    "contextual_sota_only rows cannot set direct_evidence to true"
                )
            _require_text(
                self.claim_boundary_note,
                "claim_boundary_note",
                "contextual_sota_only is true",
            )
        return self


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


def write_json(
    path: Path,
    schema_version: str,
    rows: Iterable[BaseModel | dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "schema_version": schema_version,
                "rows": [_row_to_json_dict(row) for row in rows],
            },
            handle,
            indent=2,
            ensure_ascii=False,
        )
        handle.write("\n")


def write_expanded_dataset_manifest(
    output_csv: Path,
    output_json: Path,
    rows: Iterable[ExpandedDatasetManifestRow | dict[str, Any]],
) -> tuple[Path, Path]:
    validated_rows = _validated_rows(ExpandedDatasetManifestRow, rows)
    write_csv(output_csv, ExpandedDatasetManifestRow.model_fields, validated_rows)
    write_json(output_json, EXPANDED_DATASET_MANIFEST_SCHEMA_VERSION, validated_rows)
    return output_csv, output_json


def write_expanded_run_matrix(
    output_csv: Path,
    output_json: Path,
    rows: Iterable[ExpandedRunMatrixRow | dict[str, Any]],
) -> tuple[Path, Path]:
    validated_rows = _validated_rows(ExpandedRunMatrixRow, rows)
    write_csv(output_csv, ExpandedRunMatrixRow.model_fields, validated_rows)
    write_json(output_json, EXPANDED_RUN_MATRIX_SCHEMA_VERSION, validated_rows)
    return output_csv, output_json


def write_expanded_preflight_matrix(
    output_csv: Path,
    output_json: Path,
    rows: Iterable[ExpandedPreflightMatrixRow | dict[str, Any]],
) -> tuple[Path, Path]:
    validated_rows = _validated_rows(ExpandedPreflightMatrixRow, rows)
    write_csv(output_csv, ExpandedPreflightMatrixRow.model_fields, validated_rows)
    write_json(output_json, EXPANDED_PREFLIGHT_MATRIX_SCHEMA_VERSION, validated_rows)
    return output_csv, output_json


def write_expanded_static_summary(
    output_csv: Path,
    output_json: Path,
    rows: Iterable[ExpandedStaticSummaryRow | dict[str, Any]],
) -> tuple[Path, Path]:
    validated_rows = _validated_rows(ExpandedStaticSummaryRow, rows)
    write_csv(output_csv, ExpandedStaticSummaryRow.model_fields, validated_rows)
    write_json(output_json, EXPANDED_STATIC_SUMMARY_SCHEMA_VERSION, validated_rows)
    return output_csv, output_json


def write_expanded_adaptive_summary(
    output_csv: Path,
    output_json: Path,
    rows: Iterable[ExpandedAdaptiveSummaryRow | dict[str, Any]],
) -> tuple[Path, Path]:
    validated_rows = _validated_rows(ExpandedAdaptiveSummaryRow, rows)
    write_csv(output_csv, ExpandedAdaptiveSummaryRow.model_fields, validated_rows)
    write_json(output_json, EXPANDED_ADAPTIVE_SUMMARY_SCHEMA_VERSION, validated_rows)
    return output_csv, output_json


def write_expanded_final_evidence(
    output_csv: Path,
    output_json: Path,
    rows: Iterable[ExpandedFinalEvidenceRow | dict[str, Any]],
) -> tuple[Path, Path]:
    validated_rows = _validated_rows(ExpandedFinalEvidenceRow, rows)
    write_csv(output_csv, ExpandedFinalEvidenceRow.model_fields, validated_rows)
    write_json(output_json, EXPANDED_FINAL_EVIDENCE_SCHEMA_VERSION, validated_rows)
    return output_csv, output_json


def write_expanded_claim_boundaries(
    output_csv: Path,
    output_json: Path,
    rows: Iterable[ExpandedClaimBoundaryNoteRow | dict[str, Any]],
) -> tuple[Path, Path]:
    validated_rows = _validated_rows(ExpandedClaimBoundaryNoteRow, rows)
    write_csv(output_csv, ExpandedClaimBoundaryNoteRow.model_fields, validated_rows)
    write_json(output_json, EXPANDED_CLAIM_BOUNDARY_SCHEMA_VERSION, validated_rows)
    return output_csv, output_json
