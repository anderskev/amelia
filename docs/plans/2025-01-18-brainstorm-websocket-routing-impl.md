# Brainstorm WebSocket Event Routing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Route brainstorm events through a dedicated `{type: "brainstorm", ...}` wire format so frontend handlers match.

**Architecture:** Add `EventDomain` enum to distinguish workflow vs brainstorm events at the model level. `ConnectionManager.broadcast()` branches on domain to emit different wire formats. Frontend updates `WebSocketMessage` types and adds a unified `handleBrainstormMessage` handler. Store gains `updateMessage` action and messages gain `status` field.

**Tech Stack:** Python (Pydantic, FastAPI), TypeScript (React, Zustand), Vitest

---

## Task 1: Add EventDomain Enum to Backend Events Model

**Files:**
- Modify: `amelia/server/models/events.py:1-25`
- Test: `tests/unit/server/models/test_events.py` (new or extend)

**Step 1: Write the failing test**

Create test for the new `EventDomain` enum and `domain` field on `WorkflowEvent`:

```python
# tests/unit/server/models/test_events.py
import pytest
from amelia.server.models.events import EventDomain, EventType, WorkflowEvent
from datetime import datetime, UTC


def test_event_domain_enum_values():
    """EventDomain has workflow and brainstorm values."""
    assert EventDomain.WORKFLOW == "workflow"
    assert EventDomain.BRAINSTORM == "brainstorm"


def test_workflow_event_domain_defaults_to_workflow():
    """WorkflowEvent.domain defaults to EventDomain.WORKFLOW."""
    event = WorkflowEvent(
        id="test-id",
        workflow_id="wf-1",
        sequence=1,
        timestamp=datetime.now(UTC),
        agent="system",
        event_type=EventType.WORKFLOW_STARTED,
        message="Test event",
    )
    assert event.domain == EventDomain.WORKFLOW


def test_workflow_event_domain_can_be_brainstorm():
    """WorkflowEvent.domain can be set to EventDomain.BRAINSTORM."""
    event = WorkflowEvent(
        id="test-id",
        workflow_id="session-1",
        sequence=0,
        timestamp=datetime.now(UTC),
        agent="brainstormer",
        event_type=EventType.BRAINSTORM_TEXT,
        message="Streaming text",
        domain=EventDomain.BRAINSTORM,
    )
    assert event.domain == EventDomain.BRAINSTORM
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/server/models/test_events.py -v -k "domain"`
Expected: FAIL with "cannot import name 'EventDomain'"

**Step 3: Write minimal implementation**

Add `EventDomain` enum and `domain` field to `WorkflowEvent`:

```python
# In amelia/server/models/events.py, after imports and before EventLevel

class EventDomain(StrEnum):
    """Domain of event origin.

    Attributes:
        WORKFLOW: Standard workflow events (orchestrator, agents).
        BRAINSTORM: Brainstorming session events (chat streaming).
    """
    WORKFLOW = "workflow"
    BRAINSTORM = "brainstorm"
```

Add field to `WorkflowEvent` class (after `id` field):

```python
    domain: EventDomain = Field(
        default=EventDomain.WORKFLOW,
        description="Event domain (workflow or brainstorm)",
    )
```

Update `__all__` export list to include `EventDomain`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/models/test_events.py -v -k "domain"`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/server/models/events.py tests/unit/server/models/test_events.py
git commit -m "$(cat <<'EOF'
feat(events): add EventDomain enum for routing brainstorm events

Adds EventDomain.WORKFLOW and EventDomain.BRAINSTORM to distinguish
event origins. WorkflowEvent gains a `domain` field defaulting to
WORKFLOW for backward compatibility.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Update ConnectionManager.broadcast() to Branch on Domain

**Files:**
- Modify: `amelia/server/events/connection_manager.py:131-190`
- Test: `tests/unit/server/events/test_connection_manager.py` (extend)

**Step 1: Write the failing test**

```python
# tests/unit/server/events/test_connection_manager.py
import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock
from amelia.server.events.connection_manager import ConnectionManager
from amelia.server.models.events import (
    EventDomain,
    EventType,
    EventLevel,
    WorkflowEvent,
)


