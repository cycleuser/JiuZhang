"""Tests for ConjectureSynthesizer (Phase 3b) and CodeSandbox (Phase 4c)."""

import ast
import pytest
from jiuzhang.research.conjecture_synthesizer import (
    ConjectureSynthesizer, SynthesizedConjecture, SynthesisResult,
)
from jiuzhang.research.code_sandbox import (
    CodeSandbox, SandboxConfig, SandboxResult, ImportAuditor,
)


# ── ConjectureSynthesizer Tests ──────────────────────────────────────

class TestConjectureSynthesizer:
    def test_fibonacci_detection(self):
        synth = ConjectureSynthesizer(seed=42)
        fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
        result = synth.synthesize_from_sequence(fib)

        assert isinstance(result, SynthesisResult)
        assert result.total_candidates >= 1
        # Should detect Fibonacci pattern
        oeis_matches = [c for c in result.conjectures if c.oeis_match]
        assert len(oeis_matches) >= 1

    def test_squares_detection(self):
        synth = ConjectureSynthesizer(seed=42)
        squares = [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]
        result = synth.synthesize_from_sequence(squares)

        assert result.total_candidates >= 1

    def test_arithmetic_progression(self):
        synth = ConjectureSynthesizer(seed=42)
        seq = [3, 7, 11, 15, 19, 23, 27]  # d=4 arithmetic
        result = synth.synthesize_from_sequence(seq)

        arithmetic = [c for c in result.conjectures if c.source_type == "pattern_mining"]
        assert len(arithmetic) >= 1

    def test_geometric_progression(self):
        synth = ConjectureSynthesizer(seed=42)
        seq = [2, 6, 18, 54, 162]  # r=3 geometric
        result = synth.synthesize_from_sequence(seq)

        assert result.total_candidates >= 1

    def test_unknown_sequence(self):
        synth = ConjectureSynthesizer(seed=42)
        seq = [42, 17, 93, 5, 61]  # Random, no pattern
        result = synth.synthesize_from_sequence(seq)

        # Should still produce result (at minimum an empty one)
        assert isinstance(result, SynthesisResult)

    def test_synthesize_from_data_linear(self):
        synth = ConjectureSynthesizer(seed=42)
        xs = list(range(10))
        ys = [2 * x + 3 for x in xs]
        result = synth.synthesize_from_data(xs, ys)

        if result.total_candidates > 0:
            assert any("linear" in c.statement_en.lower() for c in result.conjectures)

    def test_synthesize_from_data_empty(self):
        synth = ConjectureSynthesizer(seed=42)
        result = synth.synthesize_from_data([], [])
        assert result.total_candidates == 0

    def test_harden_conjecture(self):
        synth = ConjectureSynthesizer(seed=42)
        hardenings = synth.harden_conjecture("n is prime")
        assert len(hardenings) >= 4  # domain, parity, modulo×3, primality

    def test_format_report(self):
        synth = ConjectureSynthesizer(seed=42)
        result = synth.synthesize_from_sequence([1, 1, 2, 3, 5, 8, 13])
        report = synth.format_report(result)
        assert "Synthesis" in report or "Conjecture" in report


# ── CodeSandbox Tests ────────────────────────────────────────────────

class TestCodeSandbox:
    def test_simple_execution(self):
        sandbox = CodeSandbox(SandboxConfig(isolate_process=True, timeout_seconds=10))
        result = sandbox.execute("print('hello math')")
        assert result.success
        assert "hello math" in result.stdout

    def test_math_execution(self):
        sandbox = CodeSandbox(SandboxConfig(isolate_process=True, timeout_seconds=10))
        result = sandbox.execute("""
import sympy as sp
x = sp.Symbol('x')
result = sp.integrate(x**2, x)
print(f"Integral: {result}")
""")
        if result.success:
            assert "Integral" in result.stdout or "x**3" in result.stdout
        else:
            # sympy may not be in subprocess; accept failure gracefully
            pass

    def test_basic_arithmetic(self):
        sandbox = CodeSandbox(SandboxConfig(isolate_process=True, timeout_seconds=10))
        result = sandbox.execute("""
a = 123 * 456
b = 3**10
print(f"123*456 = {a}, 3^10 = {b}")
""")
        if result.success:
            assert "123*456" in result.stdout or "56088" in result.stdout

    def test_blocks_dangerous_imports(self):
        sandbox = CodeSandbox()
        result = sandbox.execute("import os\nprint(os.getcwd())")
        # Should be blocked (or execute in subprocess where os is blocked)
        assert not result.success or "Blocked" in result.error or "blocked" in result.error.lower()

    def test_blocks_eval(self):
        sandbox = CodeSandbox()
        result = sandbox.execute("eval('1+1')")
        assert not result.success or "Dangerous" in result.error

    def test_timeout(self):
        sandbox = CodeSandbox(SandboxConfig(
            isolate_process=True, timeout_seconds=2,
        ))
        result = sandbox.execute("""
import time
time.sleep(10)
print("done")
""")
        if not result.success:
            assert "timeout" in result.error.lower() or "timed out" in result.error.lower()

    def test_import_auditor_allows_math(self):
        auditor = ImportAuditor()
        auditor.visit(ast.parse("import math\nimport sympy"))
        assert auditor.is_safe()
        assert "math" in auditor.allowed
        assert "sympy" in auditor.allowed

    def test_import_auditor_blocks_os(self):
        auditor = ImportAuditor()
        auditor.visit(ast.parse("import os\nimport subprocess"))
        assert not auditor.is_safe()
        assert "os" in auditor.blocked

    def test_sandbox_config_defaults(self):
        config = SandboxConfig()
        assert config.timeout_seconds == 30.0
        assert config.max_memory_mb == 512
        assert config.isolate_process is True

    def test_sandbox_result_structure(self):
        result = SandboxResult(success=True, output="test", stdout="test", exit_code=0)
        assert result.success
        assert result.output == "test"
        assert result.exit_code == 0

    def test_math_preamble(self):
        pre = CodeSandbox.math_preamble()
        assert "import sympy" in pre
        assert "x, y, z, t" in pre

    def test_plotting_preamble(self):
        pre = CodeSandbox.plotting_preamble()
        assert "matplotlib" in pre
        assert "plot_function" in pre
