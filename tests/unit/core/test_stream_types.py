# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Tests for streaming types."""

from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from amelia.core.types import StreamEmitter, StreamEvent, StreamEventType


class TestStreamEventType:
    """Test StreamEventType enum."""

    def test_has_claude_thinking(self) -> None:
        """StreamEventType should have CLAUDE_THINKING."""
        assert StreamEventType.CLAUDE_THINKING.value == "claude_thinking"

    def test_has_claude_tool_call(self) -> None:
        """StreamEventType should have CLAUDE_TOOL_CALL."""
        assert StreamEventType.CLAUDE_TOOL_CALL.value == "claude_tool_call"

    def test_has_claude_tool_result(self) -> None:
        """StreamEventType should have CLAUDE_TOOL_RESULT."""
        assert StreamEventType.CLAUDE_TOOL_RESULT.value == "claude_tool_result"

    def test_has_agent_output(self) -> None:
        """StreamEventType should have AGENT_OUTPUT."""
        assert StreamEventType.AGENT_OUTPUT.value == "agent_output"

    def test_all_values(self) -> None:
        """StreamEventType should have exactly 4 values."""
        expected = {
            "claude_thinking",
            "claude_tool_call",
            "claude_tool_result",
            "agent_output",
        }
        actual = {e.value for e in StreamEventType}
        assert actual == expected


class TestStreamEvent:
    """Test StreamEvent Pydantic model."""

    def test_valid_event_all_fields(self) -> None:
        """StreamEvent should validate with all fields provided."""
        now = datetime.now(UTC)
        event = StreamEvent(
            type=StreamEventType.CLAUDE_TOOL_CALL,
            content="Calling read_file tool",
            timestamp=now,
            agent="developer",
            workflow_id="workflow-123",
            tool_name="read_file",
            tool_input={"path": "/tmp/test.py"},
        )
        assert event.type == StreamEventType.CLAUDE_TOOL_CALL
        assert event.content == "Calling read_file tool"
        assert event.timestamp == now
        assert event.agent == "developer"
        assert event.workflow_id == "workflow-123"
        assert event.tool_name == "read_file"
        assert event.tool_input == {"path": "/tmp/test.py"}

    def test_valid_event_minimal_fields(self) -> None:
        """StreamEvent should validate with only required fields."""
        now = datetime.now(UTC)
        event = StreamEvent(
            type=StreamEventType.CLAUDE_THINKING,
            timestamp=now,
            agent="architect",
            workflow_id="workflow-456",
        )
        assert event.type == StreamEventType.CLAUDE_THINKING
        assert event.content is None
        assert event.timestamp == now
        assert event.agent == "architect"
        assert event.workflow_id == "workflow-456"
        assert event.tool_name is None
        assert event.tool_input is None

    def test_agent_output_event(self) -> None:
        """StreamEvent should work for AGENT_OUTPUT type."""
        now = datetime.now(UTC)
        event = StreamEvent(
            type=StreamEventType.AGENT_OUTPUT,
            content="Plan generated successfully",
            timestamp=now,
            agent="architect",
            workflow_id="workflow-789",
        )
        assert event.type == StreamEventType.AGENT_OUTPUT
        assert event.content == "Plan generated successfully"
        assert event.agent == "architect"

    def test_tool_result_event(self) -> None:
        """StreamEvent should work for CLAUDE_TOOL_RESULT type."""
        now = datetime.now(UTC)
        event = StreamEvent(
            type=StreamEventType.CLAUDE_TOOL_RESULT,
            content="File contents: ...",
            timestamp=now,
            agent="reviewer",
            workflow_id="workflow-abc",
            tool_name="read_file",
        )
        assert event.type == StreamEventType.CLAUDE_TOOL_RESULT
        assert event.content == "File contents: ..."
        assert event.tool_name == "read_file"

    def test_invalid_type_fails_validation(self) -> None:
        """StreamEvent should reject invalid event type."""
        now = datetime.now(UTC)
        with pytest.raises(ValidationError) as exc_info:
            StreamEvent(
                type="invalid_type",  # type: ignore
                timestamp=now,
                agent="developer",
                workflow_id="workflow-123",
            )
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("type" in str(e) for e in errors)

    def test_missing_required_field_fails(self) -> None:
        """StreamEvent should reject missing required fields."""
        now = datetime.now(UTC)
        with pytest.raises(ValidationError):
            StreamEvent(  # type: ignore
                type=StreamEventType.CLAUDE_THINKING,
                timestamp=now,
                # Missing agent and workflow_id
            )

    def test_tool_input_accepts_dict(self) -> None:
        """StreamEvent tool_input should accept dict with Any values."""
        now = datetime.now(UTC)
        tool_input: dict[str, Any] = {
            "path": "/tmp/test.py",
            "count": 42,
            "flags": ["verbose", "debug"],
            "config": {"key": "value"},
        }
        event = StreamEvent(
            type=StreamEventType.CLAUDE_TOOL_CALL,
            timestamp=now,
            agent="developer",
            workflow_id="workflow-123",
            tool_input=tool_input,
        )
        assert event.tool_input == tool_input
        assert isinstance(event.tool_input, dict)


class TestStreamEmitter:
    """Test StreamEmitter type alias."""

    async def test_stream_emitter_is_callable(self) -> None:
        """StreamEmitter should be a callable that accepts StreamEvent and returns None."""
        # This test verifies the type annotation works correctly
        async def my_emitter(event: StreamEvent) -> None:
            """Example emitter implementation."""
            assert event.agent in ["architect", "developer", "reviewer"]

        emitter: StreamEmitter = my_emitter

        now = datetime.now(UTC)
        event = StreamEvent(
            type=StreamEventType.AGENT_OUTPUT,
            timestamp=now,
            agent="architect",
            workflow_id="workflow-test",
        )

        await emitter(event)

    async def test_stream_emitter_type_signature(self) -> None:
        """StreamEmitter should accept async callable with correct signature."""
        events_received: list[StreamEvent] = []

        async def collector(event: StreamEvent) -> None:
            """Collector emitter for testing."""
            events_received.append(event)

        emitter: StreamEmitter = collector

        now = datetime.now(UTC)
        event1 = StreamEvent(
            type=StreamEventType.CLAUDE_THINKING,
            content="Analyzing code...",
            timestamp=now,
            agent="reviewer",
            workflow_id="workflow-collect",
        )
        event2 = StreamEvent(
            type=StreamEventType.AGENT_OUTPUT,
            content="Review complete",
            timestamp=now,
            agent="reviewer",
            workflow_id="workflow-collect",
        )

        await emitter(event1)
        await emitter(event2)

        assert len(events_received) == 2
        assert events_received[0].type == StreamEventType.CLAUDE_THINKING
        assert events_received[1].type == StreamEventType.AGENT_OUTPUT
