"""Math Evaluation Benchmark for JiuZhang SmallMathModel.

Provides GSM8K-style benchmarks across multiple difficulty levels:
  - Arithmetic (elementary)
  - Algebra (intermediate)
  - Calculus (advanced)
  - Proof reasoning (advanced)
  - Research-level conjecture analysis (frontier)

Each benchmark problem has:
  - A clear problem statement (bilingual)
  - A canonical correct answer
  - A SymPy-verifiable answer (where applicable)
  - A scoring rubric
"""

import random
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import sympy as sp
from sympy import symbols, Rational, pi, E, sqrt, sin, cos, diff, integrate, solve, simplify, limit, oo


@dataclass
class BenchmarkProblem:
    id: str
    category: str
    difficulty: str
    problem_zh: str
    problem_en: str
    answer: str
    sympy_check: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    tolerance: float = 0.01
    rubric: str = "exact"


@dataclass
class BenchmarkResult:
    model: str
    phase: str
    scores: Dict[str, float] = field(default_factory=dict)
    total: int = 0
    correct: int = 0
    partial: int = 0
    details: List[Dict] = field(default_factory=list)


ELEMENTARY_PROBLEMS = [
    BenchmarkProblem("arith_01", "arithmetic", "elementary",
        "计算: 247 + 583 = ?", "Compute: 247 + 583 = ?",
        "830", sympy_check="830", keywords=["830"]),
    BenchmarkProblem("arith_02", "arithmetic", "elementary",
        "计算: 1024 ÷ 16 = ?", "Compute: 1024 ÷ 16 = ?",
        "64", sympy_check="64", keywords=["64"]),
    BenchmarkProblem("arith_03", "arithmetic", "elementary",
        "计算: 15! 的末尾有多少个零？", "How many trailing zeros does 15! have?",
        "3", keywords=["3", "three"]),
    BenchmarkProblem("arith_04", "arithmetic", "elementary",
        "求 gcd(252, 198)", "Find gcd(252, 198)",
        "18", sympy_check="18", keywords=["18"]),
    BenchmarkProblem("arith_05", "arithmetic", "elementary",
        "1+2+...+100 = ?", "1+2+...+100 = ?",
        "5050", sympy_check="5050", keywords=["5050"]),
    BenchmarkProblem("arith_06", "arithmetic", "elementary",
        "7² + 24² = ?", "7² + 24² = ?",
        "625", sympy_check="625", keywords=["625", "25²"]),
    BenchmarkProblem("arith_07", "arithmetic", "elementary",
        "11 是素数吗？", "Is 11 a prime number?",
        "是/Yes", keywords=["yes", "是", "prime"]),
    BenchmarkProblem("arith_08", "arithmetic", "elementary",
        "求 lcm(12, 18)", "Find lcm(12, 18)",
        "36", sympy_check="36", keywords=["36"]),
    BenchmarkProblem("arith_09", "arithmetic", "elementary",
        "2¹⁰ = ?", "2¹⁰ = ?",
        "1024", sympy_check="1024", keywords=["1024"]),
    BenchmarkProblem("arith_10", "arithmetic", "elementary",
        "3/4 + 5/6 = ?", "3/4 + 5/6 = ?",
        "19/12", sympy_check="19/12", keywords=["19/12", "1.583"]),
]

