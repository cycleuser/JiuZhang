"""Monte Carlo Tree Search for Mathematical Research Exploration.

Adapted from AlphaGo/AlphaZero-style MCTS to mathematical research:
- Each node is a research state (conjecture, partial proof, verification result)
- Actions are: prove, test, search-counterexample, generalize, specialize
- UCB-based node selection balancing exploration and exploitation
- Back-propagation of verification results to guide future search

This turns research from linear hypothesis→proof into a tree search over
the space of possible mathematical discoveries.
"""

import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable


class ActionType(Enum):
    PROVE = "prove"                           # Attempt proof
    TEST_NUMERIC = "test_numeric"             # Test numerically
    SEARCH_COUNTEREXAMPLE = "search_ce"       # Search for counterexample
    GENERALIZE = "generalize"                 # Generalize to broader claim
    SPECIALIZE = "specialize"                 # Restrict to special case
    COMBINE = "combine"                       # Combine with another conjecture
    LITERATURE_SEARCH = "literature"          # Search for related results
    SYMBOLIC_VERIFY = "symbolic_verify"       # Verify with SymPy


@dataclass
class ResearchNode:
    """A node in the MCTS tree representing a research state."""
    id: str
    description: str
    conjecture: str = ""
    parent: Optional["ResearchNode"] = None
    children: list = field(default_factory=list)
    visits: int = 0
    total_value: float = 0.0
    is_proven: bool = False
    is_disproven: bool = False
    verification_confidence: float = 0.0
    evidence_count: int = 0
    creation_time: float = field(default_factory=time.time)

    @property
    def value(self) -> float:
        if self.visits == 0:
            return 0.0
        return self.total_value / self.visits

    @property
    def ucb_score(self, c: float = 1.414) -> float:
        """Upper Confidence Bound for tree search."""
        if self.visits == 0:
            return float('inf')  # Explore unvisited nodes first

        parent_visits = self.parent.visits if self.parent else self.visits
        exploitation = self.value
        exploration = c * math.sqrt(math.log(parent_visits) / self.visits)
        return exploitation + exploration

    @property
    def is_terminal(self) -> bool:
        """A node is terminal if proven, disproven, or max depth reached."""
        return self.is_proven or self.is_disproven

    @property
    def is_expandable(self) -> bool:
        return not self.is_terminal and len(self.children) < 6  # Limit branching


@dataclass
class MCTSResult:
    best_node: Optional[ResearchNode]
    best_path: list  # Path from root to best node
    total_nodes: int
    total_simulations: int
    proven_count: int
    disproven_count: int
    search_time: float


