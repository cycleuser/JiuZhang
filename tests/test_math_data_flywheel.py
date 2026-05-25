"""Tests for JiuZhang Math Data Flywheel."""

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
    ErrorCollector,
    HardExampleGenerator,
    PersonaInjector,
    BehaviorTreeExpander,
    AdversarialGenerator,
    ConsistencyFilter,
    MathDataFlywheel,
)


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def sample_derivative_problem():
    x = symbols('x')
    return MathProblem(
        id="test_deriv_1",
        category="calculus",
        difficulty=DifficultyLevel.INTERMEDIATE,
        instruction_zh="求导数",
        instruction_en="Find the derivative",
        input_zh="f(x) = x³",
        input_en="f(x) = x³",
        answer_zh="f'(x) = 3*x²",
        answer_en="f'(x) = 3*x²",
        sympy_expression="diff(x**3, x) = 3*x**2",
        solution_steps=["Apply power rule", "f'(x) = 3*x²"],
    )


@pytest.fixture
def sample_equation_problem():
    x = symbols('x')
    return MathProblem(
        id="test_eq_1",
        category="algebra",
        difficulty=DifficultyLevel.INTERMEDIATE,
        instruction_zh="解方程",
        instruction_en="Solve the equation",
        input_zh="2x + 3 = 7",
        input_en="2x + 3 = 7",
        answer_zh="x = 2",
        answer_en="x = 2",
        sympy_expression="solve(2*x + 3 = 0)",
        solution_steps=["Subtract 3 from both sides", "Divide by 2", "x = 2"],
    )


@pytest.fixture
def sample_wrong_response():
    return ModelResponse(
        problem_id="test_deriv_1",
        response_zh="f'(x) = 2*x²",
        response_en="f'(x) = 2*x²",
        is_correct=False,
        error_type="calculation",
        confidence=0.3,
    )


@pytest.fixture
def sample_correct_response():
    return ModelResponse(
        problem_id="test_deriv_1",
        response_zh="f'(x) = 3*x²",
        response_en="f'(x) = 3*x²",
        is_correct=True,
        error_type=None,
        confidence=0.95,
    )


# ── Error Collector Tests ────────────────────────────────────────────

class TestErrorCollector:
    def test_record_error(self, sample_derivative_problem, sample_wrong_response):
        collector = ErrorCollector()
        collector.record_error(sample_derivative_problem, sample_wrong_response)
        
        assert len(collector.errors) == 1
        assert collector.error_stats["calculation"] == 1

    def test_ignore_correct_response(self, sample_derivative_problem, sample_correct_response):
        collector = ErrorCollector()
        collector.record_error(sample_derivative_problem, sample_correct_response)
        
        assert len(collector.errors) == 0

    def test_get_errors_by_category(self, sample_derivative_problem, sample_wrong_response):
        collector = ErrorCollector()
        collector.record_error(sample_derivative_problem, sample_wrong_response)
        
        errors = collector.get_errors_by_category("calculus")
        assert len(errors) == 1

    def test_get_most_frequent_error_type(self, sample_derivative_problem):
        collector = ErrorCollector()
        
        # Add multiple errors of different types
        for i in range(3):
            collector.record_error(
                sample_derivative_problem,
                ModelResponse(
                    problem_id=sample_derivative_problem.id,
                    response_zh="wrong",
                    response_en="wrong",
                    is_correct=False,
                    error_type="calculation",
                )
            )
        
        collector.record_error(
            sample_derivative_problem,
            ModelResponse(
                problem_id=sample_derivative_problem.id,
                response_zh="wrong",
                response_en="wrong",
                is_correct=False,
                error_type="concept",
            )
        )
        
        assert collector.get_most_frequent_error_type() == "calculation"

    def test_get_stats(self, sample_derivative_problem, sample_wrong_response):
        collector = ErrorCollector()
        collector.record_error(sample_derivative_problem, sample_wrong_response)
        
        stats = collector.get_stats()
        assert stats["total_errors"] == 1
        assert "by_type" in stats
        assert "by_category" in stats


# ── Hard Example Generator Tests ─────────────────────────────────────

