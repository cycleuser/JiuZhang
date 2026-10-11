"""Probability manim scenes."""

try:
    from manim import (
        Scene, Axes, NumberPlane, Dot, Text, MathTex, VGroup,
        UP, DOWN, LEFT, RIGHT, ORIGIN, BLUE, RED, GREEN, YELLOW, WHITE,
        Create, Write, FadeIn, Transform, AnimationGroup, Wait,
        Rectangle, BarChart,
    )
    from jiuzhang.visualization.font_config import get_manim_font
    HAS_MANIM = True
except ImportError:
    HAS_MANIM = False


class ProbabilityScene(Scene):
    """Visualize probability concepts."""

    def __init__(self, event="A", probability=0.5, title="Probability", **kwargs):
        super().__init__(**kwargs)
        self.event = event
        self.probability = probability
        self.title = title

    def construct(self):
        font = get_manim_font()

        prob_text = MathTex(
            rf"P({self.event}) = {self.probability}",
            font_size=48,
            color=BLUE,
        )
        self.play(Write(prob_text))

        bar_width = 6
        filled_width = bar_width * self.probability
        bg_rect = Rectangle(
            width=bar_width,
            height=0.5,
            fill_color=WHITE,
            fill_opacity=0.2,
            stroke_color=WHITE,
        )
        filled_rect = Rectangle(
            width=filled_width,
            height=0.5,
            fill_color=BLUE,
            fill_opacity=0.7,
            stroke_color=BLUE,
        )
        filled_rect.move_to(bg_rect, LEFT)

        self.play(Create(bg_rect))
        self.play(Create(filled_rect))

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)


class DistributionScene(Scene):
    """Visualize probability distributions."""

    def __init__(self, dist_type="normal", mu=0, sigma=1, title="Distribution", **kwargs):
        super().__init__(**kwargs)
        self.dist_type = dist_type
        self.mu = mu
        self.sigma = sigma
        self.title = title

    def construct(self):
        import numpy as np
        font = get_manim_font()

        axes = Axes(
            x_range=[self.mu - 4 * self.sigma, self.mu + 4 * self.sigma, 1],
            y_range=[0, 0.5, 0.1],
            x_length=10,
            y_length=4,
        )
        self.play(Create(axes))

        x = np.linspace(self.mu - 4 * self.sigma, self.mu + 4 * self.sigma, 200)
        y = (1 / (self.sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - self.mu) / self.sigma) ** 2)

        graph = axes.plot_line_graph(
            x_values=x,
            y_values=y,
            line_color=BLUE,
        )
        self.play(Create(graph))

        dist_label = MathTex(
            rf"\mathcal{{N}}({self.mu}, {self.sigma}^2)",
            font_size=32,
            color=BLUE,
        ).to_edge(DOWN)
        self.play(Write(dist_label))

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)


class CombinatoricsScene(Scene):
    """Visualize combinatorial concepts."""

    def __init__(self, n=5, k=3, title="Combinatorics", **kwargs):
        super().__init__(**kwargs)
        self.n = n
        self.k = k
        self.title = title

    def construct(self):
        import math
        font = get_manim_font()

        c_nk = math.comb(self.n, self.k)
        p_nk = math.perm(self.n, self.k)

        combo_text = MathTex(
            rf"C({self.n}, {self.k}) = \binom{{{self.n}}}{{{self.k}}} = {c_nk}",
            font_size=36,
            color=BLUE,
        ).shift(UP)
        perm_text = MathTex(
            rf"P({self.n}, {self.k}) = \frac{{{self.n}!}}{{({self.n}-{self.k})!}} = {p_nk}",
            font_size=36,
            color=GREEN,
        ).shift(DOWN)

        self.play(Write(combo_text))
        self.play(Write(perm_text))

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)
