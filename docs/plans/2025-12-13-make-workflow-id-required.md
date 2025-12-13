# Make workflow_id a Required Parameter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove backwards compatibility for `workflow_id` and make it a required parameter in agent methods.

**Architecture:** Change optional parameter `workflow_id: str | None = None` to required `workflow_id: str` across agent methods, remove fallback logic, and update all call sites to provide the value explicitly.

**Tech Stack:** Python 3.12, Pydantic, pytest

---

### Task 1: Update Architect.plan() to require workflow_id

**Files:**
- Modify: `amelia/agents/architect.py:221-226`
- Test: `tests/unit/agents/test_architect.py`

**Step 1: Update test to verify workflow_id is required**

```python
# In tests/unit/agents/test_architect.py, add new test class or test method:

class TestArchitectWorkflowIdRequired:
    """Test that workflow_id is required for Architect.plan()."""

    async def test_plan_requires_workflow_id(
        self,
        mock_driver: MagicMock,
        mock_execution_state_factory,
        mock_issue_factory,
        mock_task_response,
    ) -> None:
        """Test that plan() requires workflow_id parameter."""
        from unittest.mock import AsyncMock

        issue = mock_issue_factory(id="TEST-123")
        state = mock_execution_state_factory(issue=issue)
        mock_driver.generate.return_value = mock_task_response
        mock_emitter = AsyncMock()

        architect = Architect(driver=mock_driver, stream_emitter=mock_emitter)

        # Should work with workflow_id provided
        result = await architect.plan(state, workflow_id="required-workflow-id")
        assert result.task_dag is not None

        # Verify emitter received the provided workflow_id
        event = mock_emitter.call_args.args[0]
        assert event.workflow_id == "required-workflow-id"
```

**Step 2: Run test to verify it passes (baseline)**

Run: `uv run pytest tests/unit/agents/test_architect.py::TestArchitectWorkflowIdRequired -v`
Expected: PASS (current implementation accepts workflow_id)

**Step 3: Update Architect.plan() signature and remove fallback**

```python
# In amelia/agents/architect.py, modify the plan() method signature and body:

    async def plan(
        self,
        state: ExecutionState,
        output_dir: str | None = None,
        workflow_id: str,  # Required parameter, no default
    ) -> PlanOutput:
        """Generate a development plan from an issue and optional design.

        Creates a structured TaskDAG and saves a markdown version for human review.
        Design context is read from state.design if present.

        Args:
            state: The execution state containing the issue and optional design.
            output_dir: Directory path where the markdown plan will be saved.
                If None, uses profile's plan_output_dir from state.
            workflow_id: Workflow ID for stream events (required).

        Returns:
            PlanOutput containing the task DAG and path to the saved markdown file.

        Raises:
            ValueError: If no issue is present in the state.
        """
```

Also, in the same method body, replace lines 273-283:

```python
        # Emit completion event
        if self._stream_emitter is not None:
            event = StreamEvent(
                type=StreamEventType.AGENT_OUTPUT,
                content=f"Generated plan with {len(task_dag.tasks)} tasks",
                timestamp=datetime.now(UTC),
                agent="architect",
                workflow_id=workflow_id,  # Use directly, no fallback
            )
            await self._stream_emitter(event)
```

**Step 4: Run tests to verify signature change**

Run: `uv run pytest tests/unit/agents/test_architect.py -v`
Expected: Some tests may fail if they don't provide workflow_id

**Step 5: Commit**

```bash
git add amelia/agents/architect.py tests/unit/agents/test_architect.py
git commit -m "refactor(architect): make workflow_id required in plan()"
```

---

### Task 2: Update existing Architect tests to provide workflow_id

**Files:**
- Modify: `tests/unit/agents/test_architect.py:358-397`

**Step 1: Identify tests that call plan() without workflow_id**

Tests that need updating:
- `test_plan_reads_design_from_state` (line 267)
- `test_architect_emits_agent_output_after_plan_generation` (line 331)
- `test_architect_does_not_emit_when_no_emitter_configured` (line 378)
- `test_architect_emits_correct_task_count` (line 398)
- `test_architect_falls_back_to_issue_id_when_no_workflow_id` (line 449) - delete this test

**Step 2: Update tests to provide workflow_id**

```python
# test_plan_reads_design_from_state - add workflow_id
result = await architect.plan(state, workflow_id="test-workflow-123")

# test_architect_emits_agent_output_after_plan_generation - add workflow_id
result = await architect.plan(state, workflow_id="test-workflow-123")

# Also update assertion:
assert event.workflow_id == "test-workflow-123"  # Uses provided workflow_id

# test_architect_does_not_emit_when_no_emitter_configured - add workflow_id
result = await architect.plan(state, workflow_id="test-workflow-123")

# test_architect_emits_correct_task_count - add workflow_id
await architect.plan(state, workflow_id="test-workflow-123")

# Delete test_architect_falls_back_to_issue_id_when_no_workflow_id entirely
# (fallback logic is being removed)
```

