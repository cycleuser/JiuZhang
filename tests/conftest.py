"""Shared fixtures for JiuZhang tests."""

import pytest
from jiuzhang.core.config import Config
from jiuzhang.math_engine.curriculum import Curriculum


@pytest.fixture
def config():
    """Return a default config for testing."""
    return Config()


@pytest.fixture
def curriculum():
    """Return an empty curriculum for testing."""
    return Curriculum()
