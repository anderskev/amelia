from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from amelia.agents.architect import Architect
from amelia.core.types import Issue


async def test_pydantic_ai_validation_failure() -> None:
    """
    Verify that invalid model outputs from PydanticAI agents are caught.
    """
    mock_driver = MagicMock()

    # Create a mock response that doesn't match TaskListResponse schema
    class InvalidResponse:
        # Missing 'tasks' attribute entirely
        pass

    mock_driver.generate = AsyncMock(return_value=InvalidResponse())

    architect = Architect(mock_driver)
    issue = Issue(id="INVALID-1", title="Test", description="Test invalid response handling")

    # The architect should fail when trying to process invalid response
    with pytest.raises((ValidationError, AttributeError)):
        await architect.plan(issue)