**Step 3: Run tests to verify all pass**

Run: `uv run pytest tests/unit/agents/test_architect.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add tests/unit/agents/test_architect.py
git commit -m "test(architect): update tests to provide required workflow_id"
```

---

### Task 3: Update Developer.execute_current_task() and _execute_agentic() to require workflow_id

**Files:**
- Modify: `amelia/agents/developer.py:147-188`
- Test: `tests/unit/agents/test_developer.py`

**Step 1: Update Developer method signatures**

```python
# In amelia/agents/developer.py, modify execute_current_task():

    async def execute_current_task(
        self,
        state: ExecutionState,
        workflow_id: str,  # Required, no default
    ) -> dict[str, Any]:
        """Execute the current task from execution state.

        Args:
            state: Full execution state containing profile, plan, and current_task_id.
            workflow_id: Workflow ID for stream events (required).

        Returns:
            Dict with status, task_id, and output.

        Raises:
            ValueError: If current_task_id not found in plan.
            AgenticExecutionError: If agentic execution fails.
        """
```

And modify _execute_agentic():

```python
    async def _execute_agentic(
        self,
        task: Task,
        cwd: str,
        state: ExecutionState,
        workflow_id: str,  # Required, no default
    ) -> dict[str, Any]:
        """Execute task autonomously with full Claude tool access.

        Args:
            task: The task to execute.
            cwd: Working directory for execution.
            state: Full execution state for context compilation.
            workflow_id: Workflow ID for stream events (required).

        Returns:
            Dict with status and output.

        Raises:
            AgenticExecutionError: If execution fails.
        """
```

**Step 2: Remove fallback logic in _execute_agentic()**

Replace line 221:
```python
        # Use workflow_id directly (no fallback)
        async for event in self.driver.execute_agentic(messages, cwd, system_prompt=context.system_prompt):
            self._handle_stream_event(event, workflow_id)
```

**Step 3: Run tests**

Run: `uv run pytest tests/unit/agents/test_developer.py -v`
Expected: Some tests may fail

**Step 4: Commit**

```bash
git add amelia/agents/developer.py
git commit -m "refactor(developer): make workflow_id required"
```

---

### Task 4: Update Developer tests to provide workflow_id

**Files:**
- Modify: `tests/unit/agents/test_developer.py`

**Step 1: Update test methods to provide workflow_id**

```python
# test_developer_emits_stream_events_during_agentic_execution (line 57)
await developer.execute_current_task(state, workflow_id="TEST-123")

# test_developer_does_not_emit_when_no_emitter_configured (line 122)
result = await developer.execute_current_task(state, workflow_id="TEST-456")

# test_developer_converts_claude_events_to_stream_events (line 164)
await developer.execute_current_task(state, workflow_id="TEST-789")
```

**Step 2: Run tests**

Run: `uv run pytest tests/unit/agents/test_developer.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/unit/agents/test_developer.py
git commit -m "test(developer): update tests to provide required workflow_id"
```

---

### Task 5: Update Reviewer.review(), _single_review(), and _competitive_review() to require workflow_id

**Files:**
- Modify: `amelia/agents/reviewer.py:146-261`

**Step 1: Update Reviewer method signatures**

```python
# In amelia/agents/reviewer.py, modify review():

    async def review(
        self,
        state: ExecutionState,
        code_changes: str,
        workflow_id: str,  # Required, no default
    ) -> ReviewResult:
        """Review code changes in context of execution state and issue.

        Selects single or competitive review strategy based on profile settings.

        Args:
            state: Current execution state containing issue and profile context.
            code_changes: Diff or description of code changes to review.
            workflow_id: Workflow ID for stream events (required).

        Returns:
            ReviewResult with approval status, comments, and severity level.
        """
```

Modify _single_review():

```python
    async def _single_review(
        self,
        state: ExecutionState,
        code_changes: str,
        persona: str,
        workflow_id: str,  # Required, no default
    ) -> ReviewResult:
```

Modify _competitive_review():

```python
    async def _competitive_review(
        self,
        state: ExecutionState,
        code_changes: str,
        workflow_id: str,  # Required, no default
    ) -> ReviewResult:
```

**Step 2: Remove fallback logic in _single_review()**

Replace lines 220-230:

```python
        # Emit completion event before return
        if self._stream_emitter is not None:
            event = StreamEvent(
                type=StreamEventType.AGENT_OUTPUT,
                content=f"Review completed: {'Approved' if response.approved else 'Changes requested'}",
                timestamp=datetime.now(UTC),
                agent="reviewer",
                workflow_id=workflow_id,  # Use directly, no fallback
            )
            await self._stream_emitter(event)
```

**Step 3: Update internal call sites**

In review() method (line 165-168):
```python
        if state.profile.strategy == "competitive":
            return await self._competitive_review(state, code_changes, workflow_id)
        else:
            return await self._single_review(state, code_changes, persona="General", workflow_id=workflow_id)
```

