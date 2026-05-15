"""Mathematical Method Registry.

Registers all available mathematical methods with their:
- Domain and category
- Applicable problem types
- Prerequisites
- Execution function
- Verification rules
- Visualization templates
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, Any


class MethodCategory(Enum):
    """Categories of mathematical methods."""
    ARITHMETIC = "arithmetic"
    ALGEBRA = "algebra"
    GEOMETRY = "geometry"
    CALCULUS = "calculus"
    LINEAR_ALGEBRA = "linear_algebra"
    PROBABILITY = "probability"
    NUMBER_THEORY = "number_theory"
    DISCRETE = "discrete"
    DIFFERENTIAL_EQUATIONS = "differential_equations"
    OPTIMIZATION = "optimization"
    STATISTICS = "statistics"
    LOGIC = "logic"
    PROOF = "proof"


@dataclass
class MathMethod:
    """A registered mathematical method.

    Attributes:
        id: Unique method identifier
        name: Method name (English)
        name_cn: Method name (Chinese)
        category: Method category
        description: What this method does
        applicable_problems: Keywords/pattern that indicate this method
        prerequisites: Other methods that should be applied first
        complexity: Difficulty level (1-10)
        execute_fn: Function to execute the method
        verify_fn: Optional function to verify the result
        visualize_fn: Optional function to generate visualization
        examples: Example problems this method solves
    """
    id: str
    name: str
    name_cn: str
    category: MethodCategory
    description: str
    applicable_problems: list = field(default_factory=list)
    prerequisites: list = field(default_factory=list)
    complexity: int = 1
    execute_fn: Optional[Callable] = None
    verify_fn: Optional[Callable] = None
    visualize_fn: Optional[Callable] = None
    examples: list = field(default_factory=list)

    def match_problem(self, problem_text: str) -> float:
        """Check if this method applies to a problem.

        Returns a confidence score between 0 and 1.
        """
        text_lower = problem_text.lower()
        score = 0.0
        for keyword in self.applicable_problems:
            if keyword.lower() in text_lower:
                score += 1.0 / len(self.applicable_problems)
        return min(score, 1.0)


class MethodRegistry:
    """Central registry of all mathematical methods.

    Provides discovery, matching, and chaining of methods
    for solving mathematical problems.
    """

    def __init__(self):
        self._methods: dict[str, MathMethod] = {}
        self._register_builtin_methods()

    def register(self, method: MathMethod):
        """Register a new mathematical method."""
        self._methods[method.id] = method

    def get(self, method_id: str) -> Optional[MathMethod]:
        """Get a method by ID."""
        return self._methods.get(method_id)

    def get_all(self) -> list[MathMethod]:
        """Get all registered methods."""
        return list(self._methods.values())

    def get_by_category(self, category: MethodCategory) -> list[MathMethod]:
        """Get methods in a specific category."""
        return [m for m in self._methods.values() if m.category == category]

    def match_methods(self, problem_text: str, min_score: float = 0.1) -> list[tuple[MathMethod, float]]:
        """Find methods applicable to a problem.

        Returns list of (method, confidence_score) sorted by score.
        """
        matches = []
        for method in self._methods.values():
            score = method.match_problem(problem_text)
            if score >= min_score:
                matches.append((method, score))
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def chain_methods(self, problem_text: str) -> list[MathMethod]:
        """Build an optimal chain of methods for a problem.

        Resolves prerequisites and orders methods correctly.
        """
        matches = self.match_methods(problem_text)
        if not matches:
            return []

        selected = []
        visited = set()

        def _resolve(method: MathMethod):
            if method.id in visited:
                return
            visited.add(method.id)
            for prereq_id in method.prerequisites:
                prereq = self._methods.get(prereq_id)
                if prereq:
                    _resolve(prereq)
            selected.append(method)

        for method, score in matches:
            _resolve(method)

        return selected

    def _register_builtin_methods(self):
        """Register all built-in mathematical methods."""

        # === ARITHMETIC ===
        self.register(MathMethod(
            id="addition",
            name="Addition",
            name_cn="加法",
            category=MethodCategory.ARITHMETIC,
            description="Add two or more numbers",
            applicable_problems=["加", "add", "sum", "plus", "total", "合", "和"],
            complexity=1,
            examples=["2 + 3 = ?", "What is 15 + 27?"]
        ))
        self.register(MathMethod(
            id="subtraction",
            name="Subtraction",
            name_cn="减法",
            category=MethodCategory.ARITHMETIC,
            description="Subtract one number from another",
            applicable_problems=["减", "subtract", "difference", "minus", "差", "减少"],
            complexity=1,
            examples=["10 - 3 = ?", "What is 50 - 23?"]
        ))
        self.register(MathMethod(
            id="multiplication",
            name="Multiplication",
            name_cn="乘法",
            category=MethodCategory.ARITHMETIC,
            description="Multiply two or more numbers",
            applicable_problems=["乘", "multiply", "product", "times", "积", "倍"],
            complexity=1,
            examples=["4 × 5 = ?", "What is 12 × 8?"]
        ))
        self.register(MathMethod(
            id="division",
            name="Division",
            name_cn="除法",
            category=MethodCategory.ARITHMETIC,
            description="Divide one number by another",
            applicable_problems=["除", "divide", "quotient", "÷", "/", "商", "平均"],
            complexity=1,
            examples=["20 ÷ 4 = ?", "What is 100 / 25?"]
        ))
        self.register(MathMethod(
            id="fraction_ops",
            name="Fraction Operations",
            name_cn="分数运算",
            category=MethodCategory.ARITHMETIC,
            description="Add, subtract, multiply, divide fractions",
            applicable_problems=["分数", "fraction", "分子", "分母", "numerator", "denominator"],
            complexity=2,
            examples=["1/2 + 1/3 = ?", "Simplify 6/8"]
        ))
        self.register(MathMethod(
            id="decimal_ops",
            name="Decimal Operations",
            name_cn="小数运算",
            category=MethodCategory.ARITHMETIC,
            description="Operations with decimal numbers",
            applicable_problems=["小数", "decimal", "0.", "1.5"],
            complexity=2,
            examples=["1.5 + 2.3 = ?", "0.25 × 4 = ?"]
        ))
        self.register(MathMethod(
            id="percentage",
            name="Percentage",
            name_cn="百分比",
            category=MethodCategory.ARITHMETIC,
            description="Calculate percentages and percentage changes",
            applicable_problems=["百分比", "percent", "%", "百分之", "增长率"],
            complexity=2,
            examples=["What is 20% of 150?", "Increase 80 by 15%"]
        ))
        self.register(MathMethod(
            id="exponentiation",
            name="Exponentiation",
            name_cn="幂运算",
            category=MethodCategory.ARITHMETIC,
            description="Calculate powers and roots",
            applicable_problems=["幂", "power", "exponent", "平方", "立方", "root", "根", "^", "**"],
            complexity=2,
            examples=["2^3 = ?", "What is the square root of 144?"]
        ))

        # === ALGEBRA ===
        self.register(MathMethod(
            id="simplify_expression",
            name="Simplify Expression",
            name_cn="化简表达式",
            category=MethodCategory.ALGEBRA,
            description="Simplify algebraic expressions",
            applicable_problems=["化简", "simplify", "expand", "展开", "合并", "collect"],
            complexity=3,
            examples=["Simplify 2x + 3x - 5", "Expand (x+1)(x-2)"]
        ))
        self.register(MathMethod(
            id="solve_linear_eq",
            name="Solve Linear Equation",
            name_cn="解线性方程",
            category=MethodCategory.ALGEBRA,
            description="Solve linear equations in one or more variables",
            applicable_problems=["解方程", "solve", "linear equation", "一次方程", "find x", "求x"],
            complexity=3,
            examples=["Solve 2x + 3 = 7", "Find x: 3x - 5 = 2x + 1"]
        ))
        self.register(MathMethod(
            id="solve_quadratic_eq",
            name="Solve Quadratic Equation",
            name_cn="解二次方程",
            category=MethodCategory.ALGEBRA,
            description="Solve quadratic equations using formula, factoring, or completing square",
            applicable_problems=["二次方程", "quadratic", "x²", "x^2", "ax²", "parabola", "抛物线"],
            prerequisites=["solve_linear_eq"],
            complexity=4,
            examples=["Solve x² - 5x + 6 = 0", "Find roots of 2x² + 3x - 2 = 0"]
        ))
        self.register(MathMethod(
            id="solve_system_eq",
            name="Solve System of Equations",
            name_cn="解方程组",
            category=MethodCategory.ALGEBRA,
            description="Solve systems of linear equations",
            applicable_problems=["方程组", "system of equations", "联立", "simultaneous"],
            prerequisites=["solve_linear_eq"],
            complexity=4,
            examples=["Solve: x + y = 5, 2x - y = 1"]
        ))
        self.register(MathMethod(
            id="factor_polynomial",
            name="Factor Polynomial",
            name_cn="因式分解",
            category=MethodCategory.ALGEBRA,
            description="Factor polynomials into irreducible factors",
            applicable_problems=["因式分解", "factor", "factorize", "分解"],
            prerequisites=["simplify_expression"],
            complexity=4,
            examples=["Factor x² - 9", "Factor x² + 5x + 6"]
        ))
        self.register(MathMethod(
            id="polynomial_ops",
            name="Polynomial Operations",
            name_cn="多项式运算",
            category=MethodCategory.ALGEBRA,
            description="Add, subtract, multiply, divide polynomials",
            applicable_problems=["多项式", "polynomial", "degree", "次数"],
            complexity=3,
            examples=["(x² + 2x + 1) + (x² - 3x + 2) = ?"]
        ))
        self.register(MathMethod(
            id="inequality_solve",
            name="Solve Inequality",
            name_cn="解不等式",
            category=MethodCategory.ALGEBRA,
            description="Solve linear and quadratic inequalities",
            applicable_problems=["不等式", "inequality", ">", "<", "≥", "≤", "range", "范围"],
            prerequisites=["solve_linear_eq"],
            complexity=4,
            examples=["Solve 2x + 3 > 7", "Find range: x² - 4 < 0"]
        ))
        self.register(MathMethod(
            id="function_analysis",
            name="Function Analysis",
            name_cn="函数分析",
            category=MethodCategory.ALGEBRA,
            description="Analyze function properties: domain, range, intercepts, symmetry",
            applicable_problems=["函数", "function", "domain", "值域", "range", "定义域", "intercept", "对称"],
            prerequisites=["simplify_expression"],
            complexity=4,
            examples=["Find domain of f(x) = 1/(x-2)", "Analyze f(x) = x² - 4"]
        ))
        self.register(MathMethod(
            id="sequence_series",
            name="Sequence and Series",
            name_cn="数列与级数",
            category=MethodCategory.ALGEBRA,
            description="Work with arithmetic/geometric sequences and series",
            applicable_problems=["数列", "sequence", "series", "级数", "等差", "等比", "arithmetic", "geometric", "sum of"],
            complexity=4,
            examples=["Find the 10th term of 2, 5, 8, ...", "Sum of first 20 terms of geometric series"]
        ))
        self.register(MathMethod(
            id="logarithm",
            name="Logarithm",
            name_cn="对数",
            category=MethodCategory.ALGEBRA,
            description="Compute and manipulate logarithmic expressions",
            applicable_problems=["对数", "logarithm", "log", "ln", "指数方程"],
            prerequisites=["exponentiation"],
            complexity=4,
            examples=["Solve log₂(x) = 3", "Simplify log(100)"]
        ))

        # === GEOMETRY ===
        self.register(MathMethod(
            id="triangle_calc",
            name="Triangle Calculations",
            name_cn="三角形计算",
            category=MethodCategory.GEOMETRY,
            description="Calculate triangle properties: area, perimeter, angles",
            applicable_problems=["三角形", "triangle", "area", "面积", "perimeter", "周长", "angle", "角"],
            complexity=3,
            examples=["Find area of triangle with base 5 and height 3"]
        ))
        self.register(MathMethod(
            id="pythagorean",
            name="Pythagorean Theorem",
            name_cn="勾股定理",
            category=MethodCategory.GEOMETRY,
            description="Apply a² + b² = c² for right triangles",
            applicable_problems=["勾股", "pythagorean", "right triangle", "直角三角形", "hypotenuse", "斜边"],
            prerequisites=["triangle_calc"],
            complexity=3,
            examples=["Find hypotenuse of right triangle with legs 3 and 4"]
        ))
        self.register(MathMethod(
            id="circle_calc",
            name="Circle Calculations",
            name_cn="圆计算",
            category=MethodCategory.GEOMETRY,
            description="Calculate circle properties: circumference, area, arc length",
            applicable_problems=["圆", "circle", "circumference", "周长", "arc", "弧", "radius", "半径", "diameter", "直径"],
            complexity=3,
            examples=["Find area of circle with radius 5", "Circumference of circle with diameter 10"]
        ))
        self.register(MathMethod(
            id="trigonometry",
            name="Trigonometry",
            name_cn="三角函数",
            category=MethodCategory.GEOMETRY,
            description="Calculate sin, cos, tan and solve trigonometric equations",
            applicable_problems=["三角", "trigonometry", "sin", "cos", "tan", "正弦", "余弦", "正切", "θ", "theta"],
            prerequisites=["triangle_calc", "pythagorean"],
            complexity=5,
            examples=["Find sin(30°)", "Solve sin(x) = 0.5"]
        ))
        self.register(MathMethod(
            id="coordinate_geometry",
            name="Coordinate Geometry",
            name_cn="解析几何",
            category=MethodCategory.GEOMETRY,
            description="Distance, midpoint, slope in coordinate plane",
            applicable_problems=["坐标", "coordinate", "distance", "距离", "slope", "斜率", "midpoint", "中点"],
            prerequisites=["pythagorean"],
            complexity=4,
            examples=["Find distance between (1,2) and (4,6)"]
        ))
        self.register(MathMethod(
            id="solid_geometry",
            name="Solid Geometry",
            name_cn="立体几何",
            category=MethodCategory.GEOMETRY,
            description="Calculate volume and surface area of 3D shapes",
            applicable_problems=["体积", "volume", "表面积", "surface area", "立体", "3d", "sphere", "球", "cube", "立方体", "cylinder", "圆柱"],
            prerequisites=["circle_calc", "triangle_calc"],
            complexity=5,
            examples=["Find volume of sphere with radius 3", "Surface area of cylinder"]
        ))

        # === CALCULUS ===
        self.register(MathMethod(
            id="limit",
            name="Limit",
            name_cn="极限",
            category=MethodCategory.CALCULUS,
            description="Calculate limits of functions",
            applicable_problems=["极限", "limit", "approaches", "趋于", "lim"],
            complexity=5,
            examples=["lim(x→0) sin(x)/x", "lim(x→∞) (1+1/x)^x"]
        ))
        self.register(MathMethod(
            id="derivative",
            name="Derivative",
            name_cn="导数",
            category=MethodCategory.CALCULUS,
            description="Compute derivatives using rules (power, product, quotient, chain)",
            applicable_problems=["导数", "derivative", "differentiate", "微分", "d/dx", "f'", "斜率", "slope"],
            prerequisites=["limit", "function_analysis"],
            complexity=5,
            examples=["Find d/dx(x³ + 2x)", "Derivative of sin(x)"]
        ))
        self.register(MathMethod(
            id="integral",
            name="Integral",
            name_cn="积分",
            category=MethodCategory.CALCULUS,
            description="Compute definite and indefinite integrals",
            applicable_problems=["积分", "integral", "integrate", "∫", "area under curve", "原函数"],
            prerequisites=["derivative"],
            complexity=6,
            examples=["∫x² dx", "∫₀¹ sin(x) dx"]
        ))
        self.register(MathMethod(
            id="optimization_calc",
            name="Optimization (Calculus)",
            name_cn="最优化（微积分）",
            category=MethodCategory.CALCULUS,
            description="Find maxima and minima using derivatives",
            applicable_problems=["最大", "minimum", "maximum", "optimization", "优化", "极值", "max", "min"],
            prerequisites=["derivative"],
            complexity=6,
            examples=["Find maximum of f(x) = -x² + 4x", "Minimize cost function"]
        ))
        self.register(MathMethod(
            id="taylor_series",
            name="Taylor Series",
            name_cn="泰勒级数",
            category=MethodCategory.CALCULUS,
            description="Expand functions as Taylor/Maclaurin series",
            applicable_problems=["泰勒", "taylor", "series expansion", "级数展开", "maclaurin", "近似"],
            prerequisites=["derivative", "sequence_series"],
            complexity=7,
            examples=["Taylor expansion of e^x around 0", "Maclaurin series of sin(x)"]
        ))
        self.register(MathMethod(
            id="differential_eq_basic",
            name="Basic Differential Equations",
            name_cn="基本微分方程",
            category=MethodCategory.CALCULUS,
            description="Solve first-order differential equations",
            applicable_problems=["微分方程", "differential equation", "dy/dx", "ode", "初值问题"],
            prerequisites=["derivative", "integral"],
            complexity=6,
            examples=["Solve dy/dx = 2x", "Solve dy/dx = y"]
        ))

        # === LINEAR ALGEBRA ===
        self.register(MathMethod(
            id="vector_ops",
            name="Vector Operations",
            name_cn="向量运算",
            category=MethodCategory.LINEAR_ALGEBRA,
            description="Add, subtract, scale vectors; dot and cross products",
            applicable_problems=["向量", "vector", "dot product", "cross product", "点积", "叉积", "magnitude", "模"],
            complexity=3,
            examples=["Find dot product of (1,2,3) and (4,5,6)"]
        ))
        self.register(MathMethod(
            id="matrix_ops",
            name="Matrix Operations",
            name_cn="矩阵运算",
            category=MethodCategory.LINEAR_ALGEBRA,
            description="Add, multiply, transpose, invert matrices",
            applicable_problems=["矩阵", "matrix", "transpose", "转置", "inverse", "逆矩阵", "multiply", "相乘"],
            complexity=4,
            examples=["Multiply [[1,2],[3,4]] × [[5,6],[7,8]]"]
        ))
        self.register(MathMethod(
            id="determinant",
            name="Determinant",
            name_cn="行列式",
            category=MethodCategory.LINEAR_ALGEBRA,
            description="Calculate determinant of square matrices",
            applicable_problems=["行列式", "determinant", "det", "行列式的值"],
            prerequisites=["matrix_ops"],
            complexity=4,
            examples=["Find det([[1,2],[3,4]])"]
        ))
        self.register(MathMethod(
            id="eigenvalue",
            name="Eigenvalues and Eigenvectors",
            name_cn="特征值与特征向量",
            category=MethodCategory.LINEAR_ALGEBRA,
            description="Find eigenvalues and eigenvectors of matrices",
            applicable_problems=["特征值", "eigenvalue", "特征向量", "eigenvector", "谱", "spectrum"],
            prerequisites=["determinant", "matrix_ops"],
            complexity=6,
            examples=["Find eigenvalues of [[2,1],[1,2]]"]
        ))
        self.register(MathMethod(
            id="linear_transform",
            name="Linear Transformation",
            name_cn="线性变换",
            category=MethodCategory.LINEAR_ALGEBRA,
            description="Apply and analyze linear transformations",
            applicable_problems=["线性变换", "linear transformation", "映射", "mapping", "kernel", "核", "image", "像"],
            prerequisites=["matrix_ops", "vector_ops"],
            complexity=5,
            examples=["Find the matrix of rotation by 90°"]
        ))
        self.register(MathMethod(
            id="solve_linear_system",
            name="Solve Linear System (Matrix)",
            name_cn="解线性方程组（矩阵法）",
            category=MethodCategory.LINEAR_ALGEBRA,
            description="Solve Ax = b using matrix methods (Gaussian elimination, inverse)",
            applicable_problems=["线性方程组", "linear system", "Ax=b", "gaussian", "高斯消元"],
            prerequisites=["matrix_ops", "determinant"],
            complexity=5,
            examples=["Solve: 2x + y = 5, x - y = 1 using matrices"]
        ))

        # === PROBABILITY & STATISTICS ===
        self.register(MathMethod(
            id="basic_probability",
            name="Basic Probability",
            name_cn="基本概率",
            category=MethodCategory.PROBABILITY,
            description="Calculate probabilities of simple events",
            applicable_problems=["概率", "probability", "chance", "可能性", "p(", "likelihood"],
            complexity=3,
            examples=["Probability of rolling a 6 on a die", "P(heads) for a coin flip"]
        ))
        self.register(MathMethod(
            id="combinatorics",
            name="Combinatorics",
            name_cn="组合数学",
            category=MethodCategory.PROBABILITY,
            description="Counting principles: permutations, combinations, binomial coefficient",
            applicable_problems=["排列", "permutation", "组合", "combination", "C(n", "P(n", "n!", "choose", "选"],
            complexity=4,
            examples=["How many ways to choose 3 from 10?", "P(5,3) = ?"]
        ))
        self.register(MathMethod(
            id="conditional_probability",
            name="Conditional Probability",
            name_cn="条件概率",
            category=MethodCategory.PROBABILITY,
            description="Bayes' theorem, conditional probability, independence",
            applicable_problems=["条件概率", "conditional", "bayes", "贝叶斯", "independent", "独立", "given", "已知"],
            prerequisites=["basic_probability", "combinatorics"],
            complexity=5,
            examples=["P(A|B) given P(A), P(B), P(A∩B)"]
        ))
        self.register(MathMethod(
            id="distribution",
            name="Probability Distributions",
            name_cn="概率分布",
            category=MethodCategory.PROBABILITY,
            description="Work with normal, binomial, Poisson, uniform distributions",
            applicable_problems=["分布", "distribution", "normal", "正态", "binomial", "二项", "poisson", "泊松", "mean", "均值", "variance", "方差", "std", "标准差"],
            prerequisites=["basic_probability"],
            complexity=5,
            examples=["P(X > 2) for normal distribution μ=0, σ=1"]
        ))
        self.register(MathMethod(
            id="statistics",
            name="Statistics",
            name_cn="统计学",
            category=MethodCategory.STATISTICS,
            description="Descriptive statistics, hypothesis testing, confidence intervals",
            applicable_problems=["统计", "statistics", "hypothesis", "假设检验", "confidence", "置信区间", "correlation", "相关", "regression", "回归"],
            prerequisites=["distribution"],
            complexity=5,
            examples=["Calculate mean and std of [1,2,3,4,5]", "Test if two samples have same mean"]
        ))

        # === NUMBER THEORY ===
        self.register(MathMethod(
            id="divisibility",
            name="Divisibility",
            name_cn="整除",
            category=MethodCategory.NUMBER_THEORY,
            description="Test divisibility, find GCD, LCM",
            applicable_problems=["整除", "divisible", "gcd", "lcm", "最大公约数", "最小公倍数", "factor", "因数", "prime", "素数", "质数"],
            complexity=2,
            examples=["Find GCD of 12 and 18", "Is 123 divisible by 3?"]
        ))
        self.register(MathMethod(
            id="modular_arithmetic",
            name="Modular Arithmetic",
            name_cn="模运算",
            category=MethodCategory.NUMBER_THEORY,
            description="Compute modulo operations, congruences",
            applicable_problems=["模", "modulo", "mod", "同余", "congruence", "≡", "余数", "remainder"],
            prerequisites=["divisibility"],
            complexity=4,
            examples=["Find 17 mod 5", "Solve x ≡ 3 (mod 7)"]
        ))
        self.register(MathMethod(
            id="prime_factorization",
            name="Prime Factorization",
            name_cn="质因数分解",
            category=MethodCategory.NUMBER_THEORY,
            description="Factor integers into prime factors",
            applicable_problems=["质因数", "prime factorization", "分解质因数", "素因子"],
            prerequisites=["divisibility"],
            complexity=3,
            examples=["Factor 60 into primes", "Find all factors of 24"]
        ))
        self.register(MathMethod(
            id="euler_totient",
            name="Euler's Totient Function",
            name_cn="欧拉函数",
            category=MethodCategory.NUMBER_THEORY,
            description="Compute φ(n) and apply Euler's theorem",
            applicable_problems=["欧拉", "euler", "totient", "φ", "phi", "欧拉定理"],
            prerequisites=["prime_factorization", "modular_arithmetic"],
            complexity=5,
            examples=["Find φ(12)", "Compute 3^100 mod 11 using Euler's theorem"]
        ))

        # === DISCRETE MATHEMATICS ===
        self.register(MathMethod(
            id="set_ops",
            name="Set Operations",
            name_cn="集合运算",
            category=MethodCategory.DISCRETE,
            description="Union, intersection, complement, Cartesian product",
            applicable_problems=["集合", "set", "union", "并集", "intersection", "交集", "complement", "补集", "⊂", "⊆", "∈"],
            complexity=2,
            examples=["A ∪ B where A={1,2}, B={2,3}", "|A ∩ B|"]
        ))
        self.register(MathMethod(
            id="logic_ops",
            name="Logical Operations",
            name_cn="逻辑运算",
            category=MethodCategory.LOGIC,
            description="Propositional logic: AND, OR, NOT, implication, equivalence",
            applicable_problems=["逻辑", "logic", "and", "or", "not", "implication", "蕴含", "等价", "equivalence", "真值表", "truth table"],
            complexity=2,
            examples=["Is (P → Q) equivalent to (¬Q → ¬P)?"]
        ))
        self.register(MathMethod(
            id="graph_theory",
            name="Graph Theory",
            name_cn="图论",
            category=MethodCategory.DISCRETE,
            description="Graph properties, paths, cycles, connectivity, coloring",
            applicable_problems=["图", "graph", "vertex", "顶点", "edge", "边", "path", "路径", "cycle", "环", "connected", "连通", "coloring", "着色"],
            complexity=5,
            examples=["Find shortest path in graph", "Is the graph bipartite?"]
        ))
        self.register(MathMethod(
            id="recurrence",
            name="Recurrence Relations",
            name_cn="递推关系",
            category=MethodCategory.DISCRETE,
            description="Solve recurrence relations using characteristic equations",
            applicable_problems=["递推", "recurrence", "fibonacci", "斐波那契", "递推公式", "characteristic", "特征方程"],
            prerequisites=["sequence_series"],
            complexity=5,
            examples=["Solve a(n) = 2a(n-1) + 1, a(0) = 1"]
        ))

        # === DIFFERENTIAL EQUATIONS ===
        self.register(MathMethod(
            id="ode_first_order",
            name="First-Order ODE",
            name_cn="一阶常微分方程",
            category=MethodCategory.DIFFERENTIAL_EQUATIONS,
            description="Solve separable, linear, exact first-order ODEs",
            applicable_problems=["一阶", "first order", "separable", "可分离", "linear ode", "线性微分方程", "exact", "恰当"],
            prerequisites=["derivative", "integral"],
            complexity=6,
            examples=["Solve dy/dx = xy", "Solve dy/dx + 2y = e^x"]
        ))
        self.register(MathMethod(
            id="ode_second_order",
            name="Second-Order ODE",
            name_cn="二阶常微分方程",
            category=MethodCategory.DIFFERENTIAL_EQUATIONS,
            description="Solve linear second-order ODEs with constant coefficients",
            applicable_problems=["二阶", "second order", "harmonic", "谐振", "damped", "阻尼", "forced", "受迫"],
            prerequisites=["ode_first_order", "eigenvalue"],
            complexity=7,
            examples=["Solve y'' + 4y = 0", "Solve y'' - 3y' + 2y = e^x"]
        ))
        self.register(MathMethod(
            id="laplace_transform",
            name="Laplace Transform",
            name_cn="拉普拉斯变换",
            category=MethodCategory.DIFFERENTIAL_EQUATIONS,
            description="Apply Laplace transforms to solve ODEs",
            applicable_problems=["拉普拉斯", "laplace", "变换", "transform", "s-domain"],
            prerequisites=["integral", "ode_first_order"],
            complexity=7,
            examples=["Find L{sin(t)}", "Solve y'' + y = δ(t) using Laplace"]
        ))
        self.register(MathMethod(
            id="fourier_analysis",
            name="Fourier Analysis",
            name_cn="傅里叶分析",
            category=MethodCategory.DIFFERENTIAL_EQUATIONS,
            description="Fourier series, Fourier transform, applications",
            applicable_problems=["傅里叶", "fourier", "级数", "series", "transform", "变换", "频谱", "frequency", "周期", "periodic"],
            prerequisites=["integral", "trigonometry"],
            complexity=7,
            examples=["Find Fourier series of square wave", "Compute FT of e^(-|t|)"]
        ))

        # === PROOF METHODS ===
        self.register(MathMethod(
            id="direct_proof",
            name="Direct Proof",
            name_cn="直接证明",
            category=MethodCategory.PROOF,
            description="Prove statements by direct logical deduction",
            applicable_problems=["证明", "prove", "show that", "证明以下", "求证"],
            complexity=4,
            examples=["Prove that the sum of two even numbers is even"]
        ))
        self.register(MathMethod(
            id="proof_by_contradiction",
            name="Proof by Contradiction",
            name_cn="反证法",
            category=MethodCategory.PROOF,
            description="Prove by assuming the negation and deriving a contradiction",
            applicable_problems=["反证", "contradiction", "矛盾", "假设不成立"],
            prerequisites=["direct_proof"],
            complexity=5,
            examples=["Prove √2 is irrational"]
        ))
        self.register(MathMethod(
            id="proof_by_induction",
            name="Proof by Induction",
            name_cn="数学归纳法",
            category=MethodCategory.PROOF,
            description="Prove statements for all natural numbers by induction",
            applicable_problems=["归纳", "induction", "对所有n", "for all n", "natural number", "自然数"],
            prerequisites=["direct_proof", "sequence_series"],
            complexity=5,
            examples=["Prove 1+2+...+n = n(n+1)/2 by induction"]
        ))
        self.register(MathMethod(
            id="proof_by_construction",
            name="Proof by Construction",
            name_cn="构造法证明",
            category=MethodCategory.PROOF,
            description="Prove existence by explicitly constructing an example",
            applicable_problems=["构造", "construct", "存在", "exist", "找到", "find an example"],
            prerequisites=["direct_proof"],
            complexity=5,
            examples=["Construct a continuous function that is nowhere differentiable"]
        ))