INTERMEDIATE_PROBLEMS = [
    BenchmarkProblem("alg_01", "algebra", "intermediate",
        "解方程: 3x + 7 = 22", "Solve: 3x + 7 = 22",
        "x = 5", sympy_check="x=5", keywords=["5", "x=5"]),
    BenchmarkProblem("alg_02", "algebra", "intermediate",
        "解方程: x² - 5x + 6 = 0", "Solve: x² - 5x + 6 = 0",
        "x = 2 或 x = 3", sympy_check="x=2,x=3", keywords=["2", "3"]),
    BenchmarkProblem("alg_03", "algebra", "intermediate",
        "化简: (x+1)(x-1)", "Simplify: (x+1)(x-1)",
        "x² - 1", sympy_check="x**2-1", keywords=["x²-1", "x^2-1"]),
    BenchmarkProblem("calc_01", "calculus", "intermediate",
        "求导数: f(x) = x³ - 2x + 1 的 f'(x)", "Find f'(x) where f(x) = x³ - 2x + 1",
        "3x² - 2", sympy_check="3*x**2-2", keywords=["3x²", "3x^2"]),
    BenchmarkProblem("calc_02", "calculus", "intermediate",
        "求不定积分: ∫2x dx", "Find the indefinite integral: ∫2x dx",
        "x² + C", sympy_check="x**2+C", keywords=["x²", "x^2"]),
    BenchmarkProblem("calc_03", "calculus", "intermediate",
        "求极限: lim(x→0) sin(x)/x", "Find: lim(x→0) sin(x)/x",
        "1", sympy_check="1", keywords=["1"]),
    BenchmarkProblem("calc_04", "calculus", "intermediate",
        "求导数: f(x) = e^(2x) 的 f'(x)", "Find f'(x) where f(x) = e^(2x)",
        "2e^(2x)", sympy_check="2*exp(2*x)", keywords=["2e", "2e^(2x)"]),
    BenchmarkProblem("geom_01", "geometry", "intermediate",
        "圆的半径为5，求面积", "A circle has radius 5. Find its area.",
        "25π", sympy_check="25*pi", keywords=["25π", "78.5"]),
    BenchmarkProblem("nt_01", "number_theory", "intermediate",
        "7 的 100 次方模 11 等于多少？", "Compute 7^100 mod 11",
        "1", keywords=["1"], rubric="exact"),
    BenchmarkProblem("alg_04", "algebra", "intermediate",
        "求不等式 x² - 4 > 0 的解集", "Solve: x² - 4 > 0",
        "x < -2 或 x > 2", keywords=["-2", "2", ">2", "<-2"]),
]

ADVANCED_PROBLEMS = [
    BenchmarkProblem("proof_01", "proof", "advanced",
        "用数学归纳法证明: 1+2+...+n = n(n+1)/2",
        "Prove by induction: 1+2+...+n = n(n+1)/2",
        "Q.E.D.", rubric="structural",
        keywords=["base case", "inductive", "Q.E.D", "归纳", "基础"]),
    BenchmarkProblem("proof_02", "proof", "advanced",
        "证明 √2 是无理数",
        "Prove that √2 is irrational",
        "Q.E.D.", rubric="structural",
        keywords=["contradiction", "矛盾", "Q.E.D", "gcd", "even"]),
    BenchmarkProblem("calc_05", "calculus", "advanced",
        "求不定积分: ∫x·e^x dx",
        "Find ∫x·e^x dx",
        "(x-1)e^x + C", sympy_check="(x-1)*exp(x)+C",
        keywords=["(x-1)e", "e^x"]),
    BenchmarkProblem("la_01", "linear_algebra", "advanced",
        "求矩阵 [[1,2],[3,4]] 的行列式",
        "Find the determinant of [[1,2],[3,4]]",
        "-2", sympy_check="-2", keywords=["-2"]),
    BenchmarkProblem("la_02", "linear_algebra", "advanced",
        "求矩阵 [[4,7],[2,6]] 的逆矩阵",
        "Find the inverse of [[4,7],[2,6]]",
        "[[6/10, -7/10],[-2/10, 4/10]]", sympy_check="inverse",
        keywords=["0.6", "-0.7", "-0.2", "0.4"]),
    BenchmarkProblem("analysis_01", "analysis", "advanced",
        "证明: f(x)=x² 在 x=2 处连续",
        "Prove: f(x)=x² is continuous at x=2",
        "Q.E.D.", rubric="structural",
        keywords=["ε", "δ", "continuous", "连续", "limit"]),
    BenchmarkProblem("calc_06", "calculus", "advanced",
        "求极限: lim(x→∞) (1+1/x)^x",
        "Find: lim(x→∞) (1+1/x)^x",
        "e", sympy_check="E", keywords=["e", "E", "2.718"]),
    BenchmarkProblem("nt_02", "number_theory", "advanced",
        "验证 Fermat 小定理: a=3, p=7 时 3^6 mod 7 = ?",
        "Verify Fermat's Little Theorem: a=3, p=7, compute 3^6 mod 7",
        "1", sympy_check="1", keywords=["1"]),
    BenchmarkProblem("proof_03", "proof", "advanced",
        "证明: 对所有实数 x, x² ≥ 0",
        "Prove: for all real x, x² ≥ 0",
        "Q.E.D.", rubric="structural",
        keywords=["non-negative", "0", "≥0", "≥ 0", "≥", "nonneg"]),
    BenchmarkProblem("calc_07", "calculus", "advanced",
        "求二阶导数: f(x) = sin(x)·e^x 的 f''(x)",
        "Find f''(x) where f(x) = sin(x)·e^x",
        "2e^x·cos(x)", sympy_check="2*exp(x)*cos(x)",
        keywords=["cos", "2e", "e^x"]),
]

