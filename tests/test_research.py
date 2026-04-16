"""Tests for research module."""

import pytest
from jiuzhang.research.literature import LiteratureSearcher
from jiuzhang.research.derivation import MathDeriver
from jiuzhang.research.experiment import ExperimentDesigner
from jiuzhang.research.engine import ResearchEngine, ResearchTopic, ResearchResult


class TestLiteratureSearcher:
    @pytest.fixture
    def searcher(self):
        return LiteratureSearcher()

    def test_search_returns_list(self, searcher):
        results = searcher.search("fourier transform", max_results=3)
        assert isinstance(results, list)

    def test_search_has_paper_structure(self, searcher):
        results = searcher.search("matrix", max_results=2)
        if results and results[0].get("title"):
            paper = results[0]
            assert "title" in paper
            assert "authors" in paper
            assert "summary" in paper
            assert "url" in paper

    def test_generate_review(self, searcher):
        papers = [
            {
                "title": "Test Paper",
                "authors": "Author A",
                "summary": "Abstract",
                "url": "http://test.com",
                "published": "2024-01-01",
                "source": "arXiv",
            }
        ]
        review = searcher.generate_review(papers, "zh")
        assert "文献综述" in review
        assert "Test Paper" in review

    def test_generate_review_english(self, searcher):
        papers = [
            {
                "title": "Test Paper",
                "authors": "Author A",
                "summary": "Abstract",
                "url": "http://test.com",
                "published": "2024-01-01",
                "source": "arXiv",
            }
        ]
        review = searcher.generate_review(papers, "en")
        assert "Literature Review" in review


class TestMathDeriver:
    @pytest.fixture
    def deriver(self):
        return MathDeriver()

    def test_symbolic_computation_derivative(self, deriver):
        result = deriver._symbolic_computation("导数", "zh")
        assert "符号计算" in result
        assert "导数" in result

    def test_symbolic_computation_integral(self, deriver):
        result = deriver._symbolic_computation("积分", "zh")
        assert "符号计算" in result

    def test_symbolic_computation_limit(self, deriver):
        result = deriver._symbolic_computation("极限", "zh")
        assert "符号计算" in result
        assert "lim" in result

    def test_symbolic_computation_matrix(self, deriver):
        result = deriver._symbolic_computation("矩阵", "zh")
        assert "符号计算" in result
        assert "行列式" in result

    def test_symbolic_computation_series(self, deriver):
        result = deriver._symbolic_computation("级数", "zh")
        assert "符号计算" in result
        assert "泰勒" in result

    def test_symbolic_computation_equation(self, deriver):
        result = deriver._symbolic_computation("方程", "zh")
        assert "符号计算" in result
        assert "解" in result

    def test_symbolic_computation_pythagorean(self, deriver):
        result = deriver._symbolic_computation("勾股", "zh")
        assert "符号计算" in result
        assert "勾股定理" in result

    def test_symbolic_computation_trig(self, deriver):
        result = deriver._symbolic_computation("三角", "zh")
        assert "符号计算" in result
        assert "sin" in result

    def test_verify_derivative(self, deriver):
        result = deriver._verify_derivation("导数", "zh")
        assert "验证" in result

    def test_verify_integral(self, deriver):
        result = deriver._verify_derivation("积分", "zh")
        assert "验证" in result

    def test_verify_trig(self, deriver):
        result = deriver._verify_derivation("三角", "zh")
        assert "验证" in result


class TestExperimentDesigner:
    @pytest.fixture
    def designer(self):
        return ExperimentDesigner()

    def test_fourier_experiment(self, designer):
        experiments = designer._generate_builtin_experiments("傅里叶", "zh")
        assert len(experiments) > 0
        assert (
            "fourier" in experiments[0]["title"].lower()
            or "傅里叶" in experiments[0]["title"]
        )
        assert "code" in experiments[0]

    def test_derivative_experiment(self, designer):
        experiments = designer._generate_builtin_experiments("导数", "zh")
        assert len(experiments) > 0
        assert "code" in experiments[0]

    def test_integral_experiment(self, designer):
        experiments = designer._generate_builtin_experiments("积分", "zh")
        assert len(experiments) > 0
        assert "code" in experiments[0]

    def test_matrix_experiment(self, designer):
        experiments = designer._generate_builtin_experiments("矩阵", "zh")
        assert len(experiments) > 0
        assert "code" in experiments[0]

    def test_probability_experiment(self, designer):
        experiments = designer._generate_builtin_experiments("概率", "zh")
        assert len(experiments) > 0
        assert "code" in experiments[0]


class TestResearchEngine:
    @pytest.fixture
    def engine(self):
        return ResearchEngine()

    def test_research_topic_creation(self):
        topic = ResearchTopic(query="test")
        assert topic.query == "test"
        assert topic.language == "zh"
        assert topic.depth == "medium"

    def test_research_result_creation(self):
        result = ResearchResult(topic="test")
        assert result.topic == "test"
        assert result.papers == []
        assert result.experiments == []

    def test_research_engine_initialization(self, engine):
        assert engine is not None
        assert engine.config is not None

    def test_analyze_topic(self, engine):
        topic = ResearchTopic(query="勾股定理", language="zh", depth="shallow")
        result = engine._analyze_topic(topic)
        assert len(result) > 0

    def test_get_research_history_empty(self, engine):
        history = engine.get_research_history()
        assert isinstance(history, list)
