"""Decimals course module.

Covers decimal concepts, operations, and conversions.
"""

from jiuzhang.math_engine.curriculum import KnowledgePoint, Lesson


DECIMAL_CONCEPT = KnowledgePoint(
    id="arithmetic.decimal_concept",
    name="Decimal Concept",
    name_cn="小数概念",
    category="arithmetic",
    level="elementary",
    description="A number expressed in base-10 notation with a decimal point separating whole and fractional parts",
    description_cn="用十进制表示的数，小数点左边是整数部分，右边是小数部分。",
    prerequisites=["arithmetic.fraction_concept"],
    related_points=["arithmetic.fractions", "arithmetic.real_numbers"],
    code_examples=["arithmetic/decimals_course.py"],
    visualization_types=["place_value_chart", "number_line"],
)

DECIMAL_OPS = KnowledgePoint(
    id="arithmetic.decimal_operations",
    name="Decimal Operations",
    name_cn="小数运算",
    category="arithmetic",
    level="elementary",
    description="Addition, subtraction, multiplication, and division of decimals",
    description_cn="小数的加减乘除运算。注意小数点的位置。",
    prerequisites=["arithmetic.decimal_concept", "arithmetic.operations"],
    related_points=["arithmetic.decimal_concept", "arithmetic.fraction_operations"],
    code_examples=["arithmetic/decimals_course.py"],
    visualization_types=["number_line", "bar_chart"],
)


def get_decimal_knowledge_points() -> list:
    return [DECIMAL_CONCEPT, DECIMAL_OPS]


def get_decimals_lesson() -> Lesson:
    return Lesson(
        id="arithmetic.decimals.intro",
        title="Understanding Decimals",
        title_cn="小数的认识与运算",
        knowledge_points=[
            "arithmetic.decimal_concept",
            "arithmetic.decimal_operations",
        ],
        content_cn="""# 小数

## 1. 什么是小数？

小数是分数的另一种表示方法。小数点把数分成两部分：
- **整数部分**（小数点左边）
- **小数部分**（小数点右边）

**位值表：**

| 百位 | 十位 | 个位 | . | 十分位 | 百分位 | 千分位 |
|------|------|------|---|--------|--------|--------|
| 100  | 10   | 1    | . | 0.1    | 0.01   | 0.001  |

**生活中的例子：**
- 身高：1.65 米 = 1米65厘米
- 价格：9.99 元
- 体重：45.5 公斤
- 温度：36.5°C

## 2. 小数与分数的转换

**小数转分数：**
- 0.5 = 5/10 = 1/2
- 0.25 = 25/100 = 1/4
- 0.75 = 75/100 = 3/4
- 0.2 = 2/10 = 1/5

**分数转小数：**
- 1/2 = 0.5
- 1/3 = 0.333...（循环小数）
- 1/4 = 0.25
- 2/3 = 0.666...（循环小数）

## 3. 小数的运算

### 加减法
小数点对齐，按位相加减。

### 乘法
先按整数乘法计算，再数出两个因数共有几位小数，就在积中从右往左数出几位，点上小数点。

### 除法
移动除数的小数点使它变成整数，被除数的小数点也向右移动相同的位数。

## 4. 循环小数

有些分数化成小数时，小数部分会无限重复，这就是循环小数。
- 1/3 = 0.333... = 0.3̇
- 1/7 = 0.142857142857... = 0.1̇42857̇
""",
        code_snippets=[
            {
                "title": "Decimal Operations",
                "title_cn": "小数运算",
                "code": """# 小数运算
a, b = 3.14, 2.5

print(f"加法: {a} + {b} = {a + b}")
print(f"减法: {a} - {b} = {a - b}")
print(f"乘法: {a} × {b} = {a * b}")
print(f"除法: {a} ÷ {b} = {a / b}")

# 浮点数精度问题
print(f"0.1 + 0.2 = {0.1 + 0.2}")  # 0.30000000000000004

# 使用 Decimal 精确计算
from decimal import Decimal, getcontext
getcontext().prec = 10

x = Decimal('0.1')
y = Decimal('0.2')
print(f"精确计算: {x} + {y} = {x + y}")  # 0.3""",
            },
            {
                "title": "Decimal to Fraction",
                "title_cn": "小数与分数转换",
                "code": """from fractions import Fraction
from decimal import Decimal

# 小数转分数
decimals = [0.5, 0.25, 0.75, 0.2, 0.125, 0.333]

print("小数 → 分数:")
for d in decimals:
    frac = Fraction(d).limit_denominator(100)
    print(f"  {d} ≈ {frac}")

# 分数转小数
fractions = [(1, 2), (1, 3), (1, 4), (1, 7)]

print("\\n分数 → 小数:")
for num, den in fractions:
    dec = num / den
    print(f"  {num}/{den} = {dec:.6f}")""",
            },
        ],
        estimated_minutes=45,
    )
