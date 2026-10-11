"""Lesson generation for JiuZhang.

Generates lessons using AI models, with code examples and explanations.
"""

from typing import Optional

from jiuzhang.core.multi_provider_api import MultiProviderClient
from jiuzhang.core.config import Config
from jiuzhang.core.errors import ToolResult
from jiuzhang.math_engine.curriculum import Lesson, KnowledgePoint


class LessonGenerator:
    """Generates mathematics lessons using AI models.

    Can generate lessons in both Chinese and English, with code examples
    and visualization suggestions.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.client = MultiProviderClient(self.config)

    def generate_lesson(
        self,
        topic: str,
        level: str = "elementary",
        language: str = "zh",
        include_code: bool = True,
        include_visualization: bool = True,
    ) -> ToolResult:
        prompt = self._build_prompt(
            topic, level, language, include_code, include_visualization
        )
        messages = [{"role": "user", "content": prompt}]
        return self.client.send_message(messages)

    def _build_prompt(
        self,
        topic: str,
        level: str,
        language: str,
        include_code: bool,
        include_visualization: bool,
    ) -> str:
        lang_instructions = self._get_language_instructions(language)
        code_section = self._get_code_section(include_code, language)
        viz_section = self._get_visualization_section(include_visualization, language)

        return f"""{lang_instructions}

请为以下数学主题生成一堂完整的课程：

主题：{topic}
目标水平：{level}

课程结构：
1. 概念介绍 - 从基础开始，循序渐进
2. 详细解释 - 用具体例子说明
3. 关键要点 - 总结核心概念
4. 常见误区 - 指出容易混淆的地方
{code_section}
{viz_section}
5. 练习题 - 3-5道由易到难的练习题（附答案）

请确保讲解透彻，让初学者也能理解。"""

    def _get_language_instructions(self, language: str) -> str:
        if language == "zh":
            return "请用中文回答。"
        return "Please answer in English."

    def _get_code_section(self, include_code: bool, language: str) -> str:
        if not include_code:
            return ""
        if language == "zh":
            return "4. 代码实现 - 用 Python 实现相关数学概念（使用 numpy, sympy, manim）"
        return "4. Code Implementation - Python implementation using numpy, sympy, manim"

    def _get_visualization_section(self, include_viz: bool, language: str) -> str:
        if not include_viz:
            return ""
        if language == "zh":
            return "5. 可视化方法 - 如何用图表展示这个概念"
        return "5. Visualization - How to visualize this concept with charts"

    def generate_explanation(
        self,
        concept: str,
        level: str = "beginner",
        language: str = "zh",
    ) -> ToolResult:
        lang_prompt = "请用中文" if language == "zh" else "Please use English"
        prompt = f"""{lang_prompt}详细解释以下数学概念：

概念：{concept}
目标水平：{level}

要求：
1. 用简单易懂的语言
2. 从日常生活的例子引入
3. 逐步深入，保持逻辑清晰
4. 指出与其他概念的联系

解释："""
        messages = [{"role": "user", "content": prompt}]
        return self.client.send_message(messages)

    def generate_exercise(
        self,
        topic: str,
        difficulty: str = "easy",
        count: int = 3,
        language: str = "zh",
    ) -> ToolResult:
        lang_prompt = "请用中文" if language == "zh" else "Please use English"
        prompt = f"""{lang_prompt}生成 {count} 道关于以下主题的练习题：

主题：{topic}
难度：{difficulty}

要求：
1. 每道题后附详细解答
2. 难度循序渐进
3. 包含解题思路

练习题："""
        messages = [{"role": "user", "content": prompt}]
        return self.client.send_message(messages)
