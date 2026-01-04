# Fixed Plan Path Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Simplify plan extraction by using a fixed file path instead of parsing tool calls

**Architecture:** Add a configurable `plan_path_pattern` to Profile (default: `docs/plans/{date}-{issue_key}.md`). The architect prompt includes the resolved path, and the orchestrator reads directly from that path after architect completes. This eliminates tool call parsing and tool name normalization for plan extraction.

**Tech Stack:** Python, Pydantic

---

## Current State

The current flow:
1. Architect prompt tells Claude to write a plan via Write tool (no specific path)
2. Claude writes to whatever path it chooses
3. Orchestrator parses tool calls to find Write commands
4. Tool name normalization handles `Write` vs `write_file` differences
5. Orchestrator extracts content from tool call

Problems:
- Tool name normalization complexity
- Parsing tool calls is fragile
- `plan_path` fallback never works (always `None`)

## New Flow

1. Add `plan_path_pattern` field to Profile (default: `docs/plans/{date}-{issue_key}.md`)
2. Add helper: `resolve_plan_path(pattern: str, issue_key: str) -> str`
3. Architect prompt includes the resolved path for this issue
4. After architect completes, orchestrator reads directly from that path
5. No tool call parsing needed for plan extraction
6. Tool name normalization can be removed (no longer needed)

---

### Task 1: Add plan_path_pattern to Profile

**Files:**
- Modify: `amelia/core/types.py` (the `Profile` class)

**Step 1: Write the failing test**

```python
# tests/unit/core/test_types.py
def test_profile_has_plan_path_pattern_with_default():
    from amelia.core.types import Profile

    profile = Profile(driver="cli:claude")
    assert profile.plan_path_pattern == "docs/plans/{date}-{issue_key}.md"

def test_profile_plan_path_pattern_is_configurable():
    from amelia.core.types import Profile

    profile = Profile(driver="cli:claude", plan_path_pattern=".amelia/{issue_key}-plan.md")
    assert profile.plan_path_pattern == ".amelia/{issue_key}-plan.md"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/core/test_types.py::test_profile_has_plan_path_pattern_with_default -v`
Expected: FAIL with "AttributeError"

**Step 3: Add the field to Profile**

In `amelia/core/types.py`, add to the `Profile` class:

```python
plan_path_pattern: str = "docs/plans/{date}-{issue_key}.md"
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/core/test_types.py -k "plan_path_pattern" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/types.py tests/unit/core/test_types.py
git commit -m "feat(types): add plan_path_pattern to Profile"
```

---

### Task 2: Add resolve_plan_path helper function

**Files:**
- Modify: `amelia/core/constants.py`

**Step 1: Write the failing test**

```python
# tests/unit/core/test_constants.py
from datetime import date

def test_resolve_plan_path_substitutes_placeholders():
    from amelia.core.constants import resolve_plan_path

    pattern = "docs/plans/{date}-{issue_key}.md"
    result = resolve_plan_path(pattern, "TEST-123")
    today = date.today().isoformat()
    assert result == f"docs/plans/{today}-test-123.md"

def test_resolve_plan_path_handles_custom_pattern():
    from amelia.core.constants import resolve_plan_path

    pattern = ".amelia/plans/{issue_key}.md"
    result = resolve_plan_path(pattern, "JIRA-456")
    assert result == ".amelia/plans/jira-456.md"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/core/test_constants.py::test_resolve_plan_path_substitutes_placeholders -v`
Expected: FAIL with "ImportError: cannot import name 'resolve_plan_path'"

**Step 3: Add the helper function**

Add to `amelia/core/constants.py`:

```python
from datetime import date

def resolve_plan_path(pattern: str, issue_key: str) -> str:
    """Resolve a plan path pattern to a concrete path.

    Supported placeholders:
    - {date}: Today's date in YYYY-MM-DD format
    - {issue_key}: The issue key, lowercased

    Args:
        pattern: Path pattern with placeholders.
        issue_key: The issue key (e.g., "TEST-123").

    Returns:
        Resolved path with placeholders substituted.
    """
    today = date.today().isoformat()
    normalized_key = issue_key.lower()
    return pattern.format(date=today, issue_key=normalized_key)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/core/test_constants.py -k "resolve_plan_path" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/constants.py tests/unit/core/test_constants.py
git commit -m "feat(core): add resolve_plan_path helper"
```

