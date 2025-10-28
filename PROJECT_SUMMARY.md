# CAPTCHA 验证码求解器评测系统 - 项目总结

## 项目概述

这是一个使用**多模态大语言模型（Vision-Language Models）**自动解决各种类型验证码挑战的评测系统。项目支持 20 种不同类型的 CAPTCHA 任务，并提供了完整的评测框架、实验设计和错误分析功能。

---

## 目录结构

```
captcha/
├── captcha_data/          # 验证码数据集（20种任务类型）
│   ├── Dice_Count/
│   ├── Click_Order/
│   ├── Patch_Select/
│   ├── Place_Dot/
│   └── ...（共20个子目录）
├── few_shot_assets/       # Few-shot 示例图片资源
├── results/               # 实验结果输出目录
├── error_analysis/        # 错误分析输出目录
├── Image/                 # 示例图片存储
├── run_eval.py           # ⭐ 核心评测引擎
├── run_single_experiment.py  # ⭐ 单实验运行脚本
├── experiments_helper.py  # 实验辅助工具
├── few_shot_answers.py   # Few-shot 答案硬编码
├── few_shot_examples.yaml # Few-shot 示例配置
├── prompts_optimized.yaml # 优化的任务提示词
├── secrets.yaml          # API 密钥配置（gitignore）
├── calculate_cost.py     # API 成本计算工具
├── prepare_few_shot_examples.py  # Few-shot 配置生成
├── compress_few_shot_assets.py   # 图像压缩工具
└── resize_*.py           # 图片尺寸调整脚本（本次创建）
```

---

## 支持的 CAPTCHA 任务类型（20种）

### 1. 坐标/点击类
- **Dice_Count** - 计算骰子顶面数字总和
- **Click_Order** - 按指定顺序点击图标（两张图：主图 + 顺序参考图）
- **Place_Dot** - 在路径终点放置点
- **Geometry_Click** - 点击几何中心
- **Pick_Area** - 选择最大区域
- **Misleading_Click** - 避开误导性点击

### 2. 网格选择类
- **Patch_Select** - 选择包含目标对象的网格（5×5）
- **Select_Animal** - 六宫格动物选择
- **Image_Recognition** - 九宫格图像识别
- **Unusual_Detection** - 异常检测（选择不正常的对象）

### 3. 图像匹配类
- **Image_Matching** - 从选项中找出与参考图相同的图片
- **Object_Match** - 对象数量匹配
- **Path_Finder** - 路径寻找/视角匹配
- **Rotation_Match** - 旋转角度匹配

### 4. 逻辑推理类
- **Bingo** - 找出可交换形成连线的索引对
- **Dart_Count** - 飞镖得分计算
- **Coordinates** - 坐标定位
- **Connect_Icon** - 图标连接

### 5. 需要交互类（暂不使用）
- **Hold_Button** - 按住按钮
- **Slide_Puzzle** - 滑动拼图

---

## 核心实验设计（4个实验）

### 实验 1: Ground Truth Prompts（基准测试）
- **文件**: `run_single_experiment.py:36-128`
- **描述**: 使用原始的 ground_truth.json 中的 prompt
- **目的**: 建立基准性能
- **运行**:
  ```bash
  python run_single_experiment.py 1 --provider gemini --model gemini-2.5-flash
  ```

### 实验 2: Optimized Prompts（优化提示词）
- **文件**: `run_single_experiment.py:131-230`
- **描述**: 使用 `prompts_optimized.yaml` 中的优化 prompt
- **特点**: 针对每种任务类型设计了详细的规则和决策流程
- **运行**:
  ```bash
  python run_single_experiment.py 2 --provider gemini --model gemini-2.5-flash
  ```

### 实验 3: Until Correct Strategy（迭代纠错）
- **文件**: `run_single_experiment.py:233-336`
- **描述**: 持续尝试直到正确或达到最大尝试次数
- **参数**: `max_attempts_per_type` - 每个类型最多尝试次数
- **运行**:
  ```bash
  python run_single_experiment.py 3 --provider gemini --model gemini-2.5-flash
  ```

### 实验 4: Few-shot Learning（少样本学习）
- **文件**: `run_single_experiment.py:339-463`
- **描述**: 结合优化 prompt 和 N-shot 示例
- **配置**:
  - `few_shot_examples.yaml` - 示例配置
  - `few_shot_assets/` - 示例图片
  - `few_shot_answers.py` - 硬编码答案
- **运行**:
  ```bash
  python run_single_experiment.py 4 --n-shot 2 --provider gemini --model gemini-2.5-flash
  ```

---

## 核心代码文件说明

### 1. `run_eval.py` - 核心评测引擎（~3800行）
**功能**:
- 支持三大 API Provider: OpenAI, Anthropic Claude, Google Gemini
- 图像缓存系统（零转换，直接使用原始字节）
- JSON 响应解析和验证
- Token 使用统计
- 错误案例收集

