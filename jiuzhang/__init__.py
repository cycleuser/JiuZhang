"""JiuZhang (九章) — World-Class Autonomous Mathematical Research Platform.

From basic number concepts to frontier mathematics, now with fully autonomous
research capabilities inspired by autoresearch (Karpathy), nanobot (HKUDS),
and smallcode.

V3 Capabilities (this release):
- **AsyncAgentLoop**: Fully async research loop with parallel proof + literature + counterexample search
- **ProviderFactory**: nanobot-style provider lifecycle with health monitoring, circuit breakers, fallback chains
- **QualityController**: smallcode-grade quality governance with verifier, early-stop, auto-rollback
- **IntegratedContextManager**: Thinking budget + token counting + auto-compaction for small models
- **ResearchFlywheelBridge**: Closed-loop self-improvement — discoveries → training data → better model
- **SkillManager + MCPClient**: Extensible tool ecosystem with SKILL.md patterns and MCP protocol
- **ResearchTerminal**: Rich-based CLI with live split-pane display, interactive steering, LaTeX preview
- **WebDashboard**: FastAPI + htmx web interface with live experiment feed and metrics
- **ResearchSwarm**: Multi-agent parallel exploration with periodic synthesis
- **PaperGenerator**: Automated LaTeX paper generation from verified results
- **DreamConsolidatorV2**: Cross-session knowledge transfer with FTS search

Classic capabilities:
- Method Registry: 50+ mathematical methods
- Solver Pipeline: Step-by-step solution with verification
- Hybrid Reasoning: Symbolic + LLM reasoning
- Manim Visualizations: PNG/MP4 output
- Literature search (arXiv, CrossRef)
- Conjecture discovery engine
- Open problems database
- Math evaluation benchmark
"""

__version__ = "3.0.0"
__author__ = "JiuZhang Contributors"
__license__ = "GPL-3.0-or-later"

# ── Core ──────────────────────────────────────────────────────────────
from jiuzhang.core.errors import ToolResult, JiuZhangError
from jiuzhang.core.config import Config
from jiuzhang.api import JiuZhangAPI
from jiuzhang.courses.registry import CourseRegistry

# ── Research ──────────────────────────────────────────────────────────
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
    MathKnowledgeExtractor, LocalModelExtractor,
    GGUFModelInfo, ExtractionResult, SUPPORTED_1B_MODELS,
)

# Solver module
from jiuzhang.solver.method_registry import MethodRegistry, MathMethod, MethodCategory
from jiuzhang.solver.problem_classifier import ProblemClassifier, ProblemType as SolverProblemType, ClassificationResult
from jiuzhang.solver.pipeline import SolverPipeline, SolveResult

# Reasoning module
from jiuzhang.reasoning.hybrid_engine import HybridReasoningEngine, ReasoningResult
from jiuzhang.reasoning.proof_generator import ProofGenerator, Proof as GeneratedProof, ProofStep as GeneratedProofStep
from jiuzhang.reasoning.method_chain import MethodChain, ChainResult

# Assessment module
from jiuzhang.assessment import AssessmentEngine, Difficulty, QuizConfig, Problem, ProblemType

# ── V3: Agent Core ────────────────────────────────────────────────────
from jiuzhang.agent.loop import AgentLoop, AgentState, ExperimentResult
from jiuzhang.agent.async_loop import AsyncAgentLoop, ResearchProgress
from jiuzhang.agent.context_budget import ContextBudgetManager, ToolRouter, ToolCategory, RouteResult
from jiuzhang.agent.context_manager import (
    IntegratedContextManager, AutoCompactor, ThinkingBudget, ThinkingMode,
)
from jiuzhang.agent.quality_governance import (
    QualityController, QualityVerifier, QualityReport, QualityVerdict,
    EarlyStopGovernor, StagnationReason,
    ToolScorer, AutoRollback, MathClaimGuard, InjectionHandler,
)
from jiuzhang.agent.plan_tracker import PlanTracker, ResearchPlan, PlanStep
from jiuzhang.agent.escalation import EscalationEngine, EscalationConfig, EscalationReason
from jiuzhang.agent.research_program import ResearchProgram
from jiuzhang.agent.memory import (
    ShortTermMemory, LongTermMemory, DreamConsolidator, ResearchFlywheel,
    MemoryEntry, MemoryType, MemoryImportance,
)

