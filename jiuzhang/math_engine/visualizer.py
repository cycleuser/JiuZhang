"""Visualization engine for JiuZhang.

Provides manim-based visualizations for mathematical concepts.
Each method renders a manim Scene to MP4 (or PNG for last frame) and returns
a ToolResult with the output file path.
"""

import os
import tempfile
from typing import Optional, Callable

import numpy as np
from manim import (
    Scene,
    NumberLine as ManimNumberLine,
    Axes,
    NumberPlane,
    Dot,
    BarChart,
    MathTex,
    Text,
    VGroup,
    Rectangle as ManimRect,
    UP,
    DOWN,
    LEFT,
    RIGHT,
    ORIGIN,
    BLUE,
    RED,
    GREEN,
    YELLOW,
    WHITE,
    BLACK,
    BLUE_D,
    DEGREES,
)

from jiuzhang.visualization.font_config import configure_manim, get_manim_font
from jiuzhang.core.errors import ToolResult, VisualizationError


def _render_scene(scene_cls, output_dir: Optional[str] = None, format: str = "mp4") -> str:
    """Render a manim Scene and return the output file path.

    Args:
        scene_cls: A subclass of Scene to render.
        output_dir: Directory for output files. Defaults to temp dir.
        format: Output format ("mp4" or "png").

    Returns:
        Path to the rendered file.
    """
    from manim import config as manim_config

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="jiuzhang_viz_")

    manim_config.output_file = output_dir
    manim_config.quality = "low_quality"
    manim_config.write_to_movie = format == "mp4"

    scene = scene_cls()
    scene.render()
    return scene.renderer.file_writer.get_movie_path()


