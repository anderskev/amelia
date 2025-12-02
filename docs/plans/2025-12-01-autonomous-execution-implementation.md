# Autonomous Execution Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable autonomous task execution after plan approval, where Claude runs freely per task with streaming output.

**Architecture:** Add `execution_mode` profile setting that switches Developer between structured (step-by-step) and agentic (autonomous) execution. Merge `execute_agentic()` into main `ClaudeCliDriver`.

**Tech Stack:** Python 3.12+, Pydantic, asyncio, typer

---

## Task 1: Add ExecutionMode Type

**Files:**
- Modify: `amelia/core/types.py:6-8`
- Test: `tests/unit/test_types.py` (new)

**Step 1: Write the failing test**

```python
# tests/unit/test_types.py
"""Tests for core types."""

from amelia.core.types import ExecutionMode


def test_execution_mode_literal_values():
    """ExecutionMode should accept 'structured' and 'agentic'."""
    mode1: ExecutionMode = "structured"
    mode2: ExecutionMode = "agentic"
    assert mode1 == "structured"
    assert mode2 == "agentic"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_types.py::test_execution_mode_literal_values -v`
Expected: FAIL with "cannot import name 'ExecutionMode'"

**Step 3: Write minimal implementation**

Add after line 8 in `amelia/core/types.py`:

```python
ExecutionMode = Literal["structured", "agentic"]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_types.py::test_execution_mode_literal_values -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/types.py tests/unit/test_types.py
git commit -m "feat(types): add ExecutionMode literal type"
```

---

## Task 2: Add execution_mode and working_dir to Profile

**Files:**
- Modify: `amelia/core/types.py:10-38`
- Test: `tests/unit/test_types.py`

**Step 1: Write the failing test**

Append to `tests/unit/test_types.py`:

```python
from amelia.core.types import Profile


def test_profile_execution_mode_default():
    """Profile execution_mode should default to 'structured'."""
    profile = Profile(name="test", driver="cli:claude")
    assert profile.execution_mode == "structured"


def test_profile_execution_mode_agentic():
    """Profile should accept execution_mode='agentic'."""
    profile = Profile(name="test", driver="cli:claude", execution_mode="agentic")
    assert profile.execution_mode == "agentic"


def test_profile_working_dir_default():
    """Profile working_dir should default to None."""
    profile = Profile(name="test", driver="cli:claude")
    assert profile.working_dir is None


def test_profile_working_dir_custom():
    """Profile should accept custom working_dir."""
    profile = Profile(name="test", driver="cli:claude", working_dir="/custom/path")
    assert profile.working_dir == "/custom/path"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_types.py::test_profile_execution_mode_default -v`
Expected: FAIL with "unexpected keyword argument 'execution_mode'"

**Step 3: Write minimal implementation**

Modify Profile class in `amelia/core/types.py`:

```python
class Profile(BaseModel):
    """Configuration profile for Amelia execution.

    Attributes:
        name: Profile name (e.g., 'work', 'personal').
        driver: LLM driver type (e.g., 'api:openai', 'cli:claude').
        tracker: Issue tracker type (jira, github, none, noop).
        strategy: Review strategy (single or competitive).
        execution_mode: Execution mode (structured or agentic).
        plan_output_dir: Directory for storing generated plans.
        working_dir: Working directory for agentic execution.
    """
    name: str
    driver: DriverType
    tracker: TrackerType = "none"
    strategy: StrategyType = "single"
    execution_mode: ExecutionMode = "structured"
    plan_output_dir: str = "docs/plans"
    working_dir: str | None = None

    @model_validator(mode="after")
    def validate_work_profile_constraints(self) -> "Profile":
        """Enterprise constraint: 'work' profiles cannot use API drivers.

        Returns:
            The validated profile.

        Raises:
            ValueError: If 'work' profile attempts to use an API driver.
        """
        if self.name.lower() == "work" and self.driver.startswith("api"):
            raise ValueError(f"Profile 'work' cannot use API drivers (got '{self.driver}'). Use CLI drivers for enterprise compliance.")
        return self
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_types.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add amelia/core/types.py tests/unit/test_types.py
git commit -m "feat(types): add execution_mode and working_dir to Profile"
```

