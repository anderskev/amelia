# Pipeline Foundation Design

**Goal:** Establish the pipeline abstraction layer that enables multiple workflow types in Amelia.

**Scope:** Phase 1 - create the foundational `amelia/pipelines/` structure and refactor the existing orchestrator into the first two pipelines (Implementation and Review).

**Parent:** See [Multiple Workflow Pipelines Design (#260)](./2026-01-10-multiple-workflow-pipelines-design.md) for full context and future phases.

---

## Overview

This phase introduces four key abstractions:

1. **PipelineMetadata** - Immutable dataclass describing a pipeline
2. **Pipeline Protocol** - Interface that all workflow types implement
3. **Base State** - Common fields shared across all pipelines (self-describing)
4. **Registry** - Simple dict mapping pipeline names to implementations

The existing orchestrator becomes two pipelines:
- `ImplementationPipeline` - Full Architect → Developer ↔ Reviewer flow
- `ReviewPipeline` - Review-fix cycle for `amelia review --local`

---

## Pipeline Metadata

Metadata is separated from the protocol for cleaner typing:

```python
# amelia/pipelines/base.py
from dataclasses import dataclass

@dataclass(frozen=True)
class PipelineMetadata:
    """Immutable metadata describing a pipeline."""
    name: str           # "implementation"
    display_name: str   # "Implementation"
    description: str
```

---

## Pipeline Protocol

Each pipeline implements a common protocol:

```python
# amelia/pipelines/base.py
from typing import Protocol, TypeVar
from langgraph.graph.state import CompiledStateGraph

StateT = TypeVar("StateT", bound="BasePipelineState")

class Pipeline(Protocol[StateT]):
    """Protocol that all pipelines must implement."""

    @property
    def metadata(self) -> PipelineMetadata: ...

    def create_graph(
        self,
        checkpointer: BaseCheckpointSaver | None = None,
    ) -> CompiledStateGraph: ...

    def get_initial_state(self, **kwargs) -> StateT: ...

    def get_state_class(self) -> type[StateT]: ...
```

**Design decisions:**
- Metadata is a property returning `PipelineMetadata`, not class attributes
- `interrupt_before` is handled internally by each pipeline in `create_graph()`
- Fresh instances on each `get_pipeline()` call guarantee isolation

---

## Pipeline Registry

The registry routes to pipelines by name:

```python
# amelia/pipelines/registry.py
PIPELINES: dict[str, type[Pipeline]] = {
    "implementation": ImplementationPipeline,
    "review": ReviewPipeline,
}

def get_pipeline(name: str) -> Pipeline:
    if name not in PIPELINES:
        raise ValueError(f"Unknown pipeline: {name}")
    return PIPELINES[name]()

def list_pipelines() -> list[dict[str, str]]:
    """List available pipelines for dashboard."""
    return [
        {
            "name": p.metadata.name,
            "display_name": p.metadata.display_name,
            "description": p.metadata.description,
        }
        for p in (cls() for cls in PIPELINES.values())
    ]
```

**Design decisions:**
- Instantiate on every `get_pipeline()` call (stateless factories, cheap)
- No singleton caching (fresh instances guarantee isolation)
- No protocol validation at registration (structural typing validates at usage)

---

## HistoryEntry

Structured history entry for observability:

```python
# amelia/pipelines/base.py
@dataclass(frozen=True)
class HistoryEntry:
    """Structured history entry for agent actions."""
    timestamp: datetime
    agent: str      # "architect", "developer", "reviewer"
    message: str
```

---

## Base State

Base state contains fields common to all workflows. State is **self-describing** for serialization:

```python
# amelia/pipelines/base.py
class BasePipelineState(BaseModel):
    """Common state for all pipelines."""
    model_config = ConfigDict(frozen=True)

    # Identity (immutable, self-describing for serialization)
    workflow_id: str
    pipeline_type: str
    profile_id: str
    created_at: datetime

    # Lifecycle (replaces agentic_status)
    status: Literal["pending", "running", "paused", "completed", "failed"]

    # Observability (append-only via reducer)
    history: Annotated[list[HistoryEntry], add] = Field(default_factory=list)

    # Human interaction
    pending_user_input: bool = False
    user_message: str | None = None

    # Agentic execution
    driver_session_id: str | None = None
    final_response: str | None = None
    error: str | None = None
```

**Design decisions:**

| Field | Decision | Rationale |
|-------|----------|-----------|
| `workflow_id` | In state | Self-describing for serialization, type-safe access in nodes |
| `created_at` | In state | Immutable identity metadata |
| `updated_at` | Database only | Mutable on every change, error-prone in state |
| `status` | Replaces `agentic_status` | Simpler: pending/running/paused/completed/failed |
| `tool_calls` | **Removed** | Event-based only; never used for routing decisions |
| `tool_results` | **Removed** | Event-based only; dashboard queries events endpoint |

**Benefits of removing tool_calls/tool_results:**
- Smaller state checkpoints (no unbounded accumulation)
- Single source of truth (events are authoritative)
- Cleaner state model (state holds workflow data, events hold execution history)

---

## Implementation Pipeline

The current orchestrator becomes the Implementation pipeline:

```python
# amelia/pipelines/implementation/pipeline.py

class ImplementationPipeline:
    """Pipeline for implementing code from issues/designs."""

    @property
    def metadata(self) -> PipelineMetadata:
        return PipelineMetadata(
            name="implementation",
            display_name="Implementation",
            description="Build features and fix bugs with Architect → Developer ↔ Reviewer flow",
        )

    def get_state_class(self) -> type[ImplementationState]:
        return ImplementationState

    def create_graph(
        self,
        checkpointer: BaseCheckpointSaver | None = None,
    ) -> CompiledStateGraph:
        return create_implementation_graph(checkpointer)

    def get_initial_state(
        self,
        workflow_id: str,
        profile_id: str,
        issue: Issue | None = None,
        design: Design | None = None,
        **kwargs,
    ) -> ImplementationState:
        return ImplementationState(
            workflow_id=workflow_id,
            profile_id=profile_id,
            created_at=datetime.now(UTC),
            status="pending",
            issue=issue,
            design=design,
            **kwargs,
        )
```

Implementation state extends the base with pipeline-specific fields:

```python
# amelia/pipelines/implementation/state.py
class ImplementationState(BasePipelineState):
    """State for implementation pipeline."""
    pipeline_type: Literal["implementation"] = "implementation"

    # Domain data (from planning phase)
    issue: Issue | None = None
    design: Design | None = None
    goal: str | None = None
    base_commit: str | None = None
    plan_markdown: str | None = None
    raw_architect_output: str | None = None
    plan_path: Path | None = None
    key_files: list[str] = Field(default_factory=list)

    # Human approval (plan review)
    human_approved: bool | None = None
    human_feedback: str | None = None

    # Code review tracking
    last_review: ReviewResult | None = None
    code_changes_for_review: str | None = None

    # Review iteration tracking
    review_iteration: int = 0

    # Task-based execution (multi-task plans)
    total_tasks: int | None = None
    current_task_index: int = 0
    task_review_iteration: int = 0

    # Structured review workflow
    structured_review: StructuredReviewResult | None = None
    evaluation_result: EvaluationResult | None = None
    approved_items: list[int] = Field(default_factory=list)
    auto_approve: bool = False
    review_pass: int = 0
    max_review_passes: int = 3
```

---

## Review Pipeline

The review workflow becomes a separate pipeline:

```python
# amelia/pipelines/review/pipeline.py

class ReviewPipeline:
    """Pipeline for review-fix cycles on existing changes."""

    @property
    def metadata(self) -> PipelineMetadata:
        return PipelineMetadata(
            name="review",
            display_name="Review",
            description="Review and fix code changes with Reviewer → Evaluator → Developer cycle",
        )

    def create_graph(
        self,
        checkpointer: BaseCheckpointSaver | None = None,
    ) -> CompiledStateGraph:
        return create_review_graph(checkpointer)

    # Uses ImplementationState (subset of fields)
    def get_state_class(self) -> type[ImplementationState]:
        return ImplementationState
```

**Design decisions:**
- Separate pipeline class (different graph topology, entry point, routing)
- Shares `ImplementationState` (review uses subset of same fields)
- Shares node functions (`call_reviewer_node`, `call_developer_node`, etc.)
- Service uses `workflow_type` field: `get_pipeline(workflow_type)`

---

## Shared Utilities

Helper functions are split by scope:

```python
# amelia/pipelines/base.py (LangGraph infrastructure)
def extract_config_params(config: RunnableConfig) -> tuple[EventBus | None, str, Profile]:
    """Extract event_bus, workflow_id, profile from config.configurable."""
    ...

async def save_token_usage(driver, workflow_id: str, agent: str, repository) -> None:
    """Persist token metrics to repository after agent execution."""
    ...
```

```python
# amelia/core/extraction.py (generic LLM utility)
async def extract_structured[T: BaseModel](
    prompt: str,
    schema: type[T],
    model: str,
    driver_type: str,
) -> T:
    """Extract structured output from text using direct model call."""
    ...
```

---

## Migration Steps

1. Create `amelia/pipelines/` directory structure
2. Create `amelia/core/extraction.py` with `extract_structured()` function
3. Define `PipelineMetadata`, `HistoryEntry`, `BasePipelineState`, `Pipeline` in `base.py`
4. Add `extract_config_params()` and `save_token_usage()` to `base.py`
5. Create `ImplementationState` extending `BasePipelineState`
6. Create `ImplementationPipeline` with graph, nodes, routing, utils
7. Create `ReviewPipeline` with separate graph
8. Create registry with both pipelines
9. Update all callers (service, CLI, tests) to new locations
10. Delete `amelia/core/orchestrator.py` and `amelia/core/state.py`

**Clean break:** No backward-compatibility wrapper. Update all imports directly.

---

## File Structure

```
amelia/
├── core/
│   └── extraction.py              # extract_structured() - generic LLM helper
│
├── pipelines/
│   ├── __init__.py                # Re-exports: Pipeline, BasePipelineState, get_pipeline
│   ├── base.py                    # PipelineMetadata, HistoryEntry, BasePipelineState
│   │                              # Pipeline protocol, extract_config_params, save_token_usage
│   ├── registry.py                # PIPELINES dict, get_pipeline(), list_pipelines()
│   │
│   ├── implementation/
│   │   ├── __init__.py            # Re-exports
│   │   ├── pipeline.py            # ImplementationPipeline class
│   │   ├── state.py               # ImplementationState
│   │   ├── graph.py               # create_implementation_graph()
│   │   ├── nodes.py               # Node functions (call_architect_node, etc.)
│   │   ├── routing.py             # Route functions (route_after_review, etc.)
│   │   └── utils.py               # Helpers (extract_task_count, extract_task_section)
│   │
│   └── review/
│       ├── __init__.py            # Re-exports
│       ├── pipeline.py            # ReviewPipeline class
│       └── graph.py               # create_review_graph()
```

---

## Callers to Update

| File | Change |
|------|--------|
| `amelia/__init__.py` | Import from `amelia.pipelines.implementation` |
| `amelia/server/orchestrator/service.py` | Import from `amelia.pipelines` |
| `tests/unit/test_orchestrator_graph.py` | Import from new location |
| `tests/integration/conftest.py` | Import from new location |
| `tests/integration/test_*.py` | Update patch strings |

---

## Success Criteria

1. **Protocol defined** - `Pipeline` protocol and `BasePipelineState` exist in `amelia/pipelines/base.py`
2. **Metadata separated** - `PipelineMetadata` dataclass for clean typing
3. **Registry works** - `get_pipeline("implementation")` and `get_pipeline("review")` return valid pipelines
4. **State hierarchy** - `ImplementationState` extends `BasePipelineState` with all current fields
5. **State simplified** - No `tool_calls`/`tool_results` in state (event-based)
6. **Graphs relocated** - Implementation and review graphs in `pipelines/` package
7. **Clean break** - No backward-compatibility wrappers; old files deleted
8. **CLI unchanged** - `amelia start`, `amelia review`, and server commands work as before

**Testing (TDD):**
- Integration tests cover full orchestrator flow, mocking only external LLM API boundary
- Unit tests for registry functions, state validation, protocol compliance
- Dashboard tests updated to query events endpoint for tool history

---

## Non-Goals (Phase 1)

- Dashboard UI changes for pipeline selection
- New agents or tools
- Handoff endpoints
- Additional pipeline types beyond Implementation and Review
