import json
from typing import Any

from adaptive_artifacts import (
    FEEDBACK_MODE,
    MEMORY_MODE,
    SAMPLING_MODE,
    STOPPING_RULE,
    AdaptivePolicyState,
)
from revision_artifacts import utc_now

import run_eval


def group_tasks_by_type(
    tasks: list[run_eval.TaskItem],
) -> dict[str, list[run_eval.TaskItem]]:
    grouped: dict[str, list[run_eval.TaskItem]] = {}
    for task in tasks:
        grouped.setdefault(task.type, []).append(task)
    return grouped


def build_adapted_prompt(
    base_prompt: str,
    policy_state: AdaptivePolicyState,
) -> tuple[str, dict[str, Any]]:
    lines = [base_prompt.rstrip()]
    if policy_state.failed_attempt_count or policy_state.tried_strategy_summaries:
        lines.extend(
            [
                "",
                "Adaptive policy notes:",
                f"- Failed attempts for this task type: {policy_state.failed_attempt_count}",
            ]
        )
        for summary in policy_state.tried_strategy_summaries:
            lines.append(f"- Tried strategy: {summary}")
        for rule in policy_state.next_prompt_rules:
            lines.append(f"- Next prompt rule: {rule}")
    metadata = {
        "sampling_mode": SAMPLING_MODE,
        "feedback_mode": FEEDBACK_MODE,
        "memory_mode": MEMORY_MODE,
        "stopping_rule": STOPPING_RULE,
        "failed_attempt_count": policy_state.failed_attempt_count,
        "tried_strategy_summary_count": len(policy_state.tried_strategy_summaries),
        "next_prompt_rule_count": len(policy_state.next_prompt_rules),
    }
    return "\n".join(lines), metadata


def build_reflection_prompt(
    current_prompt: str,
    raw_answer: str,
    parsed_answer: Any,
    passed: bool = False,
) -> str:
    feedback = "PASS" if passed else "FAIL"
    parsed_text = json.dumps(parsed_answer, ensure_ascii=False, sort_keys=True)
    return "\n".join(
        [
            "Review your last CAPTCHA-solving attempt and propose a reusable policy note.",
            "Use only the facts shown here. Return JSON matching the requested schema.",
            "",
            "Current prompt:",
            current_prompt,
            "",
            "Your raw answer:",
            raw_answer,
            "",
            "Your parsed answer:",
            parsed_text,
            "",
            f"Feedback: {feedback}",
        ]
    )


def reflection_json_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "tried_strategy_summary": {
                "type": "string",
                "maxLength": 300,
            },
            "next_prompt_rule": {
                "type": "string",
                "maxLength": 500,
            },
        },
        "required": ["tried_strategy_summary", "next_prompt_rule"],
        "additionalProperties": False,
    }


def parse_policy_state(
    task_type: str,
    previous: AdaptivePolicyState,
    parsed_note: dict[str, Any] | None,
) -> AdaptivePolicyState:
    note = parsed_note or {}
    tried_strategy_summary = str(note.get("tried_strategy_summary") or "").strip()
    next_prompt_rule = str(note.get("next_prompt_rule") or "").strip()
    tried_strategy_summaries = list(previous.tried_strategy_summaries)
    next_prompt_rules = list(previous.next_prompt_rules)
    if tried_strategy_summary:
        tried_strategy_summaries.append(tried_strategy_summary)
    if next_prompt_rule:
        next_prompt_rules.append(next_prompt_rule)
    return AdaptivePolicyState(
        task_type=task_type,
        failed_attempt_count=previous.failed_attempt_count + 1,
        tried_strategy_summaries=tried_strategy_summaries,
        next_prompt_rules=next_prompt_rules,
        updated_at=utc_now(),
    )


def classify_failure(
    raw: str,
    parsed: Any,
    correct: bool,
    provider_exception: Exception | None = None,
) -> str:
    if correct:
        return "none"
    if provider_exception is not None:
        return "infrastructure_failure"
    if isinstance(raw, str) and raw.startswith("__ERROR__"):
        return "infrastructure_failure"
    if parsed is None or not isinstance(parsed, dict):
        return "protocol_failure"
    return "scientific_wrong"
