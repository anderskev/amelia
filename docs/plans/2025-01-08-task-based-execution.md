# Task-Based Execution Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable task-based Developer execution where each `### Task N:` block in Architect's plan spawns a fresh session, with review loops per task before proceeding to the next.

**Architecture:** Parse task count from plan markdown in `plan_validator_node`. Track task progression via new state fields. Route between tasks using a new `next_task_node` that commits, increments, and clears session for fresh context. Sequential execution with same-session review retries within each task.

**Tech Stack:** Python 3.12+, Pydantic, LangGraph, pytest, pytest-asyncio

---

## Task 1: Add Task Execution Fields to ExecutionState

**Files:**
- Modify: `amelia/core/state.py:38-116`
- Test: `tests/unit/core/test_execution_state.py`

**Step 1: Write the failing test for new state fields**

```python
# Add to tests/unit/core/test_execution_state.py

def test_task_execution_fields_have_correct_defaults():
    """Task execution tracking fields should have sensible defaults."""
    state = ExecutionState(profile_id="test")

    assert state.total_tasks is None  # None = legacy single-session mode
    assert state.current_task_index == 0  # 0-indexed
    assert state.task_review_iteration == 0  # Resets per task
    assert state.max_task_review_iterations == 5  # Default limit


def test_task_execution_fields_are_settable():
    """Task execution fields should be settable via model_copy."""
    state = ExecutionState(profile_id="test")

    updated = state.model_copy(update={
        "total_tasks": 3,
        "current_task_index": 1,
        "task_review_iteration": 2,
    })

    assert updated.total_tasks == 3
    assert updated.current_task_index == 1
    assert updated.task_review_iteration == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/core/test_execution_state.py -k "task_execution" -v`
Expected: FAIL with AttributeError for `total_tasks`

**Step 3: Add new fields to ExecutionState**

```python
# In amelia/core/state.py, add these fields after the existing review tracking fields:

    # Task execution tracking (for multi-task plans)
    total_tasks: int | None = None  # Parsed from plan (None = legacy single-session)
    current_task_index: int = 0  # 0-indexed, increments after each task passes review
    task_review_iteration: int = 0  # Resets to 0 when moving to next task
    max_task_review_iterations: int = 5  # Per-task limit (configurable via profile)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/core/test_execution_state.py -k "task_execution" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/state.py tests/unit/core/test_execution_state.py
git commit -m "feat(state): add task execution tracking fields"
```

---

## Task 2: Add Profile Field for max_task_review_iterations

**Files:**
- Modify: `amelia/core/types.py:37-73`
- Test: `tests/unit/core/test_types.py`

**Step 1: Write the failing test for profile field**

```python
# Add to tests/unit/core/test_types.py (create if doesn't exist)

from amelia.core.types import Profile


def test_profile_max_task_review_iterations_default():
    """Profile should have max_task_review_iterations with default value."""
    profile = Profile(
        name="test",
        driver="cli:claude",
        model="sonnet",
    )

    assert profile.max_task_review_iterations == 5


def test_profile_max_task_review_iterations_override():
    """Profile max_task_review_iterations should be configurable."""
    profile = Profile(
        name="test",
        driver="cli:claude",
        model="sonnet",
        max_task_review_iterations=10,
    )

    assert profile.max_task_review_iterations == 10
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/core/test_types.py -k "max_task_review" -v`
Expected: FAIL with validation error for unknown field

**Step 3: Add field to Profile**

```python
# In amelia/core/types.py, add after max_review_iterations field:

    max_task_review_iterations: int = 5  # Per-task review iteration limit (for task-based execution)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/core/test_types.py -k "max_task_review" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/types.py tests/unit/core/test_types.py
git commit -m "feat(profile): add max_task_review_iterations config field"
```

---

## Task 3: Add Task Count Parsing to plan_validator_node

**Files:**
- Modify: `amelia/core/orchestrator.py:128-207`
- Test: `tests/unit/core/test_plan_validator_node.py`

**Step 1: Write failing test for task count extraction**

