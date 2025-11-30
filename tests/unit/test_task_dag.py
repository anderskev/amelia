import pytest
from pydantic import ValidationError

from amelia.core.state import TaskDAG


def test_task_dag_creation(mock_task_factory):
    task1 = mock_task_factory(id="1")
    task2 = mock_task_factory(id="2")
    dag = TaskDAG(tasks=[task1, task2], original_issue="ISSUE-123")
    assert len(dag.tasks) == 2
    assert dag.original_issue == "ISSUE-123"


def test_task_dag_with_dependencies(mock_task_factory):
    task1 = mock_task_factory(id="1")
    task2 = mock_task_factory(id="2", dependencies=["1"])
    task3 = mock_task_factory(id="3", dependencies=["1", "2"])
    _dag = TaskDAG(tasks=[task1, task2, task3], original_issue="ISSUE-124")
    assert task3.dependencies == ["1", "2"]


def test_task_dag_cycle_detection(mock_task_factory):
    task_a = mock_task_factory(id="A", dependencies=["C"])
    task_b = mock_task_factory(id="B", dependencies=["A"])
    task_c = mock_task_factory(id="C", dependencies=["B"])

    with pytest.raises(ValidationError, match="Cyclic dependency detected"):
        TaskDAG(tasks=[task_a, task_b, task_c], original_issue="ISSUE-CYCLE")


def test_task_dag_dependency_resolution(mock_task_factory):
    task1 = mock_task_factory(id="1")
    task2 = mock_task_factory(id="2", dependencies=["1"])
    task3 = mock_task_factory(id="3", dependencies=["1", "2"])
    dag = TaskDAG(tasks=[task1, task2, task3], original_issue="ISSUE-125")

    ready_tasks = dag.get_ready_tasks()
    assert set(t.id for t in ready_tasks) == {"1"}

    task1.status = "completed"
    ready_tasks = dag.get_ready_tasks()
    assert set(t.id for t in ready_tasks) == {"2"}

    task2.status = "completed"
    ready_tasks = dag.get_ready_tasks()
    assert set(t.id for t in ready_tasks) == {"3"}


def test_task_dag_invalid_graph_handling(mock_task_factory):
    task1 = mock_task_factory(id="1", dependencies=["non-existent"])
    with pytest.raises(ValidationError, match="Task 'non-existent' not found"):
        TaskDAG(tasks=[task1], original_issue="ISSUE-INVALID")
