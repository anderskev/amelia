# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os
from datetime import UTC, date, datetime
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from amelia.core.context import CompiledContext, ContextSection, ContextStrategy
from amelia.core.state import (
    AgentMessage,
    ExecutionBatch,
    ExecutionPlan,
    ExecutionState,
    RiskLevel,
    Task,
    TaskDAG,
)
from amelia.core.types import Design, Issue, StreamEmitter, StreamEvent, StreamEventType
from amelia.drivers.base import DriverInterface


class TaskListResponse(BaseModel):
    """Schema for LLM-generated list of tasks.

    Attributes:
        tasks: List of actionable development tasks parsed from LLM output.
    """

    tasks: list[Task] = Field(description="A list of actionable development tasks.")


class PlanOutput(BaseModel):
    """Output from architect planning.

    Attributes:
        task_dag: The generated task dependency graph.
        markdown_path: Path to the saved markdown plan file.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    task_dag: TaskDAG
    markdown_path: Path


class ExecutionPlanOutput(BaseModel):
    """Structured output for execution plan generation.

    Attributes:
        plan: The generated execution plan with batched steps.
        reasoning: Explanation of batching decisions and approach.
    """

    plan: ExecutionPlan
    reasoning: str


def _slugify(text: str) -> str:
    """Convert text to URL-friendly slug.

    Args:
        text: Input text to convert.

    Returns:
        Lowercase, hyphenated string truncated to 50 characters.
    """
    return text.lower().replace(" ", "-").replace("_", "-")[:50]


class ArchitectContextStrategy(ContextStrategy):
    """Context compilation strategy for the Architect agent.

    Compiles minimal context for planning by including issue information
    and optional design context. Excludes developer history and review history
    to keep the context focused on planning.
    """

    SYSTEM_PROMPT = """You are a senior software architect creating implementation plans.
You analyze issues and produce structured task DAGs with clear dependencies."""

    ALLOWED_SECTIONS = {"issue", "design", "codebase"}

    def get_task_generation_system_prompt(self) -> str:
        """Get the detailed system prompt for task DAG generation.

        This prompt is used specifically when generating the structured task DAG
        from the compiled context. It includes detailed TDD instructions and
        task structure requirements.

        Returns:
            Detailed system prompt string for task generation.
        """
        return """You are an expert software architect creating implementation plans.

Your role is to break down the given context into a sequence of actionable development tasks.
Each task MUST follow TDD (Test-Driven Development) principles.

For each task, provide:
- id: Unique identifier (e.g., "1", "2", "3")
- description: Clear, concise description of what to build
- dependencies: List of task IDs this task depends on
- files: List of FileOperation objects with:
  - operation: "create", "modify", or "test"
  - path: Exact file path (e.g., "src/auth/middleware.py")
  - line_range: Optional, for modify operations (e.g., "10-25")
- steps: List of TaskStep objects following TDD:
  1. Write the failing test (include actual code)
  2. Run test to verify it fails (include command and expected output)
  3. Write minimal implementation (include actual code)
  4. Run test to verify it passes (include command and expected output)
  5. Commit (include commit message)
- commit_message: Conventional commit message (e.g., "feat: add auth middleware")

