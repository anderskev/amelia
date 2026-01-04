"""Tests for orchestrator helper functions.

Note: Plan extraction tests are in test_orchestrator_plan_extraction.py
"""

import pytest
from langchain_core.runnables.config import RunnableConfig

from amelia.core.orchestrator import _extract_config_params, _extract_goal_from_markdown
from amelia.core.types import Profile


class TestExtractConfigParams:
    """Tests for _extract_config_params helper."""

    def test_extracts_profile_from_config(self) -> None:
        """Should extract profile from config.configurable.profile."""
        profile = Profile(name="test", driver="cli:claude", model="sonnet")
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "wf-123",
                "profile": profile,
            }
        }
        stream_emitter, workflow_id, extracted_profile = _extract_config_params(config)
        assert extracted_profile == profile
        assert workflow_id == "wf-123"

    def test_raises_if_profile_missing(self) -> None:
        """Should raise ValueError if profile not in config."""
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "wf-123",
            }
        }
        with pytest.raises(ValueError, match="profile is required"):
            _extract_config_params(config)


class TestExtractGoalFromMarkdown:
    """Tests for temporary goal extraction helper."""

    def test_extracts_goal_from_markdown(self) -> None:
        """Should extract goal from **Goal:** line."""
        markdown = "# Plan\n\n**Goal:** Implement the feature\n\n## Tasks"
        result = _extract_goal_from_markdown(markdown)
        assert result == "Implement the feature"

    def test_returns_none_for_empty_input(self) -> None:
        """Should return None for empty/None input."""
        assert _extract_goal_from_markdown(None) is None
        assert _extract_goal_from_markdown("") is None

    def test_returns_fallback_when_no_goal_line(self) -> None:
        """Should return first meaningful line as fallback when no Goal line present."""
        markdown = "# Plan\n\nSome content without goal"
        # New behavior: extracts first meaningful line as fallback
        assert _extract_goal_from_markdown(markdown) == "Some content without goal"

    def test_returns_none_when_all_patterns_fail(self) -> None:
        """Should return None when no patterns match."""
        # Short lines under 20 chars, headers only, or lists only
        markdown = "# Plan\n\n- item\n- item2"
        assert _extract_goal_from_markdown(markdown) is None

    def test_handles_goal_with_colon_in_content(self) -> None:
        """Should handle goal text that contains colons."""
        markdown = "**Goal:** Fix bug: handle edge case"
        result = _extract_goal_from_markdown(markdown)
        assert result == "Fix bug: handle edge case"

    def test_handles_multiline_document(self) -> None:
        """Should find goal anywhere in document."""
        markdown = """# Implementation Plan

Some preamble text.

**Goal:** The actual goal here

## Task 1
Content
"""
        result = _extract_goal_from_markdown(markdown)
        assert result == "The actual goal here"

    def test_returns_none_for_empty_goal_line(self) -> None:
        """Should return None when Goal line has no content."""
        markdown = "# Plan\n\n**Goal:**\n\n## Tasks"
        assert _extract_goal_from_markdown(markdown) is None
        # Also test with whitespace only
        markdown_whitespace = "# Plan\n\n**Goal:**   \n\n## Tasks"
        assert _extract_goal_from_markdown(markdown_whitespace) is None

    def test_extracts_goal_from_goal_header(self) -> None:
        """Should extract goal from ## Goal: header."""
        markdown = "# Plan\n\n## Goal: Implement user authentication\n\n## Tasks"
        result = _extract_goal_from_markdown(markdown)
        assert result == "Implement user authentication"

    def test_extracts_goal_from_goal_header_next_line(self) -> None:
        """Should extract next line if ## Goal header has no inline content."""
        markdown = "# Plan\n\n## Goal\nRefactor the database layer\n\n## Tasks"
        result = _extract_goal_from_markdown(markdown)
        assert result == "Refactor the database layer"

    def test_extracts_goal_from_plan_header(self) -> None:
        """Should extract title from ## Implementation Plan: XYZ format."""
        markdown = "## Implementation Plan: Sirona API Backend\n\nBased on exploration..."
        result = _extract_goal_from_markdown(markdown)
        assert result == "Sirona API Backend"


