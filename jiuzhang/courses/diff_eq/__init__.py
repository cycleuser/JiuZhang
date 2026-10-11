"""Differential Equations course module for JiuZhang."""

from typing import List
from jiuzhang.math_engine.curriculum import KnowledgePoint, Lesson


ODE_BASICS = KnowledgePoint(
    id="diff_eq.ode_basics",
    name="Ordinary Differential Equations",
    name_cn="常微分方程基础",
    category="diff_eq",
    level="undergraduate",
    description="Equations involving derivatives of a function of one variable: F(x, y, y', y'', ...) = 0",
    description_cn="含有一个自变量函数的导数的方程：F(x, y, y', y'', ...) = 0",
    prerequisites=["calculus.derivatives", "calculus.integrals"],
    related_points=["diff_eq.separable", "diff_eq.first_order"],
    code_examples=["diff_eq/ode_basics.py"],
    visualization_types=["slope_field", "solution_curves"],
)

SEPARABLE = KnowledgePoint(
    id="diff_eq.separable",
    name="Separable Equations",
    name_cn="可分离变量方程",
    category="diff_eq",
    level="undergraduate",
    description="dy/dx = f(x)g(y), solved by separating: dy/g(y) = f(x)dx",
    description_cn="dy/dx = f(x)g(y)，通过分离变量求解：dy/g(y) = f(x)dx",
    prerequisites=["diff_eq.ode_basics"],
    related_points=["diff_eq.first_order", "diff_eq.exponential_growth"],
    code_examples=["diff_eq/separable.py"],
    visualization_types=["slope_field", "solution_curves"],
)

FIRST_ORDER = KnowledgePoint(
    id="diff_eq.first_order",
    name="First-Order Linear Equations",
    name_cn="一阶线性方程",
    category="diff_eq",
    level="undergraduate",
    description="y' + p(x)y = q(x), solved via integrating factor μ = e^∫p(x)dx",
    description_cn="y' + p(x)y = q(x)，通过积分因子 μ = e^∫p(x)dx 求解",
    prerequisites=["diff_eq.separable"],
    related_points=["diff_eq.second_order", "diff_eq.systems"],
    code_examples=["diff_eq/first_order.py"],
    visualization_types=["integrating_factor", "solution_family"],
)

SECOND_ORDER = KnowledgePoint(
    id="diff_eq.second_order",
    name="Second-Order Linear Equations",
    name_cn="二阶线性方程",
    category="diff_eq",
    level="undergraduate",
    description="ay'' + by' + cy = f(x), characteristic equation ar² + br + c = 0",
    description_cn="ay'' + by' + cy = f(x)，特征方程 ar² + br + c = 0",
    prerequisites=["diff_eq.first_order", "linear_algebra.matrices"],
    related_points=["diff_eq.systems", "diff_eq.laplace"],
    code_examples=["diff_eq/second_order.py"],
    visualization_types=["phase_portrait", "oscillation_modes"],
)

SYSTEMS = KnowledgePoint(
    id="diff_eq.systems",
    name="Systems of ODEs",
    name_cn="微分方程组",
    category="diff_eq",
    level="undergraduate",
    description="Systems of first-order equations: X' = AX + F(t), eigenvalue analysis",
    description_cn="一阶方程组：X' = AX + F(t)，特征值分析",
    prerequisites=["diff_eq.first_order", "linear_algebra.eigenvalues"],
    related_points=["diff_eq.second_order", "diff_eq.stability"],
    code_examples=["diff_eq/systems.py"],
    visualization_types=["phase_portrait", "vector_field", "trajectory"],
)

LAPLACE = KnowledgePoint(
    id="diff_eq.laplace",
    name="Laplace Transform",
    name_cn="拉普拉斯变换",
    category="diff_eq",
    level="undergraduate",
    description="L{f(t)} = ∫₀^∞ e^(-st)f(t)dt, transforms ODEs to algebraic equations",
    description_cn="L{f(t)} = ∫₀^∞ e^(-st)f(t)dt，将微分方程转化为代数方程",
    prerequisites=["diff_eq.second_order", "calculus.integrals"],
    related_points=["diff_eq.systems"],
    code_examples=["diff_eq/laplace.py"],
    visualization_types=["transform_pair", "pole_zero_plot"],
)

EXPONENTIAL_GROWTH = KnowledgePoint(
    id="diff_eq.exponential_growth",
    name="Population Dynamics",
    name_cn="种群动力学",
    category="diff_eq",
    level="high_school",
    description="Exponential growth dy/dt = ky, logistic growth dy/dt = ky(1-y/K)",
    description_cn="指数增长 dy/dt = ky，逻辑斯蒂增长 dy/dt = ky(1-y/K)",
    prerequisites=["diff_eq.separable"],
    related_points=["diff_eq.predator_prey"],
    code_examples=["diff_eq/population.py"],
    visualization_types=["growth_curves", "logistic_map"],
)

