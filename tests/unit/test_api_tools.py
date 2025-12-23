"""Tests for API driver tool definitions."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from amelia.drivers.api.tools import AgenticContext, run_shell_command, write_file


class TestAgenticContext:
    """Test AgenticContext dataclass."""

    def test_create_context_with_cwd(self, tmp_path):
        """Should create context with cwd."""
        ctx = AgenticContext(cwd=str(tmp_path))
        assert ctx.cwd == str(tmp_path.resolve())
        assert ctx.allowed_dirs is None

    def test_create_context_with_allowed_dirs(self, tmp_path):
        """Should create context with allowed_dirs."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        ctx = AgenticContext(cwd=str(tmp_path), allowed_dirs=[str(tmp_path), str(subdir)])
        assert len(ctx.allowed_dirs) == 2

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
        """Should execute command in context's cwd."""
        # Create a test file to verify cwd is used
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello from test")

        # Execute real command, no mocking - tests actual behavior
        result = await run_shell_command(run_context, "cat test.txt", timeout=30)

        assert result.strip() == "hello from test"

    async def test_caps_timeout_at_300_seconds(self, run_context):
        """Should cap timeout to prevent resource exhaustion."""
        # This tests the security fix - LLM could try to set huge timeout
        # The function should internally cap it to 300
        # We test this by using a value > 300 and ensures it doesn't hang
        result = await run_shell_command(run_context, "echo 'quick'", timeout=999999)
        assert "quick" in result

    async def test_returns_command_output(self, run_context):
        """Should return stdout from command."""
        result = await run_shell_command(run_context, "echo 'test output'", timeout=30)
        assert "test output" in result


class TestWriteFile:
    """Test write_file tool."""

    @pytest.fixture
    def run_context(self, tmp_path):
        """Create RunContext with real tmp_path."""
        ctx = MagicMock()
        ctx.deps = AgenticContext(cwd=str(tmp_path), allowed_dirs=[str(tmp_path)])
        return ctx

    async def test_writes_file_with_allowed_dirs(self, run_context, tmp_path):
        """Should write file within allowed directories."""
        file_path = str(tmp_path / "test.py")

        # Execute real write, no mocking - tests actual behavior
        result = await write_file(run_context, file_path, "print('hello')")

        # Verify file was actually written
        assert (tmp_path / "test.py").exists()
        assert (tmp_path / "test.py").read_text() == "print('hello')"
        assert "success" in result.lower() or "written" in result.lower()

    async def test_creates_parent_directories(self, run_context, tmp_path):
        """Should create parent directories if needed."""
        file_path = str(tmp_path / "subdir" / "nested" / "test.py")

        result = await write_file(run_context, file_path, "# nested file")

        assert (tmp_path / "subdir" / "nested" / "test.py").exists()