class ResearchTreeSearch:
    """MCTS-based exploration of mathematical research directions.

    Usage:
        tree = ResearchTreeSearch(verifier_fn, prover_fn)
        result = tree.search("Is every even number > 2 the sum of two primes?")
        print(tree.get_path_report(result))
    """

    def __init__(
        self,
        verifier_fn: Callable,
        prover_fn: Optional[Callable] = None,
        exploration_constant: float = 1.414,
        max_simulations: int = 100,
        max_depth: int = 5,
    ):
        self.verifier = verifier_fn
        self.prover = prover_fn or (lambda x: {"confidence": 0.5, "result": "unknown"})
        self.c = exploration_constant
        self.max_simulations = max_simulations
        self.max_depth = max_depth
        self._node_counter = 0

    def _new_id(self) -> str:
        self._node_counter += 1
        return f"n{self._node_counter}"

    def _depth(self, node: ResearchNode) -> int:
        d = 0
        current = node
        while current.parent:
            d += 1
            current = current.parent
        return d

    def search(self, question: str, initial_hypotheses: Optional[list] = None) -> MCTSResult:
        """Run MCTS to explore research directions for a question.

        Args:
            question: The research question
            initial_hypotheses: Optional list of initial conjectures to start from

        Returns:
            MCTSResult with best path and statistics
        """
        start_time = time.perf_counter()

        # Create root node
        root = ResearchNode(
            id=self._new_id(),
            description=question,
            conjecture=question,
        )

        # Expand root with initial hypotheses
        hypotheses = initial_hypotheses or self._generate_initial_hypotheses(question)
        for h in hypotheses:
            child = ResearchNode(
                id=self._new_id(),
                description=h,
                conjecture=h,
                parent=root,
            )
            root.children.append(child)

        # MCTS loop
        for sim in range(self.max_simulations):
            # Selection
            node = self._select(root)

            # Expansion
            if node.is_expandable and not node.is_terminal:
                node = self._expand(node)

            # Simulation
            value = self._simulate(node)

            # Back-propagation
            self._backpropagate(node, value)

        # Find best path
        best = self._find_best(root)
        path = self._get_path(best)

        elapsed = time.perf_counter() - start_time

        return MCTSResult(
            best_node=best,
            best_path=path,
            total_nodes=self._count_nodes(root),
            total_simulations=self.max_simulations,
            proven_count=self._count_proven(root),
            disproven_count=self._count_disproven(root),
            search_time=elapsed,
        )

    def _select(self, node: ResearchNode) -> ResearchNode:
        """Select a node using UCB."""
        current = node
        while current.children:
            # Pick child with highest UCB
            best_child = max(current.children, key=lambda c: c.ucb_score)
            if best_child.is_terminal:
                # If best child is terminal, try another approach
                non_terminal = [c for c in current.children if not c.is_terminal]
                if non_terminal:
                    current = random.choice(non_terminal)
                else:
                    break
            else:
                current = best_child
        return current

    def _expand(self, node: ResearchNode) -> ResearchNode:
        """Expand a node by adding a child action."""
        available_actions = self._get_available_actions(node)
        if not available_actions:
            return node

        # Pick a random action (UCB will guide future selections)
        action = random.choice(available_actions)
        child_description = self._apply_action(node, action)

        child = ResearchNode(
            id=self._new_id(),
            description=child_description,
            conjecture=node.conjecture,
            parent=node,
        )
        node.children.append(child)

        # If it's a verification action, run immediately
        if action == ActionType.SYMBOLIC_VERIFY:
            result = self.verifier(node.conjecture)
            child.verification_confidence = result.get("confidence", 0.5)
            child.evidence_count = result.get("evidence_count", 0)
            if result.get("passed"):
                child.is_proven = True
                child.total_value = 1.0
                child.visits = 1
            elif result.get("confidence", 0) < 0.2:
                child.is_disproven = True
                child.total_value = 0.0
                child.visits = 1

        return child

    def _simulate(self, node: ResearchNode) -> float:
        """Simulate (rollout) from this node to a terminal state.

        Uses a lightweight heuristic rather than full simulation:
        - Verification confidence contributes 0-1
        - Evidence count gives small bonus
        - Proven = 1.0, disproven = 0.0
        """
        if node.is_proven:
            return 1.0
        if node.is_disproven:
            return 0.0

        # Rollout policy: try verify + estimate
        try:
            result = self.verifier(node.conjecture)
            conf = result.get("confidence", 0.5)
            node.verification_confidence = conf
            node.evidence_count = result.get("evidence_count", 0)

            if result.get("passed"):
                node.is_proven = True
                return 1.0

            # Penalize depth (deeper conjectures are often weaker)
            depth_penalty = self._depth(node) * 0.05
            return max(0.0, conf - depth_penalty)
        except Exception:
            return 0.5  # Neutral on failure

    def _backpropagate(self, node: ResearchNode, value: float):
        """Back-propagate reward up the tree."""
        current = node
        while current:
            current.visits += 1
            current.total_value += value
            current = current.parent

    def _find_best(self, root: ResearchNode) -> ResearchNode:
        """Find the best leaf node (highest value, not just most visited)."""
        best = root
        best_value = -float('inf')

        def dfs(node: ResearchNode):
            nonlocal best, best_value
            if node.is_proven:
                if node.value > best_value:
                    best_value = node.value
                    best = node
            elif node.visits > 0 and node.value > best_value:
                best_value = node.value
                best = node
            for child in node.children:
                dfs(child)

        dfs(root)
        return best

    def _get_path(self, node: ResearchNode) -> list:
        """Get path from root to node."""
        path = []
        current = node
        while current:
            path.append({
                "id": current.id,
                "description": current.description[:150],
                "value": current.value,
                "visits": current.visits,
                "proven": current.is_proven,
            })
            current = current.parent
        return list(reversed(path))

    def _get_available_actions(self, node: ResearchNode) -> list:
        """Get available actions for a node."""
        actions = []
        depth = self._depth(node)

        if depth < self.max_depth:
            actions.append(ActionType.PROVE)
            actions.append(ActionType.TEST_NUMERIC)
            actions.append(ActionType.SYMBOLIC_VERIFY)
            actions.append(ActionType.SEARCH_COUNTEREXAMPLE)

            if depth > 0:
                actions.append(ActionType.GENERALIZE)
                actions.append(ActionType.SPECIALIZE)

        return actions

    def _apply_action(self, node: ResearchNode, action: ActionType) -> str:
        """Generate a description for the action applied to the node."""
        base = node.conjecture[:200]

        if action == ActionType.PROVE:
            return f"Attempt proof of: {base[:100]}"
        elif action == ActionType.TEST_NUMERIC:
            return f"Test numerically: {base[:100]} for small values"
        elif action == ActionType.SYMBOLIC_VERIFY:
            return f"Verify with SymPy: {base[:100]}"
        elif action == ActionType.SEARCH_COUNTEREXAMPLE:
            return f"Search counterexample for: {base[:100]}"
        elif action == ActionType.GENERALIZE:
            return f"Generalize: {base[:100]} to broader class"
        elif action == ActionType.SPECIALIZE:
            return f"Specialize: {base[:100]} to specific case"
        elif action == ActionType.COMBINE:
            return f"Combine: {base[:100]} with another result"
        elif action == ActionType.LITERATURE_SEARCH:
            return f"Search literature: {base[:100]}"
        return f"Explore: {base[:100]}"

    def _generate_initial_hypotheses(self, question: str) -> list:
        """Generate initial branching hypotheses."""
        hypotheses = [
            f"Hypothesis 1: {question} holds for all known cases",
            f"Hypothesis 2: {question} has counterexamples beyond some bound",
            f"Hypothesis 3: {question} is equivalent to a known theorem",
            f"Hypothesis 4: {question} can be proven by induction",
        ]
        return hypotheses

    def _count_nodes(self, node: ResearchNode) -> int:
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count

    def _count_proven(self, node: ResearchNode) -> int:
        count = 1 if node.is_proven else 0
        for child in node.children:
            count += self._count_proven(child)
        return count

    def _count_disproven(self, node: ResearchNode) -> int:
        count = 1 if node.is_disproven else 0
        for child in node.children:
            count += self._count_disproven(child)
        return count

    def get_path_report(self, result: MCTSResult) -> str:
        """Generate a human-readable report of the search path."""
        lines = [
            "🌳 MCTS Research Tree Search Report",
            "=" * 50,
            f"Nodes explored: {result.total_nodes}",
            f"Simulations: {result.total_simulations}",
            f"Proven: {result.proven_count} | Disproven: {result.disproven_count}",
            f"Search time: {result.search_time:.1f}s",
            "",
            "Best Path:",
            "-" * 40,
        ]

        for step in result.best_path:
            status = "✅" if step["proven"] else "🔍"
            lines.append(
                f"{status} [{step['value']:.2f}, {step['visits']} visits] {step['description'][:120]}"
            )

        return "\n".join(lines)
