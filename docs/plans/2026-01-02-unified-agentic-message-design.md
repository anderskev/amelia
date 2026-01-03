# Unified AgenticMessage Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Unify driver message types so `execute_agentic()` can join `DriverInterface`, eliminating ~300 lines of duplicated isinstance checks in agents.

**Architecture:** Introduce `AgenticMessage` as the boundary type between drivers and agents. Drivers convert their native SDK types (Claude SDK `Message`, LangChain `BaseMessage`) to `AgenticMessage` internally. Agents receive a single stream type and use `to_stream_event()` for dashboard conversion.

**Tech Stack:** Python 3.12+, Pydantic, pytest, async iterators

---

## Task 1: Define AgenticMessage Types

**Files:**
- Modify: `amelia/drivers/base.py:1-50`
- Test: `tests/unit/drivers/test_agentic_message.py` (create)

**Step 1: Write the failing test**

Create test file:

```python
# tests/unit/drivers/test_agentic_message.py
"""Tests for AgenticMessage unified driver message type."""

import pytest
from datetime import datetime, UTC

from amelia.drivers.base import AgenticMessage, AgenticMessageType


class TestAgenticMessageType:
    """Test AgenticMessageType enum values."""

    def test_has_thinking_type(self) -> None:
        assert AgenticMessageType.THINKING == "thinking"

    def test_has_tool_call_type(self) -> None:
        assert AgenticMessageType.TOOL_CALL == "tool_call"

    def test_has_tool_result_type(self) -> None:
        assert AgenticMessageType.TOOL_RESULT == "tool_result"

    def test_has_result_type(self) -> None:
        assert AgenticMessageType.RESULT == "result"


class TestAgenticMessage:
    """Test AgenticMessage model."""

    def test_creates_thinking_message(self) -> None:
        msg = AgenticMessage(
            type=AgenticMessageType.THINKING,
            content="Let me analyze this problem...",
        )
        assert msg.type == AgenticMessageType.THINKING
        assert msg.content == "Let me analyze this problem..."
        assert msg.tool_name is None
        assert msg.is_error is False

    def test_creates_tool_call_message(self) -> None:
        msg = AgenticMessage(
            type=AgenticMessageType.TOOL_CALL,
            tool_name="read_file",
            tool_input={"path": "/test.py"},
            tool_call_id="call_123",
        )
        assert msg.type == AgenticMessageType.TOOL_CALL
        assert msg.tool_name == "read_file"
        assert msg.tool_input == {"path": "/test.py"}
        assert msg.tool_call_id == "call_123"

    def test_creates_tool_result_message(self) -> None:
        msg = AgenticMessage(
            type=AgenticMessageType.TOOL_RESULT,
            tool_name="read_file",
            tool_output="file contents here",
            tool_call_id="call_123",
            is_error=False,
        )
        assert msg.type == AgenticMessageType.TOOL_RESULT
        assert msg.tool_output == "file contents here"
        assert msg.is_error is False

    def test_creates_error_result_message(self) -> None:
        msg = AgenticMessage(
            type=AgenticMessageType.TOOL_RESULT,
            tool_name="read_file",
            tool_output="File not found",
            tool_call_id="call_123",
            is_error=True,
        )
        assert msg.is_error is True

    def test_creates_result_message(self) -> None:
        msg = AgenticMessage(
            type=AgenticMessageType.RESULT,
            content="Task completed successfully",
            session_id="session_abc",
        )
        assert msg.type == AgenticMessageType.RESULT
        assert msg.content == "Task completed successfully"
        assert msg.session_id == "session_abc"

    def test_is_error_defaults_to_false(self) -> None:
        msg = AgenticMessage(type=AgenticMessageType.THINKING, content="test")
        assert msg.is_error is False
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/drivers/test_agentic_message.py -v`
Expected: FAIL with "cannot import name 'AgenticMessage'"

**Step 3: Write minimal implementation**

Add to `amelia/drivers/base.py` after existing imports:

```python
from enum import StrEnum

class AgenticMessageType(StrEnum):
    """Types of messages yielded during agentic execution."""

    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    RESULT = "result"


class AgenticMessage(BaseModel):
    """Unified message type for agentic execution across all drivers.

    This provides a common abstraction over driver-specific message types:
    - ClaudeCliDriver: claude_agent_sdk.types.Message
    - ApiDriver: langchain_core.messages.BaseMessage
    """

    type: AgenticMessageType
    content: str | None = None
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_output: str | None = None
    tool_call_id: str | None = None
    session_id: str | None = None
    is_error: bool = False
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/drivers/test_agentic_message.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/drivers/base.py tests/unit/drivers/test_agentic_message.py
git commit -m "feat(drivers): add AgenticMessage unified type

Define AgenticMessageType enum and AgenticMessage model as the unified
abstraction for agentic execution messages across all drivers.

Part of #198"
```

---

## Task 2: Add is_error to StreamEvent

**Files:**
- Modify: `amelia/core/types.py:143-164`
- Test: `tests/unit/core/test_types.py` (find existing or create)

**Step 1: Write the failing test**

Add to existing test file or create:

