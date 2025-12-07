# LangGraph Execution Bridge (Archived)

> **Status:** Completed (PR 1 merged)
> **Date:** 2025-12-06
> **Branch:** `feat/langgraph-execution-bridge`
> **Commit:** a65b5c3
>
> **Note:** This is archived documentation from a completed feature. The implementation is now part of the main codebase.

## Summary

This document describes the implementation of the LangGraph Execution Bridge, which connects the server layer (FastAPI, SQLite, REST endpoints) to the existing core LangGraph orchestrator. The implementation provides checkpoint persistence via `langgraph-checkpoint-sqlite`, interrupt-based human approval for server mode, event streaming from LangGraph to WorkflowEvents, and retry logic for transient failures. The final implementation uses `astream(stream_mode='updates')` for robust interrupt detection.

---

## Design

### Overview

This design connects the server layer (FastAPI, SQLite, REST endpoints) to the existing core LangGraph orchestrator, implementing the missing `_run_workflow()` method in `OrchestratorService`.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Server Layer                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ REST API     │───▶│ Orchestrator │───▶│ EventBus     │──▶ WS │
│  │ (FastAPI)    │    │ Service      │    │              │       │
│  └──────────────┘    └──────┬───────┘    └──────────────┘       │
│                             │                                    │
│                    ┌────────▼────────┐                          │
│                    │ ExecutionBridge │  ◀── NEW (method)        │
│                    └────────┬────────┘                          │
│                             │                                    │
│                    ┌────────▼────────┐                          │
│                    │ langgraph-      │  ◀── PACKAGE             │
│                    │ checkpoint-     │                          │
│                    │ sqlite          │                          │
│                    └────────┬────────┘                          │
└─────────────────────────────┼───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                         Core Layer                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ LangGraph State Machine (existing)                        │   │
│  │ architect_node → human_approval → developer ↔ reviewer    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Components:**
- `ExecutionBridge` - Method in OrchestratorService that invokes LangGraph, handles interrupts, streams events
- `langgraph-checkpoint-sqlite` - Official LangGraph package for checkpoint persistence
- State composition - `ServerExecutionState.execution_state: ExecutionState`

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Human approval | Interrupt-based (`interrupt_before`) | LangGraph native, keeps core clean |
| Checkpoint persistence | `langgraph-checkpoint-sqlite` package | Battle-tested, handles serialization/migrations |
| State model | Composition (wrap `ExecutionState`) | Preserves architectural boundary |
| Event streaming | Map LangGraph → WorkflowEvent | Stable dashboard interface |
| Error handling | Auto-retry with exponential backoff | Resilience for transient failures |
| Retry config | Simplified (max_retries + base_delay) | Error classification is implementation concern, not config |
| CLI vs Server | Execution mode in graph config | Same graph code, different approval behavior |

### Serialization Convention

**Enum Value Serialization:**

Python code uses UPPERCASE enum members internally, but JSON serialization uses snake_case lowercase to match frontend expectations:

| Python Code | JSON Serialization |
|-------------|-------------------|
| `EventType.STAGE_STARTED` | `"stage_started"` |
| `EventType.STAGE_COMPLETED` | `"stage_completed"` |
| `EventType.APPROVAL_REQUIRED` | `"approval_required"` |
| `EventType.SYSTEM_ERROR` | `"system_error"` |
| `EventType.SYSTEM_INFO` | `"system_info"` |

**Implementation:**

Use Pydantic's `use_enum_values=True` or custom serializer:

```python
from enum import Enum
from pydantic import BaseModel, ConfigDict

class EventType(str, Enum):
    """Event types - serialize to lowercase snake_case."""
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    APPROVAL_REQUIRED = "approval_required"
    SYSTEM_ERROR = "system_error"
    SYSTEM_INFO = "system_info"

class WorkflowEvent(BaseModel):
    """Pydantic will serialize EventType.STAGE_STARTED as 'stage_started'."""
    model_config = ConfigDict(use_enum_values=True)

    event_type: EventType
    message: str
    data: dict | None = None
```

### State Model

`ServerExecutionState` wraps `ExecutionState` via composition:

