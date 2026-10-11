"""Algebra course - Equations, Functions, Polynomials.

Covers algebraic expressions, linear equations, quadratic equations, and functions.
"""

from jiuzhang.math_engine.curriculum import KnowledgePoint, Lesson


ALGEBRAIC_EXPRESSIONS = KnowledgePoint(
    id="algebra.expressions",
    name="Algebraic Expressions",
    name_cn="代数式",
    category="algebra",
    level="middle_school",
    description="Expressions containing variables, constants, and operations",
    description_cn="含有字母（变量）、数字和运算符号的式子。字母表示未知数或任意数。",
    prerequisites=["arithmetic.operations", "arithmetic.operation_laws"],
    related_points=["algebra.linear_equations", "algebra.polynomials"],
    code_examples=["algebra/equations.py"],
    visualization_types=["function_plot", "expression_tree"],
)

LINEAR_EQUATIONS = KnowledgePoint(
    id="algebra.linear_equations",
    name="Linear Equations",
    name_cn="一元一次方程",
    category="algebra",
    level="middle_school",
    description="Equations of the form ax + b = 0, where a and b are constants",
    description_cn="形如 ax + b = 0 的方程，其中 a ≠ 0。解方程就是求出未知数 x 的值。",
    prerequisites=["algebra.expressions", "arithmetic.operations"],
    related_points=["algebra.systems_equations", "algebra.inequalities"],
    code_examples=["algebra/equations.py"],
    visualization_types=["number_line", "function_plot", "balance_scale"],
)

QUADRATIC_EQUATIONS = KnowledgePoint(
    id="algebra.quadratic_equations",
    name="Quadratic Equations",
    name_cn="一元二次方程",
    category="algebra",
    level="middle_school",
    description="Equations of the form ax² + bx + c = 0, where a ≠ 0",
    description_cn="形如 ax² + bx + c = 0 的方程。可用求根公式、配方法或因式分解法求解。",
    prerequisites=["algebra.linear_equations"],
    related_points=["algebra.parabola", "algebra.polynomials"],
    code_examples=["algebra/equations.py"],
    visualization_types=["parabola_plot", "discriminant_chart"],
)

FUNCTIONS = KnowledgePoint(
    id="algebra.functions",
    name="Functions",
    name_cn="函数",
    category="algebra",
    level="middle_school",
    description="A relation that assigns exactly one output to each input",
    description_cn="对于每一个输入值，都有唯一确定的输出值与之对应。函数是数学的核心概念。",
    prerequisites=["algebra.expressions", "algebra.linear_equations"],
    related_points=["algebra.linear_functions", "algebra.quadratic_functions"],
    code_examples=["algebra/functions.py"],
    visualization_types=["function_plot", "mapping_diagram", "table"],
)

LINEAR_FUNCTIONS = KnowledgePoint(
    id="algebra.linear_functions",
    name="Linear Functions",
    name_cn="一次函数",
    category="algebra",
    level="middle_school",
    description="Functions of the form f(x) = kx + b, graph is a straight line",
    description_cn="形如 f(x) = kx + b 的函数，图像是一条直线。k 是斜率，b 是截距。",
    prerequisites=["algebra.functions", "algebra.linear_equations"],
    related_points=["algebra.functions", "geometry.slope"],
    code_examples=["algebra/functions.py"],
    visualization_types=["function_plot", "slope_visualization"],
)

QUADRATIC_FUNCTIONS = KnowledgePoint(
    id="algebra.quadratic_functions",
    name="Quadratic Functions",
    name_cn="二次函数",
    category="algebra",
    level="middle_school",
    description="Functions of the form f(x) = ax² + bx + c, graph is a parabola",
    description_cn="形如 f(x) = ax² + bx + c 的函数，图像是抛物线。a 决定开口方向。",
    prerequisites=["algebra.functions", "algebra.quadratic_equations"],
    related_points=["algebra.parabola", "algebra.quadratic_equations"],
    code_examples=["algebra/functions.py"],
    visualization_types=["parabola_plot", "vertex_form"],
)

