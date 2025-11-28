from unittest.mock import AsyncMock

from amelia.agents.developer import Developer
from amelia.core.state import Task
from amelia.drivers.base import DriverInterface


async def test_developer_self_correction_on_command_failure():
    """
    Verifies that the Developer agent can detect and react to command failures
    (simulated via stderr or exceptions from the driver).
    """
    mock_driver = AsyncMock(spec=DriverInterface)
    # Simulate a tool execution failure returning an error message
    mock_driver.execute_tool.side_effect = RuntimeError("Mocked command failed: /bin/false returned non-zero exit code.")

    developer = Developer(driver=mock_driver)
    
    # A task that would trigger a tool execution
    failing_task = Task(id="FAIL_T1", description="Run shell command: /bin/false", dependencies=[])
    
    result = await developer.execute_task(failing_task)
    
    # Assert that the task execution is marked as failed and the error message is captured
    assert result["status"] == "failed"
    assert "Mocked command failed" in result["output"]
    mock_driver.execute_tool.assert_called_once_with("run_shell_command", command="/bin/false")

async def test_developer_reads_stderr_from_driver_for_refinement():
    """
    Tests that the Developer agent, when getting a response from `driver.execute_tool`
    that contains error messages, propagates those error messages in the output.
    """
    mock_driver = AsyncMock(spec=DriverInterface)
    # Simulate a command that returns output with error information
    mock_driver.execute_tool.return_value = "Command failed with exit code 1. Stderr: syntax error near line 5"

    developer = Developer(driver=mock_driver)
    task = Task(id="FIX_T1", description="Run shell command: python broken.py", dependencies=[])

    result = await developer.execute_task(task)

    # The developer should capture the error information in the output
    assert "failed" in result["output"].lower() or "error" in result["output"].lower()
    mock_driver.execute_tool.assert_called_once_with("run_shell_command", command="python broken.py")
