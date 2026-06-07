"""Thinking Budget Controller & Auto-Compaction for small models.

Critical for local/small models (1B-14B): controls how much "thinking" the model
does before responding, and automatically compacts context when approaching limits.

Inspired by smallcode's thinking_budget.js and nanobot's AutoCompact.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import re
import time
import math


# ── Thinking Budget ──────────────────────────────────────────────────

class ThinkingMode(Enum):
    OFF = "off"           # No explicit thinking (fast, cheap)
    BRIEF = "brief"       # Short thinking: 64-256 tokens
    STANDARD = "standard" # Normal thinking: 256-1024 tokens
    DEEP = "deep"         # Extended thinking: 1024-4096 tokens
    AUTO = "auto"         # Adaptive based on problem complexity


@dataclass
class ThinkingBudget:
    """Controls how many tokens the model spends on chain-of-thought."""
    min_tokens: int = 128
    max_tokens: int = 4096
    current_mode: ThinkingMode = ThinkingMode.AUTO

    # Budget tracking
    total_allocated: int = 0
    total_spent: int = 0
    sessions_tracked: int = 0

    def allocate(self, problem_complexity: float, context_tokens: int) -> int:
        """Allocate thinking budget based on problem complexity and context.

        Args:
            problem_complexity: 0.0 (simple arithmetic) to 1.0 (frontier research)
            context_tokens: Number of tokens already in context

        Returns:
            Recommended thinking token budget
        """
        if self.current_mode == ThinkingMode.OFF:
            return 0
        elif self.current_mode == ThinkingMode.BRIEF:
            budget = 128
        elif self.current_mode == ThinkingMode.STANDARD:
            budget = 512
        elif self.current_mode == ThinkingMode.DEEP:
            budget = 2048
        else:  # AUTO
            # Adaptive budget based on problem complexity
            base = 256
            complexity_bonus = int(problem_complexity * 2048)
            budget = base + complexity_bonus

            # Reduce budget if context is already large (model has low effective context)
            context_penalty = max(0, (context_tokens - 4096) / 32768)
            budget = int(budget * (1.0 - context_penalty * 0.5))

        budget = max(self.min_tokens, min(budget, self.max_tokens))
        self.total_allocated += budget
        self.sessions_tracked += 1
        return budget

    def spend(self, tokens: int):
        self.total_spent += tokens

    def estimate_complexity(self, question: str) -> float:
        """Estimate problem complexity from the question text.

        Returns 0.0 (trivial) to 1.0 (frontier research).
        """
        score = 0.0
        q = question.lower()

        # Length-based
        if len(question) > 200:
            score += 0.15
        elif len(question) > 100:
            score += 0.1

        # Keyword-based complexity signals
        frontier_keywords = [
            "riemann", "zeta", "goldbach", "collatz", "twin prime",
            "p vs np", "riemann hypothesis", "birch", "swinnerton",
            "hodge", "navier-stokes", "yang-mills", "poincaré",
            "category theory", "homological", "cohomology", "scheme",
            "algebraic geometry", "topos", "galois", "ergodic",
        ]
        advanced_keywords = [
            "topology", "abstract algebra", "real analysis", "fourier",
            "manifold", "lie algebra", "eigenvalue", "tensor",
            "differential equation", "functional analysis", "measure theory",
        ]
        intermediate_keywords = [
            "calculus", "linear algebra", "probability", "statistics",
            "derivative", "integral", "matrix", "vector",
        ]

        for kw in frontier_keywords:
            if kw in q:
                score += 0.25
                break
        for kw in advanced_keywords:
            if kw in q:
                score += 0.15
                break
        for kw in intermediate_keywords:
            if kw in q:
                score += 0.08
                break

        # Question type signal
        if any(p in q for p in ["prove", "证明", "proof", "conjecture"]):
            score += 0.15
        if any(p in q for p in ["derive", "推导", "solve", "求解"]):
            score += 0.1

        return min(score, 1.0)


# ── Auto-Compaction ──────────────────────────────────────────────────

class CompactionLevel(Enum):
    NONE = 0       # No compaction needed
    LIGHT = 1      # Summarize oldest messages
    MODERATE = 2   # Compress middle, keep recent intact
    AGGRESSIVE = 3 # Heavy compression, keep only essential
    EMERGENCY = 4  # Radical truncation to stay under limit


@dataclass
class CompactionResult:
    level: CompactionLevel
    original_tokens: int
    compacted_tokens: int
    savings_percent: float
    messages_before: int
    messages_after: int
    techniques_used: list[str]


class AutoCompactor:
    """Automatic context compaction when approaching token limits.

    Key features:
    - Progressive: uses lightest compaction first, escalates as needed
    - Math-aware: preserves LaTeX, equations, SymPy expressions
    - Priority-based: system messages > recent turns > key insights > rest
    - Non-destructive: always keeps enough context for coherent continuation

    Usage:
        compactor = AutoCompactor(target_tokens=4096)
        compacted = compactor.compact(messages)
    """

    def __init__(
        self,
        target_tokens: int = 4096,
        light_threshold: float = 0.7,
        moderate_threshold: float = 0.85,
        aggressive_threshold: float = 0.95,
        emergency_threshold: float = 1.05,
    ):
        self.target_tokens = target_tokens
        self.light_threshold = light_threshold
        self.moderate_threshold = moderate_threshold
        self.aggressive_threshold = aggressive_threshold
        self.emergency_threshold = emergency_threshold

        # Persist important info across compactions
        self._persistent_insights: list[str] = []
        self._key_theorems: list[str] = []
        self._total_compactions = 0

    def compact(self, messages: list, current_tokens: int | None = None) -> tuple[list, CompactionResult]:
        """Compact messages to fit within target_tokens.

        Args:
            messages: List of {"role": ..., "content": ...} dicts
            current_tokens: Pre-calculated token count (estimated if None)

        Returns:
            (compacted_messages, CompactionResult)
        """
        if not messages:
            return messages, CompactionResult(
                level=CompactionLevel.NONE, original_tokens=0, compacted_tokens=0,
                savings_percent=0.0, messages_before=0, messages_after=0,
                techniques_used=[],
            )

        total = current_tokens or self._estimate_tokens_batch(messages)
        techniques = []

        # Determine compaction level
        ratio = total / self.target_tokens if self.target_tokens > 0 else 0
        if ratio <= self.light_threshold:
            return messages, self._result(CompactionLevel.NONE, total, total, len(messages), len(messages), techniques)
        elif ratio <= self.moderate_threshold:
            level = CompactionLevel.LIGHT
        elif ratio <= self.aggressive_threshold:
            level = CompactionLevel.MODERATE
        elif ratio <= self.emergency_threshold:
            level = CompactionLevel.AGGRESSIVE
        else:
            level = CompactionLevel.EMERGENCY

        self._total_compactions += 1
        result = self._apply_compaction(messages, level, total, techniques)
        return result

    def _apply_compaction(
        self, messages: list, level: CompactionLevel, original_tokens: int, techniques: list
    ) -> tuple[list, CompactionResult]:
        """Apply the specified compaction level."""
        n_before = len(messages)

        if level == CompactionLevel.LIGHT:
            compacted = self._light_compaction(messages, techniques)
        elif level == CompactionLevel.MODERATE:
            compacted = self._moderate_compaction(messages, techniques)
        elif level == CompactionLevel.AGGRESSIVE:
            compacted = self._aggressive_compaction(messages, techniques)
        else:  # EMERGENCY
            compacted = self._emergency_compaction(messages, techniques)

        compacted_tokens = self._estimate_tokens_batch(compacted)
        return compacted, self._result(
            level, original_tokens, compacted_tokens, n_before, len(compacted), techniques,
        )

    def _light_compaction(self, messages: list, techniques: list) -> list:
        """Light compaction: truncate long individual messages."""
        techniques.append("truncate_long_messages")
        result = []
        for msg in messages:
            content = msg.get("content", "")
            if len(content) > 2000:
                # Keep first and last 500 chars, summarize middle
                content = content[:500] + "\n... [truncated middle section] ...\n" + content[-500:]
            result.append({**msg, "content": content})
        return result

    def _moderate_compaction(self, messages: list, techniques: list) -> list:
        """Moderate compaction: summarize older messages, keep recent intact."""
        techniques.append("summarize_older_exchanges")
        system_msgs = [m for m in messages if m["role"] == "system"]
        other = [m for m in messages if m["role"] != "system"]

        if len(other) <= 6:
            return messages  # Not enough to compact

        # Keep last 4 exchanges intact
        kept = other[-4:]
        middle = other[:-4]

        # Summarize the middle
        compressed = []
        for msg in middle:
            content = msg.get("content", "")
            math_blocks = self._extract_math(content)
            if math_blocks:
                summary = f"[Earlier: {len(math_blocks)} mathematical expressions discussed — see key formulas above]"
                compressed.append({"role": msg["role"], "content": summary + "\n" + "\n".join(math_blocks[:3])})
            elif len(content) > 300:
                compressed.append({"role": msg["role"], "content": content[:150] + " ... [summarized]"})
            else:
                compressed.append(msg)

        return system_msgs + compressed + kept

    def _aggressive_compaction(self, messages: list, techniques: list) -> list:
        """Aggressive compaction: keep only system, key insights, and last 2 turns."""
        techniques.append("keep_essentials_only")
        system_msgs = [m for m in messages if m["role"] == "system"]
        other = [m for m in messages if m["role"] != "system"]

        # Keep last 2 exchanges
        kept = other[-2:] if len(other) >= 2 else other

        # Build summary of everything before
        if len(other) > 2:
            summary_parts = []
            if self._persistent_insights:
                summary_parts.append("Key insights from earlier: " + "; ".join(self._persistent_insights[-5:]))
            if self._key_theorems:
                summary_parts.append("Key theorems discussed: " + "; ".join(self._key_theorems[-5:]))
            if summary_parts:
                kept.insert(0, {"role": "system", "content": "\n".join(summary_parts)})

        # Extract math from discarded messages
        for msg in other[:-2]:
            math = self._extract_math(msg.get("content", ""))
            if math:
                self._key_theorems.extend(math[:2])

        return system_msgs + kept

    def _emergency_compaction(self, messages: list, techniques: list) -> list:
        """Emergency: radical truncation, keep only absolute essentials."""
        techniques.append("emergency_truncation")
        system_msgs = [m for m in messages if m["role"] == "system"]
        essential = system_msgs[-1:] if system_msgs else []

        # Keep last user + assistant pair
        pairs = []
        for m in messages:
            if m["role"] in ("user", "assistant"):
                pairs.append(m)
        essential.extend(pairs[-2:])

        # Ultra-compact summary
        if self._persistent_insights:
            essential.insert(0, {"role": "system", "content": "Session summary: " + " | ".join(self._persistent_insights[-3:])})

        return essential

    def record_insight(self, insight: str):
        """Record an important insight for future compactions."""
        if insight not in self._persistent_insights:
            self._persistent_insights.append(insight)
        if len(self._persistent_insights) > 20:
            self._persistent_insights = self._persistent_insights[-20:]

    def record_theorem(self, theorem: str):
        """Record a key theorem for future compactions."""
        if theorem not in self._key_theorems:
            self._key_theorems.append(theorem)
        if len(self._key_theorems) > 20:
            self._key_theorems = self._key_theorems[-20:]

    @staticmethod
    def _extract_math(text: str) -> list[str]:
        """Extract mathematical expressions from text."""
        blocks = []
        blocks.extend(re.findall(r'\$\$.*?\$\$', text, re.DOTALL))
        blocks.extend(re.findall(r'\$[^$]+\$', text))
        blocks.extend(re.findall(r'```.*?```', text, re.DOTALL)[:2])
        return [b.strip()[:200] for b in blocks[:5]]

    @staticmethod
    def _estimate_tokens_batch(messages: list) -> int:
        """Estimate total tokens in a batch of messages."""
        total = 0
        for msg in messages:
            text = msg.get("content", "")
            total += max(len(text) // 4, 1)
        return total

    @staticmethod
    def _result(
        level: CompactionLevel, orig: int, comp: int,
        n_before: int, n_after: int, techniques: list,
    ) -> CompactionResult:
        savings = ((orig - comp) / orig * 100) if orig > 0 else 0.0
        return CompactionResult(
            level=level, original_tokens=orig, compacted_tokens=comp,
            savings_percent=savings, messages_before=n_before,
            messages_after=n_after, techniques_used=techniques,
        )


# ── Integrated Context Manager ───────────────────────────────────────

class IntegratedContextManager:
    """Combines thinking budget, token counting, and auto-compaction into one interface.

    This is the primary entry point for context management in the agent loop.
    """

    def __init__(
        self,
        token_limit: int = 8192,
        thinking_mode: ThinkingMode = ThinkingMode.AUTO,
    ):
        self.thinking = ThinkingBudget(current_mode=thinking_mode)
        self.compactor = AutoCompactor(target_tokens=int(token_limit * 0.85))
        self.token_limit = token_limit
        self._total_tokens_used = 0

    def prepare_call(
        self, messages: list, question: str,
    ) -> tuple[list, int]:
        """Prepare a model call with optimal context and thinking budget.

        Returns:
            (prepared_messages, thinking_budget_tokens)
        """
        # 1. Estimate current token usage
        current = self.compactor._estimate_tokens_batch(messages)

        # 2. Compact if needed
        if current > self.token_limit * 0.7:
            messages, result = self.compactor.compact(messages, current)
            current = result.compacted_tokens

        # 3. Allocate thinking budget
        complexity = self.thinking.estimate_complexity(question)
        thinking_budget = self.thinking.allocate(complexity, current)

        # 4. Track
        self._total_tokens_used += current

        return messages, thinking_budget

    def record_result(self, tokens_spent: int, insight: str = ""):
        self.thinking.spend(tokens_spent)
        self._total_tokens_used += tokens_spent
        if insight:
            self.compactor.record_insight(insight)

    @property
    def total_tokens_used(self) -> int:
        return self._total_tokens_used

    def get_stats(self) -> dict:
        return {
            "total_tokens": self._total_tokens_used,
            "thinking_allocated": self.thinking.total_allocated,
            "thinking_spent": self.thinking.total_spent,
            "compactions": self.compactor._total_compactions,
            "persistent_insights": len(self.compactor._persistent_insights),
        }