```python
# tests/unit/core/test_stream_event.py
"""Tests for StreamEvent with is_error field."""

from datetime import datetime, UTC

from amelia.core.types import StreamEvent, StreamEventType


class TestStreamEventIsError:
    """Test StreamEvent is_error field."""

    def test_is_error_defaults_to_false(self) -> None:
        event = StreamEvent(
            type=StreamEventType.CLAUDE_TOOL_RESULT,
            content="result",
            timestamp=datetime.now(UTC),
            agent="developer",
            workflow_id="wf_123",
        )
        assert event.is_error is False

    def test_is_error_can_be_true(self) -> None:
        event = StreamEvent(
            type=StreamEventType.CLAUDE_TOOL_RESULT,
            content="Error: file not found",
            timestamp=datetime.now(UTC),
            agent="developer",
            workflow_id="wf_123",
            is_error=True,
        )
        assert event.is_error is True
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/core/test_stream_event.py -v`
Expected: FAIL with "unexpected keyword argument 'is_error'"

**Step 3: Write minimal implementation**

Add to `StreamEvent` in `amelia/core/types.py`:

```python
class StreamEvent(BaseModel):
    """Event emitted during agent execution for streaming to dashboard."""

    type: StreamEventType
    content: str | None = None
    timestamp: datetime
    agent: str
    workflow_id: str
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    is_error: bool = False  # Add this line
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/core/test_stream_event.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/types.py tests/unit/core/test_stream_event.py
git commit -m "feat(types): add is_error field to StreamEvent

Allows dashboard to differentiate error results from successful ones.

Part of #198"
```

---

## Task 3: Add to_stream_event() Method

**Files:**
- Modify: `amelia/drivers/base.py`
- Test: `tests/unit/drivers/test_agentic_message.py`

**Step 1: Write the failing test**

Add to `tests/unit/drivers/test_agentic_message.py`:

```python
from amelia.core.types import StreamEvent, StreamEventType


class TestAgenticMessageToStreamEvent:
    """Test AgenticMessage.to_stream_event() conversion."""

    def test_thinking_converts_to_claude_thinking(self) -> None:
        msg = AgenticMessage(
            type=AgenticMessageType.THINKING,
            content="Analyzing the problem...",
        )
        event = msg.to_stream_event(agent="developer", workflow_id="wf_123")

        assert event.type == StreamEventType.CLAUDE_THINKING
        assert event.content == "Analyzing the problem..."
        assert event.agent == "developer"
        assert event.workflow_id == "wf_123"
        assert event.is_error is False

    def test_tool_call_converts_to_claude_tool_call(self) -> None:
        msg = AgenticMessage(
            type=AgenticMessageType.TOOL_CALL,
            tool_name="read_file",
            tool_input={"path": "/test.py"},
        )
        event = msg.to_stream_event(agent="developer", workflow_id="wf_123")

        assert event.type == StreamEventType.CLAUDE_TOOL_CALL
        assert event.tool_name == "read_file"
        assert event.tool_input == {"path": "/test.py"}

    def test_tool_result_converts_to_claude_tool_result(self) -> None:
        msg = AgenticMessage(
            type=AgenticMessageType.TOOL_RESULT,
            tool_name="read_file",
            tool_output="file contents",
            is_error=False,
        )
        event = msg.to_stream_event(agent="developer", workflow_id="wf_123")

        assert event.type == StreamEventType.CLAUDE_TOOL_RESULT
        assert event.content == "file contents"
        assert event.is_error is False

    def test_error_result_preserves_is_error(self) -> None:
        msg = AgenticMessage(
            type=AgenticMessageType.TOOL_RESULT,
            tool_name="bash",
            tool_output="Command failed",
            is_error=True,
        )
        event = msg.to_stream_event(agent="developer", workflow_id="wf_123")

        assert event.type == StreamEventType.CLAUDE_TOOL_RESULT
        assert event.is_error is True

    def test_result_converts_to_agent_output(self) -> None:
        msg = AgenticMessage(
            type=AgenticMessageType.RESULT,
            content="Task completed",
            session_id="sess_abc",
        )
        event = msg.to_stream_event(agent="developer", workflow_id="wf_123")

        assert event.type == StreamEventType.AGENT_OUTPUT
        assert event.content == "Task completed"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/drivers/test_agentic_message.py::TestAgenticMessageToStreamEvent -v`
Expected: FAIL with "AgenticMessage has no attribute 'to_stream_event'"

**Step 3: Write minimal implementation**

Add method to `AgenticMessage` in `amelia/drivers/base.py`:

```python
from datetime import datetime, UTC
from amelia.core.types import StreamEvent, StreamEventType

class AgenticMessage(BaseModel):
    # ... existing fields ...

    def to_stream_event(self, agent: str, workflow_id: str) -> StreamEvent:
        """Convert to StreamEvent for dashboard consumption."""
        type_mapping = {
            AgenticMessageType.THINKING: StreamEventType.CLAUDE_THINKING,
            AgenticMessageType.TOOL_CALL: StreamEventType.CLAUDE_TOOL_CALL,
            AgenticMessageType.TOOL_RESULT: StreamEventType.CLAUDE_TOOL_RESULT,
            AgenticMessageType.RESULT: StreamEventType.AGENT_OUTPUT,
        }
        return StreamEvent(
            type=type_mapping[self.type],
            content=self.content or self.tool_output,
            timestamp=datetime.now(UTC),
            agent=agent,
            workflow_id=workflow_id,
            tool_name=self.tool_name,
            tool_input=self.tool_input,
            is_error=self.is_error,
        )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/drivers/test_agentic_message.py::TestAgenticMessageToStreamEvent -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/drivers/base.py tests/unit/drivers/test_agentic_message.py
git commit -m "feat(drivers): add to_stream_event() method to AgenticMessage

Provides clean conversion from driver boundary type to dashboard type.

Part of #198"
```

