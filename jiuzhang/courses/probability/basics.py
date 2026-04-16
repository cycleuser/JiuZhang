"""Probability and Statistics course module."""

from jiuzhang.math_engine.curriculum import KnowledgePoint, Lesson


PROBABILITY_BASICS = KnowledgePoint(
    id="probability.basics",
    name="Probability Basics",
    name_cn="概率基础",
    category="probability",
    level="middle_school",
    description="The study of randomness and chance. P(A) = favorable outcomes / total outcomes",
    description_cn="研究随机现象的规律。P(A) = 有利结果数 / 总结果数",
    prerequisites=["arithmetic.fractions"],
    related_points=["probability.combinatorics", "statistics.descriptive"],
    code_examples=["probability/basics.py"],
    visualization_types=["probability_tree", "bar_chart", "pie_chart"],
)

COMBINATORICS = KnowledgePoint(
    id="probability.combinatorics",
    name="Combinatorics",
    name_cn="排列组合",
    category="probability",
    level="high_school",
    description="Counting techniques: permutations and combinations",
    description_cn="计数原理：排列（有序）和组合（无序）。",
    prerequisites=["probability.basics"],
    related_points=["probability.basics", "probability.distributions"],
    code_examples=["probability/combinatorics.py"],
    visualization_types=["tree_diagram", "pascal_triangle"],
)

DISTRIBUTIONS = KnowledgePoint(
    id="probability.distributions",
    name="Probability Distributions",
    name_cn="概率分布",
    category="probability",
    level="high_school",
    description="Functions describing the probability of different outcomes",
    description_cn="描述随机变量各种可能结果及其对应概率的函数。",
    prerequisites=["probability.combinatorics"],
    related_points=["statistics.descriptive", "calculus.integrals"],
    code_examples=["probability/distributions.py"],
    visualization_types=["histogram", "pdf_plot", "cdf_plot"],
)

DESCRIPTIVE_STATS = KnowledgePoint(
    id="statistics.descriptive",
    name="Descriptive Statistics",
    name_cn="描述统计",
    category="probability",
    level="middle_school",
    description="Methods for summarizing and describing data: mean, median, mode, variance",
    description_cn="用数值和图表描述数据特征的方法：平均数、中位数、众数、方差。",
    prerequisites=["arithmetic.operations"],
    related_points=["probability.basics", "probability.distributions"],
    code_examples=["statistics/descriptive.py"],
    visualization_types=["histogram", "box_plot", "scatter_plot"],
)


def get_probability_knowledge_points() -> list:
    return [PROBABILITY_BASICS, COMBINATORICS, DISTRIBUTIONS, DESCRIPTIVE_STATS]


def get_probability_lesson() -> Lesson:
    return Lesson(
        id="probability.intro",
        title="Probability and Statistics",
        title_cn="概率与统计",
        knowledge_points=["probability.basics", "statistics.descriptive"],
        content_cn="""# 概率与统计

## 1. 概率基础

**什么是概率？**
概率是衡量一个事件发生可能性大小的数值，范围是 0 到 1。
- P = 0：不可能发生
- P = 1：必然发生
- 0 < P < 1：可能发生

**计算公式：**
P(A) = 事件A包含的结果数 / 所有可能的结果数

**例子：**
- 掷硬币正面朝上：P = 1/2 = 0.5
- 掷骰子得到6：P = 1/6 ≈ 0.167
- 从52张牌中抽到红桃A：P = 1/52 ≈ 0.019

**概率的性质：**
1. 0 ≤ P(A) ≤ 1
2. P(必然事件) = 1
3. P(不可能事件) = 0
4. P(A) + P(非A) = 1

## 2. 描述统计

**集中趋势：**
- **平均数**：所有数据之和除以数据个数
- **中位数**：排序后位于中间的数
- **众数**：出现次数最多的数

**离散程度：**
- **极差**：最大值 - 最小值
- **方差**：各数据与平均数差的平方的平均
- **标准差**：方差的平方根

**例子：** 数据 [2, 4, 4, 6, 8]
- 平均数 = (2+4+4+6+8)/5 = 4.8
- 中位数 = 4
- 众数 = 4
- 极差 = 8 - 2 = 6
- 方差 = [(2-4.8)² + (4-4.8)² + ...] / 5 = 4.16
- 标准差 = √4.16 ≈ 2.04
""",
        code_snippets=[
            {
                "title": "Probability Simulation",
                "title_cn": "概率模拟",
                "code": """import random

# 模拟掷硬币
def coin_flip(n=1000):
    heads = sum(1 for _ in range(n) if random.random() < 0.5)
    return heads / n

print(f"掷硬币1000次，正面概率: {coin_flip(1000):.3f}")

# 模拟掷骰子
def dice_roll(n=1000):
    counts = {i: 0 for i in range(1, 7)}
    for _ in range(n):
        counts[random.randint(1, 6)] += 1
    return {k: v/n for k, v in counts.items()}

print(f"掷骰子1000次: {dice_roll(1000)}")

# 蒙特卡洛方法估算π
def estimate_pi(n=10000):
    inside = 0
    for _ in range(n):
        x, y = random.random(), random.random()
        if x**2 + y**2 <= 1:
            inside += 1
    return 4 * inside / n

print(f"蒙特卡洛估算π: {estimate_pi():.4f}")""",
            },
            {
                "title": "Descriptive Statistics",
                "title_cn": "描述统计",
                "code": """import numpy as np

data = [2, 4, 4, 6, 8, 10, 12]

print(f"数据: {data}")
print(f"平均数: {np.mean(data):.2f}")
print(f"中位数: {np.median(data):.2f}")
print(f"众数: {max(set(data), key=data.count)}")
print(f"极差: {max(data) - min(data)}")
print(f"方差: {np.var(data):.2f}")
print(f"标准差: {np.std(data):.2f}")

# 使用 scipy
from scipy import stats
print(f"\\nscipy 统计:")
print(f"偏度: {stats.skew(data):.2f}")
print(f"峰度: {stats.kurtosis(data):.2f}")""",
            },
        ],
        estimated_minutes=75,
    )
