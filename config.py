#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration for AIME DataGen Experiment
==========================================

All configuration parameters for the AIME-style math problem generation pipeline.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ============================================================================
# API Configuration
# ============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Model Configuration
MODEL_TYPE = "gpt-4o"  # or "gpt-4o-mini" for faster/cheaper
MODEL_PLATFORM = "openai"
TEMPERATURE = 0.7  # Higher for more creative problems
MAX_TOKENS = 4000

# ============================================================================
# Directory Configuration
# ============================================================================

# Project root
PROJECT_ROOT = Path(__file__).parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
SEED_PROBLEMS_PATH = DATA_DIR / "seed_problems.jsonl"
AIME_EXAMPLES_PATH = DATA_DIR / "aime_examples.json"

# Output directories
OUTPUT_DIR = PROJECT_ROOT / "output"
STAGE1_OUTPUT = OUTPUT_DIR / "stage1_base_problems"
STAGE2_OUTPUT = OUTPUT_DIR / "stage2_diversified"
STAGE3_OUTPUT = OUTPUT_DIR / "stage3_with_solutions"
STAGE4_OUTPUT = OUTPUT_DIR / "stage4_improved"
FINAL_OUTPUT = OUTPUT_DIR / "final_dataset"

# Verification directories
VERIFICATION_DIR = PROJECT_ROOT / "verification"
VERIFIED_PROBLEMS_DIR = VERIFICATION_DIR / "verified_problems"

# Create directories if they don't exist
for dir_path in [
    DATA_DIR,
    OUTPUT_DIR,
    STAGE1_OUTPUT,
    STAGE2_OUTPUT,
    STAGE3_OUTPUT,
    STAGE4_OUTPUT,
    FINAL_OUTPUT,
    VERIFICATION_DIR,
    VERIFIED_PROBLEMS_DIR,
]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Pipeline Configuration
# ============================================================================

@dataclass
class Stage1Config:
    """Stage 1: Base Problem Generation (ChatAgent)"""
    num_problems: int = 10
    topics: list = None
    difficulty_range: tuple = (6, 9)  # AIME difficulty: 1-15
    output_path: Path = STAGE1_OUTPUT / "base_problems.json"
    
    def __post_init__(self):
        if self.topics is None:
            self.topics = [
                "Number Theory",
                "Algebra",
                "Geometry",
                "Combinatorics",
                "Probability",
            ]


@dataclass
class Stage2Config:
    """Stage 2: Problem Diversification (Self-Instruct)"""
    input_path: Path = STAGE1_OUTPUT / "base_problems.json"
    num_machine_instructions: int = 20  # Generate 20 more problems
    human_to_machine_ratio: tuple = (1, 2)  # 1 human : 2 machine
    output_path: Path = STAGE2_OUTPUT / "diversified_problems.json"
    seed_path: Path = STAGE2_OUTPUT / "seed_for_self_instruct.jsonl"
    
    # Filter configuration
    filter_config: dict = None
    
    def __post_init__(self):
        if self.filter_config is None:
            self.filter_config = {
                "length": {},
                "keyword": {},
                "punctuation": {},
                "non_english": {},
                "rouge_similarity": {
                    "threshold": 0.7,
                    "metric": "rouge-l"
                }
            }


@dataclass
class Stage3Config:
    """Stage 3: Solution Generation (CoTDataGenerator)"""
    input_path: Path = STAGE2_OUTPUT / "diversified_problems.json"
    output_path: Path = STAGE3_OUTPUT / "problems_with_solutions.json"
    search_limit: int = 100  # MCTS search limit
    use_dual_agent: bool = True  # Use generator + verifier
    export_solutions_path: Path = STAGE3_OUTPUT / "solution_trees.json"


@dataclass
class Stage4Config:
    """Stage 4: Quality Improvement (SelfImprovingCoTPipeline)"""
    input_path: Path = STAGE3_OUTPUT / "problems_with_solutions.json"
    output_path: Path = STAGE4_OUTPUT / "improved_problems.json"
    max_iterations: int = 3  # Number of improvement iterations
    score_threshold: dict = None
    
    def __post_init__(self):
        if self.score_threshold is None:
            self.score_threshold = {
                "correctness": 0.9,  # High bar for math
                "clarity": 0.8,
                "completeness": 0.8,
            }