@pytest.fixture
def manager():
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


@pytest.mark.asyncio
async def test_broadcast_workflow_event_uses_event_wrapper(manager, mock_websocket):
    """Workflow domain events are sent as {type: 'event', payload: ...}."""
    await manager.connect(mock_websocket)
    await manager.subscribe_all(mock_websocket)

    event = WorkflowEvent(
        id="evt-1",
        workflow_id="wf-1",
        sequence=1,
        timestamp=datetime.now(UTC),
        agent="system",
        event_type=EventType.WORKFLOW_STARTED,
        message="Started",
        domain=EventDomain.WORKFLOW,
    )

    await manager.broadcast(event)

    mock_websocket.send_json.assert_called_once()
    payload = mock_websocket.send_json.call_args[0][0]
    assert payload["type"] == "event"
    assert "payload" in payload
    assert payload["payload"]["id"] == "evt-1"


@pytest.mark.asyncio
async def test_broadcast_brainstorm_event_uses_brainstorm_wrapper(manager, mock_websocket):
    """Brainstorm domain events are sent as {type: 'brainstorm', ...}."""
    await manager.connect(mock_websocket)
    await manager.subscribe_all(mock_websocket)

    event = WorkflowEvent(
        id="evt-2",
        workflow_id="session-1",
        sequence=0,
        timestamp=datetime.now(UTC),
        agent="brainstormer",
        event_type=EventType.BRAINSTORM_TEXT,
        message="Streaming",
        domain=EventDomain.BRAINSTORM,
        data={"session_id": "session-1", "message_id": "msg-1", "text": "Hello"},
    )

    await manager.broadcast(event)

    mock_websocket.send_json.assert_called_once()
    payload = mock_websocket.send_json.call_args[0][0]
    assert payload["type"] == "brainstorm"
    assert payload["event_type"] == "text"  # brainstorm_ prefix stripped
    assert payload["session_id"] == "session-1"
    assert payload["message_id"] == "msg-1"
    assert payload["data"]["text"] == "Hello"
    assert "timestamp" in payload
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/server/events/test_connection_manager.py -v -k "brainstorm_wrapper"`
Expected: FAIL - payload still has `type: "event"` for brainstorm events

**Step 3: Write minimal implementation**

Modify `broadcast()` method in `ConnectionManager` to branch on domain:

```python
# In amelia/server/events/connection_manager.py, replace the payload construction
# (around line 168-171) with:

        if event.domain == EventDomain.BRAINSTORM:
            # Brainstorm events use flat format for direct frontend handling
            event_type_str = event.event_type.value
            if event_type_str.startswith("brainstorm_"):
                event_type_str = event_type_str[len("brainstorm_"):]

            payload = {
                "type": "brainstorm",
                "event_type": event_type_str,
                "session_id": event.data.get("session_id") if event.data else None,
                "message_id": event.data.get("message_id") if event.data else None,
                "data": event.data or {},
                "timestamp": event.timestamp.isoformat(),
            }
        else:
            # Workflow events use wrapped format
            payload = {
                "type": "event",
                "payload": event.model_dump(mode="json"),
            }
```

Add import for `EventDomain` at top of file.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/events/test_connection_manager.py -v -k "brainstorm_wrapper or event_wrapper"`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/server/events/connection_manager.py tests/unit/server/events/test_connection_manager.py
git commit -m "$(cat <<'EOF'
feat(websocket): route brainstorm events with dedicated wire format

ConnectionManager.broadcast() now branches on EventDomain:
- WORKFLOW: {type: "event", payload: <WorkflowEvent>}
- BRAINSTORM: {type: "brainstorm", event_type, session_id, ...}

This enables frontend to route brainstorm events directly to
brainstormStore without parsing nested payloads.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Set domain=BRAINSTORM in BrainstormService Events

