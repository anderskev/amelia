"""API routes for brainstorming sessions.

Provides endpoints for session lifecycle management and chat functionality.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from amelia.server.models.brainstorm import (
    Artifact,
    BrainstormingSession,
    Message,
    SessionStatus,
)
from amelia.server.services.brainstorm import BrainstormService


router = APIRouter(tags=["brainstorm"])


# Dependency placeholder - will be properly wired in main.py
def get_brainstorm_service() -> BrainstormService:
    """Get BrainstormService dependency.

    Returns:
        BrainstormService instance.

    Raises:
        RuntimeError: If service not initialized.
    """
    raise RuntimeError("BrainstormService not initialized")


# Request/Response Models
class CreateSessionRequest(BaseModel):
    """Request to create a new brainstorming session."""

    profile_id: str
    topic: str | None = None


class SessionWithHistoryResponse(BaseModel):
    """Response containing session with messages and artifacts."""

    session: BrainstormingSession
    messages: list[Message]
    artifacts: list[Artifact]


# Session Lifecycle Endpoints
@router.post(
    "/sessions",
    status_code=status.HTTP_201_CREATED,
    response_model=BrainstormingSession,
)
async def create_session(
    request: CreateSessionRequest,
    service: BrainstormService = Depends(get_brainstorm_service),
) -> BrainstormingSession:
    """Create a new brainstorming session.

    Args:
        request: Session creation request.
        service: Brainstorm service dependency.

    Returns:
        Created session.
    """
    return await service.create_session(
        profile_id=request.profile_id,
        topic=request.topic,
    )


@router.get("/sessions", response_model=list[BrainstormingSession])
async def list_sessions(
    profile_id: Annotated[str | None, Query()] = None,
    status: Annotated[SessionStatus | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    service: BrainstormService = Depends(get_brainstorm_service),
) -> list[BrainstormingSession]:
    """List brainstorming sessions.

    Args:
        profile_id: Filter by profile.
        status: Filter by status.
        limit: Maximum sessions to return.
        service: Brainstorm service dependency.

    Returns:
        List of sessions.
    """
    return await service.list_sessions(
        profile_id=profile_id, status=status, limit=limit
    )


@router.get("/sessions/{session_id}", response_model=SessionWithHistoryResponse)
async def get_session(
    session_id: str,
    service: BrainstormService = Depends(get_brainstorm_service),
) -> SessionWithHistoryResponse:
    """Get session with messages and artifacts.

    Args:
        session_id: Session to retrieve.
        service: Brainstorm service dependency.

    Returns:
        Session with history.

    Raises:
        HTTPException: 404 if session not found.
    """
    result = await service.get_session_with_history(session_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )
    return SessionWithHistoryResponse(**result)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    service: BrainstormService = Depends(get_brainstorm_service),
) -> None:
    """Delete a brainstorming session.

    Args:
        session_id: Session to delete.
        service: Brainstorm service dependency.
    """
    await service.delete_session(session_id)
