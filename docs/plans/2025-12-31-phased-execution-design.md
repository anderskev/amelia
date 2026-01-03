# Phased Execution for Developer Agent

**Date**: 2025-12-31 (updated 2026-01-02)
**Status**: Draft
**Author**: Brainstorming session

## Problem

Large tasks cause context degradation. As the Developer session accumulates tool calls, file reads, and corrections, LLM quality drops - forcing human intervention.

The root cause is **context bloat**: each tool call adds tokens, file contents pile up, and correction cycles compound the problem. Even with fresh sessions per subtask, naive handoff strategies can reintroduce bloat by passing full plans and accumulated history to each subagent.

## Solution

Phased execution with context isolation. The Architect decomposes work into subtasks with explicit dependencies. Each subtask runs in a fresh session, using git as the handoff mechanism.

## Goals

- **Hands-off**: System runs autonomously until completion or unrecoverable failure
- **Context-fresh**: Each subtask starts with clean context (plan + current repo state)
- **Self-correcting**: Reviewer feedback triggers phase retry with fresh context
- **Fail-safe**: Halt on failure or 2 failed review attempts - never leave a mess

## Non-Goals

- Maximum parallelism (correctness over speed)
- Complex merge resolution (Architect ensures disjoint work)

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Task decomposition | Architect-driven | Architect already analyzes codebase; natural place for planning |
| Context handoff | Git + plan | Code is source of truth; plan provides strategic context |
| Execution model | Parallel where safe | Architect marks dependencies; independent subtasks run in parallel |
| Failure handling | Halt everything | Stop clean rather than build on broken foundations |
| Review timing | After each phase | Catches issues at natural sync points |
| Review rejection | Retry phase once | Fresh context + feedback; halt after 2 failures |
| Commit strategy | One commit per phase | Enables clean retry; subtasks work on uncommitted changes |
| TDD enforcement | Test-first subtasks | Tests written before implementation; Architect structures dependencies accordingly |
| Context strategy | Offload + summarize | Filesystem holds full state; subtasks get scoped context + phase summaries |

## Architecture

### Architect Plan Format

```python
class SubtaskType(str, Enum):
    TEST = "test"                # Write tests (red phase)
    IMPL = "impl"                # Write implementation (green phase)
    REFACTOR = "refactor"        # Refactor (optional cleanup)

@dataclass
class Subtask:
    id: str                      # e.g., "1a", "1b", "2a"
    title: str                   # Human-readable name
    description: str             # What this subtask accomplishes
    type: SubtaskType            # test, impl, or refactor
    depends_on: list[str]        # Subtask IDs that must complete first
    files_touched: list[str]     # Expected files (for conflict detection)

@dataclass
class PhasedPlanOutput:
    goal: str                    # Overall goal (existing)
    plan_markdown: str           # Full plan document (existing)
    subtasks: list[Subtask]      # Ordered list of subtasks
    phases: list[list[str]]      # Computed from dependencies
                                 # e.g., [["1"], ["2a", "2b", "2c"], ["3"]]
```

Example (TDD ordering - tests before implementation):
```
Subtasks:
  1a. "Write User model tests"       → type: test → depends: []    → phase 1
  1b. "Write Post model tests"       → type: test → depends: []    → phase 1
  2a. "Implement User model"         → type: impl → depends: [1a]  → phase 2
  2b. "Implement Post model"         → type: impl → depends: [1b]  → phase 2
  3a. "Write API endpoint tests"     → type: test → depends: [2a,2b] → phase 3
  3b. "Write CLI command tests"      → type: test → depends: [2a,2b] → phase 3
  4a. "Implement API endpoints"      → type: impl → depends: [3a]  → phase 4
  4b. "Implement CLI commands"       → type: impl → depends: [3b]  → phase 4
  5.  "Write integration tests"      → type: test → depends: [4a,4b] → phase 5
```

The Architect ensures each implementation subtask depends on its corresponding test subtask, enforcing the red-green TDD cycle at the task decomposition level.

### TDD Workflow