class Visualizer:
    """Mathematical visualization engine using manim.

    Automatically configures fonts for proper multi-language support.
    Each method renders a manim scene and returns a ToolResult with the
    path to the output video/image file.
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
        """Plot a number line using manim.

        Args:
            start: Start of number line
            end: End of number line
            highlight: List of numbers to highlight
            title: Plot title
            save_path: Path to save the rendered file
            language: Language for font configuration

        Returns:
            ToolResult with file path to rendered video/image
        """
        configure_manim(language)
        font = get_manim_font(language)
        highlight = highlight or []

        class NumberLineScene(Scene):
            def construct(self_inner):
                number_line = ManimNumberLine(
                    x_range=[start, end, 1],
                    length=10,
                    include_numbers=True,
                    include_tip=True,
                )
                self_inner.add(number_line)

                for h_val in highlight:
                    dot = Dot(number_line.n2p(h_val), color=RED, radius=0.1)
                    label = MathTex(str(h_val), font_size=24).next_to(dot, UP, buff=0.15)
                    self_inner.add(dot, label)

                title_text = Text(title, font=font, font_size=28).to_edge(UP)
                self_inner.add(title_text)

        try:
            output_dir = os.path.dirname(save_path) if save_path else None
            path = _render_scene(NumberLineScene, output_dir=output_dir)

            if save_path:
                import shutil
                shutil.move(path, save_path)
                return ToolResult.ok(data=save_path, metadata={"type": "file", "format": "mp4"})
            else:
                return ToolResult.ok(data=path, metadata={"type": "file", "format": "mp4"})
        except Exception as e:
            return ToolResult.fail(f"Visualization error: {e}")

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
        """Plot a mathematical function using manim.

        Args:
            func: Function to plot
            x_range: Range of x values
            num_points: Number of points to plot
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            grid: Whether to show grid
            save_path: Path to save the rendered file
            language: Language for font configuration

        Returns:
            ToolResult with file path to rendered video/image
        """
        configure_manim(language)
        font = get_manim_font(language)

        class FunctionScene(Scene):
            def construct(self_inner):
                axes = Axes(
                    x_range=[x_range[0], x_range[1], 1],
                    y_range=[-5, 5, 1],
                    x_length=10,
                    y_length=6,
                    axis_config={"include_numbers": True},
                )
                self_inner.add(axes)

                if grid:
                    grid_plane = NumberPlane(
                        x_range=[x_range[0], x_range[1]],
                        y_range=[-5, 5],
                        background_line_style={"stroke_opacity": 0.3},
                    )
                    self_inner.add(grid_plane)

                curve = axes.plot(func, color=BLUE)
                self_inner.add(curve)

                title_text = Text(title, font=font, font_size=28).to_edge(UP)

                x_label = MathTex(xlabel, font_size=24).next_to(axes.x_axis, DOWN, buff=0.3)
                y_label = MathTex(ylabel, font_size=24).next_to(axes.y_axis, LEFT, buff=0.3).rotate(90 * DEGREES)

                self_inner.add(title_text, x_label, y_label)

        try:
            output_dir = os.path.dirname(save_path) if save_path else None
            path = _render_scene(FunctionScene, output_dir=output_dir)

            if save_path:
                import shutil
                shutil.move(path, save_path)
                return ToolResult.ok(data=save_path, metadata={"type": "file", "format": "mp4"})
            else:
                return ToolResult.ok(data=path, metadata={"type": "file", "format": "mp4"})
        except Exception as e:
            return ToolResult.fail(f"Visualization error: {e}")

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
        """Create a scatter plot using manim.

        Args:
            x: X values
            y: Y values
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            color: Point color name (manim color string)
            save_path: Path to save the rendered file
            language: Language for font configuration

        Returns:
            ToolResult with file path to rendered video/image
        """
        configure_manim(language)
        font = get_manim_font(language)

        color_map = {
            "blue": BLUE,
            "red": RED,
            "green": GREEN,
            "yellow": YELLOW,
        }
        dot_color = color_map.get(color.lower(), BLUE)

        x_min, x_max = float(x.min()), float(x.max())
        y_min, y_max = float(y.min()), float(y.max())
        x_margin = max((x_max - x_min) * 0.1, 0.5)
        y_margin = max((y_max - y_min) * 0.1, 0.5)

        class ScatterScene(Scene):
            def construct(self_inner):
                axes = Axes(
                    x_range=[x_min - x_margin, x_max + x_margin, 1],
                    y_range=[y_min - y_margin, y_max + y_margin, 1],
                    x_length=10,
                    y_length=6,
                    axis_config={"include_numbers": True},
                )
                self_inner.add(axes)

                dots = VGroup()
                for xi, yi in zip(x, y):
                    dot = Dot(axes.c2p(float(xi), float(yi)), color=dot_color, radius=0.06)
                    dots.add(dot)
                self_inner.add(dots)

                title_text = Text(title, font=font, font_size=28).to_edge(UP)
                self_inner.add(title_text)

        try:
            output_dir = os.path.dirname(save_path) if save_path else None
            path = _render_scene(ScatterScene, output_dir=output_dir)

            if save_path:
                import shutil
                shutil.move(path, save_path)
                return ToolResult.ok(data=save_path, metadata={"type": "file", "format": "mp4"})
            else:
                return ToolResult.ok(data=path, metadata={"type": "file", "format": "mp4"})
        except Exception as e:
            return ToolResult.fail(f"Visualization error: {e}")

    @staticmethod
    def plot_bar(
        categories: list,
        values: list,
        title: str = "Bar Chart",
        xlabel: str = "Category",
        ylabel: str = "Value",
        color: str = "blue",
        save_path: Optional[str] = None,
        language: str = "zh",
    ) -> ToolResult:
        """Create a bar chart using manim.

        Args:
            categories: Category labels
            values: Bar values
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            color: Bar color name (manim color string)
            save_path: Path to save the rendered file
            language: Language for font configuration

        Returns:
            ToolResult with file path to rendered video/image
        """
        configure_manim(language)
        font = get_manim_font(language)

        color_map = {
            "blue": BLUE_D,
            "red": RED,
            "green": GREEN,
            "yellow": YELLOW,
            "steelblue": BLUE_D,
        }
        bar_color = color_map.get(color.lower(), BLUE_D)

        class BarScene(Scene):
            def construct(self_inner):
                bar_chart = BarChart(
                    values=values,
                    bar_names=[str(c) for c in categories],
                    y_range=[0, max(values) * 1.2, max(values) / 5 if max(values) > 0 else 1],
                    y_axis_config={"include_numbers": True},
                    bar_colors=[bar_color] * len(categories),
                )
                self_inner.add(bar_chart)

                title_text = Text(title, font=font, font_size=28).to_edge(UP)
                self_inner.add(title_text)

        try:
            output_dir = os.path.dirname(save_path) if save_path else None
            path = _render_scene(BarScene, output_dir=output_dir)

            if save_path:
                import shutil
                shutil.move(path, save_path)
                return ToolResult.ok(data=save_path, metadata={"type": "file", "format": "mp4"})
            else:
                return ToolResult.ok(data=path, metadata={"type": "file", "format": "mp4"})
        except Exception as e:
            return ToolResult.fail(f"Visualization error: {e}")

    @staticmethod
    def plot_histogram(
        data: np.ndarray,
        bins: int = 30,
        title: str = "Histogram",
        xlabel: str = "Value",
        ylabel: str = "Frequency",
        color: str = "blue",
        save_path: Optional[str] = None,
        language: str = "zh",
    ) -> ToolResult:
        """Create a histogram using manim.

        Args:
            data: Data to plot
            bins: Number of bins
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            color: Bar color name
            save_path: Path to save the rendered file
            language: Language for font configuration

        Returns:
            ToolResult with file path to rendered video/image
        """
        configure_manim(language)
        font = get_manim_font(language)

        counts, bin_edges = np.histogram(data, bins=bins)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        color_map = {
            "skyblue": BLUE_D,
            "blue": BLUE_D,
            "red": RED,
            "green": GREEN,
            "yellow": YELLOW,
        }
        bar_color = color_map.get(color.lower(), BLUE_D)

        class HistogramScene(Scene):
            def construct(self_inner):
                bar_chart = BarChart(
                    values=counts.tolist(),
                    bar_names=[f"{c:.1f}" for c in bin_centers[:len(counts)]],
                    y_range=[0, max(counts) * 1.2 if max(counts) > 0 else 1, max(counts) // 5 if max(counts) > 0 else 1],
                    y_axis_config={"include_numbers": True},
                    bar_colors=[bar_color] * len(counts),
                )
                self_inner.add(bar_chart)

                title_text = Text(title, font=font, font_size=28).to_edge(UP)
                self_inner.add(title_text)

        try:
            output_dir = os.path.dirname(save_path) if save_path else None
            path = _render_scene(HistogramScene, output_dir=output_dir)

            if save_path:
                import shutil
                shutil.move(path, save_path)
                return ToolResult.ok(data=save_path, metadata={"type": "file", "format": "mp4"})
            else:
                return ToolResult.ok(data=path, metadata={"type": "file", "format": "mp4"})
        except Exception as e:
            return ToolResult.fail(f"Visualization error: {e}")

    @staticmethod
    def plot_matrix(
        matrix: np.ndarray,
        title: str = "Matrix Visualization",
        cmap: str = "coolwarm",
        save_path: Optional[str] = None,
        language: str = "zh",
    ) -> ToolResult:
        """Visualize a matrix as a heatmap using manim.

        Args:
            matrix: Matrix to visualize
            title: Plot title
            cmap: Colormap name (ignored in manim, uses default gradient)
            save_path: Path to save the rendered file
            language: Language for font configuration

        Returns:
            ToolResult with file path to rendered video/image
        """
        configure_manim(language)
        font = get_manim_font(language)

        class MatrixScene(Scene):
            def construct(self_inner):
                rows, cols = matrix.shape
                cell_size = min(8.0 / cols, 4.0 / rows)

                matrix_group = VGroup()
                labels = VGroup()

                abs_max = max(np.max(np.abs(matrix)), 1e-10)

                for i in range(rows):
                    for j in range(cols):
                        val = matrix[i, j]
                        intensity = abs(val) / abs_max

                        rect = ManimRect(
                            width=cell_size,
                            height=cell_size * 0.6,
                            fill_opacity=min(intensity * 0.8 + 0.2, 1.0),
                            fill_color=RED if val > 0 else BLUE if val < 0 else WHITE,
                            stroke_color=BLACK,
                            stroke_width=1,
                        )

                        pos_x = (j - cols / 2 + 0.5) * cell_size
                        pos_y = (rows / 2 - i - 0.5) * cell_size * 0.6
                        rect.move_to([pos_x, pos_y, 0])
                        matrix_group.add(rect)

                        val_text = MathTex(f"{val:.2f}", font_size=int(cell_size * 12))
                        val_text.move_to(rect)
                        labels.add(val_text)

                self_inner.add(matrix_group, labels)

                title_text = Text(title, font=font, font_size=28).to_edge(UP)
                self_inner.add(title_text)

        try:
            output_dir = os.path.dirname(save_path) if save_path else None
            path = _render_scene(MatrixScene, output_dir=output_dir)

            if save_path:
                import shutil
                shutil.move(path, save_path)
                return ToolResult.ok(data=save_path, metadata={"type": "file", "format": "mp4"})
            else:
                return ToolResult.ok(data=path, metadata={"type": "file", "format": "mp4"})
        except Exception as e:
            return ToolResult.fail(f"Visualization error: {e}")

    @staticmethod
    def _save_or_return(scene_cls, save_path: Optional[str]) -> ToolResult:
        """Render a manim Scene class and return ToolResult.

        Args:
            scene_cls: A manim Scene subclass
            save_path: Path to save the render

        Returns:
            ToolResult with file path
        """
        try:
            output_dir = os.path.dirname(save_path) if save_path else None
            path = _render_scene(scene_cls, output_dir=output_dir)

            if save_path:
                import shutil
                shutil.move(path, save_path)
                return ToolResult.ok(data=save_path, metadata={"type": "file", "format": "mp4"})
            else:
                return ToolResult.ok(data=path, metadata={"type": "file", "format": "mp4"})
        except Exception as e:
            return ToolResult.fail(f"Visualization error: {e}")