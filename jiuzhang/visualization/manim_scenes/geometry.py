"""Geometry manim scenes."""

try:
    from manim import (
        Scene, Axes, NumberPlane, Dot, Text, MathTex, VGroup,
        UP, DOWN, LEFT, RIGHT, ORIGIN, BLUE, RED, GREEN, YELLOW, WHITE,
        Create, Write, FadeIn, Transform, AnimationGroup, Wait,
        Line, Polygon, Circle, Triangle, Rectangle, Sector, Arc,
        PI, DEGREES,
    )
    from jiuzhang.visualization.font_config import get_manim_font
    HAS_MANIM = True
except ImportError:
    HAS_MANIM = False


class TriangleScene(Scene):
    """Visualize triangle properties."""

    def __init__(self, vertices=None, title="Triangle", **kwargs):
        super().__init__(**kwargs)
        self.vertices = vertices or [[-2, -1, 0], [2, -1, 0], [0, 2, 0]]
        self.title = title

    def construct(self):
        font = get_manim_font()
        triangle = Polygon(*self.vertices, color=BLUE, fill_opacity=0.3)
        self.play(Create(triangle))

        for i, v in enumerate(self.vertices):
            dot = Dot(v, color=RED)
            label = MathTex(f"V_{i+1}", font_size=24).next_to(dot, OUT if len(v) > 2 else UP, buff=0.2)
            self.play(FadeIn(dot), Write(label))

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)


class CircleScene(Scene):
    """Visualize circle properties."""

    def __init__(self, radius=2, title="Circle", **kwargs):
        super().__init__(**kwargs)
        self.radius = radius
        self.title = title

    def construct(self):
        font = get_manim_font()
        circle = Circle(radius=self.radius, color=BLUE, fill_opacity=0.2)
        self.play(Create(circle))

        center_dot = Dot(ORIGIN, color=RED)
        radius_line = Line(ORIGIN, [self.radius, 0, 0], color=GREEN)
        radius_label = MathTex(f"r = {self.radius}", font_size=24).next_to(radius_line, DOWN, buff=0.1)

        self.play(FadeIn(center_dot))
        self.play(Create(radius_line), Write(radius_label))

        area_text = MathTex(rf"A = \pi r^2 = {3.14159 * self.radius**2:.2f}", font_size=28).shift(DOWN * 2)
        circ_text = MathTex(rf"C = 2\pi r = {2 * 3.14159 * self.radius:.2f}", font_size=28).shift(DOWN * 2.8)
        self.play(Write(area_text))
        self.play(Write(circ_text))

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)


class TrigFunctionScene(Scene):
    """Visualize trigonometric functions."""

    def __init__(self, func_name="sin", x_range=(-2 * 3.14, 2 * 3.14), title="Trigonometric Function", **kwargs):
        super().__init__(**kwargs)
        self.func_name = func_name
        self.x_range = x_range
        self.title = title

    def construct(self):
        import numpy as np
        from manim import axes

        font = get_manim_font()
        axes_obj = NumberPlane(
            x_range=[self.x_range[0], self.x_range[1], 3.14],
            y_range=[-1.5, 1.5, 0.5],
            x_length=10,
            y_length=4,
        )
        self.play(Create(axes_obj))

        if self.func_name == "sin":
            func = np.sin
            color = BLUE
        elif self.func_name == "cos":
            func = np.cos
            color = RED
        else:
            func = np.tan
            color = GREEN

        graph = axes_obj.plot(func, x_range=self.x_range, color=color)
        self.play(Create(graph))

        label = MathTex(rf"{self.func_name}(x)", font_size=36, color=color).to_edge(RIGHT)
        self.play(Write(label))

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)


class SolidGeometryScene(Scene):
    """Visualize 3D geometry."""

    def __init__(self, shape="sphere", title="3D Shape", **kwargs):
        super().__init__(**kwargs)
        self.shape = shape
        self.title = title

    def construct(self):
        from manim import ThreeDScene
        font = get_manim_font()

        if self.shape == "sphere":
            from manim import Sphere
            shape_obj = Sphere(radius=1.5, resolution=(20, 20))
            shape_obj.set_color(BLUE)
            shape_obj.set_opacity(0.5)
        elif self.shape == "cube":
            from manim import Cube
            shape_obj = Cube(side_length=2)
            shape_obj.set_color(GREEN)
            shape_obj.set_opacity(0.5)
        else:
            from manim import Cone
            shape_obj = Cone(base_radius=1.5, height=3)
            shape_obj.set_color(YELLOW)
            shape_obj.set_opacity(0.5)

        self.play(Create(shape_obj))

        title_text = Text(self.title, font=font, font_size=32).to_edge(UP)
        self.play(Write(title_text))
        self.wait(1)
