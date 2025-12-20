# Extract LangGraph Mock Fixtures Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract duplicated `AsyncSqliteSaver` + `create_orchestrator_graph` mock setup into reusable fixtures in `conftest.py`.

**Architecture:** Create a `LangGraphMocks` NamedTuple containing all mock components, and a `langgraph_mock_factory` fixture that handles the patch decorators and mock setup. Tests will use this fixture instead of repeating the ~12-line mock setup pattern.

**Tech Stack:** Python, pytest fixtures, unittest.mock

---

## Task 1: Create LangGraphMocks NamedTuple and Factory Fixture

**Files:**
- Modify: `tests/conftest.py`

**Step 1: Write the failing test for the fixture**

Create a simple test that uses the new fixture to verify it works.

```python
# tests/unit/test_langgraph_fixtures.py
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

if TYPE_CHECKING:
    from tests.conftest import LangGraphMocks


class TestLangGraphMockFactory:
    """Tests for the langgraph_mock_factory fixture."""

    def test_factory_returns_named_tuple(self, langgraph_mock_factory):
        """Factory should return LangGraphMocks NamedTuple."""
        mocks = langgraph_mock_factory()

        # Verify structure
        assert hasattr(mocks, "graph")
        assert hasattr(mocks, "saver")
        assert hasattr(mocks, "saver_class")
        assert hasattr(mocks, "create_graph")

    def test_graph_mock_has_required_methods(self, langgraph_mock_factory):
        """Graph mock should have aupdate_state, astream, aget_state methods."""
        mocks = langgraph_mock_factory()

        assert hasattr(mocks.graph, "aupdate_state")
        assert hasattr(mocks.graph, "astream")
        assert hasattr(mocks.graph, "aget_state")

    def test_saver_context_manager_setup(self, langgraph_mock_factory):
        """Saver class mock should be configured as async context manager."""
        mocks = langgraph_mock_factory()

        # from_conn_string returns context manager
        cm = mocks.saver_class.from_conn_string.return_value
        assert hasattr(cm, "__aenter__")
        assert hasattr(cm, "__aexit__")

    def test_create_graph_returns_graph_mock(self, langgraph_mock_factory):
        """create_graph mock should return the graph mock."""
        mocks = langgraph_mock_factory()

        assert mocks.create_graph.return_value is mocks.graph

    def test_custom_astream_items(self, langgraph_mock_factory, async_iterator_mock_factory):
        """Factory should accept custom astream items."""
        custom_items = [{"node": "test"}, {"__interrupt__": ("pause",)}]
        mocks = langgraph_mock_factory(astream_items=custom_items)

        # astream should return an iterator with our items
        # (actual iteration tested in integration)
        assert mocks.graph.astream is not None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_langgraph_fixtures.py -v`
Expected: FAIL with "fixture 'langgraph_mock_factory' not found"

**Step 3: Write the LangGraphMocks NamedTuple and factory fixture**

Add to `tests/conftest.py` after the existing imports:

```python
from typing import NamedTuple

class LangGraphMocks(NamedTuple):
    """Container for LangGraph mock objects.

    Attributes:
        graph: Mock CompiledStateGraph with aupdate_state, astream, aget_state.
        saver: Mock AsyncSqliteSaver instance.
        saver_class: Mock AsyncSqliteSaver class (for patching).
        create_graph: Mock create_orchestrator_graph function.
    """
    graph: MagicMock
    saver: AsyncMock
    saver_class: MagicMock
    create_graph: MagicMock


@pytest.fixture
def langgraph_mock_factory(
    async_iterator_mock_factory: Callable[[list[Any]], "AsyncIteratorMock"]
) -> Callable[..., LangGraphMocks]:
    """Factory fixture for creating LangGraph mock objects.

    Creates properly configured mocks for:
    - AsyncSqliteSaver (as async context manager)
    - create_orchestrator_graph (returns mock graph)
    - CompiledStateGraph (with aupdate_state, astream, aget_state)

    Args:
        astream_items: Items for the mock astream iterator. Defaults to [].
        aget_state_return: Return value for aget_state. Defaults to empty state.

    Returns:
        LangGraphMocks NamedTuple with all configured mocks.

    Example:
        def test_example(langgraph_mock_factory):
            mocks = langgraph_mock_factory(
                astream_items=[{"node": "data"}, {"__interrupt__": ("pause",)}]
            )
            # Use mocks.graph, mocks.saver_class in your test
    """
    def _create(
        astream_items: list[Any] | None = None,
        aget_state_return: Any = None,
    ) -> LangGraphMocks:
        if astream_items is None:
            astream_items = []
        if aget_state_return is None:
            aget_state_return = MagicMock(values={}, next=[])

        # Create mock graph with all required methods
        mock_graph = MagicMock()
        mock_graph.aupdate_state = AsyncMock()
        mock_graph.aget_state = AsyncMock(return_value=aget_state_return)
        # astream returns iterator directly (not wrapped in AsyncMock)
        mock_graph.astream = lambda *args, **kwargs: async_iterator_mock_factory(astream_items)

        # Create mock saver as async context manager
        mock_saver = AsyncMock()
        mock_saver_class = MagicMock()
        mock_saver_class.from_conn_string.return_value.__aenter__ = AsyncMock(
            return_value=mock_saver
        )
        mock_saver_class.from_conn_string.return_value.__aexit__ = AsyncMock()

        # Create mock create_graph that returns our graph
        mock_create_graph = MagicMock(return_value=mock_graph)

        return LangGraphMocks(
            graph=mock_graph,
            saver=mock_saver,
            saver_class=mock_saver_class,
            create_graph=mock_create_graph,
        )

    return _create
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_langgraph_fixtures.py -v`
Expected: PASS (all 5 tests)

**Step 5: Commit**

```bash
git add tests/conftest.py tests/unit/test_langgraph_fixtures.py
git commit -m "feat(tests): add LangGraphMocks fixture for reusable mock setup

Introduces langgraph_mock_factory fixture that creates properly configured
mocks for AsyncSqliteSaver and create_orchestrator_graph, reducing
duplication across orchestrator tests."
```

---

## Task 2: Refactor test_service.py - test_approve_workflow_success

**Files:**
- Modify: `tests/unit/server/orchestrator/test_service.py:414-470`

**Step 1: Read the current test to understand it**

The test at line 414 uses the duplicated pattern. We'll refactor it to use the new fixture.

**Step 2: Refactor to use langgraph_mock_factory**

Replace the `@patch` decorators and manual mock setup with the fixture. Note: We still need to patch, but the fixture handles mock configuration.

```python
@patch("amelia.server.orchestrator.service.AsyncSqliteSaver")
@patch("amelia.server.orchestrator.service.create_orchestrator_graph")
async def test_approve_workflow_success(
    mock_create_graph,
    mock_saver_class,
    orchestrator: OrchestratorService,
    mock_repository: AsyncMock,
    mock_event_bus: EventBus,
    langgraph_mock_factory,
):
    """Should approve blocked workflow."""
    received_events = []
    mock_event_bus.subscribe(lambda e: received_events.append(e))

    # Create mock blocked workflow
    mock_state = ServerExecutionState(
        id="wf-1",
        issue_id="ISSUE-123",
        worktree_path="/path/to/worktree",
        worktree_name="feat-123",
        workflow_status="blocked",
        started_at=datetime.now(UTC),
    )
    mock_repository.get.return_value = mock_state

    # Setup LangGraph mocks using factory
    mocks = langgraph_mock_factory(
        aget_state_return=MagicMock(values={"human_approved": True}, next=[])
    )
    mock_create_graph.return_value = mocks.graph
    mock_saver_class.from_conn_string.return_value = mocks.saver_class.from_conn_string.return_value

    # Simulate workflow waiting for approval
    orchestrator._approval_events["wf-1"] = asyncio.Event()

    # New API returns None, raises on error
    await orchestrator.approve_workflow("wf-1")

    # Should remove the approval event after setting it
    assert "wf-1" not in orchestrator._approval_events

    # Should update status - now called twice: once for in_progress, once for completed
    assert mock_repository.set_status.call_count == 2
    # First call is in_progress, second is completed
    calls = mock_repository.set_status.call_args_list
    assert calls[0][0] == ("wf-1", "in_progress")
    assert calls[1][0] == ("wf-1", "completed")

    # Should emit APPROVAL_GRANTED
    approval_granted = [e for e in received_events if e.event_type == EventType.APPROVAL_GRANTED]
    assert len(approval_granted) == 1
```