The phased execution model naturally supports TDD by structuring dependencies so tests run before implementation:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TDD Flow per Feature                            │
├─────────────────────────────────────────────────────────────────────────┤
│  Phase N:   Write tests (RED)                                           │
│             └── Tests exist but fail (no implementation yet)            │
│                                                                         │
│  Phase N+1: Write implementation (GREEN)                                │
│             └── Minimal code to make tests pass                         │
│                                                                         │
│  Phase N+2: Refactor (optional)                                         │
│             └── Clean up while keeping tests green                      │
└─────────────────────────────────────────────────────────────────────────┘
```

**Architect prompt guidance** for TDD decomposition:

```
When decomposing tasks into subtasks:
1. For each new feature/component, create a TEST subtask first
2. Create an IMPL subtask that depends on the TEST subtask
3. Tests should be written to fail initially (red phase)
4. Implementation should be minimal to pass tests (green phase)
5. Optional REFACTOR subtasks can follow implementation

Example pattern:
  "Write X tests" (type: test) → "Implement X" (type: impl) → "Refactor X" (type: refactor)
```

**Test subtask expectations**:
- Test subtask runs, writes tests, tests fail (expected - no impl yet)
- Subtask succeeds if tests are syntactically valid and would test the right behavior
- The Reviewer checks test quality, not test passage

**Impl subtask expectations**:
- Implementation subtask runs, writes code to pass tests
- Tests from prior phase should now pass
- The Reviewer checks both implementation quality and test passage

**Validation rule**: The phase executor validates that every `impl` subtask has at least one `test` subtask in its dependency chain. This catches Architect plans that skip the test-first discipline.

```python
def validate_tdd_ordering(subtasks: list[Subtask]) -> None:
    """Ensure every impl subtask depends on a test subtask."""
    subtask_map = {s.id: s for s in subtasks}

    for subtask in subtasks:
        if subtask.type == SubtaskType.IMPL:
            # Walk dependency chain looking for a test
            if not has_test_dependency(subtask, subtask_map):
                raise TDDViolationError(
                    f"Impl subtask '{subtask.id}' has no test dependency. "
                    "TDD requires tests before implementation."
                )
```

### Context Engineering

Fresh sessions alone don't solve context bloat—naive handoff reintroduces it. We apply patterns informed by production agent systems (notably [Manus](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)):

| Pattern | Application |
|---------|-------------|
| **Offloading** | Store full plan and tool outputs in filesystem; pass file references |
| **Restorable compression** | Summaries always include restoration paths (git refs, file paths) to recover full content |
| **Progressive disclosure** | Subtasks receive only context relevant to their specific assignment |
| **Goal recitation** | Restate objectives at END of context to keep them in the attention window |
| **Error preservation** | On retry, keep full error traces visible—failed attempts help models avoid repetition |
| **Stable prefixes** | Structure prompts so common prefixes are shared across same-phase subtasks (KV-cache optimization) |
| **Controlled variation** | Vary prompt framing on retry to break repetitive patterns |

#### Filesystem-Based State

The `.amelia/` directory serves as shared state across phases:

```
.amelia/execution/
├── plan.md                    # Full Architect plan (written once)
├── phase-1/
│   ├── summary.md             # Compact summary (generated post-phase)
│   └── review-feedback.md     # Reviewer comments if retry needed
├── phase-2/
│   ├── summary.md
│   └── ...
└── execution-state.json       # Phase/subtask status for recovery
```

This shifts from "push full context in prompt" to "pull on demand from filesystem."

#### Phase Summaries

After each phase commits, generate a compact summary for downstream phases. **Critical**: summaries must include restoration references so downstream phases can recover full context if needed:

```python
async def generate_phase_summary(
    phase_index: int,
    subtasks: list[Subtask],
    pre_commit: str,
    post_commit: str,
) -> str:
    """Generate compact summary with restoration references."""
    diff_stat = git_diff_stat(pre_commit, post_commit)
    files_changed = extract_files_from_diff(diff_stat)
    test_files = [f for f in files_changed if "test" in f.lower()]

    summary = f"""## Phase {phase_index} Summary

**Completed subtasks:**
{chr(10).join(f"- [{s.type.value}] {s.title}" for s in subtasks)}

**Files changed:** {', '.join(files_changed)}

**Restoration references:**
- Full diff: `git diff {pre_commit}..{post_commit}`
- Commit: `git show {post_commit}`
- Test files created: {', '.join(test_files) if test_files else 'None'}

**Key changes:**
{generate_change_summary(pre_commit, post_commit)}
"""

    summary_path = f".amelia/execution/phase-{phase_index}/summary.md"
    write_file(summary_path, summary)
    return summary_path
