import pytest
from pydantic import ValidationError

from amelia.core.state import TaskDAG


def test_task_dag_basic_construction(mock_task_factory):
    task1 = mock_task_factory(id="1")
    task2 = mock_task_factory(id="2")
    task3 = mock_task_factory(id="3", dependencies=["1", "2"])

    dag = TaskDAG(tasks=[task1, task2, task3], original_issue="ISSUE-123")

    assert len(dag.tasks) == 3
    assert dag.original_issue == "ISSUE-123"
    assert task3.dependencies == ["1", "2"]


def test_task_dag_dependency_resolution(mock_task_factory):
    task1 = mock_task_factory(id="1")
    task2 = mock_task_factory(id="2", dependencies=["1"])
    task3 = mock_task_factory(id="3", dependencies=["1", "2"])
    dag = TaskDAG(tasks=[task1, task2, task3], original_issue="ISSUE-125")

    ready_tasks = dag.get_ready_tasks()
    assert {t.id for t in ready_tasks} == {"1"}

    task1.status = "completed"
    ready_tasks = dag.get_ready_tasks()
    assert {t.id for t in ready_tasks} == {"2"}

    task2.status = "completed"
    ready_tasks = dag.get_ready_tasks()
    assert {t.id for t in ready_tasks} == {"3"}


@pytest.mark.parametrize(
    "tasks,pattern",
    [
        (
            [
                lambda f: f(id="A", dependencies=["C"]),
                lambda f: f(id="B", dependencies=["A"]),
                lambda f: f(id="C", dependencies=["B"]),
            ],
            "Cyclic dependency detected",
        ),
        ([lambda f: f(id="1", dependencies=["non-existent"])], "Task 'non-existent' not found"),
    ],
)
def test_task_dag_invalid_graphs(mock_task_factory, tasks, pattern):
    materialized_tasks = [factory(mock_task_factory) for factory in tasks]
    with pytest.raises(ValidationError, match=pattern):
        TaskDAG(tasks=materialized_tasks, original_issue="ISSUE-INVALID")
