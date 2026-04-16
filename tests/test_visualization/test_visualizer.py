"""Tests for visualization module."""

import numpy as np
import pytest
from jiuzhang.math_engine.visualizer import Visualizer


class TestVisualizer:
    def test_plot_number_line(self):
        result = Visualizer.plot_number_line(start=-5, end=5, highlight=[0])
        assert result.success is True
        assert result.metadata.get("type") == "base64"

    def test_plot_number_line_with_save(self, tmp_path):
        save_path = str(tmp_path / "test_number_line.png")
        result = Visualizer.plot_number_line(
            start=-5, end=5, highlight=[0], save_path=save_path
        )
        assert result.success is True
        assert result.metadata.get("type") == "file"
        assert result.data == save_path

    def test_plot_function(self):
        result = Visualizer.plot_function(
            lambda x: x**2, x_range=(-5, 5), title="y = x²"
        )
        assert result.success is True

    def test_plot_scatter(self):
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 5, 4, 5])
        result = Visualizer.plot_scatter(x, y, title="Test Scatter")
        assert result.success is True

    def test_plot_bar(self):
        result = Visualizer.plot_bar(
            categories=["A", "B", "C"], values=[10, 20, 15], title="Test Bar"
        )
        assert result.success is True

    def test_plot_histogram(self):
        data = np.random.randn(100)
        result = Visualizer.plot_histogram(data, bins=10, title="Test Histogram")
        assert result.success is True

    def test_plot_matrix(self):
        matrix = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        result = Visualizer.plot_matrix(matrix, title="Test Matrix")
        assert result.success is True
