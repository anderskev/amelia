# LangGraph Execution Bridge Design

> **Status:** Approved
> **Date:** 2025-12-06
> **Author:** Claude + Human collaboration

## Overview

This design connects the server layer (FastAPI, SQLite, REST endpoints) to the existing core LangGraph orchestrator, implementing the missing `_run_workflow()` method in `OrchestratorService`.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Server Layer                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ REST API     │───▶│ Orchestrator │───▶│ EventBus     │──▶ WS │
│  │ (FastAPI)    │    │ Service      │    │              │       │
│  └──────────────┘    └──────┬───────┘    └──────────────┘       │
│                             │                                    │
│                    ┌────────▼────────┐                          │
│                    │ ExecutionBridge │  ◀── NEW                 │
│                    └────────┬────────┘                          │
│                             │                                    │
│                    ┌────────▼────────┐                          │
│                    │ SQLiteCheckpoint│  ◀── NEW                 │
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

**New Components:**
- `ExecutionBridge` - Invokes LangGraph, handles interrupts, streams events
- `SQLiteCheckpointer` - Persists graph state for interrupt/resume
- State composition - `ServerExecutionState.execution_state: ExecutionState`

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Human approval | Interrupt-based (`interrupt_before`) | LangGraph native, keeps core clean |
| Checkpoint persistence | SQLite now, PostgreSQL later | Leverage existing infrastructure |
| State model | Composition (wrap `ExecutionState`) | Preserves architectural boundary |
| Event streaming | Map LangGraph → WorkflowEvent | Stable dashboard interface |
| Error handling | Auto-retry with backoff | Resilience for transient failures |
| Retry config | Per-profile in YAML | Different drivers have different failure modes |

## State Model

`ServerExecutionState` wraps `ExecutionState` via composition:

```python
class ServerExecutionState(BaseModel):
    # Server metadata
    id: str
    issue_id: str
    worktree_path: str
    worktree_name: str  # Derived from path
    workflow_status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: datetime
    completed_at: datetime | None = None
    current_stage: str = "initializing"
    failure_reason: str | None = None

    # Core orchestration state - always present
    execution_state: ExecutionState
```

**Initialization:** All fields populated at workflow creation. Issue fetched immediately, `worktree_name` derived from path. No nullable fields except `completed_at` and `failure_reason`.

## SQLite Checkpointer

Implements LangGraph's `BaseCheckpointSaver` interface:

```python
class SQLiteCheckpointer(BaseCheckpointSaver):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def aget(self, config: RunnableConfig) -> Checkpoint | None:
        """Retrieve checkpoint for thread_id."""

    async def aput(self, config: RunnableConfig, checkpoint: Checkpoint) -> None:
        """Store checkpoint for thread_id."""

    async def alist(self, config: RunnableConfig) -> list[CheckpointTuple]:
        """List checkpoint history for thread_id."""
```

**Schema:**

```sql
CREATE TABLE workflow_checkpoints (
    thread_id TEXT PRIMARY KEY,  -- workflow_id
    checkpoint BLOB NOT NULL,    -- serialized checkpoint
    metadata JSON,               -- optional metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Thread ID:** Maps to `workflow_id` for checkpoint isolation.

## Execution Bridge

The `_run_workflow()` implementation:

```python
async def _run_workflow(
    self,
    workflow_id: str,
    state: ServerExecutionState,
) -> None:
    """Execute workflow via LangGraph with interrupt support."""

    # 1. Create graph with checkpointer
    checkpointer = SQLiteCheckpointer(self._db)
    graph = create_orchestrator_graph(checkpoint_saver=checkpointer)

    # 2. Configure for this workflow
    config = {"configurable": {"thread_id": workflow_id}}

    # 3. Stream execution with event emission
    try:
        async for event in graph.astream_events(
            state.execution_state,
            config=config,
            interrupt_before=["human_approval_node"],
        ):
            await self._handle_graph_event(workflow_id, event)

    except GraphInterrupt:
        # Human approval required - checkpoint saved automatically
        await self._emit_approval_required(workflow_id, state)
        return  # Execution pauses here

    except Exception as e:
        await self._handle_execution_error(workflow_id, e)
        raise
```

## Human Approval Flow

```
1. Graph reaches human_approval_node
   └─▶ GraphInterrupt raised (checkpoint saved)
   └─▶ _run_workflow() catches, emits approval_required event
   └─▶ Workflow status → BLOCKED

2. Dashboard shows approval UI
   └─▶ User clicks Approve/Reject

3. REST API called
   └─▶ POST /workflows/{id}/approve  (or /reject)
   └─▶ OrchestratorService.approve_workflow()

4. Resume from checkpoint
   └─▶ Update execution_state.human_approved = True/False
   └─▶ graph.ainvoke(None, config)  # Resume with updated state
   └─▶ Graph continues to developer_node (or END if rejected)
