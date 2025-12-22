# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""End-to-end integration tests for multi-batch execution flows.

These tests exercise the full orchestrator workflow across multiple batches:
- Sequential batch execution with batch checkpoints
- Human approval at batch boundaries
- Blocker handling during multi-batch execution
- Complete workflow from plan approval through final completion

Tests use real orchestrator graph with in-memory checkpointing to simulate
the full human-in-the-loop workflow without mocking orchestrator internals.
"""

from contextlib import contextmanager
from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from amelia.core.state import (
    BatchResult,
    BlockerReport,
    ExecutionPlan,
    ReviewResult,
    StepResult,
)
from amelia.core.types import DeveloperStatus, TrustLevel

from .conftest import (
    assert_step_skipped,
    assert_workflow_status,
    make_batch,
    make_blocker,
    make_execution_state,
    make_issue,
    make_plan,
    make_profile,
    make_step,
)


# =============================================================================
# Helper Functions
# =============================================================================


async def run_until_interrupt(
    graph: CompiledStateGraph[Any],
    state_or_none: dict[str, Any] | None,
    config: RunnableConfig,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Run graph until interrupt, return (all_chunks, interrupt_info).

    Iterates through graph.astream() collecting chunks until
    an interrupt is encountered (chunk containing "__interrupt__").

    Args:
        graph: The orchestrator graph
        state_or_none: Initial state dict or None to continue from checkpoint
        config: Runnable config with thread_id

    Returns:
        Tuple of (list of all chunks, interrupt info dict if hit else None)
    """
    chunks = []
    interrupt_info = None
    async for chunk in graph.astream(state_or_none, config):
        chunks.append(chunk)
        if "__interrupt__" in chunk:
            interrupt_info = chunk
            break
    return chunks, interrupt_info


async def approve_at_interrupt(graph: CompiledStateGraph[Any], config: RunnableConfig) -> None:
    """Simulate human approval at an interrupt point.

    Uses graph.aupdate_state to set human_approved=True at the
    current checkpoint.
    """
    await graph.aupdate_state(config, {"human_approved": True})


async def reject_at_interrupt(
    graph: CompiledStateGraph[Any],
    config: RunnableConfig,
    feedback: str | None = None,
) -> None:
    """Simulate human rejection at an interrupt point.

    Uses graph.aupdate_state to set human_approved=False and
    optionally include rejection feedback via human_feedback field.
    """
    await graph.aupdate_state(config, {"human_approved": False, "human_feedback": feedback})


async def resolve_blocker(
    graph: CompiledStateGraph[Any],
    config: RunnableConfig,
    resolution: str,
) -> None:
    """Simulate blocker resolution (skip, abort, abort_revert, or fix instruction).

    Uses graph.aupdate_state to set blocker_resolution which will
    be processed by blocker_resolution_node.
    """
    await graph.aupdate_state(config, {"blocker_resolution": resolution})


# =============================================================================
# Mock Factory Functions
# =============================================================================


def create_batch_completing_developer(
    plan: ExecutionPlan,
    blocker_at_batch: int | None = None,
    blocker_report: BlockerReport | None = None,
) -> AsyncMock:
    """Create mock Developer that completes batches sequentially.

    Args:
        plan: The execution plan (to know total batches)
        blocker_at_batch: If set, return BLOCKED status at this batch (0-indexed)
        blocker_report: The blocker to return when blocked

    Returns:
        Mock Developer that tracks batch progress via call count.
        Returns BATCH_COMPLETE for intermediate batches,
        ALL_DONE for the final batch, or BLOCKED if blocker_at_batch matches.
    """
    mock_dev = AsyncMock()
    call_count = [0]  # Mutable to track calls

    async def run_side_effect(*args: Any, **kwargs: Any) -> dict[str, Any]:
        batch_idx = call_count[0]
        call_count[0] += 1

        # Check if this batch should block
        if blocker_at_batch is not None and batch_idx == blocker_at_batch:
            return {
                "developer_status": DeveloperStatus.BLOCKED,
                "current_blocker": blocker_report,
            }

        total_batches = len(plan.batches)
        is_last_batch = batch_idx >= total_batches - 1

        # Create batch result for this batch
        batch = plan.batches[min(batch_idx, total_batches - 1)]
        step_results = tuple(
            StepResult(step_id=step.id, status="completed", output="ok")
            for step in batch.steps
        )
        batch_result = BatchResult(
            batch_number=batch.batch_number,
            status="complete",
            completed_steps=step_results,
            blocker=None,
        )

        return {
            "developer_status": DeveloperStatus.ALL_DONE if is_last_batch else DeveloperStatus.BATCH_COMPLETE,
            "current_batch_index": batch_idx + 1,
            "batch_results": [batch_result],  # Must be list for operator.add reducer
        }

    mock_dev.run = AsyncMock(side_effect=run_side_effect)
    return mock_dev