```python
# Add to tests/unit/core/test_plan_validator_node.py

import pytest
from amelia.core.orchestrator import extract_task_count


def test_extract_task_count_returns_count_for_valid_tasks():
    """Should count ### Task N: patterns in plan markdown."""
    plan = """
# Implementation Plan

### Task 1: Setup

Do the setup.

### Task 2: Implementation

Do the implementation.

### Task 3: Testing

Run tests.
"""
    assert extract_task_count(plan) == 3


def test_extract_task_count_returns_none_for_no_tasks():
    """Should return None when no ### Task N: patterns found."""
    plan = """
# Implementation Plan

Some content without task markers.

## Section 1

More content.
"""
    assert extract_task_count(plan) is None


def test_extract_task_count_ignores_malformed_patterns():
    """Should only match exact ### Task N: pattern."""
    plan = """
### Task 1: Valid

Content.

#### Task 2: Wrong level (h4)

### Task: Missing number

### Task2: Missing space

### Task 3: Also valid
"""
    assert extract_task_count(plan) == 2  # Only Task 1 and Task 3
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/core/test_plan_validator_node.py -k "extract_task_count" -v`
Expected: FAIL with ImportError for `extract_task_count`

**Step 3: Implement extract_task_count function**

```python
# Add to amelia/core/orchestrator.py, near the top with other helper functions

import re


def extract_task_count(plan_markdown: str) -> int | None:
    """Extract task count from plan markdown by counting ### Task N: patterns.

    Args:
        plan_markdown: The markdown content of the plan.

    Returns:
        Number of tasks found, or None if no task patterns detected.
    """
    pattern = r"^### Task \d+:"
    matches = re.findall(pattern, plan_markdown, re.MULTILINE)
    return len(matches) if matches else None
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/core/test_plan_validator_node.py -k "extract_task_count" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py tests/unit/core/test_plan_validator_node.py
git commit -m "feat(orchestrator): add extract_task_count helper function"
```

---

## Task 4: Integrate Task Count into plan_validator_node Output

**Files:**
- Modify: `amelia/core/orchestrator.py:128-207` (plan_validator_node)
- Test: `tests/unit/core/test_plan_validator_node.py`

**Step 1: Write failing test for plan_validator_node returning total_tasks**

```python
# Add to tests/unit/core/test_plan_validator_node.py

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from amelia.core.orchestrator import plan_validator_node
from amelia.core.state import ExecutionState
from amelia.core.types import Profile


@pytest.fixture
def mock_profile():
    return Profile(
        name="test",
        driver="api:openrouter",
        model="anthropic/claude-3.5-sonnet",
    )


@pytest.fixture
def state_with_plan(tmp_path, mock_profile):
    plan_content = """
# Test Plan

### Task 1: First task

Do first thing.

### Task 2: Second task

Do second thing.
"""
    plan_path = tmp_path / "docs" / "plans" / "test-plan.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(plan_content)

    state = ExecutionState(
        profile_id="test",
        raw_architect_output=str(plan_path),
    )
    return state, plan_path


@pytest.mark.asyncio
async def test_plan_validator_sets_total_tasks(state_with_plan, mock_profile, tmp_path):
    """plan_validator_node should extract and return total_tasks from plan."""
    state, plan_path = state_with_plan

    # Mock the LLM call for plan validation
    mock_output = MagicMock()
    mock_output.goal = "Test goal"
    mock_output.key_files = ["file1.py"]

    mock_result = MagicMock()
    mock_result.output = mock_output

    config = {"configurable": {"profile": mock_profile}}

    with patch("amelia.core.orchestrator.resolve_plan_path", return_value=plan_path):
        with patch("amelia.core.orchestrator.Agent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(return_value=mock_result)
            mock_agent_class.return_value = mock_agent

            result = await plan_validator_node(state, config)

    assert result["total_tasks"] == 2


@pytest.mark.asyncio
async def test_plan_validator_sets_total_tasks_none_for_legacy_plans(tmp_path, mock_profile):
    """plan_validator_node should set total_tasks=None for plans without task markers."""
    plan_content = """
# Legacy Plan

No task markers here, just freeform instructions.

## Setup

Do setup.

## Implementation

Do implementation.
"""
    plan_path = tmp_path / "docs" / "plans" / "legacy-plan.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(plan_content)

    state = ExecutionState(
        profile_id="test",
        raw_architect_output=str(plan_path),
    )

    mock_output = MagicMock()
    mock_output.goal = "Legacy goal"
    mock_output.key_files = []

    mock_result = MagicMock()
    mock_result.output = mock_output

    config = {"configurable": {"profile": mock_profile}}

    with patch("amelia.core.orchestrator.resolve_plan_path", return_value=plan_path):
        with patch("amelia.core.orchestrator.Agent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(return_value=mock_result)
            mock_agent_class.return_value = mock_agent

            result = await plan_validator_node(state, config)

    assert result["total_tasks"] is None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/core/test_plan_validator_node.py -k "plan_validator_sets_total_tasks" -v`
