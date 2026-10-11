"""Calculus course module - Limits, Derivatives, Integrals."""

from jiuzhang.math_engine.curriculum import KnowledgePoint, Lesson


LIMITS = KnowledgePoint(
    id="calculus.limits",
    name="Limits",
    name_cn="极限",
    category="calculus",
    level="high_school",
    description="The value that a function approaches as the input approaches some value",
    description_cn="当自变量趋近于某个值时，函数趋近的值。极限是微积分的基础。",
    prerequisites=["algebra.functions"],
    related_points=["calculus.derivatives", "calculus.continuity"],
    code_examples=["calculus/limits.py"],
    visualization_types=["limit_approach", "sequence_plot"],
)

DERIVATIVES = KnowledgePoint(
    id="calculus.derivatives",
    name="Derivatives",
    name_cn="导数",
    category="calculus",
    level="high_school",
    description="The rate of change of a function at a point. f'(x) = lim[h→0] (f(x+h) - f(x))/h",
    description_cn="函数在某一点的瞬时变化率。几何意义是切线的斜率。",
    prerequisites=["calculus.limits"],
    related_points=["calculus.applications", "calculus.integrals"],
    code_examples=["calculus/derivatives.py"],
    visualization_types=["tangent_line", "derivative_plot", "rate_visualization"],
)

INTEGRALS = KnowledgePoint(
    id="calculus.integrals",
    name="Integrals",
    name_cn="积分",
    category="calculus",
    level="high_school",
    description="The accumulation of quantities. Definite integral gives the area under a curve",
    description_cn="量的累积。定积分表示曲线下的面积，是导数的逆运算。",
    prerequisites=["calculus.derivatives"],
    related_points=["calculus.derivatives", "calculus.applications"],
    code_examples=["calculus/integrals.py"],
    visualization_types=["area_under_curve", "riemann_sum", "accumulation"],
)


def get_calculus_knowledge_points() -> list:
    return [LIMITS, DERIVATIVES, INTEGRALS]


def get_calculus_lesson() -> Lesson:
    return Lesson(
        id="calculus.intro",
        title="Introduction to Calculus",
        title_cn="微积分入门",
        knowledge_points=[
            "calculus.limits",
            "calculus.derivatives",
            "calculus.integrals",
        ],
        content_cn="""# 微积分入门

## 1. 极限

**什么是极限？**
当 x 越来越接近某个值 a 时，f(x) 趋近的值就是极限。

**记号：** lim(x→a) f(x) = L

**例子：**
lim(x→2) (x² - 4)/(x - 2)
= lim(x→2) (x+2)(x-2)/(x-2)
= lim(x→2) (x+2)
= 4

**重要极限：**
- lim(x→0) sin(x)/x = 1
- lim(x→∞) (1 + 1/x)^x = e ≈ 2.718

## 2. 导数

**什么是导数？**
导数表示函数在某一点的变化率，几何上是切线的斜率。

**定义：**
f'(x) = lim[h→0] [f(x+h) - f(x)] / h

**常用导数公式：**
| 函数 f(x) | 导数 f'(x) |
|-----------|------------|
| C | 0 |
| xⁿ | nxⁿ⁻¹ |
| sin(x) | cos(x) |
| cos(x) | -sin(x) |
| eˣ | eˣ |
| ln(x) | 1/x |

**运算法则：**
- (f ± g)' = f' ± g'
- (fg)' = f'g + fg'
- (f/g)' = (f'g - fg') / g²

**应用：**
- 求切线方程
- 求最大值和最小值
- 判断函数增减性

## 3. 积分

**什么是积分？**
积分是导数的逆运算，表示曲线下的面积。

**不定积分：**
∫ f(x)dx = F(x) + C，其中 F'(x) = f(x)

**定积分：**
∫[a,b] f(x)dx = F(b) - F(a)

**常用积分公式：**
| f(x) | ∫f(x)dx |
|------|---------|
| xⁿ | xⁿ⁺¹/(n+1) + C |
| 1/x | ln|x| + C |
| eˣ | eˣ + C |
| sin(x) | -cos(x) + C |
| cos(x) | sin(x) + C |

**微积分基本定理：**
如果 F'(x) = f(x)，那么 ∫[a,b] f(x)dx = F(b) - F(a)

**应用：**
- 求面积
- 求体积
- 求弧长
""",
        code_snippets=[
            {
                "title": "Numerical Derivative",
                "title_cn": "数值导数",
                "code": """import numpy as np

def numerical_derivative(f, x, h=1e-7):
    return (f(x + h) - f(x - h)) / (2 * h)

# 测试不同函数
funcs = [
    (lambda x: x**2, "x²", lambda x: 2*x),
    (lambda x: x**3, "x³", lambda x: 3*x**2),
    (lambda x: np.sin(x), "sin(x)", lambda x: np.cos(x)),
]

x = 1.0
print(f"x = {x}")
for f, name, f_prime in funcs:
    numerical = numerical_derivative(f, x)
    exact = f_prime(x)
    print(f"  {name}: 数值={numerical:.6f}, 精确={exact:.6f}")""",
            },
            {
                "title": "Numerical Integration",
                "title_cn": "数值积分",
                "code": """import numpy as np
from scipy import integrate

# 数值积分
def f(x):
    return x**2

# 用 scipy 积分
result, error = integrate.quad(f, 0, 1)
print(f"∫₀¹ x² dx = {result:.6f}")
print(f"精确值 = {1/3:.6f}")

# 黎曼和
def riemann_sum(f, a, b, n=1000):
    dx = (b - a) / n
    return sum(f(a + i*dx) * dx for i in range(n))

print(f"黎曼和 (n=1000): {riemann_sum(f, 0, 1):.6f}")
print(f"黎曼和 (n=10000): {riemann_sum(f, 0, 1, 10000):.6f}")""",
            },
            {
                "title": "Derivative Visualization",
                "title_cn": "导数可视化",
                "code": """from manim import *

class DerivativeVisualization(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-2, 10, 2],
            x_length=6,
            y_length=5,
            axis_config={"color": GREY},
        ).add_coordinates().shift(LEFT * 3)
        self.add(axes)

        func_curve = axes.plot(lambda x: x**2, color=BLUE, x_range=[-3, 3])
        deriv_curve = axes.plot(lambda x: 2 * x, color=RED, x_range=[-3, 3])
        self.add(func_curve, deriv_curve)

        func_label = MathTex("f(x) = x^2", color=BLUE, font_size=28).next_to(func_curve, RIGHT).shift(UP * 0.5)
        deriv_label = MathTex("f'(x) = 2x", color=RED, font_size=28).next_to(deriv_curve, RIGHT).shift(DOWN * 0.5)
        self.add(func_label, deriv_label)

        x0 = 1
        y0 = x0**2
        slope = 2 * x0
        tan_curve = axes.plot(lambda x: slope * (x - x0) + y0, color=ORANGE, x_range=[-1, 3])
        dot = Dot(axes.c2p(x0, y0), color=ORANGE, radius=0.08)
        self.add(tan_curve, dot)

        title = Text("函数、导数与切线", font_size=36).to_edge(UP)
        self.add(title)""",
            },
        ],
        estimated_minutes=120,
    )
