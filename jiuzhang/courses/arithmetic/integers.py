"""Code examples for integers.

Demonstrates integer concepts with Python code and visualizations.
"""

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def demonstrate_integers():
    """Show integers including negative numbers."""
    integers = list(range(-5, 6))
    print(f"整数 (-5 到 5): {integers}")
    print(f"正整数: {[x for x in integers if x > 0]}")
    print(f"负整数: {[x for x in integers if x < 0]}")
    print(f"零: 0")
    return integers


def plot_integer_number_line(save_path=None):
    """Plot integers on a number line with positive/negative coloring."""
    fig, ax = plt.subplots(figsize=(12, 2))

    ax.set_xlim(-7, 7)
    ax.set_ylim(-1, 1)
    ax.axhline(y=0, color="gray", linewidth=1.5)

    for x in range(-6, 7):
        if x < 0:
            color = "red"
        elif x > 0:
            color = "blue"
        else:
            color = "green"

        ax.plot([x, x], [-0.15, 0.15], color=color, linewidth=2)
        ax.text(
            x, -0.35, str(x), ha="center", fontsize=11, color=color, fontweight="bold"
        )

    ax.axvline(x=0, color="green", linewidth=2, linestyle="--", alpha=0.5)
    ax.set_title("整数数轴 (Integer Number Line)", fontsize=14, pad=20)
    ax.axis("off")
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved to {save_path}")

    plt.close(fig)
    return fig


def demonstrate_temperature():
    """Demonstrate positive and negative integers using temperature."""
    temperatures = [-10, -5, 0, 5, 10, 15, 20, 25, 30]
    labels = [
        "-10°C\n很冷",
        "-5°C\n冷",
        "0°C\n冰点",
        "5°C\n凉",
        "10°C\n温和",
        "15°C\n舒适",
        "20°C\n暖和",
        "25°C\n热",
        "30°C\n很热",
    ]

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["red" if t < 0 else "green" if t == 0 else "blue" for t in temperatures]

    bars = ax.bar(
        range(len(temperatures)), temperatures, color=colors, edgecolor="black"
    )

    for bar, label in zip(bars, labels):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + (1 if bar.get_height() >= 0 else -2),
            label,
            ha="center",
            fontsize=9,
        )

    ax.axhline(y=0, color="black", linewidth=2)
    ax.set_xticks(range(len(temperatures)))
    ax.set_xticklabels([str(t) for t in temperatures])
    ax.set_ylabel("温度 (°C)")
    ax.set_title("温度与整数 (Temperature and Integers)")
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.close(fig)
    return fig


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
    plot_integer_number_line("integer_number_line.png")
    demonstrate_temperature()
    demonstrate_integer_operations()
    print("\n完成！")
