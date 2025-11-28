from unittest.mock import patch

from amelia.trackers.jira import JiraTracker


def test_jira_get_issue(monkeypatch):
    # Set required env vars for JiraTracker initialization
    monkeypatch.setenv("JIRA_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "test@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "token123")

    tracker = JiraTracker()
    with patch("httpx.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "key": "PROJ-123",
            "fields": {"summary": "Test Issue", "description": "Desc"}
        }
        issue = tracker.get_issue("PROJ-123")
        assert issue.title == "Test Issue"
        assert issue.description == "Desc"
