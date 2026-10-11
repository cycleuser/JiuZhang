"""Tests for the symbolic verification layer."""

import pytest
from sympy import Rational, pi, oo

from jiuzhang.symbolic_verify import (
    verify_equation,
    verify_derivative,
    verify_integral,
    verify_limit,
    verify_solution,
    verify_llm_output,
    _safe_parse,
    VerificationResult,
)


class TestSafeParse:
    def test_basic_poly(self):
        assert _safe_parse("x**2 + 1") is not None

    def test_dangerous_input(self):
        assert _safe_parse("__import__('os')") is None

    def test_invalid_expr(self):
        assert _safe_parse("!!!") is None


class TestVerifyEquation:
    def test_true_identity(self):
        r = verify_equation("x**2 - 1 = (x-1)*(x+1)")
        assert r.verified is True
        assert r.confidence >= 0.7

    def test_false_equation(self):
        r = verify_equation("2 + 2 = 5")
        assert r.verified is False

    def test_const_true(self):
        r = verify_equation("6 = 2*3")
        assert r.verified is True

    def test_no_separator(self):
        r = verify_equation("just a string")
        assert r.verified is False
        assert r.method == "no_separator"


class TestVerifyDerivative:
    def test_polynomial(self):
        r = verify_derivative("x**3", "3*x**2")
        assert r.verified is True

    def test_wrong_deriv(self):
        r = verify_derivative("x**2", "2*x**3")
        assert r.verified is False

    def test_parse_failure(self):
        r = verify_derivative("!!!", "2*x")
        assert r.verified is False
        assert r.method == "parse_failure"


class TestVerifyIntegral:
    def test_power_rule(self):
        r = verify_integral("x**2", "x**3/3")
        assert r.verified is True

    def test_wrong_integral(self):
        r = verify_integral("x**2", "x**4/4")
        assert r.verified is False


class TestVerifyLimit:
    def test_limit_infinity(self):
        r = verify_limit("1/x", target="oo")
        assert r.verified is True

    def test_limit_finite(self):
        r = verify_limit("x**2", var="x", target="2")
        assert r.verified is True


class TestVerifySolution:
    def test_quadratic(self):
        r = verify_solution("x**2 - 4 = 0", "x = 2")
        assert r.verified is True

    def test_wrong_solution(self):
        r = verify_solution("x**2 - 4 = 0", "x = 3")
        assert r.verified is False

    def test_parse_failure(self):
        r = verify_solution("!!!", "x = 1")
        assert r.verified is False


class TestVerifyLLMOutput:
    def test_extracts_equations(self):
        text = "We know that 3x + 2x = 5x, and thus (a+b)^2 = a^2 + 2*a*b + b^2."
        results = verify_llm_output(text)
        assert len(results) >= 1

    def test_empty_text(self):
        assert verify_llm_output("") == []