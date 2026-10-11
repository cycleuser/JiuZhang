"""Rejection Sampling Pipeline for JiuZhang Math Model Training.

Generates high-quality training data by:
  1. Taking a set of math problems.
  2. Generating N candidate solutions for each problem (using a base model or heuristic).
  3. Verifying each solution using SymPy or keyword matching.
  4. Keeping only the verified solutions.
  5. Formatting them into ChatML/Alpaca format for training.

This technique (Rejection Sampling) is used by models like DeepSeek-Math and Qwen-Math
to significantly improve reasoning quality.
"""

import json
import random
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from jiuzhang.symbolic_verify import (
    verify_equation, verify_derivative, verify_integral,
    verify_solution, verify_limit, VerificationResult,
)
from jiuzhang.math_benchmark import MathBenchmark, BenchmarkProblem
from jiuzhang.curriculum_pipeline import CurriculumDataPipeline


@dataclass
class CandidateSolution:
    problem_id: str
    problem_text: str
    solution_text: str
    verification_result: VerificationResult
    is_correct: bool
    generation_time: float = 0.0


@dataclass
class RejectionSamplingResult:
    total_problems: int
    total_candidates: int
    accepted_solutions: int
    rejection_rate: float
    samples: List[CandidateSolution] = field(default_factory=list)


class RejectionSampler:
    """Orchestrates rejection sampling for math training data."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.benchmark = MathBenchmark()
        self.pipeline = CurriculumDataPipeline(seed=seed)

    def generate_candidates_heuristic(self, problem: BenchmarkProblem, n: int = 5) -> List[str]:
        """Generate candidate solutions using heuristic templates.
        
        In a real scenario, this would call an LLM API.
        Here we simulate it by generating variations of the correct answer
        and some plausible wrong answers.
        """
        candidates = []
        
        # 1. The correct solution (always included)
        candidates.append(f"Solution: {problem.answer}")
        
        # 2. Variations with steps
        candidates.append(f"Step 1: Analyze problem.\nStep 2: Calculate.\nResult: {problem.answer}")
        candidates.append(f"Let's solve this.\nThe answer is {problem.answer}.")
        
        # 3. Wrong answers (for rejection)
        wrong_variations = [
            f"Solution: {problem.answer} + 1",
            f"Result: {int(problem.answer) + 1}" if problem.answer.isdigit() else f"Result: {problem.answer}x",
            f"I think it might be {problem.answer} or maybe {problem.answer} + 1.",
            f"Solution: {problem.answer} (unsure)",
        ]
        
        # Add wrong answers up to n
        for wrong in wrong_variations:
            if len(candidates) >= n:
                break
            candidates.append(wrong)
            
        return candidates[:n]

    def verify_candidate(self, problem: BenchmarkProblem, solution: str) -> Tuple[bool, VerificationResult]:
        """Verify a candidate solution against the problem."""
        # Use the benchmark's scoring logic
        score, detail = self.benchmark.score_response(problem, solution)
        
        # Create a VerificationResult-like object for consistency
        # We treat score >= 0.8 as "verified"
        is_correct = score >= 0.8
        
        # Try symbolic verification if possible
        symbolic_result = None
        if problem.sympy_check:
            try:
                if "derivative" in problem.category:
                    # Extract function and answer
                    parts = solution.split("=")
                    if len(parts) == 2:
                        symbolic_result = verify_derivative(parts[0].strip(), parts[1].strip())
                elif "integral" in problem.category:
                    parts = solution.split("=")
                    if len(parts) == 2:
                        symbolic_result = verify_integral(parts[0].strip().replace("∫", "").replace("dx", ""), parts[1].strip())
                elif "equation" in problem.category or "=" in problem.problem_en:
                    symbolic_result = verify_solution(problem.problem_en, solution)
            except Exception:
                pass
            
            if symbolic_result and symbolic_result.verified:
                is_correct = True
        
        return is_correct, symbolic_result or VerificationResult(
            claim=solution,
            verified=is_correct,
            method="heuristic_score",
            detail=f"Score: {score:.2f}",
            confidence=score,
        )

    def run_sampling(self, problems: Optional[List[BenchmarkProblem]] = None, 
                     n_candidates: int = 5) -> RejectionSamplingResult:
        """Run rejection sampling on a set of problems."""
        if problems is None:
            problems = self.benchmark.get_problems()
        
        result = RejectionSamplingResult(
            total_problems=len(problems),
            total_candidates=0,
            accepted_solutions=0,
            rejection_rate=0.0,
        )
        
        for problem in problems:
            candidates = self.generate_candidates_heuristic(problem, n_candidates)
            result.total_candidates += len(candidates)
            
            for candidate_text in candidates:
                start_time = time.time()
                is_correct, verification = self.verify_candidate(problem, candidate_text)
                gen_time = time.time() - start_time
                
                candidate = CandidateSolution(
                    problem_id=problem.id,
                    problem_text=problem.problem_en,
                    solution_text=candidate_text,
                    verification_result=verification,
                    is_correct=is_correct,
                    generation_time=gen_time,
                )
                
                if is_correct:
                    result.samples.append(candidate)
                    result.accepted_solutions += 1
        
        result.rejection_rate = 1.0 - (result.accepted_solutions / max(result.total_candidates, 1))
        return result

    def export_training_data(self, sampling_result: RejectionSamplingResult, 
                             output_path: str, format: str = "chatml"):
        """Export accepted solutions to training data format."""
        accepted = [s for s in sampling_result.samples if s.is_correct]
        
        if not accepted:
            print("No accepted solutions to export.")
            return
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in accepted:
                if format == "chatml":
                    entry = {
                        "messages": [
                            {"role": "system", "content": "You are JiuZhang-Math, a math expert. Provide clear, step-by-step solutions."},
                            {"role": "user", "content": sample.problem_text},
                            {"role": "assistant", "content": sample.solution_text},
                        ],
                        "problem_id": sample.problem_id,
                        "verification_confidence": sample.verification_result.confidence,
                    }
                else:
                    entry = {
                        "instruction": "Solve the following math problem.",
                        "input": sample.problem_text,
                        "output": sample.solution_text,
                        "problem_id": sample.problem_id,
                    }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        print(f"Exported {len(accepted)} verified samples to {output_path}")

    def print_report(self, result: RejectionSamplingResult):
        """Print a summary report of the sampling run."""
        print(f"\n{'='*60}")
        print(f"JiuZhang Rejection Sampling Report")
        print(f"{'='*60}")
        print(f"Total Problems: {result.total_problems}")
        print(f"Total Candidates Generated: {result.total_candidates}")
        print(f"Accepted Solutions: {result.accepted_solutions}")
        print(f"Rejection Rate: {result.rejection_rate:.1%}")
        print(f"{'='*60}\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="JiuZhang Rejection Sampling Pipeline")
    parser.add_argument("--n-candidates", type=int, default=5, help="Candidates per problem")
    parser.add_argument("--output", default="jiuzhang_rejection_sampling.jsonl")
    parser.add_argument("--format", choices=["chatml", "alpaca"], default="chatml")
    parser.add_argument("--stats", action="store_true", help="Print stats only")
    args = parser.parse_args()

    sampler = RejectionSampler(seed=42)
    
    # Use a subset of problems for demonstration
    problems = sampler.benchmark.get_problems(difficulties=["elementary", "intermediate"])
    
    result = sampler.run_sampling(problems, n_candidates=args.n_candidates)
    
    if args.stats:
        sampler.print_report(result)
        return
    
    sampler.export_training_data(result, args.output, format=args.format)
    sampler.print_report(result)


if __name__ == "__main__":
    main()