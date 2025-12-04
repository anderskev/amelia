"""Tests for WorkflowRepository."""

import pytest
from datetime import datetime, UTC
from uuid import uuid4

from amelia.server.database.repository import WorkflowRepository
from amelia.server.models.state import ServerExecutionState, InvalidStateTransitionError


class TestWorkflowRepository:
    """Tests for WorkflowRepository CRUD operations."""

    @pytest.fixture
    async def repository(self, db_with_schema):
        """WorkflowRepository instance."""
        return WorkflowRepository(db_with_schema)

    @pytest.mark.asyncio
    async def test_create_workflow(self, repository):
        """Can create a workflow."""
        state = ServerExecutionState(
            id=str(uuid4()),
            issue_id="ISSUE-123",
            worktree_path="/path/to/repo",
            worktree_name="main",
        )

        await repository.create(state)

        # Verify it was created
        retrieved = await repository.get(state.id)
        assert retrieved is not None
        assert retrieved.issue_id == "ISSUE-123"

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self, repository):
        """Getting nonexistent workflow returns None."""
        result = await repository.get("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_worktree(self, repository):
        """Can get active workflow by worktree path."""
        state = ServerExecutionState(
            id=str(uuid4()),
            issue_id="ISSUE-123",
            worktree_path="/path/to/repo",
            worktree_name="main",
            workflow_status="in_progress",
        )
        await repository.create(state)

        retrieved = await repository.get_by_worktree("/path/to/repo")
        assert retrieved is not None
        assert retrieved.id == state.id

    @pytest.mark.asyncio
    async def test_get_by_worktree_only_active(self, repository):
        """get_by_worktree only returns active workflows."""
        # Create completed workflow
        completed = ServerExecutionState(
            id=str(uuid4()),
            issue_id="ISSUE-1",
            worktree_path="/path/to/repo",
            worktree_name="main",
            workflow_status="completed",
        )
        await repository.create(completed)

        # No active workflow should be found
        result = await repository.get_by_worktree("/path/to/repo")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_workflow(self, repository):
        """Can update workflow state."""
        state = ServerExecutionState(
            id=str(uuid4()),
            issue_id="ISSUE-123",
            worktree_path="/path/to/repo",
            worktree_name="main",
        )
        await repository.create(state)

        # Update status
        state.workflow_status = "in_progress"
        state.started_at = datetime.now(UTC)
        await repository.update(state)

        retrieved = await repository.get(state.id)
        assert retrieved.workflow_status == "in_progress"
        assert retrieved.started_at is not None

    @pytest.mark.asyncio
    async def test_set_status_validates_transition(self, repository):
        """set_status validates state machine transitions."""
        state = ServerExecutionState(
            id=str(uuid4()),
            issue_id="ISSUE-123",
            worktree_path="/path/to/repo",
            worktree_name="main",
            workflow_status="pending",
        )
        await repository.create(state)

        # Invalid: pending -> completed (must go through in_progress)
        with pytest.raises(InvalidStateTransitionError):
            await repository.set_status(state.id, "completed")

    @pytest.mark.asyncio
    async def test_set_status_valid_transition(self, repository):
        """set_status allows valid transitions."""
        state = ServerExecutionState(
            id=str(uuid4()),
            issue_id="ISSUE-123",
            worktree_path="/path/to/repo",
            worktree_name="main",
            workflow_status="pending",
        )
        await repository.create(state)

        await repository.set_status(state.id, "in_progress")

        retrieved = await repository.get(state.id)
        assert retrieved.workflow_status == "in_progress"

    @pytest.mark.asyncio
    async def test_set_status_with_failure_reason(self, repository):
        """set_status can set failure reason."""
        state = ServerExecutionState(
            id=str(uuid4()),
            issue_id="ISSUE-123",
            worktree_path="/path/to/repo",
            worktree_name="main",
            workflow_status="in_progress",
        )
        await repository.create(state)

        await repository.set_status(state.id, "failed", failure_reason="Something went wrong")

        retrieved = await repository.get(state.id)
        assert retrieved.workflow_status == "failed"
        assert retrieved.failure_reason == "Something went wrong"

    @pytest.mark.asyncio
    async def test_list_active_workflows(self, repository):
        """Can list all active workflows."""
        # Create various workflows
        active1 = ServerExecutionState(
            id=str(uuid4()),
            issue_id="ISSUE-1",
            worktree_path="/repo1",
            worktree_name="main",
            workflow_status="in_progress",
        )
        active2 = ServerExecutionState(
            id=str(uuid4()),
            issue_id="ISSUE-2",
            worktree_path="/repo2",
            worktree_name="feat",
            workflow_status="blocked",
        )
        completed = ServerExecutionState(
            id=str(uuid4()),
            issue_id="ISSUE-3",
            worktree_path="/repo3",
            worktree_name="old",
            workflow_status="completed",
        )

        await repository.create(active1)
        await repository.create(active2)
        await repository.create(completed)

        active = await repository.list_active()
        assert len(active) == 2
        ids = {w.id for w in active}
        assert active1.id in ids
        assert active2.id in ids

    @pytest.mark.asyncio
    async def test_count_active_workflows(self, repository):
        """Can count active workflows."""
        for i in range(3):
            state = ServerExecutionState(
                id=str(uuid4()),
                issue_id=f"ISSUE-{i}",
                worktree_path=f"/repo{i}",
                worktree_name=f"wt{i}",
                workflow_status="in_progress",
            )
            await repository.create(state)

        count = await repository.count_active()
        assert count == 3
