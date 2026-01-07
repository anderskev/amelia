"""Tests for event models."""

import pytest
from amelia.server.models.events import EventLevel, EventType, get_event_level


class TestEventLevel:
    """Tests for EventLevel enum and classification."""

    def test_event_level_values(self) -> None:
        """EventLevel has info, debug, trace values."""
        assert EventLevel.INFO == "info"
        assert EventLevel.DEBUG == "debug"
        assert EventLevel.TRACE == "trace"

    @pytest.mark.parametrize(
        "event_type,expected_level",
        [
            # INFO level - workflow lifecycle
            (EventType.WORKFLOW_STARTED, EventLevel.INFO),
            (EventType.WORKFLOW_COMPLETED, EventLevel.INFO),
            (EventType.WORKFLOW_FAILED, EventLevel.INFO),
            (EventType.WORKFLOW_CANCELLED, EventLevel.INFO),
            # INFO level - stages
            (EventType.STAGE_STARTED, EventLevel.INFO),
            (EventType.STAGE_COMPLETED, EventLevel.INFO),
            # INFO level - approvals
            (EventType.APPROVAL_REQUIRED, EventLevel.INFO),
            (EventType.APPROVAL_GRANTED, EventLevel.INFO),
            (EventType.APPROVAL_REJECTED, EventLevel.INFO),
            # INFO level - review completion
            (EventType.REVIEW_COMPLETED, EventLevel.INFO),
            # DEBUG level - tasks
            (EventType.TASK_STARTED, EventLevel.DEBUG),
            (EventType.TASK_COMPLETED, EventLevel.DEBUG),
            (EventType.TASK_FAILED, EventLevel.DEBUG),
            # DEBUG level - files
            (EventType.FILE_CREATED, EventLevel.DEBUG),
            (EventType.FILE_MODIFIED, EventLevel.DEBUG),
            (EventType.FILE_DELETED, EventLevel.DEBUG),
            # DEBUG level - other
            (EventType.AGENT_MESSAGE, EventLevel.DEBUG),
            (EventType.REVISION_REQUESTED, EventLevel.DEBUG),
            (EventType.REVIEW_REQUESTED, EventLevel.DEBUG),
            (EventType.SYSTEM_ERROR, EventLevel.DEBUG),
            (EventType.SYSTEM_WARNING, EventLevel.DEBUG),
            # TRACE level - stream events
            (EventType.CLAUDE_THINKING, EventLevel.TRACE),
            (EventType.CLAUDE_TOOL_CALL, EventLevel.TRACE),
            (EventType.CLAUDE_TOOL_RESULT, EventLevel.TRACE),
            (EventType.AGENT_OUTPUT, EventLevel.TRACE),
        ],
    )
    def test_get_event_level(self, event_type: EventType, expected_level: EventLevel) -> None:
        """get_event_level returns correct level for each event type."""
        assert get_event_level(event_type) == expected_level


class TestWorkflowEvent:
    """Tests for WorkflowEvent model."""

    def test_create_event_with_all_fields(self, make_event) -> None:
        """Event can be created with all fields including optional ones."""
        event = make_event(
            agent="developer",
            event_type=EventType.FILE_CREATED,
            message="Created file",
            data={"path": "src/main.py", "lines": 100},
            correlation_id="req-789",
        )

        assert event.id == "event-123"
        assert event.workflow_id == "wf-456"
        assert event.sequence == 1
        assert event.agent == "developer"
        assert event.event_type == EventType.FILE_CREATED
        assert event.data == {"path": "src/main.py", "lines": 100}
        assert event.correlation_id == "req-789"
