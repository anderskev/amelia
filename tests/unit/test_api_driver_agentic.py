"""Tests for ApiDriver agentic execution."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from amelia.core.state import AgentMessage
from amelia.drivers.api.openai import ApiDriver


class TestValidateMessages:
    """Test _validate_messages helper method."""

    @pytest.fixture
    def driver(self):
        """Create ApiDriver instance."""
        return ApiDriver(model="openai:gpt-4o")

    def test_rejects_empty_messages(self, driver):
        """Should reject empty message list."""
        with pytest.raises(ValueError, match="cannot be empty"):
            driver._validate_messages([])

    def test_rejects_whitespace_only_content(self, driver):
        """Should reject messages with only whitespace content."""
        with pytest.raises(ValueError, match="empty or whitespace-only"):
            driver._validate_messages([AgentMessage(role="user", content="   \n\t  ")])

    def test_rejects_oversized_content(self, driver):
        """Should reject messages exceeding 100KB."""
        large_content = "x" * 100_001
        with pytest.raises(ValueError, match="exceeds maximum"):
            driver._validate_messages([AgentMessage(role="user", content=large_content)])

    def test_rejects_total_size_exceeding_limit(self, driver):
        """Should reject when total message size exceeds 500KB."""
        # 10 messages of 60KB each = 600KB > 500KB limit
        messages = [
            AgentMessage(role="user", content="x" * 60_000)
            for _ in range(10)
        ]
        with pytest.raises(ValueError, match="Total message content exceeds"):
            driver._validate_messages(messages)

    def test_rejects_invalid_role(self, driver):
        """Should reject invalid message roles."""
        with pytest.raises(ValueError, match="Invalid message role"):
            driver._validate_messages([AgentMessage(role="invalid", content="test")])

    def test_accepts_valid_messages(self, driver):
        """Should accept valid message list."""
        messages = [
            AgentMessage(role="system", content="You are helpful"),
            AgentMessage(role="user", content="Hello"),
            AgentMessage(role="assistant", content="Hi there"),
        ]
        driver._validate_messages(messages)  # Should not raise


class TestBuildMessageHistory:
    """Test _build_message_history helper method."""

    @pytest.fixture
    def driver(self):
        """Create ApiDriver instance."""
        return ApiDriver(model="openai:gpt-4o")

    def test_returns_none_for_single_message(self, driver):
        """Should return None for single user message."""
        messages = [AgentMessage(role="user", content="Hello")]
        result = driver._build_message_history(messages)
        assert result is None

    def test_returns_none_for_system_only(self, driver):
        """Should return None when only system messages present."""
        messages = [
            AgentMessage(role="system", content="You are helpful"),
            AgentMessage(role="user", content="Hello"),
        ]
        result = driver._build_message_history(messages)
        assert result is None

    def test_builds_history_from_prior_messages(self, driver):
        """Should build history excluding last user message."""
        messages = [
            AgentMessage(role="user", content="First"),
            AgentMessage(role="assistant", content="Response"),
            AgentMessage(role="user", content="Second"),
        ]
        result = driver._build_message_history(messages)
        assert result is not None
        assert len(result) == 2  # First user + assistant

    def test_skips_empty_content(self, driver):
        """Should skip messages with empty content."""
        messages = [
            AgentMessage(role="user", content="First"),
            AgentMessage(role="assistant", content=""),
            AgentMessage(role="user", content="Second"),
        ]
        result = driver._build_message_history(messages)
        assert result is not None
        assert len(result) == 1  # Only first user message


class TestExecuteAgentic:
    """Test execute_agentic core method."""

    async def test_rejects_nonexistent_cwd(self, monkeypatch):
        """Should reject non-existent working directory."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        driver = ApiDriver(model="openai:gpt-4o")

        with pytest.raises(ValueError, match="does not exist"):
            async for _ in driver.execute_agentic(
                messages=[AgentMessage(role="user", content="test")],
                cwd="/nonexistent/path/that/does/not/exist",
            ):
                pass

    async def test_yields_result_event(self, monkeypatch, tmp_path):
        """Should yield result event at end of execution."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        driver = ApiDriver(model="openai:gpt-4o")

        # Mock the pydantic-ai Agent
        with patch("amelia.drivers.api.openai.Agent") as mock_agent_class:
            # Create an async iterator that yields nothing
            async def empty_async_iter():
                return
                yield  # Make it a generator

            mock_run = AsyncMock()
            mock_run.result = MagicMock(output="Done")
            mock_run.__aenter__ = AsyncMock(return_value=mock_run)
            mock_run.__aexit__ = AsyncMock(return_value=None)
            mock_run.__aiter__ = lambda self: empty_async_iter()

            mock_agent = MagicMock()
            mock_agent.iter = MagicMock(return_value=mock_run)
            mock_agent_class.return_value = mock_agent

            events = []
            async for event in driver.execute_agentic(
                messages=[AgentMessage(role="user", content="test")],
                cwd=str(tmp_path),  # Use real tmp_path
            ):
                events.append(event)

            # Should have at least a result event
            assert len(events) >= 1, f"No events yielded"
            if events[-1].type == "error":
                print(f"Error event: {events[-1].content}")
            assert events[-1].type == "result", f"Expected result, got {events[-1].type}: {events[-1].content if events[-1].type == 'error' else ''}"
            assert events[-1].session_id is not None

    async def test_generates_unique_session_id(self, monkeypatch):
        """Should generate unique session IDs."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        driver = ApiDriver(model="openai:gpt-4o")

        session_ids = set()
        for _ in range(3):
            session_ids.add(driver._generate_session_id())

        assert len(session_ids) == 3  # All unique
