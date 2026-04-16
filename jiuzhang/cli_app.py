"""CLI application for JiuZhang with full i18n support."""

import sys
from typing import Optional

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

console = Console()


def main(args: Optional[list] = None):
    """Main CLI entry point."""
    config = Config.load()
    i18n = I18n(default_language=config.language)
    client = MultiProviderClient(config)
    registry = CourseRegistry()
    curriculum = registry.build_curriculum()
    lesson_gen = LessonGenerator(config)
    research_engine = ResearchEngine(config)
    frontier = FrontierResearchAssistant(config)
    open_problems = OpenProblemsDB()
    counterexample_finder = CounterexampleFinder()
    latex_generator = LaTeXPaperGenerator()
    proof_assistant = ProofAssistant()

    if not args:
        repl_loop(
            config,
            client,
            curriculum,
            lesson_gen,
            registry,
            i18n,
            research_engine,
            frontier,
            open_problems,
            counterexample_finder,
            latex_generator,
            proof_assistant,
        )
        return

    command = args[0]
    if command == "learn":
        topic = " ".join(args[1:]) if len(args) > 1 else i18n.t("natural_numbers")
        cmd_learn(topic, config, lesson_gen, i18n)
    elif command == "exercise":
        topic = " ".join(args[1:]) if len(args) > 1 else i18n.t("natural_numbers")
        cmd_exercise(topic, config, lesson_gen, i18n)
    elif command == "research":
        query = " ".join(args[1:]) if len(args) > 1 else "傅里叶变换"
        cmd_research(query, config, research_engine, i18n)
    elif command == "frontier":
        query = " ".join(args[1:]) if len(args) > 1 else "朗兰兹纲领"
        cmd_frontier(query, config, frontier, i18n)
    elif command == "problems":
        query = " ".join(args[1:]) if len(args) > 1 else ""
        cmd_open_problems(query, open_problems, i18n)
    elif command == "test":
        conjecture = " ".join(args[1:]) if len(args) > 1 else "goldbach"
        cmd_test_conjecture(conjecture, counterexample_finder, i18n)
    elif command == "visualize":
        viz_type = args[1] if len(args) > 1 else "number_line"
        cmd_visualize(viz_type, i18n)
    elif command == "config":
        cmd_config(config, i18n)
    elif command == "courses":
        cmd_courses(registry, i18n)
    elif command == "stats":
        cmd_stats(registry, i18n)
    elif command == "lang":
        lang = args[1] if len(args) > 1 else config.language
        cmd_language(lang, config, i18n)
    elif command == "history":
        cmd_history(research_engine, i18n)
    elif command == "paper":
        arxiv_id = args[1] if len(args) > 1 else ""
        cmd_read_paper(arxiv_id, frontier, i18n)
    elif command == "latex":
        title = " ".join(args[1:]) if len(args) > 1 else "My Research Paper"
        cmd_generate_latex(title, latex_generator, i18n)
    else:
        console.print(f"[red]{i18n.t('unknown_command')}: {command}[/red]")
        console.print(
            f"{i18n.t('available_commands')}: learn, exercise, research, frontier, problems, test, paper, latex, visualize, config, courses, stats, lang, history"
        )


