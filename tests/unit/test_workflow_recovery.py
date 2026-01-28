"""Tests for workflow recovery and resume functionality."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from amelia.server.models.events import EventType
from amelia.server.models.state import (
    InvalidStateTransitionError,
    VALID_TRANSITIONS,
    WorkflowStatus,
    validate_transition,
)
from amelia.server.orchestrator.service import OrchestratorService


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


@pytest.fixture
def event_bus() -> MagicMock:
    bus = MagicMock()
    bus.emit = MagicMock()
    return bus


@pytest.fixture
def repository() -> AsyncMock:
    repo = AsyncMock()
    repo.find_by_status = AsyncMock(return_value=[])
    repo.set_status = AsyncMock()
    repo.save_event = AsyncMock()
    repo.get_max_event_sequence = AsyncMock(return_value=0)
    return repo


@pytest.fixture
def service(event_bus: MagicMock, repository: AsyncMock) -> OrchestratorService:
    return OrchestratorService(
        event_bus=event_bus,
        repository=repository,
    )


def _make_workflow(
    workflow_id: str,
    status: WorkflowStatus,
    worktree_path: str = "/tmp/test-worktree",
) -> MagicMock:
    """Create a mock ServerExecutionState with the given status."""
    wf = MagicMock()
    wf.id = workflow_id
    wf.issue_id = f"ISSUE-{workflow_id}"
    wf.workflow_status = status
    wf.worktree_path = worktree_path
    return wf


class TestRecoverInterruptedWorkflows:
    """Tests for recover_interrupted_workflows()."""

    async def test_recover_in_progress_marks_failed(
        self,
        service: OrchestratorService,
        repository: AsyncMock,
        event_bus: MagicMock,
    ) -> None:
        """IN_PROGRESS workflow should be marked FAILED with recoverable flag."""
        wf = _make_workflow("wf-1", WorkflowStatus.IN_PROGRESS)
        repository.find_by_status = AsyncMock(
            side_effect=lambda statuses: [wf] if WorkflowStatus.IN_PROGRESS in statuses else []
        )

        await service.recover_interrupted_workflows()

        repository.set_status.assert_called_once_with(
            "wf-1",
            WorkflowStatus.FAILED,
            failure_reason="Server restarted while workflow was running",
        )
        # Check WORKFLOW_FAILED event was emitted with recoverable=True
        repository.save_event.assert_called()
        saved_event = repository.save_event.call_args[0][0]
        assert saved_event.event_type == EventType.WORKFLOW_FAILED
        assert saved_event.data["recoverable"] is True

    async def test_recover_blocked_restores_approval(
        self,
        service: OrchestratorService,
        repository: AsyncMock,
        event_bus: MagicMock,
    ) -> None:
        """BLOCKED workflow should stay BLOCKED with APPROVAL_REQUIRED re-emitted."""
        wf = _make_workflow("wf-2", WorkflowStatus.BLOCKED)
        repository.find_by_status = AsyncMock(
            side_effect=lambda statuses: [wf] if WorkflowStatus.BLOCKED in statuses else []
        )

        await service.recover_interrupted_workflows()

        # Status should NOT change — no set_status call for BLOCKED
        repository.set_status.assert_not_called()
        # APPROVAL_REQUIRED event should be emitted
        repository.save_event.assert_called()
        saved_event = repository.save_event.call_args[0][0]
        assert saved_event.event_type == EventType.APPROVAL_REQUIRED

    async def test_recover_pending_unchanged(
        self,
        service: OrchestratorService,
        repository: AsyncMock,
    ) -> None:
        """PENDING workflows should not be touched."""
        repository.find_by_status = AsyncMock(return_value=[])

        await service.recover_interrupted_workflows()

        repository.set_status.assert_not_called()

    async def test_recover_no_active_workflows(
        self,
        service: OrchestratorService,
        repository: AsyncMock,
    ) -> None:
        """With no interrupted workflows, just log summary."""
        repository.find_by_status = AsyncMock(return_value=[])

        await service.recover_interrupted_workflows()

        repository.set_status.assert_not_called()
        repository.save_event.assert_not_called()
