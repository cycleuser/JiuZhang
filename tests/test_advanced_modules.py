"""Tests for self-correction generator, multi-agent research, and step verifier."""

import pytest

from jiuzhang.self_correction_generator import SelfCorrectionDataGenerator, SelfCorrectionSample
from jiuzhang.math_research_agents import (
    MathProver, MathVerifier, CounterexampleSearcher,
    LiteratureReviewer, ResearchCoordinator, ResearchPhase, ResearchReport,
)
from jiuzhang.step_verifier import StepByStepVerifier, ProofVerificationResult


class TestSelfCorrectionGenerator:
    def test_derivative_samples(self):
        gen = SelfCorrectionDataGenerator(seed=42)
        samples = gen.generate_derivative_samples(count=10)
        assert len(samples) >= 5
        assert all(isinstance(s, SelfCorrectionSample) for s in samples)

    def test_integral_samples(self):
        gen = SelfCorrectionDataGenerator(seed=42)
        samples = gen.generate_integral_samples(count=10)
        assert len(samples) >= 5
        assert all(s.category == "calculus" for s in samples)

    def test_equation_samples(self):
        gen = SelfCorrectionDataGenerator(seed=42)
        samples = gen.generate_equation_samples(count=10)
        assert len(samples) >= 5
        assert all(s.category == "algebra" for s in samples)

    def test_limit_samples(self):
        gen = SelfCorrectionDataGenerator(seed=42)
        samples = gen.generate_limit_samples(count=10)
        assert len(samples) >= 4
        assert all(s.category == "calculus" for s in samples)

    def test_generate_all(self):
        gen = SelfCorrectionDataGenerator(seed=42)
        samples = gen.generate_all({"derivative": 20, "integral": 20, "equation": 20, "limit": 10})
        assert len(samples) >= 10

    def test_to_chatml(self):
        gen = SelfCorrectionDataGenerator(seed=42)
        samples = gen.generate_derivative_samples(count=20)
        assert len(samples) > 0
        entry = gen.to_chatml(samples[0])
        assert "messages" in entry
        assert len(entry["messages"]) == 3
        assert entry["messages"][0]["role"] == "system"
        assert entry["messages"][1]["role"] == "user"
        assert entry["messages"][2]["role"] == "assistant"

    def test_stats(self):
        gen = SelfCorrectionDataGenerator(seed=42)
        gen.generate_all({"derivative": 10, "integral": 10, "equation": 10, "limit": 5})
        stats = gen.get_stats()
        assert stats["total"] > 0
        assert stats["wrong_then_correct"] >= 0
        assert stats["always_correct"] >= 0

    def test_export_jsonl(self, tmp_path):
        gen = SelfCorrectionDataGenerator(seed=42)
        gen.generate_all({"derivative": 5, "integral": 5, "equation": 5, "limit": 3})
        path = str(tmp_path / "test_self_correction.jsonl")
        gen.export_jsonl(path)
        with open(path) as f:
            lines = f.readlines()
        assert len(lines) >= 10


class TestMathProver:
    def test_attempt_proof_direct(self):
        prover = MathProver()
        success, result = prover.attempt_proof("x + 1 = 1 + x", method="direct")
        assert isinstance(success, bool)
        assert isinstance(result, str)

    def test_attempt_proof_auto(self):
        prover = MathProver()
        success, result = prover.attempt_proof("For all n, n + 0 = n", method="auto")
        assert isinstance(success, bool)

    def test_select_proof_method(self):
        prover = MathProver()
        assert prover._select_proof_method("For all x, x > 0") == "induction"
        assert prover._select_proof_method("There exists x such that x = 0") == "direct"
        assert prover._select_proof_method("It is not possible that x < 0") == "contradiction"


class TestMathVerifier:
    def test_verify_claim_equation(self):
        verifier = MathVerifier()
        result = verifier.verify_claim("2 + 2 = 4")
        assert result.confidence > 0

    def test_verify_claim_false_equation(self):
        verifier = MathVerifier()
        result = verifier.verify_claim("2 + 2 = 5")
        assert result.verified is False

    def test_verify_proof_step(self):
        verifier = MathVerifier()
        success, detail = verifier.verify_proof_step("Therefore, x = 5", "")
        assert success is True

    def test_verification_log(self):
        verifier = MathVerifier()
        verifier.verify_claim("3 + 3 = 6")
        assert len(verifier.verification_log) >= 1


