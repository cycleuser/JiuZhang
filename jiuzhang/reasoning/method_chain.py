"""Method Chain for JiuZhang.

Chains multiple mathematical methods together to solve complex problems.
Each method's output becomes input for the next method in the chain.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Callable

from jiuzhang.solver.method_registry import MethodRegistry, MathMethod


@dataclass
class ChainStep:
    """A step in the method chain."""
    method: MathMethod
    input_data: Any = None
    output_data: Any = None
    success: bool = False
    error: Optional[str] = None


@dataclass
class ChainResult:
    """Result of executing a method chain."""
    success: bool
    steps: list = field(default_factory=list)
    final_output: Any = None
    error: Optional[str] = None

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def all_successful(self) -> bool:
        return all(s.success for s in self.steps)


class MethodChain:
    """Chains mathematical methods together.

    Takes a sequence of methods and executes them in order,
    passing output from one as input to the next.
    """

    def __init__(self, registry: Optional[MethodRegistry] = None):
        self.registry = registry or MethodRegistry()
        self._executors: dict[str, Callable] = {}

    def register_executor(self, method_id: str, executor: Callable):
        """Register an executor for a method."""
        self._executors[method_id] = executor

    def chain(self, method_ids: list[str]) -> "MethodChain":
        """Create a chain of methods by ID.

        Args:
            method_ids: List of method IDs to chain

        Returns:
            Self for method chaining
        """
        self._chain_ids = method_ids
        return self

    def execute(self, initial_input: Any = None) -> ChainResult:
        """Execute the method chain.

        Args:
            initial_input: Input for the first method

        Returns:
            ChainResult with all step results
        """
        if not hasattr(self, "_chain_ids"):
            return ChainResult(success=False, error="No chain defined")

        result = ChainResult(success=True)
        current_input = initial_input

        for method_id in self._chain_ids:
            method = self.registry.get(method_id)
            if not method:
                result.success = False
                result.error = f"Method not found: {method_id}"
                return result

            step = ChainStep(method=method, input_data=current_input)

            try:
                executor = self._executors.get(method_id)
                if executor:
                    step.output_data = executor(current_input)
                    step.success = True
                else:
                    step.output_data = {"method_id": method_id, "input": current_input}
                    step.success = True

                current_input = step.output_data
            except Exception as e:
                step.success = False
                step.error = str(e)
                result.success = False
                result.error = f"Step {method_id} failed: {e}"

            result.steps.append(step)

            if not step.success:
                return result

        result.final_output = current_input
        return result

    @classmethod
    def for_problem(cls, problem_text: str,
                    registry: Optional[MethodRegistry] = None) -> "MethodChain":
        """Create a method chain automatically for a problem.

        Uses the registry to find and chain appropriate methods.
        """
        reg = registry or MethodRegistry()
        chain = cls(reg)
        methods = reg.chain_methods(problem_text)
        if methods:
            chain.chain([m.id for m in methods])
        return chain

    @classmethod
    def for_domain(cls, domain: str,
                   registry: Optional[MethodRegistry] = None) -> "MethodChain":
        """Create a method chain for a mathematical domain.

        Chains all methods in the domain in dependency order.
        """
        from jiuzhang.solver.method_registry import MethodCategory

        reg = registry or MethodRegistry()
        chain = cls(reg)

        category_map = {
            "arithmetic": MethodCategory.ARITHMETIC,
            "algebra": MethodCategory.ALGEBRA,
            "geometry": MethodCategory.GEOMETRY,
            "calculus": MethodCategory.CALCULUS,
            "linear_algebra": MethodCategory.LINEAR_ALGEBRA,
            "probability": MethodCategory.PROBABILITY,
            "number_theory": MethodCategory.NUMBER_THEORY,
            "discrete": MethodCategory.DISCRETE,
            "differential_equations": MethodCategory.DIFFERENTIAL_EQUATIONS,
            "proof": MethodCategory.PROOF,
        }

        category = category_map.get(domain)
        if category:
            methods = reg.get_by_category(category)
            methods.sort(key=lambda m: m.complexity)
            chain.chain([m.id for m in methods])

        return chain
