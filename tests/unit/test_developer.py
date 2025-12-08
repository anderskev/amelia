# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Tests for Developer agent execution and error handling."""

from unittest.mock import AsyncMock

import pytest

from amelia.agents.developer import Developer
from amelia.core.exceptions import AgenticExecutionError
from amelia.drivers.base import DriverInterface
from amelia.drivers.cli.claude import ClaudeStreamEvent


class TestDeveloperExecution:
    """Tests for Developer.execute_task() behavior."""

    async def test_execute_shell_command_calls_driver(self, mock_task_factory):
        """Developer should call execute_tool for shell commands."""
        mock_driver = AsyncMock(spec=DriverInterface)
        mock_driver.execute_tool.return_value = "Command output"
        task = mock_task_factory(
            id="1", description="Run shell command: echo hello", status="pending"
        )
        developer = Developer(driver=mock_driver)

        result = await developer.execute_task(task)

        assert result["status"] == "completed"
        mock_driver.execute_tool.assert_called_once_with("run_shell_command", command="echo hello")

    async def test_execute_write_file_calls_driver(self, mock_task_factory):
        """Developer should call execute_tool for write file tasks."""
        mock_driver = AsyncMock(spec=DriverInterface)
        mock_driver.execute_tool.return_value = "File created"
        task = mock_task_factory(
            id="1", description="write file: test.py with print('hi')", status="pending"
        )
        developer = Developer(driver=mock_driver)

        await developer.execute_task(task)

        mock_driver.execute_tool.assert_called_once()

    async def test_exception_returns_failed_status(self, mock_task_factory):
        """Developer should return failed status on exception."""
        mock_driver = AsyncMock(spec=DriverInterface)
        mock_driver.execute_tool.side_effect = RuntimeError(
            "Mocked command failed: /bin/false returned non-zero exit code."
        )
        task = mock_task_factory(
            id="FAIL_T1", description="Run shell command: /bin/false", status="pending"
        )
        developer = Developer(driver=mock_driver)

        result = await developer.execute_task(task)

        assert result["status"] == "failed"
        assert "Mocked command failed" in result["output"]

    async def test_propagates_error_output(self, mock_task_factory):
        """Developer should propagate error messages in output."""
        mock_driver = AsyncMock(spec=DriverInterface)
        mock_driver.execute_tool.return_value = (
            "Command failed with exit code 1. Stderr: syntax error near line 5"
        )
        task = mock_task_factory(
            id="FIX_T1", description="Run shell command: python broken.py", status="pending"
        )
        developer = Developer(driver=mock_driver)

        result = await developer.execute_task(task)

        assert "failed" in result["output"].lower() or "error" in result["output"].lower()

    async def test_fallback_uses_generate(self, mock_task_factory):
        """Developer should use generate() for unstructured tasks."""
        mock_driver = AsyncMock(spec=DriverInterface)
        mock_driver.generate.return_value = "Generated response"
        task = mock_task_factory(
            id="1", description="Implement the foo feature", status="pending"
        )
        developer = Developer(driver=mock_driver)

        result = await developer.execute_task(task)

        assert result["status"] == "completed"
        mock_driver.generate.assert_called_once()


class TestDeveloperAgenticExecution:
    """Tests for Developer agentic execution mode."""

    async def test_execute_task_agentic_calls_execute_agentic(self, mock_task_factory):
        """Developer in agentic mode should call driver.execute_agentic."""
        mock_driver = AsyncMock(spec=DriverInterface)

        async def mock_execute_agentic(prompt, cwd, session_id=None):
            yield ClaudeStreamEvent(type="assistant", content="Working...")
            yield ClaudeStreamEvent(type="result", session_id="sess_001")

        mock_driver.execute_agentic = mock_execute_agentic

        task = mock_task_factory(id="1", description="Implement feature")
        developer = Developer(driver=mock_driver, execution_mode="agentic")

        result = await developer.execute_task(task, cwd="/tmp")

        assert result["status"] == "completed"

    async def test_execute_task_agentic_raises_on_error(self, mock_task_factory):
        """Developer in agentic mode should raise AgenticExecutionError on error event."""
        mock_driver = AsyncMock(spec=DriverInterface)

        async def mock_execute_agentic(prompt, cwd, session_id=None):
            yield ClaudeStreamEvent(type="error", content="Something went wrong")

        mock_driver.execute_agentic = mock_execute_agentic

        task = mock_task_factory(id="1", description="Implement feature")
        developer = Developer(driver=mock_driver, execution_mode="agentic")

        with pytest.raises(AgenticExecutionError) as exc_info:
            await developer.execute_task(task, cwd="/tmp")

        assert "Something went wrong" in str(exc_info.value)

    async def test_execute_task_structured_ignores_cwd(self, mock_task_factory):
        """Developer in structured mode should work without cwd."""
        mock_driver = AsyncMock(spec=DriverInterface)
        mock_driver.generate.return_value = "Generated response"

        task = mock_task_factory(id="1", description="Implement feature")
        developer = Developer(driver=mock_driver, execution_mode="structured")

        result = await developer.execute_task(task)

        assert result["status"] == "completed"
        mock_driver.generate.assert_called_once()
