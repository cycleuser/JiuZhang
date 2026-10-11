"""Tests for multi-engine verification (Phase 3a)."""

import pytest
from jiuzhang.research.multi_engine_verify import (
    MultiEngineVerifier, MultiEngineResult, EngineVerdict,
)


def test_engine_verdict_creation():
    v = EngineVerdict(engine="sympy", passed=True, confidence=0.9, details="OK")
    assert v.engine == "sympy"
    assert v.passed is True
    assert v.confidence == 0.9
    d = v.to_dict()
    assert d["engine"] == "sympy"


def test_verify_identity():
    verifier = MultiEngineVerifier(engines=["sympy"])
    result = verifier.verify("x^2 - y^2 = (x-y)*(x+y)", variables=["x", "y"])

    assert isinstance(result, MultiEngineResult)
    assert result.engines_total >= 1
    # SymPy should verify this identity
    sympy_verdicts = [v for v in result.verdicts if v.engine == "sympy"]
    if sympy_verdicts:
        assert sympy_verdicts[0].passed is True


def test_verify_false_claim():
    verifier = MultiEngineVerifier(engines=["sympy", "numerical"])
    result = verifier.verify("x + 1 = x + 2", variables=["x"])

    assert isinstance(result, MultiEngineResult)
    # Should be rejected
    assert not result.consensus or result.consensus_score < 0.5


def test_verify_trig_identity():
    verifier = MultiEngineVerifier(engines=["sympy"])
    result = verifier.verify("sin(x)^2 + cos(x)^2 = 1", variables=["x"])

    sympy_verdicts = [v for v in result.verdicts if v.engine == "sympy"]
    if sympy_verdicts:
        assert sympy_verdicts[0].passed is True


def test_verify_numerical_crosscheck():
    verifier = MultiEngineVerifier(engines=["numerical"])
    result = verifier.verify("x * x = x^2", variables=["x"], num_samples=500)

    numerical = [v for v in result.verdicts if v.engine == "numerical"]
    if numerical:
        # x*x = x^2 should pass numerical check
        assert numerical[0].passed is True


def test_extract_equations():
    verifier = MultiEngineVerifier()
    eqs = verifier._extract_equations("We have a = b and c = d")
    assert len(eqs) >= 1


def test_format_report():
    verifier = MultiEngineVerifier(engines=["sympy"])
    result = verifier.verify("x + 0 = x", variables=["x"])
    report = verifier.format_report(result)
    assert "Multi-Engine" in report or "Verification" in report


def test_multiple_engines_consensus():
    verifier = MultiEngineVerifier(engines=["sympy", "numerical"])
    result = verifier.verify("x + y = y + x", variables=["x", "y"], num_samples=200)

    assert result.engines_total >= 1
    # Commutativity should get high consensus
    if result.engines_total >= 2:
        assert result.consensus_score > 0.5


def test_recommendation_string():
    verifier = MultiEngineVerifier(engines=["sympy"])
    result = verifier.verify("1+1=2", variables=[])
    assert isinstance(result.recommendation, str)
    assert len(result.recommendation) > 0
