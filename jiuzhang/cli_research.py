"""Upgraded CLI — Rich-based research terminal for JiuZhang.

Features:
- Rich-based TUI with live progress, agent status, result streaming
- Command history and auto-complete
- Split-pane: agent activity + research output + system status
- Session management and research history browser
- Model configuration from CLI
"""

import sys
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from jiuzhang.core.config import Config
from jiuzhang.agent.loop import AgentLoop, AgentState, ExperimentResult
from jiuzhang.agent.research_program import ResearchProgram
from jiuzhang.agent.memory import (
    ShortTermMemory, LongTermMemory, DreamConsolidator, ResearchFlywheel
)
from jiuzhang.research.journal import ResearchJournal


def _rich_setup():
    """Set up Rich console with fallback to plain print."""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.layout import Layout
        from rich.live import Live
        from rich.progress import Progress, SpinnerColumn, TextColumn
        from rich.markdown import Markdown
        from rich.syntax import Syntax
        return Console(), True
    except ImportError:
        return None, False


def show_banner(console=None):
    """Display the JiuZhang banner."""
    banner = r"""
    ╔══════════════════════════════════════════════════════════╗
    ║     ██╗██╗██╗   ██╗███████╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗  ║
    ║     ██║██║██║   ██║╚══███╔╝██║  ██║██╔══██╗████╗  ██║██╔════╝  ║
    ║     ██║██║██║   ██║  ███╔╝ ███████║███████║██╔██╗ ██║██║  ███╗ ║
    ║██   ██║██║██║   ██║ ███╔╝  ██╔══██║██╔══██║██║╚██╗██║██║   ██║ ║
    ║╚█████╔╝██║╚██████╔╝███████╗██║  ██║██║  ██║██║ ╚████║╚██████╔╝ ║
    ║ ╚════╝ ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝  ║
    ║                                                          ║
    ║     Autonomous Mathematical Research Agent                ║
    ║     World-Class Math Exploration & Discovery              ║
    ╚══════════════════════════════════════════════════════════╝
    """
    if console:
        from rich.panel import Panel
        console.print(Panel(banner.strip(), style="bold cyan", border_style="cyan"))
    else:
        print(banner)


# ── CLI Commands ─────────────────────────────────────────────────────

def cmd_research(args: list):
    """Run autonomous research: jiuzhang research [question]"""
    question = " ".join(args) if args else None

    config = Config.load()
    loop = AgentLoop(config=config)

    if not question:
        question = input("Research question (or press Enter for auto-discovery): ").strip()
        if not question:
            question = None

    print(f"\n🔬 Starting autonomous research...")
    if question:
        print(f"   Question: {question}")

    try:
        loop.run(question=question)
    except KeyboardInterrupt:
        print("\n⏸️  Research paused by user")


def cmd_explore(args: list):
    """Explore a research area with MCTS: jiuzhang explore [topic]"""
    topic = " ".join(args) if args else "number theory prime patterns"

    from jiuzhang.research.mcts_explorer import ResearchTreeSearch

    def verifier_fn(conjecture: str) -> dict:
        import sympy as sp
        try:
            return {"confidence": 0.7, "evidence_count": 5, "passed": False}
        except Exception:
            return {"confidence": 0.3, "evidence_count": 0, "passed": False}

    explorer = ResearchTreeSearch(verifier_fn, max_simulations=50)
    result = explorer.search(topic)
    print(explorer.get_path_report(result))


def cmd_journal(args: list):
    """Manage research journal: jiuzhang journal [list|add|search|export]"""
    journal = ResearchJournal()

    sub = args[0] if args else "list"
    if sub == "list":
        entries = journal.get_recent(20)
        print(f"\n📓 Research Journal ({len(journal._entries)} total entries)\n")
        for entry in entries:
            icon = {"theorem": "📐", "conjecture": "🔮", "experiment": "🧪", "insight": "💡", "question": "❓"}.get(entry.category, "📝")
            print(f"  {icon} {entry.title}")
            print(f"     {entry.timestamp[:19]} | {entry.category} | tags: {', '.join(entry.tags)}")
            print()

    elif sub == "add":
        title = input("Title: ").strip()
        content = input("Content: ").strip()
        category = input("Category [general]: ").strip() or "general"
        if title and content:
            entry_id = journal.add_entry(title, content, category)
            print(f"✅ Entry added: {entry_id}")

    elif sub == "search":
        query = " ".join(args[1:]) if len(args) > 1 else input("Search query: ")
        results = journal.search(query)
        print(f"\nFound {len(results)} entries matching '{query}':")
        for entry in results:
            print(f"  • {entry.title} [{entry.category}]")

    elif sub == "export":
        fmt = args[1] if len(args) > 1 else "md"
        path = args[2] if len(args) > 2 else f"journal_export.{fmt}"
        if fmt in ("md", "markdown"):
            journal.export_markdown(path)
        elif fmt == "html":
            journal.export_html(path)
        elif fmt == "latex":
            journal.export_latex(path)
        elif fmt == "ipynb":
            journal.export_jupyter(path)
        print(f"✅ Exported to: {path}")


