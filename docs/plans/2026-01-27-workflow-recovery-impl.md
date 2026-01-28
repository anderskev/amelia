# Workflow Recovery Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add server startup recovery for interrupted workflows and a user-initiated resume capability (API + dashboard + CLI).

**Architecture:** On startup, `recover_interrupted_workflows()` queries the DB for IN_PROGRESS and BLOCKED workflows. IN_PROGRESS gets marked FAILED (with `recoverable: true`), BLOCKED gets its APPROVAL_REQUIRED event re-emitted. A new `resume_workflow()` method validates checkpoint existence and re-launches the workflow. This is exposed via REST endpoint, dashboard button, and CLI command.

**Tech Stack:** Python (FastAPI, LangGraph, Pydantic, pytest-asyncio), TypeScript (React, Zustand, React Router, Vitest)

**Design Spec:** `docs/plans/2026-01-27-workflow-recovery-design.md`

---

### Task 1: Add FAILED → IN_PROGRESS transition

**Files:**
- Modify: `amelia/server/models/state.py:40` (the `FAILED` entry in `VALID_TRANSITIONS`)
- Test: `tests/unit/test_workflow_recovery.py`

**Step 1: Write the failing test**

Create the test file. This test verifies the state machine allows FAILED → IN_PROGRESS.

```python
# tests/unit/test_workflow_recovery.py
"""Tests for workflow recovery and resume functionality."""

from amelia.server.models.state import (
    InvalidStateTransitionError,
    VALID_TRANSITIONS,
    WorkflowStatus,
    validate_transition,
)


class TestValidTransitions:
    """Tests for FAILED -> IN_PROGRESS state transition."""

    def test_valid_transitions_includes_failed_to_in_progress(self) -> None:
        """FAILED -> IN_PROGRESS should be a valid transition for resume."""
        assert WorkflowStatus.IN_PROGRESS in VALID_TRANSITIONS[WorkflowStatus.FAILED]

    def test_failed_to_in_progress_does_not_raise(self) -> None:
        """validate_transition should not raise for FAILED -> IN_PROGRESS."""
        validate_transition(WorkflowStatus.FAILED, WorkflowStatus.IN_PROGRESS)

    def test_failed_to_completed_still_invalid(self) -> None:
        """FAILED -> COMPLETED should remain invalid (only IN_PROGRESS is allowed)."""
        try:
            validate_transition(WorkflowStatus.FAILED, WorkflowStatus.COMPLETED)
            assert False, "Should have raised InvalidStateTransitionError"
        except InvalidStateTransitionError:
            pass
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_workflow_recovery.py::TestValidTransitions -v`
Expected: FAIL — `VALID_TRANSITIONS[WorkflowStatus.FAILED]` is currently `set()`.

**Step 3: Write minimal implementation**

In `amelia/server/models/state.py`, change line 40 from:

```python
    WorkflowStatus.FAILED: set(),  # Terminal state
```

to:

```python
    WorkflowStatus.FAILED: {WorkflowStatus.IN_PROGRESS},  # Resumable via recovery
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_workflow_recovery.py::TestValidTransitions -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/server/models/state.py tests/unit/test_workflow_recovery.py
git commit -m "feat(state): allow FAILED -> IN_PROGRESS transition for resume"
```

---

### Task 2: Implement `recover_interrupted_workflows()`

**Files:**
- Modify: `amelia/server/orchestrator/service.py:2115-2129` (replace placeholder)
- Test: `tests/unit/test_workflow_recovery.py` (append new test class)

**Context:** The current `recover_interrupted_workflows()` at `service.py:2115` is a placeholder with TODOs. Replace it with the real implementation per the design spec.

**Step 1: Write failing tests**

Append to `tests/unit/test_workflow_recovery.py`:

