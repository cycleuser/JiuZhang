"""Geometry course module - Plane geometry, triangles, circles, and trigonometry."""

from jiuzhang.math_engine.curriculum import KnowledgePoint, Lesson


TRIANGLES = KnowledgePoint(
    id="geometry.triangles",
    name="Triangles",
    name_cn="三角形",
    category="geometry",
    level="middle_school",
    description="A polygon with three edges and three vertices. Sum of interior angles is 180°",
    description_cn="由三条线段首尾相连组成的图形。三角形内角和等于180°。",
    prerequisites=["arithmetic.operations"],
    related_points=["geometry.pythagorean", "geometry.trigonometry"],
    code_examples=["geometry/triangles.py"],
    visualization_types=["triangle_plot", "angle_visualization"],
)

PYTHAGOREAN = KnowledgePoint(
    id="geometry.pythagorean",
    name="Pythagorean Theorem",
    name_cn="勾股定理",
    category="geometry",
    level="middle_school",
    description="In a right triangle, a² + b² = c² where c is the hypotenuse",
    description_cn="直角三角形中，两条直角边的平方和等于斜边的平方：a² + b² = c²",
    prerequisites=["geometry.triangles"],
    related_points=["geometry.triangles", "geometry.trigonometry"],
    code_examples=["geometry/pythagorean.py"],
    visualization_types=["right_triangle", "square_areas"],
)

CIRCLES = KnowledgePoint(
    id="geometry.circles",
    name="Circles",
    name_cn="圆",
    category="geometry",
    level="middle_school",
    description="A shape consisting of all points in a plane that are at a given distance from a center",
    description_cn="平面上到定点（圆心）距离等于定长（半径）的所有点的集合。",
    prerequisites=["arithmetic.operations"],
    related_points=["geometry.triangles", "geometry.trigonometry"],
    code_examples=["geometry/circles.py"],
    visualization_types=["circle_plot", "pi_visualization"],
)

TRIGONOMETRY = KnowledgePoint(
    id="geometry.trigonometry",
    name="Trigonometry",
    name_cn="三角函数",
    category="geometry",
    level="high_school",
    description="Functions relating angles to ratios of sides in right triangles: sin, cos, tan",
    description_cn="研究角度与直角三角形边长比之间关系的函数：正弦(sin)、余弦(cos)、正切(tan)。",
    prerequisites=["geometry.pythagorean", "geometry.triangles"],
    related_points=["geometry.circles", "algebra.functions"],
    code_examples=["geometry/trigonometry.py"],
    visualization_types=["unit_circle", "wave_plot", "triangle_visualization"],
)

COORDINATE_GEOMETRY = KnowledgePoint(
    id="geometry.coordinate",
    name="Coordinate Geometry",
    name_cn="解析几何",
    category="geometry",
    level="high_school",
    description="Using coordinates to represent and analyze geometric figures",
    description_cn="用坐标表示点，用方程表示曲线，用代数方法研究几何问题。",
    prerequisites=["algebra.functions", "geometry.triangles"],
    related_points=["geometry.triangles", "algebra.linear_functions"],
    code_examples=["geometry/coordinate.py"],
    visualization_types=["coordinate_plane", "line_plot", "conic_sections"],
)


def get_geometry_knowledge_points() -> list:
    return [TRIANGLES, PYTHAGOREAN, CIRCLES, TRIGONOMETRY, COORDINATE_GEOMETRY]


