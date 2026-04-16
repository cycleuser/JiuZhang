"""Advanced Mathematics course module - Topology, Abstract Algebra, Real Analysis."""

from jiuzhang.math_engine.curriculum import KnowledgePoint, Lesson


TOPOLOGY = KnowledgePoint(
    id="advanced.topology",
    name="Topology",
    name_cn="拓扑学",
    category="advanced",
    level="graduate",
    description="The study of properties preserved under continuous deformations",
    description_cn="研究在连续变形下保持不变的性质。拓扑学被称为'橡皮几何'。",
    prerequisites=["geometry.coordinate", "calculus.limits"],
    related_points=["advanced.real_analysis"],
    code_examples=["advanced/topology.py"],
    visualization_types=["mobius_strip", "torus", "knot_diagram"],
)

ABSTRACT_ALGEBRA = KnowledgePoint(
    id="advanced.abstract_algebra",
    name="Abstract Algebra",
    name_cn="抽象代数",
    category="advanced",
    level="undergraduate",
    description="The study of algebraic structures: groups, rings, and fields",
    description_cn="研究代数结构：群、环、域。抽象代数是现代数学的基础。",
    prerequisites=["linear_algebra.matrices"],
    related_points=["advanced.topology"],
    code_examples=["advanced/abstract_algebra.py"],
    visualization_types=["cayley_table", "group_visualization"],
)

REAL_ANALYSIS = KnowledgePoint(
    id="advanced.real_analysis",
    name="Real Analysis",
    name_cn="实分析",
    category="advanced",
    level="undergraduate",
    description="Rigorous study of real numbers, sequences, series, and functions",
    description_cn="对实数、序列、级数和函数的严格研究。是微积分的理论基础。",
    prerequisites=["calculus.limits", "calculus.integrals"],
    related_points=["advanced.topology", "advanced.abstract_algebra"],
    code_examples=["advanced/real_analysis.py"],
    visualization_types=["epsilon_delta", "convergence_plot"],
)

FOURIER = KnowledgePoint(
    id="advanced.fourier",
    name="Fourier Analysis",
    name_cn="傅里叶分析",
    category="advanced",
    level="undergraduate",
    description="Decomposing functions into sums of sinusoidal components",
    description_cn="将函数分解为正弦函数的和。傅里叶变换在信号处理中有广泛应用。",
    prerequisites=["calculus.integrals", "geometry.trigonometry"],
    related_points=["advanced.real_analysis"],
    code_examples=["advanced/fourier.py"],
    visualization_types=["fourier_series", "frequency_spectrum"],
)


def get_advanced_knowledge_points() -> list:
    return [TOPOLOGY, ABSTRACT_ALGEBRA, REAL_ANALYSIS, FOURIER]


def get_advanced_lesson() -> Lesson:
    return Lesson(
        id="advanced.intro",
        title="Frontier Mathematics",
        title_cn="前沿数学概览",
        knowledge_points=[
            "advanced.topology",
            "advanced.abstract_algebra",
            "advanced.fourier",
        ],
        content_cn="""# 前沿数学概览

## 1. 拓扑学

**什么是拓扑学？**
拓扑学研究图形在连续变形（拉伸、压缩、弯曲，但不撕裂或粘合）下保持不变的性质。

**经典例子：**
- 咖啡杯和甜甜圈在拓扑学中等价（都有一个洞）
- 莫比乌斯带：只有一个面和一个边
- 克莱因瓶：没有内外之分的曲面

**基本概念：**
- 开集、闭集
- 连通性
- 紧致性
- 同胚

**应用：**
- 数据分析（拓扑数据分析 TDA）
- 物理学（拓扑绝缘体）
- 计算机科学（网络拓扑）

## 2. 抽象代数

**群 (Group)：**
一个集合配上一种运算，满足：
1. 封闭性
2. 结合律
3. 单位元
4. 逆元

**例子：** 整数加法群 (Z, +)

**环 (Ring)：**
一个集合配上两种运算（加法和乘法），满足更多性质。

**例子：** 整数环 (Z, +, ×)

**域 (Field)：**
环的进一步推广，每个非零元素都有乘法逆元。

**例子：** 有理数域 Q，实数域 R

**应用：**
- 密码学（RSA、椭圆曲线）
- 编码理论
- 量子力学

## 3. 傅里叶分析

**核心思想：**
任何周期函数都可以表示为正弦函数的和。

**傅里叶级数：**
f(x) = a₀/2 + Σ[aₙcos(nx) + bₙsin(nx)]

**傅里叶变换：**
F(ω) = ∫ f(t)e^(-iωt) dt

**应用：**
- 信号处理
- 图像处理（JPEG压缩）
- 量子力学
- 热传导

## 4. 现代数学前沿

- **代数几何**：用代数方法研究几何对象
- **微分几何**：用微积分研究曲线和曲面
- **数论**：研究整数的性质（黎曼猜想）
- **拓扑学**：研究空间的本质性质
- **范畴论**：数学的"数学"，研究结构之间的关系
""",
        code_snippets=[
            {
                "title": "Fourier Series Demo",
                "title_cn": "傅里叶级数演示",
                "code": """import numpy as np
import matplotlib.pyplot as plt

# 方波的傅里叶级数近似
def square_wave_fourier(x, n_terms):
    result = np.zeros_like(x)
    for n in range(1, n_terms + 1, 2):
        result += (4 / (n * np.pi)) * np.sin(n * x)
    return result

x = np.linspace(-2*np.pi, 2*np.pi, 1000)

fig, axes = plt.subplots(2, 2, figsize=(10, 8))
terms = [1, 3, 7, 21]

for i, n in enumerate(terms):
    ax = axes[i // 2, i % 2]
    y = square_wave_fourier(x, n)
    ax.plot(x, y, linewidth=1.5)
    ax.set_title(f'{n} 项')
    ax.set_ylim(-1.5, 1.5)
    ax.grid(True, alpha=0.3)

plt.suptitle('方波的傅里叶级数近似')
plt.tight_layout()
plt.show()""",
            },
            {
                "title": "Group Theory Demo",
                "title_cn": "群论演示",
                "code": """# 模5加法群 Z₅
elements = [0, 1, 2, 3, 4]

print("模5加法表 (Z₅):")
print("  |", " ".join(f"{e:2}" for e in elements))
print("--|" + "---" * 5)
for a in elements:
    row = [f"{(a+b)%5:2}" for b in elements]
    print(f"{a} | {' '.join(row)}")

# 验证群的性质
print("\\n验证群的性质:")
print(f"封闭性: 所有结果都在 {{0,1,2,3,4}} 中 ✓")
print(f"结合律: (a+b)+c = a+(b+c) mod 5 ✓")
print(f"单位元: 0 ✓")
print(f"逆元: 0→0, 1→4, 2→3, 3→2, 4→1 ✓")""",
            },
        ],
        estimated_minutes=120,
    )