CRITICAL - Shell command restrictions:
- Each command must be a SINGLE command - NO command chaining
- NEVER use: && || ; | > >> < ` $( ${ or newlines in commands
- WRONG: "cd src && npm test" or "npm install && npm run build"
- CORRECT: Create separate steps for each command
- If a command needs to run in a specific directory, use the full path or create separate cd step

Each step should be 2-5 minutes of work. Include complete code, not placeholders."""

    def get_task_generation_user_prompt(self) -> str:
        """Get the user prompt for task DAG generation.

        This prompt is appended to the context to instruct the LLM to generate
        the task DAG with specific formatting requirements.

        Returns:
            User prompt string for task generation.
        """
        return """Create a detailed implementation plan with bite-sized TDD tasks.
Ensure exact file paths, complete code in steps, and single-command shell instructions (no && or chaining)."""

    def get_execution_plan_system_prompt(self) -> str:
        """Get system prompt for ExecutionPlan generation.

        This prompt provides comprehensive guidance for generating ExecutionPlan objects
        with batched execution, risk assessment, and TDD approach.

        Returns:
            Detailed system prompt string for ExecutionPlan generation.
        """
        return """You are an expert software architect creating structured execution plans.

Your role is to break down development work into batched, executable steps with clear risk assessment.

# Step Granularity
- Each PlanStep should be 2-5 minutes of work
- Break larger operations into smaller, verifiable steps
- Include explicit validation steps after risky operations

# Risk Assessment
Assign risk_level to each step based on these criteria:

- **low**: File writes, read operations, simple commands, fully reversible actions
  Examples: writing tests, running linters, reading files, creating backups

- **medium**: Database operations, configuration changes, network calls, partially reversible
  Examples: schema migrations, config updates, dependency installations

- **high**: Destructive operations, production deploys, irreversible actions
  Examples: deleting data, production pushes, dropping tables, force operations

# Batching Rules
Group semantically related steps into ExecutionBatch objects:

- **Max batch sizes**:
  - low risk: 5 steps maximum
  - medium risk: 3 steps maximum
  - high risk: 1 step only (immediate checkpoint)

- Each batch should represent a meaningful checkpoint
- Group by feature/component, not arbitrarily
- Batches execute atomically - plan accordingly

# TDD Approach
When tdd_approach=True, follow this pattern for each feature:

1. Write the failing test (action_type="code", is_test_step=True)
2. Run test to verify it fails (action_type="command", validates_step=<test_step_id>)
3. Write minimal implementation (action_type="code")
4. Run test to verify it passes (action_type="command", validates_step=<impl_step_id>)
5. Commit changes (action_type="command")

Mark test steps with is_test_step=True and link validation steps using validates_step.

# Fallback Commands
For commands that commonly fail, provide alternatives in fallback_commands:

- Package managers: try alternative registries or mirrors
- Build tools: try with/without cache, different flags
- Test runners: try with verbose output, specific test files

Examples:
- Primary: "npm install", Fallback: ("npm install --legacy-peer-deps", "yarn install")
- Primary: "pytest", Fallback: ("pytest -v", "python -m pytest")

# Command Validation
- Set expect_exit_code (default 0)
- Optionally set expected_output_pattern for stdout regex (ANSI codes stripped)
- Use validation_command for complex success checks

# Dependencies
- Use depends_on to specify step IDs that must complete first
- Dependencies must form a valid DAG (no cycles)
- System will skip dependent steps if dependencies fail

Generate complete ExecutionPlan objects with properly batched steps following these guidelines."""

    def get_execution_plan_user_prompt(self) -> str:
        """Get user prompt for ExecutionPlan generation.

        This prompt instructs the LLM to generate an ExecutionPlan with the
        proper structure and batching.

        Returns:
            User prompt string for ExecutionPlan generation.
        """
        return """Create a complete ExecutionPlan with batched steps.

Follow TDD approach, assess risk levels accurately, batch steps appropriately (max 5/3/1 by risk), and provide fallback commands for failure-prone operations.

Ensure each step is 2-5 minutes, includes proper dependencies, and validation steps are linked to what they validate."""

    def _format_design_section(self, design: Design) -> str:
        """Format Design into structured markdown for context.

        Args:
            design: The design to format.

        Returns:
            Formatted markdown string with design fields.
        """
        parts = []

        parts.append(f"## Goal\n\n{design.goal}")
        parts.append(f"## Architecture\n\n{design.architecture}")

        if design.tech_stack:
            tech_list = "\n".join(f"- {tech}" for tech in design.tech_stack)
            parts.append(f"## Tech Stack\n\n{tech_list}")

        if design.components:
            comp_list = "\n".join(f"- {comp}" for comp in design.components)
            parts.append(f"## Components\n\n{comp_list}")

        if design.data_flow:
            parts.append(f"## Data Flow\n\n{design.data_flow}")

        if design.error_handling:
            parts.append(f"## Error Handling\n\n{design.error_handling}")

        if design.testing_strategy:
            parts.append(f"## Testing Strategy\n\n{design.testing_strategy}")

        if design.conventions:
            parts.append(f"## Conventions\n\n{design.conventions}")

        if design.relevant_files:
            files_list = "\n".join(f"- `{f}`" for f in design.relevant_files)
            parts.append(f"## Relevant Files\n\n{files_list}")

        return "\n\n".join(parts)

    def _scan_codebase(self, working_dir: str, max_files: int = 500) -> str:
        """Scan the codebase directory and return a file tree structure.

        Args:
            working_dir: Path to the working directory to scan.
            max_files: Maximum number of files to include (default 500).

        Returns:
            Formatted string with file tree structure.
        """
        # Common directories and files to ignore
        ignore_dirs = {
            ".git", ".svn", ".hg",
            "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
            "node_modules", ".venv", "venv", "env",
            "dist", "build", ".next", ".nuxt",
            "coverage", ".coverage", "htmlcov",
            ".idea", ".vscode",
            "eggs", "*.egg-info",
        }
        ignore_files = {".DS_Store", "Thumbs.db", ".gitignore"}

        files: list[str] = []
        root_path = Path(working_dir)

        try:
            for dirpath, dirnames, filenames in os.walk(root_path):
                # Filter out ignored directories (modifies dirnames in-place)
                dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.endswith(".egg-info")]

                rel_dir = Path(dirpath).relative_to(root_path)

                for filename in filenames:
                    if filename in ignore_files:
                        continue
                    if len(files) >= max_files:
                        break

                    rel_path = rel_dir / filename if str(rel_dir) != "." else Path(filename)
                    files.append(str(rel_path))

                if len(files) >= max_files:
                    break
        except OSError as e:
            logger.warning(f"Error scanning codebase: {e}")

        # Sort files for consistent output
        files.sort()

        if not files:
            return "No files found in working directory."

        # Format as a simple file list
        file_list = "\n".join(f"- {f}" for f in files)
        header = f"## File Structure ({len(files)} files)\n\n"

        if len(files) >= max_files:
            header += f"(Truncated to first {max_files} files)\n\n"

        return header + file_list

    def compile(self, state: ExecutionState) -> CompiledContext:
        """Compile ExecutionState into context for planning.

        Args:
            state: The current execution state.

        Returns:
            CompiledContext with system prompt and relevant sections.

        Raises:
            ValueError: If required sections are missing.
        """
        sections: list[ContextSection] = []

        # Issue section (required)
        issue_summary = self.get_issue_summary(state)
        if not issue_summary:
            raise ValueError("Issue context is required for planning")

        sections.append(
            ContextSection(
                name="issue",
                content=issue_summary,
                source="state.issue",
            )
        )

        # Design section (optional)
        if state.design:
            design_content = self._format_design_section(state.design)
            sections.append(
                ContextSection(
                    name="design",
                    content=design_content,
                    source="state.design",
                )
            )

        # Codebase section (optional - when working_dir is set)
        if state.profile.working_dir:
            codebase_content = self._scan_codebase(state.profile.working_dir)
            sections.append(
                ContextSection(
                    name="codebase",
                    content=codebase_content,
                    source="state.profile.working_dir",
                )
            )

        # Validate all sections before returning
        self.validate_sections(sections)

        return CompiledContext(
            system_prompt=self.SYSTEM_PROMPT,
            sections=sections,
        )


class Architect:
    """Agent responsible for creating implementation plans from issues and designs.

    Attributes:
        driver: LLM driver interface for generating plans.
        context_strategy: Strategy for compiling context from ExecutionState.
    """

    context_strategy: type[ArchitectContextStrategy] = ArchitectContextStrategy

    def __init__(
        self,
        driver: DriverInterface,
        stream_emitter: StreamEmitter | None = None,
    ):
        """Initialize the Architect agent.

        Args:
            driver: LLM driver interface for generating plans.
            stream_emitter: Optional callback for streaming events.
        """
        self.driver = driver
        self._stream_emitter = stream_emitter

    async def plan(
        self,
        state: ExecutionState,
        output_dir: str | None = None,
        *,
        workflow_id: str,
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
        if not state.issue:
            raise ValueError("Cannot generate plan: no issue in ExecutionState")

        # Use profile's output directory if not specified
        if output_dir is None:
            output_dir = state.profile.plan_output_dir

        # Resolve relative paths to working_dir (not server CWD)
        output_path = Path(output_dir)
        if not output_path.is_absolute() and state.profile.working_dir:
            output_dir = str(Path(state.profile.working_dir) / output_path)

        # Compile context using strategy
        strategy = self.context_strategy()
        compiled_context = strategy.compile(state)

        # Calculate system prompt length for logging
        prompt_length = (
            len(compiled_context.system_prompt)
            if compiled_context.system_prompt
            else 0
        )
        logger.debug(
            "Compiled context",
            agent="architect",
            sections=[s.name for s in compiled_context.sections],
            system_prompt_length=prompt_length
        )

        # Generate task DAG using compiled context
        task_dag = await self._generate_task_dag(compiled_context, state.issue, strategy)

        # Emit completion event
        if self._stream_emitter is not None:
            event = StreamEvent(
                type=StreamEventType.AGENT_OUTPUT,
                content=f"Generated plan with {len(task_dag.tasks)} tasks",
                timestamp=datetime.now(UTC),
                agent="architect",
                workflow_id=workflow_id,
            )
            await self._stream_emitter(event)

        # Save markdown
        markdown_path = self._save_markdown(task_dag, state.issue, state.design, output_dir)

        return PlanOutput(task_dag=task_dag, markdown_path=markdown_path)

    async def generate_execution_plan(
        self,
        issue: Issue,
        state: ExecutionState,
    ) -> ExecutionPlan:
        """Generate batched execution plan for an issue.

        Uses the new ExecutionPlan format with batched steps, risk assessment,
        and TDD approach. Validates and splits batches to enforce size limits.

        Args:
            issue: The issue to generate a plan for.
            state: The current execution state containing context.

        Returns:
            Validated ExecutionPlan with properly sized batches.
        """
        # Compile context using strategy
        strategy = self.context_strategy()
        compiled_context = strategy.compile(state)

        # Get execution plan prompts from strategy
        system_prompt = strategy.get_execution_plan_system_prompt()
        user_prompt = strategy.get_execution_plan_user_prompt()

        # Convert compiled context to messages
        base_messages = strategy.to_messages(compiled_context)

        # Prepend execution plan system prompt and append user prompt
        messages = [
            AgentMessage(role="system", content=system_prompt),
            *base_messages,
            AgentMessage(role="user", content=user_prompt),
        ]

        # Call driver with ExecutionPlanOutput schema
        response = await self.driver.generate(messages=messages, schema=ExecutionPlanOutput)

        # Log reasoning for audit trail
        logger.info(
            "Execution plan generated",
            agent="architect",
            reasoning=response.reasoning,
            batch_count=len(response.plan.batches),
        )

        # Validate and split batches to enforce risk limits
        validated_plan, warnings = validate_and_split_batches(response.plan)

        # Log any warnings from batch validation
        for warning in warnings:
            logger.warning(warning, agent="architect")

        return validated_plan

    async def _generate_task_dag(
        self,
        compiled_context: CompiledContext,
        issue: Issue,
        strategy: ArchitectContextStrategy,
    ) -> TaskDAG:
        """Generate TaskDAG using LLM.

        Args:
            compiled_context: Compiled context from the strategy.
            issue: Original issue being planned.
            strategy: The context strategy instance for prompt generation.

        Returns:
            TaskDAG containing structured tasks with TDD steps.
        """
        task_system_prompt = strategy.get_task_generation_system_prompt()
        task_user_prompt = strategy.get_task_generation_user_prompt()

        # Convert compiled context to messages (user messages only)
        base_messages = strategy.to_messages(compiled_context)

        # Prepend task-specific system prompt and append user prompt
        messages = [
            AgentMessage(role="system", content=task_system_prompt),
            *base_messages,
            AgentMessage(role="user", content=task_user_prompt),
        ]

        response = await self.driver.generate(messages=messages, schema=TaskListResponse)

        return TaskDAG(tasks=response.tasks, original_issue=issue.id)

    def _save_markdown(
        self,
        task_dag: TaskDAG,
        issue: Issue,
        design: Design | None,
        output_dir: str
    ) -> Path:
        """Save plan as markdown file.

        Args:
            task_dag: Structured task DAG to render.
            issue: Original issue being planned.
            design: Optional design context.
            output_dir: Directory path for saving the markdown file.

        Returns:
            Path to the saved markdown file.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        title = design.title if design else issue.title
        filename = f"{date.today().isoformat()}-{_slugify(title)}.md"
        file_path = output_path / filename

        md_content = self._render_markdown(task_dag, issue, design)
        file_path.write_text(md_content)

        return file_path

    def _render_markdown(
        self,
        task_dag: TaskDAG,
        issue: Issue,
        design: Design | None
    ) -> str:
        """Render TaskDAG as markdown following writing-plans format.

        Args:
            task_dag: Structured task DAG to render.
            issue: Original issue being planned.
            design: Optional design context.

        Returns:
            Markdown-formatted string representation of the plan.
        """
        title = design.title if design else issue.title
        goal = design.goal if design else issue.description
        architecture = design.architecture if design else "See task descriptions below."
        tech_stack = ", ".join(design.tech_stack) if design else "See implementation details."

        # Build the markdown header with Claude instructions
        claude_instruction = (
            "> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans "
            "to implement this plan task-by-task."
        )

        lines = [
            f"# {title} Implementation Plan",
            "",
            claude_instruction,
            "",
            f"**Goal:** {goal}",
            "",
            f"**Architecture:** {architecture}",
            "",
            f"**Tech Stack:** {tech_stack}",
            "",
            "---",
            "",
        ]

        for i, task in enumerate(task_dag.tasks, 1):
            lines.append(f"### Task {i}: {task.description}")
            lines.append("")

            if task.files:
                lines.append("**Files:**")
                for f in task.files:
                    if f.line_range:
                        lines.append(f"- {f.operation.capitalize()}: `{f.path}:{f.line_range}`")
                    else:
                        lines.append(f"- {f.operation.capitalize()}: `{f.path}`")
                lines.append("")

            for j, step in enumerate(task.steps, 1):
                lines.append(f"**Step {j}: {step.description}**")
                lines.append("")
                if step.code:
                    lines.append("```python")
                    lines.append(step.code)
                    lines.append("```")
                    lines.append("")
                if step.command:
                    lines.append(f"Run: `{step.command}`")
                if step.expected_output:
                    lines.append(f"Expected: {step.expected_output}")
                lines.append("")

            if task.commit_message:
                lines.append("**Commit:**")
                lines.append("```bash")
                if task.files:
                    file_paths = " ".join(f.path for f in task.files)
                    lines.append(f"git add {file_paths}")
                lines.append(f'git commit -m "{task.commit_message}"')
                lines.append("```")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)


