"""Core modules for JiuZhang.

Configuration, errors, model providers, constants, and provider lifecycle management.
"""

from jiuzhang.core.config import Config, ProviderConfig
from jiuzhang.core.errors import ToolResult, JiuZhangError, ConfigError, ModelError
from jiuzhang.core.constants import (
    APP_NAME, APP_NAME_CN,
    MATH_LEVELS, MATH_LEVEL_NAMES_CN,
    COURSE_CATEGORIES, COURSE_CATEGORY_NAMES_CN,
)
from jiuzhang.core.multi_provider_api import MultiProviderClient

# V2: Async provider + ProviderFactory
from jiuzhang.core.provider_factory import (
    ProviderFactory, ProviderSnapshot, ProviderMetrics, ProviderHealth,
    FallbackChain,
)

try:
    from jiuzhang.core.async_provider import (
        AsyncModelProvider, ModelResponse, StreamEvent, StreamEventType,
    )
except ImportError:
    AsyncModelProvider = None
    ModelResponse = None
    StreamEvent = None
    StreamEventType = None

# V2: Model router
try:
    from jiuzhang.core.model_router import ModelRouter, TaskType, RoutingConfig
except ImportError:
    ModelRouter = None
    TaskType = None
    RoutingConfig = None

# V2: Local optimizations
try:
    from jiuzhang.core.local_optimizations import (
        LocalBackend, LocalModelConfig, check_model_math_capability,
        BatchInferenceRunner, get_reasoning_hint, clean_math_output,
    )
except ImportError:
    LocalBackend = None
    LocalModelConfig = None
    check_model_math_capability = None
    BatchInferenceRunner = None
    get_reasoning_hint = None
    clean_math_output = None

__all__ = [
    # Config & Errors
    "Config", "ProviderConfig",
    "ToolResult", "JiuZhangError", "ConfigError", "ModelError",
    # Sync client (backward compat)
    "MultiProviderClient",
    # Constants
    "APP_NAME", "APP_NAME_CN",
    "MATH_LEVELS", "MATH_LEVEL_NAMES_CN",
    "COURSE_CATEGORIES", "COURSE_CATEGORY_NAMES_CN",
    # V2: Async Provider + Factory
    "AsyncModelProvider", "ModelResponse", "StreamEvent", "StreamEventType",
    "ProviderFactory", "ProviderSnapshot", "ProviderMetrics", "ProviderHealth",
    "FallbackChain",
    # V2: Model Router
    "ModelRouter", "TaskType", "RoutingConfig",
    # V2: Local Optimizations
    "LocalBackend", "LocalModelConfig",
    "check_model_math_capability", "BatchInferenceRunner",
    "get_reasoning_hint", "clean_math_output",
]
