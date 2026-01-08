# tests/unit/server/orchestrator/test_service_stream_mode.py
"""Tests for LangGraph combined stream mode handling."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_repository():
    """Create mock workflow repository."""
    repo = AsyncMock()
    repo.get.return_value = MagicMock(current_stage=None)
    repo.update = AsyncMock()
    repo.set_status = AsyncMock()
    return repo


@pytest.fixture
def mock_event_bus():
    """Create mock event bus."""
    bus = MagicMock()
    bus.emit = AsyncMock()
    bus.emit_stream = MagicMock()
    return bus


class TestStreamModeTaskEvents:
    """Test handling of LangGraph tasks stream mode events."""

    @pytest.mark.asyncio
    async def test_tasks_event_emits_stage_started(
        self, mock_repository, mock_event_bus
    ):
        """Task events should emit STAGE_STARTED before node executes."""
        from amelia.server.orchestrator.service import OrchestratorService
        from amelia.server.models.events import EventType

        # Create service with mocks
        service = OrchestratorService(
            repository=mock_repository,
            event_bus=mock_event_bus,
        )

        # Simulate a tasks mode event
        task_event = {
            "id": "task-123",
            "name": "architect_node",
            "input": {},
            "triggers": ["start:issue"],
        }

        # Call the handler
        await service._handle_tasks_event("workflow-123", task_event)

        # Verify STAGE_STARTED was emitted
        mock_event_bus.emit.assert_called()
        call_args = mock_event_bus.emit.call_args
        event = call_args[0][0]
        assert event.event_type == EventType.STAGE_STARTED
        assert event.data["stage"] == "architect_node"

    @pytest.mark.asyncio
    async def test_task_result_event_ignored(
        self, mock_repository, mock_event_bus
    ):
        """Task result events should be ignored (completion handled by updates mode)."""
        from amelia.server.orchestrator.service import OrchestratorService

        service = OrchestratorService(
            repository=mock_repository,
            event_bus=mock_event_bus,
        )

        # Simulate a task RESULT event (has "result" instead of "input")
        task_result = {
            "id": "task-123",
            "name": "architect_node",
            "error": None,
            "result": {"goal": "Test goal"},
            "interrupts": [],
        }

        # Call the handler
        await service._handle_tasks_event("workflow-123", task_result)

        # Verify no event was emitted
        mock_event_bus.emit.assert_not_called()

    @pytest.mark.asyncio
    async def test_combined_stream_mode_parses_tuples(
        self, mock_repository, mock_event_bus
    ):
        """Combined stream mode should parse (mode, data) tuples."""
        from amelia.server.orchestrator.service import OrchestratorService

        service = OrchestratorService(
            repository=mock_repository,
            event_bus=mock_event_bus,
        )

        # Simulate chunks from stream_mode=["updates", "tasks"]
        chunks = [
            ("tasks", {"id": "t1", "name": "architect_node", "input": {}, "triggers": []}),
            ("updates", {"architect_node": {"goal": "Test goal"}}),
        ]

        # Process each chunk
        for chunk in chunks:
            await service._handle_combined_stream_chunk("workflow-123", chunk)

        # Verify both handlers were called appropriately
        assert mock_event_bus.emit.call_count >= 2  # STAGE_STARTED + STAGE_COMPLETED