```python
from pydantic import Field

class WorkflowStatus(str, Enum):
    """Workflow status - serialize to lowercase."""
    PENDING = "pending"
    RUNNING = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ServerExecutionState(BaseModel):
    # Server metadata
    id: str
    issue_id: str
    worktree_path: str
    worktree_name: str  # Derived from path
    workflow_status: WorkflowStatus = Field(
        default=WorkflowStatus.PENDING,
        alias="status",  # Serialize as "status" in JSON
    )
    started_at: datetime
    completed_at: datetime | None = None
    current_stage: str = "initializing"
    failure_reason: str | None = None

    # Core orchestration state - always present
    execution_state: ExecutionState

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,  # Allow both "workflow_status" and "status"
    )
```

**Field Mapping:**
- Python internal field: `workflow_status` (type: `WorkflowStatus`)
- REST API JSON field: `status` (type: `string`)
- This ensures frontend receives `{"status": "in_progress"}` not `{"workflow_status": "RUNNING"}`

**WorkflowStatus Value Mapping:**

| Python Enum | JSON Value | Description |
|-------------|------------|-------------|
| `PENDING` | `"pending"` | Not yet started |
| `RUNNING` | `"in_progress"` | Currently executing |
| `BLOCKED` | `"blocked"` | Awaiting human approval |
| `COMPLETED` | `"completed"` | Finished successfully |
| `FAILED` | `"failed"` | Finished with error |
| `CANCELLED` | `"cancelled"` | Cancelled by user |

**Initialization:** All fields populated at workflow creation. Issue fetched immediately, `worktree_name` derived from path. No nullable fields except `completed_at` and `failure_reason`.

### Checkpoint Persistence

Use the official `langgraph-checkpoint-sqlite` package instead of custom implementation.

**Installation:**
```bash
uv add langgraph-checkpoint-sqlite
```

**Usage:**
```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# Create checkpointer with dedicated file (separate from main DB)
checkpointer = AsyncSqliteSaver.from_conn_string("~/.amelia/checkpoints.db")

# Or share connection with existing database
async with aiosqlite.connect("~/.amelia/amelia.db") as conn:
    checkpointer = AsyncSqliteSaver(conn)
    graph = create_orchestrator_graph(checkpoint_saver=checkpointer)
```

**Why package over custom:**
- Handles checkpoint serialization (pickle with fallbacks)
- Manages schema migrations automatically
- Provides TTL-based cleanup via `AsyncSqliteSaver.setup(ttl=timedelta(days=7))`
- ~150 lines of code we don't need to write/test/maintain

**Thread ID:** Maps to `workflow_id` for checkpoint isolation.

### CLI vs Server Execution Mode

The same graph must work for both CLI (blocking `typer.confirm`) and server (interrupt-based) contexts.

**Solution:** Pass execution mode via graph config, check in `human_approval_node`:

```python
# In amelia/core/orchestrator.py

def human_approval_node(state: ExecutionState, config: RunnableConfig) -> ExecutionState:
    """Handle human approval - behavior depends on execution mode."""

    execution_mode = config.get("configurable", {}).get("execution_mode", "cli")

    if execution_mode == "cli":
        # CLI mode: blocking prompt
        if state.plan:
            display_plan(state.plan)
        approved = typer.confirm("Do you approve this plan?", default=False)
        return state.model_copy(update={"human_approved": approved})

    else:
        # Server mode: approval comes from resumed state after interrupt
        # If human_approved is already set (from resume), use it
        # Otherwise, just return - the interrupt mechanism will pause here
        return state
```

**Graph creation with mode:**
```python
# CLI usage (existing)
config = {
    "configurable": {
        "thread_id": "cli-session",
        "execution_mode": "cli",
    }
}
result = await graph.ainvoke(initial_state, config=config)

# Server usage (new)
config = {
    "configurable": {
        "thread_id": workflow_id,
        "execution_mode": "server",
    }
}
async for event in graph.astream_events(
    state.execution_state,
    config=config,
    interrupt_before=["human_approval_node"],
):
    await self._handle_graph_event(workflow_id, event)
```

### Execution Bridge

The `_run_workflow()` implementation:

```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# Nodes that emit stage events
STAGE_NODES = frozenset({
    "architect_node",
    "human_approval_node",
    "developer_node",
    "reviewer_node",
})

async def _run_workflow(
    self,
    workflow_id: str,
    state: ServerExecutionState,
) -> None:
    """Execute workflow via LangGraph with interrupt support."""

    # 1. Create graph with checkpointer
    async with AsyncSqliteSaver.from_conn_string(
        str(self._checkpoint_path)
    ) as checkpointer:
        graph = create_orchestrator_graph(checkpoint_saver=checkpointer)

        # 2. Configure for server execution
        config = {
            "configurable": {
                "thread_id": workflow_id,
                "execution_mode": "server",
            }
        }

        # 3. Emit workflow lifecycle event
        await self._emit(
            workflow_id,
            EventType.WORKFLOW_STARTED,
            "Workflow execution started",
            data={"issue_id": state.issue_id},
        )

        # 4. Stream execution with event emission
        try:
            async for event in graph.astream_events(
                state.execution_state,
                config=config,
                interrupt_before=["human_approval_node"],
            ):
                await self._handle_graph_event(workflow_id, event)

            # 5. Emit workflow completion event
            await self._emit(
                workflow_id,
                EventType.WORKFLOW_COMPLETED,
                "Workflow completed successfully",
                data={"final_state": state.current_stage},
            )

        except GraphInterrupt:
            # Human approval required - checkpoint saved automatically
            await self._emit_approval_required(workflow_id, state)
            return  # Execution pauses here

        except Exception as e:
            # 6. Emit workflow failure event
            await self._emit(
                workflow_id,
                EventType.WORKFLOW_FAILED,
                f"Workflow failed: {str(e)}",
                data={"error": str(e), "stage": state.current_stage},
            )
            await self._handle_execution_error(workflow_id, e)
            raise
```

### Human Approval Flow

```
1. Graph reaches human_approval_node
   └─▶ GraphInterrupt raised (checkpoint saved automatically)
   └─▶ _run_workflow() catches, emits APPROVAL_REQUIRED event
   └─▶ Workflow status → BLOCKED

2. Dashboard shows approval UI
   └─▶ User clicks Approve/Reject

3. REST API called
   └─▶ POST /workflows/{id}/approve  (or /reject)
   └─▶ OrchestratorService.approve_workflow()

4. Resume from checkpoint
   └─▶ Load checkpoint, update state.human_approved = True/False
   └─▶ graph.ainvoke(None, config)  # Resume with updated state
   └─▶ Graph continues to developer_node (or END if rejected)
```

**Resume implementation:**
```python
async def approve_workflow(self, workflow_id: str) -> None:
    """Resume workflow after approval."""
    async with AsyncSqliteSaver.from_conn_string(
        str(self._checkpoint_path)
    ) as checkpointer:
        graph = create_orchestrator_graph(checkpoint_saver=checkpointer)

        config = {
            "configurable": {
                "thread_id": workflow_id,
                "execution_mode": "server",
            }
        }

        # Update state with approval decision
        await graph.aupdate_state(
            config,
            {"human_approved": True},
        )

        # Resume execution
        async for event in graph.astream_events(None, config=config):
            await self._handle_graph_event(workflow_id, event)
```

### Event Streaming

Map LangGraph events to existing WorkflowEvents:

```python
from amelia.server.models.events import EventType

async def _handle_graph_event(
    self,
    workflow_id: str,
    event: dict,
) -> None:
    """Translate LangGraph events to WorkflowEvents and emit."""

    event_type = event.get("event")
    node_name = event.get("name")

    if event_type == "on_chain_start":
        if node_name in STAGE_NODES:
            await self._emit(
                workflow_id,
                EventType.STAGE_STARTED,
                f"Starting {node_name}",
                data={"stage": node_name},
            )

    elif event_type == "on_chain_end":
        if node_name in STAGE_NODES:
            await self._emit(
                workflow_id,
                EventType.STAGE_COMPLETED,
                f"Completed {node_name}",
                data={"stage": node_name, "output": event.get("data")},
            )

    elif event_type == "on_chain_error":
        error = event.get("data", {}).get("error", "Unknown error")
        await self._emit(
            workflow_id,
            EventType.SYSTEM_ERROR,
            f"Error in {node_name}: {error}",
            data={"stage": node_name, "error": str(error)},
        )

    elif event_type == "on_llm_stream":
        # Only emit in verbose mode to avoid flooding
        if self._verbose_mode.get(workflow_id, False):
            chunk = event.get("data", {}).get("chunk", "")
            if chunk:
                await self._emit(
                    workflow_id,
                    EventType.SYSTEM_INFO,  # Or add LLM_TOKEN to EventType
                    chunk,
                    data={"type": "llm_token"},
                )
```

