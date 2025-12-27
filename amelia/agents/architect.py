# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Architect agent for analyzing issues and generating goals/strategies.

This module provides the Architect agent that analyzes issues and produces
high-level goals and strategies for agentic execution, rather than detailed
step-by-step execution plans.
"""
import os
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, ConfigDict

from amelia.core.context import CompiledContext, ContextSection, ContextStrategy
from amelia.core.state import AgentMessage, ExecutionState
from amelia.core.types import Design, Issue, Profile, StreamEmitter, StreamEvent, StreamEventType
from amelia.drivers.base import DriverInterface


class ArchitectOutput(BaseModel):
    """Output from Architect analysis.

    Attributes:
        goal: Clear description of what needs to be done.
        strategy: High-level approach (not step-by-step).
        key_files: Files likely to be modified.
        risks: Potential risks to watch for.
    """

    model_config = ConfigDict(frozen=True)

    goal: str
    strategy: str
    key_files: list[str] = []
    risks: list[str] = []


class ArchitectContextStrategy(ContextStrategy):
    """Context compilation strategy for the Architect agent.

    Compiles minimal context for analysis by including issue information
    and optional design context. Focuses on understanding the task rather
    than generating detailed plans.
    """

    SYSTEM_PROMPT = """You are a senior software architect analyzing development tasks.
Your role is to understand issues and produce clear goals and strategies for implementation.

Focus on:
- Understanding what needs to be accomplished
- Identifying the high-level approach
- Noting key files that will likely need changes
- Highlighting potential risks or considerations

Do NOT produce step-by-step plans - the Developer agent will determine specific actions."""

    ALLOWED_SECTIONS = {"issue", "design", "codebase"}

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

    def compile(self, state: ExecutionState, profile: Profile) -> CompiledContext:
        """Compile ExecutionState into context for analysis.

        Args:
            state: The current execution state.
            profile: The profile containing working directory settings.

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
        if profile.working_dir:
            codebase_content = self._scan_codebase(profile.working_dir)
            sections.append(
                ContextSection(
                    name="codebase",
                    content=codebase_content,
                    source="profile.working_dir",
                )
            )

        # Validate all sections before returning
        self.validate_sections(sections)

        return CompiledContext(
            system_prompt=self.SYSTEM_PROMPT,
            sections=sections,
        )


class Architect:
    """Agent responsible for analyzing issues and generating goals/strategies.

    Replaces detailed execution plan generation with high-level goal and
    strategy analysis for agentic execution.

    Attributes:
        driver: LLM driver interface for analysis.
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
            driver: LLM driver interface for analysis.
            stream_emitter: Optional callback for streaming events.
        """
        self.driver = driver
        self._stream_emitter = stream_emitter

    async def analyze(
        self,
        state: ExecutionState,
        profile: Profile,
        *,
        workflow_id: str,
    ) -> ArchitectOutput:
        """Analyze an issue and generate goal/strategy.

        Creates an ArchitectOutput with high-level goal and strategy
        for the Developer agent to execute agentically.

        Args:
            state: The execution state containing the issue and optional design.
            profile: The profile containing working directory settings.
            workflow_id: Workflow ID for stream events (required).

        Returns:
            ArchitectOutput containing goal, strategy, key files, and risks.

        Raises:
            ValueError: If no issue is present in the state.
        """
        if not state.issue:
            raise ValueError("Cannot analyze: no issue in ExecutionState")

        # Compile context using strategy
        strategy = self.context_strategy()
        compiled_context = strategy.compile(state, profile)

        # Convert compiled context to messages
        base_messages = strategy.to_messages(compiled_context)

        # Add user prompt requesting analysis
        user_prompt = """Analyze this issue and provide:
1. A clear goal statement describing what needs to be accomplished
2. A high-level strategy for how to approach the implementation
3. Key files that will likely need to be modified
4. Any potential risks or considerations

Respond with a structured ArchitectOutput."""

        messages = [
            *base_messages,
            AgentMessage(role="user", content=user_prompt),
        ]

        # Call driver with ArchitectOutput schema
        raw_response, new_session_id = await self.driver.generate(
            messages=messages,
            schema=ArchitectOutput,
            cwd=profile.working_dir,
            session_id=state.driver_session_id,
        )
        response = ArchitectOutput.model_validate(raw_response)

        logger.info(
            "Architect analysis complete",
            agent="architect",
            goal=response.goal[:100] + "..." if len(response.goal) > 100 else response.goal,
            key_files_count=len(response.key_files),
            risks_count=len(response.risks),
        )

        # Emit completion event
        if self._stream_emitter is not None:
            event = StreamEvent(
                type=StreamEventType.AGENT_OUTPUT,
                content=f"Analysis complete: {response.goal[:100]}...",
                timestamp=datetime.now(UTC),
                agent="architect",
                workflow_id=workflow_id,
            )
            await self._stream_emitter(event)

        return response
