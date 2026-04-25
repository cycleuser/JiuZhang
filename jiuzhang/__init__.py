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

Math reasoning engine:
- Specialized prompting (theorem proof, problem solving, symbolic computation)
- SymPy-backed symbolic verification of LLM outputs
- Self-consistency checking
- Conjecture discovery engine (automated pattern finding + counterexample search)
- SmallMathModel fine-tuning framework (QLoRA / Unsloth / Ollama)
- Curriculum-organized training data pipeline with SymPy ground truth
- Math evaluation benchmark (GSM8K-style)
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
from jiuzhang.math_reasoning import MathReasoningEngine, MathReasoningResult
from jiuzhang.symbolic_verify import verify_equation, verify_derivative, verify_integral, verify_solution
from jiuzhang.conjecture_engine import ConjectureEngine
from jiuzhang.math_benchmark import MathBenchmark
from jiuzhang.curriculum_pipeline import CurriculumDataPipeline
from jiuzhang.code_interpreter import CodeInterpreter, CodeExecutionResult
from jiuzhang.rejection_sampling import RejectionSampler
from jiuzhang.self_correction_generator import SelfCorrectionDataGenerator
from jiuzhang.step_verifier import StepByStepVerifier
from jiuzhang.distillation_pipeline import DistillationPipeline, DistilledSample, DistillationResult
from jiuzhang.low_vram_training import LowVRAMConfig, LowVRAMTrainer
from jiuzhang.math_extractor import (
    MathKnowledgeExtractor,
    LocalModelExtractor,
    MathKnowledgeExtractor,
    GGUFModelInfo,
    ExtractionResult,
    SUPPORTED_1B_MODELS,
)

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
    "MathReasoningEngine",
    "MathReasoningResult",
    "verify_equation",
    "verify_derivative",
    "verify_integral",
    "verify_solution",
    "ConjectureEngine",
    "MathBenchmark",
    "CurriculumDataPipeline",
    "CodeInterpreter",
    "CodeExecutionResult",
    "RejectionSampler",
    "SelfCorrectionDataGenerator",
    "StepByStepVerifier",
    "DistillationPipeline",
    "DistilledSample",
    "DistillationResult",
    "LowVRAMConfig",
    "LowVRAMTrainer",
    "MathKnowledgeExtractor",
    "LocalModelExtractor",
    "GGUFModelInfo",
    "ExtractionResult",
    "SUPPORTED_1B_MODELS",
]
