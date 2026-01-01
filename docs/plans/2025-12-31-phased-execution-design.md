# Phased Execution for Developer Agent

**Date**: 2025-12-31
**Status**: Draft
**Author**: Brainstorming session

## Problem

Large tasks cause context degradation. As the Developer session accumulates tool calls, file reads, and corrections, LLM quality drops - forcing human intervention.

## Solution

Phased execution with context isolation. The Architect decomposes work into subtasks with explicit dependencies. Each subtask runs in a fresh session, using git as the handoff mechanism.

## Goals

- **Hands-off**: System runs autonomously until completion or unrecoverable failure
- **Context-fresh**: Each subtask starts with clean context (plan + current repo state)
- **Self-correcting**: Reviewer feedback triggers phase retry with fresh context
- **Fail-safe**: Halt on failure or 2 failed review attempts - never leave a mess

## Non-Goals

- Maximum parallelism (correctness over speed)
- Complex merge resolution (Architect ensures disjoint work)

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Task decomposition | Architect-driven | Architect already analyzes codebase; natural place for planning |
| Context handoff | Git + plan | Code is source of truth; plan provides strategic context |
| Execution model | Parallel where safe | Architect marks dependencies; independent subtasks run in parallel |
| Failure handling | Halt everything | Stop clean rather than build on broken foundations |
| Review timing | After each phase | Catches issues at natural sync points |
| Review rejection | Retry phase once | Fresh context + feedback; halt after 2 failures |

## Architecture

### Architect Plan Format

```python
@dataclass
class Subtask:
    id: str                      # e.g., "1", "2a", "2b"
    title: str                   # Human-readable name
    description: str             # What this subtask accomplishes
    depends_on: list[str]        # Subtask IDs that must complete first
    files_touched: list[str]     # Expected files (for conflict detection)

@dataclass
class PhasedPlanOutput:
    goal: str                    # Overall goal (existing)
    plan_markdown: str           # Full plan document (existing)
    subtasks: list[Subtask]      # Ordered list of subtasks
    phases: list[list[str]]      # Computed from dependencies
                                 # e.g., [["1"], ["2a", "2b", "2c"], ["3"]]
```

Example:
```
Subtasks:
  1.  "Create User and Post models" → depends: []      → phase 1
  2a. "Create REST API endpoints"   → depends: [1]     → phase 2
  2b. "Create CLI commands"         → depends: [1]     → phase 2
  2c. "Add model unit tests"        → depends: [1]     → phase 2
  3.  "Add integration tests"       → depends: [2a,2b] → phase 3
```

### Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Developer Node                            │
├─────────────────────────────────────────────────────────────────┤
│  for each phase in plan.phases:                                 │
│    1. Spawn subagents for all subtasks in phase (parallel)      │
│    2. Wait for all to complete                                  │
│    3. If any failed → halt everything                           │
│    4. Run Reviewer on phase changes                             │
│    5. If rejected:                                              │
│       - Retry phase once with feedback                          │
│       - If rejected again → halt                                │
│    6. Continue to next phase                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Subagent Spawning

Each subtask gets a fresh driver instance with clean context:

```python
async def run_subtask(subtask: Subtask, plan: PhasedPlanOutput) -> SubtaskResult:
    # Fresh driver instance = fresh context
    driver = DriverFactory.get_driver(profile.driver)

    prompt = f"""
    ## Overall Plan
    {plan.plan_markdown}

    ## Your Assignment
    You are executing subtask: {subtask.title}

    {subtask.description}

    The codebase reflects work from prior phases.
    Read the relevant files to understand current state.
    """

    async for message in driver.execute_agentic(prompt, cwd):
        yield message
```

### Phase Review with Retry

```python
async def run_phase_with_retry(phase: list[Subtask], plan, max_attempts=2):
    feedback = None

    for attempt in range(max_attempts):
        pre_commit = git_rev_parse("HEAD")

        if attempt > 0:
            # Reset to pre-phase state for clean retry
            git_reset(pre_commit)

        # Run all subtasks in phase (parallel)
        await run_phase_subtasks(phase, plan, feedback)

        # Review phase changes
        result = await review_phase(phase, pre_commit, plan)

        if result.approved:
            return  # Success, continue to next phase

        feedback = result.comments  # Inject into next attempt

    raise PhaseReviewFailed(phase, result)  # Halt after 2 failures
```

### State Tracking

```python
class PhaseStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class SubtaskState:
    subtask_id: str
    status: PhaseStatus
    attempt: int              # 1 or 2
    started_at: datetime | None
    completed_at: datetime | None
    error: str | None

@dataclass
class PhaseState:
    phase_index: int
    subtasks: list[SubtaskState]
    status: PhaseStatus
    pre_phase_commit: str     # For reset on retry
    review_result: ReviewResult | None
```

### Stream Events

```python
class StreamEventType(str, Enum):
    # ... existing ...
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    PHASE_RETRY = "phase_retry"
    SUBTASK_STARTED = "subtask_started"
    SUBTASK_COMPLETED = "subtask_completed"
    SUBTASK_FAILED = "subtask_failed"
```

Dashboard display:
```
Phase 1: ✓ Create models
Phase 2: ● Running (2/3 subtasks complete)
  ├── ✓ API endpoints
  ├── ✓ CLI commands
  └── ● Unit tests (running)
Phase 3: ○ Pending
```

## Implementation Plan

### Files to Modify

| File | Changes |
|------|---------|
| `amelia/agents/architect.py` | Add `PhasedPlanOutput` model, update prompt to generate subtasks with dependencies |
| `amelia/agents/developer.py` | Add `run_phased()` method alongside existing `run()`, subtask spawning logic |
| `amelia/core/state.py` | Add `PhaseState`, `SubtaskState`, extend `ExecutionState` |
| `amelia/core/types.py` | Add new `StreamEventType` variants for phase/subtask events |
| `amelia/core/orchestrator.py` | Update `call_developer_node` to detect phased plans and dispatch accordingly |

### New Module

```
amelia/core/phased_executor.py
├── run_phase()           # Execute all subtasks in a phase
├── run_subtask()         # Single subtask with fresh driver
├── review_phase()        # Review phase changes
├── run_phase_with_retry() # Retry logic wrapper
└── execute_phased_plan() # Top-level orchestrator
```

### Backward Compatibility

- If Architect returns a plan without subtasks → existing single-session behavior
- If Architect returns a plan with subtasks → phased execution
- Profile flag `enable_phased_execution: bool = True` to opt-out if needed

## Testing Strategy

1. **Unit tests**: Phase dependency resolution, retry logic, state transitions
2. **Integration tests**: Full phased execution with mock driver
3. **E2E tests**: Real multi-phase task with actual LLM calls

## Open Questions

None - all decisions made during brainstorming session.
