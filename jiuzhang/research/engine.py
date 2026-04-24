"""Enhanced Mathematical Research Engine for JiuZhang.

Orchestrates the complete research pipeline with progress tracking,
parallel processing, and comprehensive error handling.
"""

import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from jiuzhang.core.config import Config
from jiuzhang.core.multi_provider_api import MultiProviderClient
from jiuzhang.core.errors import ToolResult
from jiuzhang.research.literature import LiteratureSearcher
from jiuzhang.research.derivation import MathDeriver
from jiuzhang.research.experiment import ExperimentDesigner
from jiuzhang.research.report import ResearchReportGenerator
from jiuzhang.research.writing_style import WRITING_PRINCIPLES


@dataclass
class ResearchTopic:
    """A research topic with metadata."""

    query: str
    language: str = "zh"
    depth: str = "medium"
    include_code: bool = True
    include_visualization: bool = True
    include_literature: bool = True


@dataclass
class ResearchResult:
    """Complete research result."""

    topic: str
    summary: str = ""
    literature_review: str = ""
    papers: list = field(default_factory=list)
    mathematical_derivation: str = ""
    experiments: list = field(default_factory=list)
    visualizations: list = field(default_factory=list)
    code_snippets: list = field(default_factory=list)
    references: list = field(default_factory=list)
    full_report: str = ""
    metadata: dict = field(default_factory=dict)


class ResearchEngine:
    """Enhanced mathematical research engine.

    Usage:
        engine = ResearchEngine()
        result = engine.research("傅里叶变换的数学原理")
        print(result.full_report)
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.client = MultiProviderClient(self.config)
        self.literature = LiteratureSearcher()
        self.deriver = MathDeriver(self.config)
        self.experiment = ExperimentDesigner(self.config)
        self.report_gen = ResearchReportGenerator(self.config)
        self._output_dir = Path.home() / ".jiuzhang" / "research"
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._progress_callback: Optional[Callable] = None

    def set_progress_callback(self, callback: Callable):
        """Set a callback for progress updates.

        Args:
            callback: Function(stage: int, total: int, message: str)
        """
        self._progress_callback = callback

    def _report_progress(self, stage: int, total: int, message: str):
        """Report progress to callback."""
        if self._progress_callback:
            self._progress_callback(stage, total, message)

    def research(
        self,
        query: str,
        language: Optional[str] = None,
        depth: str = "medium",
        include_code: bool = True,
        include_visualization: bool = True,
        include_literature: bool = True,
    ) -> ResearchResult:
        """Conduct complete mathematical research on a topic.

        Pipeline:
        1. Topic Analysis - AI decomposes the research question
        2. Literature Search - Search arXiv and CrossRef for papers
        3. Mathematical Derivation - Symbolic computation + AI proofs
        4. Experiment Design - Generate runnable code and visualizations
        5. Report Generation - Compile comprehensive research report

        Args:
            query: Research query/topic
            language: Language for output (default: config language)
            depth: Research depth (shallow/medium/deep)
            include_code: Whether to generate code
            include_visualization: Whether to generate visualizations
            include_literature: Whether to search literature

        Returns:
            ResearchResult with complete research output
        """
        lang = language or self.config.language
        topic = ResearchTopic(
            query=query,
            language=lang,
            depth=depth,
            include_code=include_code,
            include_visualization=include_visualization,
            include_literature=include_literature,
        )

        result = ResearchResult(topic=query)
        result.metadata = {
            "start_time": datetime.now().isoformat(),
            "language": lang,
            "depth": depth,
            "pipeline_version": "2.0",
        }

        total_stages = 5
        current_stage = 0

        # Stage 1: Topic Analysis
        current_stage += 1
        self._report_progress(current_stage, total_stages, "分析研究主题...")
        result.summary = self._analyze_topic(topic)

        # Stage 2: Literature Search
        if include_literature:
            current_stage += 1
            self._report_progress(current_stage, total_stages, "搜索学术文献...")
            papers = self.literature.search(query, max_results=10)
            result.papers = papers
            result.literature_review = self.literature.generate_review(papers, lang)
            result.references = [
                {
                    "title": p.get("title", ""),
                    "authors": p.get("authors", ""),
                    "url": p.get("url", ""),
                    "source": p.get("source", ""),
                    "published": p.get("published", ""),
                }
                for p in papers
            ]

        # Stage 3: Mathematical Derivation
        current_stage += 1
        self._report_progress(current_stage, total_stages, "进行数学推导...")
        result.mathematical_derivation = self.deriver.derive(query, lang, depth)

        # Stage 4: Experiment Design
        if include_code:
            current_stage += 1
            self._report_progress(current_stage, total_stages, "设计实验代码...")
            experiments = self.experiment.design(query, lang, depth)
            result.experiments = experiments
            result.code_snippets = [exp.get("code", "") for exp in experiments]

        # Stage 5: Visualization
        if include_visualization:
            self._report_progress(total_stages, total_stages, "生成可视化图表...")
            result.visualizations = self.experiment.generate_visualizations(
                query, experiments
            )

        # Generate final report
        result.full_report = self.report_gen.generate(result, lang)
        result.metadata["end_time"] = datetime.now().isoformat()

        # Save result
        self._save_result(result)

        return result

    def _analyze_topic(self, topic: ResearchTopic) -> str:
        """Analyze and decompose the research topic."""
        lang = topic.language
        prompt = f"""请对以下数学研究主题进行深入分析和分解：

