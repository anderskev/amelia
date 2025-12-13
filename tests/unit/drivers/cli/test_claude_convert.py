# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Tests for convert_to_stream_event() helper in ClaudeCliDriver."""

from datetime import UTC, datetime

from amelia.core.types import StreamEvent, StreamEventType
from amelia.drivers.cli.claude import ClaudeStreamEvent, convert_to_stream_event


class TestConvertToStreamEvent:
    """Tests for convert_to_stream_event() function."""

    def test_assistant_event_converts_to_claude_thinking(self):
        """Assistant event should convert to CLAUDE_THINKING."""
        event = ClaudeStreamEvent(type="assistant", content="Let me analyze this...")

        result = convert_to_stream_event(
            event=event,
            agent="developer",
            workflow_id="wf-123"
        )

        assert result is not None
        assert isinstance(result, StreamEvent)
        assert result.type == StreamEventType.CLAUDE_THINKING
        assert result.content == "Let me analyze this..."
        assert result.agent == "developer"
        assert result.workflow_id == "wf-123"
        assert result.tool_name is None
        assert result.tool_input is None
        assert isinstance(result.timestamp, datetime)
        assert result.timestamp.tzinfo == UTC

    def test_tool_use_event_converts_to_claude_tool_call(self):
        """Tool_use event should convert to CLAUDE_TOOL_CALL."""
        event = ClaudeStreamEvent(
            type="tool_use",
            tool_name="write_file",
            tool_input={"file_path": "/tmp/test.py", "content": "# test"}
        )

        result = convert_to_stream_event(
            event=event,
            agent="architect",
            workflow_id="wf-456"
        )

        assert result is not None
        assert isinstance(result, StreamEvent)
        assert result.type == StreamEventType.CLAUDE_TOOL_CALL
        assert result.content is None
        assert result.agent == "architect"
        assert result.workflow_id == "wf-456"
        assert result.tool_name == "write_file"
        assert result.tool_input == {"file_path": "/tmp/test.py", "content": "# test"}
        assert isinstance(result.timestamp, datetime)
        assert result.timestamp.tzinfo == UTC

    def test_result_event_converts_to_claude_tool_result(self):
        """Result event should convert to CLAUDE_TOOL_RESULT."""
        event = ClaudeStreamEvent(type="result", session_id="sess_001")

        result = convert_to_stream_event(
            event=event,
            agent="reviewer",
            workflow_id="wf-789"
        )

        assert result is not None
        assert isinstance(result, StreamEvent)
        assert result.type == StreamEventType.CLAUDE_TOOL_RESULT
        assert result.content is None
        assert result.agent == "reviewer"
        assert result.workflow_id == "wf-789"
        assert result.tool_name is None
        assert result.tool_input is None
        assert isinstance(result.timestamp, datetime)
        assert result.timestamp.tzinfo == UTC

    def test_error_event_returns_none(self):
        """Error event should return None (skipped)."""
        event = ClaudeStreamEvent(type="error", content="Something went wrong")

        result = convert_to_stream_event(
            event=event,
            agent="developer",
            workflow_id="wf-123"
        )

        assert result is None

    def test_system_event_returns_none(self):
        """System event should return None (skipped)."""
        event = ClaudeStreamEvent(type="system", content="System message")

        result = convert_to_stream_event(
            event=event,
            agent="developer",
            workflow_id="wf-123"
        )

        assert result is None

    def test_all_fields_populated_correctly(self):
        """All fields should be populated correctly from source event."""
        event = ClaudeStreamEvent(
            type="tool_use",
            tool_name="run_shell_command",
            tool_input={"command": "pytest"}
        )

        before = datetime.now(UTC)
        result = convert_to_stream_event(
            event=event,
            agent="developer",
            workflow_id="wf-complete-123"
        )
        after = datetime.now(UTC)

        assert result is not None
        # Verify all required fields
        assert result.type == StreamEventType.CLAUDE_TOOL_CALL
        assert result.agent == "developer"
        assert result.workflow_id == "wf-complete-123"
        assert result.tool_name == "run_shell_command"
        assert result.tool_input == {"command": "pytest"}

        # Verify timestamp is within reasonable range
        assert before <= result.timestamp <= after
        assert result.timestamp.tzinfo == UTC

    def test_assistant_event_with_empty_content(self):
        """Assistant event with empty content should still convert."""
        event = ClaudeStreamEvent(type="assistant", content="")

        result = convert_to_stream_event(
            event=event,
            agent="developer",
            workflow_id="wf-123"
        )

        assert result is not None
        assert result.type == StreamEventType.CLAUDE_THINKING
        assert result.content == ""

    def test_assistant_event_with_none_content(self):
        """Assistant event with None content should still convert."""
        event = ClaudeStreamEvent(type="assistant", content=None)

        result = convert_to_stream_event(
            event=event,
            agent="developer",
            workflow_id="wf-123"
        )

        assert result is not None
        assert result.type == StreamEventType.CLAUDE_THINKING
        assert result.content is None

    def test_different_agents(self):
        """Should work with different agent names."""
        event = ClaudeStreamEvent(type="assistant", content="Testing")

        for agent in ["developer", "architect", "reviewer"]:
            result = convert_to_stream_event(
                event=event,
                agent=agent,
                workflow_id="wf-123"
            )
            assert result is not None
            assert result.agent == agent

    def test_different_workflow_ids(self):
        """Should preserve different workflow IDs."""
        event = ClaudeStreamEvent(type="assistant", content="Testing")

        workflow_ids = ["wf-1", "workflow-abc-123", "uuid-style-id"]
        for wf_id in workflow_ids:
            result = convert_to_stream_event(
                event=event,
                agent="developer",
                workflow_id=wf_id
            )
            assert result is not None
            assert result.workflow_id == wf_id
