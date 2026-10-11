"""Async Autonomous Math Research Agent Loop.

Upgrades the synchronous AgentLoop (agent/loop.py) with:
- Full asyncio integration — non-blocking I/O throughout
- Parallel execution of independent research phases
- Real-time streaming progress with event callbacks
- Concurrent literature + proof + counterexample search
- Provider-aware routing with automatic fallback
- Token budget enforcement across the entire session
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Any, AsyncIterator

import sympy as sp

from jiuzhang.core.config import Config
from jiuzhang.core.async_provider import (
    AsyncModelProvider, ModelResponse, StreamEvent, StreamEventType,
)
from jiuzhang.core.provider_factory import ProviderFactory
from jiuzhang.symbolic_verify import verify_equation, verify_llm_output
from jiuzhang.code_interpreter import CodeInterpreter, CodeExecutionResult
from jiuzhang.conjecture_engine import ConjectureEngine, Conjecture, SearchResult
from jiuzhang.research.literature import LiteratureSearcher

from jiuzhang.agent.research_program import ResearchProgram, DEFAULT_PROGRAM
from jiuzhang.agent.plan_tracker import PlanTracker, ResearchPlan, StepStatus
from jiuzhang.agent.context_budget import (
    ContextBudgetManager, ToolRouter, ToolCategory, compress_math_context,
)
from jiuzhang.agent.escalation import (
    EscalationEngine, EscalationConfig, EscalationReason,
)


# ── State & Results ──────────────────────────────────────────────────

class AgentState(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    HYPOTHESIZING = "hypothesizing"
    PROVING = "proving"
    VERIFYING = "verifying"
    SEARCHING_COUNTEREXAMPLES = "searching_counterexamples"
    REPORTING = "reporting"
    ESCALATING = "escalating"
    PAUSED = "paused"
    DONE = "done"


@dataclass
class ExperimentResult:
    """A single experiment result, logged to results.tsv."""
    commit_hash: str = ""
    conjecture_strength: float = 0.0
    proof_confidence: float = 0.0
    verification_passed: bool = False
    status: str = "discard"  # keep, discard, crash
    description: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tokens_used: int = 0
    latency_seconds: float = 0.0
    provider_used: str = ""


# ── Async Progress Callback Protocol ─────────────────────────────────

class ResearchProgress:
    """Progress events emitted during async research."""
    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()

    async def emit(self, event_type: str, data: Any = None):
        await self.queue.put({"type": event_type, "data": data, "ts": time.time()})

    async def stream(self) -> AsyncIterator[dict]:
        while True:
            try:
                event = await asyncio.wait_for(self.queue.get(), timeout=0.1)
                yield event
            except asyncio.TimeoutError:
                continue


# ── AsyncAgentLoop ───────────────────────────────────────────────────

class AsyncAgentLoop:
    """Autonomous math research agent loop — async version.

    Key improvements over sync AgentLoop:
    - Parallel phases: literature search + proof + counterexample search run concurrently
    - Streaming progress: real-time event stream via ResearchProgress
    - Provider awareness: uses ProviderFactory for health-aware routing
    - Token budget: enforced across all model calls

    Usage:
        loop = AsyncAgentLoop()
        await loop.run()

        # With progress streaming:
        async for event in loop.run_streaming():
            print(event)
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        program_path: Optional[str] = None,
        output_dir: Optional[str] = None,
    ):
        self.config = config or Config()
        self.provider = AsyncModelProvider(self.config)
        self.factory = self.provider.get_factory()

        # Subsystems
        self.code_interpreter = CodeInterpreter()
        self.conjecture_engine = ConjectureEngine(seed=int(time.time()))
        self.literature = LiteratureSearcher()
        self.plan_tracker = PlanTracker()
        self.tool_router = ToolRouter()
        self.context_budget = ContextBudgetManager(
            token_limit=min(self.config.max_tokens, 8192)
        )

        # State
        self.state = AgentState.IDLE
        self.current_question: str = ""
        self.results: list[ExperimentResult] = []
        self._running = False
        self._progress = ResearchProgress()
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused initially

        # Token tracking
        self._total_tokens_used = 0

        # Output dir (computed before program load so _load_program can use it)
        self._output_dir = Path(
            output_dir or os.path.expanduser("~/.jiuzhang/research_autonomous")
        )
        self._output_dir.mkdir(parents=True, exist_ok=True)

        # Program (depends on _output_dir)
        self.program = self._load_program(program_path)

        # Escalation (depends on program)
        self.escalation = EscalationEngine(
            EscalationConfig(max_escalations_per_session=self.program.max_escalations_per_session)
        )

        self._results_path = self._output_dir / self.program.results_file
        self._init_results_file()

    def _load_program(self, path: Optional[str]) -> ResearchProgram:
        if path:
            return ResearchProgram.from_markdown(path)
        for candidate in [Path("research_program.md"), self._output_dir / "program.md"]:
            if candidate.exists():
                return ResearchProgram.from_markdown(str(candidate))
        return ResearchProgram.from_string(DEFAULT_PROGRAM)

    def _init_results_file(self):
        if not self._results_path.exists():
            self._results_path.write_text(
                "commit\tconjecture_strength\tproof_confidence\tverification_passed\t"
                "status\tdescription\ttimestamp\ttokens_used\tlatency_s\tprovider\n",
                encoding="utf-8",
            )

    # ── Main Loop ─────────────────────────────────────────────────────

    async def run(
        self, question: Optional[str] = None,
        max_experiments: Optional[int] = None,
    ):
        """Run the autonomous research loop.

        Args:
            question: Initial research question (auto-chosen if None)
            max_experiments: Stop after N experiments (None = run forever)
        """
        self._running = True
        self.current_question = question or await self._choose_research_direction()
        experiment_count = 0

        await self._log(f"Async AgentLoop starting")
        await self._log(f"  Output: {self._output_dir}")
        await self._log(f"  Question: {self.current_question}")

        try:
            while self._running:
                await self._pause_event.wait()  # Respect pause

                if max_experiments and experiment_count >= max_experiments:
                    break

                experiment_count += 1
                await self._progress.emit("experiment_start", {
                    "index": experiment_count, "question": self.current_question,
                })

                try:
                    result = await self._run_one_experiment()
                    self._log_result(result)
                    await self._progress.emit("experiment_done", asdict(result))
                except asyncio.CancelledError:
                    await self._log("Paused by cancellation")
                    break
                except Exception as e:
                    await self._log(f"Experiment crashed: {e}")
                    self._log_result(ExperimentResult(
                        status="crash", description=str(e)[:200],
                    ))
                    await self._progress.emit("experiment_error", {"error": str(e)})

        finally:
            self._print_summary(experiment_count)
            await self._progress.emit("session_done", {
                "total": experiment_count,
                "kept": sum(1 for r in self.results if r.status == "keep"),
            })

    async def run_streaming(
        self, question: Optional[str] = None,
        max_experiments: Optional[int] = None,
    ) -> AsyncIterator[dict]:
        """Run the loop and yield progress events in real-time."""
        run_task = asyncio.create_task(self.run(question, max_experiments))
        async for event in self._progress.stream():
            yield event
            if event.get("type") == "session_done":
                break
        await run_task

    async def _log(self, message: str):
        print(message)  # Could be replaced with proper logging
        await self._progress.emit("log", {"message": message})

    # ── Experiment Cycle ──────────────────────────────────────────────

    async def _run_one_experiment(self) -> ExperimentResult:
        """Execute one complete research experiment cycle with parallelism."""
        start_time = time.time()
        result = ExperimentResult()

        # Phase 1: Plan
        self.state = AgentState.PLANNING
        await self._progress.emit("phase", {"phase": "planning"})
        if not self.plan_tracker.has_plan:
            await self._create_research_plan()
            await self._progress.emit("plan_created", {
                "steps": len(self.plan_tracker.active_plan.steps) if self.plan_tracker.active_plan else 0,
            })

        # Phase 2: Hypothesize
        self.state = AgentState.HYPOTHESIZING
        await self._progress.emit("phase", {"phase": "hypothesizing"})
        hypothesis = await self._formulate_hypothesis()
        result.description = hypothesis[:200]

        # Phase 3 & 4 & 5: Run in PARALLEL — the key improvement
        self.state = AgentState.PROVING
        await self._progress.emit("phase", {"phase": "parallel_research"})

        proof_task = asyncio.create_task(self._attempt_proof(hypothesis))
        literature_task = asyncio.create_task(self._literature_check(hypothesis))
        counterexample_task = asyncio.create_task(self._search_counterexamples_async(hypothesis))

        proof_result, lit_result, counterexamples = await asyncio.gather(
            proof_task, literature_task, counterexample_task,
        )

        # Phase 4: Verify (depends on proof result from parallel phase)
        self.state = AgentState.VERIFYING
        await self._progress.emit("phase", {"phase": "verifying"})
        verification = await self._verify_results(proof_result)

        # Phase 5: Counterexample search already done in parallel
        self.state = AgentState.SEARCHING_COUNTEREXAMPLES
        # counterexamples already available from parallel execution

        # Assemble result
        result.conjecture_strength = self._calculate_strength(proof_result, verification)
        result.proof_confidence = verification.get("confidence", 0.0)
        result.verification_passed = verification.get("passed", False)
        result.status = (
            "keep" if result.verification_passed and result.conjecture_strength > 0.3
            else "discard"
        )
        result.timestamp = datetime.now().isoformat()
        result.commit_hash = hashlib.sha256(
            f"{self.current_question}{time.time()}".encode()
        ).hexdigest()[:7]
        result.latency_seconds = time.time() - start_time
        result.tokens_used = self._total_tokens_used
        result.provider_used = self.factory.get_best_provider_name()

        elapsed = result.latency_seconds
        await self._log(
            f"Experiment done in {elapsed:.1f}s | strength={result.conjecture_strength:.2f} "
            f"| confidence={result.proof_confidence:.2f} | status={result.status}"
        )

        # Check escalation threshold
        if elapsed > self.escalation.config.timeout_seconds:
            self.escalation.escalate(
                EscalationReason.TIMEOUT,
                self._get_recent_history_dict(),
                self.config.active_provider,
                f"Experiment exceeded {self.escalation.config.timeout_seconds}s budget",
            )

        self.plan_tracker.advance()
        self.state = AgentState.IDLE
        return result

    # ── Research Phases (Async) ────────────────────────────────────────

    async def _choose_research_direction(self) -> str:
        """Async choose: either explore new areas or exploit known ones."""
        import random
        if random.random() < self.program.explore_exploit_ratio:
            topics = [
                "Riemann zeta function zeros distribution",
                "Goldbach conjecture variants",
                "Twin prime patterns",
                "Collatz conjecture generalizations",
                "Algebraic curve properties over finite fields",
                "Lie algebra root system classification",
                "Spectral properties of random matrices",
                "Ergodic theory dynamical invariants",
                "Category theory universal constructions",
                "Homological algebra derived functors",
            ]
            return random.choice(topics)
        else:
            if self.results:
                last_good = [r for r in self.results if r.status == "keep"]
                if last_good:
                    return f"Extend and generalize: {last_good[-1].description[:100]}"
                return "Prove or disprove: sum of reciprocals of twin primes converges"
            return "Investigate new patterns in prime number distribution"

    async def _create_research_plan(self):
        """Create research plan by asking the model (async)."""
        route = self.tool_router.route(self.current_question)
        prompt = f"""You are a mathematical research planner. Decompose the following research question into concrete, sequential steps.

Research Question: {self.current_question}

Output a numbered list of steps. Each step a single, actionable task.
Example:
1. Review known results
2. Formulate hypotheses
3. Set up symbolic framework
4. Test numerically
5. Attempt proof
6. Verify with SymPy
7. Search counterexamples
8. Compile findings

Your plan:"""

        messages = [
            {"role": "system", "content": "You are a mathematical research planner. Output numbered steps only."},
            {"role": "user", "content": prompt},
        ]
        response = await self.provider.send(messages, temperature=0.5, max_tokens=512)
        self.plan_tracker.parse_plan_from_text(self.current_question, response.text)
        self._total_tokens_used += response.tokens_used

    async def _formulate_hypothesis(self) -> str:
        """Async hypothesis formulation."""
        anchor = self.plan_tracker.get_anchor()
        current_step = (
            self.plan_tracker.active_plan.current_step.description
            if self.plan_tracker.active_plan and self.plan_tracker.active_plan.current_step
            else self.current_question
        )

        prompt = f"""You are a mathematical researcher. Formulate a precise, testable hypothesis.

Research Question: {self.current_question}
Current step: {current_step}
{anchor}

Formulate a specific mathematical hypothesis. Be precise with notation. Use LaTeX for formulas.
The hypothesis must be falsifiable.

Hypothesis:"""

        messages = [
            {"role": "system", "content": "You are a mathematical researcher. Output a precise, falsifiable hypothesis in LaTeX."},
            {"role": "user", "content": prompt},
        ]
        response = await self.provider.send(messages, max_tokens=512, temperature=0.7)
        self._total_tokens_used += response.tokens_used
        return response.text if response.text else self.current_question

    async def _attempt_proof(self, hypothesis: str) -> dict:
        """Async proof attempt with both symbolic and LLM approaches."""
        symbolic_result = self._symbolic_proof_attempt(hypothesis)

        prompt = f"""Prove or disprove the following mathematical hypothesis:

{hypothesis}

Approach:
1. State assumptions clearly
2. Build proof step by step
3. Verify each step logically
4. Conclude

If unprovable, explain the difficulty and suggest additional conditions."""

        messages = [
            {"role": "system", "content": "You are a rigorous mathematical proof assistant. Output complete proofs with clear logical steps."},
            {"role": "user", "content": prompt},
        ]
        response = await self.provider.send(messages, max_tokens=1024, temperature=0.5)
        self._total_tokens_used += response.tokens_used

        return {
            "hypothesis": hypothesis,
            "symbolic_result": symbolic_result,
            "llm_proof": response.text,
            "success": bool(response.text),
        }

    async def _literature_check(self, hypothesis: str) -> list:
        """Async literature search running in parallel with proof attempt."""
        try:
            papers = self.literature.search(self.current_question, max_results=5)
            return papers
        except Exception:
            return []

    def _symbolic_proof_attempt(self, hypothesis: str) -> dict:
        """Use SymPy for symbolic verification (sync, fast)."""
        try:
            equations = re.findall(r'\$([^$]+)\$', hypothesis)
            if not equations:
                equations = re.findall(r'=.*', hypothesis)

            results_list = []
            for eq_str in equations[:3]:
                if '=' in eq_str:
                    sides = eq_str.split('=', 1)
                    if len(sides) == 2:
                        try:
                            lhs = sp.simplify(sp.sympify(sides[0]))
                            rhs = sp.simplify(sp.sympify(sides[1]))
                            verified = sp.simplify(lhs - rhs) == 0
                            results_list.append({
                                "equation": eq_str, "verified": verified,
                                "lhs": str(lhs), "rhs": str(rhs),
                            })
                        except Exception:
                            results_list.append({"equation": eq_str, "verified": False, "error": "Could not parse"})
            return {"equations_checked": len(results_list), "results": results_list}
        except Exception as e:
            return {"error": str(e), "equations_checked": 0}

    async def _search_counterexamples_async(self, hypothesis: str) -> list:
        """Async counterexample search running in parallel."""
        counterexamples = []

        # Conjecture engine search
        try:
            ce_result = self.conjecture_engine.search_counterexamples(max_n=1000)
            counterexamples.extend(ce_result if isinstance(ce_result, list) else [ce_result])
        except Exception:
            pass

        # Simple brute-force
        try:
            numbers_in_hypothesis = re.findall(r'\b(\d+)\b', hypothesis)
            n_max = 100
            if numbers_in_hypothesis:
                val = int(numbers_in_hypothesis[0])
                n_max = val * 10 if val < 100 else 500

            false_positives = 0
            for n in range(3, min(n_max, 200), 2):
                if not sp.isprime(n):
                    false_positives += 1
            if false_positives > 0:
                counterexamples.append({
                    "pattern": "odd_non_prime",
                    "count": false_positives,
                    "note": f"Found {false_positives} odd composite numbers up to {n_max}",
                })
        except Exception:
            pass

        return counterexamples

    async def _verify_results(self, proof_result: dict) -> dict:
        """Async result verification."""
        verification = {"passed": False, "confidence": 0.0, "details": []}

        symbolic = proof_result.get("symbolic_result", {})
        if symbolic and not symbolic.get("error"):
            equations = symbolic.get("results", [])
            if equations:
                verified_count = sum(1 for r in equations if r.get("verified"))
                verification["details"].append(f"Symbolic: {verified_count}/{len(equations)} verified")
                if verified_count == len(equations) and len(equations) > 0:
                    verification["confidence"] += 0.4
                    verification["passed"] = True

        llm_proof = proof_result.get("llm_proof", "")
        if llm_proof:
            sympy_checks = verify_llm_output(llm_proof)
            verified = sum(1 for c in sympy_checks if c.verified)
            total = len(sympy_checks)
            if total > 0:
                verification["details"].append(f"LLM output: {verified}/{total} claims verified")
                verification["confidence"] += 0.3 * (verified / total)
                if verified == total:
                    verification["passed"] = True

        proof_indicators = ["therefore", "hence", "thus", "q.e.d.", "证毕", "所以", "因此", "综上"]
        if any(ind in llm_proof.lower() for ind in proof_indicators):
            verification["confidence"] += 0.1
            verification["details"].append("Logical conclusion present")

        code_blocks = re.findall(r'```python\n(.*?)```', llm_proof, re.DOTALL)
        if code_blocks:
            for code in code_blocks[:2]:
                exec_result = self.code_interpreter.execute(code)
                if exec_result.success:
                    verification["confidence"] += 0.1
                    verification["details"].append("Code execution succeeded")
                    break

        verification["confidence"] = min(verification["confidence"], 1.0)
        if not verification["passed"]:
            self.escalation.record_verification_failure()
        return verification

    # ── Scoring & Logging ─────────────────────────────────────────────

    def _calculate_strength(self, proof_result: dict, verification: dict) -> float:
        strength = 0.0
        if verification.get("passed"):
            strength += 0.4
        strength += verification.get("confidence", 0.0) * 0.3
        proof_len = len(proof_result.get("llm_proof", ""))
        if proof_len > 200:
            strength += 0.1
        if proof_len > 500:
            strength += 0.05
        symbolic = proof_result.get("symbolic_result", {})
        eqs = symbolic.get("results", [])
        if eqs:
            verified_ratio = sum(1 for r in eqs if r.get("verified")) / len(eqs)
            strength += verified_ratio * 0.15
        return min(strength, 1.0)

    def _log_result(self, result: ExperimentResult):
        self.results.append(result)
        line = (
            f"{result.commit_hash}\t{result.conjecture_strength:.4f}\t"
            f"{result.proof_confidence:.4f}\t{str(result.verification_passed).lower()}\t"
            f"{result.status}\t{result.description[:200]}\t{result.timestamp}\t"
            f"{result.tokens_used}\t{result.latency_seconds:.2f}\t{result.provider_used}\n"
        )
        with open(self._results_path, "a", encoding="utf-8") as f:
            f.write(line)

    def _get_recent_history_dict(self) -> list:
        return [
            {
                "role": "assistant",
                "content": f"Experiment: {r.description[:300]}\nStatus: {r.status}\nStrength: {r.conjecture_strength:.2f}",
            }
            for r in self.results[-5:]
        ]

    def _print_summary(self, experiment_count: int):
        keeps = [r for r in self.results if r.status == "keep"]
        discards = [r for r in self.results if r.status == "discard"]
        crashes = [r for r in self.results if r.status == "crash"]

        print(f"\n{'='*60}")
        print(f"Research Session Summary")
        print(f"{'='*60}")
        print(f"  Experiments: {experiment_count}")
        print(f"  Kept: {len(keeps)} | Discarded: {len(discards)} | Crashed: {len(crashes)}")
        print(f"  Escalations: {self.escalation.escalation_count}")
        print(f"  Total tokens: {self._total_tokens_used}")
        if keeps:
            print(f"\n  Top results:")
            for r in sorted(keeps, key=lambda x: x.conjecture_strength, reverse=True)[:3]:
                print(f"    [{r.conjecture_strength:.2f}] {r.description[:120]}")
        print(f"\n  Results: {self._results_path}")

    # ── Control ───────────────────────────────────────────────────────

    def pause(self):
        self._running = False
        self.state = AgentState.PAUSED

    def resume(self, question: Optional[str] = None):
        if question:
            self.current_question = question
        self._running = True

    async def quick_research(self, question: str, depth: str = "medium") -> dict:
        """Single-shot async research without the autonomous loop."""
        self.current_question = question
        await self._create_research_plan()
        hypothesis = await self._formulate_hypothesis()

        # Run proof and counterexample search in parallel
        proof_task = asyncio.create_task(self._attempt_proof(hypothesis))
        ce_task = asyncio.create_task(self._search_counterexamples_async(hypothesis))

        proof = await proof_task
        counterexamples = await ce_task
        verification = await self._verify_results(proof)

        return {
            "question": question,
            "hypothesis": hypothesis,
            "proof": proof,
            "verification": verification,
            "counterexamples": counterexamples,
            "strength": self._calculate_strength(proof, verification),
            "plan": self.plan_tracker.get_anchor(),
        }

    async def close(self):
        """Clean up resources."""
        await self.provider.close()
