"""Unit tests for pipeline routing functions."""

from datetime import UTC, datetime

from amelia.pipelines.implementation.routing import route_after_start
from amelia.pipelines.implementation.state import ImplementationState


class TestRouteAfterStart:
    """Tests for route_after_start routing function."""

    def test_routes_to_architect_when_not_external_plan(self) -> None:
        """Should route to architect when external_plan is False."""
        state = ImplementationState(
            workflow_id="wf-001",
            profile_id="test",
            created_at=datetime.now(UTC),
            status="pending",
            external_plan=False,
        )
        assert route_after_start(state) == "architect"

    def test_routes_to_plan_validator_when_external_plan(self) -> None:
        """Should route to plan_validator when external_plan is True."""
        state = ImplementationState(
            workflow_id="wf-001",
            profile_id="test",
            created_at=datetime.now(UTC),
            status="pending",
            external_plan=True,
        )
        assert route_after_start(state) == "plan_validator"
