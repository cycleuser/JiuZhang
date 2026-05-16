"""Assessment and quiz system for JiuZhang.

Provides automated problem generation, scoring, and progress tracking
across all mathematics domains.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict
from jiuzhang.math_engine.curriculum import KnowledgePoint
import hashlib
import json
import os
import time


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class ProblemType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_IN_BLANK = "fill_in_blank"
    TRUE_FALSE = "true_false"
    PROOF = "proof"
    COMPUTATION = "computation"
    APPLICATION = "application"


@dataclass
class Problem:
    id: str
    question: str
    question_cn: str
    category: str
    knowledge_point_ids: List[str]
    difficulty: Difficulty
    problem_type: ProblemType
    options: Optional[List[str]] = None
    options_cn: Optional[List[str]] = None
    answer: str = ""
    answer_cn: str = ""
    explanation: str = ""
    explanation_cn: str = ""
    hints: List[str] = field(default_factory=list)
    hints_cn: List[str] = field(default_factory=list)
    sympy_verification: Optional[str] = None


@dataclass
class AssessmentResult:
    problem_id: str
    user_answer: str
    correct: bool
    score: float
    time_taken_seconds: float
    feedback: str = ""
    feedback_cn: str = ""


@dataclass
class QuizConfig:
    category: str = ""
    knowledge_point_ids: List[str] = field(default_factory=list)
    difficulty: Difficulty = Difficulty.MEDIUM
    problem_types: List[ProblemType] = field(default_factory=list)
    num_problems: int = 10
    time_limit_minutes: int = 30


PROBLEM_BANK: List[Problem] = [
    Problem(
        id="arith_001",
        question="What is 2^10?",
        question_cn="2的10次方等于多少？",
        category="arithmetic",
        knowledge_point_ids=["arithmetic.natural_numbers"],
        difficulty=Difficulty.EASY,
        problem_type=ProblemType.COMPUTATION,
        answer="1024",
        answer_cn="1024",
        explanation="2^10 = 2×2×2×2×2×2×2×2×2×2 = 1024",
        explanation_cn="2^10 = 2×2×2×2×2×2×2×2×2×2 = 1024",
        hints=["Think of 2^10 as (2^5)^2 = 32^2", "2^5 = 32, so 32^2 = ..."],
        hints_cn=["把2^10看成(2^5)^2 = 32^2", "2^5 = 32, 所以32^2 = ..."],
    ),
    Problem(
        id="arith_002",
        question="What is the GCD of 48 and 18?",
        question_cn="48和18的最大公约数是多少？",
        category="arithmetic",
        knowledge_point_ids=["arithmetic.integers"],
        difficulty=Difficulty.MEDIUM,
        problem_type=ProblemType.COMPUTATION,
        answer="6",
        answer_cn="6",
        explanation="Using Euclidean algorithm: gcd(48,18) = gcd(18,12) = gcd(12,6) = 6",
        explanation_cn="使用辗转相除法：gcd(48,18) = gcd(18,12) = gcd(12,6) = 6",
    ),
    Problem(
        id="arith_003",
        question="Which of the following is a prime number?",
        question_cn="以下哪个是素数？",
        category="number_theory",
        knowledge_point_ids=["number_theory.primes"],
        difficulty=Difficulty.EASY,
        problem_type=ProblemType.MULTIPLE_CHOICE,
        options=["51", "53", "55", "57"],
        options_cn=["51", "53", "55", "57"],
        answer="53",
        answer_cn="53",
        explanation="53 has no divisors other than 1 and itself. 51=3×17, 55=5×11, 57=3×19",
        explanation_cn="53除了1和自身没有其他因数。51=3×17, 55=5×11, 57=3×19",
    ),
    Problem(
        id="alg_001",
        question="Solve x² - 5x + 6 = 0",
        question_cn="解方程 x² - 5x + 6 = 0",
        category="algebra",
        knowledge_point_ids=["algebra.equations"],
        difficulty=Difficulty.EASY,
        problem_type=ProblemType.COMPUTATION,
        answer="x=2, x=3",
        answer_cn="x=2, x=3",
        explanation="Factor: (x-2)(x-3) = 0, so x=2 or x=3",
        explanation_cn="因式分解：(x-2)(x-3) = 0，所以x=2或x=3",
        sympy_verification="solve(x**2 - 5*x + 6, x)",
    ),
    Problem(
        id="alg_002",
        question="What is the sum of the roots of x² + 7x + 12 = 0?",
        question_cn="方程 x² + 7x + 12 = 0 的两根之和等于多少？",
        category="algebra",
        knowledge_point_ids=["algebra.equations"],
        difficulty=Difficulty.MEDIUM,
        problem_type=ProblemType.COMPUTATION,
        answer="-7",
        answer_cn="-7",
        explanation="By Vieta's formulas: sum of roots = -b/a = -7/1 = -7",
        explanation_cn="由韦达定理：两根之和 = -b/a = -7/1 = -7",
    ),
    Problem(
        id="alg_003",
        question="If f(x) = 3x + 2, what is f(f(1))?",
        question_cn="如果 f(x) = 3x + 2，f(f(1)) 等于多少？",
        category="algebra",
        knowledge_point_ids=["algebra.functions"],
        difficulty=Difficulty.EASY,
        problem_type=ProblemType.COMPUTATION,
        answer="17",
        answer_cn="17",
        explanation="f(1) = 3(1)+2 = 5, f(5) = 3(5)+2 = 17",
        explanation_cn="f(1) = 3(1)+2 = 5, f(5) = 3(5)+2 = 17",
    ),
    Problem(
        id="geom_001",
        question="What is the area of a triangle with base 6 and height 4?",
        question_cn="底为6、高为4的三角形面积是多少？",
        category="geometry",
        knowledge_point_ids=["geometry.triangles"],
        difficulty=Difficulty.EASY,
        problem_type=ProblemType.COMPUTATION,
        answer="12",
        answer_cn="12",
        explanation="Area = (1/2) × base × height = (1/2) × 6 × 4 = 12",
        explanation_cn="面积 = (1/2) × 底 × 高 = (1/2) × 6 × 4 = 12",
    ),
    Problem(
        id="geom_002",
        question="In a right triangle, if the legs are 3 and 4, what is the hypotenuse?",
        question_cn="在直角三角形中，如果两条直角边分别为3和4，斜边是多少？",
        category="geometry",
        knowledge_point_ids=["geometry.triangles"],
        difficulty=Difficulty.EASY,
        problem_type=ProblemType.COMPUTATION,
        answer="5",
        answer_cn="5",
        explanation="By the Pythagorean theorem: c = √(3²+4²) = √(9+16) = √25 = 5",
        explanation_cn="由勾股定理：c = √(3²+4²) = √(9+16) = √25 = 5",
    ),
    Problem(
        id="prob_001",
        question="A fair die is rolled twice. What is the probability that the sum is 7?",
        question_cn="一枚均匀骰子掷两次，点数之和为7的概率是多少？",
        category="probability",
        knowledge_point_ids=["probability.basics"],
        difficulty=Difficulty.MEDIUM,
        problem_type=ProblemType.COMPUTATION,
        answer="1/6",
        answer_cn="1/6",
        explanation="P(sum=7) = 6/36 = 1/6 (favorable: (1,6),(2,5),(3,4),(4,3),(5,2),(6,1))",
        explanation_cn="P(和=7) = 6/36 = 1/6 (有利事件：(1,6),(2,5),(3,4),(4,3),(5,2),(6,1))",
    ),
    Problem(
        id="calc_001",
        question="What is the derivative of x³?",
        question_cn="x³的导数是什么？",
        category="calculus",
        knowledge_point_ids=["calculus.derivatives"],
        difficulty=Difficulty.EASY,
        problem_type=ProblemType.COMPUTATION,
        answer="3x²",
        answer_cn="3x²",
        explanation="By the power rule: d/dx(xⁿ) = nxⁿ⁻¹, so d/dx(x³) = 3x²",
        explanation_cn="由幂法则：d/dx(xⁿ) = nxⁿ⁻¹，所以 d/dx(x³) = 3x²",
        sympy_verification="diff(x**3, x)",
    ),
    Problem(
        id="calc_002",
        question="What is ∫₀¹ x² dx?",
        question_cn="∫₀¹ x² dx 等于多少？",
        category="calculus",
        knowledge_point_ids=["calculus.integrals"],
        difficulty=Difficulty.MEDIUM,
        problem_type=ProblemType.COMPUTATION,
        answer="1/3",
        answer_cn="1/3",
        explanation="∫₀¹ x² dx = [x³/3]₀¹ = 1/3 - 0 = 1/3",
        explanation_cn="∫₀¹ x² dx = [x³/3]₀¹ = 1/3 - 0 = 1/3",
    ),
    Problem(
        id="linalg_001",
        question="What is the determinant of [[1,2],[3,4]]?",
        question_cn="矩阵 [[1,2],[3,4]] 的行列式是多少？",
        category="linear_algebra",
        knowledge_point_ids=["linear_algebra.determinant"],
        difficulty=Difficulty.EASY,
        problem_type=ProblemType.COMPUTATION,
        answer="-2",
        answer_cn="-2",
        explanation="det([[1,2],[3,4]]) = 1×4 - 2×3 = 4 - 6 = -2",
        explanation_cn="det([[1,2],[3,4]]) = 1×4 - 2×3 = 4 - 6 = -2",
    ),
    Problem(
        id="nt_001",
        question="What is 7^100 mod 11?",
        question_cn="7^100 mod 11 等于多少？",
        category="number_theory",
        knowledge_point_ids=["number_theory.euler_theorem"],
        difficulty=Difficulty.HARD,
        problem_type=ProblemType.COMPUTATION,
        answer="1",
        answer_cn="1",
        explanation="By Fermat's Little Theorem: a^(p-1) ≡ 1 (mod p) for prime p. So 7^10 ≡ 1 (mod 11), hence 7^100 = (7^10)^10 ≡ 1 (mod 11)",
        explanation_cn="由费马小定理：a^(p-1) ≡ 1 (mod p)，所以 7^10 ≡ 1 (mod 11)，故 7^100 = (7^10)^10 ≡ 1 (mod 11)",
    ),
    Problem(
        id="de_001",
        question="Solve dy/dx = 3x²",
        question_cn="解微分方程 dy/dx = 3x²",
        category="diff_eq",
        knowledge_point_ids=["diff_eq.separable"],
        difficulty=Difficulty.EASY,
        problem_type=ProblemType.COMPUTATION,
        answer="y = x³ + C",
        answer_cn="y = x³ + C",
        explanation="Integrate both sides: ∫dy = ∫3x²dx → y = x³ + C",
        explanation_cn="两边积分：∫dy = ∫3x²dx → y = x³ + C",
    ),
    Problem(
        id="disc_001",
        question="How many ways can you choose 3 cards from a deck of 52?",
        question_cn="从52张牌中选3张有多少种方式？",
        category="discrete",
        knowledge_point_ids=["discrete.combinatorics"],
        difficulty=Difficulty.EASY,
        problem_type=ProblemType.COMPUTATION,
        answer="22100",
        answer_cn="22100",
        explanation="C(52,3) = 52!/(3!×49!) = (52×51×50)/(3×2×1) = 22100",
        explanation_cn="C(52,3) = 52!/(3!×49!) = (52×51×50)/(3×2×1) = 22100",
    ),
    Problem(
        id="arith_tf_001",
        question="True or False: 0 is a natural number.",
        question_cn="判断对错：0是自然数。",
        category="arithmetic",
        knowledge_point_ids=["arithmetic.natural_numbers"],
        difficulty=Difficulty.EASY,
        problem_type=ProblemType.TRUE_FALSE,
        answer="True",
        answer_cn="正确",
        explanation="In modern mathematics, 0 is included in the set of natural numbers (N = {0,1,2,...}), though some conventions start from 1.",
        explanation_cn="在现代数学中，0被包含在自然数集中(N = {0,1,2,...})，尽管有些约定从1开始。",
    ),
]


class AssessmentEngine:
    """Assessment engine for generating quizzes and evaluating answers."""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.expanduser("~/.jiuzhang/assessments")
        self.data_dir = data_dir
        self.results_dir = os.path.join(data_dir, "results")
        os.makedirs(self.results_dir, exist_ok=True)

    def get_problems(
        self,
        category: str = "",
        knowledge_point_ids: List[str] = [],
        difficulty: Difficulty = Difficulty.MEDIUM,
        problem_types: List[ProblemType] = [],
        num_problems: int = 10,
    ) -> List[Problem]:
        filtered = PROBLEM_BANK

        if category:
            filtered = [p for p in filtered if p.category == category]
        if knowledge_point_ids:
            kp_set = set(knowledge_point_ids)
            filtered = [p for p in filtered if kp_set & set(p.knowledge_point_ids)]
        if difficulty != Difficulty.MEDIUM or True:
            filtered_by_diff = [p for p in filtered if p.difficulty == difficulty]
            if filtered_by_diff:
                filtered = filtered_by_diff
        if problem_types:
            pt_set = set(problem_types)
            filtered = [p for p in filtered if p.problem_type in pt_set]

        return filtered[:num_problems]

    def check_answer(self, problem: Problem, user_answer: str) -> AssessmentResult:
        user_normalized = user_answer.strip().lower().replace(" ", "").replace("＝", "=")
        correct_normalized = problem.answer.strip().lower().replace(" ", "")

        correct = user_normalized == correct_normalized

        if not correct and "," in correct_normalized:
            parts_a = sorted(user_normalized.split(","))
            parts_b = sorted(correct_normalized.split(","))
            correct = parts_a == parts_b

        if not correct:
            try:
                from sympy import sympify, simplify
                user_expr = sympify(user_normalized)
                correct_expr = sympify(correct_normalized)
                correct = simplify(user_expr - correct_expr) == 0
            except Exception:
                pass

        score = 1.0 if correct else 0.0
        feedback = ""
        feedback_cn = ""

        if correct:
            feedback = f"Correct! Well done."
            feedback_cn = f"正确！做得好。"
        else:
            feedback = f"Incorrect. The correct answer is: {problem.answer}. {problem.explanation}"
            feedback_cn = f"错误。正确答案是：{problem.answer}。{problem.explanation_cn}"

        return AssessmentResult(
            problem_id=problem.id,
            user_answer=user_answer,
            correct=correct,
            score=score,
            time_taken_seconds=0,
            feedback=feedback,
            feedback_cn=feedback_cn,
        )

    def generate_quiz(self, config: QuizConfig) -> Dict:
        problems = self.get_problems(
            category=config.category,
            knowledge_point_ids=config.knowledge_point_ids,
            difficulty=config.difficulty,
            problem_types=config.problem_types,
            num_problems=config.num_problems,
        )

        quiz_id = hashlib.md5(
            f"{config.category}{config.difficulty.value}{time.time()}".encode()
        ).hexdigest()[:12]

        return {
            "quiz_id": quiz_id,
            "config": {
                "category": config.category,
                "difficulty": config.difficulty.value,
                "num_problems": config.num_problems,
                "time_limit_minutes": config.time_limit_minutes,
            },
            "problems": [
                {
                    "id": p.id,
                    "question": p.question,
                    "question_cn": p.question_cn,
                    "category": p.category,
                    "difficulty": p.difficulty.value,
                    "type": p.problem_type.value,
                    "options": p.options,
                    "options_cn": p.options_cn,
                    "hints": p.hints,
                    "hints_cn": p.hints_cn,
                }
                for p in problems
            ],
            "total_problems": len(problems),
        }

    def submit_quiz(self, quiz_id: str, answers: Dict[str, str]) -> Dict:
        results = []
        total_score = 0.0

        for problem in PROBLEM_BANK:
            if problem.id in answers:
                result = self.check_answer(problem, answers[problem.id])
                results.append(result)
                total_score += result.score

        max_score = len(results) if results else 1
        percentage = (total_score / max_score * 100) if max_score > 0 else 0

        report = {
            "quiz_id": quiz_id,
            "total_problems": len(results),
            "correct": sum(1 for r in results if r.correct),
            "score": total_score,
            "percentage": percentage,
            "results": [
                {
                    "problem_id": r.problem_id,
                    "correct": r.correct,
                    "score": r.score,
                    "feedback": r.feedback,
                    "feedback_cn": r.feedback_cn,
                }
                for r in results
            ],
        }

        result_path = os.path.join(self.results_dir, f"{quiz_id}.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report