**Files:**
- Modify: `amelia/server/services/brainstorm.py:364-407` (`_agentic_message_to_event`)
- Modify: `amelia/server/services/brainstorm.py:350-362` (complete event)
- Test: `tests/unit/server/services/test_brainstorm.py` (extend)

**Step 1: Write the failing test**

```python
# tests/unit/server/services/test_brainstorm.py (add to existing tests)
import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch
from amelia.server.services.brainstorm import BrainstormService
from amelia.server.models.events import EventDomain, EventType


@pytest.fixture
def brainstorm_service():
    repository = AsyncMock()
    event_bus = MagicMock()
    return BrainstormService(repository=repository, event_bus=event_bus)


def test_agentic_message_to_event_sets_brainstorm_domain(brainstorm_service):
    """Events from _agentic_message_to_event have domain=BRAINSTORM."""
    from amelia.drivers.interface import AgenticMessage, AgenticMessageType

    msg = AgenticMessage(
        type=AgenticMessageType.TEXT,
        content="Hello world",
    )

    event = brainstorm_service._agentic_message_to_event(msg, "session-123")

    assert event.domain == EventDomain.BRAINSTORM
    assert event.event_type == EventType.BRAINSTORM_TEXT
    assert event.data["session_id"] == "session-123"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/server/services/test_brainstorm.py -v -k "brainstorm_domain"`
Expected: FAIL - `event.domain` is WORKFLOW (default)

**Step 3: Write minimal implementation**

Modify `_agentic_message_to_event` method to set domain:

```python
# In amelia/server/services/brainstorm.py, _agentic_message_to_event method
# Add domain=EventDomain.BRAINSTORM to the WorkflowEvent constructor:

        return WorkflowEvent(
            id=str(uuid4()),
            workflow_id=session_id,
            sequence=0,
            timestamp=datetime.now(UTC),
            agent="brainstormer",
            event_type=event_type,
            message=message,
            data=data,
            domain=EventDomain.BRAINSTORM,  # Add this line
        )
```

Also update the message complete event at the end of `send_message`:

```python
        # Emit message complete event
        complete_event = WorkflowEvent(
            id=str(uuid4()),
            workflow_id=session_id,
            sequence=0,
            timestamp=datetime.now(UTC),
            agent="brainstormer",
            event_type=EventType.BRAINSTORM_MESSAGE_COMPLETE,
            message="Message complete",
            data={"message_id": assistant_message.id, "session_id": session_id},
            domain=EventDomain.BRAINSTORM,  # Add this line
        )
```

Add import for `EventDomain` at top of file.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/services/test_brainstorm.py -v -k "brainstorm_domain"`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/server/services/brainstorm.py tests/unit/server/services/test_brainstorm.py
git commit -m "$(cat <<'EOF'
feat(brainstorm): set EventDomain.BRAINSTORM on all brainstorm events

BrainstormService now emits events with domain=BRAINSTORM so
ConnectionManager routes them with the dedicated wire format.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Update Frontend WebSocket Types

**Files:**
- Modify: `dashboard/src/types/index.ts:547-562`
- Test: Type-level only (TypeScript compiler validates)

**Step 1: Update the types**

Replace the brainstorm message types in `WebSocketMessage` union:

```typescript
// dashboard/src/types/index.ts

/**
 * Event types for brainstorm streaming messages.
 */
export type BrainstormEventType =
  | 'text'
  | 'reasoning'
  | 'tool_call'
  | 'tool_result'
  | 'message_complete'
  | 'artifact_created'
  | 'session_created'
  | 'session_completed';

/**
 * Brainstorm streaming message from the server.
 * Uses a flat format (no nested payload) for direct handling.
 */
export interface BrainstormMessage {
  type: 'brainstorm';
  event_type: BrainstormEventType;
  session_id: string;
  message_id?: string;
  data: Record<string, unknown>;
  timestamp: string;
}

/**
 * Messages sent from the server to the dashboard client over WebSocket.
 */
