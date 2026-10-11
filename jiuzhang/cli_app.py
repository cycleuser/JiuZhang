"""CLI application for JiuZhang with full i18n support."""

import sys
from dataclasses import dataclass, field
from typing import Optional
import readline  # For command history
import os
import hashlib

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.tree import Tree

from jiuzhang.core.config import Config
from jiuzhang.core.multi_provider_api import MultiProviderClient
from jiuzhang.math_engine.lesson import LessonGenerator
from jiuzhang.math_engine.visualizer import Visualizer
from jiuzhang.courses.registry import CourseRegistry
from jiuzhang.i18n import I18n, SUPPORTED_LANGUAGES
from jiuzhang.research.engine import ResearchEngine
from jiuzhang.research.assistant import FrontierResearchAssistant
from jiuzhang.research.open_problems import OpenProblemsDB
from jiuzhang.research.counterexamples import CounterexampleFinder
from jiuzhang.research.latex_generator import LaTeXPaperGenerator
from jiuzhang.research.proof_assistant import ProofAssistant
from jiuzhang.visualization.tui_viz import (
    plot_number_line_tui,
    plot_bar_chart_tui,
    plot_function_tui,
    show_multiplication_table_tui,
    show_fraction_visualizer_tui,
)
from jiuzhang.learning_tracker import LearningTracker
from jiuzhang.math_reasoning import MathReasoningEngine
from jiuzhang.solver import MethodRegistry, ProblemClassifier, SolverPipeline
from jiuzhang.reasoning import HybridReasoningEngine, ProofGenerator
from jiuzhang.assessment import AssessmentEngine, Difficulty, QuizConfig


console = Console()


@dataclass
class AppContext:
    """Context object holding all CLI application components.

    Replaces the need to pass 12 individual parameters to repl_loop.
    Components are lazily initialized on first access.
    """

    config: Config
    i18n: I18n

    _client: Optional[MultiProviderClient] = field(default=None, repr=False)
    _registry: Optional[CourseRegistry] = field(default=None, repr=False)
    _curriculum: Optional = field(default=None, repr=False)
    _lesson_gen: Optional[LessonGenerator] = field(default=None, repr=False)
    _research_engine: Optional[ResearchEngine] = field(default=None, repr=False)
    _frontier: Optional[FrontierResearchAssistant] = field(default=None, repr=False)
    _open_problems: Optional[OpenProblemsDB] = field(default=None, repr=False)
    _counterexample_finder: Optional[CounterexampleFinder] = field(default=None, repr=False)
    _latex_generator: Optional[LaTeXPaperGenerator] = field(default=None, repr=False)
    _proof_assistant: Optional[ProofAssistant] = field(default=None, repr=False)
    _learning_tracker: Optional[LearningTracker] = field(default=None, repr=False)
    _math_reasoning: Optional[MathReasoningEngine] = field(default=None, repr=False)
    _method_registry: Optional[MethodRegistry] = field(default=None, repr=False)
    _problem_classifier: Optional[ProblemClassifier] = field(default=None, repr=False)
    _solver: Optional[SolverPipeline] = field(default=None, repr=False)
    _reasoning_engine: Optional[HybridReasoningEngine] = field(default=None, repr=False)
    _proof_generator: Optional[ProofGenerator] = field(default=None, repr=False)
    _assessment: Optional[AssessmentEngine] = field(default=None, repr=False)

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
    def curriculum(self):
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

    @property
    def open_problems(self) -> OpenProblemsDB:
        if self._open_problems is None:
            self._open_problems = OpenProblemsDB()
        return self._open_problems

    @property
    def counterexample_finder(self) -> CounterexampleFinder:
        if self._counterexample_finder is None:
            self._counterexample_finder = CounterexampleFinder()
        return self._counterexample_finder

    @property
    def latex_generator(self) -> LaTeXPaperGenerator:
        if self._latex_generator is None:
            self._latex_generator = LaTeXPaperGenerator()
        return self._latex_generator

    @property
    def proof_assistant(self):
        if self._proof_assistant is None:
            self._proof_assistant = ProofAssistant(self.client)
        return self._proof_assistant

    @property
    def learning_tracker(self):
        if self._learning_tracker is None:
            self._learning_tracker = LearningTracker(user_id=self.config.user_id if hasattr(self.config, 'user_id') else 'cli_user')
        return self._learning_tracker

    @property
    def math_reasoning(self):
        if self._math_reasoning is None:
            self._math_reasoning = MathReasoningEngine(self.client, self.config)
        return self._math_reasoning

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

    @property
    def assessment(self) -> AssessmentEngine:
        if self._assessment is None:
            self._assessment = AssessmentEngine()
        return self._assessment