def create_mock_reviewer(approved: bool = True, comments: list[str] | None = None) -> AsyncMock:
    """Create mock Reviewer with standard ReviewResult.

    Args:
        approved: Whether review is approved
        comments: Review comments (defaults to ["Looks good"])

    Returns:
        Mock Reviewer that returns ReviewResult
    """
    if comments is None:
        comments = ["Looks good"] if approved else ["Needs changes"]

    mock_review = ReviewResult(
        approved=approved,
        comments=comments,
        severity="low",
        reviewer_persona="Test Reviewer",
    )
    mock_reviewer = AsyncMock()
    mock_reviewer.review = AsyncMock(return_value=(mock_review, None))
    return mock_reviewer


@contextmanager
def mock_agents_context(
    architect: AsyncMock | None = None,
    developer: AsyncMock | None = None,
    reviewer: AsyncMock | None = None,
) -> Any:
    """Context manager that patches Architect, Developer, Reviewer, and DriverFactory.

    Args:
        architect: Mock Architect instance (or None to create default)
        developer: Mock Developer instance (or None to create default)
        reviewer: Mock Reviewer instance (or None to create default)

    Yields:
        Tuple of (mock_architect, mock_developer, mock_reviewer) for assertions
    """
    mock_architect = architect or AsyncMock()
    mock_developer = developer or AsyncMock()
    mock_reviewer = reviewer or AsyncMock()

    with patch("amelia.core.orchestrator.Architect", return_value=mock_architect), \
         patch("amelia.core.orchestrator.Developer", return_value=mock_developer), \
         patch("amelia.core.orchestrator.Reviewer", return_value=mock_reviewer), \
         patch("amelia.core.orchestrator.DriverFactory.get_driver", return_value=AsyncMock()):
        yield mock_architect, mock_developer, mock_reviewer


# =============================================================================
# Test Classes
# =============================================================================


