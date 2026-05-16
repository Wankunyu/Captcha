from pathlib import Path

import yaml

from revision_preflight import DATASET_DIR_ALIASES, TASK_ALIASES
from run_eval import SUPPORTED_TYPES, build_tasks


IGNORED_NOT_USED_KEYS = {"Hold_Button(Not Used)", "Slide_Puzzle(Not Used)"}


def _canonical_task_type(task_type: str) -> str:
    return TASK_ALIASES.get(task_type, task_type)


def test_supported_types_have_dataset_directories() -> None:
    missing = []
    for task_type in sorted(SUPPORTED_TYPES):
        dataset_dir = Path("captcha_data") / DATASET_DIR_ALIASES.get(task_type, task_type)
        if not dataset_dir.is_dir():
            missing.append((task_type, str(dataset_dir)))

    assert not missing


def test_connect_icon_alias() -> None:
    assert TASK_ALIASES["Connect_icon"] == "Connect_Icon"
    assert DATASET_DIR_ALIASES["Connect_Icon"] == "Connect_icon"
    assert (Path("captcha_data") / DATASET_DIR_ALIASES["Connect_Icon"]).is_dir()


def test_build_tasks_accepts_connect_icon_alias_and_canonical_name() -> None:
    alias_tasks = build_tasks("./captcha_data", ["Connect_icon"], max_per_type=1)
    canonical_tasks = build_tasks("./captcha_data", ["Connect_Icon"], max_per_type=1)

    assert alias_tasks
    assert canonical_tasks
    assert alias_tasks[0].type == "Connect_Icon"
    assert canonical_tasks[0].type == "Connect_Icon"


def test_prompt_keys_are_known() -> None:
    with open("prompts_optimized.yaml", "r", encoding="utf-8") as handle:
        prompts = yaml.safe_load(handle) or {}

    unknown = []
    for task_type in (prompts.get("types") or {}):
        canonical = _canonical_task_type(task_type)
        if canonical not in SUPPORTED_TYPES:
            unknown.append(task_type)

    assert not unknown


def test_few_shot_keys_are_known() -> None:
    with open("few_shot_examples.yaml", "r", encoding="utf-8") as handle:
        few_shot = yaml.safe_load(handle) or {}

    unknown = []
    for task_type in few_shot:
        if task_type in IGNORED_NOT_USED_KEYS:
            continue
        canonical = _canonical_task_type(task_type)
        if canonical not in SUPPORTED_TYPES:
            unknown.append(task_type)

    assert not unknown
