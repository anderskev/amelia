# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import pytest
from pydantic import BaseModel

from amelia.core.state import AgentMessage
from amelia.drivers.api.openai import ApiDriver


class ResponseSchema(BaseModel):
    """Test schema for structured output."""
    message: str


class TestApiDriverSystemMessages:
    """Tests for system message handling in ApiDriver."""

    @pytest.fixture
    def openrouter_api_key(self, monkeypatch):  # type: ignore[no-untyped-def]
        """Set OPENROUTER_API_KEY environment variable."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    @pytest.mark.parametrize("messages,expected_system_prompt,expected_history_len", [
        pytest.param(
            [
                AgentMessage(role="system", content="You are a helpful assistant."),
                AgentMessage(role="user", content="Hello"),
                AgentMessage(role="assistant", content="Hi there"),
                AgentMessage(role="user", content="How are you?")
            ],
            "You are a helpful assistant.",
            2,
            id="single_system_message"
        ),
        pytest.param(
            [
                AgentMessage(role="system", content="You are a helpful assistant."),
                AgentMessage(role="system", content="Be concise and accurate."),
                AgentMessage(role="user", content="Hello"),
            ],
            "You are a helpful assistant.\n\nBe concise and accurate.",
            0,
            id="multiple_system_messages"
        ),
        pytest.param(
            [
                AgentMessage(role="user", content="Hello"),
                AgentMessage(role="assistant", content="Hi there"),
                AgentMessage(role="user", content="How are you?"),
            ],
            (),
            2,
            id="no_system_messages"
        ),
    ])
    async def test_system_message_handling(self, openrouter_api_key, mock_pydantic_agent, messages, expected_system_prompt, expected_history_len) -> None:  # type: ignore[no-untyped-def]
        """Test system message extraction, combination, and exclusion from history."""
        driver = ApiDriver()

        with mock_pydantic_agent() as mocks:
            await driver.generate(messages)

            # Verify Agent was instantiated with correct system prompt
            mocks["agent_class"].assert_called_once()
            call_kwargs = mocks["agent_class"].call_args[1]
            assert call_kwargs["system_prompt"] == expected_system_prompt
            assert call_kwargs["output_type"] is str

            # Verify system messages are excluded from history
            mocks["agent_instance"].run.assert_called_once()
            run_kwargs = mocks["agent_instance"].run.call_args[1]
            history = run_kwargs["message_history"]
            assert len(history) == expected_history_len

    async def test_system_messages_with_schema(self, openrouter_api_key, mock_pydantic_agent) -> None:  # type: ignore[no-untyped-def]
        """System messages should work correctly with structured output."""
        driver = ApiDriver()
        messages = [
            AgentMessage(role="system", content="You are a helpful assistant."),
            AgentMessage(role="user", content="Hello"),
            AgentMessage(role="assistant", content="Hi there"),
            AgentMessage(role="user", content="How are you?")
        ]

        with mock_pydantic_agent() as mocks:
            # Override the default mock result output for this test
            mocks["result"].output = ResponseSchema(message="Test")

            result, session_id = await driver.generate(messages, schema=ResponseSchema)

            # Verify Agent was created with both system_prompt and output_type
            call_kwargs = mocks["agent_class"].call_args[1]
            assert call_kwargs["system_prompt"] == "You are a helpful assistant."
            assert call_kwargs["output_type"] is ResponseSchema
            assert isinstance(result, ResponseSchema)
            assert result.message == "Test"
            assert session_id is None  # API driver doesn't support sessions
