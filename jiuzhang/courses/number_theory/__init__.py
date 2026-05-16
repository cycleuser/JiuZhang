"""Number Theory course module for JiuZhang."""

from typing import List
from jiuzhang.math_engine.curriculum import KnowledgePoint, Lesson


DIVISIBILITY = KnowledgePoint(
    id="number_theory.divisibility",
    name="Divisibility",
    name_cn="整除性",
    category="number_theory",
    level="middle_school",
    description="Properties of integer division: a|b means b = a*k for some integer k",
    description_cn="整数整除的性质：a|b表示存在整数k使得b=a*k",
    prerequisites=["arithmetic.integers"],
    related_points=["number_theory.primes", "number_theory.gcd"],
    code_examples=["number_theory/divisibility.py"],
    visualization_types=["divisibility_grid", "factor_tree"],
)

PRIMES = KnowledgePoint(
    id="number_theory.primes",
    name="Prime Numbers",
    name_cn="素数",
    category="number_theory",
    level="middle_school",
    description="Numbers greater than 1 with exactly two divisors. Foundation of number theory.",
    description_cn="大于1且只有1和自身两个因数的数，数论的基石。",
    prerequisites=["number_theory.divisibility"],
    related_points=["number_theory.factorization", "number_theory.divisibility"],
    code_examples=["number_theory/primes.py"],
    visualization_types=["sieve_of_eratosthenes", "prime_spiral"],
)

GCD_LCM = KnowledgePoint(
    id="number_theory.gcd",
    name="GCD and LCM",
    name_cn="最大公约数与最小公倍数",
    category="number_theory",
    level="middle_school",
    description="Greatest Common Divisor (Euclidean algorithm) and Least Common Multiple",
    description_cn="最大公约数（辗转相除法）和最小公倍数",
    prerequisites=["number_theory.divisibility"],
    related_points=["number_theory.divisibility", "number_theory.diophantine"],
    code_examples=["number_theory/gcd.py"],
    visualization_types=["euclidean_animation", "venn_diagram"],
)

FACTORIZATION = KnowledgePoint(
    id="number_theory.factorization",
    name="Prime Factorization",
    name_cn="质因数分解",
    category="number_theory",
    level="middle_school",
    description="Fundamental Theorem of Arithmetic: every integer > 1 is a unique product of primes",
    description_cn="算术基本定理：每个大于1的整数都可唯一分解为素数之积",
    prerequisites=["number_theory.primes"],
    related_points=["number_theory.primes", "number_theory.gcd"],
    code_examples=["number_theory/factorization.py"],
    visualization_types=["factor_tree", "prime_decomposition"],
)

MODULAR_ARITHMETIC = KnowledgePoint(
    id="number_theory.modular",
    name="Modular Arithmetic",
    name_cn="同余与模运算",
    category="number_theory",
    level="high_school",
    description="Arithmetic on remainders: a ≡ b (mod n) means n|(a-b)",
    description_cn="基于余数的运算：a ≡ b (mod n)表示n|(a-b)",
    prerequisites=["number_theory.divisibility", "algebra.equations"],
    related_points=["number_theory.diophantine", "number_theory.euler_theorem"],
    code_examples=["number_theory/modular.py"],
    visualization_types=["clock_arithmetic", "modular_table"],
)

DIOPHANTINE = KnowledgePoint(
    id="number_theory.diophantine",
    name="Diophantine Equations",
    name_cn="丢番图方程",
    category="number_theory",
    level="undergraduate",
    description="Polynomial equations with integer solutions (e.g., Fermat's Last Theorem)",
    description_cn="求整数解的多项式方程（如费马大定理）",
    prerequisites=["number_theory.modular", "number_theory.gcd"],
    related_points=["number_theory.euler_theorem"],
    code_examples=["number_theory/diophantine.py"],
    visualization_types=["integer_lattice", "solution_set"],
)

