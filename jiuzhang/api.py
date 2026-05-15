"""Unified Python API for JiuZhang.

Provides a simple interface for all JiuZhang functionality.
"""

from typing import Optional

from jiuzhang.core.config import Config
from jiuzhang.core.multi_provider_api import MultiProviderClient
from jiuzhang.math_engine.curriculum import Curriculum
from jiuzhang.math_engine.lesson import LessonGenerator
from jiuzhang.math_engine.visualizer import Visualizer
from jiuzhang.core.errors import ToolResult
from jiuzhang.courses.registry import CourseRegistry
from jiuzhang.research.engine import ResearchEngine, ResearchResult
from jiuzhang.research.assistant import FrontierResearchAssistant
from jiuzhang.research.open_problems import OpenProblemsDB
from jiuzhang.research.counterexamples import CounterexampleFinder, ConjectureVerifier
from jiuzhang.research.latex_generator import LaTeXPaperGenerator
from jiuzhang.research.proof_assistant import ProofAssistant, Proof

# Solver and Reasoning
from jiuzhang.solver.method_registry import MethodRegistry
from jiuzhang.solver.problem_classifier import ProblemClassifier
from jiuzhang.solver.pipeline import SolverPipeline
from jiuzhang.reasoning.hybrid_engine import HybridReasoningEngine
from jiuzhang.reasoning.proof_generator import ProofGenerator, ProofStrategy


