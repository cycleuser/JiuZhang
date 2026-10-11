"""Self-Correction Training Data Generator for JiuZhang SmallMathModel.

Generates training data where the model learns to:
  1. Generate an initial answer
  2. Verify it with SymPy
  3. If wrong, identify the error and correct it
  4. Produce a verified final answer

This teaches the model the "verify then correct" pattern, which is essential
for mathematical reasoning with local models.

Each sample has the structure:
  User: Problem statement
  Assistant: 
    Initial attempt: [model's first answer]
    Verification: [SymPy check result]
    Error analysis: [what went wrong, if anything]
    Correction: [fixed answer if needed]
    Final verified answer: [correct answer with proof]
"""

import json
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

import sympy as sp
from sympy import (
    symbols, Symbol, Rational, pi, E, sqrt, sin, cos, tan,
    exp, log, diff, integrate, solve, simplify, factor, expand,
    limit, Matrix, factorial, gcd, isprime, Eq, Ne,
)

from jiuzhang.symbolic_verify import (
    verify_equation, verify_derivative, verify_integral,
    verify_limit, verify_solution, VerificationResult,
)


@dataclass
class SelfCorrectionSample:
    problem_zh: str
    problem_en: str
    initial_answer: str  # The model's first (possibly wrong) attempt
    verification_result: str  # SymPy verification output
    error_analysis: str  # What went wrong
    correction: str  # How to fix it
    final_answer: str  # The correct, verified answer
    category: str
    difficulty: str
    was_initially_wrong: bool  # Whether the initial answer was wrong


