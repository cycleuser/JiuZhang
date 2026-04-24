"""Course Registry - Central registration for all courses and knowledge points.

Provides a unified interface to access all mathematics courses.
"""

from jiuzhang.math_engine.curriculum import Curriculum, KnowledgePoint, Lesson
from jiuzhang.courses.arithmetic.number_concepts import (
    get_arithmetic_knowledge_points as get_arithmetic_kps,
    get_number_concepts_lesson,
)
from jiuzhang.courses.arithmetic.operations import (
    get_operations_knowledge_points as get_operations_kps,
    get_operations_lesson,
)
from jiuzhang.courses.arithmetic.fractions_course import (
    get_fraction_knowledge_points as get_fraction_kps,
    get_fractions_lesson,
)
from jiuzhang.courses.arithmetic.decimals_course import (
    get_decimal_knowledge_points as get_decimal_kps,
    get_decimals_lesson,
)
from jiuzhang.courses.algebra.equations import (
    get_algebra_knowledge_points as get_algebra_kps,
    get_equations_lesson,
    get_functions_lesson,
)
from jiuzhang.courses.geometry.triangles import (
    get_geometry_knowledge_points as get_geometry_kps,
    get_triangles_lesson,
    get_trigonometry_lesson,
)
from jiuzhang.courses.probability.basics import (
    get_probability_knowledge_points as get_probability_kps,
    get_probability_lesson,
)
from jiuzhang.courses.calculus.basics import (
    get_calculus_knowledge_points as get_calculus_kps,
    get_calculus_lesson,
)
from jiuzhang.courses.linear_algebra.basics import (
    get_linear_algebra_knowledge_points as get_linear_algebra_kps,
    get_linear_algebra_lesson,
)
from jiuzhang.courses.advanced.frontier import (
    get_advanced_knowledge_points as get_advanced_kps,
    get_advanced_lesson,
)
from jiuzhang.courses.discrete import (
    get_discrete_kps,
    get_discrete_lesson,
)


class CourseRegistry:
    """Central registry for all mathematics courses.

    Usage:
        registry = CourseRegistry()
        curriculum = registry.build_curriculum()
    """

    def __init__(self):
        self._lessons = []
        self._loaded = False
        self._lesson_index = {}  # Cache for O(1) lookup by ID

    def _load_all(self):
        if self._loaded:
            return

        self._knowledge_points = [
            *get_arithmetic_kps(),
            *get_operations_kps(),
            *get_fraction_kps(),
            *get_decimal_kps(),
            *get_algebra_kps(),
            *get_geometry_kps(),
            *get_probability_kps(),
            *get_calculus_kps(),
            *get_linear_algebra_kps(),
            *get_advanced_kps(),
            *get_discrete_kps(),
        ]

        self._lessons = [
            get_number_concepts_lesson(),
            get_operations_lesson(),
            get_fractions_lesson(),
            get_decimals_lesson(),
            get_equations_lesson(),
            get_functions_lesson(),
            get_triangles_lesson(),
            get_trigonometry_lesson(),
            get_probability_lesson(),
            get_calculus_lesson(),
            get_linear_algebra_lesson(),
            get_advanced_lesson(),
            get_discrete_lesson(),
        ]

        # Build index for fast lookup
        self._lesson_index = {lesson.id: lesson for lesson in self._lessons}

        self._loaded = True

    def build_curriculum(self) -> Curriculum:
        curriculum = Curriculum()
        self._load_all()

        for kp in self._knowledge_points:
            curriculum.add_knowledge_point(kp)

        for lesson in self._lessons:
            curriculum.add_lesson(lesson)

        return curriculum

    def get_all_knowledge_points(self) -> list:
        self._load_all()
        return self._knowledge_points

    def get_all_lessons(self) -> list:
        self._load_all()
        return self._lessons

    def get_knowledge_points_by_category(self, category: str) -> list:
        self._load_all()
        return [kp for kp in self._knowledge_points if kp.category == category]

    def get_knowledge_points_by_level(self, level: str) -> list:
        self._load_all()
        return [kp for kp in self._knowledge_points if kp.level == level]

    def get_lesson_by_id(self, lesson_id: str):
        self._load_all()
        # Use cached index if available
        if lesson_id in self._lesson_index:
            return self._lesson_index[lesson_id]
        # Fallback to linear search and cache the result
        for lesson in self._lessons:
            if lesson.id == lesson_id:
                self._lesson_index[lesson_id] = lesson
                return lesson
        return None

    def get_categories(self) -> list:
        self._load_all()
        return list(set(kp.category for kp in self._knowledge_points))

    def get_levels(self) -> list:
        self._load_all()
        return list(set(kp.level for kp in self._knowledge_points))

    def get_stats(self) -> dict:
        self._load_all()
        categories = {}
        levels = {}
        for kp in self._knowledge_points:
            categories[kp.category] = categories.get(kp.category, 0) + 1
            levels[kp.level] = levels.get(kp.level, 0) + 1

        return {
            "total_knowledge_points": len(self._knowledge_points),
            "total_lessons": len(self._lessons),
            "by_category": categories,
            "by_level": levels,
        }
