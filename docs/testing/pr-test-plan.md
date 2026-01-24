# Brainstormer Prompt Architecture Refactor Manual Testing Plan

**Branch:** `refactor/330-brainstormer-prompt-architecture`
**Feature:** Proper system/user prompt separation in brainstormer

## Overview

This PR refactors the brainstormer prompt architecture to properly separate system and user prompts:

1. **Removed `prime_session` endpoint and flow** - No longer sends a separate priming message
2. **Added `BRAINSTORMER_SYSTEM_PROMPT` constant** - System instructions passed via `instructions` parameter
3. **Added `BRAINSTORMER_USER_PROMPT_TEMPLATE`** - First user message wrapped with "Help me design: {idea}"
4. **Removed `is_system` field from Message model** - No longer needed with proper separation
5. **API Driver fix** - Always pass system prompt (LLM APIs are stateless)
6. **Dashboard changes** - Removed "Start Brainstorming" button; input always visible

Manual testing is critical because this changes the core interaction flow with the LLM.

---

## Prerequisites

### Environment Setup

```bash
# 1. Verify test repository exists
cd /Users/ka/github/existential-birds
ls test_repo_c  # Should exist

# 2. Install Python dependencies
cd amelia
uv sync
```

### Profile Configuration

Profiles are created via the API. After starting the server, create the test profiles:

```bash
# Create CLI driver profile for TC-03, TC-04
curl -s -X POST http://localhost:8420/api/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-cli",
    "tracker": "noop",
    "working_dir": "/Users/ka/github/existential-birds/test_repo_c",
    "agents": {
      "brainstormer": {
        "driver": "cli:claude",
        "model": "sonnet"
      }
    }
  }'

# Create API driver profile for TC-01, TC-02, TC-09
curl -s -X POST http://localhost:8420/api/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-api",
    "tracker": "noop",
    "working_dir": "/Users/ka/github/existential-birds/test_repo_c",
    "agents": {
      "brainstormer": {
        "driver": "api:openrouter",
        "model": "anthropic/claude-sonnet-4"
      }
    }
  }'

# Verify profiles were created
curl -s http://localhost:8420/api/profiles | jq '.[].id'
# Should show: "test-cli" and "test-api"
```

**Important:**
- Both profiles use `test_repo_c` as the working directory to avoid modifying the Amelia codebase
- The `test-cli` profile requires Claude CLI to be installed and authenticated
- The `test-api` profile requires `OPENROUTER_API_KEY` environment variable to be set
- Use `sonnet` model to keep costs low during testing
- Profiles persist in the database (`~/.amelia/amelia.db`) across server restarts

### Start the Server

```bash
# Start the backend server
uv run amelia server --reload
# Server runs on http://localhost:8420

# Verify server is running
curl http://localhost:8420/health
```

After starting the server, create the test profiles using the commands in the Profile Configuration section above.

### Testing Tools

- **Browser** - Chrome/Firefox with DevTools open
- **curl** - For API testing
- **Dashboard** - Available at http://localhost:8420

---

## Test Scenarios

### TC-01: New Session First Message (API Driver)

**Objective:** Verify the first user message is wrapped with "Help me design:" template and system prompt is passed correctly.

**Preconditions:**
- Server running with `test-api` profile active
- Test repo at `/Users/ka/github/existential-birds/test_repo_c`
- `OPENROUTER_API_KEY` environment variable set

**Steps:**
1. Open http://localhost:8420 in browser
2. Select the `test-api` profile from the profile selector
3. From the sidebar, ensure no active session (or start fresh)
4. Type a simple idea in the input (e.g., "a todo list app")
5. Press Enter or click Submit
6. Observe the response

**Expected Result:**
- Session is created automatically when first message is sent
- LLM receives system prompt (BRAINSTORMER_SYSTEM_PROMPT) as instructions
- LLM receives user prompt formatted as "Help me design: a todo list app"
- LLM responds with brainstorming guidance (asks clarifying questions, explores requirements)
- No separate "greeting" message before user input

**Verification Commands:**
```bash
# Check server logs for prompt formatting
# Look for log entries showing the formatted_prompt
tail -f ~/.amelia/logs/server.log | grep -i "brainstorm\|prompt\|instructions"
```

---

### TC-02: Subsequent Messages in Session (API Driver)

**Objective:** Verify subsequent messages are NOT wrapped with template but system prompt is always passed.

**Steps:**
1. Continue from TC-01 with existing session
2. Send a follow-up message (e.g., "I want it to support categories")
3. Observe the response

