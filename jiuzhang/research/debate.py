"""Multi-Agent Debate Protocol — adversarial proof validation.

Inspired by multi-agent debate systems and nanobot's agent architecture.
Multiple specialized agents collaborate to validate and strengthen mathematical proofs:

Agents:
- Proposer: Generates proofs and conjectures
- Reviewer: Checks for logical gaps, missing steps, hidden assumptions
- Critic: Actively tries to find flaws and counterexamples (adversarial)
- Synthesizer: Combines findings into the strongest possible result

The protocol runs multiple rounds:
1. Proposer → generates proof
2. Reviewer → identifies gaps
3. Critic → searches for counterexamples
4. Proposer → patches gaps
5. Repeat until convergence or max rounds
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable
import time


class AgentRole(Enum):
    PROPOSER = "proposer"
    REVIEWER = "reviewer"
    CRITIC = "critic"
    SYNTHESIZER = "synthesizer"


class Verdict(Enum):
    ACCEPT = "accept"            # Proof is valid
    REJECT = "reject"            # Proof is invalid
    REVISE = "revise"            # Needs revision
    UNCERTAIN = "uncertain"      # Cannot determine


@dataclass
class AgentMessage:
    role: AgentRole
    content: str
    confidence: float = 1.0
    evidence: list = field(default_factory=list)
    round: int = 0

    def to_dict(self) -> dict:
        return {
            "role": self.role.value,
            "content": self.content,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "round": self.round,
        }


@dataclass
class DebateRound:
    index: int
    proposer_message: str = ""
    reviewer_message: str = ""
    critic_message: str = ""
    verdict: Verdict = Verdict.UNCERTAIN
    counterexamples_found: list = field(default_factory=list)
    gaps_identified: list = field(default_factory=list)
    proof_score: float = 0.0


@dataclass
class DebateResult:
    theorem: str
    rounds: list = field(default_factory=list)  # List[DebateRound]
    final_proof: str = ""
    final_verdict: Verdict = Verdict.UNCERTAIN
    final_confidence: float = 0.0
    total_counterexamples: int = 0
    total_gaps_resolved: int = 0
    total_rounds: int = 0
    synthesis: str = ""


class DebateProtocol:
    """Multi-round adversarial debate for proof validation.

    Usage:
        protocol = DebateProtocol(prover_fn, reviewer_fn, critic_fn)
        result = protocol.debate("The sum of two even numbers is even")
        print(result.final_proof)
    """

    def __init__(
        self,
        prover_fn: Callable,
        reviewer_fn: Optional[Callable] = None,
        critic_fn: Optional[Callable] = None,
        synthesizer_fn: Optional[Callable] = None,
        max_rounds: int = 5,
        confidence_threshold: float = 0.95,
        improvement_threshold: float = 0.02,
    ):
        self.prover = prover_fn
        self.reviewer = reviewer_fn or self._default_reviewer
        self.critic = critic_fn or self._default_critic
        self.synthesizer = synthesizer_fn or self._default_synthesizer
        self.max_rounds = max_rounds
        self.confidence_threshold = confidence_threshold
        self.improvement_threshold = improvement_threshold

    def debate(
        self,
        theorem: str,
        initial_proof: str = "",
    ) -> DebateResult:
        """Run the full debate protocol.

        Args:
            theorem: The theorem to prove/validate
            initial_proof: Optional initial proof to start from

        Returns:
            DebateResult with all rounds and final synthesis
        """
        result = DebateResult(theorem=theorem)
        rounds: list[DebateRound] = []

        # Round 0: Initial proof
        if not initial_proof:
            initial_proof = self.prover(theorem, context="", feedback=[])

        current_proof = initial_proof
        best_score = 0.0
        best_proof = current_proof

        for round_idx in range(self.max_rounds):
            dr = DebateRound(index=round_idx + 1)
            dr.proposer_message = current_proof[:500]

            # Reviewer checks for gaps
            review_result = self.reviewer(theorem, current_proof)
            dr.reviewer_message = review_result.get("feedback", "")[:500]
            gaps = review_result.get("gaps", [])
            dr.gaps_identified = gaps

            # Critic searches for counterexamples
            critic_result = self.critic(theorem, current_proof)
            dr.critic_message = critic_result.get("feedback", "")[:500]
            counterexamples = critic_result.get("counterexamples", [])
            dr.counterexamples_found = counterexamples

            # Determine verdict
            has_gaps = len(gaps) > 0
            has_counterexamples = len(counterexamples) > 0
            review_score = review_result.get("score", 0.5)

            if not has_gaps and not has_counterexamples:
                dr.verdict = Verdict.ACCEPT
                dr.proof_score = 1.0
            elif has_counterexamples:
                dr.verdict = Verdict.REJECT
                dr.proof_score = 0.0
            elif has_gaps:
                dr.verdict = Verdict.REVISE
                dr.proof_score = review_score
            else:
                dr.verdict = Verdict.UNCERTAIN
                dr.proof_score = review_score

            rounds.append(dr)

            # Track best proof
            if dr.proof_score > best_score:
                best_score = dr.proof_score
                best_proof = current_proof

            # Check convergence
            if dr.verdict == Verdict.ACCEPT and review_score >= self.confidence_threshold:
                break

            if dr.verdict == Verdict.REJECT:
                # Proof is fundamentally wrong, ask proposer for new approach
                feedback = []
                for gap in gaps:
                    feedback.append(f"Gap: {gap}")
                for ce in counterexamples:
                    feedback.append(f"Counterexample: {ce}")

                current_proof = self.prover(theorem, current_proof, feedback)
            elif dr.verdict == Verdict.REVISE:
                # Proof needs patching
                feedback = [f"Please address: {g}" for g in gaps]
                current_proof = self.prover(theorem, current_proof, feedback)
            else:
                # Uncertain — minor improvement
                feedback = review_result.get("feedback", "").split("\n")[:3]
                current_proof = self.prover(theorem, current_proof, feedback)

            # Check if improving
            if best_score > 0 and dr.proof_score - best_score < self.improvement_threshold:
                # Stagnating
                if round_idx >= 2:
                    break

        # Synthesize final result
        synthesis = self.synthesizer(theorem, rounds, best_proof)

        result.rounds = rounds
        result.final_proof = best_proof
        result.final_confidence = best_score
        result.total_rounds = len(rounds)
        result.total_counterexamples = sum(len(r.counterexamples_found) for r in rounds)
        result.total_gaps_resolved = sum(len(r.gaps_identified) for r in rounds)
        result.synthesis = synthesis

        # Determine final verdict from last round
        if rounds:
            last = rounds[-1]
            result.final_verdict = last.verdict
        else:
            result.final_verdict = Verdict.UNCERTAIN

        return result

    # ── Default Agent Implementations ─────────────────────────────────

    def _default_reviewer(self, theorem: str, proof: str) -> dict:
        """Default reviewer: checks for logical gaps."""
        gaps = []
        feedback_parts = []

        # Check for common proof issues
        checks = [
            ("no_assumptions", "No explicit assumptions stated", "State your assumptions clearly"),
            ("no_conclusion", "No conclusion/QED marker", "Add a clear conclusion (Q.E.D.)"),
            ("too_short", "Proof seems too short (under 50 chars)", "Expand with more intermediate steps"),
            ("circular", "Possible circular reasoning", "Ensure each step follows from previous ones"),
            ("unjustified_leap", "Unjustified logical leap detected", "Add justification for each step"),
        ]

        proof_lower = proof.lower()
        for check_id, description, suggestion in checks:
            if self._check_issue(check_id, proof_lower, proof):
                gaps.append(description)
                feedback_parts.append(suggestion)

        if not gaps:
            feedback_parts.append("No obvious logical gaps found. Proof appears structurally sound.")

        score = max(0.0, 1.0 - 0.2 * len(gaps))
        return {
            "score": score,
            "gaps": gaps,
            "feedback": "\n".join(feedback_parts),
        }

    def _default_critic(self, theorem: str, proof: str) -> dict:
        """Default critic: searches for counterexamples."""
        counterexamples = []
        feedback_parts = []

        # Known counterexample patterns
        patterns = [
            ("all_primes", r"all\s+.*\s+primes?", "Try n=9: composite odd number is a counterexample"),
            ("always_positive", r"always\s+positive", "Check negative values or zero"),
            ("for_all_n", r"for\s+all\s+n", "Test n=0, n=1, n=-1 edge cases"),
            ("every_even", r"every\s+even", "Check n=0 and n=2 separately"),
        ]

        proof_lower = proof.lower()
        for pattern_id, pattern, feedback in patterns:
            import re
            if re.search(pattern, proof_lower):
                counterexamples.append(pattern_id)
                feedback_parts.append(feedback)

        if not counterexamples:
            feedback_parts.append("No obvious counterexample patterns detected.")

        score = 1.0 if not counterexamples else 0.3
        return {
            "score": score,
            "counterexamples": counterexamples,
            "feedback": "\n".join(feedback_parts),
        }

    def _default_synthesizer(self, theorem: str, rounds: list, best_proof: str) -> str:
        """Default synthesizer: combines findings."""
        parts = ["# Debate Synthesis\n"]

        accept_rounds = [r for r in rounds if r.verdict == Verdict.ACCEPT]
        reject_rounds = [r for r in rounds if r.verdict == Verdict.REJECT]
        revise_rounds = [r for r in rounds if r.verdict == Verdict.REVISE]

        parts.append(f"Total rounds: {len(rounds)}")
        parts.append(f"Accepted: {len(accept_rounds)}")
        parts.append(f"Rejected: {len(reject_rounds)}")
        parts.append(f"Revised: {len(revise_rounds)}")
        parts.append("")

        all_gaps = []
        all_ces = []
        for r in rounds:
            all_gaps.extend(r.gaps_identified)
            all_ces.extend(r.counterexamples_found)

        if all_gaps:
            parts.append(f"Gaps identified: {len(all_gaps)}")
        if all_ces:
            parts.append(f"Counterexamples found: {len(all_ces)}")

        parts.append(f"\n## Final Proof\n{best_proof}")
        return "\n".join(parts)

    def _check_issue(self, check_id: str, proof_lower: str, proof: str) -> bool:
        """Check for a specific proof issue."""
        if check_id == "no_assumptions":
            assumption_markers = ["assume", "suppose", "let", "设", "假设", "给定"]
            return not any(m in proof_lower for m in assumption_markers)
        elif check_id == "no_conclusion":
            conclusion_markers = ["q.e.d", "therefore", "hence", "thus", "证毕", "所以", "因此", "综上"]
            return not any(m in proof_lower for m in conclusion_markers)
        elif check_id == "too_short":
            return len(proof) < 50
        elif check_id == "circular":
            # Naive circular check: same sentence appearing twice
            sentences = [s.strip() for s in proof.split(".") if len(s) > 20]
            return len(sentences) >= 2 and len(set(sentences)) < len(sentences)
        elif check_id == "unjustified_leap":
            justification_markers = ["because", "since", "by", "from", "由于", "根据", "由"]
            return len(proof) > 100 and sum(1 for m in justification_markers if m in proof_lower) < 2
        return False

    def format_report(self, result: DebateResult) -> str:
        """Generate a human-readable debate report."""
        lines = [
            "🔄 Multi-Agent Proof Debate Report",
            "=" * 50,
            f"Theorem: {result.theorem[:200]}",
            f"Final Verdict: {result.final_verdict.value.upper()}",
            f"Confidence: {result.final_confidence:.2%}",
            f"Rounds: {result.total_rounds}",
            f"Counterexamples: {result.total_counterexamples}",
            f"Gaps resolved: {result.total_gaps_resolved}",
            "",
            "Round Summary:",
            "-" * 40,
        ]

        for dr in result.rounds:
            icon = {
                Verdict.ACCEPT: "✅",
                Verdict.REJECT: "❌",
                Verdict.REVISE: "🔧",
                Verdict.UNCERTAIN: "❓",
            }.get(dr.verdict, "❓")

            lines.append(
                f"{icon} Round {dr.index}: {dr.verdict.value} "
                f"(score: {dr.proof_score:.2f}, "
                f"gaps: {len(dr.gaps_identified)}, "
                f"CEs: {len(dr.counterexamples_found)})"
            )

        if result.synthesis:
            lines.append("")
            lines.append(result.synthesis)

        return "\n".join(lines)
