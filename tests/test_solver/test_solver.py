"""Tests for solver module."""

import pytest

from jiuzhang.solver.method_registry import MethodRegistry, MathMethod, MethodCategory
from jiuzhang.solver.problem_classifier import ProblemClassifier, ClassificationResult, ProblemDomain
from jiuzhang.solver.pipeline import SolverPipeline, SolveResult


class TestMethodRegistry:
    @pytest.fixture
    def registry(self):
        return MethodRegistry()

    def test_register_method(self, registry):
        method = MathMethod(
            id="test_method",
            name="Test",
            name_cn="测试",
            category=MethodCategory.ARITHMETIC,
            description="Test method",
            applicable_problems=["test"],
        )
        registry.register(method)
        assert registry.get("test_method") == method

    def test_get_all_methods(self, registry):
        methods = registry.get_all()
        assert len(methods) > 30

    def test_get_by_category(self, registry):
        arithmetic_methods = registry.get_by_category(MethodCategory.ARITHMETIC)
        assert len(arithmetic_methods) > 0
        assert all(m.category == MethodCategory.ARITHMETIC for m in arithmetic_methods)

    def test_match_methods(self, registry):
        matches = registry.match_methods("2 加 3 等于多少")
        assert len(matches) > 0
        assert matches[0][1] > 0

    def test_match_methods_english(self, registry):
        matches = registry.match_methods("solve x^2 + 2x = 0")
        assert len(matches) > 0

    def test_chain_methods(self, registry):
        chain = registry.chain_methods("2 加 3 等于多少")
        assert len(chain) > 0

    def test_method_match_problem(self, registry):
        method = registry.get("addition")
        assert method is not None
        score = method.match_problem("2 加 3 = ?")
        assert score > 0

    def test_all_categories_have_methods(self, registry):
        for category in MethodCategory:
            methods = registry.get_by_category(category)
            # Some categories may not have methods registered yet
            if category != MethodCategory.OPTIMIZATION:
                assert len(methods) > 0, f"No methods for {category}"


class TestProblemClassifier:
    @pytest.fixture
    def classifier(self):
        return ProblemClassifier()

    def test_classify_arithmetic(self, classifier):
        result = classifier.classify("计算 2 + 3 = ?")
        assert result.domain == ProblemDomain.ARITHMETIC

    def test_classify_algebra(self, classifier):
        result = classifier.classify("解方程 2x + 3 = 7")
        assert result.domain == ProblemDomain.ALGEBRA

    def test_classify_geometry(self, classifier):
        result = classifier.classify("三角形的面积是多少？")
        assert result.domain == ProblemDomain.GEOMETRY

    def test_classify_calculus(self, classifier):
        result = classifier.classify("求导数 d/dx(x^2)")
        assert result.domain == ProblemDomain.CALCULUS

    def test_classify_probability(self, classifier):
        result = classifier.classify("概率是多少？")
        assert result.domain == ProblemDomain.PROBABILITY

    def test_classify_english(self, classifier):
        result = classifier.classify("limit as x approaches 0")
        assert result.domain == ProblemDomain.CALCULUS

    def test_extract_keywords(self, classifier):
        result = classifier.classify("计算导数和积分")
        assert "导数" in result.keywords
        assert "积分" in result.keywords

    def test_extract_entities(self, classifier):
        result = classifier.classify("sin(30°) + cos(45°)")
        assert "functions" in result.entities
        assert "sin" in result.entities["functions"]

    def test_difficulty_estimation(self, classifier):
        easy = classifier.classify("2 + 2 = ?")
        hard = classifier.classify("证明勾股定理并应用到三维空间")
        assert easy.difficulty <= hard.difficulty


class TestSolverPipeline:
    @pytest.fixture
    def pipeline(self):
        return SolverPipeline()

    def test_solve_arithmetic(self, pipeline):
        result = pipeline.solve("2 加 3 等于？")
        assert result.success is True
        assert len(result.steps) > 0

    def test_solve_equation(self, pipeline):
        result = pipeline.solve("解方程 2x + 3 = 7")
        assert result.success is True

    def test_solve_derivative(self, pipeline):
        result = pipeline.solve("求导数 d/dx(x^2)")
        assert result.success is True

    def test_solve_integral(self, pipeline):
        result = pipeline.solve("求积分 ∫x^2 dx")
        assert result.success is True

    def test_solve_limit(self, pipeline):
        result = pipeline.solve("求极限 lim(x→0) sin(x)/x")
        assert result.success is True

    def test_solve_factor(self, pipeline):
        result = pipeline.solve("因式分解 x^2 - 9")
        assert result.success is True

    def test_solve_determinant(self, pipeline):
        result = pipeline.solve("行列式 [[1,2],[3,4]]")
        assert result.success is True

    def test_solve_divisibility(self, pipeline):
        result = pipeline.solve("12 和 18 的最大公约数")
        assert result.success is True

    def test_solve_prime_factorization(self, pipeline):
        result = pipeline.solve("质因数分解 60")
        assert result.success is True

    def test_solve_modular(self, pipeline):
        result = pipeline.solve("17 mod 5")
        assert result.success is True

    def test_solve_trigonometry(self, pipeline):
        result = pipeline.solve("sin(30°)")
        assert result.success is True

    def test_solve_logarithm(self, pipeline):
        result = pipeline.solve("log(100)")
        assert result.success is True

    def test_solve_percentage(self, pipeline):
        result = pipeline.solve("20% of 150")
        assert result.success is True

    def test_solve_combinatorics(self, pipeline):
        result = pipeline.solve("排列组合 C(10, 3)")
        assert result.success is True

    def test_solve_set_ops(self, pipeline):
        result = pipeline.solve("集合 {1,2,3} 和 {2,3,4} 的并集")
        assert result.success is True

    def test_solve_result_explanation(self, pipeline):
        result = pipeline.solve("2 加 3 等于？", language="zh")
        assert result.explanation != ""
        assert "解题过程" in result.explanation

    def test_solve_result_explanation_english(self, pipeline):
        result = pipeline.solve("add 2 and 3", language="en")
        assert "Solution" in result.explanation
