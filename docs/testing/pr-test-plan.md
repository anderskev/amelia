# Brainstorming Backend Manual Testing Plan

**Branch:** `feat/298-brainstorming-backend`
**Feature:** Backend API for brainstorming sessions with LLM integration

## Overview

This PR adds a complete brainstorming backend with:
- Session CRUD operations (`/api/brainstorm/sessions`)
- Real-time message exchange with LLM driver integration
- Artifact detection from file writes during brainstorming
- Handoff to implementation pipeline
- WebSocket event streaming for all brainstorm events

Manual testing is needed to verify the end-to-end flow works correctly with actual LLM responses and WebSocket streaming.

---

## Prerequisites

### Environment Setup

```bash
# 1. Install Python dependencies
cd /Users/ka/github/existential-birds/amelia-feature
uv sync

# 2. Use the local_haiku profile for testing
# This profile uses a fast, cost-effective model for manual testing

# 3. Start the backend server with test repo and profile
# test_repo_c is a scratch repo where artifact files can be safely created
uv run amelia server --reload --profile local_haiku --cwd /Users/ka/github/existential-birds/test_repo_c
# Server runs on http://localhost:8420

# 4. Verify server is running
curl http://localhost:8420/api/health
# Expected: {"status":"healthy",...}
```

### Testing Tools

- `curl` for API testing
- `websocat` for WebSocket testing (install via `brew install websocat` or `cargo install websocat`)

---

## Test Scenarios

### TC-01: Create Brainstorming Session

**Objective:** Verify session creation with initial goal

**Steps:**
1. Send POST request to create a new session
2. Verify response contains session ID and metadata

**Verification Commands:**
```bash
curl -X POST http://localhost:8420/api/brainstorm/sessions \
  -H "Content-Type: application/json" \
  -d '{"goal": "Design a user authentication system with OAuth2 support"}'
```

**Expected Result:**
- HTTP 201 Created
- Response contains:
  - `id`: UUID string
  - `goal`: Matches input
  - `status`: "active"
  - `created_at`: ISO timestamp
  - `messages`: Empty array initially

---

### TC-02: List Brainstorming Sessions

**Objective:** Verify session listing with optional status filter

**Steps:**
1. Create 2-3 sessions with different goals
2. List all sessions
3. Filter by status

**Verification Commands:**
```bash
# List all sessions
curl http://localhost:8420/api/brainstorm/sessions

# Filter by status (active sessions only)
curl "http://localhost:8420/api/brainstorm/sessions?status=active"
```

**Expected Result:**
- HTTP 200 OK
- Array of session objects
- Sessions sorted by `created_at` descending (most recent first)
- Filter returns only matching sessions

---

### TC-03: Get Session with History

**Objective:** Verify retrieving a session includes messages and artifacts

**Steps:**
1. Create a session
2. Send a message (TC-04)
3. Get session details

**Verification Commands:**
```bash
# Replace SESSION_ID with actual ID from TC-01
curl http://localhost:8420/api/brainstorm/sessions/{SESSION_ID}
```

**Expected Result:**
- HTTP 200 OK
- Response includes:
  - Session metadata (`id`, `goal`, `status`)
  - `messages`: Array of user/assistant messages
  - `artifacts`: Array of any detected artifacts

---

### TC-04: Send Message and Receive LLM Response

**Objective:** Verify message sending triggers LLM processing and returns response

**Steps:**
1. Create a session or use existing one
2. Send a message
3. Observe async processing via WebSocket

**Verification Commands:**
```bash
# Terminal 1: Connect to WebSocket for events
websocat ws://localhost:8420/ws/events

# Terminal 2: Send a message
curl -X POST http://localhost:8420/api/brainstorm/sessions/{SESSION_ID}/message \
  -H "Content-Type: application/json" \
  -d '{"content": "What authentication providers should we support?"}'
```

**Expected Result:**
- HTTP 202 Accepted (async processing)
- Response contains `message_id`
- WebSocket receives events:
  - `brainstorm_reasoning` (if model uses reasoning)
  - `brainstorm_text` (streaming text chunks)
  - `brainstorm_tool_call` (if LLM uses tools)
  - `brainstorm_tool_result` (tool execution results)
  - `brainstorm_message_complete` (final event with complete message)

---