**Step 3: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py::test_approve_workflow_success -v`
Expected: PASS

**Step 4: Commit**

```bash
git add tests/unit/server/orchestrator/test_service.py
git commit -m "refactor(tests): use langgraph_mock_factory in test_approve_workflow_success"
```

---

## Task 3: Refactor test_service.py - test_reject_workflow_success

**Files:**
- Modify: `tests/unit/server/orchestrator/test_service.py:473-529`

**Step 1: Refactor to use langgraph_mock_factory**

```python
@patch("amelia.server.orchestrator.service.AsyncSqliteSaver")
@patch("amelia.server.orchestrator.service.create_orchestrator_graph")
async def test_reject_workflow_success(
    mock_create_graph,
    mock_saver_class,
    orchestrator: OrchestratorService,
    mock_repository: AsyncMock,
    mock_event_bus: EventBus,
    langgraph_mock_factory,
):
    """Should reject blocked workflow."""
    received_events = []
    mock_event_bus.subscribe(lambda e: received_events.append(e))

    # Create mock workflow and task
    mock_state = ServerExecutionState(
        id="wf-1",
        issue_id="ISSUE-123",
        worktree_path="/path/to/worktree",
        worktree_name="feat-123",
        workflow_status="blocked",
        started_at=datetime.now(UTC),
    )
    mock_repository.get.return_value = mock_state

    # Setup LangGraph mocks using factory
    mocks = langgraph_mock_factory()
    mock_create_graph.return_value = mocks.graph
    mock_saver_class.from_conn_string.return_value = mocks.saver_class.from_conn_string.return_value

    # Create fake task
    task = asyncio.create_task(asyncio.sleep(100))
    orchestrator._active_tasks["/path/to/worktree"] = ("wf-1", task)
    orchestrator._approval_events["wf-1"] = asyncio.Event()

    # New API returns None, raises on error
    await orchestrator.reject_workflow("wf-1", feedback="Plan too complex")

    # Should update status to failed
    mock_repository.set_status.assert_called_once_with(
        "wf-1", "failed", failure_reason="Plan too complex"
    )

    # Should cancel task - wait for cancellation to complete
    with contextlib.suppress(asyncio.CancelledError):
        await task
    assert task.cancelled()

    # Should emit APPROVAL_REJECTED
    approval_rejected = [e for e in received_events if e.event_type == EventType.APPROVAL_REJECTED]
    assert len(approval_rejected) == 1
    assert "rejected" in approval_rejected[0].message.lower()
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py::test_reject_workflow_success -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/unit/server/orchestrator/test_service.py
git commit -m "refactor(tests): use langgraph_mock_factory in test_reject_workflow_success"
```

---

## Task 4: Refactor test_service.py - TestRejectWorkflowGraphState

**Files:**
- Modify: `tests/unit/server/orchestrator/test_service.py:532-564`

**Step 1: Refactor to use langgraph_mock_factory**

```python
class TestRejectWorkflowGraphState:
    """Test reject_workflow updates LangGraph state."""

    @patch("amelia.server.orchestrator.service.AsyncSqliteSaver")
    @patch("amelia.server.orchestrator.service.create_orchestrator_graph")
    async def test_reject_updates_graph_state(
        self, mock_create_graph, mock_saver_class, orchestrator, mock_repository, langgraph_mock_factory
    ):
        """reject_workflow updates graph state with human_approved=False."""
        workflow = ServerExecutionState(
            id="wf-123",
            issue_id="ISSUE-456",
            worktree_path="/tmp/test",
            worktree_name="test",
            workflow_status="blocked",
        )
        mock_repository.get.return_value = workflow

        # Setup LangGraph mocks using factory
        mocks = langgraph_mock_factory()
        mock_create_graph.return_value = mocks.graph
        mock_saver_class.from_conn_string.return_value = mocks.saver_class.from_conn_string.return_value

        await orchestrator.reject_workflow("wf-123", "Not ready")

        mocks.graph.aupdate_state.assert_called_once()
        call_args = mocks.graph.aupdate_state.call_args
        assert call_args[0][1] == {"human_approved": False}
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py::TestRejectWorkflowGraphState -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/unit/server/orchestrator/test_service.py
git commit -m "refactor(tests): use langgraph_mock_factory in TestRejectWorkflowGraphState"
```

---

## Task 5: Refactor test_service.py - TestApproveWorkflowResume

**Files:**
- Modify: `tests/unit/server/orchestrator/test_service.py:567-606`

**Step 1: Read the full test and refactor**

```python
class TestApproveWorkflowResume:
    """Test approve_workflow resumes LangGraph execution."""

    @patch("amelia.server.orchestrator.service.AsyncSqliteSaver")
    @patch("amelia.server.orchestrator.service.create_orchestrator_graph")
    async def test_approve_updates_state_and_resumes(
        self, mock_create_graph, mock_saver_class, orchestrator, mock_repository, langgraph_mock_factory
    ):
        """approve_workflow updates graph state and resumes execution."""
        # Setup blocked workflow
        workflow = ServerExecutionState(
            id="wf-123",
            issue_id="ISSUE-456",
            worktree_path="/tmp/test",
            worktree_name="test",
            workflow_status="blocked",
        )
        mock_repository.get.return_value = workflow
        orchestrator._active_tasks["/tmp/test"] = ("wf-123", AsyncMock())

        # Setup LangGraph mocks using factory
        mocks = langgraph_mock_factory(
            aget_state_return=MagicMock(values={"human_approved": True}, next=[])
        )
        mock_create_graph.return_value = mocks.graph
        mock_saver_class.from_conn_string.return_value = mocks.saver_class.from_conn_string.return_value

        await orchestrator.approve_workflow("wf-123")

        # Verify state was updated with approval
        mocks.graph.aupdate_state.assert_called_once()
        call_args = mocks.graph.aupdate_state.call_args
        assert call_args[0][1] == {"human_approved": True}
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py::TestApproveWorkflowResume -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/unit/server/orchestrator/test_service.py
git commit -m "refactor(tests): use langgraph_mock_factory in TestApproveWorkflowResume"
```

---

## Task 6: Refactor test_approval_flow.py - TestLifecycleEvents

**Files:**
- Modify: `tests/integration/test_approval_flow.py:127-179`

**Step 1: Refactor to use langgraph_mock_factory**

```python
class TestLifecycleEvents:
    """Test workflow lifecycle event emission."""

    @patch("amelia.server.orchestrator.service.AsyncSqliteSaver")
    @patch("amelia.server.orchestrator.service.create_orchestrator_graph")
    async def test_workflow_started_event_emitted(
        self,
        mock_create_graph,
        mock_saver_class,
        event_tracker,
        mock_repository,
        temp_checkpoint_db,
        mock_settings,
        langgraph_mock_factory,
    ):
        """WORKFLOW_STARTED event is emitted at the start."""
        # Setup LangGraph mocks using factory
        mocks = langgraph_mock_factory()
        mock_create_graph.return_value = mocks.graph
        mock_saver_class.from_conn_string.return_value = mocks.saver_class.from_conn_string.return_value

        service = OrchestratorService(
            event_tracker,
            mock_repository,
            settings=mock_settings,
            checkpoint_path=temp_checkpoint_db,
        )

        core_state = ExecutionState(
            profile=Profile(name="test", driver="cli:claude"),
        )
        server_state = ServerExecutionState(
            id="wf-lifecycle-test",
            issue_id="TEST-123",
            worktree_path="/tmp/test-lifecycle",
            worktree_name="test-lifecycle",
            started_at=datetime.now(UTC),
            execution_state=core_state,
        )

        await mock_repository.create(server_state)
        await service._run_workflow("wf-lifecycle-test", server_state)

        # Check WORKFLOW_STARTED was emitted
        started_events = event_tracker.get_by_type(EventType.WORKFLOW_STARTED)
        assert len(started_events) == 1
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_approval_flow.py::TestLifecycleEvents -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/integration/test_approval_flow.py
git commit -m "refactor(tests): use langgraph_mock_factory in TestLifecycleEvents"
```

---

## Task 7: Refactor test_approval_flow.py - TestGraphInterruptHandling

**Files:**
- Modify: `tests/integration/test_approval_flow.py:181-244`

**Step 1: Refactor to use langgraph_mock_factory**

Note: This test uses a custom `InterruptIterator` class for special interrupt behavior. We can still use the factory for the saver setup, but need custom astream handling.

```python
class TestGraphInterruptHandling:
    """Test GraphInterrupt is handled correctly."""

    @patch("amelia.server.orchestrator.service.AsyncSqliteSaver")
    @patch("amelia.server.orchestrator.service.create_orchestrator_graph")
    async def test_interrupt_sets_status_blocked(
        self,
        mock_create_graph,
        mock_saver_class,
        event_tracker,
        mock_repository,
        temp_checkpoint_db,
        mock_settings,
        langgraph_mock_factory,
    ):
        """__interrupt__ chunk sets status to blocked and emits APPROVAL_REQUIRED."""
        # Setup LangGraph mocks with custom interrupt sequence
        interrupt_items = [
            {"architect_node": {}},  # First node completes
            {"__interrupt__": ("Paused for approval",)},  # Interrupt signal
        ]
        mocks = langgraph_mock_factory(astream_items=interrupt_items)
        mock_create_graph.return_value = mocks.graph
        mock_saver_class.from_conn_string.return_value = mocks.saver_class.from_conn_string.return_value

        service = OrchestratorService(
            event_tracker,
            mock_repository,
            settings=mock_settings,
            checkpoint_path=temp_checkpoint_db,
        )

        core_state = ExecutionState(
            profile=Profile(name="test", driver="cli:claude"),
        )
        server_state = ServerExecutionState(
            id="wf-interrupt-test",
            issue_id="TEST-456",
            worktree_path="/tmp/test-interrupt",
            worktree_name="test-interrupt",
            started_at=datetime.now(UTC),
            execution_state=core_state,
        )
        # ... rest of test unchanged
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_approval_flow.py::TestGraphInterruptHandling -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/integration/test_approval_flow.py
git commit -m "refactor(tests): use langgraph_mock_factory in TestGraphInterruptHandling"
```

---

## Task 8: Run full test suite and verify

**Step 1: Run linting**

Run: `uv run ruff check amelia tests`
Expected: No errors

**Step 2: Run type checking**

Run: `uv run mypy amelia`
Expected: No errors

**Step 3: Run all tests**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py tests/integration/test_approval_flow.py tests/unit/test_langgraph_fixtures.py -v`
Expected: All tests PASS

**Step 4: Commit final cleanup if needed**

```bash
git add -A
git commit -m "chore: cleanup after langgraph mock fixture refactor"
```

---

## Task 9: Verify line reduction and close issue

**Step 1: Count lines saved**

Before: ~12 lines of mock setup per test occurrence (6 occurrences = ~72 lines)
After: ~3 lines per test + ~45 lines for fixture definition
Net savings: ~25-30 lines + improved maintainability

**Step 2: Update issue with completion**

Use `gh issue close 43` with a comment summarizing the changes.

```bash
gh issue close 43 -c "Completed. Created langgraph_mock_factory fixture and refactored 6 test occurrences. Net reduction of ~25-30 lines with improved maintainability."
```
