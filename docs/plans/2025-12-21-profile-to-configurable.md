# Profile to Configurable Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move Profile from ExecutionState.profile to config["configurable"]["profile"] for cleaner separation of runtime config from execution state.

**Architecture:** Remove `profile` field from `ExecutionState`, add `profile_id: str` for replay determinism, pass profile via `config["configurable"]["profile"]`. All nodes extract profile from config instead of state.

**Tech Stack:** Python 3.12+, Pydantic, LangGraph, pytest

---

## Task 1: Update ExecutionState to Remove profile Field

**Files:**
- Modify: `amelia/core/state.py:313-349`
- Test: `tests/unit/test_state.py`

**Step 1: Write the failing test for profile_id field**

```python
# In tests/unit/test_state.py - add new test class

class TestExecutionStateProfileId:
    """Tests for profile_id field in ExecutionState."""

    def test_profile_id_is_required(self) -> None:
        """ExecutionState requires profile_id string."""
        state = ExecutionState(profile_id="work-profile")
        assert state.profile_id == "work-profile"

    def test_profile_id_must_be_string(self) -> None:
        """profile_id must be a string, not a Profile object."""
        with pytest.raises(ValidationError):
            ExecutionState(profile_id=123)  # type: ignore

    def test_no_profile_field_exists(self) -> None:
        """ExecutionState should not have a profile field."""
        state = ExecutionState(profile_id="test")
        assert not hasattr(state, "profile")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_state.py::TestExecutionStateProfileId -v`
Expected: FAIL with "profile_id" not recognized or "profile" required

**Step 3: Update ExecutionState model**

In `amelia/core/state.py`, find the ExecutionState class and:
1. Remove `profile: Profile` field
2. Add `profile_id: str` field

```python
class ExecutionState(BaseModel):
    """State for the LangGraph orchestrator execution.

    Attributes:
        profile_id: ID of the active profile (for replay determinism).
            The actual Profile object is passed via config["configurable"]["profile"].
        issue: Issue being addressed (if any).
        ...
    """

    model_config = ConfigDict(frozen=True)

    profile_id: str  # Was: profile: Profile
    issue: Issue | None = None
    # ... rest unchanged
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_state.py::TestExecutionStateProfileId -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/state.py tests/unit/test_state.py
git commit -m "refactor(state): replace profile field with profile_id string"
```

---

## Task 2: Update _extract_config_params Helper

**Files:**
- Modify: `amelia/core/orchestrator.py:74-92`
- Test: `tests/unit/core/test_orchestrator_helpers.py` (new file)

**Step 1: Write failing test for profile extraction**

```python
# tests/unit/core/test_orchestrator_helpers.py (new file)
"""Tests for orchestrator helper functions."""
import pytest
from langchain_core.runnables.config import RunnableConfig

from amelia.core.orchestrator import _extract_config_params
from amelia.core.types import Profile


class TestExtractConfigParams:
    """Tests for _extract_config_params helper."""

    def test_extracts_profile_from_config(self) -> None:
        """Should extract profile from config.configurable.profile."""
        profile = Profile(name="test", driver="cli:claude")
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "wf-123",
                "profile": profile,
            }
        }
        stream_emitter, workflow_id, extracted_profile = _extract_config_params(config)
        assert extracted_profile == profile
        assert workflow_id == "wf-123"

    def test_raises_if_profile_missing(self) -> None:
        """Should raise ValueError if profile not in config."""
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "wf-123",
            }
        }
        with pytest.raises(ValueError, match="profile is required"):
            _extract_config_params(config)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/core/test_orchestrator_helpers.py -v`
Expected: FAIL - function returns 2 values, not 3

**Step 3: Update _extract_config_params to return profile**

```python
def _extract_config_params(config: RunnableConfig | None) -> tuple[StreamEmitter | None, str, Profile]:
    """Extract stream_emitter, workflow_id, and profile from RunnableConfig.

    Args:
        config: Optional RunnableConfig with configurable parameters.

    Returns:
        Tuple of (stream_emitter, workflow_id, profile).

    Raises:
        ValueError: If workflow_id (thread_id) or profile is not provided.
    """
    config = config or {}
    configurable = config.get("configurable", {})
    stream_emitter = configurable.get("stream_emitter")
    workflow_id = configurable.get("thread_id")
    profile = configurable.get("profile")

    if not workflow_id:
        raise ValueError("workflow_id (thread_id) is required in config.configurable")
    if not profile:
        raise ValueError("profile is required in config.configurable")

    return stream_emitter, workflow_id, profile
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/core/test_orchestrator_helpers.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py tests/unit/core/test_orchestrator_helpers.py
git commit -m "refactor(orchestrator): extract profile from config in helper"
```

