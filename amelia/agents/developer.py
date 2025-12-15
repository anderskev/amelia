# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import asyncio
import os
import re
import shlex
import shutil
import time
from collections.abc import Coroutine
from pathlib import Path
from typing import Any, Literal, cast

import typer
from loguru import logger
from pydantic import BaseModel, ConfigDict

from amelia.core.constants import ToolName
from amelia.core.context import CompiledContext, ContextSection, ContextStrategy
from amelia.core.exceptions import AgenticExecutionError
from amelia.core.state import (
    AgentMessage,
    BatchResult,
    BlockerReport,
    BlockerType,
    ExecutionBatch,
    ExecutionPlan,
    ExecutionState,
    PlanStep,
    StepResult,
    Task,
)
from amelia.core.types import DeveloperStatus, StreamEmitter
from amelia.core.utils import strip_ansi
from amelia.drivers.base import DriverInterface
from amelia.drivers.cli.claude import convert_to_stream_event
from amelia.tools.git_utils import take_git_snapshot
from amelia.tools.shell_executor import run_shell_command, write_file


# Legacy status for execute_current_task (to be deprecated)
LegacyDeveloperStatus = Literal["completed", "failed", "in_progress"]
ExecutionMode = Literal["structured", "agentic"]


def validate_command_result(
    exit_code: int,
    stdout: str,
    step: PlanStep
) -> bool:
    """Validate command result. Exit code is always checked first.

    Args:
        exit_code: The exit code returned by the command.
        stdout: The stdout output from the command.
        step: The plan step containing validation criteria.

    Returns:
        True if all validations pass, False otherwise.
    """
    # Check exit code first - if it doesn't match expected, return False
    if exit_code != step.expect_exit_code:
        return False

    # If expected_output_pattern is specified, validate it against stdout
    if step.expected_output_pattern is not None:
        # Strip ANSI codes from stdout before matching
        cleaned_stdout = strip_ansi(stdout)

        # Use re.search to find pattern anywhere in output (not just at start)
        if not re.search(step.expected_output_pattern, cleaned_stdout):
            return False

    # All validations passed
    return True


def get_cascade_skips(
    step_id: str,
    plan: ExecutionPlan,
    skip_reasons: dict[str, str]
) -> dict[str, str]:
    """Find all steps that depend on a skipped/failed step.

    Uses iterative approach to find transitive dependencies.
    Returns dict mapping step_id -> reason for skip.

    Args:
        step_id: ID of the step that was originally skipped/failed.
        plan: Complete execution plan with all batches.
        skip_reasons: Dict mapping step_id -> reason (contains original failed/skipped step).

    Returns:
        Dict mapping step_id -> reason for cascade skip (excludes original step_id).
    """
    # Start with a copy of skip_reasons to track all skipped steps
    all_skipped = dict(skip_reasons)

    # Result will only contain newly skipped steps (not the original)
    result: dict[str, str] = {}

    # Keep iterating until no new skips are found
    found_new_skips = True
    while found_new_skips:
        found_new_skips = False

        # Check all steps in all batches
        for batch in plan.batches:
            for step in batch.steps:
                # Skip if this step is already marked as skipped
                if step.id in all_skipped:
                    continue

                # Check if any of this step's dependencies are skipped
                for dep_id in step.depends_on:
                    if dep_id in all_skipped:
                        # This step should be skipped due to dependency
                        reason = f"Depends on skipped step {dep_id}"
                        all_skipped[step.id] = reason
                        result[step.id] = reason
                        found_new_skips = True
                        break  # No need to check other dependencies

    return result


class ValidationResult(BaseModel):
    """Result of pre-validating a step.

    Attributes:
        ok: Whether validation passed.
        issue: Error message if validation failed, None otherwise.
        attempted: Tuple of attempted actions during validation.
        suggestions: Tuple of suggested fixes for the issue.
    """

    model_config = ConfigDict(frozen=True)

    ok: bool
    issue: str | None = None
    attempted: tuple[str, ...] = ()
    suggestions: tuple[str, ...] = ()


