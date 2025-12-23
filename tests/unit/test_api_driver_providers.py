"""Tests for ApiDriver provider extraction."""
import pytest
from amelia.drivers.api.openai import ApiDriver


class TestProviderExtraction:
    """Test provider extraction in ApiDriver."""

    def test_extracts_openai_provider(self):
        """Should extract openai provider from model string."""
        driver = ApiDriver(model="openai:gpt-4o")
        assert driver.model_name == "openai:gpt-4o"
        assert driver._provider == "openai"

    def test_extracts_openrouter_provider(self):
        """Should extract openrouter provider from model string."""
        driver = ApiDriver(model="openrouter:anthropic/claude-3.5-sonnet")
        assert driver.model_name == "openrouter:anthropic/claude-3.5-sonnet"
        assert driver._provider == "openrouter"

    def test_defaults_to_openai_without_prefix(self):
        """Should default to openai provider when no prefix given."""
        driver = ApiDriver(model="gpt-4o")
        assert driver._provider == "openai"
