# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Tests for core state models."""

from amelia.core.state import ExecutionState, TaskDAG
from amelia.core.types import Profile


def test_execution_state_workflow_status_default():
    """ExecutionState workflow_status should default to 'running'."""
    profile = Profile(name="test", driver="cli:claude")
    state = ExecutionState(profile=profile)
    assert state.workflow_status == "running"


def test_execution_state_workflow_status_failed():
    """ExecutionState should accept workflow_status='failed'."""
    profile = Profile(name="test", driver="cli:claude")
    state = ExecutionState(profile=profile, workflow_status="failed")
    assert state.workflow_status == "failed"


class TestTaskDAGGetTask:
    """Tests for TaskDAG.get_task() method."""

    def test_get_task_returns_correct_task(self, mock_task_factory):
        """get_task should return the task with matching ID."""
        task1 = mock_task_factory(id="task-1", description="First task")
        task2 = mock_task_factory(id="task-2", description="Second task")
        dag = TaskDAG(tasks=[task1, task2], original_issue="Test issue")

        result = dag.get_task("task-2")

        assert result is not None
        assert result.id == "task-2"
        assert result.description == "Second task"

    def test_get_task_returns_none_for_missing_id(self, mock_task_factory):
        """get_task should return None when task ID doesn't exist."""
        task1 = mock_task_factory(id="task-1", description="First task")
        dag = TaskDAG(tasks=[task1], original_issue="Test issue")

        result = dag.get_task("nonexistent")

        assert result is None

    def test_get_task_on_empty_dag(self):
        """get_task should return None on empty TaskDAG."""
        dag = TaskDAG(tasks=[], original_issue="Empty")

        result = dag.get_task("any-id")

        assert result is None


def test_execution_state_accepts_design_field():
    """ExecutionState should accept optional design field."""
    from amelia.core.types import Design

    profile = Profile(name="test", driver="cli:claude")
    design = Design(
        title="Test Design",
        goal="Test goal",
        architecture="Test architecture",
        tech_stack=["Python"],
        components=["Component A"],
        raw_content="# Test Design\n\nRaw content here",
    )
    state = ExecutionState(profile=profile, design=design)

    assert state.design is not None
    assert state.design.title == "Test Design"


def test_execution_state_design_defaults_to_none():
    """ExecutionState design should default to None."""
    profile = Profile(name="test", driver="cli:claude")
    state = ExecutionState(profile=profile)

    assert state.design is None
