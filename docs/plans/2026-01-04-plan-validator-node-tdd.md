# Plan Validator Node TDD Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a `plan_validator_node` that transforms raw architect output into structured `PlanOutput`, replacing the fragile regex-based goal extraction.

**Architecture:** A new LangGraph node sits between architect_node and human_approval_node. It reads the plan file written by the architect, uses an LLM to extract structured fields (goal, plan_markdown, key_files), and returns them as state updates. The Profile type gains an optional `validator_model` field for using a fast/cheap model.

**Tech Stack:** Python 3.12+, Pydantic v2, LangGraph, pytest-asyncio

**Related Design Doc:** `docs/plans/2026-01-04-plan-validator-node-design.md`

---

## Task 1: Add `validator_model` Field to Profile

**Files:**
- Modify: `amelia/core/types.py:41-74` (Profile class)
- Test: `tests/unit/core/test_types.py` (create if needed)

**Step 1: Write the failing test**

Create or update `tests/unit/core/test_types.py`:

```python
"""Tests for amelia.core.types module."""

from amelia.core.types import Profile


class TestProfile:
    """Tests for Profile model."""

    def test_profile_validator_model_defaults_to_none(self) -> None:
        """Profile should have validator_model defaulting to None."""
        profile = Profile(
            name="test",
            driver="api:openrouter",
            model="gpt-4",
            tracker="github",
        )
        assert profile.validator_model is None

    def test_profile_validator_model_can_be_set(self) -> None:
        """Profile should accept validator_model as optional string."""
        profile = Profile(
            name="test",
            driver="api:openrouter",
            model="gpt-4",
            tracker="github",
            validator_model="gpt-4o-mini",
        )
        assert profile.validator_model == "gpt-4o-mini"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/core/test_types.py -v -k "validator_model"`
