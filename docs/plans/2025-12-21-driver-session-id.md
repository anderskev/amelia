# Driver Session ID Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable driver session continuity by passing `driver_session_id` from ExecutionState to driver calls and capturing returned session IDs.

**Architecture:** The `driver_session_id` field exists in ExecutionState but is never used. We'll thread it through orchestrator nodes → agents → driver calls, and capture session IDs from driver responses (ClaudeCliDriver returns session_id in result events).

**Tech Stack:** Python, Pydantic, LangGraph, pytest

---

## Batch 1 [LOW RISK]
*Add session_id return type to driver methods and tests*

### Step 1.1: Write failing test for ClaudeCliDriver session_id capture

**Files:**
- Test: `tests/unit/test_claude_driver.py`

```python
async def test_generate_returns_session_id_from_result(
    mock_subprocess_process_factory: Callable[..., AsyncMock],
) -> None:
    """Test that generate returns session_id when schema is provided."""
    from amelia.drivers.cli.claude import ClaudeCliDriver
    from amelia.core.state import AgentMessage
    from pydantic import BaseModel

    class TestOutput(BaseModel):
        value: str

    # Result event with session_id
    result_json = json.dumps({
        "type": "result",
        "subtype": "success",
        "session_id": "sess-abc123",
        "structured_output": {"value": "test"}
    })

    mock_process = mock_subprocess_process_factory(
        stdout_lines=[result_json.encode()],
        return_code=0
    )

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        driver = ClaudeCliDriver()
        messages = [AgentMessage(role="user", content="test")]
        result = await driver.generate(messages, schema=TestOutput)

    # Result should be tuple of (output, session_id)
    assert isinstance(result, tuple)
    output, session_id = result
    assert isinstance(output, TestOutput)
    assert output.value == "test"
    assert session_id == "sess-abc123"
```

**Step 1.2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_claude_driver.py::test_generate_returns_session_id_from_result -v`
Expected: FAIL - current implementation returns just the output, not a tuple

**Step 1.3: Write test for generate without schema (returns string)**

**Files:**
- Test: `tests/unit/test_claude_driver.py`

```python
async def test_generate_returns_session_id_without_schema(
    mock_subprocess_process_factory: Callable[..., AsyncMock],
) -> None:
    """Test that generate returns session_id even without schema."""
    from amelia.drivers.cli.claude import ClaudeCliDriver
    from amelia.core.state import AgentMessage

    mock_process = mock_subprocess_process_factory(
        stdout_lines=[b"plain text response"],
        return_code=0
    )

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        driver = ClaudeCliDriver()
        messages = [AgentMessage(role="user", content="test")]
        result = await driver.generate(messages)

    # Without JSON result wrapper, session_id is None
    assert isinstance(result, tuple)
    output, session_id = result
    assert output == "plain text response"
    assert session_id is None
```

**Step 1.4: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_claude_driver.py::test_generate_returns_session_id_without_schema -v`
Expected: FAIL

---

## Batch 2 [MEDIUM RISK]
*Update ClaudeCliDriver to return session_id*

### Step 2.1: Define GenerateResult type alias

**Files:**
- Modify: `amelia/drivers/base.py`

Add at the top of the file, after imports:

```python
# Type alias for generate return value: (output, session_id)
# output is str when no schema, or instance of schema when schema provided
# session_id is None when driver doesn't support sessions or no session was returned
GenerateResult = tuple[Any, str | None]
```

Update the DriverInterface.generate docstring to indicate it returns GenerateResult.

### Step 2.2: Update ClaudeCliDriver._generate_impl to return tuple

**Files:**
- Modify: `amelia/drivers/cli/claude.py:276-452`

Track session_id through the method and return `(output, session_id)`:

1. Initialize `session_id_result: str | None = None` at start
2. When parsing result wrapper (line ~383), capture `session_id_result = data.get("session_id")`
3. Change all return statements to return tuple:
   - Line ~440: `return (schema.model_validate(data), session_id_result)`
   - Line ~447: `return (stdout_str, session_id_result)`

### Step 2.3: Run tests to verify they pass

Run: `uv run pytest tests/unit/test_claude_driver.py -v -k "session_id"`
Expected: PASS

### Step 2.4: Run all driver tests to ensure no regressions