POLYNOMIALS = KnowledgePoint(
    id="algebra.polynomials",
    name="Polynomials",
    name_cn="多项式",
    category="algebra",
    level="middle_school",
    description="Expressions consisting of variables and coefficients with non-negative integer exponents",
    description_cn="由变量和系数组成的表达式，变量的指数是非负整数。多项式是代数的基础。",
    prerequisites=["algebra.expressions"],
    related_points=["algebra.factorization", "algebra.quadratic_equations"],
    code_examples=["algebra/polynomials.py"],
    visualization_types=["polynomial_plot", "degree_comparison"],
)


def get_algebra_knowledge_points() -> list:
    return [
        ALGEBRAIC_EXPRESSIONS,
        LINEAR_EQUATIONS,
        QUADRATIC_EQUATIONS,
        FUNCTIONS,
        LINEAR_FUNCTIONS,
        QUADRATIC_FUNCTIONS,
        POLYNOMIALS,
    ]


def get_equations_lesson() -> Lesson:
    return Lesson(
        id="algebra.equations.intro",
        title="Equations and Functions",
        title_cn="方程与函数",
        knowledge_points=[
            "algebra.expressions",
            "algebra.linear_equations",
            "algebra.quadratic_equations",
            "algebra.functions",
        ],
        content_cn="""# 方程与函数

## 1. 代数式

用字母表示数，这就是代数式。

**例子：**
- 3x + 5：x 是未知数，3 是系数，5 是常数项
- 2a² - 3b + 1：含有两个变量 a 和 b

**求值：** 当 x = 2 时，3x + 5 = 3 × 2 + 5 = 11

## 2. 一元一次方程

形如 ax + b = 0（a ≠ 0）

**解法：**
1. 移项：把含 x 的项移到一边，常数移到另一边
2. 合并同类项
3. 系数化为1

**例子：** 2x + 6 = 0
- 移项：2x = -6
- 化简：x = -3

**验证：** 2 × (-3) + 6 = -6 + 6 = 0 ✓

## 3. 一元二次方程

形如 ax² + bx + c = 0（a ≠ 0）

**求根公式：**

x = (-b ± √(b² - 4ac)) / 2a

**判别式 Δ = b² - 4ac：**
- Δ > 0：两个不相等的实数根
- Δ = 0：两个相等的实数根
- Δ < 0：没有实数根（有复数根）

**例子：** x² - 5x + 6 = 0
- a=1, b=-5, c=6
- Δ = 25 - 24 = 1 > 0
- x = (5 ± 1) / 2
- x₁ = 3, x₂ = 2

## 4. 函数

函数是一种对应关系：每个输入对应唯一的输出。

**表示方法：**
- 解析法：y = f(x) = 2x + 1
- 列表法：表格
- 图像法：坐标系中的曲线

**重要概念：**
- 定义域：x 可以取的值
- 值域：y 可以取的值
- 对应关系：f(x)

## 5. 一次函数 y = kx + b

- **k（斜率）**：决定直线的倾斜程度
  - k > 0：上升
  - k < 0：下降
  - k = 0：水平线
- **b（截距）**：直线与 y 轴的交点

## 6. 二次函数 y = ax² + bx + c

- **a**：决定开口方向（a>0 向上，a<0 向下）
- **顶点**：(-b/2a, f(-b/2a))
- **对称轴**：x = -b/2a
""",
        code_snippets=[
            {
                "title": "Solve Linear Equation",
                "title_cn": "解一元一次方程",
                "code": """# 解 ax + b = 0
def solve_linear(a, b):
    if a == 0:
        return "无解" if b != 0 else "无穷多解"
    return -b / a

print(f"2x + 6 = 0 → x = {solve_linear(2, 6)}")
print(f"3x - 9 = 0 → x = {solve_linear(3, -9)}")
print(f"0x + 5 = 0 → {solve_linear(0, 5)}")""",
            },
            {
                "title": "Solve Quadratic Equation",
                "title_cn": "解一元二次方程",
                "code": """import cmath

def solve_quadratic(a, b, c):
    delta = b**2 - 4*a*c
    x1 = (-b + cmath.sqrt(delta)) / (2*a)
    x2 = (-b - cmath.sqrt(delta)) / (2*a)
    return x1, x2

# x² - 5x + 6 = 0
x1, x2 = solve_quadratic(1, -5, 6)
print(f"x² - 5x + 6 = 0")
print(f"x₁ = {x1.real:.2f}, x₂ = {x2.real:.2f}")

# x² + 2x + 5 = 0 (复数根)
x1, x2 = solve_quadratic(1, 2, 5)
print(f"\\nx² + 2x + 5 = 0")
print(f"x₁ = {x1}, x₂ = {x2}")""",
            },
            {
                "title": "Function Visualization",
                "title_cn": "函数图像",
                "code": """from manim import *

class FunctionVisualization(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[-5, 10, 2],
            x_length=8,
            y_length=6,
            axis_config={"color": GREY},
        ).add_coordinates()
        self.add(axes)

        linear_curve = axes.plot(lambda x: 2 * x + 1, color=BLUE, x_range=[-5, 5])
        quad_curve = axes.plot(lambda x: x**2 - 4, color=RED, x_range=[-5, 5])

        linear_label = MathTex("y = 2x + 1", color=BLUE, font_size=28).next_to(linear_curve, UR, buff=0.1)
        quad_label = MathTex("y = x^2 - 4", color=RED, font_size=28).next_to(quad_curve, UR, buff=0.1)

        self.add(linear_curve, quad_curve, linear_label, quad_label)

        title = Text("一次函数与二次函数", font_size=36).to_edge(UP)
        self.add(title)""",
            },
        ],
        estimated_minutes=90,
    )


