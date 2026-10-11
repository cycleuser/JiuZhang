"""Tests for frontier mathematics module (manim-based)."""

import pytest
from jiuzhang.research.frontier import FrontierMathKB, FrontierTopic
from jiuzhang.research.advanced_symbolic import AdvancedSymbolicEngine
from jiuzhang.research.paper_reader import PaperReader
from jiuzhang.research.frontier_viz import FrontierVisualizer
from jiuzhang.research.assistant import FrontierResearchAssistant


class TestFrontierMathKB:
    @pytest.fixture
    def kb(self):
        return FrontierMathKB()

    def test_get_topic(self, kb):
        topic = kb.get_topic("langlands")
        assert topic is not None
        assert topic.name == "Langlands Program"
        assert topic.name_cn == "朗兰兹纲领"

    def test_get_topics_by_category(self, kb):
        topics = kb.get_topics_by_category("algebraic_geometry")
        assert len(topics) >= 2
        assert all(t.category == "algebraic_geometry" for t in topics)

    def test_get_all_categories(self, kb):
        categories = kb.get_all_categories()
        assert len(categories) >= 7
        assert "algebraic_geometry" in categories
        assert "number_theory" in categories
        assert "mathematical_physics" in categories

    def test_search(self, kb):
        results = kb.search("朗兰兹", "zh")
        assert len(results) > 0
        assert results[0].name_cn == "朗兰兹纲领"

    def test_search_english(self, kb):
        results = kb.search("langlands", "en")
        assert len(results) > 0
        assert results[0].name == "Langlands Program"

    def test_get_category_names(self, kb):
        names_zh = kb.get_category_names("zh")
        assert names_zh["algebraic_geometry"] == "代数几何"

        names_en = kb.get_category_names("en")
        assert names_en["algebraic_geometry"] == "Algebraic Geometry"

    def test_generate_overview(self, kb):
        overview_zh = kb.generate_overview("zh")
        assert len(overview_zh) > 100
        assert "前沿数学领域概览" in overview_zh

        overview_en = kb.generate_overview("en")
        assert len(overview_en) > 100
        assert "Frontier Mathematics Overview" in overview_en

    def test_topic_structure(self, kb):
        topic = kb.get_topic("schemes")
        assert topic is not None
        assert isinstance(topic, FrontierTopic)
        assert len(topic.key_concepts) > 0
        assert len(topic.open_problems) > 0
        assert len(topic.arxiv_categories) > 0


class TestAdvancedSymbolicEngine:
    @pytest.fixture
    def engine(self):
        return AdvancedSymbolicEngine()

    def test_riemannian_geometry(self, engine):
        result = engine._riemannian_geometry("zh")
        assert "黎曼几何" in result
        assert "克里斯托费尔" in result
        assert "曲率" in result

    def test_lie_theory(self, engine):
        result = engine._lie_theory("zh")
        assert "李" in result
        assert "对易关系" in result
        assert "嘉当" in result

    def test_algebraic_topology(self, engine):
        result = engine._algebraic_topology("zh")
        assert "同调" in result
        assert "欧拉示性数" in result
        assert "庞加莱" in result

    def test_commutative_algebra(self, engine):
        result = engine._commutative_algebra("zh")
        assert "交换代数" in result
        assert "格罗布纳" in result
        assert "希尔伯特" in result

    def test_quantum_groups(self, engine):
        result = engine._quantum_groups("zh")
        assert "量子群" in result
        assert "R-矩阵" in result
        assert "晶体基" in result

    def test_knot_theory(self, engine):
        result = engine._knot_theory("zh")
        assert "纽结" in result
        assert "琼斯" in result
        assert "亚历山大" in result

    def test_category_theory_symbolic(self, engine):
        result = engine._category_theory_symbolic("zh")
        assert "范畴" in result
        assert "米田" in result
        assert "伴随" in result

    def test_advanced_number_theory(self, engine):
        result = engine._advanced_number_theory("zh")
        assert "椭圆曲线" in result
        assert "模形式" in result
        assert "L-函数" in result

    def test_representation_theory(self, engine):
        result = engine._representation_theory("zh")
        assert "表示" in result
        assert "特征标" in result
        assert "舒尔" in result

    def test_compute(self, engine):
        result = engine.compute("黎曼几何", "zh")
        assert len(result) > 0

    def test_compute_english(self, engine):
        result = engine.compute("riemannian geometry", "en")
        assert len(result) > 0


