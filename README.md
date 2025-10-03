# AIME数据集生成系统

基于CAMEL框架的完整AIME风格数学题目生成Pipeline，包含数据生成、人工验证和质量评估。

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API Key

**方法1: 环境变量**
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-api-key"

# Linux/Mac
export OPENAI_API_KEY="your-api-key"
```

**方法2: 修改config.py**
```python
OPENAI_API_KEY = "your-api-key"
```

### 3. 生成数据

```bash
# 生成10个AIME题目
python run_full_pipeline.py --num_problems 10

# 快速测试（2个题目）
python test_stages.py --all
```

### 4. 人工验证

```bash
# 启动Web验证界面
python verification_ui.py

# 打开浏览器访问: http://127.0.0.1:7860
```

### 5. 质量评估

```bash
# 自动生成指标、图表和报告
python run_evaluation.py
```

---

## 📊 完整工作流程

```
第1步: 数据生成（自动化）
  python run_full_pipeline.py --num_problems 10
  ↓
  输出: output/stage4_improved/improved_problems.json

第2步: 人工验证（可选）
  python verification_ui.py
  ↓
  输出: verification/verified_problems/verifications.json

第3步: 质量评估（自动化）
  python run_evaluation.py
  ↓
  输出: 
    - evaluation/quality_metrics.json
    - evaluation/figures/*.png (7张图表)
    - evaluation/reports/experiment_report.md

第4步: 验证结果分析（可选）
  python analyze_verification.py
  ↓
  输出: 验证统计报告和图表
```

详细流程请查看: [WORKFLOW.md](WORKFLOW.md)

---

## 🎯 核心脚本

| 脚本 | 功能 | 输出 |
|------|------|------|
| `run_full_pipeline.py` | 4阶段数据生成 | `improved_problems.json` |
| `test_stages.py` | 测试各阶段 | 测试输出 |
| `verification_ui.py` | 人工验证Web界面 | `verifications.json` |
| `analyze_verification.py` | 验证结果分析 | 验证报告+图表 |
| `run_evaluation.py` | 质量评估 | 指标+图表+报告 |

---

## 📁 项目结构

```
aime_datagen_experiment/
├── README.md                    # 本文件
├── WORKFLOW.md                  # 详细工作流程
├── config.py                    # 配置文件
├── requirements.txt             # 依赖
│
├── run_full_pipeline.py         # 主要数据生成脚本
├── test_stages.py               # 测试脚本
├── verification_ui.py           # 人工验证UI
├── analyze_verification.py      # 验证分析
├── run_evaluation.py            # 质量评估
├── start_verification.bat       # Windows启动脚本
│
├── src/                         # 源代码
│   ├── problem_generator.py     # Stage 1: ChatAgent
│   ├── diversifier.py           # Stage 2: Self-Instruct
│   ├── solution_generator.py    # Stage 3: CoTDataGenerator
│   └── quality_improver.py      # Stage 4: SelfImprovingCoTPipeline
│
├── evaluation/                  # 评估工具
│   ├── quality_metrics.py       # 质量指标计算
│   ├── visualize_results.py     # 可视化图表
│   ├── generate_report.py       # 报告生成
│   ├── quality_metrics.json     # 指标数据
│   ├── figures/                 # 生成的图表
│   └── reports/                 # 生成的报告
│
├── verification/                # 验证系统
│   ├── verified_problems/       # 验证结果
│   └── (图表和报告)
│
└── output/                      # 生成的数据
    ├── stage1_base_problems/
    ├── stage2_diversified/
    ├── stage3_with_solutions/
    └── stage4_improved/         # 最终输出
```

---

## 🔬 Pipeline架构

### 4阶段数据生成

```
Stage 1: ChatAgent
  ↓ 生成基础AIME题目
Stage 2: Self-Instruct
  ↓ 题目多样化（带Fallback机制）
Stage 3: CoTDataGenerator
  ↓ MCTS搜索生成解答
Stage 4: SelfImprovingCoTPipeline
  ↓ STaR迭代改进质量
Final: 高质量AIME数据集
```

### 技术细节

| 模块 | 技术 | 配置 |
|------|------|------|
| Stage 1 | ChatAgent | GPT-4o, AIME prompt |
| Stage 2 | Self-Instruct | ROUGE filtering + Fallback |
| Stage 3 | CoTDataGenerator | MCTS (50 iterations) |
| Stage 4 | SelfImprovingCoTPipeline | STaR (2-3 iterations) |

---

## 🎨 人工验证指南

### 启动验证UI

```bash
python verification_ui.py
# 或双击: start_verification.bat
```

### 验证流程

1. **阅读题目**: 问题、答案、解答
2. **评分** (1-5分):
   - 正确性 (Correctness)
   - 清晰度 (Clarity)
   - 难度匹配 (Difficulty Match)
   - 完整性 (Completeness)
3. **标注状态**:
   - ✅ approved (通过)
   - ❌ rejected (拒绝)
   - 🔄 needs_revision (需修改)
4. **添加评论**: 具体反馈

### 验证标准

**通过标准 (approved)**:
- 数学完全正确
- 解答清晰完整
- 难度适中（6-9/15）
- 格式规范

**拒绝标准 (rejected)**:
- 数学错误严重
- 答案错误
- 难度严重不匹配

**需修改 (needs_revision)**:
- 有小的数学错误（可修正）
- 解答不够完整（可补充）
- 格式有问题（可调整）

---

## 📊 质量评估

### 评估指标

| 指标类别 | 具体指标 | 目标值 |
|---------|---------|--------|
| **多样性** | 多样性分数 | > 0.7 |
| **难度** | AIME范围匹配率 | > 80% |
| **主题** | 主题均衡度 | > 0.8 |
| **解答** | 完整性 | > 95% |

### 生成的图表

1. `difficulty_distribution.png` - 难度分布直方图
2. `topic_distribution.png` - 主题分布饼图
3. `answer_distribution.png` - 答案分布直方图
4. `solution_steps_distribution.png` - 解答步骤分布
5. `quality_radar.png` - 质量雷达图
6. `stage_comparison.png` - Pipeline阶段对比
7. `tag_frequency.png` - 标签频率图

### 评估报告

运行`python run_evaluation.py`后生成：
- `evaluation/quality_metrics.json` - 质量指标数据
- `evaluation/figures/*.png` - 7张可视化图表
- `evaluation/reports/experiment_report.md` - 完整实验报告

---

## 💡 使用场景

### 场景1: 快速测试

```bash
python test_stages.py --all
python run_evaluation.py
```

### 场景2: 生成论文数据

```bash
python run_full_pipeline.py --num_problems 50
python verification_ui.py  # 人工验证
python run_evaluation.py   # 生成报告和图表
python analyze_verification.py
```

### 场景3: 只看自动评估

```bash
python run_full_pipeline.py --num_problems 10
python run_evaluation.py  # 跳过人工验证
```

---

## 🔧 配置说明

### 主要配置项 (config.py)

```python
# API配置
OPENAI_API_KEY = "your-key"
MODEL_TYPE = ModelType.GPT_4O  # 或 GPT_4O_MINI

# Stage 1: 基础题目生成
STAGE1_NUM_PROBLEMS = 2

# Stage 2: 多样化
STAGE2_DIVERSIFICATION_FACTOR = 2

# Stage 3: MCTS解答生成
STAGE3_NUM_SEARCH = 50

# Stage 4: STaR改进
STAGE4_MAX_ITERATIONS = 2
```

## 📚 详细文档

- [WORKFLOW.md](WORKFLOW.md) - 完整工作流程详解（推荐阅读）

---

## 🎯 核心理解

### 数据流向

```
CAMEL生成 → improved_problems.json
              ↓
         人工验证 → verifications.json (可选)
              ↓
         质量评估 → metrics + 图表 + 报告
```

### 两种评估模式

**模式1: 自动评估（无人工标注）**
- 基于生成数据本身
- 评估多样性、难度、主题等
- 适合快速迭代

**模式2: 完整评估（含人工标注）**
- 基于生成数据 + 人工验证
- 评估所有指标 + 人工评分
- 适合论文发表

---

## 📞 获取帮助

- 查看详细流程: `cat WORKFLOW.md`
- 查看配置: `cat config.py`
- 查看依赖: `cat requirements.txt`

---

## 🎉 开始使用

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置API Key
# 编辑 config.py

# 3. 生成数据
python run_full_pipeline.py --num_problems 10

# 4. 人工验证
python verification_ui.py

# 5. 质量评估
python run_evaluation.py
```


