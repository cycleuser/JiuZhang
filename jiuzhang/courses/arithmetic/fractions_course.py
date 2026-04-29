"""Fractions course module.

Covers fraction concepts, operations, and visualizations.
"""

from jiuzhang.math_engine.curriculum import KnowledgePoint, Lesson
from fractions import Fraction


FRACTION_CONCEPT = KnowledgePoint(
    id="arithmetic.fraction_concept",
    name="Fraction Concept",
    name_cn="分数概念",
    category="arithmetic",
    level="elementary",
    description="A fraction represents a part of a whole, written as a/b where a is numerator and b is denominator",
    description_cn="分数表示一个整体的一部分，写作 a/b，其中 a 是分子，b 是分母。",
    prerequisites=["arithmetic.division"],
    related_points=["arithmetic.decimals", "arithmetic.rational_numbers"],
    code_examples=["arithmetic/fractions_course.py"],
    visualization_types=["pie_chart", "bar_model", "number_line"],
)

FRACTION_OPS = KnowledgePoint(
    id="arithmetic.fraction_operations",
    name="Fraction Operations",
    name_cn="分数运算",
    category="arithmetic",
    level="elementary",
    description="Addition, subtraction, multiplication, and division of fractions",
    description_cn="分数的加减乘除运算。需要先通分或约分。",
    prerequisites=["arithmetic.fraction_concept", "arithmetic.operations"],
    related_points=["arithmetic.fraction_concept", "arithmetic.decimals"],
    code_examples=["arithmetic/fractions_course.py"],
    visualization_types=["area_model", "number_line"],
)


def get_fraction_knowledge_points() -> list:
    return [FRACTION_CONCEPT, FRACTION_OPS]


def get_fractions_lesson() -> Lesson:
    return Lesson(
        id="arithmetic.fractions.intro",
        title="Understanding Fractions",
        title_cn="分数的认识与运算",
        knowledge_points=[
            "arithmetic.fraction_concept",
            "arithmetic.fraction_operations",
        ],
        content_cn="""# 分数

## 1. 什么是分数？

分数表示一个整体被平均分成若干份后，取其中的几份。

**分数的组成：**
- **分子**（上面的数）：表示取了几份
- **分母**（下面的数）：表示平均分成了几份
- **分数线**：表示"除以"的意思

**生活中的例子：**
- 一个蛋糕切成8块，吃了3块，就是吃了 3/8
- 一小时有60分钟，15分钟是 15/60 = 1/4 小时
- 班级有40人，男生22人，男生占 22/40 = 11/20

## 2. 分数的基本性质

**分数的基本性质：** 分子和分母同时乘以或除以同一个不为0的数，分数的大小不变。

这就是**约分**和**通分**的基础：
- **约分**：分子分母同时除以它们的公因数
- **通分**：把不同分母的分数化成相同分母

## 3. 分数的运算

### 加减法
- 同分母：分子相加减，分母不变
- 异分母：先通分，再加减

### 乘法
- 分子乘分子，分母乘分母

### 除法
- 除以一个分数等于乘以它的倒数

## 4. 分数与小数、百分数的关系

| 分数 | 小数 | 百分数 |
|------|------|--------|
| 1/2 | 0.5 | 50% |
| 1/4 | 0.25 | 25% |
| 3/4 | 0.75 | 75% |
| 1/5 | 0.2 | 20% |
| 1/10 | 0.1 | 10% |
| 1/3 | 0.333... | 33.3% |
""",
        code_snippets=[
            {
                "title": "Fraction Operations",
                "title_cn": "分数运算",
                "code": """from fractions import Fraction

# 创建分数
a = Fraction(1, 3)  # 1/3
b = Fraction(1, 4)  # 1/4

print(f"a = {a}")
print(f"b = {b}")

# 加法（自动通分）
print(f"a + b = {a + b}")  # 7/12

# 减法
print(f"a - b = {a - b}")  # 1/12

# 乘法
print(f"a × b = {a * b}")  # 1/12

# 除法
print(f"a ÷ b = {a / b}")  # 4/3

# 约分
c = Fraction(12, 18)
print(f"12/18 约分后 = {c}")  # 2/3

# 转小数
print(f"1/3 = {float(a):.4f}")  # 0.3333""",
            },
            {
                "title": "Fraction Visualization",
                "title_cn": "分数可视化",
                "code": """from manim import *

class FractionVisualization(Scene):
    def construct(self):
        fractions = [(1, 2), (1, 3), (1, 4), (1, 6)]
        labels = ['1/2', '1/3', '1/4', '1/6']
        colors = [RED, TEAL, BLUE, GREEN]

        pies = VGroup()
        for i, (num, den) in enumerate(fractions):
            pie = VGroup()
            full_angle = 2 * np.pi
            filled_angle = full_angle * num / den
            sector = Sector(
                outer_radius=1.2,
                start_angle=90 * DEGREES,
                angle=-filled_angle,
                fill_color=colors[i],
                fill_opacity=0.7,
                stroke_color=WHITE,
            )
            remaining = Sector(
                outer_radius=1.2,
                start_angle=90 * DEGREES - filled_angle,
                angle=-(full_angle - filled_angle),
                fill_color=GREY,
                fill_opacity=0.3,
                stroke_color=WHITE,
            )
            pie.add(sector, remaining)
            label = Text(f"{labels[i]} = {num/den:.0%}", font_size=20).next_to(pie, DOWN, buff=0.3)
            pie.add(label)
            pies.add(pie)

        pies.arrange_in_grid(rows=2, cols=2, buff=1)
        title = Text("分数可视化", font_size=36).to_edge(UP)
        self.add(pies, title)""",
            },
        ],
        estimated_minutes=50,
    )
