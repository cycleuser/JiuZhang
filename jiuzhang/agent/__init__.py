"""Autonomous Math Research Agent core for JiuZhang.

Inspired by:
- autoresearch (Karpathy): autonomous experiment loop, program.md, results.tsv tracking
- nanobot (HKUDS): async message-bus, tool auto-discovery, Dream memory consolidation
- smallcode: context budget management, tool routing, plan tracking, escalation engine

Provides:
- AgentLoop: synchronous autonomous research loop (backward-compatible)
- AsyncAgentLoop: fully async research loop with parallel execution and streaming
- QualityController: quality governance with verifier, early-stop, auto-rollback
- IntegratedContextManager: thinking budget + token counting + auto-compaction
- ContextBudgetManager: token-aware context optimization for small models
- PlanTracker: multi-step research planning with dependency graphs
- EscalationEngine: model tiering with automatic fallback to cloud models
- ResearchProgram: human-written research directives (like autoresearch program.md)
"""

from jiuzhang.agent.loop import AgentLoop, AgentState, ExperimentResult
from jiuzhang.agent.async_loop import AsyncAgentLoop, ResearchProgress
from jiuzhang.agent.context_budget import (
    ContextBudgetManager, ToolRouter, ToolCategory, RouteResult,
    compress_math_context, estimate_tokens,
)
from jiuzhang.agent.context_manager import (
    IntegratedContextManager, AutoCompactor, ThinkingBudget, ThinkingMode,
    CompactionLevel, CompactionResult,
)
from jiuzhang.agent.quality_governance import (
    QualityController, QualityVerifier, QualityReport, QualityVerdict,
    EarlyStopGovernor, StagnationReason, GovernorState,
    ToolScorer, ToolTrustRecord,
    AutoRollback, Checkpoint,
    MathClaimGuard,
    InjectionHandler, Injection,
)
from jiuzhang.agent.plan_tracker import PlanTracker, ResearchPlan, PlanStep
from jiuzhang.agent.escalation import EscalationEngine, EscalationConfig, EscalationReason
from jiuzhang.agent.research_program import ResearchProgram

__all__ = [
    # Core agent
    "AgentLoop",
    "AsyncAgentLoop",
    "ResearchProgress",
    "AgentState",
    "ExperimentResult",
    # Context management (Phase 2)
    "IntegratedContextManager",
    "AutoCompactor",
    "ThinkingBudget",
    "ThinkingMode",
    "CompactionLevel",
    "CompactionResult",
    "ContextBudgetManager",
    "ToolRouter",
    "ToolCategory",
    "RouteResult",
    "compress_math_context",
    "estimate_tokens",
    # Quality governance (Phase 2)
    "QualityController",
    "QualityVerifier",
    "QualityReport",
    "QualityVerdict",
    "EarlyStopGovernor",
    "StagnationReason",
    "GovernorState",
    "ToolScorer",
    "ToolTrustRecord",
    "AutoRollback",
    "Checkpoint",
    "MathClaimGuard",
    "InjectionHandler",
    "Injection",
    # Planning & escalation
    "PlanTracker",
    "ResearchPlan",
    "PlanStep",
    "EscalationEngine",
    "EscalationConfig",
    "EscalationReason",
    "ResearchProgram",
]
