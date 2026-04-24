"""Discrete Mathematics Course Materials for JiuZhang."""

from typing import List
from dataclasses import dataclass
from jiuzhang.math_engine.curriculum import Lesson


@dataclass
class DiscreteMathConcept:
    """A discrete mathematics concept with examples."""
    name: str
    name_cn: str
    definition: str
    definition_cn: str
    examples: List[str]
    examples_cn: List[str]
    prerequisites: List[str]


# Discrete mathematics fundamental concepts
DISCRETE_MATH_CONCEPTS = {
    "sets": DiscreteMathConcept(
        name="Set Theory Basics",
        name_cn="集合论基础",
        definition="A set is a collection of distinct objects, considered as an object in its own right.",
        definition_cn="集合是不同对象的聚集，被看作一个整体对象。",
        examples=[
            "A = {1, 2, 3}, B = {2, 3, 4}",
            "Union: A ∪ B = {1, 2, 3, 4}",
            "Intersection: A ∩ B = {2, 3}",
            "Difference: A - B = {1}"
        ],
        examples_cn=[
            "A = {1, 2, 3}, B = {2, 3, 4}",
            "并集: A ∪ B = {1, 2, 3, 4}",
            "交集: A ∩ B = {2, 3}",
            "差集: A - B = {1}"
        ],
        prerequisites=["arithmetic.basics"]
    ),
    "logic": DiscreteMathConcept(
        name="Propositional Logic",
        name_cn="命题逻辑",
        definition="Logic is the study of valid reasoning, focusing on the relationship between propositions.",
        definition_cn="逻辑学研究有效推理，关注命题之间的关系。",
        examples=[
            "P ∧ Q (AND)",
            "P ∨ Q (OR)", 
            "¬P (NOT)",
            "P → Q (IF-THEN)"
        ],
        examples_cn=[
            "P ∧ Q (与)",
            "P ∨ Q (或)", 
            "¬P (非)",
            "P → Q (如果-那么)"
        ],
        prerequisites=["sets"]
    ),
    "combinatorics": DiscreteMathConcept(
        name="Basic Combinatorics",
        name_cn="基础组合数学",
        definition="Combinatorics is the study of counting, arrangement, and combination of objects.",
        definition_cn="组合数学研究对象的计数、排列和组合。",
        examples=[
            "Permutations: n! = n × (n-1) × ... × 1",
            "Combinations: C(n,k) = n! / (k!(n-k)!)",
            "Example: How many ways to choose 2 from 5? C(5,2) = 10"
        ],
        examples_cn=[
            "排列: n! = n × (n-1) × ... × 1",
            "组合: C(n,k) = n! / (k!(n-k)!)",
            "例子: 从5个中选2个有多少种方式？C(5,2) = 10"
        ],
        prerequisites=["logic"]
    ),
    "graphs": DiscreteMathConcept(
        name="Graph Theory Basics",
        name_cn="图论基础",
        definition="A graph is a collection of vertices connected by edges.",
        definition_cn="图是由顶点和边连接组成的集合。",
        examples=[
            "Complete graph K₄ has 4 vertices, each connected to every other",
            "Path graph P₃: A-B-C",
            "Tree: Connected acyclic graph"
        ],
        examples_cn=[
            "完全图 K₄ 有4个顶点，每对顶点都相连",
            "路径图 P₃: A-B-C", 
            "树: 连通无环图"
        ],
        prerequisites=["combinatorics"]
    ),
    "relations": DiscreteMathConcept(
        name="Relations and Functions",
        name_cn="关系与函数",
        definition="A relation connects elements from one set to another; a function is a special type of relation.",
        definition_cn="关系连接两个集合的元素；函数是一种特殊的关系。",
        examples=[
            "Relation R on A: R = {(1,2), (2,3)}",
            "Function f(x) = x²",
            "Equivalence relation properties: reflexive, symmetric, transitive"
        ],
        examples_cn=[
            "集合A上的关系 R: R = {(1,2), (2,3)}",
            "函数 f(x) = x²", 
            "等价关系性质: 自反性、对称性、传递性"
        ],
        prerequisites=["sets", "logic"]
    )
}


def get_discrete_math_lesson(topic: str = "sets") -> Lesson:
    """Generate a discrete mathematics lesson."""
    if topic not in DISCRETE_MATH_CONCEPTS:
        topic = "sets"  # default
    
    concept = DISCRETE_MATH_CONCEPTS[topic]
    
    title = f"Discrete Math: {concept.name}" if topic != "sets" else f"离散数学: {concept.name_cn}"
    
    content_parts = [
        f"# {title}",
        f"\n## Definition 定义\n{concept.definition}\n{concept.definition_cn}",
        "\n## Examples 例子",
    ]
    
    for i, (eng, chi) in enumerate(zip(concept.examples, concept.examples_cn)):
        content_parts.append(f"{i+1}. {eng} - {chi}")
    
    exercises = []
    
    # Create lesson with correct fields
    return Lesson(
        id=f"discrete_{topic}",
        title=title,
        title_cn=f"离散数学: {concept.name_cn}",
        knowledge_points=[f"discrete.{topic}"],  # Add the corresponding knowledge point
        content="\n".join(content_parts),
        content_cn="\n".join(content_parts),  # Same content for both languages in this case
        exercises=exercises,
        estimated_minutes=20
    )


def get_discrete_kps() -> List:
    """Get discrete math knowledge points."""
    from jiuzhang.math_engine.curriculum import KnowledgePoint
    
    return [
        KnowledgePoint(
            id="discrete.sets",
            name="Sets and Operations",
            name_cn="集合与运算",
            prerequisites=["arithmetic.basics"],
            category="discrete",
            level="intermediate"
        ),
        KnowledgePoint(
            id="discrete.logic", 
            name="Propositional Logic",
            name_cn="命题逻辑",
            prerequisites=["discrete.sets"],
            category="discrete", 
            level="intermediate"
        ),
        KnowledgePoint(
            id="discrete.combinatorics",
            name="Basic Combinatorics", 
            name_cn="基础组合数学",
            prerequisites=["discrete.logic"],
            category="discrete",
            level="intermediate"
        ),
        KnowledgePoint(
            id="discrete.graphs",
            name="Graph Theory Basics",
            name_cn="图论基础", 
            prerequisites=["discrete.combinatorics"],
            category="discrete",
            level="intermediate"
        ),
        KnowledgePoint(
            id="discrete.relations",
            name="Relations and Functions", 
            name_cn="关系与函数",
            prerequisites=["discrete.sets", "discrete.logic"],
            category="discrete",
            level="intermediate"
        )
    ]


def get_discrete_lesson() -> Lesson:
    """Get the main discrete math lesson."""
    return get_discrete_math_lesson("sets")