from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


ADAPTIVE_POLICY_STATE_SCHEMA_VERSION = "cognition.revision.adaptive_policy_state.v1"
ADAPTIVE_ATTEMPT_SCHEMA_VERSION = "cognition.revision.adaptive_attempt.v1"
ADAPTIVE_SUMMARY_SCHEMA_VERSION = "cognition.revision.adaptive_summary.v1"
ADAPTIVE_COMPARISON_SCHEMA_VERSION = "cognition.revision.adaptive_comparison.v1"
SAMPLING_MODE = "without-replacement"
FEEDBACK_MODE = "binary-pass-fail"
MEMORY_MODE = "explicit-policy-notes"
STOPPING_RULE = "first-success-or-budget"
ALLOWED_FAILURE_CLASSES = {
    "scientific_wrong",
    "protocol_failure",
    "infrastructure_failure",
    "none",
}
ALLOWED_STOPPING_REASONS = {
    "continue",
    "first_success",
    "budget_exhausted",
    "pool_exhausted",
    "infrastructure_failure",
}

_BANNED_POLICY_TOKENS = (
    "ground_truth",
    "gt",
    "correct_answer",
    "correct coordinate",
    "correct coordinates",
    "label",
    "transcript",
    "raw_prompt",
    "raw_response",
)


def _contains_banned_token(text: str) -> str | None:
    lowered = text.casefold()
    for token in _BANNED_POLICY_TOKENS:
        if token == "gt":
            words = lowered.replace("_", " ").replace("-", " ").split()
            if token in words:
                return token
            continue
        if token in lowered:
            return token
    return None


def _validate_policy_note_texts(values: list[str]) -> list[str]:
    for value in values:
        banned = _contains_banned_token(value)
        if banned is not None:
            raise ValueError(f"adaptive policy state contains banned token: {banned}")
    return values


def _validate_mode(value: str, expected: str, field_name: str) -> str:
    if value != expected:
        raise ValueError(f"{field_name} must be {expected!r}")
    return value


class AdaptivePolicyState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = ADAPTIVE_POLICY_STATE_SCHEMA_VERSION
    task_type: str
    failed_attempt_count: int = Field(ge=0)
    tried_strategy_summaries: list[str] = Field(default_factory=list)
    next_prompt_rules: list[str] = Field(default_factory=list)
    updated_at: datetime

    @field_validator("tried_strategy_summaries", "next_prompt_rules")
    @classmethod
    def reject_leaky_policy_notes(cls, values: list[str]) -> list[str]:
        return _validate_policy_note_texts(values)


class AdaptiveAttemptRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = ADAPTIVE_ATTEMPT_SCHEMA_VERSION
    run_id: str
    attempt_id: str
    provider: str
    model: str
    prompt_mode: str
    task_type: str
    puzzle_id: str
    attempt_index: int = Field(ge=1)
    attempt_budget_k: int = Field(ge=1)
    sampling_mode: str = SAMPLING_MODE
    feedback_mode: str = FEEDBACK_MODE
    memory_mode: str = MEMORY_MODE
    prior_failures: list[dict[str, Any]] = Field(default_factory=list)
    policy_state_before: AdaptivePolicyState
    policy_state_after: AdaptivePolicyState
    prompt_adaptation_metadata: dict[str, Any] = Field(default_factory=dict)
    parsed_answer: Any = None
    correct: bool
    failure_class: str
    latency_ms: float | None = Field(default=None, ge=0)
    tokens_in: int | None = Field(default=None, ge=0)
    tokens_out: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)
    cumulative_latency_ms: float = Field(ge=0)
    cumulative_cost_usd: float = Field(ge=0)
    stopping_reason: str
    timestamp: datetime

    @field_validator("sampling_mode")
    @classmethod
    def validate_sampling_mode(cls, value: str) -> str:
        return _validate_mode(value, SAMPLING_MODE, "sampling_mode")

    @field_validator("feedback_mode")
    @classmethod
    def validate_feedback_mode(cls, value: str) -> str:
        return _validate_mode(value, FEEDBACK_MODE, "feedback_mode")

    @field_validator("memory_mode")
    @classmethod
    def validate_memory_mode(cls, value: str) -> str:
        return _validate_mode(value, MEMORY_MODE, "memory_mode")

    @field_validator("failure_class")
    @classmethod
    def validate_failure_class(cls, value: str) -> str:
        if value not in ALLOWED_FAILURE_CLASSES:
            raise ValueError(f"failure_class must be one of {sorted(ALLOWED_FAILURE_CLASSES)}")
        return value

    @field_validator("stopping_reason")
    @classmethod
    def validate_stopping_reason(cls, value: str) -> str:
        if value not in ALLOWED_STOPPING_REASONS:
            raise ValueError(f"stopping_reason must be one of {sorted(ALLOWED_STOPPING_REASONS)}")
        return value


class AdaptiveSummaryRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = ADAPTIVE_SUMMARY_SCHEMA_VERSION
    run_id: str
    provider: str
    model: str
    task_type: str
    attempt_budget_k: int = Field(ge=1)
    sampling_mode: str = SAMPLING_MODE
    feedback_mode: str = FEEDBACK_MODE
    memory_mode: str = MEMORY_MODE
    solve_request_count: int = Field(ge=0)
    reflection_request_count: int = Field(ge=0)
    n_attempts: int = Field(ge=0)
    n_success: int = Field(ge=0)
    success_rate: float = Field(ge=0, le=1)
    expected_attempts: float | None = Field(default=None, ge=0)
    attempts_to_success: int | None = Field(default=None, ge=1)
    cumulative_latency_ms: float = Field(ge=0)
    cumulative_cost_usd: float = Field(ge=0)
    scientific_wrong_count: int = Field(ge=0)
    protocol_failure_count: int = Field(ge=0)
    infrastructure_failure_count: int = Field(ge=0)
    stopping_reason: str
    confidence_interval_low: float | None = Field(default=None, ge=0, le=1)
    confidence_interval_high: float | None = Field(default=None, ge=0, le=1)
    confidence_interval_not_applicable_reason: str | None = None

    @field_validator("sampling_mode")
    @classmethod
    def validate_sampling_mode(cls, value: str) -> str:
        return _validate_mode(value, SAMPLING_MODE, "sampling_mode")

    @field_validator("feedback_mode")
    @classmethod
    def validate_feedback_mode(cls, value: str) -> str:
        return _validate_mode(value, FEEDBACK_MODE, "feedback_mode")

    @field_validator("memory_mode")
    @classmethod
    def validate_memory_mode(cls, value: str) -> str:
        return _validate_mode(value, MEMORY_MODE, "memory_mode")

    @field_validator("stopping_reason")
    @classmethod
    def validate_stopping_reason(cls, value: str) -> str:
        if value not in ALLOWED_STOPPING_REASONS:
            raise ValueError(f"stopping_reason must be one of {sorted(ALLOWED_STOPPING_REASONS)}")
        return value


class AdaptiveComparisonRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = ADAPTIVE_COMPARISON_SCHEMA_VERSION
    run_id: str
    provider: str
    model: str
    provider_model: str
    task_type: str
    attempt_budget_k: int = Field(ge=1)
    sampling_mode: str = SAMPLING_MODE
    feedback_mode: str = FEEDBACK_MODE
    memory_mode: str = MEMORY_MODE
    exp2_n: int = Field(ge=0)
    exp2_pass_at_1: float | None = Field(default=None, ge=0, le=1)
    bernoulli_success_at_k: float | None = Field(default=None, ge=0, le=1)
    bernoulli_expected_attempts: float | None = Field(default=None, ge=0)
    fixed_retry_observed_success: bool | None = None
    fixed_retry_attempts_to_success: int | None = Field(default=None, ge=1)
    fixed_retry_cumulative_latency_ms: float | None = Field(default=None, ge=0)
    adaptive_observed_success: bool
    adaptive_attempts_to_success: int | None = Field(default=None, ge=1)
    adaptive_cumulative_latency_ms: float = Field(ge=0)
    adaptive_solve_request_count: int = Field(ge=0)
    adaptive_reflection_request_count: int = Field(ge=0)
    adaptive_cumulative_cost_usd: float = Field(ge=0)
    scientific_wrong_count: int = Field(ge=0)
    protocol_failure_count: int = Field(ge=0)
    infrastructure_failure_count: int = Field(ge=0)
    baseline_label: str
    adaptive_label: str
    classification_change: str
    cutoff_note: str
    structural_bottleneck_tags: list[str] = Field(default_factory=list)
    persistent_failure_note: str | None = None
    confidence_interval_low: float | None = Field(default=None, ge=0, le=1)
    confidence_interval_high: float | None = Field(default=None, ge=0, le=1)
    confidence_interval_not_applicable_reason: str | None = None

    @field_validator("sampling_mode")
    @classmethod
    def validate_sampling_mode(cls, value: str) -> str:
        return _validate_mode(value, SAMPLING_MODE, "sampling_mode")

    @field_validator("feedback_mode")
    @classmethod
    def validate_feedback_mode(cls, value: str) -> str:
        return _validate_mode(value, FEEDBACK_MODE, "feedback_mode")

    @field_validator("memory_mode")
    @classmethod
    def validate_memory_mode(cls, value: str) -> str:
        return _validate_mode(value, MEMORY_MODE, "memory_mode")