---

## Task 3: Add workflow_status to ExecutionState

**Files:**
- Modify: `amelia/core/state.py:160-183`
- Test: `tests/unit/test_state.py` (new)

**Step 1: Write the failing test**

```python
# tests/unit/test_state.py
"""Tests for core state models."""

from amelia.core.state import ExecutionState
from amelia.core.types import Profile


def test_execution_state_workflow_status_default():
    """ExecutionState workflow_status should default to 'running'."""
    profile = Profile(name="test", driver="cli:claude")
    state = ExecutionState(profile=profile)
    assert state.workflow_status == "running"


def test_execution_state_workflow_status_failed():
    """ExecutionState should accept workflow_status='failed'."""
    profile = Profile(name="test", driver="cli:claude")
    state = ExecutionState(profile=profile, workflow_status="failed")
    assert state.workflow_status == "failed"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_state.py::test_execution_state_workflow_status_default -v`
Expected: FAIL with "unexpected keyword argument 'workflow_status'"

**Step 3: Write minimal implementation**

Add to ExecutionState class in `amelia/core/state.py` after line 182:

```python
    workflow_status: Literal["running", "completed", "failed"] = "running"
```

Also add the import at the top if not present - but Literal is already imported.

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_state.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add amelia/core/state.py tests/unit/test_state.py
git commit -m "feat(state): add workflow_status to ExecutionState"
```

---

## Task 4: Add AgenticExecutionError Exception

**Files:**
- Modify: `amelia/core/exceptions.py:51`
- Test: `tests/unit/test_exceptions.py` (new)

**Step 1: Write the failing test**

```python
# tests/unit/test_exceptions.py
"""Tests for custom exceptions."""

import pytest

from amelia.core.exceptions import AgenticExecutionError, AmeliaError


def test_agentic_execution_error_is_amelia_error():
    """AgenticExecutionError should inherit from AmeliaError."""
    error = AgenticExecutionError("test error")
    assert isinstance(error, AmeliaError)
    assert str(error) == "test error"


def test_agentic_execution_error_can_be_raised():
    """AgenticExecutionError should be raisable."""
    with pytest.raises(AgenticExecutionError) as exc_info:
        raise AgenticExecutionError("agentic failed")
    assert "agentic failed" in str(exc_info.value)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_exceptions.py::test_agentic_execution_error_is_amelia_error -v`
Expected: FAIL with "cannot import name 'AgenticExecutionError'"

**Step 3: Write minimal implementation**

Add at end of `amelia/core/exceptions.py`:

```python


