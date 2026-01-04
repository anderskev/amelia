"""Tests for Architect agent agentic execution."""
import pytest

from amelia.agents.architect import Architect


class TestArchitectAgenticPrompt:
    """Tests for agentic architect system prompt."""

    def test_plan_prompt_includes_exploration_guidance(self, mock_driver) -> None:
        """System prompt should guide exploration before planning."""
        architect = Architect(mock_driver)
        prompt = architect.plan_prompt

        assert "read-only" in prompt.lower() or "exploration" in prompt.lower()
        assert "DO NOT modify" in prompt or "do not modify" in prompt.lower()

    def test_plan_prompt_emphasizes_references_over_code(self, mock_driver) -> None:
        """System prompt should emphasize file references over code examples."""
        architect = Architect(mock_driver)
        prompt = architect.plan_prompt

        assert "reference" in prompt.lower()
        assert "NOT to Include" in prompt or "What NOT" in prompt