```python
import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from amelia.server.models.events import EventType
from amelia.server.orchestrator.service import OrchestratorService


@pytest.fixture
def event_bus() -> MagicMock:
    bus = MagicMock()
    bus.emit = MagicMock()
    return bus


@pytest.fixture
def repository() -> AsyncMock:
    repo = AsyncMock()
    repo.find_by_status = AsyncMock(return_value=[])
    repo.set_status = AsyncMock()
    repo.save_event = AsyncMock()
    repo.get_max_event_sequence = AsyncMock(return_value=0)
    return repo


@pytest.fixture
def service(event_bus: MagicMock, repository: AsyncMock) -> OrchestratorService:
    return OrchestratorService(
        event_bus=event_bus,
        repository=repository,
    )


def _make_workflow(
    workflow_id: str,
    status: WorkflowStatus,
    worktree_path: str = "/tmp/test-worktree",
) -> MagicMock:
    """Create a mock ServerExecutionState with the given status."""
    wf = MagicMock()
    wf.id = workflow_id
    wf.issue_id = f"ISSUE-{workflow_id}"
    wf.workflow_status = status
    wf.worktree_path = worktree_path
    return wf


class TestRecoverInterruptedWorkflows:
    """Tests for recover_interrupted_workflows()."""

    async def test_recover_in_progress_marks_failed(
        self,
        service: OrchestratorService,
        repository: AsyncMock,
        event_bus: MagicMock,
    ) -> None:
        """IN_PROGRESS workflow should be marked FAILED with recoverable flag."""
        wf = _make_workflow("wf-1", WorkflowStatus.IN_PROGRESS)
        repository.find_by_status = AsyncMock(
            side_effect=lambda statuses: [wf] if WorkflowStatus.IN_PROGRESS in statuses else []
        )

        await service.recover_interrupted_workflows()

        repository.set_status.assert_called_once_with(
            "wf-1",
            WorkflowStatus.FAILED,
            failure_reason="Server restarted while workflow was running",
        )
        # Check WORKFLOW_FAILED event was emitted with recoverable=True
        repository.save_event.assert_called()
        saved_event = repository.save_event.call_args[0][0]
        assert saved_event.event_type == EventType.WORKFLOW_FAILED
        assert saved_event.data["recoverable"] is True

    async def test_recover_blocked_restores_approval(
        self,
        service: OrchestratorService,
        repository: AsyncMock,
        event_bus: MagicMock,
    ) -> None:
        """BLOCKED workflow should stay BLOCKED with APPROVAL_REQUIRED re-emitted."""
        wf = _make_workflow("wf-2", WorkflowStatus.BLOCKED)
        repository.find_by_status = AsyncMock(
            side_effect=lambda statuses: [wf] if WorkflowStatus.BLOCKED in statuses else []
        )

        await service.recover_interrupted_workflows()

        # Status should NOT change — no set_status call for BLOCKED
        repository.set_status.assert_not_called()
        # APPROVAL_REQUIRED event should be emitted
        repository.save_event.assert_called()
        saved_event = repository.save_event.call_args[0][0]
        assert saved_event.event_type == EventType.APPROVAL_REQUIRED

    async def test_recover_pending_unchanged(
        self,
        service: OrchestratorService,
        repository: AsyncMock,
    ) -> None:
        """PENDING workflows should not be touched."""
        repository.find_by_status = AsyncMock(return_value=[])

        await service.recover_interrupted_workflows()

        repository.set_status.assert_not_called()

    async def test_recover_no_active_workflows(
        self,
        service: OrchestratorService,
        repository: AsyncMock,
    ) -> None:
        """With no interrupted workflows, just log summary."""
        repository.find_by_status = AsyncMock(return_value=[])

        await service.recover_interrupted_workflows()

        repository.set_status.assert_not_called()
        repository.save_event.assert_not_called()
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_workflow_recovery.py::TestRecoverInterruptedWorkflows -v`
Expected: FAIL — placeholder implementation does nothing.

**Step 3: Implement `recover_interrupted_workflows()`**

Replace the method body at `service.py:2115-2129` using `replace_symbol_body` on `OrchestratorService/recover_interrupted_workflows`. New body:

```python
async def recover_interrupted_workflows(self) -> None:
    """Recover workflows that were running when server restarted.

    IN_PROGRESS workflows are marked FAILED (recoverable). BLOCKED workflows
    get their APPROVAL_REQUIRED event re-emitted so dashboard clients see them.
    """
    failed_count = 0
    blocked_count = 0

    # Handle IN_PROGRESS workflows — mark as FAILED
    in_progress = await self._repository.find_by_status([WorkflowStatus.IN_PROGRESS])
    for wf in in_progress:
        await self._repository.set_status(
            wf.id,
            WorkflowStatus.FAILED,
            failure_reason="Server restarted while workflow was running",
        )
        await self._emit(
            wf.id,
            EventType.WORKFLOW_FAILED,
            "Server restarted while workflow was running",
            data={"recoverable": True},
        )
        logger.info("Recovered interrupted workflow", workflow_id=wf.id)
        failed_count += 1

    # Handle BLOCKED workflows — re-emit approval events
    blocked = await self._repository.find_by_status([WorkflowStatus.BLOCKED])
    for wf in blocked:
        await self._emit(
            wf.id,
            EventType.APPROVAL_REQUIRED,
            "Plan ready for review - awaiting human approval (restored after restart)",
            agent="human_approval",
            data={"paused_at": "human_approval_node"},
        )
        logger.info("Restored blocked workflow approval", workflow_id=wf.id)
        blocked_count += 1

    logger.info(
        "Recovery complete",
        workflows_failed=failed_count,
        approvals_restored=blocked_count,
    )
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_workflow_recovery.py::TestRecoverInterruptedWorkflows -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/server/orchestrator/service.py tests/unit/test_workflow_recovery.py
git commit -m "feat(recovery): implement recover_interrupted_workflows"
```

---

### Task 3: Implement `resume_workflow()` service method

