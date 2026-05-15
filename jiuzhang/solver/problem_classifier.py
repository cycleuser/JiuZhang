"""Problem Classifier for JiuZhang.

Analyzes mathematical problems to determine:
- Problem domain (arithmetic, algebra, geometry, etc.)
- Problem type (compute, prove, solve, analyze, etc.)
- Difficulty level
- Required knowledge points
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import re


class ProblemDomain(Enum):
    """Mathematical domain of a problem."""
    ARITHMETIC = "arithmetic"
    ALGEBRA = "algebra"
    GEOMETRY = "geometry"
    CALCULUS = "calculus"
    LINEAR_ALGEBRA = "linear_algebra"
    PROBABILITY = "probability"
    STATISTICS = "statistics"
    NUMBER_THEORY = "number_theory"
    DISCRETE = "discrete"
    DIFFERENTIAL_EQUATIONS = "differential_equations"
    LOGIC = "logic"
    PROOF = "proof"
    OPTIMIZATION = "optimization"
    UNKNOWN = "unknown"


class ProblemType(Enum):
    """Type of mathematical problem."""
    COMPUTE = "compute"          # Calculate a value
    SOLVE = "solve"              # Find unknowns
    PROVE = "prove"              # Prove a statement
    SIMPLIFY = "simplify"        # Simplify expression
    ANALYZE = "analyze"          # Analyze properties
    GRAPH = "graph"              # Visualize/draw
    OPTIMIZE = "optimize"        # Find max/min
    CLASSIFY = "classify"        # Categorize objects
    CONSTRUCT = "construct"      # Build an example
    ESTIMATE = "estimate"        # Approximate value
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Classification result for a problem."""
    domain: ProblemDomain = ProblemDomain.UNKNOWN
    problem_type: "ProblemType" = ProblemType.UNKNOWN
    difficulty: int = 1  # 1-10
    keywords: list = field(default_factory=list)
    entities: dict = field(default_factory=dict)  # extracted math entities
    confidence: float = 0.0
    suggested_methods: list = field(default_factory=list)
    knowledge_points: list = field(default_factory=list)
    language: str = "zh"


# Domain keyword patterns
DOMAIN_PATTERNS = {
    ProblemDomain.ARITHMETIC: [
        r"\d+\s*[+\-×÷*/]\s*\d+",
        r"加|减|乘|除|和|差|积|商",
        r"add|subtract|multiply|divide|sum|product|quotient",
        r"分数|fraction|小数|decimal|百分|percent",
        r"平方|立方|根号|power|root|square|cube",
    ],
    ProblemDomain.ALGEBRA: [
        r"[a-z]\s*[=<>≠≥≤]+\s*",
        r"解方程|solve.*equation|find\s+[a-z]",
        r"多项式|polynomial|因式|factor",
        r"函数|function|f\(x\)|g\(x\)",
        r"不等式|inequality",
        r"对数|logarithm|log|ln",
        r"数列|sequence|series|等差|等比",
    ],
    ProblemDomain.GEOMETRY: [
        r"三角形|triangle|圆|circle|角|angle",
        r"面积|area|周长|perimeter|体积|volume",
        r"勾股|pythagorean|sin|cos|tan",
        r"坐标|coordinate|距离|distance|斜率|slope",
        r"球|sphere|圆柱|cylinder|圆锥|cone",
    ],
    ProblemDomain.CALCULUS: [
        r"极限|limit|lim\s*\(",
        r"导数|derivative|d/dx|f'|微分|differential",
        r"积分|integral|∫|integrate",
        r"泰勒|taylor|级数展开|series expansion",
        r"最大|最小|max|min|optimization|极值",
    ],
    ProblemDomain.LINEAR_ALGEBRA: [
        r"矩阵|matrix|行列式|determinant",
        r"向量|vector|点积|dot.*product|叉积|cross.*product",
        r"特征值|eigenvalue|特征向量|eigenvector",
        r"线性变换|linear.*transformation",
        r"高斯消元|gaussian.*elimination",
    ],
    ProblemDomain.PROBABILITY: [
        r"概率|probability|p\s*\(|chance",
        r"排列|permutation|组合|combination",
        r"分布|distribution|正态|normal|二项|binomial",
        r"贝叶斯|bayes|条件概率|conditional",
        r"期望|expectation|均值|mean|方差|variance",
    ],
    ProblemDomain.NUMBER_THEORY: [
        r"素数|质数|prime|整除|divisible",
        r"模运算|modular|同余|congruence",
        r"最大公约数|gcd|最小公倍数|lcm",
        r"欧拉|euler|费马|fermat|质因数|prime.*factor",
    ],
    ProblemDomain.DISCRETE: [
        r"集合|set|并集|union|交集|intersection",
        r"图|graph|顶点|vertex|边|edge|路径|path",
        r"逻辑|logic|命题|proposition|真值表|truth.*table",
        r"递推|recurrence|斐波那契|fibonacci",
    ],
    ProblemDomain.DIFFERENTIAL_EQUATIONS: [
        r"微分方程|differential.*equation|dy/dx|ode",
        r"拉普拉斯|laplace|傅里叶|fourier",
        r"一阶|first.*order|二阶|second.*order",
    ],
    ProblemDomain.PROOF: [
        r"证明|prove|show\s+that|求证",
        r"反证|contradiction|归纳|induction",
        r"充分必要|necessary.*sufficient|当且仅当|iff",
    ],
}