**Event mapping:**

| LangGraph Event | WorkflowEvent | When |
|-----------------|---------------|------|
| Workflow start | `WORKFLOW_STARTED` | Beginning of `_run_workflow()` |
| `on_chain_start` | `STAGE_STARTED` | Node begins (if in STAGE_NODES) |
| `on_chain_end` | `STAGE_COMPLETED` | Node finishes (if in STAGE_NODES) |
| `on_chain_error` | `SYSTEM_ERROR` | Node fails |
| `on_llm_stream` | `SYSTEM_INFO` | Verbose mode only |
| `GraphInterrupt` | `APPROVAL_REQUIRED` | Before approval node |
| Workflow success | `WORKFLOW_COMPLETED` | End of successful execution |
| Workflow error | `WORKFLOW_FAILED` | Exception in execution |

**Required EventType additions:**
```python
class EventType(str, Enum):
    """Event types - serialize to lowercase snake_case."""
    WORKFLOW_STARTED = "workflow_started"     # NEW
    WORKFLOW_COMPLETED = "workflow_completed"  # NEW
    WORKFLOW_FAILED = "workflow_failed"        # NEW
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    APPROVAL_REQUIRED = "approval_required"
    SYSTEM_ERROR = "system_error"
    SYSTEM_INFO = "system_info"
```

### Error Handling & Retry

Simplified retry with typed exception handling:

```python
import asyncio
from httpx import TimeoutException

# Exceptions that warrant retry
TRANSIENT_EXCEPTIONS = (
    asyncio.TimeoutError,
    TimeoutException,
    ConnectionError,
    # Add SDK-specific rate limit errors as needed
)

async def _run_workflow_with_retry(
    self,
    workflow_id: str,
    state: ServerExecutionState,
) -> None:
    """Execute workflow with automatic retry for transient failures."""

    retry_config = state.execution_state.profile.retry
    attempt = 0

    while attempt <= retry_config.max_retries:
        try:
            await self._run_workflow(workflow_id, state)
            return  # Success

        except TRANSIENT_EXCEPTIONS as e:
            attempt += 1
            if attempt > retry_config.max_retries:
                await self._mark_failed(workflow_id, f"Failed after {attempt} attempts: {e}")
                raise

            delay = min(
                retry_config.base_delay * (2 ** (attempt - 1)),
                60.0,  # Hard cap at 60s
            )
            logger.warning(
                f"Transient error (attempt {attempt}/{retry_config.max_retries}), "
                f"retrying in {delay}s",
                workflow_id=workflow_id,
                error=str(e),
            )
            await asyncio.sleep(delay)

        except Exception as e:
            # Non-transient error - fail immediately
            await self._mark_failed(workflow_id, str(e))
            raise
```

**Error classification:**

| Error Type | Examples | Behavior |
|------------|----------|----------|
| Transient | `TimeoutError`, `ConnectionError`, rate limits | Retry with exponential backoff |
| Permanent | `ValueError`, `KeyError`, auth failures | Fail immediately |

### Configuration Schema

Simplified retry configuration:

```yaml
profiles:
  work:
    driver: api:openai
    tracker: jira
    retry:
      max_retries: 3
      base_delay: 1.0

  enterprise:
    driver: cli:claude
    tracker: github
    retry:
      max_retries: 5
      base_delay: 2.0
```

**Model addition:**

