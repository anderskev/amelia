# Pipeline Foundation Manual Testing Plan

**Branch:** `feat/pipeline-foundation-262`
**Feature:** Refactored pipeline architecture with ImplementationPipeline and ReviewPipeline

## Overview

This PR introduces a major architectural refactor that extracts the orchestrator logic into a modular pipeline system. The key changes include:

1. **New pipeline abstraction** (`amelia/pipelines/base.py`) - `Pipeline` protocol and `PipelineMetadata`
2. **ImplementationPipeline** - Architect → Developer ↔ Reviewer flow for building features
3. **ReviewPipeline** - Reviewer → Evaluator → Developer cycle for code reviews
4. **Pipeline registry** - Central registry for instantiating pipelines by name
5. **Shared utilities** - Common nodes, routing, and state management extracted for reuse

The test uses `/Users/ka/github/existential-birds/test_repo_c` as an isolated test repository.

---

## Prerequisites

### Environment Setup

```bash
# 1. Ensure you're in the amelia directory
cd /Users/ka/github/existential-birds/amelia

# 2. Sync Python dependencies
uv sync

# 3. Verify the test repository exists and is clean
ls -la /Users/ka/github/existential-birds/test_repo_c
# Should show an empty git repo (only .git directory)

# 4. Initialize the test repo if needed
cd /Users/ka/github/existential-birds/test_repo_c
git status  # Verify it's a git repo

# 5. Return to amelia directory
cd /Users/ka/github/existential-birds/amelia

# 6. Verify amelia CLI works
uv run amelia --help
```

### Configuration

Create or update `settings.amelia.yaml` with a test profile:

```yaml
active_profile: test
profiles:
  test:
    name: test
    driver: api:openrouter  # or cli:claude
    model: x-ai/grok-code-fast-1  # or your preferred model
    tracker: noop  # Use noop tracker for manual task input
    strategy: single
    validator_model: x-ai/grok-code-fast-1  # Required field
```

### Testing Tools

- Terminal for running CLI commands
- Text editor for viewing generated files
- `cat` for viewing file contents

---

## Test Scenarios

### TC-01: Hello World in C - Full E2E Implementation Pipeline

**Objective:** Verify the ImplementationPipeline can take a task from planning through implementation, creating a working Hello World program in C.

**Test Repository:** `/Users/ka/github/existential-birds/test_repo_c`

**Steps:**

1. **Clean the test repository**
   ```bash
   cd /Users/ka/github/existential-birds/test_repo_c
   # Remove any existing files (keep .git)
   find . -maxdepth 1 -not -name '.git' -not -name '.' -exec rm -rf {} \;
   git status  # Should show clean
   cd /Users/ka/github/existential-birds/amelia
   ```

2. **Start workflow with a Hello World task**
   ```bash
   cd /Users/ka/github/existential-birds/test_repo_c
   uv run --project /Users/ka/github/existential-birds/amelia amelia start HELLO-001 \
     --title "Create Hello World in C" \
     --description "Create a simple Hello World program in C. The program should:
   1. Create a file named hello.c
   2. Include the standard stdio.h header
   3. Implement a main function that prints 'Hello, World!' to stdout
   4. Return 0 to indicate success
   5. Create a Makefile that compiles hello.c to an executable named 'hello'
   The code should follow C99 standards and compile without warnings." \
     --profile test
   ```

3. **Observe the pipeline execution**
   - Watch for Architect phase (planning)
   - Watch for Developer phase (implementation)
   - Watch for Reviewer phase (code review)
   - Note any iteration between Developer and Reviewer

4. **Verify the generated files**
   ```bash
   cd /Users/ka/github/existential-birds/test_repo_c
   ls -la
   cat hello.c
   cat Makefile
   ```

5. **Compile and run the program**
   ```bash
   cd /Users/ka/github/existential-birds/test_repo_c
   make
   ./hello
   ```

**Expected Result:**
- `hello.c` file created with proper C code
- `Makefile` created with build instructions
- Code compiles without errors or warnings
- Running `./hello` outputs `Hello, World!`
- Git shows the changes as uncommitted modifications

**Verification Commands:**
```bash
# Check file exists
test -f /Users/ka/github/existential-birds/test_repo_c/hello.c && echo "PASS: hello.c exists"

# Check compilation
cd /Users/ka/github/existential-birds/test_repo_c && make clean 2>/dev/null; make && echo "PASS: Compiles successfully"

# Check output
cd /Users/ka/github/existential-birds/test_repo_c && ./hello | grep -q "Hello" && echo "PASS: Outputs Hello"

# Check git status
cd /Users/ka/github/existential-birds/test_repo_c && git status
```