class DeveloperResponse(BaseModel):
    """Schema for Developer agent's task execution output.

    Attributes:
        status: Execution status (completed, failed, or in_progress).
        output: Human-readable description of what was accomplished.
        error: Error message if status is failed, None otherwise.
    """

    status: DeveloperStatus
    output: str
    error: str | None = None


class DeveloperContextStrategy(ContextStrategy):
    """Context compilation strategy for the Developer agent.

    Compiles minimal context for task execution, focusing only on the current task
    from the TaskDAG without issue context or other agents' history.
    """

    SYSTEM_PROMPT = """You are a senior developer executing tasks following TDD principles.
Run tests after each change. Follow the task steps exactly."""

    ALLOWED_SECTIONS = {"task", "files", "steps"}

    def compile(self, state: ExecutionState) -> CompiledContext:
        """Compile ExecutionState into minimal task execution context.

        Args:
            state: The current execution state.

        Returns:
            CompiledContext with task-specific sections.

        Raises:
            ValueError: If no current task is found.
        """
        task = self.get_current_task(state)
        if task is None:
            raise ValueError("No current task found in execution state")

        sections: list[ContextSection] = []

        # Task section (required)
        sections.append(
            ContextSection(
                name="task",
                content=task.description,
                source=f"task:{task.id}",
            )
        )

        # Files section (optional, when task has files)
        if task.files:
            files_lines = [f"- {file_op.operation}: `{file_op.path}`" for file_op in task.files]
            sections.append(
                ContextSection(
                    name="files",
                    content="\n".join(files_lines),
                    source=f"task:{task.id}:files",
                )
            )

        # Steps section (optional)
        if task.steps:
            steps_lines = []
            for i, step in enumerate(task.steps, 1):
                steps_lines.append(f"### Step {i}: {step.description}")
                if step.code:
                    steps_lines.append(f"```\n{step.code}\n```")
                if step.command:
                    steps_lines.append(f"Run: `{step.command}`")
                if step.expected_output:
                    steps_lines.append(f"Expected: {step.expected_output}")
                steps_lines.append("")  # Blank line between steps

            sections.append(
                ContextSection(
                    name="steps",
                    content="\n".join(steps_lines).rstrip(),
                    source=f"task:{task.id}:steps",
                )
            )

        # Validate sections before returning
        self.validate_sections(sections)

        return CompiledContext(
            system_prompt=self.SYSTEM_PROMPT,
            sections=sections,
        )


