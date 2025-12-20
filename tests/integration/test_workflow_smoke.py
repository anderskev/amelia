# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Workflow smoke tests for the orchestrator.

These tests verify the happy path through the orchestrator graph:
- Plan generation by architect
- Human approval
- Batch execution by developer
- Review by reviewer
- Completion

Tests use mocked agents to focus on graph flow, not agent behavior.
"""

from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.runnables.config import RunnableConfig

from amelia.core.orchestrator import (
    route_after_architect,
    route_after_developer,
    route_approval,
    route_batch_approval,
    route_blocker_resolution,
    should_continue_review_loop,
)
from amelia.core.state import BatchApproval, ExecutionPlan, ReviewResult
from amelia.core.types import DeveloperStatus, TrustLevel

from .conftest import (
    make_execution_state,
    make_plan,
    make_profile,
)


class TestRoutingDecisions:
    """Tests for orchestrator routing functions."""

    @pytest.mark.parametrize("plan_only,expected_route", [
        (True, "end"),
        (False, "human_approval"),
    ])
    def test_route_after_architect(self, plan_only: bool, expected_route: str) -> None:
        """Route after architect based on plan_only mode."""
        state = make_execution_state(plan_only=plan_only)
        route = route_after_architect(state)
        assert route == expected_route

    @pytest.mark.parametrize("approved,expected_route", [
        (True, "approve"),
        (False, "reject"),
    ])
    def test_route_approval(self, approved: bool, expected_route: str) -> None:
        """Route approval based on human_approved state."""
        state = make_execution_state(human_approved=approved)
        route = route_approval(state)
        assert route == expected_route

    @pytest.mark.parametrize("developer_status,num_batches,current_batch,expected_route", [
        (DeveloperStatus.ALL_DONE, 1, 0, "reviewer"),
        (DeveloperStatus.BATCH_COMPLETE, 2, 0, "batch_approval"),
        (DeveloperStatus.BLOCKED, 1, 0, "blocker_resolution"),
        (DeveloperStatus.EXECUTING, 1, 0, "developer"),
    ])
    def test_route_after_developer(
        self,
        developer_status: DeveloperStatus,
        num_batches: int,
        current_batch: int,
        expected_route: str,
    ) -> None:
        """Route after developer based on developer status."""
        state = make_execution_state(
            execution_plan=make_plan(num_batches=num_batches),
            current_batch_index=current_batch,
            developer_status=developer_status,
        )
        route = route_after_developer(state)
        assert route == expected_route

    @pytest.mark.parametrize("approved,expected_route", [
        (True, "developer"),
        (False, "__end__"),
    ])
    def test_route_batch_approval(self, approved: bool, expected_route: str) -> None:
        """Route batch approval based on approval decision."""
        approval = BatchApproval(
            batch_number=0,
            approved=approved,
            feedback=None if approved else "Not good",
            approved_at=datetime.now(UTC),
        )
        state = make_execution_state(batch_approvals=[approval])
        route = route_batch_approval(state)
        assert route == expected_route

    @pytest.mark.parametrize("workflow_status,expected_route", [
        ("aborted", "__end__"),
        ("running", "developer"),
    ])
    def test_route_blocker_resolution(self, workflow_status: str, expected_route: str) -> None:
        """Route blocker resolution based on workflow status."""
        state = make_execution_state(workflow_status=workflow_status)
        route = route_blocker_resolution(state)
        assert route == expected_route


class TestReviewLoopDecision:
    """Tests for review loop continuation decision."""

    def test_review_approved_ends(self) -> None:
        """Approved review should end loop."""
        review = ReviewResult(
            approved=True,
            comments=["Looks good"],
            severity="low",
            reviewer_persona="Test",
        )
        state = make_execution_state(
            execution_plan=make_plan(num_batches=1),
            last_review=review,
        )
        route = should_continue_review_loop(state)
        assert route == "end"

    def test_review_rejected_with_batches_continues(self) -> None:
        """Rejected review with batches should re-evaluate."""
        review = ReviewResult(
            approved=False,
            comments=["Needs work"],
            severity="medium",
            reviewer_persona="Test",
        )
        state = make_execution_state(
            execution_plan=make_plan(num_batches=1),
            last_review=review,
        )
        route = should_continue_review_loop(state)
        assert route == "re_evaluate"

    def test_review_rejected_no_batches_ends(self) -> None:
        """Rejected review without batches should end."""
        empty_plan = ExecutionPlan(
            goal="Empty",
            batches=(),
            total_estimated_minutes=0,
            tdd_approach=False,
        )
        review = ReviewResult(
            approved=False,
            comments=["Needs work"],
            severity="medium",
            reviewer_persona="Test",
        )
        state = make_execution_state(
            execution_plan=empty_plan,
            last_review=review,
        )
        route = should_continue_review_loop(state)
        assert route == "end"


class TestGraphNodes:
    """Tests for individual graph nodes with mocked agents."""

    @pytest.fixture
    def mock_driver_factory(self) -> Any:
        """Mock DriverFactory.get_driver to return a mock driver."""
        with patch("amelia.core.orchestrator.DriverFactory.get_driver") as mock:
            mock_driver = AsyncMock()
            mock.return_value = mock_driver
            yield mock

    async def test_architect_node_generates_plan(self, mock_driver_factory: Any) -> None:
        """Architect node should generate execution plan."""
        from amelia.core.orchestrator import call_architect_node

        plan = make_plan(num_batches=2, steps_per_batch=2)

        with patch("amelia.core.orchestrator.Architect") as MockArchitect:
            mock_architect = AsyncMock()
            mock_architect.generate_execution_plan = AsyncMock(return_value=plan)
            MockArchitect.return_value = mock_architect

            state = make_execution_state()
            config = cast(RunnableConfig, {"configurable": {"thread_id": "test-123"}})

            result = await call_architect_node(state, config)

            assert "execution_plan" in result
            assert result["execution_plan"] == plan

    async def test_reviewer_node_generates_review(self, mock_driver_factory: Any) -> None:
        """Reviewer node should generate review result."""
        from amelia.core.orchestrator import call_reviewer_node

        review = ReviewResult(
            approved=True,
            comments=["Great work"],
            severity="low",
            reviewer_persona="Test Reviewer",
        )

        with patch("amelia.core.orchestrator.Reviewer") as MockReviewer:
            mock_reviewer = AsyncMock()
            mock_reviewer.review = AsyncMock(return_value=review)
            MockReviewer.return_value = mock_reviewer

            state = make_execution_state(
                execution_plan=make_plan(num_batches=1),
            )
            config = cast(RunnableConfig, {"configurable": {"thread_id": "test-123"}})

            result = await call_reviewer_node(state, config)

            assert "last_review" in result
            assert result["last_review"].approved is True

    async def test_developer_node_requires_plan(self, mock_driver_factory: Any) -> None:
        """Developer node should raise error without execution plan."""
        from amelia.core.orchestrator import call_developer_node

        state = make_execution_state(execution_plan=None)
        config = cast(RunnableConfig, {"configurable": {"thread_id": "test-123"}})

        with pytest.raises(ValueError, match="no execution plan"):
            await call_developer_node(state, config)


class TestHumanApprovalNode:
    """Tests for human approval node behavior."""

    async def test_human_approval_server_mode_returns_empty(self) -> None:
        """Server mode should return empty dict (interrupt handles pause)."""
        from amelia.core.orchestrator import human_approval_node

        state = make_execution_state()
        config = cast(RunnableConfig, {"configurable": {"execution_mode": "server", "thread_id": "test-123"}})

        result = await human_approval_node(state, config)

        assert result == {}

    async def test_batch_approval_node_records_approval(self) -> None:
        """Batch approval node should record approval."""
        from amelia.core.orchestrator import batch_approval_node

        state = make_execution_state(
            current_batch_index=0,
            human_approved=True,
        )

        result = await batch_approval_node(state)

        assert "batch_approvals" in result
        assert len(result["batch_approvals"]) == 1
        assert result["batch_approvals"][0].approved is True
        # human_approved should be reset
        assert result["human_approved"] is None


class TestTrustLevelRouting:
    """Tests for trust level affecting batch approval routing."""

    @pytest.mark.parametrize("trust_level,batch_checkpoint_enabled,expected_route", [
        (TrustLevel.AUTONOMOUS, True, "developer"),  # AUTONOMOUS skips low-risk checkpoint
        (TrustLevel.STANDARD, True, "batch_approval"),  # STANDARD always checkpoints
        (TrustLevel.STANDARD, False, "developer"),  # Checkpoint disabled skips all
    ])
    def test_trust_level_routing(
        self,
        trust_level: TrustLevel,
        batch_checkpoint_enabled: bool,
        expected_route: str,
    ) -> None:
        """Trust level and checkpoint settings affect batch approval routing."""
        profile = make_profile(
            trust_level=trust_level,
            batch_checkpoint_enabled=batch_checkpoint_enabled,
        )
        plan = make_plan(num_batches=2, steps_per_batch=1)
        state = make_execution_state(
            profile=profile,
            execution_plan=plan,
            current_batch_index=0,
            developer_status=DeveloperStatus.BATCH_COMPLETE,
        )

        route = route_after_developer(state)
        assert route == expected_route
