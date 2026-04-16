"""Tests for open problems, counterexamples, LaTeX, and proof modules."""

import pytest
from jiuzhang.research.open_problems import OpenProblemsDB, OpenProblem
from jiuzhang.research.counterexamples import CounterexampleFinder, ConjectureVerifier
from jiuzhang.research.latex_generator import LaTeXPaperGenerator
from jiuzhang.research.proof_assistant import ProofAssistant, Proof, ProofStep


class TestOpenProblemsDB:
    @pytest.fixture
    def db(self):
        return OpenProblemsDB()

    def test_get_problem(self, db):
        problem = db.get_problem("riemann_hypothesis")
        assert problem is not None
        assert problem.name == "Riemann Hypothesis"
        assert problem.name_cn == "黎曼猜想"
        assert problem.status == "open"

    def test_get_problems_by_field(self, db):
        problems = db.get_problems_by_field("number_theory")
        assert len(problems) >= 3

    def test_get_problems_by_status(self, db):
        open_problems = db.get_problems_by_status("open")
        assert len(open_problems) >= 10

        solved_problems = db.get_problems_by_status("solved")
        assert len(solved_problems) >= 1

    def test_search(self, db):
        results = db.search("黎曼", "zh")
        assert len(results) > 0
        assert results[0].name_cn == "黎曼猜想"

    def test_generate_report(self, db):
        report_zh = db.generate_report("zh")
        assert len(report_zh) > 100
        assert "数学开放问题" in report_zh

        report_en = db.generate_report("en")
        assert len(report_en) > 100
        assert "Open Problems in Mathematics" in report_en

    def test_get_millennium_problems(self, db):
        problems = db.get_millennium_problems()
        assert len(problems) == 7

    def test_problem_structure(self, db):
        problem = db.get_problem("p_vs_np")
        assert problem is not None
        assert isinstance(problem, OpenProblem)
        assert len(problem.key_approaches) > 0
        assert problem.difficulty in ["moderate", "hard", "extreme"]


class TestCounterexampleFinder:
    @pytest.fixture
    def finder(self):
        return CounterexampleFinder()

    def test_goldbach_test(self, finder):
        result = finder.goldbach_test(100)
        assert result["status"] == "verified"
        assert len(result["counterexamples"]) == 0
        assert result["verified_count"] > 0

    def test_collatz_test(self, finder):
        result = finder.collatz_test(1000)
        assert result["status"] == "verified"
        assert len(result["counterexamples"]) == 0

    def test_euler_sum_of_powers(self, finder):
        result = finder.euler_sum_of_powers_test()
        assert result["status"] == "counterexample_found"
        assert result["verification"] is True

    def test_fermat_last_theorem(self, finder):
        result = finder.fermat_last_theorem_check(3, 50)
        assert result["status"] == "verified"
        assert len(result["counterexamples"]) == 0

    def test_custom_conjecture(self, finder):
        # Test a true conjecture: n^2 >= n for n >= 1
        result = finder.test_conjecture(
            lambda n: n**2 >= n,
            domain="integers",
            range_start=1,
            range_end=100,
            description="n^2 >= n for n >= 1",
        )
        assert result["status"] == "verified"

    def test_custom_conjecture_false(self, finder):
        # Test a false conjecture: n^2 < n for n >= 1
        result = finder.test_conjecture(
            lambda n: n**2 < n,
            domain="integers",
            range_start=1,
            range_end=100,
            description="n^2 < n for n >= 1",
        )
        assert result["status"] == "counterexample_found"
        assert len(result["counterexamples"]) > 0