---

## Task 4: Update ClaudeCliDriver.execute_agentic() to Yield AgenticMessage

**Files:**
- Modify: `amelia/drivers/cli/claude.py:430-489`
- Test: `tests/unit/test_claude_driver.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_claude_driver.py`:

```python
from amelia.drivers.base import AgenticMessage, AgenticMessageType


class TestExecuteAgenticYieldsAgenticMessage:
    """Test execute_agentic() yields AgenticMessage types."""

    async def test_yields_thinking_for_text_block(self, driver: ClaudeCliDriver) -> None:
        """TextBlock in AssistantMessage should yield THINKING AgenticMessage."""
        messages = [
            MockAssistantMessage([MockTextBlock("Let me analyze this...")]),
            MockResultMessage(result="Done", session_id="sess_123"),
        ]

        with patch.object(driver, "_query", create_mock_query(messages)):
            results = [msg async for msg in driver.execute_agentic("test", "/tmp")]

        # Find the thinking message
        thinking_msgs = [m for m in results if m.type == AgenticMessageType.THINKING]
        assert len(thinking_msgs) == 1
        assert thinking_msgs[0].content == "Let me analyze this..."
        assert isinstance(thinking_msgs[0], AgenticMessage)

    async def test_yields_tool_call_for_tool_use_block(self, driver: ClaudeCliDriver) -> None:
        """ToolUseBlock should yield TOOL_CALL AgenticMessage."""
        messages = [
            MockAssistantMessage([MockToolUseBlock("read_file", {"path": "/test.py"})]),
            MockResultMessage(result="Done", session_id="sess_123"),
        ]

        with patch.object(driver, "_query", create_mock_query(messages)):
            results = [msg async for msg in driver.execute_agentic("test", "/tmp")]

        tool_calls = [m for m in results if m.type == AgenticMessageType.TOOL_CALL]
        assert len(tool_calls) == 1
        assert tool_calls[0].tool_name == "read_file"
        assert tool_calls[0].tool_input == {"path": "/test.py"}
        assert tool_calls[0].tool_call_id == "tool_use_123"

    async def test_yields_tool_result_for_tool_result_block(self, driver: ClaudeCliDriver) -> None:
        """ToolResultBlock should yield TOOL_RESULT AgenticMessage."""
        messages = [
            MockAssistantMessage([MockToolResultBlock("file contents here")]),
            MockResultMessage(result="Done", session_id="sess_123"),
        ]

        with patch.object(driver, "_query", create_mock_query(messages)):
            results = [msg async for msg in driver.execute_agentic("test", "/tmp")]

        tool_results = [m for m in results if m.type == AgenticMessageType.TOOL_RESULT]
        assert len(tool_results) == 1
        assert tool_results[0].tool_output == "file contents here"
        assert tool_results[0].is_error is False

    async def test_yields_error_tool_result(self, driver: ClaudeCliDriver) -> None:
        """ToolResultBlock with is_error=True should set is_error on AgenticMessage."""
        messages = [
            MockAssistantMessage([MockToolResultBlock("Error: not found", is_error=True)]),
            MockResultMessage(result="Failed", session_id="sess_123"),
        ]

        with patch.object(driver, "_query", create_mock_query(messages)):
            results = [msg async for msg in driver.execute_agentic("test", "/tmp")]

        tool_results = [m for m in results if m.type == AgenticMessageType.TOOL_RESULT]
        assert len(tool_results) == 1
        assert tool_results[0].is_error is True

    async def test_yields_result_for_result_message(self, driver: ClaudeCliDriver) -> None:
        """ResultMessage should yield RESULT AgenticMessage with session_id."""
        messages = [
            MockResultMessage(result="Task completed", session_id="sess_abc123"),
        ]

        with patch.object(driver, "_query", create_mock_query(messages)):
            results = [msg async for msg in driver.execute_agentic("test", "/tmp")]

        result_msgs = [m for m in results if m.type == AgenticMessageType.RESULT]
        assert len(result_msgs) == 1
        assert result_msgs[0].content == "Task completed"
        assert result_msgs[0].session_id == "sess_abc123"

    async def test_yields_error_result(self, driver: ClaudeCliDriver) -> None:
        """ResultMessage with is_error=True should set is_error on AgenticMessage."""
        messages = [
            MockResultMessage(result="Execution failed", session_id="sess_123", is_error=True),
        ]

        with patch.object(driver, "_query", create_mock_query(messages)):
            results = [msg async for msg in driver.execute_agentic("test", "/tmp")]

        result_msgs = [m for m in results if m.type == AgenticMessageType.RESULT]
        assert len(result_msgs) == 1
        assert result_msgs[0].is_error is True
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_claude_driver.py::TestExecuteAgenticYieldsAgenticMessage -v`
Expected: FAIL (currently yields native SDK types, not AgenticMessage)

**Step 3: Write minimal implementation**

Update `execute_agentic()` in `amelia/drivers/cli/claude.py`:

```python
from amelia.drivers.base import AgenticMessage, AgenticMessageType

async def execute_agentic(
    self,
    prompt: str,
    cwd: str,
    session_id: str | None = None,
    instructions: str | None = None,
    schema: type[BaseModel] | None = None,
) -> AsyncIterator[AgenticMessage]:
    """Execute prompt with full agentic capabilities, yielding AgenticMessage.

    Args:
        prompt: The prompt to send
        cwd: Working directory for tool execution
        session_id: Optional session ID for conversation continuity
        instructions: Optional system instructions
        schema: Optional schema for structured output

    Yields:
        AgenticMessage for each event (thinking, tool_call, tool_result, result)
    """
    # Build query kwargs (same as before)
    query_kwargs: dict[str, Any] = {
        "prompt": prompt,
        "options": ClaudeCodeOptions(
            cwd=cwd,
            permission_mode=self.permission_mode,
            permission_prompt_tool_allowlist=self.tool_allowlist,
        ),
    }
    if session_id:
        query_kwargs["session_id"] = session_id
    if instructions:
        query_kwargs["system_prompt"] = instructions

    last_tool_name: str | None = None  # Track for tool_result messages

    async for message in self._query(**query_kwargs):
        # Skip SDK stream events
        if isinstance(message, SDKStreamEvent):
            continue

        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    yield AgenticMessage(
                        type=AgenticMessageType.THINKING,
                        content=block.text,
                    )
                elif isinstance(block, ToolUseBlock):
                    last_tool_name = block.name
                    yield AgenticMessage(
                        type=AgenticMessageType.TOOL_CALL,
                        tool_name=block.name,
                        tool_input=block.input,
                        tool_call_id=block.id,
                    )
                elif isinstance(block, ToolResultBlock):
                    yield AgenticMessage(
                        type=AgenticMessageType.TOOL_RESULT,
                        tool_name=last_tool_name,
                        tool_output=block.content,
                        is_error=block.is_error,
                    )

        elif isinstance(message, ResultMessage):
            yield AgenticMessage(
                type=AgenticMessageType.RESULT,
                content=message.result,
                session_id=message.session_id,
                is_error=message.is_error,
            )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_claude_driver.py::TestExecuteAgenticYieldsAgenticMessage -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/drivers/cli/claude.py tests/unit/test_claude_driver.py
git commit -m "feat(cli-driver): update execute_agentic() to yield AgenticMessage

Convert native claude-agent-sdk types to unified AgenticMessage:
- TextBlock → THINKING
- ToolUseBlock → TOOL_CALL
- ToolResultBlock → TOOL_RESULT
- ResultMessage → RESULT

Part of #198"
```

---

## Task 5: Update ApiDriver.execute_agentic() to Yield AgenticMessage

**Files:**
- Modify: `amelia/drivers/api/deepagents.py:278-327`
- Test: `tests/unit/test_api_driver.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_api_driver.py`:

```python
from amelia.drivers.base import AgenticMessage, AgenticMessageType
from langchain_core.messages import AIMessage, ToolMessage


class TestExecuteAgenticYieldsAgenticMessage:
    """Test execute_agentic() yields AgenticMessage types."""

    @pytest.fixture
    def driver_with_cwd(self) -> ApiDriver:
        """Create ApiDriver with cwd set."""
        return ApiDriver(model="openrouter:test/model", cwd="/test/path")

    async def test_yields_thinking_for_text_content(
        self, driver_with_cwd: ApiDriver, mock_deepagents: MagicMock
    ) -> None:
        """AIMessage with text content should yield THINKING AgenticMessage."""
        mock_deepagents.stream_results = [
            {"messages": [AIMessage(content="Analyzing the code...")]},
        ]

        results = [msg async for msg in driver_with_cwd.execute_agentic("test prompt")]

        thinking_msgs = [m for m in results if m.type == AgenticMessageType.THINKING]
        assert len(thinking_msgs) >= 1
        assert any(m.content == "Analyzing the code..." for m in thinking_msgs)
        assert all(isinstance(m, AgenticMessage) for m in thinking_msgs)

    async def test_yields_tool_call_for_tool_calls(
        self, driver_with_cwd: ApiDriver, mock_deepagents: MagicMock
    ) -> None:
        """AIMessage with tool_calls should yield TOOL_CALL AgenticMessage."""
        ai_msg = AIMessage(content="", tool_calls=[
            {"name": "read_file", "args": {"path": "/test.py"}, "id": "call_123"}
        ])
        mock_deepagents.stream_results = [{"messages": [ai_msg]}]

        results = [msg async for msg in driver_with_cwd.execute_agentic("test prompt")]

        tool_calls = [m for m in results if m.type == AgenticMessageType.TOOL_CALL]
        assert len(tool_calls) == 1
        assert tool_calls[0].tool_name == "read_file"
        assert tool_calls[0].tool_input == {"path": "/test.py"}
        assert tool_calls[0].tool_call_id == "call_123"

    async def test_yields_tool_result_for_tool_message(
        self, driver_with_cwd: ApiDriver, mock_deepagents: MagicMock
    ) -> None:
        """ToolMessage should yield TOOL_RESULT AgenticMessage."""
        tool_msg = ToolMessage(content="file contents", tool_call_id="call_123", name="read_file")
        mock_deepagents.stream_results = [{"messages": [tool_msg]}]

        results = [msg async for msg in driver_with_cwd.execute_agentic("test prompt")]

        tool_results = [m for m in results if m.type == AgenticMessageType.TOOL_RESULT]
        assert len(tool_results) == 1
        assert tool_results[0].tool_output == "file contents"
        assert tool_results[0].tool_name == "read_file"
        assert tool_results[0].is_error is False

    async def test_yields_result_at_end(
        self, driver_with_cwd: ApiDriver, mock_deepagents: MagicMock
    ) -> None:
        """Final AIMessage should yield RESULT AgenticMessage."""
        mock_deepagents.stream_results = [
            {"messages": [AIMessage(content="Task completed successfully")]},
        ]

        results = [msg async for msg in driver_with_cwd.execute_agentic("test prompt")]

        result_msgs = [m for m in results if m.type == AgenticMessageType.RESULT]
        assert len(result_msgs) == 1
        assert result_msgs[0].content == "Task completed successfully"
        # API driver has no session support
        assert result_msgs[0].session_id is None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_api_driver.py::TestExecuteAgenticYieldsAgenticMessage -v`
