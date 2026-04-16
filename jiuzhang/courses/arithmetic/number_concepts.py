"""Arithmetic course - Number concepts.

Covers natural numbers, integers, fractions, decimals, and real numbers.
"""

from jiuzhang.math_engine.curriculum import KnowledgePoint, Lesson

# Knowledge Points - Number Concepts
NATURAL_NUMBERS = KnowledgePoint(
    id="arithmetic.natural_numbers",
    name="Natural Numbers",
    name_cn="自然数",
    category="arithmetic",
    level="elementary",
    description="The set of counting numbers starting from 0 or 1: {0, 1, 2, 3, ...} or {1, 2, 3, ...}",
    description_cn="用来计数的数，从0或1开始：{0, 1, 2, 3, ...}。自然数是最基本的数，用于表示物体的个数。",
    prerequisites=[],
    related_points=["arithmetic.integers", "arithmetic.operations"],
    code_examples=["arithmetic/natural_numbers.py"],
    visualization_types=["number_line", "counting_objects"],
)

INTEGERS = KnowledgePoint(
    id="arithmetic.integers",
    name="Integers",
    name_cn="整数",
    category="arithmetic",
    level="elementary",
    description="The set of whole numbers including negative numbers: {..., -3, -2, -1, 0, 1, 2, 3, ...}",
    description_cn="包括正整数、零和负整数的数集：{..., -3, -2, -1, 0, 1, 2, 3, ...}。整数可以表示相反意义的量。",
    prerequisites=["arithmetic.natural_numbers"],
    related_points=["arithmetic.natural_numbers", "arithmetic.rational_numbers"],
    code_examples=["arithmetic/integers.py"],
    visualization_types=["number_line", "temperature_scale"],
)

FRACTIONS = KnowledgePoint(
    id="arithmetic.fractions",
    name="Fractions",
    name_cn="分数",
    category="arithmetic",
    level="elementary",
    description="A number expressed as a ratio of two integers: a/b where b ≠ 0",
    description_cn="用两个整数的比表示的数：a/b，其中b≠0。分数表示一个整体被平均分成若干份后取其中的几份。",
    prerequisites=["arithmetic.natural_numbers", "arithmetic.division"],
    related_points=["arithmetic.decimals", "arithmetic.rational_numbers"],
    code_examples=["arithmetic/fractions.py"],
    visualization_types=["pie_chart", "number_line", "bar_model"],
)

DECIMALS = KnowledgePoint(
    id="arithmetic.decimals",
    name="Decimals",
    name_cn="小数",
    category="arithmetic",
    level="elementary",
    description="A number expressed in base-10 notation with a decimal point",
    description_cn="用十进制表示的数，包含小数点。小数是分数的另一种表示方法。",
    prerequisites=["arithmetic.natural_numbers", "arithmetic.fractions"],
    related_points=["arithmetic.fractions", "arithmetic.real_numbers"],
    code_examples=["arithmetic/decimals.py"],
    visualization_types=["number_line", "place_value_chart"],
)

REAL_NUMBERS = KnowledgePoint(
    id="arithmetic.real_numbers",
    name="Real Numbers",
    name_cn="实数",
    category="arithmetic",
    level="middle_school",
    description="All rational and irrational numbers, representing every point on the number line",
    description_cn="有理数和无理数的统称，数轴上的每一个点都对应一个实数。",
    prerequisites=["arithmetic.fractions", "arithmetic.decimals"],
    related_points=["arithmetic.rational_numbers", "algebra.irrational_numbers"],
    code_examples=["arithmetic/real_numbers.py"],
    visualization_types=["number_line", "density_plot"],
)


def get_arithmetic_knowledge_points() -> list:
    return [NATURAL_NUMBERS, INTEGERS, FRACTIONS, DECIMALS, REAL_NUMBERS]


def get_number_concepts_lesson() -> Lesson:
    return Lesson(
        id="arithmetic.number_concepts.intro",
        title="Introduction to Numbers",
        title_cn="数的概念入门",
        knowledge_points=[
            "arithmetic.natural_numbers",
            "arithmetic.integers",
            "arithmetic.fractions",
            "arithmetic.decimals",
        ],
        content_cn="""# 数的概念

## 1. 自然数

自然数是我们最先认识的数。当你数苹果时：1个、2个、3个...这些就是自然数。

**生活中的例子：**
- 家里有几个人？
- 书包里有几本书？
- 天上有几颗星星？（虽然数不清，但也是自然数！）

**数学定义：** 自然数集 N = {0, 1, 2, 3, 4, 5, ...}

## 2. 整数

如果自然数只能表示"有"，那"欠"怎么表示呢？这就需要整数了。

**生活中的例子：**
- 温度：零上5度是+5，零下5度是-5
- 钱：赚了100元是+100，亏了50元是-50
- 楼层：地上3层是+3，地下2层是-2

**数学定义：** 整数集 Z = {..., -3, -2, -1, 0, 1, 2, 3, ...}

## 3. 分数

把一个蛋糕平均分给4个人，每人得到多少？这就需要分数。

**生活中的例子：**
- 一块披萨切成8份，吃了3份，就是吃了 3/8
- 考试得了85分（满分100），就是得了 85/100 = 17/20

**数学定义：** 分数 a/b，其中a、b是整数，b≠0

## 4. 小数

小数是分数的另一种写法。1/2 = 0.5，1/4 = 0.25

**生活中的例子：**
- 身高：1.65米
- 价格：9.99元
- 体重：45.5公斤

## 关键要点

1. 数的范围是逐渐扩大的：自然数 → 整数 → 有理数 → 实数
2. 每种数都是为了解决实际问题而发明的
3. 数轴上每一个点都对应一个实数
""",
        code_snippets=[
            {
                "title": "自然数操作",
                "title_cn": "自然数操作",
                "code": """# 自然数的基本操作
natural_numbers = list(range(0, 11))  # 0到10的自然数
print(f"自然数: {natural_numbers}")
print(f"前5个自然数的和: {sum(natural_numbers[:5])}")
print(f"自然数的个数: {len(natural_numbers)}")""",
            },
            {
                "title": "整数数轴",
                "title_cn": "整数数轴可视化",
                "code": """import numpy as np
import matplotlib.pyplot as plt

# 创建数轴
fig, ax = plt.subplots(figsize=(10, 2))
ax.set_xlim(-6, 6)
ax.set_ylim(-1, 1)
ax.axhline(y=0, color='black', linewidth=2)

for x in range(-5, 6):
    ax.plot([x, x], [-0.1, 0.1], color='black')
    ax.text(x, -0.3, str(x), ha='center', fontsize=10)

ax.set_title('整数数轴')
ax.axis('off')
plt.show()""",
            },
        ],
        estimated_minutes=45,
    )
