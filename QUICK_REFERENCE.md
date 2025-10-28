# 快速参考手册

## 一、运行实验

### 实验 1：基准测试（Ground Truth Prompts）
```bash
python run_single_experiment.py 1 --provider gemini --model gemini-2.5-flash
```

### 实验 2：优化提示词（Optimized Prompts）
```bash
python run_single_experiment.py 2 --provider gemini --model gemini-2.5-flash
```

### 实验 3：迭代纠错（Until Correct）
```bash
python run_single_experiment.py 3 --provider gemini --model gemini-2.5-flash
```

### 实验 4：Few-shot 学习
```bash
python run_single_experiment.py 4 --n-shot 2 --provider gemini --model gemini-2.5-flash
```

---

## 二、常用参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--provider` | API provider | gemini, openai, anthropic |
| `--model` | 模型名称 | gemini-2.5-flash, gpt-4o |
| `--max-per-type` | 每类题数 | 15 |
| `--types` | 指定任务类型 | Dice_Count Place_Dot |
| `--thinking` | 启用 thinking | (flag) |
| `--collect-tokens` | 收集 token | (flag) |
| `--error-analysis` | 错误分析 | (flag) |
| `--dry-run` | 仅测试 | (flag) |


---

## 三、成本计算(需要核实)

### 查看支持的模型
```bash
python calculate_cost.py --list-models
```

### 计算单个实验成本
```bash
python calculate_cost.py \
  --token_summary results/exp1_gt_gemini_gemini-2.5-flash_token_summary.json \
  --model gemini-2.5-flash
```

---

## 四、目录结构速查

```
captcha/
├── captcha_data/          # 数据集（20种类型）
├── results/               # 实验结果
├── error_analysis/        # 错误分析
├── few_shot_assets/       # Few-shot图片
├── run_eval.py           # 核心评测引擎
├── run_single_experiment.py  # 实验运行脚本
└── PROJECT_SUMMARY.md    # 详细文档
```

---

## 五、任务类型速查

### 坐标/点击类（6种）
Dice_Count, Click_Order, Place_Dot, Geometry_Click, Pick_Area, Misleading_Click

### 网格选择类（4种）
Patch_Select, Select_Animal, Image_Recognition, Unusual_Detection

### 图像匹配类（4种）
Image_Matching, Object_Match, Path_Finder, Rotation_Match

### 逻辑推理类（4种）
Bingo, Dart_Count, Coordinates, Connect_Icon

### 暂不使用（2种）
Hold_Button, Slide_Puzzle

---

## 六、当前图片尺寸

| 任务类型 | 尺寸 | 状态 |
|---------|------|------|
| Click_Order | 600×390 | ✅ 已处理 |
| Place_Dot | 600×600 | ✅ 已处理 |
| Patch_Select | 正方形 | ✅ 已处理（含5×5网格） |
| 其他 | 原始尺寸 | ⏸️ 待处理 |

---

## 七、网格索引（Patch_Select）

```
 0  1  2  3  4
 5  6  7  8  9
10 11 12 13 14
15 16 17 18 19
20 21 22 23 24
```


---

## 八、实验结果位置

- **CSV**: `results/exp1_gemini_gemini-2.5-flash.csv`
- **Token**: `results/exp1_gt_gemini_gemini-2.5-flash_token_summary.json`
- **错误分析**: `error_analysis/exp1_gt/errors.csv`

---

*详细文档见 [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)*
