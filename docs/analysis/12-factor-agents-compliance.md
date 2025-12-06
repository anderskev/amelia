# 12-Factor Agents Compliance Analysis

> Analyzing Amelia's alignment with the [12-Factor Agents](https://github.com/humanlayer/12-factor-agents) methodology.

## Executive Summary

| Factor | Status | Notes |
|--------|--------|-------|
| 1. Natural Language → Tool Calls | **Strong** | Schema-validated outputs, structured task execution |
| 2. Own Your Prompts | **Partial** | Prompts embedded in code, not templated or versioned |
| 3. Own Your Context Window | **Partial** | Message history exists, but not custom-formatted |
| 4. Tools Are Structured Outputs | **Strong** | Pydantic schemas enforce structure |
| 5. Unify Execution State | **Partial** | State split between LangGraph and SQLite |
| 6. Launch/Pause/Resume | **Partial** | Approval gates exist, but no persistent pause/resume |
| 7. Contact Humans with Tools | **Weak** | CLI prompts, not tool-based human contact |
| 8. Own Your Control Flow | **Strong** | LangGraph provides full control over flow |
| 9. Compact Errors | **Weak** | Limited error recovery, no retry thresholds |
| 10. Small, Focused Agents | **Strong** | Architect/Developer/Reviewer separation |
| 11. Trigger from Anywhere | **Partial** | CLI + REST, chat integration planned |
| 12. Stateless Reducer | **Partial** | State machine exists, but state is mutable |
| 13. Pre-fetch Context | **Weak** | No proactive context fetching |

**Overall**: 4 Strong, 6 Partial, 3 Weak

---

## Detailed Analysis

### Factor 1: Natural Language to Tool Calls

> **Principle**: Convert natural language inputs into structured, deterministic tool calls.

#### Current Implementation: Strong

Amelia excels here:

```python
# Architect produces TaskDAG from natural language issue
class TaskListResponse(BaseModel):
    tasks: list[Task]

class Task(BaseModel):
    name: str
    description: str
    steps: list[Step]          # Structured sub-tasks
    dependencies: list[str]     # DAG edges
    files_modified: list[str]
```

**What we do well:**
- Issues are converted to structured `TaskDAG` objects
- Schema validation via Pydantic ensures LLM outputs conform
- CLI driver uses `--json-schema` for structured generation
- Tasks contain explicit steps (TDD structure: test → implement → commit)

**Evidence:**
- `amelia/agents/architect.py:62-68` - Schema-validated task generation
- `amelia/core/state.py:45-89` - Task/TaskDAG models with validators

#### Gap: None significant

---

### Factor 2: Own Your Prompts

> **Principle**: Treat prompts as first-class code you control and iterate on.

#### Current Implementation: Partial

**What we do well:**
- Explicit system prompts define each agent's role
- Role-specific instructions (architect vs developer vs reviewer)
- Schema definitions enforce output structure

**What we're missing:**
- Prompts are **hardcoded strings** in agent files, not templates
- No prompt versioning or A/B testing infrastructure
- No centralized prompt registry for iteration
- Can't iterate on prompts without code changes

**Current pattern (embedded):**
```python
# amelia/agents/architect.py - prompt is inline
SYSTEM_PROMPT = """You are an expert software architect..."""
```

**Recommended pattern (templated):**
```python
# prompts/architect/system.md
# prompts/architect/user.jinja2
prompt_manager.load("architect", context={"issue": issue})
```

#### Gap: Roadmap doesn't address this directly

**Recommendation**: Add prompt templating system (Jinja2 + versioning) in future phase.

---

### Factor 3: Own Your Context Window

> **Principle**: Control how history, state, and tool results are formatted for the LLM.

#### Current Implementation: Partial

**What we do well:**
- `ExecutionState` tracks messages, plan, and review history
- Messages accumulate across agent transitions
- Reviewer sees full diff context

**What we're missing:**
- Standard message format (system/user/assistant), not custom XML/event format
- No structured event thread with typed events
- History not optimized for token efficiency
- No context compaction or summarization
- Errors not structured for LLM self-healing

**Current pattern:**
```python
# Messages are simple AgentMessage objects
class AgentMessage:
    role: str  # "system", "user", "assistant"
    content: str
```

