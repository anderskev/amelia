from langgraph.checkpoint.memory import MemorySaver

from amelia.core.orchestrator import create_orchestrator_graph


def test_orchestrator_state_persistence() -> None:
    """
    Verifies that the orchestrator can be configured with a checkpoint saver.
    """
    # Create a MemorySaver checkpoint
    checkpoint_saver = MemorySaver()

    # Create orchestrator with checkpointing enabled
    app = create_orchestrator_graph(checkpoint_saver=checkpoint_saver)

    # Verify the graph was created successfully
    assert app is not None