Run: `uv run pytest tests/unit/test_claude_driver.py -v`
Expected: All tests should pass (or we need to update tests expecting single return value)

### Step 2.5: Update ApiDriver.generate to return tuple

**Files:**
- Modify: `amelia/drivers/api/openai.py:49-122`

ApiDriver doesn't have native session support, so just wrap returns in tuple with None session_id:

```python
# Line ~120: return (result.output, None)
```

### Step 2.6: Run ApiDriver tests

Run: `uv run pytest tests/unit/test_api_driver*.py -v`
Expected: PASS (may need test updates)

### Step 2.7: Commit batch 2

```bash
git add amelia/drivers/base.py amelia/drivers/cli/claude.py amelia/drivers/api/openai.py tests/unit/test_claude_driver.py
git commit -m "feat(drivers): return session_id from generate method

- Add GenerateResult type alias to base.py
- ClaudeCliDriver captures session_id from result events
- ApiDriver returns None session_id (no native support)
- Add tests for session_id capture

Part of #125"
```

---

## Batch 3 [LOW RISK]
*Update agents to accept and pass session_id*

### Step 3.1: Write failing test for Architect passing session_id

**Files:**
- Test: `tests/unit/agents/test_architect_context.py`

```python
async def test_architect_passes_session_id_to_driver(
    mock_execution_state_factory: Callable[..., ExecutionState],
    mock_async_driver_factory: Callable[..., AsyncMock],
) -> None:
    """Test that Architect passes session_id from state to driver."""
    from amelia.agents.architect import Architect, ExecutionPlanOutput
    from amelia.core.state import ExecutionPlan, ExecutionBatch, PlanStep

    # Create mock plan output
    mock_plan = ExecutionPlan(
        goal="Test",
        batches=(ExecutionBatch(
            batch_number=1,
            steps=(PlanStep(id="s1", description="test", action_type="code"),),
            risk_summary="low",
        ),),
        total_estimated_minutes=5,
        tdd_approach=True,
    )
    mock_output = ExecutionPlanOutput(plan=mock_plan, reasoning="test")

    # Driver returns (output, new_session_id)
    mock_driver = mock_async_driver_factory(generate_return=(mock_output, "new-sess-456"))

    state = mock_execution_state_factory(driver_session_id="existing-sess-123")

    architect = Architect(mock_driver)
    await architect.generate_execution_plan(state.issue, state)

    # Verify driver was called with session_id from state
    mock_driver.generate.assert_called_once()
    call_kwargs = mock_driver.generate.call_args.kwargs
    assert call_kwargs.get("session_id") == "existing-sess-123"
```

**Step 3.2: Run test to verify it fails**

Run: `uv run pytest tests/unit/agents/test_architect_context.py::test_architect_passes_session_id_to_driver -v`
Expected: FAIL - Architect doesn't pass session_id

### Step 3.3: Update Architect.generate_execution_plan to pass session_id

**Files:**
- Modify: `amelia/agents/architect.py:406-463`

Add `session_id=state.driver_session_id` to the driver.generate call:

```python
# Line ~442:
response = await self.driver.generate(
    messages=messages,
    schema=ExecutionPlanOutput,
    cwd=state.profile.working_dir,
    session_id=state.driver_session_id,  # Add this
)
```

Also need to unpack the tuple return:
```python
response, _new_session_id = await self.driver.generate(...)
```

### Step 3.4: Run tests

Run: `uv run pytest tests/unit/agents/test_architect_context.py -v`
Expected: PASS

### Step 3.5: Update Reviewer._single_review to pass session_id

**Files:**
- Modify: `amelia/agents/reviewer.py:211-272`

```python
# Line ~250-254:
response, _new_session_id = await self.driver.generate(
    messages=prompt_messages,
    schema=ReviewResponse,
    cwd=state.profile.working_dir,
    session_id=state.driver_session_id,  # Add this
)
```

### Step 3.6: Add test for Reviewer session_id passing

**Files:**
- Test: `tests/unit/agents/test_reviewer_context.py`

