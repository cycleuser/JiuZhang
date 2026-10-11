"""Unified Research Tool Registry — auto-discovering, budget-aware tool management.

Inspired by nanobot's tool auto-discovery via pkgutil + entry-point plugins,
and smallcode's tool routing with token cost awareness.

All tools auto-register via a decorator. Each tool declares:
- capabilities, token cost, reliability tier, and category.
- The router dynamically selects a subset based on context budget.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, Any
import time
import functools


class ToolTier(Enum):
    ESSENTIAL = "essential"      # Always available (verify, compute)
    STANDARD = "standard"        # Available in most contexts
    EXTENDED = "extended"        # Available with sufficient budget
    EXPERIMENTAL = "experimental"  # Opt-in only


class ToolCategory(Enum):
    SYMBOLIC = "symbolic"            # SymPy, SageMath
    VERIFICATION = "verification"    # Proof checking, cross-validation
    SEARCH = "search"                # arXiv, web, OEIS
    EXECUTION = "execution"          # Code sandbox
    KNOWLEDGE = "knowledge"          # Knowledge base, papers
    OUTPUT = "output"                # LaTeX, reports, visualization
    SYSTEM = "system"                # File I/O, git, config
    NETWORK = "network"              # API calls, downloads


@dataclass
class ToolDefinition:
    """Metadata for a research tool."""
    name: str
    description: str
    category: ToolCategory
    tier: ToolTier = ToolTier.STANDARD
    token_cost_estimate: int = 0  # Approximate tokens consumed per call
    reliability: float = 0.9     # 0-1, expected success rate
    parameters: dict = field(default_factory=dict)
    fn: Optional[Callable] = None

    def to_openai_schema(self) -> dict:
        """Convert to OpenAI function-calling schema."""
        properties = {}
        for param_name, param_info in self.parameters.items():
            properties[param_name] = {
                "type": param_info.get("type", "string"),
                "description": param_info.get("description", ""),
            }

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": [
                        k for k, v in self.parameters.items()
                        if v.get("required", False)
                    ],
                },
            },
        }


class ToolRegistry:
    """Auto-discovering registry for all math research tools.

    Tools are decorated with @ToolRegistry.register() and automatically
    added to the registry. This enables dynamic tool selection based on
    the research context and token budget.

    Usage:
        registry = ToolRegistry()

        @registry.register(
            name="verify_identity",
            description="Verify an algebraic identity using SymPy",
            category=ToolCategory.VERIFICATION,
            tier=ToolTier.ESSENTIAL,
        )
        def verify_identity(lhs: str, rhs: str) -> dict:
            ...
    """

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._by_category: dict[ToolCategory, list] = {}
        self._by_tier: dict[ToolTier, list] = {}

    def register(
        self,
        name: str,
        description: str,
        category: ToolCategory = ToolCategory.SYMBOLIC,
        tier: ToolTier = ToolTier.STANDARD,
        token_cost_estimate: int = 0,
        reliability: float = 0.9,
        parameters: Optional[dict] = None,
    ) -> Callable:
        """Decorator to register a tool function."""

        def decorator(fn: Callable) -> Callable:
            tool = ToolDefinition(
                name=name,
                description=description,
                category=category,
                tier=tier,
                token_cost_estimate=token_cost_estimate,
                reliability=reliability,
                parameters=parameters or {},
                fn=fn,
            )
            self._tools[name] = tool
            self._by_category.setdefault(category, []).append(tool)
            self._by_tier.setdefault(tier, []).append(tool)

            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                return fn(*args, **kwargs)

            return wrapper

        return decorator

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def get_all(self) -> list:
        return list(self._tools.values())

    def get_by_category(self, category: ToolCategory) -> list:
        return self._by_category.get(category, [])

    def get_by_tier(self, tier: ToolTier) -> list:
        return self._by_tier.get(tier, [])

    def get_for_budget(self, max_tokens: int) -> list:
        """Get tools that fit within a token budget."""
        result = []
        remaining = max_tokens
        # First add essentials
        for tool in self.get_by_tier(ToolTier.ESSENTIAL):
            result.append(tool)
            remaining -= tool.token_cost_estimate
        # Then standards
        for tool in self.get_by_tier(ToolTier.STANDARD):
            if tool.token_cost_estimate <= remaining:
                result.append(tool)
                remaining -= tool.token_cost_estimate
        # Extended if budget allows
        for tool in self.get_by_tier(ToolTier.EXTENDED):
            if tool.token_cost_estimate <= remaining:
                result.append(tool)
                remaining -= tool.token_cost_estimate
        return result

    def to_openai_schemas(self, tools: Optional[list] = None) -> list:
        """Convert tools to OpenAI function-calling schemas."""
        selected = tools or self.get_all()
        return [t.to_openai_schema() for t in selected]

    def execute(self, name: str, **kwargs) -> Any:
        """Execute a registered tool by name."""
        tool = self._tools.get(name)
        if not tool or not tool.fn:
            raise ValueError(f"Tool not found or not callable: {name}")
        start = time.perf_counter()
        try:
            result = tool.fn(**kwargs)
            latency = (time.perf_counter() - start) * 1000
            return {
                "success": True,
                "result": result,
                "tool": name,
                "latency_ms": latency,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool": name,
                "latency_ms": (time.perf_counter() - start) * 1000,
            }

    def list_tools(self) -> str:
        """Generate a human-readable tool listing."""
        lines = ["Available Research Tools:", "=" * 50]
        for category in ToolCategory:
            tools = self.get_by_category(category)
            if tools:
                lines.append(f"\n{category.value.upper()}:")
                for tool in tools:
                    lines.append(f"  {tool.name} [{tool.tier.value}]")
                    lines.append(f"    {tool.description}")
                    lines.append(f"    Reliability: {tool.reliability:.0%}")
        return "\n".join(lines)


# ── Global Registry ──────────────────────────────────────────────────

# Singleton for the application
global_tool_registry = ToolRegistry()
