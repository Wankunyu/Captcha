#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动生成 Few-shot 示例配置文件

从 captcha_data 中提取每种任务类型的前 N 个样本作为 few-shot 示例，
生成 few_shot_examples.yaml 配置文件。
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List


def extract_few_shot_examples(
    dataset_root: str = "./captcha_data",
    n_shot: int = 2,
    output_file: str = "./few_shot_examples.yaml"
):
    """
    从数据集中提取 few-shot 示例

    Args:
        dataset_root: 数据集根目录
        n_shot: 每种类型提取的示例数量
        output_file: 输出的 yaml 配置文件路径
    """

    dataset_path = Path(dataset_root)
    few_shot_config = {}

    # 遍历所有任务类型目录
    task_types = sorted([d.name for d in dataset_path.iterdir() if d.is_dir()])

    print(f"正在扫描 {len(task_types)} 种任务类型...")
    print("=" * 80)

    for task_type in task_types:
        type_dir = dataset_path / task_type
        gt_file = type_dir / "ground_truth.json"

        # 跳过没有 ground_truth.json 的目录
        if not gt_file.exists():
            print(f"⚠️  跳过 {task_type}: 缺少 ground_truth.json")
            continue

        try:
            # 读取 ground_truth.json
            with open(gt_file, 'r', encoding='utf-8') as f:
                ground_truth = json.load(f)

            # 提取前 n_shot 个样本
            examples = []
            for i, (filename, data) in enumerate(ground_truth.items()):
                if i >= n_shot:
                    break

                example = {"filename": filename}

                # 根据任务类型提取答案
                answer = extract_answer(task_type, data)
                if answer is not None:
                    example["answer"] = answer

                # 处理特殊字段（如 Click_Order 的 order_image）
                if "order_image" in data:
                    example["order_image"] = data["order_image"]

                if "tolerance" in data:
                    example["tolerance"] = data["tolerance"]

                examples.append(example)

            if examples:
                few_shot_config[task_type] = {"examples": examples}
                print(f"✅ {task_type}: 提取 {len(examples)} 个示例")
            else:
                print(f"⚠️  {task_type}: 未找到有效示例")

        except Exception as e:
            print(f"❌ {task_type}: 处理失败 - {e}")

    # 保存为 yaml 文件
    print("\n" + "=" * 80)
    print(f"正在保存到 {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(few_shot_config, f,
                  default_flow_style=False,
                  allow_unicode=True,
                  sort_keys=False)

    print(f"✅ 成功生成 {output_file}")
    print(f"   包含 {len(few_shot_config)} 种任务类型")
    print(f"   每种类型 {n_shot} 个示例")

    return few_shot_config


def extract_answer(task_type: str, data: Dict[str, Any]) -> Any:
    """
    根据任务类型提取答案并转换为标准格式

    Args:
        task_type: 任务类型名称
        data: ground_truth 中的数据项

    Returns:
        标准化的答案格式
    """

    # Dice_Count: sum -> {"value": ...}
    if task_type == "Dice_Count":
        if "sum" in data:
            return {"value": data["sum"]}

    # Click_Order: answer (列表坐标) -> {"points": [{"x": ..., "y": ...}, ...]}
    elif task_type == "Click_Order":
        if "answer" in data:
            points = [{"x": p[0], "y": p[1]} for p in data["answer"]]
            return {"points": points}

    # Patch_Select: correct_patches -> {"indices": [...]}
    elif task_type == "Patch_Select":
        if "correct_patches" in data:
            return {"indices": data["correct_patches"]}
        elif "answer" in data:
            return {"indices": data["answer"]}

    # Place_Dot / Geometry_Click: target_position 或 answer -> {"point": {"x": ..., "y": ...}}
    elif task_type in ["Place_Dot", "Geometry_Click"]:
        target = data.get("target_position", data.get("answer"))
        if target:
            if isinstance(target, list) and len(target) == 2:
                return {"point": {"x": target[0], "y": target[1]}}
            elif isinstance(target, dict):
                return {"point": {"x": target.get("x", 0), "y": target.get("y", 0)}}

    # 其他类型：直接使用 answer 字段
    elif "answer" in data:
        answer = data["answer"]
        # 如果是整数（如选择题索引）
        if isinstance(answer, int):
            return {"choice": answer}
        # 如果是列表（如多选）
        elif isinstance(answer, list):
            # 如果是坐标列表
            if answer and isinstance(answer[0], list) and len(answer[0]) == 2:
                return {"points": [{"x": p[0], "y": p[1]} for p in answer]}
            # 如果是索引列表
            else:
                return {"indices": answer}
        # 其他格式直接返回
        else:
            return answer

    return None


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="生成 Few-shot 示例配置文件")
    parser.add_argument("--dataset", default="./captcha_data",
                       help="数据集根目录 (默认: ./captcha_data)")
    parser.add_argument("--n-shot", type=int, default=2,
                       help="每种类型提取的示例数量 (默认: 2)")
    parser.add_argument("--output", default="./few_shot_examples.yaml",
                       help="输出文件路径 (默认: ./few_shot_examples.yaml)")

    args = parser.parse_args()

    # 执行提取
    extract_few_shot_examples(
        dataset_root=args.dataset,
        n_shot=args.n_shot,
        output_file=args.output
    )


if __name__ == "__main__":
    main()
