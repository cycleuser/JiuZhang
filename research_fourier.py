#!/usr/bin/env python3
"""
九章 (JiuZhang) 前沿数学研究：傅里叶分析
==========================================

完整研究流程：
1. 文献搜索与下载
2. 数学推导
3. 代码实现
4. 图表生成
5. 研究报告
"""

import sys
import os
import json
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

# Output directory
OUTPUT_DIR = Path("research_output")
OUTPUT_DIR.mkdir(exist_ok=True)
FIGURES_DIR = OUTPUT_DIR / "figures"
FIGURES_DIR.mkdir(exist_ok=True)


def save_fig(fig, name):
    """Save figure to file."""
    path = FIGURES_DIR / f"{name}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  ✅ 已保存: {path}")
    return path


# ============================================================================
# 1. 文献搜索
# ============================================================================
def search_arxiv(query, max_results=5):
    """Search arXiv for papers."""
    print(f"\n📚 搜索 arXiv: {query}")

    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    url = f"http://export.arxiv.org/api/query?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JiuZhang/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            xml_data = response.read().decode("utf-8")

        namespace = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }
        root = ET.fromstring(xml_data)
        entries = root.findall("atom:entry", namespace)

        papers = []
        for entry in entries:
            title = entry.find("atom:title", namespace)
            summary = entry.find("atom:summary", namespace)
            published = entry.find("atom:published", namespace)
            authors = entry.findall("atom:author", namespace)
            categories = entry.findall("atom:category", namespace)
            id_elem = entry.find("atom:id", namespace)

            author_names = []
            for author in authors:
                name_elem = author.find("atom:name", namespace)
                if name_elem is not None:
                    author_names.append(name_elem.text)

            cat_terms = [c.get("term", "") for c in categories]

            paper = {
                "title": title.text.strip().replace("\n", " ")
                if title is not None
                else "",
                "authors": ", ".join(author_names[:5]),
                "abstract": summary.text.strip().replace("\n", " ")[:500]
                if summary is not None
                else "",
                "published": published.text[:10] if published is not None else "",
                "categories": cat_terms,
                "url": id_elem.text if id_elem is not None else "",
            }
            papers.append(paper)
            print(f"  📄 {paper['title'][:80]}...")
            print(f"     作者: {paper['authors']}")
            print(f"     时间: {paper['published']}")
            print(f"     分类: {', '.join(cat_terms)}")

        return papers
    except Exception as e:
        print(f"  ❌ 搜索失败: {e}")
        return []


# ============================================================================
# 2. 数学推导
# ============================================================================
def mathematical_derivation():
    """Perform mathematical derivation for Fourier analysis."""
    print("\n🔬 数学推导")

    derivation = """
## 傅里叶分析数学推导

### 1. 傅里叶级数

对于周期为 2π 的函数 f(x)，其傅里叶级数展开为：

f(x) = a₀/2 + Σ[aₙcos(nx) + bₙsin(nx)]

其中系数为：
aₙ = (1/π)∫₋π^π f(x)cos(nx)dx
bₙ = (1/π)∫₋π^π f(x)sin(nx)dx

### 2. 傅里叶变换

傅里叶变换将时域信号转换为频域：

F(ω) = ∫₋∞^∞ f(t)e^(-iωt)dt

逆变换：
f(t) = (1/2π)∫₋∞^∞ F(ω)e^(iωt)dω

### 3. 离散傅里叶变换 (DFT)

对于 N 个采样点：

X[k] = Σₙ₌₀ᴺ⁻¹ x[n]·e^(-2πikn/N)

逆变换：
x[n] = (1/N)Σₖ₌₀ᴺ⁻¹ X[k]·e^(2πikn/N)

### 4. 快速傅里叶变换 (FFT)

Cooley-Tukey 算法将 DFT 的计算复杂度从 O(N²) 降至 O(N log N)。

核心思想：分治法
- 将 N 点 DFT 分解为两个 N/2 点 DFT
- 递归应用直到 N=1

### 5. 卷积定理

时域卷积等于频域乘积：
f * g ↔ F(ω)·G(ω)

### 6. 帕塞瓦尔定理

信号能量在时域和频域守恒：
∫|f(t)|²dt = (1/2π)∫|F(ω)|²dω
"""
    print("  ✅ 数学推导完成")
    return derivation