def get_functions_lesson() -> Lesson:
    return Lesson(
        id="algebra.functions.deep",
        title="Deep Dive into Functions",
        title_cn="函数深入理解",
        knowledge_points=[
            "algebra.functions",
            "algebra.linear_functions",
            "algebra.quadratic_functions",
        ],
        content_cn="""# 函数深入理解

## 1. 函数的本质

函数就像一台机器：你给它一个输入，它给你一个输出。

**生活中的函数：**
- 自动售货机：投入钱 → 出来饮料
- 温度计：环境温度 → 显示度数
- 计算器：输入数字和运算 → 显示结果

## 2. 函数的三种表示

| 方法 | 例子 | 优点 |
|------|------|------|
| 解析法 | y = 2x + 1 | 精确，便于计算 |
| 列表法 | 表格 | 直观，便于查值 |
| 图像法 | 坐标系中的曲线 | 直观，便于观察趋势 |

## 3. 函数的性质

**单调性：**
- 增函数：x 越大，y 越大
- 减函数：x 越大，y 越小

**奇偶性：**
- 奇函数：f(-x) = -f(x)，图像关于原点对称
- 偶函数：f(-x) = f(x)，图像关于 y 轴对称

**周期性：**
- 周期函数：f(x + T) = f(x)
""",
        code_snippets=[
            {
                "title": "Function Properties",
                "title_cn": "函数性质验证",
                "code": """import numpy as np

def check_odd_even(f, x_vals):
    for x in x_vals:
        fx = f(x)
        f_neg_x = f(-x)
        if np.isclose(f_neg_x, fx):
            return "偶函数"
        elif np.isclose(f_neg_x, -fx):
            return "奇函数"
    return "非奇非偶"

# 测试不同函数
funcs = {
    'f(x) = x²': lambda x: x**2,
    'f(x) = x³': lambda x: x**3,
    'f(x) = x + 1': lambda x: x + 1,
}

x_test = [1, 2, 3]
for name, f in funcs.items():
    result = check_odd_even(f, x_test)
    print(f"{name}: {result}")""",
            },
        ],
        estimated_minutes=60,
    )
