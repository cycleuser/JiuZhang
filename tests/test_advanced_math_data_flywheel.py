"""Tests for JiuZhang Advanced Math Data Flywheel."""

import pytest
import json
import os
import tempfile
from pathlib import Path

import sympy as sp
from sympy import symbols, Eq, sin, cos, exp, diff, integrate, simplify

from jiuzhang.math_data_flywheel import (
    MathProblem,
    ModelResponse,
    FlywheelSample,
    DifficultyLevel,
)

from jiuzhang.advanced_math_data_flywheel import (
    CrossConceptGenerator,
    StepVerifier,
    DifficultyTracker,
    DataDeduplicator,
    QualityScorer,
    MergedDatasetExporter,
    AdvancedMathDataFlywheel,
)


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def sample_problem():
    x = symbols('x')
    return MathProblem(
        id="test_1",
        category="calculus",
        difficulty=DifficultyLevel.INTERMEDIATE,
        instruction_zh="求导数",
        instruction_en="Find the derivative",
        input_zh="f(x) = x³",
        input_en="f(x) = x³",
        answer_zh="f'(x) = 3*x²",
        answer_en="f'(x) = 3*x²",
        sympy_expression="diff(x**3, x) = 3*x**2",
        solution_steps=[
            "Apply power rule",
            "f'(x) = 3*x²",
        ],
    )


@pytest.fixture
def sample_sample(sample_problem):
    return FlywheelSample(
        problem=sample_problem,
        source="error_expansion",
        parent_problem_id="parent_1",
        difficulty_increase=0.3,
        verification_methods=["sympy_verified", "numerical_verified"],
        verification_consensus=True,
    )


# ── Cross-Concept Generator Tests ────────────────────────────────────

class TestCrossConceptGenerator:
    def test_generate_optimization(self):
        gen = CrossConceptGenerator(seed=42)
        problem = gen._gen_optimization(gen.rng)
        
        assert problem.category == "calculus"
        assert problem.difficulty == DifficultyLevel.ADVANCED
        assert "cross_optim" in problem.id
        assert problem.solution_steps is not None
        assert len(problem.solution_steps) >= 3

    def test_generate_area_integral(self):
        gen = CrossConceptGenerator(seed=42)
        problem = gen._gen_area_integral(gen.rng)
        
        assert problem.category == "calculus"
        assert problem.difficulty == DifficultyLevel.ADVANCED
        assert "cross_area" in problem.id
        assert "integrate" in problem.sympy_expression

    def test_generate_probability_algebra(self):
        gen = CrossConceptGenerator(seed=42)
        problem = gen._gen_probability_algebra(gen.rng)
        
        assert problem.category == "probability"
        assert problem.difficulty == DifficultyLevel.ADVANCED
        assert "cross_prob" in problem.id
        assert "binomial" in problem.sympy_expression

    def test_generate_sequence_limit(self):
        gen = CrossConceptGenerator(seed=42)
        problem = gen._gen_sequence_limit(gen.rng)
        
        assert problem.category == "calculus"
        assert problem.difficulty == DifficultyLevel.ADVANCED
        assert "cross_seq_lim" in problem.id
        assert "limit" in problem.sympy_expression

    def test_generate_cross_concept_multiple(self):
        gen = CrossConceptGenerator(seed=42)
        problems = gen.generate_cross_concept(count=5)
        
        assert len(problems) == 5
        for problem in problems:
            assert problem.difficulty == DifficultyLevel.ADVANCED
            assert problem.solution_steps is not None

    def test_cross_concept_unique_ids(self):
        gen = CrossConceptGenerator(seed=42)
        problems = gen.generate_cross_concept(count=10)
        
        ids = [p.id for p in problems]
        assert len(ids) == len(set(ids))  # All unique


# ── Step Verifier Tests ──────────────────────────────────────────────