```python
class RetryConfig(BaseModel):
    """Retry configuration for transient failures."""
    max_retries: int = Field(default=3, ge=0, le=10)
    base_delay: float = Field(default=1.0, ge=0.1, le=30.0)

class Profile(BaseModel):
    name: str
    driver: DriverType
    tracker: TrackerType = "none"
    strategy: StrategyType = "single"
    execution_mode: ExecutionMode = "structured"
    plan_output_dir: str = "docs/plans"
    working_dir: str | None = None
    retry: RetryConfig = Field(default_factory=RetryConfig)
```

### Testing Strategy

**Test structure:**

```
tests/
├── unit/
│   ├── server/
│   │   └── orchestrator/
│   │       ├── test_execution_bridge.py  # _run_workflow with mocked graph
│   │       ├── test_event_mapping.py     # LangGraph → WorkflowEvent
│   │       └── test_retry_logic.py       # Backoff, error classification
│   └── core/
│       ├── test_retry_config.py          # RetryConfig validation
│       └── test_human_approval_node.py   # CLI vs server mode
├── integration/
│   ├── test_approval_flow.py             # Interrupt → approve → resume
│   ├── test_checkpoint_recovery.py       # Restart mid-workflow
│   └── test_concurrent_workflows.py      # Multiple workflows isolated
```

**TDD approach:**

| Component | Test First | Then Implement |
|-----------|------------|----------------|
| `RetryConfig` | Validation, defaults, bounds | Pydantic model |
| `human_approval_node` | CLI mode prompts, server mode passes through | Mode detection |
| `_run_workflow` | Mock graph, verify events emitted | Execution bridge |
| Event mapping | Each LangGraph event → correct WorkflowEvent | `_handle_graph_event` |
| Approval flow | Mock interrupt, verify resume with state | Full cycle |
| Error handling | Transient vs permanent classification | Retry wrapper |

### Implementation Order

1. **Add dependency** - `uv add langgraph-checkpoint-sqlite`
2. **RetryConfig model** - Add to `amelia/core/types.py`
3. **Update human_approval_node** - Add execution mode detection in `amelia/core/orchestrator.py`
4. **State model update** - Add `execution_state` to `ServerExecutionState`
5. **Event mapping** - Add `STAGE_NODES` constant and `_handle_graph_event()` to service
6. **Execution bridge** - Implement `_run_workflow()` with checkpointer
7. **Retry wrapper** - Add `_run_workflow_with_retry()`
8. **Approval flow** - Update `approve_workflow()` / `reject_workflow()` to resume graph
9. **Integration tests** - Full workflow cycles

### Checkpoint Cleanup

The `langgraph-checkpoint-sqlite` package supports TTL-based cleanup:

```python
# During server startup (lifespan)
async with AsyncSqliteSaver.from_conn_string(checkpoint_path) as saver:
    await saver.setup(ttl=timedelta(days=7))  # Auto-cleanup old checkpoints
```

For manual cleanup of completed workflows:
```python
# After workflow completes successfully
await checkpointer.adelete(config)
```

### Future: PostgreSQL Migration

Migration path when scaling:

1. `uv add langgraph-checkpoint-postgres`
2. Add `checkpoint_backend: sqlite | postgres` to server config
3. Factory function selects implementation:
   ```python
   def get_checkpointer(config: ServerConfig):
       if config.checkpoint_backend == "postgres":
           return AsyncPostgresSaver.from_conn_string(config.postgres_url)
       return AsyncSqliteSaver.from_conn_string(config.checkpoint_path)
   ```
4. No changes to `OrchestratorService` - same interface

---

## Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Connect the server layer to the existing LangGraph orchestrator by implementing `_run_workflow()` with checkpoint persistence, interrupt-based human approval, and event streaming.

**Architecture:** The ExecutionBridge pattern wraps the core LangGraph orchestrator with server-specific concerns: SQLite checkpointing via `langgraph-checkpoint-sqlite`, execution mode detection (CLI vs server), event mapping from LangGraph events to WorkflowEvents, and retry logic for transient failures.

**Tech Stack:** LangGraph, langgraph-checkpoint-sqlite, Pydantic, asyncio, aiosqlite

### Implementation Note: Stream API Change

**IMPORTANT:** The final implementation uses `astream(stream_mode='updates')` instead of the originally planned `astream_events()` approach. This change was necessary for proper interrupt detection in LangGraph.

