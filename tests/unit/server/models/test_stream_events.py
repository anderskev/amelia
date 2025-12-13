# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Tests for stream event models."""

from datetime import UTC, datetime

import pytest

from amelia.core.types import StreamEventType
from amelia.server.models.events import EventType, StreamEventPayload


class TestStreamEventPayload:
    """Tests for StreamEventPayload model."""

    def test_create_payload_with_all_fields(self) -> None:
        """StreamEventPayload can be created with all fields."""
        timestamp = datetime.now(UTC)
        payload = StreamEventPayload(
            subtype=StreamEventType.CLAUDE_TOOL_CALL,
            content="calling tool",
            agent="developer",
            workflow_id="wf-123",
            timestamp=timestamp,
            tool_name="read_file",
            tool_input={"path": "/foo/bar.py"},
        )

        assert payload.subtype == StreamEventType.CLAUDE_TOOL_CALL
        assert payload.content == "calling tool"
        assert payload.agent == "developer"
        assert payload.workflow_id == "wf-123"
        assert payload.timestamp == timestamp
        assert payload.tool_name == "read_file"
        assert payload.tool_input == {"path": "/foo/bar.py"}

    def test_create_payload_minimal_fields(self) -> None:
        """StreamEventPayload can be created with minimal required fields."""
        timestamp = datetime.now(UTC)
        payload = StreamEventPayload(
            subtype=StreamEventType.AGENT_OUTPUT,
            agent="architect",
            workflow_id="wf-456",
            timestamp=timestamp,
        )

        assert payload.subtype == StreamEventType.AGENT_OUTPUT
        assert payload.content is None
        assert payload.agent == "architect"
        assert payload.workflow_id == "wf-456"
        assert payload.timestamp == timestamp
        assert payload.tool_name is None
        assert payload.tool_input is None

    def test_payload_serialization_json_mode(self) -> None:
        """StreamEventPayload serializes datetime correctly in json mode."""
        timestamp = datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC)
        payload = StreamEventPayload(
            subtype=StreamEventType.CLAUDE_THINKING,
            content="analyzing requirements",
            agent="reviewer",
            workflow_id="wf-789",
            timestamp=timestamp,
        )

        data = payload.model_dump(mode="json")

        assert data["subtype"] == "claude_thinking"
        assert data["content"] == "analyzing requirements"
        assert data["agent"] == "reviewer"
        assert data["workflow_id"] == "wf-789"
        # Datetime should be serialized as ISO string in json mode
        assert isinstance(data["timestamp"], str)
        assert "2025-01-15T10:30:00" in data["timestamp"]

    @pytest.mark.parametrize(
        "subtype",
        [
            StreamEventType.CLAUDE_THINKING,
            StreamEventType.CLAUDE_TOOL_CALL,
            StreamEventType.CLAUDE_TOOL_RESULT,
            StreamEventType.AGENT_OUTPUT,
        ],
        ids=["thinking", "tool_call", "tool_result", "agent_output"],
    )
    def test_all_stream_event_types_valid(self, subtype: StreamEventType) -> None:
        """All StreamEventType values are valid for StreamEventPayload."""
        payload = StreamEventPayload(
            subtype=subtype,
            agent="developer",
            workflow_id="wf-test",
            timestamp=datetime.now(UTC),
        )

        assert payload.subtype == subtype


class TestEventTypeStream:
    """Tests for STREAM EventType."""

    def test_stream_event_type_exists(self) -> None:
        """STREAM event type exists in EventType enum."""
        assert hasattr(EventType, "STREAM")
        assert EventType.STREAM == "stream"

    def test_stream_is_distinct_from_other_types(self) -> None:
        """STREAM is a distinct event type."""
        # Ensure STREAM is not the same as other event types
        assert EventType.STREAM != EventType.WORKFLOW_STARTED
        assert EventType.STREAM != EventType.AGENT_MESSAGE
        assert EventType.STREAM != EventType.SYSTEM_ERROR