---

## Task 3: Update call_architect_node

**Files:**
- Modify: `amelia/core/orchestrator.py:96-140` (approximate)
- Test: `tests/unit/agents/test_architect_context.py`

**Step 1: Write failing test**

```python
# Add to tests/unit/agents/test_architect_context.py

async def test_architect_node_uses_profile_from_config(
    mock_profile_factory: Callable[..., Profile],
    mock_issue_factory: Callable[..., Issue],
) -> None:
    """call_architect_node should get profile from config, not state."""
    from amelia.core.orchestrator import call_architect_node
    from amelia.core.state import ExecutionState

    profile = mock_profile_factory()
    issue = mock_issue_factory()

    # State has profile_id, not profile object
    state = ExecutionState(profile_id=profile.name, issue=issue)

    # Profile is in config
    config: RunnableConfig = {
        "configurable": {
            "thread_id": "wf-test",
            "profile": profile,
        }
    }

    # Should not raise, should use profile from config
    # (We'll mock the Architect to avoid actual LLM calls)
    with patch("amelia.core.orchestrator.Architect") as mock_arch:
        mock_arch_instance = MagicMock()
        mock_arch_instance.generate_plan = AsyncMock(return_value=MagicMock())
        mock_arch.return_value = mock_arch_instance

        result = await call_architect_node(state, config)

        # Verify Architect was called with correct context
        mock_arch_instance.generate_plan.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/agents/test_architect_context.py::test_architect_node_uses_profile_from_config -v`
Expected: FAIL - state.profile AttributeError or similar

**Step 3: Update call_architect_node**

```python
async def call_architect_node(
    state: ExecutionState,
    config: RunnableConfig | None = None,
) -> dict[str, Any]:
    """Orchestrator node for the Architect agent to generate an execution plan."""
    stream_emitter, workflow_id, profile = _extract_config_params(config)

    # Use profile from config, not state
    driver = DriverFactory.get_driver(profile.driver)
    # ... rest uses profile instead of state.profile
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/agents/test_architect_context.py::test_architect_node_uses_profile_from_config -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py tests/unit/agents/test_architect_context.py
git commit -m "refactor(orchestrator): architect node uses profile from config"
```

---

## Task 4: Update call_developer_node

**Files:**
- Modify: `amelia/core/orchestrator.py` (call_developer_node function)
- Test: `tests/unit/agents/test_developer.py` or similar

**Step 1: Write failing test**

```python
# tests/unit/core/test_developer_node.py (new or existing)

async def test_developer_node_uses_profile_from_config(
    mock_profile_factory,
    mock_issue_factory,
    mock_execution_plan_factory,
) -> None:
    """call_developer_node should get profile from config."""
    from amelia.core.orchestrator import call_developer_node

    profile = mock_profile_factory()
    state = ExecutionState(
        profile_id=profile.name,
        issue=mock_issue_factory(),
        execution_plan=mock_execution_plan_factory(),
    )

    config: RunnableConfig = {
        "configurable": {
            "thread_id": "wf-test",
            "profile": profile,
        }
    }

    with patch("amelia.core.orchestrator.Developer") as mock_dev:
        mock_dev_instance = MagicMock()
        mock_dev_instance.execute_batch = AsyncMock(return_value={})
        mock_dev.return_value = mock_dev_instance

        await call_developer_node(state, config)
        # Should not raise
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/core/test_developer_node.py -v`
Expected: FAIL

**Step 3: Update call_developer_node**

Update all `state.profile` references to use profile from config:
```python
stream_emitter, workflow_id, profile = _extract_config_params(config)
driver = DriverFactory.get_driver(profile.driver)
# ... use profile instead of state.profile
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/core/test_developer_node.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py tests/unit/core/test_developer_node.py
git commit -m "refactor(orchestrator): developer node uses profile from config"
```

---

## Task 5: Update call_reviewer_node

