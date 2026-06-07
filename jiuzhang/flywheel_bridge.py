"""Research Flywheel Bridge — closed-loop self-improvement for JiuZhang.

Connects the autonomous research agent to the training data flywheel,
implementing the autoresearch core loop:

   Agent discovers → Results become training data → Model retrains → Agent gets smarter

Key capabilities:
- Auto-benchmark: evaluate model after every N experiments
- Results mining: extract training data from research results
- Curriculum detection: find the model's capability frontier
- Program.md auto-iteration: update research strategy based on what works
- Continuous improvement metrics: track and visualize progress over time
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from enum import Enum
import json
import time
import math
from pathlib import Path
from collections import defaultdict


# ── Data Types ────────────────────────────────────────────────────────

class ExperimentOutcome(Enum):
    SUCCESS = "success"         # Verified proof, keep
    FAILURE = "failure"         # Failed verification, discard
    CRASH = "crash"             # Execution error
    STALE = "stale"             # Duplicate/too similar
    NEEDS_WORK = "needs_work"   # Promising but incomplete


@dataclass
class FlywheelEntry:
    """A single entry in the flywheel — becomes training data."""
    id: str
    question: str
    hypothesis: str
    proof: str = ""
    verification: dict = field(default_factory=dict)
    outcome: ExperimentOutcome = ExperimentOutcome.FAILURE
    strength: float = 0.0
    counterexamples: list = field(default_factory=list)
    category: str = ""
    difficulty: str = "medium"
    timestamp: str = ""
    tokens_cost: int = 0

    def to_training_sample(self) -> dict:
        """Convert to a chat-formatted training sample."""
        return {
            "id": self.id,
            "messages": [
                {"role": "system", "content": "You are JiuZhang, an autonomous mathematical research agent. Prove or disprove the following."},
                {"role": "user", "content": f"Research question: {self.question}\nHypothesis: {self.hypothesis}"},
                {"role": "assistant", "content": self.proof},
            ],
            "metadata": {
                "outcome": self.outcome.value,
                "strength": self.strength,
                "verified": self.verification.get("passed", False),
                "category": self.category,
                "difficulty": self.difficulty,
            },
        }

    def to_hard_example(self) -> dict | None:
        """Convert a failure into a hard example for challenging training."""
        if self.outcome != ExperimentOutcome.FAILURE:
            return None
        return {
            "id": f"hard_{self.id}",
            "messages": [
                {"role": "system", "content": "You are a mathematical proof assistant. Given a hypothesis that was previously disproven or incorrectly proven, generate a CORRECT proof or counterexample."},
                {"role": "user", "content": f"The following hypothesis had issues: {self.hypothesis}\n\nOriginal attempt: {self.proof[:500]}\n\nCounterexamples found: {self.counterexamples}\n\nGenerate a corrected analysis."},
            ],
            "metadata": {
                "type": "hard_example",
                "original_outcome": self.outcome.value,
                "category": self.category,
            },
        }


# ── Capability Frontier ──────────────────────────────────────────────

@dataclass
class CapabilityFrontier:
    """Tracks what the model can and cannot do, to guide curriculum."""
    mastered_topics: set = field(default_factory=set)
    struggling_topics: dict = field(default_factory=dict)  # topic → failure count
    unknown_topics: set = field(default_factory=set)
    current_level: str = "intermediate"  # elementary, intermediate, advanced, research

    def record_success(self, category: str):
        self.mastered_topics.add(category)
        self.struggling_topics.pop(category, None)

    def record_failure(self, category: str):
        if category not in self.mastered_topics:
            self.struggling_topics[category] = self.struggling_topics.get(category, 0) + 1

    def get_next_topics(self, all_topics: list[str]) -> list[str]:
        """Get topics at the frontier — known but not yet mastered."""
        frontier = []
        for topic in all_topics:
            if topic in self.struggling_topics:
                frontier.append(topic)
            elif topic in self.mastered_topics:
                continue  # Skip mastered
            else:
                frontier.append(topic)  # Unknown, worth trying
        # Sort by failure count (fewer failures = closer to mastery)
        frontier.sort(key=lambda t: self.struggling_topics.get(t, 0))
        return frontier

    def estimate_level(self) -> str:
        """Estimate the model's overall capability level."""
        total_topics = len(self.mastered_topics) + len(self.struggling_topics) + len(self.unknown_topics)
        if total_topics == 0:
            return "elementary"
        mastery_ratio = len(self.mastered_topics) / max(total_topics, 1)
        if mastery_ratio > 0.7:
            return "research"
        elif mastery_ratio > 0.4:
            return "advanced"
        elif mastery_ratio > 0.2:
            return "intermediate"
        return "elementary"