class SelfCorrectionDataGenerator:
    """Generate self-correction training data."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.x, self.y, self.n = symbols('x y n')
        self.samples: List[SelfCorrectionSample] = []

    def _generate_wrong_derivative(self, correct_deriv, func) -> str:
        """Generate a plausible but wrong derivative."""
        wrong_strategies = [
            lambda d: f"{d} + 1",  # Off by one
            lambda d: f"2*({d})",  # Double the answer
            lambda d: str(d).replace('x', 'x^2'),  # Wrong power
            lambda d: f"-({d})",  # Wrong sign
            lambda d: str(d).replace('2', '3').replace('3', '2'),  # Coefficient swap
        ]
        strategy = self.rng.choice(wrong_strategies)
        try:
            return strategy(correct_deriv)
        except Exception:
            return f"{correct_deriv} + x"

    def _generate_wrong_integral(self, correct_integral, func) -> str:
        """Generate a plausible but wrong integral."""
        wrong_strategies = [
            lambda i: f"-({i})",  # Wrong sign
            lambda i: f"2*({i})",  # Double
            lambda i: str(i).replace('x**3', 'x**2').replace('x**2', 'x'),  # Wrong power
            lambda i: f"{i} + x",  # Extra term
        ]
        strategy = self.rng.choice(wrong_strategies)
        try:
            return strategy(correct_integral)
        except Exception:
            return f"{correct_integral} + 1"

    def _generate_wrong_solution(self, correct_sol, equation) -> str:
        """Generate a plausible but wrong solution."""
        wrong_strategies = [
            lambda s: f"x = {int(str(s).split('=')[-1]) + 1}" if '=' in str(s) else f"x = {s} + 1",
            lambda s: f"x = -{s}" if '-' not in str(s) else str(s).replace('-', ''),
            lambda s: f"x = {s}/2",
        ]
        strategy = self.rng.choice(wrong_strategies)
        try:
            return strategy(correct_sol)
        except Exception:
            return f"x = {correct_sol} + 1"

    def generate_derivative_samples(self, count: int = 30) -> List[SelfCorrectionSample]:
        """Generate derivative problems where some initial answers are wrong."""
        samples: List[SelfCorrectionSample] = []
        x = self.x

        functions = [
            (x**3, 3*x**2, "x³"),
            (x**4, 4*x**3, "x⁴"),
            (2*x**3 + 3*x**2, 6*x**2 + 6*x, "2x³ + 3x²"),
            (x**5 - 2*x**3 + x, 5*x**4 - 6*x**2 + 1, "x⁵ - 2x³ + x"),
            (3*x**2 - 4*x + 5, 6*x - 4, "3x² - 4x + 5"),
            (x**2 * sp.sin(x), 2*x*sp.sin(x) + x**2*sp.cos(x), "x²·sin(x)"),
            (sp.exp(x) * x, sp.exp(x) + x*sp.exp(x), "e^x · x"),
            (sp.log(x), 1/x, "ln(x)"),
            (sp.sin(x), sp.cos(x), "sin(x)"),
            (sp.cos(x), -sp.sin(x), "cos(x)"),
        ]

        for func, correct_deriv, desc in functions:
            for _ in range(count // len(functions)):
                is_wrong = self.rng.random() < 0.5
                if is_wrong:
                    wrong_deriv = self._generate_wrong_derivative(correct_deriv, func)
                    
                    # Safe verification and error message generation
                    verification_result = ""
                    try:
                        v_result = verify_derivative(str(func), str(wrong_deriv))
                        verified = v_result.verified
                        if not verified:
                            try:
                                diff_expr = simplify(correct_deriv - sp.sympify(str(wrong_deriv)))
                                verification_result = f"SymPy verification: FAILED. Expected d/dx({func}) = {correct_deriv}, but got {wrong_deriv}. The difference is {diff_expr}."
                            except Exception:
                                verification_result = f"SymPy verification: FAILED. Expected d/dx({func}) = {correct_deriv}, but got {wrong_deriv}."
                        else:
                            verification_result = f"SymPy verification: PASSED (Unexpectedly). {wrong_deriv} matches {correct_deriv}."
                    except Exception as e:
                        verified = False
                        verification_result = f"SymPy verification: FAILED due to error: {e}"

                    if not verified:
                        samples.append(SelfCorrectionSample(
                            problem_zh=f"求 f(x) = {desc} 的导数 f'(x)",
                            problem_en=f"Find the derivative f'(x) of f(x) = {desc}",
                            initial_answer=f"f'(x) = {wrong_deriv}",
                            verification_result=verification_result,
                            error_analysis=f"The derivative {wrong_deriv} is incorrect. The error is in the application of the power rule/product rule. The correct derivative should be {correct_deriv}.",
                            correction=f"Applying the correct differentiation rules: d/dx({func}) = {correct_deriv}",
                            final_answer=f"f'(x) = {correct_deriv}",
                            category="calculus",
                            difficulty="intermediate",
                            was_initially_wrong=True,
                        ))
                else:
                    samples.append(SelfCorrectionSample(
                        problem_zh=f"求 f(x) = {desc} 的导数 f'(x)",
                        problem_en=f"Find the derivative f'(x) of f(x) = {desc}",
                        initial_answer=f"f'(x) = {correct_deriv}",
                        verification_result=f"SymPy verification: PASSED. d/dx({func}) = {correct_deriv} ✓",
                        error_analysis="No error found. The initial answer is correct.",
                        correction="No correction needed.",
                        final_answer=f"f'(x) = {correct_deriv}",
                        category="calculus",
                        difficulty="intermediate",
                        was_initially_wrong=False,
                    ))

        return samples

    def generate_integral_samples(self, count: int = 30) -> List[SelfCorrectionSample]:
        """Generate integral problems with self-correction."""
        samples: List[SelfCorrectionSample] = []
        x = self.x

        integrals = [
            (x**2, x**3/3, "x²"),
            (3*x**2, x**3, "3x²"),
            (2*x, x**2, "2x"),
            (sp.cos(x), sp.sin(x), "cos(x)"),
            (sp.sin(x), -sp.cos(x), "sin(x)"),
            (sp.exp(x), sp.exp(x), "e^x"),
            (1/x, sp.log(x), "1/x"),
            (x**3, x**4/4, "x³"),
        ]

        for func, correct_integral, desc in integrals:
            for _ in range(count // len(integrals)):
                is_wrong = self.rng.random() < 0.5
                if is_wrong:
                    wrong_integral = self._generate_wrong_integral(correct_integral, func)
                    try:
                        v_result = verify_integral(str(func), wrong_integral)
                        verified = v_result.verified
                    except Exception:
                        verified = False
                    
                    if not verified:
                        try:
                            diff_of_wrong = diff(sp.sympify(wrong_integral), x)
                            error_analysis=f"The integral {wrong_integral} is incorrect. Differentiating it gives {diff_of_wrong}, which does not equal {func}."
                        except Exception:
                            error_analysis=f"The integral {wrong_integral} is incorrect."
                        
                        samples.append(SelfCorrectionSample(
                            problem_zh=f"求不定积分 ∫{desc} dx",
                            problem_en=f"Find the indefinite integral ∫{desc} dx",
                            initial_answer=f"∫{desc} dx = {wrong_integral} + C",
                            verification_result=f"SymPy verification: FAILED. d/dx({wrong_integral}) ≠ {func}. The derivative of the proposed answer does not match the integrand.",
                            error_analysis=error_analysis,
                            correction=f"The correct integral is found by applying the power rule: ∫{desc} dx = {correct_integral} + C",
                            final_answer=f"∫{desc} dx = {correct_integral} + C",
                            category="calculus",
                            difficulty="intermediate",
                            was_initially_wrong=True,
                        ))
                else:
                    samples.append(SelfCorrectionSample(
                        problem_zh=f"求不定积分 ∫{desc} dx",
                        problem_en=f"Find the indefinite integral ∫{desc} dx",
                        initial_answer=f"∫{desc} dx = {correct_integral} + C",
                        verification_result=f"SymPy verification: PASSED. d/dx({correct_integral}) = {func} ✓",
                        error_analysis="No error found. The initial answer is correct.",
                        correction="No correction needed.",
                        final_answer=f"∫{desc} dx = {correct_integral} + C",
                        category="calculus",
                        difficulty="intermediate",
                        was_initially_wrong=False,
                    ))

        return samples

    def generate_equation_samples(self, count: int = 30) -> List[SelfCorrectionSample]:
        """Generate equation solving problems with self-correction."""
        samples: List[SelfCorrectionSample] = []
        x = self.x

        equations = [
            (Eq(3*x + 7, 22), Eq(x, 5), "3x + 7 = 22", "x = 5"),
            (Eq(2*x - 3, 11), Eq(x, 7), "2x - 3 = 11", "x = 7"),
            (Eq(x**2 - 4, 0), [Eq(x, 2), Eq(x, -2)], "x² - 4 = 0", "x = 2 或 x = -2"),
            (Eq(x**2 - 5*x + 6, 0), [Eq(x, 2), Eq(x, 3)], "x² - 5x + 6 = 0", "x = 2 或 x = 3"),
            (Eq(5*x + 10, 0), Eq(x, -2), "5x + 10 = 0", "x = -2"),
            (Eq(x**2 + 2*x - 8, 0), [Eq(x, 2), Eq(x, -4)], "x² + 2x - 8 = 0", "x = 2 或 x = -4"),
        ]

        for eq, correct_sol, eq_str, sol_str in equations:
            for _ in range(count // len(equations)):
                is_wrong = self.rng.random() < 0.5
                if is_wrong:
                    wrong_sol = self._generate_wrong_solution(sol_str, eq_str)
                    try:
                        v_result = verify_solution(eq_str, wrong_sol)
                        verified = v_result.verified
                    except Exception:
                        verified = False
                    
                    if not verified:
                        samples.append(SelfCorrectionSample(
                            problem_zh=f"解方程: {eq_str}",
                            problem_en=f"Solve the equation: {eq_str}",
                            initial_answer=wrong_sol,
                            verification_result=f"SymPy verification: FAILED. Substituting {wrong_sol} into {eq_str} does not satisfy the equation.",
                            error_analysis=f"The solution {wrong_sol} is incorrect. When substituted back into {eq_str}, it does not yield a true statement.",
                            correction=f"Solving {eq_str} correctly: {sol_str}",
                            final_answer=sol_str,
                            category="algebra",
                            difficulty="intermediate",
                            was_initially_wrong=True,
                        ))
                else:
                    samples.append(SelfCorrectionSample(
                        problem_zh=f"解方程: {eq_str}",
                        problem_en=f"Solve the equation: {eq_str}",
                        initial_answer=sol_str,
                        verification_result=f"SymPy verification: PASSED. {sol_str} satisfies {eq_str} ✓",
                        error_analysis="No error found. The initial answer is correct.",
                        correction="No correction needed.",
                        final_answer=sol_str,
                        category="algebra",
                        difficulty="intermediate",
                        was_initially_wrong=False,
                    ))

        return samples

    def generate_limit_samples(self, count: int = 20) -> List[SelfCorrectionSample]:
        """Generate limit problems with self-correction."""
        samples: List[SelfCorrectionSample] = []
        x = self.x

        limits = [
            (sp.sin(x)/x, x, 0, 1, "sin(x)/x as x→0", "1"),
            ((1 + 1/x)**x, x, sp.oo, E, "(1+1/x)^x as x→∞", "e"),
            (x**2, x, 3, 9, "x² as x→3", "9"),
            (sp.exp(x), x, 0, 1, "e^x as x→0", "1"),
        ]

        for func, var, target, correct_val, desc, val_str in limits:
            for _ in range(count // len(limits)):
                is_wrong = self.rng.random() < 0.5
                if is_wrong:
                    wrong_val = str(int(correct_val) + self.rng.choice([-1, 1, 2])) if correct_val.is_integer else str(correct_val + 1)
                    samples.append(SelfCorrectionSample(
                        problem_zh=f"求极限: lim({desc})",
                        problem_en=f"Find the limit: lim({desc})",
                        initial_answer=f"lim({desc}) = {wrong_val}",
                        verification_result=f"SymPy verification: FAILED. sympy.limit({func}, {var}, {target}) = {correct_val}, not {wrong_val}.",
                        error_analysis=f"The limit {wrong_val} is incorrect. The correct limit as computed by SymPy is {correct_val}.",
                        correction=f"The correct limit is: lim({desc}) = {val_str}",
                        final_answer=f"lim({desc}) = {val_str}",
                        category="calculus",
                        difficulty="intermediate",
                        was_initially_wrong=True,
                    ))
                else:
                    samples.append(SelfCorrectionSample(
                        problem_zh=f"求极限: lim({desc})",
                        problem_en=f"Find the limit: lim({desc})",
                        initial_answer=f"lim({desc}) = {val_str}",
                        verification_result=f"SymPy verification: PASSED. lim({desc}) = {val_str} ✓",
                        error_analysis="No error found. The initial answer is correct.",
                        correction="No correction needed.",
                        final_answer=f"lim({desc}) = {val_str}",
                        category="calculus",
                        difficulty="intermediate",
                        was_initially_wrong=False,
                    ))

        return samples

    def generate_all(self, counts: Optional[Dict[str, int]] = None) -> List[SelfCorrectionSample]:
        """Generate all types of self-correction samples."""
        if counts is None:
            counts = {
                "derivative": 30,
                "integral": 30,
                "equation": 30,
                "limit": 20,
            }
        
        self.samples = []
        self.samples.extend(self.generate_derivative_samples(counts.get("derivative", 30)))
        self.samples.extend(self.generate_integral_samples(counts.get("integral", 30)))
        self.samples.extend(self.generate_equation_samples(counts.get("equation", 30)))
        self.samples.extend(self.generate_limit_samples(counts.get("limit", 20)))
        
        return self.samples

    def to_chatml(self, sample: SelfCorrectionSample) -> Dict:
        """Convert to ChatML format for training."""
        user_content = f"{sample.problem_zh}\n/\n{sample.problem_en}"
        
        assistant_content = f"""Initial attempt: {sample.initial_answer}

