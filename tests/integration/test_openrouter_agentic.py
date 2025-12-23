# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Integration tests for OpenRouter agentic execution.

These tests require a valid OPENROUTER_API_KEY environment variable.
They make real API calls to OpenRouter's free models, so no costs are incurred.

Note: Free models may be rate-limited or occasionally fail. These tests are marked
as integration tests and excluded from the default test run. Run explicitly with:
    pytest -m integration
"""
import os
from pathlib import Path

import pytest

from amelia.core.state import AgentMessage
from amelia.drivers.api.events import ApiStreamEvent
from amelia.drivers.api.openai import ApiDriver

from .conftest import OPENROUTER_FREE_MODEL


# Maximum retries for flaky free model API calls
MAX_RETRIES = 3


async def _execute_with_retry(
    driver: ApiDriver,
    messages: list[AgentMessage],
    cwd: str,
    instructions: str,
) -> list[ApiStreamEvent]:
    """Execute agentic call with retry logic for flaky free models."""
    for attempt in range(MAX_RETRIES):
        events = []
        async for event in driver.execute_agentic(
            messages=messages,
            cwd=cwd,
            instructions=instructions,
        ):
            events.append(event)

        event_types = [e.type for e in events]
        # Success if we got a tool_use event (model used tools as expected)
        if "tool_use" in event_types:
            return events
        # If error or no tool use, retry
        if attempt < MAX_RETRIES - 1:
            continue

    # Return last attempt's events for assertion
    return events


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set",
)
class TestOpenRouterAgenticIntegration:
    """Integration tests requiring real OpenRouter API.

    These tests use free models which may be rate-limited or occasionally skip
    tool calls. Retry logic is used to improve reliability.
    """

    async def test_simple_shell_command(self, tmp_path: Path) -> None:
        """Should execute a simple shell command via OpenRouter."""
        driver = ApiDriver(model=OPENROUTER_FREE_MODEL)

        events = await _execute_with_retry(
            driver=driver,
            messages=[AgentMessage(role="user", content="Run 'echo hello' and tell me the output")],
            cwd=str(tmp_path),
            instructions="You are a helpful assistant. Use tools to complete tasks.",
        )

        # Should have tool_use and result events
        event_types = [e.type for e in events]
        assert "tool_use" in event_types, f"Expected tool_use event, got: {event_types}"
        assert "result" in event_types

    async def test_file_write(self, tmp_path: Path) -> None:
        """Should write a file via OpenRouter."""
        driver = ApiDriver(model=OPENROUTER_FREE_MODEL)

        events = await _execute_with_retry(
            driver=driver,
            messages=[
                AgentMessage(
                    role="user",
                    content="Create a file called 'hello.txt' with the content 'Hello from OpenRouter!'"
                )
            ],
            cwd=str(tmp_path),
            instructions="You are a helpful assistant. Use tools to complete tasks.",
        )

        # Verify file was created
        hello_file = tmp_path / "hello.txt"
        assert hello_file.exists(), "File should have been created"
        assert "Hello" in hello_file.read_text()

        # Should have tool_use and result events
        event_types = [e.type for e in events]
        assert "tool_use" in event_types
        assert "result" in event_types