**Expected Result:**
- Message is sent as-is (not wrapped with "Help me design:")
- System prompt is still passed to the API (verified via logs or response quality)
- Context is maintained from previous messages
- Response is coherent with conversation history

**Verification:**
```bash
# Monitor logs for prompt formatting
# Should see the raw message content, not wrapped
```

---

### TC-03: New Session First Message (CLI Driver)

**Objective:** Verify the same behavior works with CLI driver (e.g., `cli:claude`)

**Preconditions:**
- Server running with `test-cli` profile active
- Claude CLI installed and authenticated

**Steps:**
1. Open http://localhost:8420 in browser
2. Select the `test-cli` profile from the profile selector
3. Start a new session (create new or use empty session)
4. Type an idea (e.g., "a recipe management app")
5. Press Enter or click Submit

**Expected Result:**
- Session created automatically
- CLI driver receives system prompt in `instructions` parameter
- First message wrapped with "Help me design:" template
- LLM responds appropriately with brainstorming guidance

**Verification:**
```bash
# CLI driver logs show the instructions being passed
# Response demonstrates understanding of brainstorming context
```

---

### TC-04: Subsequent Messages in Session (CLI Driver)

**Objective:** Verify subsequent messages work correctly with CLI driver.

**Steps:**
1. Continue from TC-03 with existing session
2. Send a follow-up message (e.g., "What database would you recommend?")
3. Observe the response

**Expected Result:**
- Message sent without wrapper
- System prompt still included (CLI maintains conversation context)
- Contextual response referencing previous discussion

---

### TC-05: Dashboard UI - No "Start Brainstorming" Button

**Objective:** Verify the "Start Brainstorming" button has been removed.

**Steps:**
1. Open http://localhost:8420
2. Navigate to Spec Builder page
3. Observe the empty state (no active session)

**Expected Result:**
- NO "Start Brainstorming" button visible
- Empty state shows text: "Type your idea below to begin exploring and producing design documents."
- Input area is ALWAYS visible at the bottom (not hidden when no session)
- User can start typing immediately

**Screenshot locations to verify:**
- Empty state hero area
- Bottom input area (always visible)

---

### TC-06: Session Creation via First Message

**Objective:** Verify a new session is created when user sends first message.

**Steps:**
1. Open fresh browser tab to http://localhost:8420
2. Navigate to Spec Builder (no active session)
3. Type an idea in the input and submit
4. Observe sidebar

**Expected Result:**
- New session appears in sidebar after first message
- Session is marked as active
- Conversation displays the user message and assistant response
- No intermediate "priming" or "system" messages visible

---

### TC-07: Message History Retrieval

**Objective:** Verify `is_system` field removal doesn't break history retrieval.

**Steps:**
1. Create a session and send 2-3 messages (use TC-01/TC-02)
2. Refresh the browser page
3. Select the same session from sidebar

**Expected Result:**
- All messages load correctly
- Messages display in correct order
- No errors in browser console about missing fields
- Conversation is fully readable

**Verification:**
```bash
# Check API response structure
curl http://localhost:8420/api/brainstorm/sessions/{session_id}/messages | jq
# Should show messages without is_system field
```

---

### TC-08: Write Design Doc Artifact Detection

**Objective:** Verify artifact detection still works (write_design_doc tool).

**Steps:**
1. Start a new brainstorming session
2. Guide conversation toward producing a design document:
   - "I want to build a simple REST API for user management"
   - "Yes, let's start with the design doc"
   - "Please write the design document"
3. Wait for LLM to use write_design_doc tool

**Expected Result:**
- Design document file is created in the working directory
- Artifact appears in the session artifacts panel
- Artifact event is emitted and visible in dashboard

**Note:** This test may take longer as it requires guiding the LLM to produce output.

---

### TC-09: API Driver - System Prompt Always Passed

**Objective:** Verify the fix that always passes system prompt (not just on new sessions).

**Preconditions:**
- `test-api` profile selected
- Server logs visible (`tail -f /tmp/amelia-server.log` or server console)

**Steps:**
1. Select `test-api` profile
2. Create session and send multiple messages (at least 3)
3. Check server logs for each request

**Expected Result:**
- Every request to the LLM API includes the system prompt
- Logs show `effective_system_prompt` is populated for ALL messages
- Response quality remains consistent across messages

**Verification:**
```bash
# In logs, look for:
# - "instructions=" parameter should be non-empty for all requests
# - Previously, subsequent messages had empty instructions
```

---

### TC-10: Cross-Profile Switching

**Objective:** Verify brainstorming works when switching between API and CLI profiles.

**Preconditions:**
- Both `test-api` and `test-cli` profiles configured
- Server running with both profiles available

