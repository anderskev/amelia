# Failure Report: TC-11

## What Failed

**Test:** Workflow status transitions correctly during resume
**Expected:**
- Initial GET shows status: "failed"
- POST resume returns 200
- Final GET shows status: "in_progress"
- The workflow should continue execution from its last checkpoint.

**Actual:**
- Initial GET shows status: "failed" ✓
- POST resume returns 200 ✓
- Final GET shows status: "failed" with failure_reason: "Cannot transition from 'in_progress' to 'in_progress'"

## Root Cause Analysis

The bug is in `amelia/server/orchestrator/service.py`:

1. `resume_workflow()` sets `workflow.workflow_status = WorkflowStatus.IN_PROGRESS` (line 883)
2. `resume_workflow()` then calls `_run_workflow_with_retry()` which calls `_run_workflow()`
3. `_run_workflow()` unconditionally calls `await self._repository.set_status(workflow_id, WorkflowStatus.IN_PROGRESS)` (line 1032)
4. The state machine (`VALID_TRANSITIONS` in `state.py:37`) doesn't allow `IN_PROGRESS -> IN_PROGRESS`
5. `set_status()` throws `InvalidStateTransitionError`
6. This exception causes the workflow to fail with the error message

## Relevant Code

**amelia/server/orchestrator/service.py:883** (in `resume_workflow`):
```python
workflow.workflow_status = WorkflowStatus.IN_PROGRESS
await self._repository.update(workflow)
```

**amelia/server/orchestrator/service.py:1032** (in `_run_workflow`):
```python
await self._repository.set_status(workflow_id, WorkflowStatus.IN_PROGRESS)
```

**amelia/server/models/state.py:37**:
```python
WorkflowStatus.IN_PROGRESS: {WorkflowStatus.BLOCKED, WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED},
```

## Suggested Fixes

**Option 1 (Recommended):** Skip the `set_status` call in `_run_workflow` if already IN_PROGRESS:
```python
workflow = await self._repository.get(workflow_id)
if workflow and workflow.workflow_status != WorkflowStatus.IN_PROGRESS:
    await self._repository.set_status(workflow_id, WorkflowStatus.IN_PROGRESS)
```

**Option 2:** Allow self-transition in state machine:
```python
WorkflowStatus.IN_PROGRESS: {WorkflowStatus.IN_PROGRESS, WorkflowStatus.BLOCKED, ...},
```

**Option 3:** Pass a flag from `resume_workflow` to indicate resumption (via config).

## Debug Session Prompt

Copy this to start a new Claude session:

---
I'm debugging a test failure in branch `docs/workflow-recovery-design`.

**Test:** TC-11 - Workflow status transitions correctly during resume
**Error:** Workflow fails with "Cannot transition from 'in_progress' to 'in_progress'"

The resume endpoint (POST /api/workflows/{id}/resume) initially succeeds with 200, but the resumed workflow immediately fails because `_run_workflow()` tries to set status to IN_PROGRESS when it's already IN_PROGRESS.

Relevant files:
- `amelia/server/orchestrator/service.py` (lines 823-913 for `resume_workflow`, lines 966-1140 for `_run_workflow`)
- `amelia/server/models/state.py` (lines 35-42 for `VALID_TRANSITIONS`)
- `amelia/server/database/repository.py` (lines 143-196 for `set_status`)

The fix should allow resumed workflows to skip the redundant status transition or allow IN_PROGRESS -> IN_PROGRESS.
---