**关键函数**:
- `run_eval()` - 主评测函数
- `run_until_type_correct()` - 迭代纠错评测
- `build_tasks()` - 从 ground_truth.json 构建任务
- `make_provider()` - 创建 API provider 实例
- `evaluate_pass1()` - 评估单个任务是否通过

**图像缓存**:
```python
class ImageCache:
    # LRU 缓存，max_items=512
    # 缓存原始字节和 base64 编码
```

### 2. `run_single_experiment.py` - 实验运行脚本
**功能**:
- 封装了 4 个实验的运行函数
- 命令行接口支持
- 参数配置（provider, model, thinking, tokens, etc.）

**实验函数**:
- `run_experiment_1()` - GT Prompts
- `run_experiment_2()` - Optimized Prompts
- `run_experiment_3()` - Until Correct
- `run_experiment_4()` - Few-shot Learning

### 3. `experiments_helper.py` - 实验辅助工具
**核心类**:
```python
class SimpleErrorCollector:
    # 收集错误案例和统计信息
    def record()  # 记录测试案例
    def save_summary()  # 保存统计摘要
```

**功能**:
- 错误案例收集（errors.csv）
- 按任务类型统计（stats.json）
- Token 消耗汇总（token_summary.json）
- 实验对比分析

### 4. `calculate_cost.py` - API 成本计算
**定价表**（美元/百万 tokens）:
- GPT-4o: $2.50 (in), $10.00 (out)
- Claude-3.5-Sonnet: $3.00 (in), $15.00 (out)
- Gemini-2.5-Flash: $0.30 (in), $2.50 (out)

**功能**:
- 单实验成本分析
- 多实验对比
- 按任务类型成本统计

---

## 数据集结构

### ground_truth.json 格式
每个任务类型目录下都有一个 `ground_truth.json`：

```json
{
  "image1.jpg": {
    "prompt": "Task description",
    "answer": [...],  // 或其他字段如 sum, target_position 等
    "tolerance": 15,  // 可选，用于坐标类任务
    "order_image": "order1.jpg"  // 可选，辅助图片
  }
}
```

### 不同任务类型的答案格式

#### Dice_Count
```json
{"sum": 85}
```

#### Click_Order
```json
{
  "answer": [[470, 100], [325, 180], ...],
  "order_image": "order1.jpg",
  "tolerance": 40
}
```

#### Patch_Select
```json
{
  "grid_size": [5, 5],
  "correct_patches": [0, 1, 2, 3, 5, 6, 7, 8, 11, 12, 13]
}
```

#### Place_Dot / Geometry_Click
```json
{
  "target_position": [190, 210],
  "tolerance": 25
}
```

#### Image_Matching / Dart_Count / Coordinates
```json
{"answer": 2}  // 索引值，从0开始
```

---

## Few-shot 系统

### 配置文件结构
**few_shot_examples.yaml**:
```yaml
Dice_Count:
  examples:
  - filename: dice1.jpg
    answer:
      value: 85
  - filename: dice2.jpg
    answer:
      value: 67
```

### 硬编码答案系统
**few_shot_answers.py**:
- 避免文件名变更（PNG→JPG）导致的匹配问题
- 包含所有 few-shot 示例的答案数据
- 函数: `get_few_shot_answer(task_type, filename)`

### 图片资源
- **目录**: `few_shot_assets/`
- **清单**: `few_shot_image_manifest.json`（110张图片）
- **结构**: 按任务类型组织（如 `few_shot_assets/Dice_Count/dice1.jpg`）

---

## 评估指标

### 1. Pass@1 准确率
- 首次尝试的正确率
- 按任务类型统计
- 总体准确率

### 2. Token 消耗
- 输入 tokens
- 输出 tokens
- 总计 tokens
- 按任务类型统计

### 3. API 成本
- 基于 token 消耗和定价表
- 每题成本
- 总成本

### 4. 错误分析
- 详细的失败案例记录
- 错误描述（如"预测点数85高于GT 67，+18"）
- 按任务类型分类

---

## 错误分析系统

### 输出目录结构
```
error_analysis/
├── exp1_gt/
│   ├── errors.csv          # 错误案例详情
│   ├── stats.json          # 统计数据
│   └── token_summary.json  # Token 汇总
├── exp2_opt/
└── exp4_fewshot/
```

### errors.csv 字段
- `type` - 任务类型
- `puzzle_id` - 题目ID
- `raw_response` - 原始响应
- `parsed` - 解析后的JSON
- `ground_truth` - 标准答案
- `error_description` - 错误描述
- `reasoning` - 模型推理过程（可选）
- `tokens_in` - 输入tokens
- `tokens_out` - 输出tokens

