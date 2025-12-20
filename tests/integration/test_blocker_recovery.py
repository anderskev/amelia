# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Integration tests for blocker recovery flow.

These tests exercise blocker resolution handling:
- Skip resolution → add to skipped_step_ids, continue
- Retry/fix resolution → clear blocker, continue to developer
- Abort resolution → set workflow_status to aborted
- Abort with revert → revert git changes, set aborted

Tests use real orchestrator routing functions and blocker_resolution_node.
"""

from unittest.mock import AsyncMock, patch

import pytest

from amelia.core.orchestrator import (
    blocker_resolution_node,
    route_after_developer,
    route_blocker_resolution,
)
from amelia.core.state import GitSnapshot
from amelia.core.types import DeveloperStatus

from .conftest import (
    assert_step_skipped,
    assert_workflow_status,
    make_batch,
    make_blocker,
    make_execution_state,
    make_plan,
    make_step,
)


class TestBlockerRoutingDecisions:
    """Tests for routing decisions based on blocker state."""

    @pytest.mark.parametrize(
        "developer_status,workflow_status,has_blocker,routing_function,expected_route",
        [
            # BLOCKED with blocker routes to blocker_resolution
            (DeveloperStatus.BLOCKED, "running", True, "route_after_developer", "blocker_resolution"),
            # Aborted workflow routes to end
            (DeveloperStatus.BLOCKED, "aborted", False, "route_blocker_resolution", "__end__"),
            # Non-aborted workflow routes to developer
            (DeveloperStatus.EXECUTING, "running", False, "route_blocker_resolution", "developer"),
        ],
    )
    def test_blocker_routing_decisions(
        self,
        developer_status: DeveloperStatus,
        workflow_status: str,
        has_blocker: bool,
        routing_function: str,
        expected_route: str,
    ) -> None:
        """Test various blocker routing decisions based on state."""
        blocker = None
        if has_blocker:
            blocker = make_blocker(
                step_id="step-1",
                step_description="Test step",
                error_message="pytest not found",
            )

        state = make_execution_state(
            execution_plan=make_plan(num_batches=1),
            current_batch_index=0,
            developer_status=developer_status,
            current_blocker=blocker,
            workflow_status=workflow_status,
            human_approved=True,
        )

        if routing_function == "route_after_developer":
            actual_route: str = route_after_developer(state)
        else:
            actual_route = route_blocker_resolution(state)

        assert actual_route == expected_route


class TestSkipResolution:
    """Tests for skip blocker resolution."""

    async def test_skip_resolution_adds_to_skipped_steps(self) -> None:
        """Skip resolution should add the blocked step to skipped_step_ids."""
        step_1 = make_step(id="step-1")
        step_2 = make_step(id="step-2")

        batch = make_batch(batch_number=1, steps=(step_1, step_2))
        plan = make_plan(batches=(batch,))

        blocker = make_blocker(
            step_id="step-1",
            step_description="Base step",
            error_message="Command failed",
        )

        state = make_execution_state(
            execution_plan=plan,
            current_batch_index=0,
            developer_status=DeveloperStatus.BLOCKED,
            current_blocker=blocker,
            blocker_resolution="skip",
            human_approved=True,
        )

        result = await blocker_resolution_node(state)

        assert_step_skipped(result, "step-1")
        # Blocker should be cleared
        assert result["current_blocker"] is None
        assert result["blocker_resolution"] is None

    async def test_skip_resolution_routes_back_to_developer(self) -> None:
        """After skip resolution, routing should continue to developer."""
        state = make_execution_state(
            execution_plan=make_plan(num_batches=1, steps_per_batch=2),
            current_batch_index=0,
            developer_status=DeveloperStatus.EXECUTING,
            current_blocker=None,
            skipped_step_ids=frozenset({"step-1"}),
            workflow_status="running",
            human_approved=True,
        )

        route = route_blocker_resolution(state)
        assert route == "developer"


class TestAbortResolution:
    """Tests for abort blocker resolution."""

    @pytest.mark.parametrize(
        "blocker_resolution,has_git_snapshot,should_call_revert",
        [
            # Plain abort - no revert
            ("abort", False, False),
            # Abort with revert and snapshot - should revert
            ("abort_revert", True, True),
            # Abort with revert but no snapshot - should not revert but still abort
            ("abort_revert", False, False),
        ],
    )
    async def test_abort_resolution_variants(
        self,
        blocker_resolution: str,
        has_git_snapshot: bool,
        should_call_revert: bool,
    ) -> None:
        """Test abort resolution variants (plain abort, abort with revert)."""
        git_snapshot = None
        if has_git_snapshot:
            git_snapshot = GitSnapshot(
                head_commit="abc123def456",
                dirty_files=(),
                stash_ref=None,
            )

        blocker = make_blocker(
            step_id="step-1",
            step_description="Test step 1",
            error_message="Critical failure",
        )

        state = make_execution_state(
            execution_plan=make_plan(num_batches=1),
            current_batch_index=0,
            developer_status=DeveloperStatus.BLOCKED,
            current_blocker=blocker,
            blocker_resolution=blocker_resolution,
            git_snapshot_before_batch=git_snapshot,
            human_approved=True,
        )

        with patch(
            "amelia.core.orchestrator.revert_to_git_snapshot",
            AsyncMock(),
        ) as mock_revert:
            result = await blocker_resolution_node(state)

            # Verify revert was called (or not)
            if should_call_revert:
                mock_revert.assert_called_once()
            else:
                mock_revert.assert_not_called()

            # Should be aborted
            assert_workflow_status(result, "aborted")
            assert result["current_blocker"] is None
            assert result["blocker_resolution"] is None

    async def test_aborted_state_routes_to_end(self) -> None:
        """Aborted workflow_status should route to END."""
        state = make_execution_state(
            execution_plan=make_plan(num_batches=1),
            current_batch_index=0,
            developer_status=DeveloperStatus.BLOCKED,
            workflow_status="aborted",
            human_approved=True,
        )

        route = route_blocker_resolution(state)
        assert route == "__end__"


class TestFixInstructionResolution:
    """Tests for fix instruction (retry) blocker resolution."""

    @pytest.mark.parametrize(
        "blocker_resolution,description",
        [
            ("pip install pytest && pytest", "Fix instruction with command"),
            ("", "Empty fix instruction (simple retry)"),
        ],
    )
    async def test_fix_instruction_clears_blocker(
        self,
        blocker_resolution: str,
        description: str,
    ) -> None:
        """Test that fix instructions (both with commands and empty) clear the blocker."""
        blocker = make_blocker(
            step_id="step-1",
            step_description="Test step 1",
            error_message="pytest not found" if blocker_resolution else "Transient error",
        )

        state = make_execution_state(
            execution_plan=make_plan(num_batches=1),
            current_batch_index=0,
            developer_status=DeveloperStatus.BLOCKED,
            current_blocker=blocker,
            blocker_resolution=blocker_resolution,
            human_approved=True,
        )

        result = await blocker_resolution_node(state)

        # Blocker should be cleared so Developer can retry
        assert result["current_blocker"] is None
        assert result["blocker_resolution"] is None
        # Workflow should NOT be aborted
        assert "workflow_status" not in result

    async def test_fix_instruction_routes_to_developer(self) -> None:
        """After fix instruction, routing should continue to developer."""
        state = make_execution_state(
            execution_plan=make_plan(num_batches=1),
            current_batch_index=0,
            developer_status=DeveloperStatus.EXECUTING,
            current_blocker=None,  # Cleared by fix
            workflow_status="running",
            human_approved=True,
        )

        route = route_blocker_resolution(state)
        assert route == "developer"


class TestBlockerWithNoBlocker:
    """Tests for edge case when blocker_resolution_node is called without a blocker."""

    async def test_no_blocker_returns_empty(self) -> None:
        """Calling with no current_blocker should return empty dict."""
        state = make_execution_state(
            execution_plan=make_plan(num_batches=1),
            current_batch_index=0,
            developer_status=DeveloperStatus.BLOCKED,
            current_blocker=None,
            blocker_resolution="skip",
            human_approved=True,
        )

        result = await blocker_resolution_node(state)

        # Should return empty dict (nothing to do)
        assert result == {}


class TestBlockerWithDependencies:
    """Tests for blocker handling with step dependencies."""

    async def test_skip_with_dependencies_in_plan(self) -> None:
        """Skip resolution should record the skip and cascade to dependents."""
        step1 = make_step(id="step-1", description="Base step")
        step2 = make_step(id="step-2", description="Dependent step", depends_on=("step-1",))
        step3 = make_step(id="step-3", description="Independent step")

        batch = make_batch(batch_number=1, steps=(step1, step2, step3))
        plan = make_plan(batches=(batch,))

        blocker = make_blocker(
            step_id="step-1",
            step_description="Base step",
            error_message="Command failed",
        )

        state = make_execution_state(
            execution_plan=plan,
            current_batch_index=0,
            developer_status=DeveloperStatus.BLOCKED,
            current_blocker=blocker,
            blocker_resolution="skip",
            human_approved=True,
        )

        result = await blocker_resolution_node(state)

        # step-1 should be skipped (direct)
        assert_step_skipped(result, "step-1")
        # step-2 should cascade skip (depends on step-1)
        assert_step_skipped(result, "step-2")
        # step-3 is independent - should NOT be in skipped_step_ids result
        # (it's not skipped by this operation)
        skipped = result.get("skipped_step_ids", set())
        assert "step-3" not in skipped