Expected: FAIL with KeyError for `total_tasks` in result

**Step 3: Modify plan_validator_node to include total_tasks**

```python
# In amelia/core/orchestrator.py, modify plan_validator_node return statement
# Find the return statement (around line 200-207) and add total_tasks:

    # Parse task count from plan markdown
    total_tasks = extract_task_count(plan_content)

    return {
        "goal": result.output.goal,
        "plan_markdown": plan_content,
        "plan_path": plan_path,
        "key_files": result.output.key_files,
        "total_tasks": total_tasks,
    }
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/core/test_plan_validator_node.py -k "plan_validator_sets_total_tasks" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py tests/unit/core/test_plan_validator_node.py
git commit -m "feat(orchestrator): plan_validator_node extracts total_tasks from plan"
```

---

## Task 5: Modify call_developer_node for Task-Scoped Execution

**Files:**
- Modify: `amelia/core/orchestrator.py:481-542`
- Test: `tests/unit/core/test_developer_node.py`

**Step 1: Write failing test for task-scoped prompt injection**

```python
# Add to tests/unit/core/test_developer_node.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from amelia.core.orchestrator import call_developer_node
from amelia.core.state import ExecutionState
from amelia.core.types import Profile
from pathlib import Path


@pytest.fixture
def mock_profile_with_working_dir(tmp_path):
    return Profile(
        name="test",
        driver="api:openrouter",
        model="anthropic/claude-3.5-sonnet",
        working_dir=str(tmp_path),
    )


@pytest.fixture
def multi_task_state(tmp_path):
    plan_path = tmp_path / "docs" / "plans" / "plan.md"
    return ExecutionState(
        profile_id="test",
        goal="Implement feature",
        plan_markdown="### Task 1: Setup\n\n### Task 2: Build",
        plan_path=plan_path,
        total_tasks=2,
        current_task_index=0,
        driver_session_id="old-session-123",  # Should be cleared
    )


@pytest.mark.asyncio
async def test_developer_node_clears_session_for_task_execution(
    multi_task_state, mock_profile_with_working_dir
):
    """Developer node should clear driver_session_id for fresh task sessions."""
    config = {"configurable": {"profile": mock_profile_with_working_dir}}

    # Track what session_id is passed to the driver
    captured_session_id = None

    async def mock_run(state, profile):
        nonlocal captured_session_id
        captured_session_id = state.driver_session_id
        # Return minimal valid state updates
        yield ({"agentic_status": "completed"}, None)

    with patch("amelia.core.orchestrator.Developer") as mock_developer_class:
        mock_developer = MagicMock()
        mock_developer.run = mock_run
        mock_developer_class.return_value = mock_developer

        result = await call_developer_node(multi_task_state, config)

    # Should have cleared session_id before calling developer
    assert captured_session_id is None


@pytest.mark.asyncio
async def test_developer_node_injects_task_scoped_prompt(
    multi_task_state, mock_profile_with_working_dir
):
    """Developer node should inject task-specific prompt for multi-task execution."""
    config = {"configurable": {"profile": mock_profile_with_working_dir}}

    captured_goal = None

    async def mock_run(state, profile):
        nonlocal captured_goal
        captured_goal = state.goal
        yield ({"agentic_status": "completed"}, None)

    with patch("amelia.core.orchestrator.Developer") as mock_developer_class:
        mock_developer = MagicMock()
        mock_developer.run = mock_run
        mock_developer_class.return_value = mock_developer

        await call_developer_node(multi_task_state, config)

    # Should include task pointer in goal
    assert "Task 1" in captured_goal
    assert str(multi_task_state.plan_path) in captured_goal


@pytest.mark.asyncio
async def test_developer_node_preserves_session_for_legacy_mode(
    mock_profile_with_working_dir, tmp_path
):
    """Developer node should preserve session_id when total_tasks is None."""
    state = ExecutionState(
        profile_id="test",
        goal="Legacy goal",
        plan_markdown="Do stuff",
        total_tasks=None,  # Legacy mode
        driver_session_id="existing-session",
    )
    config = {"configurable": {"profile": mock_profile_with_working_dir}}

    captured_session_id = None

    async def mock_run(state, profile):
        nonlocal captured_session_id
        captured_session_id = state.driver_session_id
        yield ({"agentic_status": "completed"}, None)

    with patch("amelia.core.orchestrator.Developer") as mock_developer_class:
        mock_developer = MagicMock()
        mock_developer.run = mock_run
        mock_developer_class.return_value = mock_developer

        await call_developer_node(state, config)

    # Should preserve existing session_id in legacy mode
    assert captured_session_id == "existing-session"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/core/test_developer_node.py -k "task_" -v`
