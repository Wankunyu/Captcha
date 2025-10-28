#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
单独运行实验的脚本
可以选择运行实验一、二或三中的任意一个
"""

import sys
import os

# 确保导入路径正确
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入原始 run_eval.py 中的函数
from run_eval import (
    run_eval,
    run_until_type_correct,
    SUPPORTED_TYPES,
    make_provider,
    build_json_schema,
    evaluate_pass1,
    load_secrets,
    build_tasks
)


# 导入简化的错误收集器
try:
    from experiments_helper import SimpleErrorCollector, load_tasks_from_ground_truth
    ERROR_ANALYSIS_AVAILABLE = True
except ImportError:
    ERROR_ANALYSIS_AVAILABLE = False
    print("⚠️ experiments_helper 未找到，错误分析功能不可用")


def run_experiment_1(
    dataset_root: str = "./captcha_data",
    types: list = None,
    provider: str = "gemini",
    model: str = "gemini-2.5-flash",
    max_per_type: int = 15,
    secrets_file: str = "./secrets.yaml",
    thinking: bool = False,
    thinking_options: dict = None,
    out_csv: str = None,
    enable_error_analysis: bool = False,
    error_analysis_dir: str = "./error_analysis",
    collect_tokens: bool = False,
    token_output_dir: str = "./results",
    collect_reasoning: bool = False,
    timeout_sec: float = 600.0
):
    """
    实验一：Ground Truth Prompts
    使用原始的 prompt，不做任何优化

    Args:
        dataset_root: 数据集根目录
        types: 要测试的任务类型列表，None 表示使用所有类型
        provider: API provider (gemini/openai/anthropic)
        model: 模型名称
        max_per_type: 每个类型最多测试多少题
        secrets_file: secrets.yaml 文件路径
        thinking: 是否启用 thinking mode
        thinking_options: thinking 配置选项
        out_csv: 输出 CSV 路径，None 则自动生成
        enable_error_analysis: 是否启用错误分析
        error_analysis_dir: 错误分析输出目录
        collect_tokens: 是否记录每题 token
        token_output_dir: token 统计输出目录
        collect_reasoning: 是否让模型输出 reasoning 字段

    Returns:
        实验结果字典
    """
    print("\n" + "="*80)
    print("🔵 实验一：Ground Truth Prompts")
    print("="*80)
    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print(f"Thinking: {thinking}")
    print("="*80 + "\n")

    # 默认类型
    if types is None:
        types = sorted(list(SUPPORTED_TYPES))

    # 默认输出文件
    if out_csv is None:
        out_csv = f"./results/exp1_{provider}_{model.replace('/', '_')}.csv"



    token_prefix = None
    if collect_tokens:
        token_output_root = token_output_dir or "./results"
        token_prefix = os.path.join(
            token_output_root,
            f"exp1_gt_{provider}_{model.replace('/', '_')}"
        )

    result = run_eval(
        dataset_root=dataset_root,
        types=types,
        provider=provider,
        model=model,
        max_per_type=max_per_type,
        out_csv=out_csv,
        secrets_file=secrets_file,
        prompts_file=None,  # 不使用 prompts 文件
        prompt_mode="gt",   # 使用 Ground Truth prompts
        thinking=thinking,
        thinking_options=thinking_options or {},
        stream=False,
        timeout_sec=timeout_sec,
        collect_tokens=collect_tokens,
        token_log_path=(f"{token_prefix}_tokens.csv" if token_prefix else None),
        token_summary_path=(f"{token_prefix}_token_summary.json" if token_prefix else None),
        experiment_name="exp1_gt",
        collect_errors=enable_error_analysis,
        error_analysis_dir=error_analysis_dir,
        error_experiment_name="exp1_gt",
        collect_reasoning=collect_reasoning
    )

    print(f"\n✅ Experiment 1 completed!")
    print(f"   结果文件: {out_csv}")
    return result


def run_experiment_2(
    dataset_root: str = "./captcha_data",
    types: list = None,
    provider: str = "gemini",
    model: str = "gemini-2.5-flash",
    max_per_type: int = 15,
    secrets_file: str = "./secrets.yaml",
    prompts_file: str = "./prompts_optimized.yaml",
    thinking: bool = False,
    thinking_options: dict = None,
    out_csv: str = None,
    enable_error_analysis: bool = False,
    error_analysis_dir: str = "./error_analysis",
    collect_tokens: bool = False,
    token_output_dir: str = "./results",
    collect_reasoning: bool = False,
    timeout_sec: float = 600.0
):
    """
    实验二：Optimized Prompts
    使用优化后的 prompt

    Args:
        dataset_root: 数据集根目录
        types: 要测试的任务类型列表，None 表示使用所有类型
        provider: API provider (gemini/openai/anthropic)
        model: 模型名称
        max_per_type: 每个类型最多测试多少题
        secrets_file: secrets.yaml 文件路径
        prompts_file: 优化的 prompts 文件路径
        thinking: 是否启用 thinking mode
        thinking_options: thinking 配置选项
        out_csv: 输出 CSV 路径，None 则自动生成
        enable_error_analysis: 是否启用错误分析
        error_analysis_dir: 错误分析输出目录
        collect_tokens: 是否记录每题 token
        token_output_dir: token 统计输出目录
        collect_reasoning: 是否让模型输出 reasoning 字段

    Returns:
        实验结果字典
    """
    print("\n" + "="*80)
    print("🟢 实验二：Optimized Prompts")
    print("="*80)
    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print(f"Prompts file: {prompts_file}")
    print(f"Thinking: {thinking}")
    print("="*80 + "\n")

    # 默认类型
    if types is None:
        types = sorted(list(SUPPORTED_TYPES))

    # 默认输出文件
    if out_csv is None:
        out_csv = f"./results/exp2_{provider}_{model.replace('/', '_')}.csv"

    # 检查 prompts 文件
    if not os.path.exists(prompts_file):
        print(f"⚠️ 警告：prompts 文件不存在: {prompts_file}")
        print("   将使用 Ground Truth prompts")
        prompts_file = None

    token_prefix = None
    if collect_tokens:
        token_output_root = token_output_dir or "./results"
        token_prefix = os.path.join(
            token_output_root,
            f"exp2_opt_{provider}_{model.replace('/', '_')}"
        )

    result = run_eval(
        dataset_root=dataset_root,
        types=types,
        provider=provider,
        model=model,
        max_per_type=max_per_type,
        out_csv=out_csv,
        secrets_file=secrets_file,
        prompts_file=prompts_file,
        prompt_mode="auto",
        thinking=thinking,
        thinking_options=thinking_options or {},
        stream=False,
        timeout_sec=timeout_sec,
        collect_tokens=collect_tokens,
        token_log_path=(f"{token_prefix}_tokens.csv" if token_prefix else None),
        token_summary_path=(f"{token_prefix}_token_summary.json" if token_prefix else None),
        experiment_name="exp2_opt",
        collect_errors=enable_error_analysis,
        error_analysis_dir=error_analysis_dir,
        error_experiment_name="exp2_opt",
        collect_reasoning=collect_reasoning
    )

    print(f"\n✅ Experiment 2 completed!")
    print(f"   结果文件: {out_csv}")
    return result


def run_experiment_3(
    dataset_root: str = "./captcha_data",
    types: list = None,
    provider: str = "gemini",
    model: str = "gemini-2.5-flash",
    max_attempts_per_type: int = 5,
    max_pool_per_type: int = 15,
    secrets_file: str = "./secrets.yaml",
    prompts_file: str = "./prompts_optimized.yaml",
    prompt_mode: str = "auto",
    out_csv: str = None,
    log_attempt_rows: bool = False,
    thinking: bool = False,
    thinking_options: dict = None,
    collect_tokens: bool = False,
    token_output_dir: str = "./results",
    collect_reasoning: bool = False,
    timeout_sec: float = 600.0
):
    """
    实验三：Until Correct Strategy
    迭代纠错，直到做对或达到最大尝试次数

    Args:
        dataset_root: 数据集根目录
        types: 要测试的任务类型列表，None 表示使用所有类型
        provider: API provider (gemini/openai/anthropic)
        model: 模型名称
        max_attempts_per_type: 每个类型最多尝试次数
        max_pool_per_type: 每类最多预取多少题作为候选池
        secrets_file: secrets.yaml 文件路径
        prompts_file: 优化的 prompts 文件路径（实验二同款）
        prompt_mode: Prompt 模式（'gt' 使用实验一模式，'auto' 使用实验二模式，'opt' 等）
        out_csv: 输出 CSV 路径，None 则自动生成
        log_attempt_rows: 是否记录每次尝试的详细信息
        thinking: 是否启用 thinking mode
        thinking_options: thinking 配置选项
        collect_tokens: 是否记录每次尝试的 token
        token_output_dir: token 统计输出目录
        collect_reasoning: 是否让模型输出 reasoning 字段

    Returns:
        实验结果字典
    """
    print("\n" + "="*80)
    print("🟡 实验三：Until Correct Strategy")
    print("="*80)
    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print(f"Max attempts per type: {max_attempts_per_type}")
    print(f"Prompts file: {prompts_file}")
    print("="*80 + "\n")

    # 默认类型
    if types is None:
        types = sorted(list(SUPPORTED_TYPES))

    # 默认输出文件
    if out_csv is None:
        out_csv = f"./results/exp3_{provider}_{model.replace('/', '_')}.csv"

    # 检查 prompts 文件
    if prompts_file and not os.path.exists(prompts_file):
        print(f"⚠️ 警告：prompts 文件不存在: {prompts_file}")
        print("   将使用 Ground Truth prompts")
        prompts_file = None
        prompt_mode = "gt"

    prompt_mode = prompt_mode or "gt"

    token_prefix = None
    if collect_tokens:
        token_output_root = token_output_dir or "./results"
        token_prefix = os.path.join(
            token_output_root,
            f"exp3_{provider}_{model.replace('/', '_')}"
        )

    # 运行实验
    result = run_until_type_correct(
        dataset_root=dataset_root,
        types=types,
        provider=provider,
        model=model,
        max_attempts_per_type=max_attempts_per_type,
        max_pool_per_type=max_pool_per_type,
        secrets_file=secrets_file,
        timeout_sec=timeout_sec,
        prompts_file=prompts_file,
        prompt_mode=prompt_mode,
        out_csv=out_csv,
        log_attempt_rows=log_attempt_rows,
        stream=False,
        thinking=thinking,
        thinking_options=thinking_options or {},
        collect_tokens=collect_tokens,
        token_log_path=(f"{token_prefix}_tokens.csv" if token_prefix else None),
        token_summary_path=(f"{token_prefix}_token_summary.json" if token_prefix else None),
        collect_reasoning=collect_reasoning
    )

    print(f"\n✅ 实验三完成！")
    print(f"   结果文件: {out_csv}")
    return result


def run_experiment_4(
    dataset_root: str = "./captcha_data",
    types: list = None,
    provider: str = "gemini",
    model: str = "gemini-2.5-flash",
    max_per_type: int = 15,
    secrets_file: str = "./secrets.yaml",
    prompts_file: str = "./prompts_optimized.yaml",
    few_shot_file: str = "./few_shot_examples.yaml",
    few_shot_assets_root: str = "./few_shot_assets",
    n_shot: int = 2,
    thinking: bool = False,
    thinking_options: dict = None,
    out_csv: str = None,
    enable_error_analysis: bool = False,
    error_analysis_dir: str = "./error_analysis",
    collect_tokens: bool = False,
    token_output_dir: str = "./results",
    collect_reasoning: bool = False,
    timeout_sec: float = 600.0
):
    """
    实验四：Optimized Prompts + Few-shot Learning
    结合实验二的优化prompt和N-shot示例

    Args:
        dataset_root: 数据集根目录
        types: 要测试的任务类型列表，None 表示使用所有类型
        provider: API provider (gemini/openai/anthropic)
        model: 模型名称
        max_per_type: 每个类型最多测试题数（注意：实际测试样本 = max_per_type - n_shot）
        secrets_file: secrets.yaml 文件路径
        prompts_file: 优化的 prompts 文件路径（实验二同款）
        few_shot_file: few-shot 示例配置文件路径
        n_shot: few-shot 示例数量
        thinking: 是否启用 thinking mode
        thinking_options: thinking 配置选项
        out_csv: 输出 CSV 路径，None 则自动生成
        enable_error_analysis: 是否启用错误分析
        error_analysis_dir: 错误分析输出目录
        collect_tokens: 是否记录每题 token
        token_output_dir: token 统计输出目录
        collect_reasoning: 是否让模型输出 reasoning 字段

    Returns:
        实验结果字典
    """
    print("\n" + "="*80)
    print("🟣 实验四：Optimized Prompts + Few-shot Learning")
    print("="*80)
    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print(f"Prompts file: {prompts_file}")
    print(f"Few-shot file: {few_shot_file}")
    print(f"N-shot: {n_shot}")
    print(f"Note: 每种类型使用前 {n_shot} 个样本作为示例")
    print("="*80 + "\n")

    # 默认类型
    if types is None:
        types = sorted(list(SUPPORTED_TYPES))

    # 默认输出文件
    if out_csv is None:
        out_csv = f"./results/exp4_{provider}_{model.replace('/', '_')}.csv"

    # 检查 prompts 文件
    if not os.path.exists(prompts_file):
        print(f"⚠️ 警告：prompts 文件不存在: {prompts_file}")
        print("   将使用 Ground Truth prompts")
        prompts_file = None

    # 检查 few-shot 文件
    if not os.path.exists(few_shot_file):
        raise FileNotFoundError(f"❌ Few-shot 配置文件不存在: {few_shot_file}\n"
                              f"   请先运行: python prepare_few_shot_examples.py")

    # Token统计配置
    token_prefix = None
    if collect_tokens:
        token_output_root = token_output_dir or "./results"
        token_prefix = os.path.join(
            token_output_root,
            f"exp4_fewshot_{provider}_{model.replace('/', '_')}"
        )

    # Few-shot 配置
    few_shot_config = {
        "enabled": True,
        "n_shot": n_shot,
        "include_reasoning": False
    }

    # 运行评测
    result = run_eval(
        dataset_root=dataset_root,
        types=types,
        provider=provider,
        model=model,
        max_per_type=max_per_type,
        out_csv=out_csv,
        secrets_file=secrets_file,
        prompts_file=prompts_file,
        prompt_mode="auto",  # 使用优化prompt
        thinking=thinking,
        thinking_options=thinking_options or {},
        stream=False,
        timeout_sec=timeout_sec,
        collect_tokens=collect_tokens,
        token_log_path=(f"{token_prefix}_tokens.csv" if token_prefix else None),
        token_summary_path=(f"{token_prefix}_token_summary.json" if token_prefix else None),
        experiment_name="exp4_fewshot",
        collect_errors=enable_error_analysis,
        error_analysis_dir=error_analysis_dir,
        error_experiment_name="exp4_fewshot",
        collect_reasoning=collect_reasoning,
        few_shot_config=few_shot_config,
        few_shot_file=few_shot_file,
        few_shot_assets_root=few_shot_assets_root
    )

    print(f"\n✅ 实验四完成！")
    print(f"   结果文件: {out_csv}")
    print(f"   注意：每种类型使用了 {n_shot} 个样本作为示例，剩余样本用于测试")
    return result


def _collect_error_analysis(
    experiment_name: str,
    dataset_root: str,
    types: list,
    max_per_type: int,
    provider: str,
    model: str,
    secrets_file: str,
    prompts_file: str,
    prompt_mode: str,
    thinking: bool,
    thinking_options: dict,
    error_analysis_dir: str,
    collect_tokens: bool = False,
    collect_reasoning: bool = False
):
    """兼容旧代码：委托给 run_eval 单次推理并输出错误分析。"""
    analysis_dir = os.path.join(error_analysis_dir, experiment_name)
    os.makedirs(analysis_dir, exist_ok=True)
    summary_csv = os.path.join(analysis_dir, "results.csv")

    return run_eval(
        dataset_root=dataset_root,
        types=types,
        provider=provider,
        model=model,
        max_per_type=max_per_type,
        out_csv=summary_csv,
        secrets_file=secrets_file,
        prompts_file=prompts_file,
        prompt_mode=prompt_mode,
        thinking=thinking,
        thinking_options=thinking_options or {},
        stream=False,
        collect_tokens=collect_tokens,
        token_log_path=None,
        token_summary_path=None,
        experiment_name=experiment_name,
        collect_errors=True,
        error_analysis_dir=error_analysis_dir,
        error_experiment_name=experiment_name,
        collect_reasoning=collect_reasoning
    )


# ==================== 命令行接口 ====================

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="运行单个 CAPTCHA 实验")
    parser.add_argument("experiment", type=int, choices=[1, 2, 3, 4],
                       help="实验编号：1=GT Prompts, 2=Optimized Prompts, 3=Until Correct, 4=Few-shot")
    parser.add_argument("--dataset", default="./captcha_data",
                       help="数据集根目录 (默认: ./captcha_data)")
    parser.add_argument("--types", nargs="+", default=None,
                       help="任务类型列表，不指定则使用全部类型")
    parser.add_argument("--provider", default="gemini",
                       help="Provider (默认: gemini)")
    parser.add_argument("--model", default="gemini-2.5-flash",
                       help="模型名称 (默认: gemini-2.5-flash)")
    parser.add_argument("--max-per-type", type=int, default=15,
                       help="每个类型最多测试题数 (默认: 15)")
    parser.add_argument("--thinking", action="store_true",
                       help="启用 thinking mode")
    parser.add_argument("--thinking-budget", type=int, default=-1,
                       help="Thinking budget (默认: -1, 无限制)")
    parser.add_argument("--error-analysis", action="store_true",
                       help="启用错误分析")
    parser.add_argument("--prompts-file", default="./prompts_optimized.yaml",
                       help="优化的 prompts 文件 (实验2/3/4使用)")
    parser.add_argument("--few-shot-file", default="./few_shot_examples.yaml",
                       help="Few-shot 示例配置文件 (实验4使用)")
    parser.add_argument("--few-shot-assets-root", default="./few_shot_assets",
                       help="Few-shot 示例图片目录 (实验4使用)")
    parser.add_argument("--n-shot", type=int, default=2,
                       help="Few-shot 示例数量 (实验4使用，默认: 2)")
    parser.add_argument("--out-csv", default=None,
                       help="输出 CSV 文件路径")
    parser.add_argument("--collect-tokens", action="store_true",
                       help="记录每题 token 消耗")
    parser.add_argument("--token-output-dir", default="./results",
                       help="token 统计输出目录 (默认: ./results)")
    parser.add_argument("--collect-reasoning", action="store_true",
                       help="要求模型输出 reasoning 字段（可能增加耗时和成本）")

    args = parser.parse_args()

    # 准备参数
    thinking_options = {"budget": args.thinking_budget} if args.thinking else {}

    # 运行对应的实验
    if args.experiment == 1:
        run_experiment_1(
            dataset_root=args.dataset,
            types=args.types,
            provider=args.provider,
            model=args.model,
            max_per_type=args.max_per_type,
            thinking=args.thinking,
            thinking_options=thinking_options,
            out_csv=args.out_csv,
            enable_error_analysis=args.error_analysis,
            collect_tokens=args.collect_tokens,
            token_output_dir=args.token_output_dir,
            collect_reasoning=args.collect_reasoning
        )
    elif args.experiment == 2:
        run_experiment_2(
            dataset_root=args.dataset,
            types=args.types,
            provider=args.provider,
            model=args.model,
            max_per_type=args.max_per_type,
            prompts_file=args.prompts_file,
            thinking=args.thinking,
            thinking_options=thinking_options,
            out_csv=args.out_csv,
            enable_error_analysis=args.error_analysis,
            collect_tokens=args.collect_tokens,
            token_output_dir=args.token_output_dir,
            collect_reasoning=args.collect_reasoning
        )
    elif args.experiment == 3:
        run_experiment_3(
            dataset_root=args.dataset,
            types=args.types,
            provider=args.provider,
            model=args.model,
            max_pool_per_type=args.max_per_type,
            prompts_file=args.prompts_file,
            out_csv=args.out_csv,
            thinking=args.thinking,
            thinking_options=thinking_options,
            collect_tokens=args.collect_tokens,
            token_output_dir=args.token_output_dir,
            collect_reasoning=args.collect_reasoning
        )
    elif args.experiment == 4:
        run_experiment_4(
            dataset_root=args.dataset,
            types=args.types,
            provider=args.provider,
            model=args.model,
            max_per_type=args.max_per_type,
            prompts_file=args.prompts_file,
            few_shot_file=args.few_shot_file,
            few_shot_assets_root=args.few_shot_assets_root,
            n_shot=args.n_shot,
            thinking=args.thinking,
            thinking_options=thinking_options,
            out_csv=args.out_csv,
            enable_error_analysis=args.error_analysis,
            collect_tokens=args.collect_tokens,
            token_output_dir=args.token_output_dir,
            collect_reasoning=args.collect_reasoning
        )


if __name__ == "__main__":
    # 只在直接运行脚本时执行
    if len(sys.argv) > 1:
        # 命令行模式
        main()
    else:
        # 直接运行时显示帮助信息
        print("=" * 80)
        print("单独运行实验脚本")
        print("=" * 80)
        print("\n使用方法：")
        print("\n1. 在 Python/Notebook 中导入:")
        print("   from run_single_experiment import run_experiment_1, run_experiment_2, run_experiment_3")
        print("\n2. 命令行运行:")
        print("   python run_single_experiment.py 1 --types Dice_Count --max-per-type 2")
        print("\n3. 查看帮助:")
        print("   python run_single_experiment.py --help")
        print("\n详细文档请查看: QUICK_START.md")
        print("=" * 80)
