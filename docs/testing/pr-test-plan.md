# Claude Streaming Dashboard Manual Testing Plan

**Branch:** `fix/82-claude-streaming-dashboard`
**Feature:** Real-time streaming of Claude LLM execution events to the dashboard

## Overview

This PR implements end-to-end streaming of Claude Code CLI output to the Amelia dashboard. When agents (architect, developer, reviewer) execute, their thinking, tool calls, and outputs are streamed in real-time via WebSocket to the frontend. Key changes include:

1. **Backend**: New `StreamEvent` type with UUID `id` field, `StreamEmitter` callback passed to agents, `broadcast_stream()` in connection manager
2. **Frontend**: New `stream-store` Zustand store, updated `useWebSocket` hook to handle `stream` messages, `LogsPage` with filtering and auto-scroll, `ActivityLog` live mode integration
3. **Agents**: `workflow_id` is now required on all agent methods, stream emitter callbacks integrated into architect/developer/reviewer

Manual testing is needed because:
- WebSocket streaming behavior is difficult to fully capture in unit tests
- Visual verification of the dashboard UI during live execution
- End-to-end flow from CLI driver through orchestrator to dashboard

---

## Prerequisites

### Environment Setup

```bash
# 1. Install Python dependencies
cd /Users/ka/github/amelia-feature
uv sync

# 2. Start the backend server
uv run amelia server --reload
# Server runs on http://localhost:8420 by default

# 3. For dashboard testing (general usage - no frontend changes)
# Dashboard is served at localhost:8420 by the backend server above

# 3b. For frontend development with HMR (only if modifying dashboard code)
cd dashboard
pnpm install
pnpm run dev
# Vite dev server runs on localhost:8421, proxies API to backend

# 4. Verify setup
curl http://localhost:8420/api/health
# Expected: {"status":"healthy"}
```

### Testing Tools

- Browser DevTools (Network tab for WebSocket inspection)
- Terminal for running CLI commands
- A valid issue ID from your configured tracker (or use `noop` tracker)

---

## Test Scenarios

### TC-01: StreamEvent UUID Generation

**Objective:** Verify that each StreamEvent has a unique auto-generated UUID `id` field

**Steps:**
1. Start the backend server
2. Open browser to http://localhost:8420
3. Open DevTools → Network → WS tab
4. Start a workflow using the CLI:
   ```bash
   uv run amelia start TEST-123 --profile <your-profile>
   ```
5. Observe WebSocket messages with `type: "stream"`

