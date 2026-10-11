"""Code examples for natural numbers.

Demonstrates natural number concepts with Python code and visualizations.
"""

from manim import *


def demonstrate_natural_numbers():
    """Show natural numbers on a number line."""
    natural_nums = list(range(0, 11))
    print(f"自然数 (0-10): {natural_nums}")
    print(f"自然数的个数: {len(natural_nums)}")
    print(f"前5个自然数的和: {sum(natural_nums[:5])}")
    return natural_nums


class NaturalNumberLine(Scene):
    def construct(self):
        number_line = NumberLine(
            x_range=[0, 10, 1],
            length=10,
            include_numbers=True,
            font_size=36,
        ).shift(DOWN * 0.5)

        self.add(number_line)
        title = Text("自然数数轴 (Natural Numbers)", font_size=36).to_edge(UP)
        self.add(title)


class CountingDemo(Scene):
    def construct(self):
        counts = [1, 2, 3, 4, 5]
        groups = VGroup()

        for i, count in enumerate(counts):
            dot_group = VGroup()
            for j in range(count):
                x = j % 3 - 1
                y = j // 3
                dot = Dot(point=np.array([x, y, 0]), radius=0.2, color=BLUE)
                dot_group.add(dot)

            label = Text(str(count), font_size=24).next_to(dot_group, DOWN, buff=0.3)
            group = VGroup(dot_group, label)
            groups.add(group)

        groups.arrange(RIGHT, buff=1).shift(DOWN * 0.3)
        self.add(groups)
        title = Text("计数演示 (Counting Demo)", font_size=36).to_edge(UP)
        self.add(title)


if __name__ == "__main__":
    print("=== 自然数演示 ===")
    demonstrate_natural_numbers()
    print()
    print("完成！")
