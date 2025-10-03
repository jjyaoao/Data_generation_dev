#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Individual Stages
======================

Test each stage of the pipeline individually.
"""

import argparse
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

import config


def test_stage1():
    """Test Stage 1: Problem Generation"""
    print("\n" + "=" * 70)
    print("Testing Stage 1: Problem Generation (ChatAgent)")
    print("=" * 70)
    
    from src.problem_generator import ProblemGenerator
    
    # Create test config
    test_config = config.Stage1Config()
    test_config.num_problems = 2  # Generate only 2 problems for testing
    
    generator = ProblemGenerator(test_config)
    output_path = generator.run()
    
    print(f"\n✅ Stage 1 Test Complete!")
    print(f"Output: {output_path}")
    
    # Show generated problems
    import json
    with open(output_path, 'r', encoding='utf-8') as f:
        problems = json.load(f)
    
    print(f"\nGenerated {len(problems)} problems:")
    for i, problem in enumerate(problems):
        print(f"\n{i+1}. {problem['topic']} (Difficulty: {problem['difficulty']})")
        print(f"   Problem: {problem['problem'][:100]}...")
        print(f"   Answer: {problem['answer']}")
    
    return output_path


def test_stage2(input_path: Path = None):
    """Test Stage 2: Problem Diversification"""
    print("\n" + "=" * 70)
    print("Testing Stage 2: Problem Diversification (Self-Instruct)")
    print("=" * 70)
    
    from src.diversifier import ProblemDiversifier
    
    # Use Stage 1 output if available
    if input_path is None:
        input_path = config.Stage1Config().output_path
        if not input_path.exists():
            print("❌ Stage 1 output not found. Please run Stage 1 first.")
            return None
    
    # Create test config
    test_config = config.Stage2Config()
    test_config.input_path = input_path
    test_config.num_machine_instructions = 2  # Generate only 2 more problems
    
    diversifier = ProblemDiversifier(test_config)
    output_path = diversifier.run(input_path)
    
    print(f"\n✅ Stage 2 Test Complete!")
    print(f"Output: {output_path}")
    
    # Show diversified problems
    import json
    with open(output_path, 'r', encoding='utf-8') as f:
        problems = json.load(f)
    
    print(f"\nTotal problems: {len(problems)}")
    
    # Count by source
    sources = {}
    for problem in problems:
        source = problem.get('source', problem.get('stage', 'unknown'))
        sources[source] = sources.get(source, 0) + 1
    
    print("By source:")
    for source, count in sources.items():
        print(f"  {source}: {count}")
    
    return output_path


def test_stage3(input_path: Path = None):
    """Test Stage 3: Solution Generation"""
    print("\n" + "=" * 70)
    print("Testing Stage 3: Solution Generation (CoTDataGenerator)")
    print("=" * 70)
    
    from src.solution_generator import SolutionGenerator
    
    # Use Stage 2 output if available
    if input_path is None:
        input_path = config.Stage2Config().output_path
        if not input_path.exists():
            print("❌ Stage 2 output not found. Please run Stage 2 first.")
            return None
    
    # Create test config
    test_config = config.Stage3Config()
    test_config.input_path = input_path
    test_config.search_limit = 50  # Lower search limit for testing
    
    generator = SolutionGenerator(test_config)
    output_path = generator.run(input_path)
    
    print(f"\n✅ Stage 3 Test Complete!")
    print(f"Output: {output_path}")
    
    # Show problems with solutions
    import json
    with open(output_path, 'r', encoding='utf-8') as f:
        problems = json.load(f)
    
    print(f"\nTotal problems: {len(problems)}")
    
    # Count problems with solutions
    with_solutions = sum(1 for p in problems if p.get('has_solution', False))
    print(f"Problems with solutions: {with_solutions}/{len(problems)}")
    
    # Show first solution
    if with_solutions > 0:
        for problem in problems:
            if problem.get('has_solution'):
                print(f"\nExample solution for: {problem['problem'][:80]}...")
                solution = problem.get('solution', {})
                print(f"Method: {solution.get('method', 'unknown')}")
                print(f"Steps: {len(solution.get('steps', []))}")
                print(f"Answer: {solution.get('final_answer', 'N/A')}")
                break
    
    return output_path


def test_stage4(input_path: Path = None):
    """Test Stage 4: Quality Improvement"""
    print("\n" + "=" * 70)
    print("Testing Stage 4: Quality Improvement (SelfImprovingCoTPipeline)")
    print("=" * 70)
    
    from src.quality_improver import QualityImprover
    
    # Use Stage 3 output if available
    if input_path is None:
        input_path = config.Stage3Config().output_path
        if not input_path.exists():
            print("❌ Stage 3 output not found. Please run Stage 3 first.")
            return None
    
    # Create test config
    test_config = config.Stage4Config()
    test_config.input_path = input_path
    test_config.max_iterations = 2  # Fewer iterations for testing
    
    improver = QualityImprover(test_config)
    output_path = improver.run(input_path)
    
    print(f"\n✅ Stage 4 Test Complete!")
    print(f"Output: {output_path}")
    
    # Show improved problems
    import json
    with open(output_path, 'r', encoding='utf-8') as f:
        problems = json.load(f)
    
    print(f"\nTotal problems: {len(problems)}")
    
    # Count improved problems
    improved = sum(1 for p in problems if p.get('improved', False))
    print(f"Improved problems: {improved}/{len(problems)}")
    
    # Show improvement example
    if improved > 0:
        for problem in problems:
            if problem.get('improved') and 'final_evaluation' in problem:
                print(f"\nExample improvement for: {problem['problem'][:80]}...")
                eval_scores = problem.get('final_evaluation', {})
                print(f"Final scores:")
                for key, value in eval_scores.items():
                    print(f"  {key}: {value:.2f}")
                break
    
    return output_path


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Test individual stages of AIME DataGen Pipeline"
    )
    
    parser.add_argument(
        '--stage',
        type=int,
        choices=[1, 2, 3, 4],
        help='Test a specific stage (default: test all stages)'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Test all stages in sequence'
    )
    
    args = parser.parse_args()
    
    # Validate config
    if not config.validate_config():
        print("\n❌ Configuration validation failed!")
        print("Please set OPENAI_API_KEY in config.py or as environment variable")
        return
    
    try:
        if args.stage == 1 or args.all:
            stage1_output = test_stage1()
            
            if args.all and stage1_output:
                stage2_output = test_stage2(stage1_output)
                
                if stage2_output:
                    stage3_output = test_stage3(stage2_output)
                    
                    if stage3_output:
                        test_stage4(stage3_output)
        
        elif args.stage == 2:
            test_stage2()
        
        elif args.stage == 3:
            test_stage3()
        
        elif args.stage == 4:
            test_stage4()
        
        else:
            print("Please specify --stage <1-4> or --all")
            parser.print_help()
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

