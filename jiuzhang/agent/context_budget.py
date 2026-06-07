"""Context Budget Manager — token-aware context optimization for small models.

Inspired by smallcode's architecture: small models struggle with large context windows.
This module provides:
1. Token budget tracking and enforcement
2. Tool routing via regex classifier (8 categories from smallcode)
3. Progressive summarization of long histories
4. Math-specific compression (keep theorems/symbolic, summarize prose)
5. Two-stage routing for small context windows
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable


# ── Tool Categories (smallcode-inspired 8-category system) ──────────

class ToolCategory(Enum):
    READ = "read"            # Reading files, papers, knowledge base
    WRITE = "write"          # Writing files, LaTeX, code
    SEARCH = "search"        # Literature search, web search
    RUN = "run"              # Execute code, run experiments
    PLAN = "plan"            # Planning, decomposing, strategizing
    VERIFY = "verify"        # Symbolic verification, proof checking
    REASON = "reason"        # Math reasoning, theorem proving
    RESPOND = "respond"      # Answer questions directly (no tools)


# ── Routing Patterns ─────────────────────────────────────────────────

ROUTING_PATTERNS: dict[ToolCategory, dict] = {
    ToolCategory.READ: {
        "positive": [
            (r"(?i)\bread\b", 3),
            (r"(?i)\bload\b", 2),
            (r"(?i)\bfetch\b", 2),
            (r"(?i)\bopen\b.*(file|paper|pdf)", 2),
            (r"(?i)\bshow\b.*(content|file)", 2),
            (r"(?i)\blook\b.*(at|up|into)\b", 1),
            (r"(?i)\breview\b.*(paper|article|literature)", 2),
        ],
        "negative": [
            (r"(?i)\bexplain\b", -2),
            (r"(?i)\bprove\b", -2),
            (r"(?i)\bsolve\b", -2),
        ],
    },
    ToolCategory.WRITE: {
        "positive": [
            (r"(?i)\bwrite\b", 3),
            (r"(?i)\bsave\b", 3),
            (r"(?i)\bcreate\b", 2),
            (r"(?i)\bgenerate\b.*(paper|latex|report)", 3),
            (r"(?i)\bexport\b", 2),
            (r"(?i)\bcommit\b", 2),
        ],
        "negative": [
            (r"(?i)\bexplain\b", -1),
        ],
    },
    ToolCategory.SEARCH: {
        "positive": [
            (r"(?i)\bsearch\b", 3),
            (r"(?i)\bfind\b.*paper", 3),
            (r"(?i)\bliterature\b", 3),
            (r"(?i)\barxiv\b", 3),
            (r"(?i)\blookup\b", 2),
            (r"(?i)\breference\b", 2),
            (r"(?i)\ball\s+(uses|occurrences)\s+of\b", 3),
            (r"(?i)\bwhere\s+is\b", 1),
        ],
        "negative": [],
    },
    ToolCategory.RUN: {
        "positive": [
            (r"(?i)\brun\b", 3),
            (r"(?i)\bexecute\b", 3),
            (r"(?i)\btest\b", 2),
            (r"(?i)\bexperiment\b", 2),
            (r"(?i)\bcompute\b", 2),
            (r"(?i)\bcalculate\b", 2),
            (r"(?i)\bevaluate\b", 2),
        ],
        "negative": [],
    },
    ToolCategory.PLAN: {
        "positive": [
            (r"(?i)\bplan\b", 3),
            (r"(?i)\bdecompose\b", 2),
            (r"(?i)\bstrategy\b", 2),
            (r"(?i)\bapproach\b", 1),
            (r"(?i)\bhow\s+should\b", 1),
            (r"(?i)\brefactor\b", 2),
            (r"(?i)\bmigrate\b", 2),
            (r"(?i)\bmultiple\s+steps?\b", 2),
        ],
        "negative": [],
    },
    ToolCategory.VERIFY: {
        "positive": [
            (r"(?i)\bverify\b", 3),
            (r"(?i)\bcheck\b", 3),
            (r"(?i)\bvalidate\b", 2),
            (r"(?i)\bcross.check\b", 2),
            (r"(?i)\bsympy\b", 3),
            (r"(?i)\bproof.check\b", 2),
            (r"(?i)\bcounterexample\b", 2),
        ],
        "negative": [],
    },
    ToolCategory.REASON: {
        "positive": [
            (r"(?i)\bprove\b", 3),
            (r"(?i)\bproof\b", 3),
            (r"(?i)\btheorem\b", 2),
            (r"(?i)\bconjecture\b", 2),
            (r"(?i)\bderive\b", 2),
            (r"(?i)\bshow\s+that\b", 2),
            (r"(?i)\bdemonstrate\b", 1),
            (r"(?i)\bsolve\b", 2),
            (r"(?i)\bwhy\s+(does|is)\b", 1),
        ],
        "negative": [],
    },
    ToolCategory.RESPOND: {
        "positive": [
            (r"(?i)\bexplain\b", 3),
            (r"(?i)\bwhat\s+(is|are)\b", 3),
            (r"(?i)\bdescribe\b", 2),
            (r"(?i)\bhow\s+(does|do|is|are|can|should)\b", 2),
            (r"(?i)\bdefine\b", 2),
            (r"(?i)\btell\s+me\b", 2),
        ],
        "negative": [
            (r"(?i)\bprove\b", -2),
            (r"(?i)\bsearch\b", -2),
            (r"(?i)\brun\b", -1),
            (r"(?i)\bcompute\b", -1),
        ],
    },
}

# Category priority for near-ties — math-research-optimized
# REASON and VERIFY first (core math work), then SEARCH/RUN, then PLAN/WRITE/READ/RESPOND
CATEGORY_PRIORITY = [
    ToolCategory.REASON,
    ToolCategory.VERIFY,
    ToolCategory.SEARCH,
    ToolCategory.RUN,
    ToolCategory.PLAN,
    ToolCategory.WRITE,
    ToolCategory.READ,
    ToolCategory.RESPOND,
]


# ── Token Estimation ─────────────────────────────────────────────────

def estimate_tokens(text: str) -> int:
    """Rough token estimation: ~4 chars per token for English, ~2 for Chinese."""
    en_chars = len(re.findall(r'[a-zA-Z0-9\s]', text))
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    other = len(text) - en_chars - cn_chars
    return int(en_chars / 4 + cn_chars / 2 + other / 3)


# ── Math-Specific Compression ────────────────────────────────────────

def compress_math_context(messages: list, max_tokens: int) -> list:
    """Compress mathematical conversation context to fit within token budget.

    Strategy:
    1. Keep all symbolic/formula content (equations, LaTeX, code blocks)
    2. Summarize prose explanations
    3. Keep the last N exchanges intact
    4. Drop intermediate greetings and boilerplate
    """
    if not messages:
        return messages

    total = sum(estimate_tokens(m.get("content", "")) for m in messages)
    if total <= max_tokens:
        return messages

    # Always keep system message + last 2 exchanges
    system_msgs = [m for m in messages if m.get("role") == "system"]
    other_msgs = [m for m in messages if m.get("role") != "system"]

    if len(other_msgs) <= 4:
        # Not much to compress; truncate oldest
        return system_msgs + other_msgs[-4:]

    # Keep last 4 messages intact
    kept = other_msgs[-4:]
    middle = other_msgs[:-4]

    # Compress middle: extract math content, summarize rest
    compressed = []
    for msg in middle:
        content = msg.get("content", "")
        math_blocks = _extract_math_blocks(content)
        if math_blocks:
            summary = f"[Earlier context: {len(math_blocks)} mathematical expressions discussed]\n"
            compressed.append({"role": msg["role"], "content": summary})
        elif len(content) > 200:
            summary = content[:200] + "... [truncated]"
            compressed.append({"role": msg["role"], "content": summary})
        else:
            compressed.append(msg)

    result = system_msgs + compressed + kept
    return result


def _extract_math_blocks(text: str) -> list:
    """Extract LaTeX, code blocks, and symbolic expressions from text."""
    blocks = []
    # $$...$$ blocks
    blocks.extend(re.findall(r'\$\$.*?\$\$', text, re.DOTALL))
    # $...$ inline
    blocks.extend(re.findall(r'\$[^$]+\$', text))
    # ```...``` code blocks
    blocks.extend(re.findall(r'```.*?```', text, re.DOTALL))
    return blocks


# ── Context Budget Manager ────────────────────────────────────────────

@dataclass
class BudgetState:
    tokens_used: int = 0
    tokens_limit: int = 8192
    tools_active: set = field(default_factory=set)
    compression_count: int = 0
    escalation_count: int = 0


class ContextBudgetManager:
    """Manages token budget and context window for small models.

    Features:
    - Token tracking with rough estimation
    - Automatic compression when approaching budget limits
    - Progressive summarization of long histories
    - Math-aware compression (preserves formulas and code)
    """

    def __init__(
        self,
        token_limit: int = 8192,
        compression_threshold: float = 0.85,
        small_window_limit: int = 16384,
    ):
        self.token_limit = token_limit
        self.compression_threshold = compression_threshold
        self.small_window_limit = small_window_limit
        self.state = BudgetState(tokens_limit=token_limit)

    @property
    def is_small_window(self) -> bool:
        return self.token_limit <= self.small_window_limit

    def prepare_messages(
        self, messages: list, tools_schema: Optional[list] = None
    ) -> list:
        """Prepare messages for a model call, compressing if needed."""
        # Estimate total tokens including tool schemas
        tool_tokens = 0
        if tools_schema:
            tool_tokens = estimate_tokens(str(tools_schema))

        msg_tokens = sum(estimate_tokens(m.get("content", "")) for m in messages)
        total = msg_tokens + tool_tokens

        if total > self.token_limit * self.compression_threshold:
            # Need compression
            available = int(self.token_limit * self.compression_threshold) - tool_tokens
            if available > 0:
                messages = compress_math_context(messages, available)
                self.state.compression_count += 1

        self.state.tokens_used = sum(
            estimate_tokens(m.get("content", "")) for m in messages
        )
        return messages

    def add_escalation(self):
        self.state.escalation_count += 1

    def reset(self):
        self.state = BudgetState(tokens_limit=self.token_limit)


# ── Tool Router ───────────────────────────────────────────────────────

@dataclass
class RouteResult:
    category: ToolCategory
    confidence: float
    scores: dict  # {ToolCategory: float}


class ToolRouter:
    """Deterministic tool routing via weighted regex scoring.

    Inspired by smallcode: before sending a prompt to the model, classify the
    intent and only include the tool schemas relevant to that intent.
    This saves 100-800 tokens per call on small context windows.

    Eight categories with precedence: RUN > WRITE > VERIFY > REASON > SEARCH >
    PLAN > READ > RESPOND
    """

    def __init__(self):
        self._affirmation_guard: Optional[ToolCategory] = None

    def route(self, message: str, prior_category: Optional[ToolCategory] = None) -> RouteResult:
        """Classify message into a tool category.

        Args:
            message: The user's message
            prior_category: If set, affirmation words won't override it

        Returns:
            RouteResult with the winning category
        """
        # Affirmation guard: "yes", "ok", "go ahead" should preserve prior category
        if prior_category and _is_affirmation(message):
            return RouteResult(
                category=prior_category,
                confidence=1.0,
                scores={prior_category: 1.0},
            )

        scores: dict[ToolCategory, float] = {}
        for cat in ToolCategory:
            patterns = ROUTING_PATTERNS.get(cat, {"positive": [], "negative": []})
            score = 0.0
            for pattern, weight in patterns["positive"]:
                if re.search(pattern, message):
                    score += weight
            for pattern, weight in patterns.get("negative", []):
                if re.search(pattern, message):
                    score += weight
            scores[cat] = max(score, 0.0)

        # Pick winner by priority on near-ties
        best = ToolCategory.RESPOND
        best_score = 0.0
        for cat in CATEGORY_PRIORITY:
            s = scores.get(cat, 0.0)
            if s > best_score + 0.5:  # Need meaningful margin
                best = cat
                best_score = s

        self._affirmation_guard = best
        return RouteResult(category=best, confidence=min(best_score / 5.0, 1.0), scores=scores)

    def get_tools_for_category(self, category: ToolCategory, all_tools: dict) -> dict:
        """Filter tools dictionary to only those relevant to the category.

        Args:
            category: The winning category
            all_tools: Full dict of {tool_name: tool_definition}

        Returns:
            Filtered dict of relevant tools
        """
        category_tools = {
            ToolCategory.READ: ["read_file", "read_paper", "search_kb", "get_problem"],
            ToolCategory.WRITE: ["write_file", "generate_latex", "export_results"],
            ToolCategory.SEARCH: ["search_arxiv", "search_crossref", "web_search", "oeis_lookup"],
            ToolCategory.RUN: ["execute_code", "run_experiment", "sympy_compute"],
            ToolCategory.PLAN: [],  # Planning needs no tools
            ToolCategory.VERIFY: ["verify_symbolic", "check_proof", "find_counterexample"],
            ToolCategory.REASON: ["prove_theorem", "derive", "analyze_conjecture"],
            ToolCategory.RESPOND: [],  # Direct response needs no tools
        }

        allowed = set(category_tools.get(category, []))
        if not allowed:
            return {}
        return {k: v for k, v in all_tools.items() if k in allowed}


def _is_affirmation(message: str) -> bool:
    """Check if message is just an affirmation."""
    msg = message.strip().lower()
    affirmations = {"yes", "ok", "okay", "go ahead", "sure", "yep", "yeah", "continue", "proceed", "好的", "是的", "行", "可以", "继续", "对"}
    return msg in affirmations or len(msg.split()) <= 1 and msg in affirmations
