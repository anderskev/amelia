"""Tests for orchestrator plan extraction from predictable path."""

import pytest
from datetime import date
from pathlib import Path
from typing import Callable
from unittest.mock import AsyncMock, MagicMock, patch

from amelia.core.state import ExecutionState
from amelia.core.types import Issue, Profile


@pytest.mark.asyncio
async def test_call_architect_node_reads_from_predictable_path(
    tmp_path: Path,
    mock_issue_factory: Callable[..., Issue],
    mock_profile_factory: Callable[..., Profile],
    mock_execution_state_factory: Callable[..., tuple[ExecutionState, Profile]],
) -> None:
    """Orchestrator should read plan from resolved path, not parse tool calls."""
    from amelia.core.orchestrator import call_architect_node

    # Create the plan file at the expected path
    today = date.today().isoformat()
    plan_dir = tmp_path / "docs" / "plans"
    plan_dir.mkdir(parents=True)
    plan_file = plan_dir / f"{today}-test-1.md"
    plan_content = """# Test Plan

**Goal:** Implement feature X

## Tasks
- Task 1
"""
    plan_file.write_text(plan_content)

    # Create profile with our tmp_path as working_dir
    profile = mock_profile_factory(working_dir=str(tmp_path))

    # Create state with the issue ID matching the plan path
    issue = mock_issue_factory(id="TEST-1", title="Test", description="Test issue")
    state, _ = mock_execution_state_factory(
        profile=profile,
        issue=issue,
    )

    # Mock the driver
    mock_driver = MagicMock()
    mock_driver.run_agentic = AsyncMock()

    # Create mock final state from driver
    mock_final_state = MagicMock()
    mock_final_state.raw_architect_output = "Plan written to file."
    mock_final_state.tool_calls = []  # No tool calls - we read from file
    mock_final_state.plan_path = None

    async def mock_run(*args, **kwargs):
        yield mock_final_state

    mock_driver.run_agentic.return_value = mock_run()

    # Mock the driver factory and config
    with (
        patch("amelia.core.orchestrator.DriverFactory") as mock_factory,
        patch("amelia.core.orchestrator._save_token_usage", new_callable=AsyncMock),
    ):
        mock_factory.get_driver.return_value = mock_driver

        config = {
            "configurable": {
                "thread_id": "wf-123",
                "profile": profile,
            }
        }

        result = await call_architect_node(state, config)

    # Plan should be read from predictable path
    assert result["plan_markdown"] == plan_content
    assert result["goal"] == "Implement feature X"
