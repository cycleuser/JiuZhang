"""TUI visualization for JiuZhang.

ASCII/Unicode-based visualizations for terminal display.
"""

from typing import Optional
import numpy as np

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


console = Console()


def plot_number_line_tui(
    start: int = -10,
    end: int = 10,
    highlight: Optional[list] = None,
    title: str = "Number Line",
):
    """Plot a number line in the terminal."""
    highlight = highlight or []
    line = "─" * ((end - start + 1) * 2 + 1)
    ticks = ""
    labels = ""

    for x in range(start, end + 1):
        if x in highlight:
            ticks += "┃"
            labels += f"[bold red]{x:>{len(str(end))}}[/bold red]"
        else:
            ticks += "│"
            labels += f"{x:>{len(str(end))}}"
        ticks += "─"

    output = Text()
    output.append(f"\n  {title}\n\n", style="bold blue")
    output.append(f"  {line}\n")
    output.append(f"  {ticks}\n")
    output.append(f"  {labels}\n")

    console.print(Panel(output, title="数轴", border_style="blue"))


def plot_bar_chart_tui(
    categories: list,
    values: list,
    title: str = "Bar Chart",
    max_height: int = 10,
):
    """Plot a bar chart in the terminal."""
    max_val = max(values) if values else 1
    scale = max_height / max_val if max_val > 0 else 1

    output = Text()
    output.append(f"\n  {title}\n\n", style="bold blue")

    for row in range(max_height, 0, -1):
        line = "  "
        for val in values:
            if val * scale >= row:
                line += "██ "
            else:
                line += "   "
        output.append(line + "\n")

    output.append("  " + "───" * len(values) + "\n")
    output.append("  " + " ".join(f"{c:^2}" for c in categories) + "\n")

    console.print(Panel(output, title="柱状图", border_style="green"))


def plot_function_tui(
    func,
    x_range: tuple = (-10, 10),
    width: int = 60,
    height: int = 20,
    title: str = "Function",
):
    """Plot a function in the terminal."""
    x_vals = np.linspace(x_range[0], x_range[1], width)
    y_vals = func(x_vals)

    y_min, y_max = y_vals.min(), y_vals.max()
    if y_max == y_min:
        y_max = y_min + 1

    grid = [[" " for _ in range(width)] for _ in range(height)]

    for i, (x, y) in enumerate(zip(x_vals, y_vals)):
        col = int(i)
        row = height - 1 - int((y - y_min) / (y_max - y_min) * (height - 1))
        if 0 <= row < height and 0 <= col < width:
            grid[row][col] = "●"

    output = Text()
    output.append(f"\n  {title}\n\n", style="bold blue")
    output.append(f"  y ∈ [{y_min:.2f}, {y_max:.2f}]\n\n")

    for row in grid:
        output.append("  " + "".join(row) + "\n")

    output.append(f"\n  x ∈ [{x_range[0]}, {x_range[1]}]\n")

    console.print(Panel(output, title="函数图像", border_style="magenta"))


def show_multiplication_table_tui(size: int = 9):
    """Show multiplication table."""
    output = Text()
    output.append(f"\n  九九乘法表\n\n", style="bold blue")

    header = "   " + " ".join(f"{i:>2}" for i in range(1, size + 1))
    output.append(header + "\n")
    output.append("   " + "───" * size + "\n")

    for i in range(1, size + 1):
        row = f"{i:>2} │"
        for j in range(1, size + 1):
            val = i * j
            row += f"{val:>3}"
        output.append(row + "\n")

    console.print(Panel(output, title="乘法表", border_style="yellow"))


def show_fraction_visualizer_tui(numerator: int, denominator: int):
    """Visualize a fraction."""
    if denominator == 0:
        console.print("[red]分母不能为0！[/red]")
        return

    decimal = numerator / denominator
    percentage = decimal * 100

    output = Text()
    output.append(f"\n  分数可视化: {numerator}/{denominator}\n\n", style="bold blue")
    output.append(f"  小数: {decimal:.4f}\n")
    output.append(f"  百分比: {percentage:.2f}%\n\n")

    bar_width = 40
    filled = int(bar_width * decimal)
    filled = max(0, min(filled, bar_width))

    bar = "█" * filled + "░" * (bar_width - filled)
    output.append(f"  [{bar}]\n")
    output.append(f"  0%{' ' * 15}{percentage:.0f}%{' ' * 15}100%\n")

    console.print(Panel(output, title="分数", border_style="cyan"))
