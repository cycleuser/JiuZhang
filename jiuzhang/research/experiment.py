"""Enhanced experiment design module.

Generates complete, runnable experiments with auto-execution,
result analysis, and comprehensive visualizations.
"""

import numpy as np
from typing import Optional

from jiuzhang.core.config import Config
from jiuzhang.core.multi_provider_api import MultiProviderClient
from jiuzhang.math_engine.visualizer import Visualizer


class ExperimentDesigner:
    """Enhanced experiment designer with auto-execution."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.client = MultiProviderClient(self.config)

    def design(self, topic: str, language: str = "zh", depth: str = "medium") -> list:
        """Design comprehensive experiments for the research topic.

        Args:
            topic: Research topic
            language: Output language
            depth: Experiment depth

        Returns:
            List of experiment dictionaries with code and expected results
        """
        experiments = []

        # Generate built-in code experiments based on topic
        builtin_experiments = self._generate_builtin_experiments(topic, language)
        experiments.extend(builtin_experiments)

        # Generate AI-designed experiments
        ai_experiments = self._ai_experiment_design(topic, language, depth)
        experiments.extend(ai_experiments)

        return experiments

    def _generate_builtin_experiments(self, topic: str, language: str) -> list:
        """Generate built-in experiments based on topic keywords."""
        experiments = []

        # Fourier analysis experiments
        if "傅里叶" in topic or "fourier" in topic.lower():
            experiments.append(
                {
                    "title": "傅里叶级数收敛性分析"
                    if language == "zh"
                    else "Fourier Series Convergence Analysis",
                    "description": "研究傅里叶级数逼近不同函数的收敛速度和吉布斯现象"
                    if language == "zh"
                    else "Study convergence rate and Gibbs phenomenon of Fourier series",
                    "code": '''from manim import *
import numpy as np

def fourier_square_wave(x, n_terms):
    result = np.zeros_like(x)
    for n in range(1, 2*n_terms, 2):
        result += (4 / (n * np.pi)) * np.sin(n * x)
    return result

def fourier_sawtooth(x, n_terms):
    result = np.zeros_like(x)
    for n in range(1, n_terms + 1):
        result += (2 * (-1)**(n+1) / (n * np.pi)) * np.sin(n * x)
    return result

class FourierSquareWaveScene(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-2*np.pi, 2*np.pi, np.pi],
            y_range=[-1.5, 1.5, 0.5],
            x_length=10,
            y_length=6,
        ).add_coordinates()
        grid = NumberPlane(
            x_range=[-2*np.pi, 2*np.pi, np.pi],
            y_range=[-1.5, 1.5, 0.5],
            x_length=10,
            y_length=6,
        )
        x_vals = np.linspace(-2*np.pi, 2*np.pi, 2000)
        for n in [1, 3, 10]:
            y_vals = fourier_square_wave(x_vals, n)
            curve = axes.plot_line_graph(x_vals, y_vals, line_color=BLUE)
            label = Text(f"Square Wave (n={n})").to_edge(UP)
            self.add(axes, grid, curve, label)
            self.wait(1)
            self.remove(curve, label)

class FourierSawtoothScene(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-2*np.pi, 2*np.pi, np.pi],
            y_range=[-1.5, 1.5, 0.5],
            x_length=10,
            y_length=6,
        ).add_coordinates()
        grid = NumberPlane(
            x_range=[-2*np.pi, 2*np.pi, np.pi],
            y_range=[-1.5, 1.5, 0.5],
            x_length=10,
            y_length=6,
        )
        x_vals = np.linspace(-2*np.pi, 2*np.pi, 2000)
        for n in [1, 5, 20]:
            y_vals = fourier_sawtooth(x_vals, n)
            curve = axes.plot_line_graph(x_vals, y_vals, line_color=YELLOW)
            label = Text(f"Sawtooth Wave (n={n})").to_edge(UP)
            self.add(axes, grid, curve, label)
            self.wait(1)
            self.remove(curve, label)

class FourierConvergenceRateScene(Scene):
    def construct(self):
        ns = np.arange(1, 50)
        errors = []
        x_test = np.pi / 4
        for n in ns:
            approx = fourier_square_wave(np.array([x_test]), n)[0]
            exact = 1.0
            errors.append(abs(approx - exact))
        axes = Axes(
            x_range=[0, 50, 5],
            y_range=[0, max(errors)*1.1, max(errors)/5],
            x_length=10,
            y_length=6,
        ).add_coordinates()
        curve = axes.plot_line_graph(ns, np.array(errors), line_color=BLUE)
        title = Text("Convergence Rate at x=pi/4").to_edge(UP)
        x_label = Text("Number of Terms (n)").next_to(axes, DOWN)
        self.add(axes, curve, title, x_label)

# Render: manim -pql <filename> FourierSquareWaveScene
# Render: manim -pql <filename> FourierSawtoothScene
# Render: manim -pql <filename> FourierConvergenceRateScene''',
                    "expected_output": "收敛速度图、吉布斯现象可视化",
                }
            )

            experiments.append(
                {
                    "title": "傅里叶变换频谱分析"
                    if language == "zh"
                    else "Fourier Transform Spectrum Analysis",
                    "description": "使用 FFT 分析信号的频域特性"
                    if language == "zh"
                    else "Analyze signal frequency characteristics using FFT",
                    "code": """from manim import *
