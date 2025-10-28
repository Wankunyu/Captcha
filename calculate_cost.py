#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API Cost 计算工具
根据 token_summary.json 计算各个实验的 API 使用成本
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any

# 定价表 (美元/百万 tokens)
PRICING = {
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},

    # Anthropic Claude
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},

    # Google Gemini
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00}, 
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50}, 
    "gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40},

    # Alibaba Qwen
    "qwen-vl-max": {"input": 0.20, "output": 0.60},  # 估算价格（人民币转美元）
    "qwen-vl-plus": {"input": 0.10, "output": 0.30},
}


def calculate_cost(tokens_in: int, tokens_out: int, model: str) -> float:
    """
    计算 API 调用成本

    Args:
        tokens_in: 输入 token 数
        tokens_out: 输出 token 数
        model: 模型名称

    Returns:
        成本（美元）
    """
    if model not in PRICING:
        print(f"⚠️  警告: 模型 '{model}' 未在定价表中，假设免费")
        return 0.0

    pricing = PRICING[model]

    # 转换为百万 tokens
    cost_in = (tokens_in / 1_000_000) * pricing["input"]
    cost_out = (tokens_out / 1_000_000) * pricing["output"]

    return cost_in + cost_out


def analyze_token_summary(token_summary_path: str, model: str) -> Dict[str, Any]:
    """
    分析 token_summary.json 并计算成本

    Args:
        token_summary_path: token_summary.json 文件路径
        model: 模型名称

    Returns:
        包含成本分析的字典
    """
    with open(token_summary_path, 'r', encoding='utf-8') as f:
        summary = json.load(f)

    overall = summary["overall"]

    # 计算总成本
    total_cost = calculate_cost(
        overall["total_tokens_in"],
        overall["total_tokens_out"],
        model
    )

    # 计算每题平均成本
    cost_per_question = total_cost / overall["total_questions"] if overall["total_questions"] > 0 else 0

    # 计算各任务类型成本
    by_type_costs = {}
    for task_type, stats in summary.get("by_task_type", {}).items():
        type_cost = calculate_cost(
            stats["tokens_in"],
            stats["tokens_out"],
            model
        )
        by_type_costs[task_type] = {
            "cost_usd": type_cost,
            "cost_per_question": type_cost / stats["count"] if stats["count"] > 0 else 0,
            "tokens_in": stats["tokens_in"],
            "tokens_out": stats["tokens_out"],
            "count": stats["count"]
        }

    return {
        "experiment": summary["experiment"],
        "model": model,
        "overall": {
            "total_questions": overall["total_questions"],
            "total_tokens_in": overall["total_tokens_in"],
            "total_tokens_out": overall["total_tokens_out"],
            "total_tokens": overall["total_tokens"],
            "total_cost_usd": total_cost,
            "cost_per_question_usd": cost_per_question
        },
        "by_task_type": by_type_costs,
        "pricing": PRICING.get(model, {"input": 0, "output": 0})
    }


def generate_cost_report(analysis: Dict[str, Any], output_path: str = None):
    """生成成本分析报告"""

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append(f"API Cost 分析报告 - {analysis['experiment']}")
    report_lines.append("=" * 80)
    report_lines.append(f"\n模型: {analysis['model']}")

    pricing = analysis['pricing']
    report_lines.append(f"定价: 输入=${pricing['input']:.2f}/M tokens, 输出=${pricing['output']:.2f}/M tokens")

    overall = analysis['overall']
    report_lines.append(f"\n## 总体统计\n")
    report_lines.append(f"- 总题目数: {overall['total_questions']:,}")
    report_lines.append(f"- 总输入 tokens: {overall['total_tokens_in']:,}")
    report_lines.append(f"- 总输出 tokens: {overall['total_tokens_out']:,}")
    report_lines.append(f"- 总计 tokens: {overall['total_tokens']:,}")
    report_lines.append(f"- **总成本: ${overall['total_cost_usd']:.4f} USD**")
    report_lines.append(f"- **平均每题成本: ${overall['cost_per_question_usd']:.4f} USD**")

    report_lines.append(f"\n## 按任务类型成本\n")
    report_lines.append(f"| 任务类型 | 题数 | 输入 tokens | 输出 tokens | 成本 (USD) | 每题成本 (USD) |")
    report_lines.append(f"|----------|------|-------------|-------------|-----------|---------------|")

    for task_type in sorted(analysis['by_task_type'].keys()):
        stats = analysis['by_task_type'][task_type]
        report_lines.append(
            f"| {task_type:20s} | {stats['count']:4d} | {stats['tokens_in']:11,d} | "
            f"{stats['tokens_out']:11,d} | ${stats['cost_usd']:9.4f} | ${stats['cost_per_question']:13.6f} |"
        )

    report_lines.append("\n" + "=" * 80)

    report_text = "\n".join(report_lines)

    # 打印到控制台
    print(report_text)

    # 保存到文件
    if output_path:
        # 确保输出目录存在
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"\n✅ 成本报告已保存到: {output_path}")

    return report_text