class TestStepVerifier:
    def test_verify_correct_step(self):
        verifier = StepVerifier()
        verified, detail = verifier.verify_step("f'(x) = 3*x**2", "diff(x**3, x) = 3*x**2")
        
        assert verified is True

    def test_verify_incorrect_step(self):
        verifier = StepVerifier()
        verified, detail = verifier.verify_step("f'(x) = 2*x**2", "diff(x**3, x) = 3*x**2")
        
        assert verified is False
        assert "mismatch" in detail

    def test_verify_step_no_expected(self):
        verifier = StepVerifier()
        verified, detail = verifier.verify_step("some step text", None)
        
        assert verified is True

    def test_verify_solution_steps(self, sample_problem):
        verifier = StepVerifier()
        all_verified, results = verifier.verify_solution_steps(sample_problem)
        
        assert len(results) == len(sample_problem.solution_steps)
        # Steps may or may not verify depending on content, but should not crash

    def test_verify_empty_steps(self):
        verifier = StepVerifier()
        problem = MathProblem(
            id="test_no_steps",
            category="algebra",
            difficulty=DifficultyLevel.ELEMENTARY,
            instruction_zh="test",
            instruction_en="test",
            input_zh="1+1=?",
            input_en="1+1=?",
            answer_zh="2",
            answer_en="2",
        )
        
        all_verified, results = verifier.verify_solution_steps(problem)
        assert all_verified is True
        assert results == ["no_steps_to_verify"]


# ── Difficulty Tracker Tests ─────────────────────────────────────────

class TestDifficultyTracker:
    def test_record_round(self):
        tracker = DifficultyTracker()
        samples = [
            FlywheelSample(
                problem=MathProblem(id="1", category="calc", difficulty=DifficultyLevel.INTERMEDIATE,
                                   instruction_zh="", instruction_en="", input_zh="", input_en="",
                                   answer_zh="", answer_en=""),
                source="error_expansion",
                difficulty_increase=0.3,
            ),
            FlywheelSample(
                problem=MathProblem(id="2", category="calc", difficulty=DifficultyLevel.INTERMEDIATE,
                                   instruction_zh="", instruction_en="", input_zh="", input_en="",
                                   answer_zh="", answer_en=""),
                source="persona_injection",
                difficulty_increase=0.0,
            ),
        ]
        
        tracker.record_round(1, samples)
        
        assert 1 in tracker.round_difficulties
        assert tracker.round_difficulties[1]["avg"] == 0.15
        assert tracker.round_difficulties[1]["max"] == 0.3
        assert tracker.round_difficulties[1]["min"] == 0.0

    def test_record_empty_round(self):
        tracker = DifficultyTracker()
        tracker.record_round(1, [])
        
        assert 1 not in tracker.round_difficulties

    def test_progression_report(self):
        tracker = DifficultyTracker()
        
        # Round 1
        samples1 = [FlywheelSample(
            problem=MathProblem(id="1", category="calc", difficulty=DifficultyLevel.INTERMEDIATE,
                               instruction_zh="", instruction_en="", input_zh="", input_en="",
                               answer_zh="", answer_en=""),
            source="error_expansion",
            difficulty_increase=0.2,
        )]
        tracker.record_round(1, samples1)
        
        # Round 2
        samples2 = [FlywheelSample(
            problem=MathProblem(id="2", category="calc", difficulty=DifficultyLevel.INTERMEDIATE,
                               instruction_zh="", instruction_en="", input_zh="", input_en="",
                               answer_zh="", answer_en=""),
            source="error_expansion",
            difficulty_increase=0.4,
        )]
        tracker.record_round(2, samples2)
        
        report = tracker.get_progression_report()
        
        assert "rounds" in report
        assert "category_progression" in report
        assert "trend" in report

    def test_trend_steady_increase(self):
        tracker = DifficultyTracker()
        
        for i in range(3):
            samples = [FlywheelSample(
                problem=MathProblem(id=str(i), category="calc", difficulty=DifficultyLevel.INTERMEDIATE,
                                   instruction_zh="", instruction_en="", input_zh="", input_en="",
                                   answer_zh="", answer_en=""),
                source="error_expansion",
                difficulty_increase=0.1 * (i + 1),
            )]
            tracker.record_round(i + 1, samples)
        
        report = tracker.get_progression_report()
        assert report["trend"] == "steady_increase"

    def test_should_increase_difficulty(self):
        tracker = DifficultyTracker()
        
        # Low difficulty increase
        samples = [FlywheelSample(
            problem=MathProblem(id="1", category="calc", difficulty=DifficultyLevel.INTERMEDIATE,
                               instruction_zh="", instruction_en="", input_zh="", input_en="",
                               answer_zh="", answer_en=""),
            source="error_expansion",
            difficulty_increase=0.1,
        )]
        tracker.record_round(1, samples)
        
        assert tracker.should_increase_difficulty(1) is True

    def test_should_not_increase_difficulty(self):
        tracker = DifficultyTracker()
        
        # High difficulty increase
        samples = [FlywheelSample(
            problem=MathProblem(id="1", category="calc", difficulty=DifficultyLevel.INTERMEDIATE,
                               instruction_zh="", instruction_en="", input_zh="", input_en="",
                               answer_zh="", answer_en=""),
            source="error_expansion",
            difficulty_increase=0.5,
        )]
        tracker.record_round(1, samples)
        
        assert tracker.should_increase_difficulty(1) is False