class AgenticExecutionError(AmeliaError):
    """Raised when agentic execution fails."""

    pass
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_exceptions.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add amelia/core/exceptions.py tests/unit/test_exceptions.py
git commit -m "feat(exceptions): add AgenticExecutionError"
```

---

## Task 5: Add execute_agentic to ClaudeCliDriver

**Files:**
- Modify: `amelia/drivers/cli/claude.py`
- Test: `tests/unit/test_claude_driver.py`

**Step 1: Write the failing test**

Append to `tests/unit/test_claude_driver.py`:

```python
class TestClaudeCliDriverAgentic:
    """Tests for execute_agentic method."""

    @pytest.mark.asyncio
    async def test_execute_agentic_uses_skip_permissions(self, driver, mock_subprocess_process_factory):
        """execute_agentic should use --dangerously-skip-permissions."""
        stream_lines = [
            b'{"type":"assistant","message":{"content":[{"type":"text","text":"Working..."}]}}\n',
            b'{"type":"result","session_id":"sess_001","subtype":"success"}\n',
            b""
        ]
        mock_process = mock_subprocess_process_factory(stdout_lines=stream_lines, return_code=0)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process) as mock_exec:
            events = []
            async for event in driver.execute_agentic("test prompt", "/tmp"):
                events.append(event)

            mock_exec.assert_called_once()
            args = mock_exec.call_args[0]
            assert "--dangerously-skip-permissions" in args

    @pytest.mark.asyncio
    async def test_execute_agentic_tracks_tool_calls(self, driver, mock_subprocess_process_factory):
        """execute_agentic should track tool calls in tool_call_history."""
        stream_lines = [
            b'{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{"path":"test.py"}}]}}\n',
            b'{"type":"result","session_id":"sess_001","subtype":"success"}\n',
            b""
        ]
        mock_process = mock_subprocess_process_factory(stdout_lines=stream_lines, return_code=0)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process):
            async for _ in driver.execute_agentic("test prompt", "/tmp"):
                pass

            assert len(driver.tool_call_history) == 1
            assert driver.tool_call_history[0].tool_name == "Read"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_claude_driver.py::TestClaudeCliDriverAgentic::test_execute_agentic_uses_skip_permissions -v`
Expected: FAIL with "has no attribute 'execute_agentic'"

**Step 3: Write minimal implementation**

Add to `ClaudeCliDriver` class in `amelia/drivers/cli/claude.py` after `generate_stream` method:

```python
    def __init__(
        self,
        model: str = "sonnet",
        timeout: int = 30,
        max_retries: int = 0,
        skip_permissions: bool = False,
        allowed_tools: list[str] | None = None,
        disallowed_tools: list[str] | None = None,
    ):
        """Initialize the Claude CLI driver.

        Args:
            model: Claude model to use. Defaults to "sonnet".
            timeout: Maximum execution time in seconds. Defaults to 30.
            max_retries: Number of retry attempts. Defaults to 0.
            skip_permissions: Skip permission prompts. Defaults to False.
            allowed_tools: List of allowed tool names. Defaults to None.
            disallowed_tools: List of disallowed tool names. Defaults to None.
        """
        super().__init__(timeout, max_retries)
        self.model = model
        self.skip_permissions = skip_permissions
        self.allowed_tools = allowed_tools
        self.disallowed_tools = disallowed_tools
        self.tool_call_history: list[ClaudeStreamEvent] = []
