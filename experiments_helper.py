#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
精简版实验辅助模块 - 仅包含三个实验必需的扩展功能
保持与原始 run_eval.py 的兼容性
"""

import os
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
from dataclasses import dataclass

# ==================== 数据结构 ====================

@dataclass
class ErrorCase:
    """错误案例记录"""
    task_type: str
    puzzle_id: str
    prompt: str
    gt: Dict[str, Any]
    raw: str
    parsed: Optional[Dict[str, Any]]
    pass1: bool
    e2e_ms: float
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    error_description: Optional[str] = None  # 错误描述（由代码生成）
    reasoning: Optional[str] = None  # 模型的详细推理过程（可选）

# ==================== 错误收集器 ====================

class SimpleErrorCollector:
    """简化版错误收集器 - 仅收集错误案例和基本统计"""

    def __init__(self, experiment_name: str = "exp"):
        self.experiment_name = experiment_name
        self.errors: List[ErrorCase] = []
        self.stats = defaultdict(lambda: {"total": 0, "correct": 0, "tokens_in": 0, "tokens_out": 0})

    def record(self, task_type: str, puzzle_id: str, prompt: str, gt: Dict,
               raw: str, parsed: Optional[Dict], pass1: bool, meta: Dict,
               error_description: Optional[str] = None, reasoning: Optional[str] = None):
        """记录一个测试案例"""
        # 更新统计
        self.stats[task_type]["total"] += 1
        if pass1:
            self.stats[task_type]["correct"] += 1

        tokens_in = meta.get("tokens_in")
        tokens_out = meta.get("tokens_out")
        if tokens_in:
            self.stats[task_type]["tokens_in"] += tokens_in
        if tokens_out:
            self.stats[task_type]["tokens_out"] += tokens_out

        # 仅收集错误案例
        if not pass1:
            err_desc = (error_description or "").strip()
            if len(err_desc) > 300:
                err_desc = err_desc[:300]  # 截断避免过长

            self.errors.append(ErrorCase(
                task_type=task_type,
                puzzle_id=puzzle_id,
                prompt=prompt[:200],  # 截断避免过长
                gt=gt,
                raw=(raw or "")[:500],  # 截断
                parsed=parsed,
                pass1=pass1,
                e2e_ms=meta.get("e2e_ms", 0),
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                error_description=err_desc or None,
                reasoning=(reasoning or None)
            ))

    def save_summary(self, output_dir: str):
        """保存统计摘要"""
        os.makedirs(output_dir, exist_ok=True)

        # 1. 保存错误案例
        errors_file = os.path.join(output_dir, "errors.csv")
        with open(errors_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "type",
                "puzzle_id",
                "raw_response",
                "parsed",
                "ground_truth",
                "error_description",
                "reasoning",
                "tokens_in",
                "tokens_out"
            ])
            for err in self.errors:
                # 从 parsed 中移除 reasoning 字段以避免重复
                parsed_without_reasoning = err.parsed.copy() if err.parsed else None
                if parsed_without_reasoning and "reasoning" in parsed_without_reasoning:
                    parsed_without_reasoning.pop("reasoning")

                writer.writerow([
                    err.task_type,
                    err.puzzle_id,
                    err.raw,
                    json.dumps(parsed_without_reasoning) if parsed_without_reasoning else "",
                    json.dumps(err.gt),
                    (err.error_description or ""),
                    err.reasoning or "",
                    err.tokens_in if err.tokens_in is not None else 0,
                    err.tokens_out if err.tokens_out is not None else 0
                ])

        # 2. 保存统计数据
        stats_file = os.path.join(output_dir, "stats.json")
        stats_data = {
            "experiment": self.experiment_name,
            "by_task_type": {}
        }

        total_correct = 0
        total_cases = 0
        total_tokens_in = 0
        total_tokens_out = 0

        for task_type, data in self.stats.items():
            stats_data["by_task_type"][task_type] = {
                "total": data["total"],
                "correct": data["correct"],
                "pass1": data["correct"] / data["total"] if data["total"] > 0 else 0,
                "tokens_in": data["tokens_in"],
                "tokens_out": data["tokens_out"]
            }
            total_correct += data["correct"]
            total_cases += data["total"]
            total_tokens_in += data["tokens_in"]
            total_tokens_out += data["tokens_out"]

        stats_data["overall"] = {
            "total_cases": total_cases,
            "total_correct": total_correct,
            "overall_pass1": total_correct / total_cases if total_cases > 0 else 0,
            "total_tokens_in": total_tokens_in,
            "total_tokens_out": total_tokens_out,
            "total_tokens": total_tokens_in + total_tokens_out
        }

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, indent=2, ensure_ascii=False)

        token_summary_file = os.path.join(output_dir, "token_summary.json")
        token_summary = {
            "experiment": self.experiment_name,
            "overall": {
                "total_questions": total_cases,
                "total_tokens_in": total_tokens_in,
                "total_tokens_out": total_tokens_out,
                "total_tokens": total_tokens_in + total_tokens_out
            },
            "by_task_type": {
                task_type: {
                    "count": data["total"],
                    "tokens_in": data["tokens_in"],
                    "tokens_out": data["tokens_out"],
                    "total_tokens": data["tokens_in"] + data["tokens_out"]
                }
                for task_type, data in sorted(self.stats.items())
            }
        }
        with open(token_summary_file, 'w', encoding='utf-8') as f:
            json.dump(token_summary, f, indent=2, ensure_ascii=False)

        print(f"✅ 错误分析已保存到: {output_dir}")
        print(f"   - 错误案例: {errors_file}")
        print(f"   - 统计数据: {stats_file}")
        print(f"   - Token 汇总: {token_summary_file}")

# ==================== 三实验对比 ====================

def compare_experiments(exp1_dir: str, exp2_dir: str, exp3_dir: Optional[str] = None):
    """对比三个实验的结果"""

    def load_stats(dir_path: str) -> Dict:
        stats_file = os.path.join(dir_path, "stats.json")
        if not os.path.exists(stats_file):
            return None
        with open(stats_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    exp1_stats = load_stats(exp1_dir)
    exp2_stats = load_stats(exp2_dir)
    exp3_stats = load_stats(exp3_dir) if exp3_dir else None

    if not exp1_stats or not exp2_stats:
        print("⚠️ 无法加载实验统计数据")
        return

    print("\n" + "="*80)
    print("三实验对比分析")
    print("="*80)

    # 总体对比
    print("\n【总体性能】")
    print(f"{'指标':<20} {'实验一(GT)':<15} {'实验二(优化)':<15}", end="")
    if exp3_stats:
        print(f" {'实验三(迭代)':<15}")
    else:
        print()

    print("-" * 80)

    exp1_overall = exp1_stats["overall"]
    exp2_overall = exp2_stats["overall"]

    print(f"{'Pass@1':<20} {exp1_overall['overall_pass1']:<15.2%} {exp2_overall['overall_pass1']:<15.2%}", end="")
    if exp3_stats:
        print(f" {exp3_stats['overall']['overall_pass1']:<15.2%}")
    else:
        print()

    print(f"{'总Token数':<20} {exp1_overall['total_tokens']:<15,} {exp2_overall['total_tokens']:<15,}", end="")
    if exp3_stats:
        print(f" {exp3_stats['overall']['total_tokens']:<15,}")
    else:
        print()

    # 按任务类型对比
    print("\n【按任务类型 Pass@1】")
    print(f"{'任务类型':<20} {'实验一':<12} {'实验二':<12} {'提升':<10}")
    print("-" * 80)

    for task_type in sorted(exp1_stats["by_task_type"].keys()):
        exp1_pass1 = exp1_stats["by_task_type"][task_type]["pass1"]
        exp2_pass1 = exp2_stats["by_task_type"].get(task_type, {}).get("pass1", 0)
        improvement = exp2_pass1 - exp1_pass1

        print(f"{task_type:<20} {exp1_pass1:<12.2%} {exp2_pass1:<12.2%} {improvement:+.2%}")

    print("="*80)

# ==================== 数据加载辅助（适配 ground_truth.json 格式）====================

def load_tasks_from_ground_truth(dataset_root: str, task_types: List[str], max_per_type: int = 15) -> List[Dict]:
    """
    从 ground_truth.json 格式加载任务
    返回标准的 task 列表: [{"type", "puzzle_id", "images", "prompt", "gt"}, ...]
    """
    tasks = []

    for task_type in task_types:
        type_dir = Path(dataset_root) / task_type
        gt_file = type_dir / "ground_truth.json"

        if not gt_file.exists():
            print(f"⚠️ 跳过 {task_type}: 未找到 ground_truth.json")
            continue

        try:
            with open(gt_file, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"⚠️ {task_type}/ground_truth.json 格式错误: {e}")
            continue

        count = 0
        for img_filename, data in all_data.items():
            if count >= max_per_type:
                break

            # 构建图片路径列表
            images = []
            img_path = str(type_dir / img_filename)
            if os.path.exists(img_path):
                images.append(img_path)

            # 处理第二张图（如 Click_Order 的 order_image）
            if "order_image" in data:
                order_img = str(type_dir / data["order_image"])
                if os.path.exists(order_img):
                    images.append(order_img)

            # 标准化 ground truth 格式
            gt = _normalize_ground_truth(task_type, data)

            tasks.append({
                "type": task_type,
                "puzzle_id": img_filename.replace(".png", "").replace(".jpg", ""),
                "images": images,
                "prompt": data.get("prompt", ""),
                "gt": gt
            })
            count += 1

    return tasks

def _normalize_ground_truth(task_type: str, data: Dict) -> Dict:
    """标准化不同任务类型的 ground truth 格式"""
    if task_type == "Dice_Count":
        return {"sum": data.get("sum")}

    elif task_type == "Click_Order":
        return {
            "points_gt": [{"x": p[0], "y": p[1]} for p in data.get("answer", [])],
            "tolerance": data.get("tolerance", 40.0)
        }

    elif task_type == "Patch_Select":
        return {"indices_gt": data.get("correct_patches", data.get("answer", []))}

    elif task_type in ("Place_Dot", "Geometry_Click"):
        target = data.get("target_position", data.get("answer"))
        if isinstance(target, list) and len(target) == 2:
            return {
                "target_position": {"x": target[0], "y": target[1]},
                "tolerance": data.get("tolerance", 15.0)
            }
        elif isinstance(target, dict):
            return {
                "target_position": {"x": target.get("x", 0), "y": target.get("y", 0)},
                "tolerance": data.get("tolerance", 15.0)
            }
        else:
            return {"target_position": {"x": 0, "y": 0}, "tolerance": 15.0}

    else:
        # 通用格式
        return data.get("answer", {})

# ==================== 导出函数 ====================

__all__ = [
    'ErrorCase',
    'SimpleErrorCollector',
    'compare_experiments',
    'load_tasks_from_ground_truth',
]

if __name__ == "__main__":
    print("实验辅助模块已加载")
    print("可用函数:")
    print("  - SimpleErrorCollector: 简化的错误收集器")
    print("  - compare_experiments: 对比三个实验结果")
    print("  - load_tasks_from_ground_truth: 从 ground_truth.json 加载任务")
