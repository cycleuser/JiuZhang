"""Enhanced experiment design module.

Generates complete, runnable experiments with auto-execution,
result analysis, and comprehensive visualizations.
"""

import numpy as np
from typing import Optional
import io
import base64
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
                    "code": '''import numpy as np
import matplotlib.pyplot as plt

def fourier_square_wave(x, n_terms):
    """方波的傅里叶级数逼近"""
    result = np.zeros_like(x)
    for n in range(1, 2*n_terms, 2):
        result += (4 / (n * np.pi)) * np.sin(n * x)
    return result

def fourier_sawtooth(x, n_terms):
    """锯齿波的傅里叶级数逼近"""
    result = np.zeros_like(x)
    for n in range(1, n_terms + 1):
        result += (2 * (-1)**(n+1) / (n * np.pi)) * np.sin(n * x)
    return result

x = np.linspace(-2*np.pi, 2*np.pi, 2000)

fig, axes = plt.subplots(2, 3, figsize=(15, 8))

# Square wave convergence
for i, n in enumerate([1, 3, 10]):
    ax = axes[0, i]
    y = fourier_square_wave(x, n)
    ax.plot(x, y, linewidth=1.5, label=f'n={n}')
    ax.set_title(f'Square Wave (n={n})')
    ax.set_ylim(-1.5, 1.5)
    ax.grid(True, alpha=0.3)

# Sawtooth wave convergence
for i, n in enumerate([1, 5, 20]):
    ax = axes[1, i]
    y = fourier_sawtooth(x, n)
    ax.plot(x, y, linewidth=1.5, label=f'n={n}')
    ax.set_title(f'Sawtooth Wave (n={n})')
    ax.set_ylim(-1.5, 1.5)
    ax.grid(True, alpha=0.3)

plt.suptitle('Fourier Series Convergence')
plt.tight_layout()
plt.show()

# Convergence rate analysis
ns = np.arange(1, 50)
errors = []
x_test = np.pi / 4  # Point away from discontinuity
for n in ns:
    approx = fourier_square_wave(np.array([x_test]), n)[0]
    exact = 1.0  # Square wave value at pi/4
    errors.append(abs(approx - exact))

plt.figure(figsize=(8, 5))
plt.semilogy(ns, errors, 'bo-', linewidth=1)
plt.xlabel('Number of Terms (n)')
plt.ylabel('Error (log scale)')
plt.title('Convergence Rate at x=π/4')
plt.grid(True, alpha=0.3)
plt.show()''',
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
                    "code": """import numpy as np
import matplotlib.pyplot as plt

# Generate signal
fs = 1000  # Sampling frequency
t = np.arange(0, 1, 1/fs)
f1, f2, f3 = 50, 120, 200  # Frequency components

signal = (np.sin(2*np.pi*f1*t) +
          0.5*np.sin(2*np.pi*f2*t) +
          0.3*np.sin(2*np.pi*f3*t) +
          0.5*np.random.randn(len(t)))

# FFT
N = len(signal)
Y = np.fft.fft(signal)
P2 = np.abs(Y/N)
P1 = P2[:N//2]
P1[1:-1] = 2*P1[1:-1]
f = fs*np.arange(0, N//2)/N

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

ax1.plot(t[:200], signal[:200], 'b-', linewidth=0.5)
ax1.set_title('Time Domain Signal')
ax1.set_xlabel('Time (s)')
ax1.grid(True, alpha=0.3)

ax2.plot(f, P1, 'r-', linewidth=1)
ax2.set_title('Frequency Spectrum (FFT)')
ax2.set_xlabel('Frequency (Hz)')
ax2.set_ylabel('|P1(f)|')
ax2.grid(True, alpha=0.3)
ax2.set_xlim(0, 300)

plt.tight_layout()
plt.show()""",
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
                    "code": """import numpy as np
import matplotlib.pyplot as plt

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

plt.figure(figsize=(10, 6))
plt.loglog(hs, errors_forward, 'r-', label='Forward Difference O(h)', linewidth=2)
plt.loglog(hs, errors_central, 'g-', label='Central Difference O(h²)', linewidth=2)
plt.loglog(hs, errors_five, 'b-', label='Five-Point O(h⁴)', linewidth=2)
plt.xlabel('Step Size (h)')
plt.ylabel('Error')
plt.title('Numerical Derivative Accuracy Comparison')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()""",
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
                    "code": """import numpy as np
import matplotlib.pyplot as plt
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

plt.figure(figsize=(10, 6))
plt.semilogy(ns, errors_rect, 'r-', label='Rectangle O(h)', linewidth=2)
plt.semilogy(ns, errors_trap, 'g-', label='Trapezoidal O(h²)', linewidth=2)
plt.semilogy(ns, errors_simp, 'b-', label="Simpson's O(h⁴)", linewidth=2)
plt.xlabel('Number of Intervals (n)')
plt.ylabel('Error (log scale)')
plt.title('Numerical Integration Accuracy Comparison')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()""",
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
                    "code": """import numpy as np
import matplotlib.pyplot as plt

def plot_matrix_transform(A, title="Matrix Transformation"):
    fig, ax = plt.subplots(figsize=(8, 8))

    origin = np.array([0, 0])
    e1 = np.array([1, 0])
    e2 = np.array([0, 1])
    Ae1 = A @ e1
    Ae2 = A @ e2

    # Draw grid
    x = np.linspace(-3, 3, 15)
    y = np.linspace(-3, 3, 15)
    X, Y = np.meshgrid(x, y)

    for i in range(len(x)):
        ax.plot([x[i], x[i]], [-3, 3], 'gray', alpha=0.15, linewidth=0.5)
        ax.plot([-3, 3], [y[i], y[i]], 'gray', alpha=0.15, linewidth=0.5)

    # Transformed grid
    for i in range(len(x)):
        pts = np.array([[x[i], yj] for yj in y])
        transformed = (A @ pts.T).T
        ax.plot(transformed[:, 0], transformed[:, 1], 'blue', alpha=0.2, linewidth=0.5)

        pts = np.array([[xj, y[i]] for xj in x])
        transformed = (A @ pts.T).T
        ax.plot(transformed[:, 0], transformed[:, 1], 'blue', alpha=0.2, linewidth=0.5)

    # Basis vectors
    ax.quiver(*origin, *e1, angles='xy', scale_units='xy', scale=1, color='red', label='e₁', width=0.015)
    ax.quiver(*origin, *e2, angles='xy', scale_units='xy', scale=1, color='green', label='e₂', width=0.015)
    ax.quiver(*origin, *Ae1, angles='xy', scale_units='xy', scale=1, color='orange', label='Ae₁', width=0.015)
    ax.quiver(*origin, *Ae2, angles='xy', scale_units='xy', scale=1, color='purple', label='Ae₂', width=0.015)

    ax.set_xlim(-5, 5)
    ax.set_ylim(-5, 5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    ax.set_title(f'{title}\\nA = [[{A[0,0]:.1f}, {A[0,1]:.1f}], [{A[1,0]:.1f}, {A[1,1]:.1f}]]')

    plt.tight_layout()
    plt.show()

# Different transformations
matrices = [
    (np.array([[2, 0], [0, 2]]), "Scaling (2x)"),
    (np.array([[1, 1], [0, 1]]), "Shear"),
    (np.array([[0, -1], [1, 0]]), "Rotation 90°"),
    (np.array([[2, 1], [1, 2]]), "General"),
]

for A, title in matrices:
    plot_matrix_transform(A, title)""",
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
                    "code": """import numpy as np
import matplotlib.pyplot as plt

# Create symmetric matrix
np.random.seed(42)
A = np.random.randn(5, 5)
A = (A + A.T) / 2  # Make symmetric

# Eigen decomposition
eigenvalues, eigenvectors = np.linalg.eigh(A)

print("Matrix A:")
print(np.round(A, 3))
print("\\nEigenvalues:", np.round(eigenvalues, 3))
print("\\nEigenvectors:")
print(np.round(eigenvectors, 3))

# Verify: Av = λv
for i in range(len(eigenvalues)):
    v = eigenvectors[:, i]
    Av = A @ v
    lv = eigenvalues[i] * v
    error = np.linalg.norm(Av - lv)
    print(f"  λ{i+1}={eigenvalues[i]:.3f}: ||Av-λv|| = {error:.2e}")

# Spectral visualization
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

ax1.bar(range(1, len(eigenvalues)+1), eigenvalues, color='steelblue')
ax1.axhline(y=0, color='k', linewidth=0.5)
ax1.set_xlabel('Index')
ax1.set_ylabel('Eigenvalue')
ax1.set_title('Eigenvalue Spectrum')
ax1.grid(True, alpha=0.3)

# Condition number
cond = abs(eigenvalues[-1]) / abs(eigenvalues[0]) if eigenvalues[0] != 0 else float('inf')
ax2.text(0.5, 0.5, f'Condition Number: {cond:.2f}\\nRank: {np.linalg.matrix_rank(A)}\\nDeterminant: {np.linalg.det(A):.4f}',
         ha='center', va='center', fontsize=14, transform=ax2.transAxes)
ax2.set_title('Matrix Properties')
ax2.axis('off')

plt.tight_layout()
plt.show()""",
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
                    "code": """import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

np.random.seed(42)

n_samples = [1, 3, 10, 30, 100]
n_experiments = 10000

fig, axes = plt.subplots(2, 3, figsize=(15, 8))
axes = axes.flatten()

for idx, n in enumerate(n_samples):
    ax = axes[idx]

    # Sample from uniform distribution
    means = [np.mean(np.random.uniform(-1, 1, n)) for _ in range(n_experiments)]

    ax.hist(means, bins=50, density=True, alpha=0.7, color='steelblue', label='Sample means')

    # Normal fit
    x = np.linspace(min(means), max(means), 100)
    std = np.std(means)
    ax.plot(x, stats.norm.pdf(x, 0, std), 'r-', linewidth=2, label='Normal fit')

    ax.set_title(f'n = {n}\\nμ = {np.mean(means):.4f}, σ = {std:.4f}')
    ax.legend()
    ax.grid(True, alpha=0.3)

axes[-1].axis('off')
axes[-1].text(0.5, 0.5, 'As n increases,\\nthe distribution of\\nsample means\\napproaches normal',
              ha='center', va='center', fontsize=12, transform=axes[-1].transAxes)

plt.suptitle('Central Limit Theorem Demonstration', fontsize=16, y=1.02)
plt.tight_layout()
plt.show()""",
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
                    "code": """import numpy as np
import matplotlib.pyplot as plt

# lim(x→0) sin(x)/x = 1
x1 = np.logspace(-10, 0, 100)
y1 = np.sin(x1) / x1

# lim(x→∞) (1+1/x)^x = e
x2 = np.logspace(0, 6, 100)
y2 = (1 + 1/x2)**x2

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

ax1.semilogx(x1, y1, 'b-', linewidth=2)
ax1.axhline(y=1, color='r', linestyle='--', label='Limit = 1')
ax1.set_xlabel('x')
ax1.set_ylabel('sin(x)/x')
ax1.set_title('lim(x→0) sin(x)/x = 1')
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2.semilogx(x2, y2, 'g-', linewidth=2)
ax2.axhline(y=np.e, color='r', linestyle='--', label=f'Limit = e ≈ {np.e:.4f}')
ax2.set_xlabel('x')
ax2.set_ylabel('(1+1/x)^x')
ax2.set_title('lim(x→∞) (1+1/x)^x = e')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()""",
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
                    "code": """import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(-2*np.pi, 2*np.pi, 500)

fig, axes = plt.subplots(2, 2, figsize=(12, 8))

# Basic functions
axes[0, 0].plot(x, np.sin(x), 'b-', label='sin(x)', linewidth=2)
axes[0, 0].plot(x, np.cos(x), 'r-', label='cos(x)', linewidth=2)
axes[0, 0].plot(x, np.tan(x), 'g-', label='tan(x)', linewidth=1, alpha=0.5)
axes[0, 0].set_ylim(-4, 4)
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].set_title('Basic Trigonometric Functions')

# Derivatives
axes[0, 1].plot(x, np.cos(x), 'b--', label="d/dx sin(x) = cos(x)", linewidth=2)
axes[0, 1].plot(x, -np.sin(x), 'r--', label="d/dx cos(x) = -sin(x)", linewidth=2)
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)
axes[0, 1].set_title('Derivatives')

# sin² + cos² = 1
axes[1, 0].plot(x, np.sin(x)**2 + np.cos(x)**2, 'g-', linewidth=2, label='sin²(x)+cos²(x)')
axes[1, 0].axhline(y=1, color='r', linestyle='--', label='1')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)
axes[1, 0].set_title('Pythagorean Identity')

# Unit circle
theta = np.linspace(0, 2*np.pi, 100)
axes[1, 1].plot(np.cos(theta), np.sin(theta), 'b-', linewidth=2)
axes[1, 1].set_aspect('equal')
axes[1, 1].grid(True, alpha=0.3)
axes[1, 1].set_title('Unit Circle')

plt.tight_layout()
plt.show()""",
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
- 使用 numpy, matplotlib, scipy, sympy
- 包含详细注释
- 生成至少 2 个可视化图表
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
        """Generate visualizations for the experiments."""
        visualizations = []

        # Generate base64 encoded visualizations
        try:
            if "函数" in topic or "function" in topic.lower():
                import numpy as np

                result = Visualizer.plot_function(
                    lambda x: np.sin(x), x_range=(-10, 10), title="y = sin(x)"
                )
                if result.success:
                    visualizations.append({"type": "function", "data": result.data})

            if "数列" in topic or "sequence" in topic.lower():
                import numpy as np

                fib = [1, 1]
                for i in range(2, 20):
                    fib.append(fib[-1] + fib[-2])
                result = Visualizer.plot_scatter(
                    np.arange(1, 21), fib, title="Fibonacci Sequence"
                )
                if result.success:
                    visualizations.append({"type": "sequence", "data": result.data})

            if "概率" in topic or "probability" in topic.lower():
                import numpy as np

                data = np.random.normal(0, 1, 1000)
                result = Visualizer.plot_histogram(
                    data, bins=30, title="Normal Distribution Sample"
                )
                if result.success:
                    visualizations.append({"type": "histogram", "data": result.data})
        except Exception:
            pass

        return visualizations