```

And add the method:

```python
    async def execute_agentic(
        self,
        prompt: str,
        cwd: str,
        session_id: str | None = None
    ) -> AsyncIterator[ClaudeStreamEvent]:
        """Execute prompt with full autonomous tool access (YOLO mode).

        Args:
            prompt: The task or instruction for Claude.
            cwd: Working directory for Claude Code context.
            session_id: Optional session ID to resume.

        Yields:
            ClaudeStreamEvent objects including tool executions.
        """
        cmd_args = [
            "claude", "-p",
            "--model", self.model,
            "--output-format", "stream-json",
            "--verbose",
            "--dangerously-skip-permissions"
        ]

        if session_id:
            cmd_args.extend(["--resume", session_id])
            logger.info(f"Resuming agentic session: {session_id}")

        logger.info(f"Starting agentic execution in {cwd}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )

            if process.stdin:
                process.stdin.write(prompt.encode())
                await process.stdin.drain()
                process.stdin.close()

            if process.stdout:
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break

                    event = ClaudeStreamEvent.from_stream_json(line.decode())
                    if event:
                        if event.type == "tool_use":
                            self.tool_call_history.append(event)
                            logger.info(f"Tool call: {event.tool_name}")
                        yield event

            await process.wait()

            if process.returncode != 0:
                stderr_data = await process.stderr.read() if process.stderr else b""
                logger.error(f"Agentic execution failed: {stderr_data.decode()}")

        except Exception as e:
            logger.error(f"Error in agentic execution: {e}")
            yield ClaudeStreamEvent(type="error", content=str(e))

    def clear_tool_history(self) -> None:
        """Clear the tool call history."""
        self.tool_call_history = []
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_claude_driver.py::TestClaudeCliDriverAgentic -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add amelia/drivers/cli/claude.py tests/unit/test_claude_driver.py
git commit -m "feat(driver): add execute_agentic to ClaudeCliDriver"
```

---

## Task 6: Add Agentic Execution to Developer Agent

**Files:**
- Modify: `amelia/agents/developer.py`
- Test: `tests/unit/test_developer.py`

**Step 1: Write the failing test**

Append to `tests/unit/test_developer.py`:

```python
from amelia.core.exceptions import AgenticExecutionError
from amelia.drivers.cli.claude import ClaudeStreamEvent


class TestDeveloperAgenticExecution:
    """Tests for Developer agentic execution mode."""

    async def test_execute_task_agentic_calls_execute_agentic(self, mock_task_factory):
        """Developer in agentic mode should call driver.execute_agentic."""
        mock_driver = AsyncMock(spec=DriverInterface)

        async def mock_execute_agentic(prompt, cwd, session_id=None):
            yield ClaudeStreamEvent(type="assistant", content="Working...")
            yield ClaudeStreamEvent(type="result", session_id="sess_001")

        mock_driver.execute_agentic = mock_execute_agentic

        task = mock_task_factory(id="1", description="Implement feature")
        developer = Developer(driver=mock_driver, execution_mode="agentic")

        result = await developer.execute_task(task, cwd="/tmp")

        assert result["status"] == "completed"

    async def test_execute_task_agentic_raises_on_error(self, mock_task_factory):
        """Developer in agentic mode should raise AgenticExecutionError on error event."""
        mock_driver = AsyncMock(spec=DriverInterface)

        async def mock_execute_agentic(prompt, cwd, session_id=None):
            yield ClaudeStreamEvent(type="error", content="Something went wrong")

        mock_driver.execute_agentic = mock_execute_agentic

        task = mock_task_factory(id="1", description="Implement feature")
        developer = Developer(driver=mock_driver, execution_mode="agentic")

        with pytest.raises(AgenticExecutionError) as exc_info:
            await developer.execute_task(task, cwd="/tmp")

        assert "Something went wrong" in str(exc_info.value)

    async def test_execute_task_structured_ignores_cwd(self, mock_task_factory):
        """Developer in structured mode should work without cwd."""
        mock_driver = AsyncMock(spec=DriverInterface)
        mock_driver.generate.return_value = "Generated response"

        task = mock_task_factory(id="1", description="Implement feature")
        developer = Developer(driver=mock_driver, execution_mode="structured")

        result = await developer.execute_task(task)

        assert result["status"] == "completed"
        mock_driver.generate.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_developer.py::TestDeveloperAgenticExecution::test_execute_task_agentic_calls_execute_agentic -v`
Expected: FAIL with "unexpected keyword argument 'execution_mode'"

**Step 3: Write minimal implementation**

Replace `amelia/agents/developer.py`:

```python
import os
from typing import Any, Literal

import typer
from loguru import logger
from pydantic import BaseModel

from amelia.core.constants import ToolName
from amelia.core.exceptions import AgenticExecutionError
from amelia.core.state import AgentMessage, Task
from amelia.drivers.base import DriverInterface


DeveloperStatus = Literal["completed", "failed", "in_progress"]
ExecutionMode = Literal["structured", "agentic"]


class DeveloperResponse(BaseModel):
    """Schema for Developer agent's task execution output."""
    status: DeveloperStatus
    output: str
    error: str | None = None


class Developer:
    """Agent responsible for executing development tasks following TDD principles.

    Attributes:
        driver: LLM driver interface for task execution and tool access.
        execution_mode: Execution mode (structured or agentic).
    """

    def __init__(self, driver: DriverInterface, execution_mode: ExecutionMode = "structured"):
        """Initialize the Developer agent.

        Args:
            driver: LLM driver interface for task execution and tool access.
            execution_mode: Execution mode. Defaults to "structured".
        """
        self.driver = driver
        self.execution_mode = execution_mode

    async def execute_task(self, task: Task, cwd: str | None = None) -> dict[str, Any]:
        """Execute a single development task.

        Args:
            task: The task to execute.
            cwd: Working directory for agentic execution.

        Returns:
            Dict with status and output.

        Raises:
            AgenticExecutionError: If agentic execution fails.
        """
        if self.execution_mode == "agentic":
            return await self._execute_agentic(task, cwd or os.getcwd())
        else:
            return await self._execute_structured(task)

    async def _execute_agentic(self, task: Task, cwd: str) -> dict[str, Any]:
        """Execute task autonomously with full Claude tool access.

        Args:
            task: The task to execute.
            cwd: Working directory for execution.

        Returns:
            Dict with status and output.

        Raises:
            AgenticExecutionError: If execution fails.
        """
        prompt = self._build_task_prompt(task)
        logger.info(f"Starting agentic execution for task {task.id}")

        async for event in self.driver.execute_agentic(prompt, cwd):
            self._handle_stream_event(event)

            if event.type == "error":
                raise AgenticExecutionError(event.content or "Unknown error")

        return {"status": "completed", "task_id": task.id, "output": "Agentic execution completed"}

    def _build_task_prompt(self, task: Task) -> str:
        """Convert task to a prompt for agentic execution.

        Args:
            task: The task to convert.

        Returns:
            Formatted prompt string.
        """
        sections = [f"# Task: {task.description}", "", "## Files"]

        for file_op in task.files:
            sections.append(f"- {file_op.operation}: `{file_op.path}`")

        if task.steps:
            sections.append("")
            sections.append("## Steps")
            for i, step in enumerate(task.steps, 1):
                sections.append(f"### Step {i}: {step.description}")
                if step.code:
                    sections.append(f"```\n{step.code}\n```")
                if step.command:
                    sections.append(f"Run: `{step.command}`")
                if step.expected_output:
                    sections.append(f"Expected: {step.expected_output}")

        sections.append("")
        sections.append("Execute this task following TDD principles. Run tests after each change.")

        return "\n".join(sections)

    def _handle_stream_event(self, event: Any) -> None:
        """Display streaming event to terminal.

        Args:
            event: ClaudeStreamEvent to display.
        """
        if event.type == "tool_use":
            typer.secho(f"  -> {event.tool_name}", fg=typer.colors.CYAN)
            if event.tool_input:
                preview = str(event.tool_input)[:100]
                suffix = "..." if len(str(event.tool_input)) > 100 else ""
                typer.echo(f"    {preview}{suffix}")

        elif event.type == "tool_result":
            typer.secho("  Done", fg=typer.colors.GREEN)

        elif event.type == "assistant" and event.content:
            typer.echo(f"  {event.content[:200]}")

        elif event.type == "error":
            typer.secho(f"  Error: {event.content}", fg=typer.colors.RED)

    async def _execute_structured(self, task: Task) -> dict[str, Any]:
        """Execute task using structured step-by-step approach.

        Args:
            task: The task to execute.

        Returns:
            Dict with status and output.
        """
        try:
            if task.steps:
                logger.info(f"Developer executing {len(task.steps)} steps for task {task.id}")
                results = []
                for i, step in enumerate(task.steps, 1):
                    logger.info(f"Executing step {i}: {step.description}")
                    step_output = ""

                    if step.code:
                        target_file = None
                        if task.files:
                            for f in task.files:
                                if f.operation in ("create", "modify"):
                                    target_file = f.path
                                    break

                        if target_file:
                            logger.info(f"Writing code to {target_file}")
                            await self.driver.execute_tool(ToolName.WRITE_FILE, file_path=target_file, content=step.code)
                            step_output += f"Wrote to {target_file}. "
                        else:
                            logger.warning("Step has code but no target file could be determined from task.files.")

                    if step.command:
                        logger.info(f"Running command: {step.command}")
                        cmd_result = await self.driver.execute_tool(ToolName.RUN_SHELL_COMMAND, command=step.command)
                        step_output += f"Command output: {cmd_result}"

                    results.append(f"Step {i}: {step_output}")

                return {"status": "completed", "output": "\n".join(results)}

            if task.description.lower().startswith("run shell command:"):
                command = task.description[len("run shell command:"):].strip()
                logger.info(f"Developer executing shell command: {command}")
                result = await self.driver.execute_tool(ToolName.RUN_SHELL_COMMAND, command=command)
                return {"status": "completed", "output": result}

            elif task.description.lower().startswith("write file:"):
                logger.info(f"Developer executing write file task: {task.description}")

                if " with " in task.description:
                    parts = task.description.split(" with ", 1)
                    path_part = parts[0]
                    content = parts[1]
                else:
                    path_part = task.description
                    content = ""

                file_path = path_part[len("write file:"):].strip()

                result = await self.driver.execute_tool(ToolName.WRITE_FILE, file_path=file_path, content=content)
                return {"status": "completed", "output": result}

            else:
                logger.info(f"Developer generating response for task: {task.description}")
                messages = [
                    AgentMessage(role="system", content="You are a skilled software developer. Execute the given task."),
                    AgentMessage(role="user", content=f"Task to execute: {task.description}")
                ]
                llm_response = await self.driver.generate(messages=messages)
                return {"status": "completed", "output": llm_response}

        except Exception as e:
            logger.error(f"Developer task execution failed: {e}")
            return {"status": "failed", "output": str(e), "error": str(e)}
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_developer.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add amelia/agents/developer.py tests/unit/test_developer.py
git commit -m "feat(developer): add agentic execution mode"
```

---

## Task 7: Update Orchestrator for Agentic Mode

**Files:**
- Modify: `amelia/core/orchestrator.py:141-204`
- Test: `tests/unit/test_orchestrator.py` (new or existing)

**Step 1: Write the failing test**

```python
# tests/unit/test_orchestrator.py (append or create)
"""Tests for orchestrator developer node."""

from unittest.mock import AsyncMock, patch

import pytest

from amelia.core.orchestrator import call_developer_node
from amelia.core.state import ExecutionState, Task, TaskDAG
from amelia.core.types import Profile


@pytest.fixture
def agentic_profile():
    return Profile(name="test", driver="cli:claude", execution_mode="agentic", working_dir="/test/dir")


@pytest.fixture
def structured_profile():
    return Profile(name="test", driver="cli:claude", execution_mode="structured")


class TestDeveloperNodeAgenticMode:
    """Tests for developer node with agentic execution."""

    @pytest.mark.asyncio
    async def test_developer_node_passes_execution_mode(
        self, mock_issue_factory, agentic_profile, mock_task_factory
    ):
        """Developer node should pass execution_mode from profile to Developer."""
        task = mock_task_factory(id="1", description="Test task", status="pending")
        plan = TaskDAG(tasks=[task], original_issue="TEST-1")
        state = ExecutionState(
            profile=agentic_profile,
            issue=mock_issue_factory(),
            plan=plan,
            human_approved=True
        )

        with patch("amelia.core.orchestrator.DriverFactory") as mock_factory, \
             patch("amelia.core.orchestrator.Developer") as mock_developer_class:
            mock_driver = AsyncMock()
            mock_factory.get_driver.return_value = mock_driver

            mock_developer = AsyncMock()
            mock_developer.execute_task.return_value = {"status": "completed", "output": "done"}
            mock_developer_class.return_value = mock_developer

            await call_developer_node(state)

            mock_developer_class.assert_called_once_with(mock_driver, execution_mode="agentic")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_orchestrator.py::TestDeveloperNodeAgenticMode::test_developer_node_passes_execution_mode -v`
Expected: FAIL with assertion error (Developer not called with execution_mode)

**Step 3: Write minimal implementation**

Modify `call_developer_node` in `amelia/core/orchestrator.py`:

```python
async def call_developer_node(state: ExecutionState) -> ExecutionState:
    """Orchestrator node for the Developer agent to execute tasks.

    Executes ready tasks, passing execution_mode and working directory from profile.

    Args:
        state: Current execution state containing the plan and tasks.

    Returns:
        Updated execution state with task results and messages.
    """
    logger.info("Orchestrator: Calling Developer to execute tasks.")

    if not state.plan or not state.plan.tasks:
        logger.info("Orchestrator: No plan or tasks to execute.")
        return state

    driver = DriverFactory.get_driver(state.profile.driver)
    developer = Developer(driver, execution_mode=state.profile.execution_mode)

    # Get working directory for agentic execution
    cwd = state.profile.working_dir or os.getcwd()

    ready_tasks = state.plan.get_ready_tasks()

    if not ready_tasks:
        logger.info("Orchestrator: No ready tasks found to execute in this iteration.")
        return state

    logger.info(f"Orchestrator: Executing {len(ready_tasks)} ready tasks.")

    updated_messages = list(state.messages)

    for task in ready_tasks:
        task.status = "in_progress"
        logger.info(f"Orchestrator: Developer executing task {task.id}")

        try:
            result = await developer.execute_task(task, cwd=cwd)

            if result.get("status") == "completed":
                task.status = "completed"
                output_content = result.get('output', 'No output')
                updated_messages.append(AgentMessage(role="assistant", content=f"Task {task.id} completed. Output: {output_content}"))
            else:
                task.status = "failed"
                updated_messages.append(AgentMessage(role="assistant", content=f"Task {task.id} failed. Error: {result.get('error', 'Unknown')}"))

        except Exception as e:
            task.status = "failed"
            updated_messages.append(AgentMessage(role="assistant", content=f"Task {task.id} failed. Error: {e}"))
            logger.error(f"Task {task.id} failed: {e}")

            # For agentic mode, fail fast
            if state.profile.execution_mode == "agentic":
                updated_plan = TaskDAG(tasks=state.plan.tasks, original_issue=state.plan.original_issue)
                return ExecutionState(
                    profile=state.profile,
                    issue=state.issue,
                    plan=updated_plan,
                    messages=updated_messages,
                    human_approved=state.human_approved,
                    review_results=state.review_results,
                    workflow_status="failed"
                )

    updated_plan = TaskDAG(tasks=state.plan.tasks, original_issue=state.plan.original_issue)

    return ExecutionState(
        profile=state.profile,
        issue=state.issue,
        plan=updated_plan,
        current_task_id=ready_tasks[0].id if ready_tasks else state.current_task_id,
        messages=updated_messages,
        human_approved=state.human_approved,
        review_results=state.review_results
    )
```

Also add imports at top:
```python
import os
from amelia.agents.developer import Developer
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_orchestrator.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py tests/unit/test_orchestrator.py
git commit -m "feat(orchestrator): pass execution_mode and cwd to Developer"
```

---

## Task 8: Remove ClaudeAgenticCliDriver

**Files:**
- Delete: `amelia/drivers/cli/agentic.py`
- Modify: `amelia/drivers/factory.py`
- Modify: `amelia/core/types.py`
- Delete: `tests/unit/test_claude_agentic_driver.py`
- Modify: `tests/unit/test_driver_factory.py`

**Step 1: Update factory to remove agentic driver case**

Modify `amelia/drivers/factory.py`:

```python
from typing import Any

from amelia.drivers.api.openai import ApiDriver
from amelia.drivers.base import DriverInterface
from amelia.drivers.cli.claude import ClaudeCliDriver


class DriverFactory:
    """Factory class for creating driver instances based on configuration keys."""

    @staticmethod
    def get_driver(driver_key: str, **kwargs: Any) -> DriverInterface:
        """Factory method to get a concrete driver implementation.

        Args:
            driver_key: Driver identifier (e.g., "cli:claude", "api:openai").
            **kwargs: Driver-specific configuration passed to constructor.

        Returns:
            Configured driver instance.

        Raises:
            ValueError: If driver_key is not recognized.
        """
        if driver_key == "cli:claude" or driver_key == "cli":
            return ClaudeCliDriver(**kwargs)
        elif driver_key == "api:openai" or driver_key == "api":
            return ApiDriver(**kwargs)
        else:
            raise ValueError(f"Unknown driver key: {driver_key}")
```

**Step 2: Update DriverType in types.py**

Change line 6 in `amelia/core/types.py`:

```python
DriverType = Literal["cli:claude", "api:openai", "cli", "api"]
```

**Step 3: Delete agentic driver file**

Run: `rm amelia/drivers/cli/agentic.py`

**Step 4: Delete agentic driver tests**

Run: `rm tests/unit/test_claude_agentic_driver.py`

**Step 5: Update factory tests**

Modify `tests/unit/test_driver_factory.py` to remove the agentic test:

Remove the test `test_get_cli_claude_agentic_driver` and the import of `ClaudeAgenticCliDriver`.

**Step 6: Run all tests to verify**

Run: `uv run pytest tests/ -v`
Expected: All PASS

**Step 7: Commit**

```bash
git add -A
git commit -m "refactor(drivers): remove ClaudeAgenticCliDriver, merge into ClaudeCliDriver"
```

---

## Task 9: Final Integration Test

**Files:**
- Test: `tests/integration/test_agentic_execution.py` (new)

**Step 1: Write integration test**

```python
# tests/integration/test_agentic_execution.py
"""Integration tests for agentic execution mode."""

import pytest
from unittest.mock import AsyncMock, patch

from amelia.core.orchestrator import create_orchestrator_graph
from amelia.core.state import ExecutionState, Task, TaskDAG, FileOperation, TaskStep
from amelia.core.types import Profile, Issue
from amelia.drivers.cli.claude import ClaudeStreamEvent


@pytest.fixture
def agentic_state():
    """Create execution state with agentic profile."""
    profile = Profile(
        name="test",
        driver="cli:claude",
        execution_mode="agentic",
        working_dir="/tmp/test"
    )
    issue = Issue(id="TEST-1", title="Test", description="Test issue")
    task = Task(
        id="1",
        description="Implement feature",
        files=[FileOperation(operation="create", path="test.py")],
        steps=[TaskStep(description="Write test", code="def test(): pass")]
    )
    plan = TaskDAG(tasks=[task], original_issue="TEST-1")

    return ExecutionState(
        profile=profile,
        issue=issue,
        plan=plan,
        human_approved=True
    )


class TestAgenticExecution:
    """Integration tests for agentic execution."""

    @pytest.mark.asyncio
    async def test_agentic_profile_triggers_agentic_execution(self, agentic_state):
        """Agentic profile should use execute_agentic method."""

        async def mock_execute_agentic(prompt, cwd, session_id=None):
            yield ClaudeStreamEvent(type="assistant", content="Working...")
            yield ClaudeStreamEvent(type="result", session_id="sess_001")

        with patch("amelia.core.orchestrator.DriverFactory") as mock_factory:
            mock_driver = AsyncMock()
            mock_driver.execute_agentic = mock_execute_agentic
            mock_factory.get_driver.return_value = mock_driver

            from amelia.core.orchestrator import call_developer_node
            result_state = await call_developer_node(agentic_state)

            assert result_state.plan.tasks[0].status == "completed"
```

**Step 2: Run integration test**

Run: `uv run pytest tests/integration/test_agentic_execution.py -v`
Expected: PASS

**Step 3: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All PASS

**Step 4: Run linting and type checking**

Run: `uv run ruff check amelia tests && uv run mypy amelia`
Expected: No errors

**Step 5: Commit**

```bash
git add tests/integration/test_agentic_execution.py
git commit -m "test(integration): add agentic execution integration tests"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Add ExecutionMode type | types.py, test_types.py |
| 2 | Add execution_mode/working_dir to Profile | types.py, test_types.py |
| 3 | Add workflow_status to ExecutionState | state.py, test_state.py |
| 4 | Add AgenticExecutionError | exceptions.py, test_exceptions.py |
| 5 | Add execute_agentic to ClaudeCliDriver | claude.py, test_claude_driver.py |
| 6 | Add agentic execution to Developer | developer.py, test_developer.py |
| 7 | Update orchestrator for agentic mode | orchestrator.py, test_orchestrator.py |
| 8 | Remove ClaudeAgenticCliDriver | factory.py, types.py, delete files |
| 9 | Integration test | test_agentic_execution.py |
