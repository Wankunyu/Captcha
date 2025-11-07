#!/usr/bin/env python3
"""Test if prompts are loaded correctly"""

import yaml

# Manually simulate _load_prompts_yaml
with open("./prompts_optimized.yaml", "r", encoding="utf-8") as f:
    data = yaml.safe_load(f) or {}

# Check structure
print("="*80)
print("Test 1: Raw YAML structure")
print("="*80)
print(f"Top-level keys: {list(data.keys())}")

# Simulate _load_prompts_yaml logic
if data and "types" not in data and "default" not in data and "by_id" not in data:
    data = {"version": 0, "types": data}
data.setdefault("default", {})
data.setdefault("types", {})
data.setdefault("templates", {})
data.setdefault("by_id", {})

print(f"\nAfter processing:")
print(f"  Top-level keys: {list(data.keys())}")
print(f"  Number of task types: {len(data.get('types', {}))}")
print(f"  Task types: {sorted(list(data.get('types', {}).keys()))}")

# Test resolving prompts
print("\n" + "="*80)
print("Test 2: Resolving prompts for specific tasks")
print("="*80)

def resolve_prompt(cfg, task_type):
    tcfg = cfg.get("types", {}).get(task_type, {})
    dcfg = cfg.get("default", {})

    # Check if old format (string)
    if isinstance(tcfg, str):
        return {"mode": "replace", "rules": None, "override": tcfg}

    mode = tcfg.get("mode") or dcfg.get("mode") or "merge"
    rules = tcfg.get("rules") or dcfg.get("rules")

    return {"mode": mode, "rules": rules}

test_tasks = ["Dice_Count", "Geometry_Click", "Place_Dot", "Path_Finder", "Image_Matching"]
for task_type in test_tasks:
    resolved = resolve_prompt(data, task_type)
    print(f"\n{task_type}:")
    print(f"  mode: {resolved['mode']}")
    print(f"  has_rules: {bool(resolved['rules'])}")
    if resolved.get('override'):
        print(f"  override (first 100 chars): {resolved['override'][:100]}...")
    elif resolved['rules']:
        print(f"  rules (first 100 chars): {resolved['rules'][:100]}...")

# Test non-existent task
print("\n" + "="*80)
print("Test 3: Non-existent task (should use default merge)")
print("="*80)
resolved = resolve_prompt(data, "NonExistentTask")
print(f"mode: {resolved['mode']}")
print(f"has_rules: {bool(resolved['rules'])}")
