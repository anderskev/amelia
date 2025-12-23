# Worktree Settings Loading Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Load settings from the worktree directory instead of the server startup directory, enabling multi-project setups where each project has its own `settings.amelia.yaml`.

**Architecture:** Add a `_load_settings_for_worktree()` helper to `OrchestratorService` that loads settings from a worktree path. The method handles errors gracefully (missing file, invalid YAML, validation errors) by failing the individual workflow with a clear error message. Workflows use worktree-specific settings while the server keeps its startup settings for defaults.

**Tech Stack:** Python 3.12, Pydantic, PyYAML, pytest-asyncio

---

## Task 1: Add helper method `_load_settings_for_worktree`

**Files:**
- Modify: `amelia/server/orchestrator/service.py:60-100` (add new method after `__init__`)

**Step 1: Write the failing test**

In `tests/unit/server/orchestrator/test_service.py`, add a new test class at the end of the file:

```python
# =============================================================================
# Worktree Settings Loading Tests
# =============================================================================


class TestLoadSettingsForWorktree:
    """Tests for _load_settings_for_worktree helper method."""

    async def test_loads_settings_from_worktree_path(
        self,
        orchestrator: OrchestratorService,
        tmp_path: Path,
    ):
        """_load_settings_for_worktree loads settings from worktree directory."""
        # Create settings file in worktree
        settings_content = """
active_profile: local
profiles:
  local:
    name: local
    driver: cli:claude
    tracker: github
    strategy: single
"""
        settings_file = tmp_path / "settings.amelia.yaml"
        settings_file.write_text(settings_content)

        settings = orchestrator._load_settings_for_worktree(str(tmp_path))

        assert settings is not None
        assert settings.active_profile == "local"
        assert "local" in settings.profiles
        assert settings.profiles["local"].tracker == "github"

    async def test_returns_none_when_settings_file_missing(
        self,
        orchestrator: OrchestratorService,
        tmp_path: Path,
    ):
        """_load_settings_for_worktree returns None when file not found."""
        settings = orchestrator._load_settings_for_worktree(str(tmp_path))
        assert settings is None

    async def test_returns_none_for_invalid_yaml(
        self,
        orchestrator: OrchestratorService,
        tmp_path: Path,
    ):
        """_load_settings_for_worktree returns None for malformed YAML."""
        settings_file = tmp_path / "settings.amelia.yaml"
        settings_file.write_text("invalid: yaml: content: [")

        settings = orchestrator._load_settings_for_worktree(str(tmp_path))
        assert settings is None

    async def test_returns_none_for_validation_error(
        self,
        orchestrator: OrchestratorService,
        tmp_path: Path,
    ):
        """_load_settings_for_worktree returns None for invalid config structure."""
        settings_file = tmp_path / "settings.amelia.yaml"
        # Missing required 'profiles' field
        settings_file.write_text("active_profile: test\n")

        settings = orchestrator._load_settings_for_worktree(str(tmp_path))
        assert settings is None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py::TestLoadSettingsForWorktree -v`
Expected: FAIL with "AttributeError: 'OrchestratorService' object has no attribute '_load_settings_for_worktree'"

**Step 3: Implement `_load_settings_for_worktree` method**

Add the following method to `OrchestratorService` class in `amelia/server/orchestrator/service.py` after `_get_profile_or_fail` (around line 168):

```python
def _load_settings_for_worktree(self, worktree_path: str) -> Settings | None:
    """Load settings from a worktree directory.

    Attempts to load settings.amelia.yaml from the worktree directory.
    Returns None on any error (file not found, invalid YAML, validation error)
    to allow graceful fallback to server settings.

    Args:
        worktree_path: Absolute path to the worktree directory.

    Returns:
        Settings if successfully loaded, None otherwise.
    """
    from pathlib import Path

    import yaml

    from amelia.core.types import Settings

    settings_path = Path(worktree_path) / "settings.amelia.yaml"

    if not settings_path.exists():
        logger.debug(
            "No settings file in worktree",
            worktree_path=worktree_path,
        )
        return None

    try:
        with open(settings_path) as f:
            data = yaml.safe_load(f)
        return Settings(**data)
    except yaml.YAMLError as e:
        logger.warning(
            "Invalid YAML in worktree settings",
            worktree_path=worktree_path,
            error=str(e),
        )
        return None
    except Exception as e:
        logger.warning(
            "Failed to load worktree settings",
            worktree_path=worktree_path,
            error=str(e),
        )
        return None
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py::TestLoadSettingsForWorktree -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add amelia/server/orchestrator/service.py tests/unit/server/orchestrator/test_service.py
git commit -m "feat(orchestrator): add _load_settings_for_worktree helper method"
```

---

## Task 2: Use worktree settings in `start_workflow`

**Files:**
- Modify: `amelia/server/orchestrator/service.py:169-306` (`start_workflow` method)
- Modify: `tests/unit/server/orchestrator/test_service.py`

**Step 1: Write the failing test**

Add to the `TestLoadSettingsForWorktree` class:

```python
async def test_start_workflow_uses_worktree_settings(
    self,
    orchestrator: OrchestratorService,
    mock_repository: AsyncMock,
    tmp_path: Path,
):
    """start_workflow uses settings from worktree directory, not server settings."""
    # Create valid worktree with .git
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    (worktree / ".git").touch()

    # Create worktree-specific settings with different tracker
    settings_content = """
active_profile: worktree_profile
profiles:
  worktree_profile:
    name: worktree_profile
    driver: cli:claude
    tracker: github
    strategy: single
"""
    (worktree / "settings.amelia.yaml").write_text(settings_content)

    with patch.object(orchestrator, "_run_workflow_with_retry", new=AsyncMock()):
        workflow_id = await orchestrator.start_workflow(
            issue_id="ISSUE-123",
            worktree_path=str(worktree),
            worktree_name="feat-123",
        )

    # Verify workflow was created with worktree profile
    call_args = mock_repository.create.call_args
    state = call_args[0][0]
    assert state.execution_state.profile_id == "worktree_profile"


async def test_start_workflow_fails_gracefully_when_worktree_settings_invalid(
    self,
    orchestrator: OrchestratorService,
    mock_repository: AsyncMock,
    tmp_path: Path,
):
    """start_workflow fails workflow gracefully when worktree settings are invalid."""
    # Create valid worktree with .git
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    (worktree / ".git").touch()

    # Create invalid settings (missing required fields)
    (worktree / "settings.amelia.yaml").write_text("invalid: config\n")

    with pytest.raises(ValueError) as exc_info:
        await orchestrator.start_workflow(
            issue_id="ISSUE-123",
            worktree_path=str(worktree),
            worktree_name="feat-123",
        )

    # Should fail with clear error about settings
    assert "settings" in str(exc_info.value).lower() or "profile" in str(exc_info.value).lower()


async def test_start_workflow_falls_back_to_server_settings_when_no_worktree_settings(
    self,
    orchestrator: OrchestratorService,
    mock_repository: AsyncMock,
    valid_worktree: str,
):
    """start_workflow uses server settings when worktree has no settings file."""
    with patch.object(orchestrator, "_run_workflow_with_retry", new=AsyncMock()):
        workflow_id = await orchestrator.start_workflow(
            issue_id="ISSUE-123",
            worktree_path=valid_worktree,
            worktree_name="feat-123",
        )

    # Should use server's active profile (from mock_settings fixture: "test")
    call_args = mock_repository.create.call_args
    state = call_args[0][0]
    assert state.execution_state.profile_id == "test"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py::TestLoadSettingsForWorktree::test_start_workflow_uses_worktree_settings -v`
Expected: FAIL (still using server settings, not worktree settings)

**Step 3: Modify `start_workflow` to use worktree settings**

In `amelia/server/orchestrator/service.py`, modify `start_workflow` method. Find the profile loading section (around lines 220-224) and update:

Replace:
```python
# Load the profile (use provided profile name or active profile as fallback)
profile_name = profile or self._settings.active_profile
if profile_name not in self._settings.profiles:
    raise ValueError(f"Profile '{profile_name}' not found in settings")
loaded_profile = self._settings.profiles[profile_name]
```

With:
```python
# Load settings: prefer worktree settings, fallback to server settings
worktree_settings = self._load_settings_for_worktree(worktree_path)
effective_settings = worktree_settings if worktree_settings is not None else self._settings

# If worktree has a settings file but it failed to load, that's an error
if worktree_settings is None:
    settings_path = Path(worktree_path) / "settings.amelia.yaml"
    if settings_path.exists():
        raise ValueError(
            f"Failed to load settings from {settings_path}. "
            "Check the file format and ensure all required fields are present."
        )

# Load the profile (use provided profile name or active profile as fallback)
profile_name = profile or effective_settings.active_profile
if profile_name not in effective_settings.profiles:
    raise ValueError(f"Profile '{profile_name}' not found in settings")
loaded_profile = effective_settings.profiles[profile_name]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py::TestLoadSettingsForWorktree -v`
Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add amelia/server/orchestrator/service.py tests/unit/server/orchestrator/test_service.py
git commit -m "feat(orchestrator): start_workflow uses worktree settings when available"
```

---

## Task 3: Use worktree settings in `start_review_workflow`

**Files:**
- Modify: `amelia/server/orchestrator/service.py:308-404` (`start_review_workflow` method)
- Modify: `tests/unit/server/orchestrator/test_service.py`

**Step 1: Write the failing test**

Add to `TestLoadSettingsForWorktree` class:

```python
async def test_start_review_workflow_uses_worktree_settings(
    self,
    orchestrator: OrchestratorService,
    mock_repository: AsyncMock,
    tmp_path: Path,
):
    """start_review_workflow uses settings from worktree directory."""
    # Create valid worktree (review doesn't require .git)
    worktree = tmp_path / "worktree"
    worktree.mkdir()

    # Create worktree-specific settings
    settings_content = """
active_profile: review_profile
profiles:
  review_profile:
    name: review_profile
    driver: cli:claude
    tracker: noop
    strategy: single
"""
    (worktree / "settings.amelia.yaml").write_text(settings_content)

    with patch.object(orchestrator, "_run_review_workflow", new=AsyncMock()):
        workflow_id = await orchestrator.start_review_workflow(
            diff_content="--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new",
            worktree_path=str(worktree),
            worktree_name="review-test",
        )

    # Verify workflow was created with worktree profile
    call_args = mock_repository.create.call_args
    state = call_args[0][0]
    assert state.execution_state.profile_id == "review_profile"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py::TestLoadSettingsForWorktree::test_start_review_workflow_uses_worktree_settings -v`
Expected: FAIL (still using server settings)

**Step 3: Modify `start_review_workflow` to use worktree settings**

In `amelia/server/orchestrator/service.py`, find the profile loading section in `start_review_workflow` (around lines 346-350) and update:

Replace:
```python
# Load profile
profile_name = profile or self._settings.active_profile
loaded_profile = self._settings.profiles[profile_name]
if loaded_profile.working_dir is None:
    loaded_profile = loaded_profile.model_copy(update={"working_dir": worktree_path})
