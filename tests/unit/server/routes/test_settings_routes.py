# tests/unit/server/routes/test_settings_routes.py
"""Tests for settings API routes."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from amelia.server.database import ServerSettings
from amelia.server.database.profile_repository import ProfileRecord
from amelia.server.dependencies import get_profile_repository
from amelia.server.routes.settings import get_settings_repository, router


@pytest.fixture
def mock_repo():
    """Create mock settings repository."""
    repo = MagicMock()
    repo.get_server_settings = AsyncMock()
    repo.update_server_settings = AsyncMock()
    return repo


@pytest.fixture
def app(mock_repo):
    """Create test FastAPI app with settings router."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_settings_repository] = lambda: mock_repo
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestSettingsRoutes:
    """Tests for /api/settings endpoints."""

    def test_get_server_settings(self, client, mock_repo):
        """GET /api/settings returns current settings."""
        mock_settings = ServerSettings(
            log_retention_days=30,
            log_retention_max_events=100000,
            trace_retention_days=7,
            checkpoint_retention_days=0,
            checkpoint_path="~/.amelia/checkpoints.db",
            websocket_idle_timeout_seconds=300.0,
            workflow_start_timeout_seconds=60.0,
            max_concurrent=5,
            stream_tool_results=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        mock_repo.get_server_settings.return_value = mock_settings

        response = client.get("/api/settings")
        assert response.status_code == 200
        data = response.json()
        assert data["log_retention_days"] == 30
        assert data["max_concurrent"] == 5

    def test_update_server_settings(self, client, mock_repo):
        """PUT /api/settings updates settings."""
        # Return updated settings
        mock_repo.update_server_settings.return_value = ServerSettings(
            log_retention_days=60,
            log_retention_max_events=100000,
            trace_retention_days=7,
            checkpoint_retention_days=0,
            checkpoint_path="~/.amelia/checkpoints.db",
            websocket_idle_timeout_seconds=300.0,
            workflow_start_timeout_seconds=60.0,
            max_concurrent=10,
            stream_tool_results=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        response = client.put(
            "/api/settings",
            json={"log_retention_days": 60, "max_concurrent": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["log_retention_days"] == 60
        assert data["max_concurrent"] == 10


@pytest.fixture
def mock_profile_repo():
    """Create mock profile repository."""
    repo = MagicMock()
    repo.list_profiles = AsyncMock()
    repo.create_profile = AsyncMock()
    repo.get_profile = AsyncMock()
    repo.update_profile = AsyncMock()
    repo.delete_profile = AsyncMock()
    repo.set_active = AsyncMock()
    return repo


@pytest.fixture
def profile_app(mock_repo, mock_profile_repo):
    """Create test FastAPI app with both settings and profile dependencies."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_settings_repository] = lambda: mock_repo
    app.dependency_overrides[get_profile_repository] = lambda: mock_profile_repo
    return app


@pytest.fixture
def profile_client(profile_app):
    """Create test client for profile endpoints."""
    return TestClient(profile_app)


def make_profile_record(
    id: str = "test-profile",
    driver: str = "cli:claude",
    model: str = "opus",
    validator_model: str = "haiku",
    tracker: str = "noop",
    working_dir: str = "/path/to/repo",
    is_active: bool = False,
) -> ProfileRecord:
    """Create a ProfileRecord for testing."""
    return ProfileRecord(
        id=id,
        driver=driver,
        model=model,
        validator_model=validator_model,
        tracker=tracker,
        working_dir=working_dir,
        is_active=is_active,
    )


class TestProfileRoutes:
    """Tests for /api/profiles endpoints."""

    def test_list_profiles(self, profile_client, mock_profile_repo):
        """GET /api/profiles returns all profiles."""
        mock_profile_repo.list_profiles.return_value = [
            make_profile_record(id="dev", is_active=True),
            make_profile_record(id="prod", driver="api:openrouter"),
        ]

        response = profile_client.get("/api/profiles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "dev"
        assert data[0]["is_active"] is True
        assert data[1]["id"] == "prod"
        assert data[1]["driver"] == "api:openrouter"

    def test_list_profiles_empty(self, profile_client, mock_profile_repo):
        """GET /api/profiles returns empty list when no profiles."""
        mock_profile_repo.list_profiles.return_value = []

        response = profile_client.get("/api/profiles")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_profile(self, profile_client, mock_profile_repo):
        """POST /api/profiles creates new profile."""
        mock_profile_repo.create_profile.return_value = make_profile_record(
            id="new-profile"
        )

        response = profile_client.post(
            "/api/profiles",
            json={
                "id": "new-profile",
                "driver": "cli:claude",
                "model": "opus",
                "validator_model": "haiku",
                "working_dir": "/path/to/repo",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "new-profile"
        assert data["driver"] == "cli:claude"
        assert data["is_active"] is False

    def test_create_profile_with_all_fields(self, profile_client, mock_profile_repo):
        """POST /api/profiles creates profile with all optional fields."""
        mock_profile_repo.create_profile.return_value = ProfileRecord(
            id="full-profile",
            driver="api:openrouter",
            model="gpt-4",
            validator_model="gpt-3.5-turbo",
            tracker="jira",
            working_dir="/custom/path",
            plan_output_dir="custom/plans",
            plan_path_pattern="custom/{date}.md",
            max_review_iterations=5,
            max_task_review_iterations=10,
            auto_approve_reviews=True,
        )

        response = profile_client.post(
            "/api/profiles",
            json={
                "id": "full-profile",
                "driver": "api:openrouter",
                "model": "gpt-4",
                "validator_model": "gpt-3.5-turbo",
                "tracker": "jira",
                "working_dir": "/custom/path",
                "plan_output_dir": "custom/plans",
                "plan_path_pattern": "custom/{date}.md",
                "max_review_iterations": 5,
                "max_task_review_iterations": 10,
                "auto_approve_reviews": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["tracker"] == "jira"
        assert data["plan_output_dir"] == "custom/plans"
        assert data["max_review_iterations"] == 5
        assert data["auto_approve_reviews"] is True

    def test_get_profile(self, profile_client, mock_profile_repo):
        """GET /api/profiles/{id} returns profile."""
        mock_profile_repo.get_profile.return_value = make_profile_record(
            id="dev", is_active=True
        )

        response = profile_client.get("/api/profiles/dev")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "dev"
        assert data["is_active"] is True

    def test_get_profile_not_found(self, profile_client, mock_profile_repo):
        """GET /api/profiles/{id} returns 404 for missing profile."""
        mock_profile_repo.get_profile.return_value = None

        response = profile_client.get("/api/profiles/nonexistent")
        assert response.status_code == 404
        assert response.json()["detail"] == "Profile not found"

    def test_update_profile(self, profile_client, mock_profile_repo):
        """PUT /api/profiles/{id} updates profile."""
        mock_profile_repo.update_profile.return_value = ProfileRecord(
            id="dev",
            driver="cli:claude",
            model="sonnet",
            validator_model="haiku",
            tracker="noop",
            working_dir="/path/to/repo",
        )

        response = profile_client.put(
            "/api/profiles/dev",
            json={"model": "sonnet"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "sonnet"

    def test_update_profile_multiple_fields(self, profile_client, mock_profile_repo):
        """PUT /api/profiles/{id} updates multiple fields."""
        mock_profile_repo.update_profile.return_value = ProfileRecord(
            id="dev",
            driver="api:openrouter",
            model="gpt-4",
            validator_model="gpt-3.5-turbo",
            tracker="jira",
            working_dir="/new/path",
            max_review_iterations=10,
        )

        response = profile_client.put(
            "/api/profiles/dev",
            json={
                "driver": "api:openrouter",
                "model": "gpt-4",
                "tracker": "jira",
                "max_review_iterations": 10,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["driver"] == "api:openrouter"
        assert data["tracker"] == "jira"
        assert data["max_review_iterations"] == 10

    def test_update_profile_not_found(self, profile_client, mock_profile_repo):
        """PUT /api/profiles/{id} returns 404 for missing profile."""
        mock_profile_repo.update_profile.side_effect = ValueError(
            "Profile nonexistent not found"
        )

        response = profile_client.put(
            "/api/profiles/nonexistent",
            json={"model": "sonnet"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_profile(self, profile_client, mock_profile_repo):
        """DELETE /api/profiles/{id} deletes profile."""
        mock_profile_repo.delete_profile.return_value = True

        response = profile_client.delete("/api/profiles/dev")
        assert response.status_code == 204

    def test_delete_profile_not_found(self, profile_client, mock_profile_repo):
        """DELETE /api/profiles/{id} returns 404 for missing profile."""
        mock_profile_repo.delete_profile.return_value = False

        response = profile_client.delete("/api/profiles/nonexistent")
        assert response.status_code == 404
        assert response.json()["detail"] == "Profile not found"

    def test_activate_profile(self, profile_client, mock_profile_repo):
        """POST /api/profiles/{id}/activate sets profile as active."""
        mock_profile_repo.get_profile.return_value = make_profile_record(
            id="dev", is_active=True
        )

        response = profile_client.post("/api/profiles/dev/activate")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "dev"
        assert data["is_active"] is True
        mock_profile_repo.set_active.assert_called_once_with("dev")

    def test_activate_profile_not_found(self, profile_client, mock_profile_repo):
        """POST /api/profiles/{id}/activate returns 404 for missing profile."""
        mock_profile_repo.set_active.side_effect = ValueError(
            "Profile nonexistent not found"
        )

        response = profile_client.post("/api/profiles/nonexistent/activate")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
