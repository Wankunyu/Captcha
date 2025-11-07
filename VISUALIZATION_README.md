# CAPTCHA实验结果可视化指南

## 📊 功能概述

自动生成论文级图表，展示CAPTCHA题型对大模型的挑战难度，帮助识别最适合用于CAPTCHA设计的题型。

### 核心图表

1. **热力图 (Heatmap)** - 题型难度全景
   - 显示所有题型在不同模型上的表现
   - 红色=难，绿色=易
   - 自动按平均难度排序

2. **分组柱状图 (Grouped Bar Chart)** - 优化效果对比
   - 对比Exp1/Exp2/Exp4的正确率变化
   - 标注CAPTCHA推荐阈值（60%）
   - 识别哪些题型即使优化后仍然难

3. **散点图 (Scatter Plot)** - 优化抵抗性分析
   - X轴: Exp1基线正确率
   - Y轴: Exp2优化后正确率
   - 红色区域（左下角）= 推荐CAPTCHA区

4. **箱线图 (Box Plot)** - 跨模型稳定性
   - 显示每个题型在不同模型上的正确率分布
   - 识别对所有模型都难的题型

---

## 🚀 快速开始

### 方法1: 一键生成所有图表（推荐）

```python
from visualize_results import quick_visualize

# 自动扫描results/目录，生成所有图表
viz = quick_visualize(
    results_dir="./results",
    output_dir="./figures",
    show=False
)
```

**输出**：
- `figures/` 目录下的所有图表PNG文件
- `captcha_recommendations.csv` - CAPTCHA推荐列表
- 终端输出推荐报告

---

### 方法2: 单独生成特定图表（灵活控制）

```python
from visualize_results import CAPTCHAVisualizer
import matplotlib.pyplot as plt

# 初始化
viz = CAPTCHAVisualizer(results_dir="./results")

# 图表1: 热力图
viz.plot_heatmap(
    experiment='exp1',
    save_path="./figures/heatmap_exp1.png"
)
plt.show()

# 图表2: 柱状图对比
viz.plot_comparison_bars(
    experiments=['exp1', 'exp2', 'exp4'],
    model_filter="openai/gpt-5-chat-latest",
    save_path="./figures/comparison.png"
)
plt.show()

# 图表3: 散点图分析
viz.plot_optimization_resistance(
    base_exp='exp1',
    opt_exp='exp2',
    model_filter="openai/gpt-5-chat-latest",
    save_path="./figures/resistance.png"
)
plt.show()

# 图表4: 箱线图稳定性
viz.plot_cross_model_stability(
    experiment='exp1',
    save_path="./figures/stability.png"
)
plt.show()
```

---

### 方法3: 在Jupyter Notebook中使用

打开 `test.ipynb`，运行最后几个可视化cells：

```python
# Cell 1: 快速生成所有图表
viz = quick_visualize(
    results_dir="./results",
    output_dir="./figures",
    show=False
)

# Cell 2-5: 单独生成各类图表（已自动处理数据缺失）

# Cell 6: 查看CAPTCHA推荐报告
```

---

## 🔧 高级功能

### 1. 生成CAPTCHA推荐列表

```python
recommendations = viz.generate_captcha_recommendation(
    experiment='exp2',  # 基于哪个实验
    threshold=60.0,     # CAPTCHA推荐阈值
    top_n=10            # 返回前N个最难题型
)

print(recommendations)
# 输出:
#    rank  avg_accuracy  std_accuracy  n_models  captcha_score
# 0     1          15.2           8.3         4          92.68
# 1     2          28.5          12.1         4          81.16
# ...
```

**字段说明**：
- `avg_accuracy`: 平均正确率（越低越难）
- `std_accuracy`: 标准差（越低越稳定）
- `captcha_score`: 推荐指数（综合难度60% + 稳定性40%）

---

### 2. 筛选特定模型或实验

```python
# 只显示OpenAI GPT-5的结果
viz.plot_comparison_bars(
    experiments=['exp1', 'exp2'],
    model_filter="openai/gpt-5-chat-latest"
)

# 对比Anthropic Claude的表现
viz.plot_heatmap(
    experiment='exp1',
    # 会自动显示所有可用模型
)
```

---

### 3. 自定义图表尺寸和样式

```python
viz.plot_heatmap(
    experiment='exp1',
    figsize=(20, 12),  # 更大的图表
    save_path="./custom_heatmap.png"
)

# 修改配色方案（在visualize_results.py中）
sns.set_palette("viridis")  # 使用其他配色
```

---

## 📁 数据结构要求

可视化器会自动扫描以下目录结构：

```
results/
├── exp1/
│   ├── openai/
│   │   └── gpt-5-chat-latest/
│   │       └── results.csv
│   ├── anthropic/
│   │   └── claude-3-5-sonnet/
│   │       └── results.csv
│   └── ...
├── exp2/
│   └── ...
└── exp4/
    └── ...
```

**results.csv格式**：
```csv
task_type,pass,attempts,time,...
Dice_Count,0,1,2.5,...
Bingo,1,1,3.2,...
```

---

## ⚠️ 数据缺失处理

可视化器会**自动处理**以下情况：

1. **实验缺失**：某些实验（exp1/exp2/exp3/exp4）没有运行
   - ✅ 跳过该实验的图表生成
   - ✅ 在对比图中留空或用NaN填充