**Key Differences:**
- **Original Plan:** Use `astream_events()` and catch `GraphInterrupt` exception
- **Final Implementation:** Use `astream(stream_mode='updates')` and detect `__interrupt__` in stream chunks
- **Method Name:** `_handle_stream_chunk()` instead of `_handle_graph_event()`
- **Interrupt Detection:** Check for `chunk.get("__interrupt__")` instead of catching exception

**Rationale:** The `astream_events()` API did not reliably expose interrupt signals in all scenarios. Switching to `astream(stream_mode='updates')` provides direct access to the `__interrupt__` marker in the stream, enabling more robust interrupt detection.

**Additional Enhancements (commit a65b5c3):**
- Worktree validation with `InvalidWorktreeError` before workflow start
- JSON serialization of Pydantic models via `model_dump(mode='json')` for SQLite persistence
- Custom `_pydantic_encoder` for nested Pydantic objects in event data

### PR Strategy

This implementation is split into **two PRs** for easier review and faster iteration:

#### PR 1: Core Execution Bridge (Tasks 1, 1.5, 4, 5, 6, 7, 10, 11, 12, 13, 14)

**Branch:** `feat/langgraph-execution-bridge`
**Status:** ✅ COMPLETED

The core interrupt/resume mechanism. Self-contained and functional without retry logic.

| Task | Description | Priority | Status |
|------|-------------|----------|--------|
| 1 | Add langgraph-checkpoint-sqlite dependency | Required | ✅ Done |
| 1.5 | Update create_orchestrator_graph with interrupt_before | **CRITICAL** | ✅ Done |
| 4 | Update human_approval_node for execution mode | Required | ✅ Done |
| 5 | Add execution_state to ServerExecutionState | Required | ✅ Done |
| 6 | Add STAGE_NODES and event mapping | Required | ✅ Done |
| 7 | Implement _run_workflow with interrupt detection | **CRITICAL** | ✅ Done |
| 10 | Update approve_workflow for graph resume | Required | ✅ Done |
| 11 | Update reject_workflow for graph state | Required | ✅ Done |
| 12 | Run full test suite and linting | Required | ✅ Done |
| 13 | Create integration test for approval flow | Required | ✅ Done |
| 14 | Final verification | Required | ✅ Done |

**Actual scope:** ~616 lines changed across 11 files (commit a65b5c3)

**Key Implementation Details:**
- Uses `astream(stream_mode='updates')` instead of `astream_events()` for better interrupt detection
- Includes worktree validation and JSON serialization for Pydantic models
- All 465 tests passing

#### PR 2: Retry Enhancement (Tasks 2, 3, 8, 9)

**Branch:** `feat/workflow-retry-logic`
**Depends on:** PR 1 merged

Optional but recommended enhancement for production resilience.

| Task | Description | Priority |
|------|-------------|----------|
| 2 | Add RetryConfig model | Optional |
| 3 | Add retry field to Profile | Optional |
| 8 | Implement retry wrapper | Optional |
| 9 | Integrate retry in start_workflow | Optional |

**Estimated scope:** ~200 lines + tests

> **Implementation order:** Complete all PR 1 tasks first, create PR, then start PR 2 tasks on a new branch after PR 1 is merged.

### Task Breakdown

#### Task 1: Add langgraph-checkpoint-sqlite Dependency

**Files:**
- Modify: `pyproject.toml:7-22`

**Step 1: Add the dependency**

```bash
uv add langgraph-checkpoint-sqlite
```

**Step 2: Verify installation**

Run: `uv run python -c "from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add langgraph-checkpoint-sqlite dependency"
```

#### Task 1.5: Update create_orchestrator_graph with interrupt_before Parameter

**Files:**
- Create: `tests/unit/test_orchestrator_interrupt.py`
- Modify: `amelia/core/orchestrator.py:280-340`

> **CRITICAL:** This task enables the interrupt mechanism. Without `interrupt_before`, the graph runs straight through `human_approval_node` without pausing in server mode.

**Step 1: Write the failing test**

Create `tests/unit/test_orchestrator_interrupt.py`:

