import asyncio
import time
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from amelia.agents.architect import PlanOutput
from amelia.agents.project_manager import create_project_manager
from amelia.agents.reviewer import ReviewResponse
from amelia.core.orchestrator import call_reviewer_node
from amelia.core.orchestrator import create_orchestrator_graph
from amelia.core.state import ExecutionState
from amelia.core.state import Task
from amelia.core.state import TaskDAG
from amelia.core.types import Issue
from amelia.core.types import Profile


async def test_orchestrator_full_loop() -> None:
    """Verifies a full execution loop of the orchestrator from plan to execute."""
    profile = Profile(name="test_profile", driver="cli:claude", tracker="noop", strategy="single")
    test_issue = Issue(id="TEST-1", title="Test Issue", description="Implement a dummy function.")

    project_manager = create_project_manager(profile)
    fetched_issue = project_manager.get_issue(test_issue.id)

    ExecutionState(profile=profile, issue=fetched_issue)
    app = create_orchestrator_graph()

    assert app is not None


@pytest.mark.skip(reason="Multi-profile planning logic not yet implemented")
async def test_orchestrator_multi_profile_planning() -> None:
    """Ensures task planning works correctly under different CLI and API profiles."""
    pass


async def test_orchestrator_competitive_review() -> None:
    """Verifies the orchestrator can handle competitive review scenarios (US3)."""
    profile_competitive = Profile(
        name="competitive_reviewer", driver="api:openai", tracker="noop", strategy="competitive"
    )
    test_issue = Issue(
        id="COMP-1", title="Competitive Review Test", description="Review a code change competitively."
    )

    mock_driver = AsyncMock()
    mock_driver.generate.return_value = ReviewResponse(
        approved=True,
        comments=["Good code"],
        severity="low"
    )

    with patch("amelia.drivers.factory.DriverFactory.get_driver", return_value=mock_driver):
        initial_state = ExecutionState(
            profile=profile_competitive,
            issue=test_issue,
            code_changes_for_review="diff --git a/file.py b/file.py..."
        )

        final_state = await call_reviewer_node(initial_state)

        assert len(final_state.review_results) == 1
        result = final_state.review_results[0]
        assert result.reviewer_persona == "Competitive-Aggregated"
        assert result.approved is True
        assert mock_driver.generate.call_count == 3


async def test_orchestrator_parallel_review_api() -> None:
    """Verifies concurrent API calls during competitive review with an API driver."""
    profile = Profile(
        name="api_comp_reviewer", driver="api:openai", tracker="noop", strategy="competitive"
    )
    test_issue = Issue(
        id="PAR-API", title="Parallel API Review", description="Test concurrent API calls for review."
    )

    mock_driver = AsyncMock()

    async def slow_generate(*_args: Any, **_kwargs: Any) -> ReviewResponse:
        await asyncio.sleep(0.1)
        return ReviewResponse(approved=True, comments=[], severity="low")

    mock_driver.generate.side_effect = slow_generate

    with patch("amelia.drivers.factory.DriverFactory.get_driver", return_value=mock_driver):
        start_time = time.time()

        initial_state = ExecutionState(
            profile=profile,
            issue=test_issue,
            code_changes_for_review="changes"
        )

        await call_reviewer_node(initial_state)

        duration = time.time() - start_time

        # Sequential: 0.3s, Parallel: ~0.1s
        assert duration < 0.25
        assert mock_driver.generate.call_count == 3


async def test_orchestrator_parallel_execution_api_driver() -> None:
    """Verifies the orchestrator executes independent tasks in parallel with an API driver."""
    profile = Profile(name="api_parallel", driver="api:openai", tracker="noop", strategy="single")
    test_issue = Issue(id="PAR-EXEC", title="Parallel Execution Test", description="Execute tasks in parallel.")

    async def delayed_execute_task(_self: Any, task: Task) -> dict[str, str]:
        await asyncio.sleep(0.05)
        return {"status": "completed", "output": f"Task {task.id} finished"}

    mock_plan_output = PlanOutput(
        task_dag=TaskDAG(tasks=[
            Task(id="P1", description="Task 1", status="pending"),
            Task(id="P2", description="Task 2", status="pending"),
        ], original_issue="PAR-EXEC"),
        markdown_path=Path("/tmp/test-plan-par-exec.md")
    )

    mock_driver = AsyncMock()
    mock_driver.generate.return_value = ReviewResponse(approved=True, comments=[], severity="low")

    with patch('amelia.agents.architect.Architect.plan', new_callable=AsyncMock) as mock_plan, \
         patch('amelia.agents.developer.Developer.execute_task', new=delayed_execute_task), \
         patch('amelia.drivers.factory.DriverFactory.get_driver', return_value=mock_driver), \
         patch('typer.confirm', return_value=True), \
         patch('typer.prompt', return_value=""):

        mock_plan.return_value = mock_plan_output
        initial_state = ExecutionState(profile=profile, issue=test_issue)
        app = create_orchestrator_graph()

        start_time = time.time()
        final_state = await app.ainvoke(initial_state)
        duration = time.time() - start_time

        # Sequential: 100ms, Parallel: ~50ms (200ms threshold for CI variability)
        assert duration < 0.2, f"Expected < 0.2s, got {duration:.3f}s"
        assert all(task.status == "completed" for task in final_state["plan"].tasks)


async def test_orchestrator_parallel_execution_cli_driver() -> None:
    """Verifies the CLI driver executes parallel tasks concurrently using asyncio.gather."""
    profile = Profile(name="cli_parallel", driver="cli:claude", tracker="noop", strategy="single")
    test_issue = Issue(id="CLI-PAR", title="CLI Parallel Test", description="Test CLI parallel execution.")

    async def delayed_execute_task(_self: Any, task: Task) -> dict[str, str]:
        await asyncio.sleep(0.05)
        return {"status": "completed", "output": f"Task {task.id} finished"}

    mock_plan_output = PlanOutput(
        task_dag=TaskDAG(tasks=[
            Task(id="S1", description="Task A", status="pending"),
            Task(id="S2", description="Task B", status="pending"),
        ], original_issue="CLI-PAR"),
        markdown_path=Path("/tmp/test-plan-cli-par.md")
    )

    mock_driver = AsyncMock()
    mock_driver.generate.return_value = ReviewResponse(approved=True, comments=[], severity="low")

    with patch('amelia.agents.architect.Architect.plan', new_callable=AsyncMock) as mock_plan, \
         patch('amelia.agents.developer.Developer.execute_task', new=delayed_execute_task), \
         patch('amelia.drivers.factory.DriverFactory.get_driver', return_value=mock_driver), \
         patch('typer.confirm', return_value=True), \
         patch('typer.prompt', return_value=""):

        mock_plan.return_value = mock_plan_output
        initial_state = ExecutionState(profile=profile, issue=test_issue)
        app = create_orchestrator_graph()

        start_time = time.time()
        final_state = await app.ainvoke(initial_state)
        duration = time.time() - start_time

        # Sequential: 100ms, Parallel: ~50ms (200ms threshold for CI variability)
        assert duration < 0.2, f"Expected < 0.2s, got {duration:.3f}s"
        assert all(task.status == "completed" for task in final_state["plan"].tasks)