class TestHappyPathExecution:
    """Tests for successful multi-batch execution flows."""

    async def test_three_batch_execution_with_approvals(self, orchestrator_graph: CompiledStateGraph[Any]) -> None:
        """Test complete 3-batch execution with human approvals at each checkpoint.

        Scenario:
        1. Create ExecutionPlan with 3 batches (low, medium, high risk)
        2. Run graph with STANDARD trust level
        3. Verify: architect -> approval -> batch 1 -> interrupt -> approve ->
           batch 2 -> interrupt -> approve -> batch 3 -> reviewer

        Assertions:
        - 2 batch approvals recorded (batch 3 goes to reviewer)
        - 3 batch results recorded
        - Reviewer node reached
        - Final state has last_review populated
        """
        # Create a 3-batch plan with different risk levels
        batch1 = make_batch(
            batch_number=1,
            steps=(make_step(id="step-1", risk_level="low"),),
            risk_summary="low",
        )
        batch2 = make_batch(
            batch_number=2,
            steps=(make_step(id="step-2", risk_level="medium"),),
            risk_summary="medium",
        )
        batch3 = make_batch(
            batch_number=3,
            steps=(make_step(id="step-3", risk_level="high"),),
            risk_summary="high",
        )
        plan = make_plan(batches=(batch1, batch2, batch3))

        # Create profile with STANDARD trust level (requires checkpoint at each batch)
        profile = make_profile(
            trust_level=TrustLevel.STANDARD,
            batch_checkpoint_enabled=True,
        )
        issue = make_issue()

        # Initial state - issue loaded, no plan yet
        initial_state = make_execution_state(
            issue=issue,
            profile=profile,
            execution_plan=None,
        )

        # Create mock developer that completes all batches
        mock_developer = create_batch_completing_developer(plan)

        # Create mock architect that returns our plan
        mock_architect = AsyncMock()
        mock_architect.generate_execution_plan = AsyncMock(return_value=(plan, None))

        # Create mock reviewer that approves
        mock_reviewer = create_mock_reviewer(approved=True)

        config = cast(RunnableConfig, {"configurable": {"thread_id": "test-3batch", "execution_mode": "server", "profile": profile}})

        with mock_agents_context(mock_architect, mock_developer, mock_reviewer):
            # Run until first interrupt (human_approval_node for initial plan approval)
            chunks, interrupt = await run_until_interrupt(orchestrator_graph, initial_state.model_dump(), config)
            assert interrupt is not None, "Should interrupt at human_approval_node"

            # Approve initial plan
            await approve_at_interrupt(orchestrator_graph, config)

            # Run until next interrupt (batch_approval_node after batch 1)
            chunks, interrupt = await run_until_interrupt(orchestrator_graph, None, config)
            assert interrupt is not None, "Should interrupt at batch_approval_node after batch 1"

            # Approve batch 1
            await approve_at_interrupt(orchestrator_graph, config)

            # Run until next interrupt (batch_approval_node after batch 2)
            chunks, interrupt = await run_until_interrupt(orchestrator_graph, None, config)
            assert interrupt is not None, "Should interrupt at batch_approval_node after batch 2"

            # Approve batch 2
            await approve_at_interrupt(orchestrator_graph, config)

            # Run until next interrupt (batch_approval_node after batch 3) or completion
            # Since batch 3 is the last batch, developer returns ALL_DONE, so it goes to reviewer
            # Reviewer runs and returns approved, so workflow ends
            chunks, interrupt = await run_until_interrupt(orchestrator_graph, None, config)

            # Get final state
            final_state = await orchestrator_graph.aget_state(config)
            state_values = final_state.values

            # Assertions
            # Should have 2 batch approvals (one for each intermediate batch checkpoint)
            # The final batch goes directly to reviewer without needing approval
            batch_approvals = state_values.get("batch_approvals", [])
            assert len(batch_approvals) == 2, f"Expected 2 batch approvals, got {len(batch_approvals)}"
            for approval in batch_approvals:
                assert approval.approved is True

            # Should have batch results from developer
            batch_results = state_values.get("batch_results", [])
            # batch_results is accumulated via operator.add, should have results from all 3 batches
            assert len(batch_results) == 3, f"Expected 3 batch results, got {len(batch_results)}"

            # Should have a review result
            last_review = state_values.get("last_review")
            assert last_review is not None, "Should have last_review populated"
            assert last_review.approved is True