---

### Task 3: Update architect to include plan path in user prompt

**Files:**
- Modify: `amelia/agents/architect.py` (the `_build_agentic_prompt` method and `plan` method signature)

**Intent:** The plan path is dynamic (includes date and issue key), so we inject it into the user prompt. The profile is passed to provide the pattern.

**Step 1: Write the failing test**

```python
# tests/unit/agents/test_architect.py
def test_architect_agentic_prompt_includes_plan_path():
    from unittest.mock import MagicMock
    from amelia.agents.architect import Architect
    from amelia.core.state import ExecutionState
    from amelia.core.types import Issue, Profile

    mock_driver = MagicMock()
    architect = Architect(driver=mock_driver)

    issue = Issue(key="TEST-123", title="Test", description="Test issue")
    profile = Profile(driver="cli:claude")
    state = ExecutionState(issue=issue, profile=profile)

    prompt = architect._build_agentic_prompt(state)

    assert "docs/plans/" in prompt
    assert "test-123" in prompt.lower()
    assert "Write your plan to" in prompt
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/agents/test_architect.py::test_architect_agentic_prompt_includes_plan_path -v`
Expected: FAIL with "AssertionError"

**Step 3: Update _build_agentic_prompt**

In `amelia/agents/architect.py`, update `_build_agentic_prompt` to include the plan path:

```python
from amelia.core.constants import resolve_plan_path

def _build_agentic_prompt(self, state: ExecutionState) -> str:
    # ... existing code ...

    # Add output instruction with resolved plan path
    plan_path = resolve_plan_path(state.profile.plan_path_pattern, state.issue.key)
    parts.append(f"\n## Output")
    parts.append(f"Write your plan to `{plan_path}` using the Write tool.")

    return "\n".join(parts)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/agents/test_architect.py::test_architect_agentic_prompt_includes_plan_path -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/agents/architect.py tests/unit/agents/test_architect.py
git commit -m "feat(architect): include dynamic plan path in user prompt"
```

---

### Task 4: Update orchestrator to read from predictable path

**Files:**
- Modify: `amelia/core/orchestrator.py` (the `call_architect_node` function, around line 260-344)

**Step 1: Write the failing test**

```python
# tests/unit/core/test_orchestrator_plan_extraction.py
import pytest
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_call_architect_node_reads_from_predictable_path(tmp_path):
    """Orchestrator should read plan from resolved path, not parse tool calls."""
    from amelia.core.orchestrator import call_architect_node
    from amelia.core.state import ExecutionState
    from amelia.core.types import Issue, Profile

    # Create the plan file at the expected path
    today = date.today().isoformat()
    plan_dir = tmp_path / "docs" / "plans"
    plan_dir.mkdir(parents=True)
    plan_file = plan_dir / f"{today}-test-1.md"
    plan_content = """# Test Plan

**Goal:** Implement feature X

## Tasks
- Task 1
"""
    plan_file.write_text(plan_content)

    # Create state with issue
    issue = Issue(key="TEST-1", title="Test", description="Test issue")
    profile = Profile(
        driver="cli:claude",
        working_dir=str(tmp_path),
    )
    state = ExecutionState(issue=issue, profile=profile)

    # ... rest of test setup with mocked architect
    # Assert that plan was read from predictable path
    # Assert goal was extracted correctly
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/core/test_orchestrator_plan_extraction.py -v`
Expected: FAIL (orchestrator still tries to parse tool calls)

**Step 3: Simplify plan extraction in call_architect_node**

Replace the tool call parsing section (lines ~260-296) with:

```python
from amelia.core.constants import resolve_plan_path

# Read plan from predictable path based on profile pattern
plan_rel_path = resolve_plan_path(profile.plan_path_pattern, state.issue.key)
plan_path = Path(profile.working_dir) / plan_rel_path
plan_content: str | None = None
plan_file_path: Path | None = None

if plan_path.exists():
    try:
        plan_content = plan_path.read_text()
        plan_file_path = plan_path
        logger.debug(
            "Read plan from predictable path",
            plan_path=str(plan_path),
            plan_length=len(plan_content),
        )
    except Exception as e:
        logger.warning(
            "Failed to read plan file",
            plan_path=str(plan_path),
            error=str(e),
        )
else:
    logger.warning(
        "Plan file not found at expected path",
        plan_path=str(plan_path),
    )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/core/test_orchestrator_plan_extraction.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py tests/unit/core/test_orchestrator_plan_extraction.py
git commit -m "refactor(orchestrator): read plan from fixed path instead of parsing tool calls"
```