# ── V3: Core Infrastructure ───────────────────────────────────────────
from jiuzhang.core.multi_provider_api import MultiProviderClient
from jiuzhang.core.async_provider import AsyncModelProvider, ModelResponse, StreamEvent, StreamEventType
from jiuzhang.core.provider_factory import (
    ProviderFactory, ProviderSnapshot, ProviderMetrics, ProviderHealth, FallbackChain,
)
from jiuzhang.core.model_router import ModelRouter, TaskType, RoutingConfig
from jiuzhang.core.local_optimizations import (
    LocalBackend, LocalModelConfig, check_model_math_capability,
    BatchInferenceRunner, get_reasoning_hint, clean_math_output,
)

# ── V3: Research Infrastructure ───────────────────────────────────────
from jiuzhang.research.debate import DebateProtocol, DebateResult, Verdict, AgentRole
from jiuzhang.research.multi_engine_verify import MultiEngineVerifier, MultiEngineResult, EngineVerdict
from jiuzhang.research.conjecture_synthesizer import ConjectureSynthesizer, SynthesizedConjecture, SynthesisResult
from jiuzhang.research.code_sandbox import CodeSandbox, SandboxConfig, SandboxResult
from jiuzhang.research.tool_registry import ToolRegistry, ToolDefinition, ToolTier, global_tool_registry
from jiuzhang.research.tools import (
    web_search, oeis_lookup, wolfram_query, search_math_stackexchange,
    lean_check, analyze_numeric_data, fetch_arxiv_paper, multi_search,
)
from jiuzhang.research.mcts_explorer import ResearchTreeSearch, MCTSResult, ResearchNode
from jiuzhang.research.proof_compiler import ProofCompiler, CompiledProof, ProofStep, InferenceRule
from jiuzhang.research.journal import ResearchJournal, JournalEntry

# ── V3: Flywheel & Skills ─────────────────────────────────────────────
from jiuzhang.flywheel_bridge import (
    ResearchFlywheelBridge, FlywheelEntry, ExperimentOutcome,
    AutoBenchmark, BenchmarkResult, CapabilityFrontier, ProgramIterator,
)
from jiuzhang.skills_system import SkillManager, SkillLoader, SkillDefinition, BUILTIN_SKILLS
from jiuzhang.mcp_client import MCPClient, MCPTool, MCPServerConfig, ToolDiscovery

# ── V3: Terminal & Web ────────────────────────────────────────────────
from jiuzhang.research_terminal import (
    LiveResearchDisplay, ResearchSession, ResearchCommands,
    research_cli, async_research_cli, show_banner,
)

# ── V3: Advanced Protocols ────────────────────────────────────────────
from jiuzhang.advanced_protocols import (
    ResearchSwarm, SwarmAgentConfig, SwarmAgentResult, DirectionStrategy,
    PaperGenerator, BenchmarkEvaluator, MilestoneTracker, ResearchMilestone,
    DreamConsolidatorV2,
)

