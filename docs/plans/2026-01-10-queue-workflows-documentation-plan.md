# Queue Workflows Documentation Plan

This document outlines all documentation updates required following the implementation of PR #264 (Queue Workflows and Batch Execution).

## Background

PR #264 introduced a complete workflow queuing and batch execution system including:
- New CLI flags (`--queue`, `--plan`) and command (`amelia run`)
- New API endpoints for batch operations
- Dashboard UI for queue management
- New data model fields (`planned_at`, `created_at`)

The public documentation has not been updated to reflect these changes.

## Updates Required

### 1. Guide: Usage (`/docs/site/guide/usage.md`)

**Priority: P0 - Critical**

Add new "Queue Workflows" section documenting:

#### CLI Commands

```bash
# Queue workflow without starting
amelia start ISSUE-123 --queue

# Queue workflow and generate plan for review
amelia start ISSUE-123 --queue --plan

# Start a specific pending workflow
amelia run <workflow-id>

# Start all pending workflows
amelia run --all

# Start pending workflows for specific worktree
amelia run --all --worktree /path/to/repo
```

#### Workflow Queue Lifecycle

1. **Queue** - Workflow created in `pending` state, not executing
2. **Plan (optional)** - Architect runs, `planned_at` set when complete
3. **Start** - Workflow transitions to `in_progress` and begins execution
4. **Complete** - Normal completion flow

#### Use Cases

- Review Architect plans before committing to execution
- Batch multiple issues for later processing
- Queue work during review of earlier workflows

### 2. Guide: Usage - REST API Section

**Priority: P0 - Critical**

Update API documentation with:

#### Modified Endpoint: `POST /api/workflows`

New request body fields:
```json
{
  "issue_id": "ISSUE-123",
  "worktree_path": "/path/to/repo",
  "profile": "default",
  "start": true,       // NEW: false to queue without starting
  "plan_now": false    // NEW: true to run Architect when queuing
}
```

Behavior matrix:
| `start` | `plan_now` | Result |
|---------|------------|--------|
| `true` (default) | ignored | Immediate execution |
| `false` | `false` | Queue only |
| `false` | `true` | Queue and plan |

#### New Endpoint: `POST /api/workflows/start-batch`

Request:
```json
{
  "workflow_ids": ["uuid-1", "uuid-2"],  // Optional: specific IDs or null for all
  "worktree_path": "/path/to/repo"        // Optional: filter by worktree
}
```

Response:
```json
{
  "started": ["uuid-1", "uuid-2"],
  "errors": {
    "uuid-3": "Workflow not found"
  }
}
```

#### New Endpoint: `POST /api/workflows/{id}/start`

Starts a single pending workflow. Returns 409 if workflow not in pending state.

### 3. Guide: Troubleshooting (`/docs/site/guide/troubleshooting.md`)

**Priority: P1 - High**

#### Add Queue-Specific Troubleshooting Section

**"Workflow stuck in pending state"**
- Check if another workflow is active on the same worktree
- Verify concurrency limit not reached
- Use `amelia run <id>` to manually start

**"Cannot start queued workflow"**
- Only one active workflow per worktree allowed
- Check for in_progress or blocked workflows on same worktree
- Cancel or complete existing workflow first

**"Plan not generating"**
- `plan_now=true` runs Architect in background
- Check server logs for planning errors
- Workflow remains in pending state even if planning fails

#### Update State Transition Diagram

Current states mentioned are outdated. Update to include:
- `pending` state with `planned_at` marker
- Transition from `pending` → `in_progress` (start)
- Transition from `pending` → `failed` (startup errors)

### 4. Architecture: Data Model (`/docs/site/architecture/data-model.md`)

**Priority: P1 - High**

#### Update ExecutionState/WorkflowState

Add new fields:
```python
class WorkflowState:
    # ... existing fields ...
    created_at: datetime      # When workflow was queued
    planned_at: datetime | None  # When Architect completed (null if not planned)

    @property
    def is_planned(self) -> bool:
        """True if Architect has run and plan is ready."""
        return self.planned_at is not None
```

#### Update Status Transitions Table

Add transitions:
- `pending` → `in_progress` (workflow started)
- `pending` → `failed` (startup error)

### 5. Architecture: Overview (`/docs/site/architecture/overview.md`)

**Priority: P2 - Medium**

#### Update Flow Diagram

Current flow:
```
Issue → Architect → Approval → Developer ↔ Reviewer → Done
```

Updated flow with queue support:
```
Issue → [Queue] → [Plan] → Architect → Approval → Developer ↔ Reviewer → Done
         ↓          ↓
      pending   planned_at set
```

Add note about optional queue step before Architect execution.

### 6. README.md (Root)

**Priority: P2 - Medium**

The root README focuses on quick start. Consider adding brief mention of queue capability:

```bash
# Quick start
amelia start ISSUE-123

# Or queue for later
amelia start ISSUE-123 --queue --plan
```

### 7. Dashboard Documentation (If Exists)

**Priority: P3 - Low**

Document new dashboard features:
- QuickShotModal now has three buttons: Queue, Plan & Queue, Start
- PendingWorkflowControls component for managing queued workflows
- Queue status indicators and relative timestamps

## Files to Modify

| File | Priority | Type |
|------|----------|------|
| `docs/site/guide/usage.md` | P0 | Major update |
| `docs/site/guide/troubleshooting.md` | P1 | Add section |
| `docs/site/architecture/data-model.md` | P1 | Add fields |
| `docs/site/architecture/overview.md` | P2 | Update diagram |
| `README.md` | P2 | Minor addition |

## Implementation Order

1. **Session 1**: Update `usage.md` with CLI and API documentation
2. **Session 2**: Update `troubleshooting.md` and `data-model.md`
3. **Session 3**: Update `overview.md` diagrams and `README.md`

## Verification Checklist

After updates, verify:
- [ ] All new CLI flags documented with examples
- [ ] All new API endpoints documented with request/response schemas
- [ ] State transitions accurately reflect code behavior
- [ ] Data model fields match implementation
- [ ] Troubleshooting covers common queue issues
- [ ] Examples are copy-pasteable and correct

## References

- PR #264: feat(queue-workflows): add workflow queueing and batch execution
- Commit: 7f04418
- Design docs: `docs/plans/2026-01-10-pipeline-foundation-design.md`
