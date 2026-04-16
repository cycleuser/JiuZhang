# 九章 (JiuZhang)

从基础数的概念到前沿数学的综合学习平台。

## 功能特点

- **完整课程体系**：7大类别，40+知识点，从小学到前沿数学全覆盖
  - 算术：自然数、整数、分数、小数、四则运算
  - 代数：方程、函数、多项式
  - 几何：三角形、圆、三角函数、解析几何
  - 概率统计：概率基础、排列组合、分布、描述统计
  - 微积分：极限、导数、积分
  - 线性代数：向量、矩阵、特征值
  - 前沿数学：拓扑学、抽象代数、傅里叶分析、实分析
- **AI 驱动教学**：支持接入 Ollama、OpenAI、Anthropic、阿里云 CodingPlan 等各种模型
- **多种可视化方式**：matplotlib/seaborn 图表、pyqtgraph 交互图、Web 可视化、TUI 终端可视化
- **三种交互界面**：CLI 命令行、Web 图形界面、TUI 终端界面
- **代码实现**：每个知识点都配有可运行的 Python 代码（numpy, scipy, sympy, matplotlib）
- **练习生成**：自动生成分级练习题及详细解答
- **双语支持**：完整的中文和英文支持
- **知识图谱**：所有知识点之间的前置关系和关联

## 快速开始

```bash
# 安装
pip install jiuzhang

# CLI 模式（交互式）
jiuzhang

# 学习主题
jiuzhang learn "什么是分数"

# 生成练习
jiuzhang exercise "自然数"

# 可视化
jiuzhang visualize number_line
jiuzhang visualize function

# 查看课程
jiuzhang courses
jiuzhang stats

# Web 界面
jiuzhang  # 默认打开 Web GUI

# Python API
from jiuzhang import JiuZhangAPI
api = JiuZhangAPI()

# 学习
result = api.learn("什么是分数")
print(result.data)

# 生成练习
result = api.exercise("自然数", difficulty="easy", count=5)
print(result.data)

# 可视化
result = api.visualize_number_line(-5, 10, highlight=[0, 1, 2])
result = api.visualize_function(lambda x: x**2, title="y = x²")
```

## CLI 命令

| 命令 | 说明 |
|------|------|
| `learn <主题>` | 学习一个数学主题 |
| `exercise <主题>` | 生成练习题 |
| `visualize <类型>` | 可视化（number_line, function, bar, quadratic） |
| `courses` | 查看所有课程 |
| `stats` | 查看课程统计 |
| `multiplication` | 显示九九乘法表 |
| `fraction <n/d>` | 分数可视化 |
| `config` | 查看/修改配置 |
| `help` | 显示帮助 |
| `quit` | 退出 |

## 支持的 AI 提供商

| 提供商 | 类型 | 配置方式 |
|--------|------|----------|
| Ollama | 本地 | `ollama pull qwen2.5:7b` |
| OpenAI | 云端 | 设置 `OPENAI_API_KEY` |
| Anthropic | 云端 | 设置 `ANTHROPIC_API_KEY` |
| 阿里云 CodingPlan | 云端 | 设置 `DASHSCOPE_API_KEY` |
| OpenAI 兼容 | 自定义 | 配置 base URL |

## 课程体系

```
数的概念 → 算术 → 代数 → 几何
    ↓
概率统计 → 微积分 → 线性代数 → 前沿数学
```

### 课程分类（7类）
- **算术**（12个知识点）：自然数、整数、分数、小数、四则运算、运算律
- **代数**（7个知识点）：代数式、一元一次/二次方程、函数、一次/二次函数、多项式
- **几何**（5个知识点）：三角形、勾股定理、圆、三角函数、解析几何
- **概率统计**（4个知识点）：概率基础、排列组合、概率分布、描述统计
- **微积分**（3个知识点）：极限、导数、积分
- **线性代数**（4个知识点）：向量、矩阵、行列式、特征值与特征向量
- **前沿数学**（4个知识点）：拓扑学、抽象代数、实分析、傅里叶分析

## Python API

```python
from jiuzhang import JiuZhangAPI

api = JiuZhangAPI()

# 学习
api.learn("勾股定理")
api.learn("傅里叶变换", level="undergraduate")

# 练习
api.exercise("二次方程", difficulty="medium", count=5)

# 可视化
api.visualize_number_line(-10, 10, highlight=[-5, 0, 5])
api.visualize_function(lambda x: np.sin(x), title="y = sin(x)")
api.visualize_bar(["A", "B", "C"], [10, 20, 15])
api.visualize_histogram(np.random.randn(1000))
api.visualize_matrix([[1, 2], [3, 4]])

# 课程信息
api.get_courses()
api.get_knowledge_points(category="algebra")

# 切换提供商
api.set_provider("openai", model="gpt-4o")
api.set_provider("ollama", model="qwen2.5:7b")
```

## 开发

```bash
# 克隆并安装开发模式
git clone https://github.com/cycleuser/JiuZhang.git
cd JiuZhang
pip install -e ".[dev]"

# 运行测试
pytest

# 构建包
python publish.py build

# 上传到 PyPI
python publish.py release
```

## 项目结构

```
jiuzhang/
├── core/                    # 核心模块
│   ├── config.py            # 配置管理
│   ├── multi_provider_api.py # 多模型接入
│   ├── constants.py         # 常量定义
│   └── errors.py            # 异常类型
├── math_engine/             # 数学引擎
│   ├── curriculum.py        # 课程体系
│   ├── lesson.py            # AI 课程生成
│   └── visualizer.py        # matplotlib 可视化
├── courses/                 # 课程内容
│   ├── arithmetic/          # 数的概念、四则运算、分数、小数
│   ├── algebra/             # 方程、函数、多项式
│   ├── geometry/            # 三角形、勾股定理、三角函数
│   ├── probability/         # 概率、统计
│   ├── calculus/            # 极限、导数、积分
│   ├── linear_algebra/      # 向量、矩阵、特征值
│   ├── advanced/            # 拓扑、抽象代数、傅里叶
│   └── registry.py          # 课程注册中心
├── visualization/           # 可视化模块
│   └── tui_viz.py           # 终端可视化
├── templates/               # Web 模板
└── static/                  # Web 资源
```

## 许可证

GPL-3.0-or-later

## 致谢

项目名称来源于《九章算术》，中国现存最早的数学专著，约成书于公元前200年左右。
