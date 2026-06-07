"""Skill System — nanobot-style extensible research capabilities.

Skills are Markdown files that define new research capabilities, tool integrations,
and specialized reasoning patterns. They follow a format inspired by nanobot's
SKILL.md pattern.

Directory structure:
    ~/.jiuzhang/skills/
    ├── deep-proof/
    │   └── SKILL.md
    ├── counterexample-hunter/
    │   └── SKILL.md
    ├── conjecture-generator/
    │   └── SKILL.md
    └── literature-review/
        └── SKILL.md

Each SKILL.md has:
- Frontmatter (YAML/TOML) with name, description, tools, triggers
- Body with the skill's system prompt and usage instructions
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable, Any
import os
import re
import yaml
import json


# ── Skill Definition ──────────────────────────────────────────────────

@dataclass
class SkillDefinition:
    """A loaded skill definition from a SKILL.md file."""
    name: str
    description: str = ""
    version: str = "1.0"
    author: str = ""
    tools: list[str] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)  # Keywords that trigger this skill
    category: str = "general"
    prompt: str = ""         # System prompt injected when skill is active
    examples: list[dict] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)  # Dependencies

    source_path: str = ""    # Path to the SKILL.md file

    def matches_trigger(self, text: str) -> bool:
        """Check if this skill should be activated for the given text."""
        if not self.triggers:
            return False
        text_lower = text.lower()
        return any(trigger.lower() in text_lower for trigger in self.triggers)

    def to_system_context(self) -> str:
        """Generate system prompt context for this skill."""
        return f"""[SKILL: {self.name}]
{self.description}

{self.prompt}

Available tools: {', '.join(self.tools) if self.tools else 'none'}
"""


# ── Skill Loader ──────────────────────────────────────────────────────

class SkillLoader:
    """Load and manage skills from .jiuzhang/skills/ directories.

    Searches multiple locations:
    1. Project-local: .jiuzhang/skills/
    2. User-global: ~/.jiuzhang/skills/
    3. Built-in: jiuzhang/builtin_skills/
    """

    SKILL_FILE = "SKILL.md"
    SKILL_CONFIG = "skill.json"  # Alternative to SKILL.md

    def __init__(self):
        self._skills: dict[str, SkillDefinition] = {}
        self._search_paths: list[Path] = []

    def add_search_path(self, path: str | Path):
        self._search_paths.append(Path(path))

    def discover(self) -> list[SkillDefinition]:
        """Discover all skills from search paths."""
        discovered = []

        # Default search paths
        default_paths = [
            Path(".jiuzhang/skills"),
            Path.home() / ".jiuzhang" / "skills",
            Path(__file__).parent / "builtin_skills",
        ]

        for base in default_paths + self._search_paths:
            if not base.exists():
                continue
            for skill_dir in base.iterdir():
                if not skill_dir.is_dir():
                    continue
                skill_file = skill_dir / self.SKILL_FILE
                if skill_file.exists():
                    try:
                        skill = self._load_skill_file(skill_file)
                        if skill:
                            self._skills[skill.name] = skill
                            discovered.append(skill)
                    except Exception as e:
                        print(f"Warning: Failed to load skill from {skill_file}: {e}")

        return discovered

    def _load_skill_file(self, path: Path) -> Optional[SkillDefinition]:
        """Parse a SKILL.md file into a SkillDefinition."""
        content = path.read_text(encoding="utf-8")

        # Extract YAML frontmatter if present
        frontmatter = {}
        body = content

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError:
                    pass
                body = parts[2].strip()

        # Construct the skill
        name = frontmatter.get("name", path.parent.name)
        return SkillDefinition(
            name=name,
            description=frontmatter.get("description", ""),
            version=frontmatter.get("version", "1.0"),
            author=frontmatter.get("author", ""),
            tools=frontmatter.get("tools", []),
            triggers=frontmatter.get("triggers", []),
            category=frontmatter.get("category", "general"),
            prompt=body,
            examples=frontmatter.get("examples", []),
            requires=frontmatter.get("requires", []),
            source_path=str(path),
        )

    def get(self, name: str) -> Optional[SkillDefinition]:
        return self._skills.get(name)

    def get_by_trigger(self, text: str) -> list[SkillDefinition]:
        """Get all skills that match the given text triggers."""
        return [s for s in self._skills.values() if s.matches_trigger(text)]

    def get_by_category(self, category: str) -> list[SkillDefinition]:
        return [s for s in self._skills.values() if s.category == category]

    def list_all(self) -> list[SkillDefinition]:
        return list(self._skills.values())

    def register(self, skill: SkillDefinition):
        self._skills[skill.name] = skill

    def count(self) -> int:
        return len(self._skills)


# ── Built-in Skills ───────────────────────────────────────────────────

BUILTIN_SKILLS = {
    "deep-proof": SkillDefinition(
        name="deep-proof",
        description="Rigorous mathematical proof generation with multiple strategies",
        category="reasoning",
        triggers=["prove", "proof", "demonstrate", "证明", "求证"],
        tools=["sympy_compute", "verify_symbolic", "check_proof"],
        prompt="""# Deep Proof Strategy