def get_triangles_lesson() -> Lesson:
    return Lesson(
        id="geometry.triangles.intro",
        title="Triangles and Pythagorean Theorem",
        title_cn="三角形与勾股定理",
        knowledge_points=["geometry.triangles", "geometry.pythagorean"],
        content_cn="""# 三角形与勾股定理

## 1. 三角形的基本性质

**定义：** 由三条线段首尾顺次连接组成的封闭图形。

**基本性质：**
- 三角形内角和 = 180°
- 任意两边之和大于第三边
- 任意两边之差小于第三边

**三角形的分类：**

按角分：
- 锐角三角形：三个角都小于90°
- 直角三角形：有一个角等于90°
- 钝角三角形：有一个角大于90°

按边分：
- 不等边三角形：三条边都不相等
- 等腰三角形：有两条边相等
- 等边三角形：三条边都相等（每个角60°）

**面积公式：**
- S = ½ × 底 × 高
- S = ½ × a × b × sin(C)

## 2. 勾股定理

**定理：** 在直角三角形中，两条直角边的平方和等于斜边的平方。

**公式：** a² + b² = c²

其中 c 是斜边（直角所对的边），a 和 b 是两条直角边。

**历史：**
- 中国：商高发现"勾三股四弦五"
- 希腊：毕达哥拉斯证明了这个定理
- 全世界有超过400种证明方法！

**常见勾股数：**
- (3, 4, 5)
- (5, 12, 13)
- (8, 15, 17)
- (7, 24, 25)

**应用：**
- 已知两边求第三边
- 判断三角形是否为直角三角形
- 计算距离

**例子：**
直角三角形，a = 3, b = 4，求 c
c² = 3² + 4² = 9 + 16 = 25
c = √25 = 5
""",
        code_snippets=[
            {
                "title": "Pythagorean Theorem",
                "title_cn": "勾股定理计算",
                "code": """import math

def pythagorean(a, b=None, c=None):
    if b is None:
        b = math.sqrt(c**2 - a**2)
        return f"a={a}, b={b:.2f}, c={c}"
    if c is None:
        c = math.sqrt(a**2 + b**2)
        return f"a={a}, b={b}, c={c:.2f}"
    return "请只提供两个值"

print(pythagorean(3, 4))   # 求斜边
print(pythagorean(5, c=13)) # 求另一条直角边

# 验证勾股数
triples = [(3, 4, 5), (5, 12, 13), (8, 15, 17)]
for a, b, c in triples:
    check = a**2 + b**2 == c**2
    print(f"({a}, {b}, {c}): {check}")""",
            },
            {
                "title": "Triangle Visualization",
                "title_cn": "三角形可视化",
                "code": """from manim import *

class TriangleVisualization(Scene):
    def construct(self):
        right_tri = Polygon(
            [-2, -1, 0], [1, -1, 0], [-2, 2, 0],
            color=BLUE,
        ).shift(LEFT * 4)
        right_label = Text("直角三角形 (3,4,5)", font_size=20).next_to(right_tri, DOWN)

        h = np.sqrt(3) / 2
        equi_tri = Polygon(
            [-0.5, -0.5, 0], [0.5, -0.5, 0], [0, h - 0.5, 0],
            color=GREEN,
        )
        equi_label = Text("等边三角形", font_size=20).next_to(equi_tri, DOWN)

        a, b = 3, 4
        sq_a = Square(side_length=0.6).set_color(RED).shift(LEFT * 1.5 + DOWN * 0.5)
        sq_b = Square(side_length=0.8).set_color(GREEN).next_to(sq_a, RIGHT, buff=0.1, aligned_edge=DOWN)
        pyth_label = MathTex("a^2 + b^2 = c^2", font_size=28).next_to(VGroup(sq_a, sq_b), DOWN)

        right_group = VGroup(right_tri, right_label)
        equi_group = VGroup(equi_tri, equi_label)
        pyth_group = VGroup(sq_a, sq_b, pyth_label)

        groups = VGroup(right_group, equi_group, pyth_group).arrange(RIGHT, buff=1)
        title = Text("三角形与勾股定理", font_size=36).to_edge(UP)
        self.add(groups, title)""",
            },
        ],
        estimated_minutes=75,
    )