```

With:
```python
# Load settings: prefer worktree settings, fallback to server settings
worktree_settings = self._load_settings_for_worktree(worktree_path)
effective_settings = worktree_settings if worktree_settings is not None else self._settings

# If worktree has a settings file but it failed to load, that's an error
if worktree_settings is None:
    settings_path = Path(worktree_path) / "settings.amelia.yaml"
    if settings_path.exists():
        raise ValueError(
            f"Failed to load settings from {settings_path}. "
            "Check the file format and ensure all required fields are present."
        )

# Load profile
profile_name = profile or effective_settings.active_profile
if profile_name not in effective_settings.profiles:
    raise ValueError(f"Profile '{profile_name}' not found in settings")
loaded_profile = effective_settings.profiles[profile_name]
if loaded_profile.working_dir is None:
    loaded_profile = loaded_profile.model_copy(update={"working_dir": worktree_path})
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/orchestrator/test_service.py::TestLoadSettingsForWorktree -v`
Expected: PASS (8 tests)

**Step 5: Commit**

```bash
git add amelia/server/orchestrator/service.py tests/unit/server/orchestrator/test_service.py
git commit -m "feat(orchestrator): start_review_workflow uses worktree settings when available"
```

---

## Task 4: Add import for Path in start_workflow/start_review_workflow

**Files:**
- Modify: `amelia/server/orchestrator/service.py` (imports at top)

**Step 1: Run linting to check for issues**

Run: `uv run ruff check amelia/server/orchestrator/service.py`
Expected: May show "F811 redefinition of unused 'Path'" if Path is imported inside methods

**Step 2: Move Path import to helper method only if not already at top**

Check if `Path` is already imported at the top of `service.py`. If it is, the inline imports in `_load_settings_for_worktree` should be removed.

In `_load_settings_for_worktree`, remove the inline imports since they're already at the top:

Replace:
```python
def _load_settings_for_worktree(self, worktree_path: str) -> Settings | None:
    """..."""
    from pathlib import Path

    import yaml

    from amelia.core.types import Settings
```

With:
```python
def _load_settings_for_worktree(self, worktree_path: str) -> Settings | None:
    """..."""
    import yaml
```

Note: `Path` is already imported at top (line 9), `Settings` is already imported (line 22).

**Step 3: Run full test suite for orchestrator**

Run: `uv run pytest tests/unit/server/orchestrator/ -v`
Expected: PASS

**Step 4: Run linting and type checking**

Run: `uv run ruff check amelia/server/orchestrator/service.py && uv run mypy amelia/server/orchestrator/service.py`
Expected: No errors

**Step 5: Commit**

```bash
git add amelia/server/orchestrator/service.py
git commit -m "refactor(orchestrator): clean up imports in worktree settings loading"
```

---

## Task 5: Run full test suite and verify all checks pass

**Files:**
- None (verification only)

**Step 1: Run unit tests**

Run: `uv run pytest tests/unit/ -v`
Expected: All tests PASS

**Step 2: Run linting**

Run: `uv run ruff check amelia tests`
Expected: No errors

**Step 3: Run type checking**

Run: `uv run mypy amelia`
Expected: No errors

**Step 4: Run boundary checks**

Run: `python scripts/check_boundaries.py`
Expected: No violations

**Step 5: Commit final state (if any changes needed)**

```bash
git add -A
git commit -m "chore: fix any remaining linting or type issues"
```

---

## Summary

After completing all tasks:
1. `OrchestratorService._load_settings_for_worktree()` - New helper that loads settings from a worktree directory
2. `start_workflow()` - Now loads and uses worktree-specific settings when available
3. `start_review_workflow()` - Now loads and uses worktree-specific settings when available
4. Both methods fail gracefully with clear error messages when worktree settings file exists but is invalid
5. Both methods fall back to server startup settings when no worktree settings file exists
