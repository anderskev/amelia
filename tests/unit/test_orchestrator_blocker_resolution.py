# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Tests for orchestrator blocker_resolution_node."""

from collections.abc import Callable
from unittest.mock import AsyncMock, patch

from amelia.core.orchestrator import blocker_resolution_node
from amelia.core.state import BlockerReport, ExecutionState, GitSnapshot


class TestBlockerResolutionNode:
    """Tests for blocker_resolution_node."""

    async def test_skip_resolution_adds_step_to_skipped(
        self,
        mock_execution_state_factory: Callable[..., ExecutionState],
    ) -> None:
        """Skip resolution should add blocked step to skipped_step_ids."""
        blocker = BlockerReport(
            step_id="step-1",
            step_description="Test step",
            blocker_type="command_failed",
            error_message="Command failed",
            attempted_actions=("retry",),
            suggested_resolutions=("skip",),
        )

        state = mock_execution_state_factory(
            current_blocker=blocker,
            blocker_resolution="skip",
            skipped_step_ids=set(),
        )

        result = await blocker_resolution_node(state)

        assert "skipped_step_ids" in result
        assert "step-1" in result["skipped_step_ids"]
        # Should clear the blocker
        assert result.get("current_blocker") is None
        assert result.get("blocker_resolution") is None

    async def test_abort_resolution_sets_workflow_status(
        self,
        mock_execution_state_factory: Callable[..., ExecutionState],
    ) -> None:
        """Abort resolution should set workflow_status to aborted without reverting."""
        blocker = BlockerReport(
            step_id="step-2",
            step_description="Test step",
            blocker_type="validation_failed",
            error_message="Validation failed",
            attempted_actions=(),
            suggested_resolutions=("abort",),
        )

        state = mock_execution_state_factory(
            current_blocker=blocker,
            blocker_resolution="abort",
        )

        result = await blocker_resolution_node(state)

        assert result.get("workflow_status") == "aborted"
        # Should clear the blocker
        assert result.get("current_blocker") is None
        assert result.get("blocker_resolution") is None

    async def test_abort_revert_calls_git_revert(
        self,
        mock_execution_state_factory: Callable[..., ExecutionState],
    ) -> None:
        """Abort with revert should call revert_to_git_snapshot and set status to aborted."""
        blocker = BlockerReport(
            step_id="step-3",
            step_description="Test step",
            blocker_type="unexpected_state",
            error_message="Unexpected state",
            attempted_actions=(),
            suggested_resolutions=("abort_revert",),
        )

        snapshot = GitSnapshot(
            head_commit="abc123",
            dirty_files=(),
            stash_ref=None,
        )

        state = mock_execution_state_factory(
            current_blocker=blocker,
            blocker_resolution="abort_revert",
            git_snapshot_before_batch=snapshot,
        )

        with patch(
            "amelia.core.orchestrator.revert_to_git_snapshot",
            new_callable=AsyncMock,
        ) as mock_revert:
            mock_revert.return_value = None

            result = await blocker_resolution_node(state)

            # Should call revert with the snapshot
            mock_revert.assert_called_once_with(snapshot, None)

            # Should set status to aborted
            assert result.get("workflow_status") == "aborted"

            # Should clear the blocker
            assert result.get("current_blocker") is None
            assert result.get("blocker_resolution") is None

    async def test_fix_instruction_clears_blocker(
        self,
        mock_execution_state_factory: Callable[..., ExecutionState],
    ) -> None:
        """Fix instruction should clear blocker and pass instruction to Developer."""
        blocker = BlockerReport(
            step_id="step-4",
            step_description="Test step",
            blocker_type="needs_judgment",
            error_message="Needs human judgment",
            attempted_actions=(),
            suggested_resolutions=("provide instructions",),
        )

        state = mock_execution_state_factory(
            current_blocker=blocker,
            blocker_resolution="Try using --force flag instead",
        )

        result = await blocker_resolution_node(state)

        # Should clear the blocker (Developer will handle the fix instruction)
        assert result.get("current_blocker") is None
        assert result.get("blocker_resolution") is None

    async def test_empty_resolution_clears_blocker(
        self,
        mock_execution_state_factory: Callable[..., ExecutionState],
    ) -> None:
        """Empty or None resolution should clear blocker (treat as fix attempt)."""
        blocker = BlockerReport(
            step_id="step-5",
            step_description="Test step",
            blocker_type="command_failed",
            error_message="Command failed",
            attempted_actions=(),
            suggested_resolutions=(),
        )

        state = mock_execution_state_factory(
            current_blocker=blocker,
            blocker_resolution=None,
        )

        result = await blocker_resolution_node(state)

        # Should clear the blocker
        assert result.get("current_blocker") is None
        assert result.get("blocker_resolution") is None

    async def test_skip_preserves_existing_skipped_steps(
        self,
        mock_execution_state_factory: Callable[..., ExecutionState],
    ) -> None:
        """Skip should return single-item set; reducer merges with existing."""
        blocker = BlockerReport(
            step_id="step-6",
            step_description="Test step",
            blocker_type="dependency_skipped",
            error_message="Dependency was skipped",
            attempted_actions=(),
            suggested_resolutions=("skip",),
        )

        state = mock_execution_state_factory(
            current_blocker=blocker,
            blocker_resolution="skip",
            skipped_step_ids={"step-1", "step-2"},
        )

        result = await blocker_resolution_node(state)

        assert "skipped_step_ids" in result
        # Node returns single-item set; reducer will merge with existing
        assert result["skipped_step_ids"] == {"step-6"}

    async def test_abort_revert_without_snapshot_still_aborts(
        self,
        mock_execution_state_factory: Callable[..., ExecutionState],
    ) -> None:
        """Abort with revert should still abort even if no snapshot available."""
        blocker = BlockerReport(
            step_id="step-7",
            step_description="Test step",
            blocker_type="command_failed",
            error_message="Command failed",
            attempted_actions=(),
            suggested_resolutions=("abort_revert",),
        )

        state = mock_execution_state_factory(
            current_blocker=blocker,
            blocker_resolution="abort_revert",
            git_snapshot_before_batch=None,
        )

        with patch(
            "amelia.core.orchestrator.revert_to_git_snapshot",
            new_callable=AsyncMock,
        ) as mock_revert:
            mock_revert.return_value = None

            result = await blocker_resolution_node(state)

            # Should NOT call revert if no snapshot
            mock_revert.assert_not_called()

            # Should still set status to aborted
            assert result.get("workflow_status") == "aborted"

            # Should clear the blocker
            assert result.get("current_blocker") is None
            assert result.get("blocker_resolution") is None