# ── Data Deduplicator Tests ──────────────────────────────────────────

class TestDataDeduplicator:
    def test_is_duplicate_first_time(self):
        dedup = DataDeduplicator()
        problem = MathProblem(
            id="test_1",
            category="calc",
            difficulty=DifficultyLevel.INTERMEDIATE,
            instruction_zh="",
            instruction_en="",
            input_zh="1+1=?",
            input_en="1+1=?",
            answer_zh="2",
            answer_en="2",
        )
        
        assert dedup.is_duplicate(problem) is False

    def test_is_duplicate_after_add(self):
        dedup = DataDeduplicator()
        problem = MathProblem(
            id="test_1",
            category="calc",
            difficulty=DifficultyLevel.INTERMEDIATE,
            instruction_zh="",
            instruction_en="",
            input_zh="1+1=?",
            input_en="1+1=?",
            answer_zh="2",
            answer_en="2",
        )
        
        dedup.add_problem(problem)
        assert dedup.is_duplicate(problem) is True

    def test_filter_duplicates(self):
        dedup = DataDeduplicator()
        
        problems = [
            MathProblem(id="1", category="calc", difficulty=DifficultyLevel.INTERMEDIATE,
                       instruction_zh="", instruction_en="", input_zh="1+1=?", input_en="1+1=?",
                       answer_zh="2", answer_en="2"),
            MathProblem(id="2", category="calc", difficulty=DifficultyLevel.INTERMEDIATE,
                       instruction_zh="", instruction_en="", input_zh="1+1=?", input_en="1+1=?",
                       answer_zh="2", answer_en="2"),  # Duplicate
            MathProblem(id="3", category="calc", difficulty=DifficultyLevel.INTERMEDIATE,
                       instruction_zh="", instruction_en="", input_zh="2+2=?", input_en="2+2=?",
                       answer_zh="4", answer_en="4"),
        ]
        
        unique = dedup.filter_duplicates(problems)
        assert len(unique) == 2

    def test_get_stats(self):
        dedup = DataDeduplicator()
        problem = MathProblem(
            id="test_1",
            category="calc",
            difficulty=DifficultyLevel.INTERMEDIATE,
            instruction_zh="",
            instruction_en="",
            input_zh="1+1=?",
            input_en="1+1=?",
            answer_zh="2",
            answer_en="2",
        )
        
        dedup.add_problem(problem)
        stats = dedup.get_stats()
        
        assert stats["total_seen"] == 1


# ── Quality Scorer Tests ─────────────────────────────────────────────