```python
async def test_reviewer_passes_session_id_to_driver(
    mock_execution_state_factory: Callable[..., ExecutionState],
    mock_async_driver_factory: Callable[..., AsyncMock],
    mock_review_response_factory: Callable[..., ReviewResponse],
) -> None:
    """Test that Reviewer passes session_id from state to driver."""
    from amelia.agents.reviewer import Reviewer

    mock_response = mock_review_response_factory(approved=True)
    mock_driver = mock_async_driver_factory(generate_return=(mock_response, "new-sess"))

    state = mock_execution_state_factory(
        driver_session_id="review-sess-123",
        code_changes_for_review="diff content",
    )

    reviewer = Reviewer(mock_driver)
    await reviewer._single_review(state, "diff", "General", workflow_id="wf-1")

    mock_driver.generate.assert_called_once()
    call_kwargs = mock_driver.generate.call_args.kwargs
    assert call_kwargs.get("session_id") == "review-sess-123"
```

### Step 3.7: Run Reviewer tests

Run: `uv run pytest tests/unit/agents/test_reviewer_context.py -v`
Expected: PASS

### Step 3.8: Commit batch 3

```bash
git add amelia/agents/architect.py amelia/agents/reviewer.py tests/unit/agents/
git commit -m "feat(agents): pass session_id from state to driver

- Architect passes driver_session_id to generate()
- Reviewer passes driver_session_id to generate()
- Add tests verifying session_id is passed

Part of #125"
```

---

## Batch 4 [MEDIUM RISK]
*Update orchestrator nodes to capture and store session_id in state*

### Step 4.1: Write failing test for orchestrator session_id update

**Files:**
- Test: `tests/unit/test_orchestrator_graph.py`

```python
async def test_architect_node_updates_driver_session_id(
    mock_execution_state_factory: Callable[..., ExecutionState],
) -> None:
    """Test that call_architect_node captures and returns driver_session_id."""
    from amelia.core.orchestrator import call_architect_node
    from amelia.drivers.factory import DriverFactory
    from unittest.mock import patch, AsyncMock

    state = mock_execution_state_factory()
    config = {"configurable": {"thread_id": "wf-123"}}

    # Mock the driver to return a session_id
    mock_driver = AsyncMock()
    mock_plan = state.execution_plan or mock_execution_plan_factory()()
    mock_driver.generate.return_value = (
        ExecutionPlanOutput(plan=mock_plan, reasoning="test"),
        "captured-session-id"
    )

    with patch.object(DriverFactory, "get_driver", return_value=mock_driver):
        result = await call_architect_node(state, config)

    assert "driver_session_id" in result
    assert result["driver_session_id"] == "captured-session-id"
```

**Step 4.2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_orchestrator_graph.py::test_architect_node_updates_driver_session_id -v`
Expected: FAIL

### Step 4.3: Update call_architect_node to capture session_id

**Files:**
- Modify: `amelia/core/orchestrator.py:96-159`

In `call_architect_node`, the Architect agent returns the plan. We need to:
1. Have Architect return the session_id it received
2. Update the node to return `driver_session_id` in the state update

First, update Architect.generate_execution_plan to return session_id:

**Files:**
- Modify: `amelia/agents/architect.py:406-463`

Change return type and return the session_id:
```python
async def generate_execution_plan(
    self,
    issue: Issue,
    state: ExecutionState,
) -> tuple[ExecutionPlan, str | None]:
    """Generate batched execution plan for an issue.

    Returns:
        Tuple of (validated ExecutionPlan, session_id from driver).
    """
    # ... existing code ...

    response, new_session_id = await self.driver.generate(
        messages=messages,
        schema=ExecutionPlanOutput,
        cwd=state.profile.working_dir,
        session_id=state.driver_session_id,
    )

    # ... validation code ...

    return validated_plan, new_session_id
```

Then update orchestrator to capture it:
```python
# In call_architect_node, ~line 145-148:
execution_plan, new_session_id = await architect.generate_execution_plan(
    issue=state.issue,
    state=state,
)

return {
    "execution_plan": execution_plan,
    "driver_session_id": new_session_id,
}
```

### Step 4.4: Update call_reviewer_node similarly

**Files:**
- Modify: `amelia/core/orchestrator.py:383-423`

Update Reviewer.review to return session_id, then capture in orchestrator:

```python
# In call_reviewer_node:
review_result, new_session_id = await reviewer.review(state, code_changes, workflow_id=workflow_id)

