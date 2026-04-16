"""Code examples for natural numbers.

Demonstrates natural number concepts with Python code and visualizations.
"""

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def demonstrate_natural_numbers():
    """Show natural numbers on a number line."""
    natural_nums = list(range(0, 11))
    print(f"自然数 (0-10): {natural_nums}")
    print(f"自然数的个数: {len(natural_nums)}")
    print(f"前5个自然数的和: {sum(natural_nums[:5])}")
    return natural_nums


def plot_natural_number_line(save_path=None):
    """Plot natural numbers on a number line."""
    fig, ax = plt.subplots(figsize=(10, 2))

    ax.set_xlim(-1, 11)
    ax.set_ylim(-1, 1)
    ax.axhline(y=0, color="black", linewidth=2)

    for x in range(0, 11):
        ax.plot([x, x], [-0.15, 0.15], color="black", linewidth=1.5)
        ax.text(x, -0.35, str(x), ha="center", fontsize=11, fontweight="bold")

    ax.set_title("自然数数轴 (Natural Numbers)", fontsize=14, pad=20)
    ax.axis("off")
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved to {save_path}")

    plt.close(fig)
    return fig


def demonstrate_counting():
    """Demonstrate counting with visual objects."""
    counts = [1, 2, 3, 4, 5]
    fig, axes = plt.subplots(1, 5, figsize=(12, 3))

    for i, count in enumerate(counts):
        ax = axes[i]
        ax.set_xlim(-0.5, 2.5)
        ax.set_ylim(-0.5, 2.5)

        for j in range(count):
            x = j % 3
            y = j // 3
            circle = plt.Circle((x, y), 0.3, color="steelblue", fill=True)
            ax.add_patch(circle)

        ax.set_title(f"{count}", fontsize=16)
        ax.set_aspect("equal")
        ax.axis("off")

    plt.suptitle("计数演示 (Counting Demo)", fontsize=14, y=1.05)
    plt.tight_layout()
    plt.close(fig)
    return fig


if __name__ == "__main__":
    print("=== 自然数演示 ===")
    demonstrate_natural_numbers()
    print()
    plot_natural_number_line("natural_number_line.png")
    demonstrate_counting()
    print("完成！")
