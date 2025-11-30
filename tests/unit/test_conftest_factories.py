"""Tests for conftest.py factory fixtures."""

import pytest

from amelia.core.types import Issue


def test_issue_factory_defaults(mock_issue_factory):
    """Test that issue_factory creates Issue with sensible defaults."""
    issue = mock_issue_factory()
    assert issue.id == "TEST-123"
    assert issue.title == "Test Issue"
    assert issue.status == "open"


def test_issue_factory_custom(mock_issue_factory):
    """Test that issue_factory accepts custom values."""
    issue = mock_issue_factory(id="CUSTOM-1", title="Custom Title")
    assert issue.id == "CUSTOM-1"
    assert issue.title == "Custom Title"
