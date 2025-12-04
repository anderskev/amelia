"""Tests for event models."""

import pytest
from datetime import datetime, UTC

from amelia.server.models.events import EventType, WorkflowEvent


class TestEventType:
    """Tests for EventType enum."""

    def test_event_type_values_are_strings(self):
        """Event type values are lowercase strings."""
        assert EventType.WORKFLOW_STARTED.value == "workflow_started"
        assert EventType.STAGE_COMPLETED.value == "stage_completed"


class TestWorkflowEvent:
    """Tests for WorkflowEvent model."""

    def test_create_event_with_required_fields(self):
        """Event can be created with required fields."""
        event = WorkflowEvent(
            id="event-123",
            workflow_id="wf-456",
            sequence=1,
            timestamp=datetime.now(UTC),
            agent="architect",
            event_type=EventType.STAGE_STARTED,
            message="Starting plan creation",
        )

        assert event.id == "event-123"
        assert event.workflow_id == "wf-456"
        assert event.sequence == 1
        assert event.agent == "architect"
        assert event.event_type == EventType.STAGE_STARTED

    def test_event_optional_fields_default_none(self):
        """Optional fields default to None."""
        event = WorkflowEvent(
            id="event-123",
            workflow_id="wf-456",
            sequence=1,
            timestamp=datetime.now(UTC),
            agent="system",
            event_type=EventType.WORKFLOW_STARTED,
            message="Started",
        )

        assert event.data is None
        assert event.correlation_id is None

    def test_event_with_data_payload(self):
        """Event can include structured data payload."""
        event = WorkflowEvent(
            id="event-123",
            workflow_id="wf-456",
            sequence=1,
            timestamp=datetime.now(UTC),
            agent="developer",
            event_type=EventType.FILE_CREATED,
            message="Created file",
            data={"path": "src/main.py", "lines": 100},
        )

        assert event.data["path"] == "src/main.py"
        assert event.data["lines"] == 100

    def test_event_with_correlation_id(self):
        """Event can include correlation ID for tracing."""
        event = WorkflowEvent(
            id="event-123",
            workflow_id="wf-456",
            sequence=1,
            timestamp=datetime.now(UTC),
            agent="system",
            event_type=EventType.APPROVAL_GRANTED,
            message="Approved",
            correlation_id="req-789",
        )

        assert event.correlation_id == "req-789"

    def test_event_serialization_to_json(self):
        """Event can be serialized to JSON."""
        event = WorkflowEvent(
            id="event-123",
            workflow_id="wf-456",
            sequence=1,
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            agent="system",
            event_type=EventType.WORKFLOW_STARTED,
            message="Started",
        )

        json_str = event.model_dump_json()
        assert "event-123" in json_str
        assert "workflow_started" in json_str

    def test_event_deserialization_from_json(self):
        """Event can be deserialized from JSON."""
        json_str = '''
        {
            "id": "event-123",
            "workflow_id": "wf-456",
            "sequence": 1,
            "timestamp": "2025-01-01T12:00:00",
            "agent": "system",
            "event_type": "workflow_started",
            "message": "Started"
        }
        '''

        event = WorkflowEvent.model_validate_json(json_str)
        assert event.id == "event-123"
        assert event.event_type == EventType.WORKFLOW_STARTED