# ── Auto-Benchmark ────────────────────────────────────────────────────

@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    timestamp: str
    total_problems: int
    solved: int
    accuracy: float
    avg_strength: float
    by_category: dict  # category → accuracy
    flywheel_round: int


class AutoBenchmark:
    """Automatically evaluate the model against held-out math problems.

    Runs after every N flywheel iterations to measure improvement.
    Tracks progress over time and detects regressions.
    """

    def __init__(self, eval_every_n: int = 10):
        self.eval_every_n = eval_every_n
        self._history: list[BenchmarkResult] = []
        self._held_out_problems: list[dict] = []
        self._round = 0

    def add_held_out_problem(self, problem: dict):
        """Add a problem to the held-out evaluation set."""
        self._held_out_problems.append(problem)

    def should_evaluate(self, experiment_count: int) -> bool:
        return experiment_count > 0 and experiment_count % self.eval_every_n == 0

    def record_result(self, result: BenchmarkResult):
        self._history.append(result)
        self._round += 1

    def get_improvement_curve(self) -> list[dict]:
        """Get the improvement curve over time."""
        curve = []
        for i, r in enumerate(self._history):
            curve.append({
                "round": i,
                "accuracy": r.accuracy,
                "avg_strength": r.avg_strength,
                "timestamp": r.timestamp,
            })
        return curve

    def detect_regression(self) -> bool:
        """Check if recent performance has regressed."""
        if len(self._history) < 3:
            return False
        recent = self._history[-3:]
        accuracies = [r.accuracy for r in recent]
        return accuracies[-1] < min(accuracies[:-1]) * 0.9  # 10% regression

    def build_benchmark_problems(self) -> list[dict]:
        """Build the benchmark problem set."""
        if self._held_out_problems:
            return self._held_out_problems

        # Default benchmark problems
        return [
            {"question": "Prove that sqrt(2) is irrational", "category": "number_theory", "difficulty": "intermediate"},
            {"question": "Prove that there are infinitely many primes", "category": "number_theory", "difficulty": "intermediate"},
            {"question": "Prove that (a+b)^2 = a^2 + 2ab + b^2", "category": "algebra", "difficulty": "elementary"},
            {"question": "Prove the Pythagorean theorem: a^2 + b^2 = c^2 for a right triangle", "category": "geometry", "difficulty": "intermediate"},
            {"question": "Prove that e^(i*pi) + 1 = 0", "category": "analysis", "difficulty": "advanced"},
            {"question": "Prove that the derivative of sin(x) is cos(x)", "category": "calculus", "difficulty": "intermediate"},
            {"question": "Find the sum of the first n natural numbers: 1+2+...+n", "category": "arithmetic", "difficulty": "elementary"},
            {"question": "Prove that the harmonic series diverges", "category": "analysis", "difficulty": "advanced"},
        ]


# ── Program.md Auto-Iteration ─────────────────────────────────────────