__all__ = [
    "__version__",
    # Core
    "ToolResult", "JiuZhangError", "Config", "JiuZhangAPI", "CourseRegistry",
    # Research
    "FrontierResearchAssistant", "OpenProblemsDB",
    "CounterexampleFinder", "ConjectureVerifier",
    "LaTeXPaperGenerator", "ProofAssistant", "Proof",
    "MathReasoningEngine", "MathReasoningResult",
    "verify_equation", "verify_derivative", "verify_integral", "verify_solution",
    "ConjectureEngine", "MathBenchmark", "CurriculumDataPipeline",
    "CodeInterpreter", "CodeExecutionResult",
    "RejectionSampler", "SelfCorrectionDataGenerator", "StepByStepVerifier",
    "DistillationPipeline", "DistilledSample", "DistillationResult",
    "LowVRAMConfig", "LowVRAMTrainer",
    "MathKnowledgeExtractor", "LocalModelExtractor",
    "GGUFModelInfo", "ExtractionResult", "SUPPORTED_1B_MODELS",
    # Solver
    "MethodRegistry", "MathMethod", "MethodCategory",
    "ProblemClassifier", "SolverProblemType", "ClassificationResult",
    "SolverPipeline", "SolveResult",
    # Reasoning
    "HybridReasoningEngine", "ReasoningResult",
    "ProofGenerator", "GeneratedProof", "GeneratedProofStep",
    "MethodChain", "ChainResult",
    # Assessment
    "AssessmentEngine", "Difficulty", "QuizConfig", "Problem", "ProblemType",
    # ── V3 Agent ──
    "AgentLoop", "AsyncAgentLoop", "ResearchProgress", "AgentState", "ExperimentResult",
    "ContextBudgetManager", "ToolRouter", "ToolCategory", "RouteResult",
    "IntegratedContextManager", "AutoCompactor", "ThinkingBudget", "ThinkingMode",
    "QualityController", "QualityVerifier", "QualityReport", "QualityVerdict",
    "EarlyStopGovernor", "StagnationReason",
    "ToolScorer", "AutoRollback", "MathClaimGuard", "InjectionHandler",
    "PlanTracker", "ResearchPlan", "PlanStep",
    "EscalationEngine", "EscalationConfig", "EscalationReason", "ResearchProgram",
    "ShortTermMemory", "LongTermMemory", "DreamConsolidator", "ResearchFlywheel",
    "MemoryEntry", "MemoryType", "MemoryImportance",
    # ── V3 Core Infra ──
    "MultiProviderClient", "AsyncModelProvider", "ModelResponse",
    "StreamEvent", "StreamEventType",
    "ProviderFactory", "ProviderSnapshot", "ProviderMetrics",
    "ProviderHealth", "FallbackChain",
    "ModelRouter", "TaskType", "RoutingConfig",
    "LocalBackend", "LocalModelConfig",
    "check_model_math_capability", "BatchInferenceRunner",
    "get_reasoning_hint", "clean_math_output",
    # ── V3 Research Infra ──
    "DebateProtocol", "DebateResult", "Verdict", "AgentRole",
    "MultiEngineVerifier", "MultiEngineResult", "EngineVerdict",
    "ConjectureSynthesizer", "SynthesizedConjecture", "SynthesisResult",
    "CodeSandbox", "SandboxConfig", "SandboxResult",
    "ToolRegistry", "ToolDefinition", "ToolTier", "global_tool_registry",
    "web_search", "oeis_lookup", "wolfram_query", "search_math_stackexchange",
    "lean_check", "analyze_numeric_data", "fetch_arxiv_paper", "multi_search",
    "ResearchTreeSearch", "MCTSResult", "ResearchNode",
    "ProofCompiler", "CompiledProof", "ProofStep", "InferenceRule",
    "ResearchJournal", "JournalEntry",
    # ── V3 Flywheel & Skills ──
    "ResearchFlywheelBridge", "FlywheelEntry", "ExperimentOutcome",
    "AutoBenchmark", "BenchmarkResult", "CapabilityFrontier", "ProgramIterator",
    "SkillManager", "SkillLoader", "SkillDefinition", "BUILTIN_SKILLS",
    "MCPClient", "MCPTool", "MCPServerConfig", "ToolDiscovery",
    # ── V3 Terminal & Web ──
    "LiveResearchDisplay", "ResearchSession", "ResearchCommands",
    "research_cli", "async_research_cli", "show_banner",
    # ── V3 Advanced Protocols ──
    "ResearchSwarm", "SwarmAgentConfig", "SwarmAgentResult", "DirectionStrategy",
    "PaperGenerator", "BenchmarkEvaluator", "MilestoneTracker", "ResearchMilestone",
    "DreamConsolidatorV2",
]