RESEARCH_PROBLEMS = [
    BenchmarkProblem("res_01", "conjecture", "research",
        "分析: Collatz 猜想是否对所有正整数成立？",
        "Analyze: Does the Collatz Conjecture hold for all positive integers?",
        "Open problem", rubric="qualitative",
        keywords=["open", "未解决", "unsolved", "verified", "验证"]),
    BenchmarkProblem("res_02", "conjecture", "research",
        "孪生素数猜想目前最好的结果是什么？",
        "What is the best known result for the Twin Prime Conjecture?",
        "Bounded gaps (Zhang 2013)", rubric="qualitative",
        keywords=["Zhang", "246", "70 million", "7000万", "gap", "bounded"]),
    BenchmarkProblem("res_03", "conjecture", "research",
        "哥德巴赫猜想是否对所有大于2的偶数成立？",
        "Does Goldbach's Conjecture hold for all even integers > 2?",
        "Open, verified up to 4×10^18", rubric="qualitative",
        keywords=["verified", "4×10^18", "open", "1+2", "陈景润"]),
    BenchmarkProblem("res_04", "creative", "research",
        "是否存在多项式时间算法判定素数？",
        "Is there a polynomial-time algorithm for primality testing?",
        "Yes: AKS algorithm (2002)", rubric="qualitative",
        keywords=["AKS", "polynomial", "多项式", "2002"]),
    BenchmarkProblem("res_05", "creative", "research",
        "P vs NP 问题目前的研究进展如何？",
        "What is the current research progress on P vs NP?",
        "Open, one of the Millennium Prize Problems", rubric="qualitative",
        keywords=["millennium", "open", "NP", "unsolved", "Millennium"]),
]