class ProgramIterator:
    """Automatically update research program based on what works.

    Like autoresearch's program.md iteration: the human writes the initial
    program, and the system suggests/auto-applies improvements based on
    research results.

    Tracks:
    - Which proof strategies work best
    - Which domains yield the most verified results
    - Optimal explore/exploit ratio
    - Token budget efficiency
    """

    def __init__(self):
        self._strategy_scores: dict[str, list[float]] = defaultdict(list)
        self._domain_scores: dict[str, list[float]] = defaultdict(list)

    def record_strategy_result(self, strategy: str, score: float):
        self._strategy_scores[strategy].append(score)

    def record_domain_result(self, domain: str, score: float):
        self._domain_scores[domain].append(score)

    def get_best_strategies(self, top_n: int = 3) -> list[tuple[str, float]]:
        avg = {s: sum(sc) / len(sc) for s, sc in self._strategy_scores.items() if sc}
        return sorted(avg.items(), key=lambda x: x[1], reverse=True)[:top_n]

    def get_best_domains(self, top_n: int = 3) -> list[tuple[str, float]]:
        avg = {d: sum(sc) / len(sc) for d, sc in self._domain_scores.items() if sc}
        return sorted(avg.items(), key=lambda x: x[1], reverse=True)[:top_n]

    def suggest_program_update(self) -> str:
        """Generate suggested updates to the research program."""
        best_strategies = self.get_best_strategies(3)
        best_domains = self.get_best_domains(3)

        lines = ["# Suggested Program Updates (auto-generated)", ""]
        if best_strategies:
            lines.append("## Best Strategies")
            for s, score in best_strategies:
                lines.append(f"- **{s}**: avg_score={score:.3f}")
        if best_domains:
            lines.append("\n## Most Productive Domains")
            for d, score in best_domains:
                lines.append(f"- **{d}**: avg_score={score:.3f}")
        return "\n".join(lines)


# ── Research Flywheel Bridge ──────────────────────────────────────────

