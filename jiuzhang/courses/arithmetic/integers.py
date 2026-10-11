"""Code examples for integers.

Demonstrates integer concepts with Python code and visualizations.
"""

from manim import *


def demonstrate_integers():
    """Show integers including negative numbers."""
    integers = list(range(-5, 6))
    print(f"整数 (-5 到 5): {integers}")
    print(f"正整数: {[x for x in integers if x > 0]}")
    print(f"负整数: {[x for x in integers if x < 0]}")
    print(f"零: 0")
    return integers


class IntegerNumberLine(Scene):
    def construct(self):
        number_line = NumberLine(
            x_range=[-6, 6, 1],
            length=12,
            include_numbers=True,
            font_size=36,
        ).shift(DOWN * 0.5)

        for x in range(-6, 7):
            if x < 0:
                num = MathTex(str(x), color=RED).move_to(number_line.n2p(x) + DOWN * 0.5)
            elif x > 0:
                num = MathTex(str(x), color=BLUE).move_to(number_line.n2p(x) + DOWN * 0.5)
            else:
                num = MathTex("0", color=GREEN).move_to(number_line.n2p(x) + DOWN * 0.5)

        self.add(number_line)
        title = Text("整数数轴 (Integer Number Line)", font_size=36).to_edge(UP)
        self.add(title)


class TemperatureAndIntegers(Scene):
    def construct(self):
        temperatures = [-10, -5, 0, 5, 10, 15, 20, 25, 30]
        labels = ["-10°C\n很冷", "-5°C\n冷", "0°C\n冰点", "5°C\n凉",
                  "10°C\n温和", "15°C\n舒适", "20°C\n暖和", "25°C\n热", "30°C\n很热"]

        axes = Axes(
            x_range=[0, len(temperatures), 1],
            y_range=[-15, 35, 10],
            x_length=10,
            y_length=5,
        ).add_coordinates().shift(DOWN * 0.3)

        for i, t in enumerate(temperatures):
            color = RED if t < 0 else GREEN if t == 0 else BLUE
            bar = Rectangle(
                width=0.6,
                height=abs(t) * 5 / 35,
                fill_opacity=0.7,
                fill_color=color,
                stroke_color=WHITE,
            ).move_to(axes.c2p(i + 0.5, t / 2))
            self.add(bar)

        title = Text("温度与整数", font_size=36).to_edge(UP)
        self.add(axes, title)


def demonstrate_integer_operations():
    """Demonstrate basic integer operations."""
    print("=== 整数运算 ===")
    print(f"加法: (+5) + (-3) = {5 + (-3)}")
    print(f"减法: (+2) - (+7) = {2 - 7}")
    print(f"乘法: (-3) × (+4) = {(-3) * 4}")
    print(f"除法: (-12) ÷ (+3) = {(-12) // 3}")
    print(f"绝对值: |-5| = {abs(-5)}")


if __name__ == "__main__":
    print("=== 整数演示 ===")
    demonstrate_integers()
    print()
    demonstrate_integer_operations()
    print("\n完成！")
