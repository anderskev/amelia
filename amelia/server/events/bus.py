"""Event bus implementation for pub/sub workflow events."""
import asyncio
import contextlib
from collections.abc import Callable
from typing import TYPE_CHECKING

from loguru import logger

from amelia.core.types import StreamEvent, StreamEventType
from amelia.server.config import ServerConfig
from amelia.server.models import WorkflowEvent
from amelia.server.models.events import EventType, get_event_level


if TYPE_CHECKING:
    from amelia.server.events.connection_manager import ConnectionManager


# Mapping from StreamEventType to EventType
_STREAM_TO_EVENT_TYPE: dict[StreamEventType, EventType] = {
    StreamEventType.CLAUDE_THINKING: EventType.CLAUDE_THINKING,
    StreamEventType.CLAUDE_TOOL_CALL: EventType.CLAUDE_TOOL_CALL,
    StreamEventType.CLAUDE_TOOL_RESULT: EventType.CLAUDE_TOOL_RESULT,
    StreamEventType.AGENT_OUTPUT: EventType.AGENT_OUTPUT,
}


class EventBus:
    """Simple synchronous pub/sub event bus for workflow events.

    Allows components to subscribe to and emit workflow events.
    Exceptions in subscribers are logged but don't prevent other
    subscribers from receiving events.

    Warning:
        All subscribers MUST be non-blocking. Since emit() runs
        synchronously in the caller's context, blocking operations
        in subscribers will halt the orchestrator.

    Attributes:
        _subscribers: List of callback functions to notify on emit.
        _broadcast_tasks: Set of active broadcast tasks for cleanup tracking.
        _trace_retention_days: Days to retain trace events (0 = no persistence).
        _sequence_counter: Per-workflow sequence counters for trace events.
    """

    def __init__(self) -> None:
        """Initialize event bus with no subscribers."""
        self._subscribers: list[Callable[[WorkflowEvent], None]] = []
        self._connection_manager: ConnectionManager | None = None
        self._broadcast_tasks: set[asyncio.Task[None]] = set()
        self._trace_retention_days: int = 7
        self._sequence_counter: dict[str, int] = {}

    def subscribe(self, callback: Callable[[WorkflowEvent], None]) -> None:
        """Subscribe to workflow events.

        Args:
            callback: Function to call when events are emitted.
        """
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[WorkflowEvent], None]) -> None:
        """Unsubscribe from workflow events.

        Args:
            callback: Previously subscribed callback to remove.
        """
        with contextlib.suppress(ValueError):
            self._subscribers.remove(callback)

    def set_connection_manager(self, manager: "ConnectionManager") -> None:
        """Set the ConnectionManager for WebSocket broadcasting.

        Args:
            manager: The ConnectionManager instance.
        """
        self._connection_manager = manager

    def configure(self, trace_retention_days: int | None = None) -> None:
        """Configure event bus settings.

        Args:
            trace_retention_days: Days to retain trace events. Set to 0 to disable
                persistence of trace events (WebSocket broadcast only).
        """
        if trace_retention_days is not None:
            self._trace_retention_days = trace_retention_days

    def _handle_broadcast_done(self, task: asyncio.Task[None]) -> None:
        """Handle completion of WebSocket broadcast task.

        Removes completed task from tracking set and logs any exceptions
        that occurred during broadcast.

        Args:
            task: The completed asyncio broadcast task.
        """
        self._broadcast_tasks.discard(task)
        if not task.cancelled():
            exc = task.exception()
            if exc is not None:
                logger.error(
                    "WebSocket broadcast failed",
                    error=str(exc),
                    error_type=type(exc).__name__,
                )

    def emit(self, event: WorkflowEvent) -> None:
        """Emit event to all subscribers synchronously.

        Subscribers are called in registration order. Exceptions in individual
        subscribers are logged but don't prevent other subscribers from
        receiving the event.

        Warning:
            Subscribers MUST be non-blocking. Since emit() runs synchronously
            in the caller's context, any blocking operation in a subscriber
            will halt the orchestrator. If you need to perform I/O or slow
            operations, dispatch them as background tasks within your callback.

        Args:
            event: The workflow event to broadcast.
        """
        for callback in self._subscribers:
            try:
                callback(event)
            except Exception as exc:
                # Use getattr to safely get callback name - functools.partial,
                # callable instances, etc. may not have __name__
                callback_name = getattr(callback, "__name__", repr(callback))
                logger.exception(
                    "Subscriber raised exception",
                    callback=callback_name,
                    event_type=event.event_type,
                    error=str(exc),
                )

        # Broadcast to WebSocket clients
        if self._connection_manager:
            task = asyncio.create_task(self._connection_manager.broadcast(event))
            self._broadcast_tasks.add(task)
            task.add_done_callback(self._handle_broadcast_done)

    def _get_next_sequence(self, workflow_id: str) -> int:
        """Get the next sequence number for a workflow's trace events.

        Args:
            workflow_id: The workflow identifier.

        Returns:
            Next monotonic sequence number for this workflow.
        """
        current = self._sequence_counter.get(workflow_id, 0)
        next_seq = current + 1
        self._sequence_counter[workflow_id] = next_seq
        return next_seq

    def _build_trace_message(self, event: StreamEvent) -> str:
        """Build a human-readable message for a trace event.

        Args:
            event: The stream event to describe.

        Returns:
            Human-readable message string.
        """
        if event.type == StreamEventType.CLAUDE_THINKING:
            return "Agent thinking"
        elif event.type == StreamEventType.CLAUDE_TOOL_CALL:
            tool = event.tool_name or "unknown"
            return f"Tool call: {tool}"
        elif event.type == StreamEventType.CLAUDE_TOOL_RESULT:
            tool = event.tool_name or "unknown"
            status = "error" if event.is_error else "success"
            return f"Tool result: {tool} ({status})"
        elif event.type == StreamEventType.AGENT_OUTPUT:
            return "Agent output"
        return f"Stream event: {event.type}"

    def _convert_to_workflow_event(self, event: StreamEvent) -> WorkflowEvent:
        """Convert a StreamEvent to a WorkflowEvent for persistence.

        Args:
            event: The stream event to convert.

        Returns:
            WorkflowEvent suitable for database persistence.
        """
        event_type = _STREAM_TO_EVENT_TYPE.get(event.type, EventType.STREAM)
        level = get_event_level(event_type)

        return WorkflowEvent(
            id=event.id,
            workflow_id=event.workflow_id,
            sequence=self._get_next_sequence(event.workflow_id),
            timestamp=event.timestamp,
            agent=event.agent,
            event_type=event_type,
            level=level,
            message=self._build_trace_message(event),
            data={"content": event.content} if event.content else None,
            tool_name=event.tool_name,
            tool_input=event.tool_input,
            is_error=event.is_error,
        )

    def emit_stream(self, event: StreamEvent) -> None:
        """Emit a stream event for real-time broadcast and optional persistence.

        Stream events are broadcast to WebSocket clients in real-time. When
        trace_retention_days > 0, they are also converted to WorkflowEvents
        and emitted to subscribers for database persistence.

        Args:
            event: The stream event to broadcast.
        """
        # Filter tool results unless explicitly enabled
        config = ServerConfig()
        if event.type == StreamEventType.CLAUDE_TOOL_RESULT and not config.stream_tool_results:
            return

        # Convert to WorkflowEvent for persistence if trace retention is enabled
        if self._trace_retention_days > 0:
            workflow_event = self._convert_to_workflow_event(event)
            # Emit to subscribers for persistence
            self.emit(workflow_event)

        # Broadcast to WebSocket clients
        if self._connection_manager:
            task = asyncio.create_task(self._connection_manager.broadcast_stream(event))
            self._broadcast_tasks.add(task)
            task.add_done_callback(self._handle_broadcast_done)

    async def cleanup(self) -> None:
        """Wait for all pending broadcast tasks to complete.

        Should be called during graceful shutdown to ensure all events
        are delivered before the server stops.
        """
        if self._broadcast_tasks:
            await asyncio.gather(*self._broadcast_tasks, return_exceptions=True)
            self._broadcast_tasks.clear()
