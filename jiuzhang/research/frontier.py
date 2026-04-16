"""Frontier Mathematics Knowledge Base for JiuZhang.

Comprehensive knowledge base for cutting-edge mathematical research:
- Algebraic Geometry
- Differential Geometry & Topology
- Category Theory
- Representation Theory
- Number Theory (Modern)
- Mathematical Physics
- Homological Algebra
- K-Theory
- Ergodic Theory
- Dynamical Systems
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FrontierTopic:
    """A frontier mathematics topic."""

    id: str
    name: str
    name_cn: str
    category: str
    description: str
    description_cn: str
    prerequisites: list = field(default_factory=list)
    key_concepts: list = field(default_factory=list)
    open_problems: list = field(default_factory=list)
    key_theorems: list = field(default_factory=list)
    important_papers: list = field(default_factory=list)
    arxiv_categories: list = field(default_factory=list)
    related_topics: list = field(default_factory=list)


# Frontier Mathematics Knowledge Base
FRONTIER_TOPICS = {
    # Algebraic Geometry
    "schemes": FrontierTopic(
        id="schemes",
        name="Schemes",
        name_cn="概形",
        category="algebraic_geometry",
        description="Scheme theory, the foundation of modern algebraic geometry, generalizing algebraic varieties",
        description_cn="概形理论，现代代数几何的基础，推广了代数簇的概念",
        prerequisites=["commutative_algebra", "sheaf_theory", "category_theory"],
        key_concepts=[
            "affine schemes",
            "structure sheaf",
            "morphisms",
            "fiber products",
            "proper morphisms",
        ],
        open_problems=[
            "Hodge conjecture (partially)",
            "Standard conjectures on algebraic cycles",
            "Resolution of singularities in positive characteristic",
        ],
        key_theorems=[
            "Grothendieck duality",
            "GAGA principle",
            "Riemann-Roch for schemes",
        ],
        arxiv_categories=["math.AG"],
        related_topics=["cohomology", "stacks", "derived_algebraic_geometry"],
    ),
    "stacks": FrontierTopic(
        id="stacks",
        name="Stacks and Moduli",
        name_cn="叠与模空间",
        category="algebraic_geometry",
        description="Stacks generalize schemes to handle moduli problems with automorphisms",
        description_cn="叠推广了概形，用于处理具有自同构的模问题",
        prerequisites=["schemes", "category_theory", "descent_theory"],
        key_concepts=[
            "algebraic stacks",
            "Deligne-Mumford stacks",
            "Artin stacks",
            "moduli stacks",
        ],
        open_problems=[
            "Compactification of moduli spaces",
            "Derived moduli problems",
        ],
        key_theorems=["Keel-Mori theorem", "Artin's representability criterion"],
        arxiv_categories=["math.AG", "math.CT"],
        related_topics=["schemes", "derived_algebraic_geometry", "homotopy_theory"],
    ),
    "derived_ag": FrontierTopic(
        id="derived_ag",
        name="Derived Algebraic Geometry",
        name_cn="导出代数几何",
        category="algebraic_geometry",
        description="Derived algebraic geometry uses homotopy theory to study moduli problems",
        description_cn="导出代数几何使用同伦理论研究模问题",
        prerequisites=["schemes", "homotopy_theory", "infinity_categories"],
        key_concepts=[
            "derived schemes",
            "spectral algebraic geometry",
            "derived stacks",
        ],
        open_problems=[
            "Derived deformation theory",
            "Quantization of derived symplectic structures",
        ],
        key_theorems=["Lurie's representability theorem"],
        arxiv_categories=["math.AG", "math.AT"],
        related_topics=["stacks", "infinity_categories", "homotopy_theory"],
    ),
    # Differential Geometry & Topology
    "riemannian_geometry": FrontierTopic(
        id="riemannian_geometry",
        name="Riemannian Geometry",
        name_cn="黎曼几何",
        category="differential_geometry",
        description="Study of smooth manifolds with Riemannian metrics",
        description_cn="研究带有黎曼度量的光滑流形",
        prerequisites=["differential_topology", "tensor_calculus"],
        key_concepts=["curvature", "geodesics", "holonomy", "comparison theorems"],
        open_problems=[
            "Hopf conjecture on S²×S²",
            "Positive scalar curvature obstructions",
            "Ricci flow singularities",
        ],
        key_theorems=[
            "Gauss-Bonnet-Chern",
            "Sphere theorem",
            "Cheeger-Gromoll splitting",
        ],
        arxiv_categories=["math.DG"],
        related_topics=["geometric_analysis", "topology", "mathematical_physics"],
    ),
    "geometric_analysis": FrontierTopic(
        id="geometric_analysis",
        name="Geometric Analysis",
        name_cn="几何分析",
        category="differential_geometry",
        description="PDE methods applied to geometric problems",
        description_cn="将 PDE 方法应用于几何问题",
        prerequisites=["riemannian_geometry", "pde", "functional_analysis"],
        key_concepts=[
            "Ricci flow",
            "mean curvature flow",
            "harmonic maps",
            "minimal surfaces",
        ],
        open_problems=[
            "Singularity formation in Ricci flow",
            "Mean curvature flow of high codimension",
            "Yamabe problem extensions",
        ],
        key_theorems=[
            "Hamilton's Ricci flow",
            "Perelman's entropy",
            "Simon's regularity",
        ],
        arxiv_categories=["math.DG", "math.AP"],
        related_topics=["riemannian_geometry", "pde", "topology"],
    ),
    "symplectic_topology": FrontierTopic(
        id="symplectic_topology",
        name="Symplectic Topology",
        name_cn="辛拓扑",
        category="differential_geometry",
        description="Study of symplectic manifolds and their invariants",
        description_cn="研究辛流形及其不变量",
        prerequisites=["differential_topology", "hamiltonian_mechanics"],
        key_concepts=[
            "Floer homology",
            "Gromov-Witten invariants",
            "Lagrangian submanifolds",
        ],
        open_problems=[
            "Arnold conjecture (general case)",
            "Symplectic camel problem",
            "Homological mirror symmetry",
        ],
        key_theorems=[
            "Gromov's non-squeezing",
            "Arnold conjecture (partial)",
            "Floer homology",
        ],
        arxiv_categories=["math.SG", "math.GT"],
        related_topics=[
            "algebraic_geometry",
            "mathematical_physics",
            "mirror_symmetry",
        ],
    ),
    # Category Theory
    "category_theory": FrontierTopic(
        id="category_theory",
        name="Category Theory",
        name_cn="范畴论",
        category="category_theory",
        description="Abstract study of mathematical structures and their relationships",
        description_cn="抽象研究数学结构及其关系",
        prerequisites=["abstract_algebra", "set_theory"],
        key_concepts=[
            "functors",
            "natural transformations",
            "limits",
            "adjunctions",
            "monads",
        ],
        open_problems=[
            "Foundations of higher category theory",
            "Categorification of quantum invariants",
        ],
        key_theorems=[
            "Yoneda lemma",
            "Adjoint functor theorem",
            "Grothendieck construction",
        ],
        arxiv_categories=["math.CT"],
        related_topics=["homological_algebra", "topos_theory", "infinity_categories"],
    ),
    "infinity_categories": FrontierTopic(
        id="infinity_categories",
        name="Infinity Categories",
        name_cn="无穷范畴",
        category="category_theory",
        description="Higher category theory with weak composition laws",
        description_cn="具有弱组合律的高阶范畴论",
        prerequisites=["category_theory", "homotopy_theory"],
        key_concepts=["quasi-categories", "complete Segal spaces", "model categories"],
        open_problems=[
            "Foundations of (∞,n)-categories",
            "Geometric realization of higher categories",
        ],
        key_theorems=["Lurie's straightening/unstraightening", "Joyal model structure"],
        arxiv_categories=["math.CT", "math.AT"],
        related_topics=[
            "category_theory",
            "homotopy_theory",
            "derived_algebraic_geometry",
        ],
    ),
    "topos_theory": FrontierTopic(
        id="topos_theory",
        name="Topos Theory",
        name_cn="拓扑斯理论",
        category="category_theory",
        description="Categories that behave like categories of sheaves",
        description_cn="行为类似于层范畴的范畴",
        prerequisites=["category_theory", "logic", "sheaf_theory"],
        key_concepts=[
            "elementary topos",
            "Grothendieck topos",
            "classifying topos",
            "geometric morphisms",
        ],
        open_problems=[
            "Classification of toposes",
            "Topos-theoretic foundations of mathematics",
        ],
        key_theorems=["Giraud's theorem", "Deligne's completeness theorem"],
        arxiv_categories=["math.CT", "math.LO"],
        related_topics=["category_theory", "logic", "algebraic_geometry"],
    ),
    # Number Theory
    "langlands": FrontierTopic(
        id="langlands",
        name="Langlands Program",
        name_cn="朗兰兹纲领",
        category="number_theory",
        description="Deep connections between number theory, algebraic geometry, and representation theory",
        description_cn="数论、代数几何和表示论之间的深刻联系",
        prerequisites=[
            "algebraic_number_theory",
            "representation_theory",
            "automorphic_forms",
        ],
        key_concepts=[
            "automorphic representations",
            "Galois representations",
            "L-functions",
            "functoriality",
        ],
        open_problems=[
            "Full Langlands correspondence",
            "Functoriality conjecture",
            "Ramanujan-Petersson conjecture",
        ],
        key_theorems=[
            "Modularity theorem (Wiles)",
            "Local Langlands (GL_n)",
            "Fundamental lemma (Ngô)",
        ],
        arxiv_categories=["math.NT", "math.RT", "math.AG"],
        related_topics=[
            "representation_theory",
            "algebraic_geometry",
            "mathematical_physics",
        ],
    ),
    "arithmetic_geometry": FrontierTopic(
        id="arithmetic_geometry",
        name="Arithmetic Geometry",
        name_cn="算术几何",
        category="number_theory",
        description="Intersection of number theory and algebraic geometry",
        description_cn="数论与代数几何的交叉",
        prerequisites=["algebraic_number_theory", "algebraic_geometry"],
        key_concepts=[
            "rational points",
            "height functions",
            "Mordell-Weil theorem",
            "Faltings' theorem",
        ],
        open_problems=[
            "Birch and Swinnerton-Dyer conjecture",
            "ABC conjecture",
            "Rational points on higher dimensional varieties",
        ],
        key_theorems=["Mordell-Weil", "Faltings' theorem", "Wiles' modularity"],
        arxiv_categories=["math.NT", "math.AG"],
        related_topics=["langlands", "diophantine_geometry", "p_adic_hodge"],
    ),
    # Representation Theory
    "representation_theory": FrontierTopic(
        id="representation_theory",
        name="Representation Theory",
        name_cn="表示论",
        category="representation_theory",
        description="Study of abstract algebraic structures by representing their elements as linear transformations",
        description_cn="通过将抽象代数结构的元素表示为线性变换来研究",
        prerequisites=["abstract_algebra", "linear_algebra", "lie_theory"],
        key_concepts=[
            "irreducible representations",
            "characters",
            "induced representations",
            "tensor categories",
        ],
        open_problems=[
            "Classification of finite simple groups representations",
            "Kazhdan-Lusztig conjectures extensions",
        ],
        key_theorems=[
            "Peter-Weyl theorem",
            "Schur-Weyl duality",
            "Borel-Weil-Bott theorem",
        ],
        arxiv_categories=["math.RT"],
        related_topics=["lie_theory", "quantum_groups", "geometric_representation"],
    ),
    "quantum_groups": FrontierTopic(
        id="quantum_groups",
        name="Quantum Groups",
        name_cn="量子群",
        category="representation_theory",
        description="Deformations of universal enveloping algebras of Lie algebras",
        description_cn="李代数泛包络代数的形变",
        prerequisites=["lie_theory", "representation_theory", "hopf_algebras"],
        key_concepts=[
            "quantum enveloping algebras",
            "R-matrices",
            "crystal bases",
            "canonical bases",
        ],
        open_problems=[
            "Categorification of quantum groups",
            "Quantum groups at roots of unity",
        ],
        key_theorems=["Drinfeld-Jimbo theorem", "Lusztig's canonical bases"],
        arxiv_categories=["math.QA", "math.RT"],
        related_topics=[
            "representation_theory",
            "knot_theory",
            "conformal_field_theory",
        ],
    ),
    # Mathematical Physics
    "quantum_field_theory": FrontierTopic(
        id="quantum_field_theory",
        name="Quantum Field Theory (Mathematical)",
        name_cn="量子场论（数学）",
        category="mathematical_physics",
        description="Rigorous mathematical formulation of quantum field theories",
        description_cn="量子场论的严格数学表述",
        prerequisites=[
            "functional_analysis",
            "differential_geometry",
            "representation_theory",
        ],
        key_concepts=[
            "path integrals",
            "renormalization",
            "operator algebras",
            "constructive QFT",
        ],
        open_problems=[
            "Yang-Mills existence and mass gap",
            "Construction of 4D QFT",
            "Rigorous renormalization group",
        ],
        key_theorems=["Osterwalder-Schrader axioms", "Wightman axioms"],
        arxiv_categories=["math-ph", "hep-th"],
        related_topics=["topological_qft", "conformal_field_theory", "string_theory"],
    ),
    "mirror_symmetry": FrontierTopic(
        id="mirror_symmetry",
        name="Mirror Symmetry",
        name_cn="镜像对称",
        category="mathematical_physics",
        description="Duality between Calabi-Yau manifolds in string theory",
        description_cn="弦理论中卡拉比-丘流形之间的对偶",
        prerequisites=["algebraic_geometry", "symplectic_topology", "string_theory"],
        key_concepts=[
            "Calabi-Yau manifolds",
            "A-model/B-model",
            "homological mirror symmetry",
        ],
        open_problems=[
            "Full homological mirror symmetry proof",
            "Mirror symmetry for Fano varieties",
        ],
        key_theorems=["Kontsevich's HMS conjecture (partial)", "SYZ conjecture"],
        arxiv_categories=["math.AG", "math.SG", "hep-th"],
        related_topics=["symplectic_topology", "algebraic_geometry", "string_theory"],
    ),
    # Homological Algebra & K-Theory
    "homological_algebra": FrontierTopic(
        id="homological_algebra",
        name="Homological Algebra",
        name_cn="同调代数",
        category="homological_algebra",
        description="Study of homology and cohomology in abstract algebraic settings",
        description_cn="在抽象代数框架下研究同调和上同调",
        prerequisites=["abstract_algebra", "category_theory"],
        key_concepts=[
            "derived functors",
            "spectral sequences",
            "derived categories",
            "triangulated categories",
        ],
        open_problems=[
            "Foundations of derived algebraic geometry",
            "Non-commutative motives",
        ],
        key_theorems=["Grothendieck spectral sequence", "Derived category equivalence"],
        arxiv_categories=["math.KT", "math.CT"],
        related_topics=["category_theory", "k_theory", "algebraic_topology"],
    ),
    "k_theory": FrontierTopic(
        id="k_theory",
        name="K-Theory",
        name_cn="K 理论",
        category="k_theory",
        description="Study of vector bundles and their generalizations",
        description_cn="研究向量丛及其推广",
        prerequisites=["algebraic_topology", "homological_algebra"],
        key_concepts=[
            "topological K-theory",
            "algebraic K-theory",
            "Bott periodicity",
            "Chern characters",
        ],
        open_problems=[
            "Baum-Connes conjecture",
            "Novikov conjecture",
            "Computations of higher K-groups",
        ],
        key_theorems=[
            "Bott periodicity",
            "Atiyah-Singer index theorem",
            "Grothendieck-Riemann-Roch",
        ],
        arxiv_categories=["math.KT", "math.AT"],
        related_topics=[
            "algebraic_topology",
            "index_theory",
            "noncommutative_geometry",
        ],
    ),
}


class FrontierMathKB:
    """Frontier Mathematics Knowledge Base.

    Provides access to cutting-edge mathematical topics, open problems,
    and research directions.
    """

    def __init__(self):
        self._topics = FRONTIER_TOPICS
        self._categories = self._build_categories()

    def _build_categories(self) -> dict:
        categories = {}
        for topic_id, topic in self._topics.items():
            cat = topic.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(topic_id)
        return categories

    def get_topic(self, topic_id: str) -> Optional[FrontierTopic]:
        """Get a frontier topic by ID."""
        return self._topics.get(topic_id)

    def get_topics_by_category(self, category: str) -> list:
        """Get all topics in a category."""
        topic_ids = self._categories.get(category, [])
        return [self._topics[tid] for tid in topic_ids]

    def get_all_categories(self) -> list:
        """Get all frontier categories."""
        return list(self._categories.keys())

    def search(self, query: str, language: str = "zh") -> list:
        """Search frontier topics by keyword."""
        query_lower = query.lower()
        results = []

        for topic_id, topic in self._topics.items():
            score = 0
            # Check name
            if query_lower in topic.name.lower():
                score += 3
            if query_lower in topic.name_cn:
                score += 3
            # Check description
            if query_lower in topic.description.lower():
                score += 2
            if query_lower in topic.description_cn:
                score += 2
            # Check concepts
            for concept in topic.key_concepts:
                if query_lower in concept.lower():
                    score += 1
            # Check open problems
            for problem in topic.open_problems:
                if query_lower in problem.lower():
                    score += 1

            if score > 0:
                results.append((score, topic))

        results.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in results]

    def get_category_names(self, language: str = "zh") -> dict:
        """Get category names in specified language."""
        names = {
            "algebraic_geometry": "代数几何"
            if language == "zh"
            else "Algebraic Geometry",
            "differential_geometry": "微分几何"
            if language == "zh"
            else "Differential Geometry",
            "category_theory": "范畴论" if language == "zh" else "Category Theory",
            "number_theory": "数论" if language == "zh" else "Number Theory",
            "representation_theory": "表示论"
            if language == "zh"
            else "Representation Theory",
            "mathematical_physics": "数学物理"
            if language == "zh"
            else "Mathematical Physics",
            "homological_algebra": "同调代数"
            if language == "zh"
            else "Homological Algebra",
            "k_theory": "K 理论" if language == "zh" else "K-Theory",
        }
        return names

    def generate_overview(self, language: str = "zh") -> str:
        """Generate an overview of all frontier topics."""
        parts = []
        if language == "zh":
            parts.append("# 前沿数学领域概览\n")
            parts.append(
                f"共收录 {len(self._topics)} 个前沿研究方向，涵盖 {len(self._categories)} 个主要领域。\n"
            )

            cat_names = self.get_category_names("zh")
            for cat, topic_ids in self._categories.items():
                parts.append(f"\n## {cat_names.get(cat, cat)}\n")
                for tid in topic_ids:
                    topic = self._topics[tid]
                    parts.append(f"### {topic.name_cn} ({topic.name})\n")
                    parts.append(f"{topic.description_cn}\n")
                    if topic.open_problems:
                        parts.append("**开放问题:**\n")
                        for p in topic.open_problems[:3]:
                            parts.append(f"- {p}\n")
        else:
            parts.append("# Frontier Mathematics Overview\n")
            parts.append(
                f"Covering {len(self._topics)} research areas across {len(self._categories)} major fields.\n"
            )

            cat_names = self.get_category_names("en")
            for cat, topic_ids in self._categories.items():
                parts.append(f"\n## {cat_names.get(cat, cat)}\n")
                for tid in topic_ids:
                    topic = self._topics[tid]
                    parts.append(f"### {topic.name}\n")
                    parts.append(f"{topic.description}\n")
                    if topic.open_problems:
                        parts.append("**Open Problems:**\n")
                        for p in topic.open_problems[:3]:
                            parts.append(f"- {p}\n")

        return "\n".join(parts)
