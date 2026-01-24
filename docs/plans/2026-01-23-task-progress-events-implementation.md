# Task Progress Events Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Emit task progress events (TASK_STARTED, TASK_COMPLETED, TASK_FAILED) from the orchestrator so they appear in the dashboard activity log.

**Architecture:** Events are emitted from `OrchestratorService` in response to LangGraph stream events, matching the existing STAGE_STARTED/STAGE_COMPLETED pattern. A new utility function extracts task titles from plan markdown.

**Tech Stack:** Python, LangGraph, asyncio, Pydantic

---

## Phase 1: Task Title Extraction Utility

### Task 1: Add extract_task_title utility function

**Files:**
- Modify: `amelia/pipelines/implementation/utils.py`
- Test: `tests/unit/core/test_orchestrator_helpers.py`

**Step 1: Write the failing test**

Add to `tests/unit/core/test_orchestrator_helpers.py`:

```python
class TestExtractTaskTitle:
    """Tests for extract_task_title helper."""

    def test_extracts_simple_task_title(self) -> None:
        """Should extract title from ### Task N: Title format."""
        from amelia.pipelines.implementation.utils import extract_task_title

        plan = """# Plan
### Task 1: First task title
Content
### Task 2: Second task title
More content
"""
        assert extract_task_title(plan, 0) == "First task title"
        assert extract_task_title(plan, 1) == "Second task title"

    def test_extracts_hierarchical_task_title(self) -> None:
        """Should extract title from ### Task N.M: Title format."""
        from amelia.pipelines.implementation.utils import extract_task_title

        assert extract_task_title(SAMPLE_PLAN, 0) == "Create Model Types"
        assert extract_task_title(SAMPLE_PLAN, 1) == "Add Response Types"
        assert extract_task_title(SAMPLE_PLAN, 2) == "Create PreferencesService"

    def test_returns_none_for_invalid_index(self) -> None:
        """Should return None if task index out of range."""
        from amelia.pipelines.implementation.utils import extract_task_title

        assert extract_task_title(SAMPLE_PLAN, 99) is None

    def test_returns_none_for_no_tasks(self) -> None:
        """Should return None if no task patterns found."""
        from amelia.pipelines.implementation.utils import extract_task_title

        plan = "# Plan\n\nNo tasks here"
        assert extract_task_title(plan, 0) is None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/core/test_orchestrator_helpers.py::TestExtractTaskTitle -v`
