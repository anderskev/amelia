# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Tests for orchestrator routing functions."""

import pytest

from amelia.core.orchestrator import route_after_developer
from amelia.core.types import DeveloperStatus


class TestRouteAfterDeveloper:
    """Tests for route_after_developer routing function."""

    def test_all_done_routes_to_reviewer(self, mock_execution_state_factory):
        """When developer_status is ALL_DONE, should route to reviewer."""
        state = mock_execution_state_factory(developer_status=DeveloperStatus.ALL_DONE)

        result = route_after_developer(state)

        assert result == "reviewer", (
            "route_after_developer should return 'reviewer' when "
            "developer_status is ALL_DONE"
        )

    def test_batch_complete_routes_to_batch_approval(self, mock_execution_state_factory):
        """When developer_status is BATCH_COMPLETE, should route to batch_approval."""
        state = mock_execution_state_factory(developer_status=DeveloperStatus.BATCH_COMPLETE)

        result = route_after_developer(state)

        assert result == "batch_approval", (
            "route_after_developer should return 'batch_approval' when "
            "developer_status is BATCH_COMPLETE"
        )

    def test_blocked_routes_to_blocker_resolution(self, mock_execution_state_factory):
        """When developer_status is BLOCKED, should route to blocker_resolution."""
        state = mock_execution_state_factory(developer_status=DeveloperStatus.BLOCKED)

        result = route_after_developer(state)

        assert result == "blocker_resolution", (
            "route_after_developer should return 'blocker_resolution' when "
            "developer_status is BLOCKED"
        )

    def test_executing_routes_to_developer(self, mock_execution_state_factory):
        """When developer_status is EXECUTING, should route back to developer."""
        state = mock_execution_state_factory(developer_status=DeveloperStatus.EXECUTING)

        result = route_after_developer(state)

        assert result == "developer", (
            "route_after_developer should return 'developer' when "
            "developer_status is EXECUTING (continue executing)"
        )

    def test_default_executing_status(self, mock_execution_state_factory):
        """When developer_status is not explicitly set, should default to EXECUTING."""
        # Create state without explicitly setting developer_status (uses default)
        state = mock_execution_state_factory()

        # Verify default is EXECUTING
        assert state.developer_status == DeveloperStatus.EXECUTING

        result = route_after_developer(state)

        assert result == "developer", (
            "route_after_developer should return 'developer' for default "
            "EXECUTING status"
        )

    @pytest.mark.parametrize(
        "status,expected_route",
        [
            (DeveloperStatus.ALL_DONE, "reviewer"),
            (DeveloperStatus.BATCH_COMPLETE, "batch_approval"),
            (DeveloperStatus.BLOCKED, "blocker_resolution"),
            (DeveloperStatus.EXECUTING, "developer"),
        ],
        ids=[
            "all_done_to_reviewer",
            "batch_complete_to_batch_approval",
            "blocked_to_blocker_resolution",
            "executing_to_developer",
        ],
    )
    def test_route_after_developer_parametrized(
        self,
        status: DeveloperStatus,
        expected_route: str,
        mock_execution_state_factory,
    ):
        """Parametrized test covering all developer status routing scenarios."""
        state = mock_execution_state_factory(developer_status=status)

        result = route_after_developer(state)

        assert result == expected_route, (
            f"route_after_developer should return '{expected_route}' when "
            f"developer_status is {status.value}"
        )
