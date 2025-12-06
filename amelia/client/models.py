"""Pydantic models for API requests and responses."""
from datetime import datetime

from pydantic import BaseModel, Field


class CreateWorkflowRequest(BaseModel):
    """Request to create a new workflow."""

    issue_id: str = Field(..., min_length=1, max_length=100)
    worktree_path: str = Field(..., min_length=1, max_length=4096)
    worktree_name: str | None = Field(default=None, max_length=255)
    profile: str | None = Field(default=None, max_length=64)


class RejectWorkflowRequest(BaseModel):
    """Request to reject a workflow plan."""

    feedback: str = Field(..., min_length=1, max_length=1000)


class WorkflowResponse(BaseModel):
    """Workflow detail response."""

    id: str
    issue_id: str
    status: str
    worktree_path: str
    worktree_name: str | None = None
    profile: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    error: str | None = None


class WorkflowSummary(BaseModel):
    """Workflow summary for list responses."""

    id: str
    issue_id: str
    status: str
    worktree_path: str
    worktree_name: str | None = None
    started_at: datetime
    current_stage: str | None = None


class WorkflowListResponse(BaseModel):
    """Response for listing workflows."""

    workflows: list[WorkflowSummary]
    total: int
    cursor: str | None = None
