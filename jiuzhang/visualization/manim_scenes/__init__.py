"""Manim scene templates for JiuZhang.

Pre-built manim scenes for common mathematical concepts across all domains.
"""

try:
    from jiuzhang.visualization.manim_scenes.arithmetic import (
        NumberLineScene, FractionPieScene, OperationAnimation,
    )
    from jiuzhang.visualization.manim_scenes.algebra import (
        FunctionPlotScene, EquationSolveScene, PolynomialScene,
    )
    from jiuzhang.visualization.manim_scenes.geometry import (
        TriangleScene, CircleScene, TrigFunctionScene, SolidGeometryScene,
    )
    from jiuzhang.visualization.manim_scenes.calculus import (
        DerivativeScene, IntegralScene, LimitScene, TaylorScene,
    )
    from jiuzhang.visualization.manim_scenes.linear_algebra import (
        VectorScene, MatrixTransformScene, EigenvalueScene,
    )
    from jiuzhang.visualization.manim_scenes.probability import (
        ProbabilityScene, DistributionScene, CombinatoricsScene,
    )
    HAS_MANIM = True
except ImportError:
    HAS_MANIM = False
    NumberLineScene = None
    FractionPieScene = None
    OperationAnimation = None
    FunctionPlotScene = None
    EquationSolveScene = None
    PolynomialScene = None
    TriangleScene = None
    CircleScene = None
    TrigFunctionScene = None
    SolidGeometryScene = None
    DerivativeScene = None
    IntegralScene = None
    LimitScene = None
    TaylorScene = None
    VectorScene = None
    MatrixTransformScene = None
    EigenvalueScene = None
    ProbabilityScene = None
    DistributionScene = None
    CombinatoricsScene = None

__all__ = [
    "NumberLineScene",
    "FractionPieScene",
    "OperationAnimation",
    "FunctionPlotScene",
    "EquationSolveScene",
    "PolynomialScene",
    "TriangleScene",
    "CircleScene",
    "TrigFunctionScene",
    "SolidGeometryScene",
    "DerivativeScene",
    "IntegralScene",
    "LimitScene",
    "TaylorScene",
    "VectorScene",
    "MatrixTransformScene",
    "EigenvalueScene",
    "ProbabilityScene",
    "DistributionScene",
    "CombinatoricsScene",
]