class TestQualityScorer:
    def test_score_high_quality(self, sample_sample):
        scorer = QualityScorer()
        score = scorer.score_sample(sample_sample)
        
        assert 0.0 <= score <= 1.0
        # Should be relatively high due to 2 verification methods and 0.3 difficulty increase
        assert score >= 0.5

    def test_score_low_quality(self):
        problem = MathProblem(
            id="test_low",
            category="calc",
            difficulty=DifficultyLevel.ELEMENTARY,
            instruction_zh="",
            instruction_en="",
            input_zh="",
            input_en="",
            answer_zh="",
            answer_en="",
        )
        sample = FlywheelSample(
            problem=problem,
            source="curriculum",
            difficulty_increase=0.0,
            verification_methods=["curriculum_verified"],
        )
        
        scorer = QualityScorer()
        score = scorer.score_sample(sample)
        
        assert 0.0 <= score <= 1.0

    def test_score_all_sorted(self, sample_sample):
        scorer = QualityScorer()
        
        problem2 = MathProblem(
            id="test_2",
            category="calc",
            difficulty=DifficultyLevel.ADVANCED,
            instruction_zh="",
            instruction_en="",
            input_zh="",
            input_en="",
            answer_zh="",
            answer_en="",
        )
        sample2 = FlywheelSample(
            problem=problem2,
            source="cross_concept",
            difficulty_increase=0.4,
            verification_methods=["sympy", "numerical", "step_verify"],
        )
        
        scored = scorer.score_all([sample_sample, sample2])
        
        # Should be sorted by score descending
        assert len(scored) == 2
        assert scored[0][1] >= scored[1][1]


# ── Merged Dataset Exporter Tests ────────────────────────────────────

class TestMergedDatasetExporter:
    def test_export_merged_basic(self, tmp_path):
        exporter = MergedDatasetExporter()
        
        curriculum = [FlywheelSample(
            problem=MathProblem(id="curr_1", category="calc", difficulty=DifficultyLevel.INTERMEDIATE,
                               instruction_zh="test", instruction_en="test", input_zh="1+1=?", input_en="1+1=?",
                               answer_zh="2", answer_en="2"),
            source="curriculum",
            difficulty_increase=0.0,
            verification_methods=["curriculum_verified"],
        )]
        
        flywheel = [FlywheelSample(
            problem=MathProblem(id="fw_1", category="calc", difficulty=DifficultyLevel.INTERMEDIATE,
                               instruction_zh="test", instruction_en="test", input_zh="2+2=?", input_en="2+2=?",
                               answer_zh="4", answer_en="4"),
            source="error_expansion",
            difficulty_increase=0.3,
            verification_methods=["sympy_verified"],
        )]
        
        output_file = str(tmp_path / "merged.jsonl")
        filtered = exporter.export_merged(
            curriculum_samples=curriculum,
            flywheel_samples=flywheel,
            output_path=output_file,
        )
        
        assert os.path.exists(output_file)
        assert len(filtered) == 2

    def test_export_merged_with_quality_filter(self, tmp_path):
        exporter = MergedDatasetExporter()
        
        # Low quality sample
        low_quality = FlywheelSample(
            problem=MathProblem(id="low_1", category="calc", difficulty=DifficultyLevel.ELEMENTARY,
                               instruction_zh="低质量测试", instruction_en="low quality test", input_zh="1+1=?", input_en="1+1=?",
                               answer_zh="2", answer_en="2"),
            source="curriculum",
            difficulty_increase=0.0,
            verification_methods=["curriculum_verified"],
        )
        
        # High quality sample
        high_quality = FlywheelSample(
            problem=MathProblem(id="high_1", category="calc", difficulty=DifficultyLevel.ADVANCED,
                               instruction_zh="高质量测试", instruction_en="high quality test", input_zh="求导数", input_en="find derivative",
                               answer_zh="f'(x) = 3x²", answer_en="f'(x) = 3x²"),
            source="cross_concept",
            difficulty_increase=0.5,
            verification_methods=["sympy", "numerical", "step_verify"],
        )
        
        # Score both to understand threshold
        scorer = QualityScorer()
        low_score = scorer.score_sample(low_quality)
        high_score = scorer.score_sample(high_quality)
        
        # Use a threshold below the high score but above the low score
        threshold = low_score + (high_score - low_score) * 0.5
        
        output_file = str(tmp_path / "merged_filtered.jsonl")
        filtered = exporter.export_merged(
            curriculum_samples=[low_quality],
            flywheel_samples=[high_quality],
            output_path=output_file,
            min_quality_score=threshold,
        )
        
        # Should filter out low quality, keep high quality
        assert len(filtered) == 1
        assert filtered[0][0].problem.id == "high_1"

    def test_export_merged_deduplication(self, tmp_path):
        exporter = MergedDatasetExporter()
        
        # Two identical samples
        problem = MathProblem(id="dup_1", category="calc", difficulty=DifficultyLevel.INTERMEDIATE,
                             instruction_zh="", instruction_en="", input_zh="1+1=?", input_en="1+1=?",
                             answer_zh="2", answer_en="2")
        
        sample1 = FlywheelSample(problem=problem, source="curriculum", difficulty_increase=0.0,
                                verification_methods=["curriculum_verified"])
        sample2 = FlywheelSample(problem=problem, source="error_expansion", difficulty_increase=0.3,
                                verification_methods=["sympy_verified"])
        
        output_file = str(tmp_path / "merged_dedup.jsonl")
        filtered = exporter.export_merged(
            curriculum_samples=[sample1],
            flywheel_samples=[sample2],
            output_path=output_file,
        )
        
        # Should deduplicate
        assert len(filtered) == 1