**Files:**
- Modify: `amelia/core/orchestrator.py` (call_reviewer_node function)
- Test: `tests/unit/agents/test_reviewer_context.py`

**Step 1: Write failing test**

```python
# Add to tests/unit/agents/test_reviewer_context.py

async def test_reviewer_node_uses_profile_from_config(
    mock_profile_factory,
    mock_issue_factory,
) -> None:
    """call_reviewer_node should get profile from config."""
    from amelia.core.orchestrator import call_reviewer_node

    profile = mock_profile_factory()
    state = ExecutionState(
        profile_id=profile.name,
        issue=mock_issue_factory(),
        code_changes_for_review="diff content",
    )

    config: RunnableConfig = {
        "configurable": {
            "thread_id": "wf-test",
            "profile": profile,
        }
    }

    with patch("amelia.core.orchestrator.Reviewer") as mock_rev:
        mock_rev_instance = MagicMock()
        mock_rev_instance.review = AsyncMock(return_value=MagicMock(approved=True))
        mock_rev.return_value = mock_rev_instance

        await call_reviewer_node(state, config)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/agents/test_reviewer_context.py::test_reviewer_node_uses_profile_from_config -v`
Expected: FAIL

**Step 3: Update call_reviewer_node**

```python
stream_emitter, workflow_id, profile = _extract_config_params(config)
driver = DriverFactory.get_driver(profile.driver)
# Replace state.profile with profile throughout
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/agents/test_reviewer_context.py::test_reviewer_node_uses_profile_from_config -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py tests/unit/agents/test_reviewer_context.py
git commit -m "refactor(orchestrator): reviewer node uses profile from config"
```

---

## Task 6: Update Remaining Orchestrator Nodes

**Files:**
- Modify: `amelia/core/orchestrator.py` (remaining nodes)
- Test: Existing tests + new as needed

**Step 1: Identify remaining nodes that use state.profile**

Search for `state.profile` in orchestrator.py:
- `should_checkpoint` function
- `after_review_edge` function
- Any other node functions

**Step 2: Update should_checkpoint**

This function takes `profile` as a parameter, so it should continue to work.
Verify callers pass profile from config.

**Step 3: Update after_review_edge**

```python
def after_review_edge(state: ExecutionState, config: RunnableConfig | None = None) -> str:
    """Determine next step after review."""
    _, _, profile = _extract_config_params(config)
    max_iterations = profile.max_review_iterations if profile else 3
    # ... rest
```

**Step 4: Run all orchestrator tests**

Run: `uv run pytest tests/unit/core/ tests/integration/test_orchestrator.py -v`
Expected: PASS (after fixes)

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py
git commit -m "refactor(orchestrator): remaining nodes use profile from config"
```

---

## Task 7: Update Agent Classes

**Files:**
- Modify: `amelia/agents/developer.py`
- Modify: `amelia/agents/reviewer.py`
- Modify: `amelia/agents/architect.py`
- Test: `tests/unit/agents/`

**Step 1: Check agent method signatures**

Agents receive `state: ExecutionState` and extract `state.profile`. They need to either:
1. Receive profile as a separate parameter, OR
2. Access it via a passed config

Option 1 is cleaner: update agent methods to take `profile: Profile` parameter.

**Step 2: Update Developer class**

```python
class Developer:
    async def execute_batch(
        self,
        state: ExecutionState,
        profile: Profile,  # Add this
        batch: ExecutionBatch,
        ...
    ) -> dict[str, Any]:
        # Replace state.profile with profile
```

**Step 3: Update Reviewer class**

```python
class Reviewer:
    async def review(
        self,
        state: ExecutionState,
        profile: Profile,  # Add this
        ...
    ) -> ReviewResult:
        # Replace state.profile with profile
```

**Step 4: Update Architect class**

```python
class Architect:
    async def generate_plan(
        self,
        state: ExecutionState,
        profile: Profile,  # Add this
        ...
    ) -> ExecutionPlan:
        # Replace state.profile with profile
