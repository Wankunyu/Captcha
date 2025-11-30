#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate a few-shot configuration by sampling the first N items per task type
from the dataset and writing them to few_shot_examples.yaml.
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
    Extract few-shot examples from the dataset and write a YAML manifest.

    Args:
        dataset_root: Root directory of the dataset.
        n_shot: Number of samples to take per task type.
        output_file: Output YAML path.
    """

    dataset_path = Path(dataset_root)
    few_shot_config = {}

    task_types = sorted([d.name for d in dataset_path.iterdir() if d.is_dir()])

    print(f"Scanning {len(task_types)} task types...")
    print("=" * 80)

    for task_type in task_types:
        type_dir = dataset_path / task_type
        gt_file = type_dir / "ground_truth.json"

        if not gt_file.exists():
            print(f"⚠️  Skipping {task_type}: missing ground_truth.json")
            continue

        try:
            with open(gt_file, 'r', encoding='utf-8') as f:
                ground_truth = json.load(f)

            examples = []
            for i, (filename, data) in enumerate(ground_truth.items()):
                if i >= n_shot:
                    break

                example = {"filename": filename}

                answer = extract_answer(task_type, data)
                if answer is not None:
                    example["answer"] = answer

                if "order_image" in data:
                    example["order_image"] = data["order_image"]

                if "tolerance" in data:
                    example["tolerance"] = data["tolerance"]

                examples.append(example)

            if examples:
                few_shot_config[task_type] = {"examples": examples}
                print(f"✅ {task_type}: extracted {len(examples)} examples")
            else:
                print(f"⚠️  {task_type}: no valid examples found")

        except Exception as e:
            print(f"❌ {task_type}: failed to process - {e}")

    print("\n" + "=" * 80)
    print(f"Saving to {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(few_shot_config, f,
                  default_flow_style=False,
                  allow_unicode=True,
                  sort_keys=False)

    print(f"✅ Generated {output_file}")
    print(f"   Contains {len(few_shot_config)} task types")
    print(f"   {n_shot} examples per task type")

    return few_shot_config


def extract_answer(task_type: str, data: Dict[str, Any]) -> Any:
    """
    Normalize answers according to task type.

    Args:
        task_type: Name of the task type.
        data: Entry from ground_truth.

    Returns:
        Standardized answer structure or None if unavailable.
    """

    if task_type == "Dice_Count":
        if "sum" in data:
            return {"value": data["sum"]}

    elif task_type == "Click_Order":
        if "answer" in data:
            points = [{"x": p[0], "y": p[1]} for p in data["answer"]]
            return {"points": points}

    elif task_type == "Patch_Select":
        if "correct_patches" in data:
            return {"indices": data["correct_patches"]}
        elif "answer" in data:
            return {"indices": data["answer"]}

    elif task_type in ["Place_Dot", "Geometry_Click"]:
        target = data.get("target_position", data.get("answer"))
        if target:
            if isinstance(target, list) and len(target) == 2:
                return {"point": {"x": target[0], "y": target[1]}}
            elif isinstance(target, dict):
                return {"point": {"x": target.get("x", 0), "y": target.get("y", 0)}}

    elif "answer" in data:
        answer = data["answer"]
        if isinstance(answer, int):
            return {"choice": answer}
        elif isinstance(answer, list):
            if answer and isinstance(answer[0], list) and len(answer[0]) == 2:
                return {"points": [{"x": p[0], "y": p[1]} for p in answer]}
            else:
                return {"indices": answer}
        else:
            return answer

    return None


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate few-shot example manifest.")
    parser.add_argument("--dataset", default="./captcha_data",
                       help="Dataset root (default: ./captcha_data)")
    parser.add_argument("--n-shot", type=int, default=2,
                       help="Number of examples per task type (default: 2)")
    parser.add_argument("--output", default="./few_shot_examples.yaml",
                       help="Output YAML path (default: ./few_shot_examples.yaml)")

    args = parser.parse_args()

    extract_few_shot_examples(
        dataset_root=args.dataset,
        n_shot=args.n_shot,
        output_file=args.output
    )


if __name__ == "__main__":
    main()
