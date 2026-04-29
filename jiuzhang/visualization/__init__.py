"""Visualization module for JiuZhang.

Uses manim for high-quality mathematical visualizations.
TUI-based visualizations are in tui_viz.py.
"""

from jiuzhang.visualization.font_config import configure_manim, get_manim_font, get_font_info

__all__ = [
    "configure_manim",
    "get_manim_font",
    "get_font_info",
]