class Developer:
    """Agent responsible for executing development tasks following TDD principles.

    Attributes:
        driver: LLM driver interface for task execution and tool access.
        execution_mode: Execution mode (structured or agentic).
        context_strategy: Context compilation strategy class.
    """

    context_strategy: type[ContextStrategy] = DeveloperContextStrategy

    def __init__(
        self,
        driver: DriverInterface,
        execution_mode: ExecutionMode = "structured",
        stream_emitter: StreamEmitter | None = None,
    ):
        """Initialize the Developer agent.

        Args:
            driver: LLM driver interface for task execution and tool access.
            execution_mode: Execution mode. Defaults to "structured".
            stream_emitter: Optional callback for streaming events.
        """
        self.driver = driver
        self.execution_mode = execution_mode
        self._stream_emitter = stream_emitter

    async def _filesystem_checks(self, step: PlanStep) -> ValidationResult:
        """Fast filesystem checks without LLM.

        Checks:
        - For code actions: file exists (if modifying) or parent dir exists (if creating)
        - For command actions: command executable is available (shutil.which)
        - Working directory exists (if cwd specified)

        Args:
            step: The plan step to validate.

        Returns:
            ValidationResult with ok=True if all checks pass, or ok=False with issue details.
        """
        # Check working directory exists (applies to all action types)
        if step.cwd:
            cwd_path = Path(step.cwd)
            if not cwd_path.exists() or not cwd_path.is_dir():
                return ValidationResult(
                    ok=False,
                    issue=f"Working directory does not exist: {step.cwd}",
                )

        # Code action checks
        if step.action_type == "code" and step.file_path:
            file_path = Path(step.file_path)

            # If file exists, ok (modifying)
            if file_path.exists():
                return ValidationResult(ok=True)

            # If file doesn't exist, check parent directory exists (creating)
            parent_dir = file_path.parent
            if not parent_dir.exists():
                return ValidationResult(
                    ok=False,
                    issue=f"Parent directory does not exist for file: {step.file_path}",
                )

            return ValidationResult(ok=True)

        # Command action checks
        if step.action_type == "command" and step.command:
            # Extract executable name from command, skipping environment variables
            # Environment variables follow the pattern: KEY=VALUE
            tokens = shlex.split(step.command)
            executable = None
            for token in tokens:
                # Skip environment variable assignments (pattern: KEY=VALUE)
                if not re.match(r'^\w+=', token):
                    executable = token
                    break

            if executable is None:
                return ValidationResult(
                    ok=False,
                    issue="No executable found in command",
                )

            # Check if executable is available
            if not shutil.which(executable):
                return ValidationResult(
                    ok=False,
                    issue=f"Command not found: {executable}",
                )

            return ValidationResult(ok=True)

        # Validation and manual actions don't have specific filesystem checks
        # beyond cwd (which was already checked above)
        return ValidationResult(ok=True)

    async def _pre_validate_step(
        self,
        step: PlanStep,
        state: ExecutionState,
    ) -> ValidationResult:
        """Tiered pre-validation based on step risk.

        Logic:
        - Always run filesystem checks first
        - Low-risk: filesystem only (fast path)
        - Medium-risk: filesystem only (LLM at batch level, not step level)
        - High-risk: filesystem + LLM semantic validation

        Args:
            step: The plan step to validate.
            state: The current execution state.

        Returns:
            ValidationResult from filesystem checks, or from LLM validation for high-risk.
        """
        # Always run filesystem checks first
        fs_result = await self._filesystem_checks(step)

        # If filesystem checks fail, return immediately
        if not fs_result.ok:
            return fs_result

        # Low-risk and medium-risk: return filesystem result
        # (Medium-risk LLM validation happens at batch level, not step level)
        if step.risk_level in ("low", "medium"):
            return fs_result

        # High-risk: Add LLM semantic validation
        # TODO: High-risk LLM semantic validation
        # - Check if code change makes sense in context
        # - Verify command is safe to execute
        # - For now, just return filesystem check result
        return fs_result

    async def _execute_step_with_fallbacks(
        self,
        step: PlanStep,
        state: ExecutionState
    ) -> StepResult:
        """Execute step, trying fallbacks if primary fails.

        Args:
            step: The plan step to execute.
            state: The current execution state.

        Returns:
            StepResult with status "completed" or "failed".
        """
        start_time = time.time()

        try:
            if step.action_type == "code":
                # Execute code change (write to file)
                if not step.file_path or not step.code_change:
                    raise ValueError("Code action requires file_path and code_change")

                await write_file(step.file_path, step.code_change)
                output = f"Wrote code to {step.file_path}"

                # If validation command exists, run it and validate result
                if step.validation_command:
                    try:
                        validation_output = await run_shell_command(step.validation_command)
                        output += f"\nValidation: {validation_output}"
                        # For validation commands, we assume exit code 0 means success
                        # The run_shell_command will raise RuntimeError if command fails
                    except Exception as e:
                        duration = time.time() - start_time
                        return StepResult(
                            step_id=step.id,
                            status="failed",
                            output=output,
                            error=f"Validation failed: {str(e)}",
                            executed_command=step.validation_command,
                            duration_seconds=duration,
                        )

                duration = time.time() - start_time
                return StepResult(
                    step_id=step.id,
                    status="completed",
                    output=output,
                    error=None,
                    executed_command=None,
                    duration_seconds=duration,
                )

            elif step.action_type == "command":
                # Execute command, trying fallbacks if primary fails
                commands_to_try = [step.command] + list(step.fallback_commands)
                last_error = None

                for cmd in commands_to_try:
                    if not cmd:
                        continue

                    try:
                        output = await run_shell_command(cmd)
                        duration = time.time() - start_time
                        return StepResult(
                            step_id=step.id,
                            status="completed",
                            output=output,
                            error=None,
                            executed_command=cmd,
                            duration_seconds=duration,
                        )
                    except Exception as e:
                        last_error = str(e)
                        # Try next fallback
                        continue

                # All commands failed
                duration = time.time() - start_time
                return StepResult(
                    step_id=step.id,
                    status="failed",
                    output=None,
                    error=last_error,
                    executed_command=commands_to_try[-1] if commands_to_try else None,
                    duration_seconds=duration,
                )

            elif step.action_type == "validation":
                # Just run the validation command
                if not step.validation_command:
                    raise ValueError("Validation action requires validation_command")

                try:
                    output = await run_shell_command(step.validation_command)
                    duration = time.time() - start_time
                    return StepResult(
                        step_id=step.id,
                        status="completed",
                        output=output,
                        error=None,
                        executed_command=step.validation_command,
                        duration_seconds=duration,
                    )
                except Exception as e:
                    duration = time.time() - start_time
                    return StepResult(
                        step_id=step.id,
                        status="failed",
                        output=None,
                        error=str(e),
                        executed_command=step.validation_command,
                        duration_seconds=duration,
                    )

            else:
                # Manual or other action types
                duration = time.time() - start_time
                return StepResult(
                    step_id=step.id,
                    status="failed",
                    output=None,
                    error=f"Unsupported action type: {step.action_type}",
                    executed_command=None,
                    duration_seconds=duration,
                )

        except Exception as e:
            duration = time.time() - start_time
            return StepResult(
                step_id=step.id,
                status="failed",
                output=None,
                error=str(e),
                executed_command=None,
                duration_seconds=duration,
            )

    async def _execute_batch(
        self,
        batch: ExecutionBatch,
        state: ExecutionState,
    ) -> BatchResult:
        """Execute a batch with LLM judgment.

        Uses tiered pre-validation to balance cost vs safety:
        - Low-risk steps: filesystem checks only (no LLM)
        - High-risk steps: LLM semantic review before execution
        - On any failure: report blocker immediately

        Flow:
        1. Take git snapshot for potential rollback
        2. For each step:
           a. Check cascade skips (dependency on skipped step)
           b. Pre-validate step (filesystem + LLM for high-risk)
           c. Execute step with fallbacks
        3. Return BatchResult

        Args:
            batch: The execution batch containing steps to execute.
            state: Current execution state with skipped_step_ids and other context.

        Returns:
            BatchResult with status "complete" or "blocked".
        """
        # 1. Take git snapshot for potential rollback
        _git_snapshot = await take_git_snapshot()
        logger.debug(
            "Git snapshot taken before batch execution",
            batch_number=batch.batch_number,
            head_commit=_git_snapshot.head_commit,
        )

        completed_steps: list[StepResult] = []

        for step in batch.steps:
            # 2a. Check cascade skips - if any dependency was skipped, skip this step too
            skipped_deps = [
                dep for dep in step.depends_on if dep in state.skipped_step_ids
            ]
            if skipped_deps:
                logger.info(
                    "Step skipped due to dependency",
                    step_id=step.id,
                    skipped_dependency=skipped_deps[0],
                )
                completed_steps.append(
                    StepResult(
                        step_id=step.id,
                        status="skipped",
                        error=f"Dependency {skipped_deps[0]} was skipped",
                    )
                )
                continue

            # 2b. Pre-validate step based on risk level
            validation = await self._pre_validate_step(step, state)
            if not validation.ok:
                logger.warning(
                    "Step pre-validation failed",
                    step_id=step.id,
                    issue=validation.issue,
                )
                # Determine blocker type based on validation failure
                blocker_type: BlockerType = "validation_failed"
                if validation.issue and "not found" in validation.issue.lower():
                    blocker_type = "unexpected_state"

                return BatchResult(
                    batch_number=batch.batch_number,
                    status="blocked",
                    completed_steps=tuple(completed_steps),
                    blocker=BlockerReport(
                        step_id=step.id,
                        step_description=step.description,
                        blocker_type=blocker_type,
                        error_message=validation.issue or "Pre-validation failed",
                        attempted_actions=validation.attempted,
                        suggested_resolutions=validation.suggestions,
                    ),
                )

            # 2c. Execute step with fallback handling
            result = await self._execute_step_with_fallbacks(step, state)

            if result.status == "failed":
                logger.warning(
                    "Step execution failed",
                    step_id=step.id,
                    error=result.error,
                )
                # Determine blocker type based on action type
                blocker_type = (
                    "command_failed"
                    if step.action_type == "command"
                    else "validation_failed"
                )

                return BatchResult(
                    batch_number=batch.batch_number,
                    status="blocked",
                    completed_steps=tuple(completed_steps),
                    blocker=BlockerReport(
                        step_id=step.id,
                        step_description=step.description,
                        blocker_type=blocker_type,
                        error_message=result.error or "Step execution failed",
                        attempted_actions=(
                            (result.executed_command,) if result.executed_command else ()
                        ),
                        suggested_resolutions=(),
                    ),
                )

            completed_steps.append(result)
            logger.info(
                "Step completed successfully",
                step_id=step.id,
                duration_seconds=result.duration_seconds,
            )

        # All steps completed successfully
        logger.info(
            "Batch completed successfully",
            batch_number=batch.batch_number,
            steps_completed=len(completed_steps),
        )

        return BatchResult(
            batch_number=batch.batch_number,
            status="complete",
            completed_steps=tuple(completed_steps),
            blocker=None,
        )

    async def _recover_from_blocker(
        self,
        state: ExecutionState,
    ) -> BatchResult:
        """Continue execution after human resolves blocker.

        Called when human has provided a fix instruction (blocker_resolution).
        Resumes execution from the blocked step, preserving any already-completed
        steps from the current batch.

        Args:
            state: Current execution state with current_blocker and blocker_resolution.

        Returns:
            BatchResult with status "complete" or "blocked".

        Raises:
            ValueError: If no execution plan, current blocker, or batch result exists.
        """
        if not state.execution_plan:
            raise ValueError("No execution plan in state")
        if not state.current_blocker:
            raise ValueError("No current blocker in state")

        # Get current batch
        batch = state.execution_plan.batches[state.current_batch_index]

        # Get the blocked step ID
        blocked_step_id = state.current_blocker.step_id

        # Find previously completed steps from the partial batch result
        previously_completed: list[StepResult] = []
        if state.batch_results:
            last_result = state.batch_results[-1]
            if last_result.batch_number == batch.batch_number:
                previously_completed = list(last_result.completed_steps)

        # Take git snapshot (in case we need to rollback after recovery attempt)
        _git_snapshot = await take_git_snapshot()
        logger.debug(
            "Git snapshot taken before recovery",
            batch_number=batch.batch_number,
            blocked_step_id=blocked_step_id,
        )

        completed_steps: list[StepResult] = list(previously_completed)
        found_blocked_step = False

        for step in batch.steps:
            # Skip already completed steps
            if any(s.step_id == step.id for s in previously_completed):
                continue

            # Mark that we've found the blocked step (start executing from here)
            if step.id == blocked_step_id:
                found_blocked_step = True

            # Skip steps before the blocked step (shouldn't happen but safety check)
            if not found_blocked_step:
                continue

            # Check cascade skips
            skipped_deps = [
                dep for dep in step.depends_on if dep in state.skipped_step_ids
            ]
            if skipped_deps:
                logger.info(
                    "Step skipped during recovery due to dependency",
                    step_id=step.id,
                    skipped_dependency=skipped_deps[0],
                )
                completed_steps.append(
                    StepResult(
                        step_id=step.id,
                        status="skipped",
                        error=f"Dependency {skipped_deps[0]} was skipped",
                    )
                )
                continue

            # Pre-validate step
            validation = await self._pre_validate_step(step, state)
            if not validation.ok:
                logger.warning(
                    "Step pre-validation failed during recovery",
                    step_id=step.id,
                    issue=validation.issue,
                )
                blocker_type: BlockerType = "validation_failed"
                if validation.issue and "not found" in validation.issue.lower():
                    blocker_type = "unexpected_state"

                return BatchResult(
                    batch_number=batch.batch_number,
                    status="blocked",
                    completed_steps=tuple(completed_steps),
                    blocker=BlockerReport(
                        step_id=step.id,
                        step_description=step.description,
                        blocker_type=blocker_type,
                        error_message=validation.issue or "Pre-validation failed",
                        attempted_actions=validation.attempted,
                        suggested_resolutions=validation.suggestions,
                    ),
                )

            # Execute step
            result = await self._execute_step_with_fallbacks(step, state)

            if result.status == "failed":
                logger.warning(
                    "Step execution failed during recovery",
                    step_id=step.id,
                    error=result.error,
                )
                blocker_type = (
                    "command_failed"
                    if step.action_type == "command"
                    else "validation_failed"
                )

                return BatchResult(
                    batch_number=batch.batch_number,
                    status="blocked",
                    completed_steps=tuple(completed_steps),
                    blocker=BlockerReport(
                        step_id=step.id,
                        step_description=step.description,
                        blocker_type=blocker_type,
                        error_message=result.error or "Step execution failed",
                        attempted_actions=(
                            (result.executed_command,) if result.executed_command else ()
                        ),
                        suggested_resolutions=(),
                    ),
                )

            completed_steps.append(result)
            logger.info(
                "Step completed successfully during recovery",
                step_id=step.id,
            )

        # All remaining steps completed
        logger.info(
            "Recovery completed successfully",
            batch_number=batch.batch_number,
            steps_completed=len(completed_steps),
        )

        return BatchResult(
            batch_number=batch.batch_number,
            status="complete",
            completed_steps=tuple(completed_steps),
            blocker=None,
        )

    async def run(self, state: ExecutionState) -> dict[str, Any]:
        """Main execution - follows plan with judgment.

        This is the new intelligent execution method that replaces the
        execute_current_task method for ExecutionPlan-based workflows.

        Args:
            state: Full execution state with execution_plan, current_batch_index, etc.

        Returns:
            Dict with developer_status and related state updates:
            - ALL_DONE: All batches completed
            - BATCH_COMPLETE: Current batch finished, ready for checkpoint
            - BLOCKED: Execution blocked, needs human help

        Raises:
            ValueError: If no execution plan in state.
        """
        plan = state.execution_plan
        if not plan:
            raise ValueError("No execution plan in state")

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

    async def execute_current_task(
        self,
        state: ExecutionState,
        *,
        workflow_id: str,
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
        if not state.plan or not state.current_task_id:
            raise ValueError("State must have plan and current_task_id")

        task = state.plan.get_task(state.current_task_id)
        if not task:
            raise ValueError(f"Task not found: {state.current_task_id}")

        cwd = state.profile.working_dir or os.getcwd()

        if self.execution_mode == "agentic":
            return await self._execute_agentic(task, cwd, state, workflow_id=workflow_id)
        else:
            result = await self._execute_structured(task, state)
            # Ensure task_id is included for consistency with agentic path
            result["task_id"] = task.id
            return result

    async def _execute_agentic(
        self,
        task: Task,
        cwd: str,
        state: ExecutionState,
        *,
        workflow_id: str,
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
        # Use context strategy with full state (no longer creating fake state)
        strategy = self.context_strategy()
        context = strategy.compile(state)

        logger.debug(
            "Compiled context",
            agent="developer",
            sections=[s.name for s in context.sections],
            system_prompt_length=len(context.system_prompt) if context.system_prompt else 0
        )

        messages = strategy.to_messages(context)

        logger.info(f"Starting agentic execution for task {task.id}")

        async for event in self.driver.execute_agentic(messages, cwd, system_prompt=context.system_prompt):
            self._handle_stream_event(event, workflow_id)

            if event.type == "error":
                raise AgenticExecutionError(event.content or "Unknown error")

        return {"status": "completed", "task_id": task.id, "output": "Agentic execution completed"}

    def _handle_stream_event(self, event: Any, workflow_id: str) -> None:
        """Display streaming event to terminal and emit via callback.

        Args:
            event: Stream event to display.
            workflow_id: Current workflow ID.
        """
        # Terminal display (existing logic)
        if event.type == "tool_use":
            typer.secho(f"  -> {event.tool_name}", fg=typer.colors.CYAN)
            if event.tool_input:
                preview = str(event.tool_input)[:100]
                suffix = "..." if len(str(event.tool_input)) > 100 else ""
                typer.echo(f"    {preview}{suffix}")

        elif event.type == "result":
            typer.secho("  Done", fg=typer.colors.GREEN)

        elif event.type == "assistant" and event.content:
            typer.echo(f"  {event.content[:200]}")

        elif event.type == "error":
            typer.secho(f"  Error: {event.content}", fg=typer.colors.RED)

        # Emit via callback if configured
        if self._stream_emitter is not None:
            stream_event = convert_to_stream_event(event, "developer", workflow_id)
            if stream_event is not None:
                # Fire-and-forget: emit stream event without blocking
                emit_coro = cast(Coroutine[Any, Any, None], self._stream_emitter(stream_event))
                emit_task: asyncio.Task[None] = asyncio.create_task(emit_coro)

                def _log_emit_error(t: asyncio.Task[None]) -> None:
                    if (exc := t.exception()) is not None:
                        logger.exception("Stream emitter failed", exc_info=exc)

                emit_task.add_done_callback(_log_emit_error)

    async def _execute_structured(self, task: Task, state: ExecutionState) -> dict[str, Any]:
        """Execute task using structured step-by-step approach.

        Args:
            task: The task to execute.
            state: Full execution state (for future context usage).

        Returns:
            Dict with status and output.
        """
        try:
            if task.steps:
                logger.info(f"Developer executing {len(task.steps)} steps for task {task.id}")
                results = []
                for i, step in enumerate(task.steps, 1):
                    logger.info(f"Executing step {i}: {step.description}")
                    step_output = ""

                    if step.code:
                        target_file = None
                        if task.files:
                            for f in task.files:
                                if f.operation in ("create", "modify"):
                                    target_file = f.path
                                    break

                        if target_file:
                            logger.info(f"Writing code to {target_file}")
                            await self.driver.execute_tool(ToolName.WRITE_FILE, file_path=target_file, content=step.code)
                            step_output += f"Wrote to {target_file}. "
                        else:
                            logger.warning("Step has code but no target file could be determined from task.files.")

                    if step.command:
                        logger.info(f"Running command: {step.command}")
                        cmd_result = await self.driver.execute_tool(ToolName.RUN_SHELL_COMMAND, command=step.command)
                        step_output += f"Command output: {cmd_result}"

                    results.append(f"Step {i}: {step_output}")

                return {"status": "completed", "output": "\n".join(results)}

            task_desc_lower = task.description.lower().strip()

            if task_desc_lower.startswith("run shell command:"):
                prefix_len = len("run shell command:")
                command = task.description[prefix_len:].strip()
                logger.info(f"Developer executing shell command: {command}")
                result = await self.driver.execute_tool(ToolName.RUN_SHELL_COMMAND, command=command)
                return {"status": "completed", "output": result}

            elif task_desc_lower.startswith("write file:"):
                logger.info(f"Developer executing write file task: {task.description}")

                # Using original description for content extraction
                if " with " in task.description:
                    parts = task.description.split(" with ", 1)
                    path_part = parts[0]
                    content = parts[1]
                else:
                    path_part = task.description
                    content = ""
                
                file_path = path_part[len("write file:"):].strip()

                result = await self.driver.execute_tool(ToolName.WRITE_FILE, file_path=file_path, content=content)
                return {"status": "completed", "output": result}

            else:
                logger.info(f"Developer generating response for task: {task.description}")
                # Use context strategy for consistent message compilation
                strategy = self.context_strategy()
                context = strategy.compile(state)
                # Build messages: prepend system prompt if present, then user messages
                messages: list[AgentMessage] = []
                if context.system_prompt:
                    messages.append(AgentMessage(role="system", content=context.system_prompt))
                messages.extend(strategy.to_messages(context))
                llm_response = await self.driver.generate(messages=messages)
                return {"status": "completed", "output": llm_response}

        except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
            raise
        except Exception as e:
            logger.exception(
                "Developer task execution failed",
                error_type=type(e).__name__,
            )
            return {"status": "failed", "output": str(e), "error": str(e)}
