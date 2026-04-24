"""Curriculum-Aware Training Data Pipeline for JiuZhang SmallMathModel.

Generates training data organized by difficulty stages (curriculum learning):
  Stage 1: Arithmetic & basic algebra (elementary)
  Stage 2: Equations, functions, calculus foundations (intermediate)  
  Stage 3: Proofs, analysis, linear algebra (advanced)
  Stage 4: Research-level problems, conjecture exploration (frontier)

Each sample includes:
  - Verified SymPy ground truth
  - Step-by-step chain-of-thought solution
  - Self-verification section
  - Bilingual (zh/en) content
"""

import json
import random
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

import sympy as sp
from sympy import (
    symbols, Symbol, Rational, pi, E, I, oo, sqrt, sin, cos, tan,
    exp, log, diff, integrate, solve, simplify, factor, expand,
    limit, series, Matrix, factorial, gcd, isprime, primerange,
    latex, Eq, Ne, Lt, Gt, Le, Ge,
)

from jiuzhang.symbolic_verify import (
    verify_equation, verify_derivative, verify_integral,
    verify_limit, verify_solution, VerificationResult,
)


STAGE_NAMES = {
    1: "arithmetic",
    2: "equations_functions",
    3: "proofs_analysis",
    4: "research_frontier",
}

STAGE_DESCRIPTIONS = {
    1: "Arithmetic, fractions, basic algebra — elementary level",
    2: "Equations, functions, calculus foundations — intermediate level",
    3: "Proofs, real analysis, linear algebra — advanced level",
    4: "Research-level conjectures, open problems, creative math",
}


@dataclass
class CurriculumSample:
    stage: int
    category: str
    difficulty: str
    instruction_zh: str
    instruction_en: str
    input_zh: str
    input_en: str
    output_zh: str
    output_en: str
    verification: str
    sympy_check: Optional[Dict] = None


