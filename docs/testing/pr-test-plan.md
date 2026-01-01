# Agent Prompt Configuration Manual Testing Plan

**Branch:** `feat/agent-prompt-configuration`
**Feature:** Dashboard UI for editing agent system prompts with version tracking

## Overview

This PR adds the ability to customize agent prompts (Architect, Reviewer) through the dashboard UI. Key functionality:

1. **Prompts API** - REST endpoints for listing, viewing, editing, and resetting prompts
2. **Prompt Resolution** - System resolves custom versions from DB or falls back to hardcoded defaults
3. **Agent Integration** - Prompts are injected into agents at workflow startup
4. **Dashboard UI** - Settings page with prompt cards, edit modal, and reset confirmation
5. **Version History** - Each edit creates a new version; workflows record which versions they used

Manual testing is needed because:
- End-to-end flow involves database, API, frontend, and agent coordination
- UI interactions (modal, dialogs, toasts) require visual verification
- Version tracking needs verification across multiple edits
- Fallback behavior when database has no custom versions

---

## Prerequisites

### Environment Setup

```bash
# 1. Install Python dependencies
cd /Users/ka/github/existential-birds/amelia-feature
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

# 4. Verify setup - API should return prompts
curl http://localhost:8420/api/prompts | jq
```

### Testing Tools

- Browser (Chrome/Firefox/Safari)
- `curl` or `httpie` for API testing
- `jq` for JSON formatting (optional)

---

## Test Scenarios

### TC-01: List All Prompts

**Objective:** Verify prompts API returns all hardcoded prompts with default status

**Steps:**
1. Start the server (`uv run amelia server --reload`)
2. Make GET request to `/api/prompts`
3. Verify response contains all expected prompts

**Expected Result:**
- Response contains 4 prompts: `architect.system`, `architect.plan`, `reviewer.structured`, `reviewer.agentic`
- Each prompt has `current_version_id: null` (indicating default)
- Each prompt has correct `agent`, `name`, and `description`

**Verification Commands:**
```bash
curl -s http://localhost:8420/api/prompts | jq '.prompts | length'
# Expected: 4

curl -s http://localhost:8420/api/prompts | jq '.prompts[] | {id, agent, current_version_id}'
# Expected: All prompts with current_version_id: null
```

---

### TC-02: Get Default Content

**Objective:** Verify default content endpoint returns hardcoded prompt content

**Steps:**
1. Make GET request to `/api/prompts/architect.system/default`
2. Verify response contains the hardcoded default content

**Expected Result:**
- Response includes `prompt_id`, `name`, `description`, `content`
- `content` matches hardcoded default in `amelia/agents/prompts/defaults.py`

**Verification Commands:**
```bash
curl -s http://localhost:8420/api/prompts/architect.system/default | jq '{name, content: (.content | length)}'
# Expected: name="Architect System Prompt", content length > 0

curl -s http://localhost:8420/api/prompts/reviewer.agentic/default | jq '.name'
# Expected: "Reviewer Agentic Prompt"
```

---

### TC-03: Create New Prompt Version

**Objective:** Verify creating a new version stores it and sets it as active

**Steps:**
1. Create a new version for `architect.system` with custom content
2. Verify version is created with correct version_number
3. Verify prompt now shows this version as active

**Expected Result:**
- POST returns 201 with version details
- `version_number` is 1 (first custom version)
- GET `/api/prompts` shows `current_version_id` is set
- `current_version_number` is 1

**Verification Commands:**
```bash
# Create version
curl -s -X POST http://localhost:8420/api/prompts/architect.system/versions \
  -H "Content-Type: application/json" \
  -d '{"content": "You are a custom architect prompt for testing.", "change_note": "Test version"}' | jq

# Verify prompt has active version
curl -s http://localhost:8420/api/prompts/architect.system | jq '{current_version_id, versions: (.versions | length)}'
# Expected: current_version_id is set, versions count is 1
```

---

### TC-04: Version History Tracking

**Objective:** Verify multiple versions are tracked and can be listed

**Steps:**
1. Create 2-3 more versions for `architect.system` with different content
2. List all versions
3. Verify version numbers increment correctly

**Expected Result:**
- Each new version increments `version_number`
- All versions appear in history
- Most recent version is active

**Verification Commands:**
```bash
# Create second version
curl -s -X POST http://localhost:8420/api/prompts/architect.system/versions \
  -H "Content-Type: application/json" \
  -d '{"content": "Second custom version for testing.", "change_note": "Update 2"}' | jq '.version_number'
# Expected: 2

# Create third version
curl -s -X POST http://localhost:8420/api/prompts/architect.system/versions \
  -H "Content-Type: application/json" \
  -d '{"content": "Third custom version for testing.", "change_note": "Update 3"}' | jq '.version_number'
# Expected: 3

# List all versions
curl -s http://localhost:8420/api/prompts/architect.system/versions | jq '.versions | length'
# Expected: 3
```

---

### TC-05: Reset to Default

**Objective:** Verify reset removes custom version and returns to default

