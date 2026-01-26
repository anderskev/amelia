"""Unit tests for replan state transition."""
import pytest

from amelia.server.models.state import WorkflowStatus, validate_transition, InvalidStateTransitionError


class TestReplanTransition:
    """Tests for BLOCKED -> PLANNING transition."""

    def test_blocked_to_planning_is_valid(self) -> None:
        """BLOCKED -> PLANNING should be a valid transition for replan."""
        # Should not raise
        validate_transition(WorkflowStatus.BLOCKED, WorkflowStatus.PLANNING)

    def test_completed_to_planning_is_invalid(self) -> None:
        """Terminal states cannot transition to PLANNING."""
        with pytest.raises(InvalidStateTransitionError):
            validate_transition(WorkflowStatus.COMPLETED, WorkflowStatus.PLANNING)

    def test_failed_to_planning_is_invalid(self) -> None:
        """Terminal states cannot transition to PLANNING."""
        with pytest.raises(InvalidStateTransitionError):
            validate_transition(WorkflowStatus.FAILED, WorkflowStatus.PLANNING)