**Files:**
- Modify: `amelia/server/orchestrator/service.py` (add `resume_workflow` after `cancel_workflow`)
- Test: `tests/unit/test_workflow_recovery.py` (append new test class)

**Context:** The method validates that: (1) the workflow exists, (2) it's in FAILED status, (3) a LangGraph checkpoint exists, (4) the worktree isn't occupied. Then it clears error fields, transitions to IN_PROGRESS, and launches the workflow task.

**Step 1: Write failing tests**

Append to `tests/unit/test_workflow_recovery.py`:

```python
from amelia.server.exceptions import InvalidStateError, WorkflowNotFoundError


class TestResumeWorkflow:
    """Tests for resume_workflow()."""

    async def test_resume_validates_failed_status(
        self,
        service: OrchestratorService,
        repository: AsyncMock,
    ) -> None:
        """Resuming a non-FAILED workflow should raise InvalidStateError."""
        wf = _make_workflow("wf-1", WorkflowStatus.IN_PROGRESS)
        repository.get = AsyncMock(return_value=wf)

        with pytest.raises(InvalidStateError, match="must be in 'failed' status"):
            await service.resume_workflow("wf-1")

    async def test_resume_validates_workflow_exists(
        self,
        service: OrchestratorService,
        repository: AsyncMock,
    ) -> None:
        """Resuming a non-existent workflow should raise WorkflowNotFoundError."""
        repository.get = AsyncMock(return_value=None)

        with pytest.raises(WorkflowNotFoundError):
            await service.resume_workflow("wf-nonexistent")

    async def test_resume_validates_worktree_available(
        self,
        service: OrchestratorService,
        repository: AsyncMock,
    ) -> None:
        """Resuming when worktree is occupied should raise InvalidStateError."""
        wf = _make_workflow("wf-1", WorkflowStatus.FAILED, worktree_path="/tmp/wt")
        wf.execution_state = MagicMock()  # needs execution_state to pass earlier checks
        repository.get = AsyncMock(return_value=wf)

        # Simulate occupied worktree
        service._active_tasks["/tmp/wt"] = ("wf-other", MagicMock())

        with pytest.raises(InvalidStateError, match="worktree.*occupied"):
            await service.resume_workflow("wf-1")

        # Cleanup
        service._active_tasks.clear()

    async def test_resume_transitions_to_in_progress(
        self,
        service: OrchestratorService,
        repository: AsyncMock,
        event_bus: MagicMock,
    ) -> None:
        """Successful resume should clear error fields and set IN_PROGRESS."""
        wf = _make_workflow("wf-1", WorkflowStatus.FAILED)
        wf.failure_reason = "Server restarted"
        wf.consecutive_errors = 3
        wf.last_error_context = "some context"
        wf.completed_at = datetime(2026, 1, 1, tzinfo=UTC)
        wf.execution_state = MagicMock()
        wf.worktree_path = "/tmp/wt-resume"
        repository.get = AsyncMock(return_value=wf)

        # Mock checkpoint validation — patch the graph/checkpointer
        # resume_workflow will use AsyncSqliteSaver internally,
        # so we patch at the module level
        mock_state = MagicMock()
        mock_state.values = {"some": "state"}

        with (
            pytest.MonkeyPatch.context() as mp,
        ):
            # Patch AsyncSqliteSaver to avoid real SQLite
            mock_saver = AsyncMock()
            mock_saver.__aenter__ = AsyncMock(return_value=mock_saver)
            mock_saver.__aexit__ = AsyncMock(return_value=False)

            mp.setattr(
                "amelia.server.orchestrator.service.AsyncSqliteSaver.from_conn_string",
                MagicMock(return_value=mock_saver),
            )

            # Patch graph.aget_state to return valid checkpoint
            mock_graph = MagicMock()
            mock_graph.aget_state = AsyncMock(return_value=mock_state)
            mp.setattr(service, "_create_server_graph", MagicMock(return_value=mock_graph))

            # Patch _run_workflow_with_retry to avoid real execution
            service._run_workflow_with_retry = AsyncMock()

            await service.resume_workflow("wf-1")

        # Verify error fields cleared
        assert wf.failure_reason is None
        assert wf.consecutive_errors == 0
        assert wf.last_error_context is None
        assert wf.completed_at is None
        assert wf.workflow_status == WorkflowStatus.IN_PROGRESS

        # Verify state was updated in DB
        repository.update.assert_called_once_with(wf)

    async def test_resume_emits_started_event(
        self,
        service: OrchestratorService,
        repository: AsyncMock,
        event_bus: MagicMock,
    ) -> None:
        """Successful resume should emit WORKFLOW_STARTED with resumed=True."""
        wf = _make_workflow("wf-1", WorkflowStatus.FAILED)
        wf.failure_reason = "Server restarted"
        wf.consecutive_errors = 0
        wf.last_error_context = None
        wf.completed_at = None
        wf.execution_state = MagicMock()
        wf.worktree_path = "/tmp/wt-event"
        repository.get = AsyncMock(return_value=wf)

        mock_state = MagicMock()
        mock_state.values = {"some": "state"}

        with pytest.MonkeyPatch.context() as mp:
            mock_saver = AsyncMock()
            mock_saver.__aenter__ = AsyncMock(return_value=mock_saver)
            mock_saver.__aexit__ = AsyncMock(return_value=False)
            mp.setattr(
                "amelia.server.orchestrator.service.AsyncSqliteSaver.from_conn_string",
                MagicMock(return_value=mock_saver),
            )
            mock_graph = MagicMock()
            mock_graph.aget_state = AsyncMock(return_value=mock_state)
            mp.setattr(service, "_create_server_graph", MagicMock(return_value=mock_graph))
            service._run_workflow_with_retry = AsyncMock()

            await service.resume_workflow("wf-1")

        # Check WORKFLOW_STARTED event with resumed=True
        saved_events = [c[0][0] for c in repository.save_event.call_args_list]
        started_events = [e for e in saved_events if e.event_type == EventType.WORKFLOW_STARTED]
        assert len(started_events) == 1
        assert started_events[0].data["resumed"] is True
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_workflow_recovery.py::TestResumeWorkflow -v`
Expected: FAIL — `resume_workflow` method doesn't exist yet.

