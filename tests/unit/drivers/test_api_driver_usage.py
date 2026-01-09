"""Tests for ApiDriver token usage tracking."""
import os
from unittest.mock import MagicMock, patch

import pytest

from amelia.drivers.base import DriverUsage


class TestApiDriverGetUsage:
    """Tests for ApiDriver.get_usage() method."""

    def test_get_usage_returns_none_before_execution(self) -> None:
        """get_usage() should return None before any execution."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            from amelia.drivers.api.deepagents import ApiDriver

            driver = ApiDriver(model="openrouter:test/model")

            result = driver.get_usage()

            assert result is None
