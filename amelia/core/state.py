from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from amelia.core.types import Issue, Profile


TaskStatus = Literal["pending", "in_progress", "completed", "failed"]
Severity = Literal["low", "medium", "high", "critical"]


class TaskStep(BaseModel):
    """A single step within a task (2-5 minutes of work)."""
    description: str
    code: str | None = None
    command: str | None = None
    expected_output: str | None = None


class FileOperation(BaseModel):
    """A file to be created, modified, or tested."""
    operation: Literal["create", "modify", "test"]
    path: str
    line_range: str | None = None


class Task(BaseModel):
    """Task with TDD structure."""
    id: str
    description: str
    status: TaskStatus = "pending"
    dependencies: list[str] = Field(default_factory=list)
    files: list[FileOperation] = Field(default_factory=list)
    steps: list[TaskStep] = Field(default_factory=list)
    commit_message: str | None = None

class TaskDAG(BaseModel):
    tasks: list[Task]
    original_issue: str

    @field_validator("tasks")
    @classmethod
    def validate_task_graph(cls, tasks: list[Task]) -> list[Task]:
        """Validate task graph: check dependencies exist and no cycles."""
        task_ids = {t.id for t in tasks}

        # Check all dependencies exist BEFORE checking for cycles
        for task in tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    raise ValueError(f"Task '{dep}' not found")

        # Check for cycles using DFS
        adjacency = {t.id: t.dependencies for t in tasks}
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {tid: WHITE for tid in task_ids}

        def dfs(node: str) -> bool:
            """Returns True if cycle detected."""
            color[node] = GRAY
            for neighbor in adjacency.get(node, []):
                if color[neighbor] == GRAY:
                    return True  # Back edge = cycle
                if color[neighbor] == WHITE and dfs(neighbor):
                    return True
            color[node] = BLACK
            return False

        for tid in task_ids:
            if color[tid] == WHITE and dfs(tid):
                raise ValueError("Cyclic dependency detected")

        return tasks

    def get_ready_tasks(self) -> list[Task]:
        """Return tasks that are pending and have all dependencies completed."""
        completed_ids = {t.id for t in self.tasks if t.status == "completed"}
        ready = []
        for task in self.tasks:
            if task.status == "pending" and all(dep in completed_ids for dep in task.dependencies):
                ready.append(task)
        return ready

class ReviewResult(BaseModel):
    reviewer_persona: str
    approved: bool
    comments: list[str]
    severity: Severity

class AgentMessage(BaseModel):
    role: str
    content: str
    tool_calls: list[Any] | None = None

class ExecutionState(BaseModel):
    profile: Profile
    issue: Issue | None = None
    plan: TaskDAG | None = None
    current_task_id: str | None = None
    human_approved: bool | None = None # Field to store human approval status
    review_results: list[ReviewResult] = Field(default_factory=list)
    messages: list[AgentMessage] = Field(default_factory=list)
    code_changes_for_review: str | None = None # For local review or specific review contexts