**Step 3: Implement `resume_workflow()`**

Add this method to `OrchestratorService` after the `cancel_workflow` method (use `insert_after_symbol` on `OrchestratorService/cancel_workflow`):

```python
    async def resume_workflow(self, workflow_id: str) -> ServerExecutionState:
        """Resume a failed workflow from its last checkpoint.

        Validates the workflow is in FAILED status, has a valid checkpoint,
        and the worktree is not occupied. Then clears error state, transitions
        to IN_PROGRESS, and re-launches the workflow task.

        Args:
            workflow_id: The workflow to resume.

        Returns:
            The updated workflow state.

        Raises:
            WorkflowNotFoundError: If workflow doesn't exist.
            InvalidStateError: If workflow is not FAILED, has no checkpoint,
                or its worktree is occupied.
        """
        workflow = await self._repository.get(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(workflow_id)

        if workflow.workflow_status != WorkflowStatus.FAILED:
            raise InvalidStateError(
                f"Cannot resume: workflow must be in 'failed' status, "
                f"got '{workflow.workflow_status}'",
                workflow_id=workflow_id,
                current_status=workflow.workflow_status,
            )

        # Validate checkpoint exists (read-only, safe outside lock)
        async with AsyncSqliteSaver.from_conn_string(
            str(self._checkpoint_path)
        ) as checkpointer:
            graph = self._create_server_graph(checkpointer)
            config: RunnableConfig = {
                "configurable": {"thread_id": workflow_id},
            }
            checkpoint_state = await graph.aget_state(config)
            if checkpoint_state is None or not checkpoint_state.values:
                raise InvalidStateError(
                    "Cannot resume: no checkpoint found for workflow",
                    workflow_id=workflow_id,
                    current_status=workflow.workflow_status,
                )

        async with self._start_lock:
            # Check worktree is not occupied (under lock to prevent TOCTOU race)
            if workflow.worktree_path in self._active_tasks:
                existing_id, _ = self._active_tasks[workflow.worktree_path]
                raise InvalidStateError(
                    f"Cannot resume: worktree is occupied by workflow {existing_id}",
                    workflow_id=workflow_id,
                    current_status=workflow.workflow_status,
                )

            # Clear error state and transition to IN_PROGRESS
            workflow.failure_reason = None
            workflow.consecutive_errors = 0
            workflow.last_error_context = None
            workflow.completed_at = None
            workflow.workflow_status = WorkflowStatus.IN_PROGRESS
            await self._repository.update(workflow)

            await self._emit(
                workflow_id,
                EventType.WORKFLOW_STARTED,
                "Workflow resumed from checkpoint",
                data={"resumed": True},
            )

            logger.info("Resuming workflow", workflow_id=workflow_id)

            # Launch workflow task (same as start_workflow)
            task = asyncio.create_task(
                self._run_workflow_with_retry(workflow_id, workflow)
            )
            self._active_tasks[workflow.worktree_path] = (workflow_id, task)

        def cleanup_task(_: asyncio.Task[None]) -> None:
            """Clean up resources when resumed workflow task completes."""
            self._active_tasks.pop(workflow.worktree_path, None)
            self._sequence_counters.pop(workflow_id, None)
            self._sequence_locks.pop(workflow_id, None)
            logger.debug(
                "Resumed workflow task completed",
                workflow_id=workflow_id,
                worktree_path=workflow.worktree_path,
            )

        task.add_done_callback(cleanup_task)

        return workflow
```