Expected: FAIL with ImportError (function doesn't exist)

**Step 3: Write minimal implementation**

Add to `amelia/pipelines/implementation/utils.py` after `extract_task_count`:

```python
def extract_task_title(plan_markdown: str, task_index: int) -> str | None:
    """Extract the title of a specific task from plan markdown.

    Supports both simple (### Task 1: Title) and hierarchical
    (### Task 1.1: Title) numbering formats.

    Args:
        plan_markdown: The markdown content of the plan.
        task_index: 0-indexed task number to extract title for.

    Returns:
        The task title string, or None if task not found.
    """
    pattern = r"^### Task \d+(?:\.\d+)?: (.+)$"
    matches = re.findall(pattern, plan_markdown, re.MULTILINE)

    if not matches or task_index >= len(matches):
        return None

    return matches[task_index]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/core/test_orchestrator_helpers.py::TestExtractTaskTitle -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/pipelines/implementation/utils.py tests/unit/core/test_orchestrator_helpers.py
git commit -m "feat(utils): add extract_task_title helper for task event messages"
```

---

## Phase 2: TASK_STARTED Event

### Task 2: Emit TASK_STARTED when developer_node starts in task mode

**Files:**
- Modify: `amelia/server/orchestrator/service.py`
- Test: `tests/unit/server/orchestrator/test_service.py`

**Step 1: Write the failing test**

Add to `tests/unit/server/orchestrator/test_service.py`:

```python
class TestTaskProgressEvents:
    """Tests for task progress event emission."""

    @pytest.fixture
    def service(self, repository: WorkflowRepository, event_bus: EventBus) -> OrchestratorService:
        """Create service with mocked dependencies."""
        return OrchestratorService(repository=repository, event_bus=event_bus)

    @pytest.mark.asyncio
    async def test_emits_task_started_when_developer_starts_in_task_mode(
        self, service: OrchestratorService, repository: WorkflowRepository
    ) -> None:
        """Should emit TASK_STARTED when developer_node starts with total_tasks set."""
        # Setup workflow in task mode
        workflow = WorkflowState(
            id="wf-123",
            status=WorkflowStatus.RUNNING,
            profile_id="test",
        )
        await repository.create(workflow)

        # Simulate developer_node task start event with task state
        task_data = {
            "name": "developer_node",
            "input": {
                "total_tasks": 3,
                "current_task_index": 1,
                "plan_markdown": "### Task 1: First\n### Task 2: Second task\n### Task 3: Third",
            },
        }
        await service._handle_tasks_event("wf-123", task_data)

        # Verify TASK_STARTED event emitted
        events = await repository.get_events("wf-123")
        task_events = [e for e in events if e.event_type == EventType.TASK_STARTED]
        assert len(task_events) == 1
        assert task_events[0].message == "Starting Task 2/3: Second task"
        assert task_events[0].data["task_index"] == 1
        assert task_events[0].data["total_tasks"] == 3
        assert task_events[0].data["task_title"] == "Second task"

    @pytest.mark.asyncio
    async def test_no_task_started_in_legacy_mode(
        self, service: OrchestratorService, repository: WorkflowRepository
    ) -> None:
        """Should NOT emit TASK_STARTED when total_tasks is None (legacy mode)."""
        workflow = WorkflowState(
            id="wf-456",
            status=WorkflowStatus.RUNNING,
            profile_id="test",
        )
        await repository.create(workflow)

        # Simulate developer_node start without task fields
        task_data = {
            "name": "developer_node",
            "input": {},  # No total_tasks = legacy mode
        }
        await service._handle_tasks_event("wf-456", task_data)

        events = await repository.get_events("wf-456")
        task_events = [e for e in events if e.event_type == EventType.TASK_STARTED]
        assert len(task_events) == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py::TestTaskProgressEvents::test_emits_task_started_when_developer_starts_in_task_mode -v`
Expected: FAIL (no TASK_STARTED events emitted)

**Step 3: Write minimal implementation**

Modify `_handle_tasks_event` in `amelia/server/orchestrator/service.py`:

```python
async def _handle_tasks_event(
    self,
    workflow_id: str,
    task_data: dict[str, Any],
) -> None:
    """Handle a task event from stream_mode='tasks'.

    LangGraph emits two types of task events:
    - Task START: {id, name, input, triggers} - when node begins
    - Task RESULT: {id, name, error, result, interrupts} - when node completes

    We process START events for:
    - STAGE_STARTED for all stage nodes
    - TASK_STARTED for developer_node in task-based mode

    Args:
        workflow_id: The workflow this task belongs to.
        task_data: Task event data from LangGraph.
    """
    # Ignore task result events - only process task start events
    if "input" not in task_data:
        return

    node_name = task_data.get("name", "")
    input_state = task_data.get("input", {})

    if node_name in STAGE_NODES:
        await self._emit(
            workflow_id,
            EventType.STAGE_STARTED,
            f"Starting {node_name}",
            agent=node_name.removesuffix("_node"),
            data={"stage": node_name},
        )

    # Emit TASK_STARTED for developer_node in task-based mode
    if node_name == "developer_node":
        total_tasks = input_state.get("total_tasks")
        if total_tasks is not None:
            from amelia.pipelines.implementation.utils import extract_task_title

            task_index = input_state.get("current_task_index", 0)
            plan_markdown = input_state.get("plan_markdown", "")
            task_title = extract_task_title(plan_markdown, task_index) or "Unknown"

            await self._emit(
                workflow_id,
                EventType.TASK_STARTED,
                f"Starting Task {task_index + 1}/{total_tasks}: {task_title}",
                agent="developer",
                data={
                    "task_index": task_index,
                    "total_tasks": total_tasks,
                    "task_title": task_title,
                },
            )
```

Add import at top of file:

```python
from amelia.pipelines.implementation.utils import extract_task_title
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py::TestTaskProgressEvents -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/server/orchestrator/service.py tests/unit/server/orchestrator/test_service.py
git commit -m "feat(events): emit TASK_STARTED when developer starts task in multi-task mode"
```

---

## Phase 3: TASK_COMPLETED Event

### Task 3: Emit TASK_COMPLETED when next_task_node completes

**Files:**
- Modify: `amelia/server/orchestrator/service.py`
- Test: `tests/unit/server/orchestrator/test_service.py`

**Step 1: Write the failing test**

Add to `TestTaskProgressEvents` in `tests/unit/server/orchestrator/test_service.py`:

```python
@pytest.mark.asyncio
async def test_emits_task_completed_when_next_task_node_completes(
    self, service: OrchestratorService, repository: WorkflowRepository
) -> None:
    """Should emit TASK_COMPLETED when next_task_node finishes."""
    workflow = WorkflowState(
        id="wf-789",
        status=WorkflowStatus.RUNNING,
        profile_id="test",
    )
    await repository.create(workflow)

    # Simulate next_task_node completion with state update
    # The chunk contains the state BEFORE the update (current_task_index not yet incremented)
    chunk = {
        "next_task_node": {
            "current_task_index": 1,  # Will become 2 after node runs
        }
    }

    # Need to set up initial state with total_tasks
    # This requires fetching state from repository
    # For the test, we mock the state retrieval
    state = await repository.get(workflow.id)
    state.pipeline_state = {
        "total_tasks": 5,
        "current_task_index": 0,  # Was 0, next_task_node advances to 1
    }
    await repository.update(state)

    await service._handle_stream_chunk("wf-789", chunk)

    events = await repository.get_events("wf-789")
    task_events = [e for e in events if e.event_type == EventType.TASK_COMPLETED]
    assert len(task_events) == 1
    # The completed task is the one we just finished (index 0, displayed as 1)
    assert task_events[0].message == "Completed Task 1/5"
    assert task_events[0].data["task_index"] == 0
    assert task_events[0].data["total_tasks"] == 5
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py::TestTaskProgressEvents::test_emits_task_completed_when_next_task_node_completes -v`
Expected: FAIL (no TASK_COMPLETED event)

**Step 3: Write minimal implementation**

Modify `_handle_stream_chunk` in `amelia/server/orchestrator/service.py`:

```python
async def _handle_stream_chunk(
    self,
    workflow_id: str,
    chunk: dict[str, Any],
) -> None:
    """Handle an updates chunk from astream(stream_mode=['updates', 'tasks']).

    With combined stream mode, updates chunks map node names to their
    state updates. We emit STAGE_COMPLETED after each node that's in
    STAGE_NODES, and TASK_COMPLETED when next_task_node completes.

    Note: STAGE_STARTED events are emitted by _handle_tasks_event when
    task events arrive from the tasks stream mode.

    Args:
        workflow_id: The workflow this chunk belongs to.
        chunk: Dict mapping node names to state updates.
    """
    for node_name, output in chunk.items():
        if node_name in STAGE_NODES:
            # Update current_stage in workflow state
            state = await self._repository.get(workflow_id)
            if state is not None:
                state.current_stage = node_name
                await self._repository.update(state)

            # Emit agent-specific messages based on node
            await self._emit_agent_messages(workflow_id, node_name, output)

            # Emit STAGE_COMPLETED for the current node
            await self._emit(
                workflow_id,
                EventType.STAGE_COMPLETED,
                f"Completed {node_name}",
                agent=node_name.removesuffix("_node"),
                data={"stage": node_name, "output": output},
            )

        # Emit TASK_COMPLETED when next_task_node completes
        if node_name == "next_task_node":
            state = await self._repository.get(workflow_id)
            if state is not None and state.pipeline_state:
                total_tasks = state.pipeline_state.get("total_tasks")
                if total_tasks is not None:
                    # The output contains the NEW index, so completed task is index - 1
                    new_index = output.get("current_task_index", 0)
                    completed_index = new_index - 1 if new_index > 0 else 0

                    await self._emit(
                        workflow_id,
                        EventType.TASK_COMPLETED,
                        f"Completed Task {completed_index + 1}/{total_tasks}",
                        agent="system",
                        data={
                            "task_index": completed_index,
                            "total_tasks": total_tasks,
                        },
                    )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py::TestTaskProgressEvents::test_emits_task_completed_when_next_task_node_completes -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/server/orchestrator/service.py tests/unit/server/orchestrator/test_service.py
git commit -m "feat(events): emit TASK_COMPLETED when next_task_node advances to next task"
```

---

## Phase 4: TASK_FAILED Event

### Task 4: Emit TASK_FAILED when workflow ends due to max iterations

**Files:**
- Modify: `amelia/server/orchestrator/service.py`
- Test: `tests/unit/server/orchestrator/test_service.py`

**Step 1: Write the failing test**

Add to `TestTaskProgressEvents` in `tests/unit/server/orchestrator/test_service.py`:

```python
@pytest.mark.asyncio
async def test_emits_task_failed_when_max_iterations_exceeded(
    self, service: OrchestratorService, repository: WorkflowRepository
) -> None:
    """Should emit TASK_FAILED when workflow ends with unapproved task."""
    workflow = WorkflowState(
        id="wf-fail",
        status=WorkflowStatus.RUNNING,
        profile_id="test",
    )
    await repository.create(workflow)

    # Set up state: task mode, not approved, at max iterations
    state = await repository.get(workflow.id)
    state.pipeline_state = {
        "total_tasks": 3,
        "current_task_index": 1,
        "task_review_iteration": 5,  # At max
        "last_review": {"approved": False},
    }
    await repository.update(state)

    # Simulate workflow completion (called by run_workflow on end)
    await service._emit_task_failed_if_applicable("wf-fail")

    events = await repository.get_events("wf-fail")
    task_events = [e for e in events if e.event_type == EventType.TASK_FAILED]
    assert len(task_events) == 1
    assert task_events[0].message == "Task 2/3 failed after 5 review iterations"
    assert task_events[0].data["task_index"] == 1
    assert task_events[0].data["total_tasks"] == 3
    assert task_events[0].data["iterations"] == 5

@pytest.mark.asyncio
async def test_no_task_failed_when_approved(
    self, service: OrchestratorService, repository: WorkflowRepository
) -> None:
    """Should NOT emit TASK_FAILED when last task was approved."""
    workflow = WorkflowState(
        id="wf-ok",
        status=WorkflowStatus.RUNNING,
        profile_id="test",
    )
    await repository.create(workflow)

    state = await repository.get(workflow.id)
    state.pipeline_state = {
        "total_tasks": 3,
        "current_task_index": 2,  # Last task
        "task_review_iteration": 1,
        "last_review": {"approved": True},
    }
    await repository.update(state)

    await service._emit_task_failed_if_applicable("wf-ok")

    events = await repository.get_events("wf-ok")
    task_events = [e for e in events if e.event_type == EventType.TASK_FAILED]
    assert len(task_events) == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py::TestTaskProgressEvents::test_emits_task_failed_when_max_iterations_exceeded -v`
Expected: FAIL (method doesn't exist)

**Step 3: Write minimal implementation**

Add new method to `OrchestratorService` in `amelia/server/orchestrator/service.py`:

```python
async def _emit_task_failed_if_applicable(self, workflow_id: str) -> None:
    """Emit TASK_FAILED if workflow ended due to unapproved task.

    Called when workflow completes to check if the final task was not approved
    (indicating failure due to max iterations).

    Args:
        workflow_id: The workflow to check.
    """
    state = await self._repository.get(workflow_id)
    if state is None or not state.pipeline_state:
        return

    pipeline = state.pipeline_state
    total_tasks = pipeline.get("total_tasks")

    # Only emit in task mode
    if total_tasks is None:
        return

    # Check if last review was not approved
    last_review = pipeline.get("last_review")
    if last_review is None:
        return

    approved = last_review.get("approved", False) if isinstance(last_review, dict) else getattr(last_review, "approved", False)
    if approved:
        return

    task_index = pipeline.get("current_task_index", 0)
    iterations = pipeline.get("task_review_iteration", 0)

    await self._emit(
        workflow_id,
        EventType.TASK_FAILED,
        f"Task {task_index + 1}/{total_tasks} failed after {iterations} review iterations",
        agent="system",
        data={
            "task_index": task_index,
            "total_tasks": total_tasks,
            "iterations": iterations,
        },
    )
```

Then call this method in `_run_workflow` before emitting WORKFLOW_COMPLETED. Find the location where WORKFLOW_COMPLETED is emitted and add:

```python
# Check for task failure before marking complete
await self._emit_task_failed_if_applicable(workflow_id)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py::TestTaskProgressEvents -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/server/orchestrator/service.py tests/unit/server/orchestrator/test_service.py
git commit -m "feat(events): emit TASK_FAILED when workflow ends with unapproved task"
```

---

## Phase 5: Integration & Verification

### Task 5: Run full test suite and verify type checking

**Files:**
- None (verification only)

**Step 1: Run type checking**

Run: `uv run mypy amelia/server/orchestrator/service.py amelia/pipelines/implementation/utils.py`
Expected: No errors

**Step 2: Run unit tests**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py tests/unit/core/test_orchestrator_helpers.py -v`
Expected: All tests pass

**Step 3: Run lint checks**

Run: `uv run ruff check amelia/server/orchestrator/service.py amelia/pipelines/implementation/utils.py`
Expected: No issues (or fix any issues found)

**Step 4: Run full test suite**

Run: `uv run pytest tests/unit/ -v`
Expected: All tests pass

**Step 5: Commit any fixes**

If any fixes were needed:
```bash
git add -A
git commit -m "fix: address type/lint issues in task progress events"
```

---

## Summary

| File | Changes |
|------|---------|
| `amelia/pipelines/implementation/utils.py` | Add `extract_task_title()` function |
| `amelia/server/orchestrator/service.py` | Modify `_handle_tasks_event()` for TASK_STARTED, `_handle_stream_chunk()` for TASK_COMPLETED, add `_emit_task_failed_if_applicable()` for TASK_FAILED |
| `tests/unit/core/test_orchestrator_helpers.py` | Add `TestExtractTaskTitle` test class |
| `tests/unit/server/orchestrator/test_service.py` | Add `TestTaskProgressEvents` test class |