When activated, follow this rigorous proof protocol:

1. **Parse the claim**: Identify all quantifiers (∀, ∃), conditions, and the conclusion.
2. **Choose a strategy**: 
   - Direct proof: assume premises, derive conclusion
   - Contradiction: assume negation, derive impossible result
   - Induction: prove base case + inductive step
   - Contrapositive: prove ¬Q → ¬P instead of P → Q
   - Construction: build explicit example/counterexample
3. **State assumptions**: Explicitly list all assumptions used.
4. **Build step by step**: Number each step, justify with a theorem or logical rule.
5. **Verify with SymPy**: Check any algebraic manipulations.
6. **Conclude formally**: End with QED or an explicit conclusion statement.
7. **Search counterexamples**: After proof, search for potential counterexamples to test robustness.

Output format:
```
**Theorem**: [statement]
**Strategy**: [chosen strategy]
**Proof**:
1. [Step 1 — justification]
2. [Step 2 — justification]
...
N. **QED**
**Verification**: [SymPy check results]
```""",
    ),

    "counterexample-hunter": SkillDefinition(
        name="counterexample-hunter",
        description="Systematic counterexample search for mathematical claims",
        category="verification",
        triggers=["counterexample", "disprove", "falsify", "反例", "证伪"],
        tools=["search_counterexample", "brute_force", "sympy_compute"],
        prompt="""# Counterexample Hunter

When a conjecture or theorem seems suspicious, systematically search for counterexamples:

1. **Check edge cases**: n=0, n=1, negative numbers, infinity, degenerate cases
2. **Numeric brute-force**: Test the claim for n=1..1000 numerically
3. **Symbolic counterexample**: Use SymPy to find algebraic counterexamples
4. **Dimensional analysis**: Check if the claim even makes sense dimensionally
5. **Known counterexamples**: Search literature for known counterexamples to similar claims

Report format:
```
**Claim**: [original claim]
**Search Space**: [range/domain searched]
**Counterexamples Found**: N
**Details**:
- n = [value]: [why it fails]
**Verdict**: [CLAIM REFUTED / CLAIM SURVIVES SEARCH / CLAIM PROVEN FALSE]
```""",
    ),

    "conjecture-generator": SkillDefinition(
        name="conjecture-generator",
        description="Generate novel mathematical conjectures from patterns",
        category="exploration",
        triggers=["conjecture", "hypothesize", "pattern", "猜想", "假设"],
        tools=["pattern_search", "oeis_lookup", "numeric_analyze"],
        prompt="""# Conjecture Generator

Generate novel, testable mathematical conjectures:

1. **Observe patterns**: Analyze numeric data for regularities
2. **Formulate conjecture**: State precisely with all quantifiers
3. **Test numerically**: Verify for small cases (n=1..100)
4. **Check OEIS**: See if the sequence/pattern is known
5. **State confidence**: Based on numeric evidence alone
6. **Suggest proof strategy**: How one might prove or disprove it

A good conjecture is:
- **Precise**: Uses proper mathematical notation
- **Falsifiable**: Can be disproven with a single counterexample
- **Non-trivial**: Not obvious from known theorems
- **Interesting**: Has implications or connections to other areas