**12-Factor pattern:**
```xml
<event type="tool_result" tool="create_task" status="success">
  {"task_id": "T-123", "name": "Add login"}
</event>
<event type="error" recoverable="true">
  {"message": "File not found", "suggestion": "Check path"}
</event>
```

#### Gap: Roadmap Phase 3 (Session Continuity) partially addresses this

Phase 3 adds `amelia-progress.json` and session logs, but these are for human handoffs, not LLM context optimization.

**Recommendation**: Add structured event thread format for LLM context.

---

### Factor 4: Tools Are Structured Outputs

> **Principle**: Tools are JSON outputs that trigger deterministic code, not magic function calls.

#### Current Implementation: Strong

**What we do well:**
- Tool calls produce structured responses (`DeveloperResponse`, `ReviewResponse`)
- Separation between LLM intent and execution handler
- Validation layer between LLM output and tool execution

**Evidence:**
```python
# amelia/agents/developer.py
class DeveloperResponse(BaseModel):
    status: Literal["completed", "failed", "needs_review"]
    output: str
    error: str | None
```

The handler interprets this structure and takes appropriate action.

#### Gap: None significant

---

### Factor 5: Unify Execution State

> **Principle**: Merge execution state (current step, retry count) with business state (messages, results).

#### Current Implementation: Partial

**What we do well:**
- `ExecutionState` contains both business data (issue, plan) and execution metadata (workflow_status)
- State passed through LangGraph transitions
- Server persists full state as JSON blob

**What we're missing:**
- **Dual state systems**: LangGraph in-memory checkpoints + SQLite `state_json`
- Retry counts, error history not tracked in unified state
- No single serializable object that captures everything
- State reconstruction requires both LangGraph checkpoint AND database

**Current split:**
```
ExecutionState (LangGraph) ←→ ServerExecutionState (SQLite)
    ↓                              ↓
In-memory checkpoints         state_json blob
```

**12-Factor pattern:**
```python
# Single Thread object contains everything
thread = Thread(
    events=[...],           # Full history
    current_step=3,         # Execution pointer
    error_count=1,          # Retry tracking
    human_pending=True      # Waiting state
)
```

#### Gap: Roadmap Phase 3 (Session Continuity) addresses this

`amelia-progress.json` moves toward a single source of truth that's Git-reconstructible.

---

### Factor 6: Launch/Pause/Resume

> **Principle**: Agents should support simple launch, query, pause, and resume via external triggers.

#### Current Implementation: Partial

**What we do well:**
- Launch: CLI (`amelia start ISSUE-123`) and REST API (`POST /workflows`)
- Human approval gate pauses between planning and execution
- WebSocket events enable async notification

**What we're missing:**
- **No pause between tool selection and invocation** - critical for approval workflows
- No webhook-based resume from external systems
- State not fully serializable for resume after process restart
- No "fire-and-forget" background execution with callback

**Current flow:**
```
Plan → [PAUSE: Human Approval] → Execute All Tasks → Review
```

**12-Factor flow:**
```
Plan → [PAUSE] → Select Tool → [PAUSE: Approve?] → Execute Tool → Loop
```

The granular pause between selection and execution is missing.

#### Gap: Roadmap Phase 2 + 3 partially address this

- Phase 2: WebSocket events, REST endpoints
- Phase 3: Session kickoff protocol, progress artifacts

**Still missing**: Per-tool-call approval gates, webhook resume triggers.

**Recommendation**: Add tool-level approval mode for high-risk operations.

---

### Factor 7: Contact Humans with Tool Calls

> **Principle**: Use structured tool calls (intent, question, options) to contact humans.

#### Current Implementation: Weak

**What we do:**
- CLI: `typer.confirm()` / `typer.prompt()` - blocking synchronous prompts
- Server: REST endpoints for approval/rejection
- No structured human contact from within agent loop

**What we're missing:**
- **No `request_human_input` tool** - agents can't ask clarifying questions
- Human contact is hardcoded at graph nodes, not tool-based
- No support for different contact formats (yes/no, multiple choice, free text)
- No async human response handling (webhooks)

**Current pattern:**
```python
# Human interaction hardcoded in orchestrator
def human_approval_node(state):
    approved = typer.confirm("Approve?")  # Blocking!
```

**12-Factor pattern:**
```python
# Agent requests human input as a tool call
{
    "intent": "request_human_input",
    "question": "The API schema is ambiguous. Should I...",
    "options": ["Option A: REST", "Option B: GraphQL"],
    "urgency": "high"
}
# Loop breaks, webhook resumes when human responds
```

