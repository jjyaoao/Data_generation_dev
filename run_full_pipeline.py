#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIME DataGen Full Pipeline
===========================

Complete pipeline for generating AIME-style math problems using CAMEL DataGen.

Stages:
1. Base Problem Generation (ChatAgent)
2. Problem Diversification (Self-Instruct)
3. Solution Generation (CoTDataGenerator)
4. Quality Improvement (SelfImprovingCoTPipeline)
"""

import argparse
import logging
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

import config

logger = logging.getLogger(__name__)


def print_banner():
    """Print welcome banner"""
    print("=" * 70)
    print("AIME-Style Math Problem Generation with CAMEL DataGen")
    print("=" * 70)
    print()
    print("This pipeline uses 4 CAMEL DataGen modules:")
    print("  1. ChatAgent - Base problem generation")
    print("  2. Self-Instruct - Problem diversification")
    print("  3. CoTDataGenerator - Solution generation")
    print("  4. SelfImprovingCoTPipeline - Quality improvement")
    print()
    print("=" * 70)
    print()


def run_stage1(mode_config: dict):
    """Run Stage 1: Base Problem Generation"""
    print("\n" + "=" * 70)
    print("Stage 1: Base Problem Generation (ChatAgent)")
    print("=" * 70)
    
    from src.problem_generator import ProblemGenerator
    
    # Update config with mode settings
    stage1_config = config.Stage1Config()
    for key, value in mode_config.get('stage1', {}).items():
        setattr(stage1_config, key, value)
    
    generator = ProblemGenerator(stage1_config)
    output_path = generator.run()
    
    print(f"\n✅ Stage 1 Complete! Output: {output_path}")
    return output_path


def run_stage2(input_path: Path, mode_config: dict):
    """Run Stage 2: Problem Diversification"""
    print("\n" + "=" * 70)
    print("Stage 2: Problem Diversification (Self-Instruct)")
    print("=" * 70)

    from src.diversifier import ProblemDiversifier

    # Update config with mode settings
    stage2_config = config.Stage2Config()
    stage2_config.input_path = input_path
    for key, value in mode_config.get('stage2', {}).items():
        setattr(stage2_config, key, value)

    diversifier = ProblemDiversifier(stage2_config)
    output_path = diversifier.run(input_path)

    print(f"\n✅ Stage 2 Complete! Output: {output_path}")
    return output_path


def run_stage3(input_path: Path, mode_config: dict):
    """Run Stage 3: Solution Generation"""
    print("\n" + "=" * 70)
    print("Stage 3: Solution Generation (CoTDataGenerator)")
    print("=" * 70)

    from src.solution_generator import SolutionGenerator

    # Update config with mode settings
    stage3_config = config.Stage3Config()
    stage3_config.input_path = input_path
    for key, value in mode_config.get('stage3', {}).items():
        setattr(stage3_config, key, value)

    generator = SolutionGenerator(stage3_config)
    output_path = generator.run(input_path)

    print(f"\n✅ Stage 3 Complete! Output: {output_path}")
    return output_path


def run_stage4(input_path: Path, mode_config: dict):
    """Run Stage 4: Quality Improvement"""
    print("\n" + "=" * 70)
    print("Stage 4: Quality Improvement (SelfImprovingCoTPipeline)")
    print("=" * 70)

    from src.quality_improver import QualityImprover

    # Update config with mode settings
    stage4_config = config.Stage4Config()
    stage4_config.input_path = input_path
    for key, value in mode_config.get('stage4', {}).items():
        setattr(stage4_config, key, value)

    improver = QualityImprover(stage4_config)
    output_path = improver.run(input_path)

    print(f"\n✅ Stage 4 Complete! Output: {output_path}")
    return output_path


def run_pipeline(mode: str = 'quick'):
    """
    Run the complete pipeline.
    
    Args:
        mode: Experiment mode ('test', 'quick', or 'full')
    """
    print_banner()
    
    # Validate configuration
    if not config.validate_config():
        print("\n❌ Configuration validation failed!")
        print("Please set OPENAI_API_KEY in config.py or as environment variable")
        return
    
    # Get mode configuration
    mode_config = getattr(config.ExperimentMode, mode.upper(), config.ExperimentMode.QUICK)
    
    print(f"Running in {mode.upper()} mode")
    print(f"Configuration: {mode_config}")
    print()
    
    try:
        # Stage 1: Base Problem Generation
        stage1_output = run_stage1(mode_config)
        
        # Stage 2: Problem Diversification
        stage2_output = run_stage2(stage1_output, mode_config)
        
        # Stage 3: Solution Generation
        stage3_output = run_stage3(stage2_output, mode_config)
        
        # Stage 4: Quality Improvement
        stage4_output = run_stage4(stage3_output, mode_config)
        
        # Final summary
        print("\n" + "=" * 70)
        print("🎉 Pipeline Complete!")
        print("=" * 70)
        print()
        print("Output files:")
        print(f"  Stage 1: {stage1_output}")
        print(f"  Stage 2: {stage2_output}")
        print(f"  Stage 3: {stage3_output}")
        print(f"  Stage 4: {stage4_output}")
        print()
        print("Next steps:")
        print("  1. Review generated problems in output/")
        print("  2. Run human verification: python evaluation/human_verification.py")
        print("  3. Check verification/verified_problems/")
        print()
        print("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
        print(f"\n❌ Pipeline failed: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AIME DataGen Pipeline - Generate AIME-style math problems with CAMEL"
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['test', 'quick', 'full'],
        default='quick',
        help='Experiment mode (default: quick)'
    )
    
    parser.add_argument(
        '--stage',
        type=int,
        choices=[1, 2, 3, 4],
        help='Run only a specific stage (default: run all stages)'
    )
    
    args = parser.parse_args()
    
    if args.stage:
        print(f"Running only Stage {args.stage}")
        # TODO: Implement single-stage execution
        print("Single-stage execution not yet implemented")
        print("Please run the full pipeline for now")
    else:
        run_pipeline(args.mode)


if __name__ == "__main__":
    main()