Expected: FAIL with AttributeError or validation error (field doesn't exist)

**Step 3: Write minimal implementation**

Edit `amelia/core/types.py` - add field to Profile class after existing fields (around line 66):

```python
    validator_model: str | None = None
    """Optional model for plan validation. Uses a fast/cheap model for extraction.
    If not set, falls back to profile.model."""
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/core/test_types.py -v -k "validator_model"`
Expected: PASS

**Step 5: Run full type check**

Run: `uv run mypy amelia/core/types.py`
Expected: Success: no issues found

**Step 6: Commit**

```bash
git add amelia/core/types.py tests/unit/core/test_types.py
git commit -m "feat(types): add validator_model field to Profile"
```

---

## Task 2: Write Failing Tests for plan_validator_node

**Files:**
- Create: `tests/unit/core/test_plan_validator_node.py`

**Step 1: Write the comprehensive test file**

Create `tests/unit/core/test_plan_validator_node.py`:

```python
"""Tests for plan_validator_node function."""

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from amelia.agents.architect import MarkdownPlanOutput
from amelia.core.state import ExecutionState
from amelia.core.types import Issue, Profile


@pytest.fixture
def plan_content() -> str:
    """Sample plan markdown content."""
    return """# Implementation Plan for TEST-123

**Goal:** Add user authentication with JWT tokens

## Overview

This plan implements JWT-based authentication.

## Files to Modify

- `src/auth/handler.py` - Add JWT validation
- `src/models/user.py` - Add token fields
- `tests/test_auth.py` - Add auth tests

## Implementation Steps

1. Add JWT library dependency
2. Create token validation middleware
3. Update user model
"""


@pytest.fixture
def mock_profile(tmp_path: Path) -> Profile:
    """Create a test profile with tmp_path for plan output."""
    return Profile(
        name="test",
        driver="api:openrouter",
        model="gpt-4",
        tracker="github",
        plan_output_dir=str(tmp_path / "plans"),
        plan_path_pattern="{date}-{issue_key}.md",
    )


@pytest.fixture
def mock_profile_with_validator_model(tmp_path: Path) -> Profile:
    """Create a test profile with validator_model set."""
    return Profile(
        name="test",
        driver="api:openrouter",
        model="gpt-4",
        tracker="github",
        validator_model="gpt-4o-mini",
        plan_output_dir=str(tmp_path / "plans"),
        plan_path_pattern="{date}-{issue_key}.md",
    )


@pytest.fixture
def mock_issue() -> Issue:
    """Create a test issue."""
    return Issue(
        id="TEST-123",
        title="Test Issue",
        description="Test description",
        labels=[],
    )


@pytest.fixture
def mock_state(mock_issue: Issue) -> ExecutionState:
    """Create a test execution state."""
    return ExecutionState(issue=mock_issue)


def make_config(profile: Profile) -> dict[str, Any]:
    """Create a RunnableConfig-like dict for testing."""
    return {
        "configurable": {
            "profile": profile,
            "workflow_id": "test-workflow-123",
            "stream_emitter": AsyncMock(),
        }
    }


class TestPlanValidatorNode:
    """Tests for plan_validator_node function."""

    @pytest.mark.asyncio
    async def test_validator_extracts_goal_from_plan(
        self,
        mock_state: ExecutionState,
        mock_profile: Profile,
        plan_content: str,
        tmp_path: Path,
    ) -> None:
        """Happy path - validator extracts goal, markdown, and key_files from plan."""
        from amelia.core.orchestrator import plan_validator_node

        # Setup: Create plan file at expected location
        plan_dir = tmp_path / "plans"
        plan_dir.mkdir(parents=True)
        from datetime import date
        today = date.today().isoformat()
        plan_path = plan_dir / f"{today}-test-123.md"
        plan_path.write_text(plan_content)

        # Mock the driver to return structured output
        mock_output = MarkdownPlanOutput(
            goal="Add user authentication with JWT tokens",
            plan_markdown=plan_content,
            key_files=["src/auth/handler.py", "src/models/user.py", "tests/test_auth.py"],
        )
        mock_driver = MagicMock()
        mock_driver.generate = AsyncMock(return_value=(mock_output, "session-123"))

        config = make_config(mock_profile)

        with patch("amelia.core.orchestrator.DriverFactory") as mock_factory:
            mock_factory.get_driver.return_value = mock_driver

            result = await plan_validator_node(mock_state, config)

        assert result["goal"] == "Add user authentication with JWT tokens"
        assert result["plan_markdown"] == plan_content
        assert result["plan_path"] == plan_path
        assert result["key_files"] == [
            "src/auth/handler.py",
            "src/models/user.py",
            "tests/test_auth.py",
        ]

    @pytest.mark.asyncio
    async def test_validator_fails_when_plan_file_missing(
        self,
        mock_state: ExecutionState,
        mock_profile: Profile,
        tmp_path: Path,
    ) -> None:
        """Validator raises ValueError when plan file doesn't exist."""
        from amelia.core.orchestrator import plan_validator_node

        # Don't create the plan file
        config = make_config(mock_profile)

        with pytest.raises(ValueError, match="Plan file not found"):
            await plan_validator_node(mock_state, config)

    @pytest.mark.asyncio
    async def test_validator_fails_when_plan_file_empty(
        self,
        mock_state: ExecutionState,
        mock_profile: Profile,
        tmp_path: Path,
    ) -> None:
        """Validator raises ValueError when plan file is empty."""
        from amelia.core.orchestrator import plan_validator_node

        # Create empty plan file
        plan_dir = tmp_path / "plans"
        plan_dir.mkdir(parents=True)
        from datetime import date
        today = date.today().isoformat()
        plan_path = plan_dir / f"{today}-test-123.md"
        plan_path.write_text("")

        config = make_config(mock_profile)

        with pytest.raises(ValueError, match="Plan file is empty"):
            await plan_validator_node(mock_state, config)

    @pytest.mark.asyncio
    async def test_validator_uses_validator_model_when_set(
        self,
        mock_state: ExecutionState,
        mock_profile_with_validator_model: Profile,
        plan_content: str,
        tmp_path: Path,
    ) -> None:
        """Validator uses profile.validator_model when it's set."""
        from amelia.core.orchestrator import plan_validator_node

        # Setup: Create plan file
        plan_dir = tmp_path / "plans"
        plan_dir.mkdir(parents=True)
        from datetime import date
        today = date.today().isoformat()
        plan_path = plan_dir / f"{today}-test-123.md"
        plan_path.write_text(plan_content)

        mock_output = MarkdownPlanOutput(
            goal="Goal",
            plan_markdown=plan_content,
            key_files=[],
        )
        mock_driver = MagicMock()
        mock_driver.generate = AsyncMock(return_value=(mock_output, "session-123"))

        config = make_config(mock_profile_with_validator_model)

        with patch("amelia.core.orchestrator.DriverFactory") as mock_factory:
            mock_factory.get_driver.return_value = mock_driver

            await plan_validator_node(mock_state, config)

        # Verify driver was created with validator_model, not profile.model
        mock_factory.get_driver.assert_called_once_with(
            "api:openrouter",
            model="gpt-4o-mini",  # validator_model, not "gpt-4"
        )

    @pytest.mark.asyncio
    async def test_validator_falls_back_to_profile_model(
        self,
        mock_state: ExecutionState,
        mock_profile: Profile,  # No validator_model set
        plan_content: str,
        tmp_path: Path,
    ) -> None:
        """Validator falls back to profile.model when validator_model is None."""
        from amelia.core.orchestrator import plan_validator_node

        # Setup: Create plan file
        plan_dir = tmp_path / "plans"
        plan_dir.mkdir(parents=True)
        from datetime import date
        today = date.today().isoformat()
        plan_path = plan_dir / f"{today}-test-123.md"
        plan_path.write_text(plan_content)

        mock_output = MarkdownPlanOutput(
            goal="Goal",
            plan_markdown=plan_content,
            key_files=[],
        )
        mock_driver = MagicMock()
        mock_driver.generate = AsyncMock(return_value=(mock_output, "session-123"))

        config = make_config(mock_profile)

        with patch("amelia.core.orchestrator.DriverFactory") as mock_factory:
            mock_factory.get_driver.return_value = mock_driver

            await plan_validator_node(mock_state, config)

        # Verify driver was created with profile.model as fallback
        mock_factory.get_driver.assert_called_once_with(
            "api:openrouter",
            model="gpt-4",  # Falls back to profile.model
        )
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/core/test_plan_validator_node.py -v`
Expected: FAIL with ImportError - `cannot import name 'plan_validator_node' from 'amelia.core.orchestrator'`

**Step 3: Commit test file**

```bash
git add tests/unit/core/test_plan_validator_node.py
git commit -m "test(orchestrator): add failing tests for plan_validator_node"
```

---

## Task 3: Implement plan_validator_node Function

**Files:**
- Modify: `amelia/core/orchestrator.py` (add function after `_extract_goal_from_markdown`, around line 204)

**Step 1: Add the import for MarkdownPlanOutput**

At the top of `amelia/core/orchestrator.py`, ensure this import exists (add if missing):

```python
from amelia.agents.architect import MarkdownPlanOutput
```

**Step 2: Write the implementation**

Add after `_extract_goal_from_markdown()` function (insert at line 204):

```python
async def plan_validator_node(
    state: ExecutionState,
    config: RunnableConfig | None = None,
) -> dict[str, Any]:
    """Validate and extract structure from architect's plan file.

    Reads the plan file written by the architect and uses an LLM to extract
    structured fields (goal, plan_markdown, key_files) using the MarkdownPlanOutput schema.

    Args:
        state: Current execution state with raw_architect_output.
        config: RunnableConfig with profile in configurable.

    Returns:
        Partial state dict with goal, plan_markdown, plan_path, key_files.

    Raises:
        ValueError: If plan file not found or empty.
    """
    stream_emitter, workflow_id, profile = _extract_config_params(config)

    # Resolve plan path
    plan_rel_path = resolve_plan_path(profile.plan_path_pattern, state.issue.id)
    plan_path = Path(profile.plan_output_dir) / plan_rel_path

    # Read plan file
    if not plan_path.exists():
        raise ValueError(f"Plan file not found at {plan_path}")

    plan_content = plan_path.read_text()
    if not plan_content.strip():
        raise ValueError(f"Plan file is empty at {plan_path}")

    # Get validator driver
    model = profile.validator_model or profile.model
    driver = DriverFactory.get_driver(profile.driver, model=model)

    # Extract structured fields using LLM
    prompt = f"""Extract the implementation plan structure from the following markdown plan.

<plan>
{plan_content}
</plan>

Return:
- goal: 1-2 sentence summary of what this plan accomplishes
- plan_markdown: The full plan content (preserve as-is)
- key_files: List of files that will be created or modified"""

    output, _session_id = await driver.generate(
        prompt=prompt,
        schema=MarkdownPlanOutput,
    )

    logger.info(
        "Plan validated",
        goal=output.goal,
        key_files_count=len(output.key_files),
        workflow_id=workflow_id,
    )

    return {
        "goal": output.goal,
        "plan_markdown": output.plan_markdown,
        "plan_path": plan_path,
        "key_files": output.key_files,
    }
```

**Step 3: Run tests to verify they pass**

Run: `uv run pytest tests/unit/core/test_plan_validator_node.py -v`
Expected: All 5 tests PASS

**Step 4: Run type check**

Run: `uv run mypy amelia/core/orchestrator.py`
Expected: Success or only pre-existing issues

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py
git commit -m "feat(orchestrator): implement plan_validator_node function"
```

---

## Task 4: Write Failing Tests for Graph Edge Changes

**Files:**
- Modify: `tests/unit/test_orchestrator_graph.py` (add test for new edge)

**Step 1: Write the failing test**

Add to `tests/unit/test_orchestrator_graph.py` in the `TestCreateOrchestratorGraph` class:

```python
    def test_graph_includes_plan_validator_node(self) -> None:
        """Graph should include plan_validator_node."""
        graph = create_orchestrator_graph()
        nodes = graph.nodes
        node_names = set(nodes.keys())
        assert "plan_validator_node" in node_names

    def test_graph_routes_architect_to_validator(self) -> None:
        """Graph should route from architect_node to plan_validator_node."""
        graph = create_orchestrator_graph()
        # Check that architect_node has edge to plan_validator_node
        # LangGraph stores edges in graph.edges
        edges = graph.edges
        # Find edge from architect_node
        architect_edges = [e for e in edges if e[0] == "architect_node"]
        assert len(architect_edges) == 1
        assert architect_edges[0][1] == "plan_validator_node"

    def test_graph_routes_validator_to_human_approval(self) -> None:
        """Graph should route from plan_validator_node to human_approval_node."""
        graph = create_orchestrator_graph()
        edges = graph.edges
        validator_edges = [e for e in edges if e[0] == "plan_validator_node"]
        assert len(validator_edges) == 1
        assert validator_edges[0][1] == "human_approval_node"
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_orchestrator_graph.py -v -k "validator"`
Expected: FAIL - plan_validator_node not in graph, edge not found

**Step 3: Commit test**

```bash
git add tests/unit/test_orchestrator_graph.py
git commit -m "test(orchestrator): add failing tests for plan_validator_node graph edges"
```

---

## Task 5: Update Graph to Include plan_validator_node

**Files:**
- Modify: `amelia/core/orchestrator.py:891-959` (create_orchestrator_graph function)

**Step 1: Add the node to the graph**

In `create_orchestrator_graph()`, after line 916 (`workflow.add_node("architect_node", call_architect_node)`), add:

```python
    workflow.add_node("plan_validator_node", plan_validator_node)
```

**Step 2: Update edges**

Change the edge from architect_node. Find line ~925:
```python
workflow.add_edge("architect_node", "human_approval_node")
```

Replace with:
```python
    workflow.add_edge("architect_node", "plan_validator_node")
    workflow.add_edge("plan_validator_node", "human_approval_node")
```

**Step 3: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_orchestrator_graph.py -v -k "validator"`
Expected: All 3 new tests PASS

**Step 4: Run full graph tests**

Run: `uv run pytest tests/unit/test_orchestrator_graph.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py
git commit -m "feat(orchestrator): add plan_validator_node to graph between architect and human_approval"
```

---

## Task 6: Write Failing Tests for Architect Node Simplification

**Files:**
- Modify: `tests/unit/core/test_orchestrator_plan_extraction.py`

**Step 1: Update test assertions for new architect_node return values**

The existing tests in `test_orchestrator_plan_extraction.py` expect `plan_markdown` and `plan_path` in the return. Update them to expect only `raw_architect_output`, `tool_calls`, `tool_results`.

Update `test_call_architect_node_reads_from_predictable_path()`:

```python
    @pytest.mark.asyncio
    async def test_call_architect_node_returns_raw_output_only(
        self,
        mock_execution_state_factory: Callable[..., tuple[ExecutionState, Path]],
        mock_profile_factory: Callable[..., Profile],
    ) -> None:
        """Architect node should return only raw output and tool history, not plan content."""
        mock_state, tmp_path = mock_execution_state_factory()
        profile = mock_profile_factory(tmp_path=tmp_path)

        # Create plan directory and file (architect would write this)
        plan_dir = Path(profile.plan_output_dir)
        plan_dir.mkdir(parents=True, exist_ok=True)

        from datetime import date
        today = date.today().isoformat()
        plan_path = plan_dir / f"{today}-{mock_state.issue.id.lower()}.md"
        plan_content = "# Test Plan\n\n**Goal:** Test goal"
        plan_path.write_text(plan_content)

        mock_driver = MagicMock()
        mock_driver.execute_agentic = AsyncMock(return_value=async_generator([]))

        config = {
            "configurable": {
                "profile": profile,
                "workflow_id": "test-123",
                "stream_emitter": AsyncMock(),
            }
        }

        with patch("amelia.core.orchestrator.DriverFactory") as mock_factory:
            mock_factory.get_driver.return_value = mock_driver

            result = await call_architect_node(mock_state, config)

        # Architect node should NOT return plan_markdown or plan_path
        assert "plan_markdown" not in result
        assert "plan_path" not in result
        assert "goal" not in result

        # Should only return these fields
        assert "raw_architect_output" in result
        assert "tool_calls" in result
        assert "tool_results" in result
```

Add helper at top of file:

```python
async def async_generator(items: list) -> AsyncIterator:
    """Create an async generator from a list."""
    for item in items:
        yield item
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/core/test_orchestrator_plan_extraction.py -v`
Expected: FAIL - architect_node still returns plan_markdown, plan_path, goal

**Step 3: Commit test changes**

```bash
git add tests/unit/core/test_orchestrator_plan_extraction.py
git commit -m "test(orchestrator): update architect_node tests for simplified return values"
```

---

## Task 7: Simplify Architect Node Return Values

**Files:**
- Modify: `amelia/core/orchestrator.py:206-353` (call_architect_node function)

**Step 1: Identify code to remove**

In `call_architect_node()`, remove:
- Plan file reading logic (lines ~267-305)
- Goal extraction calls (lines ~307-310)
- `plan_markdown` and `plan_path` from return values

**Step 2: Update the return statement**

Change the return statement at the end of `call_architect_node()` to:

```python
    return {
        "raw_architect_output": final_output,
        "tool_calls": list(tool_calls),
        "tool_results": list(tool_results),
    }
```

Remove all code that:
- Reads the plan file
- Calls `_extract_goal_from_markdown()`
- Sets `plan_markdown` or `plan_path` or `goal`

**Step 3: Run tests to verify they pass**

Run: `uv run pytest tests/unit/core/test_orchestrator_plan_extraction.py -v`
Expected: PASS

**Step 4: Run plan_validator_node tests (should still pass)**

Run: `uv run pytest tests/unit/core/test_plan_validator_node.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py
git commit -m "refactor(orchestrator): simplify architect_node to return only raw output"
```

---

## Task 8: Delete _extract_goal_from_markdown Function

**Files:**
- Modify: `amelia/core/orchestrator.py:128-203` (delete function)

**Step 1: Verify no remaining usages**

Run: `uv run ruff check amelia --select F401,F811` (check for unused imports)
Search codebase: `grep -r "_extract_goal_from_markdown" amelia/`
Expected: Only the function definition, no calls

**Step 2: Delete the function**

Remove lines 128-203 (the entire `_extract_goal_from_markdown()` function).

**Step 3: Run tests to verify nothing broke**

Run: `uv run pytest tests/unit/core/ -v`
Expected: All PASS (no tests should call this function anymore)

**Step 4: Run type check**

Run: `uv run mypy amelia/core/orchestrator.py`
Expected: Success

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py
git commit -m "refactor(orchestrator): delete obsolete _extract_goal_from_markdown function"
```

---

## Task 9: Delete TestExtractGoalFromMarkdown Test Class

**Files:**
- Modify: `tests/unit/core/test_orchestrator_helpers.py:40-111` (delete class)

**Step 1: Delete the test class**

Remove the entire `TestExtractGoalFromMarkdown` class (lines 40-111).

**Step 2: Run remaining tests in file to verify nothing else broke**

Run: `uv run pytest tests/unit/core/test_orchestrator_helpers.py -v`
Expected: Remaining tests PASS (or file can be deleted if empty)

**Step 3: Run full test suite**

Run: `uv run pytest tests/unit/ -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add tests/unit/core/test_orchestrator_helpers.py
git commit -m "test(orchestrator): delete obsolete TestExtractGoalFromMarkdown tests"
```

---

## Task 10: Add key_files Field to ExecutionState

**Files:**
- Modify: `amelia/core/state.py` (add field)
- Test: `tests/unit/core/test_state.py` (if exists, or verify manually)

**Step 1: Check if key_files exists in ExecutionState**

Run: `grep -n "key_files" amelia/core/state.py`
If not found, add it.

**Step 2: Add the field if missing**

In `amelia/core/state.py`, add to `ExecutionState` class after `plan_path`:

```python
    key_files: list[str] = []
    """List of key files identified in the plan."""
```

**Step 3: Run type check**

Run: `uv run mypy amelia/core/state.py`
Expected: Success

**Step 4: Run plan_validator_node tests**

Run: `uv run pytest tests/unit/core/test_plan_validator_node.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add amelia/core/state.py
git commit -m "feat(state): add key_files field to ExecutionState"
```

---

## Task 11: Integration Test - Full Flow

**Files:**
- Create: `tests/integration/test_plan_validator_flow.py`

**Step 1: Write integration test**

```python
"""Integration tests for architect → plan_validator flow."""

from datetime import date
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from amelia.agents.architect import MarkdownPlanOutput
from amelia.core.orchestrator import (
    call_architect_node,
    plan_validator_node,
)
from amelia.core.state import ExecutionState
from amelia.core.types import Issue, Profile


@pytest.fixture
def integration_profile(tmp_path: Path) -> Profile:
    """Profile for integration testing."""
    return Profile(
        name="integration-test",
        driver="api:openrouter",
        model="gpt-4",
        validator_model="gpt-4o-mini",
        tracker="github",
        plan_output_dir=str(tmp_path / "plans"),
        plan_path_pattern="{date}-{issue_key}.md",
    )


@pytest.fixture
def integration_issue() -> Issue:
    """Issue for integration testing."""
    return Issue(
        id="INT-456",
        title="Integration Test Issue",
        description="Test the full flow",
        labels=[],
    )


class TestArchitectToValidatorFlow:
    """Integration tests for architect → validator flow."""

    @pytest.mark.asyncio
    async def test_architect_to_validator_flow(
        self,
        integration_profile: Profile,
        integration_issue: Issue,
        tmp_path: Path,
    ) -> None:
        """Full flow: architect writes plan → validator extracts structure."""
        state = ExecutionState(issue=integration_issue)
        plan_content = """# Implementation Plan for INT-456

**Goal:** Implement feature X with Y integration

## Files to Modify

- `src/feature.py` - Main implementation
- `tests/test_feature.py` - Tests
"""
        # Setup: Create plan file (simulating architect output)
        plan_dir = tmp_path / "plans"
        plan_dir.mkdir(parents=True)
        today = date.today().isoformat()
        plan_path = plan_dir / f"{today}-int-456.md"
        plan_path.write_text(plan_content)

        # Mock validator driver
        mock_validator_output = MarkdownPlanOutput(
            goal="Implement feature X with Y integration",
            plan_markdown=plan_content,
            key_files=["src/feature.py", "tests/test_feature.py"],
        )
        mock_driver = MagicMock()
        mock_driver.generate = AsyncMock(return_value=(mock_validator_output, "sess"))

        config: dict[str, Any] = {
            "configurable": {
                "profile": integration_profile,
                "workflow_id": "int-test-789",
                "stream_emitter": AsyncMock(),
            }
        }

        with patch("amelia.core.orchestrator.DriverFactory") as mock_factory:
            mock_factory.get_driver.return_value = mock_driver

            # Run validator node
            result = await plan_validator_node(state, config)

        # Verify extracted structure
        assert result["goal"] == "Implement feature X with Y integration"
        assert result["plan_markdown"] == plan_content
        assert result["plan_path"] == plan_path
        assert "src/feature.py" in result["key_files"]
        assert "tests/test_feature.py" in result["key_files"]
```

**Step 2: Run integration test**

Run: `uv run pytest tests/integration/test_plan_validator_flow.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/integration/test_plan_validator_flow.py
git commit -m "test(integration): add architect → validator flow test"
```

---

## Task 12: Final Verification

**Step 1: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All tests PASS

**Step 2: Run linting**

Run: `uv run ruff check amelia tests --fix`
Expected: No errors (or auto-fixed)

**Step 3: Run type checking**

Run: `uv run mypy amelia`
Expected: Success or only pre-existing issues

**Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final cleanup for plan_validator_node implementation"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Add `validator_model` to Profile | `types.py`, `test_types.py` |
| 2 | Write failing tests for validator node | `test_plan_validator_node.py` |
| 3 | Implement `plan_validator_node` | `orchestrator.py` |
| 4 | Write failing tests for graph edges | `test_orchestrator_graph.py` |
| 5 | Update graph with new node and edges | `orchestrator.py` |
| 6 | Write failing tests for architect simplification | `test_orchestrator_plan_extraction.py` |
| 7 | Simplify architect_node return values | `orchestrator.py` |
| 8 | Delete `_extract_goal_from_markdown` | `orchestrator.py` |
| 9 | Delete obsolete tests | `test_orchestrator_helpers.py` |
| 10 | Add `key_files` to ExecutionState | `state.py` |
| 11 | Integration test for full flow | `test_plan_validator_flow.py` |
| 12 | Final verification | All files |

**Total commits:** 12
**Estimated test count:** ~15 new tests