### TC-05: Artifact Detection from File Writes

**Objective:** Verify artifacts are detected when LLM writes files

**Steps:**
1. Create a session about creating a design document
2. Send a message that prompts the LLM to write a file
3. Verify artifact is detected

**Verification Commands:**
```bash
# Create session
curl -X POST http://localhost:8420/api/brainstorm/sessions \
  -H "Content-Type: application/json" \
  -d '{"goal": "Create a technical specification for the auth system"}'

# Prompt LLM to write a spec file
curl -X POST http://localhost:8420/api/brainstorm/sessions/{SESSION_ID}/message \
  -H "Content-Type: application/json" \
  -d '{"content": "Please write the initial spec to a file called auth-spec.md"}'

# Check session for artifacts
curl http://localhost:8420/api/brainstorm/sessions/{SESSION_ID}
```

**Expected Result:**
- WebSocket receives `brainstorm_artifact_created` event
- Session response includes artifact in `artifacts` array with:
  - `path`: File path (e.g., `auth-spec.md`)
  - `artifact_type`: Detected type (e.g., `spec`, `code`, `design`)
  - `message_id`: ID of message that created it

---

### TC-06: Handoff to Implementation

**Objective:** Verify session can be handed off to implementation pipeline

**Steps:**
1. Create a session with an artifact (from TC-05)
2. Call handoff endpoint
3. Verify session status changes

**Verification Commands:**
```bash
# Handoff session to implementation
curl -X POST http://localhost:8420/api/brainstorm/sessions/{SESSION_ID}/handoff \
  -H "Content-Type: application/json" \
  -d '{"artifact_path": "auth-spec.md", "issue_title": "Implement OAuth2 Auth"}'

# Verify session status changed
curl http://localhost:8420/api/brainstorm/sessions/{SESSION_ID}
```

**Expected Result:**
- HTTP 200 OK
- Response contains `workflow_id` for implementation
- Session status changed to "completed"
- WebSocket receives `brainstorm_session_completed` event

---

### TC-07: Delete Session

**Objective:** Verify session deletion

**Steps:**
1. Create a new session
2. Delete it
3. Verify it's gone

**Verification Commands:**
```bash
# Create session
curl -X POST http://localhost:8420/api/brainstorm/sessions \
  -H "Content-Type: application/json" \
  -d '{"goal": "Temporary session for testing"}' | jq -r '.id'

# Delete session (replace ID)
curl -X DELETE http://localhost:8420/api/brainstorm/sessions/{SESSION_ID}

# Verify deleted
curl http://localhost:8420/api/brainstorm/sessions/{SESSION_ID}
```

**Expected Result:**
- DELETE returns HTTP 204 No Content
- GET returns HTTP 404 Not Found

---

### TC-08: Error Handling - Invalid Session

**Objective:** Verify proper error responses for invalid operations

**Verification Commands:**
```bash
# Get non-existent session
curl http://localhost:8420/api/brainstorm/sessions/invalid-uuid-12345

# Send message to non-existent session
curl -X POST http://localhost:8420/api/brainstorm/sessions/invalid-uuid-12345/message \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello"}'

# Handoff non-existent artifact
curl -X POST http://localhost:8420/api/brainstorm/sessions/{VALID_SESSION_ID}/handoff \
  -H "Content-Type: application/json" \
  -d '{"artifact_path": "nonexistent.md"}'
```

**Expected Result:**
- HTTP 404 Not Found for invalid session IDs
- HTTP 404 for invalid artifact in handoff
- Clear error messages in response body

---

### TC-09: WebSocket Event Streaming

**Objective:** Verify all brainstorm events are streamed correctly

**Steps:**
1. Connect to WebSocket
2. Perform various operations
3. Verify events are received

**Verification Commands:**
```bash
# Connect to WebSocket and observe events
websocat ws://localhost:8420/ws/events

# In another terminal, create session and send messages
# Events should appear in WebSocket terminal
```

**Expected Event Types:**
- `brainstorm_session_created` - When session is created
- `brainstorm_reasoning` - LLM reasoning tokens
- `brainstorm_text` - Response text chunks
- `brainstorm_tool_call` - When LLM calls a tool
- `brainstorm_tool_result` - Tool execution result
- `brainstorm_message_complete` - Message fully processed
- `brainstorm_artifact_created` - File artifact detected
- `brainstorm_session_completed` - Session handed off