class ResearchFlywheelBridge:
    """Bridges the agent loop to the training data flywheel.

    This is the central orchestrator for closed-loop self-improvement:
    1. Agent runs experiments → Results logged
    2. Results mined for training data (positive + hard examples)
    3. Benchmark evaluates current capability
    4. Curriculum adjusts based on capability frontier
    5. Program strategy updates based on what works
    6. (Optionally) Model retrains on new data
    """

    def __init__(
        self,
        output_dir: str = "flywheel_output",
        eval_every_n: int = 10,
        max_flywheel_entries: int = 1000,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.entries: list[FlywheelEntry] = []
        self.max_entries = max_flywheel_entries

        self.benchmark = AutoBenchmark(eval_every_n=eval_every_n)
        self.frontier = CapabilityFrontier()
        self.iterator = ProgramIterator()

        # Training data accumulation
        self._training_samples: list[dict] = []
        self._hard_examples: list[dict] = []

        # Metrics
        self._total_experiments = 0
        self._total_verified = 0
        self._total_tokens = 0
        self._flywheel_rounds = 0

    def record_experiment(
        self, question: str, hypothesis: str, proof: str,
        verification: dict, strength: float, status: str,
        counterexamples: list = None, category: str = "",
        tokens_cost: int = 0,
    ) -> FlywheelEntry:
        """Record an experiment result into the flywheel.

        Called after each experiment completes.
        """
        import uuid
        import datetime

        outcome = {
            "keep": ExperimentOutcome.SUCCESS,
            "discard": ExperimentOutcome.FAILURE,
            "crash": ExperimentOutcome.CRASH,
        }.get(status, ExperimentOutcome.FAILURE)

        entry = FlywheelEntry(
            id=str(uuid.uuid4())[:12],
            question=question,
            hypothesis=hypothesis,
            proof=proof,
            verification=verification,
            outcome=outcome,
            strength=strength,
            counterexamples=counterexamples or [],
            category=category or self._infer_category(question),
            difficulty=self._infer_difficulty(question),
            timestamp=datetime.datetime.now().isoformat(),
            tokens_cost=tokens_cost,
        )

        self.entries.append(entry)
        self._total_experiments += 1
        self._total_tokens += tokens_cost

        # Update capability frontier
        if outcome == ExperimentOutcome.SUCCESS:
            self.frontier.record_success(entry.category)
            self._total_verified += 1
        elif outcome == ExperimentOutcome.FAILURE:
            self.frontier.record_failure(entry.category)

        # Generate training data
        if outcome == ExperimentOutcome.SUCCESS and strength > 0.5:
            self._training_samples.append(entry.to_training_sample())
        elif outcome == ExperimentOutcome.FAILURE:
            hard = entry.to_hard_example()
            if hard:
                self._hard_examples.append(hard)

        # Track strategy/domain performance
        self.iterator.record_strategy_result(
            self._infer_strategy(proof), strength,
        )
        self.iterator.record_domain_result(entry.category, strength)

        # Prune old entries
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

        # Auto-benchmark
        if self.benchmark.should_evaluate(self._total_experiments):
            self._run_benchmark_check()

        return entry

    def _run_benchmark_check(self):
        """Run a benchmark evaluation checkpoint."""
        # This would normally call the model, but here we use heuristics
        solved = self._total_verified
        total = max(self._total_experiments, 1)
        result = BenchmarkResult(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            total_problems=total,
            solved=solved,
            accuracy=solved / total,
            avg_strength=sum(e.strength for e in self.entries[-50:]) / max(len(self.entries[-50:]), 1),
            by_category=self._compute_category_accuracy(),
            flywheel_round=self._flywheel_rounds,
        )
        self.benchmark.record_result(result)
        self._flywheel_rounds += 1

    def _compute_category_accuracy(self) -> dict:
        """Compute accuracy by category from recent entries."""
        cats = defaultdict(lambda: {"total": 0, "solved": 0})
        for e in self.entries[-100:]:
            cats[e.category]["total"] += 1
            if e.outcome == ExperimentOutcome.SUCCESS:
                cats[e.category]["solved"] += 1
        return {
            cat: data["solved"] / max(data["total"], 1)
            for cat, data in cats.items()
        }

    def get_next_research_direction(self, all_topics: list[str] = None) -> str:
        """Suggest the next research direction based on capability frontier."""
        if all_topics:
            frontier = self.frontier.get_next_topics(all_topics)
            if frontier:
                return f"Explore: {frontier[0]}"

        # Fallback: use best domains from iterator
        best = self.iterator.get_best_domains(1)
        if best:
            return f"Deepen research in: {best[0][0]}"

        return "Explore new mathematical patterns"

    def export_training_data(self) -> dict:
        """Export all accumulated training data.

        Returns dict with 'samples' and 'hard_examples' lists.
        """
        return {
            "samples": self._training_samples,
            "hard_examples": self._hard_examples,
            "total_positive": len(self._training_samples),
            "total_hard": len(self._hard_examples),
        }

    def save_state(self):
        """Persist flywheel state to disk."""
        state = {
            "entries": [
                {
                    "id": e.id, "question": e.question, "hypothesis": e.hypothesis,
                    "proof": e.proof[:500], "outcome": e.outcome.value,
                    "strength": e.strength, "category": e.category,
                    "difficulty": e.difficulty, "timestamp": e.timestamp,
                }
                for e in self.entries[-500:]
            ],
            "total_experiments": self._total_experiments,
            "total_verified": self._total_verified,
            "total_tokens": self._total_tokens,
            "flywheel_rounds": self._flywheel_rounds,
            "capability_frontier": {
                "mastered": list(self.frontier.mastered_topics),
                "struggling": self.frontier.struggling_topics,
                "level": self.frontier.estimate_level(),
            },
        }
        path = self.output_dir / "flywheel_state.json"
        path.write_text(json.dumps(state, indent=2, ensure_ascii=False))
        return path

    def load_state(self):
        """Load flywheel state from disk."""
        path = self.output_dir / "flywheel_state.json"
        if not path.exists():
            return
        try:
            state = json.loads(path.read_text())
            self._total_experiments = state.get("total_experiments", 0)
            self._total_verified = state.get("total_verified", 0)
            self._total_tokens = state.get("total_tokens", 0)
            self._flywheel_rounds = state.get("flywheel_rounds", 0)
            frontier_data = state.get("capability_frontier", {})
            self.frontier.mastered_topics = set(frontier_data.get("mastered", []))
            self.frontier.struggling_topics = frontier_data.get("struggling", {})
        except (json.JSONDecodeError, KeyError):
            pass

    def get_progress_report(self) -> str:
        """Generate a human-readable progress report."""
        lines = [
            "=" * 50,
            "JiuZhang Research Flywheel — Progress Report",
            "=" * 50,
            f"Total experiments: {self._total_experiments}",
            f"Verified proofs:  {self._total_verified}",
            f"Success rate:     {self._total_verified / max(self._total_experiments, 1):.1%}",
            f"Token cost:       {self._total_tokens:,}",
            f"Flywheel rounds:  {self._flywheel_rounds}",
            f"Training samples: {len(self._training_samples)} positive + {len(self._hard_examples)} hard",
            "",
            f"Capability Level: {self.frontier.estimate_level()}",
            f"Mastered topics:  {len(self.frontier.mastered_topics)}",
            f"Struggling:       {len(self.frontier.struggling_topics)}",
        ]

        if self.benchmark._history:
            latest = self.benchmark._history[-1]
            lines.extend([
                "",
                "Latest Benchmark:",
                f"  Accuracy: {latest.accuracy:.1%}",
                f"  Avg strength: {latest.avg_strength:.3f}",
            ])

        if self.benchmark.detect_regression():
            lines.append("\n⚠️  REGRESSION DETECTED — model performance declining!")

        best_strats = self.iterator.get_best_strategies(3)
        if best_strats:
            lines.append("\nBest Strategies:")
            for s, score in best_strats:
                lines.append(f"  - {s}: {score:.3f}")

        return "\n".join(lines)

    @staticmethod
    def _infer_category(question: str) -> str:
        q = question.lower()
        if any(w in q for w in ["prime", "number theory", "整数", "素数"]):
            return "number_theory"
        if any(w in q for w in ["algebra", "group", "ring", "field", "代数"]):
            return "algebra"
        if any(w in q for w in ["geometry", "triangle", "circle", "几何"]):
            return "geometry"
        if any(w in q for w in ["calculus", "derivative", "integral", "微积分", "导数"]):
            return "calculus"
        if any(w in q for w in ["probability", "statistics", "概率", "统计"]):
            return "probability"
        if any(w in q for w in ["topology", "拓扑"]):
            return "topology"
        if any(w in q for w in ["fourier", "傅里叶", "analysis"]):
            return "analysis"
        return "general"

    @staticmethod
    def _infer_difficulty(question: str) -> str:
        q = question.lower()
        frontier_signals = ["riemann", "goldbach", "collatz", "millennium", "p vs np"]
        advanced_signals = ["topology", "manifold", "lie", "cohomology", "scheme", "galois"]
        if any(s in q for s in frontier_signals):
            return "research"
        if any(s in q for s in advanced_signals):
            return "advanced"
        if len(q) > 150:
            return "advanced"
        if len(q) > 80:
            return "intermediate"
        return "elementary"

    @staticmethod
    def _infer_strategy(proof: str) -> str:
        proof_l = proof.lower()
        if "induction" in proof_l or "数学归纳" in proof_l:
            return "induction"
        if "contradiction" in proof_l or "反证" in proof_l or "suppose not" in proof_l:
            return "contradiction"
        if "contrapositive" in proof_l:
            return "contrapositive"
        if "direct" in proof_l or "直接" in proof_l:
            return "direct"
        if "construction" in proof_l or "构造" in proof_l:
            return "construction"
        if "exhaustion" in proof_l or "穷举" in proof_l:
            return "exhaustion"
        return "general"
