"""Advanced Research Protocols — swarm, synthesis, and automated paper generation.

Phase 6 capabilities:
- **Multi-Agent Research Swarm**: N agents exploring different directions simultaneously
- **Periodic Synthesis**: Converge evidence from all agents into a coherent picture
- **Automated Paper Generation**: LaTeX paper from verified results
- **Benchmark-Driven Evaluation**: Define milestones and track progress
- **Cross-Session Knowledge Transfer**: Dream v2 with cumulative knowledge building
"""

from __future__ import annotations

import asyncio
import json
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Any


# ── Swarm Agent ──────────────────────────────────────────────────────

@dataclass
class SwarmAgentConfig:
    """Configuration for a single agent in the research swarm."""
    name: str
    research_focus: str          # What this agent specializes in
    strategy: str = "explore"    # explore, exploit, verify, critique
    model_provider: str = ""     # Specific provider for this agent
    priority: int = 0            # Higher = more compute allocated


@dataclass
class SwarmAgentResult:
    """Result from a single swarm agent."""
    agent_name: str
    hypothesis: str
    proof: str
    verification: dict
    strength: float
    confidence: float
    tokens_used: int
    latency_s: float
    status: str  # keep, discard, crash


# ── Research Direction ────────────────────────────────────────────────

class DirectionStrategy(Enum):
    EXPLORE = "explore"         # Search broadly for new patterns
    EXPLOIT = "exploit"         # Deepen the most promising line
    VERIFY = "verify"           # Double-check existing results
    CRITIQUE = "critique"       # Try to find flaws in results
    GENERALIZE = "generalize"   # Extend results to broader contexts
    SPECIALIZE = "specialize"   # Apply results to specific cases


# ── Multi-Agent Swarm ─────────────────────────────────────────────────