def get_trigonometry_lesson() -> Lesson:
    return Lesson(
        id="geometry.trigonometry.intro",
        title="Introduction to Trigonometry",
        title_cn="三角函数入门",
        knowledge_points=["geometry.trigonometry"],
        content_cn="""# 三角函数

## 1. 什么是三角函数？

三角函数是角度与直角三角形边长比之间的关系。

**三个基本函数：**
- **正弦 sin(θ)** = 对边 / 斜边
- **余弦 cos(θ)** = 邻边 / 斜边
- **正切 tan(θ)** = 对边 / 邻边 = sin(θ) / cos(θ)

**记忆口诀：**
- SOH: Sin = Opposite / Hypotenuse
- CAH: Cos = Adjacent / Hypotenuse
- TOA: Tan = Opposite / Adjacent

## 2. 特殊角度的三角函数值

| 角度 | 0° | 30° | 45° | 60° | 90° |
|------|-----|------|------|------|------|
| 弧度 | 0 | π/6 | π/4 | π/3 | π/2 |
| sin | 0 | 1/2 | √2/2 | √3/2 | 1 |
| cos | 1 | √3/2 | √2/2 | 1/2 | 0 |
| tan | 0 | √3/3 | 1 | √3 | 不存在 |

## 3. 三角函数的图像

- **sin(x)**：周期 2π，振幅 1，从原点开始
- **cos(x)**：周期 2π，振幅 1，从最大值开始
- **tan(x)**：周期 π，有渐近线

## 4. 重要公式

**基本恒等式：**
- sin²(θ) + cos²(θ) = 1
- tan(θ) = sin(θ) / cos(θ)

**和角公式：**
- sin(A ± B) = sinA·cosB ± cosA·sinB
- cos(A ± B) = cosA·cosB ∓ sinA·sinB

**倍角公式：**
- sin(2θ) = 2sin(θ)cos(θ)
- cos(2θ) = cos²(θ) - sin²(θ)
""",
        code_snippets=[
            {
                "title": "Trigonometric Functions",
                "title_cn": "三角函数计算",
                "code": """import numpy as np

# 特殊角度的三角函数值
angles = [0, 30, 45, 60, 90]

print("角度 | sin | cos | tan")
print("-" * 35)
for deg in angles:
    rad = np.radians(deg)
    s = np.sin(rad)
    c = np.cos(rad)
    t = np.tan(rad) if deg != 90 else "∞"
    print(f"{deg:4°} | {s:.4f} | {c:.4f} | {t if isinstance(t, str) else f'{t:.4f}'}")

# 验证 sin² + cos² = 1
print("\\n验证 sin²(θ) + cos²(θ) = 1:")
for deg in [30, 45, 60]:
    rad = np.radians(deg)
    result = np.sin(rad)**2 + np.cos(rad)**2
    print(f"  {deg°}: {result:.10f}")""",
            },
            {
                "title": "Trig Function Plots",
                "title_cn": "三角函数图像",
                "code": """from manim import *

class TrigFunctionPlots(Scene):
    def construct(self):
        axes = Axes(
            x_range=[0, 2 * np.pi, np.pi / 2],
            y_range=[-4, 4, 1],
            x_length=10,
            y_length=5,
            axis_config={"color": GREY},
        ).add_coordinates()

        x_labels = {
            0: "0", np.pi / 2: "\\pi/2", np.pi: "\\pi",
            3 * np.pi / 2: "3\\pi/2", 2 * np.pi: "2\\pi",
        }
        for val, label in x_labels.items():
            axes.x_labels.add(MathTex(label, font_size=24).next_to(axes.c2p(val, 0), DOWN, buff=0.2))

        self.add(axes)

        sin_curve = axes.plot(lambda x: np.sin(x), color=BLUE, x_range=[0, 2 * np.pi])
        cos_curve = axes.plot(lambda x: np.cos(x), color=RED, x_range=[0, 2 * np.pi])
        tan_curve = axes.plot(lambda x: np.tan(x), color=GREEN, x_range=[0.1, np.pi / 2 - 0.1])

        sin_label = MathTex("\\sin(x)", color=BLUE, font_size=28).next_to(sin_curve, UR, buff=0.1)
        cos_label = MathTex("\\cos(x)", color=RED, font_size=28).next_to(cos_curve, UR, buff=0.1)
        tan_label = MathTex("\\tan(x)", color=GREEN, font_size=28).next_to(tan_curve, UR, buff=0.1)

        self.add(sin_curve, cos_curve, tan_curve, sin_label, cos_label, tan_label)

        title = Text("三角函数图像", font_size=36).to_edge(UP)
        self.add(title)""",
            },
        ],
        estimated_minutes=90,
    )
