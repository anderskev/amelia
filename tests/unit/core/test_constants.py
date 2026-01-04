"""Tests for amelia.core.constants."""

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