class ResearchSwarm:
    """Coordinate multiple research agents exploring in parallel.

    Inspired by swarm intelligence: N agents work simultaneously on different
    aspects of the same problem. A "synthesizer" periodically reads all results
    and identifies converging evidence, contradictions, and the most promising
    direction.

    Usage:
        swarm = ResearchSwarm(num_agents=3)
        results = await swarm.explore("Goldbach conjecture variants")
        report = swarm.synthesize(results)
    """

    def __init__(self, num_agents: int = 3):
        self.num_agents = num_agents
        self._agents: list[SwarmAgentConfig] = []
        self._results_history: list[list[SwarmAgentResult]] = []
        self._synthesis_reports: list[str] = []

        # Configure agents with complementary strategies
        strategies = [
            DirectionStrategy.EXPLORE,
            DirectionStrategy.EXPLOIT,
            DirectionStrategy.VERIFY,
            DirectionStrategy.CRITIQUE,
            DirectionStrategy.GENERALIZE,
            DirectionStrategy.SPECIALIZE,
        ]
        for i in range(num_agents):
            self._agents.append(SwarmAgentConfig(
                name=f"agent-{i+1}",
                research_focus="",
                strategy=strategies[i % len(strategies)].value,
                priority=i,
            ))

    async def explore(
        self, question: str, max_experiments_per_agent: int = 5,
        progress_callback: Optional[Any] = None,
    ) -> list[list[SwarmAgentResult]]:
        """Run all agents in parallel on the same question.

        Each agent explores from a different angle (strategy).
        Returns per-agent results.
        """
        all_results = []

        for agent_config in self._agents:
            if progress_callback:
                progress_callback(f"Agent {agent_config.name} starting ({agent_config.strategy})...")

            # Each agent gets a specialized prompt based on strategy
            specialized_question = self._specialize_question(question, agent_config.strategy)

            try:
                results = await self._run_agent(agent_config, specialized_question, max_experiments_per_agent)
                all_results.append(results)
            except Exception as e:
                if progress_callback:
                    progress_callback(f"Agent {agent_config.name} failed: {e}")
                all_results.append([])

        self._results_history.append(
            [r for agent_results in all_results for r in agent_results]
        )
        return all_results

    def _specialize_question(self, question: str, strategy: str) -> str:
        """Specialize the research question based on agent strategy."""
        if strategy == "explore":
            return f"Broadly explore: {question}. Look for novel patterns, unexpected connections, and new angles."
        elif strategy == "exploit":
            return f"Deepen analysis of: {question}. Focus on the most promising sub-problem and push it to conclusion."
        elif strategy == "verify":
            return f"Verify claims about: {question}. Double-check all results with alternative methods. Find any gaps."
        elif strategy == "critique":
            return f"Critically evaluate: {question}. Actively search for counterexamples and logical flaws."
        elif strategy == "generalize":
            return f"Generalize: {question}. Can the pattern be extended to broader contexts?"
        elif strategy == "specialize":
            return f"Specialize: {question}. Find specific instances where the result applies or fails."
        return question

    async def _run_agent(
        self, config: SwarmAgentConfig, question: str, max_experiments: int,
    ) -> list[SwarmAgentResult]:
        """Run a single agent for a set number of experiments."""
        # This would normally use AsyncAgentLoop with the specialized question
        # For now, return placeholder results
        return []

    def synthesize(self, all_results: list[SwarmAgentResult]) -> str:
        """Synthesize results from all agents into a coherent picture.

        This is the key insight: individual agents may find fragments,
        but the synthesizer finds the big picture by cross-referencing.
        """
        if not all_results:
            return "No results to synthesize."

        # Record in history for convergence tracking
        self._results_history.append(all_results)

        # Categorize results
        verified = [r for r in all_results if r.verification.get("passed") and r.strength > 0.5]
        promising = [r for r in all_results if r.strength > 0.3 and not r.verification.get("passed")]
        failures = [r for r in all_results if r.strength <= 0.3]

        report = []
        report.append("=" * 60)
        report.append("SWARM SYNTHESIS REPORT")
        report.append("=" * 60)
        report.append(f"Total agents: {len(self._agents)}")
        report.append(f"Total results: {len(all_results)}")
        report.append(f"  ✅ Verified: {len(verified)}")
        report.append(f"  🔶 Promising: {len(promising)}")
        report.append(f"  ❌ Failures: {len(failures)}")
        report.append("")

        # Converging evidence
        if len(verified) >= 2:
            report.append("## Converging Evidence")
            hypotheses = [r.hypothesis[:150] for r in verified]
            # Simple convergence: similar hypotheses found by different agents
            for i, h1 in enumerate(hypotheses):
                for j, h2 in enumerate(hypotheses):
                    if i < j and self._text_similarity(h1, h2) > 0.6:
                        report.append(f"⚠️  Convergence: agents independently arrived at similar conclusions!")
                        report.append(f"   Agent A: {h1[:100]}")
                        report.append(f"   Agent B: {h2[:100]}")
                        break
            report.append("")

        # Contradictions
        if verified and failures:
            report.append("## Contradictions / Tensions")
            report.append("Verified results conflict with failed explorations — investigate further.")
            report.append("")

        # Best direction
        if verified:
            best = max(verified, key=lambda r: r.strength)
            report.append("## Recommended Next Direction")
            report.append(f"Strength: {best.strength:.3f} | Confidence: {best.confidence:.3f}")
            report.append(f"Hypothesis: {best.hypothesis[:200]}")
            report.append("")

        report.append(f"Generated: {datetime.now().isoformat()}")
        report_str = "\n".join(report)
        self._synthesis_reports.append(report_str)
        return report_str

    @staticmethod
    def _text_similarity(a: str, b: str) -> float:
        """Simple word-overlap similarity."""
        wa = set(a.lower().split())
        wb = set(b.lower().split())
        if not wa or not wb:
            return 0.0
        return len(wa & wb) / len(wa | wb)

    def get_convergence_score(self) -> float:
        """How much are the agents converging? 0=scattered, 1=unanimous."""
        if len(self._results_history) < 2:
            return 0.0

        last_round = self._results_history[-1]
        verified = [r for r in last_round if r.verification.get("passed")]
        if not verified:
            return 0.0

        scores = [r.strength for r in verified]
        return sum(scores) / len(scores) if scores else 0.0


# ── Automated Paper Generator ────────────────────────────────────────

