"""Constants for JiuZhang."""

# Application
APP_NAME = "JiuZhang"
APP_NAME_CN = "九章"
APP_DESCRIPTION = "A comprehensive mathematics learning platform"
APP_DESCRIPTION_CN = "从基础到前沿的数学学习平台"

# Default settings
DEFAULT_LANGUAGE = "zh"
DEFAULT_PROVIDER = "ollama"
DEFAULT_MODEL = "qwen2.5:7b"
DEFAULT_MAX_TOKENS = 8192
DEFAULT_TEMPERATURE = 1.0

# Math levels
MATH_LEVELS = [
    "elementary",  # 小学
    "middle_school",  # 初中
    "high_school",  # 高中
    "undergraduate",  # 本科
    "graduate",  # 研究生
    "frontier",  # 前沿
]

MATH_LEVEL_NAMES_CN = {
    "elementary": "小学",
    "middle_school": "初中",
    "high_school": "高中",
    "undergraduate": "本科",
    "graduate": "研究生",
    "frontier": "前沿",
}

# Course categories
COURSE_CATEGORIES = [
    "arithmetic",  # 算术
    "algebra",  # 代数
    "geometry",  # 几何
    "probability",  # 概率统计
    "calculus",  # 微积分
    "linear_algebra",  # 线性代数
    "advanced",  # 前沿数学
]

COURSE_CATEGORY_NAMES_CN = {
    "arithmetic": "算术",
    "algebra": "代数",
    "geometry": "几何",
    "probability": "概率统计",
    "calculus": "微积分",
    "linear_algebra": "线性代数",
    "advanced": "前沿数学",
}

# Visualization backends
VIZ_BACKENDS = ["manim", "pyqtgraph", "web", "tui"]

# Knowledge point status
KNOWLEDGE_STATUS = [
    "not_started",
    "in_progress",
    "completed",
    "mastered",
]
