# JiuZhang (九章)

A comprehensive mathematics learning platform from basic number concepts to frontier mathematics.

## Features

- **Complete Curriculum**: 7 categories, 40+ knowledge points from elementary to frontier math
  - Arithmetic: Natural numbers, integers, fractions, decimals, operations
  - Algebra: Equations, functions, polynomials
  - Geometry: Triangles, circles, trigonometry, coordinate geometry
  - Probability: Probability basics, combinatorics, distributions, statistics
  - Calculus: Limits, derivatives, integrals
  - Linear Algebra: Vectors, matrices, eigenvalues
  - Advanced: Topology, abstract algebra, Fourier analysis, real analysis
- **AI-Powered Lessons**: Generate personalized lessons using Ollama, OpenAI, Anthropic, Alibaba CodingPlan, or any OpenAI-compatible model
- **Multiple Visualizations**: matplotlib/seaborn charts, pyqtgraph interactive plots, web-based visualizations, and TUI terminal visualizations
- **Three Interfaces**: CLI REPL, Web GUI (Flask), and TUI terminal interface
- **Code Examples**: Every concept comes with runnable Python code using numpy, scipy, sympy, matplotlib
- **Exercise Generation**: Auto-generate practice problems with solutions
- **Bilingual**: Full Chinese and English support
- **Knowledge Graph**: Prerequisites and relationships between all concepts

## Quick Start

```bash
# Install
pip install jiuzhang

# CLI mode (interactive)
jiuzhang

# Learn a topic
jiuzhang learn "什么是分数"

# Generate exercises
jiuzhang exercise "自然数"

# Visualizations
jiuzhang visualize number_line
jiuzhang visualize function

# View courses
jiuzhang courses
jiuzhang stats

# Web interface
jiuzhang  # Opens web GUI by default

# Python API
from jiuzhang import JiuZhangAPI
api = JiuZhangAPI()

# Learn a topic
result = api.learn("什么是分数")
print(result.data)

# Generate exercises
result = api.exercise("自然数", difficulty="easy", count=5)
print(result.data)

# Visualize
result = api.visualize_number_line(-5, 10, highlight=[0, 1, 2])
result = api.visualize_function(lambda x: x**2, title="y = x²")
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `learn <topic>` | Learn a mathematics topic |
| `exercise <topic>` | Generate practice exercises |
| `visualize <type>` | Create visualization (number_line, function, bar, quadratic) |
| `courses` | View all available courses |
| `stats` | View course statistics |
| `multiplication` | Show multiplication table |
| `fraction <n/d>` | Visualize a fraction |
| `config` | View/edit configuration |
| `help` | Show help |
| `quit` | Exit |

## Supported AI Providers

| Provider | Type | Setup |
|----------|------|-------|
| Ollama | Local | `ollama pull qwen2.5:7b` |
| OpenAI | Cloud | Set `OPENAI_API_KEY` |
| Anthropic | Cloud | Set `ANTHROPIC_API_KEY` |
| Alibaba CodingPlan | Cloud | Set `DASHSCOPE_API_KEY` |
| OpenAI Compatible | Custom | Configure base URL |

## Curriculum Structure

```
Number Concepts → Arithmetic → Algebra → Geometry
    ↓
Probability → Calculus → Linear Algebra → Frontier Math
```

### Course Categories (7)
- **Arithmetic** (12 KPs): Natural numbers, integers, fractions, decimals, operations, operation laws
- **Algebra** (7 KPs): Expressions, linear/quadratic equations, functions, polynomials
- **Geometry** (5 KPs): Triangles, Pythagorean theorem, circles, trigonometry, coordinate geometry
- **Probability** (4 KPs): Probability basics, combinatorics, distributions, descriptive statistics
- **Calculus** (3 KPs): Limits, derivatives, integrals
- **Linear Algebra** (4 KPs): Vectors, matrices, determinants, eigenvalues
- **Advanced** (4 KPs): Topology, abstract algebra, real analysis, Fourier analysis

## Python API

```python
from jiuzhang import JiuZhangAPI

api = JiuZhangAPI()

# Learn
api.learn("勾股定理")
api.learn("Fourier Transform", level="undergraduate")

# Exercises
api.exercise("二次方程", difficulty="medium", count=5)

# Visualizations
api.visualize_number_line(-10, 10, highlight=[-5, 0, 5])
api.visualize_function(lambda x: np.sin(x), title="y = sin(x)")
api.visualize_bar(["A", "B", "C"], [10, 20, 15])
api.visualize_histogram(np.random.randn(1000))
api.visualize_matrix([[1, 2], [3, 4]])

# Course info
api.get_courses()
api.get_knowledge_points(category="algebra")

# Switch provider
api.set_provider("openai", model="gpt-4o")
api.set_provider("ollama", model="qwen2.5:7b")
```

## Development

```bash
# Clone and install in dev mode
git clone https://github.com/cycleuser/JiuZhang.git
cd JiuZhang
pip install -e ".[dev]"

# Run tests
pytest

# Build package
python -m build

# Upload to PyPI
twine upload dist/*
```

## Project Structure

```
jiuzhang/
├── core/                    # Core modules
│   ├── config.py            # Configuration management
│   ├── multi_provider_api.py # Multi-model client
│   ├── constants.py         # Constants
│   └── errors.py            # Error types
├── math_engine/             # Math engine
│   ├── curriculum.py        # Curriculum structure
│   ├── lesson.py            # AI lesson generation
│   └── visualizer.py        # matplotlib visualizations
├── courses/                 # Course content
│   ├── arithmetic/          # 数的概念、四则运算、分数、小数
│   ├── algebra/             # 方程、函数、多项式
│   ├── geometry/            # 三角形、勾股定理、三角函数
│   ├── probability/         # 概率、统计
│   ├── calculus/            # 极限、导数、积分
│   ├── linear_algebra/      # 向量、矩阵、特征值
│   ├── advanced/            # 拓扑、抽象代数、傅里叶
│   └── registry.py          # Course registry
├── visualization/           # Visualization modules
│   └── tui_viz.py           # Terminal visualizations
├── templates/               # Web templates
└── static/                  # Web assets
```

## License

GPL-3.0-or-later

## Acknowledgments

Named after 《九章算术》(The Nine Chapters on the Mathematical Art), one of the earliest surviving mathematical texts from ancient China, compiled around 200 BCE.