Format:
```
**Conjecture**: [precise mathematical statement]
**Motivation**: [what pattern/data inspired this]
**Confidence**: [numerical confidence 0-1]
**Tested Range**: [n=1..N]
**Known Connections**: [related theorems, OEIS entries]
**Suggested Approach**: [how to prove or disprove]
```""",
    ),

    "literature-review": SkillDefinition(
        name="literature-review",
        description="Comprehensive literature search and synthesis for math topics",
        category="research",
        triggers=["literature", "review", "survey", "papers", "文献", "综述"],
        tools=["search_arxiv", "search_crossref", "web_search"],
        prompt="""# Literature Review Protocol

Conduct a thorough literature review:

1. **Search**: Query arXiv, CrossRef, MathSciNet for the topic
2. **Filter**: Select papers by relevance, citations, recency
3. **Summarize**: For each key paper, extract: main result, method, significance
4. **Synthesize**: Identify common themes, contradictions, open problems
5. **Gap analysis**: What hasn't been studied yet?
6. **Bibliography**: Generate properly formatted references

Output format:
```
## Literature Review: [Topic]

### Key Papers (N found)
1. **[Title]** ([Year]) — [Authors]
   - **Main Result**: ...
   - **Method**: ...
   - **Significance**: ...

### Synthesis
[Thematic summary]

### Open Problems
[Gaps identified]

### References
[Formatted bibliography]
```""",
    ),

    "multi-engine-verify": SkillDefinition(
        name="multi-engine-verify",
        description="Cross-verify results using multiple symbolic engines",
        category="verification",
        triggers=["verify", "double-check", "cross-verify", "validate", "验证"],
        tools=["sympy_compute", "wolfram_query", "numeric_check"],
        prompt="""# Multi-Engine Verification

Verify mathematical results using multiple independent methods:

1. **SymPy**: Symbolic algebra verification
2. **Numeric sampling**: Test at random points
3. **Dimensional check**: Verify dimensional consistency
4. **Special case check**: Known special cases must hold
5. **Limit check**: Behavior at limits/extremes must be consistent

Only accept results that pass ALL verification methods.

Report format:
```
**Result**: [the result being verified]
**SymPy**: ✓ / ✗ [details]
**Numeric**: ✓ / ✗ [N samples, max error]
**Dimensional**: ✓ / ✗
**Special Cases**: ✓ / ✗ [cases checked]
**Verdict**: VERIFIED / NEEDS REVIEW / REFUTED
```""",
    ),
}


# ── Skill Manager ────────────────────────────────────────────────────

class SkillManager:
    """Central skill management — loading, activation, context injection."""

    def __init__(self):
        self.loader = SkillLoader()
        self._active_skills: list[str] = []  # Currently active skill names
        self._register_builtins()

    def _register_builtins(self):
        """Register all built-in skills."""
        for skill in BUILTIN_SKILLS.values():
            self.loader.register(skill)

    def discover_external(self):
        """Discover external skills from filesystem."""
        return self.loader.discover()

    def activate(self, skill_name: str) -> bool:
        """Activate a skill by name."""
        if self.loader.get(skill_name) and skill_name not in self._active_skills:
            self._active_skills.append(skill_name)
            return True
        return False

    def deactivate(self, skill_name: str):
        if skill_name in self._active_skills:
            self._active_skills.remove(skill_name)

    def activate_by_trigger(self, text: str) -> list[SkillDefinition]:
        """Auto-activate skills matching text triggers."""
        matched = self.loader.get_by_trigger(text)
        for skill in matched:
            if skill.name not in self._active_skills:
                self._active_skills.append(skill.name)
        return matched

    def get_active_context(self) -> str:
        """Build the combined system context for all active skills."""
        if not self._active_skills:
            return ""

        parts = ["[ACTIVE SKILLS]", ""]
        for name in self._active_skills:
            skill = self.loader.get(name)
            if skill:
                parts.append(skill.to_system_context())
        return "\n".join(parts)

    def get_active_tools(self) -> list[str]:
        """Get all tools required by active skills."""
        tools = []
        for name in self._active_skills:
            skill = self.loader.get(name)
            if skill:
                tools.extend(skill.tools)
        return list(set(tools))

    def list_available(self) -> list[dict]:
        """List all available skills with metadata."""
        return [
            {
                "name": s.name,
                "description": s.description,
                "category": s.category,
                "triggers": s.triggers,
                "active": s.name in self._active_skills,
            }
            for s in self.loader.list_all()
        ]

    def reset(self):
        self._active_skills.clear()
