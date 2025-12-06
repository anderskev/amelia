# tests/unit/server/events/test_connection_manager.py
"""Tests for WebSocket connection manager."""
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocketDisconnect

from amelia.server.events.connection_manager import ConnectionManager
from amelia.server.models.events import EventType, WorkflowEvent


class TestConnectionManager:
    """Tests for ConnectionManager."""

    @pytest.fixture
    def manager(self):
        """Create ConnectionManager instance."""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket."""
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.close = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self, manager, mock_websocket):
        """connect() accepts the WebSocket connection."""
        await manager.connect(mock_websocket)

        mock_websocket.accept.assert_awaited_once()
        assert manager.active_connections == 1

    @pytest.mark.asyncio
    async def test_connect_initializes_empty_subscription(self, manager, mock_websocket):
        """New connections start with empty subscription (all events)."""
        await manager.connect(mock_websocket)

        # Empty set means subscribed to all
        assert mock_websocket in manager._connections
        assert manager._connections[mock_websocket] == set()

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self, manager, mock_websocket):
        """disconnect() removes connection from tracking."""
        await manager.connect(mock_websocket)
        await manager.disconnect(mock_websocket)

        assert mock_websocket not in manager._connections
        assert manager.active_connections == 0

    @pytest.mark.asyncio
    async def test_subscribe_adds_workflow_id(self, manager, mock_websocket):
        """subscribe() adds workflow_id to connection's subscription set."""
        await manager.connect(mock_websocket)
        await manager.subscribe(mock_websocket, "wf-123")

        assert "wf-123" in manager._connections[mock_websocket]

    @pytest.mark.asyncio
    async def test_subscribe_multiple_workflows(self, manager, mock_websocket):
        """Can subscribe to multiple workflows."""
        await manager.connect(mock_websocket)
        await manager.subscribe(mock_websocket, "wf-123")
        await manager.subscribe(mock_websocket, "wf-456")

        assert "wf-123" in manager._connections[mock_websocket]
        assert "wf-456" in manager._connections[mock_websocket]

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_workflow_id(self, manager, mock_websocket):
        """unsubscribe() removes workflow_id from subscription set."""
        await manager.connect(mock_websocket)
        await manager.subscribe(mock_websocket, "wf-123")
        await manager.unsubscribe(mock_websocket, "wf-123")

        assert "wf-123" not in manager._connections[mock_websocket]

    @pytest.mark.asyncio
    async def test_subscribe_all_clears_subscription_set(self, manager, mock_websocket):
        """subscribe_all() clears subscription set (empty = all)."""
        await manager.connect(mock_websocket)
        await manager.subscribe(mock_websocket, "wf-123")
        await manager.subscribe_all(mock_websocket)

        assert manager._connections[mock_websocket] == set()

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_subscribed_all(self, manager, mock_websocket):
        """broadcast() sends event to connections subscribed to all."""
        await manager.connect(mock_websocket)

        event = WorkflowEvent(
            id="evt-123",
            workflow_id="wf-456",
            sequence=1,
            timestamp=datetime.utcnow(),
            agent="system",
            event_type=EventType.WORKFLOW_STARTED,
            message="Started",
        )

        await manager.broadcast(event)

        mock_websocket.send_json.assert_awaited_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "event"
        assert call_args["payload"]["workflow_id"] == "wf-456"

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_specific_subscriber(self, manager, mock_websocket):
        """broadcast() sends event to connections subscribed to that workflow."""
        await manager.connect(mock_websocket)
        await manager.subscribe(mock_websocket, "wf-456")

        event = WorkflowEvent(
            id="evt-123",
            workflow_id="wf-456",
            sequence=1,
            timestamp=datetime.utcnow(),
            agent="system",
            event_type=EventType.WORKFLOW_STARTED,
            message="Started",
        )

        await manager.broadcast(event)

        mock_websocket.send_json.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_broadcast_skips_unsubscribed_connection(self, manager, mock_websocket):
        """broadcast() skips connections not subscribed to that workflow."""
        await manager.connect(mock_websocket)
        await manager.subscribe(mock_websocket, "wf-999")  # Different workflow

        event = WorkflowEvent(
            id="evt-123",
            workflow_id="wf-456",
            sequence=1,
            timestamp=datetime.utcnow(),
            agent="system",
            event_type=EventType.WORKFLOW_STARTED,
            message="Started",
        )

        await manager.broadcast(event)

        # Should not send to this connection
        mock_websocket.send_json.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_broadcast_handles_disconnected_socket(self, manager, mock_websocket):
        """broadcast() removes disconnected sockets gracefully."""
        await manager.connect(mock_websocket)
        mock_websocket.send_json.side_effect = WebSocketDisconnect()

        event = WorkflowEvent(
            id="evt-123",
            workflow_id="wf-456",
            sequence=1,
            timestamp=datetime.utcnow(),
            agent="system",
            event_type=EventType.WORKFLOW_STARTED,
            message="Started",
        )

        await manager.broadcast(event)

        # Connection should be removed after disconnect
        assert mock_websocket not in manager._connections

    @pytest.mark.asyncio
    async def test_close_all_closes_all_connections(self, manager, mock_websocket):
        """close_all() closes all connections gracefully."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.close = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.close = AsyncMock()

        await manager.connect(ws1)
        await manager.connect(ws2)

        await manager.close_all(code=1000, reason="shutdown")

        ws1.close.assert_awaited_once_with(code=1000, reason="shutdown")
        ws2.close.assert_awaited_once_with(code=1000, reason="shutdown")
        assert manager.active_connections == 0

    @pytest.mark.asyncio
    async def test_close_all_handles_errors(self, manager, mock_websocket):
        """close_all() handles errors gracefully."""
        mock_websocket.close.side_effect = Exception("Close failed")

        await manager.connect(mock_websocket)
        await manager.close_all()

        # Should not raise, just clear connections
        assert manager.active_connections == 0

    @pytest.mark.asyncio
    async def test_active_connections_count(self, manager):
        """active_connections property returns correct count."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()

        assert manager.active_connections == 0

        await manager.connect(ws1)
        assert manager.active_connections == 1

        await manager.connect(ws2)
        assert manager.active_connections == 2

        await manager.disconnect(ws1)
        assert manager.active_connections == 1