EULER_THEOREM = KnowledgePoint(
    id="number_theory.euler_theorem",
    name="Euler's Theorem and Fermat's Little Theorem",
    name_cn="欧拉定理与费马小定理",
    category="number_theory",
    level="undergraduate",
    description="a^φ(n) ≡ 1 (mod n) when gcd(a,n)=1; special case: Fermat's Little Theorem",
    description_cn="当gcd(a,n)=1时，a^φ(n) ≡ 1 (mod n)；特例：费马小定理",
    prerequisites=["number_theory.modular"],
    related_points=["number_theory.modular", "number_theory.diophantine"],
    code_examples=["number_theory/euler.py"],
    visualization_types=["totient_function", "ferat_test"],
)


def get_number_theory_knowledge_points() -> list:
    return [DIVISIBILITY, PRIMES, GCD_LCM, FACTORIZATION, MODULAR_ARITHMETIC, DIOPHANTINE, EULER_THEOREM]


def get_number_theory_lesson() -> Lesson:
    return Lesson(
        id="number_theory.intro",
        title="Introduction to Number Theory",
        title_cn="数论入门",
        knowledge_points=[
            "number_theory.divisibility",
            "number_theory.primes",
            "number_theory.gcd",
            "number_theory.factorization",
            "number_theory.modular",
        ],
        content_cn="""# 数论入门

## 1. 整除性

**定义：** 如果存在整数k使得 b = a×k，则称 a 整除 b，记作 a|b。

**性质：**
- 传递性：若 a|b 且 b|c，则 a|c
- 若 a|b 且 a|c，则 a|(b±c)
- 若 a|b，则 a|bc（c为任意整数）

**例子：**
- 2|6 成立（因为 6 = 2×3）
- 3|7 不成立

## 2. 素数

**定义：** 大于1且只有1和自身两个正因数的整数。

**重要定理：**
- 素数有无穷多个（欧几里得证明）
- 每个大于1的整数要么是素数，要么可分解为素数之积

**埃拉托斯特尼筛法：** 从2开始，划掉每个素数的倍数
- 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, ...

## 3. 最大公约数与最小公倍数

**辗转相除法（欧几里得算法）：**
```
gcd(48, 18):
48 = 18 × 2 + 12
18 = 12 × 1 + 6
12 = 6 × 2 + 0
→ gcd(48, 18) = 6
```

**关系：** gcd(a,b) × lcm(a,b) = a × b

## 4. 质因数分解

**算术基本定理：** 每个大于1的整数都可唯一地表示为素数的乘积。

**例子：**
- 12 = 2² × 3
- 360 = 2³ × 3² × 5
- 1001 = 7 × 11 × 13

## 5. 同余与模运算

**定义：** a ≡ b (mod n) 表示 n|(a-b)

**性质：**
- 加法：若 a≡b (mod n)，c≡d (mod n)，则 a+c≡b+d (mod n)
- 乘法：若 a≡b (mod n)，c≡d (mod n)，则 ac≡bd (mod n)
- 幂：若 a≡b (mod n)，则 a^k≡b^k (mod n)

**时钟算术：** 模12的算术就是时钟上的运算
""",
        code_snippets=[
            {
                "title": "Primality Test",
                "title_cn": "素数判定",
                "code": """from sympy import isprime, factorint, gcd, lcm

n = 97
print(f"Is {n} prime? {isprime(n)}")

n = 360
print(f"Factorization of {n}: {factorint(n)}")

a, b = 48, 18
print(f"GCD({a}, {b}) = {gcd(a, b)}")
print(f"LCM({a}, {b}) = {lcm(a, b)}")
print(f"Verify: gcd × lcm = {gcd(a,b) * lcm(a,b)}, a × b = {a * b}")""",
            },
            {
                "title": "Modular Arithmetic",
                "title_cn": "模运算可视化",
                "code": """from manim import *

class ModularClock(Scene):
    def construct(self):
        n = 12
        circle = Circle(radius=2, color=BLUE)
        self.add(circle)
        
        for i in range(n):
            angle = i * 2 * PI / n - PI/2
            pos = circle.point_at_angle(angle)
            num = MathTex(str(i), font_size=28)
            num.move_to(pos + (pos - circle.get_center()) * 0.3)
            self.add(num)
        
        title = Text("模12算术时钟", font_size=32).to_edge(UP)
        self.add(title)""",
            },
        ],
        estimated_minutes=60,
    )