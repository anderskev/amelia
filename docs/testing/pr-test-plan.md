# Per-Agent Driver Configuration Manual Testing Plan

**Branch:** `feat/279-per-agent-driver-config`
**Feature:** Per-agent driver and model configuration (#279)

## Overview

This PR replaces the profile-level `driver` and `model` fields with per-agent configuration via an `agents` dict. Each agent (architect, developer, reviewer, etc.) can now have its own driver and model, enabling:
- Different models for different agents (expensive for planning, cheap for validation)
- Mixing CLI and API drivers across agents
- Agent-specific options like max iterations

**Breaking change:** This PR changes the database schema. Users with existing databases must delete and recreate them.

---

## Prerequisites

### Environment Setup

```bash
# 1. Install Python dependencies
cd /Users/ka/github/existential-birds/amelia
uv sync

# 2. Delete existing database (schema breaking change)
rm -f ~/.amelia/amelia.db

# 3. Start the backend server
uv run amelia server --reload
# Server runs on http://localhost:8420 by default

# 4. For dashboard testing
# Dashboard is served at localhost:8420 by the backend server

# 5. Verify setup
curl http://localhost:8420/health
```

### Test Repository

All tests use the following test repository as the working directory:
```
/Users/ka/github/existential-birds/test_repo_c
```

### Testing Tools

- **agent-browser**: Used for dashboard UI testing
  ```bash
  agent-browser open http://localhost:8420
  agent-browser snapshot -i  # Get interactive elements
  agent-browser click @e1    # Click element by ref
  ```

---

## Test Scenarios

### TC-01: First-Time Setup Creates Profile with Agents Dict

**Objective:** Verify that the first-time setup wizard creates a profile with proper per-agent configuration.

**Steps:**
1. Delete existing database: `rm -f ~/.amelia/amelia.db`
2. Run any CLI command that triggers first-time setup: `uv run amelia config profile list`
3. Complete the interactive prompts (driver: `cli:claude`, model: `opus`, working_dir: `/Users/ka/github/existential-birds/test_repo_c`)
4. Verify profile was created with agents configuration

**Expected Result:**
- Setup prompts for name, driver, model, and working directory (NOT validator_model)
- Profile is created with 7 standard agents: architect, developer, reviewer, task_reviewer, evaluator, brainstormer, plan_validator
- All agents share the same driver and model specified during setup

**Verification Commands:**
```bash
rm -f ~/.amelia/amelia.db
uv run amelia config profile list
# Follow prompts, then:
uv run amelia config profile show default
```

---

### TC-02: CLI Profile List Shows Agent Count

**Objective:** Verify that `profile list` displays agent count instead of active marker.

**Steps:**
1. Ensure at least one profile exists
2. Run `uv run amelia config profile list`

**Expected Result:**
- Table shows columns: Name, Driver, Model, Tracker, Agents
- Driver/Model columns show values from first agent (for backward compatibility display)
- Agents column shows count (e.g., "7" for default agents)

**Verification Commands:**
```bash
uv run amelia config profile list
```

---

### TC-03: CLI Profile Show Displays Agents Table

**Objective:** Verify that `profile show` displays per-agent configuration in a separate table.

**Steps:**
1. Ensure a profile exists
2. Run `uv run amelia config profile show <profile_name>`

**Expected Result:**
- Main profile table shows: Tracker, Working Dir, Plan Output Dir, Plan Path Pattern, Auto Approve Reviews
- Separate "Agents" table shows each agent with: Agent, Driver, Model, Options
- Old fields (driver, model, validator_model, max_review_iterations) are NOT shown

**Verification Commands:**
```bash
uv run amelia config profile show default
```

---

### TC-04: API Profile Create with Agents Dict

**Objective:** Verify that the API accepts the new profile format with agents dict.

**Steps:**
1. Start the server: `uv run amelia server`
2. Create a profile via API with per-agent configuration
3. Retrieve the profile to verify it was stored correctly

**Expected Result:**
- POST succeeds with 201 status
- Profile is retrievable with correct agents configuration
- Each agent has driver, model, and options fields

**Verification Commands:**
```bash
# Create profile with different models per agent
curl -X POST http://localhost:8420/api/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "id": "mixed-models",
    "tracker": "noop",
    "working_dir": "/Users/ka/github/existential-birds/test_repo_c",
    "agents": {
      "architect": {"driver": "api:openrouter", "model": "opus", "options": {}},
      "developer": {"driver": "cli:claude", "model": "sonnet", "options": {}},
      "reviewer": {"driver": "api:openrouter", "model": "haiku", "options": {}}
    }
  }'

# Retrieve and verify
curl http://localhost:8420/api/profiles/mixed-models | jq
```

---

### TC-05: API Profile Update Agents

**Objective:** Verify that the API can update agent configurations.

**Steps:**
1. Create a profile
2. Update the agents dict via PUT
3. Verify changes were applied

**Expected Result:**
- PUT succeeds with 200 status
- Updated profile shows new agent configurations

**Verification Commands:**
```bash
# Update profile agents
curl -X PUT http://localhost:8420/api/profiles/mixed-models \
  -H "Content-Type: application/json" \
  -d '{
    "agents": {
      "architect": {"driver": "cli:claude", "model": "opus", "options": {}},
      "developer": {"driver": "cli:claude", "model": "opus", "options": {}},
      "reviewer": {"driver": "cli:claude", "model": "opus", "options": {}}
    }
  }'

# Verify update
curl http://localhost:8420/api/profiles/mixed-models | jq '.agents'
```

---

### TC-06: Old Database Schema Warning

**Objective:** Verify that users with old database schemas see a warning.

**Steps:**
1. Create a database with the old schema (has `driver` column in profiles table)
2. Start the server
3. Check logs for migration warning

**Expected Result:**
- Warning message appears in logs about old schema
- Message instructs user to delete database file and restart

**Verification Commands:**
```bash
# Create old-schema database (manual SQL or use backup)
# For testing, you can manually create old schema:
sqlite3 ~/.amelia/test-old.db "CREATE TABLE profiles (id TEXT PRIMARY KEY, driver TEXT, model TEXT)"

# Start server with old database
AMELIA_DATABASE_PATH=~/.amelia/test-old.db uv run amelia server

# Check logs for warning about 'driver' column
```

---

### TC-07: Dashboard Profile List (using agent-browser)

**Objective:** Verify the dashboard displays profiles with agent information.

**Steps:**
1. Start the server: `uv run amelia server`
2. Use agent-browser to navigate to the dashboard
3. Navigate to Settings page
4. Verify profiles are displayed with agent information

**Expected Result:**
- Profiles are listed in the UI
- Agent count or configuration is visible
- No JavaScript errors in console

**Verification Commands:**
```bash
# Open dashboard
agent-browser open http://localhost:8420

# Take snapshot to see page structure
agent-browser snapshot -i

# Navigate to Settings (find the settings link/button ref from snapshot)
agent-browser click @<settings-ref>

# Take snapshot of settings page
agent-browser snapshot -i

# Look for profiles section and verify agents are shown
# The snapshot should show profile cards/rows with agent information
```

---

### TC-08: Profile get_agent_config Method

**Objective:** Verify that `Profile.get_agent_config()` correctly returns agent config and raises on missing agents.

**Steps:**
1. Create a profile with specific agents
2. Test retrieving existing and non-existing agent configs

**Expected Result:**
- `get_agent_config("architect")` returns AgentConfig for architect
- `get_agent_config("nonexistent")` raises ValueError with helpful message

**Verification Commands:**
```bash
# Python test
uv run python -c "
from amelia.core.types import Profile, AgentConfig

profile = Profile(
    name='test',
    working_dir='/Users/ka/github/existential-birds/test_repo_c',
    agents={
        'architect': AgentConfig(driver='cli:claude', model='opus')
    }
)

# Should work
config = profile.get_agent_config('architect')
print(f'architect config: {config}')

# Should raise
try:
    profile.get_agent_config('developer')
except ValueError as e:
    print(f'Expected error: {e}')
"
```

---

### TC-09: Brainstorm Uses Per-Agent Config

**Objective:** Verify that brainstorm endpoint uses `profile.get_agent_config("brainstormer")`.

**Steps:**
1. Create profile with brainstormer agent configured
2. Start a brainstorm session via API
3. Verify the correct model is used

**Expected Result:**
- Brainstorm uses the driver/model from agents.brainstormer config
- Not a profile-level driver/model (which no longer exists)

**Verification Commands:**
```bash
# Create profile with brainstormer
curl -X POST http://localhost:8420/api/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "id": "brainstorm-test",
    "tracker": "noop",
    "working_dir": "/Users/ka/github/existential-birds/test_repo_c",
    "agents": {
      "brainstormer": {"driver": "cli:claude", "model": "haiku", "options": {}}
    }
  }'

# Activate profile
curl -X POST http://localhost:8420/api/profiles/brainstorm-test/activate

# Start brainstorm and check logs for model used
curl -X POST http://localhost:8420/api/brainstorm \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test brainstorm"}'
```

---

### TC-10: Profile Activation Returns Correct is_active

**Objective:** Verify profile endpoints return correct `is_active` status.

**Steps:**
1. Create two profiles
2. Activate one profile
3. List profiles and verify is_active flags

**Expected Result:**
- Only the activated profile has `is_active: true`
- Other profiles have `is_active: false`

**Verification Commands:**
```bash
# Create two profiles
curl -X POST http://localhost:8420/api/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "id": "profile-a",
    "tracker": "noop",
    "working_dir": "/Users/ka/github/existential-birds/test_repo_c",
    "agents": {"architect": {"driver": "cli:claude", "model": "opus"}}
  }'

curl -X POST http://localhost:8420/api/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "id": "profile-b",
    "tracker": "noop",
    "working_dir": "/Users/ka/github/existential-birds/test_repo_c",
    "agents": {"architect": {"driver": "cli:claude", "model": "opus"}}
  }'

# Activate profile-a
curl -X POST http://localhost:8420/api/profiles/profile-a/activate

# List and verify is_active
curl http://localhost:8420/api/profiles | jq '.[] | {id, is_active}'
```

---

### TC-11: Dashboard Profile Edit (using agent-browser)

**Objective:** Verify the dashboard allows editing profile agent configurations.

**Steps:**
1. Start the server with existing profiles
2. Use agent-browser to navigate to profile edit
3. Modify an agent's driver or model
4. Save and verify changes persisted

**Expected Result:**
- Profile edit form shows agents with their configurations
- Changes can be made to individual agent settings
- Save persists changes to database

**Verification Commands:**
```bash
# Ensure server is running and profiles exist

# Open dashboard
agent-browser open http://localhost:8420

# Take snapshot
agent-browser snapshot -i

# Navigate to Settings > Profiles
agent-browser click @<settings-ref>
agent-browser snapshot -i

# Click edit on a profile
agent-browser click @<edit-profile-ref>
agent-browser snapshot -i

# Verify agent configuration fields are visible
# Look for driver/model inputs for each agent

# Make a change and save (refs from snapshot)
agent-browser fill @<model-input-ref> "sonnet"
agent-browser click @<save-button-ref>

# Verify via API
curl http://localhost:8420/api/profiles/<profile-id> | jq '.agents'
```

---

## Test Environment Cleanup

After testing:
```bash
# Stop the server (Ctrl+C)

# Remove test database
rm -f ~/.amelia/amelia.db
rm -f ~/.amelia/test-old.db

# Close browser
agent-browser close
```

---

## Test Result Template

| Test ID | Description | Status | Notes |
|---------|-------------|--------|-------|
| TC-01 | First-time setup creates agents dict | [ ] Pass / [ ] Fail | |
| TC-02 | CLI profile list shows agent count | [ ] Pass / [ ] Fail | |
| TC-03 | CLI profile show displays agents table | [ ] Pass / [ ] Fail | |
| TC-04 | API profile create with agents | [ ] Pass / [ ] Fail | |
| TC-05 | API profile update agents | [ ] Pass / [ ] Fail | |
| TC-06 | Old database schema warning | [ ] Pass / [ ] Fail | |
| TC-07 | Dashboard profile list (agent-browser) | [ ] Pass / [ ] Fail | |
| TC-08 | Profile.get_agent_config method | [ ] Pass / [ ] Fail | |
| TC-09 | Brainstorm uses per-agent config | [ ] Pass / [ ] Fail | |
| TC-10 | Profile activation is_active status | [ ] Pass / [ ] Fail | |
| TC-11 | Dashboard profile edit (agent-browser) | [ ] Pass / [ ] Fail | |

---

## Agent Execution Notes

### For LLM Agent Executing This Plan:

1. **Start fresh** - Delete existing database before testing
2. **Use test_repo_c** - All working_dir values should be `/Users/ka/github/existential-birds/test_repo_c`
3. **Use agent-browser for UI tests** - Follow the snapshot-then-interact pattern:
   - `agent-browser open <url>` to navigate
   - `agent-browser snapshot -i` to get element refs (@e1, @e2, etc.)
   - `agent-browser click @<ref>` or `agent-browser fill @<ref> "value"` to interact
   - Re-snapshot after any navigation or state change
4. **Execute tests sequentially** - Some tests depend on state from previous tests
5. **Capture output** - Log curl responses, CLI output, and agent-browser snapshots
6. **Check logs** - Many verifications require checking server logs
7. **Report issues** - Note exact error messages and stack traces

---

## Key Changes in This Branch

The following changes should be verified through testing:

1. **Core types** (`amelia/core/types.py`):
   - New `AgentConfig` class with driver, model, options
   - `Profile` now has `agents: dict[str, AgentConfig]` instead of driver/model fields
   - `Profile.get_agent_config()` method for retrieving agent-specific config

2. **Database schema** (`amelia/server/database/connection.py`):
   - `profiles` table has `agents TEXT` (JSON) instead of driver/model/validator_model columns
   - Old schema detection and warning message

3. **Agents** (`amelia/agents/*.py`):
   - All agents accept `AgentConfig` and create their own driver internally
   - Removed driver injection in favor of config-based driver creation

4. **Pipeline nodes** (`amelia/pipelines/**/*.py`):
   - All nodes call `profile.get_agent_config()` to get agent-specific config
   - Pass config to agent constructors instead of pre-built drivers

5. **CLI** (`amelia/cli/config.py`):
   - `profile list` shows agent count column
   - `profile show` displays agents in separate table
   - `profile create` builds default agents from single driver/model input
   - Removed `--validator-model` flag

6. **API routes** (`amelia/server/routes/settings.py`):
   - Profile endpoints accept/return agents dict
   - New `AgentConfigCreate` and `AgentConfigResponse` schemas
   - Correct `is_active` status in profile responses
