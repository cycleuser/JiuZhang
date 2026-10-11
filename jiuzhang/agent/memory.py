"""Two-Phase Memory System for JiuZhang Research.

Inspired by nanobot's Dream memory consolidation:
- Short-term: conversation/research history with TTL eviction
- Long-term: SQLite-backed knowledge base with full-text search
- Dream consolidation: periodically distill research sessions into structured
  knowledge entries (theorems, conjectures, techniques, counterexamples, references)

Also implements the Research Flywheel (Phase 5b): a continuous self-improvement loop
that mines failures for knowledge gaps and auto-generates practice examples.
"""

import json
import sqlite3
import time
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional
import re


# ── Memory Types ──────────────────────────────────────────────────────

class MemoryType(Enum):
    THEOREM = "theorem"
    CONJECTURE = "conjecture"
    TECHNIQUE = "technique"
    COUNTEREXAMPLE = "counterexample"
    REFERENCE = "reference"
    FAILURE = "failure"
    INSIGHT = "insight"
    SESSION = "session"


class MemoryImportance(Enum):
    TRIVIAL = 0      # Ephemeral, not consolidated
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4     # Always kept


@dataclass
class MemoryEntry:
    id: str = ""
    memory_type: MemoryType = MemoryType.INSIGHT
    content: str = ""
    summary: str = ""
    tags: list = field(default_factory=list)
    importance: MemoryImportance = MemoryImportance.MEDIUM
    source_session: str = ""
    created_at: str = ""
    last_accessed: str = ""
    access_count: int = 0
    verified: bool = False
    related_ids: list = field(default_factory=list)


# ── Short-Term Memory ─────────────────────────────────────────────────

class ShortTermMemory:
    """In-memory session history with TTL eviction.

    Stores recent conversation turns, research results, and intermediate states.
    Evicts old entries based on TTL and importance.
    """

    def __init__(self, max_entries: int = 100, ttl_hours: int = 24):
        self._entries: list[MemoryEntry] = []
        self.max_entries = max_entries
        self.ttl = timedelta(hours=ttl_hours)

    def add(self, entry: MemoryEntry):
        """Add an entry, evicting old ones if needed."""
        entry.created_at = entry.created_at or datetime.now().isoformat()
        entry.last_accessed = entry.last_accessed or datetime.now().isoformat()
        self._entries.append(entry)
        self._evict()

    def _evict(self):
        """Evict entries that exceed TTL or count limits."""
        now = datetime.now()

        # Remove TTL-expired low-importance entries
        self._entries = [
            e for e in self._entries
            if (now - datetime.fromisoformat(e.created_at)) < self.ttl
            or e.importance.value >= MemoryImportance.HIGH.value
        ]

        # Trim to max_entries, keeping highest importance
        if len(self._entries) > self.max_entries:
            self._entries.sort(key=lambda e: (e.importance.value, e.access_count), reverse=True)
            self._entries = self._entries[:self.max_entries]

    def search(self, query: str) -> list:
        """Simple keyword search over recent entries."""
        query_lower = query.lower()
        matches = []
        for entry in self._entries:
            if query_lower in entry.content.lower() or query_lower in entry.summary.lower():
                entry.access_count += 1
                entry.last_accessed = datetime.now().isoformat()
                matches.append(entry)
        return matches

    def get_recent(self, n: int = 10) -> list:
        """Get most recent entries."""
        sorted_entries = sorted(
            self._entries,
            key=lambda e: e.created_at, reverse=True
        )
        return sorted_entries[:n]

    def clear(self):
        self._entries.clear()


# ── Long-Term Memory (SQLite) ─────────────────────────────────────────

