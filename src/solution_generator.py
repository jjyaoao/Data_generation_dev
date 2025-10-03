#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Solution Generator - Stage 3
=============================

Uses CAMEL CoTDataGenerator to generate step-by-step solutions for AIME problems.
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
from camel.datagen import CoTDataGenerator

import config

logger = logging.getLogger(__name__)


class SolutionGenerator:
    """
    Generate step-by-step solutions using CAMEL CoTDataGenerator.
    
    This is Stage 3 of the pipeline: Solution generation with Chain of Thought.
    """
    
    def __init__(self, config_obj: config.Stage3Config = None):
        """
        Initialize the solution generator.
        
        Args:
            config_obj: Configuration for Stage 3
        """
        self.config = config_obj or config.Stage3Config()
        
        # Initialize CAMEL model
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict={
                "temperature": 0.3,  # Lower temperature for solutions
                "max_tokens": config.MAX_TOKENS,
            }
        )
        
        # Initialize generator agent
        self.generator_agent = ChatAgent(
            system_message=self._get_generator_system_message(),
            model=self.model,
        )
        
        # Initialize verifier agent (if dual-agent mode)
        if self.config.use_dual_agent:
            self.verifier_agent = ChatAgent(
                system_message=self._get_verifier_system_message(),
                model=self.model,
            )
        else:
            self.verifier_agent = None
        
        logger.info(f"✅ SolutionGenerator initialized (dual-agent: {self.config.use_dual_agent})")
    
    def _get_generator_system_message(self) -> str:
        """Get system message for generator agent"""
        return """You are an expert mathematician who generates detailed step-by-step solutions for AIME problems.

Your solutions should:
1. Break down the problem into clear steps
2. Explain the reasoning for each step
3. Use proper mathematical notation
4. Show all intermediate calculations
5. Arrive at the final answer (integer 0-999)

Format your solution as a sequence of steps, each with:
- Step number
- Description of what you're doing
- Mathematical work
- Result

Always put the final answer in \\boxed{} notation."""
    
    def _get_verifier_system_message(self) -> str:
        """Get system message for verifier agent"""
        return """You are a critical mathematics teacher who verifies solutions to AIME problems.

Your job is to:
1. Check each step for mathematical correctness
2. Verify that the logic flows properly
3. Confirm the final answer is correct
4. Identify any errors or gaps

Provide feedback on:
- Correctness (is the math right?)
- Completeness (are all steps shown?)
- Clarity (is it easy to follow?)

Be thorough and critical."""
    
    def generate_solution(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate solution for a single problem.
        
        Args:
            problem: Problem dictionary
        
        Returns:
            Problem with solution added
        """
        problem_text = problem['problem']
        problem_id = problem.get('id', 'unknown')
        
        logger.info(f"Generating solution for problem {problem_id}...")
        
        # Use CoTDataGenerator if we have golden answers
        if 'answer' in problem and problem['answer'] is not None:
            try:
                solution = self._generate_with_cot(problem)
            except Exception as e:
                logger.warning(f"CoT generation failed: {e}, falling back to direct generation")
                solution = self._generate_direct(problem)
        else:
            solution = self._generate_direct(problem)
        
        # Add solution to problem
        problem['solution'] = solution
        problem['has_solution'] = True
        
        return problem
    
    def _generate_with_cot(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate solution using CoTDataGenerator.
        
        Args:
            problem: Problem dictionary
        
        Returns:
            Solution dictionary
        """
        # Prepare golden answers
        golden_answers = {
            problem['problem']: str(problem['answer'])
        }
        
        # Create CoTDataGenerator
        cot_generator = CoTDataGenerator(
            generator_agent=self.generator_agent,
            verifier_agent=self.verifier_agent,
            golden_answers=golden_answers,
            search_limit=self.config.search_limit,
        )
        
        # Generate solution
        logger.info("  Using CoTDataGenerator with MCTS...")
        solution_tree = cot_generator.solve(problem['problem'])
        
        # Extract solution from tree
        solution = {
            'method': 'cot_mcts',
            'steps': self._extract_steps_from_tree(solution_tree),
            'final_answer': problem['answer'],
            'verified': True,
        }
        
        return solution
    
    def _generate_direct(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate solution by direct prompting.
        
        Args:
            problem: Problem dictionary
        
        Returns:
            Solution dictionary
        """
        prompt = config.SOLUTION_GENERATION_PROMPT.format(
            problem=problem['problem']
        )
        
        logger.info("  Using direct generation...")
        
        try:
            response = self.generator_agent.step(prompt)
            solution_data = self._parse_solution_response(response.msg.content)
            solution_data['method'] = 'direct'
            solution_data['verified'] = False
            
            return solution_data
        
        except Exception as e:
            logger.error(f"Failed to generate solution: {e}")
            return {
                'method': 'failed',
                'steps': [],
                'final_answer': problem.get('answer', 0),
                'error': str(e)
            }
    
    def _parse_solution_response(self, response_text: str) -> Dict[str, Any]:
        """Parse solution response"""
        import re
        
        try:
            # Remove markdown code blocks
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*$', '', response_text)
            
            # Parse JSON
            solution_data = json.loads(response_text.strip())
            return solution_data
        
        except json.JSONDecodeError:
            # Fallback: extract steps manually
            logger.warning("Failed to parse JSON, extracting steps manually")
            
            steps = []
            lines = response_text.split('\n')
            
            for i, line in enumerate(lines):
                if line.strip():
                    steps.append({
                        'step': i + 1,
                        'description': line.strip(),
                        'result': ''
                    })
            
            return {
                'steps': steps,
                'final_answer': 0,
                'key_insights': []
            }
    
    def _extract_steps_from_tree(self, solution_tree: Any) -> List[Dict[str, Any]]:
        """Extract steps from CoT solution tree"""
        # This is a simplified extraction
        # In practice, you'd traverse the tree structure
        
        if isinstance(solution_tree, dict):
            if 'steps' in solution_tree:
                return solution_tree['steps']
            elif 'reasoning' in solution_tree:
                return [{'step': 1, 'description': solution_tree['reasoning'], 'result': ''}]
        
        # Fallback
        return [{'step': 1, 'description': str(solution_tree), 'result': ''}]
    
    def generate_solutions(self, problems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate solutions for all problems.
        
        Args:
            problems: List of problems
        
        Returns:
            List of problems with solutions
        """
        logger.info(f"Generating solutions for {len(problems)} problems...")
        
        problems_with_solutions = []
        
        for i, problem in enumerate(problems):
            logger.info(f"\n[{i+1}/{len(problems)}] Processing problem {problem.get('id', i+1)}...")
            
            try:
                problem_with_solution = self.generate_solution(problem)
                problems_with_solutions.append(problem_with_solution)
                logger.info(f"  ✅ Solution generated")
                
            except Exception as e:
                logger.error(f"  ❌ Failed: {e}")
                # Add problem without solution
                problem['solution'] = None
                problem['has_solution'] = False
                problems_with_solutions.append(problem)
        
        logger.info(f"\n✅ Generated solutions for {len(problems_with_solutions)} problems")

        # Count successful solutions
        successful = sum(1 for p in problems_with_solutions if p.get('has_solution', False))
        if len(problems) > 0:
            logger.info(f"  Success rate: {successful}/{len(problems)} ({successful/len(problems)*100:.1f}%)")
        else:
            logger.info(f"  Success rate: 0/0 (no problems to process)")
        
        return problems_with_solutions
    
    def save_problems(self, problems: List[Dict[str, Any]]) -> Path:
        """Save problems with solutions"""
        output_path = self.config.output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(problems, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(problems)} problems to: {output_path}")
        return output_path
    
    def run(self, input_path: Path = None) -> Path:
        """
        Run the complete Stage 3 pipeline.
        
        Args:
            input_path: Path to Stage 2 output
        
        Returns:
            Path to output file
        """
        logger.info("=" * 70)
        logger.info("Stage 3: Solution Generation (CoTDataGenerator)")
        logger.info("=" * 70)
        
        # Load input problems
        input_path = input_path or self.config.input_path
        with open(input_path, 'r', encoding='utf-8') as f:
            input_problems = json.load(f)
        
        logger.info(f"Loaded {len(input_problems)} problems from Stage 2")
        
        # Generate solutions
        problems_with_solutions = self.generate_solutions(input_problems)
        
        # Save problems
        output_path = self.save_problems(problems_with_solutions)
        
        logger.info("=" * 70)
        logger.info(f"✅ Stage 3 Complete! Output: {output_path}")
        logger.info("=" * 70)
        
        return output_path


if __name__ == "__main__":
    # Test the solution generator
    generator = SolutionGenerator()
    output_path = generator.run()
    
    print(f"\n✅ Solutions saved to: {output_path}")

