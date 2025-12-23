"""Tests for API driver tool definitions."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from amelia.drivers.api.tools import AgenticContext, run_shell_command, write_file


class TestAgenticContext:
    """Test AgenticContext dataclass."""

    def test_raises_for_nonexistent_cwd(self):
        """Should raise ValueError for non-existent cwd."""
        with pytest.raises(ValueError, match="does not exist"):
            AgenticContext(cwd="/nonexistent/path/that/does/not/exist")


class TestRunShellCommand:
    """Test run_shell_command tool."""

    @pytest.fixture
    def run_context(self, tmp_path):
        """Create RunContext with real tmp_path."""
        ctx = MagicMock()
        ctx.deps = AgenticContext(cwd=str(tmp_path))
        return ctx

    async def test_executes_command_with_cwd(self, run_context, tmp_path):
        """Should pass context's cwd to SafeShellExecutor."""
        # Create a test file to verify cwd is used
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello from test")

        # Execute real command - tests that cwd from context is passed through
        result = await run_shell_command(run_context, "cat test.txt", timeout=30)

        assert result.strip() == "hello from test"

    async def test_caps_timeout_at_300_seconds(self, run_context):
        """Should cap timeout to prevent resource exhaustion."""
        # This tests the security fix - LLM could try to set huge timeout
        # The function should internally cap it to 300
        with patch('amelia.drivers.api.tools.SafeShellExecutor.execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "quick"
            await run_shell_command(run_context, "echo 'quick'", timeout=999999)

            # Verify SafeShellExecutor.execute was called with capped timeout
            mock_execute.assert_called_once()
            call_kwargs = mock_execute.call_args.kwargs
            assert call_kwargs['timeout'] == 300, f"Expected timeout=300, got timeout={call_kwargs['timeout']}"


class TestWriteFile:
    """Test write_file tool."""

    @pytest.fixture
    def run_context(self, tmp_path):
        """Create RunContext with real tmp_path."""
        ctx = MagicMock()
        ctx.deps = AgenticContext(cwd=str(tmp_path), allowed_dirs=[str(tmp_path)])
        return ctx

    async def test_passes_allowed_dirs_from_context(self, run_context, tmp_path):
        """Should pass allowed_dirs from context to SafeFileWriter."""
        file_path = str(tmp_path / "test.py")

        # Execute real write - tests that allowed_dirs from context is passed through
        result = await write_file(run_context, file_path, "print('hello')")

        # Verify file was actually written
        assert (tmp_path / "test.py").exists()
        assert (tmp_path / "test.py").read_text() == "print('hello')"
        assert "success" in result.lower() or "written" in result.lower()