**Expected Result:**
- Each stream event payload contains an `id` field
- The `id` is a valid UUID (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
- Each event has a unique `id` (no duplicates)

**Verification Commands:**
```bash
# In browser console, after receiving events:
# Check that stream events have id field
```

---

### TC-02: StreamEvent Type Mapping (type → subtype)

**Objective:** Verify that `StreamEvent.type` is correctly mapped to `subtype` in WebSocket payloads

**Steps:**
1. With backend running and WebSocket connected
2. Trigger an agent execution (start a workflow)
3. Inspect WebSocket messages in DevTools

**Expected Result:**
- WebSocket messages have wrapper `type: "stream"`
- Payload has `subtype` field (not `type`)
- Valid subtypes: `claude_thinking`, `claude_tool_call`, `claude_tool_result`, `agent_output`

---

### TC-03: LogsPage Stream Event Display

**Objective:** Verify the LogsPage displays stream events with correct visual styling

**Steps:**
1. Navigate to http://localhost:8420/logs
2. Start a workflow from another terminal
3. Observe events appearing in the logs page

**Expected Result:**
- Events appear in real-time without page refresh
- Each event type has distinct color/icon:
  - `claude_thinking`: Yellow brain icon, yellow background
  - `claude_tool_call`: Blue wrench icon, blue background
  - `claude_tool_result`: Green check icon, green background
  - `agent_output`: Purple message icon, purple background
- Events show timestamp, agent name, and content/tool_name

---

### TC-04: LogsPage Event Filtering

**Objective:** Verify event type filtering works correctly

**Steps:**
1. Navigate to http://localhost:8420/logs
2. Ensure there are events in the log (run a workflow if needed)
3. Click the filter button
4. Toggle different event types on/off

**Expected Result:**
- Filter dropdown shows all 4 event types
- Unchecking a type hides those events immediately
- Re-checking shows them again
- Filter state persists while on the page

---

### TC-05: LogsPage Auto-Scroll Behavior

**Objective:** Verify auto-scroll to bottom works correctly in live mode

**Steps:**
1. Navigate to http://localhost:8420/logs
2. Generate enough events to enable scrolling (run a workflow)
3. Scroll up manually
4. Observe new events arriving

**Expected Result:**
- When scrolled to bottom: new events auto-scroll into view
- When scrolled up: new events do NOT force scroll to bottom
- "Scroll to bottom" button appears when not at bottom
- Clicking the button scrolls to bottom and resumes auto-scroll

---

### TC-06: LogsPage Clear Events

**Objective:** Verify clearing events works correctly

**Steps:**
1. Navigate to http://localhost:8420/logs
2. Ensure there are events displayed
3. Click the trash/clear button

**Expected Result:**
- All events are immediately cleared
- Empty state message is displayed
- New incoming events appear normally after clearing

---

### TC-07: ActivityLog Live Mode Integration

**Objective:** Verify ActivityLog shows stream events when live mode is enabled

**Steps:**
1. Navigate to a workflow detail page (http://localhost:8420/workflows/{id})
2. Enable live mode toggle (if present)
3. Trigger agent execution for that workflow

**Expected Result:**
- Stream events appear interleaved with workflow events chronologically
- Stream events have distinct visual styling (lightning icon, primary color)
- Format: timestamp, [AGENT], tool_name or content
- Events for OTHER workflows do NOT appear

---

### TC-08: workflow_id Required Validation

**Objective:** Verify agents reject execution without workflow_id

**Steps:**
1. Attempt to call an agent method without workflow_id (via test or direct API call)

**Expected Result:**
- Agent raises a validation error
- Error message indicates workflow_id is required

**Verification Commands:**
```bash
# Run existing unit tests that verify this
uv run pytest tests/unit/agents/test_architect.py -k "workflow_id" -v
uv run pytest tests/unit/agents/test_developer.py -k "workflow_id" -v
uv run pytest tests/unit/agents/test_reviewer.py -k "workflow_id" -v
```

---

### TC-09: Stream Emitter Error Handling

**Objective:** Verify stream emitter errors don't crash agent execution

**Steps:**
1. Review the stream emitter implementation
2. Verify error handling in connection manager

**Expected Result:**
- Stream emitter catches and logs errors
- Agent execution continues even if streaming fails
- Disconnected clients are cleaned up

**Verification Commands:**
```bash
# Run integration tests
uv run pytest tests/integration/test_stream_emitter_integration.py -v
uv run pytest tests/integration/test_stream_propagation.py -v
```

---

### TC-10: formatTime Null Handling

**Objective:** Verify formatTime utility handles null/undefined/invalid timestamps

**Steps:**
1. Verify the fix handles edge cases

**Expected Result:**
- `formatTime(null)` returns `"--:--:--"`
- `formatTime(undefined)` returns `"--:--:--"`
- `formatTime("invalid")` returns `"--:--:--"`
- Valid timestamps format correctly

**Verification Commands:**
```bash
cd dashboard
pnpm test -- --run src/lib/__tests__/utils.test.ts
```

---

### TC-11: React Key Uniqueness

**Objective:** Verify React list keys use event.id for stability

**Steps:**
1. Open browser DevTools Console
2. Navigate to LogsPage or ActivityLog with events
3. Check for React key warnings

**Expected Result:**
- No React warnings about duplicate keys
- No warnings about missing keys
- Event items use `event.id` as key

---

### TC-12: Stream Store Buffer Limit

**Objective:** Verify stream store respects MAX_STREAM_EVENTS (1000) limit

**Steps:**
1. Generate many stream events (long-running workflow)
2. Check stream store state

**Expected Result:**
- Store never holds more than 1000 events
- Oldest events are trimmed when limit exceeded
- Most recent events are preserved

**Verification Commands:**
```bash
cd dashboard
pnpm test -- --run src/store/__tests__/stream-store.test.ts
```

---

## Test Environment Cleanup

After testing:
```bash
# Stop any running processes
# Ctrl+C on backend server
# Ctrl+C on frontend dev server (if running)

# Reset state if needed
# Stream events are ephemeral (not persisted), no cleanup needed
```

---

## Test Result Template

| Test ID | Description | Status | Notes |
|---------|-------------|--------|-------|
| TC-01 | StreamEvent UUID Generation | [ ] Pass / [ ] Fail | |
| TC-02 | StreamEvent Type Mapping | [ ] Pass / [ ] Fail | |
| TC-03 | LogsPage Stream Display | [ ] Pass / [ ] Fail | |
| TC-04 | LogsPage Event Filtering | [ ] Pass / [ ] Fail | |
| TC-05 | LogsPage Auto-Scroll | [ ] Pass / [ ] Fail | |
| TC-06 | LogsPage Clear Events | [ ] Pass / [ ] Fail | |
| TC-07 | ActivityLog Live Mode | [ ] Pass / [ ] Fail | |
| TC-08 | workflow_id Required | [ ] Pass / [ ] Fail | |
| TC-09 | Stream Emitter Errors | [ ] Pass / [ ] Fail | |
| TC-10 | formatTime Null Handling | [ ] Pass / [ ] Fail | |
| TC-11 | React Key Uniqueness | [ ] Pass / [ ] Fail | |
| TC-12 | Stream Store Buffer | [ ] Pass / [ ] Fail | |

---

## Agent Execution Notes

### For LLM Agent Executing This Plan:

1. **Start backend first** - `uv run amelia server --reload`
2. **Execute tests sequentially** - Some tests depend on having events in the store
3. **Capture WebSocket traffic** - Use browser DevTools for verification
4. **Run automated tests** - Use provided pytest/vitest commands where applicable
5. **Mark results** - Update the result template after each test
6. **Report issues** - Note any failures with exact error messages

### Programmatic Verification

```python
# Python: Verify StreamEvent has id field
from amelia.core.types import StreamEvent, StreamEventType
from datetime import datetime

event = StreamEvent(
    type=StreamEventType.CLAUDE_THINKING,
    content="test",
    timestamp=datetime.now(),
    agent="test",
    workflow_id="wf-123"
)
assert event.id is not None
assert len(event.id) == 36  # UUID length
```

```typescript
// TypeScript: Verify stream store works
import { useStreamStore } from '@/store/stream-store';

const store = useStreamStore.getState();
store.addEvent({ /* mock event */ });
expect(store.events.length).toBe(1);
```

---

## Key Changes in This Branch

The following changes should be verified through testing:

1. **StreamEvent model** (`amelia/core/types.py`):
   - New `id` field with auto-generated UUID
   - `StreamEventType` enum for event types
   - `StreamEmitter` type alias

2. **Connection Manager** (`amelia/server/events/connection_manager.py`):
   - New `broadcast_stream()` method
   - `_send_to_client()` helper extracted
   - Converts `type` to `subtype` in WebSocket payload

3. **Agent changes** (`amelia/agents/*.py`):
   - `workflow_id` now required parameter
   - `stream_emitter` callback support
   - All agents: architect, developer, reviewer

4. **Dashboard store** (`dashboard/src/store/stream-store.ts`):
   - New Zustand store for stream events
   - 1000 event buffer limit
   - Live mode toggle

5. **LogsPage** (`dashboard/src/pages/LogsPage.tsx`):
   - Real-time stream event viewer
   - Filtering by event type
   - Auto-scroll behavior
   - Clear events functionality

6. **ActivityLog** (`dashboard/src/components/ActivityLog.tsx`):
   - Live mode integration
   - Interleaved workflow + stream events
   - Chronological sorting

7. **useWebSocket hook** (`dashboard/src/hooks/useWebSocket.ts`):
   - Handles `stream` message type
   - Dispatches to stream store