def repl_loop(
    config,
    client,
    curriculum,
    lesson_gen,
    registry,
    i18n,
    research_engine,
    frontier,
    open_problems,
    counterexample_finder,
    latex_generator,
    proof_assistant,
):
    """Interactive REPL loop."""
    console.print(
        Panel.fit(
            f"[bold blue]{i18n.t('app_name')}[/bold blue] - {i18n.t('app_subtitle')}\n"
            f"{i18n.t('welcome_desc')}",
            title=i18n.t("welcome"),
        )
    )

    while True:
        try:
            user_input = Prompt.ask(
                f"\n[bold green]{i18n.t('app_name')}[/bold green]"
            ).strip()
        except (KeyboardInterrupt, EOFError):
            console.print(f"\n[yellow]{i18n.t('goodbye')}[/yellow]")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            console.print(f"[yellow]{i18n.t('goodbye')}[/yellow]")
            break

        if user_input.lower() == "help":
            show_help(i18n)
            continue

        if user_input.lower().startswith("learn "):
            topic = user_input[6:].strip()
            cmd_learn(topic, config, lesson_gen, i18n)
        elif user_input.lower().startswith("exercise "):
            topic = user_input[9:].strip()
            cmd_exercise(topic, config, lesson_gen, i18n)
        elif user_input.lower().startswith("research "):
            query = user_input[9:].strip()
            cmd_research(query, config, research_engine, i18n)
        elif user_input.lower().startswith("frontier "):
            query = user_input[9:].strip()
            cmd_frontier(query, config, frontier, i18n)
        elif user_input.lower().startswith("problems "):
            query = user_input[9:].strip()
            cmd_open_problems(query, open_problems, i18n)
        elif user_input.lower().startswith("test "):
            conjecture = user_input[5:].strip()
            cmd_test_conjecture(conjecture, counterexample_finder, i18n)
        elif user_input.lower().startswith("paper "):
            arxiv_id = user_input[6:].strip()
            cmd_read_paper(arxiv_id, frontier, i18n)
        elif user_input.lower().startswith("latex "):
            title = user_input[6:].strip()
            cmd_generate_latex(title, latex_generator, i18n)
        elif user_input.lower().startswith("visualize "):
            viz_type = user_input[10:].strip()
            cmd_visualize(viz_type, i18n)
        elif user_input.lower() == "config":
            cmd_config(config, i18n)
        elif user_input.lower() == "courses":
            cmd_courses(registry, i18n)
        elif user_input.lower() == "stats":
            cmd_stats(registry, i18n)
        elif user_input.lower() == "history":
            cmd_history(research_engine, i18n)
        elif user_input.lower() == "multiplication":
            show_multiplication_table_tui()
        elif user_input.lower().startswith("fraction "):
            parts = user_input[9:].strip().split("/")
            if len(parts) == 2:
                try:
                    show_fraction_visualizer_tui(int(parts[0]), int(parts[1]))
                except ValueError:
                    console.print(f"[red]{i18n.t('fraction')}: 3/4[/red]")
            else:
                console.print(f"[red]{i18n.t('fraction')} <n/d>[/red]")
        elif user_input.lower().startswith("lang "):
            lang = user_input[5:].strip()
            cmd_language(lang, config, i18n)
        else:
            cmd_learn(user_input, config, lesson_gen, i18n)


def show_help(i18n):
    """Show available commands."""
    table = Table(title=i18n.t("available_commands"))
    table.add_column(i18n.t("command"), style="cyan")
    table.add_column(i18n.t("description"), style="green")

    table.add_row("learn <topic>", i18n.t("learn"))
    table.add_row("exercise <topic>", i18n.t("exercise"))
    table.add_row("research <query>", "数学研究（文献搜索、推导、实验）")
    table.add_row("frontier <query>", "前沿数学研究（知识库、符号计算、论文）")
    table.add_row("problems [query]", "开放问题数据库（千禧年大奖问题等）")
    table.add_row("test <conjecture>", "猜想验证（goldbach, collatz, fermat）")
    table.add_row("paper <arxiv_id>", "阅读 arXiv 论文")
    table.add_row("latex <title>", "生成 LaTeX 论文")
    table.add_row("history", "查看研究历史")
    table.add_row("visualize <type>", i18n.t("visualize"))
    table.add_row("courses", i18n.t("courses"))
    table.add_row("stats", i18n.t("stats"))
    table.add_row("multiplication", i18n.t("multiplication_table"))
    table.add_row("fraction <n/d>", i18n.t("fraction"))
    table.add_row("lang <code>", i18n.t("language"))
    table.add_row("config", i18n.t("config"))
    table.add_row("help", i18n.t("help"))
    table.add_row("quit", i18n.t("quit"))

    console.print(table)


def cmd_learn(topic: str, config: Config, lesson_gen: LessonGenerator, i18n: I18n):
    """Learn a topic."""
    console.print(f"\n[bold blue]{i18n.t('learning')}: {topic}[/bold blue]\n")

    with console.status(
        f"[bold green]{i18n.t('generating_lesson')}[/bold green]", spinner="dots"
    ):
        result = lesson_gen.generate_lesson(
            topic, level="elementary", language=config.language
        )

    if result.success:
        console.print(Markdown(result.data))
    else:
        console.print(f"[red]{i18n.t('lesson_failed')}: {result.error}[/red]")


