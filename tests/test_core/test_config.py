"""Tests for core config module."""

import json
import tempfile
from pathlib import Path

import pytest

from jiuzhang.core.config import Config, ProviderConfig
from jiuzhang.core.errors import ConfigError


class TestConfig:
    def test_default_config(self):
        config = Config()
        assert config.active_provider == "ollama"
        assert config.language == "zh"
        assert config.max_tokens == 8192
        assert len(config.providers) > 0

    def test_get_provider(self):
        config = Config()
        provider = config.get_provider("ollama")
        assert provider.provider_type == "ollama"
        assert provider.is_local is True

    def test_get_unknown_provider(self):
        config = Config()
        with pytest.raises(ConfigError):
            config.get_provider("unknown_provider")

    def test_save_and_load(self):
        config = Config()
        config.active_model = "test_model"

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            config.save(f.name)
            loaded = Config.load(f.name)

        assert loaded.active_model == "test_model"
        Path(f.name).unlink()

    def test_to_dict(self):
        config = Config()
        data = config.to_dict()
        assert isinstance(data, dict)
        assert "active_provider" in data
        assert "providers" in data

    def test_from_dict(self):
        data = {
            "active_provider": "openai",
            "active_model": "gpt-4",
            "language": "en",
        }
        config = Config.from_dict(data)
        assert config.active_provider == "openai"
        assert config.active_model == "gpt-4"
        assert config.language == "en"


class TestProviderConfig:
    def test_default_provider(self):
        provider = ProviderConfig()
        assert provider.provider_type == "ollama"
        assert provider.enabled is True

    def test_provider_to_dict(self):
        provider = ProviderConfig(api_key="test")
        data = provider.to_dict()
        assert data["api_key"] == "test"

    def test_provider_from_dict(self):
        data = {"provider_type": "openai", "api_key": "sk-test"}
        provider = ProviderConfig.from_dict(data)
        assert provider.provider_type == "openai"
        assert provider.api_key == "sk-test"
