# AIME数据集生成完整工作流程

## 📋 整体流程概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    AIME数据集生成工作流                          │
└─────────────────────────────────────────────────────────────────┘

第一阶段：数据生成（自动化）
┌──────────────────────────────────────────────────────────────┐
│  CAMEL Pipeline (4 Stages)                                   │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐            │
│  │Stage 1 │→ │Stage 2 │→ │Stage 3 │→ │Stage 4 │            │
│  │ChatAgent│ │Self-   │  │CoT     │  │STaR    │            │
│  │        │  │Instruct│  │MCTS    │  │Improve │            │
│  └────────┘  └────────┘  └────────┘  └────────┘            │
│       ↓                                                       │
│  生成的数据：improved_problems.json (4个题目)                │
└──────────────────────────────────────────────────────────────┘
                            ↓
第二阶段：人工验证（人工标注）
┌──────────────────────────────────────────────────────────────┐
│  Human Verification (Web UI)                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  verification_ui.py                                  │    │
│  │  - 阅读题目、答案、解答                              │    │
│  │  - 评分（正确性、清晰度、难度、完整性）              │    │
│  │  - 标注状态（通过/拒绝/需修改）                      │    │
│  │  - 添加评论                                          │    │
│  └─────────────────────────────────────────────────────┘    │
│       ↓                                                       │
│  验证结果：verifications.json (人工标注数据)                 │
└──────────────────────────────────────────────────────────────┘
                            ↓
