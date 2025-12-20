# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Integration tests for cascade skip propagation.

Tests that when a step is skipped via blocker resolution, all dependent steps
are automatically (transitively) skipped via get_cascade_skips().

Dependency chain example: A <- B <- C (C depends on B, B depends on A)
When A is skipped, both B and C should be automatically skipped.
"""

import pytest

from amelia.core.orchestrator import blocker_resolution_node
from amelia.core.state import PlanStep
from amelia.core.types import DeveloperStatus

from .conftest import (
    assert_step_not_skipped,
    assert_step_skipped,
    make_batch,
    make_blocker,
    make_execution_state,
    make_plan,
    make_step,
)


@pytest.mark.parametrize(
    ("steps", "blocked_step_id", "expected_skipped", "expected_not_skipped"),
    [
        pytest.param(
            (
                make_step(id="step-a", depends_on=()),
                make_step(id="step-b", depends_on=("step-a",)),
                make_step(id="step-c", depends_on=("step-b",)),
            ),
            "step-a",
            ("step-a", "step-b", "step-c"),
            (),
            id="linear_chain",
        ),
        pytest.param(
            (
                make_step(id="step-a", depends_on=()),
                make_step(id="step-b", depends_on=("step-a",)),
                make_step(id="step-d", depends_on=()),
            ),
            "step-a",
            ("step-a", "step-b"),
            ("step-d",),
            id="with_independent_step",
        ),
        pytest.param(
            (
                make_step(id="step-a", depends_on=()),
                make_step(id="step-b", depends_on=("step-a",)),
                make_step(id="step-c", depends_on=("step-b",)),
                make_step(id="step-d", depends_on=("step-c",)),
                make_step(id="step-e", depends_on=("step-d",)),
            ),
            "step-a",
            ("step-a", "step-b", "step-c", "step-d", "step-e"),
            (),
            id="long_transitive_chain",
        ),
        pytest.param(
            (
                make_step(id="step-a", depends_on=()),
                make_step(id="step-b", depends_on=()),
                make_step(id="step-c", depends_on=("step-a",)),
                make_step(id="step-d", depends_on=("step-a",)),
                make_step(id="step-e", depends_on=("step-b",)),
                make_step(id="step-f", depends_on=("step-d", "step-e")),
            ),
            "step-a",
            ("step-a", "step-c", "step-d", "step-f"),
            ("step-b", "step-e"),
            id="multi_root_tree",
        ),
    ],
)
async def test_cascade_skip_propagation(
    steps: tuple[PlanStep, ...],
    blocked_step_id: str,
    expected_skipped: tuple[str, ...],
    expected_not_skipped: tuple[str, ...],
) -> None:
    """Test cascade skip propagation with various dependency patterns.

    Args:
        steps: Steps to create in the batch
        blocked_step_id: ID of the step to block and skip
        expected_skipped: Step IDs that should be skipped (direct + cascade)
        expected_not_skipped: Step IDs that should not be skipped (independent)
    """
    batch = make_batch(batch_number=1, steps=steps)
    plan = make_plan(batches=(batch,))
    blocker = make_blocker(blocked_step_id)

    state = make_execution_state(
        execution_plan=plan,
        current_batch_index=0,
        developer_status=DeveloperStatus.BLOCKED,
        current_blocker=blocker,
        blocker_resolution="skip",
        human_approved=True,
    )

    result = await blocker_resolution_node(state)

    # Assert all expected skips
    for step_id in expected_skipped:
        assert_step_skipped(result, step_id)

    # Assert all expected non-skips
    for step_id in expected_not_skipped:
        assert_step_not_skipped(result, step_id)


async def test_skip_resolution_clears_blocker_state() -> None:
    """After skip resolution, blocker state should be cleared."""
    step_a = make_step(id="step-a", depends_on=())
    batch = make_batch(batch_number=1, steps=(step_a,))
    plan = make_plan(batches=(batch,))
    blocker = make_blocker("step-a")

    state = make_execution_state(
        execution_plan=plan,
        current_batch_index=0,
        developer_status=DeveloperStatus.BLOCKED,
        current_blocker=blocker,
        blocker_resolution="skip",
        human_approved=True,
    )

    result = await blocker_resolution_node(state)

    # Blocker should be cleared
    assert result.get("current_blocker") is None
    assert result.get("blocker_resolution") is None