### 错误描述示例
- Dice_Count: "预测点数 85 高于 GT 67 (Δ=+18)，说明模型重复计数或误把非顶面算入"
- Click_Order: "第 1 个点击距离目标 45.2px (> tolerance 40)"
- Patch_Select: "缺失 3 个正确索引: [5, 10, 15]；多选 2 个错误索引: [8, 13]"

---

## 配置文件

### secrets.yaml（gitignore）
```yaml
providers:
  openai:
    api_key: "sk-..."
  anthropic:
    api_key: "sk-ant-..."
  gemini:
    api_key: "..."

pricing:
  gemini:
    gemini-2.5-flash:
      in_per_1k: 0.0003
      out_per_1k: 0.0025
```

### prompts_optimized.yaml
包含所有任务类型的优化提示词，例如：

```yaml
Dice_Count: |-
  Task: Compute the TOTAL value of all dice TOP faces.

  Rules:
  1) Count ONLY the TOP face of each die
  2) If TOP face shows digit, use that digit
  3) If TOP face shows pips, count the dots
  4) Sum values over all dice
  ...
```

---

## 技术特点

### 1. 零图像转换
- 直接使用原始图像字节
- 避免重编码导致的质量损失
- 缓存原始字节和 base64

### 2. 多 Provider 支持
- OpenAI (GPT-4o, GPT-4o-mini)
- Anthropic (Claude-3.5-Sonnet, Claude-3.5-Haiku)
- Google (Gemini-2.5-Flash, Gemini-2.5-Pro)

### 3. Thinking 模式
- 支持模型的深度推理过程追踪
- 可配置 thinking budget
- 详细的认知过程记录

### 4. JSON Schema 验证
```python
def build_json_schema(task_type):
    # 为每种任务类型构建严格的 JSON Schema
    # 确保模型输出符合预期格式
```

### 5. 图像缓存机制
- LRU 淘汰策略
- 最大 512 项
- 内存可控

---

## 使用示例

### 运行单个实验
```bash
# 实验1：基准测试
python run_single_experiment.py 1 \
  --provider gemini \
  --model gemini-2.5-flash \
  --max-per-type 15 \
  --collect-tokens

# 实验2：优化提示词
python run_single_experiment.py 2 \
  --provider gemini \
  --model gemini-2.5-flash \
  --prompts-file ./prompts_optimized.yaml

# 实验4：Few-shot学习
python run_single_experiment.py 4 \
  --provider gemini \
  --model gemini-2.5-flash \
  --n-shot 2 \
  --few-shot-file ./few_shot_examples.yaml
```

### 计算成本
```bash
# 查看支持的模型定价
python calculate_cost.py --list-models

# 计算单个实验成本
python calculate_cost.py \
  --token_summary results/exp1_gt_gemini_gemini-2.5-flash_token_summary.json \
  --model gemini-2.5-flash

# 对比多个实验成本
python calculate_cost.py \
  --compare error_analysis/exp1_gt error_analysis/exp2_opt \
  --model gemini-2.5-flash
```

### 准备 Few-shot 示例
```bash
# 自动生成 few_shot_examples.yaml
python prepare_few_shot_examples.py \
  --dataset ./captcha_data \
  --n-shot 2 \
  --output ./few_shot_examples.yaml

# 压缩 Few-shot 图片资源
python compress_few_shot_assets.py
```

---

## 输出文件说明

### CSV 结果文件
```csv
task_type,puzzle_id,provider,model,pass1,e2e_ms,tokens_in,tokens_out,cost_usd
Dice_Count,dice1.png,gemini,gemini-2.5-flash,True,1250.5,1234,56,0.0012
```

### Token 统计 JSON
```json
{
  "experiment": "exp1_gt",
  "overall": {
    "total_questions": 150,
    "total_tokens_in": 123456,
    "total_tokens_out": 5678,
    "total_tokens": 129134
  },
  "by_task_type": {
    "Dice_Count": {
      "count": 15,
      "tokens_in": 12345,
      "tokens_out": 567,
      "total_tokens": 12912
    }
  }
}
```

---

## 注意事项

### 1. 坐标系统
- 原点 (0, 0) 在图片左上角
- X 轴向右，Y 轴向下
- 所有坐标都是像素值


### 2. API 限流
- 建议添加 `time.sleep()` 避免触发限流
- 使用 `timeout_sec` 参数设置超时时间

### 3. 成本控制
- 使用 `--collect-tokens` 跟踪 token 消耗
- 先用小数据集测试（`--max-per-type 2`）
- 选择性运行任务类型（`--types Dice_Count Place_Dot`）

---

**核心依赖**:
- `pillow` - 图像处理
- `pyyaml` - YAML 配置文件
- `openai` - OpenAI API
- `anthropic` - Anthropic API
- `google-genai` - Google Gemini API
- `tqdm` - 进度条


---

*最后更新: 2025-10-28*
*文档版本: 1.0*
