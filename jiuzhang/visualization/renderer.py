"""Unified renderer for JiuZhang visualizations.

Supports both PNG (static) and MP4 (animated) output from manim scenes.
Provides a simple interface for rendering any manim scene to file.
"""

import os
import tempfile
from typing import Optional, Type
from pathlib import Path

try:
    from manim import Scene, config as manim_config
    HAS_MANIM = True
except ImportError:
    HAS_MANIM = False
    Scene = None  # type: ignore


class RenderResult:
    """Result of a render operation."""

    def __init__(self, success: bool, file_path: Optional[str] = None,
                 format: str = "mp4", error: Optional[str] = None):
        self.success = success
        self.file_path = file_path
        self.format = format
        self.error = error

    @property
    def exists(self) -> bool:
        return self.file_path is not None and os.path.exists(self.file_path)

    def read_bytes(self) -> Optional[bytes]:
        """Read file contents as bytes."""
        if self.exists:
            with open(self.file_path, "rb") as f:
                return f.read()
        return None


class ManimRenderer:
    """Unified manim renderer supporting PNG and MP4 output."""

    def __init__(self, output_dir: Optional[str] = None,
                 quality: str = "low_quality"):
        self.output_dir = output_dir or tempfile.mkdtemp(prefix="jiuzhang_viz_")
        self.quality = quality
        os.makedirs(self.output_dir, exist_ok=True)

    def render(self, scene_cls: Type[Scene], format: str = "mp4",
               output_name: Optional[str] = None) -> RenderResult:
        """Render a manim scene to file.

        Args:
            scene_cls: Manim Scene class to render
            format: Output format ("mp4" or "png")
            output_name: Output filename (without extension)

        Returns:
            RenderResult with file path
        """
        try:
            if format == "png":
                return self._render_png(scene_cls, output_name)
            else:
                return self._render_mp4(scene_cls, output_name)
        except Exception as e:
            return RenderResult(success=False, error=str(e))

    def _render_mp4(self, scene_cls: Type[Scene],
                    output_name: Optional[str] = None) -> RenderResult:
        """Render scene to MP4 video."""
        output_name = output_name or scene_cls.__name__

        manim_config.quality = self.quality
        manim_config.format = "mp4"
        manim_config.write_to_movie = True
        manim_config.disable_caching = True
        manim_config.media_dir = self.output_dir

        scene = scene_cls()
        scene.render()

        movie_path = scene.renderer.file_writer.movie_file_path
        if movie_path and os.path.exists(movie_path):
            return RenderResult(success=True, file_path=movie_path, format="mp4")

        return RenderResult(success=False, error="No output file generated")

    def _render_png(self, scene_cls: Type[Scene],
                    output_name: Optional[str] = None) -> RenderResult:
        """Render scene to PNG image (last frame)."""
        output_name = output_name or scene_cls.__name__

        manim_config.quality = self.quality
        manim_config.format = "png"
        manim_config.write_to_movie = False
        manim_config.save_last_frame = True
        manim_config.disable_caching = True
        manim_config.media_dir = self.output_dir

        scene = scene_cls()
        scene.render()

        # Find the last frame image
        image_dir = os.path.join(self.output_dir, "images", self.quality)
        if os.path.exists(image_dir):
            for f in os.listdir(image_dir):
                if f.endswith(".png") and output_name.lower() in f.lower():
                    return RenderResult(
                        success=True,
                        file_path=os.path.join(image_dir, f),
                        format="png",
                    )

        return RenderResult(success=False, error="No PNG output generated")

    def render_to_base64(self, scene_cls: Type[Scene],
                         format: str = "png") -> Optional[str]:
        """Render scene and return as base64 string.

        Args:
            scene_cls: Manim Scene class
            format: Output format

        Returns:
            Base64 encoded string or None
        """
        import base64
        result = self.render(scene_cls, format=format)
        if result.success:
            data = result.read_bytes()
            if data:
                return base64.b64encode(data).decode("utf-8")
        return None

    def cleanup(self):
        """Remove temporary output files."""
        import shutil
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)


# Global renderer instance
_default_renderer: Optional[ManimRenderer] = None


def get_renderer(output_dir: Optional[str] = None) -> ManimRenderer:
    """Get or create the default renderer."""
    global _default_renderer
    if _default_renderer is None:
        _default_renderer = ManimRenderer(output_dir=output_dir)
    return _default_renderer


def render_scene(scene_cls: Type[Scene], format: str = "mp4",
                 output_name: Optional[str] = None) -> RenderResult:
    """Convenience function to render a scene."""
    renderer = get_renderer()
    return renderer.render(scene_cls, format=format, output_name=output_name)