def cmd_exercise(topic: str, config: Config, lesson_gen: LessonGenerator, i18n: I18n):
    """Generate exercises."""
    console.print(f"\n[bold blue]{i18n.t('exercise')}: {topic}[/bold blue]\n")

    with console.status(
        f"[bold green]{i18n.t('generating_exercise')}[/bold green]", spinner="dots"
    ):
        result = lesson_gen.generate_exercise(
            topic, difficulty="easy", count=3, language=config.language
        )

    if result.success:
        console.print(Markdown(result.data))
    else:
        console.print(f"[red]{i18n.t('exercise_failed')}: {result.error}[/red]")


def cmd_visualize(viz_type: str, i18n: I18n):
    """Create a visualization."""
    console.print(f"\n[bold blue]{i18n.t('visualize')}: {viz_type}[/bold blue]\n")

    if viz_type == "number_line":
        plot_number_line_tui(
            -5, 10, highlight=[0, 1, 2, 3], title=i18n.t("natural_numbers")
        )
    elif viz_type == "integers":
        plot_number_line_tui(-10, 10, highlight=[-5, 0, 5], title=i18n.t("integers"))
    elif viz_type == "bar":
        plot_bar_chart_tui(
            ["A", "B", "C", "D", "E"], [23, 45, 56, 78, 32], title=i18n.t("bar_chart")
        )
    elif viz_type == "function":
        import numpy as np

        plot_function_tui(lambda x: np.sin(x), (-10, 10), title="y = sin(x)")
    elif viz_type == "quadratic":
        import numpy as np

        plot_function_tui(lambda x: x**2 - 4, (-5, 5), title="y = x² - 4")
    else:
        console.print(f"[red]{i18n.t('unknown_command')}: {viz_type}[/red]")
        console.print("number_line, integers, bar, function, quadratic")


def cmd_config(config: Config, i18n: I18n):
    """Show and edit configuration."""
    table = Table(title=i18n.t("current_config"))
    table.add_column(i18n.t("setting"), style="cyan")
    table.add_column(i18n.t("value"), style="green")

    table.add_row(i18n.t("ai_provider"), config.active_provider)
    table.add_row(i18n.t("model"), config.active_model)
    table.add_row(i18n.t("language"), i18n.get_language_name(config.language))
    table.add_row(i18n.t("max_tokens"), str(config.max_tokens))
    table.add_row(i18n.t("temperature"), str(config.temperature))

    console.print(table)

    if Confirm.ask(f"\n{i18n.t('edit_config')}"):
        provider = Prompt.ask(i18n.t("ai_provider"), default=config.active_provider)
        model = Prompt.ask(i18n.t("model"), default=config.active_model)
        config.active_provider = provider
        config.active_model = model
        config.save()
        console.print(f"[green]{i18n.t('config_saved')}[/green]")


def cmd_courses(registry: CourseRegistry, i18n: I18n):
    """Show all available courses."""
    tree = Tree(f"[bold blue]{i18n.t('course_system')}[/bold blue]")

    categories = registry.get_categories()
    for category in sorted(categories):
        branch = tree.add(f"[bold cyan]{category}[/bold cyan]")
        kps = registry.get_knowledge_points_by_category(category)
        for kp in kps:
            branch.add(f"{kp.name_cn} ({kp.name})")

    console.print(tree)


def cmd_stats(registry: CourseRegistry, i18n: I18n):
    """Show course statistics."""
    stats = registry.get_stats()

    table = Table(title=i18n.t("course_stats"))
    table.add_column(i18n.t("category"), style="cyan")
    table.add_column(i18n.t("knowledge_points"), style="green", justify="right")

    for category, count in sorted(stats["by_category"].items()):
        table.add_row(category, str(count))

    table.add_row(
        f"[bold]{i18n.t('total')}[/bold]",
        f"[bold]{stats['total_knowledge_points']}[/bold]",
    )

    console.print(table)

    level_table = Table(title=i18n.t("level_distribution"))
    level_table.add_column(i18n.t("level"), style="cyan")
    level_table.add_column(i18n.t("knowledge_points"), style="green", justify="right")

    level_names = {
        "elementary": i18n.t("elementary"),
        "middle_school": i18n.t("middle_school"),
        "high_school": i18n.t("high_school"),
        "undergraduate": i18n.t("undergraduate"),
        "graduate": i18n.t("graduate"),
        "frontier": i18n.t("frontier"),
    }

    for level, count in sorted(stats["by_level"].items()):
        name = level_names.get(level, level)
        level_table.add_row(name, str(count))

    console.print(level_table)