```python
"""Tests for create_orchestrator_graph interrupt configuration."""

from unittest.mock import MagicMock, patch

import pytest

from amelia.core.orchestrator import create_orchestrator_graph


class TestCreateOrchestratorGraphInterrupt:
    """Test interrupt_before parameter handling."""

    def test_graph_accepts_interrupt_before_parameter(self):
        """create_orchestrator_graph accepts interrupt_before parameter."""
        # Should not raise
        graph = create_orchestrator_graph(interrupt_before=["human_approval_node"])
        assert graph is not None

    def test_graph_without_interrupt_before_defaults_to_none(self):
        """Graph created without interrupt_before has no interrupts configured."""
        graph = create_orchestrator_graph()
        # Graph should still be valid
        assert graph is not None

    @patch("amelia.core.orchestrator.StateGraph")
    def test_interrupt_before_passed_to_compile(self, mock_state_graph_class):
        """interrupt_before is passed through to graph.compile()."""
        mock_workflow = MagicMock()
        mock_state_graph_class.return_value = mock_workflow
        mock_workflow.compile = MagicMock(return_value=MagicMock())

        create_orchestrator_graph(
            checkpoint_saver=MagicMock(),
            interrupt_before=["human_approval_node"],
        )

        mock_workflow.compile.assert_called_once()
        call_kwargs = mock_workflow.compile.call_args[1]
        assert call_kwargs.get("interrupt_before") == ["human_approval_node"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_orchestrator_interrupt.py -v`
Expected: FAIL with "TypeError: create_orchestrator_graph() got an unexpected keyword argument 'interrupt_before'"

**Step 3: Update create_orchestrator_graph signature**

Modify `amelia/core/orchestrator.py`:

```python
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledGraph

def create_orchestrator_graph(
    checkpoint_saver: BaseCheckpointSaver | None = None,
    interrupt_before: list[str] | None = None,
) -> CompiledGraph:
    """Creates and compiles the LangGraph state machine for the orchestrator.

    Args:
        checkpoint_saver: Optional checkpoint saver for state persistence.
        interrupt_before: List of node names to interrupt before executing.
            Use ["human_approval_node"] for server-mode human-in-the-loop.

    Returns:
        Compiled StateGraph ready for execution.
    """
    workflow = StateGraph(ExecutionState)

    # Add nodes
    workflow.add_node("architect_node", call_architect_node)
    workflow.add_node("human_approval_node", human_approval_node)
    workflow.add_node("developer_node", call_developer_node)
    workflow.add_node("reviewer_node", call_reviewer_node)

    # ... existing edge definitions ...

    return workflow.compile(
        checkpointer=checkpoint_saver,
        interrupt_before=interrupt_before,
    )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_orchestrator_interrupt.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add tests/unit/test_orchestrator_interrupt.py amelia/core/orchestrator.py
git commit -m "feat(core): add interrupt_before parameter to create_orchestrator_graph"
```

#### Task 2: Add RetryConfig Model (PR 2)

**Files:**
- Create: `tests/unit/test_retry_config.py`
- Modify: `amelia/core/types.py:10-28`

**Step 1: Write the failing test**

Create `tests/unit/test_retry_config.py`:

```python
"""Tests for RetryConfig model."""

import pytest
from pydantic import ValidationError

from amelia.core.types import RetryConfig


class TestRetryConfigDefaults:
    """Test default values for RetryConfig."""

    def test_default_values(self):
        """RetryConfig has sensible defaults."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0


class TestRetryConfigValidation:
    """Test validation constraints for RetryConfig."""

    def test_max_retries_minimum(self):
        """max_retries cannot be negative."""
        with pytest.raises(ValidationError):
            RetryConfig(max_retries=-1)

    def test_max_retries_maximum(self):
        """max_retries cannot exceed 10."""
        with pytest.raises(ValidationError):
            RetryConfig(max_retries=11)

    def test_base_delay_minimum(self):
        """base_delay must be at least 0.1."""
        with pytest.raises(ValidationError):
            RetryConfig(base_delay=0.05)

    def test_base_delay_maximum(self):
        """base_delay cannot exceed 30.0."""
        with pytest.raises(ValidationError):
            RetryConfig(base_delay=31.0)

    def test_valid_custom_values(self):
        """Valid custom values are accepted."""
        config = RetryConfig(max_retries=5, base_delay=2.0)
        assert config.max_retries == 5
        assert config.base_delay == 2.0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_retry_config.py -v`
