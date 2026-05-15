"""Calculus manim scenes."""

try:
    from manim import (
        Scene, Axes, NumberPlane, Dot, Text, MathTex, VGroup,
        UP, DOWN, LEFT, RIGHT, ORIGIN, BLUE, RED, GREEN, YELLOW, WHITE,
        Create, Write, FadeIn, Transform, AnimationGroup, Wait,
        Line, DashedLine, Polygon,
    )
    from jiuzhang.visualization.font_config import get_manim_font
    HAS_MANIM = True
except ImportError:
    HAS_MANIM = False


class DerivativeScene(Scene):
    """Visualize derivatives and tangent lines."""

    def __init__(self, func=None, point=1, title="Derivative", **kwargs):
        super().__init__(**kwargs)
        self.func = func or (lambda x: x ** 2)
        self.point = point
        self.title = title

    def construct(self):
        font = get_manim_font()
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-1, 5, 1],
            x_length=8,
            y_length=5,
        )
        self.play(Create(axes))

        graph = axes.plot(self.func, color=BLUE)
        self.play(Create(graph))

        y_val = self.func(self.point)
        point_dot = Dot(axes.c2p(self.point, y_val), color=RED, radius=0.1)
        self.play(FadeIn(point_dot))

        tangent_label = MathTex(
            rf"f'({self.point}) = {2 * self.point}" if self.func(0) == 0 else rf"f'({self.point})",
            font_size=32,
            color=GREEN,
        ).to_edge(DOWN)
        self.play(Write(tangent_label))

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)


class IntegralScene(Scene):
    """Visualize definite integrals as area under curve."""

    def __init__(self, func=None, a=0, b=2, title="Integral", **kwargs):
        super().__init__(**kwargs)
        self.func = func or (lambda x: x ** 2)
        self.a = a
        self.b = b
        self.title = title

    def construct(self):
        font = get_manim_font()
        axes = Axes(
            x_range=[-1, 3, 1],
            y_range=[-1, 5, 1],
            x_length=8,
            y_length=5,
        )
        self.play(Create(axes))

        graph = axes.plot(self.func, color=BLUE)
        self.play(Create(graph))

        area = axes.get_area(
            graph,
            x_range=(self.a, self.b),
            color=GREEN,
            opacity=0.3,
        )
        self.play(FadeIn(area))

        integral_label = MathTex(
            rf"\int_{{{self.a}}}^{{{self.b}}} f(x) \, dx",
            font_size=36,
            color=GREEN,
        ).to_edge(DOWN)
        self.play(Write(integral_label))

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)


class LimitScene(Scene):
    """Visualize limits of functions."""

    def __init__(self, func=None, point=0, limit_value=1, title="Limit", **kwargs):
        super().__init__(**kwargs)
        self.func = func or (lambda x: x)
        self.point = point
        self.limit_value = limit_value
        self.title = title

    def construct(self):
        font = get_manim_font()
        axes = Axes(
            x_range=[-2, 2, 0.5],
            y_range=[-1, 3, 0.5],
            x_length=8,
            y_length=5,
        )
        self.play(Create(axes))

        graph = axes.plot(self.func, color=BLUE)
        self.play(Create(graph))

        limit_label = MathTex(
            rf"\lim_{{x \to {self.point}}} f(x) = {self.limit_value}",
            font_size=36,
            color=GREEN,
        ).to_edge(DOWN)
        self.play(Write(limit_label))

        point_line = DashedLine(
            axes.c2p(self.point, -1),
            axes.c2p(self.point, 3),
            color=RED,
        )
        self.play(Create(point_line))

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)


class TaylorScene(Scene):
    """Visualize Taylor series approximation."""

    def __init__(self, func=None, center=0, n_terms=3, title="Taylor Series", **kwargs):
        super().__init__(**kwargs)
        self.func = func or (lambda x: x)
        self.center = center
        self.n_terms = n_terms
        self.title = title

    def construct(self):
        font = get_manim_font()
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-2, 4, 1],
            x_length=10,
            y_length=5,
        )
        self.play(Create(axes))

        graph = axes.plot(self.func, color=BLUE)
        self.play(Create(graph))

        taylor_label = MathTex(
            rf"T_{{{self.n_terms}}}(x) \text{{ around }} x = {self.center}",
            font_size=32,
            color=GREEN,
        ).to_edge(DOWN)
        self.play(Write(taylor_label))

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)
