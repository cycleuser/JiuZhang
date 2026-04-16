"""JiuZhang (九章) - A comprehensive mathematics learning and research platform.

From basic number concepts to frontier mathematics, with code implementations,
visualizations, and thorough explanations. Supports multiple AI model providers
including Ollama, OpenAI, Anthropic, and Alibaba CodingPlan.

Research capabilities:
- Literature search (arXiv, CrossRef)
- Advanced symbolic computation (differential geometry, Lie theory, etc.)
- Frontier mathematics knowledge base (15 topics across 8 fields)
- Open problems database (Millennium Prize Problems and more)
- Counterexample search and conjecture verification
- Proof assistant
- LaTeX paper generation
- Advanced visualizations (3D manifolds, root systems, fractals, etc.)
"""

__version__ = "0.0.1"
__author__ = "JiuZhang Contributors"
__license__ = "GPL-3.0-or-later"

from jiuzhang.core.errors import ToolResult, JiuZhangError
from jiuzhang.core.config import Config
from jiuzhang.api import JiuZhangAPI
from jiuzhang.courses.registry import CourseRegistry
from jiuzhang.research.assistant import FrontierResearchAssistant
from jiuzhang.research.open_problems import OpenProblemsDB
from jiuzhang.research.counterexamples import CounterexampleFinder, ConjectureVerifier
from jiuzhang.research.latex_generator import LaTeXPaperGenerator
from jiuzhang.research.proof_assistant import ProofAssistant, Proof

__all__ = [
    "__version__",
    "ToolResult",
    "JiuZhangError",
    "Config",
    "JiuZhangAPI",
    "CourseRegistry",
    "FrontierResearchAssistant",
    "OpenProblemsDB",
    "CounterexampleFinder",
    "ConjectureVerifier",
    "LaTeXPaperGenerator",
    "ProofAssistant",
    "Proof",
]
