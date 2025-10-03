#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quality Improver - Stage 4
===========================

Uses CAMEL SelfImprovingCoTPipeline to iteratively improve problem quality.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.datagen import SelfImprovingCoTPipeline

import config

logger = logging.getLogger(__name__)


class QualityImprover:
    """
    Improve problem and solution quality using CAMEL SelfImprovingCoTPipeline.
    
    This is Stage 4 of the pipeline: Iterative quality improvement.
    """
    
    def __init__(self, config_obj: config.Stage4Config = None):
        """
        Initialize the quality improver.
        
        Args:
            config_obj: Configuration for Stage 4
        """
        self.config = config_obj or config.Stage4Config()
        
        # Initialize CAMEL model
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict={
                "temperature": 0.5,
                "max_tokens": config.MAX_TOKENS,
            }
        )
        
        # Initialize reason agent
        self.reason_agent = ChatAgent(
            system_message=self._get_reason_system_message(),
            model=self.model,
        )
        
        # Initialize evaluate agent
        self.evaluate_agent = ChatAgent(
            system_message=self._get_evaluate_system_message(),
            model=self.model,
        )
        
        logger.info(f"✅ QualityImprover initialized (max_iterations: {self.config.max_iterations})")
    
    def _get_reason_system_message(self) -> str:
        """Get system message for reason agent"""
        return """You are an expert mathematician who improves AIME problems and solutions.

Your task is to:
1. Review the problem statement for clarity and correctness
2. Review the solution for completeness and accuracy
3. Suggest improvements to make them better

Focus on:
- Mathematical correctness
- Clarity of explanation
- Completeness of steps
- Elegance of solution

Provide specific, actionable improvements."""
    
    def _get_evaluate_system_message(self) -> str:
        """Get system message for evaluate agent"""
        return """You are a critical mathematics teacher who evaluates AIME problems and solutions.

Evaluate on these criteria (score 0.0-1.0):
1. Correctness: Is the mathematics correct?
2. Clarity: Is it easy to understand?
3. Completeness: Are all steps included?
4. Elegance: Is the solution elegant?

Be strict but fair. Provide detailed feedback."""
    
    def improve_problem(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Improve a single problem using iterative refinement.
        
        Args:
            problem: Problem dictionary with solution
        
        Returns:
            Improved problem
        """
        problem_id = problem.get('id', 'unknown')
        logger.info(f"Improving problem {problem_id}...")
        
        # Try to use SelfImprovingCoTPipeline
        try:
            improved = self._improve_with_pipeline(problem)
            return improved
        except Exception as e:
            logger.warning(f"Pipeline improvement failed: {e}, using direct improvement")
            return self._improve_direct(problem)
    
    def _improve_with_pipeline(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Improve using SelfImprovingCoTPipeline.

        Args:
            problem: Problem dictionary

        Returns:
            Improved problem
        """
        # Prepare problem in the format expected by SelfImprovingCoTPipeline
        # It expects: {"problem": "text", "solution": "text" (optional)}
        star_problem = {
            "problem": problem['problem'],
        }

        # Add solution if it exists
        if 'solution' in problem and isinstance(problem['solution'], dict) and 'steps' in problem['solution']:
            # Extract the solution text from steps
            solution_text = ""
            for step in problem['solution']['steps']:
                if 'description' in step:
                    solution_text += step['description'] + "\n\n"
            star_problem["solution"] = solution_text.strip()

        # Create pipeline
        pipeline = SelfImprovingCoTPipeline(
            reason_agent=self.reason_agent,
            evaluate_agent=self.evaluate_agent,
            problems=[star_problem],  # Pass dictionary, not string
            max_iterations=self.config.max_iterations,
        )

        logger.info(f"  Running SelfImprovingCoTPipeline ({self.config.max_iterations} iterations)...")

        # Generate improved version
        improved_data = pipeline.generate()

        # Extract improved problem
        if improved_data and len(improved_data) > 0:
            improved_item = improved_data[0]

            # Update problem with improvements
            if 'trace' in improved_item:
                # Add improved trace to solution
                if 'solution' not in problem:
                    problem['solution'] = {}
                problem['solution']['improved_trace'] = improved_item['trace']
                problem['solution']['improvement_iterations'] = improved_item.get('iteration', 0)
                problem['solution']['final_scores'] = improved_item.get('scores', {})

            problem['improvement_history'] = improved_item.get('history', [])
            problem['quality_score'] = improved_item.get('score', 0.0)
            problem['improved'] = True

        return problem
    
    def _improve_direct(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Improve using direct iteration.
        
        Args:
            problem: Problem dictionary
        
        Returns:
            Improved problem
        """
        current_problem = problem.copy()
        improvement_history = []
        
        for iteration in range(self.config.max_iterations):
            logger.info(f"  Iteration {iteration + 1}/{self.config.max_iterations}")
            
            # Evaluate current version
            evaluation = self._evaluate_problem(current_problem)
            improvement_history.append({
                'iteration': iteration + 1,
                'evaluation': evaluation
            })
            
            logger.info(f"    Scores: {evaluation}")
            
            # Check if quality threshold met
            if self._meets_threshold(evaluation):
                logger.info(f"    ✅ Quality threshold met!")
                break
            
            # Generate improvements
            improvements = self._generate_improvements(current_problem, evaluation)
            
            # Apply improvements
            current_problem = self._apply_improvements(current_problem, improvements)
        
        # Add improvement metadata
        current_problem['improvement_history'] = improvement_history
        current_problem['final_evaluation'] = evaluation
        current_problem['improved'] = True
        
        return current_problem
    
    def _evaluate_problem(self, problem: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate problem quality"""
        prompt = config.EVALUATION_PROMPT.format(
            problem=problem['problem'],
            solution=problem.get('solution', 'No solution'),
            answer=problem.get('answer', 'Unknown')
        )
        
        try:
            response = self.evaluate_agent.step(prompt)
            evaluation = self._parse_evaluation(response.msg.content)
            return evaluation
        
        except Exception as e:
            logger.warning(f"Evaluation failed: {e}")
            return {
                'correctness': 0.5,
                'clarity': 0.5,
                'completeness': 0.5,
                'elegance': 0.5
            }
    
    def _parse_evaluation(self, response_text: str) -> Dict[str, float]:
        """Parse evaluation response"""
        import re
        
        try:
            # Remove markdown
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*$', '', response_text)
            
            evaluation = json.loads(response_text.strip())
            return {
                'correctness': evaluation.get('correctness', 0.5),
                'clarity': evaluation.get('clarity', 0.5),
                'completeness': evaluation.get('completeness', 0.5),
                'elegance': evaluation.get('elegance', 0.5)
            }
        
        except:
            return {
                'correctness': 0.5,
                'clarity': 0.5,
                'completeness': 0.5,
                'elegance': 0.5
            }
    
    def _meets_threshold(self, evaluation: Dict[str, float]) -> bool:
        """Check if evaluation meets quality threshold"""
        thresholds = self.config.score_threshold
        
        return (
            evaluation.get('correctness', 0) >= thresholds.get('correctness', 0.9) and
            evaluation.get('clarity', 0) >= thresholds.get('clarity', 0.8) and
            evaluation.get('completeness', 0) >= thresholds.get('completeness', 0.8)
        )
    
    def _generate_improvements(
        self, 
        problem: Dict[str, Any], 
        evaluation: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate improvement suggestions"""
        prompt = f"""Review this AIME problem and suggest improvements:

Problem: {problem['problem']}
Solution: {problem.get('solution', 'No solution')}

Current scores:
- Correctness: {evaluation.get('correctness', 0):.2f}
- Clarity: {evaluation.get('clarity', 0):.2f}
- Completeness: {evaluation.get('completeness', 0):.2f}

Suggest specific improvements to increase these scores.
"""
        
        try:
            response = self.reason_agent.step(prompt)
            return {'suggestions': response.msg.content}
        except:
            return {'suggestions': 'No improvements generated'}
    
    def _apply_improvements(
        self, 
        problem: Dict[str, Any], 
        improvements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply improvements to problem"""
        # For now, just add improvement suggestions
        # In practice, you'd use another agent to rewrite
        problem['improvement_suggestions'] = improvements.get('suggestions', '')
        return problem
    
    def improve_problems(self, problems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Improve all problems"""
        logger.info(f"Improving {len(problems)} problems...")
        
        improved_problems = []
        
        for i, problem in enumerate(problems):
            logger.info(f"\n[{i+1}/{len(problems)}] Processing problem {problem.get('id', i+1)}...")
            
            try:
                improved = self.improve_problem(problem)
                improved_problems.append(improved)
                logger.info(f"  ✅ Improvement complete")
                
            except Exception as e:
                logger.error(f"  ❌ Failed: {e}")
                problem['improved'] = False
                improved_problems.append(problem)
        
        logger.info(f"\n✅ Improved {len(improved_problems)} problems")
        return improved_problems
    
    def save_problems(self, problems: List[Dict[str, Any]]) -> Path:
        """Save improved problems"""
        output_path = self.config.output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(problems, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(problems)} problems to: {output_path}")
        return output_path
    
    def run(self, input_path: Path = None) -> Path:
        """Run the complete Stage 4 pipeline"""
        logger.info("=" * 70)
        logger.info("Stage 4: Quality Improvement (SelfImprovingCoTPipeline)")
        logger.info("=" * 70)
        
        # Load input problems
        input_path = input_path or self.config.input_path
        with open(input_path, 'r', encoding='utf-8') as f:
            input_problems = json.load(f)
        
        logger.info(f"Loaded {len(input_problems)} problems from Stage 3")
        
        # Improve problems
        improved_problems = self.improve_problems(input_problems)
        
        # Save problems
        output_path = self.save_problems(improved_problems)
        
        logger.info("=" * 70)
        logger.info(f"✅ Stage 4 Complete! Output: {output_path}")
        logger.info("=" * 70)
        
        return output_path


if __name__ == "__main__":
    # Test the quality improver
    improver = QualityImprover()
    output_path = improver.run()
    
    print(f"\n✅ Improved problems saved to: {output_path}")

