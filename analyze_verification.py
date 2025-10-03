"""
验证结果分析脚本
分析人工验证的结果，生成统计报告和可视化
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 中文字体
matplotlib.rcParams['axes.unicode_minus'] = False

class VerificationAnalyzer:
    """验证结果分析器"""
    
    def __init__(self, verification_file: str = "verification/verified_problems/verifications.json"):
        self.verification_file = Path(verification_file)
        self.verifications = self.load_verifications()
    
    def load_verifications(self) -> Dict[str, Any]:
        """加载验证结果"""
        if not self.verification_file.exists():
            print(f"❌ 验证文件不存在: {self.verification_file}")
            return {}
        
        with open(self.verification_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.verifications:
            return {}
        
        total = len(self.verifications)
        
        # 状态统计
        approved = sum(1 for v in self.verifications.values() if v['status'] == 'approved')
        rejected = sum(1 for v in self.verifications.values() if v['status'] == 'rejected')
        needs_revision = sum(1 for v in self.verifications.values() if v['status'] == 'needs_revision')
        
        # 平均分数
        avg_scores = {
            'correctness': 0,
            'clarity': 0,
            'difficulty_match': 0,
            'completeness': 0
        }
        
        for v in self.verifications.values():
            for key in avg_scores:
                avg_scores[key] += v['scores'][key]
        
        for key in avg_scores:
            avg_scores[key] /= total
        
        # 分数分布
        score_distribution = {
            'correctness': [0] * 5,
            'clarity': [0] * 5,
            'difficulty_match': [0] * 5,
            'completeness': [0] * 5
        }
        
        for v in self.verifications.values():
            for key in score_distribution:
                score = v['scores'][key]
                score_distribution[key][score - 1] += 1
        
        return {
            'total': total,
            'approved': approved,
            'rejected': rejected,
            'needs_revision': needs_revision,
            'avg_scores': avg_scores,
            'score_distribution': score_distribution
        }
    
    def print_report(self):
        """打印统计报告"""
        stats = self.get_statistics()
        
        if not stats:
            print("❌ 没有验证数据")
            return
        
        print("\n" + "="*60)
        print("AIME题目验证结果分析报告")
        print("="*60)
        
        print(f"\n📊 验证统计")
        print(f"  总题目数: {stats['total']}")
        print(f"  ✅ 通过: {stats['approved']} ({stats['approved']/stats['total']*100:.1f}%)")
        print(f"  ❌ 拒绝: {stats['rejected']} ({stats['rejected']/stats['total']*100:.1f}%)")
        print(f"  🔄 需修改: {stats['needs_revision']} ({stats['needs_revision']/stats['total']*100:.1f}%)")
        
        print(f"\n📈 平均质量分数")
        for key, value in stats['avg_scores'].items():
            print(f"  {key}: {value:.2f}/5.0")
        
        print(f"\n🎯 高质量题目")
        high_quality = [
            v for v in self.verifications.values()
            if all(score >= 4 for score in v['scores'].values())
        ]
        print(f"  所有维度>=4分: {len(high_quality)} ({len(high_quality)/stats['total']*100:.1f}%)")
        
        print("\n" + "="*60)
    
    def plot_status_distribution(self, save_path: str = "verification/status_distribution.png"):
        """绘制状态分布饼图"""
        stats = self.get_statistics()
        
        if not stats:
            return
        
        labels = ['通过', '拒绝', '需修改']
        sizes = [stats['approved'], stats['rejected'], stats['needs_revision']]
        colors = ['#90EE90', '#FFB6C1', '#FFD700']
        explode = (0.1, 0, 0)
        
        plt.figure(figsize=(8, 6))
        plt.pie(sizes, explode=explode, labels=labels, colors=colors,
                autopct='%1.1f%%', shadow=True, startangle=90)
        plt.title('验证状态分布', fontsize=16, fontweight='bold')
        plt.axis('equal')
        
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ 状态分布图已保存: {save_path}")
        plt.close()
    
    def plot_score_distribution(self, save_path: str = "verification/score_distribution.png"):
        """绘制分数分布柱状图"""
        stats = self.get_statistics()
        
        if not stats:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('质量分数分布', fontsize=16, fontweight='bold')
        
        dimensions = ['correctness', 'clarity', 'difficulty_match', 'completeness']
        titles = ['正确性', '清晰度', '难度匹配', '完整性']
        
        for idx, (dim, title) in enumerate(zip(dimensions, titles)):
            ax = axes[idx // 2, idx % 2]
            distribution = stats['score_distribution'][dim]
            
            x = [1, 2, 3, 4, 5]
            ax.bar(x, distribution, color='skyblue', edgecolor='black')
            ax.set_xlabel('分数', fontsize=12)
            ax.set_ylabel('题目数量', fontsize=12)
            ax.set_title(f'{title} (平均: {stats["avg_scores"][dim]:.2f})', fontsize=14)
            ax.set_xticks(x)
            ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ 分数分布图已保存: {save_path}")
        plt.close()
    
    def plot_average_scores(self, save_path: str = "verification/average_scores.png"):
        """绘制平均分数雷达图"""
        stats = self.get_statistics()
        
        if not stats:
            return
        
        categories = ['正确性', '清晰度', '难度匹配', '完整性']
        values = [
            stats['avg_scores']['correctness'],
            stats['avg_scores']['clarity'],
            stats['avg_scores']['difficulty_match'],
            stats['avg_scores']['completeness']
        ]
        
        # 闭合雷达图
        values += values[:1]
        angles = [n / float(len(categories)) * 2 * 3.14159 for n in range(len(categories))]
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
        ax.plot(angles, values, 'o-', linewidth=2, color='blue')
        ax.fill(angles, values, alpha=0.25, color='blue')
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=12)
        ax.set_ylim(0, 5)
        ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_title('平均质量分数', fontsize=16, fontweight='bold', pad=20)
        ax.grid(True)
        
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ 平均分数雷达图已保存: {save_path}")
        plt.close()
    
    def export_approved_problems(self, output_file: str = "verification/approved_problems.json"):
        """导出通过的题目"""
        approved = [
            v['problem'] for v in self.verifications.values()
            if v['status'] == 'approved'
        ]
        
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(approved, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 已导出{len(approved)}个通过的题目: {output_file}")
    
    def export_high_quality_problems(self, output_file: str = "verification/high_quality_problems.json"):
        """导出高质量题目（所有维度>=4分）"""
        high_quality = [
            v['problem'] for v in self.verifications.values()
            if all(score >= 4 for score in v['scores'].values())
        ]
        
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(high_quality, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 已导出{len(high_quality)}个高质量题目: {output_file}")


def main():
    """主函数"""
    print("\n🔍 AIME题目验证结果分析")
    print("="*60)
    
    analyzer = VerificationAnalyzer()
    
    if not analyzer.verifications:
        print("\n❌ 没有找到验证数据")
        print("请先使用 verification_ui.py 进行人工验证")
        return
    
    # 打印统计报告
    analyzer.print_report()
    
    # 生成可视化
    print("\n📊 生成可视化图表...")
    analyzer.plot_status_distribution()
    analyzer.plot_score_distribution()
    analyzer.plot_average_scores()
    
    # 导出数据
    print("\n💾 导出数据...")
    analyzer.export_approved_problems()
    analyzer.export_high_quality_problems()
    
    print("\n✅ 分析完成！")
    print("="*60)


if __name__ == "__main__":
    main()