---

### Task 5: Remove tool name normalization for plan extraction

**Files:**
- Modify: `amelia/core/constants.py` - remove TOOL_NAME_ALIASES and normalize_tool_name if no longer used elsewhere
- Modify: `amelia/core/orchestrator.py` - remove import of normalize_tool_name if unused
- Delete or update: `tests/integration/test_tool_name_normalization.py`

**Step 1: Check if tool name normalization is used elsewhere**

Run: `grep -r "normalize_tool_name\|TOOL_NAME_ALIASES" amelia/`

If only used in orchestrator plan extraction → remove entirely.
If used elsewhere → keep, but remove from orchestrator.

**Step 2: Update or remove tests**

If removing entirely:
```bash
git rm tests/integration/test_tool_name_normalization.py
```

If keeping but removing from orchestrator, update tests to reflect new behavior.

**Step 3: Remove unused code**

Remove from `amelia/core/constants.py`:
- `TOOL_NAME_ALIASES` dict
- `normalize_tool_name()` function

Remove from `amelia/core/orchestrator.py`:
- Import of `normalize_tool_name`
- Any remaining references

**Step 4: Run full test suite**

Run: `uv run pytest`
Expected: All tests pass

**Step 5: Commit**

```bash
git add -A
git commit -m "refactor(core): remove tool name normalization (no longer needed)"
```

---

### Task 6: Update existing tests to use predictable path

**Files:**
- Modify: `tests/unit/core/test_orchestrator_helpers.py`
- Modify: `tests/integration/test_agentic_workflow.py` (if exists)
- Modify: Any other tests that mock tool calls for plan extraction

**Step 1: Find all affected tests**

Run: `grep -r "tool_name.*Write\|Write.*tool_name" tests/`

**Step 2: Update each test**

Update tests to:

1. Create `docs/plans/{date}-{issue_key}.md` file in test fixture
2. Remove tool call mocking for plan extraction
3. Assert plan is read from predictable path

**Step 3: Run full test suite**

Run: `uv run pytest`
Expected: All tests pass

**Step 4: Commit**

```bash
git add tests/
git commit -m "test: update tests to use predictable plan path"
```

---

### Task 7: Ensure docs/plans directory is created

**Files:**
- Modify: `amelia/core/orchestrator.py`

**Intent:** The docs/plans directory may not exist in a fresh repo. Ensure it's created before the architect tries to write to it.

**Step 1: Write the failing test**

```python
def test_plans_dir_created_if_missing(tmp_path):
    """The docs/plans directory should be created if it doesn't exist."""
    plans_dir = tmp_path / "docs" / "plans"
    assert not plans_dir.exists()

    # ... run orchestrator setup that triggers directory creation

    assert plans_dir.exists()
```

**Step 2: Add directory creation**

In orchestrator, before calling architect (or in the prompt setup):

```python
plan_rel_path = resolve_plan_path(profile.plan_path_pattern, state.issue.key)
plan_path = Path(profile.working_dir) / plan_rel_path
plan_path.parent.mkdir(parents=True, exist_ok=True)
```

Or alternatively, let the Write tool handle it (most implementations create parent dirs).

**Step 3: Run test**

Run: `uv run pytest tests/unit/core/test_plans_dir_creation.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add -A
git commit -m "feat(orchestrator): ensure plan directory exists"
```

---

### Task 8: Run full verification

**Step 1: Run linting**

Run: `uv run ruff check amelia tests`
Expected: No errors

**Step 2: Run type checking**

Run: `uv run mypy amelia`
Expected: No errors

**Step 3: Run full test suite**

Run: `uv run pytest`
Expected: All tests pass

**Step 4: Final commit if any fixes needed**

```bash
git add -A
git commit -m "chore: fix linting and type errors"
```

---

## Summary

After completing all tasks:

1. Profile has configurable `plan_path_pattern` (default: `docs/plans/{date}-{issue_key}.md`)
2. Architect prompt tells Claude to write to the resolved path
3. Orchestrator reads directly from that predictable path
4. No tool call parsing for plan extraction
5. No tool name normalization needed
6. Same behavior for CLI and API drivers
