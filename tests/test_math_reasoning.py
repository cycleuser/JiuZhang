"""Tests for the math reasoning engine and training data generator."""

import pytest
from unittest.mock import MagicMock, patch

from jiuzhang.core.errors import ToolResult
from jiuzhang.math_reasoning import MathReasoningEngine, MathReasoningResult
from jiuzhang.math_config import MathModelConfig, get_optimal_math_config, MATHEMATICAL_PROMPTING_STRATEGIES
from jiuzhang.train_math_model import MathTrainingDataGenerator


class TestMathReasoningResult:
    def test_defaults(self):
        r = MathReasoningResult(success=True, response="ok", steps=[], verification="", confidence=0.5)
        assert r.symbolic_checks is None
        assert r.self_consistent is None

    def test_with_extras(self):
        r = MathReasoningResult(
            success=True, response="ok", steps=[], verification="",
            confidence=0.5, symbolic_checks=[], self_consistent=True,
        )
        assert r.symbolic_checks == []
        assert r.self_consistent is True


class TestMathModelConfig:
    def test_default_model(self):
        cfg = MathModelConfig()
        assert "deepseek" in cfg.theorem_proving_model or cfg.theorem_proving_model

    def test_get_model_for_task(self):
        cfg = MathModelConfig()
        m = cfg.get_model_for_task("theorem_proving")
        assert m == cfg.theorem_proving_model

    def test_unknown_task(self):
        cfg = MathModelConfig()
        m = cfg.get_model_for_task("unknown_task")
        assert m == cfg.theorem_proving_model

    def test_reasoning_params_proofs(self):
        cfg = MathModelConfig()
        p = cfg.get_reasoning_params("theorem_proving")
        assert p["temperature"] <= 0.1

    def test_reasoning_params_conjecture(self):
        cfg = MathModelConfig()
        p = cfg.get_reasoning_params("conjecture_analysis")
        assert p["temperature"] > 0.1


class TestMathReasoningEngine:
    def _make_engine(self, return_data="Test response"):
        client = MagicMock()
        client.send_message.return_value = ToolResult(success=True, data=return_data)
        config = MagicMock()
        config.active_provider = "ollama"
        config.active_model = "test"
        return MathReasoningEngine(client, config)

    def test_prove_theorem_success(self):
        eng = self._make_engine("Step 1: Assume. Step 2: Therefore. Q.E.D.")
        r = eng.prove_theorem("Pythagorean theorem")
        assert r.success
        assert r.symbolic_checks is not None

    def test_solve_problem_success(self):
        eng = self._make_engine("Answer: x = 5. Verify: 3*5+7=22.")
        r = eng.solve_problem("Solve 3x+7=22")
        assert r.success
        assert r.symbolic_checks is not None

    def test_symbolic_computation_success(self):
        eng = self._make_engine("Result: f'(x) = 3x^2. Step by step done.")
        r = eng.symbolic_computation("differentiate x^3")
        assert r.success
        assert r.symbolic_checks is not None

    def test_engine_failure(self):
        client = MagicMock()
        client.send_message.return_value = ToolResult(success=False, error="LLM down")
        config = MagicMock()
        eng = MathReasoningEngine(client, config)
        r = eng.prove_theorem("test")
        assert not r.success
        assert r.error == "LLM down"

    def test_extract_proof_steps(self):
        eng = self._make_engine()
        steps = eng._extract_proof_steps("1. First step\n2. Second step\n3. Third step")
        assert len(steps) >= 1

    def test_calculate_confidence(self):
        eng = self._make_engine()
        c = eng._calculate_confidence("short", "Verification: 2/5 indicators")
        assert 0.0 <= c <= 1.0

    def test_self_consistency_disabled(self):
        assert MATHEMATICAL_PROMPTING_STRATEGIES["self_consistency"]["enabled"] is False


class TestMathTrainingDataGenerator:
    def test_algebra_samples(self):
        gen = MathTrainingDataGenerator()
        samples = gen.generate_algebra_samples(5)
        assert len(samples) >= 5

    def test_calculus_samples(self):
        gen = MathTrainingDataGenerator()
        samples = gen.generate_calculus_samples(5)
        assert len(samples) >= 5

    def test_proof_samples(self):
        gen = MathTrainingDataGenerator()
        samples = gen.generate_proof_samples(30)
        assert len(samples) >= 4

    def test_geometry_samples(self):
        gen = MathTrainingDataGenerator()
        samples = gen.generate_geometric_samples(5)
        assert len(samples) >= 5

    def test_number_theory_samples(self):
        gen = MathTrainingDataGenerator()
        samples = gen.generate_number_theory_samples(8)
        assert len(samples) >= 8
        assert all(s.category == "number_theory" for s in samples)

    def test_analysis_samples(self):
        gen = MathTrainingDataGenerator()
        samples = gen.generate_analysis_samples(6)
        assert len(samples) >= 6
        assert all(s.category == "analysis" for s in samples)

    def test_linear_algebra_samples(self):
        gen = MathTrainingDataGenerator()
        samples = gen.generate_linear_algebra_samples(6)
        assert len(samples) >= 6
        assert all(s.category == "linear_algebra" for s in samples)

    def test_full_dataset(self):
        gen = MathTrainingDataGenerator()
        data = gen.generate_training_dataset({
            "algebra": 10, "calculus": 6, "proofs": 3,
            "geometry": 8, "number_theory": 4,
            "analysis": 3, "linear_algebra": 3,
        })
        assert len(data) >= 10
        for entry in data:
            assert "messages" in entry
            assert len(entry["messages"]) == 3