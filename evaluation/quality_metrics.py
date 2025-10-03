"""
质量评估工具
自动计算AIME题目的多样性指标和质量指标
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re


class QualityMetrics:
    """质量指标计算器"""
    
    def __init__(self, problems_file: str = "output/stage4_improved/improved_problems.json"):
        self.problems_file = Path(problems_file)
        self.problems = self.load_problems()
    
    def load_problems(self) -> List[Dict[str, Any]]:
        """加载题目"""
        if not self.problems_file.exists():
            print(f"❌ 题目文件不存在: {self.problems_file}")
            return []
        
        with open(self.problems_file, 'r', encoding='utf-8') as f:
            problems = json.load(f)
        
        return problems
    
    def calculate_all_metrics(self) -> Dict[str, Any]:
        """计算所有质量指标"""
        if not self.problems:
            return {}
        
        metrics = {
            'basic_stats': self.get_basic_statistics(),
            'diversity': self.calculate_diversity_metrics(),
            'difficulty': self.analyze_difficulty_distribution(),
            'topic_coverage': self.analyze_topic_coverage(),
            'answer_distribution': self.analyze_answer_distribution(),
            'solution_quality': self.analyze_solution_quality(),
            'similarity': self.calculate_similarity_metrics(),
        }
        
        return metrics
    
    def get_basic_statistics(self) -> Dict[str, Any]:
        """基本统计信息"""
        total = len(self.problems)
        
        # 统计有解答的题目
        with_solution = sum(1 for p in self.problems if 'solution' in p and p['solution'])
        
        # 统计改进的题目
        improved = sum(1 for p in self.problems if p.get('improved', False))
        
        # 平均问题长度
        avg_problem_length = np.mean([len(p.get('problem', '')) for p in self.problems])
        
        # 平均解答步骤数
        avg_solution_steps = 0
        if with_solution > 0:
            total_steps = sum(
                len(p['solution'].get('steps', [])) 
                for p in self.problems 
                if 'solution' in p and 'steps' in p['solution']
            )
            avg_solution_steps = total_steps / with_solution
        
        return {
            'total_problems': total,
            'with_solution': with_solution,
            'solution_rate': with_solution / total if total > 0 else 0,
            'improved_count': improved,
            'improvement_rate': improved / total if total > 0 else 0,
            'avg_problem_length': avg_problem_length,
            'avg_solution_steps': avg_solution_steps,
        }
    
    def calculate_diversity_metrics(self) -> Dict[str, Any]:
        """计算多样性指标"""
        # 提取所有问题文本
        problem_texts = [p.get('problem', '') for p in self.problems]
        
        if len(problem_texts) < 2:
            return {'error': 'Not enough problems for diversity calculation'}
        
        # 使用TF-IDF计算文本相似度
        vectorizer = TfidfVectorizer(max_features=100)
        try:
            tfidf_matrix = vectorizer.fit_transform(problem_texts)
            
            # 计算平均余弦相似度
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # 排除对角线（自己和自己的相似度）
            n = len(problem_texts)
            total_similarity = (similarity_matrix.sum() - n) / (n * (n - 1))
            
            # 计算最大和最小相似度
            upper_triangle = similarity_matrix[np.triu_indices(n, k=1)]
            max_similarity = upper_triangle.max()
            min_similarity = upper_triangle.min()
            
            # 多样性分数（1 - 平均相似度）
            diversity_score = 1 - total_similarity
            
        except Exception as e:
            return {'error': f'TF-IDF calculation failed: {str(e)}'}
        
        # 词汇多样性
        all_words = []
        for text in problem_texts:
            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            all_words.extend(words)
        
        unique_words = len(set(all_words))
        total_words = len(all_words)
        lexical_diversity = unique_words / total_words if total_words > 0 else 0
        
        return {
            'avg_similarity': total_similarity,
            'max_similarity': max_similarity,
            'min_similarity': min_similarity,
            'diversity_score': diversity_score,
            'lexical_diversity': lexical_diversity,
            'unique_words': unique_words,
            'total_words': total_words,
        }
    
    def analyze_difficulty_distribution(self) -> Dict[str, Any]:
        """分析难度分布"""
        difficulties = [p.get('difficulty', 0) for p in self.problems if 'difficulty' in p]
        
        if not difficulties:
            return {'error': 'No difficulty information'}
        
        return {
            'mean': np.mean(difficulties),
            'median': np.median(difficulties),
            'std': np.std(difficulties),
            'min': min(difficulties),
            'max': max(difficulties),
            'distribution': dict(Counter(difficulties)),
            'in_aime_range': sum(1 for d in difficulties if 6 <= d <= 9),
            'aime_range_rate': sum(1 for d in difficulties if 6 <= d <= 9) / len(difficulties),
        }
    
    def analyze_topic_coverage(self) -> Dict[str, Any]:
        """分析主题覆盖"""
        topics = [p.get('topic', 'Unknown') for p in self.problems]
        topic_counts = Counter(topics)
        
        # 标签统计
        all_tags = []
        for p in self.problems:
            if 'tags' in p:
                all_tags.extend(p['tags'])
        
        tag_counts = Counter(all_tags)
        
        # 计算主题均衡度（熵）
        total = len(topics)
        topic_entropy = 0
        for count in topic_counts.values():
            p = count / total
            topic_entropy -= p * np.log2(p) if p > 0 else 0
        
        # 最大熵（完全均衡）
        max_entropy = np.log2(len(topic_counts)) if len(topic_counts) > 0 else 1
        balance_score = topic_entropy / max_entropy if max_entropy > 0 else 0
        
        return {
            'topic_distribution': dict(topic_counts),
            'unique_topics': len(topic_counts),
            'topic_entropy': topic_entropy,
            'balance_score': balance_score,
            'tag_distribution': dict(tag_counts.most_common(10)),
            'unique_tags': len(tag_counts),
        }
    
    def analyze_answer_distribution(self) -> Dict[str, Any]:
        """分析答案分布"""
        answers = [p.get('answer', -1) for p in self.problems if 'answer' in p]
        
        if not answers:
            return {'error': 'No answer information'}
        
        # 检查答案范围
        valid_answers = [a for a in answers if 0 <= a <= 999]
        
        # 答案分布统计
        answer_ranges = {
            '0-99': sum(1 for a in valid_answers if 0 <= a < 100),
            '100-199': sum(1 for a in valid_answers if 100 <= a < 200),
            '200-299': sum(1 for a in valid_answers if 200 <= a < 300),
            '300-499': sum(1 for a in valid_answers if 300 <= a < 500),
            '500-999': sum(1 for a in valid_answers if 500 <= a <= 999),
        }
        
        return {
            'total_answers': len(answers),
            'valid_answers': len(valid_answers),
            'validity_rate': len(valid_answers) / len(answers) if answers else 0,
            'mean': np.mean(valid_answers) if valid_answers else 0,
            'median': np.median(valid_answers) if valid_answers else 0,
            'std': np.std(valid_answers) if valid_answers else 0,
            'range_distribution': answer_ranges,
        }
    
    def analyze_solution_quality(self) -> Dict[str, Any]:
        """分析解答质量"""
        solutions = [p['solution'] for p in self.problems if 'solution' in p and p['solution']]
        
        if not solutions:
            return {'error': 'No solution information'}
        
        # 解答步骤数统计
        step_counts = [len(s.get('steps', [])) for s in solutions]
        
        # 解答长度统计
        solution_lengths = []
        for s in solutions:
            total_length = 0
            for step in s.get('steps', []):
                if 'description' in step:
                    total_length += len(step['description'])
            solution_lengths.append(total_length)
        
        # 解答完整性（有final_answer的比例）
        with_final_answer = sum(1 for s in solutions if 'final_answer' in s)
        
        return {
            'total_solutions': len(solutions),
            'avg_steps': np.mean(step_counts) if step_counts else 0,
            'median_steps': np.median(step_counts) if step_counts else 0,
            'min_steps': min(step_counts) if step_counts else 0,
            'max_steps': max(step_counts) if step_counts else 0,
            'avg_length': np.mean(solution_lengths) if solution_lengths else 0,
            'with_final_answer': with_final_answer,
            'completeness_rate': with_final_answer / len(solutions) if solutions else 0,
        }
    
    def calculate_similarity_metrics(self) -> Dict[str, Any]:
        """计算相似度指标（找出最相似和最不相似的题目对）"""
        problem_texts = [p.get('problem', '') for p in self.problems]
        
        if len(problem_texts) < 2:
            return {'error': 'Not enough problems'}
        
        try:
            vectorizer = TfidfVectorizer(max_features=100)
            tfidf_matrix = vectorizer.fit_transform(problem_texts)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            n = len(problem_texts)
            
            # 找出最相似的题目对
            max_sim = -1
            max_pair = (0, 0)
            for i in range(n):
                for j in range(i + 1, n):
                    if similarity_matrix[i, j] > max_sim:
                        max_sim = similarity_matrix[i, j]
                        max_pair = (i, j)
            
            # 找出最不相似的题目对
            min_sim = 2
            min_pair = (0, 0)
            for i in range(n):
                for j in range(i + 1, n):
                    if similarity_matrix[i, j] < min_sim:
                        min_sim = similarity_matrix[i, j]
                        min_pair = (i, j)
            
            return {
                'most_similar_pair': {
                    'indices': max_pair,
                    'similarity': max_sim,
                    'problem_1_id': self.problems[max_pair[0]].get('id', 'unknown'),
                    'problem_2_id': self.problems[max_pair[1]].get('id', 'unknown'),
                },
                'least_similar_pair': {
                    'indices': min_pair,
                    'similarity': min_sim,
                    'problem_1_id': self.problems[min_pair[0]].get('id', 'unknown'),
                    'problem_2_id': self.problems[min_pair[1]].get('id', 'unknown'),
                }
            }
        except Exception as e:
            return {'error': f'Similarity calculation failed: {str(e)}'}
    
    def generate_summary_report(self) -> str:
        """生成摘要报告"""
        metrics = self.calculate_all_metrics()
        
        if not metrics:
            return "❌ 无法生成报告：没有数据"
        
        report = []
        report.append("=" * 60)
        report.append("AIME题目质量评估报告")
        report.append("=" * 60)
        
        # 基本统计
        if 'basic_stats' in metrics:
            stats = metrics['basic_stats']
            report.append("\n📊 基本统计")
            report.append(f"  总题目数: {stats['total_problems']}")
            report.append(f"  带解答: {stats['with_solution']} ({stats['solution_rate']*100:.1f}%)")
            report.append(f"  已改进: {stats['improved_count']} ({stats['improvement_rate']*100:.1f}%)")
            report.append(f"  平均问题长度: {stats['avg_problem_length']:.0f} 字符")
            report.append(f"  平均解答步骤: {stats['avg_solution_steps']:.1f} 步")
        
        # 多样性指标
        if 'diversity' in metrics and 'error' not in metrics['diversity']:
            div = metrics['diversity']
            report.append("\n🎨 多样性指标")
            report.append(f"  多样性分数: {div['diversity_score']:.3f} (越高越好)")
            report.append(f"  平均相似度: {div['avg_similarity']:.3f}")
            report.append(f"  词汇多样性: {div['lexical_diversity']:.3f}")
            report.append(f"  独特词汇: {div['unique_words']}")
        
        # 难度分布
        if 'difficulty' in metrics and 'error' not in metrics['difficulty']:
            diff = metrics['difficulty']
            report.append("\n📈 难度分布")
            report.append(f"  平均难度: {diff['mean']:.2f}/15")
            report.append(f"  中位数: {diff['median']:.1f}")
            report.append(f"  标准差: {diff['std']:.2f}")
            report.append(f"  AIME范围(6-9): {diff['in_aime_range']} ({diff['aime_range_rate']*100:.1f}%)")
        
        # 主题覆盖
        if 'topic_coverage' in metrics:
            topic = metrics['topic_coverage']
            report.append("\n🎯 主题覆盖")
            report.append(f"  独特主题: {topic['unique_topics']}")
            report.append(f"  主题均衡度: {topic['balance_score']:.3f} (越高越均衡)")
            report.append("  主题分布:")
            for t, count in topic['topic_distribution'].items():
                report.append(f"    - {t}: {count}")
        
        # 答案分布
        if 'answer_distribution' in metrics and 'error' not in metrics['answer_distribution']:
            ans = metrics['answer_distribution']
            report.append("\n🎲 答案分布")
            report.append(f"  有效答案率: {ans['validity_rate']*100:.1f}%")
            report.append(f"  平均答案: {ans['mean']:.1f}")
            report.append(f"  中位数: {ans['median']:.1f}")
        
        # 解答质量
        if 'solution_quality' in metrics and 'error' not in metrics['solution_quality']:
            sol = metrics['solution_quality']
            report.append("\n💡 解答质量")
            report.append(f"  平均步骤数: {sol['avg_steps']:.1f}")
            report.append(f"  平均长度: {sol['avg_length']:.0f} 字符")
            report.append(f"  完整性: {sol['completeness_rate']*100:.1f}%")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    def save_metrics(self, output_file: str = "evaluation/quality_metrics.json"):
        """保存指标到JSON文件"""
        metrics = self.calculate_all_metrics()
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 质量指标已保存: {output_path}")
        
        return metrics


def main():
    """主函数"""
    print("\n🔍 AIME题目质量评估")
    
    calculator = QualityMetrics()
    
    if not calculator.problems:
        print("❌ 没有找到题目数据")
        return
    
    # 计算并显示报告
    report = calculator.generate_summary_report()
    print(report)
    
    # 保存指标
    calculator.save_metrics()
    
    print("\n✅ 评估完成！")


if __name__ == "__main__":
    main()