---

### TC-02: Queue and Plan Mode

**Objective:** Verify the `--queue --plan` workflow generates a plan and waits for approval.

**Steps:**

1. **Queue a workflow with plan**
   ```bash
   cd /Users/ka/github/existential-birds/test_repo_c
   uv run --project /Users/ka/github/existential-birds/amelia amelia start FEAT-002 \
     --title "Add command-line argument support" \
     --description "Modify hello.c to accept an optional name argument. If provided, print 'Hello, <name>!' instead of 'Hello, World!'" \
     --profile test \
     --queue --plan
   ```

2. **Check the workflow status**
   ```bash
   uv run --project /Users/ka/github/existential-birds/amelia amelia status
   ```

3. **Verify plan was generated**
   - Look for plan output in the terminal
   - Workflow should be in `pending_approval` state

4. **Approve the plan**
   ```bash
   uv run --project /Users/ka/github/existential-birds/amelia amelia approve
   ```

5. **Run the approved workflow**
   ```bash
   uv run --project /Users/ka/github/existential-birds/amelia amelia run
   ```

**Expected Result:**
- Plan is displayed before execution
- Workflow waits for approval
- After approval and run, implementation proceeds

---

### TC-03: Review Pipeline - Local Changes

**Objective:** Verify the ReviewPipeline can review local uncommitted changes.

**Steps:**

1. **Make a local change to hello.c**
   ```bash
   cd /Users/ka/github/existential-birds/test_repo_c
   # Ensure hello.c exists from TC-01 (or create it manually)
   # Add a simple change - e.g., add a comment
   echo "// Review test comment" >> hello.c
   git diff  # Should show the change
   ```

2. **Run local review**
   ```bash
   uv run --project /Users/ka/github/existential-birds/amelia amelia review --local --profile test
   ```

3. **Observe review output**
   - Watch for Reviewer analysis
   - Note any feedback provided

**Expected Result:**
- Review pipeline successfully analyzes the diff
- Feedback is provided about the change
- No errors during review execution

---

### TC-04: Pipeline Registry Functions

**Objective:** Verify the pipeline registry correctly lists and instantiates pipelines.

**Steps:**

1. **Test via Python REPL**
   ```bash
   uv run python -c "
   from amelia.pipelines.registry import get_pipeline, list_pipelines

   # Test list_pipelines
   pipelines = list_pipelines()
   print('Available pipelines:')
   for p in pipelines:
       print(f'  - {p[\"name\"]}: {p[\"description\"]}')

   # Test get_pipeline
   impl = get_pipeline('implementation')
   print(f'\nImplementation pipeline: {impl.metadata.display_name}')

   review = get_pipeline('review')
   print(f'Review pipeline: {review.metadata.display_name}')

   # Test invalid pipeline
   try:
       get_pipeline('invalid')
   except ValueError as e:
       print(f'\nCorrectly raised error for invalid pipeline: {e}')
   "
   ```

**Expected Result:**
- `list_pipelines()` returns both 'implementation' and 'review' pipelines
- `get_pipeline('implementation')` returns an ImplementationPipeline instance
- `get_pipeline('review')` returns a ReviewPipeline instance
- `get_pipeline('invalid')` raises ValueError

---

### TC-05: Pipeline State Management

**Objective:** Verify that pipeline state is correctly initialized and updated.

**Steps:**

1. **Test state initialization via Python**
   ```bash
   uv run python -c "
   from amelia.pipelines.registry import get_pipeline

   # Get implementation pipeline
   impl = get_pipeline('implementation')

   # Create initial state
   state = impl.get_initial_state(
       workflow_id='test-123',
       profile_id='test-profile'
   )

   print(f'Workflow ID: {state.workflow_id}')
   print(f'Profile ID: {state.profile_id}')
   print(f'Status: {state.status}')
   print(f'Created at: {state.created_at}')

   # Verify state class
   state_class = impl.get_state_class()
   print(f'State class: {state_class.__name__}')
   "
   ```

**Expected Result:**
- State is created with correct workflow_id and profile_id
- Initial status is 'pending'
- created_at is set to current time
- State class is ImplementationState

---

### TC-06: Shared Node Imports

**Objective:** Verify shared nodes are correctly exported and accessible.

