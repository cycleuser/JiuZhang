"""Functions course module - Linear, Quadratic, and Special Functions."""

from manim import *


class LinearFunctions(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[-5, 5, 1],
            x_length=8,
            y_length=6,
            axis_config={"color": GREY},
        ).add_coordinates()
        self.add(axes)

        params = [
            (1, 0, "y = x", BLUE),
            (2, 0, "y = 2x", RED),
            (-1, 0, "y = -x", GREEN),
            (1, 2, "y = x + 2", ORANGE),
            (1, -2, "y = x - 2", PURPLE),
        ]

        for k, b, label, color in params:
            curve = axes.plot(lambda x: k * x + b, color=color)
            self.add(curve)

        title = Text("一次函数 y = kx + b", font_size=36).to_edge(UP)
        self.add(title)


class QuadraticFunctions(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[-5, 5, 1],
            x_length=8,
            y_length=6,
            axis_config={"color": GREY},
        ).add_coordinates()
        self.add(axes)

        params = [
            (1, 0, 0, "y = x²", BLUE),
            (2, 0, 0, "y = 2x²", RED),
            (-1, 0, 0, "y = -x²", GREEN),
            (1, -2, 0, "y = x² - 2x", ORANGE),
            (1, 0, -4, "y = x² - 4", PURPLE),
        ]

        for a, b, c, label, color in params:
            curve = axes.plot(lambda x: a * x**2 + b * x + c, color=color)
            self.add(curve)

        title = Text("二次函数 y = ax² + bx + c", font_size=36).to_edge(UP)
        self.add(title)


class SpecialFunctions(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[-5, 5, 1],
            x_length=8,
            y_length=6,
            axis_config={"color": GREY},
        ).add_coordinates()
        self.add(axes)

        abs_curve = axes.plot(lambda x: abs(x), color=BLUE)
        sqrt_curve = axes.plot(lambda x: np.sqrt(x) if x >= 0 else 0, x_range=[0, 5], color=GREEN)
        recip_neg = axes.plot(lambda x: 1 / x, x_range=[-5, -0.1], color=RED)
        recip_pos = axes.plot(lambda x: 1 / x, x_range=[0.1, 5], color=RED)

        self.add(abs_curve, sqrt_curve, recip_neg, recip_pos)

        title = Text("特殊函数图像", font_size=36).to_edge(UP)
        self.add(title)