```

The restoration references ensure information is never irreversibly lost—downstream phases can `git show` or `git diff` to recover full details when the summary is insufficient.

Context growth becomes **O(phases)** not **O(total_tokens)**:

```
Phase 1: [full context for phase 1]
Phase 2: [phase 1 summary ~200 tokens] + [full context for phase 2]
Phase 3: [phase 1+2 summaries ~400 tokens] + [full context for phase 3]
```

#### Subtask-Scoped Context

Rather than passing the full plan to every subtask, scope context to relevance. Two key patterns:

1. **Stable prefix**: Start all subtask prompts with identical text to maximize KV-cache hits
2. **Goal recitation**: Restate the assignment at the END to keep it in the attention window

```python
# Stable prefix shared across ALL subtasks (enables KV-cache hits)
SUBTASK_PREFIX = """## Phased Execution Context

You are executing a subtask within a phased development plan.
- The orchestrator handles commits—do NOT commit
- Focus only on your specific assignment
- Read files from the codebase to understand current state
- The full plan is at .amelia/execution/plan.md if needed

"""

def build_subtask_context(
    subtask: Subtask,
    plan: PhasedPlanOutput,
    phase_index: int,
) -> str:
    """Build minimal context for a subtask with goal recitation."""
    # Get completed phase summaries (not full history)
    prior_summaries = [
        read_file(f".amelia/execution/phase-{i}/summary.md")
        for i in range(1, phase_index)
        if path_exists(f".amelia/execution/phase-{i}/summary.md")
    ]

    # Get direct dependency descriptions
    deps = [s for s in plan.subtasks if s.id in subtask.depends_on]

    # Extract only plan sections relevant to this subtask's files
    relevant_sections = extract_relevant_plan_sections(
        plan.plan_markdown,
        subtask.files_touched,
    )

    # Build context with stable prefix first
    context = f"""{SUBTASK_PREFIX}
## Prior Phase Summaries
{chr(10).join(prior_summaries) if prior_summaries else "This is phase 1 - no prior phases."}

## Your Dependencies (Completed)
{chr(10).join(f"- {d.title}: {d.description}" for d in deps) if deps else "None - this subtask has no dependencies."}

## Relevant Plan Sections
{relevant_sections}

## Your Assignment (Restated for Attention)

**Subtask:** {subtask.title}
**Type:** {subtask.type.value}
**Files:** {', '.join(subtask.files_touched)}

{subtask.description}

Remember: Make the changes. Do NOT commit.
"""
    return context
```

The goal recitation at the end combats "lost-in-the-middle" issues where models lose track of objectives after processing long contexts.

#### Feedback for Retry (Error Preservation)

On retry, the instinct is to compact feedback to save tokens. However, research shows that **preserving full error context improves recovery**—failed attempts help models avoid repetition and update their beliefs about what doesn't work.

The key insight: put actionable items at the END (in the attention window) while keeping full errors visible:

```python
def prepare_retry_feedback(
    raw_feedback: str,
    phase_index: int,
    attempt: int,
) -> str:
    """Preserve full errors but structure for attention."""
    action_items = extract_actionable_items(raw_feedback)

    # Vary framing on retry to break repetitive patterns
    retry_framing = [
        "The previous approach failed. A different strategy is needed.",
        "Review the errors carefully before proceeding differently.",
        "The prior attempt had issues. Consider an alternative approach.",
    ]

    return f"""## Retry Attempt {attempt}

{retry_framing[(attempt - 1) % len(retry_framing)]}

### Previous Attempt Errors (Full Context)

The following errors occurred. Keeping them visible helps avoid repetition:

{raw_feedback}

### Action Items (Focus Here)

{action_items}

Full feedback preserved at: .amelia/execution/phase-{phase_index}/review-feedback.md
"""
```

This follows the Manus insight: "leave the wrong turns in the context." Error recovery requires seeing what failed.

### Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Developer Node                            │
├─────────────────────────────────────────────────────────────────┤
│  for each phase in plan.phases:                                 │
│    1. Spawn subagents for all subtasks in phase (parallel)      │
│    2. Wait for all to complete                                  │
│    3. If any failed → halt everything                           │
│    4. Run Reviewer on phase changes                             │
│    5. If rejected:                                              │
│       - Retry phase once with feedback                          │
│       - If rejected again → halt                                │
│    6. Continue to next phase                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Subagent Spawning

Each subtask gets a fresh driver instance with **scoped context** (not the full plan). The context is structured for KV-cache optimization and attention management:

```python
async def run_subtask(
    subtask: Subtask,
    plan: PhasedPlanOutput,
    phase_index: int,
    attempt: int = 1,
    retry_feedback: str | None = None,
) -> SubtaskResult:
    # Fresh driver instance = fresh context
    driver = DriverFactory.get_driver(profile.driver)

    # Build scoped context with stable prefix and goal recitation
    context = build_subtask_context(subtask, plan, phase_index)

    # On retry, prepend error context (full errors + action items at end)
    if retry_feedback:
        prompt = f"{retry_feedback}\n\n{context}"
    else:
        prompt = context

    async for message in driver.execute_agentic(prompt, cwd):
        yield message
