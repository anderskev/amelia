# Plan Validator Node Design

**Issue:** #199 - Plan validator node for agentic architect output
**Date:** 2026-01-04
**Status:** Ready for implementation

## Overview

Add a `plan_validator_node` that transforms raw architect output into structured `PlanOutput`, replacing the fragile regex-based goal extraction (`_extract_goal_from_markdown()`).

## Graph Changes

**New flow:**
```
architect_node → plan_validator_node → human_approval_node → developer_node → ...
```

**Changes to `create_orchestrator_graph()`:**
```python
# Add node
workflow.add_node("plan_validator_node", plan_validator_node)

# Update edges
workflow.add_edge("architect_node", "plan_validator_node")  # NEW
workflow.add_edge("plan_validator_node", "human_approval_node")  # Changed from architect
```

## Validator Node Implementation

**Location:** `amelia/core/orchestrator.py`

**Function signature:**
```python
async def plan_validator_node(
    state: ExecutionState,
    config: RunnableConfig | None = None,
) -> dict[str, Any]:
    """Validate and extract structure from architect's plan file.

    Reads the plan file written by the architect and uses an LLM to extract
    structured fields (goal, plan_markdown, key_files) using the MarkdownPlanOutput schema.

    Args:
        state: Current execution state with raw_architect_output.
        config: RunnableConfig with profile in configurable.

    Returns:
        Partial state dict with goal, plan_markdown, plan_path, key_files.

    Raises:
        ValueError: If plan file not found or empty.
    """
```

**Logic flow:**
1. Extract config params (profile, workflow_id, stream_emitter)
2. Resolve plan path using `resolve_plan_path(profile.plan_path_pattern, issue.id)`
3. Read plan file content - fail if file doesn't exist or is empty
4. Get validator driver using `profile.validator_model` (with fallback to `profile.model`)
5. Call `driver.generate()` with `MarkdownPlanOutput` schema to extract structured fields
6. Return `{goal, plan_markdown, plan_path, key_files}`

**Extraction prompt:**
```
Extract the implementation plan structure from the following markdown plan.

<plan>
{plan_content}
</plan>

Return:
- goal: 1-2 sentence summary of what this plan accomplishes
- plan_markdown: The full plan content (preserve as-is)
- key_files: List of files that will be created or modified
```

**Error handling:**
- Plan file doesn't exist → `ValueError("Plan file not found at {path}")`
- Plan file empty → `ValueError("Plan file is empty")`
- LLM extraction fails → Let driver exception propagate

## Profile Changes

**Add to `amelia/core/types.py`:**
```python
class Profile(BaseModel):
    # ... existing fields ...

    validator_model: str | None = None
    """Optional model for plan validation. Uses a fast/cheap model for extraction.
    If not set, falls back to profile.model."""
```

**Usage in validator node:**
```python
model = profile.validator_model or profile.model
driver = DriverFactory.get_driver(profile.driver, model=model)
```

## Architect Node Simplification

**Current:** `call_architect_node()` does plan reading, goal extraction, and returns structured data.

**After:** Returns only raw output and tool history:
```python
return {
    "raw_architect_output": final_state.raw_architect_output,
    "tool_calls": list(final_state.tool_calls),
    "tool_results": list(final_state.tool_results),
}
```

**Removed from architect_node:**
- Plan file reading logic (lines 267-305)
- Goal extraction calls (lines 307-310)
- `plan_markdown` and `plan_path` return values

## Cleanup

**Delete:**
- `_extract_goal_from_markdown()` function (lines 128-203 in orchestrator.py)

**Tests to remove:**
- `TestExtractGoalFromMarkdown` class in `tests/unit/core/test_orchestrator_helpers.py`

**Tests to update:**
- `tests/unit/core/test_orchestrator_plan_extraction.py` - update assertions for new architect_node return values

## Testing Strategy

**New tests in `tests/unit/core/test_plan_validator_node.py`:**

| Test Case | Description |
|-----------|-------------|
| `test_validator_extracts_goal_from_plan` | Happy path - valid plan file, extracts goal/markdown/key_files |
| `test_validator_fails_when_plan_file_missing` | Raises `ValueError` with clear message |
| `test_validator_fails_when_plan_file_empty` | Raises `ValueError` |
| `test_validator_uses_validator_model_when_set` | Confirms driver uses `profile.validator_model` |
| `test_validator_falls_back_to_profile_model` | When `validator_model` is None, uses `profile.model` |

**Integration tests:**

| Test Case | Description |
|-----------|-------------|
| `test_architect_to_validator_flow` | Full flow: architect writes plan → validator extracts structure |
| `test_graph_routes_through_validator` | Verify graph edge: architect → validator → human_approval |

## Files to Modify

| File | Changes |
|------|---------|
| `amelia/core/orchestrator.py` | Add `plan_validator_node()`, update graph edges, delete `_extract_goal_from_markdown()`, simplify `call_architect_node()` |
| `amelia/core/types.py` | Add `validator_model: str \| None = None` to `Profile` |
| `tests/unit/core/test_orchestrator_helpers.py` | Delete `TestExtractGoalFromMarkdown` class |
| `tests/unit/core/test_orchestrator_plan_extraction.py` | Update assertions for new architect_node return values |
| `tests/unit/core/test_plan_validator_node.py` | New file with validator tests |

## Design Decisions

1. **Validator location:** In `orchestrator.py` alongside other nodes (matches existing pattern)
2. **Model selection:** Configurable `profile.validator_model` with fallback to `profile.model`
3. **Error handling:** Fail workflow on validation errors (clear signal, user can retry)
4. **Extraction source:** Plan file content (not raw_architect_output)
