"""Quality Governance System — smallcode-grade reliability for math research.

Inspired by smallcode's quality monitor, early-stop governor, and tool scorer:
- **Quality Verifier**: Multi-pass validation of research results before acceptance
- **Early-Stop Governor**: Detect stagnation and force direction changes
- **Tool Scorer**: Track tool reliability and decay trust in unreliable tools
- **Auto-Rollback**: Revert bad conjectures/proofs to checkpoint state
- **Read-Before-Write Guard**: Ensure mathematical claims are grounded in known results
- **Injection Handler**: Process human corrections mid-research without breaking the loop
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any
import time
import math
from collections import defaultdict


# ── Quality Verdict ──────────────────────────────────────────────────

class QualityVerdict(Enum):
    PASS = "pass"               # Result passes all checks
    WARN = "warn"               # Minor issues, still accepted
    FAIL = "fail"               # Result rejected
    NEEDS_REVIEW = "needs_review"  # Requires human/expert review
    STALE = "stale"             # Too similar to prior results


@dataclass
class QualityReport:
    verdict: QualityVerdict
    score: float         # 0.0-1.0
    checks: list[dict]   # Individual check results
    suggestions: list[str]
    timestamp: float = field(default_factory=time.time)


# ── Quality Verifier ─────────────────────────────────────────────────

class QualityVerifier:
    """Multi-pass validation of research results.

    Checks:
    1. Soundness: Are the proof steps logically connected?
    2. Novelty: Is this result genuinely new (not duplicate)?
    3. Falsifiability: Can the claim be tested/falsified?
    4. Completeness: Is the proof complete (no missing steps)?
    5. Grounding: Does it cite known results properly?
    6. Code safety: Are generated code snippets safe to execute?
    """

    # Weights for different quality dimensions
    WEIGHTS = {
        "soundness": 0.30,
        "novelty": 0.20,
        "falsifiability": 0.15,
        "completeness": 0.15,
        "grounding": 0.10,
        "code_safety": 0.10,
    }

    def __init__(self, novelty_window: int = 20):
        self._recent_results: list[str] = []  # For novelty checking
        self._novelty_window = novelty_window
        self._total_checks = 0
        self._passed_checks = 0

    def verify(
        self, hypothesis: str, proof: str, verification: dict,
        counterexamples: list, code_blocks: list[str] = None,
    ) -> QualityReport:
        """Run full quality verification on a research result.

        Returns QualityReport with verdict, score, and detailed checks.
        """
        checks = []
        suggestions = []
        code_blocks = code_blocks or []

        # 1. Soundness check
        soundness = self._check_soundness(proof)
        checks.append({"name": "soundness", "passed": soundness["passed"], "score": soundness["score"], "detail": soundness.get("detail", "")})
        if not soundness["passed"]:
            suggestions.append("Proof lacks logical structure — add explicit step numbering and justification")

        # 2. Novelty check
        novelty = self._check_novelty(hypothesis)
        checks.append({"name": "novelty", "passed": novelty["passed"], "score": novelty["score"], "detail": novelty.get("detail", "")})
        if not novelty["passed"]:
            suggestions.append("Result is too similar to a recent experiment — try a different direction")

        # 3. Falsifiability check
        falsifiability = self._check_falsifiability(hypothesis, counterexamples)
        checks.append({"name": "falsifiability", "passed": falsifiability["passed"], "score": falsifiability["score"], "detail": falsifiability.get("detail", "")})

        # 4. Completeness check
        completeness = self._check_completeness(proof)
        checks.append({"name": "completeness", "passed": completeness["passed"], "score": completeness["score"], "detail": completeness.get("detail", "")})
        if not completeness["passed"]:
            suggestions.append("Proof may be incomplete — check for hidden assumptions or missing edge cases")

        # 5. Grounding check
        grounding = self._check_grounding(proof)
        checks.append({"name": "grounding", "passed": grounding["passed"], "score": grounding["score"], "detail": grounding.get("detail", "")})
        if not grounding["passed"]:
            suggestions.append("Proof does not cite any known theorems — ground it in established results")

        # 6. Code safety check
        code_safety = self._check_code_safety(code_blocks)
        checks.append({"name": "code_safety", "passed": code_safety["passed"], "score": code_safety["score"], "detail": code_safety.get("detail", "")})

        # Compute weighted score
        score = sum(
            c["score"] * self.WEIGHTS.get(c["name"], 0.1)
            for c in checks
        )

        # Determine verdict
        all_passed = all(c["passed"] for c in checks)
        if all_passed and score >= 0.8:
            verdict = QualityVerdict.PASS
        elif score >= 0.5:
            verdict = QualityVerdict.WARN
        elif novelty["score"] < 0.3:
            verdict = QualityVerdict.STALE
        elif score < 0.3:
            verdict = QualityVerdict.FAIL
        else:
            verdict = QualityVerdict.NEEDS_REVIEW

        # Track for novelty
        self._recent_results.append(hypothesis[:200])
        if len(self._recent_results) > self._novelty_window:
            self._recent_results = self._recent_results[-self._novelty_window:]

        self._total_checks += 1
        if verdict in (QualityVerdict.PASS, QualityVerdict.WARN):
            self._passed_checks += 1

        return QualityReport(
            verdict=verdict, score=score,
            checks=checks, suggestions=suggestions,
        )

    def _check_soundness(self, proof: str) -> dict:
        """Check logical soundness of the proof."""
        score = 0.0
        passed = False

        # Has proof structure markers
        if any(kw in proof.lower() for kw in ["proof", "证明", "theorem", "lemma", "therefore", "hence", "所以", "因此", "qed"]):
            score += 0.3

        # Has step indicators
        if any(kw in proof for kw in ["1.", "2.", "Step", "step", "步骤"]):
            score += 0.2

        # Has equations/formulas
        if proof.count("$") >= 4 or proof.count("$$") >= 1:
            score += 0.2

        # Has a conclusion
        if any(kw in proof.lower()[-200:] for kw in ["therefore", "hence", "thus", "conclude", "所以", "因此", "综上", "证毕", "qed"]):
            score += 0.15

        # Has some length (not trivial)
        if len(proof) > 100:
            score += 0.15

        passed = score >= 0.5
        return {"passed": passed, "score": score, "detail": f"Structure score: {score:.2f}"}

    def _check_novelty(self, hypothesis: str) -> dict:
        """Check if result is novel (not duplicate of recent results)."""
        if not self._recent_results:
            return {"passed": True, "score": 1.0, "detail": "First result — automatically novel"}

        # Simple overlap check
        hypothesis_lower = hypothesis.lower()
        overlaps = 0
        for recent in self._recent_results[-10:]:
            words_h = set(hypothesis_lower.split())
            words_r = set(recent.lower().split())
            overlap = len(words_h & words_r) / max(len(words_h | words_r), 1)
            if overlap > 0.7:
                overlaps += 1

        score = 1.0 - (overlaps / min(len(self._recent_results[-10:]), 10)) * 0.8
        passed = overlaps <= 2
        return {"passed": passed, "score": max(score, 0.0), "detail": f"Similar to {overlaps} recent results"}

    def _check_falsifiability(self, hypothesis: str, counterexamples: list) -> dict:
        """Check if the hypothesis is falsifiable."""
        score = 0.5  # Neutral start
        detail = ""

        # Has specific numbers/conditions
        import re
        if re.search(r'\bfor\s+(all|every|any)\b', hypothesis.lower()):
            score += 0.2
            detail += "Universal quantifier found; "

        # Counterexample search ran
        if counterexamples:
            score += 0.1
            detail += f"Counterexample search found {len(counterexamples)} candidates; "
        else:
            detail += "No counterexamples found; "

        # Has testable conditions
        if any(kw in hypothesis.lower() for kw in ["=", "<", ">", "≤", "≥", "∈", "⊂", "iff"]):
            score += 0.1
            detail += "Has testable relational operators; "

        if "prove or disprove" in hypothesis.lower():
            score += 0.1

        passed = score >= 0.6
        return {"passed": passed, "score": min(score, 1.0), "detail": detail.strip("; ")}

    def _check_completeness(self, proof: str) -> dict:
        """Check if proof is complete (not missing steps)."""
        if not proof:
            return {"passed": False, "score": 0.0, "detail": "No proof provided"}

        score = 0.0
        # Length-based completeness
        length = len(proof)
        if length > 1000:
            score += 0.4
        elif length > 500:
            score += 0.3
        elif length > 200:
            score += 0.2
        elif length > 50:
            score += 0.1

        # Has explicit assumptions
        if any(kw in proof.lower() for kw in ["assume", "given", "let", "suppose", "假设", "已知", "设"]):
            score += 0.2

        # Has closing
        if any(kw in proof.lower()[-100:] for kw in ["qed", "证毕", "therefore proved", "hence proved"]):
            score += 0.2

        # No obvious "TODO" or gaps
        gap_markers = ["todo", "??", "missing", "obviously", "clearly", "trivially"]
        gaps = sum(1 for g in gap_markers if g in proof.lower())
        if gaps > 2:
            score -= 0.2 * (gaps - 2)

        passed = score >= 0.45
        return {"passed": passed, "score": max(min(score, 1.0), 0.0), "detail": f"Length: {length} chars, {gaps} gap markers"}

    def _check_grounding(self, proof: str) -> dict:
        """Check if proof is grounded in known results."""
        score = 0.0

        # Check for theorem references
        theorem_patterns = [
            r"(?:by|from|using)\s+(?:the\s+)?([A-Z][\w\s]+(?:Theorem|Lemma|Corollary|Identity|Formula|Principle|Law))",
            r"(?:定理|引理|公式|恒等式|原理|定律)",
        ]
        import re
        for pat in theorem_patterns:
            if re.search(pat, proof):
                score += 0.3
                break

        # Has citation markers
        if any(marker in proof for marker in ["[", "(", "ref", "cite"]):
            score += 0.2

        # Has variable definitions
        if "where" in proof.lower() or "令" in proof or "定义" in proof:
            score += 0.2

        # Non-trivial proof without any grounding is suspicious
        if len(proof) > 300 and score == 0:
            score = 0.1

        passed = score >= 0.3
        return {"passed": passed, "score": min(score, 1.0), "detail": f"Grounding score: {score:.2f}"}

    def _check_code_safety(self, code_blocks: list[str]) -> dict:
        """Check if generated code is safe to execute."""
        if not code_blocks:
            return {"passed": True, "score": 1.0, "detail": "No code to check"}

        dangerous = ["os.system", "subprocess", "exec(", "eval(", "__import__", "open(", "rm ", "rmdir"]
        issues = 0
        for block in code_blocks:
            for pattern in dangerous:
                if pattern in block:
                    issues += 1

        score = 1.0 - min(issues * 0.2, 1.0)
        passed = issues == 0
        return {"passed": passed, "score": score, "detail": f"{issues} dangerous patterns found"}

    @property
    def pass_rate(self) -> float:
        if self._total_checks == 0:
            return 0.0
        return self._passed_checks / self._total_checks


# ── Early-Stop Governor ──────────────────────────────────────────────

class StagnationReason(Enum):
    REPEATED_FAILURE = "repeated_failure"
    DIMINISHING_RETURNS = "diminishing_returns"
    CIRCULAR_REASONING = "circular_reasoning"
    TOO_MANY_CRASHES = "too_many_crashes"


@dataclass
class GovernorState:
    consecutive_failures: int = 0
    consecutive_crashes: int = 0
    last_n_scores: list = field(default_factory=list)
    best_score: float = 0.0
    improvement_streak: int = 0
    direction_changes: int = 0
    total_experiments: int = 0


class EarlyStopGovernor:
    """Decide when to stop a line of investigation and pivot.

    Inspired by smallcode: detect when the agent is stuck in a local minimum
    and force a direction change before burning tokens.

    Triggers:
    - 3+ consecutive failures → hard fail, pivot required
    - 5+ experiments with no improvement → diminishing returns
    - 3+ crashes in a row → bad code path, revert
    - Score oscillating without advancement → circular reasoning
    """

    def __init__(
        self,
        max_consecutive_failures: int = 3,
        max_no_improvement: int = 5,
        max_crashes: int = 3,
        improvement_threshold: float = 0.02,
    ):
        self.max_consecutive_failures = max_consecutive_failures
        self.max_no_improvement = max_no_improvement
        self.max_crashes = max_crashes
        self.improvement_threshold = improvement_threshold
        self.state = GovernorState()

    def should_stop(self, score: float, status: str) -> tuple[bool, Optional[StagnationReason], str]:
        """Check if the current line of research should be abandoned.

        Args:
            score: Quality/strength score from the latest experiment
            status: 'keep', 'discard', or 'crash'

        Returns:
            (should_stop, reason, message)
        """
        self.state.total_experiments += 1
        self.state.last_n_scores.append(score)
        if len(self.state.last_n_scores) > 10:
            self.state.last_n_scores = self.state.last_n_scores[-10:]

        # Check crashes
        if status == "crash":
            self.state.consecutive_crashes += 1
            self.state.consecutive_failures = 0
            if self.state.consecutive_crashes >= self.max_crashes:
                return True, StagnationReason.TOO_MANY_CRASHES, (
                    f"{self.state.consecutive_crashes} consecutive crashes — "
                    "revert and try different approach"
                )
        else:
            self.state.consecutive_crashes = 0

        # Check failures
        if status == "discard" or score < 0.2:
            self.state.consecutive_failures += 1
            self.state.improvement_streak = 0
            if self.state.consecutive_failures >= self.max_consecutive_failures:
                return True, StagnationReason.REPEATED_FAILURE, (
                    f"{self.state.consecutive_failures} consecutive failures — "
                    "pivot to new research direction"
                )
        else:
            self.state.consecutive_failures = 0

        # Check diminishing returns
        if status == "keep":
            if score > self.state.best_score + self.improvement_threshold:
                self.state.best_score = score
                self.state.improvement_streak += 1
            elif self.state.total_experiments >= self.max_no_improvement:
                recent_best = max(self.state.last_n_scores) if self.state.last_n_scores else 0
                if recent_best <= self.state.best_score + self.improvement_threshold:
                    return True, StagnationReason.DIMINISHING_RETURNS, (
                        f"No improvement in {self.state.total_experiments} experiments "
                        f"(best: {self.state.best_score:.3f})"
                    )

        # Check circular reasoning (scores oscillating)
        if len(self.state.last_n_scores) >= 4:
            scores = self.state.last_n_scores[-4:]
            if max(scores) - min(scores) < 0.1 and self.state.total_experiments > 4:
                # All recent scores are similar — not making progress
                return True, StagnationReason.CIRCULAR_REASONING, (
                    "Scores oscillating without advancement — try a radically different approach"
                )

        return False, None, ""

    def force_pivot(self):
        """Force a direction change. Resets failure counters but keeps best score."""
        self.state.consecutive_failures = 0
        self.state.consecutive_crashes = 0
        self.state.direction_changes += 1

    def reset(self):
        """Full reset for a new research question."""
        self.state = GovernorState()


# ── Tool Trust Scoring ───────────────────────────────────────────────

@dataclass
class ToolTrustRecord:
    name: str
    total_uses: int = 0
    successful_uses: int = 0
    failed_uses: int = 0
    last_used: float = 0.0
    trust_score: float = 1.0  # 0.0-1.0, starts at full trust
    decay_rate: float = 0.95  # Multiplied on failure


class ToolScorer:
    """Track tool reliability and decay trust in unreliable tools.

    Inspired by smallcode's trust_decay: tools that produce unverified or
    incorrect results lose priority. The system learns which tools are reliable
    for which task types.
    """

    def __init__(self):
        self._records: dict[str, ToolTrustRecord] = {}

    def record_success(self, tool_name: str):
        rec = self._get(tool_name)
        rec.total_uses += 1
        rec.successful_uses += 1
        rec.last_used = time.time()
        rec.trust_score = min(rec.trust_score + 0.05, 1.0)

    def record_failure(self, tool_name: str):
        rec = self._get(tool_name)
        rec.total_uses += 1
        rec.failed_uses += 1
        rec.last_used = time.time()
        rec.trust_score *= rec.decay_rate

    def record_result(self, tool_name: str, verified: bool):
        if verified:
            self.record_success(tool_name)
        else:
            self.record_failure(tool_name)

    def get_trust(self, tool_name: str) -> float:
        return self._get(tool_name).trust_score

    def is_reliable(self, tool_name: str, threshold: float = 0.5) -> bool:
        return self.get_trust(tool_name) >= threshold

    def get_ranked_tools(self) -> list[tuple[str, float]]:
        """Get tools ranked by trust score (most trusted first)."""
        ranked = [(name, rec.trust_score) for name, rec in self._records.items()]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

    def _get(self, tool_name: str) -> ToolTrustRecord:
        if tool_name not in self._records:
            self._records[tool_name] = ToolTrustRecord(name=tool_name)
        return self._records[tool_name]


# ── Auto-Rollback System ─────────────────────────────────────────────

@dataclass
class Checkpoint:
    """A snapshot of research state before a risky operation."""
    id: str
    question: str
    plan_state: str  # Serialized plan state
    results_snapshot: list  # Copy of recent results
    timestamp: float = field(default_factory=time.time)
    reason: str = ""


class AutoRollback:
    """Rollback bad conjectures/proofs to a known-good checkpoint.

    Before each experiment, a checkpoint is opened. If the experiment fails
    quality verification or crashes, we can roll back to the checkpoint.
    """

    def __init__(self, max_checkpoints: int = 5):
        self._checkpoints: list[Checkpoint] = []
        self.max_checkpoints = max_checkpoints
        self._total_rollbacks = 0
        self._total_saves = 0

    def save(self, question: str, plan_state: str, results: list, reason: str = "") -> Checkpoint:
        """Create a checkpoint before a risky experiment."""
        cp = Checkpoint(
            id=f"cp_{int(time.time())}",
            question=question,
            plan_state=plan_state,
            results_snapshot=list(results),
            reason=reason or "pre-experiment",
        )
        self._checkpoints.append(cp)
        if len(self._checkpoints) > self.max_checkpoints:
            self._checkpoints = self._checkpoints[-self.max_checkpoints:]
        self._total_saves += 1
        return cp

    def rollback(self) -> Optional[Checkpoint]:
        """Roll back to the most recent checkpoint."""
        if not self._checkpoints:
            return None
        cp = self._checkpoints.pop()
        self._total_rollbacks += 1
        return cp

    def get_latest(self) -> Optional[Checkpoint]:
        return self._checkpoints[-1] if self._checkpoints else None

    @property
    def rollback_count(self) -> int:
        return self._total_rollbacks

    def clear(self):
        self._checkpoints.clear()


# ── Read-Before-Write Guard ──────────────────────────────────────────

class MathClaimGuard:
    """Ensure mathematical claims are grounded in known results.

    Before accepting a new conjecture or proof step, verify that it:
    1. Cites at least one known theorem/reference (for non-trivial claims)
    2. Does not contradict known results without explicit justification
    3. Is not a trivial tautology disguised as a discovery
    """

    def __init__(self):
        self._known_theorems: dict[str, str] = {}  # name → statement
        self._pending_claims: list[dict] = []

    def add_known_theorem(self, name: str, statement: str):
        self._known_theorems[name] = statement

    def check_claim(self, claim: str, proof: str) -> dict:
        """Check if a mathematical claim is properly grounded.

        Returns dict with: allowed, reason, required_action
        """
        # Triviality check
        if len(claim) < 20:
            return {"allowed": False, "reason": "Claim too short — might be trivial", "required_action": "expand"}

        # Grounding check
        has_reference = False
        for theorem_name in self._known_theorems:
            if theorem_name.lower() in proof.lower():
                has_reference = True
                break

        if not has_reference and len(proof) > 300:
            # Non-trivial proof without any citation
            return {
                "allowed": False,
                "reason": "Proof does not cite any known theorem — ground it in established results",
                "required_action": "add_citations",
            }

        # Tautology check (very basic)
        claim_clean = claim.lower().strip()
        if claim_clean.startswith("x = x") or claim_clean.startswith("a = a"):
            return {"allowed": False, "reason": "Appears to be a tautology", "required_action": "revise"}

        return {"allowed": True, "reason": "", "required_action": ""}


# ── Injection Handler ────────────────────────────────────────────────

@dataclass
class Injection:
    """A human correction injected mid-research without breaking the loop."""
    id: str
    content: str
    priority: int = 0  # 0=low, 1=normal, 2=high, 3=critical
    applied: bool = False
    timestamp: float = field(default_factory=time.time)


class InjectionHandler:
    """Process human corrections injected during autonomous research.

    Inspired by nanobot's mid-turn injection: the human can type corrections
    that get applied to the current research context without restarting the loop.
    """

    def __init__(self):
        self._pending: list[Injection] = []
        self._applied: list[Injection] = []

    def inject(self, content: str, priority: int = 1) -> str:
        """Inject a human correction. Returns injection ID."""
        import uuid
        inj = Injection(id=str(uuid.uuid4())[:8], content=content, priority=priority)
        self._pending.append(inj)
        self._pending.sort(key=lambda x: x.priority, reverse=True)
        return inj.id

    def get_pending(self) -> list[Injection]:
        """Get all pending injections, highest priority first."""
        return [i for i in self._pending if not i.applied]

    def apply_next(self) -> Optional[Injection]:
        """Apply the highest priority pending injection."""
        pending = self.get_pending()
        if not pending:
            return None
        inj = pending[0]
        inj.applied = True
        self._applied.append(inj)
        self._pending = [i for i in self._pending if not i.applied]
        return inj

    def build_injection_context(self) -> str:
        """Build context string for all pending injections."""
        pending = self.get_pending()
        if not pending:
            return ""
        lines = ["[HUMAN CORRECTIONS — incorporate these into your research:]"]
        for inj in pending:
            lines.append(f"- [{inj.priority}] {inj.content}")
        return "\n".join(lines)

    @property
    def has_pending(self) -> bool:
        return len(self.get_pending()) > 0


# ── Unified Quality Controller ────────────────────────────────────────

class QualityController:
    """Unified quality governance for autonomous math research.

    Combines all quality systems into a single decision point:
    1. Before experiment: read-before-write guard, checkpoint save
    2. During experiment: injection handling
    3. After experiment: quality verification, early-stop check, tool scoring

    Usage:
        qc = QualityController()
        # Before experiment
        guard_result = qc.guard_claim(hypothesis)
        qc.save_checkpoint(question, plan)
        # ... run experiment ...
        # After experiment
        report = qc.evaluate(hypothesis, proof, verification, counterexamples)
        should_stop, reason = qc.check_stagnation(report.score, status)
    """

    def __init__(self):
        self.verifier = QualityVerifier()
        self.governor = EarlyStopGovernor()
        self.tool_scorer = ToolScorer()
        self.rollback = AutoRollback()
        self.guard = MathClaimGuard()
        self.injections = InjectionHandler()

    def evaluate(
        self, hypothesis: str, proof: str, verification: dict,
        counterexamples: list, code_blocks: list[str] = None,
    ) -> QualityReport:
        return self.verifier.verify(hypothesis, proof, verification, counterexamples, code_blocks)

    def guard_claim(self, claim: str, proof: str = "") -> dict:
        return self.guard.check_claim(claim, proof)

    def save_checkpoint(self, question: str, plan_state: str, results: list):
        return self.rollback.save(question, plan_state, results)

    def check_stagnation(self, score: float, status: str) -> tuple[bool, Optional[StagnationReason], str]:
        return self.governor.should_stop(score, status)

    def inject_correction(self, content: str, priority: int = 1) -> str:
        return self.injections.inject(content, priority)

    def get_quality_stats(self) -> dict:
        return {
            "verifier_pass_rate": self.verifier.pass_rate,
            "total_rollbacks": self.rollback.rollback_count,
            "direction_changes": self.governor.state.direction_changes,
            "best_score": self.governor.state.best_score,
            "pending_injections": len(self.injections.get_pending()),
            "trusted_tools": self.tool_scorer.get_ranked_tools()[:5],
        }
