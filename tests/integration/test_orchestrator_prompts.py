"""Integration tests for orchestrator prompt injection.

Tests that prompts flow from orchestrator config through to agents.
"""
from pathlib import Path
from typing import cast
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.runnables.config import RunnableConfig

from amelia.agents.architect import MarkdownPlanOutput
from amelia.agents.reviewer import ReviewResponse
from amelia.core.orchestrator import call_architect_node, call_reviewer_node
from tests.integration.conftest import make_config, make_execution_state, make_issue, make_profile


@pytest.fixture(autouse=True)
def mock_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set API key env var to allow driver construction."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-for-integration-tests")


@pytest.mark.integration
class TestOrchestratorPromptInjection:
    """Tests for prompt injection through orchestrator nodes."""

    async def test_architect_uses_injected_prompt_via_driver(self, tmp_path: Path) -> None:
        """Verify Architect uses injected prompt when calling driver.

        This test patches at the driver level to verify the prompt flows through.
        """
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)

        custom_plan_prompt = "Custom plan prompt from config..."
        prompts = {"architect.plan": custom_plan_prompt}

        profile = make_profile(
            plan_output_dir=str(plans_dir),
            working_dir=str(tmp_path),
        )
        issue = make_issue(id="TEST-1", title="Test feature")
        state = make_execution_state(issue=issue, profile=profile)
        config = make_config(thread_id="test-wf-1", profile=profile, prompts=prompts)

        mock_llm_response = MarkdownPlanOutput(
            goal="Test goal",
            plan_markdown="# Test Plan",
            key_files=["test.py"],
        )

        # Patch at driver.generate level to check system_prompt
        with patch("amelia.drivers.api.deepagents.ApiDriver.generate", new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = (mock_llm_response.model_dump(), "session-1")

            await call_architect_node(state, cast(RunnableConfig, config))

            # Verify the custom prompt was used
            mock_generate.assert_called_once()
            call_kwargs = mock_generate.call_args.kwargs
            assert call_kwargs["system_prompt"] == custom_plan_prompt

    async def test_reviewer_uses_injected_prompt_via_driver(self, tmp_path: Path) -> None:
        """Verify Reviewer uses injected prompt when calling driver.

        This test patches at the driver level to verify the prompt flows through.
        The reviewer node uses review() -> _single_review() which uses template_prompt.
        """
        # Template prompt has {persona} placeholder that gets formatted
        custom_template_prompt = "Custom {persona} review prompt..."
        prompts = {"reviewer.template": custom_template_prompt}

        profile = make_profile(working_dir=str(tmp_path))
        state = make_execution_state(
            profile=profile,
            goal="Test goal",
            code_changes_for_review="diff content",
        )
        config = make_config(thread_id="test-wf-2", profile=profile, prompts=prompts)

        mock_llm_response = ReviewResponse(
            approved=True,
            comments=["LGTM"],
            severity="low",
        )

        # Patch at driver.generate level to check system_prompt
        with patch("amelia.drivers.api.deepagents.ApiDriver.generate", new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = (mock_llm_response, "session-1")

            await call_reviewer_node(state, cast(RunnableConfig, config))

            # Verify the custom prompt was used (formatted with "General" persona)
            mock_generate.assert_called_once()
            call_kwargs = mock_generate.call_args.kwargs
            assert call_kwargs["system_prompt"] == "Custom General review prompt..."

    async def test_prompts_not_in_config_uses_defaults(self, tmp_path: Path) -> None:
        """When prompts not in config, agents should use class defaults.

        This ensures backward compatibility - existing workflows without
        prompts in config continue to work with default prompts.
        """
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)

        profile = make_profile(
            plan_output_dir=str(plans_dir),
            working_dir=str(tmp_path),
        )
        issue = make_issue(id="TEST-1", title="Test feature")
        state = make_execution_state(issue=issue, profile=profile)
        # No prompts in config
        config = make_config(thread_id="test-wf-3", profile=profile)

        mock_llm_response = MarkdownPlanOutput(
            goal="Test goal",
            plan_markdown="# Test Plan",
            key_files=["test.py"],
        )

        with patch("amelia.drivers.api.deepagents.ApiDriver.generate", new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = (mock_llm_response.model_dump(), "session-1")

            await call_architect_node(state, cast(RunnableConfig, config))

            # Verify default prompt was used (contains expected text)
            call_kwargs = mock_generate.call_args.kwargs
            system_prompt = call_kwargs["system_prompt"]
            assert "senior software architect" in system_prompt
            assert "Phase" in system_prompt or "phase" in system_prompt.lower()

    async def test_empty_prompts_dict_uses_defaults(self, tmp_path: Path) -> None:
        """Empty prompts dict in config should use agent defaults."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)

        profile = make_profile(
            plan_output_dir=str(plans_dir),
            working_dir=str(tmp_path),
        )
        issue = make_issue(id="TEST-1", title="Test feature")
        state = make_execution_state(issue=issue, profile=profile)
        # Empty prompts dict
        config = make_config(thread_id="test-wf-4", profile=profile, prompts={})

        mock_llm_response = MarkdownPlanOutput(
            goal="Test goal",
            plan_markdown="# Test Plan",
            key_files=["test.py"],
        )

        with patch("amelia.drivers.api.deepagents.ApiDriver.generate", new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = (mock_llm_response.model_dump(), "session-1")

            await call_architect_node(state, cast(RunnableConfig, config))

            # Verify default prompt was used
            call_kwargs = mock_generate.call_args.kwargs
            system_prompt = call_kwargs["system_prompt"]
            assert "senior software architect" in system_prompt