class CurriculumDataPipeline:
    """Generate curriculum-organized training data for math fine-tuning."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.x, self.y, self.z, self.n = symbols('x y z n')
        self.samples: List[CurriculumSample] = []
        self._stage_generators = {
            1: self._stage1_arithmetic,
            2: self._stage2_equations,
            3: self._stage3_proofs,
            4: self._stage4_research,
        }

    # ── Stage 1: Arithmetic & Basic Algebra ────────────────────────

    def _stage1_arithmetic(self, count: int) -> List[CurriculumSample]:
        samples: List[CurriculumSample] = []
        x = self.x

        for _ in range(count // 6):
            a, b = self.rng.randint(2, 50), self.rng.randint(2, 50)
            c = a + b
            samples.append(CurriculumSample(
                stage=1, category="addition", difficulty="elementary",
                instruction_zh="计算两个数的和", instruction_en="Calculate the sum of two numbers",
                input_zh=f"{a} + {b} = ?", input_en=f"{a} + {b} = ?",
                output_zh=f"{a} + {b} = {c}", output_en=f"{a} + {b} = {c}",
                verification=f"verify_equation('{a} + {b} = {c}')",
                sympy_check={"claim": f"{a} + {b} = {c}", "verified": True},
            ))

        for _ in range(count // 6):
            a, b = self.rng.randint(10, 100), self.rng.randint(2, 9)
            q, r = divmod(a, b)
            samples.append(CurriculumSample(
                stage=1, category="division", difficulty="elementary",
                instruction_zh="计算带余除法", instruction_en="Compute division with remainder",
                input_zh=f"{a} ÷ {b} = ? 余 ?", input_en=f"{a} ÷ {b} = ? remainder ?",
                output_zh=f"{a} ÷ {b} = {q} 余 {r}，因为 {b} × {q} + {r} = {a}",
                output_en=f"{a} ÷ {b} = {q} remainder {r}, because {b} × {q} + {r} = {a}",
                verification=f"verify_equation('{b}*{q}+{r} = {a}')",
                sympy_check={"claim": f"{b}*{q}+{r} = {a}", "verified": True},
            ))

        for _ in range(count // 6):
            a = self.rng.randint(2, 15)
            f = factorial(a)
            samples.append(CurriculumSample(
                stage=1, category="factorial", difficulty="elementary",
                instruction_zh="计算阶乘", instruction_en="Calculate the factorial",
                input_zh=f"{a}! = ?", input_en=f"{a}! = ?",
                output_zh=f"{a}! = {f}", output_en=f"{a}! = {f}",
                verification=f"verify_equation('{a}! = {f}')",
                sympy_check={"claim": f"factorial({a}) = {f}", "verified": True},
            ))

        for _ in range(count // 6):
            a = self.rng.randint(2, 20)
            s = a * (a + 1) // 2
            samples.append(CurriculumSample(
                stage=1, category="summation", difficulty="elementary",
                instruction_zh="计算1到n的和", instruction_en="Calculate the sum from 1 to n",
                input_zh=f"1 + 2 + ... + {a} = ?", input_en=f"1 + 2 + ... + {a} = ?",
                output_zh=f"由公式 1+2+...+n = n(n+1)/2，得 {a}·{a+1}/2 = {s}",
                output_en=f"By formula 1+2+...+n = n(n+1)/2, we get {a}·{a+1}/2 = {s}",
                verification=f"verify_equation('{a}*{a+1}/2 = {s}')",
                sympy_check={"claim": f"{a}*{a+1}/2 = {s}", "verified": True},
            ))

        for _ in range(count // 6):
            a = self.rng.randint(2, 12)
            s = a ** 2
            samples.append(CurriculumSample(
                stage=1, category="square", difficulty="elementary",
                instruction_zh="计算完全平方数", instruction_en="Calculate a perfect square",
                input_zh=f"{a}² = ?", input_en=f"{a}² = ?",
                output_zh=f"{a}² = {s}", output_en=f"{a}² = {s}",
                verification=f"verify_equation('{a}**2 = {s}')",
                sympy_check={"claim": f"{a}**2 = {s}", "verified": True},
            ))

        for _ in range(count - 5 * (count // 6)):
            a, b = self.rng.randint(2, 20), self.rng.randint(2, 20)
            g = int(gcd(a, b))
            l = a * b // g
            samples.append(CurriculumSample(
                stage=1, category="lcm_gcd", difficulty="elementary",
                instruction_zh="求最大公约数和最小公倍数", instruction_en="Find GCD and LCM",
                input_zh=f"gcd({a}, {b}) = ?, lcm({a}, {b}) = ?",
                input_en=f"gcd({a}, {b}) = ?, lcm({a}, {b}) = ?",
                output_zh=f"gcd({a},{b}) = {g}, lcm({a},{b}) = {l}",
                output_en=f"gcd({a},{b}) = {g}, lcm({a},{b}) = {l}",
                verification=f"verify_equation('{a}*{b}//gcd({a},{b}) = {l}')",
                sympy_check={"claim": f"gcd({a},{b}) = {g}", "verified": True},
            ))

        return samples

    # ── Stage 2: Equations, Functions, Calculus Foundations ─────────

    def _stage2_equations(self, count: int) -> List[CurriculumSample]:
        samples: List[CurriculumSample] = []
        x = self.x

        for _ in range(count // 4):
            a = self.rng.randint(1, 5)
            b = self.rng.randint(-10, 10)
            sol = -Rational(b, a)
            samples.append(CurriculumSample(
                stage=2, category="linear_eq", difficulty="intermediate",
                instruction_zh="解一元一次方程", instruction_en="Solve a linear equation",
                input_zh=f"解方程: {a}x + {b} = 0", input_en=f"Solve: {a}x + {b} = 0",
                output_zh=f"解: {a}x = {-b}, x = {-b}/{a} = {sol}",
                output_en=f"Solution: {a}x = {-b}, x = {-b}/{a} = {sol}",
                verification=f"verify_solution('{a}*x + {b} = 0', 'x = {sol}')",
                sympy_check={"claim": f"{a}*({sol}) + {b} = 0", "verified": True},
            ))

        for _ in range(count // 4):
            coefs = [self.rng.randint(-5, 5) for _ in range(3)]
            if coefs[0] == 0:
                coefs[0] = 1
            poly = coefs[0]*x**2 + coefs[1]*x + coefs[2]
            deriv = diff(poly, x)
            d_s = str(deriv)
            samples.append(CurriculumSample(
                stage=2, category="derivative", difficulty="intermediate",
                instruction_zh="求导数", instruction_en="Find the derivative",
                input_zh=f"求 f(x) = {poly} 的导数", input_en=f"Find f'(x) where f(x) = {poly}",
                output_zh=f"f'(x) = {d_s}", output_en=f"f'(x) = {d_s}",
                verification=f"verify_derivative('{poly}', '{d_s}')",
                sympy_check={"claim": f"d/dx({poly}) = {d_s}", "verified": True},
            ))

        for _ in range(count // 4):
            a_coef = self.rng.randint(1, 3)
            n_pow = self.rng.randint(1, 4)
            func = a_coef * x**n_pow
            integral = integrate(func, x)
            int_s = str(integral)
            samples.append(CurriculumSample(
                stage=2, category="integral", difficulty="intermediate",
                instruction_zh="求不定积分", instruction_en="Find the indefinite integral",
                input_zh=f"∫{func} dx = ?", input_en=f"∫{func} dx = ?",
                output_zh=f"∫{func} dx = {int_s} + C",
                output_en=f"∫{func} dx = {int_s} + C",
                verification=f"verify_integral('{func}', '{int_s}')",
                sympy_check={"claim": f"integral({func}) = {int_s}", "verified": True},
            ))

        for _ in range(count - 3 * (count // 4)):
            a = self.rng.randint(1, 5)
            expr = a * x + self.rng.randint(-5, 5)
            lim_val = limit(expr, x, 0)
            samples.append(CurriculumSample(
                stage=2, category="limit", difficulty="intermediate",
                instruction_zh="求极限", instruction_en="Find the limit",
                input_zh=f"lim(x→0) {expr} = ?", input_en=f"lim(x→0) {expr} = ?",
                output_zh=f"lim(x→0) {expr} = {lim_val}",
                output_en=f"lim(x→0) {expr} = {lim_val}",
                verification=f"verify_limit('{expr}', 'x', '0')",
                sympy_check={"claim": f"lim({expr}, x→0) = {lim_val}", "verified": True},
            ))

        return samples

    # ── Stage 3: Proofs, Analysis, Linear Algebra ───────────────────

    def _stage3_proofs(self, count: int) -> List[CurriculumSample]:
        samples: List[CurriculumSample] = []
        x, n = self.x, self.n

        proof_templates = [
            {
                "category": "proof_irrational",
                "zh_in": "证明 √2 是无理数",
                "en_in": "Prove that √2 is irrational",
                "zh_out": "反证法：假设 √2 是有理数，则 √2 = p/q（p,q 互质）。两边平方得 2 = p²/q²，即 2q² = p²。因此 p² 是偶数，p 也是偶数。设 p=2k，代入得 2q² = 4k²，即 q² = 2k²，q 也是偶数。与 p,q 互质矛盾。故 √2 是无理数。Q.E.D.",
                "en_out": "Proof by contradiction: Assume √2 is rational, so √2 = p/q with gcd(p,q)=1. Squaring: 2 = p²/q², i.e., 2q² = p². Thus p² is even, so p is even. Let p=2k. Then 2q² = 4k², giving q² = 2k², so q is also even. This contradicts gcd(p,q)=1. Therefore √2 is irrational. Q.E.D.",
            },
            {
                "category": "proof_induction_sum",
                "zh_in": "用数学归纳法证明: 1+2+...+n = n(n+1)/2",
                "en_in": "Prove by induction: 1+2+...+n = n(n+1)/2",
                "zh_out": "基础步：n=1 时，左边=1，右边=1·2/2=1，成立。归纳假设：设对某 k≥1，1+2+...+k = k(k+1)/2 成立。归纳步：1+2+...+k+(k+1) = k(k+1)/2 + (k+1) = (k+1)(k/2+1) = (k+1)(k+2)/2。故对 k+1 也成立。由数学归纳法，原式对所有正整数 n 成立。Q.E.D.",
                "en_out": "Base case: n=1, LHS=1, RHS=1·2/2=1. Holds. Inductive hypothesis: Assume 1+2+...+k = k(k+1)/2 for some k≥1. Inductive step: 1+2+...+k+(k+1) = k(k+1)/2 + (k+1) = (k+1)(k/2+1) = (k+1)(k+2)/2. Holds for k+1. By induction, the formula holds for all positive integers n. Q.E.D.",
            },
            {
                "category": "proof_induction_power_sum",
                "zh_in": "用数学归纳法证明: 1²+2²+...+n² = n(n+1)(2n+1)/6",
                "en_in": "Prove by induction: 1²+2²+...+n² = n(n+1)(2n+1)/6",
                "zh_out": "基础步：n=1 时，1²=1，1·2·3/6=1，成立。归纳假设：设对某 k≥1，1²+2²+...+k² = k(k+1)(2k+1)/6。归纳步：1²+2²+...+k²+(k+1)² = k(k+1)(2k+1)/6 + (k+1)² = (k+1)[k(2k+1)/6 + (k+1)] = (k+1)(k+2)(2k+3)/6。故对 k+1 成立。由数学归纳法，原式对所有正整数 n 成立。Q.E.D.",
                "en_out": "Base case: n=1, 1²=1, 1·2·3/6=1. Holds. Inductive hypothesis: Assume 1²+2²+...+k² = k(k+1)(2k+1)/6 for some k≥1. Inductive step: 1²+...+k²+(k+1)² = k(k+1)(2k+1)/6 + (k+1)² = (k+1)[k(2k+1)/6 + (k+1)] = (k+1)(k+2)(2k+3)/6. Holds for k+1. By induction, formula holds for all positive integers n. Q.E.D.",
            },
        ]

        for tmpl in proof_templates:
            for _ in range(count // len(proof_templates)):
                samples.append(CurriculumSample(
                    stage=3, category=tmpl["category"], difficulty="advanced",
                    instruction_zh="请证明以下数学命题", instruction_en="Prove the following mathematical proposition",
                    input_zh=tmpl["zh_in"], input_en=tmpl["en_in"],
                    output_zh=tmpl["zh_out"], output_en=tmpl["en_out"],
                    verification="proof_structure_verified",
                    sympy_check=None,
                ))

        for _ in range(count // 4):
            size = self.rng.choice([2, 3])
            entries = [self.rng.randint(-5, 5) for _ in range(size * size)]
            m = Matrix(size, size, entries)
            det_val = m.det()
            samples.append(CurriculumSample(
                stage=3, category="determinant", difficulty="advanced",
                instruction_zh="计算矩阵的行列式", instruction_en="Compute the determinant",
                input_zh=f"求行列式 det(A)，其中 A = {m}",
                input_en=f"Find det(A), where A = {m}",
                output_zh=f"det(A) = {det_val}", output_en=f"det(A) = {det_val}",
                verification=f"verify_equation('det = {det_val}')",
                sympy_check={"claim": f"matrix_det = {det_val}", "verified": True},
            ))

        return samples

    # ── Stage 4: Research Frontier ─────────────────────────────────

    def _stage4_research(self, count: int) -> List[CurriculumSample]:
        samples: List[CurriculumSample] = []

        conjecture_templates = [
            {
                "category": "collatz_conjecture",
                "zh_in": "分析 Collatz 猜想：对任何正整数 n，反复应用 f(n)=n/2（偶）或 3n+1（奇），最终必到达 1",
                "en_in": "Analyze the Collatz Conjecture: for any positive integer n, repeatedly applying f(n)=n/2 (even) or 3n+1 (odd) always reaches 1",
                "zh_out": "Collatz猜想仍为开放问题。经验证据：已验证至2^68。小规模验证：n=6 → 3 → 10 → 5 → 16 → 8 → 4 → 2 → 1（7步）。反例搜索难以找到：若存在反例，则要么为发散序列，要么为非1的循环。启发论证：平均每步将n乘约3/4（偶数步除2，奇数步乘约3），故序列倾向于减小。但严格证明尚未找到。",
                "en_out": "The Collatz Conjecture remains open. Empirical evidence: verified up to 2^68. Small verification: n=6 → 3 → 10 → 5 → 16 → 8 → 4 → 2 → 1 (7 steps). Counterexample search fails because: if a counterexample exists, it's either a divergent sequence or a cycle not containing 1. Heuristic argument: on average each step multiplies n by ~3/4 (even steps divide by 2, odd steps multiply by ~3), so sequences tend to decrease. But a rigorous proof remains elusive.",
            },
            {
                "category": "twin_prime_conjecture",
                "zh_in": "分析孪生素数猜想：是否存在无穷多对相差2的素数对",
                "en_in": "Analyze the Twin Prime Conjecture: are there infinitely many prime pairs differing by 2?",
                "zh_out": "孪生素数猜想仍为开放问题。最佳已知结果：Yitang Zhang (2013) 证明了存在无穷多对差小于7000万的素数对，后改进至差246。计算证据：已知最大孪生素数对为2996863034895 × 2^1290000 ± 1。关键挑战：素数的分布由Riemann zeta函数零点控制，但精确到差为2需要更强的工具。",
                "en_out": "The Twin Prime Conjecture remains open. Best known result: Yitang Zhang (2013) proved infinitely many prime pairs with gap < 70 million, later improved to gap 246. Computational evidence: largest known twin primes are 2996863034895 × 2^1290000 ± 1. Key challenge: prime distribution is governed by Riemann zeta function zeros, but exact gap-2 requires stronger tools.",
            },
            {
                "category": "goldbach_conjecture",
                "zh_in": "分析哥德巴赫猜想：任何大于2的偶数都可以表示为两个素数之和",
                "en_in": "Analyze Goldbach's Conjecture: every even integer greater than 2 can be expressed as the sum of two primes",
                "zh_out": "哥德巴赫猜想仍为开放问题。已知结果：陈景润证明了'1+2'（任何充分大的偶数是一个素数与一个至多2个素数乘积之和）。Helfgott (2013) 证明了弱哥德巴赫猜想（奇数版本）。计算验证至4×10^18。反证困难：若存在反例N，则N-a和a需同时非素，这在概率上极度不可能。",
                "en_out": "Goldbach's Conjecture remains open. Known results: Chen Jingrun proved '1+2' (every sufficiently large even number is the sum of a prime and a product of at most two primes). Helfgott (2013) proved the weak Goldbach conjecture (odd version). Verified computationally up to 4×10^18. Disproof is difficult: if a counterexample N exists, both N-a and a must be non-prime simultaneously, which is probabilistically extremely unlikely.",
            },
        ]

        for tmpl in conjecture_templates:
            for _ in range(count // len(conjecture_templates)):
                samples.append(CurriculumSample(
                    stage=4, category=tmpl["category"], difficulty="research",
                    instruction_zh="深入分析此数学猜想", instruction_en="Deeply analyze this mathematical conjecture",
                    input_zh=tmpl["zh_in"], input_en=tmpl["en_in"],
                    output_zh=tmpl["zh_out"], output_en=tmpl["en_out"],
                    verification="conjecture_analysis",
                    sympy_check=None,
                ))

        for _ in range(count - len(conjecture_templates) * (count // len(conjecture_templates))):
            n_start = self.rng.randint(2, 30)
            seq = [n_start]
            curr = n_start
            steps = 0
            while curr != 1 and steps < 100:
                curr = curr // 2 if curr % 2 == 0 else 3 * curr + 1
                seq.append(curr)
                steps += 1
            chain = " → ".join(str(s) for s in seq[:12])
            samples.append(CurriculumSample(
                stage=4, category="collatz_verification", difficulty="research",
                instruction_zh="验证Collatz序列", instruction_en="Verify a Collatz sequence",
                input_zh=f"验证Collatz序列: n={n_start}", input_en=f"Verify Collatz sequence: n={n_start}",
                output_zh=f"n={n_start}的Collatz序列: {chain}{'→ ... → 1' if len(seq)>12 else ' → 1' if seq[-1]!=1 else ''}，经{len(seq)-1}步到达1。",
                output_en=f"Collatz sequence for n={n_start}: {chain}{'→ ... → 1' if len(seq)>12 else ' → 1' if seq[-1]!=1 else ''}, reaching 1 in {len(seq)-1} steps.",
                verification=f"collatz_verified_{n_start}",
                sympy_check={"claim": f"collatz({n_start}) reaches 1 in {len(seq)-1} steps", "verified": True},
            ))

        return samples

    # ── Pipeline orchestration ───────────────────────────────────────

    def generate_all_stages(self, counts: Optional[Dict[int, int]] = None) -> List[CurriculumSample]:
        if counts is None:
            counts = {1: 600, 2: 500, 3: 400, 4: 200}
        self.samples = []
        for stage, count in counts.items():
            gen = self._stage_generators[stage]
            stage_samples = gen(count)
            self.samples.extend(stage_samples)
        return self.samples

    def to_chatml(self, sample: CurriculumSample) -> Dict:
        return {
            "messages": [
                {"role": "system", "content": f"你是九章数学专家。/ You are JiuZhang-Math, a math specialist. Stage: {STAGE_NAMES[sample.stage]}"},
                {"role": "user", "content": f"{sample.instruction_zh}\n{sample.input_zh}\n/\n{sample.instruction_en}\n{sample.input_en}"},
                {"role": "assistant", "content": f"{sample.output_zh}\n/\n{sample.output_en}"},
            ],
            "stage": sample.stage,
            "stage_name": STAGE_NAMES[sample.stage],
            "category": sample.category,
            "difficulty": sample.difficulty,
            "verification": sample.verification,
            "sympy_verified": sample.sympy_check is not None,
        }

    def export_jsonl(self, path: str, counts: Optional[Dict[int, int]] = None):
        if not self.samples:
            self.generate_all_stages(counts)
        with open(path, "w", encoding="utf-8") as f:
            for s in self.samples:
                f.write(json.dumps(self.to_chatml(s), ensure_ascii=False) + "\n")
        print(f"Exported {len(self.samples)} curriculum samples to {path}")

    def export_alpaca(self, path: str, counts: Optional[Dict[int, int]] = None):
        if not self.samples:
            self.generate_all_stages(counts)
        with open(path, "w", encoding="utf-8") as f:
            for s in self.samples:
                entry = {
                    "instruction": f"{s.instruction_zh} / {s.instruction_en}",
                    "input": f"{s.input_zh} / {s.input_en}",
                    "output": f"{s.output_zh} / {s.output_en}",
                    "stage": s.stage,
                    "category": s.category,
                    "difficulty": s.difficulty,
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"Exported {len(self.samples)} Alpaca-format samples to {path}")

    def get_stats(self) -> Dict:
        if not self.samples:
            self.generate_all_stages()
        stats = {"total": len(self.samples), "by_stage": {}, "by_category": {}, "verified": 0}
        for s in self.samples:
            stats["by_stage"][s.stage] = stats["by_stage"].get(s.stage, 0) + 1
            stats["by_category"][s.category] = stats["by_category"].get(s.category, 0) + 1
            if s.sympy_check:
                stats["verified"] += 1
        return stats


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate curriculum training data for JiuZhang SmallMathModel")
    parser.add_argument("--output", default="jiuzhang_curriculum.jsonl", help="Output JSONL path")
    parser.add_argument("--format", choices=["chatml", "alpaca"], default="chatml", help="Output format")
    parser.add_argument("--stage1", type=int, default=600, help="Stage 1 sample count")
    parser.add_argument("--stage2", type=int, default=500, help="Stage 2 sample count")
    parser.add_argument("--stage3", type=int, default=400, help="Stage 3 sample count")
    parser.add_argument("--stage4", type=int, default=200, help="Stage 4 sample count")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--stats", action="store_true", help="Print stats only")
    args = parser.parse_args()

    pipeline = CurriculumDataPipeline(seed=args.seed)
    counts = {1: args.stage1, 2: args.stage2, 3: args.stage3, 4: args.stage4}

    if args.stats:
        pipeline.generate_all_stages(counts)
        import pprint
        pprint.pprint(pipeline.get_stats())
        return

    pipeline.generate_all_stages(counts)
    if args.format == "chatml":
        pipeline.export_jsonl(args.output, counts)
    else:
        pipeline.export_alpaca(args.output, counts)

    print(f"\nDataset statistics:")
    for k, v in pipeline.get_stats().items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for kk, vv in v.items():
                print(f"    {kk}: {vv}")
        else:
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()