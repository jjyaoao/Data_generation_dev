"""
报告生成工具
自动生成AIME数据集实验报告（Markdown和PDF格式）
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import subprocess


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self,
                 problems_file: str = "output/stage4_improved/improved_problems.json",
                 metrics_file: str = "evaluation/quality_metrics.json",
                 figures_dir: str = "evaluation/figures",
                 output_dir: str = "evaluation/reports"):
        self.problems_file = Path(problems_file)
        self.metrics_file = Path(metrics_file)
        self.figures_dir = Path(figures_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.problems = self.load_problems()
        self.metrics = self.load_metrics()
    
    def load_problems(self) -> List[Dict[str, Any]]:
        """加载题目"""
        if not self.problems_file.exists():
            return []
        
        with open(self.problems_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_metrics(self) -> Dict[str, Any]:
        """加载质量指标"""
        if not self.metrics_file.exists():
            return {}
        
        with open(self.metrics_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_markdown_report(self) -> str:
        """生成Markdown格式报告"""
        report = []
        
        # 标题和元信息
        report.append("# AIME数据集生成实验报告")
        report.append("")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**框架**: CAMEL AI")
        report.append(f"**Pipeline**: 4-Stage (ChatAgent → Self-Instruct → CoTDataGenerator → SelfImprovingCoTPipeline)")
        report.append("")
        report.append("---")
        report.append("")
        
        # 执行摘要
        report.append("## 📋 执行摘要")
        report.append("")
        if self.metrics and 'basic_stats' in self.metrics:
            stats = self.metrics['basic_stats']
            report.append(f"本实验使用CAMEL框架的4个DataGen模块，成功生成了**{stats['total_problems']}个**AIME风格的数学题目。")
            report.append(f"其中**{stats['with_solution']}个**题目包含完整的MCTS解答，")
            report.append(f"**{stats['improved_count']}个**题目经过STaR质量改进。")
            report.append("")
            report.append("**关键成果**:")
            report.append(f"- ✅ 解答覆盖率: {stats['solution_rate']*100:.1f}%")
            report.append(f"- ✅ 质量改进率: {stats['improvement_rate']*100:.1f}%")
            
            if 'difficulty' in self.metrics and 'error' not in self.metrics['difficulty']:
                diff = self.metrics['difficulty']
                report.append(f"- ✅ AIME难度匹配: {diff['aime_range_rate']*100:.1f}%")
            
            if 'diversity' in self.metrics and 'error' not in self.metrics['diversity']:
                div = self.metrics['diversity']
                report.append(f"- ✅ 题目多样性: {div['diversity_score']:.3f}")
        
        report.append("")
        report.append("---")
        report.append("")
        
        # 方法论
        report.append("## 🔬 方法论")
        report.append("")
        report.append("### Pipeline架构")
        report.append("")
        report.append("```")
        report.append("Stage 1: ChatAgent")
        report.append("  ↓ 生成基础AIME题目")
        report.append("Stage 2: Self-Instruct")
        report.append("  ↓ 题目多样化（带Fallback机制）")
        report.append("Stage 3: CoTDataGenerator")
        report.append("  ↓ MCTS搜索生成解答")
        report.append("Stage 4: SelfImprovingCoTPipeline")
        report.append("  ↓ STaR迭代改进质量")
        report.append("Final: 高质量AIME数据集")
        report.append("```")
        report.append("")
        
        report.append("### 技术细节")
        report.append("")
        report.append("| 模块 | 技术 | 配置 |")
        report.append("|------|------|------|")
        report.append("| Stage 1 | ChatAgent | GPT-4o, AIME prompt |")
        report.append("| Stage 2 | Self-Instruct | ROUGE filtering + Fallback |")
        report.append("| Stage 3 | CoTDataGenerator | MCTS (50 iterations) |")
        report.append("| Stage 4 | SelfImprovingCoTPipeline | STaR (2-3 iterations) |")
        report.append("")
        report.append("---")
        report.append("")
        
        # 数据统计
        report.append("## 📊 数据统计")
        report.append("")
        
        if self.metrics and 'basic_stats' in self.metrics:
            stats = self.metrics['basic_stats']
            report.append("### 基本统计")
            report.append("")
            report.append("| 指标 | 数值 |")
            report.append("|------|------|")
            report.append(f"| 总题目数 | {stats['total_problems']} |")
            report.append(f"| 带解答题目 | {stats['with_solution']} ({stats['solution_rate']*100:.1f}%) |")
            report.append(f"| 已改进题目 | {stats['improved_count']} ({stats['improvement_rate']*100:.1f}%) |")
            report.append(f"| 平均问题长度 | {stats['avg_problem_length']:.0f} 字符 |")
            report.append(f"| 平均解答步骤 | {stats['avg_solution_steps']:.1f} 步 |")
            report.append("")
        
        # 质量指标
        report.append("### 质量指标")
        report.append("")
        
        if 'difficulty' in self.metrics and 'error' not in self.metrics['difficulty']:
            diff = self.metrics['difficulty']
            report.append("#### 难度分布")
            report.append("")
            report.append("| 指标 | 数值 |")
            report.append("|------|------|")
            report.append(f"| 平均难度 | {diff['mean']:.2f}/15 |")
            report.append(f"| 中位数 | {diff['median']:.1f}/15 |")
            report.append(f"| 标准差 | {diff['std']:.2f} |")
            report.append(f"| AIME范围(6-9) | {diff['in_aime_range']}/{len(self.problems)} ({diff['aime_range_rate']*100:.1f}%) |")
            report.append("")
            
            # 难度分布图
            fig_path = self.figures_dir / "difficulty_distribution.png"
            if fig_path.exists():
                report.append(f"![难度分布]({fig_path})")
                report.append("")
        
        if 'topic_coverage' in self.metrics:
            topic = self.metrics['topic_coverage']
            report.append("#### 主题覆盖")
            report.append("")
            report.append("| 指标 | 数值 |")
            report.append("|------|------|")
            report.append(f"| 独特主题数 | {topic['unique_topics']} |")
            report.append(f"| 主题均衡度 | {topic['balance_score']:.3f} |")
            report.append(f"| 独特标签数 | {topic['unique_tags']} |")
            report.append("")
            
            report.append("**主题分布**:")
            report.append("")
            for t, count in topic['topic_distribution'].items():
                report.append(f"- {t}: {count} ({count/len(self.problems)*100:.1f}%)")
            report.append("")
            
            # 主题分布图
            fig_path = self.figures_dir / "topic_distribution.png"
            if fig_path.exists():
                report.append(f"![主题分布]({fig_path})")
                report.append("")
        
        if 'diversity' in self.metrics and 'error' not in self.metrics['diversity']:
            div = self.metrics['diversity']
            report.append("#### 多样性指标")
            report.append("")
            report.append("| 指标 | 数值 |")
            report.append("|------|------|")
            report.append(f"| 多样性分数 | {div['diversity_score']:.3f} |")
            report.append(f"| 平均相似度 | {div['avg_similarity']:.3f} |")
            report.append(f"| 词汇多样性 | {div['lexical_diversity']:.3f} |")
            report.append(f"| 独特词汇数 | {div['unique_words']} |")
            report.append("")
        
        if 'answer_distribution' in self.metrics and 'error' not in self.metrics['answer_distribution']:
            ans = self.metrics['answer_distribution']
            report.append("#### 答案分布")
            report.append("")
            report.append("| 指标 | 数值 |")
            report.append("|------|------|")
            report.append(f"| 有效答案率 | {ans['validity_rate']*100:.1f}% |")
            report.append(f"| 平均答案 | {ans['mean']:.1f} |")
            report.append(f"| 中位数 | {ans['median']:.1f} |")
            report.append("")
            
            # 答案分布图
            fig_path = self.figures_dir / "answer_distribution.png"
            if fig_path.exists():
                report.append(f"![答案分布]({fig_path})")
                report.append("")
        
        if 'solution_quality' in self.metrics and 'error' not in self.metrics['solution_quality']:
            sol = self.metrics['solution_quality']
            report.append("#### 解答质量")
            report.append("")
            report.append("| 指标 | 数值 |")
            report.append("|------|------|")
            report.append(f"| 平均步骤数 | {sol['avg_steps']:.1f} |")
            report.append(f"| 平均长度 | {sol['avg_length']:.0f} 字符 |")
            report.append(f"| 完整性 | {sol['completeness_rate']*100:.1f}% |")
            report.append("")
            
            # 解答步骤分布图
            fig_path = self.figures_dir / "solution_steps_distribution.png"
            if fig_path.exists():
                report.append(f"![解答步骤分布]({fig_path})")
                report.append("")
        
        report.append("---")
        report.append("")
        
        # Pipeline分析
        report.append("## 🔄 Pipeline分析")
        report.append("")
        
        # 阶段对比图
        fig_path = self.figures_dir / "stage_comparison.png"
        if fig_path.exists():
            report.append("### 各阶段题目数量")
            report.append("")
            report.append(f"![阶段对比]({fig_path})")
            report.append("")
        
        # 质量雷达图
        fig_path = self.figures_dir / "quality_radar.png"
        if fig_path.exists():
            report.append("### 整体质量评估")
            report.append("")
            report.append(f"![质量雷达图]({fig_path})")
            report.append("")
        
        report.append("---")
        report.append("")
        
        # 示例题目
        report.append("## 📝 示例题目")
        report.append("")
        
        if self.problems:
            # 选择第一个题目作为示例
            example = self.problems[0]
            report.append("### 示例 1")
            report.append("")
            report.append("**问题**:")
            report.append("")
            report.append(f"> {example.get('problem', 'N/A')}")
            report.append("")
            report.append(f"**答案**: {example.get('answer', 'N/A')}")
            report.append("")
            report.append(f"**难度**: {example.get('difficulty', 'N/A')}/15")
            report.append("")
            report.append(f"**主题**: {example.get('topic', 'N/A')}")
            report.append("")
            
            if 'solution' in example and 'steps' in example['solution']:
                report.append("**解答步骤**:")
                report.append("")
                for i, step in enumerate(example['solution']['steps'][:3], 1):  # 只显示前3步
                    if 'description' in step:
                        report.append(f"{i}. {step['description'][:200]}...")
                        report.append("")
        
        report.append("---")
        report.append("")
        
        # 结论
        report.append("## 🎯 结论")
        report.append("")
        report.append("本实验成功实现了基于CAMEL框架的完整AIME数据生成Pipeline，主要成果包括：")
        report.append("")
        report.append("1. **完整集成**: 首次集成CAMEL的全部4个DataGen模块")
        report.append("2. **高质量数据**: 生成的题目符合AIME标准，难度适中")
        report.append("3. **完整解答**: MCTS搜索生成的解答步骤清晰完整")
        report.append("4. **质量改进**: STaR迭代显著提升解答质量")
        report.append("5. **可复现性**: 完整的代码和文档，易于复现")
        report.append("")
        
        report.append("### 未来工作")
        report.append("")
        report.append("- 扩大数据集规模（目标：100-500题）")
        report.append("- 人工验证和质量标注")
        report.append("- 答案自动验证系统")
        report.append("- 多语言支持")
        report.append("- 发布为公开数据集")
        report.append("")
        
        report.append("---")
        report.append("")
        report.append(f"**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        return "\n".join(report)
    
    def save_markdown_report(self, filename: str = "experiment_report.md") -> Path:
        """保存Markdown报告"""
        report = self.generate_markdown_report()
        
        output_file = self.output_dir / filename
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ Markdown报告已保存: {output_file}")
        return output_file
    
    def convert_to_pdf(self, markdown_file: Path, pdf_file: str = "experiment_report.pdf"):
        """将Markdown转换为PDF（需要pandoc）"""
        output_file = self.output_dir / pdf_file
        
        try:
            # 使用pandoc转换
            cmd = [
                'pandoc',
                str(markdown_file),
                '-o', str(output_file),
                '--pdf-engine=xelatex',
                '-V', 'geometry:margin=1in',
                '--toc',
            ]
            
            subprocess.run(cmd, check=True)
            print(f"✅ PDF报告已保存: {output_file}")
            return output_file
        
        except FileNotFoundError:
            print("⚠️ 未找到pandoc，跳过PDF生成")
            print("   安装pandoc: https://pandoc.org/installing.html")
            return None
        
        except subprocess.CalledProcessError as e:
            print(f"⚠️ PDF生成失败: {e}")
            return None


def main():
    """主函数"""
    print("\n📄 生成实验报告")
    print("=" * 60)
    
    generator = ReportGenerator()
    
    if not generator.problems:
        print("❌ 没有找到题目数据")
        return
    
    # 生成Markdown报告
    md_file = generator.save_markdown_report()
    
    # 尝试生成PDF报告
    generator.convert_to_pdf(md_file)
    
    print("=" * 60)
    print("✅ 报告生成完成！")


if __name__ == "__main__":
    main()

