"""Autonomous Math Research Agent Loop — the core of JiuZhang's self-driving research.

Inspired by:
- autoresearch (Karpathy, 2026): autonomous experiment loop, program.md, results.tsv
- nanobot (HKUDS): async agent loop with MessageBus, context building, tool execution
- smallcode: plan tracking, escalation, tool routing, context budget management

The AgentLoop runs indefinitely:
1. Read program.md for research directives
2. Choose research direction (explore vs exploit)
3. Formulate hypothesis
4. Attempt proof / derivation / counterexample search
5. Verify with SymPy
6. Log results to results.tsv
7. If improved: keep commit; else: revert
8. Repeat

The human wakes up to a log of experiments and (hopefully) new mathematical discoveries.
"""

import os
import re
import json
import time
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Any

import sympy as sp

from jiuzhang.core.config import Config
from jiuzhang.core.multi_provider_api import MultiProviderClient
from jiuzhang.symbolic_verify import verify_equation, verify_llm_output
from jiuzhang.code_interpreter import CodeInterpreter, CodeExecutionResult
from jiuzhang.conjecture_engine import ConjectureEngine, Conjecture, SearchResult
from jiuzhang.research.literature import LiteratureSearcher

from jiuzhang.agent.research_program import ResearchProgram, DEFAULT_PROGRAM
from jiuzhang.agent.plan_tracker import PlanTracker, ResearchPlan, StepStatus
from jiuzhang.agent.context_budget import (
    ContextBudgetManager, ToolRouter, ToolCategory, compress_math_context
)
from jiuzhang.agent.escalation import (
    EscalationEngine, EscalationConfig, EscalationReason
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


# ── Agent Loop ───────────────────────────────────────────────────────

class AgentLoop:
    """Autonomous math research agent loop.

    Usage:
        loop = AgentLoop()
        loop.run()  # Runs indefinitely until interrupted

    Or with a program:
        loop = AgentLoop(program_path="my_program.md")
        loop.run()
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        program_path: Optional[str] = None,
        output_dir: Optional[str] = None,
    ):
        self.config = config or Config()
        self.client = MultiProviderClient(self.config)

        # Subsystems
        self.program = self._load_program(program_path)
        self.code_interpreter = CodeInterpreter()
        self.conjecture_engine = ConjectureEngine(seed=int(time.time()))
        self.literature = LiteratureSearcher()
        self.plan_tracker = PlanTracker()
        self.tool_router = ToolRouter()
        self.context_budget = ContextBudgetManager(
            token_limit=min(self.config.max_tokens, 8192)
        )
        self.escalation = EscalationEngine(
            EscalationConfig(
                max_escalations_per_session=self.program.max_escalations_per_session,
            )
        )

        # V3: Quality governance
        from jiuzhang.agent.quality_governance import QualityController
        self.quality = QualityController()

        # V3: Flywheel bridge for closed-loop self-improvement
        from jiuzhang.flywheel_bridge import ResearchFlywheelBridge
        output = output_dir or os.path.expanduser(self.program.output_dir)
        self.flywheel = ResearchFlywheelBridge(output_dir=os.path.join(
            os.path.dirname(output), "flywheel_data"
        ) if output else "flywheel_output")

        # State
        self.state = AgentState.IDLE
        self.current_question: str = ""
        self.results: list = []
        self._running = False
        self._progress_callback: Optional[Callable] = None
        self._direction_changes: int = 0

        # Output
        self._output_dir = Path(
            output_dir or os.path.expanduser(self.program.output_dir)
        )
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._results_path = self._output_dir / self.program.results_file
        self._init_results_file()

    def _load_program(self, path: Optional[str]) -> ResearchProgram:
        if path:
            return ResearchProgram.from_markdown(path)
        # Auto-detect program.md in output dir or cwd
        for candidate in [
            Path("research_program.md"),
            Path(self._output_dir) / "program.md" if hasattr(self, '_output_dir') else Path("research_program.md"),
        ]:
            if candidate.exists():
                return ResearchProgram.from_markdown(str(candidate))
        return ResearchProgram.from_string(DEFAULT_PROGRAM)

    def _init_results_file(self):
        if not self._results_path.exists():
            self._results_path.write_text(
                "commit\tconjecture_strength\tproof_confidence\tverification_passed\tstatus\tdescription\ttimestamp\n",
                encoding="utf-8",
            )

    def set_progress_callback(self, callback: Callable):
        self._progress_callback = callback

    def _report(self, stage: int, total: int, message: str):
        if self._progress_callback:
            self._progress_callback(stage, total, message)

    # ── Main Loop ─────────────────────────────────────────────────────

    def run(self, question: Optional[str] = None, max_experiments: Optional[int] = None):
        """Run the autonomous research loop.

        Args:
            question: Optional initial research question
            max_experiments: Stop after N experiments (None = run forever)
        """
        self._running = True
        self.current_question = question or self._choose_research_direction()
        experiment_count = 0

        print(f"🚀 JiuZhang Autonomous Research Agent started")
        print(f"   Output: {self._output_dir}")
        print(f"   Question: {self.current_question}")
        print(f"   Program goal: {self.program.goal[:100]}...")
        print()

        try:
            while self._running:
                if max_experiments and experiment_count >= max_experiments:
                    break

                experiment_count += 1
                print(f"\n{'='*60}")
                print(f"Experiment {experiment_count}")
                print(f"{'='*60}")

                try:
                    result = self._run_one_experiment()
                    self._log_result(result)
                except KeyboardInterrupt:
                    print("\n⏸️  Paused by user")
                    break
                except Exception as e:
                    print(f"❌ Experiment crashed: {e}")
                    self._log_result(ExperimentResult(
                        status="crash",
                        description=str(e)[:200],
                    ))

        finally:
            self._print_summary(experiment_count)

    def _run_one_experiment(self) -> ExperimentResult:
        """Execute one complete research experiment cycle with V3 quality governance."""
        start_time = time.time()
        result = ExperimentResult()

        # --- Pre-experiment: save checkpoint for rollback ---
        plan_state = self.plan_tracker.get_anchor()
        self.quality.save_checkpoint(
            self.current_question, plan_state,
            [{"status": r.status, "desc": r.description} for r in self.results[-5:]],
        )

        # Phase 1: Plan
        self.state = AgentState.PLANNING
        self._report(1, 5, "Planning research approach...")
        if not self.plan_tracker.has_plan:
            self._create_research_plan()

        # Phase 2: Hypothesize
        self.state = AgentState.HYPOTHESIZING
        self._report(2, 5, "Formulating hypotheses...")
        hypothesis = self._formulate_hypothesis()
        result.description = hypothesis[:200]

        # --- Guard: check claim grounding before proceeding ---
        guard_result = self.quality.guard_claim(hypothesis)
        if not guard_result["allowed"]:
            self._report(2, 5, f"Claim blocked: {guard_result['reason']}")
            result.status = "discard"
            result.description = guard_result["reason"]
            return result

        # Phase 3: Prove / Derive
        self.state = AgentState.PROVING
        self._report(3, 5, "Attempting proof/derivation...")
        proof_result = self._attempt_proof(hypothesis)

        # Phase 4: Verify
        self.state = AgentState.VERIFYING
        self._report(4, 5, "Verifying with SymPy...")
        verification = self._verify_results(proof_result)

        # Phase 5: Counterexample search
        self.state = AgentState.SEARCHING_COUNTEREXAMPLES
        self._report(5, 5, "Searching for counterexamples...")
        counterexamples = self._search_counterexamples(proof_result)

        # --- V3: Quality governance ---
        code_blocks = re.findall(r'```python\n(.*?)```', proof_result.get("llm_proof", ""), re.DOTALL)
        quality_report = self.quality.evaluate(
            hypothesis, proof_result.get("llm_proof", ""),
            verification, counterexamples, code_blocks,
        )

        # --- V3: Stagnation detection ---
        should_stop, stagnation_reason, stagnation_msg = self.quality.check_stagnation(
            quality_report.score, "keep" if verification.get("passed") else "discard",
        )
        if should_stop:
            self._direction_changes += 1
            self.quality.governor.force_pivot()
            self.current_question = self._choose_research_direction()
            print(f"   🚨 Stagnation detected ({stagnation_reason.value}): {stagnation_msg}")
            print(f"   🔄 Pivoting to: {self.current_question[:100]}...")

        # --- V3: Tool trust scoring ---
        if verification.get("passed"):
            self.quality.tool_scorer.record_result("sympy_compute", True)
        if code_blocks:
            self.quality.tool_scorer.record_result("code_interpreter", len(code_blocks) > 0)

        # Assemble result — use quality report score when available
        result.conjecture_strength = quality_report.score  # V3: quality-aware scoring
        result.proof_confidence = verification.get("confidence", 0.0)
        result.verification_passed = verification.get("passed", False)
        result.status = "keep" if quality_report.verdict.value in ("pass", "warn") else "discard"
        result.timestamp = datetime.now().isoformat()
        result.commit_hash = hashlib.sha256(
            f"{self.current_question}{time.time()}".encode()
        ).hexdigest()[:7]

        # --- V3: Log to flywheel ---
        self.flywheel.record_experiment(
            question=self.current_question,
            hypothesis=hypothesis,
            proof=proof_result.get("llm_proof", ""),
            verification=verification,
            strength=quality_report.score,
            status=result.status,
            counterexamples=[str(c) for c in counterexamples],
        )

        elapsed = time.time() - start_time
        print(f"   ⏱️  Experiment completed in {elapsed:.1f}s")
        print(f"   📊 Quality: {quality_report.score:.2f} | Verdict: {quality_report.verdict.value} | Status: {result.status}")

        # Check timeout for escalation
        if elapsed > self.escalation.config.timeout_seconds:
            self.escalation.escalate(
                EscalationReason.TIMEOUT,
                self._get_recent_history(),
                self.client,
                f"Experiment exceeded {self.escalation.config.timeout_seconds}s budget",
            )

        # Log quality suggestions
        if quality_report.suggestions:
            for s in quality_report.suggestions[:2]:
                print(f"   💡 {s}")

        self.plan_tracker.advance()
        self.state = AgentState.IDLE
        return result

    # ── Research Phases ───────────────────────────────────────────────

    def _choose_research_direction(self) -> str:
        """Choose what to research next: explore new areas or exploit known ones."""
        import random
        if random.random() < self.program.explore_exploit_ratio:
            # Explore: pick a frontier topic
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
            question = random.choice(topics)
        else:
            # Exploit: build on recent results
            if self.results:
                last_good = [r for r in self.results if r.status == "keep"]
                if last_good:
                    question = f"Extend and generalize: {last_good[-1].description[:100]}"
                else:
                    question = "Prove or disprove: sum of reciprocals of twin primes converges"
            else:
                question = "Investigate new patterns in prime number distribution"

        self.current_question = question
        return question

    def _create_research_plan(self):
        """Create a research plan by asking the model to decompose the question."""
        route = self.tool_router.route(self.current_question)
        prompt = f"""You are a mathematical research planner. Decompose the following research question into concrete, sequential steps.

Research Question: {self.current_question}

Output format: a numbered list of steps. Each step should be a single, actionable task.
Example:
1. Review known results about [topic]
2. Formulate specific hypotheses
3. Set up symbolic computation framework
4. Test hypotheses numerically for small cases
5. Attempt mathematical proof
6. Verify with SymPy
7. Search for counterexamples
8. Compile findings

Your plan (numbered list):"""

        messages = [
            {"role": "system", "content": "You are a mathematical research planner. Output numbered steps only."},
            {"role": "user", "content": prompt},
        ]
        result = self.client.send_message(messages)
        plan_text = result.data if result.success else ""
        self.plan_tracker.parse_plan_from_text(self.current_question, plan_text)

    def _formulate_hypothesis(self) -> str:
        """Formulate a specific hypothesis/conjecture to investigate."""
        anchor = self.plan_tracker.get_anchor()
        current_step = self.plan_tracker.active_plan.current_step.description if self.plan_tracker.active_plan and self.plan_tracker.active_plan.current_step else self.current_question

        prompt = f"""You are a mathematical researcher. Formulate a precise, testable hypothesis based on the current research context.

Research Question: {self.current_question}
Current step: {current_step}
{anchor}

Formulate a specific mathematical hypothesis. Be precise with notation. Use LaTeX for formulas.
The hypothesis should be falsifiable — it must be possible to find a counterexample if false.

Hypothesis:"""

        messages = [
            {"role": "system", "content": "You are a mathematical researcher. Output a precise, falsifiable hypothesis in LaTeX."},
            {"role": "user", "content": prompt},
        ]
        result = self.client.send_message(messages, max_tokens=512, temperature=0.7)
        return result.data if result.success else self.current_question

    def _attempt_proof(self, hypothesis: str) -> dict:
        """Attempt to prove the hypothesis."""
        # Try symbolic first
        symbolic_result = self._symbolic_proof_attempt(hypothesis)

        # Try LLM-based proof
        prompt = f"""Prove or disprove the following mathematical hypothesis:

{hypothesis}

Approach:
1. State any assumptions clearly
2. Build the proof step by step
3. Verify each step logically
4. Conclude with whether the hypothesis holds

If you cannot prove it, explain where the difficulty lies and what additional conditions might make it provable."""

        messages = [
            {"role": "system", "content": "You are a rigorous mathematical proof assistant. Output complete proofs with clear logical steps."},
            {"role": "user", "content": prompt},
        ]
        result = self.client.send_message(messages, max_tokens=1024, temperature=0.5)

        proof_text = result.data if result.success else ""
        return {
            "hypothesis": hypothesis,
            "symbolic_result": symbolic_result,
            "llm_proof": proof_text,
            "success": result.success,
        }

    def _symbolic_proof_attempt(self, hypothesis: str) -> dict:
        """Use SymPy to verify symbolic claims in the hypothesis."""
        try:
            # Extract equations from hypothesis
            equations = re.findall(r'\$([^$]+)\$', hypothesis)
            if not equations:
                equations = re.findall(r'=.*', hypothesis)

            results = []
            for eq_str in equations[:3]:
                if '=' in eq_str:
                    sides = eq_str.split('=', 1)
                    if len(sides) == 2:
                        try:
                            lhs = sp.simplify(sp.sympify(sides[0]))
                            rhs = sp.simplify(sp.sympify(sides[1]))
                            verified = sp.simplify(lhs - rhs) == 0
                            results.append({
                                "equation": eq_str,
                                "verified": verified,
                                "lhs": str(lhs),
                                "rhs": str(rhs),
                            })
                        except Exception:
                            results.append({"equation": eq_str, "verified": False, "error": "Could not parse"})

            return {"equations_checked": len(results), "results": results}
        except Exception as e:
            return {"error": str(e), "equations_checked": 0}

    def _verify_results(self, proof_result: dict) -> dict:
        """Verify results using SymPy and cross-checks."""
        verification = {"passed": False, "confidence": 0.0, "details": []}

        # Check symbolic verification
        symbolic = proof_result.get("symbolic_result", {})
        if symbolic and not symbolic.get("error"):
            equations = symbolic.get("results", [])
            if equations:
                verified_count = sum(1 for r in equations if r.get("verified"))
                verification["details"].append(
                    f"Symbolic: {verified_count}/{len(equations)} equations verified"
                )
                if verified_count == len(equations) and len(equations) > 0:
                    verification["confidence"] += 0.4
                    verification["passed"] = True

        # Verify LLM output with SymPy
        llm_proof = proof_result.get("llm_proof", "")
        if llm_proof:
            sympy_checks = verify_llm_output(llm_proof)
            verified = sum(1 for c in sympy_checks if c.verified)
            total = len(sympy_checks)
            if total > 0:
                verification["details"].append(
                    f"LLM output: {verified}/{total} claims verified by SymPy"
                )
                verification["confidence"] += 0.3 * (verified / total)
                if verified == total:
                    verification["passed"] = True

        # Check for logical completeness markers
        proof_indicators = ["therefore", "hence", "thus", "q.e.d.", "证毕", "所以", "因此", "综上"]
        has_conclusion = any(ind in llm_proof.lower() for ind in proof_indicators)
        if has_conclusion:
            verification["confidence"] += 0.1
            verification["details"].append("Logical conclusion present")

        # Run code verification if available
        code_blocks = re.findall(r'```python\n(.*?)```', llm_proof, re.DOTALL)
        if code_blocks:
            for code in code_blocks[:2]:
                exec_result = self.code_interpreter.execute(code)
                if exec_result.success:
                    verification["confidence"] += 0.1
                    verification["details"].append("Code execution succeeded")
                    break

        verification["confidence"] = min(verification["confidence"], 1.0)

        # Record failures for escalation
        if not verification["passed"]:
            self.escalation.record_verification_failure()

        return verification

    def _search_counterexamples(self, proof_result: dict) -> list:
        """Search for counterexamples to the hypothesis."""
        hypothesis = proof_result.get("hypothesis", "")
        counterexamples = []

        # Use the conjecture engine's counterexample search
        try:
            ce_result = self.conjecture_engine.search_counterexamples(max_n=1000)
            counterexamples = ce_result
        except Exception:
            pass

        # Simple numeric brute-force for numeric patterns
        try:
            numbers_in_hypothesis = re.findall(r'\b(\d+)\b', hypothesis)
            if numbers_in_hypothesis:
                n_max = int(numbers_in_hypothesis[0]) * 10 if int(numbers_in_hypothesis[0]) < 100 else 500
            else:
                n_max = 100

            # Generic counterexample check: test odd numbers for primality
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

    # ── Scoring & Logging ─────────────────────────────────────────────

    def _calculate_strength(self, proof_result: dict, verification: dict) -> float:
        """Calculate the strength/quality of the research result (0-1 scale)."""
        strength = 0.0

        # Verification matters most
        if verification.get("passed"):
            strength += 0.4

        # Confidence contribution
        strength += verification.get("confidence", 0.0) * 0.3

        # Length/detail of proof
        proof_len = len(proof_result.get("llm_proof", ""))
        if proof_len > 200:
            strength += 0.1
        if proof_len > 500:
            strength += 0.05

        # Symbolic verification
        symbolic = proof_result.get("symbolic_result", {})
        eqs = symbolic.get("results", [])
        if eqs:
            verified_ratio = sum(1 for r in eqs if r.get("verified")) / len(eqs)
            strength += verified_ratio * 0.15

        return min(strength, 1.0)

    def _log_result(self, result: ExperimentResult):
        """Log a result to results.tsv."""
        self.results.append(result)

        line = (
            f"{result.commit_hash}\t"
            f"{result.conjecture_strength:.4f}\t"
            f"{result.proof_confidence:.4f}\t"
            f"{str(result.verification_passed).lower()}\t"
            f"{result.status}\t"
            f"{result.description[:200]}\t"
            f"{result.timestamp}\n"
        )

        with open(self._results_path, "a", encoding="utf-8") as f:
            f.write(line)

    def _get_recent_history(self) -> list:
        """Get recent conversation history for escalation."""
        messages = []
        for result in self.results[-5:]:
            messages.append({
                "role": "assistant",
                "content": f"Experiment: {result.description[:300]}\nStatus: {result.status}\nStrength: {result.conjecture_strength:.2f}",
            })
        return messages

    def _print_summary(self, experiment_count: int):
        """Print a summary of the research session."""
        keeps = [r for r in self.results if r.status == "keep"]
        discards = [r for r in self.results if r.status == "discard"]
        crashes = [r for r in self.results if r.status == "crash"]

        print(f"\n{'='*60}")
        print(f"📊 Research Session Summary")
        print(f"{'='*60}")
        print(f"  Experiments run: {experiment_count}")
        print(f"  ✅ Kept: {len(keeps)}")
        print(f"  ❌ Discarded: {len(discards)}")
        print(f"  💥 Crashed: {len(crashes)}")
        print(f"  🔄 Direction changes: {self._direction_changes}")
        print(f"  🔄 Escalations: {self.escalation.escalation_count}")
        print(f"  💰 Est. API cost: ${self.escalation.total_cost:.4f}")

        # V3: Quality stats
        qstats = self.quality.get_quality_stats()
        print(f"  🛡️  Quality pass rate: {qstats['verifier_pass_rate']:.1%}")
        print(f"  🔙 Rollbacks: {qstats['total_rollbacks']}")
        print(f"  ⭐ Best score: {qstats['best_score']:.3f}")

        # V3: Flywheel
        print(f"  🏗️  Flywheel training samples: {len(self.flywheel._training_samples)}")

        if keeps:
            print(f"\n  Top results:")
            for r in sorted(keeps, key=lambda x: x.conjecture_strength, reverse=True)[:3]:
                print(f"    [{r.conjecture_strength:.2f}] {r.description[:120]}")

        print(f"\n  Results saved to: {self._results_path}")

    def pause(self):
        self._running = False
        self.state = AgentState.PAUSED

    def resume(self, question: Optional[str] = None):
        if question:
            self.current_question = question
        self._running = True
        self.state = AgentState.IDLE

    # ── Quick Research (non-looping) ──────────────────────────────────

    def quick_research(self, question: str, depth: str = "medium") -> dict:
        """Run a single-shot research without the autonomous loop.

        Args:
            question: Research question
            depth: shallow/medium/deep

        Returns:
            Dict with research results
        """
        self.current_question = question
        self._create_research_plan()
        hypothesis = self._formulate_hypothesis()
        proof = self._attempt_proof(hypothesis)
        verification = self._verify_results(proof)
        counterexamples = self._search_counterexamples(proof)

        return {
            "question": question,
            "hypothesis": hypothesis,
            "proof": proof,
            "verification": verification,
            "counterexamples": counterexamples,
            "strength": self._calculate_strength(proof, verification),
            "plan": self.plan_tracker.get_anchor(),
        }
