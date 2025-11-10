#!/usr/bin/env python3
"""
分析 Anthropic Claude 实验中的两个主要问题：
1. 图片超过 5MB 限制
2. 模型输出 1-based 索引而非 0-based
"""

import os
import csv
import re
from collections import defaultdict

def analyze_errors():
    """分析错误文件"""
    errors_csv = "./error_analysis/exp1/anthropic/claude-sonnet-4-5/exp1_gt/errors.csv"

    # 统计超过 5MB 的图片
    size_errors = defaultdict(list)

    # 统计 1-based 索引问题
    index_errors = defaultdict(list)

    with open(errors_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_type = row['type']
            puzzle_id = row['puzzle_id']
            raw_response = row['raw_response']
            parsed = row['parsed']
            ground_truth = row['ground_truth']

            # 检查 5MB 限制错误
            if 'image exceeds 5 MB maximum' in raw_response:
                # 提取文件大小
                match = re.search(r'(\d+) bytes > 5242880 bytes', raw_response)
                if match:
                    file_size_bytes = int(match.group(1))
                    file_size_mb = file_size_bytes / (1024 * 1024)
                    size_errors[task_type].append({
                        'puzzle_id': puzzle_id,
                        'size_mb': file_size_mb
                    })

            # 检查索引问题 - 如果预测比 GT 大 1，可能是 1-based
            if parsed and ground_truth:
                # Select_Animal: 预测 5/6 而 GT 是 4/5
                if task_type == 'Select_Animal':
                    try:
                        import json
                        pred = json.loads(parsed)
                        gt = json.loads(ground_truth)
                        if 'indices' in pred and 'indices_gt' in gt:
                            pred_indices = pred['indices']
                            gt_indices = gt['indices_gt']
                            # 检查是否所有预测都比 GT 大 1
                            if len(pred_indices) == len(gt_indices):
                                diff = [p - g for p, g in zip(sorted(pred_indices), sorted(gt_indices))]
                                if all(d == 1 for d in diff):
                                    index_errors[task_type].append({
                                        'puzzle_id': puzzle_id,
                                        'predicted': pred_indices,
                                        'ground_truth': gt_indices,
                                        'diff': diff
                                    })
                    except:
                        pass

    return size_errors, index_errors

def main():
    print("=" * 80)
    print("Anthropic Claude 实验问题分析")
    print("=" * 80)
    print()

    size_errors, index_errors = analyze_errors()

    # 问题 1: 图片大小超过 5MB
    print("问题 1: 图片超过 5MB 限制 (Anthropic API 限制)")
    print("-" * 80)

    total_size_errors = sum(len(v) for v in size_errors.values())
    print(f"共发现 {total_size_errors} 个文件超过 5MB 限制\n")

    for task_type, files in sorted(size_errors.items()):
        print(f"📦 {task_type}: {len(files)} 个文件")
        for file_info in files:
            print(f"  - {file_info['puzzle_id']}: {file_info['size_mb']:.2f} MB")
        print()

    print("解决方案:")
    print("1. 方案 A: 压缩图片到 5MB 以下（推荐）")
    print("   - 使用 PIL/Pillow 压缩图片质量")
    print("   - 保持零转换管道，只在超限时压缩")
    print("   - 实现方式：检测 base64 大小，超过阈值则压缩")
    print()
    print("2. 方案 B: 跳过超限图片（不推荐）")
    print("   - 这些题目将无法评测")
    print("   - 影响实验完整性")
    print()
    print("3. 方案 C: 使用其他模型测试这些图片")
    print("   - OpenAI/Gemini 可能有更高的限制")
    print()

    # 问题 2: 1-based 索引
    print("=" * 80)
    print("问题 2: 模型输出 1-based 索引")
    print("-" * 80)

    # 手动分析发现的 1-based 问题
    one_based_tasks = {
        "Select_Animal": "所有预测索引都比 GT 大 1 (预测 5/6，GT 是 4/5)",
        "Image_Matching": "索引超出范围或偏移 1-2",
        "Connect_Icon": "索引偏移",
        "Dart_Count": "索引偏移",
        "Coordinates": "索引偏移",
        "Path_Finder": "可能存在索引偏移",
        "Patch_Select": "部分索引可能偏移",
        "Image_Recognition": "可能存在索引偏移",
        "Unusual_Detection": "可能存在索引偏移"
    }

    print(f"发现 {len(one_based_tasks)} 个任务类型可能存在 1-based 索引问题：\n")

    for task_type, description in one_based_tasks.items():
        print(f"📦 {task_type}")
        print(f"  问题: {description}")
        print()

    print("解决方案:")
    print("在 prompts_optimized.yaml 中为所有索引类型任务添加明确说明：")
    print("  - 'Indices are 0-based (starting from 0, not 1)'")
    print("  - 'Index 0 represents the first item'")
    print("  - 'Valid indices range from 0 to N-1 for N items'")
    print()

    print("=" * 80)
    print("需要修改的任务类型")
    print("=" * 80)
    print()

    tasks_need_index_clarification = [
        "Image_Matching",
        "Patch_Select",
        "Select_Animal",
        "Image_Recognition",
        "Unusual_Detection",
        "Path_Finder",
        "Dart_Count",
        "Coordinates",
        "Connect_Icon",
        "Object_Match"
    ]

    print("需要在 prompt 中添加 0-based 索引说明的任务类型：")
    for task in tasks_need_index_clarification:
        print(f"  ✓ {task}")

    print()
    print("注意: Bingo 已经在 prompts_optimized.yaml 中添加了 0-based 说明")

if __name__ == "__main__":
    main()