#### Gap: Not addressed in current roadmap

Phase 9 (Chat Integration) adds Slack/Discord, but doesn't restructure human contact as tool calls.

**Recommendation**: Add `request_human_input` tool type that breaks execution loop.

---

### Factor 8: Own Your Control Flow

> **Principle**: Build custom control structures tailored to your use case.

#### Current Implementation: Strong

**What we do well:**
- LangGraph provides full control over transitions
- Conditional edges based on task completion, review status
- Custom routing logic (developer loop, reviewer rejection loop)
- Execution modes (agentic vs structured)

**Evidence:**
```python
# amelia/core/orchestrator.py
graph.add_conditional_edges(
    "developer",
    lambda s: "developer" if s.plan.get_ready_tasks() else "reviewer"
)
graph.add_conditional_edges(
    "reviewer",
    route_after_review  # Custom logic
)
```

**What we could improve:**
- No context compaction mid-workflow
- No LLM-as-judge validation layer
- Rate limiting handled per-driver, not centrally

#### Gap: Mostly addressed

Control flow is a strength. Future work could add compaction and validation.

---

### Factor 9: Compact Errors into Context Window

> **Principle**: Enable self-healing by capturing errors in context for LLM analysis.

#### Current Implementation: Weak

**What we do:**
- Errors logged via loguru
- `SafeShellExecutor` returns error details
- `DeveloperResponse` can contain `error` field

**What we're missing:**
- **No error event thread** - errors not accumulated in context
- **No retry threshold** - no consecutive error counter
- **No self-healing loop** - errors don't trigger adjusted tool calls
- Errors logged but not fed back to LLM for correction

**Current pattern:**
```python
# Error returned, but not added to context for retry
try:
    result = await executor.run(command)
except ShellExecutionError as e:
    logger.error(f"Command failed: {e}")
    return DeveloperResponse(status="failed", error=str(e))
```

**12-Factor pattern:**
```python
# Error added to thread, LLM retries with context
thread.append(Event(type="error", data=format_error(e)))
if consecutive_errors < 3:
    continue  # LLM sees error and adjusts
else:
    escalate_to_human()
```

#### Gap: Not addressed in roadmap

**Recommendation**: Add error event tracking with retry thresholds in Phase 4 (Verification Framework).

---

### Factor 10: Small, Focused Agents

> **Principle**: Build specialized agents with limited scope (3-10 steps max).

#### Current Implementation: Strong

**What we do well:**
- **Architect**: Single responsibility - issue → plan
- **Developer**: Single responsibility - task → code
- **Reviewer**: Single responsibility - code → feedback
- Tasks scoped to ~3-5 steps each
- Competitive review spawns multiple focused reviewer personas

**Evidence:**
```
Issue → Architect (1 step)
     → Developer (N tasks, each 3-5 steps)
     → Reviewer (1 review per diff)
```

**What we could improve:**
- No explicit step limit enforcement
- Large tasks could still overwhelm context

#### Gap: None significant

Strong compliance with this factor.

---

### Factor 11: Trigger from Anywhere

> **Principle**: Enable triggers from multiple channels (CLI, Slack, email, events).

#### Current Implementation: Partial

**What we do:**
- CLI: `amelia start`, `amelia plan-only`, `amelia review`
- REST API: Full CRUD for workflows
- WebSocket: Real-time event streaming

**What we're missing:**
- **No chat integration** - can't trigger from Slack/Discord
- **No event-driven triggers** - no cron, webhook, or external event support
- **No bidirectional chat** - agents can't respond in channels

#### Gap: Roadmap Phase 9 (Chat Integration) addresses this

- Slack DM interface
- Discord bot commands
- Approval via action buttons
- Per-channel verbosity

**Timeline**: Currently Phase 2 is in progress; Phase 9 is future.

---

### Factor 12: Stateless Reducer

> **Principle**: Treat agents as stateless reducers transforming input through deterministic steps.

#### Current Implementation: Partial

**What we do well:**
- LangGraph nodes are effectively reducers (state in → state out)
- `ExecutionState` is immutable (updates create new instances)
- Transitions are deterministic based on state

