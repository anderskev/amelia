# Remove Legacy Mode Support - Manual Testing Plan

**Branch:** `refactor/334-remove-legacy-mode-support`
**Feature:** Remove legacy execution mode, ensure `total_tasks >= 1` always

## Overview

This PR removes the legacy execution mode where `total_tasks` could be `None`. The refactoring ensures:

1. `extract_task_count()` returns `1` instead of `None` when no task patterns found
2. `total_tasks` field defaults to `1` instead of `None`
3. All conditional checks for `total_tasks is None` are removed
4. The `route_after_review()` legacy routing function is deleted
5. Task-based execution is now the only code path

**Why manual testing:** The automated tests cover unit and integration logic, but we need to verify the full orchestrator flow works correctly with both single-task and multi-task plans.

---

## Prerequisites

### Clean Up Existing Processes

**IMPORTANT:** Before starting, kill any existing Amelia processes that may occupy the default port (8420).

```bash
# Kill any existing Amelia servers or dev processes
pkill -f "amelia server" || true
pkill -f "amelia dev" || true

# Verify port 8420 is free
lsof -i :8420 || echo "Port 8420 is free"

# If port is still occupied, force kill the process
# lsof -ti :8420 | xargs kill -9 || true
```

### Environment Setup

```bash
# 1. Navigate to amelia project root
cd /Users/ka/github/existential-birds/amelia

# 2. Install Python dependencies
uv sync

# 3. Create test repository
rm -rf test_repo_c
mkdir -p test_repo_c
cd test_repo_c
git init
echo "# Test Repo C" > README.md
git add README.md
git commit -m "Initial commit"
cd ..

# 4. Verify test repo setup
ls -la test_repo_c/
```

### Start the Server

```bash
# Terminal 1: Start the Amelia server
cd /Users/ka/github/existential-birds/amelia
uv run amelia server --reload

# Wait for server to be ready (check for "Application startup complete")
# Server runs on http://localhost:8420
```

### Verify Server is Running

```bash
# Health check
curl -s http://localhost:8420/health | jq .
# Expected: {"status": "healthy", ...}
```

### Create Test Profile via API

```bash
# Create the test profile
curl -s -X POST http://localhost:8420/api/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test",
    "tracker": "noop",
    "working_dir": "/Users/ka/github/existential-birds/amelia/test_repo_c",
    "plan_output_dir": "docs/plans",
    "plan_path_pattern": "docs/plans/{date}-{issue_key}.md",
    "auto_approve_reviews": false,
    "agents": {
      "architect": {
        "driver": "cli:claude",
        "model": "sonnet",
        "options": {}
      },
      "developer": {
        "driver": "cli:claude",
        "model": "sonnet",
        "options": {}
      },
      "reviewer": {
        "driver": "cli:claude",
        "model": "sonnet",
        "options": {"max_iterations": 3}
      },
      "task_reviewer": {
        "driver": "cli:claude",
        "model": "haiku",
        "options": {"max_iterations": 2}
      }
    }
  }' | jq .

# Activate the profile
curl -s -X POST http://localhost:8420/api/profiles/test/activate | jq .

# Verify profile was created
curl -s http://localhost:8420/api/profiles | jq .
```

### Alternative: Create Profile via Dashboard UI

1. Open http://localhost:8420 in browser
2. Navigate to Settings → Profiles
3. Click "Create Profile"
4. Fill in:
   - ID: `test`
   - Tracker: `noop`
   - Working Directory: `/Users/ka/github/existential-birds/amelia/test_repo_c`
   - Configure agents with `cli:claude` driver and `sonnet` model
5. Save and activate the profile

---

## Test Scenarios

### TC-01: Single-Task Plan Execution

**Objective:** Verify that plans without explicit `### Task N:` patterns execute correctly with `total_tasks=1`

**Steps:**
1. Navigate to test_repo_c
2. Start a workflow with a simple task that produces a single-task plan
3. Verify the plan is generated and executed as a single task

**Expected Result:**
- Plan is generated without `### Task N:` headers
- `total_tasks` is set to `1` in state
- Developer executes the entire plan
- Reviewer reviews the complete implementation
- Workflow completes successfully

**Verification Commands:**
```bash
cd /Users/ka/github/existential-birds/amelia/test_repo_c

# Start a simple task using noop tracker with inline title/description
uv run amelia start TASK-001 \
  --profile test \
  --title "Add a hello function" \
  --description "Create a simple hello() function in hello.py that returns 'Hello, World!'"

# Monitor workflow status
uv run amelia status

# Check logs for total_tasks=1
# Look for: "Starting task execution" with task=1, total_tasks=1
```

---

### TC-02: Multi-Task Plan Execution

**Objective:** Verify that plans with `### Task N:` patterns execute task-by-task correctly

**Steps:**
1. Navigate to test_repo_c
2. Start a workflow with a complex task that will produce multiple tasks
3. Verify tasks are executed sequentially with proper state transitions