2. **模型缺失**：某些模型（GPT/Claude/Gemini）没有结果
   - ✅ 热力图中该列留白
   - ✅ 柱状图中不显示该模型

3. **题型缺失**：某些题型没有在某个实验中测试
   - ✅ 自动过滤，不影响其他题型

**示例**：
```python
# 即使只有exp1和exp2，也能正常运行
viz.plot_comparison_bars(
    experiments=['exp1', 'exp2', 'exp4'],  # exp4不存在也没问题
    model_filter="openai/gpt-5-chat-latest"
)
# 输出: ⚠️ 实验 exp4 没有数据，跳过
```

---

## 🎨 输出示例

### 热力图示例
![heatmap](https://via.placeholder.com/800x600.png?text=Heatmap+Example)

- 红色区域：难题型（正确率<40%）→ **推荐用于CAPTCHA**
- 橙色区域：中等难度（40-70%）
- 绿色区域：简单题型（>70%）→ 不推荐

### 散点图示例
![scatter](https://via.placeholder.com/600x600.png?text=Scatter+Example)

- 左下角红色区域：即使优化后仍然难 → **强烈推荐**
- 对角线上方：优化有效果
- 对角线下方：优化反而变差（需检查prompt）

---

## 💡 使用建议

### 论文/报告场景

1. **正文图表**：
   - Figure 1: 热力图（Exp1基线） - 展示整体难度分布
   - Figure 2: 柱状图（Exp1 vs Exp2） - 展示优化效果
   - Figure 3: 散点图 - 标注推荐CAPTCHA题型

2. **附录图表**：
   - 箱线图（跨模型稳定性）
   - 详细数值表格

### 实验分析场景

1. **快速检查实验结果**：
   ```python
   viz = quick_visualize()  # 一键生成
   ```

2. **深入分析特定题型**：
   ```python
   # 查看Dice_Count在不同实验的表现
   df = viz.data[viz.data['task_type'] == 'Dice_Count']
   print(df.groupby('experiment')['pass'].mean())
   ```

3. **对比不同模型**：
   ```python
   # 生成每个模型的独立报告
   for model in viz.data['provider_model'].unique():
       viz.plot_comparison_bars(
           experiments=['exp1', 'exp2'],
           model_filter=model,
           save_path=f"./figures/comparison_{model}.png"
       )
   ```

---

## 🐛 故障排除

### 问题1: 没有找到数据

**症状**：
```
❌ 未找到任何结果数据
```

**解决方案**：
1. 检查 `results/` 目录是否存在
2. 确认至少运行过一个实验（exp1/exp2/exp3/exp4）
3. 检查 `results.csv` 文件是否包含 `task_type` 和 `pass` 列

---

### 问题2: 图表显示异常

**症状**：图表只显示部分数据或NaN值

**解决方案**：
```python
# 检查数据完整性
viz = CAPTCHAVisualizer()
print(viz.data.info())
print(viz.data['experiment'].value_counts())
print(viz.data['task_type'].value_counts())
```

---

### 问题3: 中文显示乱码

**解决方案**（修改 `visualize_results.py`）：
```python
# 在文件开头添加
plt.rcParams['font.sans-serif'] = ['SimHei']  # Mac用PingFang SC
plt.rcParams['axes.unicode_minus'] = False
```

---

## 📦 依赖库

确保安装以下库：
```bash
pip install pandas numpy matplotlib seaborn
```

版本要求：
- pandas >= 1.3.0
- matplotlib >= 3.4.0
- seaborn >= 0.11.0
- numpy >= 1.21.0

---

## 📚 API文档

### CAPTCHAVisualizer类

#### 初始化
```python
viz = CAPTCHAVisualizer(
    results_dir: str = "./results",
    error_dir: str = "./error_analysis"
)
```

#### 方法

**plot_heatmap**
```python
viz.plot_heatmap(
    experiment: str = 'exp1',
    figsize: Tuple[int, int] = (14, 10),
    save_path: Optional[str] = None
) -> Figure
```

**plot_comparison_bars**
```python
viz.plot_comparison_bars(
    experiments: List[str] = ['exp1', 'exp2'],
    model_filter: Optional[str] = None,
    figsize: Tuple[int, int] = (18, 7),
    save_path: Optional[str] = None
) -> Figure
```

**plot_optimization_resistance**
```python
viz.plot_optimization_resistance(
    base_exp: str = 'exp1',
    opt_exp: str = 'exp2',
    model_filter: Optional[str] = None,
    figsize: Tuple[int, int] = (11, 11),
    save_path: Optional[str] = None
) -> Figure
```

**generate_captcha_recommendation**
```python
viz.generate_captcha_recommendation(
    experiment: str = 'exp2',
    threshold: float = 60.0,
    top_n: int = 8
) -> DataFrame
```

---

## 🎯 总结

**推荐工作流**：

1. 运行实验 → `run_experiment_1/2/3/4()`
2. 生成图表 → `quick_visualize()`
3. 查看推荐 → `generate_captcha_recommendation()`
4. 深入分析 → 单独生成特定图表

**关键洞察**：
- 左下角（散点图）= 强推荐CAPTCHA题型
- 跨实验一致难 = 高质量CAPTCHA
- 跨模型一致难 = 通用性强

---

## 📮 反馈

如有问题或建议，请查看：
- 代码实现：`visualize_results.py`
- 使用示例：`test.ipynb` 最后几个cells
