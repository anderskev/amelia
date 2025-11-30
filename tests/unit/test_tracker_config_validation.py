# tests/unit/test_tracker_config_validation.py
"""Tests for tracker configuration validation."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from amelia.core.exceptions import ConfigurationError
from amelia.trackers.github import GithubTracker
from amelia.trackers.jira import JiraTracker


class TestJiraTrackerConfigValidation:
    """Test JiraTracker configuration validation."""

    @pytest.mark.parametrize(
        "missing_var,present_vars",
        [
            (
                "JIRA_URL",
                {"JIRA_EMAIL": "test@example.com", "JIRA_API_TOKEN": "token123"},
            ),
            (
                "JIRA_EMAIL",
                {"JIRA_URL": "https://example.atlassian.net", "JIRA_API_TOKEN": "token123"},
            ),
            (
                "JIRA_API_TOKEN",
                {"JIRA_URL": "https://example.atlassian.net", "JIRA_EMAIL": "test@example.com"},
            ),
        ],
        ids=["missing_url", "missing_email", "missing_token"]
    )
    def test_missing_jira_env_var_raises_config_error(
        self, monkeypatch, missing_var, present_vars
    ):
        """Missing JIRA environment variables should raise ConfigurationError."""
        monkeypatch.delenv(missing_var, raising=False)
        for key, value in present_vars.items():
            monkeypatch.setenv(key, value)

        with pytest.raises(ConfigurationError, match=missing_var):
            JiraTracker()

    def test_all_jira_vars_present_succeeds(self, monkeypatch):
        """With all env vars set, JiraTracker should initialize."""
        monkeypatch.setenv("JIRA_URL", "https://example.atlassian.net")
        monkeypatch.setenv("JIRA_EMAIL", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "token123")

        tracker = JiraTracker()
        assert tracker is not None


class TestGithubTrackerConfigValidation:
    """Test GithubTracker configuration validation."""

    def test_gh_cli_not_installed_raises_config_error(self):
        """Missing gh CLI should raise ConfigurationError."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("gh not found")

            with pytest.raises(ConfigurationError, match="gh.*not found"):
                GithubTracker()

    def test_gh_cli_not_authenticated_raises_config_error(self):
        """Unauthenticated gh CLI should raise ConfigurationError."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "You are not logged into any GitHub hosts"
            mock_run.return_value = mock_result

            with pytest.raises(ConfigurationError, match="not authenticated"):
                GithubTracker()

    def test_gh_cli_authenticated_succeeds(self):
        """Authenticated gh CLI should allow initialization."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Logged in to github.com as user"
            mock_run.return_value = mock_result

            tracker = GithubTracker()
            assert tracker is not None