**What we're missing:**
- State mutations happen in-place within nodes
- No pure-function composition pattern
- Hidden state in driver sessions, subprocess handles
- `MemorySaver` is mutable shared state

**Evidence of mutation:**
```python
# State is updated in place, not returned as new object
state.plan.tasks[idx].status = "completed"
```

**12-Factor pattern:**
```python
# Pure reducer returns new state
def developer_node(state: State) -> State:
    new_tasks = [t.with_status("completed") if ... else t for t in state.tasks]
    return state.with_tasks(new_tasks)
```

#### Gap: Not directly addressed in roadmap

**Recommendation**: Consider immutable state updates for better debugging/replay.

---

### Appendix 13: Pre-fetch Context

> **Principle**: Fetch likely-needed data upfront rather than mid-workflow.

#### Current Implementation: Weak

**What we do:**
- Issue context fetched once at start
- Design documents attached if provided
- Git diff fetched for reviewer

**What we're missing:**
- **No proactive context fetching** - don't pre-fetch codebase structure, existing tests, CI status
- **No RAG integration** - don't retrieve relevant code before planning
- **No pre-fetched documentation** - architect doesn't see existing patterns

**12-Factor pattern:**
```python
# Before architect runs, pre-fetch:
context = {
    "issue": issue,
    "existing_tests": find_related_tests(issue),
    "similar_features": search_codebase(issue.keywords),
    "ci_status": get_pipeline_status(),
    "recent_commits": get_commit_history(5)
}
```

#### Gap: Roadmap Phase 11 (Spec Builder) partially addresses this

Spec Builder adds document ingestion, semantic search, and source citations. This enables pre-fetching design context.

**Still missing**: Automatic code/test pre-fetching for Architect.

---

## Gap Summary by Roadmap Phase

### Addressed in Current Roadmap

| Gap | Roadmap Phase |
|-----|---------------|
| State persistence | Phase 2: SQLite, REST API |
| Session continuity | Phase 3: Progress artifacts, handoff protocol |
| Event streaming | Phase 2: WebSocket events |
| Multi-channel triggers | Phase 9: Slack/Discord integration |
| Document context | Phase 11: Spec Builder with RAG |

### Not Addressed in Roadmap

| Gap | Recommendation |
|-----|----------------|
| Prompt templating | Add prompt versioning system |
| Structured event thread | Replace message history with typed events |
| Tool-level approval | Add granular pause between selection/execution |
| `request_human_input` tool | Enable agents to ask clarifying questions |
| Error self-healing | Add retry thresholds and error context |
| Context pre-fetching | Auto-fetch related code for Architect |
| Immutable state | Refactor to pure reducer pattern |

---

## Recommendations

### High Priority

1. **Add `request_human_input` tool** - Enables agents to ask clarifying questions mid-workflow, breaking the loop for async response.

2. **Implement error retry with thresholds** - Track consecutive errors, feed them back to LLM context, escalate after threshold.

3. **Pre-fetch code context for Architect** - Before planning, fetch existing tests, similar features, and recent changes.

### Medium Priority

4. **Add tool-level approval mode** - For high-risk operations (deployments, data mutations), pause between tool selection and execution.

5. **Externalize prompts** - Move to Jinja2 templates with version control and A/B testing capability.

6. **Structured event thread** - Replace simple message history with typed events (tool_call, tool_result, error, human_response).

### Lower Priority

7. **Immutable state updates** - Refactor to pure reducer pattern for better debugging and replay.

8. **Context compaction** - Add summarization for long-running workflows to prevent context exhaustion.

---

## Conclusion

Amelia follows the 12-Factor Agents methodology in key areas:
- **Strong**: Structured outputs (F1, F4), focused agents (F10), control flow ownership (F8)
- **Partial**: State management (F5, F12), launch/pause (F6), context (F3)
- **Weak**: Human contact as tools (F7), error recovery (F9), pre-fetching (F13)

The roadmap addresses several gaps through Phase 2-11, particularly around persistence, session continuity, and multi-channel triggers. However, critical patterns like structured human contact, error self-healing, and context pre-fetching require additional work not currently planned.

The strongest alignment is with Factor 10 (Small, Focused Agents) - Amelia's Architect/Developer/Reviewer separation exemplifies the recommended pattern. The weakest alignment is with Factor 7 (Human Contact via Tools) - human interaction is currently hardcoded at graph nodes rather than being a first-class tool type.
