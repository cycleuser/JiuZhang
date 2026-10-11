"""Curriculum management for JiuZhang.

Defines the mathematics curriculum structure, knowledge points, and their relationships.
"""

from dataclasses import dataclass, field
from typing import Optional

from jiuzhang.core.constants import MATH_LEVELS, COURSE_CATEGORIES


@dataclass
class KnowledgePoint:
    """A single knowledge point in the curriculum.

    Attributes:
        id: Unique identifier (e.g., "arithmetic.natural_numbers.intro")
        name: Name of the knowledge point
        name_cn: Chinese name
        category: Course category (arithmetic, algebra, etc.)
        level: Math level (elementary, middle_school, etc.)
        description: Detailed description
        description_cn: Chinese description
        prerequisites: List of prerequisite knowledge point IDs
        related_points: List of related knowledge point IDs
        code_examples: List of code example paths
        visualization_types: List of visualization types supported
    """

    id: str
    name: str
    name_cn: str
    category: str
    level: str
    description: str = ""
    description_cn: str = ""
    prerequisites: list = field(default_factory=list)
    related_points: list = field(default_factory=list)
    code_examples: list = field(default_factory=list)
    visualization_types: list = field(default_factory=list)


@dataclass
class Lesson:
    """A lesson covering one or more knowledge points.

    Attributes:
        id: Unique lesson ID
        title: Lesson title
        title_cn: Chinese title
        knowledge_points: List of knowledge point IDs covered
        content: Lesson content (markdown)
        content_cn: Chinese content
        code_snippets: List of code snippets
        exercises: List of exercise IDs
        estimated_minutes: Estimated completion time
    """

    id: str
    title: str
    title_cn: str
    knowledge_points: list = field(default_factory=list)
    content: str = ""
    content_cn: str = ""
    code_snippets: list = field(default_factory=list)
    exercises: list = field(default_factory=list)
    estimated_minutes: int = 30


@dataclass
class Curriculum:
    """The complete mathematics curriculum.

    Manages all knowledge points, lessons, and their relationships.
    """

    knowledge_points: dict = field(default_factory=dict)
    lessons: dict = field(default_factory=dict)
    learning_paths: dict = field(default_factory=dict)

    def add_knowledge_point(self, kp: KnowledgePoint):
        self.knowledge_points[kp.id] = kp

    def add_lesson(self, lesson: Lesson):
        self.lessons[lesson.id] = lesson

    def get_knowledge_point(self, kp_id: str) -> Optional[KnowledgePoint]:
        return self.knowledge_points.get(kp_id)

    def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        return self.lessons.get(lesson_id)

    def get_prerequisites(self, kp_id: str) -> list:
        return self._get_prerequisites_recursive(kp_id, set())
    
    def _get_prerequisites_recursive(self, kp_id: str, visited: set) -> list:
        # Prevent infinite recursion from circular dependencies
        if kp_id in visited:
            return []
        visited.add(kp_id)
        
        kp = self.get_knowledge_point(kp_id)
        if not kp:
            return []
        result = []
        for prereq_id in kp.prerequisites:
            prereq = self.get_knowledge_point(prereq_id)
            if prereq:
                result.append(prereq)
                result.extend(self._get_prerequisites_recursive(prereq_id, visited.copy()))
        return result

    def get_learning_path(self, category: str, level: str) -> list:
        path_key = f"{category}.{level}"
        if path_key in self.learning_paths:
            return self.learning_paths[path_key]

        path = []
        for kp_id, kp in self.knowledge_points.items():
            if kp.category == category and kp.level == level:
                path.append(kp)
        path.sort(key=lambda x: x.id)
        self.learning_paths[path_key] = path
        return path

    def get_all_categories(self) -> list:
        return COURSE_CATEGORIES

    def get_all_levels(self) -> list:
        return MATH_LEVELS
