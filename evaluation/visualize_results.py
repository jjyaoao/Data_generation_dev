"""
可视化工具
生成AIME题目数据集的各种图表和对比分析
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from collections import Counter

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


class ResultVisualizer:
    """结果可视化器"""
    
    def __init__(self, 
                 problems_file: str = "output/stage4_improved/improved_problems.json",
                 metrics_file: str = "evaluation/quality_metrics.json",
                 output_dir: str = "evaluation/figures"):
        self.problems_file = Path(problems_file)
        self.metrics_file = Path(metrics_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.problems = self.load_problems()
        self.metrics = self.load_metrics()
    
    def load_problems(self) -> List[Dict[str, Any]]:
        """加载题目"""
        if not self.problems_file.exists():
            print(f"⚠️ 题目文件不存在: {self.problems_file}")
            return []
        
        with open(self.problems_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_metrics(self) -> Dict[str, Any]:
        """加载质量指标"""
        if not self.metrics_file.exists():
            print(f"⚠️ 指标文件不存在: {self.metrics_file}")
            return {}
        
        with open(self.metrics_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def plot_difficulty_distribution(self):
        """绘制难度分布直方图"""
        difficulties = [p.get('difficulty', 0) for p in self.problems if 'difficulty' in p]
        
        if not difficulties:
            print("⚠️ 没有难度数据")
            return
        
        plt.figure(figsize=(10, 6))
        
        # 绘制直方图
        counts, bins, patches = plt.hist(difficulties, bins=range(1, 17), 
                                         edgecolor='black', alpha=0.7, color='skyblue')
        
        # 标记AIME范围
        for i, patch in enumerate(patches):
            if 6 <= bins[i] <= 9:
                patch.set_facecolor('lightgreen')
                patch.set_alpha(0.8)
        
        plt.xlabel('难度等级', fontsize=12)
        plt.ylabel('题目数量', fontsize=12)
        plt.title('AIME题目难度分布', fontsize=14, fontweight='bold')
        plt.xticks(range(1, 16))
        plt.grid(axis='y', alpha=0.3)
        
        # 添加AIME范围标注
        plt.axvspan(6, 9, alpha=0.2, color='green', label='AIME标准范围(6-9)')
        plt.legend()
        
        # 添加统计信息
        mean_diff = np.mean(difficulties)
        plt.axvline(mean_diff, color='red', linestyle='--', linewidth=2, label=f'平均值: {mean_diff:.2f}')
        
        output_file = self.output_dir / "difficulty_distribution.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ 难度分布图已保存: {output_file}")
        plt.close()
    
    def plot_topic_distribution(self):
        """绘制主题分布饼图"""
        topics = [p.get('topic', 'Unknown') for p in self.problems]
        topic_counts = Counter(topics)
        
        if not topic_counts:
            print("⚠️ 没有主题数据")
            return
        
        plt.figure(figsize=(10, 8))
        
        labels = list(topic_counts.keys())
        sizes = list(topic_counts.values())
        colors = plt.cm.Set3(range(len(labels)))
        
        # 突出显示最大的部分
        explode = [0.1 if size == max(sizes) else 0 for size in sizes]
        
        plt.pie(sizes, explode=explode, labels=labels, colors=colors,
                autopct='%1.1f%%', shadow=True, startangle=90)
        plt.title('AIME题目主题分布', fontsize=14, fontweight='bold')
        plt.axis('equal')
        
        output_file = self.output_dir / "topic_distribution.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ 主题分布图已保存: {output_file}")
        plt.close()
    
    def plot_answer_distribution(self):
        """绘制答案分布图"""
        answers = [p.get('answer', -1) for p in self.problems if 'answer' in p and 0 <= p['answer'] <= 999]
        
        if not answers:
            print("⚠️ 没有答案数据")
            return
        
        plt.figure(figsize=(12, 6))
        
        # 绘制直方图
        plt.hist(answers, bins=20, edgecolor='black', alpha=0.7, color='coral')
        
        plt.xlabel('答案值', fontsize=12)
        plt.ylabel('题目数量', fontsize=12)
        plt.title('AIME题目答案分布 (0-999)', fontsize=14, fontweight='bold')
        plt.grid(axis='y', alpha=0.3)
        
        # 添加统计信息
        mean_ans = np.mean(answers)
        median_ans = np.median(answers)
        plt.axvline(mean_ans, color='red', linestyle='--', linewidth=2, label=f'平均值: {mean_ans:.1f}')
        plt.axvline(median_ans, color='blue', linestyle='--', linewidth=2, label=f'中位数: {median_ans:.1f}')
        plt.legend()
        
        output_file = self.output_dir / "answer_distribution.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ 答案分布图已保存: {output_file}")
        plt.close()
    
    def plot_solution_steps_distribution(self):
        """绘制解答步骤数分布"""
        step_counts = []
        for p in self.problems:
            if 'solution' in p and 'steps' in p['solution']:
                step_counts.append(len(p['solution']['steps']))
        
        if not step_counts:
            print("⚠️ 没有解答步骤数据")
            return
        
        plt.figure(figsize=(10, 6))
        
        plt.hist(step_counts, bins=range(min(step_counts), max(step_counts) + 2), 
                 edgecolor='black', alpha=0.7, color='lightblue')
        
        plt.xlabel('解答步骤数', fontsize=12)
        plt.ylabel('题目数量', fontsize=12)
        plt.title('AIME题目解答步骤数分布', fontsize=14, fontweight='bold')
        plt.grid(axis='y', alpha=0.3)
        
        # 添加统计信息
        mean_steps = np.mean(step_counts)
        plt.axvline(mean_steps, color='red', linestyle='--', linewidth=2, label=f'平均值: {mean_steps:.1f}')
        plt.legend()
        
        output_file = self.output_dir / "solution_steps_distribution.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ 解答步骤分布图已保存: {output_file}")
        plt.close()
    
    def plot_quality_radar(self):
        """绘制质量指标雷达图"""
        if not self.metrics or 'basic_stats' not in self.metrics:
            print("⚠️ 没有质量指标数据")
            return
        
        # 提取指标
        categories = ['解答率', '改进率', '难度匹配', '主题均衡', '多样性']
        
        values = [
            self.metrics.get('basic_stats', {}).get('solution_rate', 0),
            self.metrics.get('basic_stats', {}).get('improvement_rate', 0),
            self.metrics.get('difficulty', {}).get('aime_range_rate', 0),
            self.metrics.get('topic_coverage', {}).get('balance_score', 0),
            self.metrics.get('diversity', {}).get('diversity_score', 0),
        ]
        
        # 闭合雷达图
        values += values[:1]
        angles = [n / float(len(categories)) * 2 * np.pi for n in range(len(categories))]
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        ax.plot(angles, values, 'o-', linewidth=2, color='blue', label='当前数据集')
        ax.fill(angles, values, alpha=0.25, color='blue')
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=12)
        ax.set_ylim(0, 1)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'])
        ax.set_title('AIME数据集质量雷达图', fontsize=14, fontweight='bold', pad=20)
        ax.grid(True)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        
        output_file = self.output_dir / "quality_radar.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ 质量雷达图已保存: {output_file}")
        plt.close()
    
    def plot_stage_comparison(self):
        """绘制各阶段对比图"""
        # 加载各阶段数据
        stages = {
            'Stage 1': 'output/stage1_base_problems/base_problems.json',
            'Stage 2': 'output/stage2_diversified/diversified_problems.json',
            'Stage 3': 'output/stage3_with_solutions/problems_with_solutions.json',
            'Stage 4': 'output/stage4_improved/improved_problems.json',
        }
        
        stage_counts = {}
        for stage_name, file_path in stages.items():
            if Path(file_path).exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    stage_counts[stage_name] = len(data)
            else:
                stage_counts[stage_name] = 0
        
        if not any(stage_counts.values()):
            print("⚠️ 没有阶段数据")
            return
        
        plt.figure(figsize=(10, 6))
        
        stages_list = list(stage_counts.keys())
        counts = list(stage_counts.values())
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        bars = plt.bar(stages_list, counts, color=colors, edgecolor='black', alpha=0.8)
        
        # 在柱子上添加数值
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        plt.xlabel('Pipeline阶段', fontsize=12)
        plt.ylabel('题目数量', fontsize=12)
        plt.title('AIME数据生成Pipeline各阶段题目数量', fontsize=14, fontweight='bold')
        plt.grid(axis='y', alpha=0.3)
        
        output_file = self.output_dir / "stage_comparison.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ 阶段对比图已保存: {output_file}")
        plt.close()
    
    def plot_tag_frequency(self):
        """绘制标签频率图"""
        all_tags = []
        for p in self.problems:
            if 'tags' in p:
                all_tags.extend(p['tags'])
        
        if not all_tags:
            print("⚠️ 没有标签数据")
            return
        
        tag_counts = Counter(all_tags)
        top_tags = tag_counts.most_common(15)
        
        plt.figure(figsize=(12, 6))
        
        tags = [t[0] for t in top_tags]
        counts = [t[1] for t in top_tags]
        
        plt.barh(tags, counts, color='teal', edgecolor='black', alpha=0.7)
        plt.xlabel('出现次数', fontsize=12)
        plt.ylabel('标签', fontsize=12)
        plt.title('AIME题目标签频率 (Top 15)', fontsize=14, fontweight='bold')
        plt.grid(axis='x', alpha=0.3)
        
        # 在柱子上添加数值
        for i, count in enumerate(counts):
            plt.text(count, i, f' {count}', va='center', fontsize=10)
        
        output_file = self.output_dir / "tag_frequency.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ 标签频率图已保存: {output_file}")
        plt.close()
    
    def generate_all_plots(self):
        """生成所有图表"""
        print("\n📊 生成可视化图表...")
        print("=" * 60)
        
        self.plot_difficulty_distribution()
        self.plot_topic_distribution()
        self.plot_answer_distribution()
        self.plot_solution_steps_distribution()
        self.plot_quality_radar()
        self.plot_stage_comparison()
        self.plot_tag_frequency()
        
        print("=" * 60)
        print(f"✅ 所有图表已生成！保存在: {self.output_dir}")


def main():
    """主函数"""
    print("\n🎨 AIME数据集可视化")
    
    visualizer = ResultVisualizer()
    
    if not visualizer.problems:
        print("❌ 没有找到题目数据")
        return
    
    visualizer.generate_all_plots()
    
    print("\n✅ 可视化完成！")


if __name__ == "__main__":
    main()

