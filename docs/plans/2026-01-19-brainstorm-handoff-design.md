# Brainstorm Handoff to Implementation

## Problem

The brainstorm handoff feature returns a fake workflow ID without creating an actual workflow. When the frontend navigates to `/workflows/{id}`, the workflow doesn't exist.

Secondary issue: "View Document" button returns 404 because `GET /api/files/{path}` endpoint doesn't exist.

## Solution

### Backend: Create Real Workflow on Handoff

**Service changes** (`amelia/server/services/brainstorm.py`):

Update `handoff_to_implementation` to accept orchestrator and worktree_path:

```python
async def handoff_to_implementation(
    self,
    session_id: str,
    artifact_path: str,
    issue_title: str | None = None,
    issue_description: str | None = None,
    orchestrator: OrchestratorService,
    worktree_path: str,
) -> dict[str, str]:
```

Logic:
1. Validate session and artifact exist (existing)
2. Load settings from `worktree_path` to get active profile
3. Check tracker type:
   - **noop**: Call `orchestrator.queue_workflow()` with `task_title=issue_title`
   - **jira/github**: Raise `NotImplementedError` (stub for now)
4. Update session status to "completed"
5. Return real `workflow_id` from orchestrator

**Route changes** (`amelia/server/routes/brainstorm.py`):

Add dependencies to handoff endpoint:
- `orchestrator: OrchestratorService = Depends(get_orchestrator)`
- `cwd: str = Depends(get_cwd)`

Pass both to service method.

### Backend: Add GET File Endpoint

**New endpoint** (`amelia/server/routes/files.py`):

```python
@router.get("/{file_path:path}")
async def get_file(file_path: str, config: ServerConfig = Depends(get_config)) -> Response:
```

Reuse existing validation logic from `POST /api/files/read`:
- Validate absolute path
- Check path is within working_dir
- Return file content with appropriate content-type

### Error Handling

| Error | HTTP Status | Behavior |
|-------|-------------|----------|
| `InvalidWorktreeError` | 400 | working_dir not a git repo |
| `ValueError` | 400 | Invalid settings or profile |
| `ConcurrencyLimitError` | 503 | At max workflow capacity |
| `WorkflowConflictError` | N/A | Use `queue_workflow()` to avoid this |
| Non-noop tracker | 501 | "Handoff with {tracker} tracker not yet supported" |

**Session state on failure:** Keep session "active" so user can retry.

### Frontend

No changes needed. Existing code:
- Calls `POST /sessions/{id}/handoff` with `artifact_path` and `issue_title`
- Navigates to `/workflows/{workflow_id}` on success
- Once backend returns real workflow_id, navigation works

## Files to Modify

1. `amelia/server/services/brainstorm.py` - Update `handoff_to_implementation`
2. `amelia/server/routes/brainstorm.py` - Add orchestrator/cwd dependencies
3. `amelia/server/routes/files.py` - Add GET endpoint
4. `tests/unit/server/services/test_brainstorm_service.py` - Update tests
5. `tests/unit/server/routes/test_files.py` - Add GET endpoint tests

## Out of Scope

- Jira/GitHub tracker support (stubbed with 501)
- Auto-creating issues in external trackers
- Passing design document content to Architect (future enhancement)
