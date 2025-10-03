"""
AIME Problem Verification UI
人工验证工具 - 带Web界面的题目验证系统
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import gradio as gr

class ProblemVerifier:
    """题目验证器"""
    
    def __init__(self, input_dir: str = "output/stage4_improved", 
                 output_dir: str = "verification/verified_problems"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载题目
        self.problems = self.load_problems()
        self.current_index = 0
        
        # 加载已有的验证结果
        self.verifications = self.load_verifications()
    
    def load_problems(self) -> List[Dict[str, Any]]:
        """加载待验证的题目"""
        problem_file = self.input_dir / "improved_problems.json"
        
        if not problem_file.exists():
            return []
        
        with open(problem_file, 'r', encoding='utf-8') as f:
            problems = json.load(f)
        
        return problems
    
    def load_verifications(self) -> Dict[str, Any]:
        """加载已有的验证结果"""
        verification_file = self.output_dir / "verifications.json"
        
        if not verification_file.exists():
            return {}
        
        with open(verification_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_verification(self, problem_id: str, verification: Dict[str, Any]):
        """保存验证结果"""
        self.verifications[problem_id] = verification
        
        verification_file = self.output_dir / "verifications.json"
        with open(verification_file, 'w', encoding='utf-8') as f:
            json.dump(self.verifications, f, indent=2, ensure_ascii=False)
    
    def get_current_problem(self) -> Dict[str, Any]:
        """获取当前题目"""
        if not self.problems or self.current_index >= len(self.problems):
            return None
        
        return self.problems[self.current_index]
    
    def get_verification_status(self, problem_id: str) -> str:
        """获取验证状态"""
        if problem_id in self.verifications:
            return self.verifications[problem_id].get('status', 'unknown')
        return 'not_verified'
    
    def format_problem_display(self, problem: Dict[str, Any]) -> str:
        """格式化题目显示"""
        if not problem:
            return "没有更多题目了！"
        
        # 提取解答步骤
        solution_text = ""
        if 'solution' in problem and 'steps' in problem['solution']:
            for step in problem['solution']['steps']:
                if 'description' in step:
                    solution_text += f"\n{step['description']}\n"
        
        display = f"""
# 题目 {problem.get('id', 'unknown')}

## 📝 问题描述
{problem.get('problem', 'N/A')}

## 🎯 答案
{problem.get('answer', 'N/A')}

## 📊 元数据
- **主题**: {problem.get('topic', 'N/A')}
- **难度**: {problem.get('difficulty', 'N/A')}/15
- **标签**: {', '.join(problem.get('tags', []))}

## 💡 解答过程
{solution_text if solution_text else '无解答'}

## 🔄 改进信息
- **是否改进**: {'是' if problem.get('improved', False) else '否'}
"""
        
        return display
    
    def submit_verification(self,
                          correctness: int,
                          clarity: int,
                          difficulty_match: int,
                          completeness: int,
                          status: str,
                          comments: str) -> tuple:
        """提交验证结果"""
        problem = self.get_current_problem()

        if not problem:
            return "没有题目可验证", "", "进度: 0/0"

        # 保存验证结果
        verification = {
            'problem_id': problem.get('id'),
            'timestamp': datetime.now().isoformat(),
            'scores': {
                'correctness': correctness,
                'clarity': clarity,
                'difficulty_match': difficulty_match,
                'completeness': completeness
            },
            'status': status,
            'comments': comments,
            'problem': problem
        }

        self.save_verification(problem.get('id'), verification)

        # 移动到下一题
        self.current_index += 1

        # 获取下一题
        next_problem = self.get_current_problem()
        next_display = self.format_problem_display(next_problem)

        verified_count = len(self.verifications)
        total_count = len(self.problems)

        message = f"✅ 验证已保存！进度: {verified_count}/{total_count}"
        progress = f"**进度**: {verified_count}/{total_count} ({verified_count/total_count*100:.1f}%)"

        return message, next_display, progress
    
    def skip_problem(self) -> tuple:
        """跳过当前题目"""
        self.current_index += 1
        next_problem = self.get_current_problem()
        next_display = self.format_problem_display(next_problem)

        verified_count = len(self.verifications)
        total_count = len(self.problems)
        progress = f"**进度**: {verified_count}/{total_count} ({verified_count/total_count*100:.1f}%)"

        return next_display, progress

    def previous_problem(self) -> tuple:
        """返回上一题"""
        if self.current_index > 0:
            self.current_index -= 1

        problem = self.get_current_problem()
        display = self.format_problem_display(problem)

        verified_count = len(self.verifications)
        total_count = len(self.problems)
        progress = f"**进度**: {verified_count}/{total_count} ({verified_count/total_count*100:.1f}%)"

        return display, progress
    
    def export_results(self) -> str:
        """导出验证结果"""
        # 统计信息
        total = len(self.problems)
        verified = len(self.verifications)
        
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
        
        if verified > 0:
            for v in self.verifications.values():
                for key in avg_scores:
                    avg_scores[key] += v['scores'][key]
            
            for key in avg_scores:
                avg_scores[key] /= verified
        
        # 生成报告
        report = f"""
