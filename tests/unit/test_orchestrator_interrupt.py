"""Tests for create_orchestrator_graph interrupt configuration."""

from unittest.mock import MagicMock, patch

import pytest

from amelia.core.orchestrator import create_orchestrator_graph


class TestCreateOrchestratorGraphInterrupt:
    """Test interrupt_before parameter handling."""

    def test_graph_accepts_interrupt_before_parameter(self):
        """create_orchestrator_graph accepts interrupt_before parameter."""
        # Should not raise
        graph = create_orchestrator_graph(interrupt_before=["human_approval_node"])
        assert graph is not None

    def test_graph_without_interrupt_before_defaults_to_none(self):
        """Graph created without interrupt_before has no interrupts configured."""
        graph = create_orchestrator_graph()
        # Graph should still be valid
        assert graph is not None

    @patch("amelia.core.orchestrator.StateGraph")
    def test_interrupt_before_passed_to_compile(self, mock_state_graph_class):
        """interrupt_before is passed through to graph.compile()."""
        mock_workflow = MagicMock()
        mock_state_graph_class.return_value = mock_workflow
        mock_workflow.compile = MagicMock(return_value=MagicMock())

        create_orchestrator_graph(
            checkpoint_saver=MagicMock(),
            interrupt_before=["human_approval_node"],
        )

        mock_workflow.compile.assert_called_once()
        call_kwargs = mock_workflow.compile.call_args[1]
        assert call_kwargs.get("interrupt_before") == ["human_approval_node"]