def compare_experiments_cost(exp_dirs: list, model: str, output_dir: str = "./"):
    """对比多个实验的成本"""

    analyses = []
    for exp_dir in exp_dirs:
        token_summary_path = Path(exp_dir) / "token_summary.json"
        if not token_summary_path.exists():
            print(f"⚠️  跳过 {exp_dir}: token_summary.json 不存在")
            continue

        analysis = analyze_token_summary(str(token_summary_path), model)
        analyses.append(analysis)

    if len(analyses) == 0:
        print("❌ 没有找到有效的 token_summary.json 文件")
        return

    # 确保输出目录存在
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 生成对比报告
    report_path = output_path / "cost_comparison.md"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# API Cost 对比分析\n\n")
        f.write(f"**模型**: {model}\n\n")

        f.write("## 总体成本对比\n\n")
        f.write("| 实验 | 题目数 | 输入 tokens | 输出 tokens | 总 tokens | 总成本 (USD) | 每题成本 (USD) |\n")
        f.write("|------|--------|-------------|-------------|-----------|-------------|---------------|\n")

        for analysis in analyses:
            exp = analysis['experiment']
            overall = analysis['overall']
            f.write(
                f"| {exp} | {overall['total_questions']} | {overall['total_tokens_in']:,} | "
                f"{overall['total_tokens_out']:,} | {overall['total_tokens']:,} | "
                f"${overall['total_cost_usd']:.4f} | ${overall['cost_per_question_usd']:.6f} |\n"
            )

        f.write("\n## 各实验详细分析\n\n")

        for analysis in analyses:
            f.write(f"### {analysis['experiment']}\n\n")
            f.write("| 任务类型 | 题数 | 成本 (USD) | 每题成本 (USD) |\n")
            f.write("|----------|------|-----------|---------------|\n")

            for task_type in sorted(analysis['by_task_type'].keys()):
                stats = analysis['by_task_type'][task_type]
                f.write(
                    f"| {task_type} | {stats['count']} | ${stats['cost_usd']:.4f} | "
                    f"${stats['cost_per_question']:.6f} |\n"
                )
            f.write("\n")

    print(f"\n✅ 对比报告已保存到: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="计算 API 调用成本")
    parser.add_argument("--token_summary", type=str, help="token_summary.json 文件路径")
    parser.add_argument("--model", type=str, help="模型名称（--list-models 时可选）")
    parser.add_argument("--output", type=str, help="输出报告路径")
    parser.add_argument("--compare", nargs="+", help="对比多个实验目录")
    parser.add_argument("--list-models", action="store_true", help="列出支持的模型")

    args = parser.parse_args()

    if args.list_models:
        print("支持的模型定价:")
        print("=" * 80)
        for model, pricing in sorted(PRICING.items()):
            print(f"{model:40s} 输入: ${pricing['input']:.2f}/M  输出: ${pricing['output']:.2f}/M")
        return

    # 非 list-models 模式时，model 参数必需
    if not args.model:
        parser.error("--model 参数是必需的（除非使用 --list-models）")

    if args.compare:
        compare_experiments_cost(args.compare, args.model, "./error_analysis")
    elif args.token_summary:
        analysis = analyze_token_summary(args.token_summary, args.model)
        generate_cost_report(analysis, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
