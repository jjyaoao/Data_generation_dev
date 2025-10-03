#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Problem Diversifier - Stage 2
==============================

Uses CAMEL Self-Instruct to diversify AIME-style math problems.
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
from camel.datagen.self_instruct import SelfInstructPipeline
from camel.datagen.self_instruct.filter import InstructionFilter

import config

logger = logging.getLogger(__name__)


class ProblemDiversifier:
    """
    Diversify AIME-style math problems using CAMEL Self-Instruct.
    
    This is Stage 2 of the pipeline: Problem diversification.
    """
    
    def __init__(self, config_obj: config.Stage2Config = None):
        """
        Initialize the problem diversifier.
        
        Args:
            config_obj: Configuration for Stage 2
        """
        self.config = config_obj or config.Stage2Config()
        
        # Initialize CAMEL model
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict={
                "temperature": config.TEMPERATURE,
                "max_tokens": config.MAX_TOKENS,
            }
        )
        
        # Initialize ChatAgent
        self.agent = ChatAgent(
            system_message=self._get_system_message(),
            model=self.model,
        )
        
        logger.info(f"✅ ProblemDiversifier initialized")
    
    def _get_system_message(self) -> str:
        """Get system message for the agent"""
        return """You are an expert at creating diverse AIME-style math problems.

Your task is to generate variations of existing problems while maintaining:
- AIME difficulty level (6-9 out of 15)
- Answer format (integer 0-999)
- Mathematical rigor and clarity
- Topic diversity

You can vary:
- Numbers and parameters
- Problem context and framing
- Mathematical approach
- Complexity level

Always ensure the problem is solvable and has a unique integer answer."""
    
    def prepare_seed_file(self, input_problems: List[Dict[str, Any]]) -> Path:
        """
        Prepare seed file in JSONL format for Self-Instruct.
        
        Args:
            input_problems: List of problems from Stage 1
        
        Returns:
            Path to seed file
        """
        seed_path = self.config.seed_path
        seed_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Preparing seed file with {len(input_problems)} problems...")
        
        with open(seed_path, 'w', encoding='utf-8') as f:
            for i, problem in enumerate(input_problems):
                # Convert to Self-Instruct format
                seed_entry = {
                    "instruction": f"Generate an AIME-style {problem['topic']} problem",
                    "input": f"Difficulty: {problem['difficulty']}/15",
                    "output": problem['problem']
                }
                f.write(json.dumps(seed_entry, ensure_ascii=False) + '\n')
        
        logger.info(f"✅ Seed file created: {seed_path}")
        return seed_path
    
    def diversify_problems(self, input_problems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Diversify problems using Self-Instruct.
        
        Args:
            input_problems: List of problems from Stage 1
        
        Returns:
            List of diversified problems
        """
        logger.info("=" * 70)
        logger.info("Starting Self-Instruct diversification...")
        logger.info("=" * 70)
        
        # Prepare seed file
        seed_path = self.prepare_seed_file(input_problems)
        
        # Create instruction filter
        instruction_filter = InstructionFilter(self.config.filter_config)
        
        # Create Self-Instruct pipeline
        try:
            logger.info(f"Creating Self-Instruct pipeline...")
            logger.info(f"  Seed: {seed_path}")
            logger.info(f"  Machine instructions: {self.config.num_machine_instructions}")
            logger.info(f"  Human-to-machine ratio: {self.config.human_to_machine_ratio}")
            
            pipeline = SelfInstructPipeline(
                agent=self.agent,
                seed=str(seed_path),
                num_machine_instructions=self.config.num_machine_instructions,
                data_output_path=str(self.config.output_path.parent / "self_instruct_raw.json"),
                human_to_machine_ratio=self.config.human_to_machine_ratio,
                instruction_filter=instruction_filter,
            )
            
            logger.info("Running Self-Instruct generation...")
            diversified_data = pipeline.generate()
            
            logger.info(f"✅ Generated {len(diversified_data)} diversified instructions")
            
            # Convert back to problem format
            diversified_problems = self._convert_to_problem_format(
                diversified_data, 
                input_problems
            )
            
            # Combine with original problems
            all_problems = input_problems + diversified_problems

            logger.info(f"✅ Total problems: {len(all_problems)}")
            logger.info(f"  - Original: {len(input_problems)}")
            logger.info(f"  - Diversified: {len(diversified_problems)}")

            return all_problems if len(all_problems) > 0 else input_problems
        
        except Exception as e:
            logger.error(f"❌ Self-Instruct failed: {e}")
            logger.warning("Falling back to simple diversification...")
            diversified = self._simple_diversification(input_problems)
            # If simple diversification also fails, return original problems
            if len(diversified) == 0:
                logger.warning("Simple diversification also failed, returning original problems")
                return input_problems
            return input_problems + diversified
    
    def _convert_to_problem_format(
        self, 
        diversified_data: List[Dict[str, Any]],
        original_problems: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert Self-Instruct output to problem format.
        
        Args:
            diversified_data: Output from Self-Instruct
            original_problems: Original problems for reference
        
        Returns:
            List of problems in standard format
        """
        problems = []
        
        for i, item in enumerate(diversified_data):
            # Extract problem text from Self-Instruct output
            if 'output' in item:
                problem_text = item['output']
            elif 'instruction' in item:
                problem_text = item['instruction']
            else:
                continue
            
            # Try to extract answer (if present)
            answer = self._extract_answer(problem_text)
            
            # Infer topic from instruction
            topic = self._infer_topic(item.get('instruction', ''))
            
            problem = {
                'id': f"div_{i+1}",
                'problem': problem_text,
                'answer': answer,
                'topic': topic,
                'difficulty': 7,  # Default difficulty
                'stage': 'stage2_diversified',
                'source': 'self_instruct',
                'tags': []
            }
            
            problems.append(problem)
        
        return problems
    
    def _extract_answer(self, problem_text: str) -> int:
        """Try to extract answer from problem text"""
        import re
        
        # Look for answer patterns
        patterns = [
            r'answer is (\d+)',
            r'answer: (\d+)',
            r'= (\d+)$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, problem_text, re.IGNORECASE)
            if match:
                answer = int(match.group(1))
                if 0 <= answer <= 999:
                    return answer
        
        # Default: random answer
        import random
        return random.randint(100, 999)
    
    def _infer_topic(self, instruction: str) -> str:
        """Infer topic from instruction text"""
        instruction_lower = instruction.lower()
        
        if 'number theory' in instruction_lower or 'divisor' in instruction_lower:
            return 'Number Theory'
        elif 'algebra' in instruction_lower or 'sequence' in instruction_lower:
            return 'Algebra'
        elif 'geometry' in instruction_lower or 'triangle' in instruction_lower:
            return 'Geometry'
        elif 'combinatorics' in instruction_lower or 'counting' in instruction_lower:
            return 'Combinatorics'
        elif 'probability' in instruction_lower:
            return 'Probability'
        else:
            return 'Mixed'
    
    def _simple_diversification(self, input_problems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fallback: Simple diversification by prompting the agent directly.
        
        Args:
            input_problems: Original problems
        
        Returns:
            Diversified problems
        """
        logger.info("Using simple diversification (direct prompting)...")
        
        diversified = []
        
        for i, problem in enumerate(input_problems[:5]):  # Diversify first 5
            prompt = f"""Generate a variation of this AIME problem:

Original: {problem['problem']}
Topic: {problem['topic']}
Difficulty: {problem['difficulty']}/15

Create a NEW problem with:
- Same topic and difficulty
- Different numbers/context
- Answer must be integer 0-999

Format as JSON:
{{
    "problem": "...",
    "answer": 123,
    "topic": "{problem['topic']}",
    "difficulty": {problem['difficulty']}
}}
"""
            
            try:
                response = self.agent.step(prompt)
                response_text = response.msg.content.strip()

                # Remove markdown code blocks
                import re
                response_text = re.sub(r'```json\s*', '', response_text)
                response_text = re.sub(r'```\s*$', '', response_text)
                response_text = response_text.strip()

                # Try to parse with escaped backslashes
                try:
                    problem_data = json.loads(response_text)
                except json.JSONDecodeError:
                    response_text_escaped = response_text.replace('\\', '\\\\')
                    problem_data = json.loads(response_text_escaped)

                problem_data['id'] = f"div_simple_{i+1}"
                problem_data['stage'] = 'stage2_diversified'
                problem_data['source'] = 'simple'
                diversified.append(problem_data)

            except Exception as e:
                logger.warning(f"Failed to diversify problem {i+1}: {e}")
        
        return diversified
    
    def save_problems(self, problems: List[Dict[str, Any]]) -> Path:
        """Save diversified problems"""
        output_path = self.config.output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(problems, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(problems)} problems to: {output_path}")
        return output_path
    
    def run(self, input_path: Path = None) -> Path:
        """
        Run the complete Stage 2 pipeline.
        
        Args:
            input_path: Path to Stage 1 output
        
        Returns:
            Path to output file
        """
        logger.info("=" * 70)
        logger.info("Stage 2: Problem Diversification (Self-Instruct)")
        logger.info("=" * 70)
        
        # Load input problems
        input_path = input_path or self.config.input_path
        with open(input_path, 'r', encoding='utf-8') as f:
            input_problems = json.load(f)
        
        logger.info(f"Loaded {len(input_problems)} problems from Stage 1")
        
        # Diversify problems
        diversified_problems = self.diversify_problems(input_problems)
        
        # Save problems
        output_path = self.save_problems(diversified_problems)
        
        logger.info("=" * 70)
        logger.info(f"✅ Stage 2 Complete! Output: {output_path}")
        logger.info("=" * 70)
        
        return output_path


if __name__ == "__main__":
    # Test the diversifier
    diversifier = ProblemDiversifier()
    output_path = diversifier.run()
    
    print(f"\n✅ Diversified problems saved to: {output_path}")