```

**Token savings**: A 2000-token plan becomes ~300 tokens of scoped context per subtask.

**Cache optimization**: The stable `SUBTASK_PREFIX` at the start of every prompt enables KV-cache hits across subtasks. For Claude Sonnet, this is a 10x cost reduction on cached tokens (0.30 vs 3.00 USD/MTok).

### Commit Strategy

Subtasks within a phase run in parallel on the same working directory. To avoid git conflicts and enable clean retries, we use **one commit per phase**:

1. **Subtasks make file changes only** - no commits during subtask execution
2. **Phase executor commits** - after all subtasks complete successfully, create a single commit
3. **Reviewer reviews the phase commit** - diffs against pre-phase HEAD
4. **On retry, reset is clean** - `git reset --hard pre_commit` discards all uncommitted changes

```python
async def run_phase(
    phase_index: int,
    phase: list[Subtask],
    plan: PhasedPlanOutput,
    attempt: int = 1,
    retry_feedback: str | None = None,
) -> str:
    """Execute all subtasks in a phase, commit, and generate summary.

    Returns the post-commit SHA for summary generation.
    """
    pre_commit = git_rev_parse("HEAD")

    # Run subtasks in parallel with scoped context
    results = await asyncio.gather(*[
        run_subtask(subtask, plan, phase_index, attempt, retry_feedback)
        for subtask in phase
    ])

    # Check for failures
    if any(r.failed for r in results):
        raise SubtaskFailed(results)

    # Single commit for the entire phase
    subtask_titles = ", ".join(s.title for s in phase)
    git_add(".")
    git_commit(f"Phase {phase_index}: {subtask_titles}")

    post_commit = git_rev_parse("HEAD")

    # Generate summary with restoration references for downstream phases
    await generate_phase_summary(phase_index, phase, pre_commit, post_commit)

    return post_commit
```

**Why not worktrees?** Git worktrees would allow true parallel commits, but add complexity:
- Merge conflicts between worktrees
- Subtask isolation breaks "read current state" semantics
- Architect already ensures disjoint file changes

The single-commit approach is simpler and aligns with the "correctness over speed" non-goal.

### Phase Review with Retry

```python
async def run_phase_with_retry(
    phase_index: int,
    phase: list[Subtask],
    plan: PhasedPlanOutput,
    max_attempts: int = 2,
) -> None:
    retry_feedback = None
    pre_commit = git_rev_parse("HEAD")  # Capture once before any attempts

    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            # Reset to pre-phase state for clean retry
            git_reset_hard(pre_commit)

        # Run all subtasks (with error context on retry)
        await run_phase(phase_index, phase, plan, attempt, retry_feedback)

        # Review phase changes
        result = await review_phase(phase, pre_commit, plan)

        if result.approved:
            return  # Success, continue to next phase

        # Store full feedback in filesystem
        feedback_path = f".amelia/execution/phase-{phase_index}/review-feedback.md"
        write_file(feedback_path, result.comments)

        # Prepare retry feedback: full errors + action items at end + varied framing
        retry_feedback = prepare_retry_feedback(
            result.comments, phase_index, attempt
        )

    raise PhaseReviewFailed(phase, result)  # Halt after max_attempts failures
```

### State Tracking

```python
class PhaseStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class SubtaskState:
    subtask_id: str
    status: PhaseStatus
    attempt: int              # 1 or 2
    started_at: datetime | None
    completed_at: datetime | None
    error: str | None

@dataclass
class PhaseState:
    phase_index: int
    subtasks: list[SubtaskState]
    status: PhaseStatus
    pre_phase_commit: str     # For reset on retry
    review_result: ReviewResult | None
```

### Stream Events

```python
class StreamEventType(str, Enum):
    # ... existing ...
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    PHASE_RETRY = "phase_retry"
    SUBTASK_STARTED = "subtask_started"
    SUBTASK_COMPLETED = "subtask_completed"
    SUBTASK_FAILED = "subtask_failed"
