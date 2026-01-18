"""Service layer for brainstorming operations.

Handles business logic for brainstorming sessions, coordinating
between the repository, event bus, and Claude driver.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from amelia.server.database.brainstorm_repository import BrainstormRepository
from amelia.server.events.bus import EventBus
from amelia.server.models.brainstorm import (
    BrainstormingSession,
    SessionStatus,
)
from amelia.server.models.events import EventType, WorkflowEvent


class BrainstormService:
    """Service for brainstorming session management.

    Coordinates session lifecycle, message handling, and event emission.

    Attributes:
        _repository: Database repository for persistence.
        _event_bus: Event bus for WebSocket broadcasting.
    """

    def __init__(
        self,
        repository: BrainstormRepository,
        event_bus: EventBus,
    ) -> None:
        """Initialize service.

        Args:
            repository: Database repository.
            event_bus: Event bus for broadcasting.
        """
        self._repository = repository
        self._event_bus = event_bus

    async def create_session(
        self,
        profile_id: str,
        topic: str | None = None,
    ) -> BrainstormingSession:
        """Create a new brainstorming session.

        Args:
            profile_id: Profile/project for the session.
            topic: Optional initial topic.

        Returns:
            Created session.
        """
        now = datetime.now(UTC)
        session = BrainstormingSession(
            id=str(uuid4()),
            profile_id=profile_id,
            status="active",
            topic=topic,
            created_at=now,
            updated_at=now,
        )

        await self._repository.create_session(session)

        # Emit session created event
        event = WorkflowEvent(
            id=str(uuid4()),
            workflow_id=session.id,  # Use session_id as workflow_id for events
            sequence=0,
            timestamp=now,
            agent="brainstormer",
            event_type=EventType.BRAINSTORM_SESSION_CREATED,
            message=f"Brainstorming session created: {topic or 'No topic'}",
            data={"session_id": session.id, "profile_id": profile_id, "topic": topic},
        )
        self._event_bus.emit(event)

        return session

    async def get_session_with_history(
        self, session_id: str
    ) -> dict[str, Any] | None:
        """Get session with messages and artifacts.

        Args:
            session_id: Session to retrieve.

        Returns:
            Dict with session, messages, and artifacts, or None if not found.
        """
        session = await self._repository.get_session(session_id)
        if session is None:
            return None

        messages = await self._repository.get_messages(session_id)
        artifacts = await self._repository.get_artifacts(session_id)

        return {
            "session": session,
            "messages": messages,
            "artifacts": artifacts,
        }

    async def list_sessions(
        self,
        profile_id: str | None = None,
        status: SessionStatus | None = None,
        limit: int = 50,
    ) -> list[BrainstormingSession]:
        """List sessions with optional filters.

        Args:
            profile_id: Filter by profile.
            status: Filter by status.
            limit: Maximum sessions to return.

        Returns:
            List of sessions.
        """
        return await self._repository.list_sessions(
            profile_id=profile_id, status=status, limit=limit
        )

    async def delete_session(self, session_id: str) -> None:
        """Delete a session.

        Args:
            session_id: Session to delete.
        """
        await self._repository.delete_session(session_id)

    async def update_session_status(
        self, session_id: str, status: SessionStatus
    ) -> BrainstormingSession:
        """Update session status.

        Args:
            session_id: Session to update.
            status: New status.

        Returns:
            Updated session.

        Raises:
            ValueError: If session not found.
        """
        session = await self._repository.get_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        session.status = status
        session.updated_at = datetime.now(UTC)
        await self._repository.update_session(session)

        return session

    async def update_driver_session_id(
        self, session_id: str, driver_session_id: str
    ) -> None:
        """Update the Claude driver session ID.

        Args:
            session_id: Session to update.
            driver_session_id: New driver session ID.

        Raises:
            ValueError: If session not found.
        """
        session = await self._repository.get_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        session.driver_session_id = driver_session_id
        session.updated_at = datetime.now(UTC)
        await self._repository.update_session(session)