class TestBatchRejection:
    """Tests for batch rejection scenarios."""

    async def test_batch_rejection_ends_workflow(self, orchestrator_graph: CompiledStateGraph[Any]) -> None:
        """Test that rejecting a batch ends the workflow.

        Scenario:
        1. Create ExecutionPlan with 3 batches
        2. Run graph, approve batch 1
        3. After batch 2 completes, reject with feedback
        4. Verify workflow ends, batch 3 not executed

        Assertions:
        - Only 1 BatchApproval with approved=True
        - 1 BatchApproval with approved=False
        - Workflow ends (no more chunks after rejection)
        - batch_results has 2 entries (batch 1 and 2 executed)
        """
        # Create a 3-batch plan
        plan = make_plan(num_batches=3, steps_per_batch=1)

        # Create profile with STANDARD trust level
        profile = make_profile(
            trust_level=TrustLevel.STANDARD,
            batch_checkpoint_enabled=True,
        )
        issue = make_issue()

        # Initial state
        initial_state = make_execution_state(
            issue=issue,
            profile=profile,
            execution_plan=None,
        )

        # Create mock developer that completes batches
        mock_developer = create_batch_completing_developer(plan)

        # Create mock architect
        mock_architect = AsyncMock()
        mock_architect.generate_execution_plan = AsyncMock(return_value=(plan, None))

        config = cast(RunnableConfig, {"configurable": {"thread_id": "test-rejection", "execution_mode": "server", "profile": profile}})

        with mock_agents_context(mock_architect, mock_developer):
            # Run until first interrupt (human_approval_node)
            chunks, interrupt = await run_until_interrupt(orchestrator_graph, initial_state.model_dump(), config)
            assert interrupt is not None

            # Approve initial plan
            await approve_at_interrupt(orchestrator_graph, config)

            # Run until batch_approval_node after batch 1
            chunks, interrupt = await run_until_interrupt(orchestrator_graph, None, config)
            assert interrupt is not None

            # Approve batch 1
            await approve_at_interrupt(orchestrator_graph, config)

            # Run until batch_approval_node after batch 2
            chunks, interrupt = await run_until_interrupt(orchestrator_graph, None, config)
            assert interrupt is not None

            # REJECT batch 2 with feedback
            await reject_at_interrupt(orchestrator_graph, config, feedback="Changes look risky, stopping here")

            # Run to completion (should end workflow)
            chunks, interrupt = await run_until_interrupt(orchestrator_graph, None, config)

            # Get final state
            final_state = await orchestrator_graph.aget_state(config)
            state_values = final_state.values

            # Assertions
            batch_approvals = state_values.get("batch_approvals", [])
            assert len(batch_approvals) == 2, f"Expected 2 batch approvals, got {len(batch_approvals)}"

            # First should be approved, second should be rejected
            assert batch_approvals[0].approved is True
            assert batch_approvals[1].approved is False
            assert batch_approvals[1].feedback == "Changes look risky, stopping here"

            # Should have 2 batch results (batches 1 and 2 were executed)
            batch_results = state_values.get("batch_results", [])
            assert len(batch_results) == 2, f"Expected 2 batch results, got {len(batch_results)}"