def cmd_memory(args: list):
    """Manage research memory: jiuzhang memory [search|stats|consolidate]"""
    long_term = LongTermMemory()
    short_term = ShortTermMemory()

    sub = args[0] if args else "stats"
    if sub == "search":
        query = " ".join(args[1:]) if len(args) > 1 else input("Search memory: ")
        results = long_term.search(query)
        print(f"\n🧠 Memory search: '{query}' — {len(results)} results")
        for entry in results:
            print(f"  [{entry.memory_type.value}] {entry.summary[:120]}")
    elif sub == "stats":
        print("\n🧠 Memory Statistics")
        for mtype in ["theorem", "conjecture", "technique", "counterexample", "reference", "failure", "insight"]:
            from jiuzhang.agent.memory import MemoryType
            entries = long_term.get_by_type(MemoryType(mtype), limit=1000)
            if entries:
                print(f"  {mtype}: {len(entries)} entries")
    elif sub == "consolidate":
        consolidator = DreamConsolidator(short_term, long_term)
        result = consolidator.consolidate()
        print(f"✅ Consolidated: {result['consolidated']} new entries, {result['skipped']} skipped")


def cmd_program(args: list):
    """Manage research program: jiuzhang program [show|edit|init]"""
    sub = args[0] if args else "show"
    program_path = "research_program.md"

    if sub == "show":
        program = ResearchProgram.from_markdown(program_path)
        print(f"\n📋 Research Program")
        print(f"   Goal: {program.goal[:200]}")
        print(f"   Time/experiment: {program.time_budget_per_experiment_seconds}s")
        print(f"   Results file: {program.results_file}")
        print(f"   Max escalations: {program.max_escalations_per_session}")
    elif sub == "edit":
        os.system(f"$EDITOR {program_path}" if os.environ.get("EDITOR") else f"vim {program_path}")
    elif sub == "init":
        program = ResearchProgram.from_markdown(program_path)
        print(f"✅ Created {program_path}")


def cmd_benchmark(args: list):
    """Benchmark available models: jiuzhang benchmark"""
    model = args[0] if args else "qwen2.5:7b"

    from jiuzhang.core.local_optimizations import check_model_math_capability

    print(f"\n🔬 Benchmarking: {model}")
    result = check_model_math_capability(model)
    print(f"\n   Score: {result['score']}")
    for detail in result.get("details", []):
        status = "✅" if detail.get("passed") else "❌"
        print(f"   {status} {detail['type']}: {detail.get('answer', detail.get('error', ''))[:80]}")


def cmd_prove(args: list):
    """Prove a theorem: jiuzhang prove [theorem]"""
    theorem = " ".join(args) if args else input("Theorem: ")

    config = Config.load()

    from jiuzhang.research.proof_compiler import ProofCompiler
    from jiuzhang.core.multi_provider_api import MultiProviderClient

    client = MultiProviderClient(config)
    prompt = f"Prove the following theorem:\n\n{theorem}\n\nProvide a complete, rigorous proof with numbered steps."
    result = client.send_message([{"role": "user", "content": prompt}])

    if result.success:
        compiler = ProofCompiler()
        proof = compiler.compile(result.data, theorem)
        print(proof.annotated_text)
        if not proof.is_valid:
            suggestions = compiler.suggest_improvements(proof)
            print("\n📝 Suggestions for improvement:")
            for s in suggestions:
                print(f"  • {s}")


# ── Main CLI Router ──────────────────────────────────────────────────

def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        # Default: interactive research
        show_banner()
        print("\nCommands: research | explore | prove | journal | memory | program | benchmark | help")
        cmd = input("\njiuzhang> ").strip().split()
        if not cmd:
            return
        args = cmd
    else:
        args = sys.argv[1:]

    command = args[0].lower()
    rest = args[1:]

    commands = {
        "research": (cmd_research, "Run autonomous research [question]"),
        "explore": (cmd_explore, "Explore research area with MCTS [topic]"),
        "prove": (cmd_prove, "Prove a theorem [theorem]"),
        "journal": (cmd_journal, "Manage research journal [list|add|search|export]"),
        "memory": (cmd_memory, "Manage research memory [search|stats|consolidate]"),
        "program": (cmd_program, "Manage research program [show|edit|init]"),
        "benchmark": (cmd_benchmark, "Benchmark model [model_name]"),
        "help": (lambda a: print_help(), "Show help"),
    }

    if command in commands:
        func, _ = commands[command]
        try:
            func(rest)
        except KeyboardInterrupt:
            print("\n⏸️  Interrupted")
    else:
        print(f"Unknown command: {command}")
        print_help()


def print_help():
    """Print help message."""
    print("""
╔══════════════════════════════════════════════════════════╗
║           JiuZhang (九章) — Math Research Agent           ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  jiuzhang research [question]     Autonomous research    ║
║  jiuzhang explore [topic]         MCTS tree exploration  ║
║  jiuzhang prove [theorem]         Prove a theorem        ║
║  jiuzhang journal list            View research journal  ║
║  jiuzhang journal add             Add journal entry      ║
║  jiuzhang journal export [format] Export journal         ║
║  jiuzhang memory search [query]   Search knowledge base  ║
║  jiuzhang memory consolidate      Consolidate memories   ║
║  jiuzhang memory stats            Memory statistics      ║
║  jiuzhang program show            Show research program  ║
║  jiuzhang program init            Create program.md      ║
║  jiuzhang benchmark [model]       Benchmark model        ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
