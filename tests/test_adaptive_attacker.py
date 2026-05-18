import inspect

import pytest

import run_eval
from adaptive_artifacts import AdaptivePolicyState
from revision_artifacts import utc_now

import adaptive_attacker


def _policy_state() -> AdaptivePolicyState:
    return AdaptivePolicyState(
        task_type="Dice_Count",
        failed_attempt_count=1,
        tried_strategy_summaries=["Checked the most visible foreground objects first."],
        next_prompt_rules=["Double-check occluded objects before producing JSON."],
        updated_at=utc_now(),
    )


def test_helper_signatures_do_not_accept_task_ground_truth() -> None:
    reflection_signature = inspect.signature(adaptive_attacker.build_reflection_prompt)
    assert list(reflection_signature.parameters) == [
        "current_prompt",
        "raw_answer",
        "parsed_answer",
        "passed",
    ]
    assert "TaskItem" not in str(reflection_signature)
    assert "gt" not in str(reflection_signature)

    adapted_signature = inspect.signature(adaptive_attacker.build_adapted_prompt)
    assert list(adapted_signature.parameters) == ["base_prompt", "policy_state"]


def test_group_tasks_by_type_preserves_task_instances() -> None:
    tasks = [
        run_eval.TaskItem("Dice_Count", "dice1.png", "prompt 1", [], {"sum": 3}),
        run_eval.TaskItem("Patch_Select", "patch1.png", "prompt 2", [], {"correct_patches": [1]}),
        run_eval.TaskItem("Dice_Count", "dice2.png", "prompt 3", [], {"sum": 4}),
    ]

    grouped = adaptive_attacker.group_tasks_by_type(tasks)

    assert list(grouped) == ["Dice_Count", "Patch_Select"]
    assert [task.puzzle_id for task in grouped["Dice_Count"]] == ["dice1.png", "dice2.png"]
    assert grouped["Patch_Select"][0] is tasks[1]


def test_adapted_prompt_and_reflection_prompt_do_not_leak_sentinel_ground_truth() -> None:
    sentinel = "SECRET_GT_COORDINATE_999"
    task = run_eval.TaskItem(
        "Geometry_Click",
        "geometry1.png",
        "Click the marked target.",
        [],
        {"bbox": sentinel},
    )
    policy_state = _policy_state()

    adapted_prompt, metadata = adaptive_attacker.build_adapted_prompt(
        task.prompt,
        policy_state,
    )
    reflection_prompt = adaptive_attacker.build_reflection_prompt(
        current_prompt=adapted_prompt,
        raw_answer='{"answer_type":"single_point","point":{"x":1,"y":2}}',
        parsed_answer={"answer_type": "single_point", "point": {"x": 1, "y": 2}},
    )
    next_state = adaptive_attacker.parse_policy_state(
        task.type,
        policy_state,
        {
            "tried_strategy_summary": "The attempted point was selected from visible marks.",
            "next_prompt_rule": "Inspect all visible target-like marks before choosing one point.",
        },
    )

    serialized = "\n".join(
        [
            adapted_prompt,
            str(metadata),
            reflection_prompt,
            next_state.model_dump_json(),
        ]
    )
    assert "Feedback: FAIL" in reflection_prompt
    assert sentinel not in serialized


def test_reflection_schema_only_requires_strategy_and_next_rule() -> None:
    schema = adaptive_attacker.reflection_json_schema()

    assert schema["type"] == "object"
    assert schema["required"] == ["tried_strategy_summary", "next_prompt_rule"]
    assert set(schema["properties"]) == {"tried_strategy_summary", "next_prompt_rule"}
    assert schema["properties"]["tried_strategy_summary"]["maxLength"] == 300
    assert schema["properties"]["next_prompt_rule"]["maxLength"] == 500


def test_parse_policy_state_updates_memory_and_rejects_leaky_notes() -> None:
    previous = _policy_state()

    updated = adaptive_attacker.parse_policy_state(
        "Dice_Count",
        previous,
        {
            "tried_strategy_summary": "Counted only clear top faces.",
            "next_prompt_rule": "Separate top faces from side faces before answering.",
        },
    )

    assert updated.failed_attempt_count == 2
    assert updated.tried_strategy_summaries[-1] == "Counted only clear top faces."
    assert updated.next_prompt_rules[-1] == "Separate top faces from side faces before answering."

    with pytest.raises(ValueError):
        adaptive_attacker.parse_policy_state(
            "Dice_Count",
            previous,
            {
                "tried_strategy_summary": "ground_truth says 3",
                "next_prompt_rule": "Use the answer directly.",
            },
        )


def test_classify_failure_values() -> None:
    assert adaptive_attacker.classify_failure("{}", {}, True) == "none"
    assert (
        adaptive_attacker.classify_failure("{}", {}, False, provider_exception=RuntimeError("boom"))
        == "infrastructure_failure"
    )
    assert adaptive_attacker.classify_failure("__ERROR__: timeout", None, False) == (
        "infrastructure_failure"
    )
    assert adaptive_attacker.classify_failure("not json", None, False) == "protocol_failure"
    assert adaptive_attacker.classify_failure("[]", [], False) == "protocol_failure"
    assert adaptive_attacker.classify_failure("{}", {"answer_type": "number"}, False) == (
        "scientific_wrong"
    )
