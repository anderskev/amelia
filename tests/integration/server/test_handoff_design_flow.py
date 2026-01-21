"""Integration tests for brainstorming handoff to implementation."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from amelia.server.models.requests import CreateWorkflowRequest
from amelia.server.orchestrator.service import OrchestratorService


@pytest.fixture
def mock_settings():
    """Create minimal mock settings."""
    settings = MagicMock()
    settings.active_profile = "test"
    profile = MagicMock()
    profile.name = "test"
    profile.tracker = "noop"
    profile.model_copy.return_value = profile
    settings.profiles = {"test": profile}
    return settings


class TestHandoffDesignFlow:
    """Test design artifact flows through handoff to implementation."""

    async def test_prepare_workflow_state_loads_design_from_artifact_path(
        self, tmp_path: Path, mock_settings: MagicMock
    ) -> None:
        """Design is loaded from artifact_path into ImplementationState."""
        # Create a design artifact file
        design_file = tmp_path / "design.md"
        design_file.write_text("# Design\n\nThis is the design content.")

        # Create orchestrator with mocked dependencies
        orchestrator = OrchestratorService.__new__(OrchestratorService)
        orchestrator._event_bus = MagicMock()
        orchestrator._workflows = {}
        orchestrator._load_settings_for_worktree = MagicMock(return_value=mock_settings)

        # Patch get_git_head to avoid actual git operations
        with patch(
            "amelia.server.orchestrator.service.get_git_head",
            new_callable=AsyncMock,
            return_value="abc123",
        ):
            _, _, state = await orchestrator._prepare_workflow_state(
                workflow_id="wf-123",
                worktree_path=str(tmp_path),
                issue_id="issue-1",
                task_title="Implement design",
                artifact_path=str(design_file),
            )

        # Verify design was loaded
        assert state.design is not None
        assert state.design.content == "# Design\n\nThis is the design content."
        assert state.design.source == "file"

    async def test_prepare_workflow_state_without_artifact_path(
        self, tmp_path: Path, mock_settings: MagicMock
    ) -> None:
        """Design is None when no artifact_path provided (backward compatible)."""
        orchestrator = OrchestratorService.__new__(OrchestratorService)
        orchestrator._event_bus = MagicMock()
        orchestrator._workflows = {}
        orchestrator._load_settings_for_worktree = MagicMock(return_value=mock_settings)

        with patch(
            "amelia.server.orchestrator.service.get_git_head",
            new_callable=AsyncMock,
            return_value="abc123",
        ):
            _, _, state = await orchestrator._prepare_workflow_state(
                workflow_id="wf-123",
                worktree_path=str(tmp_path),
                issue_id="issue-1",
                task_title="Implement feature",
            )

        # Design should remain None
        assert state.design is None

    async def test_prepare_workflow_state_with_missing_artifact_file(
        self, tmp_path: Path, mock_settings: MagicMock
    ) -> None:
        """Raises FileNotFoundError when artifact file doesn't exist."""
        orchestrator = OrchestratorService.__new__(OrchestratorService)
        orchestrator._event_bus = MagicMock()
        orchestrator._workflows = {}
        orchestrator._load_settings_for_worktree = MagicMock(return_value=mock_settings)

        with patch(
            "amelia.server.orchestrator.service.get_git_head",
            new_callable=AsyncMock,
            return_value="abc123",
        ):
            with pytest.raises(FileNotFoundError):
                await orchestrator._prepare_workflow_state(
                    workflow_id="wf-123",
                    worktree_path=str(tmp_path),
                    issue_id="issue-1",
                    task_title="Implement design",
                    artifact_path="/nonexistent/design.md",
                )
