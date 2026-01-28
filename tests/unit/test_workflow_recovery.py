"""Tests for workflow recovery and resume functionality."""

from amelia.server.models.state import (
    InvalidStateTransitionError,
    VALID_TRANSITIONS,
    WorkflowStatus,
    validate_transition,
)


class TestValidTransitions:
    """Tests for FAILED -> IN_PROGRESS state transition."""

    def test_valid_transitions_includes_failed_to_in_progress(self) -> None:
        """FAILED -> IN_PROGRESS should be a valid transition for resume."""
        assert WorkflowStatus.IN_PROGRESS in VALID_TRANSITIONS[WorkflowStatus.FAILED]

    def test_failed_to_in_progress_does_not_raise(self) -> None:
        """validate_transition should not raise for FAILED -> IN_PROGRESS."""
        validate_transition(WorkflowStatus.FAILED, WorkflowStatus.IN_PROGRESS)

    def test_failed_to_completed_still_invalid(self) -> None:
        """FAILED -> COMPLETED should remain invalid (only IN_PROGRESS is allowed)."""
        try:
            validate_transition(WorkflowStatus.FAILED, WorkflowStatus.COMPLETED)
            assert False, "Should have raised InvalidStateTransitionError"
        except InvalidStateTransitionError:
            pass