**Expected Result:**
- Plan is generated with `### Task 1:`, `### Task 2:`, etc. headers
- `total_tasks` matches the number of tasks in the plan
- Each task is executed by Developer in sequence
- Task Reviewer reviews each task before proceeding
- Final Reviewer reviews the complete implementation
- `current_task_index` increments correctly

**Verification Commands:**
```bash
cd /Users/ka/github/existential-birds/amelia/test_repo_c

# Start a more complex task that should generate multiple tasks
uv run amelia start TASK-002 \
  --profile test \
  --title "Add calculator module" \
  --description "Create a calculator module with: 1) add function, 2) subtract function, 3) multiply function, 4) divide function with zero-division handling, 5) unit tests for all functions"

# Monitor workflow - should show task progression
uv run amelia status

# Check logs for multi-task execution
# Look for: task=1, total_tasks=N (where N > 1)
# Then: task=2, task=3, etc.
```

---

### TC-03: Task Extraction from Various Plan Formats

**Objective:** Verify `extract_task_count()` handles different markdown formats

**Steps:**
1. Run programmatic tests for task extraction
2. Test with plans containing simple numbering: `### Task 1:`
3. Test with plans containing hierarchical numbering: `### Task 1.1:`
4. Test with plans containing no task markers

**Expected Result:**
- Simple numbering: counts each `### Task N:` pattern
- Hierarchical: counts each `### Task N.M:` pattern
- No markers: returns `1` (not `None`)

**Verification Commands:**
```bash
cd /Users/ka/github/existential-birds/amelia

# Run programmatic test
uv run python << 'EOF'
from amelia.pipelines.implementation.utils import extract_task_count

test_cases = [
    ("## Overview\nJust do it", 1, "no tasks"),
    ("### Task 1: First\n### Task 2: Second", 2, "simple numbering"),
    ("### Task 1.1: Sub\n### Task 1.2: Another", 2, "hierarchical"),
    ("### Task 1: A\n### Task 2: B\n### Task 3: C", 3, "three tasks"),
    ("Some text\n### Task 1: Only one", 1, "single task"),
]

all_passed = True
for plan, expected, desc in test_cases:
    result = extract_task_count(plan)
    status = "PASS" if result == expected else "FAIL"
    if status == "FAIL":
        all_passed = False
    print(f"{status}: {desc} - got {result}, expected {expected}")

print("\n" + ("ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED"))
EOF
```

---

### TC-04: Review Iteration Tracking

**Objective:** Verify `task_review_iteration` is always incremented (not conditional on `total_tasks`)

**Steps:**
1. Start a workflow that will likely require reviewer changes
2. Verify `task_review_iteration` increments on each review cycle
3. Verify max iterations limit is respected

**Expected Result:**
- `task_review_iteration` starts at 0
- Increments after each reviewer pass
- Max iterations (default 3) terminates the loop

**Verification Commands:**
```bash
cd /Users/ka/github/existential-birds/amelia/test_repo_c

# Enable debug logging to see iteration counts
AMELIA_LOG_LEVEL=DEBUG uv run amelia start TASK-003 \
  --profile test \
  --title "Add complex validation" \
  --description "Add input validation to hello.py that validates email format using regex"

# Watch for iteration logs
# Look for: task_review_iteration=0, then task_review_iteration=1, etc.
```

---

### TC-05: Developer Session Fresh Start per Task

**Objective:** Verify `driver_session_id` is cleared for each task execution

**Steps:**
1. Run a multi-task workflow
2. Monitor logs for session reset between tasks

**Expected Result:**
- Log shows `fresh_session=True` at the start of each task
- Each task starts with a clean driver session
- No state leakage between tasks

**Verification Commands:**
```bash
cd /Users/ka/github/existential-birds/amelia/test_repo_c

# Run with debug logging to see session resets
AMELIA_LOG_LEVEL=DEBUG uv run amelia start TASK-004 \
  --profile test \
  --title "Multi-file feature" \
  --description "Create a utils module with: 1) string_utils.py with capitalize_words(), 2) number_utils.py with is_even(), 3) __init__.py that exports both" \
  2>&1 | grep -E "(fresh_session|Starting task|driver_session)"
```

---

### TC-06: Dashboard State Display

**Objective:** Verify dashboard correctly displays task progress

**Steps:**
1. Ensure server is running with dashboard
2. Run a multi-task workflow
3. Monitor dashboard for task progress indicators

**Expected Result:**
- Dashboard shows current task number
- Total tasks displayed correctly
- Progress updates in real-time via WebSocket

**Verification Commands:**
```bash
# Terminal 1: Start dev server (if not already running)
cd /Users/ka/github/existential-birds/amelia
uv run amelia dev

# Terminal 2: Start a multi-task workflow
cd /Users/ka/github/existential-birds/amelia/test_repo_c
uv run amelia start TASK-005 \
  --profile test \
  --title "Feature with tests" \
  --description "Create greeting module: 1) greet() function, 2) farewell() function, 3) tests for both"

# Browser: Open http://localhost:8420
# Observe:
# - Workflow appears in dashboard
# - Task progress indicator shows "Task 1 of N"
# - Progress updates as tasks complete
```

---