主题：{topic.query}
研究深度：{topic.depth}

写作要求：
{WRITING_PRINCIPLES}

请包含以下内容（使用自然段落，不要分点）：

主题概述：介绍该主题是什么，在数学中的地位。

核心概念：涉及的关键数学概念和定义，每个概念后标注来源。

历史背景：该主题的发展历程和重要人物，引用相关文献。

研究现状：当前的研究热点和开放问题，引用最新文献。

应用价值：在实际中的应用领域，给出具体例子。

学习路径：研究该主题需要的前置知识。

参考文献：在文末列出所有引用的文献，格式为 [编号] 作者。文献名。期刊/出版社，年份。

请用{"中文" if lang == "zh" else "English"}详细回答。"""

        messages = [{"role": "user", "content": prompt}]
        result = self.client.send_message(messages)
        return result.data if result.success else f"分析失败: {result.error}"

    def _save_result(self, result: ResearchResult):
        """Save research result to file."""
        import logging

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"research_{timestamp}.json"
        filepath = self._output_dir / filename

        try:
            data = {
                "topic": result.topic,
                "summary": result.summary,
                "literature_review": result.literature_review,
                "papers": result.papers,
                "mathematical_derivation": result.mathematical_derivation,
                "experiments": result.experiments,
                "visualizations": result.visualizations,
                "code_snippets": result.code_snippets,
                "references": result.references,
                "full_report": result.full_report,
                "metadata": result.metadata,
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.warning(f"Failed to save research result to {filepath}: {e}")

    def get_research_history(self) -> list:
        """Get list of past research results."""
        results = []
        if self._output_dir.exists():
            for f in sorted(self._output_dir.glob("research_*.json"), reverse=True):
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                        results.append(
                            {
                                "file": str(f.name),
                                "topic": data.get("topic", ""),
                                "time": data.get("metadata", {}).get("start_time", ""),
                                "depth": data.get("metadata", {}).get("depth", ""),
                            }
                        )
                except (json.JSONDecodeError, UnicodeDecodeError, KeyError) as e:
                    # Log the error for debugging, but continue processing other files
                    import logging
                    logging.warning(f"Failed to load research file {f.name}: {e}")
                    continue
        return results

    def load_research(self, filename: str) -> Optional[dict]:
        """Load a past research result."""
        # Validate filename to prevent path traversal
        if not self._is_safe_filename(filename):
            return None
        
        filepath = self._output_dir / filename
        # Double-check that resolved path is within output directory
        try:
            filepath.resolve().relative_to(self._output_dir.resolve())
        except ValueError:
            return None  # Path is outside output directory
            
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def delete_research(self, filename: str) -> bool:
        """Delete a past research result."""
        # Validate filename to prevent path traversal
        if not self._is_safe_filename(filename):
            return False
        
        filepath = self._output_dir / filename
        # Double-check that resolved path is within output directory
        try:
            filepath.resolve().relative_to(self._output_dir.resolve())
        except ValueError:
            return False  # Path is outside output directory
            
        if filepath.exists():
            filepath.unlink()
            return True
        return False
    
    def _is_safe_filename(self, filename: str) -> bool:
        """Check if filename is safe (no path traversal, only alphanumeric + ._-)."""
        import re
        # Only allow alphanumeric, underscore, hyphen, dot, and forward slash for subdirectories
        # But prevent path traversal patterns
        if '..' in filename or './' in filename or filename.startswith('/'):
            return False
        # Only allow safe characters in filename
        if not re.match(r'^[a-zA-Z0-9._/-]+$', filename):
            return False
        # Must end with .json
        if not filename.endswith('.json'):
            return False
        return True

    def get_stats(self) -> dict:
        """Get research statistics."""
        history = self.get_research_history()
        topics = {}
        for item in history:
            depth = item.get("depth", "unknown")
            topics[depth] = topics.get(depth, 0) + 1

        return {
            "total_researches": len(history),
            "by_depth": topics,
            "output_dir": str(self._output_dir),
        }