class TestBlockerResolution:
    """Tests for blocker resolution scenarios."""

    @pytest.mark.parametrize("resolution,expect_revert,expect_cascade_skips,expect_review", [
        pytest.param("abort_revert", True, False, False, id="abort_revert"),
        pytest.param("skip", False, True, True, id="skip_cascades"),
        pytest.param("fix_instruction", False, False, True, id="fix_retries"),
    ])
    async def test_blocker_resolution_scenarios(
        self,
        orchestrator_graph: CompiledStateGraph[Any],
        resolution: str,
        expect_revert: bool,
        expect_cascade_skips: bool,
        expect_review: bool,
    ) -> None:
        """Test blocker resolution with different strategies.

        Parameters:
            resolution: Resolution strategy (abort_revert, skip, or fix instruction)
            expect_revert: Whether revert_to_git_snapshot should be called
            expect_cascade_skips: Whether cascade skips should be applied
            expect_review: Whether workflow should reach reviewer
        """
        # Create plan with 2 batches for abort_revert/fix, or with dependencies for skip
        if expect_cascade_skips:
            # For skip test: create batch with dependencies
            batch1 = make_batch(
                batch_number=1,
                steps=(make_step(id="step-1", description="Setup step", risk_level="low"),),
                risk_summary="low",
            )
            step_a = make_step(id="step-a", description="Primary task", risk_level="medium", depends_on=())
            step_b = make_step(id="step-b", description="Dependent task", risk_level="medium", depends_on=("step-a",))
            batch2 = make_batch(
                batch_number=2,
                steps=(step_a, step_b),
                risk_summary="medium",
            )
            plan = make_plan(batches=(batch1, batch2))
            blocker_step_id = "step-a"
            blocker_description = "Primary task"
        else:
            # For abort_revert and fix tests: simple 2-batch or 1-batch plan
            if expect_revert:
                # 2 batches for abort_revert
                batch1 = make_batch(
                    batch_number=1,
                    steps=(make_step(id="step-1", risk_level="low"),),
                    risk_summary="low",
                )
                batch2 = make_batch(
                    batch_number=2,
                    steps=(make_step(id="step-2", risk_level="medium"),),
                    risk_summary="medium",
                )
                plan = make_plan(batches=(batch1, batch2))
                blocker_step_id = "step-2"
                blocker_description = "step-2 (blocked)"
                blocker_at_batch = 1
            else:
                # 1 batch for fix test
                batch1 = make_batch(
                    batch_number=1,
                    steps=(make_step(id="step-1", description="Create feature", risk_level="medium"),),
                    risk_summary="medium",
                )
                plan = make_plan(batches=(batch1,))
                blocker_step_id = "step-1"
                blocker_description = "Create feature"
                blocker_at_batch = 0

        # Create blocker
        blocker = make_blocker(
            step_id=blocker_step_id,
            step_description=blocker_description,
            error_message="Database connection failed" if expect_revert else "Command failed with exit code 1",
        )

        # Create profile
        profile = make_profile(
            trust_level=TrustLevel.STANDARD,
            batch_checkpoint_enabled=True,
        )
        issue = make_issue()

        # Initial state
        from amelia.core.state import GitSnapshot
        git_snapshot = GitSnapshot(
            head_commit="abc123",
            dirty_files=(),
            stash_ref=None,
        )
        initial_state = make_execution_state(
            issue=issue,
            profile=profile,
            execution_plan=None,
            git_snapshot_before_batch=git_snapshot if expect_revert else None,
        )

        # Create mock architect
        mock_architect = AsyncMock()
        mock_architect.generate_execution_plan = AsyncMock(return_value=(plan, None))

        # Create mock developer
        if expect_cascade_skips:
            # Custom developer for skip test with 3 calls
            mock_developer = AsyncMock()
            call_count = [0]

            async def developer_side_effect(*args: Any, **kwargs: Any) -> dict[str, Any]:
                call_num = call_count[0]
                call_count[0] += 1

                if call_num == 0:
                    # First call: Complete batch 1
                    batch_result = BatchResult(
                        batch_number=1,
                        status="complete",
                        completed_steps=(
                            StepResult(step_id="step-1", status="completed", output="ok"),
                        ),
                        blocker=None,
                    )
                    return {
                        "developer_status": DeveloperStatus.BATCH_COMPLETE,
                        "current_batch_index": 1,
                        "batch_results": [batch_result],
                    }
                elif call_num == 1:
                    # Second call: Block on step-a in batch 2
                    return {
                        "developer_status": DeveloperStatus.BLOCKED,
                        "current_blocker": blocker,
                    }
                else:
                    # Third call (after resolution): ALL_DONE
                    return {
                        "developer_status": DeveloperStatus.ALL_DONE,
                        "current_batch_index": 2,
                    }

            mock_developer.run = AsyncMock(side_effect=developer_side_effect)
        elif resolution == "fix_instruction":
            # Custom developer for fix test
            mock_developer = AsyncMock()
            call_count = [0]

            async def developer_side_effect(*args: Any, **kwargs: Any) -> dict[str, Any]:
                call_num = call_count[0]
                call_count[0] += 1

                if call_num == 0:
                    # First call: Block
                    return {
                        "developer_status": DeveloperStatus.BLOCKED,
                        "current_blocker": blocker,
                    }
                else:
                    # Second call (after fix): ALL_DONE
                    batch_result = BatchResult(
                        batch_number=1,
                        status="complete",
                        completed_steps=(
                            StepResult(step_id="step-1", status="completed", output="Feature created"),
                        ),
                        blocker=None,
                    )
                    return {
                        "developer_status": DeveloperStatus.ALL_DONE,
                        "current_batch_index": 1,
                        "batch_results": [batch_result],
                    }

            mock_developer.run = AsyncMock(side_effect=developer_side_effect)
        else:
            # For abort_revert: use standard developer that blocks at batch 1
            mock_developer = create_batch_completing_developer(
                plan,
                blocker_at_batch=blocker_at_batch,
                blocker_report=blocker,
            )

        # Create mock reviewer if needed
        mock_reviewer = create_mock_reviewer(approved=True) if expect_review else None

        # Mock revert function
        mock_revert = AsyncMock()

        from tests.integration.conftest import make_config
        config = cast(RunnableConfig, make_config(
            thread_id=f"test-blocker-{resolution}",
            profile=profile,
            execution_mode="server",
        ))

        with mock_agents_context(mock_architect, mock_developer, mock_reviewer), \
             patch("amelia.core.orchestrator.revert_to_git_snapshot", mock_revert):

            # Run until first interrupt (human_approval_node)
            chunks, interrupt = await run_until_interrupt(orchestrator_graph, initial_state.model_dump(), config)
            assert interrupt is not None

            # Approve initial plan
            await approve_at_interrupt(orchestrator_graph, config)

            # For multi-batch scenarios, approve batch 1
            if expect_revert or expect_cascade_skips:
                chunks, interrupt = await run_until_interrupt(orchestrator_graph, None, config)
                assert interrupt is not None
                await approve_at_interrupt(orchestrator_graph, config)

            # Run until blocker_resolution_node
            chunks, interrupt = await run_until_interrupt(orchestrator_graph, None, config)
            assert interrupt is not None

            # Verify we're at blocker_resolution_node
            state_after_block = await orchestrator_graph.aget_state(config)
            assert state_after_block.values.get("current_blocker") is not None

            # Resolve blocker
            resolution_instruction = resolution if resolution in ("skip", "abort_revert") else "create the missing config.yaml file"
            await resolve_blocker(orchestrator_graph, config, resolution_instruction)

            # Run to completion
            chunks, interrupt = await run_until_interrupt(orchestrator_graph, None, config)

            # Get final state
            final_state = await orchestrator_graph.aget_state(config)
            state_values = final_state.values

            # Assertions
            if expect_revert:
                mock_revert.assert_called_once()
                assert_workflow_status(state_values, "aborted")
                assert final_state.next == (), "Workflow should have no next nodes after abort"
            else:
                assert state_values.get("current_blocker") is None

            if expect_cascade_skips:
                assert_step_skipped(state_values, "step-a", "Blocked step should be skipped")
                assert_step_skipped(state_values, "step-b", "Dependent step should be cascade-skipped")

            if expect_review:
                last_review = state_values.get("last_review")
                assert last_review is not None, "Should have last_review populated (workflow reached reviewer)"
                assert last_review.approved is True

            if resolution == "fix_instruction":
                skipped_step_ids = state_values.get("skipped_step_ids", set())
                assert "step-1" not in skipped_step_ids, "step-1 should NOT be skipped (fix succeeded)"
                assert state_values.get("blocker_resolution") is None, "blocker_resolution should be cleared"
                batch_results = state_values.get("batch_results", [])
                assert len(batch_results) == 1, f"Expected 1 batch result, got {len(batch_results)}"
                assert batch_results[0].status == "complete"


