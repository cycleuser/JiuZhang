"""Research module for JiuZhang.

Provides mathematical research capabilities: literature search, derivation,
experiment design, code generation, visualization, frontier mathematics,
open problems, counterexample search, proof assistance, and LaTeX generation.
"""

from jiuzhang.research.engine import ResearchEngine, ResearchResult, ResearchTopic
from jiuzhang.research.assistant import FrontierResearchAssistant
from jiuzhang.research.frontier import FrontierMathKB, FrontierTopic
from jiuzhang.research.literature import LiteratureSearcher
from jiuzhang.research.derivation import MathDeriver
from jiuzhang.research.experiment import ExperimentDesigner
from jiuzhang.research.paper_reader import PaperReader
from jiuzhang.research.frontier_viz import FrontierVisualizer
from jiuzhang.research.open_problems import OpenProblemsDB, OpenProblem
from jiuzhang.research.counterexamples import CounterexampleFinder, ConjectureVerifier
from jiuzhang.research.latex_generator import LaTeXPaperGenerator
from jiuzhang.research.proof_assistant import ProofAssistant, Proof, ProofStep

__all__ = [
    "ResearchEngine",
    "ResearchResult",
    "ResearchTopic",
    "FrontierResearchAssistant",
    "FrontierMathKB",
    "FrontierTopic",
    "LiteratureSearcher",
    "MathDeriver",
    "ExperimentDesigner",
    "PaperReader",
    "FrontierVisualizer",
    "OpenProblemsDB",
    "OpenProblem",
    "CounterexampleFinder",
    "ConjectureVerifier",
    "LaTeXPaperGenerator",
    "ProofAssistant",
    "Proof",
    "ProofStep",
]