Verification: {sample.verification_result}

Error analysis: {sample.error_analysis}

Correction: {sample.correction}

Final verified answer: {sample.final_answer}"""
        
        return {
            "messages": [
                {"role": "system", "content": "你是九章数学专家。请先给出初步答案，然后用SymPy验证，如有错误则纠正。/ You are JiuZhang-Math. First give an initial answer, then verify with SymPy, and correct if wrong."},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": assistant_content},
            ],
            "category": sample.category,
            "difficulty": sample.difficulty,
            "was_initially_wrong": sample.was_initially_wrong,
        }

    def export_jsonl(self, path: str, counts: Optional[Dict[str, int]] = None):
        """Export to JSONL format."""
        if not self.samples:
            self.generate_all(counts)
        
        with open(path, "w", encoding="utf-8") as f:
            for s in self.samples:
                f.write(json.dumps(self.to_chatml(s), ensure_ascii=False) + "\n")
        
        wrong_count = sum(1 for s in self.samples if s.was_initially_wrong)
        print(f"Exported {len(self.samples)} self-correction samples to {path}")
        print(f"  Initially wrong (teaches correction): {wrong_count}")
        print(f"  Initially correct (teaches verification): {len(self.samples) - wrong_count}")

    def get_stats(self) -> Dict:
        if not self.samples:
            self.generate_all()
        
        stats = {
            "total": len(self.samples),
            "wrong_then_correct": sum(1 for s in self.samples if s.was_initially_wrong),
            "always_correct": sum(1 for s in self.samples if not s.was_initially_wrong),
            "by_category": {},
        }
        
        for s in self.samples:
            stats["by_category"][s.category] = stats["by_category"].get(s.category, 0) + 1
        
        return stats


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate self-correction training data")
    parser.add_argument("--output", default="jiuzhang_self_correction.jsonl")
    parser.add_argument("--deriv", type=int, default=30)
    parser.add_argument("--integral", type=int, default=30)
    parser.add_argument("--equation", type=int, default=30)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args()

    gen = SelfCorrectionDataGenerator(seed=42)
    gen.generate_all({
        "derivative": args.deriv,
        "integral": args.integral,
        "equation": args.equation,
        "limit": args.limit,
    })

    if args.stats:
        import pprint
        pprint.pprint(gen.get_stats())
        return

    gen.export_jsonl(args.output)
    print(f"\nDataset statistics:")
    for k, v in gen.get_stats().items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for kk, vv in v.items():
                print(f"    {kk}: {vv}")
        else:
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()