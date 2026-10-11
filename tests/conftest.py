"""Shared fixtures for JiuZhang tests."""

import pytest


@pytest.fixture
def config():
    """Return a default config for testing."""
    from jiuzhang.core.config import Config
    return Config()


@pytest.fixture
def curriculum():
    """Return an empty curriculum for testing."""
    from jiuzhang.math_engine.curriculum import Curriculum
    return Curriculum()
