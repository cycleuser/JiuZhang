"""Solver Pipeline for JiuZhang.

Chains mathematical methods to solve problems step by step.
Provides detailed solution traces with verification at each step.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
import time

from jiuzhang.solver.method_registry import MethodRegistry, MathMethod, MethodCategory
from jiuzhang.solver.problem_classifier import ProblemClassifier, ProblemType, ProblemDomain


@dataclass
class SolveStep:
    """A single step in the solution process."""
    step_number: int
    method_id: str
    method_name: str
    description: str
    input_data: Any = None
    output_data: Any = None
    verified: bool = False
    verification_detail: str = ""
    execution_time: float = 0.0
    error: Optional[str] = None


@dataclass
class SolveResult:
    """Complete result of solving a problem."""
    success: bool
    problem_text: str
    classification: Optional[ProblemType] = None
    steps: list = field(default_factory=list)
    final_answer: Any = None
    total_time: float = 0.0
    error: Optional[str] = None
    explanation: str = ""
    visualization_path: Optional[str] = None
    confidence: float = 0.0

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def all_verified(self) -> bool:
        return all(s.verified for s in self.steps if s.output_data is not None)


class SolverPipeline:
    """Main solver pipeline.

    Takes a problem, classifies it, selects methods,
    executes them in order, and verifies results.
    """

    def __init__(self, method_registry: Optional[MethodRegistry] = None,
                 classifier: Optional[ProblemClassifier] = None):
        self.registry = method_registry or MethodRegistry()
        self.classifier = classifier or ProblemClassifier(self.registry)
        self._method_executors = {}
        self._register_default_executors()

    def solve(self, problem_text: str, language: str = "zh",
              max_steps: int = 10) -> SolveResult:
        """Solve a mathematical problem.

        Args:
            problem_text: The problem statement
            language: Language for output
            max_steps: Maximum number of solution steps

        Returns:
            SolveResult with complete solution trace
        """
        start_time = time.time()
        result = SolveResult(success=False, problem_text=problem_text)

        try:
            # Step 1: Classify the problem
            classification = self.classifier.classify(problem_text, language)
            result.classification = classification

            # Step 2: Select methods
            methods = self.registry.chain_methods(problem_text)
            if not methods:
                result.error = "No applicable methods found"
                result.total_time = time.time() - start_time
                return result

            # Step 3: Execute methods in order
            context = {"problem": problem_text, "language": language}
            step_number = 0

            for method in methods[:max_steps]:
                step_number += 1
                step = self._execute_method(method, context, step_number)
                result.steps.append(step)

                if step.error:
                    result.error = f"Step {step_number} failed: {step.error}"
                    result.total_time = time.time() - start_time
                    return result

                # Update context with step output
                if step.output_data is not None:
                    context[f"step_{step_number}_output"] = step.output_data
                    result.final_answer = step.output_data

            # Step 4: Build explanation
            result.success = True
            result.explanation = self._build_explanation(result, language)
            result.confidence = self._calculate_confidence(result)

            # Step 5: Generate visualization if applicable
            result.visualization_path = self._try_visualize(result, language)

        except Exception as e:
            result.error = str(e)

        result.total_time = time.time() - start_time
        return result

    def _execute_method(self, method: MathMethod, context: dict,
                        step_number: int) -> SolveStep:
        """Execute a single method."""
        step = SolveStep(
            step_number=step_number,
            method_id=method.id,
            method_name=method.name_cn if context.get("language") == "zh" else method.name,
            description=method.description,
            input_data=context.copy(),
        )

        start = time.time()
        try:
            # Look for registered executor
            executor = self._method_executors.get(method.id)
            if executor:
                step.output_data = executor(context)
            else:
                # No executor registered - generate placeholder
                step.output_data = self._generate_method_output(method, context)

            # Verify if verifier exists
            if method.verify_fn and step.output_data is not None:
                try:
                    verified, detail = method.verify_fn(step.output_data, context)
                    step.verified = verified
                    step.verification_detail = detail
                except Exception as e:
                    step.verified = False
                    step.verification_detail = f"Verification error: {e}"

        except Exception as e:
            step.error = str(e)

        step.execution_time = time.time() - start
        return step

    def _generate_method_output(self, method: MathMethod, context: dict) -> Any:
        """Generate output for a method without a registered executor.

        This provides a structured placeholder that the LLM can fill in.
        """
        return {
            "method_id": method.id,
            "method_name": method.name,
            "description": method.description,
            "status": "pending_llm_execution",
            "context": {k: v for k, v in context.items() if k != "problem"},
        }

    def _build_explanation(self, result: SolveResult, language: str) -> str:
        """Build a human-readable explanation of the solution."""
        if language == "zh":
            parts = [f"# 解题过程\n"]
            parts.append(f"**问题**: {result.problem_text}\n")
            parts.append(f"**领域**: {result.classification.domain.value if result.classification else '未知'}\n")
            parts.append(f"**难度**: {'★' * (result.classification.difficulty if result.classification else 1)}\n")
            parts.append(f"**使用的方法**: {', '.join(s.method_name for s in result.steps)}\n")
            parts.append("---\n")

            for step in result.steps:
                parts.append(f"\n## 步骤 {step.step_number}: {step.method_name}\n")
                parts.append(f"{step.description}\n")
                if step.output_data:
                    parts.append(f"\n**结果**: {step.output_data}\n")
                if step.verified:
                    parts.append(f"\n✅ 验证通过: {step.verification_detail}\n")
                if step.error:
                    parts.append(f"\n❌ 错误: {step.error}\n")

            if result.final_answer:
                parts.append(f"\n---\n")
                parts.append(f"\n## 最终答案\n\n{result.final_answer}\n")

            if result.all_verified:
                parts.append(f"\n✅ 所有步骤均已验证\n")
        else:
            parts = [f"# Solution\n"]
            parts.append(f"**Problem**: {result.problem_text}\n")
            parts.append(f"**Domain**: {result.classification.domain.value if result.classification else 'unknown'}\n")
            parts.append(f"**Difficulty**: {'★' * (result.classification.difficulty if result.classification else 1)}\n")
            parts.append(f"**Methods used**: {', '.join(s.method_name for s in result.steps)}\n")
            parts.append("---\n")

            for step in result.steps:
                parts.append(f"\n## Step {step.step_number}: {step.method_name}\n")
                parts.append(f"{step.description}\n")
                if step.output_data:
                    parts.append(f"\n**Result**: {step.output_data}\n")
                if step.verified:
                    parts.append(f"\n✅ Verified: {step.verification_detail}\n")
                if step.error:
                    parts.append(f"\n❌ Error: {step.error}\n")

            if result.final_answer:
                parts.append(f"\n---\n")
                parts.append(f"\n## Final Answer\n\n{result.final_answer}\n")

            if result.all_verified:
                parts.append(f"\n✅ All steps verified\n")

        return "\n".join(parts)

    def _calculate_confidence(self, result: SolveResult) -> float:
        """Calculate confidence in the solution."""
        if not result.steps:
            return 0.0

        verified_count = sum(1 for s in result.steps if s.verified)
        total_count = sum(1 for s in result.steps if s.output_data is not None)

        if total_count == 0:
            return 0.5  # No verification possible

        base_confidence = verified_count / total_count

        # Adjust for classification confidence
        if result.classification:
            base_confidence *= result.classification.confidence

        return min(base_confidence, 1.0)

    def _try_visualize(self, result: SolveResult, language: str) -> Optional[str]:
        """Try to generate a visualization for the solution."""
        if not result.steps:
            return None

        # Find the last step with a visualization function
        for step in reversed(result.steps):
            method = self.registry.get(step.method_id)
            if method and method.visualize_fn:
                try:
                    return method.visualize_fn(result)
                except Exception:
                    continue
        return None

    def register_executor(self, method_id: str, executor_fn):
        """Register an executor function for a method.

        Args:
            method_id: The method ID to register for
            executor_fn: Function(context) -> result
        """
        self._method_executors[method_id] = executor_fn

    def register_executors(self, executors: dict):
        """Register multiple executor functions at once."""
        self._method_executors.update(executors)

    def _register_default_executors(self):
        """Register default executors for basic arithmetic."""
        import sympy
        from sympy import sympify, solve as sympy_solve, N

        self.register_executor("addition", lambda ctx: self._exec_arithmetic(ctx, "+"))
        self.register_executor("subtraction", lambda ctx: self._exec_arithmetic(ctx, "-"))
        self.register_executor("multiplication", lambda ctx: self._exec_arithmetic(ctx, "*"))
        self.register_executor("division", lambda ctx: self._exec_arithmetic(ctx, "/"))
        self.register_executor("exponentiation", lambda ctx: self._exec_arithmetic(ctx, "**"))

        self.register_executor("solve_linear_eq", lambda ctx: self._exec_solve_equation(ctx))
        self.register_executor("solve_quadratic_eq", lambda ctx: self._exec_solve_equation(ctx))
        self.register_executor("simplify_expression", lambda ctx: self._exec_simplify(ctx))
        self.register_executor("derivative", lambda ctx: self._exec_derivative(ctx))
        self.register_executor("integral", lambda ctx: self._exec_integral(ctx))
        self.register_executor("limit", lambda ctx: self._exec_limit(ctx))
        self.register_executor("factor_polynomial", lambda ctx: self._exec_factor(ctx))
        self.register_executor("determinant", lambda ctx: self._exec_determinant(ctx))
        self.register_executor("divisibility", lambda ctx: self._exec_divisibility(ctx))
        self.register_executor("prime_factorization", lambda ctx: self._exec_prime_factorization(ctx))
        self.register_executor("modular_arithmetic", lambda ctx: self._exec_modular(ctx))
        self.register_executor("vector_ops", lambda ctx: self._exec_vector_ops(ctx))
        self.register_executor("matrix_ops", lambda ctx: self._exec_matrix_ops(ctx))
        self.register_executor("trigonometry", lambda ctx: self._exec_trigonometry(ctx))
        self.register_executor("logarithm", lambda ctx: self._exec_logarithm(ctx))
        self.register_executor("percentage", lambda ctx: self._exec_percentage(ctx))
        self.register_executor("sequence_series", lambda ctx: self._exec_sequence(ctx))
        self.register_executor("combinatorics", lambda ctx: self._exec_combinatorics(ctx))
        self.register_executor("set_ops", lambda ctx: self._exec_set_ops(ctx))
        self.register_executor("basic_probability", lambda ctx: self._exec_probability(ctx))

    def _extract_expression(self, context: dict) -> Optional[str]:
        """Extract a mathematical expression from context."""
        problem = context.get("problem", "")
        # Try to find expression after = or in the problem
        import re
        # Look for patterns like "2 + 3", "x^2 + 2x", etc.
        match = re.search(r"([0-9a-zA-Z\s+\-*/().^%]+)\s*[=？?]", problem)
        if match:
            expr = match.group(1).strip()
            if expr:
                return expr
        return None

    def _exec_arithmetic(self, context: dict, op: str) -> Any:
        """Execute arithmetic operation."""
        problem = context.get("problem", "")
        import re
        # Find numbers and operation
        match = re.search(r"([\d.]+)\s*([+\-×÷*/^])\s*([\d.]+)", problem)
        if match:
            a = float(match.group(1))
            b = float(match.group(3))
            op_char = match.group(2)
            op_map = {"+": "+", "-": "-", "×": "*", "÷": "/", "/": "/", "^": "**"}
            actual_op = op_map.get(op_char, op)
            result = eval(f"{a} {actual_op} {b}")
            return f"{a} {op_char} {b} = {result}"
        return "Could not parse arithmetic expression"

    def _exec_solve_equation(self, context: dict) -> Any:
        """Solve equation using SymPy."""
        problem = context.get("problem", "")
        import re
        from sympy import Symbol, Eq

        # Find equation pattern
        match = re.search(r"([^=]+)\s*=\s*([^,\n]+)", problem)
        if match:
            lhs_str = match.group(1).strip()
            rhs_str = match.group(2).strip()

            # Detect variables
            x = Symbol("x")
            y = Symbol("y")
            z = Symbol("z")
            t = Symbol("t")

            try:
                lhs = sympify(lhs_str)
                rhs = sympify(rhs_str)
                equation = Eq(lhs, rhs)
                solutions = sympy_solve(equation, x)
                if solutions:
                    return f"x = {', '.join(str(s) for s in solutions)}"
                return "No solution found"
            except Exception:
                pass
        return "Could not parse equation"

    def _exec_simplify(self, context: dict) -> Any:
        """Simplify expression using SymPy."""
        problem = context.get("problem", "")
        import re
        match = re.search(r"simplify\s+(.+)|化简\s+(.+)", problem, re.IGNORECASE)
        if match:
            expr_str = match.group(1) or match.group(2)
            try:
                expr = sympify(expr_str.strip())
                simplified = sympy.simplify(expr)
                return f"{expr} = {simplified}"
            except Exception:
                pass
        return "Could not simplify"

    def _exec_derivative(self, context: dict) -> Any:
        """Compute derivative using SymPy."""
        problem = context.get("problem", "")
        from sympy import diff, symbols
        import re

        x = symbols("x")
        match = re.search(r"d/dx\s*\(?([^)]+)\)?|导数.*?([a-zA-Z0-9^+\-*/() ]+)", problem, re.IGNORECASE)
        if match:
            expr_str = match.group(1) or match.group(2)
            try:
                expr = sympify(expr_str.strip())
                deriv = diff(expr, x)
                return f"d/dx({expr}) = {deriv}"
            except Exception:
                pass
        return "Could not compute derivative"

    def _exec_integral(self, context: dict) -> Any:
        """Compute integral using SymPy."""
        problem = context.get("problem", "")
        from sympy import integrate, symbols
        import re

        x = symbols("x")
        match = re.search(r"∫\s*([^\s]+)|integrate\s+(.+)|积分.*?([a-zA-Z0-9^+\-*/() ]+)", problem, re.IGNORECASE)
        if match:
            expr_str = match.group(1) or match.group(2) or match.group(3)
            try:
                expr = sympify(expr_str.strip())
                integral = integrate(expr, x)
                return f"∫{expr} dx = {integral} + C"
            except Exception:
                pass
        return "Could not compute integral"

    def _exec_limit(self, context: dict) -> Any:
        """Compute limit using SymPy."""
        problem = context.get("problem", "")
        from sympy import limit, symbols, oo
        import re

        x = symbols("x")
        match = re.search(r"lim\s*\(\s*([^,]+)\s*,?\s*x\s*→\s*([^)]+)\)", problem)
        if match:
            expr_str = match.group(1).strip()
            point_str = match.group(2).strip()
            try:
                expr = sympify(expr_str)
                point = oo if "∞" in point_str or "inf" in point_str.lower() else sympify(point_str)
                result = limit(expr, x, point)
                return f"lim(x→{point}) {expr} = {result}"
            except Exception:
                pass
        return "Could not compute limit"

    def _exec_factor(self, context: dict) -> Any:
        """Factor polynomial using SymPy."""
        problem = context.get("problem", "")
        from sympy import factor
        import re

        match = re.search(r"factor\s+(.+)|因式分解\s+(.+)", problem, re.IGNORECASE)
        if match:
            expr_str = match.group(1) or match.group(2)
            try:
                expr = sympify(expr_str.strip())
                factored = factor(expr)
                return f"{expr} = {factored}"
            except Exception:
                pass
        return "Could not factor"

    def _exec_determinant(self, context: dict) -> Any:
        """Compute determinant using SymPy."""
        problem = context.get("problem", "")
        from sympy import Matrix
        import re

        # Find matrix pattern [[a,b],[c,d]]
        match = re.search(r"\[\[.*?\]\]", problem)
        if match:
            try:
                matrix = Matrix(eval(match.group()))
                det = matrix.det()
                return f"det({matrix}) = {det}"
            except Exception:
                pass
        return "Could not compute determinant"

    def _exec_divisibility(self, context: dict) -> Any:
        """Check divisibility."""
        problem = context.get("problem", "")
        import re
        match = re.search(r"(\d+)\s*(?:整除|divisible|÷)\s*(\d+)|gcd.*?(\d+).*?(\d+)|lcm.*?(\d+).*?(\d+)", problem, re.IGNORECASE)
        if match:
            if match.group(1) and match.group(2):
                a, b = int(match.group(1)), int(match.group(2))
                return f"{a} ÷ {b} = {a // b} 余 {a % b}, {'整除' if a % b == 0 else '不整除'}"
            elif match.group(3) and match.group(4):
                import math
                a, b = int(match.group(3)), int(match.group(4))
                return f"GCD({a}, {b}) = {math.gcd(a, b)}"
            elif match.group(5) and match.group(6):
                import math
                a, b = int(match.group(5)), int(match.group(6))
                return f"LCM({a}, {b}) = {abs(a * b) // math.gcd(a, b)}"
        return "Could not check divisibility"

    def _exec_prime_factorization(self, context: dict) -> Any:
        """Factor into primes."""
        problem = context.get("problem", "")
        import re
        match = re.search(r"(\d+)", problem)
        if match:
            n = int(match.group(1))
            from sympy import factorint
            factors = factorint(n)
            factor_str = " × ".join(f"{p}^{e}" if e > 1 else str(p) for p, e in factors.items())
            return f"{n} = {factor_str}"
        return "Could not factor"

    def _exec_modular(self, context: dict) -> Any:
        """Compute modular arithmetic."""
        problem = context.get("problem", "")
        import re
        match = re.search(r"(\d+)\s*(?:mod|模|%\s*)(\d+)", problem, re.IGNORECASE)
        if match:
            a, m = int(match.group(1)), int(match.group(2))
            return f"{a} mod {m} = {a % m}"
        return "Could not compute modular"

    def _exec_vector_ops(self, context: dict) -> Any:
        """Compute vector operations."""
        problem = context.get("problem", "")
        from sympy import Matrix
        import re

        # Find vector patterns like (1,2,3) or [1,2,3]
        vectors = re.findall(r"[\(\[]([\d,\s]+)[\)\]]", problem)
        if len(vectors) >= 2:
            try:
                v1 = Matrix([float(x) for x in vectors[0].split(",")])
                v2 = Matrix([float(x) for x in vectors[1].split(",")])
                dot = v1.dot(v2)
                return f"({', '.join(str(x) for x in v1)}) · ({', '.join(str(x) for x in v2)}) = {dot}"
            except Exception:
                pass
        return "Could not compute vector operation"

    def _exec_matrix_ops(self, context: dict) -> Any:
        """Compute matrix operations."""
        problem = context.get("problem", "")
        from sympy import Matrix
        import re

        matrices = re.findall(r"\[\[.*?\]\]", problem)
        if len(matrices) >= 2:
            try:
                m1 = Matrix(eval(matrices[0]))
                m2 = Matrix(eval(matrices[1]))
                result = m1 * m2
                return f"{m1} × {m2} = {result}"
            except Exception:
                pass
        return "Could not compute matrix operation"

    def _exec_trigonometry(self, context: dict) -> Any:
        """Compute trigonometric values."""
        problem = context.get("problem", "")
        from sympy import sin, cos, tan, pi, N
        import re

        match = re.search(r"(sin|cos|tan)\s*\(\s*(\d+)\s*°?\s*\)", problem, re.IGNORECASE)
        if match:
            func_name = match.group(1).lower()
            degrees = int(match.group(2))
            radians = pi * degrees / 180
            func_map = {"sin": sin, "cos": cos, "tan": tan}
            func = func_map.get(func_name)
            if func:
                exact = func(radians)
                numeric = N(exact, 6)
                return f"{func_name}({degrees}°) = {exact} ≈ {numeric}"
        return "Could not compute trigonometric value"

    def _exec_logarithm(self, context: dict) -> Any:
        """Compute logarithmic values."""
        problem = context.get("problem", "")
        from sympy import log, N, E
        import re

        match = re.search(r"log\s*\(\s*(\d+)\s*\)|ln\s*\(\s*(\d+)\s*\)|log_(\d+)\s*\(\s*(\d+)\s*\)", problem, re.IGNORECASE)
        if match:
            if match.group(1):
                val = int(match.group(1))
                result = log(val)
                return f"ln({val}) = {result} ≈ {N(result, 6)}"
            elif match.group(2):
                val = int(match.group(2))
                result = log(val)
                return f"ln({val}) = {result} ≈ {N(result, 6)}"
            elif match.group(3) and match.group(4):
                base = int(match.group(3))
                val = int(match.group(4))
                result = log(val) / log(base)
                return f"log_{base}({val}) = {result} ≈ {N(result, 6)}"
        return "Could not compute logarithm"

    def _exec_percentage(self, context: dict) -> Any:
        """Compute percentage."""
        problem = context.get("problem", "")
        import re
        match = re.search(r"(\d+)%\s*(?:of|的)\s*(\d+)", problem, re.IGNORECASE)
        if match:
            pct = int(match.group(1))
            val = int(match.group(2))
            result = pct / 100 * val
            return f"{pct}% of {val} = {result}"
        return "Could not compute percentage"

    def _exec_sequence(self, context: dict) -> Any:
        """Compute sequence terms."""
        problem = context.get("problem", "")
        from sympy import symbols, Function, Eq, rsolve
        import re

        # Simple arithmetic sequence
        match = re.search(r"(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", problem)
        if match:
            a, b, c = int(match.group(1)), int(match.group(2)), int(match.group(3))
            d = b - a
            if c - b == d:
                # Arithmetic sequence
                nth_match = re.search(r"第\s*(\d+)\s*项|(\d+)(?:st|nd|rd|th)\s*term", problem, re.IGNORECASE)
                if nth_match:
                    n = int(nth_match.group(1) or nth_match.group(2))
                    nth_term = a + (n - 1) * d
                    return f"等差数列: 首项={a}, 公差={d}, 第{n}项={nth_term}"
                return f"等差数列: 首项={a}, 公差={d}, 通项公式: a(n) = {a} + (n-1)×{d}"
        return "Could not analyze sequence"

    def _exec_combinatorics(self, context: dict) -> Any:
        """Compute combinatorial values."""
        problem = context.get("problem", "")
        from sympy import binomial, factorial
        import re

        # C(n, k) or P(n, k)
        match = re.search(r"C\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)|P\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)|(\d+)\s*选\s*(\d+)", problem, re.IGNORECASE)
        if match:
            if match.group(1) and match.group(2):
                n, k = int(match.group(1)), int(match.group(2))
                result = binomial(n, k)
                return f"C({n}, {k}) = {result}"
            elif match.group(3) and match.group(4):
                n, k = int(match.group(3)), int(match.group(4))
                result = factorial(n) // factorial(n - k)
                return f"P({n}, {k}) = {result}"
            elif match.group(5) and match.group(6):
                n, k = int(match.group(5)), int(match.group(6))
                result = binomial(n, k)
                return f"C({n}, {k}) = {result}"
        return "Could not compute combinatorial value"

    def _exec_set_ops(self, context: dict) -> Any:
        """Compute set operations."""
        problem = context.get("problem", "")
        import re

        # Find set patterns like {1,2,3}
        sets = re.findall(r"\{([^}]+)\}", problem)
        if len(sets) >= 2:
            try:
                a = set(x.strip() for x in sets[0].split(","))
                b = set(x.strip() for x in sets[1].split(","))
                union = a | b
                intersection = a & b
                return f"A ∪ B = {union}\nA ∩ B = {intersection}"
            except Exception:
                pass
        return "Could not compute set operation"

    def _exec_probability(self, context: dict) -> Any:
        """Compute basic probability."""
        problem = context.get("problem", "")
        import re

        # Simple probability: "probability of X out of Y"
        match = re.search(r"(\d+)\s*(?:out of|/|分之)\s*(\d+)", problem, re.IGNORECASE)
        if match:
            favorable = int(match.group(1))
            total = int(match.group(2))
            prob = favorable / total
            return f"P = {favorable}/{total} = {prob:.4f} = {prob*100:.2f}%"
        return "Could not compute probability"