class TestHardExampleGenerator:
    def test_expand_derivative_problem(self, sample_derivative_problem):
        generator = HardExampleGenerator(seed=42)
        harder = generator.expand_derivative_problem(sample_derivative_problem, count=4)
        
        assert len(harder) > 0
        for problem in harder:
            assert problem.category == "calculus"
            assert problem.difficulty == DifficultyLevel.INTERMEDIATE
            assert problem.sympy_expression is not None

    def test_expand_equation_problem(self, sample_equation_problem):
        generator = HardExampleGenerator(seed=42)
        harder = generator.expand_equation_problem(sample_equation_problem, count=4)
        
        assert len(harder) > 0
        for problem in harder:
            assert problem.category == "algebra"

    def test_expand_integral_problem(self, sample_derivative_problem):
        generator = HardExampleGenerator(seed=42)
        harder = generator.expand_integral_problem(sample_derivative_problem, count=4)
        
        assert len(harder) > 0
        for problem in harder:
            assert problem.category == "calculus"

    def test_generate_from_errors(self, sample_derivative_problem, sample_wrong_response):
        generator = HardExampleGenerator(seed=42)
        errors = [(sample_derivative_problem, sample_wrong_response)]
        
        harder = generator.generate_from_errors(errors, count_per_error=2)
        assert len(harder) > 0

    def test_different_problems_generated(self, sample_derivative_problem, sample_wrong_response):
        generator = HardExampleGenerator(seed=42)
        errors = [(sample_derivative_problem, sample_wrong_response)]
        
        harder = generator.generate_from_errors(errors, count_per_error=3)
        
        # Check that generated problems have unique IDs
        ids = [p.id for p in harder]
        assert len(ids) == len(set(ids))


# ── Persona Injector Tests ───────────────────────────────────────────

class TestPersonaInjector:
    def test_inject_persona(self, sample_derivative_problem):
        injector = PersonaInjector(seed=42)
        persona_problem = injector.inject_persona(sample_derivative_problem, "physics")
        
        assert persona_problem.id.startswith("persona_physics_")
        assert "物理" in persona_problem.instruction_zh or "physicist" in persona_problem.instruction_en.lower()

    def test_inject_all_personas(self, sample_derivative_problem):
        injector = PersonaInjector(seed=42)
        persona_problems = injector.inject_all_personas(sample_derivative_problem)
        
        assert len(persona_problems) == len(injector.PERSONAS)
        
        # Check each persona is represented
        sources = [p.id.split("_")[1] for p in persona_problems]
        for key in injector.PERSONAS:
            assert key in sources

    def test_persona_preserves_answer(self, sample_derivative_problem):
        injector = PersonaInjector(seed=42)
        persona_problem = injector.inject_persona(sample_derivative_problem, "economics")
        
        # The core answer should still be present
        assert sample_derivative_problem.answer_zh in persona_problem.answer_zh or \
               "3*x" in persona_problem.answer_zh  # Part of the answer

    def test_random_persona_selection(self, sample_derivative_problem):
        injector = PersonaInjector(seed=42)
        persona_problem = injector.inject_persona(sample_derivative_problem)
        
        # Should have a persona prefix
        assert persona_problem.id.startswith("persona_")


# ── Behavior Tree Expander Tests ─────────────────────────────────────

class TestBehaviorTreeExpander:
    def test_expand_quadratic_solver(self):
        x = symbols('x')
        base_problem = MathProblem(
            id="test_quad",
            category="algebra",
            difficulty=DifficultyLevel.INTERMEDIATE,
            instruction_zh="解一元二次方程",
            instruction_en="Solve quadratic equation",
            input_zh="x² - 4 = 0",
            input_en="x² - 4 = 0",
            answer_zh="x = 2 或 x = -2",
            answer_en="x = 2 or x = -2",
            sympy_expression="solve(x**2 - 4 = 0)",
        )
        
        expander = BehaviorTreeExpander(seed=42)
        branches = expander.expand_quadratic_solver(base_problem)
        
        assert len(branches) > 0
        
        # Should have problems for different discriminant cases
        has_positive = any("positive" in p.id for p in branches)
        has_zero = any("zero" in p.id for p in branches)
        has_negative = any("negative" in p.id for p in branches)
        
        assert has_positive or has_zero or has_negative  # At least one branch type

    def test_expand_limit_problem(self):
        x = symbols('x')
        base_problem = MathProblem(
            id="test_limit",
            category="calculus",
            difficulty=DifficultyLevel.INTERMEDIATE,
            instruction_zh="求极限",
            instruction_en="Find the limit",
            input_zh="lim(x→0) sin(x)/x",
            input_en="lim(x→0) sin(x)/x",
            answer_zh="1",
            answer_en="1",
            sympy_expression="limit(sin(x)/x, x, 0) = 1",
        )
        
        expander = BehaviorTreeExpander(seed=42)
        branches = expander.expand_limit_problem(base_problem)
        
        assert len(branches) > 0
        
        # Check that different methods are represented
        methods = []
        for p in branches:
            if "lhopital" in p.id:
                methods.append("lhopital")
            elif "factorization" in p.id:
                methods.append("factorization")
            elif "direct" in p.id:
                methods.append("direct")
        
        assert len(methods) > 0

    def test_expand_problem_generic(self, sample_equation_problem):
        expander = BehaviorTreeExpander(seed=42)
        # Generic problem should return empty list (no specific expansion)
        branches = expander.expand_problem(sample_equation_problem)
        assert isinstance(branches, list)