Expected: FAIL - session_id not cleared, task prompt not injected

**Step 3: Modify call_developer_node for task-based execution**

```python
# In amelia/core/orchestrator.py, modify call_developer_node
# Add this logic near the start of the function, after extracting state:

async def call_developer_node(
    state: ExecutionState, config: RunnableConfig
) -> dict[str, Any]:
    """Execute development task agentically using LLM tool-calling."""
    event_bus = config.get("configurable", {}).get("event_bus")
    workflow_id = config.get("configurable", {}).get("workflow_id", "unknown")
    profile: Profile = config["configurable"]["profile"]

    # Task-based execution: clear session and inject task-scoped prompt
    if state.total_tasks is not None:
        # Fresh session for each task
        state = state.model_copy(update={"driver_session_id": None})

        # Inject task-scoped prompt
        task_number = state.current_task_index + 1  # 1-indexed for display
        task_prompt = f"Execute Task {task_number} from plan at {state.plan_path}"
        state = state.model_copy(update={
            "goal": f"{state.goal}\n\n**Current Task:** {task_prompt}"
        })

    # ... rest of existing implementation
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/core/test_developer_node.py -k "task_" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py tests/unit/core/test_developer_node.py
git commit -m "feat(orchestrator): task-based execution in call_developer_node"
```

---

## Task 6: Create route_after_task_review Function

**Files:**
- Modify: `amelia/core/orchestrator.py`
- Test: `tests/unit/test_orchestrator_graph.py`

**Step 1: Write failing test for task review routing**

```python
# Add to tests/unit/test_orchestrator_graph.py

import pytest
from amelia.core.orchestrator import route_after_task_review
from amelia.core.state import ExecutionState
from amelia.core.types import Profile


@pytest.fixture
def mock_profile_task_review():
    return Profile(
        name="test",
        driver="cli:claude",
        model="sonnet",
        max_task_review_iterations=3,
    )


def test_route_after_task_review_ends_when_all_tasks_complete(mock_profile_task_review):
    """Should END when approved and all tasks complete."""
    state = ExecutionState(
        profile_id="test",
        total_tasks=2,
        current_task_index=1,  # On task 2 (0-indexed)
        last_review=MagicMock(approved=True),
    )
    config = {"configurable": {"profile": mock_profile_task_review}}

    result = route_after_task_review(state, config)
    assert result == "__end__"


def test_route_after_task_review_goes_to_next_task_when_approved(mock_profile_task_review):
    """Should go to next_task_node when approved and more tasks remain."""
    state = ExecutionState(
        profile_id="test",
        total_tasks=3,
        current_task_index=0,  # On task 1, more tasks remain
        last_review=MagicMock(approved=True),
    )
    config = {"configurable": {"profile": mock_profile_task_review}}

    result = route_after_task_review(state, config)
    assert result == "next_task_node"


def test_route_after_task_review_retries_developer_when_not_approved(mock_profile_task_review):
    """Should retry developer when review not approved and iterations remain."""
    state = ExecutionState(
        profile_id="test",
        total_tasks=2,
        current_task_index=0,
        task_review_iteration=1,  # Under limit of 3
        last_review=MagicMock(approved=False),
    )
    config = {"configurable": {"profile": mock_profile_task_review}}

    result = route_after_task_review(state, config)
    assert result == "developer"


def test_route_after_task_review_ends_on_max_iterations(mock_profile_task_review):
    """Should END when max iterations reached without approval."""
    state = ExecutionState(
        profile_id="test",
        total_tasks=2,
        current_task_index=0,
        task_review_iteration=3,  # At limit
        last_review=MagicMock(approved=False),
    )
    config = {"configurable": {"profile": mock_profile_task_review}}

    result = route_after_task_review(state, config)
    assert result == "__end__"


def test_route_after_task_review_uses_profile_max_iterations():
    """Should respect profile's max_task_review_iterations setting."""
    profile = Profile(
        name="test",
        driver="cli:claude",
        model="sonnet",
        max_task_review_iterations=10,
    )
    state = ExecutionState(
        profile_id="test",
        total_tasks=2,
        current_task_index=0,
        task_review_iteration=5,  # Under custom limit of 10
        last_review=MagicMock(approved=False),
    )
    config = {"configurable": {"profile": profile}}

    result = route_after_task_review(state, config)
    assert result == "developer"  # Should retry since under limit
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_orchestrator_graph.py -k "route_after_task_review" -v`
Expected: FAIL with ImportError for `route_after_task_review`