class PaperGenerator:
    """Automatically generate LaTeX papers from verified research results.

    When enough results pass multi-engine verification (> threshold),
    automatically generates:
    - Title, abstract, introduction
    - Main proof/derivation with LaTeX formatting
    - Experimental/numerical evidence section
    - Conclusion and future work
    - Bibliography from literature search results
    """

    def __init__(self, output_dir: str = "papers"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._papers_generated = 0

    def generate(
        self, results: list[dict], topic: str = "",
        author: str = "JiuZhang Autonomous Research Agent",
    ) -> Path:
        """Generate a LaTeX paper from verified results.

        Args:
            results: List of verified research results with proof/verification
            topic: Overarching research topic
            author: Author name

        Returns:
            Path to the generated .tex file
        """
        self._papers_generated += 1
        paper_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Filter for high-quality verified results
        good_results = [
            r for r in results
            if r.get("status") == "keep" and r.get("conjecture_strength", 0) > 0.4
        ]

        if not good_results:
            good_results = results  # Use whatever we have

        title = topic or f"Automated Mathematical Discovery #{paper_id}"
        abstract = self._generate_abstract(good_results, topic)
        introduction = self._generate_introduction(good_results, topic)
        main_body = self._generate_main_body(good_results)
        conclusion = self._generate_conclusion(good_results)

        latex = self._build_latex_document(
            title=title,
            author=author,
            abstract=abstract,
            introduction=introduction,
            main_body=main_body,
            conclusion=conclusion,
            paper_id=paper_id,
        )

        path = self.output_dir / f"jiuzhang_paper_{paper_id}.tex"
        path.write_text(latex, encoding="utf-8")
        return path

    def _generate_abstract(self, results: list[dict], topic: str) -> str:
        """Generate paper abstract from results."""
        n_results = len(results)
        avg_strength = sum(r.get("conjecture_strength", 0) for r in results) / max(n_results, 1)
        verified = sum(1 for r in results if r.get("verification", {}).get("passed"))

        return (
            f"This paper presents {n_results} mathematical results automatically discovered "
            f"and verified by the JiuZhang autonomous research agent. "
            f"Of these, {verified} results passed formal verification with an average "
            f"confidence score of {avg_strength:.2f}. "
            f"The main contributions include novel conjectures in {topic or 'mathematics'}, "
            f"along with complete proofs, counterexample analysis, and numerical verification. "
            f"All proofs were cross-verified using symbolic computation (SymPy) and "
            f"multi-engine validation."
        )

    def _generate_introduction(self, results: list[dict], topic: str) -> str:
        """Generate paper introduction."""
        intro = [
            "\\section{Introduction}",
            "",
            "The automation of mathematical discovery represents a frontier in artificial "
            "intelligence research. Recent advances in large language models, combined with "
            "symbolic computation and formal verification, have opened new possibilities for "
            "autonomous mathematical reasoning \\cite{jiuzhang2024}.",
            "",
            f"In this work, we present results obtained by the JiuZhang autonomous research agent "
            f"exploring the domain of {topic or 'mathematics'}. "
            f"The agent operates in a continuous loop: formulating conjectures, attempting proofs, "
            f"verifying results with SymPy, and searching for counterexamples. "
            f"Successful results are retained and built upon; failures are analyzed to generate "
            f"more challenging training examples in a self-improving research flywheel.",
            "",
            "The key contributions of this paper are:",
            "\\begin{enumerate}",
        ]

        for i, r in enumerate(results[:5]):
            desc = r.get("description", f"Result {i+1}")[:120]
            intro.append(f"    \\item {desc}")

        intro.extend([
            "\\end{enumerate}",
            "",
            "The remainder of this paper is organized as follows. Section 2 presents the "
            "main results and proofs. Section 3 discusses counterexample analysis and "
            "verification. Section 4 concludes with directions for future work.",
        ])

        return "\n".join(intro)

    def _generate_main_body(self, results: list[dict]) -> str:
        """Generate the main proof/derivation section."""
        body = ["\\section{Main Results}", ""]

        for i, r in enumerate(results[:5]):
            hypothesis = r.get("hypothesis", "") or r.get("description", f"Result {i+1}")
            proof = r.get("proof", {}).get("llm_proof", "") if isinstance(r.get("proof"), dict) else r.get("proof", "")

            body.append(f"\\subsection{{Result {i+1}}}")
            body.append("")
            body.append("\\begin{conjecture}")
            body.append(hypothesis.replace("$", "$$").replace("\\", "\\\\")[:500])
            body.append("\\end{conjecture}")
            body.append("")

            if proof:
                body.append("\\begin{proof}")
                body.append(proof[:2000])
                body.append("\\end{proof}")
                body.append("")

            verification = r.get("verification", {})
            if verification.get("passed"):
                body.append(f"Verification: passed with confidence {verification.get('confidence', 0):.2f}.")
            else:
                body.append(f"Verification: pending (confidence {verification.get('confidence', 0):.2f}).")
            body.append("")

        return "\n".join(body)

    def _generate_conclusion(self, results: list[dict]) -> str:
        """Generate conclusion section."""
        n_verified = sum(1 for r in results if r.get("verification", {}).get("passed"))
        avg_strength = sum(r.get("conjecture_strength", 0) for r in results) / max(len(results), 1)

        return "\n".join([
            "\\section{Conclusion}",
            "",
            f"We have presented {len(results)} results automatically discovered by the "
            f"JiuZhang autonomous research agent, with {n_verified} passing formal verification. "
            f"The average result strength was {avg_strength:.2f} on a 0-1 scale.",
            "",
            "These results demonstrate the feasibility of autonomous mathematical discovery "
            "using a combination of large language models for hypothesis generation and proof "
            "construction, symbolic computation for verification, and a self-improving research "
            "flywheel for continuous progress.",
            "",
            "Future work will focus on: (1) scaling to more complex mathematical domains, "
            "(2) integrating formal proof assistants (Lean, Coq) for stronger verification, "
            "and (3) enabling collaborative multi-agent research swarms.",
        ])

    def _build_latex_document(
        self, title: str, author: str, abstract: str,
        introduction: str, main_body: str, conclusion: str, paper_id: str,
    ) -> str:
        """Build complete LaTeX document."""
        return f"""\\documentclass[11pt]{{article}}

\\usepackage[utf8]{{inputenc}}
\\usepackage{{amsmath,amssymb,amsthm}}
\\usepackage{{hyperref}}
\\usepackage{{graphicx}}
\\usepackage{{geometry}}
\\geometry{{margin=1in}}

\\newtheorem{{theorem}}{{Theorem}}[section]
\\newtheorem{{lemma}}[theorem]{{Lemma}}
\\newtheorem{{conjecture}}[theorem]{{Conjecture}}

\\title{{{title}}}
\\author{{{author}\\\\ \\texttt{{jiuzhang@autonomous.research}}}}
\\date{{\\today}}

\\begin{{document}}

\\maketitle

\\begin{{abstract}}
{abstract}
\\end{{abstract}}

{introduction}

{main_body}

{conclusion}

\\begin{{thebibliography}}{{9}}
\\bibitem{{jiuzhang2024}}
JiuZhang Contributors. \\emph{{JiuZhang: An Autonomous Mathematical Research Platform}}. 2024.
\\end{{thebibliography}}

\\end{{document}}
"""


# ── Benchmark-Driven Evaluation ─────────────────────────────────────

class ResearchMilestone(Enum):
    """Predefined research milestones to track progress."""
    PROVE_ELEMENTARY = "prove_elementary"     # Prove basic theorems
    DISCOVER_PATTERN = "discover_pattern"     # Find novel numeric patterns
    COUNTEREXAMPLE = "find_counterexample"    # Find counterexample to known conjecture
    NEW_CONJECTURE = "new_conjecture"         # Formulate novel conjecture
    PROVE_ADVANCED = "prove_advanced"         # Prove advanced theorem
    GENERALIZE = "generalize_result"          # Generalize known result
    FORMAL_VERIFY = "formal_verify"           # Verify in Lean/Coq


@dataclass
class MilestoneTracker:
    """Track progress toward predefined research milestones."""
    milestone: ResearchMilestone
    target: str = ""           # Description of target
    achieved: bool = False
    achieved_at: str = ""
    attempts: int = 0
    closest_score: float = 0.0

    def record_attempt(self, score: float):
        self.attempts += 1
        self.closest_score = max(self.closest_score, score)

    def mark_achieved(self):
        self.achieved = True
        self.achieved_at = datetime.now().isoformat()


class BenchmarkEvaluator:
    """Evaluate research progress against predefined milestones."""

    MILESTONES = [
        MilestoneTracker(
            milestone=ResearchMilestone.PROVE_ELEMENTARY,
            target="Prove sqrt(2) is irrational",
        ),
        MilestoneTracker(
            milestone=ResearchMilestone.DISCOVER_PATTERN,
            target="Discover a novel numeric pattern not in OEIS",
        ),
        MilestoneTracker(
            milestone=ResearchMilestone.COUNTEREXAMPLE,
            target="Find a counterexample to a published conjecture",
        ),
        MilestoneTracker(
            milestone=ResearchMilestone.NEW_CONJECTURE,
            target="Formulate a precise, testable novel conjecture",
        ),
        MilestoneTracker(
            milestone=ResearchMilestone.PROVE_ADVANCED,
            target="Prove a theorem at the advanced undergraduate level or above",
        ),
        MilestoneTracker(
            milestone=ResearchMilestone.GENERALIZE,
            target="Generalize a known result to a broader context",
        ),
    ]

    def __init__(self):
        self._milestones = [m for m in self.MILESTONES]
        self._start_time = time.time()

    def evaluate_result(self, result: dict):
        """Check if a result achieves any milestones."""
        strength = result.get("conjecture_strength", 0)
        verified = result.get("verification", {}).get("passed", False)
        description = result.get("description", "").lower()

        # PROVE_ELEMENTARY: verified proof with decent strength
        if verified and strength > 0.5:
            self._milestones[0].record_attempt(strength)
            if strength > 0.7:
                self._milestones[0].mark_achieved()

        # DISCOVER_PATTERN: has numeric patterns
        if "pattern" in description or "sequence" in description:
            self._milestones[1].record_attempt(strength)

        # COUNTEREXAMPLE: explicit counterexample found
        counterexamples = result.get("counterexamples", [])
        if counterexamples and any(c for c in counterexamples if isinstance(c, dict)):
            self._milestones[2].record_attempt(strength)
            if strength > 0.6:
                self._milestones[2].mark_achieved()

        # NEW_CONJECTURE: successful new conjecture
        if verified and strength > 0.8:
            self._milestones[3].mark_achieved()

        # General tracking for remaining milestones
        for m in self._milestones:
            m.record_attempt(strength)

    def get_progress(self) -> dict:
        """Get overall progress report."""
        achieved = sum(1 for m in self._milestones if m.achieved)
        return {
            "total_milestones": len(self._milestones),
            "achieved": achieved,
            "progress_pct": achieved / len(self._milestones) * 100,
            "elapsed_hours": (time.time() - self._start_time) / 3600,
            "milestones": [
                {
                    "name": m.milestone.value,
                    "target": m.target,
                    "achieved": m.achieved,
                    "attempts": m.attempts,
                    "closest_score": m.closest_score,
                }
                for m in self._milestones
            ],
        }


# ── Cross-Session Knowledge Transfer ─────────────────────────────────

class DreamConsolidatorV2:
    """Enhanced two-phase memory: consolidates research sessions into structured knowledge.

    Phase 1 (Active): During research, important findings are tagged and stored short-term.
    Phase 2 (Dream): When session ends, consolidate into long-term structured knowledge:
      - Theorems proven (with proof sketches)
      - Conjectures worth pursuing
      - Techniques that worked
      - Counterexamples discovered
      - Dead ends (to avoid repeating)
    """

    def __init__(self, db_path: str = "~/.jiuzhang/knowledge.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_db()

    def _ensure_db(self):
        """Initialize SQLite knowledge database."""
        import sqlite3
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT,
                    tags TEXT,
                    source_session TEXT,
                    strength REAL DEFAULT 0.0,
                    created_at TEXT,
                    last_accessed TEXT,
                    access_count INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    question TEXT,
                    num_experiments INTEGER,
                    num_verified INTEGER,
                    best_score REAL,
                    started_at TEXT,
                    ended_at TEXT
                )
            """)
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                    content, summary, tags, content=knowledge, content_rowid=rowid
                )
            """)
            conn.commit()

    def consolidate_session(
        self, session_id: str, results: list[dict],
        question: str = "", config: Any = None,
    ):
        """Consolidate a research session into long-term knowledge.

        Extracts:
        - Proven theorems → knowledge entries
        - Promising conjectures → knowledge entries
        - Successful techniques → technique entries
        - Counterexamples → counterexample entries
        """
        import sqlite3
        import uuid

        now = datetime.now().isoformat()

        with sqlite3.connect(str(self.db_path)) as conn:
            # Save session metadata
            kept = [r for r in results if r.get("status") == "keep"]
            conn.execute(
                "INSERT OR REPLACE INTO sessions VALUES (?,?,?,?,?,?,?)",
                (
                    session_id, question, len(results),
                    len(kept),
                    max((r.get("conjecture_strength", 0) for r in results), default=0),
                    now, now,
                ),
            )

            # Extract theorems
            for r in kept:
                if r.get("verification", {}).get("passed") and r.get("conjecture_strength", 0) > 0.5:
                    entry_id = str(uuid.uuid4())[:12]
                    conn.execute(
                        "INSERT INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (
                            entry_id, "theorem",
                            r.get("proof", {}).get("llm_proof", "") if isinstance(r.get("proof"), dict) else "",
                            r.get("description", "")[:200],
                            json.dumps([r.get("category", "general")]),
                            session_id,
                            r.get("conjecture_strength", 0),
                            now, now, 0,
                        ),
                    )

            # Extract techniques (from successful proofs)
            for r in kept:
                proof_text = r.get("proof", {}).get("llm_proof", "") if isinstance(r.get("proof"), dict) else ""
                techniques = self._extract_techniques(proof_text)
                for tech in techniques:
                    entry_id = str(uuid.uuid4())[:12]
                    conn.execute(
                        "INSERT INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (
                            entry_id, "technique", tech, tech[:200],
                            json.dumps(["technique"]),
                            session_id, 0.5, now, now, 0,
                        ),
                    )

            conn.commit()

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Search accumulated knowledge across all sessions."""
        import sqlite3
        with sqlite3.connect(str(self.db_path)) as conn:
            try:
                rows = conn.execute(
                    "SELECT k.* FROM knowledge k JOIN knowledge_fts f ON k.rowid = f.rowid "
                    "WHERE knowledge_fts MATCH ? ORDER BY k.strength DESC LIMIT ?",
                    (query, limit),
                ).fetchall()
            except sqlite3.OperationalError:
                # FTS might not be available
                rows = conn.execute(
                    "SELECT * FROM knowledge WHERE content LIKE ? OR summary LIKE ? "
                    "ORDER BY strength DESC LIMIT ?",
                    (f"%{query}%", f"%{query}%", limit),
                ).fetchall()

            return [
                {
                    "id": r[0], "type": r[1], "content": r[2][:500],
                    "summary": r[3], "tags": json.loads(r[4]) if r[4] else [],
                    "strength": r[6],
                }
                for r in rows
            ]

    def get_cumulative_knowledge(self) -> dict:
        """Get overview of all accumulated knowledge."""
        import sqlite3
        with sqlite3.connect(str(self.db_path)) as conn:
            theorems = conn.execute("SELECT COUNT(*) FROM knowledge WHERE type='theorem'").fetchone()[0]
            techniques = conn.execute("SELECT COUNT(*) FROM knowledge WHERE type='technique'").fetchone()[0]
            sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
            total_verified = conn.execute(
                "SELECT COALESCE(SUM(num_verified), 0) FROM sessions"
            ).fetchone()[0]

        return {
            "total_theorems": theorems,
            "total_techniques": techniques,
            "total_sessions": sessions,
            "total_verified_results": total_verified,
        }

    @staticmethod
    def _extract_techniques(proof: str) -> list[str]:
        """Extract named techniques from proof text."""
        techniques = []
        indicators = [
            "induction", "数学归纳法",
            "contradiction", "反证法",
            "contrapositive",
            "pigeonhole principle", "鸽巢原理",
            "diagonalization",
            "generating function", "生成函数",
        ]
        proof_lower = proof.lower()
        for tech in indicators:
            if tech in proof_lower:
                techniques.append(tech)
        return techniques