Expected: FAIL (currently yields native LangChain types, not AgenticMessage)

**Step 3: Write minimal implementation**

Update `execute_agentic()` in `amelia/drivers/api/deepagents.py`:

```python
from amelia.drivers.base import AgenticMessage, AgenticMessageType

async def execute_agentic(
    self,
    prompt: str,
) -> AsyncIterator[AgenticMessage]:
    """Execute prompt with full agentic capabilities, yielding AgenticMessage.

    Args:
        prompt: The prompt to send

    Yields:
        AgenticMessage for each event (thinking, tool_call, tool_result, result)

    Raises:
        ValueError: If cwd is not set on driver instance
    """
    if not self.cwd:
        raise ValueError("cwd must be set on ApiDriver for agentic execution")

    agent = create_deep_agent(
        model=_create_chat_model(self.model),
        tools=[create_shell_tool(cwd=self.cwd)],
    )

    last_message: AIMessage | None = None

    async for chunk in agent.astream(
        {"messages": [{"role": "user", "content": prompt}]},
        stream_mode="values",
    ):
        if not chunk.get("messages"):
            continue

        message = chunk["messages"][-1]

        if isinstance(message, AIMessage):
            last_message = message

            # Text content → THINKING
            if isinstance(message.content, str) and message.content:
                yield AgenticMessage(
                    type=AgenticMessageType.THINKING,
                    content=message.content,
                )
            elif isinstance(message.content, list):
                for block in message.content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        yield AgenticMessage(
                            type=AgenticMessageType.THINKING,
                            content=block.get("text", ""),
                        )

            # Tool calls
            for tool_call in message.tool_calls or []:
                yield AgenticMessage(
                    type=AgenticMessageType.TOOL_CALL,
                    tool_name=tool_call["name"],
                    tool_input=tool_call.get("args", {}),
                    tool_call_id=tool_call.get("id"),
                )

        elif isinstance(message, ToolMessage):
            yield AgenticMessage(
                type=AgenticMessageType.TOOL_RESULT,
                tool_name=message.name,
                tool_output=message.content,
                tool_call_id=message.tool_call_id,
                is_error=False,  # LangChain doesn't have error flag
            )

    # Final result from last AI message
    if last_message:
        final_content = ""
        if isinstance(last_message.content, str):
            final_content = last_message.content
        elif isinstance(last_message.content, list):
            for block in last_message.content:
                if isinstance(block, dict) and block.get("type") == "text":
                    final_content += block.get("text", "")

        yield AgenticMessage(
            type=AgenticMessageType.RESULT,
            content=final_content,
            session_id=None,  # API driver has no session support
        )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_api_driver.py::TestExecuteAgenticYieldsAgenticMessage -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/drivers/api/deepagents.py tests/unit/test_api_driver.py
git commit -m "feat(api-driver): update execute_agentic() to yield AgenticMessage

Convert native LangChain types to unified AgenticMessage:
- AIMessage text → THINKING
- AIMessage.tool_calls → TOOL_CALL
- ToolMessage → TOOL_RESULT
- Final AIMessage → RESULT

Part of #198"
```

---

## Task 6: Add execute_agentic() to DriverInterface Protocol

**Files:**
- Modify: `amelia/drivers/base.py:29-50`
- Test: `tests/unit/test_driver_factory.py` (verify protocol conformance)

**Step 1: Write the failing test**

Add to `tests/unit/test_driver_factory.py`:

```python
from amelia.drivers.base import DriverInterface, AgenticMessage
from collections.abc import AsyncIterator
import inspect


class TestDriverInterfaceProtocol:
    """Test DriverInterface protocol includes execute_agentic."""

    def test_protocol_has_execute_agentic_method(self) -> None:
        """DriverInterface should define execute_agentic method."""
        assert hasattr(DriverInterface, "execute_agentic")
        method = getattr(DriverInterface, "execute_agentic")
        sig = inspect.signature(method)
        # Should have prompt, cwd, session_id, instructions, schema params
        assert "prompt" in sig.parameters
        assert "cwd" in sig.parameters

    def test_claude_cli_driver_implements_protocol(self) -> None:
        """ClaudeCliDriver should implement DriverInterface including execute_agentic."""
        from amelia.drivers.cli.claude import ClaudeCliDriver

        driver = ClaudeCliDriver()
        # Should have execute_agentic that returns AsyncIterator[AgenticMessage]
        assert hasattr(driver, "execute_agentic")
        assert hasattr(driver, "generate")

    def test_api_driver_implements_protocol(self) -> None:
        """ApiDriver should implement DriverInterface including execute_agentic."""
        from amelia.drivers.api.deepagents import ApiDriver

        driver = ApiDriver(cwd="/tmp")
        assert hasattr(driver, "execute_agentic")
        assert hasattr(driver, "generate")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_driver_factory.py::TestDriverInterfaceProtocol -v`
Expected: FAIL with "DriverInterface has no attribute 'execute_agentic'"