**Step 3: Implement route_after_task_review**

```python
# Add to amelia/core/orchestrator.py, near route_after_review

def route_after_task_review(
    state: ExecutionState, config: RunnableConfig
) -> Literal["developer", "next_task_node", "__end__"]:
    """Route after task review: next task, retry developer, or end.

    Args:
        state: Current execution state with task tracking fields.
        config: Runnable config with profile.

    Returns:
        "next_task_node" if approved and more tasks remain.
        "developer" if not approved and iterations remain.
        "__end__" if all tasks complete or max iterations reached.
    """
    profile: Profile = config["configurable"]["profile"]

    if state.last_review and state.last_review.approved:
        # Task approved - check if more tasks remain
        if state.current_task_index + 1 >= state.total_tasks:
            return "__end__"  # All tasks complete
        return "next_task_node"  # Move to next task

    # Not approved - check iteration limit
    max_iterations = profile.max_task_review_iterations
    if state.task_review_iteration >= max_iterations:
        return "__end__"  # Halt on repeated failure

    return "developer"  # Retry with feedback
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_orchestrator_graph.py -k "route_after_task_review" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py tests/unit/test_orchestrator_graph.py
git commit -m "feat(orchestrator): add route_after_task_review routing function"
```

---

## Task 7: Create next_task_node

**Files:**
- Modify: `amelia/core/orchestrator.py`
- Test: `tests/unit/test_orchestrator_graph.py`

**Step 1: Write failing test for next_task_node**

```python
# Add to tests/unit/test_orchestrator_graph.py

import pytest
from unittest.mock import patch, MagicMock
from amelia.core.orchestrator import next_task_node
from amelia.core.state import ExecutionState
from amelia.core.types import Profile


@pytest.fixture
def task_state_for_next():
    return ExecutionState(
        profile_id="test",
        total_tasks=3,
        current_task_index=0,
        task_review_iteration=2,
        driver_session_id="session-123",
    )


@pytest.mark.asyncio
async def test_next_task_node_increments_task_index(task_state_for_next):
    """next_task_node should increment current_task_index."""
    config = {"configurable": {"profile": MagicMock()}}

    with patch("amelia.core.orchestrator.commit_task_changes"):
        result = await next_task_node(task_state_for_next, config)

    assert result["current_task_index"] == 1


@pytest.mark.asyncio
async def test_next_task_node_resets_review_iteration(task_state_for_next):
    """next_task_node should reset task_review_iteration to 0."""
    config = {"configurable": {"profile": MagicMock()}}

    with patch("amelia.core.orchestrator.commit_task_changes"):
        result = await next_task_node(task_state_for_next, config)

    assert result["task_review_iteration"] == 0


@pytest.mark.asyncio
async def test_next_task_node_clears_session_id(task_state_for_next):
    """next_task_node should clear driver_session_id for fresh session."""
    config = {"configurable": {"profile": MagicMock()}}

    with patch("amelia.core.orchestrator.commit_task_changes"):
        result = await next_task_node(task_state_for_next, config)

    assert result["driver_session_id"] is None


@pytest.mark.asyncio
async def test_next_task_node_commits_changes(task_state_for_next):
    """next_task_node should commit current task changes."""
    config = {"configurable": {"profile": MagicMock()}}

    with patch("amelia.core.orchestrator.commit_task_changes") as mock_commit:
        await next_task_node(task_state_for_next, config)

    mock_commit.assert_called_once_with(task_state_for_next, config)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_orchestrator_graph.py -k "next_task_node" -v`
Expected: FAIL with ImportError for `next_task_node`

**Step 3: Implement next_task_node**

