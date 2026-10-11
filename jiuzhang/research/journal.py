"""Research Journal — persistent, searchable research notebook.

Provides:
- Chronological research log with search and tagging
- Link related experiments and conjectures
- Export to: Markdown, LaTeX, HTML, Jupyter notebook
- Visual knowledge graph of explored topics
- Integration with the memory system for cross-referencing
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
import re


@dataclass
class JournalEntry:
    """A single entry in the research journal."""
    id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    title: str = ""
    content: str = ""
    category: str = "general"  # theorem, conjecture, experiment, insight, question
    tags: list = field(default_factory=list)
    related_experiments: list = field(default_factory=list)  # commit hashes
    related_ids: list = field(default_factory=list)  # other entry IDs
    metrics: dict = field(default_factory=dict)  # optional metrics
    latex_source: str = ""   # LaTeX version for export
    status: str = "draft"    # draft, final, archived


class ResearchJournal:
    """Persistent research journal with multiple export formats.

    Usage:
        journal = ResearchJournal()
        journal.add_entry("Proved quadratic reciprocity", ...)
        journal.export_markdown("my_research.md")
    """

    def __init__(self, journal_path: str = "~/.jiuzhang/journal.json"):
        self._path = Path(journal_path).expanduser()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, JournalEntry] = {}
        self._load()

    def _load(self):
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for entry_data in data.get("entries", []):
                    entry = JournalEntry(**entry_data)
                    self._entries[entry.id] = entry
            except (json.JSONDecodeError, TypeError):
                pass

    def _save(self):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(
                {"entries": [self._entry_to_dict(e) for e in self._entries.values()]},
                f, ensure_ascii=False, indent=2, default=str,
            )

    def _entry_to_dict(self, entry: JournalEntry) -> dict:
        return {
            "id": entry.id,
            "timestamp": entry.timestamp,
            "title": entry.title,
            "content": entry.content,
            "category": entry.category,
            "tags": entry.tags,
            "related_experiments": entry.related_experiments,
            "related_ids": entry.related_ids,
            "metrics": entry.metrics,
            "latex_source": entry.latex_source,
            "status": entry.status,
        }

    def add_entry(
        self,
        title: str,
        content: str,
        category: str = "general",
        tags: Optional[list] = None,
        metrics: Optional[dict] = None,
        latex_source: str = "",
    ) -> str:
        """Add an entry to the journal. Returns the entry ID."""
        import hashlib
        entry_id = hashlib.sha256(
            f"{title}{content[:50]}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        entry = JournalEntry(
            id=entry_id,
            title=title,
            content=content,
            category=category,
            tags=tags or [],
            metrics=metrics or {},
            latex_source=latex_source,
        )
        self._entries[entry_id] = entry
        self._save()
        return entry_id

    def get_entry(self, entry_id: str) -> Optional[JournalEntry]:
        return self._entries.get(entry_id)

    def search(self, query: str) -> list:
        """Search journal entries by keyword."""
        query_lower = query.lower()
        results = []
        for entry in self._entries.values():
            if (query_lower in entry.title.lower()
                or query_lower in entry.content.lower()
                or any(query_lower in t.lower() for t in entry.tags)):
                results.append(entry)
        return sorted(results, key=lambda e: e.timestamp, reverse=True)

    def get_by_category(self, category: str) -> list:
        return [e for e in self._entries.values() if e.category == category]

    def get_by_tag(self, tag: str) -> list:
        return [e for e in self._entries.values() if tag in e.tags]

    def link_entries(self, id1: str, id2: str):
        """Link two entries together."""
        if id1 in self._entries and id2 in self._entries:
            if id2 not in self._entries[id1].related_ids:
                self._entries[id1].related_ids.append(id2)
            if id1 not in self._entries[id2].related_ids:
                self._entries[id2].related_ids.append(id1)
            self._save()

    def get_recent(self, n: int = 20) -> list:
        return sorted(
            self._entries.values(),
            key=lambda e: e.timestamp, reverse=True,
        )[:n]

    def get_stats(self) -> dict:
        categories = {}
        for e in self._entries.values():
            categories[e.category] = categories.get(e.category, 0) + 1
        return {
            "total_entries": len(self._entries),
            "by_category": categories,
            "total_tags": len(set(t for e in self._entries.values() for t in e.tags)),
        }

    # ── Export ────────────────────────────────────────────────────────

    def export_markdown(self, output_path: str):
        """Export journal to Markdown format."""
        lines = [
            "# JiuZhang Research Journal",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total entries: {len(self._entries)}",
            "",
            "---",
            "",
        ]

        entries = sorted(
            self._entries.values(), key=lambda e: e.timestamp, reverse=True
        )

        for entry in entries:
            lines.append(f"## {entry.title}")
            lines.append(f"**Date**: {entry.timestamp[:19]}")
            lines.append(f"**Category**: {entry.category}")
            if entry.tags:
                lines.append(f"**Tags**: {', '.join(entry.tags)}")
            lines.append("")
            lines.append(entry.content)
            if entry.latex_source:
                lines.append("")
                lines.append(f"```latex\n{entry.latex_source}\n```")
            lines.append("")
            lines.append("---")
            lines.append("")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def export_latex(self, output_path: str):
        """Export journal as a LaTeX article."""
        lines = [
            r"\documentclass{article}",
            r"\usepackage[utf8]{inputenc}",
            r"\usepackage{amsmath,amssymb,amsthm}",
            r"\usepackage{hyperref}",
            r"\title{JiuZhang Research Journal}",
            r"\author{Autonomous Research Agent}",
            r"\date{\today}",
            r"\begin{document}",
            r"\maketitle",
            r"\tableofcontents",
            r"\newpage",
        ]

        entries = sorted(
            self._entries.values(), key=lambda e: e.timestamp
        )
        for entry in entries:
            safe_title = re.sub(r'[^a-zA-Z0-9]', '_', entry.title)
            lines.append(rf"\section{{{entry.title}}}")
            lines.append(rf"\label{{sec:{safe_title}}}")

            content = entry.content
            # Convert markdown math to LaTeX
            content = re.sub(r'\$\$(.+?)\$\$', r'\\[\1\\]', content, flags=re.DOTALL)
            content = re.sub(r'\$(.+?)\$', r'$\1$', content)
            lines.append(content)
            lines.append("")

        lines.append(r"\end{document}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def export_html(self, output_path: str):
        """Export journal as a standalone HTML page."""
        entries_html = ""
        for entry in sorted(
            self._entries.values(), key=lambda e: e.timestamp, reverse=True
        ):
            tags_html = " ".join(
                f'<span class="tag">{t}</span>' for t in entry.tags
            )
            entries_html += f"""
            <article>
                <h2>{entry.title}</h2>
                <div class="meta">
                    <time>{entry.timestamp[:19]}</time>
                    <span class="category">{entry.category}</span>
                    {tags_html}
                </div>
                <div class="content">{entry.content}</div>
            </article>
            """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>JiuZhang Research Journal</title>
    <style>
        body {{ max-width: 800px; margin: 0 auto; padding: 20px; font-family: system-ui; }}
        article {{ border-bottom: 1px solid #eee; padding: 20px 0; }}
        .meta {{ color: #666; font-size: 0.9em; margin: 5px 0; }}
        .tag {{ background: #e8f0fe; padding: 2px 8px; border-radius: 12px; margin: 0 4px; }}
        .category {{ background: #fef3e0; padding: 2px 8px; border-radius: 12px; }}
        h1 {{ color: #1a1a2e; }}
    </style>
</head>
<body>
    <h1>JiuZhang Research Journal</h1>
    <p>Total entries: {len(self._entries)}</p>
    {entries_html}
</body>
</html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

    def export_jupyter(self, output_path: str):
        """Export journal as a Jupyter notebook (.ipynb)."""
        cells = []
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": ["# JiuZhang Research Journal\n", f"*{len(self._entries)} entries*"],
        })

        for entry in sorted(self._entries.values(), key=lambda e: e.timestamp, reverse=True):
            cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"## {entry.title}\n",
                    f"**Date**: {entry.timestamp[:19]}  \n",
                    f"**Category**: {entry.category}  \n",
                    f"\n{entry.content}",
                ],
            })
            if entry.latex_source:
                cells.append({
                    "cell_type": "code",
                    "metadata": {},
                    "source": entry.latex_source.split("\n"),
                    "outputs": [],
                })

        notebook = {
            "cells": cells,
            "metadata": {
                "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                "language_info": {"name": "python", "version": "3.10.0"},
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(notebook, f, indent=1, ensure_ascii=False)

    def generate_knowledge_graph(self) -> dict:
        """Generate a knowledge graph of linked entries."""
        nodes = []
        edges = []

        for entry in self._entries.values():
            nodes.append({
                "id": entry.id,
                "label": entry.title[:50],
                "category": entry.category,
                "tags": entry.tags,
            })

            for related in entry.related_ids:
                if related in self._entries:
                    edges.append({
                        "source": entry.id,
                        "target": related,
                    })

        return {"nodes": nodes, "edges": edges}