class TestCounterexampleSearcher:
    def test_search_number_theory(self):
        searcher = CounterexampleSearcher()
        counters = searcher._search_number_theory("all numbers are prime", 50)
        assert len(counters) >= 1
        assert counters[0]["counterexample"] == 4  # 4 is not prime

    def test_search_counterexamples(self):
        searcher = CounterexampleSearcher()
        counters = searcher.search_counterexamples("all integers are prime", max_n=20)
        assert len(counters) >= 1

    def test_search_log(self):
        searcher = CounterexampleSearcher()
        searcher.search_counterexamples("test claim", max_n=10)
        assert len(searcher.search_log) >= 1


class TestLiteratureReviewer:
    def test_search_related(self):
        reviewer = LiteratureReviewer()
        results = reviewer.search_related("pythagorean theorem")
        assert len(results) >= 1
        assert any("Pythagorean" in r["name"] for r in results)

    def test_get_context(self):
        reviewer = LiteratureReviewer()
        context = reviewer.get_context("fermat last theorem")
        assert "Fermat" in context
        assert "Wiles" in context

    def test_get_context_unknown(self):
        reviewer = LiteratureReviewer()
        context = reviewer.get_context("unknown_topic_xyz")
        assert "No specific literature" in context


class TestResearchCoordinator:
    def test_conduct_research(self):
        coordinator = ResearchCoordinator()
        report = coordinator.conduct_research("Is 2 + 2 = 4?")
        assert isinstance(report, ResearchReport)
        assert report.question == "Is 2 + 2 = 4?"
        assert report.hypothesis != ""
        assert len(report.steps) >= 5
        assert 0 <= report.confidence <= 1.0

    def test_format_report(self):
        coordinator = ResearchCoordinator()
        report = coordinator.conduct_research("Is 2 + 2 = 4?")
        formatted = coordinator.format_report(report)
        assert "Research Report" in formatted
        assert "Hypothesis" in formatted
        assert "Conclusion" in formatted


class TestStepByStepVerifier:
    def test_extract_steps_numbered(self):
        verifier = StepByStepVerifier()
        proof = "1. Let x = 5\n2. Then x + 1 = 6\n3. Therefore, 5 + 1 = 6"
        steps = verifier.extract_steps(proof)
        assert len(steps) >= 2

    def test_extract_steps_bullet(self):
        verifier = StepByStepVerifier()
        proof = "- Let x = 5\n- Then x + 1 = 6\n- Therefore, 5 + 1 = 6"
        steps = verifier.extract_steps(proof)
        assert len(steps) >= 2

    def test_verify_step_equation(self):
        verifier = StepByStepVerifier()
        verified, method, confidence, error = verifier.verify_step("2 + 2 = 4")
        assert verified is True

    def test_verify_step_false_equation(self):
        verifier = StepByStepVerifier()
        verified, method, confidence, error = verifier.verify_step("2 + 2 = 5")
        assert verified is False

    def test_verify_step_logical(self):
        verifier = StepByStepVerifier()
        verified, method, confidence, error = verifier.verify_step("Therefore, x = 5")
        assert verified is True

    def test_verify_proof(self):
        verifier = StepByStepVerifier()
        proof = """Step 1: Let f(x) = x^2 + 2x + 1
Step 2: f'(x) = 2x + 2
Step 3: f''(x) = 2
Step 4: Therefore, f(x) is convex.
Step 5: Q.E.D."""
        result = verifier.verify_proof(proof)
        assert isinstance(result, ProofVerificationResult)
        assert result.total_steps >= 3
        assert result.verified_steps >= 0

    def test_format_verification_report(self):
        verifier = StepByStepVerifier()
        proof = "1. x = 5\n2. x + 1 = 6"
        result = verifier.verify_proof(proof)
        report = verifier.format_verification_report(result)
        assert "Verification Report" in report
        assert "Step" in report

    def test_generate_suggestion(self):
        verifier = StepByStepVerifier()
        suggestion = verifier._generate_suggestion("x = 5", "parse_error in expression")
        assert suggestion is not None
        assert "syntax" in suggestion.lower()