class JiuZhangAPI:
    """Main API for JiuZhang.

    Example:
        >>> from jiuzhang.api import JiuZhangAPI
        >>> api = JiuZhangAPI()
        >>> result = api.learn("什么是分数")
        >>> print(result.data)
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._client = None
        self._registry = None
        self._curriculum = None
        self._lesson_gen = None
        self._research_engine = None
        self._frontier = None
        self._method_registry = None
        self._problem_classifier = None
        self._solver = None
        self._reasoning_engine = None
        self._proof_generator = None
        self.open_problems = OpenProblemsDB()
        self.counterexample_finder = CounterexampleFinder()
        self.latex_generator = LaTeXPaperGenerator()
        self.proof_assistant = ProofAssistant()

    @property
    def client(self) -> MultiProviderClient:
        if self._client is None:
            self._client = MultiProviderClient(self.config)
        return self._client

    @property
    def registry(self) -> CourseRegistry:
        if self._registry is None:
            self._registry = CourseRegistry()
        return self._registry

    @property
    def curriculum(self) -> Curriculum:
        if self._curriculum is None:
            self._curriculum = self.registry.build_curriculum()
        return self._curriculum

    @property
    def lesson_gen(self) -> LessonGenerator:
        if self._lesson_gen is None:
            self._lesson_gen = LessonGenerator(self.config)
        return self._lesson_gen

    @property
    def research_engine(self) -> ResearchEngine:
        if self._research_engine is None:
            self._research_engine = ResearchEngine(self.config)
        return self._research_engine

    @property
    def frontier(self) -> FrontierResearchAssistant:
        if self._frontier is None:
            self._frontier = FrontierResearchAssistant(self.config)
        return self._frontier

    def learn(self, topic: str, level: str = "elementary") -> ToolResult:
        """Learn a mathematics topic."""
        return self.lesson_gen.generate_lesson(
            topic, level=level, language=self.config.language
        )

    def exercise(
        self, topic: str, difficulty: str = "easy", count: int = 3
    ) -> ToolResult:
        """Generate exercises."""
        return self.lesson_gen.generate_exercise(
            topic, difficulty=difficulty, count=count, language=self.config.language
        )

    def explain(self, concept: str, level: str = "beginner") -> ToolResult:
        """Explain a math concept."""
        return self.client.explain_concept(
            concept, level=level, language=self.config.language
        )

    def visualize_number_line(
        self, start: float = -10, end: float = 10, highlight: Optional[list] = None
    ) -> ToolResult:
        """Visualize a number line."""
        return Visualizer.plot_number_line(start=start, end=end, highlight=highlight)

    def visualize_function(
        self, func, x_range: tuple = (-10, 10), title: str = "Function"
    ) -> ToolResult:
        """Visualize a mathematical function."""
        return Visualizer.plot_function(func, x_range=x_range, title=title)

    def visualize_scatter(self, x, y, title: str = "Scatter Plot") -> ToolResult:
        """Create a scatter plot."""
        return Visualizer.plot_scatter(x, y, title=title)

    def visualize_bar(
        self, categories: list, values: list, title: str = "Bar Chart"
    ) -> ToolResult:
        """Create a bar chart."""
        return Visualizer.plot_bar(categories, values, title=title)

    def visualize_histogram(
        self, data, bins: int = 30, title: str = "Histogram"
    ) -> ToolResult:
        """Create a histogram."""
        return Visualizer.plot_histogram(data, bins=bins, title=title)

    def visualize_matrix(self, matrix, title: str = "Matrix") -> ToolResult:
        """Visualize a matrix."""
        return Visualizer.plot_matrix(matrix, title=title)

    def get_courses(self) -> dict:
        """Get all available courses."""
        return self.registry.get_stats()

    def get_knowledge_points(self, category: Optional[str] = None) -> list:
        """Get knowledge points, optionally filtered by category."""
        if category:
            return self.registry.get_knowledge_points_by_category(category)
        return self.registry.get_all_knowledge_points()

    def set_provider(self, provider: str, model: Optional[str] = None):
        """Set the AI provider."""
        self.config.active_provider = provider
        if model:
            self.config.active_model = model
        self._client = MultiProviderClient(self.config)
        self._lesson_gen = LessonGenerator(self.config)

    def save_config(self):
        """Save current configuration."""
        self.config.save()

    def research(
        self,
        query: str,
        depth: str = "medium",
        include_code: bool = True,
        include_visualization: bool = True,
        include_literature: bool = True,
    ) -> ResearchResult:
        """Conduct complete mathematical research on a topic.

        Searches literature, performs derivation, generates experiments and visualizations.

        Args:
            query: Research query
            depth: Research depth (shallow/medium/deep)
            include_code: Include experiment code
            include_visualization: Include visualizations
            include_literature: Search arXiv literature

        Returns:
            ResearchResult with complete research output
        """
        return self.research_engine.research(
            query=query,
            language=self.config.language,
            depth=depth,
            include_code=include_code,
            include_visualization=include_visualization,
            include_literature=include_literature,
        )

    def get_research_history(self) -> list:
        """Get list of past research results."""
        return self.research_engine.get_research_history()

    def load_research(self, filename: str) -> Optional[dict]:
        """Load a past research result."""
        return self.research_engine.load_research(filename)

    def frontier_research(
        self,
        query: str,
        depth: str = "deep",
        include_papers: bool = True,
        include_visualization: bool = True,
    ) -> str:
        """Conduct frontier mathematics research.

        Searches knowledge base, performs advanced symbolic computation,
        finds papers, and generates visualizations.

        Args:
            query: Research query
            depth: Research depth
            include_papers: Search arXiv papers
            include_visualization: Suggest visualizations

        Returns:
            Complete frontier research report
        """
        return self.frontier.research(
            query=query,
            language=self.config.language,
            include_papers=include_papers,
            include_visualization=include_visualization,
            depth=depth,
        )

    def get_frontier_overview(self) -> str:
        """Get overview of all frontier mathematics topics."""
        return self.frontier.get_frontier_overview(self.config.language)

    def read_paper(self, arxiv_id: str) -> str:
        """Read and summarize an arXiv paper.

        Args:
            arxiv_id: arXiv ID (e.g., "2401.12345")

        Returns:
            Paper summary
        """
        return self.frontier.read_paper(arxiv_id, self.config.language)

    def generate_frontier_viz(self, viz_type: str, **kwargs) -> Optional[str]:
        """Generate frontier mathematics visualization.

        Args:
            viz_type: Type (torus, mobius, klein, root_system, fractal, complex, vector_field, 3d_surface)
            **kwargs: Visualization parameters

        Returns:
            Base64 encoded image or None
        """
        return self.frontier.generate_visualization(viz_type, **kwargs)

    # Open Problems
    def get_open_problem(self, problem_id: str) -> Optional[dict]:
        """Get details of an open problem.

        Args:
            problem_id: Problem ID (e.g., "riemann_hypothesis")

        Returns:
            Problem details dictionary
        """
        problem = self.open_problems.get_problem(problem_id)
        if problem:
            return {
                "id": problem.id,
                "name": problem.name,
                "name_cn": problem.name_cn,
                "field": problem.field,
                "description": problem.description,
                "description_cn": problem.description_cn,
                "status": problem.status,
                "prize": problem.prize,
                "key_approaches": problem.key_approaches,
                "difficulty": problem.difficulty,
                "year_proposed": problem.year_proposed,
            }
        return None

    def search_open_problems(self, query: str) -> list:
        """Search open problems by keyword.

        Args:
            query: Search query

        Returns:
            List of matching problems
        """
        problems = self.open_problems.search(query, self.config.language)
        return [
            {
                "id": p.id,
                "name": p.name,
                "name_cn": p.name_cn,
                "status": p.status,
                "difficulty": p.difficulty,
            }
            for p in problems
        ]

    def get_millennium_problems(self) -> list:
        """Get the 7 Millennium Prize Problems."""
        problems = self.open_problems.get_millennium_problems()
        return [
            {
                "id": p.id,
                "name": p.name,
                "name_cn": p.name_cn,
                "status": p.status,
                "prize": p.prize,
            }
            for p in problems
        ]

    def get_open_problems_report(self) -> str:
        """Get a report of all open problems."""
        return self.open_problems.generate_report(self.config.language)

    # Counterexample Search
    def test_goldbach(self, max_n: int = 1000) -> dict:
        """Test Goldbach's conjecture.

        Args:
            max_n: Maximum even number to test

        Returns:
            Test results
        """
        return self.counterexample_finder.goldbach_test(max_n)

    def test_collatz(self, max_n: int = 100000) -> dict:
        """Test Collatz conjecture.

        Args:
            max_n: Maximum number to test

        Returns:
            Test results
        """
        return self.counterexample_finder.collatz_test(max_n)

    def test_fermat_last_theorem(self, exponent: int = 3, max_val: int = 100) -> dict:
        """Test Fermat's Last Theorem for small cases.

        Args:
            exponent: Exponent to test
            max_val: Maximum value to test

        Returns:
            Test results
        """
        return self.counterexample_finder.fermat_last_theorem_check(exponent, max_val)

    def test_custom_conjecture(
        self,
        conjecture_fn,
        domain: str = "integers",
        range_start: int = 1,
        range_end: int = 1000,
        description: str = "",
    ) -> dict:
        """Test a custom conjecture.

        Args:
            conjecture_fn: Function that returns True if conjecture holds
            domain: Type of domain
            range_start: Start of test range
            range_end: End of test range
            description: Description of conjecture

        Returns:
            Test results
        """
        return self.counterexample_finder.test_conjecture(
            conjecture_fn, domain, range_start, range_end, description
        )

    # Proof Assistant
    def create_proof(self, theorem: str, context: str = "") -> Proof:
        """Create a new proof.

        Args:
            theorem: Theorem statement
            context: Additional context

        Returns:
            Proof object
        """
        return self.proof_assistant.create_proof(theorem, context)

    def verify_identity(self, lhs, rhs, variables: list) -> dict:
        """Verify an algebraic identity.

        Args:
            lhs: Left-hand side (sympy expression)
            rhs: Right-hand side (sympy expression)
            variables: List of variables

        Returns:
            Verification result
        """
        return self.proof_assistant.verify_algebraic_identity(lhs, rhs, variables)

    def generate_proof_template(self, theorem_type: str, topic: str) -> Proof:
        """Generate a proof template.

        Args:
            theorem_type: Type (direct, contradiction, induction, contrapositive)
            topic: Topic description

        Returns:
            Proof template
        """
        return self.proof_assistant.generate_proof_template(theorem_type, topic)

    # LaTeX Generation
    def generate_latex_paper(
        self,
        title: str,
        author: str,
        abstract: str,
        sections: list,
        output_path: Optional[str] = None,
    ) -> str:
        """Generate a LaTeX paper.

        Args:
            title: Paper title
            author: Author name
            abstract: Abstract text
            sections: List of section dictionaries
            output_path: Output file path

        Returns:
            LaTeX source code
        """
        return self.latex_generator.generate_paper(
            title, author, abstract, sections, output_path=output_path
        )

    def generate_latex_from_research(
        self,
        research_result,
        author: str = "JiuZhang Research Assistant",
        output_path: Optional[str] = None,
    ) -> str:
        """Generate a LaTeX paper from research results.

        Args:
            research_result: ResearchResult object
            author: Author name
            output_path: Output file path

        Returns:
            LaTeX source code
        """
        return self.latex_generator.generate_from_research(
            research_result, author, output_path=output_path
        )

    def generate_beamer_presentation(
        self, title: str, author: str, slides: list, output_path: Optional[str] = None
    ) -> str:
        """Generate a Beamer presentation.

        Args:
            title: Presentation title
            author: Author name
            slides: List of slide dictionaries
            output_path: Output file path

        Returns:
            LaTeX Beamer source code
        """
        return self.latex_generator.generate_beamer_presentation(
            title, author, slides, output_path=output_path
        )

    # === Solver & Reasoning ===

    @property
    def method_registry(self) -> MethodRegistry:
        if self._method_registry is None:
            self._method_registry = MethodRegistry()
        return self._method_registry

    @property
    def problem_classifier(self) -> ProblemClassifier:
        if self._problem_classifier is None:
            self._problem_classifier = ProblemClassifier(self.method_registry)
        return self._problem_classifier

    @property
    def solver(self) -> SolverPipeline:
        if self._solver is None:
            self._solver = SolverPipeline(self.method_registry, self.problem_classifier)
        return self._solver

    @property
    def reasoning_engine(self) -> HybridReasoningEngine:
        if self._reasoning_engine is None:
            self._reasoning_engine = HybridReasoningEngine(self.config, self.method_registry)
        return self._reasoning_engine

    @property
    def proof_generator(self) -> ProofGenerator:
        if self._proof_generator is None:
            self._proof_generator = ProofGenerator()
        return self._proof_generator

    def solve(self, problem: str, language: str = "zh"):
        """Solve a mathematical problem with step-by-step solution.

        Args:
            problem: The problem statement
            language: Output language

        Returns:
            SolveResult with complete solution trace
        """
        return self.solver.solve(problem, language)

    def classify_problem(self, problem: str, language: str = "zh"):
        """Classify a mathematical problem.

        Args:
            problem: The problem statement
            language: Language code

        Returns:
            ProblemType classification
        """
        return self.problem_classifier.classify(problem, language)

    def reason(self, problem: str, language: str = "zh", mode: str = "full"):
        """Perform hybrid reasoning on a problem.

        Args:
            problem: The problem statement
            language: Output language
            mode: "symbolic", "llm", or "full"

        Returns:
            ReasoningResult with complete analysis
        """
        return self.reasoning_engine.reason(problem, language, mode)

    def generate_proof(self, theorem: str, strategy=None, language: str = "zh"):
        """Generate a structured mathematical proof.

        Args:
            theorem: The theorem to prove
            strategy: Proof strategy (auto-detected if None)
            language: Output language

        Returns:
            Proof object with steps and verification
        """
        return self.proof_generator.generate(theorem, strategy, language)

    def list_methods(self, category: Optional[str] = None):
        """List available mathematical methods.

        Args:
            category: Filter by category (optional)

        Returns:
            List of MathMethod objects
        """
        if category:
            from jiuzhang.solver.method_registry import MethodCategory
            cat = MethodCategory(category)
            return self.method_registry.get_by_category(cat)
        return self.method_registry.get_all()

    def find_methods_for(self, problem: str):
        """Find applicable methods for a problem.

        Args:
            problem: The problem statement

        Returns:
            List of (method, confidence_score) tuples
        """
        return self.method_registry.match_methods(problem)

    def chain_methods_for(self, problem: str):
        """Build optimal method chain for a problem.

        Args:
            problem: The problem statement

        Returns:
            List of MathMethod objects in execution order
        """
        return self.method_registry.chain_methods(problem)