**Step 3: Write minimal implementation**

Update `DriverInterface` in `amelia/drivers/base.py`:

```python
from collections.abc import AsyncIterator

class DriverInterface(Protocol):
    """Protocol defining the LLM driver interface.

    All drivers must implement both generate() for single-turn generation
    and execute_agentic() for autonomous tool-using execution.
    """

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: type[BaseModel] | None = None,
    ) -> GenerateResult:
        """Generate a response from the LLM.

        Args:
            prompt: The user prompt to send
            system_prompt: Optional system instructions
            schema: Optional Pydantic model for structured output

        Returns:
            Tuple of (output, session_id). Output is str or schema instance.
        """
        ...

    def execute_agentic(
        self,
        prompt: str,
        cwd: str,
        session_id: str | None = None,
        instructions: str | None = None,
        schema: type[BaseModel] | None = None,
    ) -> AsyncIterator[AgenticMessage]:
        """Execute prompt with autonomous tool use, yielding messages.

        Args:
            prompt: The prompt to send
            cwd: Working directory for tool execution
            session_id: Optional session ID for conversation continuity
            instructions: Optional system instructions
            schema: Optional schema for structured output

        Yields:
            AgenticMessage for each event during execution
        """
        ...
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_driver_factory.py::TestDriverInterfaceProtocol -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/drivers/base.py tests/unit/test_driver_factory.py
git commit -m "feat(drivers): add execute_agentic() to DriverInterface protocol

DriverInterface now defines the full driver contract including agentic
execution. Both drivers yield unified AgenticMessage type.

Part of #198"
```

---

## Task 7: Refactor Developer to Use Unified Execution Path

**Files:**
- Modify: `amelia/agents/developer.py:86-385`
- Test: `tests/unit/core/test_developer_node.py`

**Step 1: Write the failing test**

Add to `tests/unit/core/test_developer_node.py`:

```python
from amelia.drivers.base import AgenticMessage, AgenticMessageType
from amelia.drivers.cli.claude import ClaudeCliDriver
from amelia.drivers.api.deepagents import ApiDriver


class TestDeveloperUnifiedExecution:
    """Test Developer uses unified AgenticMessage execution path."""

    async def test_no_isinstance_checks_on_driver(self) -> None:
        """Developer._run_agentic() should not use isinstance on driver."""
        import ast
        import inspect
        from amelia.agents.developer import Developer

        # Get source code of Developer class
        source = inspect.getsource(Developer)
        tree = ast.parse(source)

        # Find isinstance calls checking for driver types
        isinstance_driver_checks = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "isinstance":
                    if len(node.args) >= 2:
                        # Check if checking against ClaudeCliDriver or ApiDriver
                        if isinstance(node.args[1], ast.Name):
                            if node.args[1].id in ("ClaudeCliDriver", "ApiDriver"):
                                isinstance_driver_checks.append(node.args[1].id)

        assert isinstance_driver_checks == [], (
            f"Developer should not use isinstance checks on driver types, "
            f"found checks for: {isinstance_driver_checks}"
        )

    async def test_processes_agentic_message_thinking(
        self, mock_driver: MagicMock, mock_profile: Profile
    ) -> None:
        """Developer should process THINKING AgenticMessage."""
        developer = Developer(driver=mock_driver, profile=mock_profile)

        # Mock execute_agentic to yield AgenticMessage
        async def mock_execute():
            yield AgenticMessage(
                type=AgenticMessageType.THINKING,
                content="Analyzing the code...",
            )
            yield AgenticMessage(
                type=AgenticMessageType.RESULT,
                content="Done",
            )

        mock_driver.execute_agentic = mock_execute

        # Run should process messages without errors
        state = create_test_state()
        results = []
        async for update in developer._run_agentic(state, "test prompt"):
            results.append(update)

        # Should have received stream events
        assert any(
            e.type == StreamEventType.CLAUDE_THINKING
            for _, e in results
            if isinstance(e, StreamEvent)
        )
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/core/test_developer_node.py::TestDeveloperUnifiedExecution -v`
Expected: FAIL (Developer still has isinstance checks)

**Step 3: Write minimal implementation**

Refactor `amelia/agents/developer.py` to use single execution path:

```python
from amelia.drivers.base import AgenticMessage, AgenticMessageType, DriverInterface
from amelia.core.agentic_state import ToolCall, ToolResult
from amelia.core.types import StreamEvent, StreamEventType

class Developer:
    def __init__(self, driver: DriverInterface, profile: Profile) -> None:
        self.driver = driver
        self.profile = profile

    async def run(
        self,
        state: ExecutionState,
        feedback: str | None = None,
    ) -> AsyncIterator[tuple[ExecutionState, StreamEvent]]:
        """Execute development task using unified agentic execution."""
        prompt = self._build_prompt(state, feedback)

        async for state_update, event in self._run_agentic(state, prompt):
            yield state_update, event

    async def _run_agentic(
        self,
        state: ExecutionState,
        prompt: str,
    ) -> AsyncIterator[tuple[ExecutionState, StreamEvent]]:
        """Execute agentic loop using unified AgenticMessage handling."""
        workflow_id = state.workflow_id
        cwd = str(state.worktree) if state.worktree else os.getcwd()

        tool_calls: list[ToolCall] = []
        tool_results: list[ToolResult] = []
        final_response: str | None = None
        session_id = state.driver_session_id

        async for msg in self.driver.execute_agentic(
            prompt=prompt,
            cwd=cwd,
            session_id=session_id,
            instructions=self._get_instructions(),
        ):
            event = msg.to_stream_event(agent="developer", workflow_id=workflow_id)

            if msg.type == AgenticMessageType.THINKING:
                # Thinking messages don't update state, just emit event
                yield state, event

            elif msg.type == AgenticMessageType.TOOL_CALL:
                tool_call = ToolCall(
                    id=msg.tool_call_id or "",
                    tool_name=msg.tool_name or "",
                    tool_input=msg.tool_input or {},
                )
                tool_calls.append(tool_call)
                yield state.model_copy(update={"tool_calls": tool_calls}), event

            elif msg.type == AgenticMessageType.TOOL_RESULT:
                tool_result = ToolResult(
                    call_id=msg.tool_call_id or "",
                    tool_name=msg.tool_name or "",
                    output=msg.tool_output or "",
                    success=not msg.is_error,
                    error=msg.tool_output if msg.is_error else None,
                )
                tool_results.append(tool_result)
                yield state.model_copy(update={"tool_results": tool_results}), event

            elif msg.type == AgenticMessageType.RESULT:
                final_response = msg.content
                session_id = msg.session_id
                yield state.model_copy(
                    update={
                        "final_response": final_response,
                        "driver_session_id": session_id,
                        "agentic_status": AgenticStatus.COMPLETED,
                    }
                ), event
```

Remove the old `_run_with_cli_driver()` and `_run_with_api_driver()` methods entirely.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/core/test_developer_node.py::TestDeveloperUnifiedExecution -v`
Expected: PASS

**Step 5: Run full test suite to catch regressions**

Run: `uv run pytest tests/unit/core/test_developer_node.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add amelia/agents/developer.py tests/unit/core/test_developer_node.py
git commit -m "refactor(developer): unify execution path with AgenticMessage

Replace _run_with_cli_driver() and _run_with_api_driver() with single
_run_agentic() that processes unified AgenticMessage stream.

Removes ~120 lines of duplicated isinstance checks and message handling.

Part of #198"
```

---

## Task 8: Refactor Reviewer to Use Unified Execution Path

**Files:**
- Modify: `amelia/agents/reviewer.py:526-697`
- Test: `tests/unit/agents/test_reviewer.py`

**Step 1: Write the failing test**

Add to `tests/unit/agents/test_reviewer.py`:

```python
from amelia.drivers.base import AgenticMessage, AgenticMessageType


class TestReviewerUnifiedExecution:
    """Test Reviewer uses unified AgenticMessage execution path."""

    async def test_no_isinstance_checks_on_driver(self) -> None:
        """Reviewer agentic review should not use isinstance on driver."""
        import ast
        import inspect
        from amelia.agents.reviewer import Reviewer

        source = inspect.getsource(Reviewer)
        tree = ast.parse(source)

        isinstance_driver_checks = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "isinstance":
                    if len(node.args) >= 2:
                        if isinstance(node.args[1], ast.Name):
                            if node.args[1].id in ("ClaudeCliDriver", "ApiDriver"):
                                isinstance_driver_checks.append(node.args[1].id)

        assert isinstance_driver_checks == [], (
            f"Reviewer should not use isinstance checks on driver types, "
            f"found checks for: {isinstance_driver_checks}"
        )

    async def test_processes_agentic_message_stream(
        self, mock_driver: MagicMock, mock_profile: Profile
    ) -> None:
        """Reviewer should process AgenticMessage stream."""
        reviewer = Reviewer(driver=mock_driver, profile=mock_profile)

        async def mock_execute(*args, **kwargs):
            yield AgenticMessage(
                type=AgenticMessageType.THINKING,
                content="Reviewing changes...",
            )
            yield AgenticMessage(
                type=AgenticMessageType.TOOL_CALL,
                tool_name="read_file",
                tool_input={"path": "/test.py"},
                tool_call_id="call_1",
            )
            yield AgenticMessage(
                type=AgenticMessageType.RESULT,
                content='{"approved": true, "feedback": "LGTM"}',
            )

        mock_driver.execute_agentic = mock_execute

        # Should process without errors
        state = create_test_state()
        events = []
        async for update, event in reviewer._run_agentic_review(state):
            events.append(event)

        assert len(events) >= 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/agents/test_reviewer.py::TestReviewerUnifiedExecution -v`
Expected: FAIL (Reviewer still has isinstance checks)

**Step 3: Write minimal implementation**

Refactor `amelia/agents/reviewer.py` agentic review section:

```python
from amelia.drivers.base import AgenticMessage, AgenticMessageType, DriverInterface

async def _run_agentic_review(
    self,
    state: ExecutionState,
) -> AsyncIterator[tuple[ExecutionState, StreamEvent]]:
    """Execute agentic review using unified AgenticMessage handling."""
    workflow_id = state.workflow_id
    cwd = str(state.worktree) if state.worktree else os.getcwd()
    prompt = self._build_review_prompt(state)

    final_content: str | None = None

    async for msg in self.driver.execute_agentic(
        prompt=prompt,
        cwd=cwd,
        session_id=state.driver_session_id,
        instructions=self._get_review_instructions(),
    ):
        event = msg.to_stream_event(agent="reviewer", workflow_id=workflow_id)

        if msg.type == AgenticMessageType.THINKING:
            yield state, event

        elif msg.type == AgenticMessageType.TOOL_CALL:
            yield state, event

        elif msg.type == AgenticMessageType.TOOL_RESULT:
            yield state, event

        elif msg.type == AgenticMessageType.RESULT:
            final_content = msg.content
            yield state.model_copy(
                update={"driver_session_id": msg.session_id}
            ), event

    # Parse final result
    if final_content:
        review_result = self._parse_review_result(final_content)
        yield state.model_copy(update={"review_result": review_result}), event
