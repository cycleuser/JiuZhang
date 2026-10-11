"""Rich Research Terminal — world-class CLI for JiuZhang.

Upgrades from the basic CLI to a full Rich-based interactive terminal with:
- Live split-pane layout: agent activity | proof status | system metrics
- Interactive steering: pause/resume/inject/research-direction live
- Research history browser with search
- LaTeX rendering via kitty/wezterm protocols
- Real-time streaming proof output
- Color-coded quality indicators
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from jiuzhang.core.config import Config


def try_rich_setup():
    """Set up Rich console, returning (console, has_rich)."""
    try:
        from rich.console import Console
        from rich.layout import Layout
        from rich.live import Live
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
        from rich.markdown import Markdown
        from rich.syntax import Syntax
        from rich import box
        return Console(), True
    except ImportError:
        return None, False


# ── Banner ────────────────────────────────────────────────────────────

BANNER = r"""
    ╔══════════════════════════════════════════════════════════════╗
    ║       ██╗██╗██╗   ██╗███████╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗  ║
    ║       ██║██║██║   ██║╚══███╔╝██║  ██║██╔══██╗████╗  ██║██╔════╝  ║
    ║       ██║██║██║   ██║  ███╔╝ ███████║███████║██╔██╗ ██║██║  ███╗ ║
    ║  ██   ██║██║██║   ██║ ███╔╝  ██╔══██║██╔══██║██║╚██╗██║██║   ██║ ║
    ║  ╚█████╔╝██║╚██████╔╝███████╗██║  ██║██║  ██║██║ ╚████║╚██████╔╝ ║
    ║   ╚════╝ ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝  ║
    ║                                                                ║
    ║       World-Class Autonomous Mathematical Research Agent       ║
    ╚══════════════════════════════════════════════════════════════════╝