# ── Advanced Math Data Flywheel Tests ────────────────────────────────

class TestAdvancedMathDataFlywheel:
    def test_generate_initial_data(self):
        flywheel = AdvancedMathDataFlywheel(seed=42)
        samples = flywheel.generate_initial_data(counts={1: 20, 2: 15, 3: 10, 4: 5})
        
        assert len(samples) > 0
        assert flywheel.round_count == 0

    def test_generate_next_round_with_cross_concept(self):
        flywheel = AdvancedMathDataFlywheel(seed=42)
        flywheel.generate_initial_data(counts={1: 10, 2: 10, 3: 5, 4: 5})
        
        # Record errors
        for sample in flywheel.all_generated[:5]:
            flywheel.record_errors([
                (sample.problem, ModelResponse(
                    problem_id=sample.problem.id,
                    response_zh="错误",
                    response_en="wrong",
                    is_correct=False,
                    error_type="calculation",
                ))
            ])
        
        new_samples = flywheel.generate_next_round(
            generate_cross_concept=True,
            max_new_samples=50,
        )
        
        assert flywheel.round_count == 1
        assert len(new_samples) > 0
        
        # Should have cross-concept samples
        sources = set(s.source for s in new_samples)
        assert "cross_concept" in sources

    def test_generate_next_round_no_errors_cross_concept_only(self):
        flywheel = AdvancedMathDataFlywheel(seed=42)
        flywheel.generate_initial_data(counts={1: 10, 2: 10, 3: 5, 4: 5})
        
        # Don't record errors
        new_samples = flywheel.generate_next_round(
            generate_cross_concept=True,
            max_new_samples=20,
        )
        
        # Should still generate cross-concept data
        assert len(new_samples) > 0
        assert all(s.source == "cross_concept" for s in new_samples)

    def test_deduplication_across_rounds(self):
        flywheel = AdvancedMathDataFlywheel(seed=42)
        flywheel.generate_initial_data(counts={1: 10, 2: 10, 3: 5, 4: 5})
        
        # Record errors for round 1
        for sample in flywheel.all_generated[:5]:
            flywheel.record_errors([
                (sample.problem, ModelResponse(
                    problem_id=sample.problem.id,
                    response_zh="错误",
                    response_en="wrong",
                    is_correct=False,
                    error_type="calculation",
                ))
            ])
        
        round1_samples = flywheel.generate_next_round(max_new_samples=30)
        
        # Record errors for round 2
        for sample in flywheel.all_generated[-5:]:
            flywheel.record_errors([
                (sample.problem, ModelResponse(
                    problem_id=sample.problem.id,
                    response_zh="错误",
                    response_en="wrong",
                    is_correct=False,
                    error_type="concept",
                ))
            ])
        
        round2_samples = flywheel.generate_next_round(max_new_samples=30)
        
        # Check no duplicates across rounds
        all_ids = [s.problem.id for s in flywheel.all_generated]
        assert len(all_ids) == len(set(all_ids))

    def test_difficulty_tracking(self):
        flywheel = AdvancedMathDataFlywheel(seed=42)
        flywheel.generate_initial_data(counts={1: 10, 2: 10, 3: 5, 4: 5})
        
        # Run 3 rounds
        for round_num in range(3):
            for sample in flywheel.all_generated[:3]:
                flywheel.record_errors([
                    (sample.problem, ModelResponse(
                        problem_id=sample.problem.id,
                        response_zh="错误",
                        response_en="wrong",
                        is_correct=False,
                        error_type="calculation",
                    ))
                ])
            flywheel.generate_next_round(max_new_samples=20)
        
        stats = flywheel.get_advanced_stats()
        assert "difficulty_progression" in stats
        assert len(stats["difficulty_progression"]["rounds"]) == 3

    def test_quality_distribution(self):
        flywheel = AdvancedMathDataFlywheel(seed=42)
        samples = flywheel.generate_initial_data(counts={1: 10, 2: 10, 3: 5, 4: 5})
        
        stats = flywheel.get_advanced_stats()
        assert "quality_distribution" in stats
        assert "avg" in stats["quality_distribution"]
        assert "max" in stats["quality_distribution"]
        assert "min" in stats["quality_distribution"]

    def test_export_merged_dataset(self, tmp_path):
        flywheel = AdvancedMathDataFlywheel(seed=42)
        flywheel.generate_initial_data(counts={1: 10, 2: 10, 3: 5, 4: 5})
        
        output_file = str(tmp_path / "advanced_merged.jsonl")
        filtered = flywheel.export_merged_dataset(
            output_path=output_file,
            min_quality_score=0.0,
        )
        
        assert os.path.exists(output_file)
        assert len(filtered) > 0

    def test_export_merged_dataset_with_quality_filter(self, tmp_path):
        flywheel = AdvancedMathDataFlywheel(seed=42)
        flywheel.generate_initial_data(counts={1: 10, 2: 10, 3: 5, 4: 5})
        
        # Run one round to get higher quality samples
        for sample in flywheel.all_generated[:5]:
            flywheel.record_errors([
                (sample.problem, ModelResponse(
                    problem_id=sample.problem.id,
                    response_zh="错误",
                    response_en="wrong",
                    is_correct=False,
                    error_type="calculation",
                ))
            ])
        flywheel.generate_next_round(max_new_samples=20)
        
        output_file = str(tmp_path / "advanced_merged_filtered.jsonl")
        filtered = flywheel.export_merged_dataset(
            output_path=output_file,
            min_quality_score=0.5,
        )
        
        # All samples should have quality >= 0.5
        for sample, score in filtered:
            assert score >= 0.5

    def test_advanced_stats_comprehensive(self):
        flywheel = AdvancedMathDataFlywheel(seed=42)
        flywheel.generate_initial_data(counts={1: 10, 2: 10, 3: 5, 4: 5})
        
        stats = flywheel.get_advanced_stats()
        
        # Base stats
        assert "total_samples" in stats
        assert "rounds_completed" in stats
        assert "by_source" in stats
        assert "by_category" in stats
        assert "by_difficulty" in stats
        
        # Advanced stats
        assert "deduplication" in stats
        assert "difficulty_progression" in stats
        assert "quality_distribution" in stats

    def test_multiple_rounds_integration(self):
        flywheel = AdvancedMathDataFlywheel(seed=42)
        flywheel.generate_initial_data(counts={1: 20, 2: 15, 3: 10, 4: 5})
        
        # Run 3 rounds with different error patterns
        error_types = ["calculation", "concept", "reasoning"]
        for round_num in range(3):
            error_count = min(5 + round_num * 3, len(flywheel.all_generated))
            for sample in flywheel.all_generated[:error_count]:
                flywheel.record_errors([
                    (sample.problem, ModelResponse(
                        problem_id=sample.problem.id,
                        response_zh="错误",
                        response_en="wrong",
                        is_correct=False,
                        error_type=error_types[round_num],
                    ))
                ])
            
            new_samples = flywheel.generate_next_round(max_new_samples=30)
            assert len(new_samples) > 0
        
        assert flywheel.round_count == 3
        
        # Verify no duplicates
        all_ids = [s.problem.id for s in flywheel.all_generated]
        assert len(all_ids) == len(set(all_ids))
        
        # Verify quality distribution exists
        stats = flywheel.get_advanced_stats()
        assert stats["quality_distribution"]["avg"] > 0