```

Remove the old driver-specific handling code.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/agents/test_reviewer.py::TestReviewerUnifiedExecution -v`
Expected: PASS

**Step 5: Run full test suite to catch regressions**

Run: `uv run pytest tests/unit/agents/test_reviewer.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add amelia/agents/reviewer.py tests/unit/agents/test_reviewer.py
git commit -m "refactor(reviewer): unify execution path with AgenticMessage

Replace driver isinstance checks with unified AgenticMessage processing.
Removes duplicated message handling code.

Part of #198"
```

---

## Task 9: Remove Driver-Specific Type Imports from Agents

**Files:**
- Modify: `amelia/agents/developer.py`
- Modify: `amelia/agents/reviewer.py`

**Step 1: Write the failing test**

Add to a new test file `tests/unit/agents/test_agent_imports.py`:

```python
"""Test agents don't import driver-specific types."""

import ast
import inspect


class TestAgentImports:
    """Verify agents only import from drivers.base, not SDK-specific types."""

    def test_developer_no_sdk_imports(self) -> None:
        """Developer should not import claude_agent_sdk or langchain types."""
        from amelia.agents import developer

        source = inspect.getsource(developer)
        tree = ast.parse(source)

        forbidden_imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and ("claude_agent_sdk" in node.module or "langchain" in node.module):
                    forbidden_imports.append(node.module)

        assert forbidden_imports == [], (
            f"Developer should not import SDK-specific types: {forbidden_imports}"
        )

    def test_reviewer_no_sdk_imports(self) -> None:
        """Reviewer should not import claude_agent_sdk or langchain types."""
        from amelia.agents import reviewer

        source = inspect.getsource(reviewer)
        tree = ast.parse(source)

        forbidden_imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and ("claude_agent_sdk" in node.module or "langchain" in node.module):
                    forbidden_imports.append(node.module)

        assert forbidden_imports == [], (
            f"Reviewer should not import SDK-specific types: {forbidden_imports}"
        )
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/agents/test_agent_imports.py -v`
Expected: FAIL (agents still have SDK imports in methods)

**Step 3: Write minimal implementation**

Remove all remaining SDK imports from developer.py and reviewer.py:

In `amelia/agents/developer.py`, remove:
- `from claude_agent_sdk.types import ...`
- `from langchain_core.messages import ...`

In `amelia/agents/reviewer.py`, remove:
- `from claude_agent_sdk.types import ...`
- Any langchain imports for message types

Ensure only `from amelia.drivers.base import AgenticMessage, AgenticMessageType, DriverInterface` is used.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/agents/test_agent_imports.py -v`
Expected: PASS

**Step 5: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add amelia/agents/developer.py amelia/agents/reviewer.py tests/unit/agents/test_agent_imports.py
git commit -m "refactor(agents): remove driver-specific SDK imports

Agents now only import from amelia.drivers.base for the unified
AgenticMessage type. No direct coupling to claude-agent-sdk or langchain.

Closes #198"
```

---

## Task 10: Final Verification and Cleanup

**Files:**
- All modified files

**Step 1: Run linting**

Run: `uv run ruff check amelia tests --fix`
Expected: No errors or auto-fixed

**Step 2: Run type checking**

Run: `uv run mypy amelia`
Expected: No type errors

**Step 3: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All tests pass

**Step 4: Verify acceptance criteria**

Check each criterion from the design doc:

- [ ] `DriverInterface` protocol includes `execute_agentic()` method
- [ ] Both drivers yield `AgenticMessage` from `execute_agentic()`
- [ ] Developer and Reviewer use unified execution path (no `isinstance` checks)
- [ ] All existing tests pass
- [ ] `to_stream_event()` method works for agent→dashboard conversion

**Step 5: Final commit**

```bash
git add -A
git commit -m "chore: cleanup and verify unified AgenticMessage implementation

All acceptance criteria met:
- DriverInterface includes execute_agentic()
- Both drivers yield AgenticMessage
- Agents use unified execution path
- All tests pass
- to_stream_event() works correctly

Closes #198"
```

---

## Summary

| Task | Description | Files Changed | LOC Estimate |
|------|-------------|---------------|--------------|
| 1 | Define AgenticMessage types | base.py, test_agentic_message.py | +60 |
| 2 | Add is_error to StreamEvent | types.py, test_stream_event.py | +10 |
| 3 | Add to_stream_event() method | base.py, test_agentic_message.py | +40 |
| 4 | Update ClaudeCliDriver | claude.py, test_claude_driver.py | +80/-60 |
| 5 | Update ApiDriver | deepagents.py, test_api_driver.py | +60/-40 |
| 6 | Add to DriverInterface | base.py, test_driver_factory.py | +30 |
| 7 | Refactor Developer | developer.py, test_developer_node.py | +50/-150 |
| 8 | Refactor Reviewer | reviewer.py, test_reviewer.py | +40/-80 |
| 9 | Remove SDK imports | developer.py, reviewer.py, test_agent_imports.py | +20/-30 |
| 10 | Verification | all | 0 |

**Net change:** ~-100 LOC (removes duplication)
