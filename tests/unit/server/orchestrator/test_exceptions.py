"""Unit tests for orchestrator exceptions."""
from amelia.server.orchestrator.exceptions import (
    ConcurrencyLimitError,
    WorkflowConflictError,
)


def test_workflow_conflict_error():
    """WorkflowConflictError should have custom message."""
    error = WorkflowConflictError("/path/to/worktree")
    assert "already active" in str(error).lower()
    assert "/path/to/worktree" in str(error)


def test_concurrency_limit_error():
    """ConcurrencyLimitError should have custom message."""
    error = ConcurrencyLimitError(5)
    assert "maximum" in str(error).lower()
    assert "5" in str(error)
    assert error.max_concurrent == 5
