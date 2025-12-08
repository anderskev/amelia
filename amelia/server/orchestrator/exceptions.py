# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Custom exceptions for orchestrator service."""


class WorkflowConflictError(ValueError):
    """Raised when attempting to start a workflow in a worktree that already has an active workflow."""

    def __init__(self, worktree_path: str):
        """Initialize error.

        Args:
            worktree_path: The path to the conflicting worktree.
        """
        self.worktree_path = worktree_path
        super().__init__(f"Workflow already active in worktree: {worktree_path}")


class ConcurrencyLimitError(ValueError):
    """Raised when attempting to start a workflow beyond the concurrency limit."""

    def __init__(self, max_concurrent: int):
        """Initialize error.

        Args:
            max_concurrent: The maximum number of concurrent workflows allowed.
        """
        self.max_concurrent = max_concurrent
        super().__init__(
            f"Maximum {max_concurrent} concurrent workflows already running"
        )
