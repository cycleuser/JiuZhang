"""Research Program — human-authored research directives for the autonomous agent.

Inspired by autoresearch's `program.md` pattern (Karpathy, 2026): the human writes
a Markdown file describing the research goal, constraints, and methodology, and the
autonomous agent executes it indefinitely.

Unlike autoresearch's single-file approach (only train.py is editable), JiuZhang's
ResearchProgram defines:
- Research goals and success criteria
- Allowed/disallowed operations and tools
- Time/money budgets per experiment and total
- Model routing preferences
- Output format and logging requirements
- Safety and ethical boundaries
"""

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
import re
try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


DEFAULT_PROGRAM = """# JiuZhang Autonomous Math Research Program

## Goal
Explore and advance mathematical knowledge through autonomous experimentation.
The agent will formulate conjectures, attempt proofs, search for counterexamples,
conduct literature reviews, and iterate.

## Success Criteria
- Valid proofs discovered (verified by SymPy + cross-checked)
- Novel conjectures with empirical evidence
- Counterexamples found for known conjectures (within verified ranges)
- Research papers generated with proper citations

## Constraints
- **Time budget per experiment**: 300 seconds (5 minutes)
- **Total run budget**: unlimited (runs until human stops)
- **Model budget**: prefer local model for routine work; escalate only on hard failures
- **Disk**: store results in ~/.jiuzhang/research_autonomous/

## Allowed Operations
- Symbolic computation (SymPy)
- Numerical experiments (numpy, scipy)
- Literature search (arXiv, CrossRef)
- Code execution in sandbox
- File I/O within output directory
- Git operations on research branch

## Disallowed Operations
- Network requests to untrusted hosts
- System modification outside output directory
- Installing packages
- Modifying core jiuzhang source code

## Model Routing
- Routine computation → local model (ollama / openai_compatible)
- Theorem proving → larger local model if available
- Deep analysis → cloud model (if API key configured)
- Symbolic verification → SymPy directly (no LLM)

## Output Format
Each experiment produces:
1. A git commit with changes
2. An entry in results.tsv (tab-separated):
   commit  conjecture_strength  proof_confidence  verification_passed  status  description

## Workflow
LOOP FOREVER:
1. Read current state from results.tsv and git log
2. Choose a research direction (explore vs exploit trade-off)
3. Formulate hypothesis
4. Attempt proof or counterexample search
5. Verify with SymPy
6. Log result to results.tsv
7. If improved: keep commit; else: git reset
8. Continue

## Safety
- Never claim a proof without SymPy verification
- Always flag conjectures as unproven
- Don't modify system files
- Respect API rate limits
"""


