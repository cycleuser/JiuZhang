"""Enhanced research report generation module.

Generates comprehensive research reports with all components,
proper formatting, and structured sections.
"""

from typing import Optional
from datetime import datetime

from jiuzhang.core.config import Config
from jiuzhang.core.multi_provider_api import MultiProviderClient


class ResearchReportGenerator:
    """Generates comprehensive research reports."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.client = MultiProviderClient(self.config)

    def generate(self, research_result, language: str = "zh") -> str:
        """Generate a complete research report.

        Args:
            research_result: ResearchResult object
            language: Output language

        Returns:
            Complete research report as markdown
        """
        parts = []

        # Header
        if language == "zh":
            parts.append(f"# 数学研究报告：{research_result.topic}\n")
            parts.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            parts.append(
                f"研究深度：{research_result.metadata.get('depth', 'medium')}\n"
            )
        else:
            parts.append(f"# Mathematical Research Report: {research_result.topic}\n")
            parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            parts.append(f"Depth: {research_result.metadata.get('depth', 'medium')}\n")

        parts.append("---\n")

        # Table of Contents
        if language == "zh":
            parts.append("## 目录\n")
            parts.append("1. [主题分析](#1-主题分析)")
            parts.append("2. [文献综述](#2-文献综述)")
            parts.append("3. [数学推导](#3-数学推导)")
            parts.append("4. [实验设计与代码](#4-实验设计与代码)")
            parts.append("5. [可视化结果](#5-可视化结果)")
            parts.append("6. [参考文献](#6-参考文献)")
            parts.append("---\n")
        else:
            parts.append("## Table of Contents\n")
            parts.append("1. [Topic Analysis](#1-topic-analysis)")
            parts.append("2. [Literature Review](#2-literature-review)")
            parts.append("3. [Mathematical Derivation](#3-mathematical-derivation)")
            parts.append("4. [Experiment Design & Code](#4-experiment-design--code)")
            parts.append("5. [Visualizations](#5-visualizations)")
            parts.append("6. [References](#6-references)")
            parts.append("---\n")

        # Section 1: Topic Analysis
        if research_result.summary:
            parts.append(
                "## 1. 主题分析\n\n" if language == "zh" else "## 1. Topic Analysis\n\n"
            )
            parts.append(research_result.summary + "\n\n")

        # Section 2: Literature Review
        if research_result.literature_review:
            parts.append(
                "## 2. 文献综述\n\n"
                if language == "zh"
                else "## 2. Literature Review\n\n"
            )
            parts.append(research_result.literature_review + "\n\n")

        # Section 3: Mathematical Derivation
        if research_result.mathematical_derivation:
            parts.append(
                "## 3. 数学推导\n\n"
                if language == "zh"
                else "## 3. Mathematical Derivation\n\n"
            )
            parts.append(research_result.mathematical_derivation + "\n\n")

        # Section 4: Experiments
        if research_result.experiments:
            parts.append(
                "## 实验设计与代码\n\n"
                if language == "zh"
                else "## Experiment Design & Code\n\n"
            )
            for i, exp in enumerate(research_result.experiments, 1):
                parts.append(f"### 实验 {i}\n\n")
                title = exp.get("title", "")
                if title:
                    parts.append(f"{title}\n\n")
                desc = exp.get("description", "")
                if desc:
                    parts.append(f"{desc}\n\n")
                expected = exp.get("expected_output", "")
                if expected:
                    parts.append(f"预期输出：{expected}\n\n")
                code = exp.get("code", "")
                if code:
                    parts.append(f"```python\n{code}\n```\n\n")

        # Section 5: Visualizations
        if research_result.visualizations:
            parts.append(
                "## 5. 可视化结果\n\n"
                if language == "zh"
                else "## 5. Visualizations\n\n"
            )
            parts.append(
                f"共生成 {len(research_result.visualizations)} 个可视化图表。\n\n"
            )
            for i, viz in enumerate(research_result.visualizations, 1):
                parts.append(f"### 图表 {i}: {viz.get('type', 'unknown')}\n")
                parts.append("![Visualization](data:image/png;base64,...)\n\n")

        # Section 6: References
        if research_result.references:
            parts.append("## 参考文献\n\n" if language == "zh" else "## References\n\n")
            for i, ref in enumerate(research_result.references, 1):
                authors = ref.get("authors", "Unknown")
                title = ref.get("title", "Unknown")
                source = ref.get("source", "")
                year = ref.get("published", "")[:4] if ref.get("published") else ""
                url = ref.get("url", "")

                ref_str = f"[{i}] {authors}. {title}."
                if source:
                    ref_str += f" {source},"
                if year:
                    ref_str += f" {year}."
                else:
                    ref_str += "."
                if url:
                    ref_str += f" {url}"
                parts.append(ref_str + "\n")

        # Footer
        parts.append("\n---\n")
        if language == "zh":
            parts.append("*本报告由九章 (JiuZhang) 数学研究平台自动生成*\n")
            parts.append(
                f"*研究时间: {research_result.metadata.get('start_time', '')} - {research_result.metadata.get('end_time', '')}*\n"
            )
        else:
            parts.append(
                "*This report was automatically generated by JiuZhang Mathematics Research Platform*\n"
            )
            parts.append(
                f"*Research time: {research_result.metadata.get('start_time', '')} - {research_result.metadata.get('end_time', '')}*\n"
            )

        return "\n".join(parts)