class LongTermMemory:
    """Persistent SQLite-backed knowledge base with full-text search.

    Stores distilled knowledge: theorems, conjectures, techniques, counterexamples,
    and references. Supports FTS5 for fast semantic search.
    """

    def __init__(self, db_path: str = "~/.jiuzhang/memory.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT,
                    tags TEXT,
                    importance INTEGER DEFAULT 2,
                    source_session TEXT,
                    created_at TEXT,
                    last_accessed TEXT,
                    access_count INTEGER DEFAULT 0,
                    verified INTEGER DEFAULT 0,
                    related_ids TEXT
                )
            """)

            # Full-text search index
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    content, summary, tags,
                    content='memories',
                    content_rowid='rowid'
                )
            """)

            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                    INSERT INTO memories_fts(rowid, content, summary, tags)
                    VALUES (new.rowid, new.content, new.summary, new.tags);
                END;
            """)

            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                    INSERT INTO memories_fts(memories_fts, rowid, content, summary, tags)
                    VALUES ('delete', old.rowid, old.content, old.summary, old.tags);
                END;
            """)

            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                    INSERT INTO memories_fts(memories_fts, rowid, content, summary, tags)
                    VALUES ('delete', old.rowid, old.content, old.summary, old.tags);
                    INSERT INTO memories_fts(rowid, content, summary, tags)
                    VALUES (new.rowid, new.content, new.summary, new.tags);
                END;
            """)

            conn.commit()

    def store(self, entry: MemoryEntry):
        """Store a memory entry persistently."""
        entry.created_at = entry.created_at or datetime.now().isoformat()
        entry.last_accessed = entry.last_accessed or datetime.now().isoformat()
        if not entry.id:
            entry.id = hashlib.sha256(
                f"{entry.memory_type.value}{entry.content[:100]}{time.time()}".encode()
            ).hexdigest()[:16]

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO memories
                   (id, memory_type, content, summary, tags, importance,
                    source_session, created_at, last_accessed, access_count, verified, related_ids)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    entry.id,
                    entry.memory_type.value,
                    entry.content,
                    entry.summary,
                    json.dumps(entry.tags),
                    entry.importance.value,
                    entry.source_session,
                    entry.created_at,
                    entry.last_accessed,
                    entry.access_count,
                    1 if entry.verified else 0,
                    json.dumps(entry.related_ids),
                ),
            )
            conn.commit()

    def search(self, query: str, limit: int = 10) -> list:
        """Full-text search over all stored knowledge."""
        with sqlite3.connect(str(self.db_path)) as conn:
            try:
                rows = conn.execute(
                    """SELECT m.* FROM memories m
                       JOIN memories_fts fts ON m.rowid = fts.rowid
                       WHERE memories_fts MATCH ?
                       ORDER BY rank
                       LIMIT ?""",
                    (query, limit),
                ).fetchall()
            except sqlite3.OperationalError:
                # FTS query syntax error — fall back to LIKE
                rows = conn.execute(
                    """SELECT * FROM memories
                       WHERE content LIKE ? OR summary LIKE ?
                       ORDER BY importance DESC
                       LIMIT ?""",
                    (f"%{query}%", f"%{query}%", limit),
                ).fetchall()

        return [self._row_to_entry(row) for row in rows]

    def get_by_type(self, memory_type: MemoryType, limit: int = 50) -> list:
        """Get entries by type."""
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                "SELECT * FROM memories WHERE memory_type = ? ORDER BY importance DESC LIMIT ?",
                (memory_type.value, limit),
            ).fetchall()
        return [self._row_to_entry(row) for row in rows]

    def get_high_importance(self, limit: int = 20) -> list:
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                "SELECT * FROM memories WHERE importance >= ? ORDER BY created_at DESC LIMIT ?",
                (MemoryImportance.HIGH.value, limit),
            ).fetchall()
        return [self._row_to_entry(row) for row in rows]

    def _row_to_entry(self, row: tuple) -> MemoryEntry:
        return MemoryEntry(
            id=row[0],
            memory_type=MemoryType(row[1]),
            content=row[2],
            summary=row[3] or "",
            tags=json.loads(row[4]) if row[4] else [],
            importance=MemoryImportance(row[5]),
            source_session=row[6] or "",
            created_at=row[7] or "",
            last_accessed=row[8] or "",
            access_count=row[9] or 0,
            verified=bool(row[10]),
            related_ids=json.loads(row[11]) if row[11] else [],
        )


# ── Dream Consolidation ───────────────────────────────────────────────

class DreamConsolidator:
    """Periodically distill short-term research sessions into long-term knowledge.

    Inspired by nanobot's Dream two-phase memory: during idle periods, the consolidator
    extracts structured knowledge from recent research activity and stores it permanently.
    """

    def __init__(self, short_term: ShortTermMemory, long_term: LongTermMemory):
        self.short_term = short_term
        self.long_term = long_term

    def consolidate(self) -> dict:
        """Run consolidation: distill recent sessions into knowledge entries.

        Returns:
            Dict with consolidation statistics
        """
        recent = self.short_term.get_recent(50)
        if not recent:
            return {"consolidated": 0, "skipped": 0}

        consolidated = 0
        skipped = 0

        for entry in recent:
            # Only consolidate medium+ importance entries
            if entry.importance.value < MemoryImportance.MEDIUM.value:
                skipped += 1
                continue

            # Check if already in long-term
            existing = self.long_term.search(entry.summary[:100], limit=1)
            if existing:
                skipped += 1
                continue

            # Extract distilled summary
            distilled = self._distill(entry)

            # Store in long-term
            distilled_entry = MemoryEntry(
                memory_type=entry.memory_type,
                content=distilled,
                summary=self._summarize(distilled),
                tags=entry.tags,
                importance=entry.importance,
                source_session=entry.source_session,
                verified=entry.verified,
                related_ids=entry.related_ids,
            )
            self.long_term.store(distilled_entry)
            consolidated += 1

        return {"consolidated": consolidated, "skipped": skipped}

    def _distill(self, entry: MemoryEntry) -> str:
        """Distill a memory entry into its essential mathematical content."""
        # Extract key equations
        equations = re.findall(r'\$(.+?)\$', entry.content)
        key_info = []
        if equations:
            key_info.append("Key equations: " + "; ".join(equations[:3]))
        if entry.summary:
            key_info.append(entry.summary)

        return "\n".join(key_info) if key_info else entry.content[:500]

    def _summarize(self, text: str) -> str:
        """Generate a 1-2 sentence summary."""
        sentences = re.split(r'[.!?。！？]', text)
        return ". ".join(sentences[:2]).strip()[:200]


# ── Research Flywheel ─────────────────────────────────────────────────

class ResearchFlywheel:
    """Continuous self-improvement through failure analysis.

    Tracks every research outcome, mines failures for knowledge gaps,
    auto-generates targeted practice examples, and tracks improvement over time.
    """

    def __init__(self, long_term: LongTermMemory):
        self.long_term = long_term
        self._failure_counts: dict[str, int] = {}  # failure_type -> count
        self._improvement_log: list = []

    def record_outcome(
        self,
        task: str,
        success: bool,
        failure_type: str = "",
        details: str = "",
    ):
        """Record a research outcome."""
        if not success and failure_type:
            self._failure_counts[failure_type] = self._failure_counts.get(failure_type, 0) + 1

            # Store failure for learning
            entry = MemoryEntry(
                memory_type=MemoryType.FAILURE,
                content=f"Task: {task}\nFailure: {failure_type}\nDetails: {details}",
                summary=f"Failed at {failure_type}: {task[:100]}",
                tags=[failure_type, "failure"],
                importance=MemoryImportance.MEDIUM,
            )
            self.long_term.store(entry)

    def get_gaps(self) -> list:
        """Identify knowledge gaps from accumulated failures."""
        gaps = []
        sorted_failures = sorted(
            self._failure_counts.items(), key=lambda x: x[1], reverse=True
        )
        for failure_type, count in sorted_failures[:5]:
            gaps.append({
                "type": failure_type,
                "count": count,
                "suggestion": self._get_suggestion(failure_type),
            })
        return gaps

    def _get_suggestion(self, failure_type: str) -> str:
        suggestions = {
            "verification_failure": "Study more examples of verified proofs; practice cross-checking with SymPy",
            "proof_incomplete": "Practice completing partial proofs; review common proof strategies",
            "counterexample_found": "Refine conjecture scope; add preconditions to exclude counterexamples",
            "symbolic_error": "Review SymPy fundamentals; check variable definitions and assumptions",
            "reasoning_gap": "Practice step-by-step reasoning; break complex problems into sub-problems",
            "timeout": "Reduce problem scope; break into smaller, independently verifiable sub-conjectures",
        }
        return suggestions.get(failure_type, "Review fundamental concepts in this area")

    def generate_practice(self, failure_type: str) -> list:
        """Generate targeted practice examples for a failure type."""
        practices = {
            "verification_failure": [
                "Verify: (x+1)^2 = x^2 + 2x + 1 using SymPy",
                "Verify: sin^2(x) + cos^2(x) = 1 using SymPy",
                "Check if: d/dx(e^x * sin(x)) = e^x * (sin(x) + cos(x))",
            ],
            "proof_incomplete": [
                "Complete the proof: If n is odd, n^2 is odd",
                "Complete the proof: √2 is irrational",
                "Complete the proof: There are infinitely many primes",
            ],
            "counterexample_found": [
                "Find counterexample: All odd numbers are prime",
                "Find counterexample: n^2 + n + 41 is always prime",
                "Find counterexample: All functions continuous at a point are differentiable",
            ],
            "symbolic_error": [
                "Compute: integral of x^2 * sin(x)",
                "Compute: derivative of ln(x^2 + 1)",
                "Solve: x^3 - 6x^2 + 11x - 6 = 0",
            ],
        }
        return practices.get(failure_type, ["Review foundational material for this topic"])

    def get_progress_report(self) -> str:
        """Generate a progress report with improvement metrics."""
        lines = ["📊 Research Flywheel Progress Report", "=" * 40]

        gaps = self.get_gaps()
        if gaps:
            lines.append("\nKnowledge Gaps:")
            for gap in gaps:
                lines.append(f"  • {gap['type']}: {gap['count']} failures → {gap['suggestion']}")
        else:
            lines.append("\nNo significant knowledge gaps detected.")

        total_failures = sum(self._failure_counts.values())
        lines.append(f"\nTotal failures tracked: {total_failures}")

        if self._improvement_log:
            lines.append(f"\nImprovement log: {len(self._improvement_log)} entries")
            for entry in self._improvement_log[-3:]:
                lines.append(f"  {entry}")

        return "\n".join(lines)