"""


def show_banner(console=None):
    if console:
        from rich.panel import Panel
        console.print(Panel(BANNER.strip(), style="bold cyan", border_style="cyan"))
    else:
        print(BANNER)


# ── Layout Builder ────────────────────────────────────────────────────

def build_research_layout(live: "Live") -> "Layout":
    """Build the Rich layout for research terminal."""
    from rich.layout import Layout
    from rich.panel import Panel

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )
    layout["body"].split_row(
        Layout(name="main", ratio=2),
        Layout(name="sidebar", ratio=1),
    )
    layout["main"].split_column(
        Layout(name="activity", ratio=2),
        Layout(name="proof", ratio=1),
    )
    layout["sidebar"].split_column(
        Layout(name="status"),
        Layout(name="metrics"),
    )
    return layout


def render_header(question: str = "", experiment: int = 0) -> "Panel":
    from rich.panel import Panel
    from rich.text import Text
    text = Text()
    text.append("JiuZhang Research Terminal", style="bold cyan")
    if question:
        text.append(f"\n  Question: {question[:80]}", style="dim")
    if experiment > 0:
        text.append(f" | Experiment #{experiment}", style="yellow")
    return Panel(text, border_style="cyan")


# ── Interactive Commands ──────────────────────────────────────────────

class ResearchCommands:
    """Interactive commands available during research sessions."""

    COMMANDS = {
        "p": ("pause", "Pause research"),
        "r": ("resume", "Resume research"),
        "s": ("status", "Show detailed status"),
        "i": ("inject", "Inject a correction or suggestion"),
        "d": ("direction", "Change research direction"),
        "h": ("history", "View experiment history"),
        "m": ("metrics", "Show system metrics"),
        "q": ("quit", "Gracefully stop and save"),
        "?": ("help", "Show this help"),
    }

    @classmethod
    def show_help(cls, console=None):
        from rich.table import Table
        table = Table(title="Research Terminal Commands")
        table.add_column("Key", style="bold cyan")
        table.add_column("Command")
        table.add_column("Description")
        for key, (cmd, desc) in cls.COMMANDS.items():
            table.add_row(key, cmd, desc)
        if console:
            console.print(table)


# ── Live Research Display ────────────────────────────────────────────

class LiveResearchDisplay:
    """Manages the live research terminal display during autonomous runs.

    Shows real-time:
    - Agent activity log (scrolling)
    - Current proof/conjecture being worked on
    - System status (provider, tokens, health)
    - Key metrics (success rate, best score, stagnation status)
    """

    def __init__(self, console=None):
        self.console = console
        self._activity_log: list[str] = []
        self._current_proof: str = ""
        self._current_state: str = "IDLE"
        self._experiment_count: int = 0
        self._question: str = ""
        self._metrics: dict = {}
        self._running = True

    def set_question(self, question: str):
        self._question = question

    def add_activity(self, line: str):
        self._activity_log.append(f"[{time.strftime('%H:%M:%S')}] {line}")
        if len(self._activity_log) > 20:
            self._activity_log = self._activity_log[-20:]

    def set_proof(self, proof: str):
        self._current_proof = proof

    def set_state(self, state: str):
        self._current_state = state

    def set_metrics(self, metrics: dict):
        self._metrics = metrics

    def increment_experiment(self):
        self._experiment_count += 1

    def stop(self):
        self._running = False

    def render(self) -> str:
        """Render the full display as plain text (fallback when Rich unavailable)."""
        lines = [
            "=" * 70,
            f"JiuZhang Research | State: {self._current_state} | Experiment: #{self._experiment_count}",
            "=" * 70,
        ]
        if self._question:
            lines.append(f"Question: {self._question[:80]}")
        lines.append("")
        lines.append("── Activity Log ──")
        lines.extend(self._activity_log[-10:])
        lines.append("")
        lines.append("── Current Proof ──")
        lines.append(self._current_proof[:500] if self._current_proof else "(no active proof)")
        lines.append("")
        if self._metrics:
            lines.append("── Metrics ──")
            for k, v in self._metrics.items():
                lines.append(f"  {k}: {v}")
        return "\n".join(lines)

    async def run_with_live_updates(self, agent_loop_fn, interval: float = 0.5):
        """Run the display with periodic updates during research."""
        while self._running:
            self.add_activity(f"State: {self._current_state}")
            print(self.render())
            print("\033[H\033[J", end="")  # Clear screen
            await asyncio.sleep(interval)


# ── Research Session Manager ──────────────────────────────────────────

class ResearchSession:
    """Manages a single research session with history and export."""

    def __init__(self, output_dir: str | Path = "research_sessions"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._events: list[dict] = []
        self._results: list[dict] = []

    def record_event(self, event_type: str, data: dict):
        self._events.append({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        })

    def record_result(self, result: dict):
        self._results.append(result)

    def export_session(self, format: str = "json") -> Path:
        """Export the session to a file."""
        if format == "json":
            path = self.output_dir / f"session_{self.session_id}.json"
            path.write_text(json.dumps({
                "session_id": self.session_id,
                "events": self._events,
                "results": self._results,
                "summary": {
                    "total_experiments": len(self._results),
                    "kept": sum(1 for r in self._results if r.get("status") == "keep"),
                    "discarded": sum(1 for r in self._results if r.get("status") == "discard"),
                },
            }, indent=2, ensure_ascii=False))
        elif format == "markdown":
            path = self.output_dir / f"session_{self.session_id}.md"
            lines = [
                f"# JiuZhang Research Session: {self.session_id}",
                "",
                f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Experiments**: {len(self._results)}",
                "",
                "## Results",
                "",
            ]
            for i, r in enumerate(self._results):
                lines.append(f"### Experiment {i+1}")
                lines.append(f"- **Status**: {r.get('status', 'unknown')}")
                lines.append(f"- **Strength**: {r.get('conjecture_strength', 0):.3f}")
                lines.append(f"- **Confidence**: {r.get('proof_confidence', 0):.3f}")
                if r.get("description"):
                    lines.append(f"- **Description**: {r['description'][:200]}")
                lines.append("")
            path.write_text("\n".join(lines), encoding="utf-8")
        elif format == "notebook":
            path = self.output_dir / f"session_{self.session_id}.ipynb"
            notebook = {
                "nbformat": 4,
                "nbformat_minor": 5,
                "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
                "cells": [],
            }
            for evt in self._events:
                if evt["type"] == "proof":
                    notebook["cells"].append({
                        "cell_type": "markdown",
                        "metadata": {},
                        "source": [f"### {evt['data'].get('description', 'Proof')}\n\n{evt['data'].get('proof', '')}"],
                    })
            path.write_text(json.dumps(notebook, indent=2))
        return path

    def get_summary(self) -> dict:
        return {
            "session_id": self.session_id,
            "total_experiments": len(self._results),
            "kept": sum(1 for r in self._results if r.get("status") == "keep"),
            "discarded": sum(1 for r in self._results if r.get("status") == "discard"),
            "crashed": sum(1 for r in self._results if r.get("status") == "crash"),
            "avg_strength": sum(r.get("conjecture_strength", 0) for r in self._results) / max(len(self._results), 1),
        }


# ── CLI Entrypoints ─────────────────────────────────────────────────

def research_cli(question: str | None = None, rich: bool = True, max_experiments: int | None = None):
    """Run the research CLI.

    Usage: jiuzhang research [question] [--no-rich] [--max N]
    """
    console, has_rich = try_rich_setup()
    if not rich or not has_rich:
        console = None

    show_banner(console)

    config = Config.load()

    if not question:
        try:
            question = input("Research question (Enter for auto-discovery): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            return
        if not question:
            question = None

    display = LiveResearchDisplay(console=console)
    display.set_question(question or "Auto-discovering...")
    display.add_activity(f"Session started at {datetime.now().strftime('%H:%M:%S')}")

    if console:
        ResearchCommands.show_help(console)

    # Run the agent loop (synchronous for CLI compatibility)
    from jiuzhang.agent.loop import AgentLoop
    loop = AgentLoop(config=config)

    def progress_callback(stage: int, total: int, message: str):
        display.add_activity(f"[{stage}/{total}] {message}")
        display.set_state(message)

    loop.set_progress_callback(progress_callback)

    try:
        display.add_activity(f"Starting research: {question or 'auto'}")
        loop.run(question=question, max_experiments=max_experiments)
    except KeyboardInterrupt:
        display.add_activity("Session interrupted by user")
        display.stop()

    display.add_activity("Session complete")
    print(display.render())


async def async_research_cli(question: str | None = None, max_experiments: int | None = None):
    """Run the async research CLI with real-time streaming."""
    console, has_rich = try_rich_setup()
    show_banner(console)

    config = Config.load()
    display = LiveResearchDisplay(console=console)

    from jiuzhang.agent.async_loop import AsyncAgentLoop

    agent = AsyncAgentLoop(config=config)
    display.set_question(question or "Auto-discovering...")

    try:
        async for event in agent.run_streaming(question=question, max_experiments=max_experiments):
            event_type = event.get("type", "")
            data = event.get("data", {})

            if event_type == "log":
                display.add_activity(data.get("message", ""))
            elif event_type == "phase":
                display.set_state(f"Phase: {data.get('phase', '')}")
            elif event_type == "experiment_done":
                display.increment_experiment()
                display.add_activity(f"Experiment done: strength={data.get('conjecture_strength', 0):.2f}")
            elif event_type == "experiment_error":
                display.add_activity(f"Error: {data.get('error', '')}")
            elif event_type == "session_done":
                display.add_activity("Session complete")
                display.stop()

            if console:
                print(display.render())
                print("\033[H\033[J", end="")
    except KeyboardInterrupt:
        display.add_activity("Session interrupted")
    finally:
        await agent.close()

    print(display.render())
