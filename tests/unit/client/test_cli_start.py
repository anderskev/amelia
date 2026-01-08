"""Tests for CLI start command."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from amelia.main import app


class TestStartCommandTaskFlags:
    """Tests for --title and --description flags on start command."""

    @pytest.fixture
    def runner(self):
        """Typer CLI test runner."""
        return CliRunner()

    def test_description_without_title_errors(self, runner):
        """--description without --title should error at client side."""
        result = runner.invoke(
            app,
            ["start", "TASK-1", "--description", "Some description"],
        )
        assert result.exit_code != 0
        # Check output includes the validation error message
        output = result.stdout.lower() + (result.output.lower() if hasattr(result, 'output') else '')
        assert "requires" in output or "title" in output

    def test_title_flag_passed_to_client(self, runner, tmp_path):
        """--title should be passed to API client."""
        # Create mock git worktree
        worktree = tmp_path / "repo"
        worktree.mkdir()
        (worktree / ".git").touch()

        with patch("amelia.client.cli._get_worktree_context") as mock_ctx, \
             patch("amelia.client.cli.AmeliaClient") as mock_client_class:
            mock_ctx.return_value = (str(worktree), "repo")
            mock_client = mock_client_class.return_value
            mock_client.create_workflow = AsyncMock(return_value=MagicMock(
                id="wf-123", status="pending"
            ))

            runner.invoke(
                app,
                ["start", "TASK-1", "-p", "noop", "--title", "Add logout button"],
            )

            # Verify create_workflow was called with task_title
            mock_client.create_workflow.assert_called_once()
            call_kwargs = mock_client.create_workflow.call_args.kwargs
            assert call_kwargs.get("task_title") == "Add logout button"

    def test_title_and_description_flags_passed_to_client(self, runner, tmp_path):
        """--title and --description should both be passed to API client."""
        # Create mock git worktree
        worktree = tmp_path / "repo"
        worktree.mkdir()
        (worktree / ".git").touch()

        with patch("amelia.client.cli._get_worktree_context") as mock_ctx, \
             patch("amelia.client.cli.AmeliaClient") as mock_client_class:
            mock_ctx.return_value = (str(worktree), "repo")
            mock_client = mock_client_class.return_value
            mock_client.create_workflow = AsyncMock(return_value=MagicMock(
                id="wf-123", status="pending"
            ))

            runner.invoke(
                app,
                [
                    "start", "TASK-1", "-p", "noop",
                    "--title", "Add logout button",
                    "--description", "Implement logout functionality in the navbar",
                ],
            )

            # Verify create_workflow was called with both parameters
            mock_client.create_workflow.assert_called_once()
            call_kwargs = mock_client.create_workflow.call_args.kwargs
            assert call_kwargs.get("task_title") == "Add logout button"
            assert call_kwargs.get("task_description") == "Implement logout functionality in the navbar"