In _competitive_review() (line 260):
```python
        review_tasks = [self._single_review(state, code_changes, persona, workflow_id) for persona in personas]
```

**Step 4: Run tests**

Run: `uv run pytest tests/unit/agents/test_reviewer.py -v`
Expected: Some tests may fail

**Step 5: Commit**

```bash
git add amelia/agents/reviewer.py
git commit -m "refactor(reviewer): make workflow_id required"
```

---

### Task 6: Update Reviewer tests to provide workflow_id

**Files:**
- Modify: `tests/unit/agents/test_reviewer.py`

**Step 1: Update test methods to provide workflow_id**

```python
# test_reviewer_emits_agent_output_after_review (line 44)
result = await reviewer.review(state, code_changes, workflow_id="TEST-123")
# Update assertion:
assert event.workflow_id == "TEST-123"

# test_reviewer_emits_changes_requested_event (line 102)
result = await reviewer.review(state, code_changes, workflow_id="test-workflow-456")

# test_reviewer_does_not_emit_when_no_emitter_configured (line 138)
result = await reviewer.review(state, code_changes, workflow_id="test-workflow-789")

# test_reviewer_emits_for_competitive_review (line 164)
result = await reviewer.review(state, code_changes, workflow_id="test-workflow-competitive")
```

**Step 2: Run tests**

Run: `uv run pytest tests/unit/agents/test_reviewer.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/unit/agents/test_reviewer.py
git commit -m "test(reviewer): update tests to provide required workflow_id"
```

---

### Task 7: Verify orchestrator nodes pass workflow_id correctly

**Files:**
- Review: `amelia/core/orchestrator.py:29-298`

**Step 1: Verify call_architect_node passes workflow_id**

Current code at lines 54-59:
```python
    stream_emitter = configurable.get("stream_emitter")
    workflow_id = configurable.get("thread_id")

    driver = DriverFactory.get_driver(state.profile.driver)
    architect = Architect(driver, stream_emitter=stream_emitter)
    plan_output = await architect.plan(state, workflow_id=workflow_id)
```

This correctly extracts `thread_id` from config and passes it as `workflow_id`. However, since `workflow_id` is now required, we should ensure the orchestrator validates it.

**Step 2: Add validation in orchestrator nodes**

In `call_architect_node` after extracting workflow_id (add around line 56):
```python
    workflow_id = configurable.get("thread_id")
    if not workflow_id:
        raise ValueError("workflow_id (thread_id) is required in config.configurable")
```

Similarly in `call_developer_node` and `call_reviewer_node`.

**Step 3: Run type checking**

Run: `uv run mypy amelia/core/orchestrator.py`
Expected: PASS or type errors to fix

**Step 4: Run full test suite**

Run: `uv run pytest tests/unit/ -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/core/orchestrator.py
git commit -m "refactor(orchestrator): validate workflow_id in nodes"
```

---

### Task 8: Verify CLI passes workflow_id correctly

**Files:**
- Review: `amelia/main.py:146-153`

**Step 1: Check plan-only command**

Current code at line 152-153:
```python
        architect = Architect(DriverFactory.get_driver(active_profile.driver))
        result = await architect.plan(state)
```

This does NOT pass workflow_id! Need to add it.

**Step 2: Update plan-only command to pass workflow_id**

```python
        architect = Architect(DriverFactory.get_driver(active_profile.driver))
        # Use issue_id as workflow_id for CLI mode
        result = await architect.plan(state, workflow_id=issue_id)
```

**Step 3: Check review command**

Current code at line 236:
```python
                result_dict = await call_reviewer_node(initial_state)
```

This calls the orchestrator node directly without config. Need to pass config with workflow_id.

**Step 4: Update review command**

```python
                # Create config with workflow_id for CLI mode
                from langchain_core.runnables.config import RunnableConfig
                config: RunnableConfig = {
                    "configurable": {
                        "thread_id": "LOCAL-REVIEW",  # Use issue ID as workflow_id
                        "execution_mode": "cli",
                    }
                }
                result_dict = await call_reviewer_node(initial_state, config=config)
```

**Step 5: Run CLI smoke test**

Run: `uv run amelia plan-only TEST-1 --help`
Expected: Shows help without error

**Step 6: Commit**

```bash
git add amelia/main.py
git commit -m "fix(cli): pass workflow_id to agents"
```

---

### Task 9: Run full verification

**Files:**
- All modified files

**Step 1: Run type checking**

Run: `uv run mypy amelia`
Expected: PASS

**Step 2: Run linting**

Run: `uv run ruff check amelia tests`
Expected: PASS or fixable warnings

**Step 3: Run full test suite**

Run: `uv run pytest tests/unit/ -v`
Expected: PASS

**Step 4: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "chore: fix any remaining issues from workflow_id refactor"
```

---
