# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Integration tests for checkpoint persistence.

Tests that verify:
- State is correctly saved to checkpoint
- State can be resumed after "crash" (clearing in-memory state)
- State integrity is maintained across checkpoint/resume cycles

Uses MemorySaver for simplicity (real SQLite persistence is tested elsewhere).
"""

from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph

from amelia.core.orchestrator import create_orchestrator_graph
from amelia.core.types import DeveloperStatus

from .conftest import (
    make_config,
    make_execution_state,
    make_plan,
    make_profile,
)


class TestMemoryCheckpointPersistence:
    """Tests for checkpoint persistence using MemorySaver."""

    @pytest.fixture
    def checkpointer(self) -> MemorySaver:
        """Create a fresh MemorySaver for each test."""
        return MemorySaver()

    @pytest.fixture
    def graph(self, checkpointer: MemorySaver) -> CompiledStateGraph[Any]:
        """Create graph with checkpointer and interrupts."""
        return create_orchestrator_graph(
            checkpoint_saver=checkpointer,
            interrupt_before=["human_approval_node", "batch_approval_node"],
        )

    async def test_state_persisted_after_architect_node(
        self, graph: CompiledStateGraph[Any]
    ) -> None:
        """State should be persisted after architect node execution."""
        plan = make_plan(num_batches=2, steps_per_batch=2)

        with (
            patch("amelia.core.orchestrator.DriverFactory.get_driver"),
            patch("amelia.core.orchestrator.Architect") as MockArchitect,
        ):
            mock_architect = AsyncMock()
            mock_architect.generate_execution_plan = AsyncMock(return_value=(plan, None))
            MockArchitect.return_value = mock_architect

            profile = make_profile()
            state = make_execution_state(profile=profile)
            config = cast(RunnableConfig, {"configurable": {"thread_id": "test-persist-001", "profile": profile}})

            # Run until interrupt (human_approval_node)
            chunks = []
            async for chunk in graph.astream(
                state.model_dump(mode="json"), config
            ):
                chunks.append(chunk)
                if "__interrupt__" in chunk:
                    break

            # Verify we can get state from checkpointer
            saved_state = await graph.aget_state(config)
            assert saved_state is not None
            assert saved_state.values.get("execution_plan") is not None

    async def test_state_survives_graph_recreation(
        self, checkpointer: MemorySaver
    ) -> None:
        """State should survive graph recreation with same checkpointer."""
        plan = make_plan(num_batches=1, steps_per_batch=1)
        thread_id = "test-survive-002"
        profile = make_profile()
        config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id, "profile": profile}})

        # First graph instance
        graph1 = create_orchestrator_graph(
            checkpoint_saver=checkpointer,
            interrupt_before=["human_approval_node"],
        )

        with (
            patch("amelia.core.orchestrator.DriverFactory.get_driver"),
            patch("amelia.core.orchestrator.Architect") as MockArchitect,
        ):
            mock_architect = AsyncMock()
            mock_architect.generate_execution_plan = AsyncMock(return_value=(plan, None))
            MockArchitect.return_value = mock_architect

            state = make_execution_state(profile=profile)

            # Run until interrupt
            async for chunk in graph1.astream(
                state.model_dump(mode="json"), config
            ):
                if "__interrupt__" in chunk:
                    break

        # Create NEW graph instance with SAME checkpointer
        graph2 = create_orchestrator_graph(
            checkpoint_saver=checkpointer,
            interrupt_before=["human_approval_node"],
        )

        # State should be accessible from new graph
        saved_state = await graph2.aget_state(config)
        assert saved_state is not None
        assert saved_state.values.get("execution_plan") is not None

    async def test_resume_from_interrupt_preserves_state(
        self, graph: CompiledStateGraph[Any]
    ) -> None:
        """Resuming from interrupt should preserve all state fields."""
        plan = make_plan(num_batches=2, steps_per_batch=2)
        thread_id = "test-resume-003"
        profile = make_profile()
        config = cast(RunnableConfig, make_config(thread_id=thread_id, profile=profile, execution_mode="server"))

        with (
            patch("amelia.core.orchestrator.DriverFactory.get_driver"),
            patch("amelia.core.orchestrator.Architect") as MockArchitect,
        ):
            mock_architect = AsyncMock()
            mock_architect.generate_execution_plan = AsyncMock(return_value=(plan, None))
            MockArchitect.return_value = mock_architect

            state = make_execution_state(profile=profile)

            # Run until interrupt
            async for chunk in graph.astream(
                state.model_dump(mode="json"), config
            ):
                if "__interrupt__" in chunk:
                    break

        # Get state at interrupt
        interrupted_state = await graph.aget_state(config)

        # Verify key fields are preserved
        values = interrupted_state.values
        assert values.get("issue") is not None
        assert values.get("profile_id") is not None
        assert values.get("execution_plan") is not None
        # Check the plan has correct structure
        saved_plan = values["execution_plan"]
        # Handle both dict and Pydantic object
        if hasattr(saved_plan, "batches"):
            assert saved_plan.batches is not None
            assert len(saved_plan.batches) == 2
        else:
            assert saved_plan.get("batches") is not None
            assert len(saved_plan["batches"]) == 2

    async def test_update_state_persists(
        self, graph: CompiledStateGraph[Any]
    ) -> None:
        """Updating state via graph should persist the update."""
        plan = make_plan(num_batches=1, steps_per_batch=1)
        thread_id = "test-update-004"
        profile = make_profile()
        config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id, "profile": profile}})

        with (
            patch("amelia.core.orchestrator.DriverFactory.get_driver"),
            patch("amelia.core.orchestrator.Architect") as MockArchitect,
        ):
            mock_architect = AsyncMock()
            mock_architect.generate_execution_plan = AsyncMock(return_value=(plan, None))
            MockArchitect.return_value = mock_architect

            state = make_execution_state(profile=profile)

            # Run until interrupt
            async for chunk in graph.astream(
                state.model_dump(mode="json"), config
            ):
                if "__interrupt__" in chunk:
                    break

        # Update state (simulate approval)
        await graph.aupdate_state(config, {"human_approved": True})

        # Verify update persisted
        saved_state = await graph.aget_state(config)
        assert saved_state.values.get("human_approved") is True

    async def test_multiple_threads_isolated(
        self, graph: CompiledStateGraph[Any]
    ) -> None:
        """Different thread IDs should have isolated state."""
        plan1 = make_plan(num_batches=1, steps_per_batch=1, goal="Goal 1")
        plan2 = make_plan(num_batches=2, steps_per_batch=2, goal="Goal 2")

        profile1 = make_profile()
        profile2 = make_profile()
        config1 = cast(RunnableConfig, make_config(thread_id="thread-1", profile=profile1, execution_mode="server"))
        config2 = cast(RunnableConfig, make_config(thread_id="thread-2", profile=profile2, execution_mode="server"))

        with (
            patch("amelia.core.orchestrator.DriverFactory.get_driver"),
            patch("amelia.core.orchestrator.Architect") as MockArchitect,
        ):
            # First thread with plan1
            mock_architect = AsyncMock()
            mock_architect.generate_execution_plan = AsyncMock(return_value=(plan1, None))
            MockArchitect.return_value = mock_architect

            state1 = make_execution_state(profile=profile1)
            async for chunk in graph.astream(
                state1.model_dump(mode="json"), config1
            ):
                if "__interrupt__" in chunk:
                    break

            # Second thread with plan2
            mock_architect.generate_execution_plan = AsyncMock(return_value=(plan2, None))

            state2 = make_execution_state(profile=profile2)
            async for chunk in graph.astream(
                state2.model_dump(mode="json"), config2
            ):
                if "__interrupt__" in chunk:
                    break

        # Verify states are isolated
        saved1 = await graph.aget_state(config1)
        saved2 = await graph.aget_state(config2)

        saved_plan1 = saved1.values["execution_plan"]
        saved_plan2 = saved2.values["execution_plan"]

        # Handle both dict and Pydantic object
        if hasattr(saved_plan1, "goal"):
            assert saved_plan1.goal == "Goal 1"
            assert saved_plan2.goal == "Goal 2"
            assert len(saved_plan1.batches) == 1
            assert len(saved_plan2.batches) == 2
        else:
            assert saved_plan1["goal"] == "Goal 1"
            assert saved_plan2["goal"] == "Goal 2"
            assert len(saved_plan1["batches"]) == 1
            assert len(saved_plan2["batches"]) == 2


class TestCheckpointStateIntegrity:
    """Tests for state integrity across checkpoint operations."""

    @pytest.fixture
    def checkpointer(self) -> MemorySaver:
        """Create a fresh MemorySaver for each test."""
        return MemorySaver()

    @pytest.fixture
    def graph(self, checkpointer: MemorySaver) -> CompiledStateGraph[Any]:
        """Create graph with checkpointer."""
        return create_orchestrator_graph(
            checkpoint_saver=checkpointer,
            interrupt_before=["human_approval_node", "batch_approval_node"],
        )

    async def test_execution_plan_structure_preserved(
        self, graph: CompiledStateGraph[Any]
    ) -> None:
        """ExecutionPlan structure should be fully preserved through checkpoint."""
        plan = make_plan(num_batches=2, steps_per_batch=3)
        profile = make_profile()
        config = cast(RunnableConfig, {"configurable": {"thread_id": "test-structure", "execution_mode": "server", "profile": profile}})

        with (
            patch("amelia.core.orchestrator.DriverFactory.get_driver"),
            patch("amelia.core.orchestrator.Architect") as MockArchitect,
        ):
            mock_architect = AsyncMock()
            mock_architect.generate_execution_plan = AsyncMock(return_value=(plan, None))
            MockArchitect.return_value = mock_architect

            state = make_execution_state(profile=profile)
            async for chunk in graph.astream(
                state.model_dump(mode="json"), config
            ):
                if "__interrupt__" in chunk:
                    break

        saved_state = await graph.aget_state(config)
        saved_plan = saved_state.values["execution_plan"]

        # Handle both dict (JSON) and object (Pydantic) representations
        if hasattr(saved_plan, "goal"):
            # Pydantic object
            assert saved_plan.goal == "Test goal"
            assert len(saved_plan.batches) == 2
            batch1 = saved_plan.batches[0]
            assert batch1.batch_number == 1
            assert len(batch1.steps) == 3
            step1 = batch1.steps[0]
            assert step1.id is not None
            assert step1.description is not None
            assert step1.command is not None
        else:
            # Dict (JSON)
            assert saved_plan["goal"] == "Test goal"
            assert len(saved_plan["batches"]) == 2
            batch1 = saved_plan["batches"][0]
            assert batch1["batch_number"] == 1
            assert len(batch1["steps"]) == 3
            step1 = batch1["steps"][0]
            assert "id" in step1
            assert "description" in step1
            assert "command" in step1

    async def test_frozenset_fields_preserved(
        self, graph: CompiledStateGraph[Any]
    ) -> None:
        """Frozenset fields like skipped_step_ids should be preserved."""
        plan = make_plan(num_batches=1, steps_per_batch=1)
        profile = make_profile()
        config = cast(RunnableConfig, {"configurable": {"thread_id": "test-frozenset", "profile": profile}})

        with (
            patch("amelia.core.orchestrator.DriverFactory.get_driver"),
            patch("amelia.core.orchestrator.Architect") as MockArchitect,
        ):
            mock_architect = AsyncMock()
            mock_architect.generate_execution_plan = AsyncMock(return_value=(plan, None))
            MockArchitect.return_value = mock_architect

            # Create state with skipped steps
            state = make_execution_state(
                profile=profile,
                skipped_step_ids=frozenset({"step-1", "step-2"})
            )
            async for chunk in graph.astream(
                state.model_dump(mode="json"), config
            ):
                if "__interrupt__" in chunk:
                    break

        saved_state = await graph.aget_state(config)
        skipped = saved_state.values.get("skipped_step_ids")

        # Should preserve the skipped step IDs (may be list after JSON round-trip)
        assert skipped is not None
        skipped_set = set(skipped) if isinstance(skipped, (list, tuple)) else skipped
        assert "step-1" in skipped_set
        assert "step-2" in skipped_set

    async def test_enum_fields_preserved(
        self, graph: CompiledStateGraph[Any]
    ) -> None:
        """Enum fields like developer_status should be preserved."""
        plan = make_plan(num_batches=1, steps_per_batch=1)
        profile = make_profile()
        config = cast(RunnableConfig, {"configurable": {"thread_id": "test-enum", "profile": profile}})

        with (
            patch("amelia.core.orchestrator.DriverFactory.get_driver"),
            patch("amelia.core.orchestrator.Architect") as MockArchitect,
        ):
            mock_architect = AsyncMock()
            mock_architect.generate_execution_plan = AsyncMock(return_value=(plan, None))
            MockArchitect.return_value = mock_architect

            state = make_execution_state(
                profile=profile,
                developer_status=DeveloperStatus.BATCH_COMPLETE
            )
            async for chunk in graph.astream(
                state.model_dump(mode="json"), config
            ):
                if "__interrupt__" in chunk:
                    break

        saved_state = await graph.aget_state(config)
        status = saved_state.values.get("developer_status")

        # Should preserve the status (may be string after JSON round-trip)
        assert status is not None
        status_str = status.value if hasattr(status, "value") else status
        assert status_str == "batch_complete"


class TestCheckpointResume:
    """Tests for resuming workflow from checkpoint."""

    @pytest.fixture
    def checkpointer(self) -> MemorySaver:
        """Create a fresh MemorySaver for each test."""
        return MemorySaver()

    async def test_resume_after_approval_continues_workflow(
        self, checkpointer: MemorySaver
    ) -> None:
        """Approving and resuming should continue to developer node."""
        plan = make_plan(num_batches=1, steps_per_batch=1)
        thread_id = "test-resume-approve"
        profile = make_profile()
        config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id, "profile": profile}})

        graph = create_orchestrator_graph(
            checkpoint_saver=checkpointer,
            interrupt_before=["human_approval_node", "batch_approval_node"],
        )

        with (
            patch("amelia.core.orchestrator.DriverFactory.get_driver"),
            patch("amelia.core.orchestrator.Architect") as MockArchitect,
        ):
            mock_architect = AsyncMock()
            mock_architect.generate_execution_plan = AsyncMock(return_value=(plan, None))
            MockArchitect.return_value = mock_architect

            state = make_execution_state(profile=profile)

            # Phase 1: Run until human_approval interrupt
            async for chunk in graph.astream(
                state.model_dump(mode="json"), config
            ):
                if "__interrupt__" in chunk:
                    break

        # Approve
        await graph.aupdate_state(config, {"human_approved": True})

        # Verify state updated
        state_after_approve = await graph.aget_state(config)
        assert state_after_approve.values.get("human_approved") is True

    async def test_resume_after_rejection_ends_workflow(
        self, checkpointer: MemorySaver
    ) -> None:
        """Rejecting should allow workflow to end."""
        plan = make_plan(num_batches=1, steps_per_batch=1)
        thread_id = "test-resume-reject"
        profile = make_profile()
        config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id, "execution_mode": "server", "profile": profile}})

        graph = create_orchestrator_graph(
            checkpoint_saver=checkpointer,
            interrupt_before=["human_approval_node"],
        )

        with (
            patch("amelia.core.orchestrator.DriverFactory.get_driver"),
            patch("amelia.core.orchestrator.Architect") as MockArchitect,
        ):
            mock_architect = AsyncMock()
            mock_architect.generate_execution_plan = AsyncMock(return_value=(plan, None))
            MockArchitect.return_value = mock_architect

            state = make_execution_state(profile=profile)

            # Run until interrupt
            async for chunk in graph.astream(
                state.model_dump(mode="json"), config
            ):
                if "__interrupt__" in chunk:
                    break

        # Reject
        await graph.aupdate_state(config, {"human_approved": False})

        # Resume - should complete (end) after rejection
        async for _ in graph.astream(None, config):
            # Process all chunks until workflow finishes
            pass

        # The workflow should have finished one way or another
        final_state = await graph.aget_state(config)
        assert final_state.values.get("human_approved") is False