class MathBenchmark:
    """Evaluate math models against structured benchmarks."""

    def __init__(self):
        self.all_problems = (
            ELEMENTARY_PROBLEMS + INTERMEDIATE_PROBLEMS +
            ADVANCED_PROBLEMS + RESEARCH_PROBLEMS
        )

    def get_problems(self, categories: Optional[List[str]] = None,
                     difficulties: Optional[List[str]] = None) -> List[BenchmarkProblem]:
        filtered = self.all_problems
        if categories:
            filtered = [p for p in filtered if p.category in categories]
        if difficulties:
            filtered = [p for p in filtered if p.difficulty in difficulties]
        return filtered

    def score_response(self, problem: BenchmarkProblem, response: str) -> Tuple[float, Dict]:
        response_lower = response.lower().strip()
        answer_lower = problem.answer.lower().strip()

        detail = {"id": problem.id, "category": problem.category, "answer": problem.answer}

        if problem.rubric == "qualitative":
            matched = sum(1 for kw in problem.keywords if kw.lower() in response_lower)
            score = min(matched / max(len(problem.keywords), 1), 1.0)
            detail["keyword_matches"] = matched
            detail["score"] = score
            return score, detail

        if problem.rubric == "structural":
            structural_keywords = ["step", "therefore", "thus", "hence", "since",
                                   "because", "qed", "证明", "因此", "因为", "所以",
                                   "基础", "归纳", "假设", "矛盾"]
            matched_structural = sum(1 for kw in structural_keywords if kw.lower() in response_lower)
            matched_content = sum(1 for kw in problem.keywords if kw.lower() in response_lower)
            structural_score = min(matched_structural / 4, 1.0) * 0.5
            content_score = min(matched_content / max(len(problem.keywords), 1), 1.0) * 0.5
            score = structural_score + content_score
            detail["structural_keywords"] = matched_structural
            detail["content_keywords"] = matched_content
            detail["score"] = score
            return score, detail

        keyword_matched = sum(1 for kw in problem.keywords if kw.lower() in response_lower)
        exact_match = answer_lower in response_lower
        if exact_match:
            detail["score"] = 1.0
            return 1.0, detail
        if keyword_matched > 0:
            score = keyword_matched / len(problem.keywords) * 0.8
            detail["score"] = score
            return score, detail
        detail["score"] = 0.0
        return 0.0, detail

    def run(self, model_name: str = "default", phase: str = "eval",
            categories: Optional[List[str]] = None,
            difficulties: Optional[List[str]] = None) -> BenchmarkResult:
        problems = self.get_problems(categories, difficulties)
        result = BenchmarkResult(model=model_name, phase=phase, total=len(problems))

        for problem in problems:
            score, detail = self.score_response(problem, f"[{model_name} response placeholder]")
            result.details.append(detail)
            result.scores[problem.id] = score
            if score >= 0.8:
                result.correct += 1
            elif score >= 0.4:
                result.partial += 1

        by_category = {}
        for p in problems:
            if p.category not in by_category:
                by_category[p.category] = {"total": 0, "score": 0.0}
            by_category[p.category]["total"] += 1
            by_category[p.category]["score"] += result.scores.get(p.id, 0.0)

        for cat, data in by_category.items():
            result.scores[f"{cat}_avg"] = data["score"] / max(data["total"], 1)

        result.scores["overall"] = sum(result.scores[p.id] for p in problems) / max(len(problems), 1)
        return result

    def evaluate_local(self, model_path: str) -> BenchmarkResult:
        """Evaluate a local model (Ollama or HuggingFace) against the benchmark."""
        result = BenchmarkResult(model=model_path, phase="local_eval")
        problems = self.all_problems

        try:
            from jiuzhang.core.multi_provider_api import MultiProviderClient
            from jiuzhang.core.config import Config
            client = MultiProviderClient(Config())

            for problem in problems:
                prompt = problem.problem_en
                response_result = client.send_message(
                    [{"role": "user", "content": prompt}],
                    model=model_path if "/" not in model_path else None,
                    max_tokens=1024,
                    temperature=0.1,
                )
                if response_result.success:
                    score, detail = self.score_response(problem, response_result.data)
                    result.details.append(detail)
                    result.scores[problem.id] = score
                    if score >= 0.8:
                        result.correct += 1
                    elif score >= 0.4:
                        result.partial += 1
                else:
                    result.scores[problem.id] = 0.0
                    result.details.append({"id": problem.id, "error": response_result.error})
            result.total = len(problems)
            result.scores["overall"] = sum(v for k, v in result.scores.items() if "_" not in k) / max(result.total, 1)
        except Exception as e:
            print(f"Evaluation failed: {e}")
            result.scores["error"] = str(e)

        return result

    def export_problems(self, path: str, format: str = "jsonl"):
        problems = self.all_problems
        if format == "jsonl":
            with open(path, "w", encoding="utf-8") as f:
                for p in problems:
                    f.write(json.dumps(asdict(p), ensure_ascii=False) + "\n")
        elif format == "json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump([asdict(p) for p in problems], f, ensure_ascii=False, indent=2)
        print(f"Exported {len(problems)} benchmark problems to {path}")

    def print_report(self, result: BenchmarkResult):
        print(f"\n{'='*60}")
        print(f"JiuZhang Math Benchmark — {result.phase}")
        print(f"{'='*60}")
        print(f"Model: {result.model}")
        print(f"Problems: {result.total}")
        print(f"Correct (≥80%): {result.correct}")
        print(f"Partial (≥40%): {result.partial}")
        print(f"Overall: {result.scores.get('overall', 0):.1%}")
        print(f"\nBy category:")
        for p in self.all_problems:
            cat = p.category
            key = f"{cat}_avg"
            if key in result.scores and p.id == next(
                (pp for pp in self.all_problems if pp.category == cat), None
            ):
                print(f"  {cat:20s}: {result.scores[key]:.1%}")
        print(f"{'='*60}\n")


import json