# ── Adversarial Generator Tests ──────────────────────────────────────

class TestAdversarialGenerator:
    def test_generate_adversarial_derivative(self, sample_derivative_problem):
        generator = AdversarialGenerator(seed=42)
        adv_problem = generator.generate_adversarial(sample_derivative_problem)
        
        assert adv_problem.id.startswith("adv_")
        assert "常见错误" in adv_problem.answer_zh or "Common mistake" in adv_problem.answer_en

    def test_generate_adversarial_has_trap(self, sample_derivative_problem):
        generator = AdversarialGenerator(seed=42)
        adv_problem = generator.generate_adversarial(sample_derivative_problem)
        
        # Should have misleading hints in input
        assert "注意" in adv_problem.input_zh or "Note" in adv_problem.input_en or \
               "提示" in adv_problem.input_zh or "Hint" in adv_problem.input_en

    def test_adversarial_preserves_core_problem(self, sample_derivative_problem):
        generator = AdversarialGenerator(seed=42)
        adv_problem = generator.generate_adversarial(sample_derivative_problem)
        
        # Core instruction should be preserved
        assert sample_derivative_problem.instruction_zh == adv_problem.instruction_zh
        assert sample_derivative_problem.instruction_en == adv_problem.instruction_en


# ── Consistency Filter Tests ─────────────────────────────────────────

class TestConsistencyFilter:
    def test_verify_with_sympy_derivative(self, sample_derivative_problem):
        filter = ConsistencyFilter()
        verified, detail = filter.verify_with_sympy(sample_derivative_problem)
        
        assert verified is True

    def test_verify_with_sympy_no_expression(self):
        filter = ConsistencyFilter()
        problem = MathProblem(
            id="test_no_expr",
            category="algebra",
            difficulty=DifficultyLevel.ELEMENTARY,
            instruction_zh="test",
            instruction_en="test",
            input_zh="1+1=?",
            input_en="1+1=?",
            answer_zh="2",
            answer_en="2",
        )
        
        verified, detail = filter.verify_with_sympy(problem)
        assert verified is True  # No expression means pass by default

    def test_verify_consensus(self, sample_derivative_problem):
        filter = ConsistencyFilter()
        consensus, methods = filter.verify_consensus(sample_derivative_problem)
        
        assert consensus is True
        assert len(methods) == 3  # Three verification methods

    def test_verify_consensus_returns_method_details(self, sample_derivative_problem):
        filter = ConsistencyFilter()
        consensus, methods = filter.verify_consensus(sample_derivative_problem)
        
        # Each method should have a name and result
        for method in methods:
            assert ":" in method  # Format: "method_name: result"


# ── Math Data Flywheel Integration Tests ─────────────────────────────