return {
    "last_review": review_result,
    "driver_session_id": new_session_id,
}
```

### Step 4.5: Update Architect.plan to handle tuple return

**Files:**
- Modify: `amelia/agents/architect.py:348-404`

The `plan` method calls `generate_execution_plan` and needs to handle tuple return:
```python
execution_plan, _session_id = await self.generate_execution_plan(state.issue, state)
```

### Step 4.6: Run orchestrator tests

Run: `uv run pytest tests/unit/test_orchestrator_graph.py -v`
Expected: PASS

### Step 4.7: Run all tests to check for regressions

Run: `uv run pytest tests/unit/ -v`
Expected: PASS (fix any failures from API changes)

### Step 4.8: Commit batch 4

```bash
git add amelia/core/orchestrator.py amelia/agents/architect.py amelia/agents/reviewer.py tests/
git commit -m "feat(core): orchestrator captures and stores driver_session_id

- Architect.generate_execution_plan returns (plan, session_id)
- Reviewer.review returns (result, session_id)
- Orchestrator nodes update driver_session_id in state
- Session continuity now persisted across workflow steps

Closes #125"
```

---

## Batch 5 [LOW RISK]
*Final integration test and cleanup*

### Step 5.1: Write integration test for session continuity

**Files:**
- Create: `tests/integration/test_session_continuity.py`

```python
"""Integration tests for driver session continuity."""
import pytest
from unittest.mock import AsyncMock, patch

from amelia.core.orchestrator import call_architect_node, call_reviewer_node
from amelia.core.state import ExecutionState
from amelia.drivers.factory import DriverFactory


@pytest.fixture
def mock_cli_driver_with_session():
    """Create a mock CLI driver that returns session_id."""
    driver = AsyncMock()
    # First call (architect) returns session-1
    # Second call (reviewer) returns session-2
    driver.generate.side_effect = [
        (mock_plan_output, "session-1"),
        (mock_review_response, "session-2"),
    ]
    return driver


async def test_session_id_flows_through_workflow(
    mock_execution_state_factory,
    mock_cli_driver_with_session,
):
    """Test that session_id is captured and passed between nodes."""
    # Start with no session
    state = mock_execution_state_factory(driver_session_id=None)
    config = {"configurable": {"thread_id": "wf-test"}}

    with patch.object(DriverFactory, "get_driver", return_value=mock_cli_driver_with_session):
        # Architect captures session-1
        arch_result = await call_architect_node(state, config)
        assert arch_result["driver_session_id"] == "session-1"

        # Update state with captured session
        state = state.model_copy(update=arch_result)
        assert state.driver_session_id == "session-1"

        # Reviewer uses session-1, captures session-2
        state = state.model_copy(update={"code_changes_for_review": "diff"})
        review_result = await call_reviewer_node(state, config)
        assert review_result["driver_session_id"] == "session-2"
```

### Step 5.2: Run integration test

Run: `uv run pytest tests/integration/test_session_continuity.py -v`
Expected: PASS

### Step 5.3: Run full test suite

Run: `uv run pytest`
Expected: All tests pass

### Step 5.4: Run linting and type checking

Run: `uv run ruff check amelia tests && uv run mypy amelia`
Expected: No errors

### Step 5.5: Final commit

```bash
git add tests/integration/test_session_continuity.py
git commit -m "test: add integration test for session continuity

Verifies that driver_session_id flows through the workflow:
- Architect captures and stores session_id
- Session is passed to subsequent agent calls
- Each node updates session_id in state

Part of #125"
```

---

## Summary

**Files Modified:**
- `amelia/drivers/base.py` - Add GenerateResult type alias
- `amelia/drivers/cli/claude.py` - Return (output, session_id) tuple
- `amelia/drivers/api/openai.py` - Return (output, None) tuple
- `amelia/agents/architect.py` - Pass and return session_id
- `amelia/agents/reviewer.py` - Pass and return session_id
- `amelia/core/orchestrator.py` - Capture session_id in state updates

**Files Created:**
- `tests/integration/test_session_continuity.py`

**Tests Added:**
- `test_generate_returns_session_id_from_result`
- `test_generate_returns_session_id_without_schema`
- `test_architect_passes_session_id_to_driver`
- `test_reviewer_passes_session_id_to_driver`
- `test_architect_node_updates_driver_session_id`
- `test_session_id_flows_through_workflow`
