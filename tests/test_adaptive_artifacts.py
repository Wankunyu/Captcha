from datetime import datetime, timezone

import pytest

from adaptive_artifacts import (
    ADAPTIVE_ATTEMPT_SCHEMA_VERSION,
    ADAPTIVE_COMPARISON_SCHEMA_VERSION,
    ADAPTIVE_POLICY_STATE_SCHEMA_VERSION,
    ADAPTIVE_SUMMARY_SCHEMA_VERSION,
    FEEDBACK_MODE,
    MEMORY_MODE,
    SAMPLING_MODE,
    STOPPING_RULE,
    AdaptiveAttemptRecord,
    AdaptiveComparisonRow,
    AdaptivePolicyState,
    AdaptiveSummaryRow,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _policy_state(task_type: str = "Dice_Count", failed_attempt_count: int = 0) -> AdaptivePolicyState:
    return AdaptivePolicyState(
        task_type=task_type,
        failed_attempt_count=failed_attempt_count,
        tried_strategy_summaries=["Count visible objects before answering."],
        next_prompt_rules=["Use the declared answer schema."],
        updated_at=_now(),
    )


def test_adaptive_models_expose_schema_versions_and_modes() -> None:
    before = _policy_state()
    after = _policy_state(failed_attempt_count=1)

    attempt = AdaptiveAttemptRecord(
        run_id="run-1",
        attempt_id="run-1:Dice_Count:1:dice1",
        provider="openai",
        model="gpt-5",
        prompt_mode="optimized",
        task_type="Dice_Count",
        puzzle_id="dice1.png",
        attempt_index=1,
        attempt_budget_k=3,
        prior_failures=[],
        policy_state_before=before,
        policy_state_after=after,
        prompt_adaptation_metadata={"stopping_rule": STOPPING_RULE},
        parsed_answer={"answer_type": "number", "value": 3},
        correct=False,
        failure_class="scientific_wrong",
        latency_ms=120.0,
        tokens_in=10,
        tokens_out=5,
        cost_usd=0.01,
        cumulative_latency_ms=120.0,
        cumulative_cost_usd=0.01,
        stopping_reason="continue",
        timestamp=_now(),
    )
    summary = AdaptiveSummaryRow(
        run_id="run-1",
        provider="openai",
        model="gpt-5",
        task_type="Dice_Count",
        attempt_budget_k=3,
        solve_request_count=1,
        reflection_request_count=1,
        n_attempts=1,
        n_success=0,
        success_rate=0.0,
        expected_attempts=None,
        attempts_to_success=None,
        cumulative_latency_ms=120.0,
        cumulative_cost_usd=0.01,
        scientific_wrong_count=1,
        protocol_failure_count=0,
        infrastructure_failure_count=0,
        stopping_reason="continue",
        confidence_interval_low=None,
        confidence_interval_high=None,
        confidence_interval_not_applicable_reason=(
            "single adaptive session; repeated-run CI deferred to Phase 3"
        ),
    )
    comparison = AdaptiveComparisonRow(
        run_id="run-1",
        provider="openai",
        model="gpt-5",
        provider_model="openai/gpt-5",
        task_type="Dice_Count",
        attempt_budget_k=3,
        exp2_n=10,
        exp2_pass_at_1=0.1,
        bernoulli_success_at_k=0.271,
        bernoulli_expected_attempts=2.71,
        fixed_retry_observed_success=False,
        fixed_retry_attempts_to_success=None,
        fixed_retry_cumulative_latency_ms=None,
        adaptive_observed_success=False,
        adaptive_attempts_to_success=None,
        adaptive_cumulative_latency_ms=120.0,
        adaptive_solve_request_count=1,
        adaptive_reflection_request_count=1,
        adaptive_cumulative_cost_usd=0.01,
        scientific_wrong_count=1,
        protocol_failure_count=0,
        infrastructure_failure_count=0,
        baseline_label="hard",
        adaptive_label="hard",
        classification_change="unchanged",
        cutoff_note="40 percent cutoff is operational, not a universal security boundary.",
        structural_bottleneck_tags=["counting"],
        persistent_failure_note="Still failed after binary-feedback adaptation.",
        confidence_interval_low=None,
        confidence_interval_high=None,
        confidence_interval_not_applicable_reason=(
            "single adaptive session; repeated-run CI deferred to Phase 3"
        ),
    )

    assert before.schema_version == ADAPTIVE_POLICY_STATE_SCHEMA_VERSION
    assert attempt.schema_version == ADAPTIVE_ATTEMPT_SCHEMA_VERSION
    assert summary.schema_version == ADAPTIVE_SUMMARY_SCHEMA_VERSION
    assert comparison.schema_version == ADAPTIVE_COMPARISON_SCHEMA_VERSION
    assert attempt.sampling_mode == SAMPLING_MODE == "without-replacement"
    assert summary.feedback_mode == FEEDBACK_MODE == "binary-pass-fail"
    assert comparison.memory_mode == MEMORY_MODE == "explicit-policy-notes"
    assert attempt.prompt_adaptation_metadata["stopping_rule"] == "first-success-or-budget"


def test_policy_state_rejects_banned_text() -> None:
    with pytest.raises(ValueError):
        AdaptivePolicyState(
            task_type="Dice_Count",
            failed_attempt_count=1,
            tried_strategy_summaries=["ground_truth says 3"],
            next_prompt_rules=[],
            updated_at=_now(),
        )

    with pytest.raises(ValueError):
        AdaptivePolicyState(
            task_type="Dice_Count",
            failed_attempt_count=1,
            tried_strategy_summaries=[],
            next_prompt_rules=["raw_response transcript"],
            updated_at=_now(),
        )
