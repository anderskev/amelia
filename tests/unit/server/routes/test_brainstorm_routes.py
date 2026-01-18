"""Tests for brainstorming API routes."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from amelia.server.models.brainstorm import BrainstormingSession
from amelia.server.routes.brainstorm import router


class TestBrainstormRoutes:
    """Test brainstorming API endpoints."""

    @pytest.fixture
    def mock_service(self) -> MagicMock:
        """Create mock BrainstormService."""
        service = MagicMock()
        service.create_session = AsyncMock()
        service.get_session_with_history = AsyncMock()
        service.list_sessions = AsyncMock(return_value=[])
        service.delete_session = AsyncMock()
        return service

    @pytest.fixture
    def app(self, mock_service: MagicMock) -> FastAPI:
        """Create test app with mocked dependencies."""
        app = FastAPI()
        app.include_router(router, prefix="/api/brainstorm")

        # Override dependency
        from amelia.server.routes.brainstorm import get_brainstorm_service
        app.dependency_overrides[get_brainstorm_service] = lambda: mock_service

        return app

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        """Create test client."""
        return TestClient(app)


class TestCreateSession(TestBrainstormRoutes):
    """Test POST /api/brainstorm/sessions."""

    def test_create_session_minimal(
        self, client: TestClient, mock_service: MagicMock
    ) -> None:
        """Should create session with minimal fields."""
        now = datetime.now(UTC)
        mock_service.create_session.return_value = BrainstormingSession(
            id="sess-123",
            profile_id="work",
            status="active",
            created_at=now,
            updated_at=now,
        )

        response = client.post(
            "/api/brainstorm/sessions",
            json={"profile_id": "work"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "sess-123"
        assert data["status"] == "active"

    def test_create_session_with_topic(
        self, client: TestClient, mock_service: MagicMock
    ) -> None:
        """Should create session with topic."""
        now = datetime.now(UTC)
        mock_service.create_session.return_value = BrainstormingSession(
            id="sess-123",
            profile_id="work",
            status="active",
            topic="Design a cache",
            created_at=now,
            updated_at=now,
        )

        response = client.post(
            "/api/brainstorm/sessions",
            json={"profile_id": "work", "topic": "Design a cache"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["topic"] == "Design a cache"


class TestListSessions(TestBrainstormRoutes):
    """Test GET /api/brainstorm/sessions."""

    def test_list_sessions_empty(
        self, client: TestClient, mock_service: MagicMock
    ) -> None:
        """Should return empty list when no sessions."""
        response = client.get("/api/brainstorm/sessions")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_sessions_with_filter(
        self, client: TestClient, mock_service: MagicMock
    ) -> None:
        """Should pass filters to service."""
        now = datetime.now(UTC)
        mock_service.list_sessions.return_value = [
            BrainstormingSession(
                id="sess-1", profile_id="work", status="active",
                created_at=now, updated_at=now,
            )
        ]

        response = client.get(
            "/api/brainstorm/sessions",
            params={"profile_id": "work", "status": "active"},
        )

        assert response.status_code == 200
        mock_service.list_sessions.assert_called_once_with(
            profile_id="work", status="active", limit=50
        )


class TestGetSession(TestBrainstormRoutes):
    """Test GET /api/brainstorm/sessions/{id}."""

    def test_get_session_found(
        self, client: TestClient, mock_service: MagicMock
    ) -> None:
        """Should return session with history."""
        now = datetime.now(UTC)
        mock_service.get_session_with_history.return_value = {
            "session": BrainstormingSession(
                id="sess-123", profile_id="work", status="active",
                created_at=now, updated_at=now,
            ),
            "messages": [],
            "artifacts": [],
        }

        response = client.get("/api/brainstorm/sessions/sess-123")

        assert response.status_code == 200
        data = response.json()
        assert data["session"]["id"] == "sess-123"

    def test_get_session_not_found(
        self, client: TestClient, mock_service: MagicMock
    ) -> None:
        """Should return 404 for non-existent session."""
        mock_service.get_session_with_history.return_value = None

        response = client.get("/api/brainstorm/sessions/nonexistent")

        assert response.status_code == 404


class TestDeleteSession(TestBrainstormRoutes):
    """Test DELETE /api/brainstorm/sessions/{id}."""

    def test_delete_session(
        self, client: TestClient, mock_service: MagicMock
    ) -> None:
        """Should delete session."""
        response = client.delete("/api/brainstorm/sessions/sess-123")

        assert response.status_code == 204
        mock_service.delete_session.assert_called_once_with("sess-123")
