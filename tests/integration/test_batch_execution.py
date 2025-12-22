# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Integration tests for batch execution flow.

These tests exercise the orchestrator nodes with real state transitions,
testing state changes across developer → batch_approval → developer flows.
"""

from collections.abc import Callable
from unittest.mock import AsyncMock, patch

from amelia.core.orchestrator import (
    batch_approval_node,
    call_developer_node,
    route_after_developer,
)
from amelia.core.state import (
    BatchResult,
    ExecutionPlan,
    ExecutionState,
    StepResult,
)
from amelia.core.types import DeveloperStatus, Issue, Profile, TrustLevel


class TestBatchExecutionFlow:
    """Integration tests for complete batch execution flows."""

    async def test_single_batch_completes_successfully(
        self,
        test_profile: Profile,
        test_issue: Issue,
        mock_execution_plan_factory: Callable[..., ExecutionPlan],
    ) -> None:
        """Test that a single batch executes and completes successfully."""
        plan = mock_execution_plan_factory(num_batches=1, steps_per_batch=2)

        initial_state = ExecutionState(
            profile_id=test_profile.name,
            issue=test_issue,
            execution_plan=plan,
            current_batch_index=0,
            human_approved=True,
        )

        # Mock the Developer to simulate successful execution
        mock_batch_result = BatchResult(
            batch_number=1,
            status="complete",
            completed_steps=(
                StepResult(step_id="step-1", status="completed", output="ok"),
                StepResult(step_id="step-2", status="completed", output="ok"),
            ),
            blocker=None,
        )

        mock_driver = AsyncMock()
        mock_developer = AsyncMock()
        mock_developer.run.return_value = {
            "developer_status": DeveloperStatus.BATCH_COMPLETE,
            "current_batch_index": 1,
            "batch_results": (mock_batch_result,),
        }

        with patch(
            "amelia.drivers.factory.DriverFactory.get_driver",
            return_value=mock_driver,
        ), patch(
            "amelia.core.orchestrator.Developer",
        ) as MockDeveloper:
            MockDeveloper.return_value = mock_developer

            config = {"configurable": {"thread_id": "test-1", "profile": test_profile}}
            result = await call_developer_node(initial_state, config)

        # Verify batch completed
        assert result["developer_status"] == DeveloperStatus.BATCH_COMPLETE
        assert result["current_batch_index"] == 1
        assert len(result["batch_results"]) == 1
        assert result["batch_results"][0].status == "complete"

    async def test_multiple_batches_routes_through_approval(
        self,
        test_issue: Issue,
        mock_execution_plan_factory: Callable[..., ExecutionPlan],
        mock_profile_factory: Callable[..., Profile],
    ) -> None:
        """Test that multiple batches route to batch_approval between each."""
        profile = mock_profile_factory(
            trust_level=TrustLevel.STANDARD,
            batch_checkpoint_enabled=True,
        )
        plan = mock_execution_plan_factory(num_batches=2, steps_per_batch=1)

        # State after first batch completes
        state = ExecutionState(
            profile_id=profile.name,
            issue=test_issue,
            execution_plan=plan,
            current_batch_index=1,  # Batch 1 done
            developer_status=DeveloperStatus.BATCH_COMPLETE,
            human_approved=True,
        )

        # Route should go to batch_approval
        config = {"configurable": {"thread_id": "test-routing", "profile": profile}}
        route = route_after_developer(state, config)
        assert route == "batch_approval"

    async def test_batch_approval_continues_on_approval(
        self,
        test_issue: Issue,
        mock_execution_plan_factory: Callable[..., ExecutionPlan],
        mock_profile_factory: Callable[..., Profile],
    ) -> None:
        """Test that batch_approval_node records approval and continues."""
        profile = mock_profile_factory(
            trust_level=TrustLevel.STANDARD,
            batch_checkpoint_enabled=True,
        )
        plan = mock_execution_plan_factory(num_batches=2, steps_per_batch=1)

        state = ExecutionState(
            profile_id=profile.name,
            issue=test_issue,
            execution_plan=plan,
            current_batch_index=1,  # Batch 1 done
            developer_status=DeveloperStatus.BATCH_COMPLETE,
            human_approved=True,  # Approved
        )

        result = await batch_approval_node(state)

        # batch_approval_node records the approval and resets human_approved
        assert result is not None
        assert "batch_approvals" in result
        assert len(result["batch_approvals"]) == 1
        assert result["batch_approvals"][0].approved is True

    async def test_developer_routes_to_reviewer_when_all_done(
        self,
        test_issue: Issue,
        mock_execution_plan_factory: Callable[..., ExecutionPlan],
        mock_profile_factory: Callable[..., Profile],
    ) -> None:
        """Test that developer routes to reviewer when all batches complete."""
        profile = mock_profile_factory()
        plan = mock_execution_plan_factory(num_batches=1, steps_per_batch=1)

        # State after all batches complete
        state = ExecutionState(
            profile_id=profile.name,
            issue=test_issue,
            execution_plan=plan,
            current_batch_index=1,  # Only 1 batch, now done
            developer_status=DeveloperStatus.ALL_DONE,
            human_approved=True,
        )

        # Route should go to reviewer
        route = route_after_developer(state)
        assert route == "reviewer"


