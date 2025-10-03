"""
完整评估脚本
一次运行所有评估工具：质量指标计算、可视化、报告生成
"""

import sys
from pathlib import Path

# 添加evaluation目录到路径
sys.path.insert(0, str(Path(__file__).parent / "evaluation"))

from evaluation.quality_metrics import QualityMetrics
from evaluation.visualize_results import ResultVisualizer
from evaluation.generate_report import ReportGenerator


def run_full_evaluation():
    """运行完整评估流程"""
    print("\n" + "=" * 60)
    print("🔍 AIME数据集完整评估")
    print("=" * 60)
    
    # Step 1: 计算质量指标
    print("\n📊 Step 1: 计算质量指标...")
    print("-" * 60)
    
    calculator = QualityMetrics()
    
    if not calculator.problems:
        print("❌ 没有找到题目数据")
        print("请先运行: python run_full_pipeline.py")
        return
    
    # 显示统计报告
    report = calculator.generate_summary_report()
    print(report)
    
    # 保存指标
    metrics = calculator.save_metrics()
    
    # Step 2: 生成可视化图表
    print("\n📈 Step 2: 生成可视化图表...")
    print("-" * 60)
    
    visualizer = ResultVisualizer()
    visualizer.generate_all_plots()
    
    # Step 3: 生成实验报告
    print("\n📄 Step 3: 生成实验报告...")
    print("-" * 60)
    
    generator = ReportGenerator()
    md_file = generator.save_markdown_report()
    
    # 尝试生成PDF
    generator.convert_to_pdf(md_file)
    
    # 总结
    print("\n" + "=" * 60)
    print("✅ 完整评估完成！")
    print("=" * 60)
    
    print("\n📁 生成的文件:")
    print(f"  - 质量指标: evaluation/quality_metrics.json")
    print(f"  - 可视化图表: evaluation/figures/*.png")
    print(f"  - Markdown报告: evaluation/reports/experiment_report.md")
    print(f"  - PDF报告: evaluation/reports/experiment_report.pdf (如果安装了pandoc)")
    
    print("\n🎯 下一步:")
    print("  1. 查看报告: evaluation/reports/experiment_report.md")
    print("  2. 查看图表: evaluation/figures/")
    print("  3. 人工验证: python verification_ui.py")
    print("  4. 分析验证结果: python analyze_verification.py")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_full_evaluation()