```python
# Add to amelia/core/orchestrator.py

async def next_task_node(
    state: ExecutionState, config: RunnableConfig
) -> dict[str, Any]:
    """Transition to next task: commit changes, increment index, reset iteration.

    Args:
        state: Current execution state with task tracking.
        config: Runnable config.

    Returns:
        State update with incremented task index, reset iteration, cleared session.
    """
    # Commit current task changes
    await commit_task_changes(state, config)

    return {
        "current_task_index": state.current_task_index + 1,
        "task_review_iteration": 0,
        "driver_session_id": None,  # Fresh session for next task
    }


async def commit_task_changes(state: ExecutionState, config: RunnableConfig) -> None:
    """Commit changes for completed task.

    Args:
        state: Current execution state.
        config: Runnable config with profile.
    """
    profile: Profile = config["configurable"]["profile"]
    working_dir = Path(profile.working_dir) if profile.working_dir else Path.cwd()

    task_number = state.current_task_index + 1

    # Stage all changes
    result = await run_shell(f"git add -A", cwd=working_dir)
    if not result.success:
        logger.warning("Failed to stage changes for task commit", error=result.stderr)
        return

    # Check if there are staged changes
    status_result = await run_shell("git diff --cached --quiet", cwd=working_dir)
    if status_result.success:
        logger.info("No changes to commit for task", task=task_number)
        return

    # Commit with task reference
    issue_key = state.issue.id if state.issue else "unknown"
    commit_msg = f"feat({issue_key}): complete task {task_number}"

    commit_result = await run_shell(
        f'git commit -m "{commit_msg}"',
        cwd=working_dir,
    )
    if commit_result.success:
        logger.info("Committed task changes", task=task_number, message=commit_msg)
    else:
        logger.warning("Failed to commit task changes", error=commit_result.stderr)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_orchestrator_graph.py -k "next_task_node" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py tests/unit/test_orchestrator_graph.py
git commit -m "feat(orchestrator): add next_task_node and commit_task_changes"
```

---

## Task 8: Increment task_review_iteration in Reviewer Node

**Files:**
- Modify: `amelia/core/orchestrator.py` (reviewer node)
- Test: `tests/unit/test_orchestrator_graph.py`

**Step 1: Write failing test for iteration increment**

```python
# Add to tests/unit/test_orchestrator_graph.py

@pytest.mark.asyncio
async def test_reviewer_node_increments_task_review_iteration():
    """Reviewer node should increment task_review_iteration for task-based execution."""
    state = ExecutionState(
        profile_id="test",
        total_tasks=2,  # Task-based mode
        current_task_index=0,
        task_review_iteration=1,
    )
    profile = Profile(name="test", driver="cli:claude", model="sonnet")
    config = {"configurable": {"profile": profile}}

    # Mock reviewer to return a review result
    mock_review = MagicMock(approved=False)

    with patch("amelia.core.orchestrator.Reviewer") as mock_reviewer_class:
        mock_reviewer = MagicMock()
        mock_reviewer.review = AsyncMock(return_value=mock_review)
        mock_reviewer_class.return_value = mock_reviewer

        result = await call_reviewer_node(state, config)

    assert result["task_review_iteration"] == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_orchestrator_graph.py -k "increments_task_review" -v`
Expected: FAIL - task_review_iteration not in result

**Step 3: Modify call_reviewer_node to increment task_review_iteration**

```python
# In amelia/core/orchestrator.py, modify call_reviewer_node return statement
# Add task_review_iteration increment for task-based execution:

    # Build return dict
    result_dict = {
        "last_review": review_result,
        "review_iteration": state.review_iteration + 1,
    }

    # Increment task review iteration for task-based execution
    if state.total_tasks is not None:
        result_dict["task_review_iteration"] = state.task_review_iteration + 1

    return result_dict
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_orchestrator_graph.py -k "increments_task_review" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py tests/unit/test_orchestrator_graph.py
git commit -m "feat(orchestrator): increment task_review_iteration in reviewer node"
```

---

## Task 9: Wire Task-Based Routing into LangGraph

**Files:**
- Modify: `amelia/core/orchestrator.py` (graph construction)
- Test: `tests/unit/test_orchestrator_graph.py`

**Step 1: Write failing test for graph edge from next_task_node**

