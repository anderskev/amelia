"""Tests for BrainstormService."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from amelia.server.models.brainstorm import BrainstormingSession, Message
from amelia.server.services.brainstorm import BrainstormService


class TestBrainstormService:
    """Test BrainstormService operations."""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create mock repository."""
        repo = MagicMock()
        repo.create_session = AsyncMock()
        repo.get_session = AsyncMock(return_value=None)
        repo.update_session = AsyncMock()
        repo.delete_session = AsyncMock()
        repo.list_sessions = AsyncMock(return_value=[])
        repo.save_message = AsyncMock()
        repo.get_messages = AsyncMock(return_value=[])
        repo.get_max_sequence = AsyncMock(return_value=0)
        repo.save_artifact = AsyncMock()
        repo.get_artifacts = AsyncMock(return_value=[])
        return repo

    @pytest.fixture
    def mock_event_bus(self) -> MagicMock:
        """Create mock event bus."""
        bus = MagicMock()
        bus.emit = MagicMock()
        return bus

    @pytest.fixture
    def service(
        self, mock_repository: MagicMock, mock_event_bus: MagicMock
    ) -> BrainstormService:
        """Create service instance."""
        return BrainstormService(mock_repository, mock_event_bus)


class TestCreateSession(TestBrainstormService):
    """Test session creation."""

    async def test_create_session_generates_id(
        self, service: BrainstormService, mock_repository: MagicMock
    ) -> None:
        """Should generate UUID for new session."""
        session = await service.create_session(
            profile_id="work", topic="Design a cache"
        )

        assert session.id is not None
        assert len(session.id) == 36  # UUID format
        mock_repository.create_session.assert_called_once()

    async def test_create_session_sets_defaults(
        self, service: BrainstormService, mock_repository: MagicMock
    ) -> None:
        """Should set default status and timestamps."""
        session = await service.create_session(profile_id="work")

        assert session.status == "active"
        assert session.created_at is not None
        assert session.updated_at is not None

    async def test_create_session_emits_event(
        self, service: BrainstormService, mock_event_bus: MagicMock
    ) -> None:
        """Should emit session created event."""
        await service.create_session(profile_id="work")

        mock_event_bus.emit.assert_called_once()
        event = mock_event_bus.emit.call_args[0][0]
        assert event.event_type.value == "brainstorm_session_created"


class TestGetSession(TestBrainstormService):
    """Test session retrieval."""

    async def test_get_session_returns_session_with_messages(
        self, service: BrainstormService, mock_repository: MagicMock
    ) -> None:
        """Should return session with messages and artifacts."""
        now = datetime.now(UTC)
        mock_session = BrainstormingSession(
            id="sess-1", profile_id="work", status="active",
            created_at=now, updated_at=now,
        )
        mock_repository.get_session.return_value = mock_session
        mock_repository.get_messages.return_value = [
            Message(
                id="msg-1", session_id="sess-1", sequence=1,
                role="user", content="Hello", created_at=now,
            )
        ]
        mock_repository.get_artifacts.return_value = []

        result = await service.get_session_with_history("sess-1")

        assert result is not None
        assert result["session"].id == "sess-1"
        assert len(result["messages"]) == 1
        assert result["artifacts"] == []

    async def test_get_session_not_found(
        self, service: BrainstormService, mock_repository: MagicMock
    ) -> None:
        """Should return None for non-existent session."""
        mock_repository.get_session.return_value = None

        result = await service.get_session_with_history("nonexistent")

        assert result is None


class TestDeleteSession(TestBrainstormService):
    """Test session deletion."""

    async def test_delete_session(
        self, service: BrainstormService, mock_repository: MagicMock
    ) -> None:
        """Should delete session."""
        await service.delete_session("sess-1")
        mock_repository.delete_session.assert_called_once_with("sess-1")


class TestUpdateSessionStatus(TestBrainstormService):
    """Test session status updates."""

    async def test_update_status(
        self, service: BrainstormService, mock_repository: MagicMock
    ) -> None:
        """Should update session status."""
        now = datetime.now(UTC)
        mock_session = BrainstormingSession(
            id="sess-1", profile_id="work", status="active",
            created_at=now, updated_at=now,
        )
        mock_repository.get_session.return_value = mock_session

        await service.update_session_status("sess-1", "ready_for_handoff")

        mock_repository.update_session.assert_called_once()
        updated = mock_repository.update_session.call_args[0][0]
        assert updated.status == "ready_for_handoff"

    async def test_update_status_session_not_found(
        self, service: BrainstormService, mock_repository: MagicMock
    ) -> None:
        """Should raise error if session not found."""
        mock_repository.get_session.return_value = None

        with pytest.raises(ValueError, match="Session not found"):
            await service.update_session_status("nonexistent", "completed")
