"""Test static file serving for dashboard."""
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from amelia.server.main import app


class TestDashboardServing:
    """Tests for dashboard static file serving."""

    @pytest.fixture
    def client(self) -> Generator[TestClient, None, None]:
        """FastAPI test client."""
        with TestClient(app) as test_client:
            yield test_client

    def test_root_returns_dashboard_or_message(self, client: TestClient) -> None:
        """GET / returns dashboard index.html or helpful message."""
        response = client.get("/")

        # Should return 200 in either case
        assert response.status_code == 200

        content_type = response.headers.get("content-type", "")

        if "text/html" in content_type:
            # Dashboard is built - should serve index.html
            assert b"Amelia Dashboard" in response.content
        else:
            # Dashboard not built - should return instructions JSON
            data = response.json()
            assert data["message"] == "Dashboard not built"
            assert "instructions" in data

    def test_api_routes_not_affected(self, client: TestClient) -> None:
        """API routes work normally regardless of dashboard state."""
        response = client.get("/api/health/live")

        assert response.status_code == 200
        assert response.json() == {"status": "alive"}

    def test_api_docs_accessible(self, client: TestClient) -> None:
        """Swagger docs still accessible."""
        response = client.get("/api/docs")

        assert response.status_code == 200

    def test_unknown_api_route_returns_404(self, client: TestClient) -> None:
        """Unknown /api/ routes return 404, not index.html."""
        response = client.get("/api/nonexistent")

        assert response.status_code == 404

    def test_websocket_routes_not_affected(self, client: TestClient) -> None:
        """WebSocket routes work normally."""
        # Just verify the SPA fallback doesn't catch /ws/ routes
        # WebSocket routes return various codes for non-WS requests
        response = client.get("/ws/events")

        # The route exists but returns 404 for non-WebSocket GET requests
        # This confirms the route is registered (not the SPA fallback)
        assert response.status_code == 404

    def test_spa_routing_returns_index(self, client: TestClient) -> None:
        """SPA routes like /workflows return index.html for client-side routing."""
        response = client.get("/workflows")

        # Should return 200 (index.html or instructions)
        assert response.status_code == 200

        content_type = response.headers.get("content-type", "")

        if "text/html" in content_type:
            # Dashboard built - serves index.html for SPA routing
            assert b"Amelia Dashboard" in response.content
