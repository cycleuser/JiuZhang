"""Configuration management for JiuZhang."""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from jiuzhang.core.errors import ConfigError

DEFAULT_CONFIG_DIR = Path.home() / ".jiuzhang"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"

DEFAULT_PROVIDER = "ollama"
DEFAULT_MODEL = "qwen2.5:7b"
DEFAULT_BASE_URL = "http://localhost:11434/v1"

SUPPORTED_PROVIDERS = {
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "default_model": "qwen2.5:7b",
        "is_local": True,
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "is_local": False,
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com",
        "default_model": "claude-sonnet-4-20250514",
        "is_local": False,
    },
    "aliyun_coding_plan": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-max",
        "is_local": False,
    },
    "openai_compatible": {
        "base_url": "",
        "default_model": "",
        "is_local": False,
    },
}


@dataclass
class ProviderConfig:
    """Configuration for a single provider."""

    provider_type: str = "ollama"
    api_key: str = ""
    base_url: str = DEFAULT_BASE_URL
    default_model: str = DEFAULT_MODEL
    enabled: bool = True
    is_local: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "ProviderConfig":
        return cls(
            provider_type=data.get("provider_type", "ollama"),
            api_key=data.get("api_key", ""),
            base_url=data.get("base_url", DEFAULT_BASE_URL),
            default_model=data.get("default_model", DEFAULT_MODEL),
            enabled=data.get("enabled", True),
            is_local=data.get("is_local", True),
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Config:
    """Main configuration for JiuZhang.

    Manages provider settings, model selection, and application preferences.
    """

    active_provider: str = DEFAULT_PROVIDER
    active_model: str = DEFAULT_MODEL
    providers: dict = field(default_factory=dict)
    max_tokens: int = 8192
    temperature: float = 1.0
    language: str = "zh"
    data_dir: str = str(DEFAULT_CONFIG_DIR)
    first_run: bool = True

    def __post_init__(self):
        if not self.providers:
            self.providers = {}
            for name, defaults in SUPPORTED_PROVIDERS.items():
                self.providers[name] = ProviderConfig(
                    provider_type=name,
                    base_url=defaults["base_url"],
                    default_model=defaults["default_model"],
                    is_local=defaults["is_local"],
                )

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        path = Path(config_path) if config_path else DEFAULT_CONFIG_FILE
        if not path.exists():
            return cls()

        try:
            with open(path) as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (json.JSONDecodeError, IOError) as e:
            raise ConfigError(f"Failed to load config: {e}")

    def save(self, config_path: Optional[str] = None):
        path = Path(config_path) if config_path else DEFAULT_CONFIG_FILE
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "w") as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise ConfigError(f"Failed to save config: {e}")

    def to_dict(self) -> dict:
        result = asdict(self)
        result["providers"] = {
            k: v.to_dict() if isinstance(v, ProviderConfig) else v
            for k, v in self.providers.items()
        }
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        providers = {}
        for k, v in data.get("providers", {}).items():
            if isinstance(v, dict):
                providers[k] = ProviderConfig.from_dict(v)
            else:
                providers[k] = v

        return cls(
            active_provider=data.get("active_provider", DEFAULT_PROVIDER),
            active_model=data.get("active_model", DEFAULT_MODEL),
            providers=providers,
            max_tokens=data.get("max_tokens", 8192),
            temperature=data.get("temperature", 1.0),
            language=data.get("language", "zh"),
            data_dir=data.get("data_dir", str(DEFAULT_CONFIG_DIR)),
            first_run=data.get("first_run", True),
        )

    def get_provider(self, name: Optional[str] = None) -> ProviderConfig:
        provider_name = name or self.active_provider
        if provider_name not in self.providers:
            raise ConfigError(f"Unknown provider: {provider_name}")

        provider = self.providers[provider_name]
        if isinstance(provider, dict):
            provider = ProviderConfig.from_dict(provider)
            self.providers[provider_name] = provider

        api_key = self._get_api_key(provider)
        base_url = self._get_base_url(provider)

        provider.api_key = api_key
        provider.base_url = base_url
        return provider

    def _get_api_key(self, provider: ProviderConfig) -> str:
        if provider.api_key:
            return provider.api_key

        env_vars = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "aliyun_coding_plan": "DASHSCOPE_API_KEY",
            "openai_compatible": "OPENAI_API_KEY",
        }

        env_var = env_vars.get(provider.provider_type)
        if env_var:
            return os.environ.get(env_var, "")
        return ""

    def _get_base_url(self, provider: ProviderConfig) -> str:
        if provider.base_url:
            return provider.base_url

        env_vars = {
            "openai": "OPENAI_BASE_URL",
            "anthropic": "ANTHROPIC_BASE_URL",
        }

        env_var = env_vars.get(provider.provider_type)
        if env_var and os.environ.get(env_var):
            return os.environ[env_var]

        if provider.provider_type in SUPPORTED_PROVIDERS:
            return SUPPORTED_PROVIDERS[provider.provider_type]["base_url"]
        return ""