# ============================================================================
# 3. 代码实现与图表生成
# ============================================================================
def generate_figures():
    """Generate all figures for the research."""
    print("\n📊 生成图表")

    # Figure 1: Fourier Series Convergence
    print("  图 1: 傅里叶级数收敛性")
    x = np.linspace(-2 * np.pi, 2 * np.pi, 2000)

    def fourier_square(x, n_terms):
        result = np.zeros_like(x)
        for n in range(1, 2 * n_terms, 2):
            result += (4 / (n * np.pi)) * np.sin(n * x)
        return result

    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(2, 3, figure=fig, hspace=0.3, wspace=0.3)

    for i, n in enumerate([1, 3, 5, 10, 20, 50]):
        ax = fig.add_subplot(gs[i // 3, i % 3])
        y = fourier_square(x, n)
        ax.plot(x, y, linewidth=1.5, color="#2563eb", label=f"n={n}")
        ax.set_xlim(-2 * np.pi, 2 * np.pi)
        ax.set_ylim(-1.5, 1.5)
        ax.axhline(y=0, color="gray", linewidth=0.5, alpha=0.5)
        ax.axvline(x=0, color="gray", linewidth=0.5, alpha=0.5)
        ax.grid(True, alpha=0.2)
        ax.set_title(f"傅里叶级数逼近方波 (n={n})", fontsize=11, fontweight="bold")
        ax.legend(loc="upper right", fontsize=9)

    plt.suptitle("傅里叶级数收敛性分析", fontsize=16, fontweight="bold", y=1.02)
    save_fig(fig, "01_fourier_convergence")

    # Figure 2: FFT Spectrum Analysis
    print("  图 2: FFT 频谱分析")
    fs = 1000
    t = np.arange(0, 1, 1 / fs)
    f1, f2, f3 = 50, 120, 200

    signal = (
        np.sin(2 * np.pi * f1 * t)
        + 0.5 * np.sin(2 * np.pi * f2 * t)
        + 0.3 * np.sin(2 * np.pi * f3 * t)
        + 0.5 * np.random.randn(len(t))
    )

    N = len(signal)
    Y = np.fft.fft(signal)
    P2 = np.abs(Y / N)
    P1 = P2[: N // 2]
    P1[1:-1] = 2 * P1[1:-1]
    f = fs * np.arange(0, N // 2) / N

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))

    ax1.plot(t[:200], signal[:200], color="#2563eb", linewidth=0.8)
    ax1.set_title("时域信号 (含噪声)", fontsize=13, fontweight="bold")
    ax1.set_xlabel("时间 (s)")
    ax1.set_ylabel("幅值")
    ax1.grid(True, alpha=0.3)

    ax2.plot(f, P1, color="#dc2626", linewidth=1.2)
    ax2.set_title("频域频谱 (FFT)", fontsize=13, fontweight="bold")
    ax2.set_xlabel("频率 (Hz)")
    ax2.set_ylabel("|P1(f)|")
    ax2.set_xlim(0, 300)
    ax2.grid(True, alpha=0.3)
    ax2.axvline(x=f1, color="green", linestyle="--", alpha=0.7, label=f"{f1}Hz")
    ax2.axvline(x=f2, color="orange", linestyle="--", alpha=0.7, label=f"{f2}Hz")
    ax2.axvline(x=f3, color="purple", linestyle="--", alpha=0.7, label=f"{f3}Hz")
    ax2.legend()

    plt.suptitle("FFT 频谱分析", fontsize=16, fontweight="bold", y=1.02)
    save_fig(fig, "02_fft_spectrum")

    # Figure 3: Convergence Rate
    print("  图 3: 收敛速度分析")
    ns = np.arange(1, 100)
    errors = []
    x_test = np.pi / 4
    for n in ns:
        approx = fourier_square(np.array([x_test]), n)[0]
        exact = 1.0
        errors.append(abs(approx - exact))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.semilogy(ns, errors, "bo-", linewidth=1.5, markersize=3, color="#2563eb")
    ax.set_xlabel("项数 (n)", fontsize=12)
    ax.set_ylabel("误差 (对数坐标)", fontsize=12)
    ax.set_title("傅里叶级数收敛速度", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3, which="both")
    ax.axhline(y=1e-3, color="red", linestyle="--", alpha=0.5, label="10⁻³")
    ax.axhline(y=1e-6, color="green", linestyle="--", alpha=0.5, label="10⁻⁶")
    ax.legend()
    save_fig(fig, "03_convergence_rate")

    # Figure 4: Gibbs Phenomenon
    print("  图 4: 吉布斯现象")
    x_gibbs = np.linspace(-0.5, 0.5, 2000)

    fig, ax = plt.subplots(figsize=(12, 6))
    for n in [5, 15, 50, 200]:
        y = fourier_square(x_gibbs * 2 * np.pi, n)
        ax.plot(x_gibbs, y, linewidth=1.5, label=f"n={n}")

    ax.set_xlim(-0.5, 0.5)
    ax.set_ylim(-1.5, 1.5)
    ax.axhline(y=0, color="gray", linewidth=0.5, alpha=0.5)
    ax.axvline(x=0, color="red", linestyle="--", linewidth=1, alpha=0.7, label="间断点")
    ax.axhline(
        y=1.089,
        color="orange",
        linestyle=":",
        linewidth=1.5,
        alpha=0.7,
        label="吉布斯过冲 (~9%)",
    )
    ax.set_title("吉布斯现象 (Gibbs Phenomenon)", fontsize=14, fontweight="bold")
    ax.set_xlabel("x")
    ax.set_ylabel("f(x)")
    ax.legend()
    ax.grid(True, alpha=0.2)
    save_fig(fig, "04_gibbs_phenomenon")

    # Figure 5: Signal Reconstruction
    print("  图 5: 信号重构")
    t_recon = np.linspace(0, 1, 500)
    original = np.sin(2 * np.pi * 5 * t_recon) + 0.5 * np.sin(2 * np.pi * 15 * t_recon)

    # Add noise
    noisy = original + 0.3 * np.random.randn(len(t_recon))

    # FFT and filter
    N = len(noisy)
    Y = np.fft.fft(noisy)
    freqs = np.fft.fftfreq(N, 1 / 500)

    # Low-pass filter
    cutoff = 10
    Y_filtered = Y.copy()
    Y_filtered[np.abs(freqs) > cutoff] = 0

    reconstructed = np.real(np.fft.ifft(Y_filtered))

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10))

    ax1.plot(t_recon, noisy, color="#6b7280", linewidth=0.5, label="含噪信号")
    ax1.set_title("原始含噪信号", fontsize=12, fontweight="bold")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(
        np.abs(freqs[: N // 2]), np.abs(Y[: N // 2]), color="#2563eb", linewidth=0.8
    )
    ax2.axvline(x=cutoff, color="red", linestyle="--", label=f"截止频率 {cutoff}Hz")
    ax2.set_title("频谱", fontsize=12, fontweight="bold")
    ax2.set_xlabel("频率 (Hz)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    ax3.plot(t_recon, original, "b-", linewidth=1.5, label="原始信号", alpha=0.7)
    ax3.plot(t_recon, reconstructed, "r--", linewidth=1.5, label="重构信号")
    ax3.set_title("低通滤波重构", fontsize=12, fontweight="bold")
    ax3.set_xlabel("时间 (s)")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    plt.suptitle("基于 FFT 的信号去噪与重构", fontsize=16, fontweight="bold", y=1.02)
    save_fig(fig, "05_signal_reconstruction")

    # Figure 6: Complex Function Domain Coloring
    print("  图 6: 复函数域着色")
    x_c = np.linspace(-3, 3, 400)
    y_c = np.linspace(-3, 3, 400)
    X_c, Y_c = np.meshgrid(x_c, y_c)
    Z_c = X_c + 1j * Y_c

    W_c = Z_c**2

    hue = np.angle(W_c) / (2 * np.pi)
    hue = (hue + 1) % 1
    saturation = np.ones_like(hue)
    value = np.clip(np.abs(W_c), 0, 10) / 10

    import matplotlib.colors as mcolors

    hsv = np.stack([hue, saturation, value], axis=-1)
    rgb = mcolors.hsv_to_rgb(hsv)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(rgb, extent=[-3, 3, -3, 3], origin="lower", aspect="equal")
    ax.set_xlabel("Re(z)", fontsize=12)
    ax.set_ylabel("Im(z)", fontsize=12)
    ax.set_title("复函数 f(z) = z² 域着色", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.2, color="white")
    save_fig(fig, "06_complex_domain_coloring")

    # Figure 7: Heat Equation Solution
    print("  图 7: 热方程傅里叶解")
    x_heat = np.linspace(0, 1, 200)
    times = [0.001, 0.01, 0.05, 0.1, 0.5, 1.0]

    fig, ax = plt.subplots(figsize=(12, 6))
    for t_val in times:
        u = np.zeros_like(x_heat)
        for n in range(1, 100):
            u += (
                (4 / (n * np.pi))
                * np.sin(n * np.pi * x_heat)
                * np.exp(-((n * np.pi) ** 2) * t_val)
            )
        ax.plot(x_heat, u, linewidth=2, label=f"t={t_val}")

    ax.set_xlabel("x", fontsize=12)
    ax.set_ylabel("u(x,t)", fontsize=12)
    ax.set_title("一维热方程的傅里叶级数解", fontsize=14, fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)
    save_fig(fig, "07_heat_equation")

    # Figure 8: Uncertainty Principle
    print("  图 8: 不确定性原理")
    sigmas = [0.5, 1.0, 2.0]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for i, sigma in enumerate(sigmas):
        ax = axes[i]
        t_unc = np.linspace(-5, 5, 500)
        gauss_t = np.exp(-(t_unc**2) / (2 * sigma**2))

        # Fourier transform of Gaussian is Gaussian
        freq_unc = np.linspace(-5, 5, 500)
        gauss_f = (
            sigma * np.sqrt(2 * np.pi) * np.exp(-2 * np.pi**2 * sigma**2 * freq_unc**2)
        )

        ax.plot(t_unc, gauss_t / gauss_t.max(), "b-", linewidth=2, label="时域")
        ax.plot(freq_unc, gauss_f / gauss_f.max(), "r-", linewidth=2, label="频域")
        ax.set_title(f"σ = {sigma}", fontsize=12, fontweight="bold")
        ax.set_xlabel("频率/时间")
        ax.grid(True, alpha=0.3)
        if i == 0:
            ax.legend()

    plt.suptitle(
        "海森堡不确定性原理：时域与频域的反比关系",
        fontsize=14,
        fontweight="bold",
        y=1.05,
    )
    save_fig(fig, "08_uncertainty_principle")

    print("  ✅ 所有图表生成完成")


# ============================================================================
# 4. 生成研究报告
# ============================================================================
def generate_report(papers, derivation):
    """Generate comprehensive research report."""
    print("\n📝 生成研究报告")

    report = f"""# 傅里叶分析前沿研究

**九章 (JiuZhang) 数学研究平台**
**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 摘要

本文对傅里叶分析进行了系统研究，从傅里叶级数的收敛性到快速傅里叶变换 (FFT) 的应用，
从吉布斯现象到不确定性原理，涵盖了这一数学分支的核心理论和现代应用。

---

## 1. 文献综述

共找到 {len(papers)} 篇相关文献：

"""

    for i, paper in enumerate(papers, 1):
        report += f"### {i}. {paper['title']}\n"
        report += f"- **作者**: {paper['authors']}\n"
        report += f"- **发表时间**: {paper['published']}\n"
        report += f"- **分类**: {', '.join(paper['categories'])}\n"
        report += f"- **摘要**: {paper['abstract'][:300]}...\n"
        report += f"- **链接**: {paper['url']}\n\n"

    report += f"""
---

## 2. 数学推导
{derivation}

---

## 3. 实验与可视化

### 3.1 傅里叶级数收敛性

![傅里叶级数收敛性](figures/01_fourier_convergence.png)

随着项数 n 的增加，傅里叶级数逐渐逼近方波。注意在间断点附近的吉布斯现象。

### 3.2 FFT 频谱分析

![FFT 频谱分析](figures/02_fft_spectrum.png)

通过 FFT 可以清晰地识别出信号中的三个频率成分 (50Hz, 120Hz, 200Hz)，即使存在噪声。

### 3.3 收敛速度

![收敛速度](figures/03_convergence_rate.png)

傅里叶级数的收敛速度与函数的光滑性相关。方波（不连续）的收敛速度为 O(1/n)。

### 3.4 吉布斯现象

![吉布斯现象](figures/04_gibbs_phenomenon.png)

在间断点附近，傅里叶级数会出现约 9% 的过冲，这就是著名的吉布斯现象。
即使项数趋于无穷，过冲也不会消失，只会越来越靠近间断点。

### 3.5 信号重构

![信号重构](figures/05_signal_reconstruction.png)

通过 FFT 进行频域滤波，可以有效去除噪声并重构原始信号。

### 3.6 复函数域着色

![复函数域着色](figures/06_complex_domain_coloring.png)

复函数 f(z) = z² 的域着色可视化，颜色表示相位，亮度表示模长。

### 3.7 热方程傅里叶解

![热方程](figures/07_heat_equation.png)

一维热方程的解可以用傅里叶级数表示，随时间演化，高频分量迅速衰减。

### 3.8 不确定性原理

![不确定性原理](figures/08_uncertainty_principle.png)

高斯函数的傅里叶变换仍是高斯函数。时域越窄 (σ 小)，频域越宽，体现了海森堡不确定性原理。

---

## 4. 核心代码

### 4.1 傅里叶级数计算

```python
def fourier_square(x, n_terms):
    result = np.zeros_like(x)
    for n in range(1, 2*n_terms, 2):
        result += (4 / (n * np.pi)) * np.sin(n * x)
    return result
```

### 4.2 FFT 频谱分析

```python
N = len(signal)
Y = np.fft.fft(signal)
P2 = np.abs(Y/N)
P1 = P2[:N//2]
P1[1:-1] = 2*P1[1:-1]
f = fs*np.arange(0, N//2)/N
```

### 4.3 信号滤波

```python
Y_filtered = Y.copy()
Y_filtered[np.abs(freqs) > cutoff] = 0
reconstructed = np.real(np.fft.ifft(Y_filtered))
```

---

## 5. 结论

傅里叶分析是数学中最重要的工具之一，其应用遍及：
- **信号处理**: 滤波、压缩、特征提取
- **物理学**: 量子力学、热传导、波动方程
- **工程学**: 控制系统、通信、图像处理
- **数学**: 偏微分方程、数论、概率论

本研究通过系统的理论推导和数值实验，展示了傅里叶分析的核心思想和强大能力。

---

*本报告由九章 (JiuZhang) 数学研究平台自动生成*
"""

    report_path = OUTPUT_DIR / "research_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"  ✅ 报告已保存: {report_path}")
    return report_path


# ============================================================================
# 5. 主函数
# ============================================================================
def main():
    print("=" * 60)
    print("  九章 (JiuZhang) 前沿数学研究")
    print("  主题：傅里叶分析 (Fourier Analysis)")
    print("=" * 60)

    # Step 1: Literature search
    papers = search_arxiv("fourier analysis", max_results=5)

    # Step 2: Mathematical derivation
    derivation = mathematical_derivation()

    # Step 3: Generate figures
    generate_figures()

    # Step 4: Generate report
    report_path = generate_report(papers, derivation)

    # Save metadata
    metadata = {
        "topic": "傅里叶分析 (Fourier Analysis)",
        "date": datetime.now().isoformat(),
        "papers_found": len(papers),
        "figures_generated": 8,
        "report": str(report_path),
    }
    metadata_path = OUTPUT_DIR / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("  研究完成！")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"  图表数量: 8")
    print(f"  文献数量: {len(papers)}")
    print(f"  研究报告: {report_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