```

**Step 5: Run agent tests**

Run: `uv run pytest tests/unit/agents/ -v`
Expected: PASS (after updating test fixtures)

**Step 6: Commit**

```bash
git add amelia/agents/
git commit -m "refactor(agents): accept profile as parameter instead of from state"
```

---

## Task 8: Update Server Service

**Files:**
- Modify: `amelia/server/orchestrator/service.py`
- Test: `tests/unit/server/orchestrator/test_service.py`

**Step 1: Update start_workflow to pass profile in config**

```python
# In OrchestratorService.start_workflow (around line 500)
config: RunnableConfig = {
    "configurable": {
        "thread_id": workflow_id,
        "execution_mode": "server",
        "stream_emitter": stream_emitter,
        "profile": loaded_profile,  # Add this
    }
}
```

**Step 2: Update ExecutionState creation**

```python
# Around line 225
execution_state = ExecutionState(
    profile_id=loaded_profile.name,  # Was: profile=loaded_profile
    issue=issue,
    plan_only=plan_only,
)
```

**Step 3: Update all graph.astream calls**

Ensure config with profile is passed to all astream/resume calls.

**Step 4: Run service tests**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/server/orchestrator/service.py
git commit -m "refactor(server): pass profile via config, use profile_id in state"
```

---

## Task 9: Update Test Fixtures

**Files:**
- Modify: `tests/conftest.py`
- Modify: `tests/integration/conftest.py`
- Modify: Various test files that create ExecutionState

**Step 1: Update mock_execution_state_factory**

```python
# In tests/conftest.py
@pytest.fixture
def mock_execution_state_factory(
    mock_profile_factory: Callable[..., Profile],
    mock_issue_factory: Callable[..., Issue],
) -> Callable[..., ExecutionState]:
    def _factory(
        profile: Profile | None = None,
        issue: Issue | None = None,
        **kwargs: Any,
    ) -> ExecutionState:
        if profile is None:
            profile = mock_profile_factory()
        if issue is None:
            issue = mock_issue_factory()
        return ExecutionState(
            profile_id=profile.name,  # Changed from profile=profile
            issue=issue,
            **kwargs,
        )
    return _factory
```

**Step 2: Update test helper for config**

```python
@pytest.fixture
def mock_config_factory(mock_profile_factory):
    def _factory(profile: Profile | None = None, **kwargs):
        if profile is None:
            profile = mock_profile_factory()
        return {
            "configurable": {
                "thread_id": kwargs.get("workflow_id", "test-wf"),
                "profile": profile,
                **kwargs,
            }
        }
    return _factory
```

**Step 3: Update all tests creating ExecutionState directly**

Search for `ExecutionState(profile=` and update to `ExecutionState(profile_id=`.

**Step 4: Run full test suite**

Run: `uv run pytest`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/
git commit -m "test: update fixtures for profile_id pattern"
```

---

## Task 10: Final Integration Test

**Files:**
- Test: `tests/integration/test_orchestrator.py`
- Test: `tests/integration/test_workflow_smoke.py`

**Step 1: Run integration tests**

Run: `uv run pytest tests/integration/ -v`

**Step 2: Fix any remaining issues**

Address any test failures found.

**Step 3: Run full test suite + type check + lint**

Run: `uv run pytest && uv run mypy amelia && uv run ruff check amelia tests`
Expected: All pass

**Step 4: Commit any fixes**

```bash
git add .
git commit -m "fix: integration test fixes for profile refactor"
```

---

## Task 11: Update Documentation

**Files:**
- Modify: `docs/site/architecture/overview.md`

**Step 1: Update architecture docs**

Update the ExecutionState example in docs to show profile_id:
```python
class ExecutionState(BaseModel):
    profile_id: str  # Profile name for replay determinism
    issue: Issue | None = None
    # ... rest
```

Add note about profile being passed via config:
```python
config = {
    "configurable": {
        "thread_id": workflow_id,
        "profile": profile,  # Runtime config passed here
    }
}
```

**Step 2: Commit**

```bash
git add docs/
git commit -m "docs: update architecture for profile in configurable"
```

---

## Summary Checklist

- [ ] ExecutionState no longer has `profile` field
- [ ] ExecutionState has `profile_id: str` for replay tracking
- [ ] `_extract_config_params` returns profile from config
- [ ] All orchestrator nodes access profile via `config["configurable"]["profile"]`
- [ ] Agent classes receive profile as parameter
- [ ] Server service passes profile in config when invoking graph
- [ ] All test fixtures updated
- [ ] All tests pass
- [ ] Type checks pass
- [ ] Lint passes