```python
# Add to tests/unit/test_orchestrator_graph.py

def test_orchestrator_graph_has_next_task_node():
    """Orchestrator graph should include next_task_node."""
    graph = build_orchestrator_graph()

    # Check that next_task_node exists in the graph
    assert "next_task_node" in graph.nodes


def test_orchestrator_graph_routes_to_next_task():
    """Graph should route from reviewer to next_task_node when conditions met."""
    graph = build_orchestrator_graph()

    # Verify conditional edges exist from reviewer
    # The graph should have a conditional edge that can route to next_task_node
    edges = graph.edges

    # Check that reviewer has outgoing conditional edge
    reviewer_edges = [e for e in edges if e[0] == "reviewer"]
    assert any("next_task_node" in str(e) or "conditional" in str(e) for e in reviewer_edges)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_orchestrator_graph.py -k "next_task" -v`
Expected: FAIL - next_task_node not in graph

**Step 3: Modify graph construction to include task-based routing**

```python
# In amelia/core/orchestrator.py, modify the graph construction
# Replace the simple route_after_review edge with conditional routing:

def build_orchestrator_graph() -> StateGraph:
    """Build the main orchestrator LangGraph."""
    builder = StateGraph(ExecutionState)

    # Add existing nodes
    builder.add_node("architect", call_architect_node)
    builder.add_node("plan_validator", plan_validator_node)
    builder.add_node("human_approval", human_approval_node)
    builder.add_node("developer", call_developer_node)
    builder.add_node("reviewer", call_reviewer_node)
    builder.add_node("next_task_node", next_task_node)  # NEW

    # Add edges
    builder.add_edge(START, "architect")
    builder.add_edge("architect", "plan_validator")
    builder.add_edge("plan_validator", "human_approval")
    builder.add_conditional_edges(
        "human_approval",
        route_approval,
        {"approve": "developer", "reject": END},
    )
    builder.add_edge("developer", "reviewer")

    # Conditional routing after review - handles both legacy and task-based
    builder.add_conditional_edges(
        "reviewer",
        route_after_review_or_task,
        {
            "developer": "developer",
            "next_task_node": "next_task_node",
            "__end__": END,
        },
    )

    # next_task_node loops back to developer for the next task
    builder.add_edge("next_task_node", "developer")

    return builder.compile(interrupt_before=["human_approval"])


def route_after_review_or_task(
    state: ExecutionState, config: RunnableConfig
) -> Literal["developer", "next_task_node", "__end__"]:
    """Route after review: handles both legacy and task-based execution.

    For task-based execution (total_tasks is set), uses route_after_task_review.
    For legacy execution (total_tasks is None), uses route_after_review.
    """
    if state.total_tasks is not None:
        return route_after_task_review(state, config)
    return route_after_review(state, config)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_orchestrator_graph.py -k "next_task" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py tests/unit/test_orchestrator_graph.py
git commit -m "feat(orchestrator): wire task-based routing into LangGraph"
```

---

## Task 10: Integration Test for Multi-Task Execution

**Files:**
- Create: `tests/integration/test_task_based_execution.py`

**Step 1: Write integration test for full task loop**