---

### TC-10: Concurrent Message Handling

**Objective:** Verify only one message processes at a time per session

**Steps:**
1. Create a session
2. Send a message
3. Immediately send another message before first completes

**Verification Commands:**
```bash
# Send first message
curl -X POST http://localhost:8420/api/brainstorm/sessions/{SESSION_ID}/message \
  -H "Content-Type: application/json" \
  -d '{"content": "First question about the design"}'

# Immediately send second message
curl -X POST http://localhost:8420/api/brainstorm/sessions/{SESSION_ID}/message \
  -H "Content-Type: application/json" \
  -d '{"content": "Second question while first is processing"}'
```

**Expected Result:**
- Both return HTTP 202 Accepted
- Second message waits for first to complete (session-level locking)
- Messages appear in correct order in session history

---

## Test Environment Cleanup

After testing:
```bash
# Stop the server (Ctrl+C in terminal running server)

# Optional: Clean up test data
# Sessions are stored in ~/.amelia/amelia.db
rm ~/.amelia/amelia.db  # Warning: removes all data

# Clean up any files created in test repo during artifact tests
cd /Users/ka/github/existential-birds/test_repo_c
git checkout .  # Discard any created files
```

---

## Test Result Template

| Test ID | Description | Status | Notes |
|---------|-------------|--------|-------|
| TC-01 | Create session | [ ] Pass / [ ] Fail | |
| TC-02 | List sessions | [ ] Pass / [ ] Fail | |
| TC-03 | Get session with history | [ ] Pass / [ ] Fail | |
| TC-04 | Send message and receive response | [ ] Pass / [ ] Fail | |
| TC-05 | Artifact detection | [ ] Pass / [ ] Fail | |
| TC-06 | Handoff to implementation | [ ] Pass / [ ] Fail | |
| TC-07 | Delete session | [ ] Pass / [ ] Fail | |
| TC-08 | Error handling | [ ] Pass / [ ] Fail | |
| TC-09 | WebSocket streaming | [ ] Pass / [ ] Fail | |
| TC-10 | Concurrent message handling | [ ] Pass / [ ] Fail | |

---

## Agent Execution Notes

### For LLM Agent Executing This Plan:

1. **Start server** - Ensure `uv run amelia server --reload --profile local_haiku --cwd /Users/ka/github/existential-birds/test_repo_c` is running
2. **Execute tests sequentially** - Many tests build on previous state
3. **Capture session IDs** - Store IDs from creation for use in subsequent tests
4. **Monitor WebSocket** - Keep a WebSocket connection open to observe events
5. **Record actual responses** - Note any deviations from expected results

### Programmatic Testing (Python):

```python
import httpx

async with httpx.AsyncClient(base_url="http://localhost:8420") as client:
    # Create session
    resp = await client.post("/api/brainstorm/sessions", json={"goal": "Test"})
    session_id = resp.json()["id"]

    # Send message
    resp = await client.post(
        f"/api/brainstorm/sessions/{session_id}/message",
        json={"content": "Hello"}
    )
    message_id = resp.json()["message_id"]

    # Poll for completion or use WebSocket
```

---

## Key Changes in This Branch

The following changes should be verified through testing:

1. **API Routes** (`amelia/server/routes/brainstorm.py`):
   - POST `/sessions` - Create session
   - GET `/sessions` - List sessions with optional status filter
   - GET `/sessions/{id}` - Get session with messages and artifacts
   - DELETE `/sessions/{id}` - Delete session
   - POST `/sessions/{id}/message` - Send message (async)
   - POST `/sessions/{id}/handoff` - Handoff to implementation

2. **Service Layer** (`amelia/server/services/brainstorm.py`):
   - LLM driver integration for message processing
   - Artifact detection from `write_file` tool calls
   - Event emission for WebSocket streaming
   - Session-level locking for concurrent safety

3. **Data Models** (`amelia/server/models/brainstorm.py`):
   - `BrainstormingSession` - Session with status lifecycle
   - `Message` - User/assistant messages with parts
   - `Artifact` - Detected file artifacts with types

4. **Event Types** (`amelia/server/models/events.py`):
   - 8 new brainstorm event types for real-time updates
