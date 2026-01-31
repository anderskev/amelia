# Remove Extension System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove the unused `amelia/ext/` extension system and all references to it.

**Architecture:** Delete all extension files, remove imports and usages from `service.py`, update tests, and update documentation. The extension hooks (`emit_workflow_event`, `check_policy_workflow_start`) are called but do nothing meaningful (noop implementations), so they can be safely deleted.

**Tech Stack:** Python, pytest

---

## Summary of Changes

**Delete (7 files):**
- `amelia/ext/__init__.py`
- `amelia/ext/protocols.py`
- `amelia/ext/hooks.py`
- `amelia/ext/registry.py`
- `amelia/ext/noop.py`
- `amelia/ext/exceptions.py`
- `tests/unit/ext/` (entire directory)

**Modify (4 files):**
- `amelia/server/orchestrator/service.py` - Remove extension imports and all usages
- `tests/unit/server/orchestrator/test_service.py` - Remove extension-related tests and patches
- `CLAUDE.md` - Remove Extensions row from Architecture table
- `docs/site/architecture/overview.md` - Remove Extensions row from Architecture table

---

### Task 1: Remove Extension Usage from Service

**Files:**
- Modify: `amelia/server/orchestrator/service.py`

**Step 1: Remove extension imports**

Remove these lines (around lines 23-31):

```python
from amelia.ext import WorkflowEventType as ExtWorkflowEventType
from amelia.ext.exceptions import PolicyDeniedError
from amelia.ext.hooks import (
    check_policy_workflow_start,
    emit_workflow_event,
)
```

**Step 2: Remove policy check in `_start_workflow`**

In the `_start_workflow` method, remove the policy check block (around lines 496-517). This code calls `check_policy_workflow_start` and raises `PolicyDeniedError` if denied. Remove the entire block:

```python
# Before workflow execution, check policy hooks
allowed, hook_name = await check_policy_workflow_start(
    workflow_id=workflow_id,
    issue_key=execution.issue_key,
    profile_name=execution.profile_name,
)
if not allowed:
    logger.warning(
        "Workflow start denied by policy hook",
        workflow_id=workflow_id,
        hook_name=hook_name,
    )
    raise PolicyDeniedError(
        f"Workflow start denied by policy hook: {hook_name}",
        hook_name=hook_name,
        workflow_id=workflow_id,
        context={"issue_key": execution.issue_key},
    )
```

**Step 3: Remove all `emit_workflow_event` calls**

Remove all calls to `emit_workflow_event` throughout the file. These are at approximately:
- Lines 811-816 (CANCELLED event in `cancel_workflow`)
- Lines 1029-1037 (STARTED event in `_run_workflow`)
- Lines 1099-1110 (APPROVAL_REQUESTED and PAUSED events)
- Lines 1127-1135 (COMPLETED event)
- Lines 1181-1189 (FAILED event)
- Lines 1217-1225 (FAILED event in exception handler)
- Lines 1434-1442 (RESUMED event in `provide_plan_approval`)
- Lines 1446-1454 (APPROVAL_GRANTED event)
- Lines 1527-1535 (COMPLETED event)
- Lines 1542-1550 (FAILED event)
- Lines 1591-1599 (APPROVAL_DENIED event)

For each call, remove the entire `await emit_workflow_event(...)` statement.

**Step 4: Run type checker**

Run: `uv run mypy amelia/server/orchestrator/service.py`
Expected: PASS (no errors about missing imports)

**Step 5: Commit**

```bash
git add amelia/server/orchestrator/service.py
git commit -m "refactor(server): remove extension hook usage from service"
```

---

### Task 2: Update Service Tests

**Files:**
- Modify: `tests/unit/server/orchestrator/test_service.py`

**Step 1: Remove policy denial test**

Delete the entire `test_start_workflow_policy_denied` test function (around lines 825-875). This test imports `PolicyDeniedError` and `get_registry` from `amelia.ext` and tests policy hook denial behavior that no longer exists.

**Step 2: Remove emit_workflow_event patches**

Remove the `emit_workflow_event` patches from tests:
- Around line 1059: Remove `patch("amelia.server.orchestrator.service.emit_workflow_event", new=AsyncMock())`
- Around line 1120: Remove `patch("amelia.server.orchestrator.service.emit_workflow_event", new=AsyncMock())`

These patches are in context managers for tests. Remove just the patch line, keeping the rest of the test intact.

**Step 3: Run tests to verify**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add tests/unit/server/orchestrator/test_service.py
git commit -m "test(server): remove extension-related test code"
```

---

### Task 3: Delete Extension Module

**Files:**
- Delete: `amelia/ext/__init__.py`
- Delete: `amelia/ext/protocols.py`
- Delete: `amelia/ext/hooks.py`
- Delete: `amelia/ext/registry.py`
- Delete: `amelia/ext/noop.py`
- Delete: `amelia/ext/exceptions.py`

**Step 1: Delete the entire ext directory**

```bash
rm -rf amelia/ext
```

**Step 2: Verify no remaining imports**

Run: `uv run ruff check amelia --select F401,F811`
Expected: PASS (no unused or undefined imports)

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: remove amelia/ext/ extension system"
```

---

### Task 4: Delete Extension Tests

**Files:**
- Delete: `tests/unit/ext/` (entire directory)

**Step 1: Delete the test directory**

```bash
rm -rf tests/unit/ext
```

**Step 2: Run all tests**

Run: `uv run pytest tests/unit/ -v`
Expected: PASS

**Step 3: Commit**

```bash
git add -A
git commit -m "test: remove extension system tests"
```

---

### Task 5: Update Documentation

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/site/architecture/overview.md`

**Step 1: Update CLAUDE.md**

Remove the Extensions row from the Architecture table (around line 96):

```markdown
| **Extensions** | `amelia/ext/` | Protocols for optional integrations (policy hooks, audit exporters, analytics sinks) |
```

**Step 2: Update docs/site/architecture/overview.md**

Remove the Extensions row from the Architecture table (around line 45):

```markdown
| **Extensions** | `amelia/ext/` | Protocols for optional integrations (policy hooks, audit exporters) | `ExtensionRegistry`, `protocols` |
```

**Step 3: Commit**

```bash
git add CLAUDE.md docs/site/architecture/overview.md
git commit -m "docs: remove extension system from architecture docs"
```

---

### Task 6: Final Verification

**Step 1: Run full lint check**

Run: `uv run ruff check amelia tests`
Expected: PASS

**Step 2: Run type checker**

Run: `uv run mypy amelia`
Expected: PASS

**Step 3: Run full test suite**

Run: `uv run pytest`
Expected: PASS

**Step 4: Verify no remaining ext references**

Run: `grep -r "amelia.ext\|amelia/ext" --include="*.py" amelia tests`
Expected: No output (no remaining references in Python files)

Note: `docs/plans/` may still contain historical references to `amelia/ext/` in old plan documents - these are documentation artifacts and can be ignored.