def validate_and_split_batches(plan: ExecutionPlan) -> tuple[ExecutionPlan, list[str]]:
    """Validate Architect batches and split if needed.

    Enforces maximum batch sizes based on risk level:
    - Low risk: max 5 steps
    - Medium risk: max 3 steps
    - High risk: max 1 step (always isolated)

    Args:
        plan: The execution plan to validate.

    Returns:
        Tuple of (validated_plan, warnings).
        - validated_plan: Plan with batches split if needed, batch numbers renumbered.
        - warnings: List of warning messages for batches that were split.
    """
    # Risk level limits
    RISK_LIMITS: dict[RiskLevel, int] = {
        "low": 5,
        "medium": 3,
        "high": 1,
    }

    warnings: list[str] = []
    new_batches: list[ExecutionBatch] = []

    for batch in plan.batches:
        # Get the maximum allowed size for this batch's risk level
        max_size = RISK_LIMITS[batch.risk_summary]

        # If batch is within limits, keep it as-is
        if len(batch.steps) <= max_size:
            new_batches.append(batch)
            continue

        # Batch needs splitting
        warnings.append(
            f"Batch {batch.batch_number} exceeded size limit for {batch.risk_summary} risk "
            f"({len(batch.steps)} steps > {max_size} max). Split into multiple batches."
        )

        # Split the batch into chunks
        steps_list = list(batch.steps)
        for i in range(0, len(steps_list), max_size):
            chunk = steps_list[i:i + max_size]

            # Determine the risk summary for this chunk
            # If any step is high-risk, the chunk is high-risk
            # Otherwise, use the highest risk level in the chunk
            chunk_risks = {step.risk_level for step in chunk}
            chunk_risk: RiskLevel
            if "high" in chunk_risks:
                chunk_risk = "high"
            elif "medium" in chunk_risks:
                chunk_risk = "medium"
            else:
                chunk_risk = "low"

            # Create a new batch for this chunk
            new_batch = ExecutionBatch(
                batch_number=0,  # Will be renumbered later
                steps=tuple(chunk),
                risk_summary=chunk_risk,
                description=batch.description,
            )
            new_batches.append(new_batch)

    # Renumber all batches sequentially
    renumbered_batches = []
    for i, batch in enumerate(new_batches, start=1):
        renumbered_batch = ExecutionBatch(
            batch_number=i,
            steps=batch.steps,
            risk_summary=batch.risk_summary,
            description=batch.description,
        )
        renumbered_batches.append(renumbered_batch)

    # Create the validated plan
    validated_plan = ExecutionPlan(
        goal=plan.goal,
        batches=tuple(renumbered_batches),
        total_estimated_minutes=plan.total_estimated_minutes,
        tdd_approach=plan.tdd_approach,
    )

    return validated_plan, warnings