class TestTrustLevelBehavior:
    """Tests for trust level effects on batch checkpoint behavior."""

    async def test_autonomous_skips_low_risk_checkpoint(self, orchestrator_graph: CompiledStateGraph[Any]) -> None:
        """Test that AUTONOMOUS trust level auto-approves low-risk batches.

        Scenario:
        1. Create plan: batch 1 (low-risk), batch 2 (high-risk)
        2. Run with AUTONOMOUS trust level
        3. Verify: batch 1 auto-approved (no interrupt), batch 2 interrupts

        Assertions:
        - Only 1 interrupt occurs (for high-risk batch 2)
        - Batch 1 has implicit approval (auto-approved, no BatchApproval record needed)
        - Batch 2 requires explicit approval
        """
        # Create a 2-batch plan with explicit risk levels
        batch1 = make_batch(
            batch_number=1,
            steps=(make_step(id="step-1", risk_level="low"),),
            risk_summary="low",
        )
        batch2 = make_batch(
            batch_number=2,
            steps=(make_step(id="step-2", risk_level="high"),),
            risk_summary="high",
        )
        plan = make_plan(batches=(batch1, batch2))

        # Create profile with AUTONOMOUS trust level
        profile = make_profile(
            trust_level=TrustLevel.AUTONOMOUS,
            batch_checkpoint_enabled=True,
        )
        issue = make_issue()

        # Initial state
        initial_state = make_execution_state(
            issue=issue,
            profile=profile,
            execution_plan=None,
        )

        # Create mock developer that completes all batches
        mock_developer = create_batch_completing_developer(plan)

        # Create mock architect that returns our plan
        mock_architect = AsyncMock()
        mock_architect.generate_execution_plan = AsyncMock(return_value=(plan, None))

        # Create mock reviewer that approves
        mock_reviewer = create_mock_reviewer(approved=True)

        config = cast(RunnableConfig, {"configurable": {"thread_id": "test-autonomous", "execution_mode": "server", "profile": profile}})

        with mock_agents_context(mock_architect, mock_developer, mock_reviewer):
            # Count total interrupts for batch approval
            interrupt_count = 0

            # Run until first interrupt (human_approval_node for initial plan approval)
            chunks, interrupt = await run_until_interrupt(orchestrator_graph, initial_state.model_dump(), config)
            assert interrupt is not None, "Should interrupt at human_approval_node"

            # Approve initial plan
            await approve_at_interrupt(orchestrator_graph, config)

            # Run until next interrupt - batch 1 is low-risk so should be auto-approved
            # Next interrupt should be for batch 2 (high-risk)
            chunks, interrupt = await run_until_interrupt(orchestrator_graph, None, config)

            # Check if we hit an interrupt - this should be batch 2 approval
            if interrupt is not None:
                interrupt_count += 1
                # This should be the batch_approval_node for batch 2
                await approve_at_interrupt(orchestrator_graph, config)

            # Run to completion
            chunks, interrupt = await run_until_interrupt(orchestrator_graph, None, config)

            # Get final state
            final_state = await orchestrator_graph.aget_state(config)
            state_values = final_state.values

            # Assertions
            # Should have only 1 interrupt for batch approval (batch 2 - high risk)
            assert interrupt_count == 1, f"Expected 1 batch approval interrupt, got {interrupt_count}"

            # Should have 1 batch approval in state (only for batch 2 - high risk)
            # Batch 1 (low risk) was auto-approved and doesn't create a BatchApproval record
            # Note: batch_number in BatchApproval is the current_batch_index (1), which is
            # the index of the batch being approved for execution (batch 2 at index 1)
            batch_approvals = state_values.get("batch_approvals", [])
            assert len(batch_approvals) == 1, f"Expected 1 batch approval (for high-risk batch), got {len(batch_approvals)}"
            assert batch_approvals[0].batch_number == 1  # Index of batch 2
            assert batch_approvals[0].approved is True

            # Should have batch results from both batches
            batch_results = state_values.get("batch_results", [])
            assert len(batch_results) == 2, f"Expected 2 batch results, got {len(batch_results)}"

            # Should have a review result
            last_review = state_values.get("last_review")
            assert last_review is not None, "Should have last_review populated"
            assert last_review.approved is True
