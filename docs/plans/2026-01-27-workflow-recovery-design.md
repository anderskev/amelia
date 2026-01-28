# Workflow Recovery After Server Restart

**Issue:** #156
**Date:** 2026-01-27
**Status:** Draft

## Overview

When the server restarts while workflows are running, those workflows become stuck in non-terminal states with no processing occurring. This design adds recovery on startup and a resume capability so users can restart failed workflows from their last checkpoint.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| IN_PROGRESS on restart | Mark as FAILED | Safest default; user decides when to resume |
| BLOCKED on restart | Restore to BLOCKED | No execution was interrupted; just re-emit the approval prompt |
| PENDING on restart | Leave unchanged | Never started; no recovery needed |
| Resume trigger | User-initiated (API + dashboard + CLI) | Gives users control over when execution resumes |
| Resume strategy | Resume from checkpoint as-is | Agent reads worktree and adapts; avoids discarding partial progress |

## Recovery on Startup

`recover_interrupted_workflows()` runs during server startup in `ServerLifecycle.startup()`. It handles two cases:

**IN_PROGRESS workflows:**
1. Query via `repository.find_by_status([WorkflowStatus.IN_PROGRESS])`
2. For each, call `repository.set_status(id, WorkflowStatus.FAILED, failure_reason="Server restarted while workflow was running")`
3. Emit `WORKFLOW_FAILED` event with `data={"recoverable": True}` so the dashboard can show a resume button
4. Log each recovered workflow at info level

**BLOCKED workflows:**
1. Query via `repository.find_by_status([WorkflowStatus.BLOCKED])`
2. These already have the correct status in the database. The problem is that no in-memory event subscribers exist yet and the dashboard has no knowledge of them.
3. Re-emit `APPROVAL_REQUIRED` event for each so newly connected dashboard clients see the pending approval
4. Log each restored workflow at info level

After processing, log a summary: "Recovery complete: {n} workflows marked failed, {m} approvals restored."

## Resume API Endpoint

`POST /api/workflows/{workflow_id}/resume`

**Validation:**
- Workflow must exist (404 if not)
- Workflow must be in FAILED status (409 if not)
- A valid LangGraph checkpoint must exist for the workflow's `thread_id` — open `AsyncSqliteSaver`, call `graph.aget_state(config)`, return 409 if checkpoint is missing or empty
- The worktree path must not have an active workflow running (409 if occupied, checked via `_active_tasks`)

**Execution:**
1. Transition status from FAILED to IN_PROGRESS (add FAILED -> IN_PROGRESS to `VALID_TRANSITIONS`)
2. Clear `failure_reason`, `consecutive_errors`, `last_error_context`; reset `completed_at` to None
3. Emit `WORKFLOW_STARTED` event with `data={"resumed": True}`
4. Create an `asyncio.Task` that calls the existing `_run_workflow` flow, which already detects checkpoints and resumes with `input_state = None`
5. Register the task in `_active_tasks` with the standard cleanup callback

**Response:** Return the workflow state as JSON.

## Dashboard Resume Button

**Visibility:**
- Workflow status is FAILED
- The workflow's last `WORKFLOW_FAILED` event has `data.recoverable === true`
- The button does not appear for workflows that failed due to non-recoverable reasons

**Behavior:**
- Placed alongside existing action buttons (approve, reject, cancel) in the workflow detail view
- Label: "Resume" with a retry icon
- On click: `POST /api/workflows/{id}/resume`
- On success: UI updates via WebSocket `WORKFLOW_STARTED` event
- On error (409): toast with the error message

**Store changes:**
- Add `resumeWorkflow(id)` action to the Zustand workflow store, mirroring the existing `cancelWorkflow(id)` pattern
- WebSocket listener already handles status updates, so the UI reacts automatically

## CLI Resume Command

```
amelia resume WORKFLOW_ID [--profile PROFILE]
```

- Calls `POST /api/workflows/{workflow_id}/resume` on the running server
- On success: prints "Workflow {id} resumed"
- On 404: prints "Workflow not found"
- On 409: prints the error message (no checkpoint, worktree occupied, wrong status)
- On connection error: prints "Server not running"

Follows the same pattern as `amelia cancel`.

## Testing

### Unit Tests

| Test | Validates |
|------|-----------|
| `test_recover_in_progress_marks_failed` | IN_PROGRESS workflow marked FAILED with correct reason and `recoverable: True` |
| `test_recover_blocked_restores_approval` | BLOCKED workflow stays BLOCKED, APPROVAL_REQUIRED event re-emitted |
| `test_recover_pending_unchanged` | PENDING workflows left untouched |
| `test_recover_no_active_workflows` | No non-terminal workflows, clean log |
| `test_resume_validates_failed_status` | Resuming non-FAILED workflow raises InvalidStateError |
| `test_resume_validates_checkpoint_exists` | Resuming without checkpoint returns error |
| `test_resume_validates_worktree_available` | Resuming with occupied worktree raises error |
| `test_resume_transitions_to_in_progress` | Successful resume clears failure fields, sets IN_PROGRESS |
| `test_resume_emits_started_event` | WORKFLOW_STARTED emitted with `resumed: True` |
| `test_valid_transitions_includes_failed_to_in_progress` | State machine allows FAILED -> IN_PROGRESS |

### Integration Tests

| Test | Validates |
|------|-----------|
| `test_recovery_on_startup` | Pre-seeded interrupted workflows recovered correctly on server start |
| `test_resume_endpoint` | POST to resume endpoint with valid checkpoint triggers workflow resumption |

Integration tests mock only the external boundary (LLM HTTP calls), not internal components.

## Files Changed

| File | Change |
|------|--------|
| `amelia/server/orchestrator/service.py` | Implement `recover_interrupted_workflows()`, add `resume_workflow()` method |
| `amelia/server/models/state.py` | Add FAILED -> IN_PROGRESS to `VALID_TRANSITIONS` |
| `amelia/server/routes/workflows.py` | Add `POST /api/workflows/{id}/resume` endpoint |
| `amelia/cli/commands/resume.py` | New CLI command |
| `dashboard/src/stores/workflow-store.ts` | Add `resumeWorkflow()` action |
| `dashboard/src/components/workflow-detail.tsx` | Add resume button (conditional on `recoverable`) |
| `tests/unit/test_workflow_recovery.py` | Unit tests for recovery and resume |
| `tests/integration/test_workflow_recovery.py` | Integration tests |