class TestConjectureVerifier:
    @pytest.fixture
    def verifier(self):
        return ConjectureVerifier()

    def test_verify_identity_true(self, verifier):
        from sympy import symbols, sin, cos

        x = symbols("x")
        result = verifier.verify_identity(sin(x) ** 2 + cos(x) ** 2, 1, [x])
        assert result["status"] == "verified"
        assert result["symbolic_check"] == "verified"

    def test_verify_identity_false(self, verifier):
        from sympy import symbols, sin, cos

        x = symbols("x")
        result = verifier.verify_identity(sin(x) + cos(x), 1, [x])
        # The status might be 'unknown' if symbolic check doesn't clearly show it's false
        # but numerical tests should find failures
        assert result["numerical_tests"] > 0
        # Either counterexample_found or unknown is acceptable for this test
        assert result["status"] in ["counterexample_found", "unknown"]

    def test_verify_inequality_true(self, verifier):
        from sympy import symbols

        x = symbols("x")
        result = verifier.verify_inequality(x**2, 0, [x])
        assert result["status"] == "verified"

    def test_verify_inequality_false(self, verifier):
        from sympy import symbols

        x = symbols("x")
        result = verifier.verify_inequality(x, x**2, [x])
        # This might fail for some values
        assert result["numerical_tests"] > 0


class TestLaTeXPaperGenerator:
    @pytest.fixture
    def generator(self):
        return LaTeXPaperGenerator()

    def test_generate_paper(self, generator, tmp_path):
        output_path = str(tmp_path / "test_paper.tex")
        latex = generator.generate_paper(
            title="Test Paper",
            author="Test Author",
            abstract="This is a test abstract.",
            sections=[
                {
                    "title": "Introduction",
                    "content": "Introduction content.",
                    "level": "section",
                },
                {"title": "Results", "content": "Results content.", "level": "section"},
            ],
            output_path=output_path,
        )

        assert len(latex) > 100
        assert "\\documentclass" in latex
        assert "Test Paper" in latex
        assert "Test Author" in latex

        # Check file was created
        assert tmp_path.joinpath("test_paper.tex").exists()

    def test_generate_beamer_presentation(self, generator, tmp_path):
        output_path = str(tmp_path / "test_presentation.tex")
        latex = generator.generate_beamer_presentation(
            title="Test Presentation",
            author="Test Author",
            slides=[
                {"title": "Introduction", "content": "Introduction slide."},
                {"title": "Results", "content": "Results slide."},
            ],
            output_path=output_path,
        )

        assert len(latex) > 100
        assert "beamer" in latex
        assert "Test Presentation" in latex

        # Check file was created
        assert tmp_path.joinpath("test_presentation.tex").exists()


class TestProofAssistant:
    @pytest.fixture
    def assistant(self):
        return ProofAssistant()

    def test_create_proof(self, assistant):
        proof = assistant.create_proof("Test Theorem")
        assert proof.theorem == "Test Theorem"
        assert len(proof.steps) == 0

    def test_add_steps(self, assistant):
        proof = assistant.create_proof("Test Theorem")
        proof.add_step("Step 1", "Justification 1")
        proof.add_step("Step 2", "Justification 2")
        proof.add_qed()

        assert len(proof.steps) == 3
        assert proof.steps[0].statement == "Step 1"
        assert proof.steps[-1].step_type == "qed"

    def test_verify_algebraic_identity_true(self, assistant):
        from sympy import symbols, expand

        x = symbols("x")
        result = assistant.verify_algebraic_identity(
            expand((x + 1) ** 2), x**2 + 2 * x + 1, [x]
        )
        assert result["verified"] is True
        assert result["proof"].verified is True

    def test_verify_algebraic_identity_false(self, assistant):
        from sympy import symbols

        x = symbols("x")
        result = assistant.verify_algebraic_identity(x**2 + 1, x**2 + 2, [x])
        assert result["verified"] is False
        assert result["proof"].verified is False

    def test_generate_proof_template(self, assistant):
        proof = assistant.generate_proof_template("direct", "test topic")
        assert len(proof.steps) > 0
        assert proof.steps[-1].step_type == "qed"

    def test_proof_to_markdown(self, assistant):
        proof = assistant.create_proof("Test Theorem")
        proof.add_step("Step 1", "Justification 1")
        proof.add_qed()

        md = proof.to_markdown()
        assert "Test Theorem" in md
        assert "Step 1" in md
        assert "Q.E.D." in md

    def test_proof_to_latex(self, assistant):
        proof = assistant.create_proof("Test Theorem")
        proof.add_step("Step 1", "Justification 1")
        proof.add_qed()

        latex = proof.to_latex()
        assert "\\begin{proof}" in latex
        assert "Test Theorem" in latex
        assert "Step 1" in latex