class TestMathDataFlywheel:
    def test_generate_initial_data(self):
        flywheel = MathDataFlywheel(seed=42)
        samples = flywheel.generate_initial_data(counts={1: 20, 2: 15, 3: 10, 4: 5})
        
        assert len(samples) > 0
        assert flywheel.round_count == 0

    def test_record_errors_and_generate_next_round(self):
        flywheel = MathDataFlywheel(seed=42)
        samples = flywheel.generate_initial_data(counts={1: 10, 2: 10, 3: 5, 4: 5})
        
        # Record some errors
        for sample in samples[:5]:
            flywheel.record_errors([
                (sample.problem, ModelResponse(
                    problem_id=sample.problem.id,
                    response_zh="错误",
                    response_en="wrong",
                    is_correct=False,
                    error_type="calculation",
                ))
            ])
        
        # Generate next round
        new_samples = flywheel.generate_next_round(max_new_samples=50)
        
        assert flywheel.round_count == 1
        assert len(new_samples) > 0

    def test_flywheel_multiple_rounds(self):
        flywheel = MathDataFlywheel(seed=42)
        flywheel.generate_initial_data(counts={1: 10, 2: 10, 3: 5, 4: 5})
        
        # Round 1
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
        round1_samples = flywheel.generate_next_round(max_new_samples=20)
        
        # Round 2
        for sample in flywheel.all_generated[-3:]:
            flywheel.record_errors([
                (sample.problem, ModelResponse(
                    problem_id=sample.problem.id,
                    response_zh="错误",
                    response_en="wrong",
                    is_correct=False,
                    error_type="concept",
                ))
            ])
        round2_samples = flywheel.generate_next_round(max_new_samples=20)
        
        assert flywheel.round_count == 2

    def test_export_training_data(self, tmp_path):
        flywheel = MathDataFlywheel(seed=42)
        flywheel.generate_initial_data(counts={1: 10, 2: 10, 3: 5, 4: 5})
        
        output_file = str(tmp_path / "test_flywheel.jsonl")
        flywheel.export_training_data(output_path=output_file, format="chatml")
        
        assert os.path.exists(output_file)
        
        # Verify JSONL format
        with open(output_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) > 0
            for line in lines:
                entry = json.loads(line)
                assert "messages" in entry
                assert len(entry["messages"]) == 3  # system, user, assistant

    def test_export_alpaca_format(self, tmp_path):
        flywheel = MathDataFlywheel(seed=42)
        flywheel.generate_initial_data(counts={1: 5, 2: 5, 3: 3, 4: 2})
        
        output_file = str(tmp_path / "test_flywheel_alpaca.jsonl")
        flywheel.export_training_data(output_path=output_file, format="alpaca")
        
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                entry = json.loads(line)
                assert "instruction" in entry
                assert "input" in entry
                assert "output" in entry

    def test_get_stats(self):
        flywheel = MathDataFlywheel(seed=42)
        flywheel.generate_initial_data(counts={1: 10, 2: 10, 3: 5, 4: 5})
        
        stats = flywheel.get_stats()
        
        assert "total_samples" in stats
        assert "rounds_completed" in stats
        assert "by_source" in stats
        assert "by_category" in stats
        assert "by_difficulty" in stats
        assert "error_collector" in stats
        assert "verification_consensus_rate" in stats
        
        assert stats["total_samples"] > 0
        assert stats["rounds_completed"] == 0

    def test_flywheel_with_all_expansions(self):
        flywheel = MathDataFlywheel(seed=42)
        samples = flywheel.generate_initial_data(counts={1: 10, 2: 10, 3: 5, 4: 5})
        
        # Record errors for different categories
        for sample in samples[:5]:
            flywheel.record_errors([
                (sample.problem, ModelResponse(
                    problem_id=sample.problem.id,
                    response_zh="错误",
                    response_en="wrong",
                    is_correct=False,
                    error_type="calculation",
                ))
            ])
        
        # Generate with all expansions enabled
        new_samples = flywheel.generate_next_round(
            expand_hard=True,
            inject_persona=True,
            expand_behavior_tree=True,
            generate_adversarial=True,
            max_new_samples=100,
        )
        
        # Should have samples from multiple sources
        sources = set(s.source for s in new_samples)
        assert len(sources) >= 1  # At least one source should generate samples

    def test_no_errors_skips_expansion(self):
        flywheel = MathDataFlywheel(seed=42)
        flywheel.generate_initial_data(counts={1: 5, 2: 5, 3: 3, 4: 2})
        
        # Don't record any errors
        new_samples = flywheel.generate_next_round(max_new_samples=50)
        
        assert len(new_samples) == 0

    def test_verify_all_samples_pass_consensus(self):
        flywheel = MathDataFlywheel(seed=42)
        samples = flywheel.generate_initial_data(counts={1: 10, 2: 10, 3: 5, 4: 5})
        
        # All initial curriculum samples should pass consensus
        for sample in samples:
            assert sample.verification_consensus is True