export type WebSocketMessage =
  | { type: 'ping' }
  | { type: 'event'; payload: WorkflowEvent }
  | { type: 'backfill_complete'; count: number }
  | { type: 'backfill_expired'; message: string }
  | BrainstormMessage;
```

**Step 2: Run type check to verify it compiles**

Run: `cd dashboard && pnpm type-check`
Expected: Type errors in `useWebSocket.ts` (switch cases now invalid) - this is expected and fixed in next task

**Step 3: Commit**

```bash
git add dashboard/src/types/index.ts
git commit -m "$(cat <<'EOF'
feat(types): add BrainstormMessage type for unified event handling

Replaces individual brainstorm_* message types with a single
BrainstormMessage interface using event_type discriminator.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Add updateMessage Action to brainstormStore

**Files:**
- Modify: `dashboard/src/store/brainstormStore.ts`
- Modify: `dashboard/src/types/api.ts:121-129` (BrainstormMessage)
- Test: `dashboard/src/store/__tests__/brainstormStore.test.ts`

**Step 1: Update BrainstormMessage type with status field**

```typescript
// dashboard/src/types/api.ts - update BrainstormMessage interface

/** A message in a brainstorming session. */
export interface BrainstormMessage {
  id: string;
  session_id: string;
  sequence: number;
  role: "user" | "assistant";
  content: string;
  reasoning?: string;
  parts: MessagePart[] | null;
  created_at: string;
  /** Streaming status: undefined = complete, 'streaming' = in progress, 'error' = failed */
  status?: 'streaming' | 'error';
  /** Human-readable error message when status is 'error' */
  errorMessage?: string;
}
```

**Step 2: Write failing test for updateMessage action**

```typescript
// dashboard/src/store/__tests__/brainstormStore.test.ts (add test)
import { describe, it, expect, beforeEach } from 'vitest';
import { useBrainstormStore } from '../brainstormStore';

describe('useBrainstormStore', () => {
  beforeEach(() => {
    useBrainstormStore.setState({
      messages: [],
      sessions: [],
      activeSessionId: null,
      artifacts: [],
      isStreaming: false,
      streamingMessageId: null,
      drawerOpen: false,
    });
  });

  describe('updateMessage', () => {
    it('updates a message using updater function', () => {
      const message = {
        id: 'msg-1',
        session_id: 'session-1',
        sequence: 1,
        role: 'assistant' as const,
        content: 'Hello',
        parts: null,
        created_at: new Date().toISOString(),
        status: 'streaming' as const,
      };

      useBrainstormStore.getState().addMessage(message);

      useBrainstormStore.getState().updateMessage('msg-1', (m) => ({
        ...m,
        content: m.content + ' world',
        status: undefined,
      }));

      const updated = useBrainstormStore.getState().messages[0];
      expect(updated.content).toBe('Hello world');
      expect(updated.status).toBeUndefined();
    });

    it('does nothing if message not found', () => {
      useBrainstormStore.getState().updateMessage('nonexistent', (m) => ({
        ...m,
        content: 'changed',
      }));

      expect(useBrainstormStore.getState().messages).toHaveLength(0);
    });
  });
});
```

**Step 3: Run test to verify it fails**

Run: `cd dashboard && pnpm test:run -- brainstormStore.test.ts`
Expected: FAIL - "updateMessage is not a function"

**Step 4: Add updateMessage action to store**

```typescript
// dashboard/src/store/brainstormStore.ts

interface BrainstormState {
  // ... existing properties ...

  // Add to Message actions section:
  updateMessage: (
    messageId: string,
    updater: (message: BrainstormMessage) => BrainstormMessage
  ) => void;
}

// In the create() implementation, add:
  updateMessage: (messageId, updater) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === messageId ? updater(m) : m
      ),
    })),
```

**Step 5: Run test to verify it passes**

Run: `cd dashboard && pnpm test:run -- brainstormStore.test.ts`
Expected: PASS

**Step 6: Commit**

