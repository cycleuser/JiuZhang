"""Advanced Visualization for Frontier Mathematics.

3D plots, manifolds, spectral sequences, and other advanced visualizations.
Uses automatic font detection for proper multi-language support.
"""

import numpy as np
from typing import Optional
import io
import base64
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from jiuzhang.visualization.font_config import configure_matplotlib


class FrontierVisualizer:
    """Advanced visualizations for frontier mathematics."""

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
        """Plot a 3D surface.

        Args:
            func: Function f(x, y)
            x_range: x range tuple
            y_range: y range tuple
            resolution: Grid resolution
            title: Plot title
            cmap: Colormap
            language: Language for font configuration

        Returns:
            Base64 encoded image or None
        """
        try:
            configure_matplotlib(language)
            x = np.linspace(x_range[0], x_range[1], resolution)
            y = np.linspace(y_range[0], y_range[1], resolution)
            X, Y = np.meshgrid(x, y)
            Z = func(X, Y)

            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection="3d")
            surf = ax.plot_surface(
                X, Y, Z, cmap=cmap, alpha=0.8, linewidth=0, antialiased=True
            )
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            ax.set_zlabel("z")
            ax.set_title(title)
            fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10)
            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode("utf-8")
            plt.close(fig)
            return img_base64
        except Exception:
            return None

    @staticmethod
    def plot_torus(
        major_radius=3, minor_radius=1, resolution=50, language="zh"
    ) -> Optional[str]:
        """Plot a torus (donut shape).

        Args:
            major_radius: Distance from center of tube to center of torus
            minor_radius: Radius of the tube
            resolution: Grid resolution
            language: Language for font configuration

        Returns:
            Base64 encoded image or None
        """
        try:
            configure_matplotlib(language)
            u = np.linspace(0, 2 * np.pi, resolution)
            v = np.linspace(0, 2 * np.pi, resolution)
            U, V = np.meshgrid(u, v)

            X = (major_radius + minor_radius * np.cos(V)) * np.cos(U)
            Y = (major_radius + minor_radius * np.cos(V)) * np.sin(U)
            Z = minor_radius * np.sin(V)

            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection="3d")
            ax.plot_surface(
                X, Y, Z, cmap="coolwarm", alpha=0.8, linewidth=0, antialiased=True
            )
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            ax.set_zlabel("z")
            ax.set_title("Torus (\u73af\u9762)" if language == "zh" else "Torus")
            ax.set_box_aspect([1, 1, 0.5])
            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode("utf-8")
            plt.close(fig)
            return img_base64
        except Exception:
            return None

    @staticmethod
    def plot_mobius_strip(width=2, resolution=100, language="zh") -> Optional[str]:
        """Plot a Möbius strip.

        Args:
            width: Width of the strip
            resolution: Grid resolution
            language: Language for font configuration

        Returns:
            Base64 encoded image or None
        """
        try:
            configure_matplotlib(language)
            u = np.linspace(0, 2 * np.pi, resolution)
            v = np.linspace(-1, 1, resolution // 2)
            U, V = np.meshgrid(u, v)

            X = (1 + V * np.cos(U / 2)) * np.cos(U)
            Y = (1 + V * np.cos(U / 2)) * np.sin(U)
            Z = V * np.sin(U / 2)

            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection="3d")
            ax.plot_surface(
                X, Y, Z, cmap="plasma", alpha=0.9, linewidth=0, antialiased=True
            )
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            ax.set_zlabel("z")
            ax.set_title(
                "M\u00f6bius Strip (\u83ab\u6bd4\u4e4c\u65af\u5e26)"
                if language == "zh"
                else "Möbius Strip"
            )
            ax.set_box_aspect([1, 1, 0.5])
            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode("utf-8")
            plt.close(fig)
            return img_base64
        except Exception:
            return None

    @staticmethod
    def plot_klein_bottle(resolution=50, language="zh") -> Optional[str]:
        """Plot a Klein bottle (figure-8 immersion).

        Args:
            resolution: Grid resolution
            language: Language for font configuration

        Returns:
            Base64 encoded image or None
        """
        try:
            configure_matplotlib(language)
            u = np.linspace(0, 2 * np.pi, resolution)
            v = np.linspace(0, 2 * np.pi, resolution)
            U, V = np.meshgrid(u, v)

            r = 3 * (1 + 0.3 * np.cos(U))
            X = r * np.cos(V)
            Y = r * np.sin(V)
            Z = 2 * np.sin(U) + np.sin(V) * np.cos(U)

            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection="3d")
            ax.plot_surface(
                X, Y, Z, cmap="viridis", alpha=0.8, linewidth=0, antialiased=True
            )
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            ax.set_zlabel("z")
            ax.set_title(
                "Klein Bottle (\u514b\u83b1\u56e0\u74f6)"
                if language == "zh"
                else "Klein Bottle"
            )
            ax.set_box_aspect([1, 1, 0.5])
            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode("utf-8")
            plt.close(fig)
            return img_base64
        except Exception:
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
        """Plot a 2D vector field.

        Args:
            func_x: Function for x-component
            func_y: Function for y-component
            x_range: x range
            y_range: y range
            grid_size: Grid size
            title: Plot title
            language: Language for font configuration

        Returns:
            Base64 encoded image or None
        """
        try:
            configure_matplotlib(language)
            x = np.linspace(x_range[0], x_range[1], grid_size)
            y = np.linspace(y_range[0], y_range[1], grid_size)
            X, Y = np.meshgrid(x, y)
            U = func_x(X, Y)
            V = func_y(X, Y)

            fig, ax = plt.subplots(figsize=(8, 8))
            ax.quiver(
                X, Y, U, V, np.sqrt(U**2 + V**2), cmap="plasma", scale=30, width=0.003
            )
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            ax.set_title(title)
            ax.set_aspect("equal")
            ax.grid(True, alpha=0.3)
            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode("utf-8")
            plt.close(fig)
            return img_base64
        except Exception:
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
        """Plot a complex function using domain coloring.

        Args:
            func: Complex function f(z)
            x_range: Real part range
            y_range: Imaginary part range
            resolution: Grid resolution
            title: Plot title
            language: Language for font configuration

        Returns:
            Base64 encoded image or None
        """
        try:
            configure_matplotlib(language)
            x = np.linspace(x_range[0], x_range[1], resolution)
            y = np.linspace(y_range[0], y_range[1], resolution)
            X, Y = np.meshgrid(x, y)
            Z = X + 1j * Y

            W = func(Z)

            # Domain coloring
            hue = np.angle(W) / (2 * np.pi)
            hue = (hue + 1) % 1
            saturation = np.ones_like(hue)
            value = np.clip(np.abs(W), 0, 10) / 10

            import matplotlib.colors as mcolors

            hsv = np.stack([hue, saturation, value], axis=-1)
            rgb = mcolors.hsv_to_rgb(hsv)

            fig, ax = plt.subplots(figsize=(8, 8))
            ax.imshow(
                rgb,
                extent=[x_range[0], x_range[1], y_range[0], y_range[1]],
                origin="lower",
                aspect="equal",
            )
            ax.set_xlabel("Re(z)")
            ax.set_ylabel("Im(z)")
            ax.set_title(title)
            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode("utf-8")
            plt.close(fig)
            return img_base64
        except Exception:
            return None

    @staticmethod
    def plot_root_system(root_type="A2", language="zh") -> Optional[str]:
        """Plot a root system.

        Args:
            root_type: Root system type (A2, B2, G2)
            language: Language for font configuration

        Returns:
            Base64 encoded image or None
        """
        try:
            configure_matplotlib(language)
            fig, ax = plt.subplots(figsize=(8, 8))

            if root_type == "A2":
                # A2 root system (6 roots)
                angles = np.array([0, 60, 120, 180, 240, 300]) * np.pi / 180
                roots = np.array([[np.cos(a), np.sin(a)] for a in angles])
            elif root_type == "B2":
                # B2 root system (8 roots)
                angles = np.array([0, 45, 90, 135, 180, 225, 270, 315]) * np.pi / 180
                roots = np.array([[np.cos(a), np.sin(a)] for a in angles])
                roots = np.vstack([roots, [[0, 0]]])
            else:
                # Default: A2
                angles = np.array([0, 60, 120, 180, 240, 300]) * np.pi / 180
                roots = np.array([[np.cos(a), np.sin(a)] for a in angles])

            ax.quiver(
                np.zeros(len(roots)),
                np.zeros(len(roots)),
                roots[:, 0],
                roots[:, 1],
                angles="xy",
                scale_units="xy",
                scale=1,
                color="steelblue",
                width=0.005,
            )

            ax.set_xlim(-1.5, 1.5)
            ax.set_ylim(-1.5, 1.5)
            ax.set_aspect("equal")
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color="k", linewidth=0.5)
            ax.axvline(x=0, color="k", linewidth=0.5)
            root_name = (
                f"{root_type} \u6839\u7cfb"
                if language == "zh"
                else f"{root_type} Root System"
            )
            ax.set_title(root_name)
            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode("utf-8")
            plt.close(fig)
            return img_base64
        except Exception:
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
        """Plot a fractal (Mandelbrot or Julia set).

        Args:
            mandelbrot: True for Mandelbrot, False for Julia
            x_range: Real part range
            y_range: Imaginary part range
            resolution: Grid resolution
            max_iter: Maximum iterations
            language: Language for font configuration

        Returns:
            Base64 encoded image or None
        """
        try:
            configure_matplotlib(language)
            x = np.linspace(x_range[0], x_range[1], resolution)
            y = np.linspace(y_range[0], y_range[1], resolution)
            X, Y = np.meshgrid(x, y)
            C = X + 1j * Y

            if mandelbrot:
                Z = np.zeros_like(C)
            else:
                Z = C.copy()
                C = -0.4 + 0.6j  # Julia set parameter

            M = np.zeros(C.shape, dtype=int)

            for i in range(max_iter):
                mask = np.abs(Z) < 2
                Z[mask] = Z[mask] ** 2 + C[mask]
                M[mask] = i

            fig, ax = plt.subplots(figsize=(10, 8))
            ax.imshow(
                M,
                extent=[x_range[0], x_range[1], y_range[0], y_range[1]],
                cmap="magma",
                origin="lower",
                aspect="equal",
            )
            ax.set_xlabel("Re(z)")
            ax.set_ylabel("Im(z)")
            title = (
                (
                    "Mandelbrot Set (\u66fc\u5fb7\u535a\u96c6\u5408)"
                    if language == "zh"
                    else "Mandelbrot Set"
                )
                if mandelbrot
                else (
                    "Julia Set (\u6731\u5229\u4e9a\u96c6\u5408)"
                    if language == "zh"
                    else "Julia Set"
                )
            )
            ax.set_title(title)
            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode("utf-8")
            plt.close(fig)
            return img_base64
        except Exception:
            return None