**Steps:**
1. Ensure `architect.system` has a custom version (from TC-03/TC-04)
2. Call reset endpoint
3. Verify prompt is using default again

**Expected Result:**
- Reset returns success message
- `current_version_id` becomes null
- Version history is preserved (not deleted)

**Verification Commands:**
```bash
# Reset to default
curl -s -X POST http://localhost:8420/api/prompts/architect.system/reset | jq

# Verify reset
curl -s http://localhost:8420/api/prompts/architect.system | jq '{current_version_id, versions: (.versions | length)}'
# Expected: current_version_id: null, versions still exist
```

---

### TC-06: Empty Content Validation

**Objective:** Verify API rejects empty prompt content

**Steps:**
1. Try to create a version with empty content
2. Try to create a version with whitespace-only content

**Expected Result:**
- Both requests return 422 Unprocessable Entity
- Error message indicates content cannot be empty

**Verification Commands:**
```bash
# Empty content
curl -s -X POST http://localhost:8420/api/prompts/architect.system/versions \
  -H "Content-Type: application/json" \
  -d '{"content": ""}' | jq
# Expected: 422 error

# Whitespace only
curl -s -X POST http://localhost:8420/api/prompts/architect.system/versions \
  -H "Content-Type: application/json" \
  -d '{"content": "   "}' | jq
# Expected: 422 error
```

---

### TC-07: Dashboard Prompts Page Load

**Objective:** Verify dashboard settings page loads and displays all prompts

**Steps:**
1. Open browser to http://localhost:8420
2. Click "Prompts" in the sidebar (or navigate to /prompts)
3. Verify page displays all prompts grouped by agent

**Expected Result:**
- Page loads without errors
- Header shows "Agent Prompts" with total count (4)
- Prompts are grouped under "Architect" and "Reviewer" sections
- Each prompt card shows name, description, and version badge
- Prompts with no custom version show "Default" badge
- Prompts with custom versions show "v{N}" badge

**Verification:**
- Visual inspection of page layout
- Check browser console for JavaScript errors
- Verify badge states match API response

---

### TC-08: Dashboard Edit Modal

**Objective:** Verify edit modal opens, loads content, and saves correctly

**Steps:**
1. Navigate to Settings/Prompts page
2. Click "Edit" on "Architect System Prompt" card
3. Verify modal opens with default content loaded
4. Modify the content slightly
5. Add a change note
6. Click "Save"
7. Verify prompt card updates to show new version

**Expected Result:**
- Modal opens with large textarea containing current content
- Character count displays at bottom
- Change note input is available
- "Reset to default" button is available
- After save, modal closes
- Success toast appears
- Prompt card shows "v1" (or next version number)

**Verification:**
- Visual inspection of modal UI
- Check that content loads correctly
- Verify save creates new version (check via API)

---

### TC-09: Dashboard Reset Confirmation

**Objective:** Verify reset confirmation dialog works correctly

**Steps:**
1. Navigate to Settings/Prompts page
2. Ensure a prompt has a custom version (create one if needed via TC-08)
3. Click "Reset" on the prompt card
4. Verify confirmation dialog appears
5. Click "Cancel" - verify nothing changes
6. Click "Reset" again, then confirm
7. Verify prompt reverts to default

**Expected Result:**
- Confirmation dialog shows prompt name
- Cancel dismisses dialog without action
- Confirm resets prompt and shows success toast
- Prompt card shows "Default" badge after reset

**Verification:**
- Visual inspection of dialog
- Check badge state changes
- Verify via API that `current_version_id` is null

---

### TC-10: Character Count Warning

**Objective:** Verify character count warning appears for large prompts

**Steps:**
1. Open edit modal for any prompt
2. Paste or type content exceeding 10,000 characters
3. Verify warning appears

**Expected Result:**
- Character count updates in real-time
- When exceeding 10,000 characters:
  - Count turns amber/yellow
  - Warning icon appears
  - Text shows "(exceeds 10,000)"

**Verification Commands:**
```bash
# Generate large content for testing
python3 -c "print('x' * 10001)"
```
Then paste into the editor.

---

### TC-11: Agent Prompt Injection (E2E)

**Objective:** Verify custom prompts are actually used by agents during workflow execution

**Test Repository:** `/Users/ka/github/anderskev-dot-com`
**Test Issue:** GitHub issue #4

**Prerequisites:**
- Server running (`uv run amelia server --reload`)
- GitHub tracker configured in profile

**Steps:**
1. Create a custom prompt version for `architect.system` with distinctive content:
   ```bash
   curl -s -X POST http://localhost:8420/api/prompts/architect.system/versions \
     -H "Content-Type: application/json" \
     -d '{
       "content": "You are a senior software architect. IMPORTANT: Always start your plan with the phrase \"E2E TEST MARKER\" to verify custom prompts are being used. Then proceed with normal planning.",
       "change_note": "E2E test marker for verification"
     }' | jq
   ```

2. Start a new workflow for issue #4:
   ```bash
   cd /Users/ka/github/anderskev-dot-com
   uv run amelia start 4
   ```