def main(args: Optional[list] = None):
    """Main CLI entry point."""
    config = Config.load()
    i18n = I18n(default_language=config.language)
    ctx = AppContext(config=config, i18n=i18n)

    if not args:
        repl_loop(ctx)
        return

    command = args[0]
    if command == "learn":
        topic = " ".join(args[1:]) if len(args) > 1 else ctx.i18n.t("natural_numbers")
        cmd_learn(topic, ctx)
    elif command == "exercise":
        topic = " ".join(args[1:]) if len(args) > 1 else ctx.i18n.t("natural_numbers")
        cmd_exercise(topic, ctx)
    elif command == "research":
        query = " ".join(args[1:]) if len(args) > 1 else "傅里叶变换"
        cmd_research(query, ctx)
    elif command == "frontier":
        query = " ".join(args[1:]) if len(args) > 1 else "朗兰兹纲领"
        cmd_frontier(query, ctx)
    elif command == "problems":
        query = " ".join(args[1:]) if len(args) > 1 else ""
        cmd_open_problems(query, ctx)
    elif command == "test":
        conjecture = " ".join(args[1:]) if len(args) > 1 else "goldbach"
        cmd_test_conjecture(conjecture, ctx)
    elif command == "visualize":
        viz_type = args[1] if len(args) > 1 else "number_line"
        cmd_visualize(viz_type, ctx)
    elif command == "config":
        cmd_config(ctx)
    elif command == "courses":
        cmd_courses(ctx)
    elif command == "stats":
        cmd_stats(ctx)
    elif command == "lang":
        lang = args[1] if len(args) > 1 else ctx.config.language
        cmd_language(lang, ctx)
    elif command == "history":
        cmd_history(ctx)
    elif command == "paper":
        arxiv_id = args[1] if len(args) > 1 else ""
        cmd_read_paper(arxiv_id, ctx)
    elif command == "latex":
        title = " ".join(args[1:]) if len(args) > 1 else "My Research Paper"
        cmd_generate_latex(title, ctx)
    elif command == "recommendations":
        cmd_recommendations(ctx)
    elif command == "math_prove":
        theorem = " ".join(args[1:]) if len(args) > 1 else "勾股定理"
        cmd_math_prove(theorem, ctx)
    elif command == "math_solve":
        problem = " ".join(args[1:]) if len(args) > 1 else "解方程 x² - 5x + 6 = 0"
        cmd_math_solve(problem, ctx)
    elif command == "math_analyze":
        conjecture = " ".join(args[1:]) if len(args) > 1 else "哥德巴赫猜想"
        cmd_math_analyze(conjecture, ctx)
    elif command == "math_compute":
        expression = " ".join(args[1:]) if len(args) > 1 else "integrate(x^2, x)"
        cmd_math_compute(expression, ctx)
    elif command == "benchmark":
        cmd_benchmark(ctx)
    elif command == "discover":
        max_n = int(args[1]) if len(args) > 1 else 500
        cmd_discover(ctx, max_n)
    elif command == "train":
        cmd_train_model(ctx)
    elif command == "distill":
        cmd_distill(ctx)
    elif command == "low_vram":
        cmd_low_vram_train(ctx)
    elif command == "solve":
        problem = " ".join(args) if args else "x^2 - 5x + 6 = 0"
        cmd_solve(problem, ctx)
    elif command == "classify":
        problem = " ".join(args) if args else "解方程 x^2 - 5x + 6 = 0"
        cmd_classify(problem, ctx)
    elif command == "reason":
        problem = " ".join(args) if args else "证明根号2是无理数"
        cmd_reason(problem, ctx)
    elif command == "methods":
        cmd_methods(ctx, " ".join(args) if args else "")
    elif command == "quiz":
        cmd_quiz(ctx, " ".join(args) if args else "")
    elif command == "proof_gen":
        theorem = " ".join(args) if args else "勾股定理"
        cmd_proof_gen(theorem, ctx)
    else:
        console.print(f"[red]{ctx.i18n.t('unknown_command')}: {command}[/red]")
        console.print(
            f"{ctx.i18n.t('available_commands')}: learn, exercise, research, frontier, problems, test, paper, latex, visualize, config, courses, stats, recommendations, math_prove, math_solve, math_analyze, math_compute, benchmark, discover, train, distill, low_vram, lang, history"
        )


