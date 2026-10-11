"""Solver module for JiuZhang.

Provides method registry, problem classification, and solver pipeline.
Enables models without mathematical ability to select and chain
appropriate methods for any given problem.
"""

from jiuzhang.solver.method_registry import MethodRegistry, MathMethod, MethodCategory
from jiuzhang.solver.problem_classifier import ProblemClassifier, ProblemType, ClassificationResult
from jiuzhang.solver.pipeline import SolverPipeline, SolveResult

__all__ = [
    "MethodRegistry",
    "MathMethod",
    "MethodCategory",
    "ProblemClassifier",
    "ProblemType",
    "ClassificationResult",
    "SolverPipeline",
    "SolveResult",
]