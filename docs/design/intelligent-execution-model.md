# Intelligent Execution Model Design

> Transforming Developer from blind executor to intelligent plan follower with batch checkpoints and blocker handling.
> Complements [Dynamic Orchestration](./dynamic-orchestration.md) and [Stateless Reducer Pattern](./stateless-reducer-pattern.md).

## Problem Statement

Amelia's Developer agent currently has two execution modes, neither of which is ideal:

| Mode | Behavior | Problem |
|------|----------|---------|
| **Structured** | Blindly executes TaskStep commands | Crashes when `npm test` doesn't exist; no judgment |
| **Agentic** | Full LLM autonomy | No plan structure; unpredictable; hard to checkpoint |

The target behavior mirrors the `superpowers:writing-plans` + `superpowers:executing-plans` workflow:

1. **Detailed plans** with bite-sized tasks (2-5 min each), exact code, exact commands, expected output
2. **Intelligent execution** where an LLM follows the plan WITH judgment:
   - Reviews plan critically before starting
   - Validates steps before execution (e.g., checks if npm test exists)
   - Executes in batches with checkpoints for human review
   - Stops and asks when blocked (doesn't crash)

## Design Goals

1. **Intelligent Following**: LLM executes plan steps but validates and adapts
2. **Batch Checkpoints**: Pause every N tasks for human approval
3. **Blocker Handling**: Detect, report, and recover from blockers gracefully
4. **Adaptive Batching**: High-risk steps get isolated; low-risk can batch together
5. **Observable State**: Batch progress, blockers, approvals all visible in state

## Key Insight

The execution model is NOT a dumb script executor. It's an LLM that:

1. Reads detailed plan steps as guidance
2. Validates before executing (e.g., checks if npm test exists)
3. Tries fallback actions before declaring blockers
4. Stops and reports blockers instead of crashing
5. Pauses for review checkpoints between batches

**Blocker trigger**: Any situation where the agent would ask for human input to proceed.

## Plan Schema

The current `TaskStep`/`FileOperation` structure is too rigid. The new schema supports:

- Fallback commands when primary fails
- Exit code validation (primary) with optional output pattern (secondary)
- Risk levels for adaptive batching
- Explicit dependency graph
- Working directory per step
- TDD markers

```python
# amelia/core/state.py (additions)

class PlanStep(BaseModel):
    """A single step in an execution plan."""
    model_config = ConfigDict(frozen=True)

    id: str                           # Unique identifier for tracking
    description: str                  # Human-readable description
    action_type: Literal["code", "command", "validation", "manual"]

    # For code actions
    file_path: str | None = None
    code_change: str | None = None    # Exact code or diff

    # For command actions
    command: str | None = None
    cwd: str | None = None            # Working directory (relative to repo root)
    fallback_commands: tuple[str, ...] = ()     # Try these if primary fails

    # Validation (exit code is ALWAYS checked; these are additional)
    expect_exit_code: int = 0                   # Expected exit code (primary validation)
    expected_output_pattern: str | None = None  # Regex for stdout (secondary, stripped of ANSI)

    # For validation actions
    validation_command: str | None = None
    success_criteria: str | None = None

    # Execution hints
    risk_level: Literal["low", "medium", "high"] = "medium"
    estimated_minutes: int = 2
    requires_human_judgment: bool = False

    # Dependencies
    depends_on: tuple[str, ...] = ()  # Step IDs this depends on

    # TDD markers
    is_test_step: bool = False
    validates_step: str | None = None  # Step ID this validates


class ExecutionBatch(BaseModel):
    """A batch of steps to execute before checkpoint.

    Architect defines batches based on semantic grouping.
    System enforces size limits (max 5 low-risk, max 3 medium-risk).
    """
    model_config = ConfigDict(frozen=True)

    batch_number: int
    steps: tuple[PlanStep, ...]
    risk_summary: Literal["low", "medium", "high"]
    description: str = ""  # Optional: why these steps are grouped


class ExecutionPlan(BaseModel):
    """Complete plan with batched execution.

    Created by Architect, consumed by Developer.
    Batches are defined upfront for predictable checkpoints.
    """
    model_config = ConfigDict(frozen=True)

    goal: str
    batches: tuple[ExecutionBatch, ...]
    total_estimated_minutes: int
    tdd_approach: bool = True
```

### Validation Strategy

**Exit codes are primary.** The `expected_output_pattern` is optional and only used when:
- Exit code alone is insufficient (e.g., command exits 0 but output indicates failure)
- Pattern is applied to **stripped plain text** (ANSI codes removed)

```python
def validate_command_result(exit_code: int, stdout: str, step: PlanStep) -> bool:
    """Validate command result. Exit code is always checked first."""
    if exit_code != step.expect_exit_code:
        return False

    if step.expected_output_pattern:
        # Strip ANSI codes before matching
        clean_output = strip_ansi(stdout)
        if not re.search(step.expected_output_pattern, clean_output):
            return False

    return True
```

### Key Differences from Current TaskStep

| Current | New | Why |
|---------|-----|-----|
| No fallbacks | `fallback_commands` | Agent can try alternatives before blocking |
| No validation | `expect_exit_code` + optional `expected_output_pattern` | Exit codes primary; regex only when needed |
| No risk info | `risk_level` | Drives batch sizing and pre-validation depth |
| No working dir | `cwd` | Commands often need specific subdirectories |
| Implicit judgment | `requires_human_judgment` | Explicit blocker markers |
| Implicit deps | `depends_on` | Explicit dependency graph (enables cascade handling) |
| Flat list | Pre-batched | Architect creates semantic batches; system enforces limits |

## Batch Ownership (Hybrid Approach)

**Architect defines batches semantically.** The LLM groups steps that logically belong together (e.g., "setup db" + "run migration"). This preserves context for human reviewers.

**System enforces size limits.** To ensure predictable checkpoint frequency:

| Risk Level | Max Batch Size |
|------------|----------------|
| Low | 5 steps |
| Medium | 3 steps |
| High | 1 step (always isolated) |

If an Architect-defined batch exceeds limits, the system splits it with a warning:

```python
def validate_and_split_batches(plan: ExecutionPlan) -> ExecutionPlan:
    """Validate Architect batches and split if needed.

    Architect defines semantic groupings. System enforces size limits.
    """
    validated_batches = []
    warnings = []

    for batch in plan.batches:
        max_size = {"low": 5, "medium": 3, "high": 1}[batch.risk_summary]

        if len(batch.steps) <= max_size:
            validated_batches.append(batch)
        else:
            # Split oversized batch, preserving order
            warnings.append(f"Batch {batch.batch_number} exceeded {max_size} steps, splitting")
            for i in range(0, len(batch.steps), max_size):
                chunk = batch.steps[i:i + max_size]
                validated_batches.append(ExecutionBatch(
                    batch_number=len(validated_batches) + 1,
                    steps=chunk,
                    risk_summary=batch.risk_summary,
                    description=f"{batch.description} (part {i // max_size + 1})",
                ))

    return plan.model_copy(update={"batches": tuple(validated_batches)})
```

**Why hybrid?**
- Pure algorithm might split logical units (bad for human review)
- Pure LLM might create inconsistent batch sizes (bad for predictability)
- Hybrid gives semantic grouping with predictable checkpoints

## Blocker Detection & Handling

A blocker is triggered when the agent would need human input to proceed:

| Blocker Type | Trigger | Example |
|--------------|---------|---------|
| `command_failed` | Command fails and no fallback succeeds | `npm test` not found, tried `yarn test`, `pnpm test` |
| `validation_failed` | Code change doesn't pass validation | Tests fail after implementation |
| `needs_judgment` | Step marked `requires_human_judgment` | Security-sensitive change |
| `unexpected_state` | Pre-validation fails | File doesn't exist, dependency missing |
| `dependency_skipped` | A dependency was skipped/failed | Step B depends on Step A which was skipped |

```python
class BlockerReport(BaseModel):
    """Report when execution is blocked."""
    model_config = ConfigDict(frozen=True)

    step_id: str
    step_description: str
    blocker_type: Literal["command_failed", "validation_failed", "needs_judgment", "unexpected_state", "dependency_skipped"]
    error_message: str
    attempted_actions: tuple[str, ...]  # What the agent already tried
    suggested_resolutions: tuple[str, ...]  # Agent's suggestions for human (labeled as AI suggestions in UI)
```

### Cascading Skip Handling

When a step is skipped or fails, all dependent steps are automatically marked for skip:

```python
def get_cascade_skips(step_id: str, plan: ExecutionPlan, skip_reasons: dict[str, str]) -> dict[str, str]:
    """Find all steps that depend on a skipped/failed step.

    Returns dict of step_id -> skip reason.
    """
    skips = {step_id: skip_reasons.get(step_id, "skipped by user")}

    # Iterate until no new skips found (avoids recursion issues)
    changed = True
    while changed:
        changed = False
        for batch in plan.batches:
            for step in batch.steps:
                if step.id not in skips and any(dep in skips for dep in step.depends_on):
                    skips[step.id] = f"dependency {step.depends_on[0]} was skipped"
                    changed = True

    return skips
```

When executing, the Developer checks for cascade skips before each step:

```python
# In _execute_batch
for step in batch.steps:
    # Check if any dependency was skipped/failed
    skipped_deps = [dep for dep in step.depends_on if dep in state.skipped_step_ids]
    if skipped_deps:
        completed_steps.append(StepResult(
            step_id=step.id,
            status="skipped",
            error=f"Dependency {skipped_deps[0]} was skipped",
        ))
        continue
    # ... proceed with execution
```

### Blocker Resolution Flow

```
Developer executes batch
    │
    ├─[success]──► Batch Checkpoint (human reviews)
    │                   │
    │                   ├─[approved]──► Next Batch
    │                   └─[feedback]──► Developer adjusts, re-executes
    │
    └─[blocked]──► Blocker Report
                        │
                        ▼
                  Human Resolution
                        │
                        ├─[provides fix]──► Developer continues
                        ├─[skip step]──► Developer marks skipped + cascade skips
                        ├─[abort + keep changes]──► Workflow ends (default)
                        └─[abort + revert]──► Revert batch changes, workflow ends
```

## State Management

### New State Fields

```python
class DeveloperStatus(str, Enum):
    """Developer agent execution status."""
    EXECUTING = "executing"
    BATCH_COMPLETE = "batch_complete"    # Ready for checkpoint
    BLOCKED = "blocked"                  # Needs human help
    ALL_DONE = "all_done"                # All batches complete


class BatchApproval(BaseModel):
    """Record of human approval for a batch."""
    model_config = ConfigDict(frozen=True)

    batch_number: int
    approved: bool
    feedback: str | None = None
    approved_at: datetime


# Constants for output truncation
MAX_OUTPUT_LINES = 100
MAX_OUTPUT_CHARS = 4000


def truncate_output(output: str | None) -> str | None:
    """Truncate command output to prevent state bloat.

    Keeps first 50 lines + last 50 lines if output exceeds limit.
    """
    if not output:
        return output

    lines = output.split("\n")
    if len(lines) <= MAX_OUTPUT_LINES:
        truncated = output
    else:
        # Keep first 50 + last 50 lines
        first = lines[:50]
        last = lines[-50:]
        truncated = "\n".join(first + [f"\n... ({len(lines) - 100} lines truncated) ...\n"] + last)

    if len(truncated) > MAX_OUTPUT_CHARS:
        truncated = truncated[:MAX_OUTPUT_CHARS] + f"\n... (truncated at {MAX_OUTPUT_CHARS} chars)"

    return truncated


class StepResult(BaseModel):
    """Result of executing a single step."""
    model_config = ConfigDict(frozen=True)

    step_id: str
    status: Literal["completed", "skipped", "failed"]
    output: str | None = None           # Truncated to prevent state bloat
    error: str | None = None
    executed_command: str | None = None  # Actual command run (may differ from plan if fallback)
    duration_seconds: float = 0.0

    @field_validator("output", mode="before")
    @classmethod
    def truncate(cls, v: str | None) -> str | None:
        return truncate_output(v)


class BatchResult(BaseModel):
    """Result of executing a batch."""
    model_config = ConfigDict(frozen=True)

    batch_number: int
    status: Literal["complete", "blocked", "partial"]
    completed_steps: tuple[StepResult, ...]
    blocker: BlockerReport | None = None


class GitSnapshot(BaseModel):
    """Git state snapshot for potential revert."""
    model_config = ConfigDict(frozen=True)

    head_commit: str              # git rev-parse HEAD before batch
    dirty_files: tuple[str, ...]  # Files modified before batch started
    stash_ref: str | None = None  # If we stashed changes


# Extensions to ExecutionState (in amelia/core/state.py)
class ExecutionState(BaseModel):
    # ... existing fields from stateless-reducer-pattern.md ...

    # New execution plan (replaces task_dag for Developer)
    execution_plan: ExecutionPlan | None = None

    # Batch tracking
    current_batch_index: int = 0
    batch_results: Annotated[list[BatchResult], add] = Field(default_factory=list)

    # Developer status
    developer_status: DeveloperStatus = DeveloperStatus.EXECUTING

    # Blocker handling
    current_blocker: BlockerReport | None = None
    blocker_resolution: str | None = None  # Human's response

    # Approval tracking
    batch_approvals: Annotated[list[BatchApproval], add] = Field(default_factory=list)

    # Skip tracking (for cascade handling)
    skipped_step_ids: Annotated[set[str], set_union] = Field(default_factory=set)

    # Git state for revert capability
    git_snapshot_before_batch: GitSnapshot | None = None
```

## Orchestrator Integration

### Updated Graph (Hybrid Approval Flow)

Developer yields to orchestrator for batch checkpoints and blocker resolution:

```
                                    ┌─────────────────┐
                                    │                 │
                                    ▼                 │
Issue → PM → Architect → Plan Approval → Developer ───┼──→ Reviewer → Done
                              ▲            │          │
                              │            │          │
                              │            ▼          │
                              │    Batch Checkpoint ──┘
                              │            │
                              │            ▼
                              └─── Blocker Resolution
```

### Routing Logic

```python
def route_after_developer(state: ExecutionState) -> str:
    """Route based on Developer status."""
    if state.developer_status == DeveloperStatus.ALL_DONE:
        return "reviewer"
    elif state.developer_status == DeveloperStatus.BATCH_COMPLETE:
        return "batch_approval"
    elif state.developer_status == DeveloperStatus.BLOCKED:
        return "blocker_resolution"
    else:
        raise ValueError(f"Unexpected status: {state.developer_status}")


async def batch_approval_node(state: ExecutionState) -> dict:
    """Human reviews completed batch. Graph interrupts before this node."""
    # When resumed, approval will be in state
    last_batch = state.batch_results[-1] if state.batch_results else None

    if state.human_approved:
        return {
            "batch_approvals": [BatchApproval(
                batch_number=last_batch.batch_number if last_batch else 0,
                approved=True,
                approved_at=datetime.utcnow(),
            )],
            "developer_status": DeveloperStatus.EXECUTING,
            "human_approved": None,  # Reset for next checkpoint
        }
    else:
        # Human provided feedback - Developer will re-execute with adjustments
        return {
            "batch_approvals": [BatchApproval(
                batch_number=last_batch.batch_number if last_batch else 0,
                approved=False,
                feedback=state.blocker_resolution,  # Reuse field for feedback
                approved_at=datetime.utcnow(),
            )],
            "developer_status": DeveloperStatus.EXECUTING,
            "human_approved": None,
        }


async def blocker_resolution_node(state: ExecutionState) -> dict:
    """Human resolves blocker. Graph interrupts before this node."""
    # When resumed, resolution will be in blocker_resolution
    if state.blocker_resolution == "skip":
        # Mark step as skipped; Developer will handle cascade
        return {
            "current_blocker": None,
            "blocker_resolution": None,
            "developer_status": DeveloperStatus.EXECUTING,
            "skipped_step_ids": {state.current_blocker.step_id},
        }
    elif state.blocker_resolution == "abort":
        # Keep changes (default)
        return {
            "workflow_status": "failed",
        }
    elif state.blocker_resolution == "abort_revert":
        # Revert batch changes before aborting
        await revert_to_git_snapshot(state.git_snapshot_before_batch)
        return {
            "workflow_status": "failed",
            "git_snapshot_before_batch": None,
        }
    else:
        # Human provided fix instruction
        return {
            "current_blocker": None,
            "developer_status": DeveloperStatus.EXECUTING,
            # blocker_resolution retained for Developer to use
        }
```

## Git Revert Strategy

**No auto-commits.** Commits clutter history and the reviewer hasn't approved yet.

**Snapshot before each batch.** Record git state so we can offer revert on failure.

```python
async def take_git_snapshot() -> GitSnapshot:
    """Capture git state before batch execution."""
    head = await run_command("git rev-parse HEAD")
    status = await run_command("git status --porcelain")
    dirty_files = tuple(line[3:] for line in status.split("\n") if line)

    return GitSnapshot(
        head_commit=head.strip(),
        dirty_files=dirty_files,
        stash_ref=None,  # We don't stash; just track
    )


async def revert_to_git_snapshot(snapshot: GitSnapshot) -> None:
    """Revert to pre-batch state.

    IMPORTANT: This only reverts files changed during the batch.
    User's manual changes (if any) are preserved unless they overlap.
    """
    if not snapshot:
        return

    # Get files changed since snapshot
    diff_files = await run_command(f"git diff --name-only {snapshot.head_commit}")
    batch_changed_files = set(diff_files.strip().split("\n")) - set(snapshot.dirty_files)

    # Revert only batch-changed files
    if batch_changed_files:
        await run_command(f"git checkout {snapshot.head_commit} -- {' '.join(batch_changed_files)}")
```

### Revert Granularity

| Option | Behavior | When to use |
|--------|----------|-------------|
| Keep changes (default) | Workflow ends, file changes remain | Want to manually fix and retry |
| Revert batch | Undo files changed during current batch only | Batch was wrong direction |
| Revert all | Reset to state before execution started | Start over completely |

**Why no step-level revert?** Too complex. Steps often have interdependencies (step 2 modifies file created by step 1). Batch-level revert is the natural unit.

## Developer Execution Loop

The Developer becomes an **intelligent plan follower**:

```python
class Developer:
    """Developer agent - executes plans intelligently."""

    async def run(self, state: ExecutionState) -> dict:
        """Main execution - follows plan with judgment."""
        plan = state.execution_plan
        current_batch_idx = state.current_batch_index

        # All batches complete?
        if current_batch_idx >= len(plan.batches):
            return {"developer_status": DeveloperStatus.ALL_DONE}

        # Check if we're recovering from a blocker
        if state.blocker_resolution and state.blocker_resolution not in ("skip", "abort"):
            result = await self._recover_from_blocker(state)
        else:
            batch = plan.batches[current_batch_idx]
            result = await self._execute_batch(batch, state)

        if result.status == "blocked":
            return {
                "current_blocker": result.blocker,
                "developer_status": DeveloperStatus.BLOCKED,
                "batch_results": [result],
            }

        # Batch complete - checkpoint
        return {
            "batch_results": [result],
            "current_batch_index": current_batch_idx + 1,
            "developer_status": DeveloperStatus.BATCH_COMPLETE,
            "blocker_resolution": None,  # Clear any previous resolution
        }

    async def _execute_batch(self, batch: ExecutionBatch, state: ExecutionState) -> BatchResult:
        """Execute a batch with LLM judgment.

        Uses tiered pre-validation to balance cost vs safety:
        - Low-risk steps: filesystem checks only (no LLM)
        - High-risk steps: LLM semantic review before execution
        - On any failure: LLM tries to adapt before blocking
        """

        # 1. Take git snapshot for potential revert
        git_snapshot = await take_git_snapshot()

        # 2. Review batch before starting (only for medium/high risk batches)
        if batch.risk_summary in ("medium", "high"):
            review = await self._review_batch_before_execution(batch, state)
            if review.has_concerns:
                return BatchResult(
                    batch_number=batch.batch_number,
                    status="blocked",
                    completed_steps=(),
                    blocker=review.to_blocker(),
                )

        completed_steps = []
        for step in batch.steps:
            # Check cascade skips first
            skipped_deps = [dep for dep in step.depends_on if dep in state.skipped_step_ids]
            if skipped_deps:
                completed_steps.append(StepResult(
                    step_id=step.id,
                    status="skipped",
                    error=f"Dependency {skipped_deps[0]} was skipped",
                ))
                continue

            # 3. Tiered pre-validation based on risk
            validation = await self._pre_validate_step(step, state)
            if not validation.ok:
                # Only use LLM adaptation for high-risk or after simple checks fail
                if step.risk_level == "high":
                    adapted = await self._try_adapt_step_with_llm(step, validation.issue, state)
                else:
                    adapted = None  # Fail fast for low-risk steps

                if not adapted:
                    return BatchResult(
                        batch_number=batch.batch_number,
                        status="blocked",
                        completed_steps=tuple(completed_steps),
                        blocker=BlockerReport(
                            step_id=step.id,
                            step_description=step.description,
                            blocker_type="unexpected_state",
                            error_message=validation.issue,
                            attempted_actions=validation.attempted,
                            suggested_resolutions=validation.suggestions,
                        ),
                    )
                step = adapted

            # 4. Execute step with fallback handling
            result = await self._execute_step_with_fallbacks(step, state)

            if result.status == "failed":
                return BatchResult(
                    batch_number=batch.batch_number,
                    status="blocked",
                    completed_steps=tuple(completed_steps),
                    blocker=BlockerReport(
                        step_id=step.id,
                        step_description=step.description,
                        blocker_type="command_failed" if step.action_type == "command" else "validation_failed",
                        error_message=result.error or "Step failed",
                        attempted_actions=(result.executed_command,) if result.executed_command else (),
                        suggested_resolutions=(),
                    ),
                )

            completed_steps.append(result)

        return BatchResult(
            batch_number=batch.batch_number,
            status="complete",
            completed_steps=tuple(completed_steps),
            blocker=None,
        )

    async def _execute_step_with_fallbacks(self, step: PlanStep, state: ExecutionState) -> StepResult:
        """Execute step, trying fallbacks if primary fails."""
        if step.action_type == "command":
            commands_to_try = [step.command] + list(step.fallback_commands)

            for cmd in commands_to_try:
                result = await self._run_command(cmd, step.expected_output_pattern)
                if result.status == "completed":
                    return StepResult(
                        step_id=step.id,
                        status="completed",
                        output=result.output,
                        executed_command=cmd,
                        duration_seconds=result.duration,
                    )

            # All commands failed
            return StepResult(
                step_id=step.id,
                status="failed",
                error=f"All commands failed: {commands_to_try}",
                executed_command=commands_to_try[-1],
            )

        elif step.action_type == "code":
            # Apply code change, then run validation if specified
            await self._apply_code_change(step.file_path, step.code_change)

            if step.validation_command:
                result = await self._run_command(step.validation_command, step.success_criteria)
                if result.status != "completed":
                    return StepResult(
                        step_id=step.id,
                        status="failed",
                        error=f"Validation failed: {result.error}",
                    )

            return StepResult(step_id=step.id, status="completed")

        # ... handle other action types ...
```

## Architect Integration

Architect must produce the new `ExecutionPlan` format:

```python
class ArchitectContextStrategy(ContextStrategy):
    """Extended to request batched plans."""

    SYSTEM_PROMPT = """You are a software architect creating implementation plans.

Create detailed, batched execution plans following these rules:

## Step Granularity
- Each step should take 2-5 minutes
- Include exact code changes or exact commands
- Include expected output patterns for validation

## Risk Assessment
- Mark steps that could break the build as high risk
- Mark steps that need human judgment (security, business logic) explicitly
- Low risk: documentation, comments, simple refactors
- Medium risk: new functions, test changes
- High risk: configuration changes, auth changes, data migrations

## Batching
- Group related low-risk steps (up to 5)
- Group related medium-risk steps (up to 3)
- Isolate high-risk steps in their own batch
- Isolate steps requiring human judgment

## TDD Approach
- Write test steps before implementation steps
- Mark test steps with is_test_step: true
- Link implementation to its test with validates_step

## Fallbacks
- For commands, provide fallback alternatives (npm vs yarn vs pnpm)
- Exit codes are primary validation; use expected_output_pattern only when needed
"""
```

## Pre-Validation Tiering

To balance latency/cost vs safety, pre-validation depth varies by risk:

| Risk Level | Pre-Validation | LLM Calls |
|------------|----------------|-----------|
| Low | Filesystem checks only (file exists, command available) | 0 |
| Medium | Filesystem checks; LLM review only if batch review flagged concerns | 0-1 per batch |
| High | Full LLM semantic review before each step | 1 per step |

```python
async def _pre_validate_step(self, step: PlanStep, state: ExecutionState) -> ValidationResult:
    """Tiered pre-validation based on step risk.

    Low-risk: Quick filesystem checks only
    High-risk: Full LLM semantic validation
    """
    # Always do filesystem checks (fast, no LLM)
    fs_result = await self._filesystem_checks(step)
    if not fs_result.ok:
        return fs_result

    # For low-risk steps, filesystem checks are sufficient
    if step.risk_level == "low":
        return ValidationResult(ok=True)

    # For high-risk steps, also do LLM semantic validation
    if step.risk_level == "high":
        return await self._llm_semantic_validation(step, state)

    # Medium-risk: filesystem checks are usually enough
    # LLM validation happens at batch level, not step level
    return ValidationResult(ok=True)


async def _filesystem_checks(self, step: PlanStep) -> ValidationResult:
    """Fast filesystem checks without LLM."""
    if step.action_type == "code" and step.file_path:
        if not Path(step.file_path).exists():
            return ValidationResult(
                ok=False,
                issue=f"File does not exist: {step.file_path}",
                attempted=["checked file existence"],
                suggestions=["Create the file first", "Check the path"],
            )

    if step.action_type == "command" and step.command:
        cmd_name = step.command.split()[0]
        which_result = await run_command(f"which {cmd_name}")
        if which_result.exit_code != 0 and not step.fallback_commands:
            return ValidationResult(
                ok=False,
                issue=f"Command not found: {cmd_name}",
                attempted=[f"which {cmd_name}"],
                suggestions=["Install the tool", "Use a fallback command"],
            )

    return ValidationResult(ok=True)
```

**Why tiered?**
- Low-risk steps (docs, simple refactors) don't need LLM validation - fail fast
- High-risk steps (auth, config) benefit from LLM catching semantic issues
- Avoids the "2 LLM calls per step" latency problem from review feedback

## Trust Level Configuration

Profile includes `trust_level` to control checkpoint frequency:

```python
class TrustLevel(str, Enum):
    """How much autonomy the Developer gets."""
    PARANOID = "paranoid"      # Approve every step
    STANDARD = "standard"      # Approve batches (default)
    AUTONOMOUS = "autonomous"  # Auto-approve low/medium, stop only for high-risk or blockers


class Profile(BaseModel):
    # ... existing fields ...

    # Execution model settings
    trust_level: TrustLevel = TrustLevel.STANDARD
    batch_checkpoint_enabled: bool = True
    auto_approve_low_risk_batches: bool = False  # Only if trust_level == AUTONOMOUS
```

### Trust Level Behavior

| Level | Low-Risk Batch | Medium-Risk Batch | High-Risk Batch | Blocker |
|-------|----------------|-------------------|-----------------|---------|
| Paranoid | Checkpoint each step | Checkpoint each step | Checkpoint each step | Always stop |
| Standard | Checkpoint after batch | Checkpoint after batch | Checkpoint after batch | Always stop |
| Autonomous | Auto-approve | Auto-approve | Checkpoint | Always stop |

```python
def should_checkpoint(batch: ExecutionBatch, profile: Profile) -> bool:
    """Determine if we should pause for human approval."""
    if profile.trust_level == TrustLevel.PARANOID:
        return True  # Always checkpoint

    if profile.trust_level == TrustLevel.AUTONOMOUS:
        return batch.risk_summary == "high"  # Only high-risk

    # STANDARD: always checkpoint batches
    return True
```

## Migration Path

### Phase 1: Add Types (No Behavior Change)

1. Add new types to `amelia/core/state.py`:
   - `PlanStep`, `ExecutionBatch`, `ExecutionPlan`
   - `BlockerReport`, `StepResult`, `BatchResult`, `BatchApproval`
   - `DeveloperStatus` enum, `TrustLevel` enum
   - `GitSnapshot` for revert capability
   - `truncate_output()` helper
   - New fields on `ExecutionState` (including `skipped_step_ids`, `git_snapshot_before_batch`)

2. Add execution config to `Profile`:
   - `trust_level: TrustLevel = TrustLevel.STANDARD`
   - `batch_checkpoint_enabled: bool = True`

### Phase 2: Update Architect

1. Update `ArchitectContextStrategy` with new prompts (semantic batching, exit code validation)
2. Update output schema to `ExecutionPlan`
3. Add `validate_and_split_batches()` helper to enforce size limits

### Phase 3: Refactor Developer

1. Remove `_execute_structured` vs `_execute_agentic` split
2. Implement single `_execute_batch` method with tiered pre-validation
3. Add fallback handling with exit code validation
4. Add blocker detection, cascade skip handling
5. Add git snapshot/revert capability

### Phase 4: Update Orchestrator

1. Add `batch_approval_node` and `blocker_resolution_node`
2. Update routing with `route_after_developer` (including revert option)
3. Add `interrupt_before` for new approval nodes
4. Integrate `should_checkpoint()` based on trust level

### Phase 5: Dashboard Integration

1. Batch progress visualization
2. Blocker UI with resolution options (including "Revert batch")
3. Step-level execution timeline
4. Trust level selector in settings

## Files to Create/Modify

| File | Changes |
|------|---------|
| `amelia/core/state.py` | Add `PlanStep`, `ExecutionPlan`, `BlockerReport`, `GitSnapshot`, `truncate_output()`, state extensions |
| `amelia/core/types.py` | Add `DeveloperStatus`, `TrustLevel` enums |
| `amelia/core/config.py` | Add `trust_level` to `Profile` |
| `amelia/agents/architect.py` | Update to produce `ExecutionPlan`, add `validate_and_split_batches()` |
| `amelia/agents/developer.py` | Refactor execution model with tiered pre-validation, cascade skips, git snapshot |
| `amelia/core/orchestrator.py` | Add batch/blocker nodes, update routing, trust level integration |
| `amelia/tools/git_utils.py` | Add `take_git_snapshot()`, `revert_to_git_snapshot()` |
| `tests/unit/test_developer.py` | Test intelligent execution, cascade skips |
| `tests/unit/test_batch_execution.py` | New: batch checkpoint tests, revert tests |
| `tests/integration/test_blocker_recovery.py` | New: integration tests for blocker → human → resume flow |

## Success Criteria

- [ ] Developer validates steps before execution (doesn't blindly crash)
- [ ] Developer tries fallback commands before blocking
- [ ] Exit codes are primary validation; regex only when specified
- [ ] Batch checkpoints pause for human review (respects trust_level)
- [ ] Blockers report what was tried and suggest resolutions
- [ ] Cascade skips handled correctly (dependent steps auto-skipped)
- [ ] High-risk steps isolated in their own batches
- [ ] Git revert works for batch-level changes
- [ ] State tracks batch progress, blockers, approvals, skipped steps
- [ ] Output truncation prevents state bloat
- [ ] Existing fixed orchestration mode still works
- [ ] All existing tests pass

## Example Workflow

### Issue: "Add user logout endpoint"

**Architect produces:**

```yaml
goal: "Add user logout endpoint with session invalidation"
tdd_approach: true
total_estimated_minutes: 25
batches:
  - batch_number: 1
    risk_summary: low
    steps:
      - id: "1.1"
        description: "Write logout endpoint test"
        action_type: code
        file_path: tests/test_auth.py
        code_change: |
          def test_logout_invalidates_session():
              ...
        is_test_step: true
        risk_level: low

  - batch_number: 2
    risk_summary: medium
    steps:
      - id: "2.1"
        description: "Implement logout endpoint"
        action_type: code
        file_path: src/auth/routes.py
        code_change: |
          @router.post("/logout")
          async def logout(session: Session = Depends(get_session)):
              ...
        validates_step: null
        risk_level: medium
        depends_on: ["1.1"]

      - id: "2.2"
        description: "Run tests"
        action_type: command
        command: "pytest tests/test_auth.py -v"
        fallback_commands: ["python -m pytest tests/test_auth.py -v"]
        expected_output_pattern: "passed"
        risk_level: low
        depends_on: ["2.1"]
```

**Execution flow:**

1. Developer executes Batch 1 (test step)
2. → Batch Checkpoint: Human reviews test looks correct
3. Developer executes Batch 2 (implementation + validation)
4. → Batch Checkpoint: Human reviews implementation
5. → Reviewer: Full code review
6. → Done

**If `pytest` not found:**

1. Developer tries `pytest tests/test_auth.py -v` → fails
2. Developer tries `python -m pytest tests/test_auth.py -v` → success
3. Continues without blocking

**If tests fail:**

1. Developer detects validation failure
2. Reports blocker with:
   - What failed: "pytest returned non-zero"
   - What was tried: ["pytest tests/test_auth.py -v"]
   - Suggestions: ["Check test assertions", "Review implementation logic"]
3. Human provides fix or skips
4. Developer continues

## Resolved Design Questions

1. **Should Architect or Developer calculate batches?** → Hybrid: Architect defines semantic groups, system enforces size limits
2. **How to handle partial batch completion on resume?** → Track `skipped_step_ids` in state, skip on resume
3. **Should auto-approve be configurable per batch risk level?** → Yes, via `trust_level` in Profile
4. **Regex validation brittleness?** → Exit codes are primary; regex optional and applied to stripped text
5. **Pre-validation latency?** → Tiered: filesystem checks for low-risk, LLM only for high-risk
6. **Git dirty state on abort?** → Snapshot before batch; offer "Keep changes" (default) or "Revert batch"
7. **Cascading failures?** → Auto-skip steps whose dependencies were skipped/failed

8. **How to display batch progress in dashboard?** → Split view: compact `AgentProgressBar` + `BatchStepCanvas` with horizontal swimlanes
9. **Should we support editing pending batches mid-execution?** → Not in v1; user can abort and re-plan
10. **How to handle very long-running steps (>10 min)?** → User intervention via "Cancel" button; new `user_cancelled` blocker type (no automatic timeouts)

## Dashboard Batch Progress Design

### Layout Structure

Split view with compact agent progress bar and batch/step canvas:

```
┌─────────────────────────────────────────────────────────┐
│  AgentProgressBar (compact, ~50px)                      │
│  [PM ✓] → [Architect ✓] → [Developer ●] → [Reviewer]    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  BatchStepCanvas (main content, React Flow)             │
│                                                         │
│  ┌─ Batch 1 (low risk) ──────────────────────────────┐  │
│  │ [Step 1.1 ✓] → [Step 1.2 ✓]                       │  │
│  └───────────────────────────────────────────────────┘  │
│            ══════ ✓ Approved ══════                     │
│  ┌─ Batch 2 (medium risk) ───────────────────────────┐  │
│  │ [Step 2.1 ● 3:42] → [Step 2.2]      [Cancel]      │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Components

| Component | Purpose |
|-----------|---------|
| `AgentProgressBar` | New lightweight horizontal stepper showing agent stages |
| `BatchStepCanvas` | Refactored `WorkflowCanvas`, shows batches as horizontal swimlane rows |
| `BatchNode` | Container node for each batch, displays risk level and description |
| `StepNode` | Adapted from `WorkflowNode`, shows step status + elapsed time when running |
| `CheckpointMarker` | Visual separator between batches showing approval status |

### Rationale

- Compact agent bar provides context without consuming screen space
- Horizontal swimlanes maintain consistency with existing left-to-right flow
- Vertical scrolling handles many batches naturally
- Checkpoint boundaries are visually clear between batch rows
- Reuses existing `WorkflowNode` styling and status patterns

## Long-Running Step Cancellation

### User Intervention Model

No automatic timeouts. User monitors elapsed time and clicks "Cancel" if a step appears stuck.

**UI Elements:**
- Elapsed time displayed prominently on running step (e.g., "Running... 12:34")
- "Cancel" button visible when a step is actively executing
- `estimated_minutes` field remains informational only (not enforced)

### Cancel Button Flow

```
User clicks [Cancel]
    │
    ├─► Confirmation dialog: "Cancel this step? The running process will be terminated."
    │       [Cancel Step] [Keep Running]
    │
    └─► On confirm:
            1. Kill running process (SIGTERM, then SIGKILL after 5s)
            2. Create BlockerReport with blocker_type: "user_cancelled"
            3. Update developer_status to BLOCKED
            4. Standard blocker resolution UI appears
```

### New Blocker Type

```python
blocker_type: Literal[
    "command_failed",
    "validation_failed",
    "needs_judgment",
    "unexpected_state",
    "dependency_skipped",
    "user_cancelled"  # NEW: User clicked Cancel on running step
]
```

### New Step Status

```python
class StepResult(BaseModel):
    step_id: str
    status: Literal["completed", "skipped", "failed", "cancelled"]  # "cancelled" is NEW
    # ... existing fields ...
    cancelled_by_user: bool = False  # NEW: distinguishes user cancel from failure
```

### Resolution Options

Same as other blockers:
- Retry the step
- Skip step (cascades to dependents)
- Provide fix instruction
- Abort (keep changes)
- Abort (revert batch)