Note: This requires the following imports already exist at the top of `service.py`: `AsyncSqliteSaver`, `RunnableConfig`, `asyncio`, `EventType`. The file already imports all of these. Verify by checking existing imports.

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_workflow_recovery.py::TestResumeWorkflow -v`
Expected: PASS

**Step 5: Run full test suite for state.py and service.py**

Run: `uv run pytest tests/unit/test_workflow_recovery.py -v`
Expected: All tests PASS.

**Step 6: Commit**

```bash
git add amelia/server/orchestrator/service.py tests/unit/test_workflow_recovery.py
git commit -m "feat(recovery): implement resume_workflow service method"
```

---

### Task 4: Add resume REST endpoint

**Files:**
- Modify: `amelia/server/routes/workflows.py` (add endpoint after `cancel_workflow`)
- Test: `tests/unit/test_workflow_recovery.py` (append endpoint test, or verify via integration)

**Context:** Follow the exact pattern of `cancel_workflow` at `routes/workflows.py:378-398`. The endpoint calls `orchestrator.resume_workflow()` and returns an `ActionResponse`.

**Step 1: Write the failing test**

Append to `tests/unit/test_workflow_recovery.py`:

```python
from unittest.mock import patch

from fastapi.testclient import TestClient


class TestResumeEndpoint:
    """Tests for POST /api/workflows/{id}/resume endpoint."""

    def _get_test_app(self) -> TestClient:
        """Create a test app with mocked dependencies."""
        from fastapi import FastAPI
        from amelia.server.routes.workflows import router, configure_exception_handlers
        from amelia.server.dependencies import get_orchestrator, get_repository

        app = FastAPI()
        app.include_router(router, prefix="/api/workflows")
        configure_exception_handlers(app)

        # These will be overridden per-test
        return app

    async def test_resume_endpoint_success(self) -> None:
        """POST /resume should return 200 with resumed status."""
        from amelia.server.dependencies import get_orchestrator

        app = self._get_test_app()

        mock_orchestrator = AsyncMock()
        mock_workflow = MagicMock()
        mock_workflow.id = "wf-1"
        mock_orchestrator.resume_workflow = AsyncMock(return_value=mock_workflow)

        app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator

        client = TestClient(app)
        response = client.post("/api/workflows/wf-1/resume")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resumed"
        assert data["workflow_id"] == "wf-1"

    async def test_resume_endpoint_not_found(self) -> None:
        """POST /resume for missing workflow should return 404."""
        from amelia.server.dependencies import get_orchestrator

        app = self._get_test_app()

        mock_orchestrator = AsyncMock()
        mock_orchestrator.resume_workflow = AsyncMock(
            side_effect=WorkflowNotFoundError("wf-missing")
        )

        app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator

        client = TestClient(app)
        response = client.post("/api/workflows/wf-missing/resume")

        assert response.status_code == 404

    async def test_resume_endpoint_conflict(self) -> None:
        """POST /resume for non-FAILED workflow should return 409."""
        from amelia.server.dependencies import get_orchestrator

        app = self._get_test_app()

        mock_orchestrator = AsyncMock()
        mock_orchestrator.resume_workflow = AsyncMock(
            side_effect=InvalidStateError(
                "Cannot resume",
                workflow_id="wf-1",
                current_status=WorkflowStatus.IN_PROGRESS,
            )
        )

        app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator

        client = TestClient(app)
        response = client.post("/api/workflows/wf-1/resume")

        assert response.status_code == 409
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_workflow_recovery.py::TestResumeEndpoint -v`
Expected: FAIL — no `/resume` endpoint yet.

**Step 3: Implement the endpoint**

Add after the `cancel_workflow` endpoint in `amelia/server/routes/workflows.py` (use `insert_after_symbol` on `cancel_workflow` in the routes file):

```python
@router.post("/{workflow_id}/resume", response_model=ActionResponse)
async def resume_workflow(
    workflow_id: str,
    orchestrator: OrchestratorService = Depends(get_orchestrator),
) -> ActionResponse:
    """Resume a failed workflow from its last checkpoint.

    Args:
        workflow_id: Unique workflow identifier.
        orchestrator: Orchestrator service dependency.

    Returns:
        ActionResponse with status and workflow_id.

    Raises:
        WorkflowNotFoundError: If workflow doesn't exist.
        InvalidStateError: If workflow cannot be resumed.
    """
    await orchestrator.resume_workflow(workflow_id)
    logger.info("Resumed workflow", workflow_id=workflow_id)
    return ActionResponse(status="resumed", workflow_id=workflow_id)
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_workflow_recovery.py::TestResumeEndpoint -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/server/routes/workflows.py tests/unit/test_workflow_recovery.py
git commit -m "feat(api): add POST /api/workflows/{id}/resume endpoint"
```

---

### Task 5: Add `resumeWorkflow` to API client and CLI

**Files:**
- Modify: `amelia/client/api.py` (add `resume_workflow` after `cancel_workflow`)
- Modify: `amelia/client/cli.py` (add `resume_command` function)
- Modify: `amelia/main.py` (register `resume_command`)

**Context:** Follow the `cancel_workflow` / `cancel_command` pattern exactly. The CLI command takes a `WORKFLOW_ID` argument instead of auto-detecting from worktree (per the design spec: `amelia resume WORKFLOW_ID`).

**Step 1: Add `resume_workflow` to `AmeliaClient`**

In `amelia/client/api.py`, add after `cancel_workflow`:

```python
    async def resume_workflow(self, workflow_id: str) -> None:
        """Resume a failed workflow from its last checkpoint.

        Args:
            workflow_id: Workflow ID to resume.

        Raises:
            WorkflowNotFoundError: If workflow doesn't exist.
            InvalidRequestError: If workflow cannot be resumed (wrong status, no checkpoint).
            ServerUnreachableError: If server is not running.
        """
        async with self._http_client() as client:
            response = await client.post(
                f"{self.base_url}/api/workflows/{workflow_id}/resume"
            )

            if response.status_code == 200:
                return
            elif response.status_code == 404:
                raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")
            elif response.status_code == 409:
                data = response.json()
                raise InvalidRequestError(data.get("detail", "Cannot resume workflow"))
            else:
                response.raise_for_status()