Expected: FAIL with "ImportError: cannot import name 'RetryConfig'"

**Step 3: Write minimal implementation**

Add to `amelia/core/types.py` after the existing imports:

```python
class RetryConfig(BaseModel):
    """Retry configuration for transient failures.

    Attributes:
        max_retries: Maximum number of retry attempts (0-10).
        base_delay: Base delay in seconds for exponential backoff (0.1-30.0).
    """

    max_retries: int = Field(default=3, ge=0, le=10)
    base_delay: float = Field(default=1.0, ge=0.1, le=30.0)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_retry_config.py -v`
Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add tests/unit/test_retry_config.py amelia/core/types.py
git commit -m "feat(core): add RetryConfig model with validation"
```

#### Task 3: Add RetryConfig to Profile Model (PR 2)

**Files:**
- Modify: `tests/unit/test_types.py` (add test)
- Modify: `amelia/core/types.py:10-28`

**Step 1: Write the failing test**

Add to `tests/unit/test_types.py`:

```python
class TestProfileRetryConfig:
    """Test Profile.retry field."""

    def test_profile_has_default_retry_config(self):
        """Profile has default RetryConfig."""
        profile = Profile(name="test", driver="cli:claude")
        assert profile.retry.max_retries == 3
        assert profile.retry.base_delay == 1.0

    def test_profile_accepts_custom_retry_config(self):
        """Profile accepts custom RetryConfig."""
        from amelia.core.types import RetryConfig

        custom_retry = RetryConfig(max_retries=5, base_delay=2.0)
        profile = Profile(name="test", driver="cli:claude", retry=custom_retry)
        assert profile.retry.max_retries == 5
        assert profile.retry.base_delay == 2.0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_types.py::TestProfileRetryConfig -v`
Expected: FAIL with "unexpected keyword argument 'retry'"

**Step 3: Update Profile model**

Modify `Profile` class in `amelia/core/types.py`:

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
        retry: Retry configuration for transient failures.
    """

    name: str
    driver: DriverType
    tracker: TrackerType = "none"
    strategy: StrategyType = "single"
    execution_mode: ExecutionMode = "structured"
    plan_output_dir: str = "docs/plans"
    working_dir: str | None = None
    retry: RetryConfig = Field(default_factory=RetryConfig)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_types.py::TestProfileRetryConfig -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add tests/unit/test_types.py amelia/core/types.py
git commit -m "feat(core): add retry config to Profile model"
```

#### Task 4: Update human_approval_node for Execution Mode

**Files:**
- Create: `tests/unit/test_human_approval_node.py`
- Modify: `amelia/core/orchestrator.py:50-78`

> **How interrupt_before Works:**
> With `interrupt_before=["human_approval_node"]` configured in server mode:
> 1. Graph executes `architect_node` and creates a plan
> 2. Graph pauses BEFORE entering `human_approval_node` (checkpoint saved)
> 3. `GraphInterrupt` exception is raised, caught by `_run_workflow`
> 4. User approves via REST API → `approve_workflow` calls `aupdate_state({"human_approved": True})`
> 5. Graph resumes → `human_approval_node` runs and reads `state.human_approved`
> 6. Conditional edge routes based on approval status
>
> In **CLI mode**, no interrupt occurs - the node prompts interactively via `typer.confirm`.

*[Detailed test and implementation steps included in original document]*

#### Task 5-14: [Additional Tasks]

*[All remaining tasks follow the same TDD pattern with tests, implementation, verification, and commits as detailed in the original implementation plan]*

### Final Status

**PR 1:** ✅ COMPLETED (commit a65b5c3)
- All 465 tests passing
- ~616 lines changed across 11 files
- Core interrupt/resume mechanism fully implemented
- Worktree validation and JSON serialization enhancements included

**PR 2:** Not yet started (requires PR 1 merge)
- Retry logic for transient failures
- RetryConfig model and Profile integration
- Estimated ~200 lines + tests