第三阶段：质量评估（自动化）
┌──────────────────────────────────────────────────────────────┐
│  Quality Evaluation                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │quality_metrics │→ │visualize_      │→ │generate_     │  │
│  │.py             │  │results.py      │  │report.py     │  │
│  │计算指标        │  │生成图表        │  │生成报告      │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
│       ↓                    ↓                    ↓            │
│  metrics.json         figures/*.png      experiment_report  │
└──────────────────────────────────────────────────────────────┘
                            ↓
第四阶段：最终输出
┌──────────────────────────────────────────────────────────────┐
│  Final Outputs                                               │
│  - 高质量AIME题目数据集                                      │
│  - 人工验证标注                                              │
│  - 质量评估报告                                              │
│  - 可视化图表                                                │
│  - 实验报告（论文素材）                                      │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔄 详细工作流程

### **阶段1: 数据生成（CAMEL自动化）**

**目标**: 使用CAMEL生成AIME风格的数学题目

**步骤**:
```bash
python run_full_pipeline.py --num_problems 10
```

**输出**:
- `output/stage1_base_problems/base_problems.json` (2个基础题目)
- `output/stage2_diversified/diversified_problems.json` (4个多样化题目)
- `output/stage3_with_solutions/problems_with_solutions.json` (4个带解答)
- `output/stage4_improved/improved_problems.json` (4个改进后的题目) ✅

**数据格式**:
```json
{
  "id": "gen_1",
  "problem": "Let n be the smallest...",
  "answer": 25,
  "difficulty": 6,
  "topic": "Number Theory",
  "tags": ["modular arithmetic", "divisibility"],
  "solution": {
    "steps": [...],
    "final_answer": 25
  },
  "improved": true
}
```

---

### **阶段2: 人工验证（人工标注）**

**目标**: 专家验证题目质量，打标签

**步骤**:
```bash
python verification_ui.py
# 打开浏览器: http://127.0.0.1:7860
```

**验证内容**:
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

**输出**:
- `verification/verified_problems/verifications.json` ✅

**验证数据格式**:
```json
{
  "gen_1": {
    "problem_id": "gen_1",
    "timestamp": "2025-10-03T20:00:00",
    "scores": {
      "correctness": 5,
      "clarity": 4,
      "difficulty_match": 4,
      "completeness": 5
    },
    "status": "approved",
    "comments": "题目质量很好，解答清晰完整。",
    "problem": {...}
  }
}
```

---

### **阶段3: 质量评估（自动化）**

**目标**: 基于生成的数据和人工标注，自动计算质量指标和生成报告

**步骤**:
```bash
python run_evaluation.py
```

**这个命令会自动执行3个步骤**:

#### **3.1 计算质量指标**
```bash
python evaluation/quality_metrics.py
```

**计算内容**:
- 基本统计（题目数、解答率等）
- 多样性指标（TF-IDF相似度、词汇多样性）
- 难度分布
- 主题覆盖
- 答案分布
- 解答质量

**输出**:
- `evaluation/quality_metrics.json` ✅

#### **3.2 生成可视化图表**
```bash
python evaluation/visualize_results.py
```

**生成7张图表**:
1. 难度分布直方图
2. 主题分布饼图
3. 答案分布直方图
4. 解答步骤分布
5. 质量雷达图
6. Pipeline阶段对比
7. 标签频率图

**输出**:
- `evaluation/figures/*.png` (7张图表) ✅

#### **3.3 生成实验报告**
```bash
python evaluation/generate_report.py
```

**报告内容**:
- 执行摘要
- 方法论
- 数据统计
- 质量指标
- Pipeline分析
- 示例题目
- 结论

**输出**:
- `evaluation/reports/experiment_report.md` ✅
- `evaluation/reports/experiment_report.pdf` (可选)

---

### **阶段4: 验证结果分析（可选）**

**目标**: 分析人工验证的结果

**步骤**:
```bash
python analyze_verification.py
```

**输出**:
- 验证统计报告（控制台）
- 3张验证相关图表:
  - `verification/status_distribution.png` (状态分布)
  - `verification/score_distribution.png` (分数分布)
  - `verification/average_scores.png` (平均分数雷达图)
- `verification/approved_problems.json` (通过的题目)
- `verification/high_quality_problems.json` (高质量题目)

---

## 📊 数据流向图

```
┌─────────────────┐
│  CAMEL Pipeline │
│  (自动生成)     │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────┐
│  improved_problems.json         │  ← 生成的题目数据
│  (4个AIME题目)                  │
└────────┬────────────────────────┘
         │
         ↓
┌─────────────────────────────────┐
│  verification_ui.py             │  ← 人工验证
│  (Web界面打标签)                │
└────────┬────────────────────────┘
         │
         ↓
┌─────────────────────────────────┐
│  verifications.json             │  ← 人工标注数据
│  (验证结果和评分)               │
└────────┬────────────────────────┘
         │
         ├──────────────────────────┐
         ↓                          ↓
┌──────────────────┐      ┌──────────────────┐
│ quality_metrics  │      │ analyze_         │
│ (计算指标)       │      │ verification     │
└────────┬─────────┘      │ (分析验证结果)   │
         │                └──────────────────┘
         ↓
┌──────────────────┐
│ quality_metrics  │  ← 质量指标数据
│ .json            │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│ visualize_       │
│ results          │
│ (生成图表)       │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│ figures/*.png    │  ← 7张可视化图表
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│ generate_report  │
│ (生成报告)       │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│ experiment_      │  ← 最终实验报告
│ report.md        │
└──────────────────┘
```

---

## 🎯 关键理解

### **您的理解是正确的！**

完整流程是：

1. **CAMEL生成数据** → `improved_problems.json`
2. **人工打标签** → `verifications.json`
3. **自动评估** → `quality_metrics.json` + `figures/*.png` + `experiment_report.md`

### **重要说明**

#### **质量评估工具的两种使用方式**:

**方式1: 只基于生成的数据（无需人工标注）**
```bash
# 生成数据后直接评估
python run_full_pipeline.py --num_problems 10
python run_evaluation.py
```

这种方式会评估：
- ✅ 题目多样性
- ✅ 难度分布
- ✅ 主题覆盖
- ✅ 答案分布
- ✅ 解答质量
- ❌ 人工评分（没有）

**方式2: 基于生成数据 + 人工标注（完整评估）**
```bash
# 1. 生成数据
python run_full_pipeline.py --num_problems 10

# 2. 人工验证
python verification_ui.py
# 在Web界面打标签

# 3. 评估（包含人工标注）
python run_evaluation.py

# 4. 分析验证结果
python analyze_verification.py
```

这种方式会评估：
- ✅ 题目多样性
- ✅ 难度分布
- ✅ 主题覆盖
- ✅ 答案分布
- ✅ 解答质量
- ✅ 人工评分（正确性、清晰度等）
- ✅ 通过率、拒绝率

---

## 📝 完整操作示例

### **场景: 生成10个题目并完整评估**

```bash
# Step 1: 生成数据（自动化）
python run_full_pipeline.py --num_problems 10
# 输出: output/stage4_improved/improved_problems.json (10个题目)

# Step 2: 人工验证（人工标注）
python verification_ui.py
# 在浏览器中打开 http://127.0.0.1:7860
# 逐个验证10个题目，打分和标注
# 输出: verification/verified_problems/verifications.json

# Step 3: 质量评估（自动化）
python run_evaluation.py
# 输出:
#   - evaluation/quality_metrics.json
#   - evaluation/figures/*.png (7张图表)
#   - evaluation/reports/experiment_report.md

# Step 4: 验证结果分析（自动化）
python analyze_verification.py
# 输出:
#   - verification/status_distribution.png
#   - verification/score_distribution.png
#   - verification/average_scores.png
#   - verification/approved_problems.json
```

---

## 🔍 数据依赖关系

```
improved_problems.json (必需)
    ↓
    ├─→ quality_metrics.py (自动评估)
    │       ↓
    │   quality_metrics.json
    │       ↓
    │   visualize_results.py
    │       ↓
    │   figures/*.png
    │       ↓
    │   generate_report.py
    │       ↓
    │   experiment_report.md
    │
    └─→ verification_ui.py (人工标注)
            ↓
        verifications.json
            ↓
        analyze_verification.py
            ↓
        verification_report.md + 图表
```

---

## 💡 最佳实践

### **推荐工作流程**

1. **小规模测试** (2-4个题目)
   ```bash
   python test_stages.py --all
   python verification_ui.py  # 快速验证
   python run_evaluation.py
   ```

2. **中等规模** (10-20个题目)
   ```bash
   python run_full_pipeline.py --num_problems 10
   python verification_ui.py  # 完整验证
   python run_evaluation.py
   python analyze_verification.py
   ```

3. **大规模生产** (50-100个题目)
   ```bash
   python run_full_pipeline.py --num_problems 50
   # 多人分工验证
   python verification_ui.py
   python run_evaluation.py
   python analyze_verification.py
   ```

---

## ❓ 常见问题

**Q: 必须人工验证才能生成报告吗？**  
A: 不是。可以直接运行`run_evaluation.py`，但报告中不会包含人工评分数据。

**Q: 人工验证的数据用在哪里？**  
A: 主要用在`analyze_verification.py`中，生成验证统计和筛选高质量题目。

**Q: 质量指标是基于什么计算的？**  
A: 基于生成的题目数据本身（文本、难度、主题等），不依赖人工标注。

**Q: 如果只想看自动评估结果？**  
A: 直接运行`python run_evaluation.py`，跳过人工验证步骤。

---

**现在流程清楚了吗？** 🎯

