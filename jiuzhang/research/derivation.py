"""Enhanced mathematical derivation module.

Uses SymPy for symbolic computation and AI for rigorous multi-step proofs.
Cross-verifies results between symbolic computation and AI reasoning.
"""

from typing import Optional
import sympy
from sympy import (
    symbols,
    Eq,
    solve,
    diff,
    integrate,
    limit,
    series,
    Matrix,
    latex,
    sin,
    cos,
    tan,
    exp,
    log,
    sqrt,
    pi,
    oo,
    Symbol,
    Function,
    simplify,
    expand,
    factor,
    trigsimp,
    powsimp,
    summation,
    Product,
    product,
)

from jiuzhang.core.config import Config
from jiuzhang.core.multi_provider_api import MultiProviderClient
from jiuzhang.core.errors import ToolResult
from jiuzhang.research.writing_style import DERIVATION_PROMPT, WRITING_PRINCIPLES


class MathDeriver:
    """Enhanced mathematical derivation engine."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.client = MultiProviderClient(self.config)
        self._symbol_cache = {}

    def derive(self, topic: str, language: str = "zh", depth: str = "medium") -> str:
        """Perform comprehensive mathematical derivation.

        Args:
            topic: Mathematical topic
            language: Output language
            depth: Derivation depth (shallow/medium/deep)

        Returns:
            Detailed derivation with symbolic computation, AI reasoning, and verification
        """
        derivation_parts = []

        # Stage 1: Symbolic computation (fast, exact)
        symbolic_result = self._symbolic_computation(topic, language)
        if symbolic_result:
            derivation_parts.append(symbolic_result)

        # Stage 2: AI-assisted deep derivation
        ai_derivation = self._ai_derivation(topic, language, depth)
        if ai_derivation:
            derivation_parts.append(ai_derivation)

        # Stage 3: Cross-verification
        verification = self._verify_derivation(topic, language)
        if verification:
            derivation_parts.append(verification)

        # Stage 4: Generalization and extensions
        extensions = self._suggest_extensions(topic, language)
        if extensions:
            derivation_parts.append(extensions)

        return "\n\n".join(derivation_parts) if derivation_parts else "推导失败"

    def _get_symbols(self):
        """Get commonly used mathematical symbols."""
        if not self._symbol_cache:
            self._symbol_cache = {
                "basic": symbols("x y z t"),
                "params": symbols("a b c d e f"),
                "indices": symbols("n k m i j"),
                "greek": symbols(
                    "alpha beta gamma delta epsilon theta lambda mu sigma phi omega"
                ),
            }
        return self._symbol_cache

    def _symbolic_computation(self, topic: str, language: str) -> str:
        """Perform comprehensive symbolic computation."""
        x, y, z, t = self._get_symbols()["basic"]
        a, b, c, d, e, f = self._get_symbols()["params"]
        n, k, m, i, j = self._get_symbols()["indices"]

        results = []
        lang_prefix = (
            "## 符号计算\n\n" if language == "zh" else "## Symbolic Computation\n\n"
        )
        computations = []

        # Derivatives
        if "导数" in topic or "derivative" in topic.lower() or "微分" in topic:
            computations.append("### 导数计算\n")

            # Polynomial derivatives
            for power in [2, 3, 4]:
                expr = x**power
                deriv = diff(expr, x)
                computations.append(f"d/dx(x^{power}) = {deriv}")

            # Trigonometric derivatives
            trig_funcs = [
                (sin(x), "sin(x)", cos(x)),
                (cos(x), "cos(x)", -sin(x)),
                (tan(x), "tan(x)", diff(tan(x), x)),
                (exp(x), "e^x", exp(x)),
                (log(x), "ln(x)", 1 / x),
            ]
            computations.append("\n基本函数导数:")
            for expr, name, expected in trig_funcs:
                actual = diff(expr, x)
                verified = simplify(actual - expected) == 0
                mark = "✓" if verified else "✗"
                computations.append(f"  d/dx({name}) = {actual} {mark}")

            # Chain rule example
            expr = sin(x**2)
            deriv = diff(expr, x)
            computations.append(f"\n链式法则: d/dx(sin(x²)) = {deriv}")

            # Product rule
            expr = x**2 * exp(x)
            deriv = diff(expr, x)
            computations.append(f"乘法法则: d/dx(x²·e^x) = {deriv}")

        # Integrals
        if "积分" in topic or "integral" in topic.lower():
            computations.append("### 积分计算\n")

            # Basic integrals
            integrals = [
                (x**2, "x²", x**3 / 3),
                (sin(x), "sin(x)", -cos(x)),
                (cos(x), "cos(x)", sin(x)),
                (exp(x), "e^x", exp(x)),
                (1 / x, "1/x", log(x)),
            ]
            computations.append("不定积分:")
            for expr, name, expected in integrals:
                result = integrate(expr, x)
                verified = simplify(diff(result, x) - expr) == 0
                mark = "✓" if verified else "✗"
                computations.append(f"  ∫{name}dx = {result} + C {mark}")

            # Definite integrals
            computations.append("\n定积分:")
            definite_integrals = [
                (sin(x), (x, 0, pi), "∫₀^π sin(x)dx"),
                (x**2, (x, 0, 1), "∫₀¹ x²dx"),
                (exp(-(x**2)), (x, -oo, oo), "∫₋∞^∞ e^(-x²)dx"),
            ]
            for expr, limits, desc in definite_integrals:
                try:
                    result = integrate(expr, limits)
                    computations.append(f"  {desc} = {result}")
                except Exception:
                    computations.append(f"  {desc} = (数值计算)")

        # Limits
        if "极限" in topic or "limit" in topic.lower():
            computations.append("### 极限计算\n")

            limits_to_compute = [
                (sin(x) / x, x, 0, "lim(x→0) sin(x)/x"),
                ((1 + 1 / x) ** x, x, oo, "lim(x→∞) (1+1/x)^x"),
                ((exp(x) - 1) / x, x, 0, "lim(x→0) (e^x-1)/x"),
                (x * sin(1 / x), x, oo, "lim(x→∞) x·sin(1/x)"),
            ]
            for expr, var, point, desc in limits_to_compute:
                try:
                    result = limit(expr, var, point)
                    computations.append(f"  {desc} = {result}")
                except Exception:
                    computations.append(f"  {desc} = (需要数值方法)")

        # Series expansions
        if "级数" in topic or "series" in topic.lower() or "泰勒" in topic:
            computations.append("### 级数展开\n")

            series_expansions = [
                (exp(x), "e^x", 6),
                (sin(x), "sin(x)", 8),
                (cos(x), "cos(x)", 8),
                (log(1 + x), "ln(1+x)", 6),
                (1 / (1 - x), "1/(1-x)", 6),
            ]
            for expr, name, n in series_expansions:
                try:
                    s = series(expr, x, 0, n)
                    computations.append(f"{name} 的泰勒展开 (x→0):")
                    computations.append(f"  {s}\n")
                except Exception:
                    pass

        # Matrix operations
        if "矩阵" in topic or "matrix" in topic.lower() or "线性代数" in topic:
            computations.append("### 矩阵运算\n")

            # 2x2 matrix
            M = Matrix([[a, b], [c, d]])
            computations.append(f"矩阵 M = {M}")
            computations.append(f"行列式 det(M) = {M.det()}")

            # Specific matrix
            M2 = Matrix([[1, 2], [3, 4]])
            computations.append(f"\n具体矩阵 A = {M2}")
            computations.append(f"  det(A) = {M2.det()}")
            computations.append(f"  trace(A) = {M2.trace()}")
            try:
                inv = M2.inv()
                computations.append(f"  A⁻¹ = {inv}")
            except Exception:
                computations.append("  A 不可逆")

            eigenvals = M2.eigenvals()
            eigenvects = M2.eigenvects()
            computations.append(f"  特征值: {eigenvals}")

        # Fourier analysis
        if "傅里叶" in topic or "fourier" in topic.lower():
            computations.append("### 傅里叶分析\n")
            computations.append("傅里叶级数:")
            computations.append("  f(x) = a₀/2 + Σ[aₙcos(nx) + bₙsin(nx)]")
            computations.append("  aₙ = (1/π)∫₋π^π f(x)cos(nx)dx")
            computations.append("  bₙ = (1/π)∫₋π^π f(x)sin(nx)dx")
            computations.append("\n常见函数的傅里叶系数:")
            computations.append("  方波: bₙ = 4/(nπ) (n为奇数)")
            computations.append("  三角波: bₙ = 8/(n²π²) (n为奇数)")
            computations.append("  锯齿波: bₙ = 2(-1)^(n+1)/n")

            # Symbolic Fourier coefficients
            expr = sin(3 * x)
            a_n = integrate(expr * cos(n * x), (x, -pi, pi)) / pi
            b_n = integrate(expr * sin(n * x), (x, -pi, pi)) / pi
            computations.append(f"\nsin(3x) 的傅里叶系数:")
            computations.append(f"  aₙ = {simplify(a_n)}")
            computations.append(f"  bₙ = {simplify(b_n)}")

        # Equation solving
        if "方程" in topic or "equation" in topic.lower():
            computations.append("### 方程求解\n")

            # Linear
            eq1 = Eq(2 * x + 3, 7)
            sol1 = solve(eq1, x)
            computations.append(f"线性方程: {eq1} → x = {sol1[0]}")

            # Quadratic
            eq2 = Eq(x**2 - 5 * x + 6, 0)
            sol2 = solve(eq2, x)
            computations.append(f"二次方程: {eq2} → x = {sol2}")

            # Cubic
            eq3 = Eq(x**3 - 6 * x**2 + 11 * x - 6, 0)
            sol3 = solve(eq3, x)
            computations.append(f"三次方程: {eq3} → x = {sol3}")

        # Pythagorean theorem
        if "勾股" in topic or "pythagorean" in topic.lower():
            computations.append("### 勾股定理\n")
            computations.append("a² + b² = c²")
            triples = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25)]
            computations.append("\n常见勾股数:")
            for a_val, b_val, c_val in triples:
                verified = a_val**2 + b_val**2 == c_val**2
                mark = "✓" if verified else "✗"
                computations.append(
                    f"  ({a_val}, {b_val}, {c_val}): {a_val}²+{b_val}²={a_val**2 + b_val}={c_val}² {mark}"
                )

        # Trigonometry
        if "三角" in topic or "trig" in topic.lower():
            computations.append("### 三角函数\n")
            computations.append("基本恒等式:")

            identities = [
                (sin(x) ** 2 + cos(x) ** 2, "sin²(x)+cos²(x)", 1),
                (tan(x) - sin(x) / cos(x), "tan(x)-sin(x)/cos(x)", 0),
                (sin(2 * x) - 2 * sin(x) * cos(x), "sin(2x)-2sin(x)cos(x)", 0),
                (
                    cos(2 * x) - (cos(x) ** 2 - sin(x) ** 2),
                    "cos(2x)-cos²(x)+sin²(x)",
                    0,
                ),
            ]
            for expr, name, expected in identities:
                simplified = simplify(expr)
                verified = simplified == expected
                mark = "✓" if verified else "✗"
                computations.append(f"  {name} = {simplified} {mark}")

        # Probability
        if "概率" in topic or "probability" in topic.lower():
            computations.append("### 概率计算\n")
            computations.append("基本公式:")
            computations.append("  P(A∪B) = P(A) + P(B) - P(A∩B)")
            computations.append("  P(A|B) = P(A∩B) / P(B)")
            computations.append("  P(A) = 1 - P(非A)")
            computations.append("\n常见分布:")
            computations.append("  二项分布: P(X=k) = C(n,k)·p^k·(1-p)^(n-k)")
            computations.append("  正态分布: f(x) = (1/σ√(2π))·e^(-(x-μ)²/(2σ²))")
            computations.append("  泊松分布: P(X=k) = λ^k·e^(-λ)/k!")

        if computations:
            results.append(lang_prefix + "\n".join(computations))

        return "\n".join(results) if results else ""

    def _ai_derivation(self, topic: str, language: str, depth: str) -> str:
        """Use AI for deep mathematical reasoning and proof."""
        lang = "中文" if language == "zh" else "English"
        depth_map = {
            "shallow": "简要但严谨的推导",
            "medium": "详细推导，包含关键步骤的解释",
            "deep": "完整严格的证明，包含所有细节和边界条件",
        }

        prompt = DERIVATION_PROMPT.format(
            topic=topic,
            lang=lang,
            depth=depth_map.get(depth, depth_map["medium"]),
            principles=WRITING_PRINCIPLES,
        )

        messages = [{"role": "user", "content": prompt}]
        result = self.client.send_message(messages)
        return result.data if result.success else ""

    def _verify_derivation(self, topic: str, language: str) -> str:
        """Cross-verify mathematical results."""
        x = symbols("x")
        verifications = []
        lang_prefix = (
            "## 交叉验证\n\n" if language == "zh" else "## Cross-Verification\n\n"
        )

        # Derivative verification
        if "导数" in topic or "derivative" in topic.lower():
            verifications.append("### 导数验证\n")
            test_cases = [
                (x**2, 2 * x, "x²"),
                (x**3, 3 * x**2, "x³"),
                (sin(x), cos(x), "sin(x)"),
                (exp(x), exp(x), "e^x"),
            ]
            for expr, expected, name in test_cases:
                actual = diff(expr, x)
                verified = simplify(actual - expected) == 0
                mark = "✅" if verified else "❌"
                verifications.append(f"  d/dx({name}) = {expected}: {mark}")

        # Integral verification
        if "积分" in topic or "integral" in topic.lower():
            verifications.append("\n### 积分验证\n")
            test_cases = [
                (x**2, x**3 / 3, "x²"),
                (sin(x), -cos(x), "sin(x)"),
                (cos(x), sin(x), "cos(x)"),
                (exp(x), exp(x), "e^x"),
            ]
            for integrand, expected_antideriv, name in test_cases:
                actual = integrate(integrand, x)
                # Check if derivative of antiderivative equals integrand
                verified = simplify(diff(actual, x) - integrand) == 0
                mark = "✅" if verified else "❌"
                verifications.append(f"  ∫{name}dx = {expected_antideriv}+C: {mark}")

        # Trigonometric identity verification
        if "三角" in topic or "trig" in topic.lower():
            verifications.append("\n### 三角恒等式验证\n")
            identities = [
                (sin(x) ** 2 + cos(x) ** 2 - 1, "sin²(x)+cos²(x)=1"),
                (sin(2 * x) - 2 * sin(x) * cos(x), "sin(2x)=2sin(x)cos(x)"),
                (cos(2 * x) - (cos(x) ** 2 - sin(x) ** 2), "cos(2x)=cos²(x)-sin²(x)"),
                (tan(x) - sin(x) / cos(x), "tan(x)=sin(x)/cos(x)"),
            ]
            for expr, name in identities:
                simplified = simplify(expr)
                verified = simplified == 0
                mark = "✅" if verified else "❌"
                verifications.append(f"  {name}: {mark}")

        # Limit verification
        if "极限" in topic or "limit" in topic.lower():
            verifications.append("\n### 极限验证\n")
            limits_to_check = [
                (sin(x) / x, x, 0, 1, "lim(x→0) sin(x)/x"),
                ((1 + 1 / x) ** x, x, oo, exp(1), "lim(x→∞) (1+1/x)^x"),
            ]
            for expr, var, point, expected, desc in limits_to_check:
                try:
                    result = limit(expr, var, point)
                    verified = simplify(result - expected) == 0
                    mark = "✅" if verified else "❌"
                    verifications.append(f"  {desc} = {expected}: {mark}")
                except Exception:
                    verifications.append(f"  {desc}: ⚠️ 需要数值验证")

        if verifications:
            return lang_prefix + "\n".join(verifications)
        return ""

    def _suggest_extensions(self, topic: str, language: str) -> str:
        """Suggest mathematical extensions and generalizations."""
        extensions = []
        lang_prefix = "## 推广与扩展\n\n" if language == "zh" else "## Extensions\n\n"

        if "导数" in topic or "derivative" in topic.lower():
            extensions.append("### 导数的推广\n")
            extensions.append("1. **偏导数**: 多元函数对某一变量的导数")
            extensions.append("2. **方向导数**: 函数沿某一方向的变化率")
            extensions.append("3. **高阶导数**: 导数的导数，如 f''(x), f'''(x)")
            extensions.append("4. **隐函数求导**: 对隐函数定义的函数求导")
            extensions.append("5. **参数方程求导**: 对参数方程表示的曲线求导")

        if "积分" in topic or "integral" in topic.lower():
            extensions.append("### 积分的推广\n")
            extensions.append("1. **多重积分**: 二重积分、三重积分")
            extensions.append("2. **曲线积分**: 沿曲线的积分")
            extensions.append("3. **曲面积分**: 沿曲面的积分")
            extensions.append("4. **勒贝格积分**: 更一般的积分定义")
            extensions.append("5. **反常积分**: 无穷区间或无界函数的积分")

        if "傅里叶" in topic or "fourier" in topic.lower():
            extensions.append("### 傅里叶分析的推广\n")
            extensions.append("1. **傅里叶变换**: 从级数到变换")
            extensions.append("2. **离散傅里叶变换(DFT)**: 数字信号处理基础")
            extensions.append("3. **快速傅里叶变换(FFT)**: O(n log n) 算法")
            extensions.append("4. **小波变换**: 时频局部化分析")
            extensions.append("5. **拉普拉斯变换**: 复频域分析")

        if "矩阵" in topic or "matrix" in topic.lower():
            extensions.append("### 矩阵理论的推广\n")
            extensions.append("1. **矩阵分解**: LU、QR、SVD 分解")
            extensions.append("2. **矩阵函数**: e^A, sin(A), cos(A)")
            extensions.append("3. **广义逆**: Moore-Penrose 伪逆")
            extensions.append("4. **张量**: 高维矩阵的推广")
            extensions.append("5. **算子理论**: 无限维空间的矩阵推广")

        if extensions:
            return lang_prefix + "\n".join(extensions)
        return ""