# AIME题目验证报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 验证统计

- **总题目数**: {total}
- **已验证**: {verified} ({verified/total*100:.1f}%)
- **未验证**: {total - verified}

### 验证结果分布

- ✅ **通过**: {approved} ({approved/verified*100:.1f}% of verified)
- ❌ **拒绝**: {rejected} ({rejected/verified*100:.1f}% of verified)
- 🔄 **需修改**: {needs_revision} ({needs_revision/verified*100:.1f}% of verified)

## 📈 平均质量分数

- **正确性**: {avg_scores['correctness']:.2f}/5
- **清晰度**: {avg_scores['clarity']:.2f}/5
- **难度匹配**: {avg_scores['difficulty_match']:.2f}/5
- **完整性**: {avg_scores['completeness']:.2f}/5

## 💾 数据文件

验证结果已保存至: `{self.output_dir}/verifications.json`
"""
        
        # 保存报告
        report_file = self.output_dir / "verification_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return report


def create_ui():
    """创建Gradio UI"""
    verifier = ProblemVerifier()
    
    with gr.Blocks(title="AIME题目验证系统", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🎓 AIME题目人工验证系统")
        gr.Markdown("请仔细阅读题目、答案和解答，然后进行评分和标注。")
        
        with gr.Row():
            with gr.Column(scale=3):
                # 题目显示区域
                problem_display = gr.Markdown(
                    value=verifier.format_problem_display(verifier.get_current_problem()),
                    label="题目内容"
                )
            
            with gr.Column(scale=1):
                # 评分区域
                gr.Markdown("## 📊 质量评分")
                
                correctness = gr.Slider(1, 5, value=3, step=1, label="正确性 (1-5)")
                clarity = gr.Slider(1, 5, value=3, step=1, label="清晰度 (1-5)")
                difficulty_match = gr.Slider(1, 5, value=3, step=1, label="难度匹配 (1-5)")
                completeness = gr.Slider(1, 5, value=3, step=1, label="完整性 (1-5)")
                
                gr.Markdown("## 🏷️ 验证状态")
                status = gr.Radio(
                    choices=["approved", "rejected", "needs_revision"],
                    value="approved",
                    label="状态",
                    info="approved=通过, rejected=拒绝, needs_revision=需修改"
                )
                
                comments = gr.Textbox(
                    label="评论/建议",
                    placeholder="请输入您的评论或改进建议...",
                    lines=5
                )
                
                # 按钮区域
                with gr.Row():
                    submit_btn = gr.Button("✅ 提交验证", variant="primary")
                    skip_btn = gr.Button("⏭️ 跳过")
                
                with gr.Row():
                    prev_btn = gr.Button("⬅️ 上一题")
                    export_btn = gr.Button("📊 导出报告")
                
                # 进度显示
                progress_text = gr.Markdown(
                    f"**进度**: {len(verifier.verifications)}/{len(verifier.problems)}"
                )
                
                message = gr.Textbox(label="消息", interactive=False)
        
        # 导出结果显示
        export_output = gr.Markdown(visible=False)
        
        # 事件处理
        submit_btn.click(
            fn=verifier.submit_verification,
            inputs=[correctness, clarity, difficulty_match, completeness, status, comments],
            outputs=[message, problem_display, progress_text]
        )

        skip_btn.click(
            fn=verifier.skip_problem,
            outputs=[problem_display, progress_text]
        )

        prev_btn.click(
            fn=verifier.previous_problem,
            outputs=[problem_display, progress_text]
        )
        
        export_btn.click(
            fn=verifier.export_results,
            outputs=[export_output]
        ).then(
            lambda: gr.update(visible=True),
            outputs=[export_output]
        )
    
    return demo


if __name__ == "__main__":
    demo = create_ui()
    demo.launch(share=False, server_name="127.0.0.1", server_port=7860)