**Steps:**
1. Select `test-api` profile, start session, send a message
2. Close the session
3. Switch to `test-cli` profile from profile selector
4. Start new session, send a message

**Expected Result:**
- Both sessions work correctly
- System prompt is passed in both cases
- First message is wrapped in both cases
- No errors or unexpected behavior during switch

---

## Test Environment Cleanup

After testing:
```bash
# Stop the server (Ctrl+C in terminal)

# Optionally clean up test profiles (while server is running)
curl -s -X DELETE http://localhost:8420/api/profiles/test-cli
curl -s -X DELETE http://localhost:8420/api/profiles/test-api

# Optionally clean up test sessions
# Sessions are stored in ~/.amelia/amelia.db

# View session data (SQLite)
sqlite3 ~/.amelia/amelia.db "SELECT id, name, profile_id FROM brainstorm_sessions ORDER BY created_at DESC LIMIT 10;"

# Delete test sessions if needed
sqlite3 ~/.amelia/amelia.db "DELETE FROM brainstorm_messages WHERE session_id IN (SELECT id FROM brainstorm_sessions WHERE name LIKE '%test%');"
sqlite3 ~/.amelia/amelia.db "DELETE FROM brainstorm_sessions WHERE name LIKE '%test%';"
```

---

## Test Result Template

| Test ID | Description | Driver | Status | Notes |
|---------|-------------|--------|--------|-------|
| TC-01 | New session first message | API | [ ] Pass / [ ] Fail | |
| TC-02 | Subsequent messages | API | [ ] Pass / [ ] Fail | |
| TC-03 | New session first message | CLI | [ ] Pass / [ ] Fail | |
| TC-04 | Subsequent messages | CLI | [ ] Pass / [ ] Fail | |
| TC-05 | No "Start Brainstorming" button | N/A | [ ] Pass / [ ] Fail | |
| TC-06 | Session creation via first message | Both | [ ] Pass / [ ] Fail | |
| TC-07 | Message history retrieval | Both | [ ] Pass / [ ] Fail | |
| TC-08 | Write design doc artifact | Either | [ ] Pass / [ ] Fail | |
| TC-09 | System prompt always passed | API | [ ] Pass / [ ] Fail | |
| TC-10 | Cross-profile switching | Both | [ ] Pass / [ ] Fail | |

---

## Agent Execution Notes

### For LLM Agent Executing This Plan:

1. **Start server first** - Run `uv run amelia server --reload` before creating profiles
2. **Create profiles via API** - Use the curl commands in the Profile Configuration section to create `test-cli` and `test-api` profiles
3. **Verify working directory** - Both profiles must have `working_dir` set to `/Users/ka/github/existential-birds/test_repo_c` to avoid modifying the Amelia codebase
4. **Test both drivers** - Run TC-01/02 with `test-api` profile, TC-03/04 with `test-cli` profile
5. **Capture evidence** - Take screenshots or log excerpts for verification
6. **Sequential execution** - Some tests build on previous session state
7. **Log monitoring** - Keep `tail -f ~/.amelia/logs/server.log` running during tests

### Automated Verification (where applicable)

```bash
# Verify API response for session messages (no is_system field)
curl http://localhost:8420/api/brainstorm/sessions | jq '.[0].id' -r | xargs -I {} curl http://localhost:8420/api/brainstorm/sessions/{}/messages | jq '.[] | keys'

# Check that prime_session endpoint is removed (should 404)
curl -X POST http://localhost:8420/api/brainstorm/sessions/test-id/prime
# Expected: 404 Not Found or method not allowed
```

---

## Key Changes in This Branch

The following changes should be verified through testing:

1. **Prompt separation** (`amelia/server/services/brainstorm.py`):
   - `BRAINSTORMER_SYSTEM_PROMPT` constant added (line ~200)
   - `BRAINSTORMER_USER_PROMPT_TEMPLATE` added (line ~247)
   - `send_message` passes instructions parameter (line ~666)
   - First message detection and wrapping (lines ~633-636)

2. **Prime session removal** (`amelia/server/routes/brainstorm.py`):
   - `POST /sessions/{id}/prime` endpoint removed
   - `PrimeSessionResponse` model removed

3. **API Driver fix** (`amelia/drivers/api/deepagents.py`):
   - Always passes system prompt (lines ~385)
   - Previously only passed on new sessions

4. **Dashboard UI** (`dashboard/src/pages/SpecBuilderPage.tsx`):
   - "Start Brainstorming" button removed
   - Input area always visible
   - Updated empty state text

5. **Model/Repository cleanup**:
   - `is_system` field removed from Message model
   - Repository no longer handles `is_system` field
