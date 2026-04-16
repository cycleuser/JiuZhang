"""Visualization engine for JiuZhang.

Provides matplotlib-based visualizations for mathematical concepts.
Uses automatic font detection for proper multi-language support.
"""

import io
import base64
from typing import Optional

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from jiuzhang.visualization.font_config import configure_matplotlib
from jiuzhang.core.errors import ToolResult, VisualizationError


class Visualizer:
    """Mathematical visualization engine using matplotlib.

    Automatically configures fonts for proper multi-language support.
    """

    @staticmethod
    def plot_number_line(
        start: float = -10,
        end: float = 10,
        highlight: Optional[list] = None,
        title: str = "Number Line",
        save_path: Optional[str] = None,
        language: str = "zh",
    ) -> ToolResult:
        """Plot a number line.

        Args:
            start: Start of number line
            end: End of number line
            highlight: List of numbers to highlight
            title: Plot title
            save_path: Path to save the plot
            language: Language for font configuration

        Returns:
            ToolResult with plot data
        """
        configure_matplotlib(language)
        fig, ax = plt.subplots(figsize=(12, 2))

        ax.set_xlim(start - 1, end + 1)
        ax.set_ylim(-1, 1)
        ax.axhline(y=0, color="black", linewidth=2)

        for x in range(int(start), int(end) + 1):
            ax.plot([x, x], [-0.1, 0.1], color="black", linewidth=1)
            ax.text(x, -0.4, str(x), ha="center", fontsize=10)

        if highlight:
            for h in highlight:
                ax.plot(h, 0, "ro", markersize=12)
                ax.annotate(
                    f"{h}",
                    (h, 0.1),
                    textcoords="offset points",
                    xytext=(0, 15),
                    ha="center",
                    color="red",
                    fontweight="bold",
                )

        ax.set_title(title, fontsize=14, pad=20)
        ax.axis("off")
        plt.tight_layout()

        return Visualizer._save_or_return(fig, save_path)

    @staticmethod
    def plot_function(
        func,
        x_range: tuple = (-10, 10),
        num_points: int = 1000,
        title: str = "Function Plot",
        xlabel: str = "x",
        ylabel: str = "y",
        grid: bool = True,
        save_path: Optional[str] = None,
        language: str = "zh",
    ) -> ToolResult:
        """Plot a mathematical function.

        Args:
            func: Function to plot
            x_range: Range of x values
            num_points: Number of points to plot
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            grid: Whether to show grid
            save_path: Path to save the plot
            language: Language for font configuration

        Returns:
            ToolResult with plot data
        """
        configure_matplotlib(language)
        x = np.linspace(x_range[0], x_range[1], num_points)
        y = func(x)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(x, y, "b-", linewidth=2, label=title)

        ax.axhline(y=0, color="k", linewidth=0.5)
        ax.axvline(x=0, color="k", linewidth=0.5)

        if grid:
            ax.grid(True, alpha=0.3)

        ax.set_title(title, fontsize=14)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.legend()
        plt.tight_layout()

        return Visualizer._save_or_return(fig, save_path)

    @staticmethod
    def plot_scatter(
        x: np.ndarray,
        y: np.ndarray,
        title: str = "Scatter Plot",
        xlabel: str = "x",
        ylabel: str = "y",
        color: str = "blue",
        save_path: Optional[str] = None,
        language: str = "zh",
    ) -> ToolResult:
        """Create a scatter plot.

        Args:
            x: X values
            y: Y values
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            color: Point color
            save_path: Path to save the plot
            language: Language for font configuration

        Returns:
            ToolResult with plot data
        """
        configure_matplotlib(language)
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(x, y, c=color, alpha=0.6, edgecolors="black")

        ax.set_title(title, fontsize=14)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        return Visualizer._save_or_return(fig, save_path)

    @staticmethod
    def plot_bar(
        categories: list,
        values: list,
        title: str = "Bar Chart",
        xlabel: str = "Category",
        ylabel: str = "Value",
        color: str = "steelblue",
        save_path: Optional[str] = None,
        language: str = "zh",
    ) -> ToolResult:
        """Create a bar chart.

        Args:
            categories: Category labels
            values: Bar values
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            color: Bar color
            save_path: Path to save the plot
            language: Language for font configuration

        Returns:
            ToolResult with plot data
        """
        configure_matplotlib(language)
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(categories, values, color=color, edgecolor="black")

        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.01,
                f"{value:.2f}",
                ha="center",
                va="bottom",
                fontsize=10,
            )

        ax.set_title(title, fontsize=14)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        plt.tight_layout()

        return Visualizer._save_or_return(fig, save_path)

    @staticmethod
    def plot_histogram(
        data: np.ndarray,
        bins: int = 30,
        title: str = "Histogram",
        xlabel: str = "Value",
        ylabel: str = "Frequency",
        color: str = "skyblue",
        save_path: Optional[str] = None,
        language: str = "zh",
    ) -> ToolResult:
        """Create a histogram.

        Args:
            data: Data to plot
            bins: Number of bins
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            color: Bar color
            save_path: Path to save the plot
            language: Language for font configuration

        Returns:
            ToolResult with plot data
        """
        configure_matplotlib(language)
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(data, bins=bins, color=color, edgecolor="black", alpha=0.7)

        ax.set_title(title, fontsize=14)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3, axis="y")
        plt.tight_layout()

        return Visualizer._save_or_return(fig, save_path)

    @staticmethod
    def plot_matrix(
        matrix: np.ndarray,
        title: str = "Matrix Visualization",
        cmap: str = "coolwarm",
        save_path: Optional[str] = None,
        language: str = "zh",
    ) -> ToolResult:
        """Visualize a matrix as a heatmap.

        Args:
            matrix: Matrix to visualize
            title: Plot title
            cmap: Colormap
            save_path: Path to save the plot
            language: Language for font configuration

        Returns:
            ToolResult with plot data
        """
        configure_matplotlib(language)
        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(matrix, cmap=cmap, aspect="auto")

        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(
                    j,
                    i,
                    f"{matrix[i, j]:.2f}",
                    ha="center",
                    va="center",
                    color="black"
                    if abs(matrix[i, j]) < np.max(np.abs(matrix)) * 0.5
                    else "white",
                    fontsize=10,
                )

        ax.set_title(title, fontsize=14)
        plt.colorbar(im, ax=ax)
        plt.tight_layout()

        return Visualizer._save_or_return(fig, save_path)

    @staticmethod
    def _save_or_return(fig, save_path: Optional[str]) -> ToolResult:
        """Save figure to file or return as base64.

        Args:
            fig: Matplotlib figure
            save_path: Path to save the figure

        Returns:
            ToolResult with figure data
        """
        try:
            if save_path:
                fig.savefig(save_path, dpi=150, bbox_inches="tight")
                plt.close(fig)
                return ToolResult.ok(data=save_path, metadata={"type": "file"})
            else:
                buf = io.BytesIO()
                fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
                buf.seek(0)
                img_base64 = base64.b64encode(buf.read()).decode("utf-8")
                plt.close(fig)
                return ToolResult.ok(data=img_base64, metadata={"type": "base64"})
        except Exception as e:
            plt.close(fig)
            return ToolResult.fail(f"Visualization error: {e}")
