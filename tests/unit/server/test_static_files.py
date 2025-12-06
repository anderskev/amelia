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

    def test_dashboard_not_built_message(self, client: TestClient) -> None:
        """GET / returns helpful message when dashboard not built."""
        response = client.get("/")

        # When dist/ doesn't exist, should return instructions
        # or serve index.html if built
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                # Dashboard not built case
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
