"""Tests for workflow state models."""

import pytest
from datetime import datetime, UTC

from amelia.server.models.state import (
    WorkflowStatus,
    validate_transition,
    InvalidStateTransitionError,
    ServerExecutionState,
)


class TestStateTransitions:
    """Tests for state machine transitions."""

    def test_pending_can_go_to_in_progress(self):
        """pending -> in_progress is valid."""
        validate_transition("pending", "in_progress")  # Should not raise

    def test_pending_can_go_to_cancelled(self):
        """pending -> cancelled is valid."""
        validate_transition("pending", "cancelled")

    def test_pending_cannot_go_to_completed(self):
        """pending -> completed is invalid (must go through in_progress)."""
        with pytest.raises(InvalidStateTransitionError) as exc:
            validate_transition("pending", "completed")

        assert exc.value.current == "pending"
        assert exc.value.target == "completed"

    def test_in_progress_can_go_to_blocked(self):
        """in_progress -> blocked is valid (awaiting approval)."""
        validate_transition("in_progress", "blocked")

    def test_in_progress_can_go_to_completed(self):
        """in_progress -> completed is valid."""
        validate_transition("in_progress", "completed")

    def test_in_progress_can_go_to_failed(self):
        """in_progress -> failed is valid."""
        validate_transition("in_progress", "failed")

    def test_blocked_can_go_to_in_progress(self):
        """blocked -> in_progress is valid (approval granted)."""
        validate_transition("blocked", "in_progress")

    def test_blocked_can_go_to_failed(self):
        """blocked -> failed is valid (approval rejected)."""
        validate_transition("blocked", "failed")

    def test_completed_is_terminal(self):
        """completed is terminal - cannot transition."""
        for target in ["pending", "in_progress", "blocked", "failed", "cancelled"]:
            with pytest.raises(InvalidStateTransitionError):
                validate_transition("completed", target)

    def test_failed_is_terminal(self):
        """failed is terminal - cannot transition."""
        for target in ["pending", "in_progress", "blocked", "completed", "cancelled"]:
            with pytest.raises(InvalidStateTransitionError):
                validate_transition("failed", target)

    def test_cancelled_is_terminal(self):
        """cancelled is terminal - cannot transition."""
        for target in ["pending", "in_progress", "blocked", "completed", "failed"]:
            with pytest.raises(InvalidStateTransitionError):
                validate_transition("cancelled", target)

    def test_same_state_transition_invalid(self):
        """Cannot transition to same state."""
        with pytest.raises(InvalidStateTransitionError):
            validate_transition("in_progress", "in_progress")


class TestServerExecutionState:
    """Tests for ServerExecutionState model."""

    def test_create_with_required_fields(self):
        """ServerExecutionState requires id, issue_id, worktree fields."""
        state = ServerExecutionState(
            id="wf-123",
            issue_id="ISSUE-456",
            worktree_path="/path/to/repo",
            worktree_name="main",
        )

        assert state.id == "wf-123"
        assert state.issue_id == "ISSUE-456"
        assert state.worktree_path == "/path/to/repo"
        assert state.worktree_name == "main"

    def test_default_status_is_pending(self):
        """Default workflow status is pending."""
        state = ServerExecutionState(
            id="wf-123",
            issue_id="ISSUE-456",
            worktree_path="/path/to/repo",
            worktree_name="main",
        )

        assert state.workflow_status == "pending"

    def test_timestamps_default_none(self):
        """Timestamps default to None."""
        state = ServerExecutionState(
            id="wf-123",
            issue_id="ISSUE-456",
            worktree_path="/path/to/repo",
            worktree_name="main",
        )

        assert state.started_at is None
        assert state.completed_at is None

    def test_stage_timestamps_default_empty(self):
        """Stage timestamps default to empty dict."""
        state = ServerExecutionState(
            id="wf-123",
            issue_id="ISSUE-456",
            worktree_path="/path/to/repo",
            worktree_name="main",
        )

        assert state.stage_timestamps == {}

    def test_serialization_to_json(self):
        """State can be serialized to JSON."""
        state = ServerExecutionState(
            id="wf-123",
            issue_id="ISSUE-456",
            worktree_path="/path/to/repo",
            worktree_name="main",
            workflow_status="in_progress",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
        )

        json_str = state.model_dump_json()
        assert "wf-123" in json_str
        assert "in_progress" in json_str

    def test_deserialization_from_json(self):
        """State can be deserialized from JSON."""
        json_str = '''
        {
            "id": "wf-123",
            "issue_id": "ISSUE-456",
            "worktree_path": "/path/to/repo",
            "worktree_name": "main",
            "workflow_status": "blocked"
        }
        '''

        state = ServerExecutionState.model_validate_json(json_str)
        assert state.id == "wf-123"
        assert state.workflow_status == "blocked"
