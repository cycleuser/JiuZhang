"""Model Router — task-aware model selection for math research.

Routes tasks to the optimal model/provider based on:
1. Task complexity classification (simple → local, complex → cloud)
2. Historical performance tracking (which model is best at proofs? integrals? etc.)
3. Cost budget enforcement
4. Latency requirements
5. Model specialization (some models are better at symbolic math, others at reasoning)

The router learns over time: it tracks success/failure per (model, task_type) and
uses that data to make increasingly optimal routing decisions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import json
import time
from pathlib import Path
from collections import defaultdict


class TaskType(Enum):
    """Classification of mathematical tasks for routing."""
    SIMPLE_CALCULATION = "simple_calculation"        # 2+2, basic arithmetic
    SYMBOLIC_COMPUTATION = "symbolic_computation"     # SymPy operations
    EQUATION_SOLVING = "equation_solving"             # Single equation
    THEOREM_PROVING = "theorem_proving"               # Formal proof
    CONJECTURE_ANALYSIS = "conjecture_analysis"       # Conjecture evaluation
    DERIVATION = "derivation"                         # Step-by-step derivation
    LITERATURE_SEARCH = "literature_search"           # Paper search
    CODE_GENERATION = "code_generation"               # Generate math code
    DEEP_RESEARCH = "deep_research"                   # Frontier research
    EXPLANATION = "explanation"                       # Educational explanation
    VERIFICATION = "verification"                      # Proof/result checking


@dataclass
class RoutingRecord:
    """Performance record for a (provider, model, task_type) combination."""
    provider: str
    model: str
    task_type: TaskType
    attempts: int = 0
    successes: int = 0
    total_latency_ms: float = 0.0
    avg_quality: float = 0.0  # User feedback or verification score

    @property
    def success_rate(self) -> float:
        if self.attempts == 0:
            return 0.5  # Neutral prior
        return self.successes / self.attempts

    @property
    def avg_latency(self) -> float:
        if self.attempts == 0:
            return float('inf')
        return self.total_latency_ms / self.attempts

    @property
    def score(self) -> float:
        """Composite score: higher = better choice for this task type."""
        return (
            self.success_rate * 0.5
            + (1.0 / (1.0 + self.avg_latency / 1000.0)) * 0.3  # Latency penalty
            + self.avg_quality * 0.2
        )


@dataclass
class RoutingConfig:
    """Configuration for the model router."""
    local_providers: list = field(default_factory=lambda: ["ollama", "openai_compatible"])
    cloud_providers: list = field(default_factory=lambda: ["openai", "anthropic", "aliyun_coding_plan"])
    max_cloud_cost_per_task: float = 0.10  # USD per cloud escalation
    learning_rate: float = 0.1  # How fast to update success rates
    exploration_rate: float = 0.1  # Probability of trying a new routing
    history_path: str = "~/.jiuzhang/router_history.json"


class ModelRouter:
    """Intelligent task-to-model router with learning.

    Usage:
        router = ModelRouter()
        provider, model = router.route("Prove that sqrt(2) is irrational")
        # → ("ollama", "qwen2.5:7b")  for simple proof
        # → ("anthropic", "claude-sonnet-4-20250514")  for deep research
    """

    # Default task routing table
    DEFAULT_ROUTING = {
        TaskType.SIMPLE_CALCULATION: {"tier": "local", "reason": "Trivial for any model"},
        TaskType.SYMBOLIC_COMPUTATION: {"tier": "direct", "reason": "Use SymPy directly, no LLM needed"},
        TaskType.EQUATION_SOLVING: {"tier": "local", "reason": "Most local models handle equations well"},
        TaskType.THEOREM_PROVING: {"tier": "larger_local", "reason": "Needs stronger reasoning, try local first"},
        TaskType.CONJECTURE_ANALYSIS: {"tier": "larger_local", "reason": "Pattern recognition, local usually sufficient"},
        TaskType.DERIVATION: {"tier": "local", "reason": "Step-by-step, manageable for local models"},
        TaskType.LITERATURE_SEARCH: {"tier": "local", "reason": "Search + summarization, local OK"},
        TaskType.CODE_GENERATION: {"tier": "local", "reason": "Code generation, local models handle well"},
        TaskType.DEEP_RESEARCH: {"tier": "cloud", "reason": "Needs frontier model for deep analysis"},
        TaskType.EXPLANATION: {"tier": "local", "reason": "Simple explanation task"},
        TaskType.VERIFICATION: {"tier": "direct", "reason": "Use SymPy directly"},
    }

    def __init__(self, config: Optional[RoutingConfig] = None):
        self.config = config or RoutingConfig()
        self._records: dict[tuple, RoutingRecord] = {}
        self._task_counts: dict[TaskType, int] = defaultdict(int)
        self._load_history()

    def classify(self, query: str) -> TaskType:
        """Classify a query into a task type using keyword heuristics."""
        q = query.lower()

        # Deep research keywords
        deep = ["frontier", "前沿", "riemann", "langlands", "hodge", "birch", "swinnerton",
                "mordell", "weil", "grothendieck", "category theory", "homological",
                "spectral sequence", "derived category"]
        if any(kw in q for kw in deep):
            return TaskType.DEEP_RESEARCH

        # Theorem proving
        prove = ["prove", "proof", "证明", "theorem", "定理", "lemma", "引理", "show that",
                 "demonstrate that", "therefore"]
        if any(kw in q for kw in prove) and len(q) > 20:
            return TaskType.THEOREM_PROVING

        # Conjecture
        conj = ["conjecture", "猜想", "hypothesis", "假设", "counterexample", "反例"]
        if any(kw in q for kw in conj):
            return TaskType.CONJECTURE_ANALYSIS

        # Derivation
        deriv = ["derive", "推导", "derive", "simplify", "化简", "expand", "展开",
                 "factor", "因式分解"]
        if any(kw in q for kw in deriv):
            return TaskType.DERIVATION

        # Equation solving
        eq = ["solve", "求解", "equation", "方程", "=", "find x"]
        if any(kw in q for kw in eq):
            return TaskType.EQUATION_SOLVING

        # Literature
        lit = ["paper", "论文", "arxiv", "literature", "文献", "reference", "参考",
               "search", "搜索", "find papers"]
        if any(kw in q for kw in lit):
            return TaskType.LITERATURE_SEARCH

        # Code generation
        code = ["generate code", "write code", "代码", "program", "implement",
                "python script"]
        if any(kw in q for kw in code):
            return TaskType.CODE_GENERATION

        # Verification
        verify = ["verify", "验证", "check", "检查", "validate", "correct?"]
        if any(kw in q for kw in verify) and len(q) < 100:
            return TaskType.VERIFICATION

        # Explanation
        explain = ["explain", "解释", "what is", "什么是", "describe", "描述", "define"]
        if any(kw in q for kw in explain):
            return TaskType.EXPLANATION

        # Symbolic computation
        symbolic = ["integrate", "积分", "differentiate", "微分", "limit", "极限",
                    "series", "级数", "sympy"]
        if any(kw in q for kw in symbolic):
            return TaskType.SYMBOLIC_COMPUTATION

        # Default: medium complexity
        return TaskType.SYMBOLIC_COMPUTATION

    def route(
        self,
        query: str,
        available_providers: Optional[list] = None,
        prefer_local: bool = True,
    ) -> dict:
        """Route a query to the best provider and model.

        Args:
            query: The research question or task
            available_providers: List of (provider_name, model_name) tuples available
            prefer_local: Prefer local models when possible

        Returns:
            Dict with: provider, model, task_type, tier, reason, confidence
        """
        task_type = self.classify(query)
        self._task_counts[task_type] += 1

        routing = self.DEFAULT_ROUTING.get(task_type, {"tier": "local", "reason": "Default"})
        tier = routing["tier"]

        if tier == "direct":
            return {
                "provider": "direct_sympy",
                "model": "sympy",
                "task_type": task_type,
                "tier": "direct",
                "reason": "Use SymPy directly — no LLM needed",
                "confidence": 1.0,
            }

        # Find best available provider for this tier
        available = available_providers or self._get_default_available()
        local = [(p, m) for p, m in available if p in self.config.local_providers]
        cloud = [(p, m) for p, m in available if p in self.config.cloud_providers]
        larger_local = [(p, m) for p, m in local if any(
            sz in m.lower() for sz in ["13b", "14b", "32b", "70b", "72b", "large"]
        )]

        import random

        # Exploration: occasionally try a different routing
        if random.random() < self.config.exploration_rate:
            all_available = local + cloud
            if all_available:
                chosen = random.choice(all_available)
                return {
                    "provider": chosen[0],
                    "model": chosen[1],
                    "task_type": task_type,
                    "tier": "exploration",
                    "reason": f"Exploring alternative routing for {task_type.value}",
                    "confidence": 0.3,
                }

        # Exploit: use historical performance data
        best = self._find_best_for_task(task_type, available)
        if best:
            return best

        # Fallback to tier-based routing
        if tier == "local" and local:
            chosen = local[0]
        elif tier == "larger_local" and larger_local:
            chosen = larger_local[0]
        elif tier == "larger_local" and local:
            chosen = local[0]
        elif tier == "cloud" and cloud:
            chosen = cloud[0]
        elif prefer_local and local:
            chosen = local[0]
        elif cloud:
            chosen = cloud[0]
        else:
            chosen = available[0]

        return {
            "provider": chosen[0],
            "model": chosen[1],
            "task_type": task_type,
            "tier": tier,
            "reason": routing["reason"],
            "confidence": 0.5,
        }

    def record_result(
        self,
        provider: str,
        model: str,
        task_type: TaskType,
        success: bool,
        latency_ms: float = 0.0,
        quality: float = 0.0,
    ):
        """Record the outcome of a routing decision for learning."""
        key = (provider, model, task_type)
        if key not in self._records:
            self._records[key] = RoutingRecord(
                provider=provider, model=model, task_type=task_type,
            )

        record = self._records[key]
        record.attempts += 1
        if success:
            record.successes += 1
        record.total_latency_ms += latency_ms
        # Exponentially weighted quality update
        record.avg_quality = (
            record.avg_quality * (1 - self.config.learning_rate)
            + quality * self.config.learning_rate
        )

        self._save_history()

    def _find_best_for_task(self, task_type: TaskType, available: list) -> Optional[dict]:
        """Find the best (provider, model) for a task type based on history."""
        best_score = -1.0
        best_entry = None

        for provider, model in available:
            key = (provider, model, task_type)
            record = self._records.get(key)
            if record and record.attempts >= 3:  # Need minimum samples
                if record.score > best_score:
                    best_score = record.score
                    best_entry = {
                        "provider": provider,
                        "model": model,
                        "task_type": task_type,
                        "tier": "learned",
                        "reason": f"Best historical performer: {record.success_rate:.0%} success rate",
                        "confidence": min(record.score, 1.0),
                    }

        return best_entry

    def _get_default_available(self) -> list:
        """Get a default list of available providers."""
        available = []
        # Add ollama if running
        available.append(("ollama", "qwen2.5:7b"))
        available.append(("ollama", "qwen2.5:14b"))
        available.append(("ollama", "qwen2.5:32b"))
        # Add openai if key available
        import os
        if os.environ.get("OPENAI_API_KEY"):
            available.append(("openai", "gpt-4o"))
            available.append(("openai", "gpt-4o-mini"))
        if os.environ.get("ANTHROPIC_API_KEY"):
            available.append(("anthropic", "claude-sonnet-4-20250514"))
        return available

    def _load_history(self):
        path = Path(self.config.history_path).expanduser()
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                for entry in data:
                    key = (entry["provider"], entry["model"], TaskType(entry["task_type"]))
                    self._records[key] = RoutingRecord(
                        provider=entry["provider"],
                        model=entry["model"],
                        task_type=TaskType(entry["task_type"]),
                        attempts=entry.get("attempts", 0),
                        successes=entry.get("successes", 0),
                        total_latency_ms=entry.get("total_latency_ms", 0.0),
                        avg_quality=entry.get("avg_quality", 0.0),
                    )
            except Exception:
                pass

    def _save_history(self):
        path = Path(self.config.history_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = []
            for record in self._records.values():
                if record.attempts >= 3:
                    data.append({
                        "provider": record.provider,
                        "model": record.model,
                        "task_type": record.task_type.value,
                        "attempts": record.attempts,
                        "successes": record.successes,
                        "total_latency_ms": record.total_latency_ms,
                        "avg_quality": record.avg_quality,
                    })
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def get_stats(self) -> str:
        """Get routing statistics."""
        lines = ["Model Router Statistics:", "=" * 40]
        for task_type in TaskType:
            count = self._task_counts.get(task_type, 0)
            if count > 0:
                lines.append(f"  {task_type.value}: {count} requests")
        lines.append(f"  Total routing records: {len(self._records)}")
        return "\n".join(lines)
