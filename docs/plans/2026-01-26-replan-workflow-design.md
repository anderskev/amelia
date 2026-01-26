# Replan Workflow

Allow re-generating a plan for a workflow that has already been planned and is awaiting approval.

## Background

Non-blocking concurrent plan generation was implemented in PR #269. Multiple workflows can have their Architect phases running simultaneously. What remains is the ability to regenerate a plan for a workflow that has already been planned.

**Use case:** After reviewing a plan, the user realizes the approach is wrong — the issue description was updated, the codebase changed, or they want a different approach — and wants to regenerate with updated context.

## Design Decisions

- **Scope:** Replan works for `blocked` workflows only (plan generated, awaiting approval). Pending workflows can already use `set_workflow_plan` for external plans.
- **Plan history:** Overwrite only, no versioning. The event log provides an audit trail. Versioning can be added later if needed.
- **Checkpoint handling:** Delete the old LangGraph checkpoint and run fresh. The old checkpoint is stale — that's the whole point of replanning.
- **Dashboard placement:** "Replan" button alongside Approve/Reject buttons for blocked workflows.

## State Machine Change

Add `PLANNING` to the valid transitions from `BLOCKED`:

```python
WorkflowStatus.BLOCKED: {WorkflowStatus.PLANNING, WorkflowStatus.IN_PROGRESS, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED},
```

This is the only new transition. The rest of the flow reuses existing transitions: `PLANNING → BLOCKED` (new plan ready) and `PLANNING → FAILED`/`CANCELLED`.

## API Endpoint

`POST /api/workflows/{id}/replan`

- No request body (reuses the same issue/profile as the original workflow)
- Returns `200` with `{ "workflow_id": str, "status": "planning" }`
- `404`: workflow not found
- `422`: workflow not in `blocked` status
- `409`: planning task already running

## Orchestrator Method

New method `OrchestratorService.replan_workflow(workflow_id: str)`:

1. Fetch workflow from repository, validate it's in `blocked` status
2. Cancel any existing planning task for this workflow ID (defensive check)
3. Delete the existing LangGraph checkpoint for this thread ID
4. Clear plan-related fields from `execution_state` (`plan_markdown`, `plan_path`, `goal`, `key_files`, `total_tasks`, `planned_at`)
5. Transition workflow to `PLANNING` status, set `current_stage = "architect"`
6. Spawn `_run_planning_task` in background (reuses existing method)
7. Emit event indicating replanning started

## Checkpoint Deletion

New private method `OrchestratorService._delete_checkpoint(workflow_id: str)` to clear the stale LangGraph checkpoint. Opens an `AsyncSqliteSaver` connection and deletes all checkpoint data for the given thread ID.

## Dashboard Changes

Add a "Replan" button alongside the existing Approve/Reject buttons for blocked workflows:

- Calls `POST /api/workflows/{id}/replan`
- On success, the workflow transitions to `planning` status — the dashboard already handles this with the `PlanningIndicator` (elapsed time + cancel button)
- No new WebSocket event types needed

## Testing

### Integration Tests (Critical Path)

The integration tests are the most critical part of this feature. They validate the full replan lifecycle with real components.

**API driver e2e** (`tests/integration/`): Full replan flow with real `OrchestratorService`, real `Architect`, real LangGraph graph. Only mock the HTTP boundary (pydantic-ai's HTTP calls to the LLM API). Workflow goes `PENDING → PLANNING → BLOCKED → (replan) → PLANNING → BLOCKED`, verifying the plan is regenerated and the checkpoint is fresh.

**CLI driver e2e** (`tests/integration/`): Same flow but with the CLI driver. Mock at the subprocess boundary (the CLI tool invocation) instead of HTTP.

Both integration tests verify:
1. State transitions happen correctly through the full cycle
2. Old checkpoint is deleted and new one is created
3. Plan fields are cleared and repopulated
4. Events are emitted correctly
5. The workflow can still be approved after replanning

### Unit Tests

- `replan_workflow` method: happy path, wrong status rejection, checkpoint deletion, planning task cancellation
- Route handler: status codes for success, not found, wrong status, conflict
- State machine: `BLOCKED → PLANNING` transition validity
- Dashboard: Replan button renders for blocked workflows, hidden for other statuses, calls correct API endpoint

## Files Changed

| File | Change |
|------|--------|
| `amelia/server/models/state.py` | Add `PLANNING` to `BLOCKED` transitions |
| `amelia/server/orchestrator/service.py` | Add `replan_workflow()` and `_delete_checkpoint()` |
| `amelia/server/routes/workflows.py` | Add `POST /{id}/replan` route |
| Dashboard workflow detail component | Add "Replan" button for blocked workflows |
| `tests/integration/` | API driver and CLI driver e2e replan tests |
| `tests/unit/` | Unit tests for orchestrator, routes, state machine |
| `dashboard/` test files | Replan button tests |
