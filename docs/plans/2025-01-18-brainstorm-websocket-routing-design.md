# Brainstorm WebSocket Event Routing Design

## Problem

Brainstorm agent responses don't appear in the UI until navigating away and back. The data shows in server logs but never reaches the brainstormStore.

**Root cause:** Backend sends all events wrapped as `{type: "event", payload: <WorkflowEvent>}`. Frontend expects brainstorm events with `type: "brainstorm_text"` at the top level. The mismatch means brainstorm events fall through to workflowStore instead of brainstormStore.

**Secondary issue:** `appendMessageContent` needs an existing message, but no assistant message placeholder is created when the API returns `message_id`.

## Solution

Separate brainstorm events at the wire protocol level with a dedicated `brainstorm` message type.

## Design

### Message Format

```typescript
type BrainstormMessage = {
  type: 'brainstorm';
  event_type: 'text' | 'reasoning' | 'tool_call' | 'tool_result' | 'message_complete' | 'artifact_created' | 'session_created' | 'session_completed';
  session_id: string;
  message_id?: string;  // Present for streaming events, absent for session-level events
  data: Record<string, unknown>;
  timestamp: string;
};
```

Key differences from workflow events:
- No `workflow_id` — brainstorm uses `session_id`
- No `sequence` — no gap detection needed for chat streaming
- No `level` — all brainstorm events are user-facing
- Flat `data` field — no nested `payload` wrapper

### Backend Changes

**Add domain to WorkflowEvent** (`amelia/server/models/events.py`):

```python
class EventDomain(StrEnum):
    WORKFLOW = "workflow"
    BRAINSTORM = "brainstorm"

class WorkflowEvent(BaseModel):
    domain: EventDomain = EventDomain.WORKFLOW
    # ... rest unchanged
```

**BrainstormService sets domain** when emitting events:

```python
WorkflowEvent(
    domain=EventDomain.BRAINSTORM,
    event_type=EventType.BRAINSTORM_TEXT,
    # ...
)
```

**ConnectionManager.broadcast() branches on domain** (`amelia/server/events/connection_manager.py`):

```python
if event.domain == EventDomain.BRAINSTORM:
    payload = {
        "type": "brainstorm",
        "event_type": event.event_type.value.removeprefix("brainstorm_"),
        "session_id": event.data.get("session_id"),
        "message_id": event.data.get("message_id"),
        "data": event.data,
        "timestamp": event.timestamp.isoformat(),
    }
else:
    payload = {
        "type": "event",
        "payload": event.model_dump(mode="json"),
    }
```

### Frontend Changes

**Update WebSocket message type** (`dashboard/src/types/index.ts`):

```typescript
type BrainstormEventType =
  | 'text'
  | 'reasoning'
  | 'tool_call'
  | 'tool_result'
  | 'message_complete'
  | 'artifact_created'
  | 'session_created'
  | 'session_completed';

type BrainstormMessage = {
  type: 'brainstorm';
  event_type: BrainstormEventType;
  session_id: string;
  message_id?: string;
  data: Record<string, unknown>;
  timestamp: string;
};

export type WebSocketMessage =
  | { type: 'event'; payload: WorkflowEvent }
  | BrainstormMessage
  | { type: 'ping' }
  // ... other existing types
```

**Add handler in `useWebSocket.ts`:**

```typescript
case 'brainstorm':
  handleBrainstormMessage(message);
  break;
```

**New `handleBrainstormMessage` function:**

```typescript
function handleBrainstormMessage(msg: BrainstormMessage) {
  const state = useBrainstormStore.getState();
  if (msg.session_id !== state.activeSessionId) return;

  switch (msg.event_type) {
    case 'text':
      state.updateMessage(msg.message_id!, m => ({
        ...m,
        status: undefined,
        content: m.content + (msg.data.text as string),
      }));
      break;

    case 'reasoning':
      state.updateMessage(msg.message_id!, m => ({
        ...m,
        reasoning: (m.reasoning ?? '') + (msg.data.text as string),
      }));
      break;

    case 'message_complete':
      const error = msg.data.error as string | undefined;
      state.updateMessage(msg.message_id!, m => ({
        ...m,
        status: error ? 'error' : undefined,
        errorMessage: error,
      }));
      state.setStreaming(false);
      break;

    // ... other cases
  }
}
```

**Remove dead `case 'brainstorm_text'` branches** that currently exist but never match.

### Assistant Message Placeholder

Create the assistant message placeholder when the send API returns:

```typescript
sendMessage: async (content: string) => {
  const userMessage = { id: generateId(), role: 'user', content };
  set((state) => ({
    messages: [...state.messages, userMessage],
    isStreaming: true,
  }));

  const response = await api.sendBrainstormMessage(sessionId, content);

  // Create assistant placeholder with the returned message_id
  const assistantMessage = {
    id: response.message_id,
    role: 'assistant',
    content: '',
    status: 'streaming' as const,
  };
  set((state) => ({
    messages: [...state.messages, assistantMessage]
  }));
}
```

### Message Type with Status

```typescript
type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  reasoning?: string;
  status?: 'streaming' | 'error';  // undefined = complete/idle
  errorMessage?: string;           // Human-readable error text
};
```

- `status: 'streaming'` — UI shows shimmer/loading indicator
- `status: 'error'` — UI shows error state, `errorMessage` contains details
- `status: undefined` — message is complete

### Error Handling

Errors during streaming are communicated via `message_complete` with an optional `error` field:

```python
WorkflowEvent(
    domain=EventDomain.BRAINSTORM,
    event_type=EventType.BRAINSTORM_MESSAGE_COMPLETE,
    data={
        "message_id": msg_id,
        "error": "Connection to LLM failed"  # Optional, present on failure
    },
)
```

This aligns with the ai-elements `ChatStatus` pattern where error display is delegated to parent components.

## Testing

**Backend integration test** (add to existing BrainstormService tests):
- Send a message → assert WebSocket receives `{type: "brainstorm", event_type: "text", ...}`
- Complete a message → assert `message_complete` event arrives with expected shape
- Trigger an error → assert `message_complete` includes `error` field

**Frontend tests:**

1. WebSocket handler test:
   - `{type: "brainstorm", ...}` routes to brainstormStore
   - `{type: "event", ...}` routes to workflowStore (unchanged)

2. Store tests:
   - `sendMessage` creates assistant placeholder with `status: 'streaming'`
   - Text events append content and clear loading state
   - `message_complete` with error sets `status: 'error'`

3. Component tests:
   - Shimmer shown when `status: 'streaming'`
   - Error state shown when `status: 'error'`

## Files Changed

### Backend
- `amelia/server/models/events.py` — Add `EventDomain` enum and `domain` field to `WorkflowEvent`
- `amelia/server/events/connection_manager.py` — Branch on domain in `broadcast()`
- `amelia/server/services/brainstorm.py` — Set `domain=EventDomain.BRAINSTORM` on all events

### Frontend
- `dashboard/src/types/index.ts` — Add `BrainstormMessage` type, update `Message` type
- `dashboard/src/hooks/useWebSocket.ts` — Add `case 'brainstorm'` handler, remove dead branches
- `dashboard/src/store/brainstormStore.ts` — Add `updateMessage` action, update `sendMessage` to create placeholder