class TestPaperReader:
    @pytest.fixture
    def reader(self):
        return PaperReader()

    def test_fetch_paper(self, reader):
        paper = reader.fetch_paper("2401.00001")
        assert paper is not None
        if "error" not in paper:
            assert "title" in paper
            assert "authors" in paper
            assert "abstract" in paper

    def test_generate_summary(self, reader):
        paper = {
            "title": "Test Paper",
            "authors_str": "Author A, Author B",
            "abstract": "This is a test abstract",
            "published": "2024-01-01",
            "categories": ["math.AG"],
            "url": "https://arxiv.org/abs/2401.00001",
            "abs_url": "https://arxiv.org/abs/2401.00001",
            "pdf_url": "https://arxiv.org/pdf/2401.00001",
        }
        summary = reader.generate_summary(paper, "zh")
        assert "论文摘要" in summary
        assert "Test Paper" in summary

    def test_generate_summary_english(self, reader):
        paper = {
            "title": "Test Paper",
            "authors_str": "Author A, Author B",
            "abstract": "This is a test abstract",
            "published": "2024-01-01",
            "categories": ["math.AG"],
            "url": "https://arxiv.org/abs/2401.00001",
        }
        summary = reader.generate_summary(paper, "en")
        assert "Paper Summary" in summary
        assert "Test Paper" in summary


class TestFrontierVisualizer:
    @pytest.fixture
    def visualizer(self):
        return FrontierVisualizer()

    def test_plot_torus(self, visualizer):
        result = visualizer.plot_torus()
        assert result is not None
        assert len(result) > 0

    def test_plot_mobius_strip(self, visualizer):
        result = visualizer.plot_mobius_strip()
        assert result is not None
        assert len(result) > 0

    def test_plot_klein_bottle(self, visualizer):
        result = visualizer.plot_klein_bottle()
        assert result is not None
        assert len(result) > 0

    def test_plot_root_system(self, visualizer):
        result = visualizer.plot_root_system("A2")
        assert result is not None
        assert len(result) > 0

    def test_plot_fractal(self, visualizer):
        result = visualizer.plot_fractal(mandelbrot=True, resolution=100)
        assert result is not None
        assert len(result) > 0

    def test_plot_complex_function(self, visualizer):
        result = visualizer.plot_complex_function(lambda z: z**2, resolution=100)
        assert result is not None
        assert len(result) > 0

    def test_plot_vector_field(self, visualizer):
        result = visualizer.plot_vector_field(
            lambda x, y: -y, lambda x, y: x, grid_size=10
        )
        assert result is not None
        assert len(result) > 0

    def test_plot_3d_surface(self, visualizer):
        import numpy as np

        result = visualizer.plot_3d_surface(
            lambda x, y: np.sin(np.sqrt(x**2 + y**2)), resolution=50
        )
        assert result is not None
        assert len(result) > 0


class TestFrontierResearchAssistant:
    @pytest.fixture
    def assistant(self):
        return FrontierResearchAssistant()

    def test_research(self, assistant):
        result = assistant.research(
            "朗兰兹纲领",
            language="zh",
            include_papers=False,
            include_visualization=False,
        )
        assert len(result) > 100
        assert "前沿数学研究" in result or "Frontier Mathematics Research" in result

    def test_get_frontier_overview(self, assistant):
        overview = assistant.get_frontier_overview("zh")
        assert len(overview) > 100
        assert "前沿数学" in overview

    def test_generate_visualization(self, assistant):
        result = assistant.generate_visualization("torus")
        assert result is not None
        assert len(result) > 0

    def test_generate_visualization_mobius(self, assistant):
        result = assistant.generate_visualization("mobius")
        assert result is not None
        assert len(result) > 0

    def test_generate_visualization_root_system(self, assistant):
        result = assistant.generate_visualization("root_system", root_type="A2")
        assert result is not None
        assert len(result) > 0