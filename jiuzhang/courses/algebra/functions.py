"""Functions course module - Linear, Quadratic, and Special Functions."""

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_linear_functions():
    """Plot multiple linear functions to show slope and intercept."""
    x = np.linspace(-5, 5, 100)
    fig, ax = plt.subplots(figsize=(8, 6))

    params = [
        (1, 0, "y = x"),
        (2, 0, "y = 2x"),
        (-1, 0, "y = -x"),
        (1, 2, "y = x + 2"),
        (1, -2, "y = x - 2"),
    ]

    for k, b, label in params:
        y = k * x + b
        ax.plot(x, y, linewidth=2, label=label)

    ax.axhline(y=0, color="k", linewidth=0.5)
    ax.axvline(x=0, color="k", linewidth=0.5)
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_title("一次函数 y = kx + b")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    plt.tight_layout()
    plt.close(fig)
    return fig


def plot_quadratic_functions():
    """Plot quadratic functions showing vertex and axis of symmetry."""
    x = np.linspace(-5, 5, 100)
    fig, ax = plt.subplots(figsize=(8, 6))

    params = [
        (1, 0, 0, "y = x²"),
        (2, 0, 0, "y = 2x²"),
        (-1, 0, 0, "y = -x²"),
        (1, -2, 0, "y = x² - 2x"),
        (1, 0, -4, "y = x² - 4"),
    ]

    for a, b, c, label in params:
        y = a * x**2 + b * x + c
        ax.plot(x, y, linewidth=2, label=label)

    ax.axhline(y=0, color="k", linewidth=0.5)
    ax.axvline(x=0, color="k", linewidth=0.5)
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_title("二次函数 y = ax² + bx + c")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    plt.tight_layout()
    plt.close(fig)
    return fig


def plot_special_functions():
    """Plot absolute value, square root, and reciprocal functions."""
    x = np.linspace(-5, 5, 200)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # |x|
    y1 = np.abs(x)
    axes[0].plot(x, y1, "b-", linewidth=2)
    axes[0].set_title("y = |x|")
    axes[0].grid(True, alpha=0.3)

    # √x
    x_pos = np.linspace(0, 10, 100)
    y2 = np.sqrt(x_pos)
    axes[1].plot(x_pos, y2, "g-", linewidth=2)
    axes[1].set_title("y = √x")
    axes[1].grid(True, alpha=0.3)

    # 1/x
    x_neg = np.linspace(-5, -0.1, 50)
    x_pos2 = np.linspace(0.1, 5, 50)
    y3_neg = 1 / x_neg
    y3_pos = 1 / x_pos2
    axes[2].plot(x_neg, y3_neg, "r-", linewidth=2)
    axes[2].plot(x_pos2, y3_pos, "r-", linewidth=2)
    axes[2].set_title("y = 1/x")
    axes[2].grid(True, alpha=0.3)

    for ax in axes:
        ax.axhline(y=0, color="k", linewidth=0.5)
        ax.axvline(x=0, color="k", linewidth=0.5)

    plt.suptitle("特殊函数图像")
    plt.tight_layout()
    plt.close(fig)
    return fig


if __name__ == "__main__":
    print("=== 函数可视化 ===")
    plot_linear_functions()
    plot_quadratic_functions()
    plot_special_functions()
    print("完成！")