@dataclass
class ResearchProgram:
    """A parsed research program with extracted directives.

    The human writes a Markdown file; this class parses the structured sections
    and makes them available programmatically for the agent loop.
    """

    raw: str = ""
    goal: str = ""
    success_criteria: list = field(default_factory=list)

    # Budget constraints
    time_budget_per_experiment_seconds: int = 300
    total_run_budget_minutes: Optional[int] = None
    max_api_cost_usd: Optional[float] = None
    max_escalations_per_session: int = 5

    # Model routing
    routine_model: str = "local"
    deep_model: str = "cloud"
    prefer_local: bool = True

    # Operations
    allowed_operations: list = field(default_factory=list)
    disallowed_operations: list = field(default_factory=list)

    # Output
    output_dir: str = "~/.jiuzhang/research_autonomous/"
    results_file: str = "results.tsv"

    # Workflow
    explore_exploit_ratio: float = 0.3  # 30% exploration

    @classmethod
    def from_markdown(cls, path: str) -> "ResearchProgram":
        """Parse a program.md file into a ResearchProgram."""
        p = Path(path)
        if not p.exists():
            # Create default
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(DEFAULT_PROGRAM, encoding="utf-8")

        raw = p.read_text(encoding="utf-8")
        program = cls(raw=raw)
        program._parse(raw)
        return program

    @classmethod
    def from_string(cls, content: str) -> "ResearchProgram":
        """Parse a string as a ResearchProgram."""
        program = cls(raw=content)
        program._parse(content)
        return program

    def _parse(self, text: str):
        """Extract structured directives from Markdown sections."""
        sections = self._split_sections(text)

        self.goal = sections.get("Goal", "").strip()

        # Parse success criteria as bullet list
        sc_text = sections.get("Success Criteria", "")
        self.success_criteria = self._extract_bullets(sc_text)

        # Parse constraints
        constraints = sections.get("Constraints", "")
        self._parse_constraints(constraints)

        # Parse allowed/disallowed
        self.allowed_operations = self._extract_bullets(
            sections.get("Allowed Operations", "")
        )
        self.disallowed_operations = self._extract_bullets(
            sections.get("Disallowed Operations", "")
        )

        # Parse model routing
        routing = sections.get("Model Routing", "")
        self._parse_routing(routing)

        # Parse output format
        output_section = sections.get("Output Format", "")
        self._parse_output(output_section)

    def _split_sections(self, text: str) -> dict:
        """Split Markdown into sections by ## headings."""
        sections = {}
        current_heading = ""
        current_content = []

        for line in text.split("\n"):
            if line.startswith("## "):
                if current_heading:
                    sections[current_heading] = "\n".join(current_content)
                current_heading = line[3:].strip()
                current_content = []
            elif current_heading:
                current_content.append(line)

        if current_heading:
            sections[current_heading] = "\n".join(current_content)

        return sections

    def _extract_bullets(self, text: str) -> list:
        """Extract bullet-point items from text."""
        items = []
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("- ") or stripped.startswith("* "):
                items.append(stripped[2:].strip())
            elif stripped and re.match(r"^\d+\.\s", stripped):
                items.append(re.sub(r"^\d+\.\s", "", stripped).strip())
        return items

    def _parse_constraints(self, text: str):
        """Parse time and budget constraints."""
        for line in text.split("\n"):
            line = line.strip().lower()
            # Time per experiment
            m = re.search(r"time\s*budget.*?(\d+)\s*(second|minute|sec|min|s)", line)
            if m:
                val = int(m.group(1))
                unit = m.group(2)
                if unit.startswith("min"):
                    val *= 60
                self.time_budget_per_experiment_seconds = val

            # Total budget
            m = re.search(r"total.*?(\d+)\s*(minute|min|hour|hr|h)", line)
            if m:
                val = int(m.group(1))
                unit = m.group(2)
                if unit.startswith("h"):
                    val *= 60
                self.total_run_budget_minutes = val

            # API cost
            m = re.search(r"\$?(\d+\.?\d*)\s*(usd|dollar)", line)
            if m:
                self.max_api_cost_usd = float(m.group(1))

            # Escalations
            m = re.search(r"escalat.*?(\d+)", line)
            if m:
                self.max_escalations_per_session = int(m.group(1))

    def _parse_routing(self, text: str):
        """Parse model routing preferences."""
        for line in text.split("\n"):
            line = line.strip()
            if "local" in line.lower() and "routine" in line.lower():
                self.routine_model = "local"
            if "cloud" in line.lower() or "api" in line.lower():
                self.deep_model = "cloud"
            if "prefer local" in line.lower():
                self.prefer_local = True

    def _parse_output(self, text: str):
        """Parse output format and result tracking."""
        for line in text.split("\n"):
            line = line.strip()
            if "results.tsv" in line or "results_file" in line:
                self.results_file = "results.tsv"
            m = re.search(r"output.*?directory.*?[:\s]+(\S+)", line, re.I)
            if m:
                self.output_dir = m.group(1)
            m = re.search(r"explore.*?(\d+\.?\d*)", line, re.I)
            if m:
                self.explore_exploit_ratio = float(m.group(1))
