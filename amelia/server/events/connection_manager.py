# amelia/server/events/connection_manager.py
"""WebSocket connection manager with subscription filtering."""
import asyncio
from contextlib import suppress

from fastapi import WebSocket, WebSocketDisconnect

from amelia.server.models.events import WorkflowEvent


class ConnectionManager:
    """Manages WebSocket connections with subscription-based filtering.

    Each connection tracks which workflows it's subscribed to:
    - Empty set = subscribed to all workflows
    - Non-empty set = subscribed to specific workflows only

    Thread-safe via asyncio.Lock.
    """

    def __init__(self) -> None:
        """Initialize connection manager."""
        self._connections: dict[WebSocket, set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket to connect.
        """
        await websocket.accept()
        async with self._lock:
            # Empty set = subscribed to all workflows
            self._connections[websocket] = set()

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection.

        Args:
            websocket: The WebSocket to disconnect.
        """
        async with self._lock:
            self._connections.pop(websocket, None)

    async def subscribe(self, websocket: WebSocket, workflow_id: str) -> None:
        """Subscribe connection to specific workflow events.

        Args:
            websocket: The WebSocket connection.
            workflow_id: The workflow to subscribe to.
        """
        async with self._lock:
            if websocket in self._connections:
                self._connections[websocket].add(workflow_id)

    async def unsubscribe(self, websocket: WebSocket, workflow_id: str) -> None:
        """Unsubscribe connection from specific workflow events.

        Args:
            websocket: The WebSocket connection.
            workflow_id: The workflow to unsubscribe from.
        """
        async with self._lock:
            if websocket in self._connections:
                self._connections[websocket].discard(workflow_id)

    async def subscribe_all(self, websocket: WebSocket) -> None:
        """Subscribe connection to all workflow events.

        Args:
            websocket: The WebSocket connection.
        """
        async with self._lock:
            if websocket in self._connections:
                # Empty set = subscribed to all
                self._connections[websocket] = set()

    async def broadcast(self, event: WorkflowEvent) -> None:
        """Broadcast event to subscribed connections only.

        Connections with empty subscription set receive all events.
        Connections with specific workflow IDs only receive matching events.

        Automatically removes disconnected clients.

        Args:
            event: The workflow event to broadcast.
        """
        async with self._lock:
            for ws, subscribed_ids in list(self._connections.items()):
                # Empty set = subscribed to all workflows
                if not subscribed_ids or event.workflow_id in subscribed_ids:
                    try:
                        await ws.send_json({
                            "type": "event",
                            "payload": event.model_dump(mode="json"),
                        })
                    except WebSocketDisconnect:
                        # Remove disconnected client
                        self._connections.pop(ws, None)
                    except Exception:
                        # Remove on any error
                        self._connections.pop(ws, None)

    async def close_all(self, code: int = 1000, reason: str = "") -> None:
        """Close all connections gracefully.

        Args:
            code: WebSocket close code (default 1000 = normal closure).
            reason: Human-readable close reason.
        """
        async with self._lock:
            for ws in list(self._connections.keys()):
                with suppress(Exception):
                    # Ignore errors during shutdown
                    await ws.close(code=code, reason=reason)
            self._connections.clear()

    @property
    def active_connections(self) -> int:
        """Get count of active connections.

        Returns:
            Number of active WebSocket connections.
        """
        return len(self._connections)
