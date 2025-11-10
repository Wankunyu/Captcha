#!/usr/bin/env python3
"""
批量更新 ground_truth.json 文件，添加 0-based 索引说明
"""

import json
import os
from pathlib import Path

# 定义需要添加索引说明的任务类型及其对应的索引说明模板
TASK_INDEX_TEMPLATES = {
    "Image_Matching": """
Indexing Rules:
- Indices are 0-based (starting from 0, not 1)
- Index 0 represents the first option
- If there are N options, valid indices are 0 to N-1
- If multiple candidates appear valid, choose the smallest index""",

    "Patch_Select": """
Indexing Rules:
- Indices are 0-based (starting from 0, not 1) and row-major
- Index 0 is the top-left cell, index 1 is to its right, etc.
- For a 5×5 grid: indices 0-4 are row 1, indices 5-9 are row 2, etc.
- Return a unique ascending set of indices""",

    "Select_Animal": """
Indexing Rules:
- Indices are 0-based (starting from 0, not 1) and row-major
- Index 0 is the first cell, index 1 is the second cell, etc.
- Deduplicate and sort ascending""",

    "Unusual_Detection": """
Indexing Rules:
- Indices are 0-based (starting from 0, not 1) and row-major
- Index 0 is the first item, index 1 is the second item, etc.
- Return a unique ascending set""",

    "Path_Finder": """
Indexing Rules:
- Indices are 0-based (starting from 0, not 1) and row-major when applicable
- Index 0 is the first option/cell
- For ties in classify mode: choose the smallest index
- For multi-select mode: include all valid cells""",

    "Dart_Count": """
Indexing Rules:
- Indices are 0-based (starting from 0, not 1)
- Index 0 represents the first option
- If multiple candidates fit, choose the smallest index""",

    "Coordinates": """
Indexing Rules:
- Indices are 0-based (starting from 0, not 1)
- Index 0 represents the first option
- If multiple options appear correct, choose the smallest index""",

    "Connect_Icon": """
Indexing Rules:
- Indices are 0-based (starting from 0, not 1)
- Index 0 represents the first option
- If multiple candidates fit, choose the smallest index""",

    "Object_Match": """
Indexing Rules:
- Indices are 0-based (starting from 0, not 1)
- Index 0 represents the first option
- If still tied, choose the smallest index""",

    "Image_Recognition": """
Indexing Rules:
- Indices are 0-based (starting from 0, not 1) and row-major
- Index 0 is the first image, index 1 is the second image, etc.
- Return a unique ascending set"""
}

def update_ground_truth(task_type: str, index_template: str):
    """更新指定任务类型的 ground_truth.json 文件"""

    # 构建文件路径（处理可能的目录名变体）
    base_dir = Path("./captcha_data")
    possible_dirs = [
        base_dir / task_type,
        base_dir / task_type.replace("_", ""),
        base_dir / task_type.replace("_", " "),
    ]

    gt_path = None
    for dir_path in possible_dirs:
        potential_path = dir_path / "ground_truth.json"
        if potential_path.exists():
            gt_path = potential_path
            break

    if not gt_path:
        print(f"⚠️  未找到 {task_type} 的 ground_truth.json")
        return False

    # 读取 JSON 文件
    try:
        with open(gt_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 读取 {gt_path} 失败: {e}")
        return False

    # 更新每个样本的 prompt
    updated_count = 0
    for key, item in data.items():
        if 'prompt' in item:
            original_prompt = item['prompt']

            # 检查是否已经包含索引说明
            if "Indexing Rules" in original_prompt or "0-based" in original_prompt:
                continue

            # 添加索引说明
            new_prompt = original_prompt.rstrip() + index_template
            item['prompt'] = new_prompt
            updated_count += 1

    if updated_count == 0:
        print(f"✓ {task_type}: 所有 prompt 已包含索引说明，跳过")
        return True

    # 写回 JSON 文件
    try:
        with open(gt_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ {task_type}: 更新了 {updated_count} 个样本的 prompt")
        return True
    except Exception as e:
        print(f"❌ 写入 {gt_path} 失败: {e}")
        return False

def main():
    print("=" * 80)
    print("批量更新 ground_truth.json 文件，添加 0-based 索引说明")
    print("=" * 80)
    print()

    success_count = 0
    fail_count = 0

    for task_type, index_template in TASK_INDEX_TEMPLATES.items():
        if update_ground_truth(task_type, index_template):
            success_count += 1
        else:
            fail_count += 1

    print()
    print("=" * 80)
    print(f"完成: 成功 {success_count} 个，失败 {fail_count} 个")
    print("=" * 80)

if __name__ == "__main__":
    main()
