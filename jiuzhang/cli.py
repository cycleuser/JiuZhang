"""CLI entry point for JiuZhang — V3 unified command router."""

import sys


def _print_help():
    print("""JiuZhang (九章) — World-Class Autonomous Mathematical Research Platform

Commands:
  jiuzhang                  Launch classic web GUI
  jiuzhang research [Q]      Run autonomous research agent (CLI)
  jiuzhang web               Launch V3 research web dashboard
  jiuzhang explore [topic]   MCTS research space exploration
  jiuzhang benchmark         Run math evaluation benchmark
  jiuzhang flywheel          Show research flywheel progress
  jiuzhang skills            List available research skills
  jiuzhang journal [cmd]     Manage research journal
  jiuzhang learn <topic>     Learn a math topic (classic)
  jiuzhang exercise <topic>  Generate exercises (classic)
  jiuzhang help              Show this help

Examples:
  jiuzhang research "Prove Fermat's Last Theorem for n=3"
  jiuzhang explore "prime number distribution"
  jiuzhang skills
  jiuzhang learn "calculus"
""")


def main():
    """Main entry point for the jiuzhang command.

    Routes:
        jiuzhang                → Classic web GUI (backward-compat)
        jiuzhang research [...] → Autonomous research agent (CLI)
        jiuzhang web            → V3 research web dashboard
        jiuzhang explore [...]  → MCTS research exploration
        jiuzhang benchmark      → Run math benchmark
        jiuzhang flywheel       → Flywheel progress report
        jiuzhang skills         → List available research skills
        jiuzhang learn/...      → Classic math learning CLI
    """
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    if not args:
        # Default: classic web GUI
        try:
            from jiuzhang.app import run_web
            run_web()
        except ImportError:
            from jiuzhang.cli_app import main as cli_main
            cli_main(["learn", "数的概念"])
        return

    cmd = args[0].lower()

    # Help
    if cmd in ("--help", "-h", "help"):
        _print_help()
        return

    # ── V3 Commands ────────────────────────────────────────────────
    if cmd == "research":
        from jiuzhang.research_terminal import research_cli
        research_cli(
            question=" ".join(args[1:]) if len(args) > 1 else None,
        )
        return

    if cmd == "web":
        from jiuzhang.web_dashboard import start_web_server
        start_web_server()
        return

    if cmd == "benchmark":
        from jiuzhang.math_benchmark import main as bench_main
        bench_main()
        return

    if cmd == "explore":
        from jiuzhang.cli_research import cmd_explore
        cmd_explore(args[1:])
        return

    if cmd == "flywheel":
        from jiuzhang.flywheel_bridge import ResearchFlywheelBridge
        bridge = ResearchFlywheelBridge()
        bridge.load_state()
        print(bridge.get_progress_report())
        return

    if cmd == "skills":
        from jiuzhang.skills_system import SkillManager
        sm = SkillManager()
        for s in sm.list_available():
            status = "🟢" if s["active"] else "⚪"
            print(f"  {status} {s['name']:30s} [{s['category']}] {s['description']}")
        return

    if cmd == "journal":
        from jiuzhang.cli_research import cmd_journal
        cmd_journal(args[1:])
        return

    # ── Classic Commands ───────────────────────────────────────────
    if cmd in ("cli", "learn", "exercise", "visualize", "config"):
        from jiuzhang.cli_app import main as cli_main
        cli_main(args)
        return

    # Fallback
    try:
        from jiuzhang.app import run_web
        run_web()
    except ImportError:
        from jiuzhang.cli_app import main as cli_main
        cli_main(["learn", args[0]])


if __name__ == "__main__":
    main()
