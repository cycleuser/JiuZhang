"""Algebra manim scenes."""

try:
    from manim import (
        Scene, Axes, NumberPlane, Dot, Text, MathTex, VGroup,
        UP, DOWN, LEFT, RIGHT, ORIGIN, BLUE, RED, GREEN, YELLOW, WHITE,
        Create, Write, FadeIn, Transform, AnimationGroup, Wait,
        Line, DashedLine,
    )
    from jiuzhang.visualization.font_config import get_manim_font
    HAS_MANIM = True
except ImportError:
    HAS_MANIM = False


class FunctionPlotScene(Scene):
    """Plot a mathematical function."""

    def __init__(self, func=None, x_range=(-5, 5), title="Function Plot", **kwargs):
        super().__init__(**kwargs)
        self.func = func or (lambda x: x ** 2)
        self.x_range = x_range
        self.title = title

    def construct(self):
        font = get_manim_font()
        axes = Axes(
            x_range=[self.x_range[0], self.x_range[1], 1],
            y_range=[-5, 10, 1],
            x_length=10,
            y_length=6,
        )
        self.play(Create(axes))

        graph = axes.plot(self.func, color=BLUE)
        self.play(Create(graph))

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)


class EquationSolveScene(Scene):
    """Visualize solving an equation."""

    def __init__(self, lhs="2x + 3", rhs="7", solution="x = 2", title="Solve Equation", **kwargs):
        super().__init__(**kwargs)
        self.lhs = lhs
        self.rhs = rhs
        self.solution = solution
        self.title = title

    def construct(self):
        font = get_manim_font()
        equation = MathTex(
            rf"{self.lhs} = {self.rhs}",
            font_size=48,
        ).shift(UP * 2)
        self.play(Write(equation))

        steps = [
            rf"{self.lhs} - 3 = {self.rhs} - 3",
            rf"2x = {int(self.rhs) - 3}" if self.rhs.isdigit() else rf"2x = {self.rhs} - 3",
            rf"x = {self.solution.split('=')[1].strip()}" if "=" in self.solution else self.solution,
        ]

        y_pos = UP * 1
        for step in steps:
            step_text = MathTex(step, font_size=36, color=GREEN).shift(y_pos)
            self.play(Write(step_text))
            y_pos += DOWN * 1

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)


class PolynomialScene(Scene):
    """Visualize polynomial operations."""

    def __init__(self, poly1="x^2 + 2x + 1", poly2="x - 1", operation="+", result="x^2 + 3x", title="Polynomial", **kwargs):
        super().__init__(**kwargs)
        self.poly1 = poly1
        self.poly2 = poly2
        self.operation = operation
        self.result = result
        self.title = title

    def construct(self):
        font = get_manim_font()
        p1 = MathTex(rf"P_1(x) = {self.poly1}", font_size=36).shift(UP * 2)
        op = MathTex(self.operation, font_size=36)
        p2 = MathTex(rf"P_2(x) = {self.poly2}", font_size=36).shift(DOWN * 0.5)
        eq = MathTex("=", font_size=36).shift(DOWN * 1.5)
        res = MathTex(rf"Result = {self.result}", font_size=36, color=GREEN).shift(DOWN * 2.5)

        self.play(Write(p1))
        self.play(Write(op))
        self.play(Write(p2))
        self.play(Write(eq))
        self.play(Write(res))

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)
