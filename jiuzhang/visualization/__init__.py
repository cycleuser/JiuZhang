"""Visualization module for JiuZhang.

Uses manim for high-quality mathematical visualizations.
Supports both PNG (static) and MP4 (animated) output.
"""

from jiuzhang.visualization.font_config import configure_manim, get_manim_font, get_font_info
from jiuzhang.visualization.renderer import ManimRenderer, RenderResult, get_renderer, render_scene

# Only import manim scenes if manim is available
try:
    from jiuzhang.visualization.manim_scenes import *
    _has_manim_scenes = True
except (ImportError, NameError):
    _has_manim_scenes = False

__all__ = [
    "configure_manim",
    "get_manim_font",
    "get_font_info",
    "ManimRenderer",
    "RenderResult",
    "get_renderer",
    "render_scene",
]