```bash
git add dashboard/src/store/brainstormStore.ts dashboard/src/types/api.ts dashboard/src/store/__tests__/brainstormStore.test.ts
git commit -m "$(cat <<'EOF'
feat(store): add updateMessage action and message status field

- BrainstormMessage gains status ('streaming' | 'error' | undefined)
  and errorMessage fields
- useBrainstormStore gains updateMessage(id, updater) for atomic updates
- Supports streaming UI feedback and error display

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Add handleBrainstormMessage to useWebSocket

**Files:**
- Modify: `dashboard/src/hooks/useWebSocket.ts`
- Test: `dashboard/src/hooks/__tests__/useWebSocket.test.ts` (extend or create)

**Step 1: Write failing test**

```typescript
// dashboard/src/hooks/__tests__/useWebSocket.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useBrainstormStore } from '../../store/brainstormStore';

describe('useWebSocket brainstorm handling', () => {
  beforeEach(() => {
    useBrainstormStore.setState({
      messages: [
        {
          id: 'msg-1',
          session_id: 'session-1',
          sequence: 1,
          role: 'assistant',
          content: '',
          parts: null,
          created_at: new Date().toISOString(),
          status: 'streaming',
        },
      ],
      activeSessionId: 'session-1',
      isStreaming: true,
      streamingMessageId: 'msg-1',
      sessions: [],
      artifacts: [],
      drawerOpen: false,
    });
  });

  it('handles brainstorm text event by appending content', () => {
    const { handleBrainstormMessage } = await import('../useWebSocket');

    handleBrainstormMessage({
      type: 'brainstorm',
      event_type: 'text',
      session_id: 'session-1',
      message_id: 'msg-1',
      data: { text: 'Hello' },
      timestamp: new Date().toISOString(),
    });

    const msg = useBrainstormStore.getState().messages[0];
    expect(msg.content).toBe('Hello');
  });

  it('handles brainstorm message_complete by clearing streaming status', () => {
    const { handleBrainstormMessage } = await import('../useWebSocket');

    handleBrainstormMessage({
      type: 'brainstorm',
      event_type: 'message_complete',
      session_id: 'session-1',
      message_id: 'msg-1',
      data: {},
      timestamp: new Date().toISOString(),
    });

    const msg = useBrainstormStore.getState().messages[0];
    expect(msg.status).toBeUndefined();
    expect(useBrainstormStore.getState().isStreaming).toBe(false);
  });

  it('handles brainstorm message_complete with error', () => {
    const { handleBrainstormMessage } = await import('../useWebSocket');

    handleBrainstormMessage({
      type: 'brainstorm',
      event_type: 'message_complete',
      session_id: 'session-1',
      message_id: 'msg-1',
      data: { error: 'Connection failed' },
      timestamp: new Date().toISOString(),
    });

    const msg = useBrainstormStore.getState().messages[0];
    expect(msg.status).toBe('error');
    expect(msg.errorMessage).toBe('Connection failed');
  });

  it('ignores events for different session', () => {
    const { handleBrainstormMessage } = await import('../useWebSocket');

    handleBrainstormMessage({
      type: 'brainstorm',
      event_type: 'text',
      session_id: 'other-session',
      message_id: 'msg-1',
      data: { text: 'Hello' },
      timestamp: new Date().toISOString(),
    });

    const msg = useBrainstormStore.getState().messages[0];
    expect(msg.content).toBe(''); // unchanged
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && pnpm test:run -- useWebSocket.test.ts`
Expected: FAIL - `handleBrainstormMessage` not exported

**Step 3: Implement handleBrainstormMessage and update switch**

```typescript
// dashboard/src/hooks/useWebSocket.ts

import type { WebSocketMessage, WorkflowEvent, BrainstormMessage } from '../types';

/**
 * Handle incoming brainstorm streaming events.
 * Routes events to the brainstormStore based on event_type.
 */
export function handleBrainstormMessage(msg: BrainstormMessage): void {
  const state = useBrainstormStore.getState();

  // Ignore events for different sessions
  if (msg.session_id !== state.activeSessionId) return;

  switch (msg.event_type) {
    case 'text':
      if (msg.message_id) {
        state.updateMessage(msg.message_id, (m) => ({
          ...m,
          status: undefined,
          content: m.content + (msg.data.text as string ?? ''),
        }));
      }
      break;

    case 'reasoning':
      if (msg.message_id) {
        state.updateMessage(msg.message_id, (m) => ({
          ...m,
          reasoning: (m.reasoning ?? '') + (msg.data.text as string ?? ''),
        }));
      }
      break;

    case 'message_complete': {
      const error = msg.data.error as string | undefined;
      if (msg.message_id) {
        state.updateMessage(msg.message_id, (m) => ({
          ...m,
          status: error ? 'error' : undefined,
          errorMessage: error,
        }));
      }
      state.setStreaming(false, null);
      break;
    }

    case 'artifact_created': {
      const artifact = msg.data.artifact;
      if (artifact) {
        state.addArtifact(artifact as import('../types/api').BrainstormArtifact);
        state.updateSession(msg.session_id, { status: 'ready_for_handoff' });
      }
      break;
    }

    // tool_call, tool_result, session_created, session_completed can be
    // handled later as needed
    default:
      break;
  }
}

// In the ws.onmessage handler, replace the switch statement:
        switch (message.type) {
          case 'event':
            handleEvent(message.payload);
            break;

          case 'ping':
            ws.send(JSON.stringify({ type: 'pong' }));
            break;

          case 'backfill_complete':
            console.log('Backfill complete', message.count);
            break;

          case 'backfill_expired':
            console.warn('Backfill expired:', message.message);
            setLastEventId(null);
            break;

          case 'brainstorm':
            handleBrainstormMessage(message);
            break;

          default:
            console.warn('Unknown WebSocket message type:', message);
        }
```

Remove the dead `brainstorm_text`, `brainstorm_reasoning`, `brainstorm_message_complete`, and `brainstorm_artifact_created` case branches.

**Step 4: Run test to verify it passes**

Run: `cd dashboard && pnpm test:run -- useWebSocket.test.ts`
Expected: PASS

**Step 5: Run type-check to ensure no TypeScript errors**

Run: `cd dashboard && pnpm type-check`
Expected: PASS

**Step 6: Commit**

```bash
git add dashboard/src/hooks/useWebSocket.ts dashboard/src/hooks/__tests__/useWebSocket.test.ts
git commit -m "$(cat <<'EOF'
feat(websocket): add handleBrainstormMessage for unified event routing

- Exports handleBrainstormMessage() for brainstorm event handling
- Routes text, reasoning, message_complete, artifact_created events
- Removes dead brainstorm_* case branches that never matched
- Uses updateMessage for atomic message state updates

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Create Assistant Message Placeholder on Send

**Files:**
- Modify: `dashboard/src/hooks/useBrainstormSession.ts` (or equivalent send logic)
- Test: `dashboard/src/hooks/__tests__/useBrainstormSession.test.ts`

**Step 1: Locate the sendMessage implementation**

Find where the API call to send a brainstorm message is made and the assistant placeholder should be created.

**Step 2: Write failing test**

```typescript
// In the appropriate test file for send message logic
it('creates assistant placeholder with streaming status after sending', async () => {
  // Mock API response with message_id
  mockApi.sendBrainstormMessage.mockResolvedValue({ message_id: 'assistant-1' });

  await sendMessage('Hello');

  const messages = useBrainstormStore.getState().messages;
  const assistantMsg = messages.find(m => m.id === 'assistant-1');

  expect(assistantMsg).toBeDefined();
  expect(assistantMsg?.role).toBe('assistant');
  expect(assistantMsg?.content).toBe('');
  expect(assistantMsg?.status).toBe('streaming');
});
```

**Step 3: Implement placeholder creation**

After the API returns `message_id`, create the assistant placeholder:

```typescript
const response = await api.sendBrainstormMessage(sessionId, content);

// Create assistant placeholder with streaming status
const assistantMessage: BrainstormMessage = {
  id: response.message_id,
  session_id: sessionId,
  sequence: 0, // Will be updated by backend
  role: 'assistant',
  content: '',
  parts: null,
  created_at: new Date().toISOString(),
  status: 'streaming',
};
useBrainstormStore.getState().addMessage(assistantMessage);
useBrainstormStore.getState().setStreaming(true, response.message_id);
```

**Step 4: Run test to verify it passes**

Run: `cd dashboard && pnpm test:run -- useBrainstormSession.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/src/hooks/useBrainstormSession.ts dashboard/src/hooks/__tests__/useBrainstormSession.test.ts
git commit -m "$(cat <<'EOF'
feat(brainstorm): create assistant placeholder on send

Creates an assistant message with status='streaming' when the
API returns message_id, so WebSocket text events have a target
to append content to.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Integration Test - End-to-End Message Flow

**Files:**
- Test: `tests/integration/server/test_brainstorm_websocket.py` (new)

**Step 1: Write integration test**

```python
# tests/integration/server/test_brainstorm_websocket.py
import pytest
from httpx import AsyncClient, ASGITransport
from starlette.websockets import WebSocket
from amelia.server.main import app
from amelia.server.models.events import EventDomain


@pytest.mark.asyncio
async def test_brainstorm_events_use_dedicated_wire_format():
    """Brainstorm events arrive with type='brainstorm' over WebSocket."""
    # This test requires mocking the driver to emit events
    # and verifying the WebSocket receives the correct format

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        # Create a session
        response = await client.post("/api/brainstorm/sessions", json={
            "profile_id": "test-profile",
        })
        assert response.status_code == 200
        session_id = response.json()["id"]

        # Connect to WebSocket and send a message
        # Verify events arrive with type="brainstorm"
        # (Full implementation depends on test infrastructure)
```

**Step 2: Run integration test**

Run: `uv run pytest tests/integration/server/test_brainstorm_websocket.py -v`
Expected: PASS (or skip if infrastructure not available)

**Step 3: Commit**

```bash
git add tests/integration/server/test_brainstorm_websocket.py
git commit -m "$(cat <<'EOF'
test(integration): verify brainstorm WebSocket wire format

Adds integration test confirming brainstorm events arrive with
{type: "brainstorm", event_type: "text", ...} format over WebSocket.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Run Full Test Suite and Fix Any Issues

**Step 1: Run backend tests**

Run: `uv run pytest tests/ -v`
Expected: All tests pass

**Step 2: Run frontend tests**

Run: `cd dashboard && pnpm test:run`
Expected: All tests pass

**Step 3: Run type checks**

Run: `uv run mypy amelia && cd dashboard && pnpm type-check`
Expected: No type errors

**Step 4: Run linters**

Run: `uv run ruff check amelia tests && cd dashboard && pnpm lint`
Expected: No lint errors

**Step 5: Commit any fixes**

If any fixes were needed, commit them:

```bash
git add -A
git commit -m "$(cat <<'EOF'
fix: address test and lint issues from brainstorm routing

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Add EventDomain enum | `amelia/server/models/events.py` |
| 2 | Branch broadcast() on domain | `amelia/server/events/connection_manager.py` |
| 3 | Set domain=BRAINSTORM in BrainstormService | `amelia/server/services/brainstorm.py` |
| 4 | Update WebSocket types | `dashboard/src/types/index.ts` |
| 5 | Add updateMessage action | `dashboard/src/store/brainstormStore.ts` |
| 6 | Add handleBrainstormMessage | `dashboard/src/hooks/useWebSocket.ts` |
| 7 | Create assistant placeholder | `dashboard/src/hooks/useBrainstormSession.ts` |
| 8 | Integration test | `tests/integration/server/test_brainstorm_websocket.py` |
| 9 | Final test suite | All files |
