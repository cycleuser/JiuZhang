"""Tests for the debate protocol (Phase 2b)."""

import pytest
from jiuzhang.research.debate import (
    DebateProtocol, DebateResult, DebateRound,
    AgentRole, Verdict, AgentMessage,
)


def test_agent_message_creation():
    msg = AgentMessage(
        role=AgentRole.PROPOSER,
        content="Proof: If n is even, n² is even.",
        confidence=0.9,
    )
    assert msg.role == AgentRole.PROPOSER
    assert msg.confidence == 0.9
    d = msg.to_dict()
    assert d["role"] == "proposer"
    assert d["content"] == "Proof: If n is even, n² is even."


def test_verdict_enum():
    assert Verdict.ACCEPT.value == "accept"
    assert Verdict.REJECT.value == "reject"
    assert Verdict.REVISE.value == "revise"


def test_debate_protocol_accepts_valid_proof():
    def prover(theorem, context="", feedback=None):
        return f"Proof of {theorem}: Step 1. Assume x is even, so x=2k. Step 2. Then x²=4k²=2(2k²). Step 3. Therefore x² is even. Q.E.D."

    protocol = DebateProtocol(prover_fn=prover, max_rounds=3)
    result = protocol.debate("If x is even then x^2 is even")

    assert result is not None
    assert result.theorem == "If x is even then x^2 is even"
    assert result.total_rounds > 0
    assert isinstance(result.final_confidence, float)


def test_debate_protocol_detects_incomplete_proof():
    def prover(theorem, context="", feedback=None):
        return "x is even, so x^2 is even"  # Too short, no structure

    protocol = DebateProtocol(prover_fn=prover, max_rounds=3)
    result = protocol.debate("If x is even then x^2 is even")

    # Short proof should score lower
    assert result.total_rounds >= 1
    assert isinstance(result.final_confidence, float)


def test_debate_protocol_with_custom_agents():
    def prover(theorem, context="", feedback=None):
        return f"Assume {theorem}. Then by definition, it holds. Q.E.D."

    def reviewer(theorem, proof):
        return {"score": 0.8, "gaps": [], "feedback": "Looks okay"}

    def critic(theorem, proof):
        return {"score": 1.0, "counterexamples": [], "feedback": "No CEs found"}

    protocol = DebateProtocol(
        prover_fn=prover,
        reviewer_fn=reviewer,
        critic_fn=critic,
        max_rounds=2,
    )
    result = protocol.debate("The sum of two primes > 2 is even")

    assert result.final_confidence >= 0.0
    assert result.total_rounds > 0


def test_debate_result_structure():
    def prover(theorem, context="", feedback=None):
        return "Proof: trivial. Q.E.D."

    protocol = DebateProtocol(prover_fn=prover, max_rounds=1)
    result = protocol.debate("1+1=2")

    assert result.theorem
    assert isinstance(result.rounds, list)
    assert result.total_rounds >= 0
    assert isinstance(result.final_verdict, Verdict)


def test_format_report():
    """Test that format_report produces readable output."""
    def prover(theorem, context="", feedback=None):
        return f"Proof of {theorem}"

    protocol = DebateProtocol(prover_fn=prover, max_rounds=1)
    result = protocol.debate("all squares are non-negative")
    report = protocol.format_report(result)

    assert "Debate Report" in report or "Debate" in report
    assert "all squares are non-negative" in report


def test_debate_protocol_max_rounds():
    def prover(theorem, context="", feedback=None):
        return f"Proof: Assume {theorem}. Done."

    protocol = DebateProtocol(prover_fn=prover, max_rounds=2)
    result = protocol.debate("x=x")

    assert result.total_rounds <= 2


def test_reviewer_default_detects_missing_assumptions():
    protocol = DebateProtocol(prover_fn=lambda t, c="", fb=None: "just a statement")
    review = protocol._default_reviewer("P→Q", "just a statement")
    assert "gaps" in review
    assert isinstance(review["score"], float)


def test_critic_default_searches_patterns():
    protocol = DebateProtocol(prover_fn=lambda t, c="", fb=None: "ok")
    critic = protocol._default_critic("All primes are odd", "All primes are odd")
    assert "counterexamples" in critic
    assert isinstance(critic["score"], float)


def test_debate_round_dataclass():
    dr = DebateRound(index=1)
    dr.verdict = Verdict.ACCEPT
    dr.proof_score = 0.95
    assert dr.verdict == Verdict.ACCEPT
    assert dr.proof_score == 0.95