**Steps:**

1. **Test node imports**
   ```bash
   uv run python -c "
   from amelia.pipelines.nodes import (
       call_developer_node,
       call_reviewer_node,
   )
   from amelia.pipelines.routing import route_after_review_or_task

   print('Successfully imported:')
   print(f'  - call_developer_node: {call_developer_node}')
   print(f'  - call_reviewer_node: {call_reviewer_node}')
   print(f'  - route_after_review_or_task: {route_after_review_or_task}')
   "
   ```

**Expected Result:**
- All shared nodes import successfully
- Functions are callable objects

---

### TC-07: Error Handling - Invalid Issue

**Objective:** Verify graceful error handling for invalid inputs.

**Steps:**

1. **Try to start with missing required args**
   ```bash
   uv run --project /Users/ka/github/existential-birds/amelia amelia start
   # Should show usage error
   ```

2. **Try with invalid profile**
   ```bash
   cd /Users/ka/github/existential-birds/test_repo_c
   uv run --project /Users/ka/github/existential-birds/amelia amelia start TEST-001 \
     --title "Test" \
     --profile nonexistent_profile 2>&1 | head -20
   ```

**Expected Result:**
- Clear error messages are shown
- No stack traces for user errors
- Helpful usage information provided

---

## Test Environment Cleanup

After testing:

```bash
# Clean up test repository
cd /Users/ka/github/existential-birds/test_repo_c
rm -f hello.c Makefile hello
git checkout -- . 2>/dev/null || true
git clean -fd

# Return to amelia directory
cd /Users/ka/github/existential-birds/amelia
```

---

## Test Result Template

| Test ID | Description | Status | Notes |
|---------|-------------|--------|-------|
| TC-01 | Hello World in C - Full E2E | [ ] Pass / [ ] Fail | |
| TC-02 | Queue and Plan Mode | [ ] Pass / [ ] Fail | |
| TC-03 | Review Pipeline - Local Changes | [ ] Pass / [ ] Fail | |
| TC-04 | Pipeline Registry Functions | [ ] Pass / [ ] Fail | |
| TC-05 | Pipeline State Management | [ ] Pass / [ ] Fail | |
| TC-06 | Shared Node Imports | [ ] Pass / [ ] Fail | |
| TC-07 | Error Handling - Invalid Issue | [ ] Pass / [ ] Fail | |

---

## Agent Execution Notes

### For LLM Agent Executing This Plan:

1. **Environment setup** - Ensure uv is available and dependencies are synced
2. **Execute tests sequentially** - TC-01 creates files needed by TC-02 and TC-03
3. **Capture full output** - Log command output for debugging failures
4. **Mark results immediately** - Update the result table after each test
5. **Report issues** - Include exact error messages and stack traces for failures

### Programmatic Test Execution

```python
import subprocess
import os

TEST_REPO = "/Users/ka/github/existential-birds/test_repo_c"
AMELIA_DIR = "/Users/ka/github/existential-birds/amelia"

def run_command(cmd: str, cwd: str = AMELIA_DIR) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True
    )
    return result.returncode, result.stdout, result.stderr

# Example: Run TC-04 registry test
code, stdout, stderr = run_command(
    'uv run python -c "from amelia.pipelines.registry import list_pipelines; print(list_pipelines())"'
)
print(f"Exit code: {code}")
print(f"Output: {stdout}")
```

---

## Key Changes in This Branch

The following changes should be verified through testing:

1. **Pipeline Abstraction** (`amelia/pipelines/base.py`):
   - `Pipeline` protocol is correctly implemented
   - `PipelineMetadata` provides accurate metadata
   - `BasePipelineState` includes required fields

2. **Implementation Pipeline** (`amelia/pipelines/implementation/`):
   - Graph creates correct node flow
   - Nodes execute in proper sequence (Architect → Developer ↔ Reviewer)
   - State transitions work correctly
   - Utilities extract config params properly

3. **Review Pipeline** (`amelia/pipelines/review/`):
   - Review-only workflow functions correctly
   - Local changes are properly analyzed
   - Routing decisions are accurate

4. **Registry** (`amelia/pipelines/registry.py`):
   - All pipelines are registered
   - `get_pipeline()` returns correct instances
   - `list_pipelines()` returns complete metadata

5. **Orchestrator Migration** (`amelia/core/orchestrator.py`):
   - Reduced from 700+ lines (uses pipeline utilities)
   - Still functions correctly with new structure
