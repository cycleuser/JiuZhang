"""Tests for course registry."""

import pytest
from jiuzhang.courses.registry import CourseRegistry


class TestCourseRegistry:
    @pytest.fixture
    def registry(self):
        return CourseRegistry()

    def test_build_curriculum(self, registry):
        curriculum = registry.build_curriculum()
        assert curriculum is not None
        assert len(curriculum.knowledge_points) > 0
        assert len(curriculum.lessons) > 0

    def test_get_all_knowledge_points(self, registry):
        kps = registry.get_all_knowledge_points()
        assert len(kps) > 0
        assert all(hasattr(kp, "id") for kp in kps)

    def test_get_all_lessons(self, registry):
        lessons = registry.get_all_lessons()
        assert len(lessons) > 0
        assert all(hasattr(lesson, "id") for lesson in lessons)

    def test_get_knowledge_points_by_category(self, registry):
        arithmetic_kps = registry.get_knowledge_points_by_category("arithmetic")
        assert len(arithmetic_kps) > 0
        assert all(kp.category == "arithmetic" for kp in arithmetic_kps)

        algebra_kps = registry.get_knowledge_points_by_category("algebra")
        assert len(algebra_kps) > 0
        assert all(kp.category == "algebra" for kp in algebra_kps)

    def test_get_knowledge_points_by_level(self, registry):
        elementary_kps = registry.get_knowledge_points_by_level("elementary")
        assert len(elementary_kps) > 0
        assert all(kp.level == "elementary" for kp in elementary_kps)

    def test_get_lesson_by_id(self, registry):
        lesson = registry.get_lesson_by_id("arithmetic.number_concepts.intro")
        assert lesson is not None
        assert lesson.id == "arithmetic.number_concepts.intro"

    def test_get_lesson_by_id_not_found(self, registry):
        lesson = registry.get_lesson_by_id("nonexistent.lesson")
        assert lesson is None

    def test_get_categories(self, registry):
        categories = registry.get_categories()
        assert "arithmetic" in categories
        assert "algebra" in categories
        assert "geometry" in categories
        assert "probability" in categories
        assert "calculus" in categories
        assert "linear_algebra" in categories
        assert "advanced" in categories

    def test_get_levels(self, registry):
        levels = registry.get_levels()
        assert "elementary" in levels
        assert "middle_school" in levels
        assert "high_school" in levels

    def test_get_stats(self, registry):
        stats = registry.get_stats()
        assert "total_knowledge_points" in stats
        assert "total_lessons" in stats
        assert "by_category" in stats
        assert "by_level" in stats
        assert stats["total_knowledge_points"] > 0
        assert stats["total_lessons"] > 0
        assert len(stats["by_category"]) >= 7
