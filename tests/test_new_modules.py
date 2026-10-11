"""Tests for curriculum data pipeline, math benchmark, and conjecture engine."""

import pytest

from jiuzhang.curriculum_pipeline import CurriculumDataPipeline, STAGE_NAMES
from jiuzhang.math_benchmark import MathBenchmark, ELEMENTARY_PROBLEMS, INTERMEDIATE_PROBLEMS, ADVANCED_PROBLEMS, RESEARCH_PROBLEMS
from jiuzhang.conjecture_engine import ConjectureEngine, Conjecture


class TestCurriculumPipeline:
    def test_stage1_arithmetic(self):
        pipe = CurriculumDataPipeline(seed=42)
        samples = pipe._stage1_arithmetic(30)
        assert len(samples) >= 24  # 5 groups of count//6 + remainder
        assert all(s.stage == 1 for s in samples)

    def test_stage2_equations(self):
        pipe = CurriculumDataPipeline(seed=42)
        samples = pipe._stage2_equations(20)
        assert len(samples) >= 16
        assert all(s.stage == 2 for s in samples)

    def test_stage3_proofs(self):
        pipe = CurriculumDataPipeline(seed=42)
        samples = pipe._stage3_proofs(15)
        assert len(samples) >= 10
        assert all(s.stage == 3 for s in samples)

    def test_stage4_research(self):
        pipe = CurriculumDataPipeline(seed=42)
        samples = pipe._stage4_research(10)
        assert len(samples) >= 3
        assert all(s.stage == 4 for s in samples)

    def test_generate_all_stages(self):
        pipe = CurriculumDataPipeline(seed=42)
        samples = pipe.generate_all_stages({1: 30, 2: 20, 3: 15, 4: 10})
        assert len(samples) >= 50

    def test_to_chatml(self):
        pipe = CurriculumDataPipeline(seed=42)
        samples = pipe._stage1_arithmetic(6)
        entry = pipe.to_chatml(samples[0])
        assert "messages" in entry
        assert len(entry["messages"]) == 3
        assert entry["stage"] == 1
        assert entry["sympy_verified"] is not None

    def test_stats(self):
        pipe = CurriculumDataPipeline(seed=42)
        pipe.generate_all_stages({1: 30, 2: 20, 3: 10, 4: 5})
        stats = pipe.get_stats()
        assert stats["total"] > 0
        assert stats["verified"] >= 0
        assert 1 in stats["by_stage"]

    def test_export_jsonl(self, tmp_path):
        pipe = CurriculumDataPipeline(seed=42)
        pipe.generate_all_stages({1: 10, 2: 8, 3: 6, 4: 4})
        path = str(tmp_path / "test_curriculum.jsonl")
        pipe.export_jsonl(path)
        import json
        with open(path) as f:
            lines = f.readlines()
        assert len(lines) >= 20

    def test_stage_names(self):
        assert 1 in STAGE_NAMES
        assert STAGE_NAMES[1] == "arithmetic"
        assert STAGE_NAMES[4] == "research_frontier"


class TestMathBenchmark:
    def test_get_problems(self):
        bench = MathBenchmark()
        problems = bench.get_problems()
        assert len(problems) >= 30

    def test_get_problems_by_category(self):
        bench = MathBenchmark()
        alg = bench.get_problems(categories=["algebra"])
        assert len(alg) > 0
        assert all(p.category == "algebra" for p in alg)

    def test_get_problems_by_difficulty(self):
        bench = MathBenchmark()
        elem = bench.get_problems(difficulties=["elementary"])
        assert len(elem) > 0

    def test_score_exact_match(self):
        bench = MathBenchmark()
        p = ELEMENTARY_PROBLEMS[0]  # "830"
        score, detail = bench.score_response(p, "The answer is 830")
        assert score > 0

    def test_score_zero_match(self):
        bench = MathBenchmark()
        p = ELEMENTARY_PROBLEMS[0]
        score, detail = bench.score_response(p, "I don't know")
        assert score == 0.0

    def test_score_qualitative(self):
        bench = MathBenchmark()
        p = RESEARCH_PROBLEMS[0]  # Collatz
        score, detail = bench.score_response(p, "This is an open unsolved problem that has been verified computationally")
        assert score > 0

    def test_run_benchmark(self):
        bench = MathBenchmark()
        result = bench.run(model_name="test", categories=["arithmetic"])
        assert result.total > 0
        assert "overall" in result.scores


class TestConjectureEngine:
    def test_algebraic_identities(self):
        engine = ConjectureEngine(seed=42)
        results = engine.discover_algebraic_identities(trials=50)
        assert len(results) >= 0  # May find some identities

    def test_number_theory(self):
        engine = ConjectureEngine(seed=42)
        results = engine.discover_number_theory_patterns(max_n=50)
        assert len(results) >= 1  # Should find at least Fermat verification

    def test_calculus_patterns(self):
        engine = ConjectureEngine(seed=42)
        results = engine.discover_calculus_patterns()
        assert len(results) >= 4  # Should find derivative rules
        verified = [c for c in results if c.sympy_verified]
        assert len(verified) >= 2

    def test_counterexample_search(self):
        engine = ConjectureEngine(seed=42)
        counters = engine.search_counterexamples(max_n=100)
        assert len(counters) >= 1

    def test_full_discovery(self):
        engine = ConjectureEngine(seed=42)
        result = engine.run_discovery(max_n=50, algebraic_trials=50)
        assert result.total_candidates > 0
        assert result.verified_count >= 0

    def test_score_conjecture(self):
        engine = ConjectureEngine(seed=42)
        conj = Conjecture(
            statement_zh="test", statement_en="test", category="test",
            evidence_count=100, sympy_verified=True, is_known=True,
        )
        score = engine.score_conjecture(conj)
        assert 0 <= score <= 1.0

    def test_format_report(self):
        engine = ConjectureEngine(seed=42)
        result = engine.run_discovery(max_n=30, algebraic_trials=20)
        report = engine.format_report(result)
        assert "Conjecture Discovery" in report
        assert "counterexample" in report.lower() or "反例" in report