"""Arithmetic manim scenes."""

try:
    from manim import (
        Scene, NumberLine, Dot, Text, MathTex, VGroup,
        UP, DOWN, LEFT, RIGHT, ORIGIN, BLUE, RED, GREEN, YELLOW, WHITE,
        Circle, Sector, Arc, Polygon, Rectangle,
        Create, Write, FadeIn, Transform, AnimationGroup, Wait,
    )
    from jiuzhang.visualization.font_config import get_manim_font
    HAS_MANIM = True
except ImportError:
    HAS_MANIM = False
    Scene = object  # Stub
    NumberLine = Dot = Text = MathTex = VGroup = object
    UP = DOWN = LEFT = RIGHT = ORIGIN = BLUE = RED = GREEN = YELLOW = WHITE = None
    Circle = Sector = Arc = Polygon = Rectangle = object
    Create = Write = FadeIn = Transform = AnimationGroup = Wait = lambda x: x
    def get_manim_font(): return "Sans"


class NumberLineScene(Scene):
    """Visualize a number line with highlighted points."""

    def __init__(self, start=-10, end=10, highlight=None, title="Number Line", **kwargs):
        super().__init__(**kwargs)
        self.start = start
        self.end = end
        self.highlight = highlight or []
        self.title = title

    def construct(self):
        if not HAS_MANIM:
            return
        font = get_manim_font()
        number_line = NumberLine(
            x_range=[self.start, self.end, 1],
            length=10,
            include_numbers=True,
        )
        self.play(Create(number_line))

        for h in self.highlight:
            dot = Dot(number_line.n2p(h), color=RED, radius=0.12)
            label = MathTex(str(h), font_size=28).next_to(dot, UP, buff=0.2)
            self.play(FadeIn(dot), Write(label))

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)


class FractionPieScene(Scene):
    """Visualize fractions as pie charts."""

    def __init__(self, numerator=1, denominator=4, title="Fraction", **kwargs):
        super().__init__(**kwargs)
        self.numerator = numerator
        self.denominator = denominator
        self.title = title

    def construct(self):
        if not HAS_MANIM:
            return
        font = get_manim_font()
        radius = 2
        full_circle = Circle(radius=radius, color=WHITE, fill_opacity=0.1)
        self.play(Create(full_circle))

        filled_angle = 360 * self.numerator / self.denominator
        filled_sector = Sector(
            radius=radius,
            start_angle=0,
            angle=filled_angle * 3.14159 / 180,
            color=BLUE,
            fill_opacity=0.7,
        )
        self.play(Create(filled_sector))

        fraction_text = MathTex(
            rf"\frac{{{self.numerator}}}{{{self.denominator}}}",
            font_size=48,
        ).to_edge(DOWN)
        self.play(Write(fraction_text))

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)


class OperationAnimation(Scene):
    """Animate arithmetic operations."""

    def __init__(self, a=3, b=5, op="+", title="Addition", **kwargs):
        super().__init__(**kwargs)
        self.a = a
        self.b = b
        self.op = op
        self.title = title

    def construct(self):
        if not HAS_MANIM:
            return
        font = get_manim_font()

        a_text = MathTex(str(self.a), font_size=60).shift(LEFT * 3)
        op_text = MathTex(self.op, font_size=60)
        b_text = MathTex(str(self.b), font_size=60).shift(RIGHT * 3)
        eq_text = MathTex("=", font_size=60).shift(RIGHT * 5)

        result = None
        if self.op == "+":
            result = self.a + self.b
        elif self.op == "-":
            result = self.a - self.b
        elif self.op in ("*", "×"):
            result = self.a * self.b
        elif self.op in ("/", "÷"):
            result = self.a / self.b if self.b != 0 else "undefined"

        result_text = MathTex(str(result), font_size=60, color=GREEN).shift(RIGHT * 7)

        self.play(Write(a_text))
        self.play(Write(op_text))
        self.play(Write(b_text))
        self.play(Write(eq_text))
        self.play(Write(result_text))

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)