def repl_loop(ctx: AppContext):
    """Main REPL loop with full i18n support and command history."""
    # Setup command history
    histfile = os.path.expanduser("~/.jiuzhang_history")
    try:
        readline.read_history_file(histfile)
        # Set maximum number of history entries
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass  # New user, history file doesn't exist yet

    console.print(
        ctx.i18n.t("welcome_message").format(
            version=__import__("jiuzhang").__version__
        ),
        style="bold green",
    )
    console.print(ctx.i18n.t("help_tip"), style="italic")

    while True:
        try:
            cmd_input = Prompt.ask(
                ctx.i18n.t("prompt"),
                default="",
                show_default=False,
            ).strip()

            if not cmd_input:
                continue

            # Save command to history
            if cmd_input.lower() not in ["quit", "exit", "q", "history"]:
                readline.add_history(cmd_input)

            if cmd_input.lower() in ["quit", "exit", "q"]:
                # Save history before exiting
                readline.write_history_file(histfile)
                console.print(ctx.i18n.t("farewell_message"))
                break
            elif cmd_input.lower() == "history":
                # Show command history
                console.print("[bold]Command History:[/bold]")
                for i in range(readline.get_current_history_length()):
                    item = readline.get_history_item(i + 1)
                    if item:
                        console.print(f"{i + 1}: {item}")
                continue

            parts = cmd_input.split(maxsplit=1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            handler = COMMAND_HANDLERS.get(cmd)
            if handler:
                handler(ctx, args)
            else:
                console.print(
                    ctx.i18n.t("unknown_command").format(command=cmd_input),
                    style="bold red",
                )
                console.print(ctx.i18n.t("help_tip"))

        except KeyboardInterrupt:
            # Save history before exiting
            readline.write_history_file(histfile)
            console.print("\n" + ctx.i18n.t("farewell_message"))
            break
        except EOFError:
            # Save history before exiting
            readline.write_history_file(histfile)
            console.print("\n" + ctx.i18n.t("farewell_message"))
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            console.print(f"[yellow]{ctx.i18n.t('goodbye')}[/yellow]")
            break

        if user_input.lower() == "help":
            show_help(ctx)
            continue

        if user_input.lower().startswith("learn "):
            topic = user_input[6:].strip()
            cmd_learn(topic, ctx)
        elif user_input.lower().startswith("exercise "):
            topic = user_input[9:].strip()
            cmd_exercise(topic, ctx)
        elif user_input.lower().startswith("research "):
            query = user_input[9:].strip()
            cmd_research(query, ctx)
        elif user_input.lower().startswith("frontier "):
            query = user_input[9:].strip()
            cmd_frontier(query, ctx)
        elif user_input.lower().startswith("problems "):
            query = user_input[9:].strip()
            cmd_open_problems(query, ctx)
        elif user_input.lower().startswith("test "):
            conjecture = user_input[5:].strip()
            cmd_test_conjecture(conjecture, ctx)
        elif user_input.lower().startswith("paper "):
            arxiv_id = user_input[6:].strip()
            cmd_read_paper(arxiv_id, ctx)
        elif user_input.lower().startswith("latex "):
            title = user_input[6:].strip()
            cmd_generate_latex(title, ctx)
        elif user_input.lower().startswith("visualize "):
            viz_type = user_input[10:].strip()
            cmd_visualize(viz_type, ctx)
        elif user_input.lower() == "config":
            cmd_config(ctx)
        elif user_input.lower() == "courses":
            cmd_courses(ctx)
        elif user_input.lower() == "stats":
            cmd_stats(ctx)
        elif user_input.lower() == "recommendations":
            cmd_recommendations(ctx)
        elif user_input.lower().startswith("math_prove "):
            theorem = user_input[11:].strip()
            cmd_math_prove(theorem, ctx)
        elif user_input.lower().startswith("math_solve "):
            problem = user_input[11:].strip()
            cmd_math_solve(problem, ctx)
        elif user_input.lower().startswith("math_analyze "):
            conjecture = user_input[13:].strip()
            cmd_math_analyze(conjecture, ctx)
        elif user_input.lower().startswith("math_compute "):
            expression = user_input[13:].strip()
            cmd_math_compute(expression, ctx)
        elif user_input.lower() == "benchmark":
            cmd_benchmark(ctx)
        elif user_input.lower().startswith("discover"):
            parts = user_input.split(maxsplit=1)
            max_n = int(parts[1].strip()) if len(parts) > 1 else 500
            cmd_discover(ctx, max_n)
        elif user_input.lower() == "train":
            cmd_train_model(ctx)
        elif user_input.lower() == "distill":
            cmd_distill(ctx)
        elif user_input.lower() == "low_vram":
            cmd_low_vram_train(ctx)
        elif user_input.lower() == "history":
            cmd_history(ctx)
        elif user_input.lower() == "multiplication":
            show_multiplication_table_tui()
        elif user_input.lower().startswith("fraction "):
            parts = user_input[9:].strip().split("/")
            if len(parts) == 2:
                try:
                    show_fraction_visualizer_tui(int(parts[0]), int(parts[1]))
                except ValueError:
                    console.print(f"[red]{ctx.i18n.t('fraction')}: 3/4[/red]")
            else:
                console.print(f"[red]{ctx.i18n.t('fraction')} <n/d>[/red]")
        elif user_input.lower().startswith("lang "):
            lang = user_input[5:].strip()
            cmd_language(lang, ctx)
        else:
            cmd_learn(user_input, ctx)


def cmd_solve(problem: str, ctx: AppContext):
    """Solve a math problem using the solver pipeline."""
    console.print(f"\n[bold blue]🧮 Solving: {problem}[/bold blue]\n")

    with console.status("[bold green]Classifying and solving...", spinner="dots"):
        result = ctx.solver.solve(problem)

    console.print(f"[bold]Classification:[/bold] {result.problem_type}")
    console.print(f"[bold]Complexity:[/bold] {result.complexity}")
    console.print(f"[bold]Method Chain:[/bold] {' → '.join(m.name for m in result.method_chain) if result.method_chain else 'None'}")

    if result.steps:
        console.print(f"\n[bold]Solution Steps:[/bold]")
        for i, step in enumerate(result.steps, 1):
            console.print(f"  {i}. {step}")

    if result.answer:
        console.print(f"\n[bold green]Answer: {result.answer}[/bold green]")
    elif result.symbolic_result:
        console.print(f"\n[bold green]Result: {result.symbolic_result}[/bold green]")


def cmd_classify(problem: str, ctx: AppContext):
    """Classify a math problem."""
    console.print(f"\n[bold blue]🔍 Classifying: {problem}[/bold blue]\n")

    result = ctx.problem_classifier.classify(problem)

    table = Table(title="Problem Classification")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Domain", result.domain)
    table.add_row("Problem Type", str(result.problem_type))
    table.add_row("Difficulty", result.difficulty)
    table.add_row("Confidence", f"{result.confidence:.2f}")
    if result.keywords:
        table.add_row("Keywords", ", ".join(result.keywords))
    if result.suggested_methods:
        table.add_row("Suggested Methods", ", ".join(result.suggested_methods))
    console.print(table)


def cmd_reason(problem: str, ctx: AppContext):
    """Hybrid reasoning on a problem."""
    console.print(f"\n[bold blue]🧠 Reasoning: {problem}[/bold blue]\n")

    with console.status("[bold green]Performing hybrid reasoning...", spinner="dots"):
        result = ctx.reasoning_engine.reason(problem)

    console.print(f"[bold]Mode:[/bold] {result.mode}")
    console.print(f"[bold]Confidence:[/bold] {result.confidence:.2f}")

    if result.symbolic_result:
        console.print(f"\n[bold]Symbolic Result:[/bold] {result.symbolic_result}")
    if result.llm_analysis:
        console.print(Markdown(result.llm_analysis))
    if result.verification:
        console.print(f"\n[bold]Verification:[/bold] {result.verification}")
    if result.steps:
        console.print(f"\n[bold]Reasoning Steps:[/bold]")
        for i, step in enumerate(result.steps, 1):
            console.print(f"  {i}. {step}")


def cmd_methods(ctx: AppContext, category: str):
    """List available mathematical methods."""
    if category:
        methods = ctx.method_registry.get_by_category(category)
        console.print(f"\n[bold blue]📐 Methods in '{category}':[/bold blue]\n")
    else:
        methods = ctx.method_registry.get_all()
        console.print(f"\n[bold blue]📐 All Available Methods ({len(methods)}):[/bold blue]\n")

    table = Table()
    table.add_column("ID", style="cyan", max_width=30)
    table.add_column("Name", style="green")
    table.add_column("Category", style="yellow")
    table.add_column("Level", style="magenta")

    for m in methods[:50]:
        table.add_row(m.id, m.name, m.category.value, m.level)

    console.print(table)
    if len(methods) > 50:
        console.print(f"\n[dim]... and {len(methods) - 50} more methods[/dim]")


def cmd_quiz(ctx: AppContext, category: str):
    """Take a quiz."""
    console.print(f"\n[bold blue]📝 JiuZhang Quiz[/bold blue]\n")

    config = QuizConfig(
        category=category,
        difficulty=Difficulty.MEDIUM,
        num_problems=10,
    )

    quiz = ctx.assessment.generate_quiz(config)

    if not quiz["problems"]:
        console.print("[red]No problems found for this category.[/red]")
        console.print(f"Available categories: arithmetic, algebra, geometry, probability, calculus, linear_algebra, number_theory, diff_eq, discrete")
        return

    console.print(f"Quiz ID: {quiz['quiz_id']}")
    console.print(f"Problems: {quiz['total_problems']}")
    console.print(f"Time Limit: {quiz['config']['time_limit_minutes']} min\n")

    answers = {}
    for p in quiz["problems"]:
        q = p["question_cn"] if ctx.i18n.get_language() == "zh" else p["question"]
        console.print(f"[bold]{p['id']}[/bold] ({p['difficulty']}, {p['type']}): {q}")
        if p.get("options_cn") and ctx.i18n.get_language() == "zh":
            for i, opt in enumerate(p["options_cn"]):
                console.print(f"  {chr(65+i)}) {opt}")
        elif p.get("options"):
            for i, opt in enumerate(p["options"]):
                console.print(f"  {chr(65+i)}) {opt}")

        answer = Prompt.ask("Your answer", default="")
        if answer:
            answers[p["id"]] = answer
        console.print()

    report = ctx.assessment.submit_quiz(quiz["quiz_id"], answers)

    console.print(f"\n[bold]Quiz Results[/bold]")
    console.print(f"Correct: {report['correct']}/{report['total_problems']}")
    console.print(f"Score: {report['percentage']:.1f}%\n")

    for r in report["results"]:
        icon = "✅" if r["correct"] else "❌"
        fb = r.get("feedback_cn", r["feedback"]) if ctx.i18n.get_language() == "zh" else r["feedback"]
        console.print(f"  {icon} {r['problem_id']}: {fb}")


def cmd_proof_gen(theorem: str, ctx: AppContext):
    """Generate a structured proof."""
    console.print(f"\n[bold blue]📜 Generating proof: {theorem}[/bold blue]\n")

    with console.status("[bold green]Generating proof...", spinner="dots"):
        proof = ctx.proof_generator.generate(theorem)

    console.print(f"[bold]Strategy:[/bold] {proof.strategy.value if hasattr(proof.strategy, 'value') else proof.strategy}")
    console.print(f"[bold]Theorem:[/bold] {proof.theorem}")

    if proof.steps:
        console.print(f"\n[bold]Proof Steps:[/bold]")
        for i, step in enumerate(proof.steps, 1):
            console.print(f"  {i}. [{step.type.value if hasattr(step.type, 'value') else step.type}] {step.statement}")
            if step.justification:
                console.print(f"     Justification: {step.justification}")

    if proof.conclusion:
        console.print(f"\n[bold green]QED: {proof.conclusion}[/bold green]")


def show_help(ctx: AppContext):
    """Show available commands."""
    t = ctx.i18n.t
    table = Table(title=t("available_commands"))
    table.add_column(t("command"), style="cyan")
    table.add_column(t("description"), style="green")

    table.add_row("learn <topic>", t("learn"))
    table.add_row("exercise <topic>", t("exercise"))
    table.add_row("research <query>", "数学研究（文献搜索、推导、实验）")
    table.add_row("frontier <query>", "前沿数学研究（知识库、符号计算、论文）")
    table.add_row("problems [query]", "开放问题数据库（千禧年大奖问题等）")
    table.add_row("test <conjecture>", "猜想验证（goldbach, collatz, fermat）")
    table.add_row("paper <arxiv_id>", "阅读 arXiv 论文")
    table.add_row("latex <title>", "生成 LaTeX 论文")
    table.add_row("history", "查看研究历史")
    table.add_row("visualize <type>", t("visualize"))
    table.add_row("courses", t("courses"))
    table.add_row("stats", t("stats"))
    table.add_row("recommendations", "个性化学习建议")
    table.add_row("math_prove <theorem>", "定理证明")
    table.add_row("math_solve <problem>", "问题求解")
    table.add_row("math_analyze <conjecture>", "猜想分析")
    table.add_row("math_compute <expression>", "符号计算")
    table.add_row("benchmark", "数学评估基准/Math Benchmark")
    table.add_row("discover [max_n]", "猜想发现引擎/Conjecture Discovery")
    table.add_row("train", "训练小模型/Train SmallMathModel")
    table.add_row("distill", "蒸馏在线模型/Distill Online Teacher")
    table.add_row("low_vram", "低显存训练/Low-VRAM Training (慢工出细活)")
    table.add_row("multiplication", t("multiplication_table"))
    table.add_row("fraction <n/d>", t("fraction"))
    table.add_row("lang <code>", t("language"))
    table.add_row("config", t("config"))
    table.add_row("solve <problem>", "Solver pipeline: classify + solve")
    table.add_row("classify <problem>", "Classify problem type and difficulty")
    table.add_row("reason <problem>", "Hybrid symbolic + LLM reasoning")
    table.add_row("methods [category]", "List available mathematical methods")
    table.add_row("quiz [category]", "Take an interactive quiz")
    table.add_row("proof_gen <theorem>", "Generate structured proof")
    table.add_row("help", t("help"))
    table.add_row("quit", t("quit"))

    console.print(table)


def cmd_learn(topic: str, ctx: AppContext):
    """Learn a topic."""
    console.print(f"\n[bold blue]{ctx.i18n.t('learning')}: {topic}[/bold blue]\n")

    # Track lesson start
    ctx.learning_tracker.start_lesson(
        lesson_id=hashlib.md5(topic.encode()).hexdigest()[:8],
        category="unknown",  # Could parse topic to determine category
        level="elementary"
    )

    with console.status(
        f"[bold green]{ctx.i18n.t('generating_lesson')}[/bold green]", spinner="dots"
    ):
        result = ctx.lesson_gen.generate_lesson(
            topic, level="elementary", language=ctx.config.language
        )

    if result.success:
        console.print(Markdown(result.data))
        # Track lesson completion
        ctx.learning_tracker.complete_lesson(
            lesson_id=hashlib.md5(topic.encode()).hexdigest()[:8],
            category="unknown",
            level="elementary",
            time_taken=0  # Could track actual time
        )
    else:
        console.print(f"[red]{ctx.i18n.t('lesson_failed')}: {result.error}[/red]")


def cmd_exercise(topic: str, ctx: AppContext):
    """Generate exercises."""
    console.print(f"\n[bold blue]{ctx.i18n.t('exercise')}: {topic}[/bold blue]\n")

    with console.status(
        f"[bold green]{ctx.i18n.t('generating_exercise')}[/bold green]", spinner="dots"
    ):
        result = ctx.lesson_gen.generate_exercise(
            topic, difficulty="easy", count=3, language=ctx.config.language
        )

    if result.success:
        console.print(Markdown(result.data))
    else:
        console.print(f"[red]{ctx.i18n.t('exercise_failed')}: {result.error}[/red]")


def cmd_visualize(viz_type: str, ctx: AppContext):
    """Create a visualization."""
    t = ctx.i18n.t
    console.print(f"\n[bold blue]{t('visualize')}: {viz_type}[/bold blue]\n")

    if viz_type == "number_line":
        plot_number_line_tui(
            -5, 10, highlight=[0, 1, 2, 3], title=t("natural_numbers")
        )
    elif viz_type == "integers":
        plot_number_line_tui(-10, 10, highlight=[-5, 0, 5], title=t("integers"))
    elif viz_type == "bar":
        plot_bar_chart_tui(
            ["A", "B", "C", "D", "E"], [23, 45, 56, 78, 32], title=t("bar_chart")
        )
    elif viz_type == "function":
        import numpy as np

        plot_function_tui(lambda x: np.sin(x), (-10, 10), title="y = sin(x)")
    elif viz_type == "quadratic":
        import numpy as np

        plot_function_tui(lambda x: x**2 - 4, (-5, 5), title="y = x² - 4")
    else:
        console.print(f"[red]{t('unknown_command')}: {viz_type}[/red]")
        console.print("number_line, integers, bar, function, quadratic")


def cmd_config(ctx: AppContext):
    """Show and edit configuration."""
    t = ctx.i18n.t
    cfg = ctx.config
    table = Table(title=t("current_config"))
    table.add_column(t("setting"), style="cyan")
    table.add_column(t("value"), style="green")

    table.add_row(t("ai_provider"), cfg.active_provider)
    table.add_row(t("model"), cfg.active_model)
    table.add_row(t("language"), ctx.i18n.get_language_name(cfg.language))
    table.add_row(t("max_tokens"), str(cfg.max_tokens))
    table.add_row(t("temperature"), str(cfg.temperature))

    console.print(table)

    if Confirm.ask(f"\n{t('edit_config')}"):
        provider = Prompt.ask(t("ai_provider"), default=cfg.active_provider)
        model = Prompt.ask(t("model"), default=cfg.active_model)
        cfg.active_provider = provider
        cfg.active_model = model
        cfg.save()
        console.print(f"[green]{t('config_saved')}[/green]")


def cmd_courses(ctx: AppContext):
    """Show all available courses."""
    t = ctx.i18n.t
    tree = Tree(f"[bold blue]{t('course_system')}[/bold blue]")

    categories = ctx.registry.get_categories()
    for category in sorted(categories):
        branch = tree.add(f"[bold cyan]{category}[/bold cyan]")
        kps = ctx.registry.get_knowledge_points_by_category(category)
        for kp in kps:
            branch.add(f"{kp.name_cn} ({kp.name})")

    console.print(tree)


def cmd_stats(ctx: AppContext):
    """Show comprehensive statistics."""
    t = ctx.i18n.t
    stats = ctx.registry.get_stats()

    # Course registry stats
    table = Table(title=t("course_stats"))
    table.add_column(t("category"), style="cyan")
    table.add_column(t("knowledge_points"), style="green", justify="right")

    for category, count in sorted(stats["by_category"].items()):
        table.add_row(category, str(count))

    table.add_row(
        f"[bold]{t('total')}[/bold]",
        f"[bold]{stats['total_knowledge_points']}[/bold]",
    )

    console.print(table)

    level_table = Table(title=t("level_distribution"))
    level_table.add_column(t("level"), style="cyan")
    level_table.add_column(t("knowledge_points"), style="green", justify="right")

    level_names = {
        "elementary": t("elementary"),
        "middle_school": t("middle_school"),
        "high_school": t("high_school"),
        "undergraduate": t("undergraduate"),
        "graduate": t("graduate"),
        "frontier": t("frontier"),
    }

    for level, count in sorted(stats["by_level"].items()):
        name = level_names.get(level, level)
        level_table.add_row(name, str(count))

    console.print(level_table)
    
    # Learning tracker stats
    progress = ctx.learning_tracker.get_progress_summary()
    console.print(f"\n[bold blue]{t('learning_progress')}[/bold blue]\n")
    
    progress_table = Table(show_header=True, header_style="bold magenta")
    progress_table.add_column(t("statistic"), style="cyan")
    progress_table.add_column(t("value"), justify="right", style="green")
    
    progress_table.add_row(t("completed_lessons"), str(progress["completed_lessons"]))
    progress_table.add_row(t("started_lessons"), str(progress["started_lessons"]))
    progress_table.add_row(t("courses_completed"), str(progress["total_courses_completed"]))
    progress_table.add_row(t("topics_mastered"), str(progress["topics_mastered"]))
    progress_table.add_row(t("hours_spent"), str(progress["total_time_spent_hours"]))
    progress_table.add_row(t("current_streak"), f"{progress['current_streak_days']} days")
    progress_table.add_row(t("completion_rate"), f"{progress['completion_rate']}%")
    
    console.print(progress_table)


def cmd_language(lang: str, ctx: AppContext):
    """Change language."""
    if lang in SUPPORTED_LANGUAGES:
        ctx.i18n.set_language(lang)
        ctx.config.language = lang
        ctx.config.save()
        console.print(
            f"[green]{ctx.i18n.t('config_saved')}: {ctx.i18n.get_language_name(lang)}[/green]"
        )
    else:
        console.print(f"[red]Unsupported: {lang}[/red]")
        console.print(f"Supported: {', '.join(SUPPORTED_LANGUAGES.keys())}")


def cmd_research(query: str, ctx: AppContext):
    """Conduct mathematical research."""
    console.print(f"\n[bold blue]🔬 {ctx.i18n.t('research')}: {query}[/bold blue]\n")

    with console.status("[bold green]正在进行数学研究...", spinner="dots") as status:
        status.update("[bold green]步骤 1/5: 分析主题...[/bold green]")
        result = ctx.research_engine.research(
            query=query,
            language=ctx.config.language,
            depth="medium",
            include_code=True,
            include_visualization=True,
            include_literature=True,
        )

    console.print(Markdown(result.full_report))

    if result.papers:
        console.print(f"\n[bold]📚 找到 {len(result.papers)} 篇文献[/bold]")

    if result.experiments:
        console.print(f"\n[bold]🧪 生成 {len(result.experiments)} 个实验[/bold]")

    console.print(f"\n[green]💾 报告已保存到 ~/.jiuzhang/research/[/green]")


def cmd_history(ctx: AppContext):
    """Show research history."""
    history = ctx.research_engine.get_research_history()

    if not history:
        console.print("[yellow]暂无研究历史[/yellow]")
        return

    table = Table(title="研究历史")
    table.add_column("#", style="cyan")
    table.add_column("主题", style="green")
    table.add_column("时间", style="yellow")
    table.add_column("文件", style="blue")

    for i, item in enumerate(history[:20], 1):
        table.add_row(
            str(i),
            item.get("topic", "")[:40],
            item.get("time", "")[:19],
            item.get("file", ""),
        )

    console.print(table)


def cmd_frontier(query: str, ctx: AppContext):
    """Conduct frontier mathematics research."""
    console.print(f"\n[bold blue]🔬 前沿数学研究: {query}[/bold blue]\n")

    with console.status("[bold green]正在进行前沿数学研究...", spinner="dots"):
        result = ctx.frontier.research(
            query=query,
            language=ctx.config.language,
            include_papers=True,
            include_visualization=True,
            depth="deep",
        )

    console.print(Markdown(result))


def cmd_read_paper(arxiv_id: str, ctx: AppContext):
    """Read and summarize an arXiv paper."""
    if not arxiv_id:
        console.print("[red]请提供 arXiv ID，例如：paper 2401.12345[/red]")
        return

    console.print(f"\n[bold blue]📄 阅读论文: {arxiv_id}[/bold blue]\n")

    with console.status("[bold green]正在获取论文...", spinner="dots"):
        summary = ctx.frontier.read_paper(arxiv_id, ctx.i18n.get_language())

    console.print(Markdown(summary))


def cmd_open_problems(query: str, ctx: AppContext):
    """Show open problems in mathematics."""
    t = ctx.i18n.get_language
    if not query:
        console.print("\n[bold blue]数学开放问题[/bold blue]\n")
        report = ctx.open_problems.generate_report(t())
        console.print(Markdown(report))
    else:
        console.print(f"\n[bold blue]搜索开放问题：{query}[/bold blue]\n")
        problems = ctx.open_problems.search(query, t())
        if problems:
            for p in problems:
                console.print(f"{p.name_cn} ({p.name})")
                console.print(f"  领域：{p.field}")
                console.print(f"  状态：{p.status}")
                console.print(f"  难度：{p.difficulty}")
                if p.prize:
                    console.print(f"  奖励：{p.prize}")
                console.print(f"  {p.description_cn}")
                console.print()
        else:
            console.print("[yellow]未找到相关开放问题[/yellow]")


def cmd_test_conjecture(conjecture: str, ctx: AppContext):
    """Test a mathematical conjecture."""
    console.print(f"\n[bold blue]猜想验证：{conjecture}[/bold blue]\n")

    if conjecture.lower() == "goldbach" or "哥德巴赫" in conjecture:
        result = ctx.counterexample_finder.goldbach_test(1000)
    elif conjecture.lower() == "collatz" or "考拉兹" in conjecture:
        result = ctx.counterexample_finder.collatz_test(10000)
    elif conjecture.lower() == "fermat" or "费马" in conjecture:
        result = ctx.counterexample_finder.fermat_last_theorem_check(3, 50)
    elif conjecture.lower() == "euler" or "欧拉" in conjecture:
        result = ctx.counterexample_finder.euler_sum_of_powers_test()
    else:
        console.print(f"[red]未知猜想：{conjecture}[/red]")
        console.print("可用：goldbach, collatz, fermat, euler")
        return

    console.print(f"{result.get('conjecture', '')}")
    console.print(f"状态：{result.get('status', '')}")
    if result.get("counterexamples"):
        console.print(f"反例：{result['counterexamples'][:5]}")
    console.print(f"验证数量：{result.get('verified_count', 0)}")


def cmd_generate_latex(title: str, ctx: AppContext):
    """Generate a LaTeX paper template."""
    console.print(f"\n[bold blue]📝 生成 LaTeX 论文: {title}[/bold blue]\n")

    sections = [
        {
            "title": "Introduction",
            "content": "This paper presents a study of " + title + ".",
            "level": "section",
        },
        {
            "title": "Main Results",
            "content": "Our main results are as follows...",
            "level": "section",
        },
        {
            "title": "Conclusion",
            "content": "In conclusion, we have shown...",
            "level": "section",
        },
    ]

    output_path = f"research_output/{title.replace(' ', '_')}.tex"
    latex = ctx.latex_generator.generate_paper(
        title=title,
        author="JiuZhang Research Assistant",
        abstract=f"This paper studies {title}.",
        sections=sections,
        output_path=output_path,
    )

    console.print(f"[green]✅ LaTeX 论文已生成: {output_path}[/green]")
    console.print(f"字数: {len(latex)}")


def cmd_recommendations(ctx: AppContext):
    """Show personalized study recommendations."""
    t = ctx.i18n.t
    console.print(f"\n[bold blue]{t('recommendations')}[/bold blue]\n")
    
    recommendations = ctx.learning_tracker.get_study_recommendations()
    
    for i, rec in enumerate(recommendations, 1):
        console.print(f"{i}. {rec['message']}")
        if 'category' in rec:
            console.print(f"   [italic]Category: {rec['category']}[/italic]")


def cmd_math_prove(theorem: str, ctx: AppContext):
    """Prove a mathematical theorem."""
    t = ctx.i18n.t
    console.print(f"\n[bold blue]🔍 {t('theorem_proof')}: {theorem}[/bold blue]\n")
    
    with console.status("[bold green]正在证明定理...", spinner="dots"):
        result = ctx.math_reasoning.prove_theorem(theorem, language=ctx.config.language)
    
    if result.success:
        console.print(Markdown(result.response))
        console.print(f"\n[green]置信度: {result.confidence:.2f}[/green]")
        
        if result.steps:
            console.print(f"\n[bold]证明步骤/Proof Steps:[/bold]")
            for i, step in enumerate(result.steps, 1):
                console.print(f"  {i}. {step}")
    else:
        console.print(f"[red]❌ 证明失败: {result.error}[/red]")


def cmd_math_solve(problem: str, ctx: AppContext):
    """Solve a mathematical problem."""
    t = ctx.i18n.t
    console.print(f"\n[bold blue]🧮 {t('problem_solving')}: {problem}[/bold blue]\n")
    
    with console.status("[bold green]正在解决问题...", spinner="dots"):
        result = ctx.math_reasoning.solve_problem(problem, language=ctx.config.language)
    
    if result.success:
        console.print(Markdown(result.response))
        console.print(f"\n[green]置信度: {result.confidence:.2f}[/green]")
        
        if result.steps:
            console.print(f"\n[bold]解题步骤/Solution Steps:[/bold]")
            for i, step in enumerate(result.steps, 1):
                console.print(f"  {i}. {step}")
    else:
        console.print(f"[red]❌ 解决失败: {result.error}[/red]")


def cmd_math_analyze(conjecture: str, ctx: AppContext):
    """Analyze a mathematical conjecture."""
    t = ctx.i18n.t
    console.print(f"\n[bold blue]🔬 {t('conjecture_analysis')}: {conjecture}[/bold blue]\n")
    
    with console.status("[bold green]正在分析猜想...", spinner="dots"):
        result = ctx.math_reasoning.analyze_conjecture(conjecture, language=ctx.config.language)
    
    if result.success:
        console.print(Markdown(result.response))
        console.print(f"\n[green]分析质量: {result.confidence:.2f}[/green]")
        
        if result.steps:
            console.print(f"\n[bold]分析步骤/Analysis Steps:[/bold]")
            for i, step in enumerate(result.steps, 1):
                console.print(f"  {i}. {step}")
    else:
        console.print(f"[red]❌ 分析失败: {result.error}[/red]")


def cmd_math_compute(expression: str, ctx: AppContext):
    """Perform symbolic computation."""
    t = ctx.i18n.t
    console.print(f"\n[bold blue]🔢 {t('symbolic_computation')}: {expression}[/bold blue]\n")
    
    with console.status("[bold green]正在计算...", spinner="dots"):
        result = ctx.math_reasoning.symbolic_computation(expression, language=ctx.config.language)
    
    if result.success:
        console.print(Markdown(result.response))
        console.print(f"\n[green]计算置信度: {result.confidence:.2f}[/green]")
        
        if result.steps:
            console.print(f"\n[bold]计算步骤/Computation Steps:[/bold]")
            for i, step in enumerate(result.steps, 1):
                console.print(f"  {i}. {step}")
    else:
        console.print(f"[red]❌ 计算失败: {result.error}[/red]")


def cmd_benchmark(ctx: AppContext):
    """Run math evaluation benchmark."""
    from jiuzhang.math_benchmark import MathBenchmark
    bench = MathBenchmark()
    console.print("\n[bold blue]📊 JiuZhang Math Benchmark[/bold blue]")
    
    problems = bench.get_problems()
    table = Table(title="Benchmark Problems")
    table.add_column("ID", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Difficulty", style="yellow")
    table.add_column("Problem (EN)", style="white", max_width=50)
    
    for p in problems:
        table.add_row(p.id, p.category, p.difficulty, p.problem_en[:50])
    
    console.print(table)
    console.print(f"\nTotal: {len(problems)} problems across {len(set(p.category for p in problems))} categories")
    
    choice = Prompt.ask("Run benchmark against a model?", choices=["y", "n"], default="n")
    if choice == "y":
        model = Prompt.ask("Model name", default=ctx.config.active_model)
        result = bench.evaluate_local(model)
        bench.print_report(result)


def cmd_discover(ctx: AppContext, max_n: int = 500):
    """Run automated conjecture discovery engine."""
    from jiuzhang.conjecture_engine import ConjectureEngine
    engine = ConjectureEngine(seed=42)
    
    console.print("\n[bold blue]🔍 JiuZhang Conjecture Discovery Engine[/bold blue]")
    with console.status("[bold green]Discovering conjectures...", spinner="dots"):
        result = engine.run_discovery(max_n=max_n)
    
    console.print(engine.format_report(result))
    
    choice = Prompt.ask("Export results?", choices=["y", "n"], default="n")
    if choice == "y":
        path = Prompt.ask("Output path", default="jiuzhang_conjectures.json")
        engine.export_conjectures(path, result)


def cmd_train_model(ctx: AppContext):
    """Setup small math model training."""
    from jiuzhang.small_math_model import SmallMathModelTrainer, SmallMathModelConfig
    
    console.print("\n[bold blue]🧠 JiuZhang SmallMathModel Trainer[/bold blue]")
    
    size = Prompt.ask("Model size", choices=["0.8B", "1.5B", "3B", "7B"], default="0.8B")
    method = Prompt.ask("Training method", choices=["qlora", "full", "ollama"], default="qlora")
    
    model_map = {
        "0.8B": "Qwen/Qwen3.5-0.8B",
        "1.5B": "Qwen/Qwen2.5-1.5B-Instruct",
        "3B": "Qwen/Qwen2.5-3B-Instruct",
        "7B": "Qwen/Qwen2.5-7B-Instruct",
    }
    
    cfg = SmallMathModelConfig(
        base_model=model_map.get(size, model_map["1.5B"]),
        model_size=size,
        training_method=method,
        output_dir=f"jiuzhang-math-{size.lower()}",
    )
    trainer = SmallMathModelTrainer(cfg)
    trainer.generate_training_data()
    
    if method == "qlora":
        trainer.build_unsloth_script(cfg.data_path)
    elif method == "full":
        trainer.build_hf_script(cfg.data_path)
    elif method == "ollama":
        trainer.build_ollama_modelfile()
    
    trainer.print_full_report()


def cmd_distill(ctx: AppContext):
    """Run distillation pipeline with online teacher model."""
    from jiuzhang.distillation_pipeline import DistillationPipeline
    
    console.print("\n[bold blue]🔄 JiuZhang Distillation Pipeline[/bold blue]")
    console.print("Combine online teacher models with SymPy verification to train a local math model")
    
    teacher = Prompt.ask("Teacher model (online)", default=ctx.config.active_model)
    problems = Prompt.ask("Number of problems", default="50")
    categories = Prompt.ask("Categories (comma-separated, or empty for all)", default="")
    difficulties = Prompt.ask("Difficulties (comma-separated, or empty for all)", default="")
    method = Prompt.ask("Training method", choices=["qlora", "full"], default="qlora")
    base_model = Prompt.ask("Base model for training", default="Qwen/Qwen3.5-0.8B")
    
    pipeline = DistillationPipeline(config=ctx.config, seed=42)
    
    cats = [c.strip() for c in categories.split(",")] if categories else None
    diffs = [d.strip() for d in difficulties.split(",")] if difficulties else None
    
    console.print(f"\n[bold]Starting distillation with {teacher}...[/bold]")
    result = pipeline.run_distillation(
        teacher_model=teacher,
        categories=cats,
        difficulties=diffs,
        problem_count=int(problems),
        output_path="jiuzhang_distilled.jsonl",
    )
    
    pipeline.generate_training_script(
        base_model=base_model,
        method=method,
    )
    
    pipeline.generate_ollama_modelfile("jiuzhang-math")
    
    pipeline.print_full_report(result)


def cmd_low_vram_train(ctx: AppContext):
    """Setup low-VRAM math model training."""
    from jiuzhang.low_vram_training import LowVRAMConfig, LowVRAMTrainer
    
    console.print("\n[bold blue]🐢 JiuZhang Low-VRAM Math Trainer[/bold blue]")
    console.print("Slow and steady training - minimal VRAM, extended time")
    
    size = Prompt.ask("Model size", choices=["0.8B", "1.5B"], default="0.8B")
    lora_r = Prompt.ask("LoRA rank (lower = less memory)", choices=["8", "16", "32"], default="16")
    grad_accum = Prompt.ask("Gradient accumulation (higher = less memory, slower)", choices=["16", "32", "64", "128"], default="32")
    epochs = Prompt.ask("Number of epochs", default="5")
    staged = Confirm.ask("Use staged training (better quality, more steps)?", default=True)
    
    model_map = {
        "0.8B": "Qwen/Qwen3.5-0.8B",
        "1.5B": "Qwen/Qwen2.5-1.5B-Instruct",
    }
    
    cfg = LowVRAMConfig(
        base_model=model_map.get(size, model_map["0.8B"]),
        model_size=size,
        output_dir=f"jiuzhang-math-low-vram-{size.lower()}",
        lora_r=int(lora_r),
        gradient_accumulation=int(grad_accum),
        num_epochs=int(epochs),
    )
    trainer = LowVRAMTrainer(cfg)
    
    if staged:
        scripts = trainer.generate_all_scripts()
    else:
        trainer.generate_training_script()
        trainer.generate_ollama_import_script()
    
    trainer.print_training_guide()
