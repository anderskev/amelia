# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# tests/unit/test_exceptions.py
"""Tests for custom exceptions."""

import pytest

from amelia.core.exceptions import AgenticExecutionError, AmeliaError


def test_agentic_execution_error_is_amelia_error():
    """AgenticExecutionError should inherit from AmeliaError."""
    error = AgenticExecutionError("test error")
    assert isinstance(error, AmeliaError)
    assert str(error) == "test error"


def test_agentic_execution_error_can_be_raised():
    """AgenticExecutionError should be raisable."""
    with pytest.raises(AgenticExecutionError) as exc_info:
        raise AgenticExecutionError("agentic failed")
    assert "agentic failed" in str(exc_info.value)