# ── Data Class Tests ─────────────────────────────────────────────────

class TestDataClasses:
    def test_math_problem_creation(self):
        problem = MathProblem(
            id="test_1",
            category="algebra",
            difficulty=DifficultyLevel.ELEMENTARY,
            instruction_zh="测试",
            instruction_en="test",
            input_zh="1+1=?",
            input_en="1+1=?",
            answer_zh="2",
            answer_en="2",
        )
        
        assert problem.id == "test_1"
        assert problem.category == "algebra"
        assert problem.difficulty == DifficultyLevel.ELEMENTARY

    def test_model_response_creation(self):
        response = ModelResponse(
            problem_id="test_1",
            response_zh="2",
            response_en="2",
            is_correct=True,
            confidence=0.95,
        )
        
        assert response.is_correct is True
        assert response.confidence == 0.95

    def test_flywheel_sample_creation(self):
        problem = MathProblem(
            id="test_1",
            category="algebra",
            difficulty=DifficultyLevel.ELEMENTARY,
            instruction_zh="测试",
            instruction_en="test",
            input_zh="1+1=?",
            input_en="1+1=?",
            answer_zh="2",
            answer_en="2",
        )
        
        sample = FlywheelSample(
            problem=problem,
            source="error_expansion",
            parent_problem_id="parent_1",
            difficulty_increase=0.3,
            verification_methods=["sympy", "numerical"],
            verification_consensus=True,
        )
        
        assert sample.source == "error_expansion"
        assert sample.parent_problem_id == "parent_1"
        assert sample.difficulty_increase == 0.3
        assert len(sample.verification_methods) == 2


# ── Edge Case Tests ──────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_error_collector(self):
        collector = ErrorCollector()
        assert collector.get_stats()["total_errors"] == 0
        assert collector.get_most_frequent_error_type() is None

    def test_hard_generator_no_matching_category(self):
        generator = HardExampleGenerator(seed=42)
        problem = MathProblem(
            id="test_unknown",
            category="unknown_category",
            difficulty=DifficultyLevel.ELEMENTARY,
            instruction_zh="test",
            instruction_en="test",
            input_zh="test",
            input_en="test",
            answer_zh="test",
            answer_en="test",
        )
        
        errors = [(problem, ModelResponse(
            problem_id="test_unknown",
            response_zh="wrong",
            response_en="wrong",
            is_correct=False,
            error_type="unknown",
        ))]
        
        harder = generator.generate_from_errors(errors, count_per_error=2)
        # Should fall back to equation expansion for unknown category
        assert len(harder) > 0
        assert all(p.category == "algebra" for p in harder)

    def test_behavior_tree_expander_non_matching_problem(self):
        expander = BehaviorTreeExpander(seed=42)
        problem = MathProblem(
            id="test_non_matching",
            category="arithmetic",
            difficulty=DifficultyLevel.ELEMENTARY,
            instruction_zh="加法",
            instruction_en="addition",
            input_zh="1+2=?",
            input_en="1+2=?",
            answer_zh="3",
            answer_en="3",
        )
        
        branches = expander.expand_problem(problem)
        assert branches == []

    def test_consistency_filter_with_invalid_expression(self):
        filter = ConsistencyFilter()
        problem = MathProblem(
            id="test_invalid",
            category="calculus",
            difficulty=DifficultyLevel.INTERMEDIATE,
            instruction_zh="test",
            instruction_en="test",
            input_zh="test",
            input_en="test",
            answer_zh="test",
            answer_en="test",
            sympy_expression="invalid expression that cannot be parsed",
        )
        
        # Should handle gracefully
        verified, detail = filter.verify_with_sympy(problem)
        # May return False or True depending on parsing, but should not crash
        assert isinstance(verified, bool)

    def test_flywheel_seed_reproducibility(self):
        flywheel1 = MathDataFlywheel(seed=42)
        flywheel2 = MathDataFlywheel(seed=42)
        
        samples1 = flywheel1.generate_initial_data(counts={1: 10, 2: 10, 3: 5, 4: 5})
        samples2 = flywheel2.generate_initial_data(counts={1: 10, 2: 10, 3: 5, 4: 5})
        
        # Same seed should produce same results
        assert len(samples1) == len(samples2)
        for s1, s2 in zip(samples1, samples2):
            assert s1.problem.id == s2.problem.id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
