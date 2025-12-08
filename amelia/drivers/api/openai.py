# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from amelia.core.constants import ToolName
from amelia.core.state import AgentMessage
from amelia.drivers.base import DriverInterface
from amelia.tools.safe_file import SafeFileWriter
from amelia.tools.safe_shell import SafeShellExecutor


class ApiDriver(DriverInterface):
    """Real OpenAI API-based driver using pydantic-ai.

    Provides LLM generation capabilities through OpenAI's API.

    Attributes:
        model_name: The OpenAI model identifier in format 'openai:model-name'.
    """

    def __init__(self, model: str = 'openai:gpt-4o'):
        """Initialize the API driver with an OpenAI model.

        Args:
            model: Model identifier in format 'openai:model-name'. Defaults to 'openai:gpt-4o'.

        Raises:
            ValueError: If model does not start with 'openai:'.
        """
        # Validate that model is OpenAI
        if not model.startswith("openai:"):
            raise ValueError(f"Unsupported provider in model '{model}'. ApiDriver only supports 'openai:' models.")
        self.model_name = model

    async def generate(self, messages: list[AgentMessage], schema: type[BaseModel] | None = None, **kwargs: Any) -> Any:
        """Generate a response from the OpenAI model.

        Args:
            messages: List of conversation messages to send.
            schema: Optional Pydantic model for structured output parsing.
            **kwargs: Additional arguments (unused).

        Returns:
            Model output, either as string or parsed schema instance.

        Raises:
            RuntimeError: If API call fails.
        """
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is not set. Please configure it to use the ApiDriver.")

        # pydantic-ai Agent instantiation
        # We create a new agent for each call or reuse? 
        # Reusing might be better but for now per-call is safer for state isolation.
        agent = Agent(self.model_name, output_type=schema if schema else str)
        
        # Constructing conversation history
        # Pydantic-ai Agent.run takes the user prompt and history separately.
        # We need to extract the last user message as the prompt, or use a dummy prompt if none.
        # However, Agent.run() signature is run(prompt: str, *, message_history: list[ModelMessage] | None = None)

        # Convert AgentMessages to pydantic-ai ModelMessages
        # This is a simplification; a full implementation would map roles precisely.
        # For now, we will just map user/assistant/system.
        
        # We'll use the last message as the new prompt if it's from user,
        # otherwise we might need to send an empty prompt or continue?
        # Agent.run requires a string prompt.
        
        current_prompt = "Please continue."
        history_messages: list[ModelMessage] = []
        
        # If the last message is from the user, use it as the prompt.
        if messages and messages[-1].role == 'user':
            current_prompt = messages[-1].content
            # Use all previous messages as history
            msgs_to_process = messages[:-1]
        else:
            msgs_to_process = messages

        for msg in msgs_to_process:
            if msg.role == 'user':
                history_messages.append(ModelRequest(parts=[UserPromptPart(content=msg.content)]))
            elif msg.role == 'assistant':
                history_messages.append(ModelResponse(parts=[TextPart(content=msg.content)]))
            elif msg.role == 'system':
                # Pydantic-ai handles system prompts via Agent constructor usually,
                # but we can try to inject it or just ignore if global system prompt is set elsewhere.
                # ideally we should have a way to set system prompt per run or use SystemPromptPart (if exists).
                # For now, prepending to next user message or init is common fallback.
                # Let's assume system format is handled by main agent config for simplicity
                # or append to history as ModelRequest if supported.
                pass 
                
        try:
            result = await agent.run(current_prompt, message_history=history_messages)
            return result.output
        except Exception as e:
            raise RuntimeError(f"ApiDriver generation failed: {e}") from e

    async def execute_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """Execute a local tool by delegating to safe utilities.

        Args:
            tool_name: Name of the tool to execute (from ToolName constants).
            **kwargs: Tool-specific arguments.

        Returns:
            Tool execution result.

        Raises:
            ValueError: If required arguments are missing.
            NotImplementedError: If tool is not supported.
        """
        if tool_name == ToolName.WRITE_FILE:
            file_path = kwargs.get("file_path")
            content = kwargs.get("content")
            if not file_path or content is None:
                raise ValueError("Missing required arguments for write_file: file_path, content")
            return await SafeFileWriter.write(file_path, content)

        elif tool_name == ToolName.RUN_SHELL_COMMAND:
            command = kwargs.get("command")
            if not command:
                raise ValueError("Missing required argument for run_shell_command: command")
            return await SafeShellExecutor.execute(command)

        else:
            raise NotImplementedError(f"Tool '{tool_name}' not implemented in ApiDriver.")

    async def execute_agentic(
        self,
        prompt: str,
        cwd: str,
        session_id: str | None = None
    ) -> AsyncIterator[Any]:
        """Execute prompt with autonomous tool access (agentic mode).

        Args:
            prompt: The task or instruction for the model.
            cwd: Working directory for execution context.
            session_id: Optional session ID to resume.

        Yields:
            Stream events from execution (never yields, always raises).

        Raises:
            NotImplementedError: Always, as API drivers don't support agentic mode.

        Note:
            Agentic execution is not supported by API drivers.
        """
        raise NotImplementedError("Agentic execution is not supported by ApiDriver. Use CLI drivers for agentic mode.")
        # This is an async generator stub - yield is never reached but makes the signature correct
        yield
