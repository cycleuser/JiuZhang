"""Open Problems Database for Frontier Mathematics.

Tracks famous unsolved problems across all major fields.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OpenProblem:
    """A famous open problem in mathematics."""

    id: str
    name: str
    name_cn: str
    field: str
    description: str
    description_cn: str
    status: str = "open"
    prize: str = ""
    key_approaches: list = field(default_factory=list)
    related_topics: list = field(default_factory=list)
    difficulty: str = "extreme"
    year_proposed: int = 0


def _get_data_path(filename: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "data", filename)


def _load_open_problems() -> dict:
    path = _get_data_path("open_problems.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {
            k: OpenProblem(
                id=v["id"],
                name=v["name"],
                name_cn=v["name_cn"],
                field=v["field"],
                description=v["description"],
                description_cn=v["description_cn"],
                status=v.get("status", "open"),
                prize=v.get("prize", ""),
                key_approaches=v.get("key_approaches", []),
                related_topics=v.get("related_topics", []),
                difficulty=v.get("difficulty", "extreme"),
                year_proposed=v.get("year_proposed", 0),
            )
            for k, v in raw.items()
        }
    return _OPEN_PROBLEMS_INLINE


_OPEN_PROBLEMS_INLINE = {
    "riemann_hypothesis": OpenProblem(
        id="riemann_hypothesis",
        name="Riemann Hypothesis",
        name_cn="黎曼猜想",
        field="number_theory",
        description="All non-trivial zeros of the Riemann zeta function have real part 1/2",
        description_cn="黎曼ζ函数的所有非平凡零点的实部都等于 1/2",
        status="open",
        prize="$1,000,000 (Millennium Prize)",
        key_approaches=[
            "Random matrix theory",
            "Quantum chaos",
            "Noncommutative geometry",
        ],
        related_topics=[
            "zeta_functions",
            "prime_distribution",
            "analytic_number_theory",
        ],
        difficulty="extreme",
        year_proposed=1859,
    ),
    "p_vs_np": OpenProblem(
        id="p_vs_np",
        name="P vs NP Problem",
        name_cn="P vs NP 问题",
        field="computer_science",
        description="Is every problem whose solution can be verified quickly also solvable quickly?",
        description_cn="每个可以快速验证解的问题是否也可以快速求解？",
        status="open",
        prize="$1,000,000 (Millennium Prize)",
        key_approaches=[
            "Circuit complexity",
            "Proof complexity",
            "Geometric complexity theory",
        ],
        related_topics=["complexity_theory", "cryptography", "algorithms"],
        difficulty="extreme",
        year_proposed=1971,
    ),
    "navier_stokes": OpenProblem(
        id="navier_stokes",
        name="Navier-Stokes Existence and Smoothness",
        name_cn="纳维 - 斯托克斯方程存在性与光滑性",
        field="mathematical_physics",
        description="Prove existence and smoothness of solutions to the 3D Navier-Stokes equations",
        description_cn="证明三维纳维 - 斯托克斯方程解的存在性和光滑性",
        status="open",
        prize="$1,000,000 (Millennium Prize)",
        key_approaches=["Energy methods", "Regularity theory", "Turbulence modeling"],
        related_topics=["fluid_dynamics", "pde", "geometric_analysis"],
        difficulty="extreme",
        year_proposed=1845,
    ),
    "hodge_conjecture": OpenProblem(
        id="hodge_conjecture",
        name="Hodge Conjecture",
        name_cn="霍奇猜想",
        field="algebraic_geometry",
        description="Every Hodge class on a projective complex manifold is a rational linear combination of algebraic cycles",
        description_cn="射影复流形上的每个霍奇类都是代数圈的有理线性组合",
        status="open",
        prize="$1,000,000 (Millennium Prize)",
        key_approaches=[
            "Motivic cohomology",
            "Derived categories",
            "Non-abelian Hodge theory",
        ],
        related_topics=["algebraic_cycles", "cohomology", "complex_geometry"],
        difficulty="extreme",
        year_proposed=1950,
    ),
    "yang_mills": OpenProblem(
        id="yang_mills",
        name="Yang-Mills Existence and Mass Gap",
        name_cn="杨 - 米尔斯存在性与质量间隙",
        field="mathematical_physics",
        description="Prove existence of Yang-Mills theory with a mass gap",
        description_cn="证明存在质量间隙的杨 - 米尔斯理论",
        status="open",
        prize="$1,000,000 (Millennium Prize)",
        key_approaches=[
            "Constructive QFT",
            "Lattice gauge theory",
            "Renormalization group",
        ],
        related_topics=["quantum_field_theory", "gauge_theory", "particle_physics"],
        difficulty="extreme",
        year_proposed=1954,
    ),
    "birch_swinnerton_dyer": OpenProblem(
        id="birch_swinnerton_dyer",
        name="Birch and Swinnerton-Dyer Conjecture",
        name_cn="BSD 猜想",
        field="number_theory",
        description="The rank of an elliptic curve equals the order of vanishing of its L-function at s=1",
        description_cn="椭圆曲线的秩等于其 L-函数在 s=1 处的零点阶数",
        status="partial",
        prize="$1,000,000 (Millennium Prize)",
        key_approaches=["Iwasawa theory", "Euler systems", "p-adic L-functions"],
        related_topics=["elliptic_curves", "l_functions", "arithmetic_geometry"],
        difficulty="extreme",
        year_proposed=1965,
    ),
    "poincare_conjecture": OpenProblem(
        id="poincare_conjecture",
        name="Poincare Conjecture",
        name_cn="庞加莱猜想",
        field="topology",
        description="Every simply connected closed 3-manifold is homeomorphic to the 3-sphere",
        description_cn="每个单连通的闭 3-流形都同胚于 3-球面",
        status="solved",
        prize="Solved by Perelman (2003)",
        key_approaches=["Ricci flow", "Geometric analysis", "Surgery theory"],
        related_topics=["3_manifolds", "ricci_flow", "geometric_topology"],
        difficulty="extreme",
        year_proposed=1904,
    ),
    "goldbach": OpenProblem(
        id="goldbach",
        name="Goldbach's Conjecture",
        name_cn="哥德巴赫猜想",
        field="number_theory",
        description="Every even integer greater than 2 is the sum of two primes",
        description_cn="每个大于 2 的偶数都可以表示为两个素数之和",
        status="open",
        prize="",
        key_approaches=["Sieve methods", "Circle method", "Additive number theory"],
        related_topics=["prime_numbers", "additive_number_theory"],
        difficulty="hard",
        year_proposed=1742,
    ),
    "twin_prime": OpenProblem(
        id="twin_prime",
        name="Twin Prime Conjecture",
        name_cn="孪生素数猜想",
        field="number_theory",
        description="There are infinitely many pairs of primes that differ by 2",
        description_cn="存在无穷多对相差 2 的素数",
        status="partial",
        prize="",
        key_approaches=["Sieve theory", "Bounded gaps (Zhang, Maynard)", "GPY method"],
        related_topics=["prime_numbers", "analytic_number_theory"],
        difficulty="hard",
        year_proposed=1849,
    ),
    "collatz": OpenProblem(
        id="collatz",
        name="Collatz Conjecture",
        name_cn="考拉兹猜想",
        field="dynamical_systems",
        description="The Collatz sequence always reaches 1 for any positive starting integer",
        description_cn="考拉兹序列从任何正整数开始最终都会到达 1",
        status="open",
        prize="",
        key_approaches=["Ergodic theory", "Probabilistic methods", "2-adic analysis"],
        related_topics=["dynamical_systems", "number_theory"],
        difficulty="hard",
        year_proposed=1937,
    ),
    "abc_conjecture": OpenProblem(
        id="abc_conjecture",
        name="ABC Conjecture",
        name_cn="ABC 猜想",
        field="number_theory",
        description="For any epsilon>0, there exists K_epsilon such that for all coprime a+b=c, c < K_epsilon * rad(abc)^(1+epsilon)",
        description_cn="对任意epsilon>0，存在 K_epsilon使得对所有互素的 a+b=c，有 c < K_epsilon * rad(abc)^(1+epsilon)",
        status="open",
        prize="",
        key_approaches=[
            "Inter-universal Teichmuller theory (Mochizuki)",
            "Diophantine approximation",
        ],
        related_topics=["diophantine_equations", "arithmetic_geometry"],
        difficulty="extreme",
        year_proposed=1985,
    ),
    "homological_mirror_symmetry": OpenProblem(
        id="homological_mirror_symmetry",
        name="Homological Mirror Symmetry Conjecture",
        name_cn="同调镜像对称猜想",
        field="mathematical_physics",
        description="The derived category of coherent sheaves on a Calabi-Yau is equivalent to the Fukaya category of its mirror",
        description_cn="卡拉比 - 丘流形上的凝聚层导出范畴等价于其镜像的 Fukaya 范畴",
        status="partial",
        prize="",
        key_approaches=[
            "Symplectic topology",
            "Derived algebraic geometry",
            "Floer theory",
        ],
        related_topics=["mirror_symmetry", "symplectic_topology", "algebraic_geometry"],
        difficulty="extreme",
        year_proposed=1994,
    ),
    "langlands_full": OpenProblem(
        id="langlands_full",
        name="Full Langlands Correspondence",
        name_cn="朗兰兹对应（完整形式）",
        field="number_theory",
        description="Establish the full functoriality and reciprocity in the Langlands program",
        description_cn="建立朗兰兹纲领中的完整函子性和互反律",
        status="partial",
        prize="",
        key_approaches=["Trace formula", "Automorphic forms", "Galois representations"],
        related_topics=[
            "automorphic_forms",
            "galois_representations",
            "representation_theory",
        ],
        difficulty="extreme",
        year_proposed=1967,
    ),
    "smooth_4d_poincare": OpenProblem(
        id="smooth_4d_poincare",
        name="Smooth 4D Poincare Conjecture",
        name_cn="光滑 4 维庞加莱猜想",
        field="topology",
        description="Every smooth homotopy 4-sphere is diffeomorphic to the standard 4-sphere",
        description_cn="每个光滑同伦 4-球面都微分同胚于标准 4-球面",
        status="open",
        prize="",
        key_approaches=["Gauge theory", "Floer homology", "Exotic smooth structures"],
        related_topics=["4_manifolds", "differential_topology", "gauge_theory"],
        difficulty="extreme",
        year_proposed=1960,
    ),
    "jacobian_conjecture": OpenProblem(
        id="jacobian_conjecture",
        name="Jacobian Conjecture",
        name_cn="雅可比猜想",
        field="algebraic_geometry",
        description="A polynomial map with constant non-zero Jacobian determinant is invertible",
        description_cn="雅可比行列式为非零常数的多项式映射是可逆的",
        status="open",
        prize="",
        key_approaches=[
            "Algebraic geometry",
            "Dynamical systems",
            "Commutative algebra",
        ],
        related_topics=["polynomial_maps", "automorphisms", "algebraic_geometry"],
        difficulty="hard",
        year_proposed=1939,
    ),
}


class OpenProblemsDB:
    """Database of open problems in mathematics."""

    def __init__(self):
        self._problems: Optional[dict] = None

    @property
    def _loaded_problems(self) -> dict:
        if self._problems is None:
            self._problems = _load_open_problems()
        return self._problems

    def get_problem(self, problem_id: str) -> Optional[OpenProblem]:
        """Get a problem by ID."""
        return self._loaded_problems.get(problem_id)

    def get_problems_by_field(self, field: str) -> list:
        """Get all problems in a field."""
        return [p for p in self._loaded_problems.values() if p.field == field]

    def get_problems_by_status(self, status: str) -> list:
        """Get problems by status."""
        return [p for p in self._loaded_problems.values() if p.status == status]

    def get_problems_by_difficulty(self, difficulty: str) -> list:
        """Get problems by difficulty."""
        return [p for p in self._loaded_problems.values() if p.difficulty == difficulty]

    def search(self, query: str, language: str = "zh") -> list:
        """Search problems by keyword."""
        query_lower = query.lower()
        results = []

        for problem in self._loaded_problems.values():
            score = 0
            if query_lower in problem.name.lower():
                score += 3
            if query_lower in problem.name_cn:
                score += 3
            if query_lower in problem.description.lower():
                score += 2
            if query_lower in problem.description_cn:
                score += 2
            if query_lower in problem.field.lower():
                score += 1

            if score > 0:
                results.append((score, problem))

        results.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in results]

    def generate_report(self, language: str = "zh") -> str:
        """Generate a report of all open problems."""
        parts = []
        if language == "zh":
            parts.append("# 数学开放问题\n")
            parts.append(
                f"共收录 {len(self._loaded_problems)} 个重要开放问题，按解决状态分类如下。\n"
            )

            for status in ["solved", "partial", "open"]:
                status_name = {
                    "solved": "已解决",
                    "partial": "部分解决",
                    "open": "未解决",
                }[status]
                problems = self.get_problems_by_status(status)
                if problems:
                    parts.append(f"\n## {status_name}\n")
                    parts.append(f"共 {len(problems)} 个。\n\n")
                    for p in problems:
                        parts.append(f"### {p.name_cn}\n\n")
                        parts.append(f"{p.description_cn}\n\n")
                        parts.append(
                            f"所属领域：{p.field}。提出年份：{p.year_proposed}。\n"
                        )
                        if p.prize:
                            parts.append(f"奖励：{p.prize}。\n")
                        if p.key_approaches:
                            approaches_str = "、".join(p.key_approaches)
                            parts.append(f"主要研究方向包括{approaches_str}。\n")
                        parts.append("\n")
        else:
            parts.append("# Open Problems in Mathematics\n")
            parts.append(
                f"Database of {len(self._loaded_problems)} important unsolved problems.\n"
            )

            for status in ["solved", "partial", "open"]:
                problems = self.get_problems_by_status(status)
                if problems:
                    parts.append(f"\n## {status.title()}\n")
                    parts.append(f"{len(problems)} problems.\n\n")
                    for p in problems:
                        parts.append(f"### {p.name}\n\n")
                        parts.append(f"{p.description}\n\n")
                        parts.append(
                            f"Field: {p.field}. Proposed: {p.year_proposed}.\n"
                        )
                        if p.prize:
                            parts.append(f"Prize: {p.prize}.\n")
                        if p.key_approaches:
                            approaches_str = ", ".join(p.key_approaches)
                            parts.append(f"Key approaches: {approaches_str}.\n")
                        parts.append("\n")

        return "\n".join(parts)

    def get_millennium_problems(self) -> list:
        """Get the 7 Millennium Prize Problems."""
        millennium_ids = [
            "riemann_hypothesis",
            "p_vs_np",
            "navier_stokes",
            "hodge_conjecture",
            "yang_mills",
            "birch_swinnerton_dyer",
            "poincare_conjecture",
        ]
        return [self._loaded_problems[pid] for pid in millennium_ids if pid in self._loaded_problems]