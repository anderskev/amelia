# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Tests for core state models."""

from amelia.core.state import ExecutionState
from amelia.core.types import Profile


def test_execution_state_workflow_status_default():
    """ExecutionState workflow_status should default to 'running'."""
    profile = Profile(name="test", driver="cli:claude")
    state = ExecutionState(profile=profile)
    assert state.workflow_status == "running"


def test_execution_state_workflow_status_failed():
    """ExecutionState should accept workflow_status='failed'."""
    profile = Profile(name="test", driver="cli:claude")
    state = ExecutionState(profile=profile, workflow_status="failed")
    assert state.workflow_status == "failed"