```python
# Create tests/integration/test_task_based_execution.py

"""Integration tests for task-based execution flow."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from amelia.core.orchestrator import build_orchestrator_graph
from amelia.core.state import ExecutionState
from amelia.core.types import Profile, Issue


@pytest.fixture
def multi_task_plan_content():
    return """# Test Plan

### Task 1: Create module

Create the new module file.

### Task 2: Add tests

Add unit tests for the module.

### Task 3: Update docs

Update documentation.
"""


@pytest.fixture
def integration_profile(tmp_path):
    return Profile(
        name="test",
        driver="api:openrouter",
        model="anthropic/claude-3.5-sonnet",
        working_dir=str(tmp_path),
        max_task_review_iterations=2,
    )


@pytest.fixture
def integration_issue():
    return Issue(
        id="TEST-123",
        title="Test Issue",
        description="Test description",
    )


@pytest.mark.asyncio
async def test_task_based_execution_processes_all_tasks(
    tmp_path, multi_task_plan_content, integration_profile, integration_issue
):
    """Full integration test: task-based execution processes all 3 tasks."""
    # Setup plan file
    plan_path = tmp_path / "docs" / "plans" / "test-plan.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(multi_task_plan_content)

    # Initialize git repo for commits
    import subprocess
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)

    # Create initial commit
    (tmp_path / "README.md").write_text("# Test")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=tmp_path, capture_output=True)

    state = ExecutionState(
        profile_id="test",
        issue=integration_issue,
        raw_architect_output=str(plan_path),
        human_approved=True,
    )

    # Track task indices seen by developer
    task_indices_seen = []

    async def mock_developer_run(dev_state, profile):
        task_indices_seen.append(dev_state.current_task_index)
        # Simulate making a change
        (tmp_path / f"file_{dev_state.current_task_index}.py").write_text("# code")
        yield ({"agentic_status": "completed"}, None)

    # Mock reviewer to always approve
    mock_review = MagicMock(approved=True)

    config = {"configurable": {"profile": integration_profile}}

    with patch("amelia.core.orchestrator.Developer") as mock_dev_class:
        with patch("amelia.core.orchestrator.Reviewer") as mock_rev_class:
            with patch("amelia.core.orchestrator.Agent"):  # For plan validator
                mock_dev = MagicMock()
                mock_dev.run = mock_developer_run
                mock_dev_class.return_value = mock_dev

                mock_rev = MagicMock()
                mock_rev.review = AsyncMock(return_value=mock_review)
                mock_rev_class.return_value = mock_rev

                graph = build_orchestrator_graph()

                # Run the graph
                final_state = None
                async for event in graph.astream(state, config):
                    if isinstance(event, dict):
                        final_state = event

    # Verify all 3 tasks were processed (indices 0, 1, 2)
    assert task_indices_seen == [0, 1, 2]

    # Verify 3 commits were made (one per task)
    result = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    # Initial commit + 3 task commits = 4 commits
    commit_count = len(result.stdout.strip().split("\n"))
    assert commit_count == 4


@pytest.mark.asyncio
async def test_task_based_execution_halts_on_max_iterations(
    tmp_path, multi_task_plan_content, integration_profile, integration_issue
):
    """Task execution should halt when max review iterations reached."""
    plan_path = tmp_path / "docs" / "plans" / "test-plan.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(multi_task_plan_content)

    state = ExecutionState(
        profile_id="test",
        issue=integration_issue,
        raw_architect_output=str(plan_path),
        human_approved=True,
    )

    developer_calls = 0

    async def mock_developer_run(dev_state, profile):
        nonlocal developer_calls
        developer_calls += 1
        yield ({"agentic_status": "completed"}, None)

    # Mock reviewer to always reject
    mock_review = MagicMock(approved=False)

    config = {"configurable": {"profile": integration_profile}}

    with patch("amelia.core.orchestrator.Developer") as mock_dev_class:
        with patch("amelia.core.orchestrator.Reviewer") as mock_rev_class:
            with patch("amelia.core.orchestrator.Agent"):
                mock_dev = MagicMock()
                mock_dev.run = mock_developer_run
                mock_dev_class.return_value = mock_dev

                mock_rev = MagicMock()
                mock_rev.review = AsyncMock(return_value=mock_review)
                mock_rev_class.return_value = mock_rev

                graph = build_orchestrator_graph()

                async for _ in graph.astream(state, config):
                    pass

    # With max_task_review_iterations=2, should call developer 2 times then halt
    # (initial + 1 retry = 2 calls on first task)
    assert developer_calls == 2
```

**Step 2: Run test to verify the integration works**

Run: `uv run pytest tests/integration/test_task_based_execution.py -v`
Expected: PASS (once all previous tasks are complete)

**Step 3: Commit**

```bash
git add tests/integration/test_task_based_execution.py
git commit -m "test(integration): add task-based execution integration tests"
```

---

## Task 11: Run Full Test Suite and Verify

**Files:**
- All modified files

**Step 1: Run linting**

Run: `uv run ruff check amelia tests`
Expected: No errors

**Step 2: Run type checking**

Run: `uv run mypy amelia`
Expected: No errors

**Step 3: Run all tests**

Run: `uv run pytest -v`
Expected: All tests pass

**Step 4: Fix any issues found**

Address any failing tests or type errors discovered.

**Step 5: Final commit**

```bash
git add -A
git commit -m "chore: fix any issues from full test suite"
```

---

## Summary

This plan implements task-based execution for the Developer agent with:

1. **State tracking** (`total_tasks`, `current_task_index`, `task_review_iteration`)
2. **Task parsing** (`extract_task_count` function)
3. **Fresh sessions** (cleared `driver_session_id` per task)
4. **Task-scoped prompts** (injected in `call_developer_node`)
5. **Routing logic** (`route_after_task_review`, `route_after_review_or_task`)
6. **Task transitions** (`next_task_node` with commits)
7. **Backward compatibility** (legacy mode when `total_tasks` is None)

All changes follow TDD with tests written before implementation.