def cmd_language(lang: str, config: Config, i18n: I18n):
    """Change language."""
    if lang in SUPPORTED_LANGUAGES:
        i18n.set_language(lang)
        config.language = lang
        config.save()
        console.print(
            f"[green]{i18n.t('config_saved')}: {i18n.get_language_name(lang)}[/green]"
        )
    else:
        console.print(f"[red]Unsupported: {lang}[/red]")
        console.print(f"Supported: {', '.join(SUPPORTED_LANGUAGES.keys())}")


def cmd_research(
    query: str, config: Config, research_engine: ResearchEngine, i18n: I18n
):
    """Conduct mathematical research."""
    console.print(f"\n[bold blue]🔬 {i18n.t('research')}: {query}[/bold blue]\n")

    with console.status("[bold green]正在进行数学研究...", spinner="dots") as status:
        status.update("[bold green]步骤 1/5: 分析主题...[/bold green]")
        result = research_engine.research(
            query=query,
            language=config.language,
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


def cmd_history(research_engine: ResearchEngine, i18n: I18n):
    """Show research history."""
    history = research_engine.get_research_history()

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


def cmd_frontier(
    query: str, config: Config, frontier: FrontierResearchAssistant, i18n: I18n
):
    """Conduct frontier mathematics research."""
    console.print(f"\n[bold blue]🔬 前沿数学研究: {query}[/bold blue]\n")

    with console.status("[bold green]正在进行前沿数学研究...", spinner="dots"):
        result = frontier.research(
            query=query,
            language=config.language,
            include_papers=True,
            include_visualization=True,
            depth="deep",
        )

    console.print(Markdown(result))


def cmd_read_paper(arxiv_id: str, frontier: FrontierResearchAssistant, i18n: I18n):
    """Read and summarize an arXiv paper."""
    if not arxiv_id:
        console.print("[red]请提供 arXiv ID，例如：paper 2401.12345[/red]")
        return

    console.print(f"\n[bold blue]📄 阅读论文: {arxiv_id}[/bold blue]\n")

    with console.status("[bold green]正在获取论文...", spinner="dots"):
        summary = frontier.read_paper(arxiv_id, i18n.get_language())

    console.print(Markdown(summary))


def cmd_open_problems(query: str, open_problems: OpenProblemsDB, i18n: I18n):
    """Show open problems in mathematics."""
    if not query:
        # Show all open problems
        console.print("\n[bold blue]数学开放问题[/bold blue]\n")
        report = open_problems.generate_report(i18n.get_language())
        console.print(Markdown(report))
    else:
        # Search for specific problems
        console.print(f"\n[bold blue]搜索开放问题：{query}[/bold blue]\n")
        problems = open_problems.search(query, i18n.get_language())
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


def cmd_test_conjecture(conjecture: str, finder: CounterexampleFinder, i18n: I18n):
    """Test a mathematical conjecture."""
    console.print(f"\n[bold blue]猜想验证：{conjecture}[/bold blue]\n")

    if conjecture.lower() == "goldbach" or "哥德巴赫" in conjecture:
        result = finder.goldbach_test(1000)
    elif conjecture.lower() == "collatz" or "考拉兹" in conjecture:
        result = finder.collatz_test(10000)
    elif conjecture.lower() == "fermat" or "费马" in conjecture:
        result = finder.fermat_last_theorem_check(3, 50)
    elif conjecture.lower() == "euler" or "欧拉" in conjecture:
        result = finder.euler_sum_of_powers_test()
    else:
        console.print(f"[red]未知猜想：{conjecture}[/red]")
        console.print("可用：goldbach, collatz, fermat, euler")
        return

    console.print(f"{result.get('conjecture', '')}")
    console.print(f"状态：{result.get('status', '')}")
    if result.get("counterexamples"):
        console.print(f"反例：{result['counterexamples'][:5]}")
    console.print(f"验证数量：{result.get('verified_count', 0)}")


def cmd_generate_latex(title: str, generator: LaTeXPaperGenerator, i18n: I18n):
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
    latex = generator.generate_paper(
        title=title,
        author="JiuZhang Research Assistant",
        abstract=f"This paper studies {title}.",
        sections=sections,
        output_path=output_path,
    )

    console.print(f"[green]✅ LaTeX 论文已生成: {output_path}[/green]")
    console.print(f"字数: {len(latex)}")
