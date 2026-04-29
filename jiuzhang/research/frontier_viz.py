"""Advanced Visualization for Frontier Mathematics.

3D surfaces, manifolds, spectral sequences, and other advanced visualizations.
Uses manim for high-quality mathematical animations.
"""

import numpy as np
from typing import Optional
import os
import tempfile

from manim import (
    Scene,
    ThreeDScene,
    ThreeDAxes,
    Surface,
    NumberPlane,
    Arrow,
    Dot,
    VGroup,
    Text,
    MathTex,
    ImageMobject,
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
    PI,
    DEGREES,
    Create,
    Write,
)

from jiuzhang.visualization.font_config import configure_manim, get_manim_font
from jiuzhang.math_engine.visualizer import _render_scene


class FrontierVisualizer:
    """Advanced visualizations for frontier mathematics using manim."""

    @staticmethod
    def plot_3d_surface(
        func,
        x_range=(-5, 5),
        y_range=(-5, 5),
        resolution=100,
        title="3D Surface",
        cmap="viridis",
        language="zh",
    ) -> Optional[str]:
        """Plot a 3D surface using manim.

        Args:
            func: Function f(x, y)
            x_range: x range tuple
            y_range: y range tuple
            resolution: Grid resolution
            title: Plot title
            cmap: Colormap name (manim uses fill_color instead)
            language: Language for font configuration

        Returns:
            Path to rendered MP4 file or None
        """
        try:
            configure_manim(language)
            font = get_manim_font(language)

            class SurfaceScene(ThreeDScene):
                def construct(self_inner):
                    self_inner.set_camera_orientation(phi=75 * DEGREES, theta=30 * DEGREES)

                    axes = ThreeDAxes(
                        x_range=[x_range[0], x_range[1], 1],
                        y_range=[y_range[0], y_range[1], 1],
                        z_range=[-5, 5, 1],
                    )
                    self_inner.add(axes)

                    surface = Surface(
                        lambda u, v: axes.c2p(u, v, func(u, v)),
                        u_range=[x_range[0], x_range[1]],
                        v_range=[y_range[0], y_range[1]],
                        resolution=(resolution // 5, resolution // 5),
                        fill_opacity=0.8,
                        fill_color=BLUE,
                    )
                    self_inner.add(surface)

                    title_text = Text(title, font=font, font_size=28).to_edge(UP)
                    self_inner.add_fixed_in_frame_mobjects(title_text)

            path = _render_scene(SurfaceScene)
            return path
        except Exception as e:
            import logging
            logging.warning(f"Error in plot_3d_surface: {e}")
            return None

    @staticmethod
    def plot_torus(
        major_radius=3, minor_radius=1, resolution=50, language="zh"
    ) -> Optional[str]:
        """Plot a torus (donut shape) using manim.

        Args:
            major_radius: Distance from center of tube to center of torus
            minor_radius: Radius of the tube
            resolution: Grid resolution
            language: Language for font configuration

        Returns:
            Path to rendered MP4 file or None
        """
        try:
            configure_manim(language)
            font = get_manim_font(language)

            R, r = major_radius, minor_radius

            class TorusScene(ThreeDScene):
                def construct(self_inner):
                    self_inner.set_camera_orientation(phi=75 * DEGREES, theta=30 * DEGREES)

                    torus = Surface(
                        lambda u, v: np.array([
                            (R + r * np.cos(v)) * np.cos(u),
                            (R + r * np.cos(v)) * np.sin(u),
                            r * np.sin(v),
                        ]),
                        u_range=[0, 2 * PI],
                        v_range=[0, 2 * PI],
                        resolution=(resolution // 3, resolution // 3),
                        fill_opacity=0.8,
                        fill_color=BLUE,
                    )
                    self_inner.add(torus)

                    title = "环面 (Torus)" if language == "zh" else "Torus"
                    title_text = Text(title, font=font, font_size=28).to_edge(UP)
                    self_inner.add_fixed_in_frame_mobjects(title_text)

            path = _render_scene(TorusScene)
            return path
        except Exception as e:
            import logging
            logging.warning(f"Error in plot_torus: {e}")
            return None

    @staticmethod
    def plot_mobius_strip(width=2, resolution=100, language="zh") -> Optional[str]:
        """Plot a Möbius strip using manim.

        Args:
            width: Width of the strip
            resolution: Grid resolution
            language: Language for font configuration

        Returns:
            Path to rendered MP4 file or None
        """
        try:
            configure_manim(language)
            font = get_manim_font(language)
            w = width / 2

            class MobiusScene(ThreeDScene):
                def construct(self_inner):
                    self_inner.set_camera_orientation(phi=75 * DEGREES, theta=30 * DEGREES)

                    mobius = Surface(
                        lambda u, v: np.array([
                            (1 + v * np.cos(u / 2)) * np.cos(u),
                            (1 + v * np.cos(u / 2)) * np.sin(u),
                            v * np.sin(u / 2),
                        ]),
                        u_range=[0, 2 * PI],
                        v_range=[-0.5, 0.5],
                        resolution=(resolution // 3, resolution // 6),
                        fill_opacity=0.9,
                        fill_color=YELLOW,
                    )
                    self_inner.add(mobius)

                    title = "莫比乌斯带 (Möbius Strip)" if language == "zh" else "Möbius Strip"
                    title_text = Text(title, font=font, font_size=28).to_edge(UP)
                    self_inner.add_fixed_in_frame_mobjects(title_text)

            path = _render_scene(MobiusScene)
            return path
        except Exception as e:
            import logging
            logging.warning(f"Error in plot_mobius_strip: {e}")
            return None

    @staticmethod
    def plot_klein_bottle(resolution=50, language="zh") -> Optional[str]:
        """Plot a Klein bottle (figure-8 immersion) using manim.

        Args:
            resolution: Grid resolution
            language: Language for font configuration

        Returns:
            Path to rendered MP4 file or None
        """
        try:
            configure_manim(language)
            font = get_manim_font(language)

            class KleinBottleScene(ThreeDScene):
                def construct(self_inner):
                    self_inner.set_camera_orientation(phi=75 * DEGREES, theta=30 * DEGREES)

                    def klein_func(u, v):
                        r_val = 3 * (1 + 0.3 * np.cos(u))
                        x = r_val * np.cos(v)
                        y = r_val * np.sin(v)
                        z = 2 * np.sin(u) + np.sin(v) * np.cos(u)
                        return np.array([x, y, z])

                    klein = Surface(
                        klein_func,
                        u_range=[0, 2 * PI],
                        v_range=[0, 2 * PI],
                        resolution=(resolution // 3, resolution // 3),
                        fill_opacity=0.8,
                        fill_color=BLUE,
                    )
                    self_inner.add(klein)

                    title = "克莱因瓶 (Klein Bottle)" if language == "zh" else "Klein Bottle"
                    title_text = Text(title, font=font, font_size=28).to_edge(UP)
                    self_inner.add_fixed_in_frame_mobjects(title_text)

            path = _render_scene(KleinBottleScene)
            return path
        except Exception as e:
            import logging
            logging.warning(f"Error in plot_klein_bottle: {e}")
            return None

    @staticmethod
    def plot_vector_field(
        func_x,
        func_y,
        x_range=(-3, 3),
        y_range=(-3, 3),
        grid_size=15,
        title="Vector Field",
        language="zh",
    ) -> Optional[str]:
        """Plot a 2D vector field using manim.

        Args:
            func_x: Function for x-component
            func_y: Function for y-component
            x_range: x range
            y_range: y range
            grid_size: Grid size
            title: Plot title
            language: Language for font configuration

        Returns:
            Path to rendered MP4 file or None
        """
        try:
            configure_manim(language)
            font = get_manim_font(language)

            class VectorFieldScene(Scene):
                def construct(self_inner):
                    x_vals = np.linspace(x_range[0], x_range[1], grid_size)
                    y_vals = np.linspace(y_range[0], y_range[1], grid_size)

                    axes = NumberPlane(
                        x_range=[x_range[0], x_range[1], 0.5],
                        y_range=[y_range[0], y_range[1], 0.5],
                        background_line_style={"stroke_opacity": 0.3},
                    )
                    self_inner.add(axes)

                    arrows = VGroup()
                    for xi in x_vals[::2]:
                        for yi in y_vals[::2]:
                            vx = func_x(xi, yi)
                            vy = func_y(xi, yi)
                            mag = np.sqrt(vx**2 + vy**2)
                            if mag > 0.01:
                                scale = min(0.3, 0.3 / mag)
                                arrow = Arrow(
                                    start=axes.c2p(xi, yi),
                                    end=axes.c2p(xi + vx * scale, yi + vy * scale),
                                    buff=0,
                                    color=BLUE,
                                    stroke_width=2,
                                )
                                arrows.add(arrow)

                    self_inner.add(arrows)

                    title_text = Text(title, font=font, font_size=28).to_edge(UP)
                    self_inner.add(title_text)

            path = _render_scene(VectorFieldScene)
            return path
        except Exception as e:
            import logging
            logging.warning(f"Error in plot_vector_field: {e}")
            return None

    @staticmethod
    def plot_complex_function(
        func,
        x_range=(-3, 3),
        y_range=(-3, 3),
        resolution=200,
        title="Complex Function",
        language="zh",
    ) -> Optional[str]:
        """Plot a complex function using domain coloring with manim.

        Args:
            func: Complex function f(z)
            x_range: Real part range
            y_range: Imaginary part range
            resolution: Grid resolution
            title: Plot title
            language: Language for font configuration

        Returns:
            Path to rendered MP4 file or None
        """
        try:
            configure_manim(language)
            font = get_manim_font(language)

            class ComplexFunctionScene(Scene):
                def construct(self_inner):
                    axes = NumberPlane(
                        x_range=[x_range[0], x_range[1]],
                        y_range=[y_range[0], y_range[1]],
                        background_line_style={"stroke_opacity": 0.2},
                    )
                    self_inner.add(axes)

                    x = np.linspace(x_range[0], x_range[1], min(resolution // 2, 80))
                    y = np.linspace(y_range[0], y_range[1], min(resolution // 2, 80))
                    X, Y = np.meshgrid(x, y)
                    Z = X + 1j * Y
                    W = func(Z)

                    from manim import ImageMobject
                    from PIL import Image as PILImage

                    hue = (np.angle(W) / (2 * np.pi) + 1) % 1
                    saturation = np.ones_like(hue) * 0.8
                    value = np.clip(np.abs(W) / np.max(np.abs(W) + 1e-10), 0, 1)
                    value = 1 - 1.0 / (1 + value * 3)

                    import colorsys
                    rgb_array = np.zeros((len(y), len(x), 3))
                    for i in range(len(y)):
                        for j in range(len(x)):
                            r, g, b = colorsys.hsv_to_rgb(hue[i, j], saturation[i, j], value[i, j])
                            rgb_array[i, j] = [r * 255, g * 255, b * 255]

                    img = PILImage.fromarray(rgb_array.astype(np.uint8))
                    img_path = os.path.join(tempfile.mkdtemp(), "complex_domain.png")
                    img.save(img_path)

                    domain_img = ImageMobject(img_path)
                    domain_img.height = 6
                    domain_img.move_to(ORIGIN)
                    self_inner.add(domain_img)

                    title_text = Text(title, font=font, font_size=28).to_edge(UP)
                    self_inner.add(title_text)

            path = _render_scene(ComplexFunctionScene)
            return path
        except Exception as e:
            import logging
            logging.warning(f"Error in plot_complex_function: {e}")
            return None

    @staticmethod
    def plot_root_system(root_type="A2", language="zh") -> Optional[str]:
        """Plot a root system using manim.

        Args:
            root_type: Root system type (A2, B2, G2)
            language: Language for font configuration

        Returns:
            Path to rendered MP4 file or None
        """
        try:
            configure_manim(language)
            font = get_manim_font(language)

            if root_type == "A2":
                angles = np.array([0, 60, 120, 180, 240, 300]) * np.pi / 180
                roots = np.array([[np.cos(a), np.sin(a)] for a in angles])
            elif root_type == "B2":
                long_roots = np.array([[1, 0], [-1, 0], [0, 1], [0, -1]])
                short_roots = np.array([[1, 1], [1, -1], [-1, 1], [-1, -1]]) / np.sqrt(2)
                roots = np.vstack([long_roots, short_roots])
            elif root_type == "G2":
                angles_60 = np.array([0, 60, 120, 180, 240, 300]) * np.pi / 180
                long_roots = np.array([[np.cos(a), np.sin(a)] for a in angles_60])
                short_roots = np.array([
                    [np.cos((a + 30) * np.pi / 180), np.sin((a + 30) * np.pi / 180)]
                    for a in [0, 60, 120, 180, 240, 300]
                ]) * np.sqrt(3) / 2
                roots = np.vstack([long_roots, short_roots])
            else:
                angles = np.array([0, 60, 120, 180, 240, 300]) * np.pi / 180
                roots = np.array([[np.cos(a), np.sin(a)] for a in angles])

            class RootSystemScene(Scene):
                def construct(self_inner):
                    axes = NumberPlane(
                        x_range=[-1.8, 1.8],
                        y_range=[-1.8, 1.8],
                        background_line_style={"stroke_opacity": 0.2},
                    )
                    self_inner.add(axes)

                    arrows = VGroup()
                    for root in roots:
                        arrow = Arrow(
                            start=axes.c2p(0, 0),
                            end=axes.c2p(float(root[0]), float(root[1])),
                            buff=0,
                            color=BLUE,
                            stroke_width=3,
                        )
                        arrows.add(arrow)

                    self_inner.add(arrows)

                    dots = VGroup(*[
                        Dot(axes.c2p(float(r[0]), float(r[1])), color=RED, radius=0.06)
                        for r in roots
                    ])
                    self_inner.add(dots)

                    title = f"{root_type} 根系" if language == "zh" else f"{root_type} Root System"
                    title_text = Text(title, font=font, font_size=28).to_edge(UP)
                    self_inner.add(title_text)

            path = _render_scene(RootSystemScene)
            return path
        except Exception as e:
            import logging
            logging.warning(f"Error in plot_root_system: {e}")
            return None

    @staticmethod
    def plot_fractal(
        mandelbrot=True,
        x_range=(-2, 1),
        y_range=(-1.5, 1.5),
        resolution=500,
        max_iter=100,
        language="zh",
    ) -> Optional[str]:
        """Plot a fractal (Mandelbrot or Julia set) using manim.

        Args:
            mandelbrot: True for Mandelbrot, False for Julia
            x_range: Real part range
            y_range: Imaginary part range
            resolution: Grid resolution
            max_iter: Maximum iterations
            language: Language for font configuration

        Returns:
            Path to rendered MP4 file or None
        """
        try:
            configure_manim(language)
            font = get_manim_font(language)

            res = min(resolution // 2, 200)
            x = np.linspace(x_range[0], x_range[1], res)
            y = np.linspace(y_range[0], y_range[1], res)
            C = x[:, np.newaxis] + 1j * y[np.newaxis, :]

            if mandelbrot:
                Z = np.zeros_like(C)
            else:
                Z = C.copy()
                C = -0.4 + 0.6j

            M = np.zeros(C.shape, dtype=int)
            for i in range(max_iter):
                mask = np.abs(Z) < 2
                Z[mask] = Z[mask] ** 2 + C[mask]
                M[mask] = i

            class FractalScene(Scene):
                def construct(self_inner):
                    from manim import ImageMobject
                    from PIL import Image as PILImage

                    hue = (M.T / max_iter * 0.7 + 0.8) % 1.0
                    sat = np.ones_like(hue)
                    val = np.ones_like(hue) * 0.9
                    val[M.T == max_iter] = 0

                    import colorsys
                    rgb_array = np.zeros((*hue.shape, 3))
                    for i in range(hue.shape[0]):
                        for j in range(hue.shape[1]):
                            r, g, b = colorsys.hsv_to_rgb(hue[i, j], sat[i, j], val[i, j])
                            rgb_array[i, j] = [r * 255, g * 255, b * 255]

                    img = PILImage.fromarray(rgb_array.astype(np.uint8))
                    img_path = os.path.join(tempfile.mkdtemp(), "fractal.png")
                    img.save(img_path)

                    fractal_img = ImageMobject(img_path)
                    fractal_img.height = 6
                    fractal_img.move_to(ORIGIN)
                    self_inner.add(fractal_img)

                    if mandelbrot:
                        title = "曼德博集合 (Mandelbrot Set)" if language == "zh" else "Mandelbrot Set"
                    else:
                        title = "朱利亚集合 (Julia Set)" if language == "zh" else "Julia Set"
                    title_text = Text(title, font=font, font_size=28).to_edge(UP)
                    self_inner.add(title_text)

            path = _render_scene(FractalScene)
            return path
        except Exception as e:
            import logging
            logging.warning(f"Error in plot_fractal: {e}")
            return None