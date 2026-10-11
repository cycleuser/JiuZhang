"""Arithmetic operations - Addition, Subtraction, Multiplication, Division.

Covers the four basic operations with code examples and visualizations.
"""

from jiuzhang.math_engine.curriculum import KnowledgePoint, Lesson

ADDITION = KnowledgePoint(
    id="arithmetic.addition",
    name="Addition",
    name_cn="加法",
    category="arithmetic",
    level="elementary",
    description="Combining two or more numbers to get their sum. a + b = c",
    description_cn="把两个或多个数合并，得到它们的和。a + b = c。加法是最基本的运算之一。",
    prerequisites=["arithmetic.natural_numbers"],
    related_points=["arithmetic.subtraction", "arithmetic.multiplication"],
    code_examples=["arithmetic/operations.py"],
    visualization_types=["number_line", "bar_chart", "counting_objects"],
)

SUBTRACTION = KnowledgePoint(
    id="arithmetic.subtraction",
    name="Subtraction",
    name_cn="减法",
    category="arithmetic",
    level="elementary",
    description="Finding the difference between numbers. a - b = c",
    description_cn="求两个数之间的差。a - b = c。减法是加法的逆运算。",
    prerequisites=["arithmetic.addition"],
    related_points=["arithmetic.addition", "arithmetic.negative_numbers"],
    code_examples=["arithmetic/operations.py"],
    visualization_types=["number_line", "bar_chart"],
)

MULTIPLICATION = KnowledgePoint(
    id="arithmetic.multiplication",
    name="Multiplication",
    name_cn="乘法",
    category="arithmetic",
    level="elementary",
    description="Repeated addition. a × b = c, meaning adding a, b times",
    description_cn="重复的加法。a × b = c，表示把 a 加 b 次。乘法是加法的简便运算。",
    prerequisites=["arithmetic.addition"],
    related_points=["arithmetic.division", "arithmetic.addition"],
    code_examples=["arithmetic/operations.py"],
    visualization_types=["grid", "area_model", "number_line"],
)

DIVISION = KnowledgePoint(
    id="arithmetic.division",
    name="Division",
    name_cn="除法",
    category="arithmetic",
    level="elementary",
    description="Splitting a number into equal parts. a ÷ b = c",
    description_cn="把一个数分成相等的几份。a ÷ b = c。除法是乘法的逆运算。",
    prerequisites=["arithmetic.multiplication"],
    related_points=["arithmetic.multiplication", "arithmetic.fractions"],
    code_examples=["arithmetic/operations.py"],
    visualization_types=["grouping", "number_line", "bar_chart"],
)

OPERATION_LAWS = KnowledgePoint(
    id="arithmetic.operation_laws",
    name="Operation Laws",
    name_cn="运算律",
    category="arithmetic",
    level="elementary",
    description="Commutative, associative, and distributive laws of operations",
    description_cn="交换律、结合律、分配律。这些运算律帮助我们简化和理解计算。",
    prerequisites=["arithmetic.addition", "arithmetic.multiplication"],
    related_points=[
        "arithmetic.addition",
        "arithmetic.multiplication",
        "algebra.expressions",
    ],
    code_examples=["arithmetic/operations.py"],
    visualization_types=["area_model", "number_line"],
)


def get_operations_knowledge_points() -> list:
    return [ADDITION, SUBTRACTION, MULTIPLICATION, DIVISION, OPERATION_LAWS]


def get_operations_lesson() -> Lesson:
    return Lesson(
        id="arithmetic.operations.intro",
        title="Four Basic Operations",
        title_cn="四则运算",
        knowledge_points=[
            "arithmetic.addition",
            "arithmetic.subtraction",
            "arithmetic.multiplication",
            "arithmetic.division",
            "arithmetic.operation_laws",
        ],
        content_cn="""# 四则运算

## 1. 加法 (+)

加法是最基本的运算。把两个数合在一起，得到总和。

**生活中的例子：**
- 你有3个苹果，妈妈又给了你2个，现在有几个？3 + 2 = 5
- 公交车上原来有15人，又上来8人，现在有多少人？15 + 8 = 23

**关键性质：**
- 交换律：a + b = b + a（3 + 5 = 5 + 3）
- 结合律：(a + b) + c = a + (b + c)
- 任何数加0等于它本身：a + 0 = a

## 2. 减法 (-)

减法是加法的逆运算。从总数中去掉一部分，求剩下多少。

**生活中的例子：**
- 你有10元钱，花了3元，还剩多少？10 - 3 = 7
- 温度从5度降到-2度，降了多少度？5 - (-2) = 7

**关键性质：**
- 减法是加法的逆运算：如果 a + b = c，那么 c - a = b
- 任何数减0等于它本身：a - 0 = a
- 减去一个数等于加上它的相反数：a - b = a + (-b)

## 3. 乘法 (×)

乘法是加法的简便运算。表示几个相同数相加。

**生活中的例子：**
- 一盒有6个鸡蛋，买了3盒，共有几个？6 × 3 = 18
- 长方形长5米，宽3米，面积是多少？5 × 3 = 15 平方米

**关键性质：**
- 交换律：a × b = b × a
- 结合律：(a × b) × c = a × (b × c)
- 分配律：a × (b + c) = a × b + a × c
- 任何数乘1等于它本身：a × 1 = a
- 任何数乘0等于0：a × 0 = 0

## 4. 除法 (÷)

除法是乘法的逆运算。把一个数平均分成几份。

**生活中的例子：**
- 12个苹果分给4个人，每人几个？12 ÷ 4 = 3
- 100元买5本书，每本多少钱？100 ÷ 5 = 20 元

**关键性质：**
- 除法是乘法的逆运算：如果 a × b = c，那么 c ÷ a = b
- 0不能做除数
- 任何数除以1等于它本身：a ÷ 1 = a

## 5. 运算律总结

| 运算律 | 加法 | 乘法 |
|--------|------|------|
| 交换律 | a + b = b + a | a × b = b × a |
| 结合律 | (a+b)+c = a+(b+c) | (a×b)×c = a×(b×c) |
| 分配律 | - | a×(b+c) = a×b + a×c |
""",
        code_snippets=[
            {
                "title": "Basic Operations",
                "title_cn": "基本运算",
                "code": """# 四则运算演示
a, b = 12, 5

print(f"加法: {a} + {b} = {a + b}")
print(f"减法: {a} - {b} = {a - b}")
print(f"乘法: {a} × {b} = {a * b}")
print(f"除法: {a} ÷ {b} = {a / b}")
print(f"整除: {a} // {b} = {a // b}")
print(f"余数: {a} % {b} = {a % b}")""",
            },
            {
                "title": "Operation Laws",
                "title_cn": "运算律验证",
                "code": """# 验证运算律
a, b, c = 3, 5, 7

# 交换律
print(f"加法交换律: {a}+{b}={a+b}, {b}+{a}={b+a}, 相等: {a+b == b+a}")
print(f"乘法交换律: {a}×{b}={a*b}, {b}×{a}={b*a}, 相等: {a*b == b*a}")

# 结合律
print(f"加法结合律: ({a}+{b})+{c}={(a+b)+c}, {a}+({b}+{c})={a+(b+c)}")

# 分配律
print(f"分配律: {a}×({b}+{c})={a*(b+c)}, {a}×{b}+{a}×{c}={a*b+a*c}")""",
            },
        ],
        estimated_minutes=60,
    )
