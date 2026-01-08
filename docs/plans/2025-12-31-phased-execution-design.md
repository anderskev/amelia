# Task-Based Execution for Developer Agent

**Status**: Ready for Implementation

## Problem

Single Developer session runs entire plan. As the session accumulates tool calls, file reads, and review feedback, context bloats and LLM quality degrades.

## Solution

Parse tasks from Architect's markdown (`### Task N:`). Spawn fresh Developer session per task. Each task goes through Review loop before next task starts. Scales to 100+ tasks.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Task source | Architect's existing markdown | No new formats; tasks already defined as `### Task N:` |
| Task execution | Sequential | Simpler; parallel added later |
| Fresh session | Per task, not per retry | Balance context freshness with review continuity |
| Review loop | Same session within task | Feedback appended; Developer retains context for fixes |
| Failure handling | Halt after max iterations | Default 5 per task; configurable via profile |
| Context passing | Full plan + pointer | "Execute Task N from plan"; future: add summaries |

## Execution Flow

```
Architect → Plan Validator (extracts task count) → Human Approval →

  For task_index in 1..total_tasks:
    │
    ├─→ Developer (fresh session)
    │     Prompt: "Execute Task {task_index} from plan at {plan_path}"
    │
    ├─→ Review
    │     if approved: commit, task_index++, continue
    │     else: loop back to Developer (same session, feedback appended)
    │           halt if max_iterations reached (default: 5)
    │
    └─→ Commit task changes

→ Done
```

**Key behaviors:**
- Fresh Developer session per task (not per retry)
- Same session continues within a task's review loop
- One commit per successfully reviewed task
- Sequential tasks for now

## State Changes

Add to `ExecutionState`:

```python
# Task execution tracking
total_tasks: int | None = None          # Parsed from plan (None = legacy single-session)
current_task_index: int = 0             # 0-indexed, increments after each task passes review
task_review_iteration: int = 0          # Resets to 0 when moving to next task
max_task_review_iterations: int = 5     # Per-task limit (configurable via profile)
```

Add to `Profile`:

```python
max_task_review_iterations: int = 5     # Override per-task review limit
```

**Backward compatibility:** If `total_tasks` is `None`, existing single-session behavior applies.

## Orchestrator Changes

### Modify `plan_validator_node`

Parse `### Task \d+:` pattern from plan markdown and set `total_tasks` in state.

### Modify `call_developer_node`

If `total_tasks` is set:
1. Create fresh driver session (clear `driver_session_id`)
2. Inject task-scoped prompt: "Execute Task {current_task_index + 1} from plan at {plan_path}"

### Modify `route_after_review`

```python
if approved:
    if current_task_index + 1 >= total_tasks:
        return END  # All tasks done
    else:
        return "next_task_node"  # Increment and loop
else:
    if task_review_iteration >= max_task_review_iterations:
        return END  # Halt on repeated failure
    else:
        return "developer_node"  # Same session, retry
```

### New `next_task_node`

1. Commit current task changes
2. Increment `current_task_index`
3. Reset `task_review_iteration` to 0
4. Clear `driver_session_id` (forces fresh session next iteration)

## Files to Modify

| File | Changes |
|------|---------|
| `amelia/core/state.py` | Add `total_tasks`, `current_task_index`, `task_review_iteration`, `max_task_review_iterations` |
| `amelia/core/types.py` | Add profile field `max_task_review_iterations` |
| `amelia/core/orchestrator.py` | Modify `plan_validator_node`, `call_developer_node`, `route_after_review`; add `next_task_node` |

## Testing Strategy

1. **Unit tests**: Task count parsing from markdown, state transitions, routing logic
2. **Integration tests**: Full task loop with mock driver (2-3 tasks, verify fresh sessions)
3. **E2E tests**: Real multi-task plan with actual LLM calls

## Future Work

- Fresh Developer session per retry attempt (GitHub issue created)
- Parallel task execution
- Context engineering (task summaries passed to downstream tasks)