# Problem type patterns
TYPE_PATTERNS = {
    ProblemType.COMPUTE: [
        r"计算|compute|calculate|求.*值|what\s+is|=\s*\?",
        r"\d+\s*[+\-×÷*/]\s*\d+\s*=\s*\?",
    ],
    ProblemType.SOLVE: [
        r"解|solve|find\s+[a-z]|求.*解",
        r"方程|equation",
    ],
    ProblemType.PROVE: [
        r"证明|prove|show\s+that|求证|verify",
    ],
    ProblemType.SIMPLIFY: [
        r"化简|simplify|展开|expand|合并",
    ],
    ProblemType.ANALYZE: [
        r"分析|analyze|性质|property|特征|characteristic",
    ],
    ProblemType.GRAPH: [
        r"画|draw|plot|graph|可视化|visualize|图像",
    ],
    ProblemType.OPTIMIZE: [
        r"最大|minimum|maximum|optimization|最优|极值",
    ],
    ProblemType.ESTIMATE: [
        r"估计|estimate|近似|approximate|约",
    ],
}


class ProblemClassifier:
    """Classifies mathematical problems.

    Uses pattern matching and keyword analysis to determine
    the domain, type, difficulty, and suggested methods.
    """

    def __init__(self, method_registry=None):
        self._method_registry = method_registry
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns."""
        self._domain_patterns = {}
        for domain, patterns in DOMAIN_PATTERNS.items():
            self._domain_patterns[domain] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

        self._type_patterns = {}
        for ptype, patterns in TYPE_PATTERNS.items():
            self._type_patterns[ptype] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def classify(self, problem_text: str, language: str = "zh") -> ClassificationResult:
        """Classify a mathematical problem.

        Args:
            problem_text: The problem statement
            language: Language code (zh/en)

        Returns:
            ProblemType classification result
        """
        result = ClassificationResult()
        result.language = language

        # Detect domain
        domain_scores = {}
        for domain, patterns in self._domain_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern.search(problem_text):
                    score += 1
            if score > 0:
                domain_scores[domain] = score

        if domain_scores:
            result.domain = max(domain_scores, key=domain_scores.get)
            result.confidence = min(domain_scores[result.domain] / 3.0, 1.0)
        else:
            result.domain = ProblemDomain.UNKNOWN
            result.confidence = 0.0

        # Detect problem type
        type_scores = {}
        for ptype, patterns in self._type_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern.search(problem_text):
                    score += 1
            if score > 0:
                type_scores[ptype] = score

        if type_scores:
            result.problem_type = max(type_scores, key=type_scores.get)
        else:
            result.problem_type = ProblemType.UNKNOWN

        # Extract keywords
        result.keywords = self._extract_keywords(problem_text)

        # Extract entities (numbers, variables, functions)
        result.entities = self._extract_entities(problem_text)

        # Estimate difficulty
        result.difficulty = self._estimate_difficulty(problem_text, result)

        # Suggest methods
        if self._method_registry:
            result.suggested_methods = self._method_registry.chain_methods(problem_text)

        # Suggest knowledge points
        result.knowledge_points = self._suggest_knowledge_points(result)

        return result

    def _extract_keywords(self, text: str) -> list:
        """Extract mathematical keywords from text."""
        math_keywords = [
            "导数", "积分", "极限", "矩阵", "向量", "概率", "统计",
            "函数", "方程", "不等式", "数列", "级数",
            "derivative", "integral", "limit", "matrix", "vector",
            "probability", "statistics", "function", "equation",
            "sin", "cos", "tan", "log", "exp", "sqrt",
            "证明", "归纳", "反证", "prove", "induction",
        ]
        found = []
        text_lower = text.lower()
        for kw in math_keywords:
            if kw.lower() in text_lower:
                found.append(kw)
        return found

    def _extract_entities(self, text: str) -> dict:
        """Extract mathematical entities from text."""
        entities = {}

        # Numbers
        numbers = re.findall(r"[-+]?\d*\.?\d+", text)
        if numbers:
            entities["numbers"] = [float(n) for n in numbers]

        # Variables (single letters used as math symbols)
        variables = re.findall(r"\b[a-zA-Z]\b", text)
        math_vars = [v for v in variables if v not in ("a", "an", "the", "is", "of", "to", "in", "on", "for", "by", "with")]
        if math_vars:
            entities["variables"] = list(set(math_vars))

        # Functions
        functions = re.findall(r"(sin|cos|tan|log|ln|exp|sqrt|abs)\s*\(", text, re.IGNORECASE)
        if functions:
            entities["functions"] = list(set(f.lower() for f in functions))

        # Mathematical operators
        if any(op in text for op in ["+", "-", "×", "÷", "*", "/"]):
            entities["has_arithmetic"] = True
        if "=" in text:
            entities["has_equation"] = True
        if any(op in text for op in ["∫", "∂", "∇", "Σ", "Π"]):
            entities["has_advanced_notation"] = True

        return entities

    def _estimate_difficulty(self, text: str, classification: ClassificationResult) -> int:
        """Estimate problem difficulty on a scale of 1-10."""
        difficulty = 1

        # Base difficulty from domain
        domain_difficulty = {
            ProblemDomain.ARITHMETIC: 1,
            ProblemDomain.ALGEBRA: 3,
            ProblemDomain.GEOMETRY: 3,
            ProblemDomain.CALCULUS: 5,
            ProblemDomain.LINEAR_ALGEBRA: 4,
            ProblemDomain.PROBABILITY: 4,
            ProblemDomain.STATISTICS: 4,
            ProblemDomain.NUMBER_THEORY: 5,
            ProblemDomain.DISCRETE: 4,
            ProblemDomain.DIFFERENTIAL_EQUATIONS: 6,
            ProblemDomain.LOGIC: 3,
            ProblemDomain.PROOF: 5,
            ProblemDomain.OPTIMIZATION: 5,
            ProblemDomain.UNKNOWN: 1,
        }
        difficulty = domain_difficulty.get(classification.domain, 1)

        # Increase for multiple concepts
        if len(classification.keywords) > 3:
            difficulty += 1
        if len(classification.keywords) > 5:
            difficulty += 1

        # Increase for proof problems
        if classification.problem_type == ProblemType.PROVE:
            difficulty += 2

        # Increase for multi-step problems
        if "然后" in text or "then" in text.lower() or "先" in text or "first" in text.lower():
            difficulty += 1

        # Increase for advanced notation
        entities = classification.entities
        if entities.get("has_advanced_notation"):
            difficulty += 2

        return min(max(difficulty, 1), 10)

    def _suggest_knowledge_points(self, classification: ClassificationResult) -> list:
        """Suggest relevant knowledge points based on classification."""
        kp_map = {
            ProblemDomain.ARITHMETIC: ["natural_numbers", "integers", "fractions", "decimals", "operations"],
            ProblemDomain.ALGEBRA: ["expressions", "linear_equations", "quadratic_equations", "functions", "polynomials"],
            ProblemDomain.GEOMETRY: ["triangles", "pythagorean", "circles", "trigonometry", "coordinate_geometry"],
            ProblemDomain.CALCULUS: ["limits", "derivatives", "integrals", "taylor_series"],
            ProblemDomain.LINEAR_ALGEBRA: ["vectors", "matrices", "determinants", "eigenvalues"],
            ProblemDomain.PROBABILITY: ["probability_basics", "combinatorics", "distributions"],
            ProblemDomain.NUMBER_THEORY: ["divisibility", "primes", "modular_arithmetic"],
            ProblemDomain.DISCRETE: ["sets", "logic", "graph_theory", "combinatorics"],
            ProblemDomain.DIFFERENTIAL_EQUATIONS: ["first_order_ode", "second_order_ode", "laplace", "fourier"],
            ProblemDomain.PROOF: ["direct_proof", "contradiction", "induction"],
        }
        return kp_map.get(classification.domain, [])