## Test Environment Cleanup

After testing:
```bash
# Stop any running servers
pkill -f "amelia server" || true
pkill -f "amelia dev" || true

# Delete the test profile (optional - via API)
curl -s -X DELETE http://localhost:8420/api/profiles/test

# Clean up test repository
cd /Users/ka/github/existential-birds/amelia
rm -rf test_repo_c

# Clear checkpoints if needed (optional)
rm -rf ~/.amelia/checkpoints.db
```

---

## Test Result Template

| Test ID | Description | Status | Notes |
|---------|-------------|--------|-------|
| TC-01 | Single-task plan execution | [ ] Pass / [ ] Fail | |
| TC-02 | Multi-task plan execution | [ ] Pass / [ ] Fail | |
| TC-03 | Task extraction formats | [ ] Pass / [ ] Fail | |
| TC-04 | Review iteration tracking | [ ] Pass / [ ] Fail | |
| TC-05 | Developer session fresh start | [ ] Pass / [ ] Fail | |
| TC-06 | Dashboard state display | [ ] Pass / [ ] Fail | |

---

## Agent Execution Notes

### For LLM Agent Executing This Plan:

1. **Start server first** - Server must be running before profile creation
2. **Create profile via API** - Use curl commands or agent-browser with dashboard
3. **TC-03 can be run standalone** - No server needed, just Python execution
4. **TC-01/TC-02 are core tests** - These verify the main refactoring works
5. **Capture log output** - Debug logs are essential for verifying internal state
6. **Dashboard testing (TC-06)** - Use agent-browser to observe dashboard state

### Setup Script (Run First):

```bash
#!/bin/bash
set -e

cd /Users/ka/github/existential-birds/amelia

# Kill any existing Amelia processes
pkill -f "amelia server" || true
pkill -f "amelia dev" || true

# Wait for processes to terminate
sleep 2

# Verify port 8420 is free (force kill if needed)
if lsof -i :8420 > /dev/null 2>&1; then
    echo "Port 8420 still occupied, force killing..."
    lsof -ti :8420 | xargs kill -9 || true
    sleep 1
fi

# Sync dependencies
uv sync

# Create test repo
rm -rf test_repo_c
mkdir -p test_repo_c
cd test_repo_c
git init
echo "# Test Repo C" > README.md
git add README.md
git commit -m "Initial commit"
cd ..

echo "Test repo created at $(pwd)/test_repo_c"
echo ""
echo "Next steps:"
echo "1. Start server: uv run amelia server --reload"
echo "2. Create profile via API (see curl commands in test plan)"
echo "3. Run test scenarios"
```

### Profile Creation via curl:

```bash
# Create profile
curl -s -X POST http://localhost:8420/api/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test",
    "tracker": "noop",
    "working_dir": "/Users/ka/github/existential-birds/amelia/test_repo_c",
    "plan_output_dir": "docs/plans",
    "plan_path_pattern": "docs/plans/{date}-{issue_key}.md",
    "auto_approve_reviews": false,
    "agents": {
      "architect": {"driver": "cli:claude", "model": "sonnet", "options": {}},
      "developer": {"driver": "cli:claude", "model": "sonnet", "options": {}},
      "reviewer": {"driver": "cli:claude", "model": "sonnet", "options": {"max_iterations": 3}},
      "task_reviewer": {"driver": "cli:claude", "model": "haiku", "options": {"max_iterations": 2}}
    }
  }' | jq .

# Activate profile
curl -s -X POST http://localhost:8420/api/profiles/test/activate | jq .
```

### Programmatic Test for TC-03:

```python
from amelia.pipelines.implementation.utils import extract_task_count

test_cases = [
    ("## Overview\nJust do it", 1, "no tasks"),
    ("### Task 1: First\n### Task 2: Second", 2, "simple numbering"),
    ("### Task 1.1: Sub\n### Task 1.2: Another", 2, "hierarchical"),
    ("### Task 1: A\n### Task 2: B\n### Task 3: C", 3, "three tasks"),
]

for plan, expected, desc in test_cases:
    result = extract_task_count(plan)
    status = "PASS" if result == expected else "FAIL"
    print(f"{status}: {desc} - got {result}, expected {expected}")
```

---

## Key Changes in This Branch

The following changes should be verified through testing:

1. **State default change** (`amelia/pipelines/implementation/state.py`):
   - `total_tasks: int | None = None` → `total_tasks: int = 1`

2. **Utility function change** (`amelia/pipelines/implementation/utils.py`):
   - `extract_task_count()` returns `1` instead of `None` for no-task plans

3. **Node behavior change** (`amelia/pipelines/nodes.py`):
   - Removed `if state.total_tasks is not None:` conditionals
   - Task logging and session reset now unconditional

4. **Routing simplification** (`amelia/pipelines/implementation/routing.py`):
   - Deleted `route_after_review()` legacy function
   - `route_after_task_review()` no longer handles `None` case

5. **Graph simplification** (`amelia/pipelines/implementation/graph.py`):
   - Removed legacy mode routing logic
   - Single unified execution path