import numpy as np

fs = 1000
t = np.arange(0, 1, 1/fs)
f1, f2, f3 = 50, 120, 200

signal = (np.sin(2*np.pi*f1*t) +
          0.5*np.sin(2*np.pi*f2*t) +
          0.3*np.sin(2*np.pi*f3*t) +
          0.5*np.random.randn(len(t)))

N = len(signal)
Y = np.fft.fft(signal)
P2 = np.abs(Y/N)
P1 = P2[:N//2]
P1[1:-1] = 2*P1[1:-1]
f = fs*np.arange(0, N//2)/N

class TimeDomainScene(Scene):
    def construct(self):
        axes = Axes(
            x_range=[0, t[199], 0.02],
            y_range=[-3, 3, 1],
            x_length=10,
            y_length=5,
        ).add_coordinates()
        grid = NumberPlane(
            x_range=[0, t[199], 0.02],
            y_range=[-3, 3, 1],
            x_length=10,
            y_length=5,
        )
        curve = axes.plot_line_graph(t[:200], signal[:200], line_color=BLUE)
        title = Text("Time Domain Signal").to_edge(UP)
        x_label = Text("Time (s)").next_to(axes, DOWN)
        self.add(axes, grid, curve, title, x_label)

class FrequencySpectrumScene(Scene):
    def construct(self):
        axes = Axes(
            x_range=[0, 300, 50],
            y_range=[0, float(P1.max())*1.1, 0.1],
            x_length=10,
            y_length=5,
        ).add_coordinates()
        grid = NumberPlane(
            x_range=[0, 300, 50],
            y_range=[0, float(P1.max())*1.1, 0.1],
            x_length=10,
            y_length=5,
        )
        mask = f <= 300
        curve = axes.plot_line_graph(f[mask], P1[mask], line_color=RED)
        title = Text("Frequency Spectrum (FFT)").to_edge(UP)
        x_label = Text("Frequency (Hz)").next_to(axes, DOWN)
        y_label = Text("|P1(f)|").next_to(axes, LEFT)
        self.add(axes, grid, curve, title, x_label, y_label)

# Render: manim -pql <filename> TimeDomainScene
# Render: manim -pql <filename> FrequencySpectrumScene""",
                    "expected_output": "时域信号图、频域频谱图",
                }
            )

        # Derivative experiments
        if "导数" in topic or "derivative" in topic.lower() or "微分" in topic:
            experiments.append(
                {
                    "title": "数值导数精度分析"
                    if language == "zh"
                    else "Numerical Derivative Accuracy Analysis",
                    "description": "比较不同数值微分方法的精度和收敛性"
                    if language == "zh"
                    else "Compare accuracy and convergence of numerical differentiation methods",
                    "code": """from manim import *
import numpy as np

def forward_diff(f, x, h):
    return (f(x + h) - f(x)) / h

def central_diff(f, x, h):
    return (f(x + h) - f(x - h)) / (2*h)

def five_point(f, x, h):
    return (-f(x+2*h) + 8*f(x+h) - 8*f(x-h) + f(x-2*h)) / (12*h)

f = lambda x: np.sin(x) * np.exp(-x/5)
f_prime = lambda x: np.cos(x)*np.exp(-x/5) - 0.2*np.sin(x)*np.exp(-x/5)

x = 1.0
hs = np.logspace(-10, -1, 50)

errors_forward = []
errors_central = []
errors_five = []

for h in hs:
    errors_forward.append(abs(forward_diff(f, x, h) - f_prime(x)))
    errors_central.append(abs(central_diff(f, x, h) - f_prime(x)))
    errors_five.append(abs(five_point(f, x, h) - f_prime(x)))

class DerivativeAccuracyScene(Scene):
    def construct(self):
        axes = Axes(
            x_range=[1e-10, 1e-1, 1e-2],
            y_range=[1e-16, 1, 1e-2],
            x_length=10,
            y_length=6,
            x_axis_config={"scaling": LogBase(base=10)},
            y_axis_config={"scaling": LogBase(base=10)},
        ).add_coordinates()
        grid = NumberPlane(
            x_range=[1e-10, 1e-1, 1e-2],
            y_range=[1e-16, 1, 1e-2],
            x_length=10,
            y_length=6,
            x_axis_config={"scaling": LogBase(base=10)},
            y_axis_config={"scaling": LogBase(base=10)},
        )
        curve_fwd = axes.plot_line_graph(hs, np.array(errors_forward), line_color=RED)
        curve_cen = axes.plot_line_graph(hs, np.array(errors_central), line_color=GREEN)
        curve_fiv = axes.plot_line_graph(hs, np.array(errors_five), line_color=BLUE)
        labels = VGroup(
            Text("Forward Difference O(h)", color=RED, font_size=24),
            Text("Central Difference O(h^2)", color=GREEN, font_size=24),
            Text("Five-Point O(h^4)", color=BLUE, font_size=24),
        ).arrange(DOWN, aligned_edge=LEFT).to_edge(RIGHT)
        title = Text("Numerical Derivative Accuracy Comparison").to_edge(UP)
        x_label = Text("Step Size (h)").next_to(axes, DOWN)
        y_label = Text("Error").next_to(axes, LEFT)
        self.add(axes, grid, curve_fwd, curve_cen, curve_fiv, labels, title, x_label, y_label)

# Render: manim -pql <filename> DerivativeAccuracyScene""",
                    "expected_output": "数值微分精度对比图",
                }
            )

        # Integral experiments
        if "积分" in topic or "integral" in topic.lower():
            experiments.append(
                {
                    "title": "数值积分方法比较"
                    if language == "zh"
                    else "Numerical Integration Methods Comparison",
                    "description": "比较矩形法、梯形法、辛普森法的精度和收敛速度"
                    if language == "zh"
                    else "Compare accuracy and convergence of rectangle, trapezoidal, and Simpson's methods",
                    "code": """from manim import *
import numpy as np
from scipy import integrate

def rectangle_method(f, a, b, n):
    h = (b - a) / n
    return sum(f(a + (i+0.5)*h) for i in range(n)) * h

def trapezoidal_method(f, a, b, n):
    h = (b - a) / n
    return (f(a)/2 + sum(f(a + i*h) for i in range(1, n)) + f(b)/2) * h

def simpson_method(f, a, b, n):
    if n % 2 == 1: n += 1
    h = (b - a) / n
    return (h/3) * (f(a) + 4*sum(f(a + i*h) for i in range(1, n, 2)) +
                    2*sum(f(a + i*h) for i in range(2, n, 2)) + f(b))

f = lambda x: np.sin(x) / (1 + x**2)
a, b = 0, 10
exact, _ = integrate.quad(f, a, b)

ns = np.arange(2, 100)
errors_rect = [abs(rectangle_method(f, a, b, n) - exact) for n in ns]
errors_trap = [abs(trapezoidal_method(f, a, b, n) - exact) for n in ns]
errors_simp = [abs(simpson_method(f, a, b, n) - exact) for n in ns]

class IntegrationAccuracyScene(Scene):
    def construct(self):
        min_err = min(min(errors_rect), min(errors_trap), min(errors_simp))
        axes = Axes(
            x_range=[2, 100, 10],
            y_range=[min_err*0.5, max(errors_rect)*2, 0.001],
            x_length=10,
            y_length=6,
            y_axis_config={"scaling": LogBase(base=10)},
        ).add_coordinates()
        grid = NumberPlane(
            x_range=[2, 100, 10],
            y_range=[min_err*0.5, max(errors_rect)*2, 0.001],
            x_length=10,
            y_length=6,
            y_axis_config={"scaling": LogBase(base=10)},
        )
        curve_rect = axes.plot_line_graph(ns, np.array(errors_rect), line_color=RED)
        curve_trap = axes.plot_line_graph(ns, np.array(errors_trap), line_color=GREEN)
        curve_simp = axes.plot_line_graph(ns, np.array(errors_simp), line_color=BLUE)
        labels = VGroup(
            Text("Rectangle O(h)", color=RED, font_size=24),
            Text("Trapezoidal O(h^2)", color=GREEN, font_size=24),
            Text("Simpson's O(h^4)", color=BLUE, font_size=24),
        ).arrange(DOWN, aligned_edge=LEFT).to_edge(RIGHT)
        title = Text("Numerical Integration Accuracy Comparison").to_edge(UP)
        x_label = Text("Number of Intervals (n)").next_to(axes, DOWN)
        y_label = Text("Error (log scale)").next_to(axes, LEFT)
        self.add(axes, grid, curve_rect, curve_trap, curve_simp, labels, title, x_label, y_label)

# Render: manim -pql <filename> IntegrationAccuracyScene""",
                    "expected_output": "数值积分方法精度对比图",
                }
            )

        # Matrix experiments
        if "矩阵" in topic or "matrix" in topic.lower() or "线性代数" in topic:
            experiments.append(
                {
                    "title": "矩阵变换可视化"
                    if language == "zh"
                    else "Matrix Transformation Visualization",
                    "description": "可视化矩阵对向量和网格的线性变换效果"
                    if language == "zh"
                    else "Visualize linear transformation effects on vectors and grids",
                    "code": """from manim import *
import numpy as np

def make_transform_scene(A, title_text):
    class MatrixTransformScene(Scene):
        def construct(self):
            axes = Axes(
                x_range=[-5, 5, 1],
                y_range=[-5, 5, 1],
                x_length=8,
                y_length=8,
            ).add_coordinates()
            grid = NumberPlane(
                x_range=[-5, 5, 1],
                y_range=[-5, 5, 1],
                x_length=8,
                y_length=8,
            )

            x_pts = np.linspace(-3, 3, 15)
            y_pts = np.linspace(-3, 3, 15)

            # Original basis vectors
            e1 = Arrow(axes.c2p(0,0), axes.c2p(1,0), buff=0, color=RED, stroke_width=4)
            e2 = Arrow(axes.c2p(0,0), axes.c2p(0,1), buff=0, color=GREEN, stroke_width=4)
            e1_label = Text("e1", color=RED, font_size=28).next_to(e1, DOWN)
            e2_label = Text("e2", color=GREEN, font_size=28).next_to(e2, LEFT)

            # Transformed basis vectors
            Ae1 = A @ np.array([1, 0])
            Ae2 = A @ np.array([0, 1])
            Ae1_arrow = Arrow(axes.c2p(0,0), axes.c2p(Ae1[0], Ae1[1]), buff=0, color=ORANGE, stroke_width=4)
            Ae2_arrow = Arrow(axes.c2p(0,0), axes.c2p(Ae2[0], Ae2[1]), buff=0, color=PURPLE, stroke_width=4)
            Ae1_label = Text("Ae1", color=ORANGE, font_size=28).next_to(Ae1_arrow, DOWN)
            Ae2_label = Text("Ae2", color=PURPLE, font_size=28).next_to(Ae2_arrow, LEFT)

            matrix_str = f"[[{A[0,0]:.1f}, {A[0,1]:.1f}], [{A[1,0]:.1f}, {A[1,1]:.1f}]]"
            title = Text(f"{title_text} A = {matrix_str}").to_edge(UP)

            self.add(axes, grid, e1, e2, e1_label, e2_label,
                     Ae1_arrow, Ae2_arrow, Ae1_label, Ae2_label, title)
    return MatrixTransformScene

matrices = [
    (np.array([[2, 0], [0, 2]]), "Scaling (2x)"),
    (np.array([[1, 1], [0, 1]]), "Shear"),
    (np.array([[0, -1], [1, 0]]), "Rotation 90 deg"),
    (np.array([[2, 1], [1, 2]]), "General"),
]

Scenes = [make_transform_scene(A, title) for A, title in matrices]

# Render each: manim -pql <filename> Scenes[0]  (or assign to named classes)
# To render all, iterate: for S in Scenes: manim -pql <filename> S""",
                    "expected_output": "矩阵变换可视化图",
                }
            )

            experiments.append(
                {
                    "title": "特征值与特征向量分析"
                    if language == "zh"
                    else "Eigenvalue and Eigenvector Analysis",
                    "description": "分析矩阵的特征结构和谱性质"
                    if language == "zh"
                    else "Analyze matrix spectral properties",
                    "code": """from manim import *
import numpy as np

np.random.seed(42)
A = np.random.randn(5, 5)
A = (A + A.T) / 2

eigenvalues, eigenvectors = np.linalg.eigh(A)

print("Matrix A:")
print(np.round(A, 3))
print("\\nEigenvalues:", np.round(eigenvalues, 3))
print("\\nEigenvectors:")
print(np.round(eigenvectors, 3))

for i in range(len(eigenvalues)):
    v = eigenvectors[:, i]
    Av = A @ v
    lv = eigenvalues[i] * v
    error = np.linalg.norm(Av - lv)
    print(f"  lambda{i+1}={eigenvalues[i]:.3f}: ||Av-lv|| = {error:.2e}")

class EigenvalueSpectrumScene(Scene):
    def construct(self):
        bar_chart = BarChart(
            values=list(eigenvalues),
            bar_names=[f"l{i+1}" for i in range(len(eigenvalues))],
            y_range=[min(eigenvalues)-0.5, max(eigenvalues)+0.5, 1],
            y_length=6,
            x_length=6,
            bar_colors=[STEEL_BLUE for _ in eigenvalues],
        )
        title = Text("Eigenvalue Spectrum").to_edge(UP)
        x_label = Text("Index").next_to(bar_chart, DOWN)
        y_label = Text("Eigenvalue").next_to(bar_chart, LEFT)
        zero_line = Line(
            bar_chart.c2p(0, 0), bar_chart.c2p(len(eigenvalues)+1, 0),
            color=WHITE, stroke_width=1
        )
        self.add(bar_chart, title, x_label, y_label, zero_line)

cond = abs(eigenvalues[-1]) / abs(eigenvalues[0]) if eigenvalues[0] != 0 else float('inf')

class MatrixPropertiesScene(Scene):
    def construct(self):
        props = VGroup(
            Text(f"Condition Number: {cond:.2f}", font_size=36),
            Text(f"Rank: {np.linalg.matrix_rank(A)}", font_size=36),
            Text(f"Determinant: {np.linalg.det(A):.4f}", font_size=36),
        ).arrange(DOWN, buff=0.5)
        title = Text("Matrix Properties").to_edge(UP)
        self.add(props, title)

# Render: manim -pql <filename> EigenvalueSpectrumScene
# Render: manim -pql <filename> MatrixPropertiesScene""",
                    "expected_output": "特征值谱图、矩阵性质分析",
                }
            )

        # Probability experiments
        if "概率" in topic or "probability" in topic.lower() or "统计" in topic:
            experiments.append(
                {
                    "title": "中心极限定理模拟"
                    if language == "zh"
                    else "Central Limit Theorem Simulation",
                    "description": "通过大量随机实验验证中心极限定理"
                    if language == "zh"
                    else "Verify CLT through large-scale random experiments",
                    "code": """from manim import *
import numpy as np
from scipy import stats

np.random.seed(42)

n_samples = [1, 3, 10, 30, 100]
n_experiments = 10000

class CLTSimulationScene(Scene):
    def construct(self):
        for n in n_samples:
            means = [np.mean(np.random.uniform(-1, 1, n)) for _ in range(n_experiments)]
            std = np.std(means)

            bar_vals, bin_edges = np.histogram(means, bins=50, density=True)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

            bar_chart = BarChart(
                values=list(bar_vals),
                bar_names=[f"" for _ in bar_vals],
                y_range=[0, float(bar_vals.max())*1.2, float(bar_vals.max())/5],
                y_length=5,
                x_length=8,
            )

            x_norm = np.linspace(min(means), max(means), 100)
            y_norm = stats.norm.pdf(x_norm, 0, std)

            title = Text(f"n = {n}, mu = {np.mean(means):.4f}, sigma = {std:.4f}").to_edge(UP)
            subtitle = Text("Central Limit Theorem Demonstration", font_size=36).to_edge(UP).shift(UP * 0.05)
            self.play(FadeIn(bar_chart), FadeIn(title))
            self.wait(2)
            self.play(FadeOut(bar_chart), FadeOut(title))

# Render: manim -pql <filename> CLTSimulationScene""",
                    "expected_output": "中心极限定理验证图",
                }
            )

        # Calculus experiments
        if "极限" in topic or "limit" in topic.lower():
            experiments.append(
                {
                    "title": "极限的数值验证"
                    if language == "zh"
                    else "Numerical Verification of Limits",
                    "description": "通过数值方法验证重要极限"
                    if language == "zh"
                    else "Verify important limits numerically",
                    "code": """from manim import *
import numpy as np

x1 = np.logspace(-10, 0, 100)
y1 = np.sin(x1) / x1

x2 = np.logspace(0, 6, 100)
y2 = (1 + 1/x2)**x2

class LimitSinXScene(Scene):
    def construct(self):
        axes = Axes(
            x_range=[1e-10, 1, 1e-1],
            y_range=[0, 1.2, 0.2],
            x_length=8,
            y_length=5,
            x_axis_config={"scaling": LogBase(base=10)},
        ).add_coordinates()
        grid = NumberPlane(
            x_range=[1e-10, 1, 1e-1],
            y_range=[0, 1.2, 0.2],
            x_length=8,
            y_length=5,
            x_axis_config={"scaling": LogBase(base=10)},
        )
        curve = axes.plot_line_graph(x1, y1, line_color=BLUE)
        limit_line = DashedLine(axes.c2p(1e-10, 1), axes.c2p(1, 1), color=RED)
        limit_label = Text("Limit = 1", color=RED, font_size=28).next_to(limit_line, UP)
        title = Text("lim(x->0) sin(x)/x = 1").to_edge(UP)
        x_label = Text("x").next_to(axes, DOWN)
        y_label = Text("sin(x)/x").next_to(axes, LEFT)
        self.add(axes, grid, curve, limit_line, limit_label, title, x_label, y_label)

class LimitEScene(Scene):
    def construct(self):
        axes = Axes(
            x_range=[1, 1e6, 1e5],
            y_range=[1, 3, 0.5],
            x_length=8,
            y_length=5,
            x_axis_config={"scaling": LogBase(base=10)},
        ).add_coordinates()
        grid = NumberPlane(
            x_range=[1, 1e6, 1e5],
            y_range=[1, 3, 0.5],
            x_length=8,
            y_length=5,
            x_axis_config={"scaling": LogBase(base=10)},
        )
        curve = axes.plot_line_graph(x2, y2, line_color=GREEN)
        limit_line = DashedLine(axes.c2p(1, np.e), axes.c2p(1e6, np.e), color=RED)
        limit_label = Text(f"Limit = e = {np.e:.4f}", color=RED, font_size=28).next_to(limit_line, UP)
        title = Text("lim(x->inf) (1+1/x)^x = e").to_edge(UP)
        x_label = Text("x").next_to(axes, DOWN)
        y_label = Text("(1+1/x)^x").next_to(axes, LEFT)
        self.add(axes, grid, curve, limit_line, limit_label, title, x_label, y_label)

# Render: manim -pql <filename> LimitSinXScene
# Render: manim -pql <filename> LimitEScene""",
                    "expected_output": "极限数值验证图",
                }
            )

        # Trigonometry experiments
        if "三角" in topic or "trig" in topic.lower():
            experiments.append(
                {
                    "title": "三角函数图像与性质"
                    if language == "zh"
                    else "Trigonometric Functions Visualization",
                    "description": "可视化三角函数及其导数、积分的关系"
                    if language == "zh"
                    else "Visualize trigonometric functions and their derivatives/integrals",
                    "code": """from manim import *
import numpy as np

class BasicTrigScene(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-2*np.pi, 2*np.pi, np.pi],
            y_range=[-4, 4, 1],
            x_length=10,
            y_length=5,
        ).add_coordinates()
        grid = NumberPlane(
            x_range=[-2*np.pi, 2*np.pi, np.pi],
            y_range=[-4, 4, 1],
            x_length=10,
            y_length=5,
        )
        x_vals = np.linspace(-2*np.pi, 2*np.pi, 500)
        sin_curve = axes.plot_line_graph(x_vals, np.sin(x_vals), line_color=BLUE)
        cos_curve = axes.plot_line_graph(x_vals, np.cos(x_vals), line_color=RED)
        tan_curve = axes.plot_line_graph(x_vals, np.clip(np.tan(x_vals), -4, 4), line_color=GREEN)
        labels = VGroup(
            Text("sin(x)", color=BLUE, font_size=24),
            Text("cos(x)", color=RED, font_size=24),
            Text("tan(x)", color=GREEN, font_size=24),
        ).arrange(DOWN, aligned_edge=LEFT).to_edge(RIGHT)
        title = Text("Basic Trigonometric Functions").to_edge(UP)
        self.add(axes, grid, sin_curve, cos_curve, tan_curve, labels, title)

class TrigDerivativesScene(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-2*np.pi, 2*np.pi, np.pi],
            y_range=[-1.5, 1.5, 0.5],
            x_length=10,
            y_length=5,
        ).add_coordinates()
        grid = NumberPlane(
            x_range=[-2*np.pi, 2*np.pi, np.pi],
            y_range=[-1.5, 1.5, 0.5],
            x_length=10,
            y_length=5,
        )
        x_vals = np.linspace(-2*np.pi, 2*np.pi, 500)
        d_sin = axes.plot_line_graph(x_vals, np.cos(x_vals), line_color=BLUE)
        d_cos = axes.plot_line_graph(x_vals, -np.sin(x_vals), line_color=RED)
        labels = VGroup(
            Text("d/dx sin(x) = cos(x)", color=BLUE, font_size=24),
            Text("d/dx cos(x) = -sin(x)", color=RED, font_size=24),
        ).arrange(DOWN, aligned_edge=LEFT).to_edge(RIGHT)
        title = Text("Derivatives").to_edge(UP)
        self.add(axes, grid, d_sin, d_cos, labels, title)

class PythagoreanIdentityScene(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-2*np.pi, 2*np.pi, np.pi],
            y_range=[0, 1.5, 0.5],
            x_length=10,
            y_length=5,
        ).add_coordinates()
        grid = NumberPlane(
            x_range=[-2*np.pi, 2*np.pi, np.pi],
            y_range=[0, 1.5, 0.5],
            x_length=10,
            y_length=5,
        )
        x_vals = np.linspace(-2*np.pi, 2*np.pi, 500)
        identity_curve = axes.plot_line_graph(x_vals, np.sin(x_vals)**2 + np.cos(x_vals)**2, line_color=GREEN)
        one_line = DashedLine(axes.c2p(-2*np.pi, 1), axes.c2p(2*np.pi, 1), color=RED)
        one_label = Text("1", color=RED, font_size=28).next_to(one_line, UP)
        title = Text("Pythagorean Identity: sin^2(x) + cos^2(x) = 1").to_edge(UP)
        self.add(axes, grid, identity_curve, one_line, one_label, title)

class UnitCircleScene(Scene):
    def construct(self):
        theta_vals = np.linspace(0, 2*np.pi, 100)
        circle = Ellipse(width=4, height=4, color=BLUE)
        axes = Axes(
            x_range=[-1.5, 1.5, 0.5],
            y_range=[-1.5, 1.5, 0.5],
            x_length=6,
            y_length=6,
        ).add_coordinates()
        grid = NumberPlane(
            x_range=[-1.5, 1.5, 0.5],
            y_range=[-1.5, 1.5, 0.5],
            x_length=6,
            y_length=6,
        )
        title = Text("Unit Circle").to_edge(UP)
        self.add(axes, grid, circle, title)

# Render: manim -pql <filename> BasicTrigScene
# Render: manim -pql <filename> TrigDerivativesScene
# Render: manim -pql <filename> PythagoreanIdentityScene
# Render: manim -pql <filename> UnitCircleScene""",
                    "expected_output": "三角函数综合可视化图",
                }
            )

        return experiments

    def _ai_experiment_design(self, topic: str, language: str, depth: str) -> list:
        """Use AI to design additional experiments."""
        lang = "中文" if language == "zh" else "English"
        prompt = f"""请为以下数学主题设计实验方案：

主题：{topic}
语言：{lang}
深度：{depth}

请提供：
1. 实验目的和假设
2. 实验步骤（详细）
3. 预期结果和分析方法
4. 完整的 Python 代码实现

代码要求：
- 使用 numpy, manim, scipy, sympy
- 包含详细注释
- 生成至少 2 个可视化场景（使用 manim Scene 类）
- 包含结果分析和结论"""

        messages = [{"role": "user", "content": prompt}]
        result = self.client.send_message(messages)

        if result.success:
            return [
                {
                    "title": "AI 设计的实验"
                    if language == "zh"
                    else "AI-Designed Experiment",
                    "description": result.data[:300],
                    "code": result.data,
                    "expected_output": "AI 生成的实验结果",
                }
            ]
        return []

    def generate_visualizations(self, topic: str, experiments: list) -> list:
        """Generate visualizations for the experiments using manim."""
        visualizations = []

        try:
            if "函数" in topic or "function" in topic.lower():
                import numpy as np

                result = Visualizer.plot_function(
                    lambda x: np.sin(x), x_range=(-10, 10), title="y = sin(x)"
                )
                if result.success:
                    visualizations.append({"type": "function", "path": result.data})

            if "数列" in topic or "sequence" in topic.lower():
                import numpy as np

                fib = [1, 1]
                for i in range(2, 20):
                    fib.append(fib[-1] + fib[-2])
                result = Visualizer.plot_scatter(
                    np.arange(1, 21), np.array(fib), title="Fibonacci Sequence"
                )
                if result.success:
                    visualizations.append({"type": "sequence", "path": result.data})

            if "概率" in topic or "probability" in topic.lower():
                import numpy as np

                data = np.random.normal(0, 1, 1000)
                result = Visualizer.plot_histogram(
                    data, bins=30, title="Normal Distribution Sample"
                )
                if result.success:
                    visualizations.append({"type": "histogram", "path": result.data})
        except Exception:
            pass

        return visualizations