PREDATOR_PREY = KnowledgePoint(
    id="diff_eq.predator_prey",
    name="Predator-Prey Models",
    name_cn="捕食者-猎物模型",
    category="diff_eq",
    level="undergraduate",
    description="Lotka-Volterra equations: dx/dt = αx - βxy, dy/dt = δxy - γy",
    description_cn="洛特卡-沃尔泰拉方程：dx/dt = αx - βxy, dy/dt = δxy - γy",
    prerequisites=["diff_eq.systems", "diff_eq.exponential_growth"],
    related_points=["diff_eq.stability"],
    code_examples=["diff_eq/predator_prey.py"],
    visualization_types=["phase_portrait", "population_cycles"],
)

STABILITY = KnowledgePoint(
    id="diff_eq.stability",
    name="Stability and Phase Analysis",
    name_cn="稳定性与相分析",
    category="diff_eq",
    level="graduate",
    description="Equilibrium points, Lyapunov stability, bifurcation analysis",
    description_cn="平衡点、李雅普诺夫稳定性、分岔分析",
    prerequisites=["diff_eq.systems", "linear_algebra.eigenvalues"],
    related_points=["diff_eq.predator_prey"],
    code_examples=["diff_eq/stability.py"],
    visualization_types=["bifurcation_diagram", "lyapunov", "nullcline"],
)


def get_diff_eq_knowledge_points() -> list:
    return [ODE_BASICS, SEPARABLE, FIRST_ORDER, SECOND_ORDER, SYSTEMS, LAPLACE, EXPONENTIAL_GROWTH, PREDATOR_PREY, STABILITY]


def get_diff_eq_lesson() -> Lesson:
    return Lesson(
        id="diff_eq.intro",
        title="Introduction to Differential Equations",
        title_cn="微分方程入门",
        knowledge_points=[
            "diff_eq.ode_basics",
            "diff_eq.separable",
            "diff_eq.first_order",
            "diff_eq.exponential_growth",
        ],
        content_cn="""# 微分方程入门

## 1. 什么是微分方程？

**定义：** 含有未知函数及其导数的方程。

**例子：**
- dy/dx = 2x（最简单的一阶方程）
- y'' + 3y' + 2y = sin(x)（二阶方程）
- ∂u/∂t = k ∂²u/∂x²（偏微分方程——热传导方程）

**微分方程的分类：**
| 类型 | 阶数 | 线性阶数 |
|------|------|----------|
| 常微分方程(ODE) | y的导数阶 | 一阶/二阶/... |
| 偏微分方程(PDE) | 偏导数阶 | 线性/非线性 |

## 2. 可分离变量方程

**形式：** dy/dx = f(x)·g(y)

**解法：** 分离变量并积分
```
dy/g(y) = f(x)dx
∫ dy/g(y) = ∫ f(x)dx + C
```

**例题：** 解 dy/dx = xy
```
dy/y = x dx
ln|y| = x²/2 + C
y = Ce^(x²/2)
```

## 3. 一阶线性方程

**形式：** y' + p(x)y = q(x)

**积分因子法：**
1. 计算积分因子：μ(x) = e^∫p(x)dx
2. 两边乘以μ：μy' + μpy = μq
3. 左边是 (μy)'，积分得解

## 4. 种群动力学

**指数增长模型：**
- dy/dt = ky → y(t) = y₀e^(kt)
- 种群无限增长（不现实）

**逻辑斯蒂增长模型：**
- dy/dt = ky(1 - y/K)
- 考虑环境容量K的限制
- 解：y(t) = K / (1 + Ae^(-kt))
""",
        code_snippets=[
            {
                "title": "Solving ODEs with SymPy",
                "title_cn": "使用SymPy解微分方程",
                "code": """from sympy import Function, dsolve, Eq, symbols, exp

x = symbols('x')
f = Function('f')

# 可分离变量方程：y' = xy
ode1 = Eq(f(x).diff(x), x * f(x))
sol1 = dsolve(ode1, f(x))
print(f"y' = xy 的解：{sol1}")

# 一阶线性方程：y' + 2y = e^(-x)
ode2 = Eq(f(x).diff(x) + 2*f(x), exp(-x))
sol2 = dsolve(ode2, f(x))
print(f"y' + 2y = e^(-x) 的解：{sol2}")

# 二阶常系数方程：y'' + 3y' + 2y = 0
ode3 = Eq(f(x).diff(x, 2) + 3*f(x).diff(x) + 2*f(x), 0)
sol3 = dsolve(ode3, f(x))
print(f"y'' + 3y' + 2y = 0 的解：{sol3}")""",
            },
            {
                "title": "Phase Portrait Animation",
                "title_cn": "相图动画",
                "code": """from manim import *

class PhasePortrait(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            x_length=6,
            y_length=6,
        ).add_coordinates()
        self.add(axes)

        # Lotka-Volterra vector field
        alpha, beta, delta, gamma = 1.0, 0.1, 0.075, 1.5
        
        def vector_field(pos):
            x, y = pos[0], pos[1]
            dx = alpha * x - beta * x * y
            dy = delta * x * y - gamma * y
            return np.array([dx, dy, 0])

        # Draw a few trajectories
        for x0, y0 in [(2, 1), (1, 2), (3, 0.5)]:
            trajectory = Trajectory(
                lambda t: vector_field(np.array([x0, y0])),
                t_range=[0, 5],
                color=BLUE,
            )
            self.add(trajectory)

        title = Text("捕食者-猎物相图", font_size=32).to_edge(UP)
        self.add(title)""",
            },
        ],
        estimated_minutes=90,
    )