# ============================================================================
# Experiment Modes
# ============================================================================

class ExperimentMode:
    """Different experiment modes with preset configurations"""
    
    TEST = {
        "stage1": {"num_problems": 2},
        "stage2": {"num_machine_instructions": 3},
        "stage3": {"search_limit": 50},
        "stage4": {"max_iterations": 2},
    }
    
    QUICK = {
        "stage1": {"num_problems": 5},
        "stage2": {"num_machine_instructions": 10},
        "stage3": {"search_limit": 100},
        "stage4": {"max_iterations": 3},
    }
    
    FULL = {
        "stage1": {"num_problems": 10},
        "stage2": {"num_machine_instructions": 20},
        "stage3": {"search_limit": 150},
        "stage4": {"max_iterations": 3},
    }


# ============================================================================
# Prompt Templates
# ============================================================================

PROBLEM_GENERATION_PROMPT = """You are an expert at creating AIME (American Invitational Mathematics Examination) style problems.

AIME problems have these characteristics:
- Difficulty level: 6-9 out of 15 (challenging but solvable)
- Answer: Always an integer from 0 to 999
- Topics: Number theory, algebra, geometry, combinatorics, probability
- Style: Clear, concise, elegant
- Requires: Creative thinking and multiple steps

Generate a {topic} problem suitable for AIME.

Requirements:
1. Problem statement should be clear and unambiguous
2. Answer must be an integer from 0 to 999
3. Problem should require 3-5 steps to solve
4. Difficulty level: {difficulty}/15

Format your response as JSON:
{{
    "problem": "Problem statement here",
    "answer": 123,
    "topic": "{topic}",
    "difficulty": {difficulty},
    "tags": ["tag1", "tag2"]
}}
"""

SOLUTION_GENERATION_PROMPT = """Generate a detailed step-by-step solution for this AIME problem.

Problem: {problem}

Requirements:
1. Show all intermediate steps
2. Explain the reasoning for each step
3. Use proper mathematical notation
4. Final answer should be clearly marked

Format your response as JSON:
{{
    "steps": [
        {{"step": 1, "description": "...", "result": "..."}},
        {{"step": 2, "description": "...", "result": "..."}}
    ],
    "final_answer": 123,
    "key_insights": ["insight1", "insight2"]
}}
"""

EVALUATION_PROMPT = """You are a highly critical mathematics teacher evaluating an AIME problem and its solution.

Problem: {problem}
Solution: {solution}
Answer: {answer}

Evaluate on these criteria (score 0.0-1.0):
1. Correctness: Is the solution mathematically correct?
2. Clarity: Is the solution easy to follow?
3. Completeness: Are all steps included?
4. Elegance: Is the solution elegant and efficient?

Format your response as JSON:
{{
    "correctness": 0.9,
    "clarity": 0.8,
    "completeness": 0.9,
    "elegance": 0.7,
    "feedback": "Detailed feedback here",
    "suggestions": ["suggestion1", "suggestion2"]
}}
"""

# ============================================================================
# Logging Configuration
# ============================================================================

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / 'pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ============================================================================
# Validation
# ============================================================================

def validate_config():
    """Validate configuration"""
    if OPENAI_API_KEY == "your-api-key-here":
        logger.warning("⚠️  OPENAI_API_KEY not set! Please set it in config.py or as environment variable.")
        return False
    
    logger.info("✅ Configuration validated successfully")
    return True


if __name__ == "__main__":
    print("=" * 70)
    print("AIME DataGen Experiment Configuration")
    print("=" * 70)
    print()
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Model: {MODEL_TYPE}")
    print(f"API Key Set: {'Yes' if OPENAI_API_KEY != 'your-api-key-here' else 'No'}")
    print()
    print("Directories:")
    print(f"  Data: {DATA_DIR}")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"  Verification: {VERIFICATION_DIR}")
    print()
    print("=" * 70)
    
    validate_config()

