"""Plan Tracker — multi-step research planning with dependency graphs.

Inspired by smallcode: small models drift by turn 4 of a 6-turn task. The plan tracker
mitigates this by injecting a running anchor showing current progress on every turn.

Adapted for mathematical research:
- Plans decompose research into: hypothesize → derive → prove → verify → report
- Dependency graph tracks which steps depend on others
- Topological sort produces batches of independent steps
- Running anchor injected into every agent turn
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Set
import re
import time


class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class PlanStep:
    id: int
    description: str
    status: StepStatus = StepStatus.PENDING
    depends_on: Set[int] = field(default_factory=set)
    result: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0

    @property
    def is_ready(self) -> bool:
        return self.status == StepStatus.PENDING

    @property
    def is_blocked(self) -> bool:
        return self.status == StepStatus.BLOCKED


@dataclass
class ResearchPlan:
    question: str
    steps: list  # List[PlanStep]
    created_at: float = field(default_factory=time.time)
    current_step_idx: int = 0

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def completed_steps(self) -> int:
        return sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)

    @property
    def current_step(self) -> Optional[PlanStep]:
        if 0 <= self.current_step_idx < len(self.steps):
            return self.steps[self.current_step_idx]
        return None

    def advance(self):
        """Mark current step complete and move to next ready step."""
        if self.current_step:
            self.current_step.status = StepStatus.COMPLETED
            self.current_step.completed_at = time.time()

        # Find next ready step
        for i in range(self.current_step_idx + 1, len(self.steps)):
            step = self.steps[i]
            if step.status == StepStatus.PENDING and self._dependencies_met(step):
                step.status = StepStatus.IN_PROGRESS
                step.started_at = time.time()
                self.current_step_idx = i
                return

        self.current_step_idx = len(self.steps)  # All done

    def _dependencies_met(self, step: PlanStep) -> bool:
        for dep_id in step.depends_on:
            dep_step = self._find_step(dep_id)
            if dep_step is None or dep_step.status != StepStatus.COMPLETED:
                return False
        return True

    def _find_step(self, step_id: int) -> Optional[PlanStep]:
        for s in self.steps:
            if s.id == step_id:
                return s
        return None

    def add_step(
        self, description: str, depends_on: Optional[Set[int]] = None
    ) -> PlanStep:
        """Dynamically add a step mid-plan."""
        step_id = len(self.steps) + 1
        step = PlanStep(id=step_id, description=description, depends_on=depends_on or set())
        self.steps.append(step)
        return step

    def mark_failed(self, step_idx: int, reason: str = ""):
        if 0 <= step_idx < len(self.steps):
            self.steps[step_idx].status = StepStatus.FAILED
            self.steps[step_idx].result = reason

    def get_anchor_text(self) -> str:
        """Generate the running anchor injected into every turn.

        Follows smallcode format:
        ```
        ACTIVE PLAN (step X of Y):
        ✓ 1. Completed step description
        → 2. Current step description
          3. Future step description
          4. Future step description
        ```
        """
        lines = [
            f"ACTIVE RESEARCH PLAN (step {self.current_step_idx + 1} of {self.total_steps}):",
        ]
        for i, step in enumerate(self.steps):
            prefix = "  "
            if step.status == StepStatus.COMPLETED:
                prefix = "✓ "
            elif step.status == StepStatus.IN_PROGRESS:
                prefix = "→ "
            elif step.status == StepStatus.FAILED:
                prefix = "✗ "
            elif step.status == StepStatus.BLOCKED:
                prefix = "⊘ "
            lines.append(f"{prefix}{step.id}. {step.description}")

        return "\n".join(lines)

    def get_batch(self, step_ids: list) -> list:
        """Get a batch of steps that can run in parallel (all deps met)."""
        return [s for s in self.steps if s.id in step_ids and s.is_ready and self._dependencies_met(s)]


class PlanTracker:
    """Tracks and advances multi-step research plans.

    Features:
    - Parse plans from model output (LLM-based + regex fallback)
    - Dependency graph and topological sorting
    - Running anchor injection
    - Dynamic step addition mid-plan
    - Batch execution of independent steps
    """

    def __init__(self):
        self._active_plan: Optional[ResearchPlan] = None
        self._completed_plans: list = []

    @property
    def active_plan(self) -> Optional[ResearchPlan]:
        return self._active_plan

    @property
    def has_plan(self) -> bool:
        return self._active_plan is not None and self._active_plan.current_step is not None

    def create_plan(self, question: str, steps_descriptions: list, dependencies: Optional[dict] = None) -> ResearchPlan:
        """Create a new research plan."""
        steps = []
        for i, desc in enumerate(steps_descriptions):
            deps = set()
            if dependencies and (i + 1) in dependencies:
                deps = set(dependencies[i + 1])
            step = PlanStep(id=i + 1, description=desc, depends_on=deps)
            steps.append(step)

        plan = ResearchPlan(question=question, steps=steps)
        if steps:
            plan.steps[0].status = StepStatus.IN_PROGRESS
            plan.steps[0].started_at = time.time()
        self._active_plan = plan
        return plan

    def parse_plan_from_text(self, question: str, text: str) -> ResearchPlan:
        """Parse a plan from model output with regex fallback.

        Handles both LLM-generated numbered plans and prose-embedded plans.
        """
        steps = []

        # Try numbered list pattern: "1. Do X\n2. Do Y"
        numbered = re.findall(r'(?:^|\n)\s*(\d+)[\.\)]\s*(.+?)(?=\n\s*\d+[\.\)]|\n\n|\Z)', text, re.DOTALL)
        if numbered:
            for num, desc in numbered:
                desc = desc.strip().rstrip(',;')
                if desc and len(desc) > 3:
                    steps.append(desc)
        else:
            # Fallback: try step marker pattern
            step_markers = re.findall(
                r'(?:Step\s+\d+|Phase\s+\d+|Stage\s+\d+)[:\-]\s*(.+?)(?=\n|$)',
                text, re.IGNORECASE
            )
            if step_markers:
                steps = [s.strip() for s in step_markers if s.strip()]
            else:
                # Last fallback: split on double newlines, take non-empty lines
                paras = [p.strip() for p in text.split('\n\n') if p.strip()]
                if len(paras) >= 2:
                    steps = paras[:5]  # Take first 5 paragraphs as steps

        if not steps:
            # Auto-generate default research plan
            steps = [
                "Analyze the research question and review known results",
                "Formulate hypotheses and conjectures",
                "Attempt mathematical proofs or derivations",
                "Verify results with symbolic computation (SymPy)",
                "Search for counterexamples or edge cases",
                "Compile findings into a research report",
            ]

        return self.create_plan(question, steps)

    def advance(self) -> bool:
        """Mark current step complete, advance to next."""
        if not self._active_plan:
            return False
        self._active_plan.advance()
        if self._active_plan.current_step is None:
            self._completed_plans.append(self._active_plan)
            self._active_plan = None
            return False
        return True

    def add_step(self, description: str, depends_on: Optional[Set[int]] = None) -> Optional[PlanStep]:
        """Dynamically add a step to the current plan."""
        if not self._active_plan:
            return None
        return self._active_plan.add_step(description, depends_on)

    def mark_current_failed(self, reason: str = ""):
        if self._active_plan and self._active_plan.current_step:
            self._active_plan.mark_failed(self._active_plan.current_step_idx, reason)

    def get_anchor(self) -> str:
        """Get the anchor text for injection into the current turn."""
        if not self._active_plan:
            return ""
        return self._active_plan.get_anchor_text()

    def dependency_graph_text(self) -> str:
        """Generate a text description of the dependency graph."""
        if not self._active_plan:
            return "No active plan."
        lines = ["Dependency Graph:"]
        for step in self._active_plan.steps:
            if step.depends_on:
                deps = ", ".join(str(d) for d in step.depends_on)
                lines.append(f"  Step {step.id} depends on: {deps}")
            else:
                lines.append(f"  Step {step.id}: no dependencies (can run immediately)")
        return "\n".join(lines)
