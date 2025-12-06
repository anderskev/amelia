# tests/unit/server/events/test_event_bus_websocket.py
"""Tests for EventBus WebSocket integration."""
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from amelia.server.events.bus import EventBus
from amelia.server.events.connection_manager import ConnectionManager
from amelia.server.models.events import EventType, WorkflowEvent


@pytest.mark.asyncio
class TestEventBusWebSocketIntegration:
    """Tests for EventBus broadcasting to WebSocket."""

    @pytest.fixture
    def mock_connection_manager(self):
        """Mock ConnectionManager."""
        manager = AsyncMock(spec=ConnectionManager)
        manager.broadcast = AsyncMock()
        return manager

    @pytest.fixture
    def event_bus(self, mock_connection_manager):
        """EventBus with mocked ConnectionManager."""
        bus = EventBus()
        bus.set_connection_manager(mock_connection_manager)
        return bus

    async def test_emit_broadcasts_to_websocket(self, event_bus, mock_connection_manager):
        """emit() broadcasts event to ConnectionManager."""
        event = WorkflowEvent(
            id="evt-123",
            workflow_id="wf-456",
            sequence=1,
            timestamp=datetime.utcnow(),
            agent="system",
            event_type=EventType.WORKFLOW_STARTED,
            message="Started",
        )

        event_bus.emit(event)

        # Give asyncio time to process
        await asyncio.sleep(0.01)

        mock_connection_manager.broadcast.assert_awaited_once_with(event)

    async def test_emit_without_connection_manager_does_not_crash(self):
        """emit() works even without ConnectionManager set."""
        bus = EventBus()
        # Don't set connection manager

        event = WorkflowEvent(
            id="evt-123",
            workflow_id="wf-456",
            sequence=1,
            timestamp=datetime.utcnow(),
            agent="system",
            event_type=EventType.WORKFLOW_STARTED,
            message="Started",
        )

        # Should not crash
        bus.emit(event)
        await asyncio.sleep(0.01)

    async def test_subscribe_still_works_with_websocket(self, event_bus, mock_connection_manager):
        """Local subscribers still receive events when WebSocket enabled.

        Note: Subscribers MUST be non-blocking. If you need to perform I/O
        or slow operations, dispatch them as background tasks.
        """
        received_events = []

        def handler(event: WorkflowEvent):
            # Example of non-blocking subscriber - quick operation only
            received_events.append(event)
            # If you need I/O: asyncio.create_task(slow_operation(event))

        event_bus.subscribe(handler)

        event = WorkflowEvent(
            id="evt-123",
            workflow_id="wf-456",
            sequence=1,
            timestamp=datetime.utcnow(),
            agent="system",
            event_type=EventType.WORKFLOW_STARTED,
            message="Started",
        )

        event_bus.emit(event)
        await asyncio.sleep(0.01)

        # Both local subscriber and WebSocket should receive
        assert len(received_events) == 1
        mock_connection_manager.broadcast.assert_awaited_once()
