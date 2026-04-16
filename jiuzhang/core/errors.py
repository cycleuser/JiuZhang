"""Custom exceptions and result types for JiuZhang."""

from dataclasses import dataclass, field
from typing import Any, Optional


class JiuZhangError(Exception):
    """Base exception for JiuZhang."""

    pass


class ModelError(JiuZhangError):
    """Error related to AI model operations."""

    pass


class CourseError(JiuZhangError):
    """Error related to course operations."""

    pass


class VisualizationError(JiuZhangError):
    """Error related to visualization operations."""

    pass


class ConfigError(JiuZhangError):
    """Error related to configuration operations."""

    pass


@dataclass
class ToolResult:
    """Unified result for tool operations.

    Attributes:
        success: Whether the operation succeeded.
        data: Result data if successful.
        error: Error message if failed.
        metadata: Additional metadata.
    """

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @classmethod
    def ok(cls, data: Any, metadata: Optional[dict] = None) -> "ToolResult":
        return cls(success=True, data=data, metadata=metadata or {})

    @classmethod
    def fail(cls, error: str, metadata: Optional[dict] = None) -> "ToolResult":
        return cls(success=False, error=error, metadata=metadata or {})