3. Monitor the architect output for the "E2E TEST MARKER" phrase
4. Check dashboard workflow detail for prompt version tracking

**Expected Result:**
- Architect plan includes "E2E TEST MARKER" phrase
- Workflow records which prompt versions were used
- Dashboard shows prompt version association in workflow detail

**Cleanup:**
```bash
# Reset prompt to default after test
curl -s -X POST http://localhost:8420/api/prompts/architect.system/reset | jq
```

**Verification:**
- Check architect output for custom marker
- Verify in dashboard that workflow used custom prompt version

---

### TC-12: Sidebar Navigation

**Objective:** Verify sidebar correctly highlights Prompts section

**Steps:**
1. Navigate to dashboard home (http://localhost:8420)
2. Click "Prompts" in sidebar
3. Navigate to Workflows page
4. Navigate back to Prompts

**Expected Result:**
- Prompts menu item is in Settings section
- Active page shows highlighted/selected state in sidebar
- Navigation works without page reload (SPA behavior)

**Verification:**
- Visual inspection of sidebar states
- URL changes to /prompts

---

## Test Environment Cleanup

After testing:
```bash
# Stop the server (Ctrl+C if running in foreground)

# Optional: Reset database to clean state
rm -f ~/.amelia/amelia.db
# Database will be recreated with defaults on next server start
```

---

## Test Result Template

| Test ID | Description | Status | Notes |
|---------|-------------|--------|-------|
| TC-01 | List All Prompts | [ ] Pass / [ ] Fail | |
| TC-02 | Get Default Content | [ ] Pass / [ ] Fail | |
| TC-03 | Create New Prompt Version | [ ] Pass / [ ] Fail | |
| TC-04 | Version History Tracking | [ ] Pass / [ ] Fail | |
| TC-05 | Reset to Default | [ ] Pass / [ ] Fail | |
| TC-06 | Empty Content Validation | [ ] Pass / [ ] Fail | |
| TC-07 | Dashboard Prompts Page Load | [ ] Pass / [ ] Fail | |
| TC-08 | Dashboard Edit Modal | [ ] Pass / [ ] Fail | |
| TC-09 | Dashboard Reset Confirmation | [ ] Pass / [ ] Fail | |
| TC-10 | Character Count Warning | [ ] Pass / [ ] Fail | |
| TC-11 | Agent Prompt Injection (E2E) | [ ] Pass / [ ] Fail / [ ] Skip | |
| TC-12 | Sidebar Navigation | [ ] Pass / [ ] Fail | |

---

## Agent Execution Notes

### For LLM Agent Executing This Plan:

1. **Start server first** - Many tests require the backend running
2. **Execute API tests (TC-01 to TC-06)** before UI tests - confirms API is working
3. **UI tests (TC-07 to TC-12)** require browser interaction
4. **TC-11 is optional** - requires full system setup with tracker
5. **Clean up** - Database state accumulates across tests; reset if needed between runs

### Programmatic API Testing

```python
import httpx
import asyncio

async def test_prompts_api():
    async with httpx.AsyncClient(base_url="http://localhost:8420") as client:
        # TC-01: List prompts
        response = await client.get("/api/prompts")
        assert response.status_code == 200
        data = response.json()
        assert len(data["prompts"]) == 4

        # TC-02: Get default
        response = await client.get("/api/prompts/architect.system/default")
        assert response.status_code == 200
        assert "content" in response.json()

        # TC-03: Create version
        response = await client.post(
            "/api/prompts/architect.system/versions",
            json={"content": "Test prompt", "change_note": "Test"}
        )
        assert response.status_code == 201

        # TC-05: Reset
        response = await client.post("/api/prompts/architect.system/reset")
        assert response.status_code == 200

asyncio.run(test_prompts_api())
```

---

## Key Changes in This Branch

The following changes should be verified through testing:

1. **Prompts Module** (`amelia/agents/prompts/`):
   - `defaults.py`: Hardcoded prompt defaults
   - `models.py`: Pydantic models for prompts
   - `resolver.py`: Resolution logic (DB vs default fallback)

2. **API Routes** (`amelia/server/routes/prompts.py`):
   - GET `/api/prompts` - List all prompts
   - GET `/api/prompts/{id}` - Get prompt with versions
   - GET `/api/prompts/{id}/versions` - List versions
   - POST `/api/prompts/{id}/versions` - Create version
   - POST `/api/prompts/{id}/reset` - Reset to default
   - GET `/api/prompts/{id}/default` - Get default content

3. **Agent Integration** (`amelia/agents/architect.py`, `amelia/agents/reviewer.py`):
   - Accept `prompts` dict in constructor
   - Use injected prompts with fallback to class constants

4. **Orchestrator** (`amelia/core/orchestrator.py`):
   - Extract prompts from config
   - Pass to agent constructors

5. **Dashboard** (`dashboard/src/pages/PromptConfigPage.tsx`, `dashboard/src/components/prompts/`):
   - Settings page with prompt cards
   - Edit modal with textarea and character count
   - Reset confirmation dialog
   - Version badge display