```

## Event Streaming

Map LangGraph events to WorkflowEvents:

```python
async def _handle_graph_event(
    self,
    workflow_id: str,
    event: dict,
) -> None:
    """Translate LangGraph events to WorkflowEvents and emit."""

    event_type = event.get("event")

    if event_type == "on_chain_start":
        node_name = event.get("name")
        if node_name in STAGE_NODES:
            await self._emit(workflow_id, "stage_changed", {"stage": node_name})

    elif event_type == "on_chain_end":
        node_name = event.get("name")
        if node_name in STAGE_NODES:
            await self._emit(workflow_id, "stage_completed", {"stage": node_name, "output": event.get("data")})

    elif event_type == "on_llm_stream" and self._verbose_mode(workflow_id):
        await self._emit(workflow_id, "llm_token", {"token": event.get("data", {}).get("chunk")})
```

**Event mapping:**

| LangGraph Event | WorkflowEvent | When |
|-----------------|---------------|------|
| `on_chain_start` | `stage_changed` | Node begins |
| `on_chain_end` | `stage_completed` | Node finishes |
| `on_llm_stream` | `llm_token` | Verbose mode only |
| `GraphInterrupt` | `approval_required` | Before approval node |

## Error Handling & Retry

```python
async def _run_workflow_with_retry(
    self,
    workflow_id: str,
    state: ServerExecutionState,
) -> None:
    """Execute workflow with automatic retry for transient failures."""

    retry_config = state.execution_state.profile.retry_config
    attempt = 0

    while attempt <= retry_config.max_retries:
        try:
            await self._run_workflow(workflow_id, state)
            return

        except TransientError as e:
            attempt += 1
            if attempt > retry_config.max_retries:
                await self._mark_failed(workflow_id, e)
                raise

            delay = retry_config.base_delay * (2 ** (attempt - 1))
            await asyncio.sleep(delay)

        except PermanentError as e:
            await self._mark_failed(workflow_id, e)
            raise
```

**Error classification:**

| Error Type | Examples | Behavior |
|------------|----------|----------|
| Transient | Network timeout, rate limit, LLM overload | Retry with backoff |
| Permanent | Invalid issue ID, auth failure, validation | Fail immediately |

## Configuration Schema

```yaml
profiles:
  work:
    driver: api:openai
    tracker: jira
    retry:
      max_retries: 3
      base_delay: 1.0
      max_delay: 30.0
      retryable_errors:
        - network_timeout
        - rate_limit
        - llm_overload

  enterprise:
    driver: cli:claude
    tracker: github
    retry:
      max_retries: 5
      base_delay: 2.0
      max_delay: 60.0
      retryable_errors:
        - network_timeout
        - rate_limit
        - llm_overload
        - cli_timeout
```

**Model addition:**

```python
class RetryConfig(BaseModel):
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    retryable_errors: list[str] = ["network_timeout", "rate_limit", "llm_overload"]

class Profile(BaseModel):
    name: str
    driver: str
    tracker: str
    retry: RetryConfig = RetryConfig()
```

## Testing Strategy

**Test structure:**

```
tests/
├── unit/
│   ├── server/
│   │   ├── database/
│   │   │   └── test_checkpointer.py     # SQLiteCheckpointer isolation
│   │   └── orchestrator/
│   │       ├── test_execution_bridge.py # _run_workflow with mocked graph
│   │       ├── test_event_mapping.py    # LangGraph → WorkflowEvent
│   │       └── test_retry_logic.py      # Backoff, error classification
│   └── core/
│       └── test_retry_config.py         # RetryConfig validation
├── integration/
│   ├── test_approval_flow.py            # Interrupt → approve → resume
│   ├── test_checkpoint_recovery.py      # Restart mid-workflow
│   └── test_concurrent_workflows.py     # Multiple workflows isolated
```

**TDD approach:**

| Component | Test First | Then Implement |
|-----------|------------|----------------|
| `SQLiteCheckpointer` | `aget`/`aput` round-trip | Schema + methods |
| `RetryConfig` | Validation, defaults | Pydantic model |
| `_run_workflow` | Mock graph, verify events | Execution bridge |
| Approval flow | Mock interrupt, verify resume | Full cycle |
| Error handling | Error classification | Retry wrapper |

## Implementation Order

1. **RetryConfig model** - Add to `amelia/core/types.py`
2. **SQLiteCheckpointer** - New file `amelia/server/database/checkpointer.py`
3. **State model update** - Add `execution_state` to `ServerExecutionState`
4. **Event mapping** - Add `_handle_graph_event()` to service
5. **Execution bridge** - Implement `_run_workflow()`
6. **Retry wrapper** - Add `_run_workflow_with_retry()`
7. **Approval flow** - Update `approve_workflow()` / `reject_workflow()`
8. **Integration tests** - Full workflow cycles

## Future: PostgreSQL Migration

The `SQLiteCheckpointer` interface matches `langgraph-checkpoint-postgres`. Migration path:

1. Add `langgraph-checkpoint-postgres` dependency
2. Add `checkpoint_backend` config option
3. Factory function selects implementation based on config
4. No changes to `OrchestratorService` - same interface