```

Check that `InvalidRequestError` is already imported — look at existing imports in `amelia/client/api.py`. If not, add it.

**Step 2: Add `resume_command` to CLI**

In `amelia/client/cli.py`, add after `cancel_command`:

```python
def resume_command(
    workflow_id: Annotated[str, typer.Argument(help="Workflow ID to resume")],
) -> None:
    """Resume a failed workflow from its last checkpoint.

    Sends a resume request to the running Amelia server. The workflow must
    be in FAILED status with a valid checkpoint to resume.

    Args:
        workflow_id: The workflow ID to resume.
    """
    client = AmeliaClient()

    async def _resume() -> None:
        await client.resume_workflow(workflow_id=workflow_id)

    try:
        asyncio.run(_resume())
        console.print(f"[green]✓[/green] Workflow [bold]{workflow_id}[/bold] resumed")
    except WorkflowNotFoundError:
        console.print(f"[red]Error:[/red] Workflow {workflow_id} not found")
        raise typer.Exit(1) from None
    except InvalidRequestError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None
    except ServerUnreachableError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\n[yellow]Start the server:[/yellow] amelia server")
        raise typer.Exit(1) from None
```

Check that `InvalidRequestError`, `WorkflowNotFoundError`, and `ServerUnreachableError` are already imported at the top of `cli.py`.

**Step 3: Register in `amelia/main.py`**

Add `resume_command` to the import and register it:

In the import block (around line 15):
```python
from amelia.client.cli import (
    approve_command,
    cancel_command,
    plan_command,
    reject_command,
    resume_command,  # Add this
    run_command,
    start_command,
    status_command,
)
```

After the `cancel` command registration (around line 38):
```python
app.command(name="resume", help="Resume a failed workflow from checkpoint.")(resume_command)
```

**Step 4: Run linter and type check**

Run: `uv run ruff check amelia/client/api.py amelia/client/cli.py amelia/main.py`
Run: `uv run mypy amelia/client amelia/main.py`
Expected: No errors.

**Step 5: Commit**

```bash
git add amelia/client/api.py amelia/client/cli.py amelia/main.py
git commit -m "feat(cli): add amelia resume command and API client method"
```

---

### Task 6: Add `resumeWorkflow` to dashboard API client

**Files:**
- Modify: `dashboard/src/api/client.ts` (add `resumeWorkflow` after `cancelWorkflow`)
- Test: `dashboard/src/api/__tests__/client.test.ts`

**Context:** Follow the `cancelWorkflow` pattern at `client.ts:291-297`.

**Step 1: Write the failing test**

In `dashboard/src/api/__tests__/client.test.ts`, add a test case mirroring the existing `cancelWorkflow` test. Find the test for `cancelWorkflow` and add after it:

```typescript
{
  method: 'resumeWorkflow' as const,
  args: ['workflow-123'],
  expectedUrl: '/api/workflows/workflow-123/resume',
  expectedMethod: 'POST',
},
```

Add this to the same test array/data structure that tests the other API methods.

**Step 2: Run test to verify it fails**

Run: `cd dashboard && pnpm test:run -- --reporter=verbose api/__tests__/client.test.ts`
Expected: FAIL — `resumeWorkflow` doesn't exist.

**Step 3: Implement `resumeWorkflow`**

In `dashboard/src/api/client.ts`, add after `cancelWorkflow`:

```typescript
  /**
   * Resume a failed workflow from its last checkpoint.
   *
   * @example
   * await api.resumeWorkflow('workflow-123');
   */
  async resumeWorkflow(id: string): Promise<void> {
    const response = await fetchWithTimeout(`${API_BASE_URL}/workflows/${id}/resume`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    await handleResponse(response);
  },
```

**Step 4: Run test to verify it passes**

Run: `cd dashboard && pnpm test:run -- --reporter=verbose api/__tests__/client.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/src/api/client.ts dashboard/src/api/__tests__/client.test.ts
git commit -m "feat(dashboard): add resumeWorkflow API client method"
```

---

### Task 7: Add resume action and hook to dashboard

**Files:**
- Modify: `dashboard/src/actions/workflows.ts` (add `resumeAction`)
- Modify: `dashboard/src/hooks/useWorkflowActions.ts` (add `resumeWorkflow`)
- Test: `dashboard/src/actions/__tests__/workflows.test.ts`
- Test: `dashboard/src/hooks/__tests__/useWorkflowActions.test.tsx`

**Context:** Follow the `cancelAction` / `cancelWorkflow` patterns exactly.

**Step 1: Add `resumeAction`**

In `dashboard/src/actions/workflows.ts`, add after `cancelAction`:

```typescript
export async function resumeAction({ params }: ActionFunctionArgs): Promise<ActionResult> {
  if (!params.id) {
    return { success: false, action: 'resumed', error: 'Workflow ID required' };
  }

  try {
    await api.resumeWorkflow(params.id);
    return { success: true, action: 'resumed' };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to resume workflow';
    return { success: false, action: 'resumed', error: message };
  }
}
```

**Step 2: Add `resumeWorkflow` to hook**

In `dashboard/src/hooks/useWorkflowActions.ts`:

1. Add to the `UseWorkflowActionsResult` interface:
```typescript
resumeWorkflow: (workflowId: string) => Promise<void>;
```

2. Add the implementation (follow `cancelWorkflow` pattern):
```typescript
const resumeWorkflow = useCallback(
  async (workflowId: string) => {
    const actionId = `resume-${workflowId}`;
    addPendingAction(actionId);

    try {
      await api.resumeWorkflow(workflowId);
      toast.success('Workflow resumed');
    } catch (error) {
      toast.error(`Resume failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      removePendingAction(actionId);
    }
  },
  [addPendingAction, removePendingAction]
);
```

3. Add `resumeWorkflow` to the return object.

**Step 3: Add tests**

In `dashboard/src/actions/__tests__/workflows.test.ts`, add a test block for `resumeAction` following the `cancelAction` test pattern:

```typescript
describe('resumeAction', () => {
  it('should call api.resumeWorkflow', async () => {
    vi.mocked(api.resumeWorkflow).mockResolvedValueOnce(undefined);
    const result = await resumeAction({ params: { id: 'wf-1' } } as any);
    expect(api.resumeWorkflow).toHaveBeenCalledWith('wf-1');
    expect(result).toEqual({ success: true, action: 'resumed' });
  });

  it('should handle errors', async () => {
    vi.mocked(api.resumeWorkflow).mockRejectedValueOnce(new Error('Cannot resume'));
    const result = await resumeAction({ params: { id: 'wf-1' } } as any);
    expect(result).toEqual({ success: false, action: 'resumed', error: 'Cannot resume' });
  });
});
```

In `dashboard/src/hooks/__tests__/useWorkflowActions.test.tsx`, add a test for `resumeWorkflow` following the `cancelWorkflow` test data pattern.

**Step 4: Run tests**

Run: `cd dashboard && pnpm test:run -- --reporter=verbose`
Expected: All tests PASS.

**Step 5: Commit**

```bash
git add dashboard/src/actions/workflows.ts dashboard/src/hooks/useWorkflowActions.ts
git add dashboard/src/actions/__tests__/workflows.test.ts dashboard/src/hooks/__tests__/useWorkflowActions.test.tsx
git commit -m "feat(dashboard): add resume action and hook"
```

---

### Task 8: Add resume button to workflow detail page

**Files:**
- Modify: `dashboard/src/pages/WorkflowDetailPage.tsx` (add resume button in FAILED state)
- Modify: `dashboard/src/components/ApprovalControls.tsx` (or add separate component)

**Context:** The design spec says the button appears when: (1) status is FAILED, (2) the last WORKFLOW_FAILED event has `data.recoverable === true`. The button should be alongside existing action buttons. Look at how `ApprovalControls` is rendered in `WorkflowDetailPage.tsx:130` and decide whether to add the resume button to that component or render a separate button conditionally.

The simplest approach: add a conditional resume button directly in `WorkflowDetailPage.tsx` near where `ApprovalControls` is rendered. This avoids coupling resume logic into the approval component.

**Step 1: Determine recoverable status**

Read the events from the store. The workflow detail page already has access to `allEvents`. Check if the most recent `workflow_failed` event has `data.recoverable === true`.

Add to `WorkflowDetailPage.tsx`:

```tsx
// Near the top of the component, after existing hooks
const isRecoverable = useMemo(() => {
  if (workflow?.status !== 'failed') return false;
  const failedEvents = allEvents
    .filter((e: WorkflowEvent) => e.event_type === 'workflow_failed')
    .sort((a: WorkflowEvent, b: WorkflowEvent) => b.sequence - a.sequence);
  return failedEvents.length > 0 && failedEvents[0].data?.recoverable === true;
}, [workflow?.status, allEvents]);
```

**Step 2: Add resume button**

Import `useWorkflowActions` (or use the existing action pattern with `useFetcher`). Add a resume button that's visible when `isRecoverable` is true:

```tsx
{isRecoverable && (
  <div className="p-4 border border-border rounded-lg bg-card">
    <h4 className="font-heading text-xs font-semibold tracking-widest text-muted-foreground mb-2">
      RECOVERY
    </h4>
    <p className="text-sm text-muted-foreground mb-3">
      This workflow failed due to a server restart and can be resumed from its last checkpoint.
    </p>
    <Button
      onClick={() => resumeWorkflow(workflow.id)}
      disabled={isResuming}
      variant="outline"
    >
      <RotateCcw className="w-4 h-4 mr-2" />
      Resume
    </Button>
  </div>
)}
```

Import `RotateCcw` from `lucide-react` and `Button` from `@/components/ui/button`. Set up `resumeWorkflow` and `isResuming` state from the hook or inline.

**Step 3: Add tests**

In `dashboard/src/pages/WorkflowDetailPage.test.tsx`, add tests:

```typescript
it('shows resume button for recoverable failed workflows', () => {
  // Render with a failed workflow and a workflow_failed event with recoverable: true
  // Assert the Resume button is visible
});

it('does not show resume button for non-recoverable failed workflows', () => {
  // Render with a failed workflow and a workflow_failed event without recoverable
  // Assert the Resume button is NOT visible
});
```

**Step 4: Run tests**

Run: `cd dashboard && pnpm test:run -- --reporter=verbose pages/WorkflowDetailPage.test.tsx`
Expected: PASS

**Step 5: Run type-check and lint**

Run: `cd dashboard && pnpm type-check && pnpm lint`
Expected: No errors.

**Step 6: Commit**

```bash
git add dashboard/src/pages/WorkflowDetailPage.tsx
git commit -m "feat(dashboard): add resume button for recoverable failed workflows"
```

---

### Task 9: Full lint, type-check, and test pass

**Files:** None (validation only)

**Step 1: Run Python checks**

Run: `uv run ruff check amelia tests`
Run: `uv run mypy amelia`
Run: `uv run pytest tests/unit/ -v`

Fix any issues.

**Step 2: Run frontend checks**

Run: `cd dashboard && pnpm type-check && pnpm lint && pnpm test:run`

Fix any issues.

**Step 3: Run existing test suite (check no regressions)**

Run: `uv run pytest tests/ -v --timeout=60`

**Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: lint and type-check fixes for workflow recovery"
```

---

## File Path Corrections vs. Design Spec

The design spec mentions some file paths that don't match the actual codebase:

| Design Spec Path | Actual Path |
|-----------------|-------------|
| `amelia/cli/commands/resume.py` | `amelia/client/cli.py` (add function, register in `amelia/main.py`) |
| `dashboard/src/stores/workflow-store.ts` | `dashboard/src/store/workflowStore.ts` |
| `dashboard/src/components/workflow-detail.tsx` | `dashboard/src/pages/WorkflowDetailPage.tsx` |

## Actual Files Changed

| File | Change |
|------|--------|
| `amelia/server/models/state.py` | Add FAILED → IN_PROGRESS to `VALID_TRANSITIONS` |
| `amelia/server/orchestrator/service.py` | Implement `recover_interrupted_workflows()`, add `resume_workflow()` |
| `amelia/server/routes/workflows.py` | Add `POST /api/workflows/{id}/resume` endpoint |
| `amelia/client/api.py` | Add `resume_workflow()` to `AmeliaClient` |
| `amelia/client/cli.py` | Add `resume_command` function |
| `amelia/main.py` | Register `resume` CLI command |
| `dashboard/src/api/client.ts` | Add `resumeWorkflow()` method |
| `dashboard/src/actions/workflows.ts` | Add `resumeAction` |
| `dashboard/src/hooks/useWorkflowActions.ts` | Add `resumeWorkflow` to hook |
| `dashboard/src/pages/WorkflowDetailPage.tsx` | Add conditional resume button |
| `tests/unit/test_workflow_recovery.py` | Unit tests for all backend changes |
| `dashboard/src/api/__tests__/client.test.ts` | Test for `resumeWorkflow` |
| `dashboard/src/actions/__tests__/workflows.test.ts` | Test for `resumeAction` |
| `dashboard/src/hooks/__tests__/useWorkflowActions.test.tsx` | Test for `resumeWorkflow` hook |
| `dashboard/src/pages/WorkflowDetailPage.test.tsx` | Test for resume button visibility |
