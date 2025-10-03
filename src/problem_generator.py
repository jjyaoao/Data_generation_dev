#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Problem Generator - Stage 1
============================

Uses CAMEL ChatAgent to generate base AIME-style math problems.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.messages import BaseMessage

import config

logger = logging.getLogger(__name__)


class ProblemGenerator:
    """
    Generate AIME-style math problems using CAMEL ChatAgent.
    
    This is Stage 1 of the pipeline: Base problem generation.
    """
    
    def __init__(self, config_obj: config.Stage1Config = None):
        """
        Initialize the problem generator.
        
        Args:
            config_obj: Configuration for Stage 1
        """
        self.config = config_obj or config.Stage1Config()
        
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
        
        logger.info(f"✅ ProblemGenerator initialized with {self.config.num_problems} problems to generate")
    
    def _get_system_message(self) -> str:
        """Get system message for the agent"""
        return """You are an expert mathematician and problem creator specializing in AIME (American Invitational Mathematics Examination) style problems.

Your expertise includes:
- Number Theory (divisibility, modular arithmetic, prime numbers)
- Algebra (sequences, polynomials, functional equations)
- Geometry (triangles, circles, coordinate geometry)
- Combinatorics (counting, arrangements, graph theory)
- Probability (expected value, conditional probability)

AIME problems are characterized by:
1. Difficulty: Challenging but solvable (difficulty 6-9 out of 15)
2. Answer: Always an integer from 0 to 999
3. Style: Clear, elegant, requiring creative thinking
4. Steps: Typically 3-5 steps to solve

You generate high-quality, original problems that match AIME standards."""
    
    def generate_problem(self, topic: str, difficulty: int) -> Dict[str, Any]:
        """
        Generate a single AIME-style problem.
        
        Args:
            topic: Math topic (e.g., "Number Theory")
            difficulty: Difficulty level (1-15, typically 6-9 for AIME)
        
        Returns:
            Dictionary containing problem data
        """
        prompt = config.PROBLEM_GENERATION_PROMPT.format(
            topic=topic,
            difficulty=difficulty
        )
        
        logger.info(f"Generating {topic} problem (difficulty {difficulty})...")
        
        try:
            # Generate problem
            response = self.agent.step(prompt)
            
            # Parse response
            problem_data = self._parse_response(response.msg.content)
            
            # Validate
            if self._validate_problem(problem_data):
                logger.info(f"✅ Generated problem: {problem_data['problem'][:50]}...")
                return problem_data
            else:
                logger.warning("⚠️  Generated problem failed validation, retrying...")
                return self.generate_problem(topic, difficulty)
        
        except Exception as e:
            logger.error(f"❌ Error generating problem: {e}")
            raise
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse agent response to extract problem data"""
        try:
            # Try to extract JSON from response
            import re

            # Remove markdown code blocks if present
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*$', '', response_text)
            response_text = response_text.strip()

            # Try to parse JSON directly first
            try:
                problem_data = json.loads(response_text)
                return problem_data
            except json.JSONDecodeError:
                # If direct parsing fails, try to escape LaTeX backslashes
                # Replace single backslashes with double backslashes for JSON
                response_text_escaped = response_text.replace('\\', '\\\\')
                problem_data = json.loads(response_text_escaped)
                return problem_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response text: {response_text}")
            raise
    
    def _validate_problem(self, problem_data: Dict[str, Any]) -> bool:
        """Validate generated problem"""
        required_fields = ['problem', 'answer', 'topic', 'difficulty']
        
        # Check required fields
        for field in required_fields:
            if field not in problem_data:
                logger.warning(f"Missing field: {field}")
                return False
        
        # Validate answer range
        answer = problem_data['answer']
        if not isinstance(answer, int) or answer < 0 or answer > 999:
            logger.warning(f"Invalid answer: {answer} (must be integer 0-999)")
            return False
        
        # Validate problem text
        if len(problem_data['problem']) < 20:
            logger.warning("Problem text too short")
            return False
        
        return True
    
    def generate_problems(self) -> List[Dict[str, Any]]:
        """
        Generate multiple AIME-style problems.
        
        Returns:
            List of problem dictionaries
        """
        problems = []
        
        logger.info(f"Starting generation of {self.config.num_problems} problems...")
        logger.info(f"Topics: {self.config.topics}")
        logger.info(f"Difficulty range: {self.config.difficulty_range}")
        
        import random
        random.seed(42)
        
        for i in range(self.config.num_problems):
            # Select random topic and difficulty
            topic = random.choice(self.config.topics)
            difficulty = random.randint(*self.config.difficulty_range)
            
            logger.info(f"\n[{i+1}/{self.config.num_problems}] Generating problem...")
            
            try:
                problem = self.generate_problem(topic, difficulty)
                problem['id'] = f"gen_{i+1}"
                problem['stage'] = 'stage1_base'
                problems.append(problem)
                
            except Exception as e:
                logger.error(f"Failed to generate problem {i+1}: {e}")
                continue
        
        logger.info(f"\n✅ Successfully generated {len(problems)} problems")
        return problems
    
    def save_problems(self, problems: List[Dict[str, Any]]) -> Path:
        """
        Save generated problems to JSON file.
        
        Args:
            problems: List of problem dictionaries
        
        Returns:
            Path to saved file
        """
        output_path = self.config.output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(problems, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(problems)} problems to: {output_path}")
        return output_path
    
    def run(self) -> Path:
        """
        Run the complete Stage 1 pipeline.
        
        Returns:
            Path to output file
        """
        logger.info("=" * 70)
        logger.info("Stage 1: Base Problem Generation (ChatAgent)")
        logger.info("=" * 70)
        
        # Generate problems
        problems = self.generate_problems()
        
        # Save problems
        output_path = self.save_problems(problems)
        
        logger.info("=" * 70)
        logger.info(f"✅ Stage 1 Complete! Output: {output_path}")
        logger.info("=" * 70)
        
        return output_path


if __name__ == "__main__":
    # Test the generator
    generator = ProblemGenerator()
    output_path = generator.run()
    
    print(f"\n✅ Generated problems saved to: {output_path}")