```

Dashboard display:
```
Phase 1 (test): ✓ Write model tests
  ├── ✓ [test] User model tests
  └── ✓ [test] Post model tests
Phase 2 (impl): ● Running (1/2 subtasks complete)
  ├── ✓ [impl] User model
  └── ● [impl] Post model (running)
Phase 3 (test): ○ Pending - Write API tests
Phase 4 (impl): ○ Pending - Implement APIs
Phase 5 (test): ○ Pending - Integration tests
```

## Implementation Plan

### Files to Modify

| File | Changes |
|------|---------|
| `amelia/agents/architect.py` | Add `PhasedPlanOutput` model, update prompt to generate TDD-ordered subtasks with dependencies |
| `amelia/agents/developer.py` | Add `run_phased()` method alongside existing `run()`, subtask spawning logic |
| `amelia/core/state.py` | Add `PhaseState`, `SubtaskState`, extend `ExecutionState` |
| `amelia/core/types.py` | Add `SubtaskType` enum, new `StreamEventType` variants for phase/subtask events |
| `amelia/core/orchestrator.py` | Update `call_developer_node` to detect phased plans and dispatch accordingly |

### New Modules

```
amelia/core/phased_executor.py
├── validate_tdd_ordering()     # Ensure impl subtasks depend on test subtasks
├── run_phase()                 # Execute all subtasks in a phase + commit + summary
├── run_subtask()               # Single subtask with fresh driver (scoped context)
├── run_phase_with_retry()      # Retry logic with git reset on failure
├── execute_phased_plan()       # Top-level orchestrator
└── initialize_execution_dir()  # Create .amelia/execution/ structure

amelia/core/context_engineering.py
├── SUBTASK_PREFIX                  # Stable prefix for KV-cache optimization
├── build_subtask_context()         # Assemble scoped context with goal recitation
├── extract_relevant_plan_sections() # Extract plan sections by file patterns
├── generate_phase_summary()        # Create summary with restoration references
├── prepare_retry_feedback()        # Full errors + action items + varied framing
├── extract_actionable_items()      # Parse reviewer feedback into action list
├── write_execution_state()         # Persist phase/subtask state to JSON
└── read_execution_state()          # Recover state for resumption
```

### Backward Compatibility

- If Architect returns a plan without subtasks → existing single-session behavior
- If Architect returns a plan with subtasks → phased execution
- Profile flag `enable_phased_execution: bool = True` to opt-out if needed

## Testing Strategy

1. **Unit tests**: Phase dependency resolution, retry logic, state transitions
2. **Context engineering tests**:
   - `build_subtask_context()` returns expected tokens for various subtask positions
   - `build_subtask_context()` starts with stable `SUBTASK_PREFIX` (cache optimization)
   - `build_subtask_context()` ends with goal recitation (attention optimization)
   - `extract_relevant_plan_sections()` correctly filters by file patterns
   - `generate_phase_summary()` produces valid markdown with restoration references
   - `generate_phase_summary()` includes git refs that resolve correctly
   - `prepare_retry_feedback()` preserves full error context
   - `prepare_retry_feedback()` puts action items at end of output
   - `prepare_retry_feedback()` varies framing across attempts
3. **Integration tests**: Full phased execution with mock driver
4. **E2E tests**: Real multi-phase task with actual LLM calls
5. **Token budget tests**: Verify context stays under target budget across phases
6. **Cache optimization tests**: Verify prompt prefix stability across same-phase subtasks

## Open Questions

1. **Summary generation strategy**: Should `generate_phase_summary()` use LLM summarization or rule-based extraction? LLM produces better summaries but adds latency and cost. Initial implementation will use rule-based extraction (git diff parsing) with LLM as optional enhancement.

2. **Relevant section extraction**: How sophisticated should `extract_relevant_plan_sections()` be? Options:
   - Simple: Regex for file paths in markdown headers
   - Medium: Parse markdown AST, match sections by mentioned files
   - Complex: Semantic search over plan chunks

   Start with medium approach; upgrade if subtasks lack sufficient context.

3. **Controlled variation scope**: How much should retry framing vary? Current design uses 3 static variations. Options:
   - Static list (current): Simple, predictable
   - LLM-generated: More natural variation but adds latency
   - Template with random elements: Middle ground

   Start with static list; measure repetition rates before adding complexity.
