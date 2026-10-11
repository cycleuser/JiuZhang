"""Tests for math engine curriculum module."""

import pytest

from jiuzhang.math_engine.curriculum import KnowledgePoint, Lesson, Curriculum


class TestKnowledgePoint:
    def test_create_knowledge_point(self):
        kp = KnowledgePoint(
            id="test.natural_numbers",
            name="Natural Numbers",
            name_cn="自然数",
            category="arithmetic",
            level="elementary",
        )
        assert kp.id == "test.natural_numbers"
        assert kp.category == "arithmetic"
        assert kp.prerequisites == []


class TestLesson:
    def test_create_lesson(self):
        lesson = Lesson(
            id="test.intro",
            title="Introduction",
            title_cn="入门",
            estimated_minutes=30,
        )
        assert lesson.id == "test.intro"
        assert lesson.estimated_minutes == 30


class TestCurriculum:
    def test_add_knowledge_point(self, curriculum):
        kp = KnowledgePoint(
            id="test.kp1",
            name="Test",
            name_cn="测试",
            category="arithmetic",
            level="elementary",
        )
        curriculum.add_knowledge_point(kp)
        assert curriculum.get_knowledge_point("test.kp1") == kp

    def test_add_lesson(self, curriculum):
        lesson = Lesson(
            id="test.lesson1",
            title="Test Lesson",
            title_cn="测试课程",
        )
        curriculum.add_lesson(lesson)
        assert curriculum.get_lesson("test.lesson1") == lesson

    def test_get_prerequisites(self, curriculum):
        kp1 = KnowledgePoint(
            id="test.kp1",
            name="KP1",
            name_cn="知识点1",
            category="arithmetic",
            level="elementary",
        )
        kp2 = KnowledgePoint(
            id="test.kp2",
            name="KP2",
            name_cn="知识点2",
            category="arithmetic",
            level="elementary",
            prerequisites=["test.kp1"],
        )
        curriculum.add_knowledge_point(kp1)
        curriculum.add_knowledge_point(kp2)

        prereqs = curriculum.get_prerequisites("test.kp2")
        assert len(prereqs) == 1
        assert prereqs[0].id == "test.kp1"

    def test_get_learning_path(self, curriculum):
        kp = KnowledgePoint(
            id="test.kp1",
            name="KP1",
            name_cn="知识点1",
            category="arithmetic",
            level="elementary",
        )
        curriculum.add_knowledge_point(kp)
        path = curriculum.get_learning_path("arithmetic", "elementary")
        assert len(path) == 1

    def test_get_all_categories(self, curriculum):
        categories = curriculum.get_all_categories()
        assert "arithmetic" in categories
        assert "algebra" in categories

    def test_get_all_levels(self, curriculum):
        levels = curriculum.get_all_levels()
        assert "elementary" in levels
        assert "undergraduate" in levels