# ── Edge Case Tests ──────────────────────────────────────────────────

class TestAdvancedEdgeCases:
    def test_cross_concept_generator_deterministic(self):
        gen1 = CrossConceptGenerator(seed=42)
        gen2 = CrossConceptGenerator(seed=42)
        
        problems1 = gen1.generate_cross_concept(count=5)
        problems2 = gen2.generate_cross_concept(count=5)
        
        ids1 = [p.id for p in problems1]
        ids2 = [p.id for p in problems2]
        
        assert ids1 == ids2

    def test_step_verifier_with_invalid_expression(self):
        verifier = StepVerifier()
        verified, detail = verifier.verify_step("f'(x) = invalid_expr", "diff(x**3, x) = 3*x**2")
        
        # Should handle gracefully
        assert isinstance(verified, bool)

    def test_difficulty_tracker_empty_report(self):
        tracker = DifficultyTracker()
        report = tracker.get_progression_report()
        
        assert report["trend"] == "insufficient_data"

    def test_deduplicator_hash_consistency(self):
        dedup = DataDeduplicator()
        problem = MathProblem(
            id="test_hash",
            category="calc",
            difficulty=DifficultyLevel.INTERMEDIATE,
            instruction_zh="",
            instruction_en="",
            input_zh="1+1=?",
            input_en="1+1=?",
            answer_zh="2",
            answer_en="2",
        )
        
        h1 = dedup._compute_hash(problem)
        h2 = dedup._compute_hash(problem)
        
        assert h1 == h2

    def test_quality_scorer_bounds(self):
        scorer = QualityScorer()
        
        # Create extreme cases
        low_sample = FlywheelSample(
            problem=MathProblem(id="low", category="calc", difficulty=DifficultyLevel.ELEMENTARY,
                               instruction_zh="", instruction_en="", input_zh="", input_en="",
                               answer_zh="", answer_en=""),
            source="curriculum",
            difficulty_increase=0.0,
            verification_methods=["one"],
        )
        
        high_sample = FlywheelSample(
            problem=MathProblem(id="high", category="calc", difficulty=DifficultyLevel.ADVANCED,
                               instruction_zh="", instruction_en="", input_zh="", input_en="",
                               answer_zh="", answer_en=""),
            source="cross_concept",
            difficulty_increase=0.5,
            verification_methods=["sympy", "numerical", "step_verify"],
        )
        
        low_score = scorer.score_sample(low_sample)
        high_score = scorer.score_sample(high_sample)
        
        assert 0.0 <= low_score <= 1.0
        assert 0.0 <= high_score <= 1.0
        assert high_score > low_score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
