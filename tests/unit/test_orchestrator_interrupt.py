# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Tests for create_orchestrator_graph interrupt configuration."""

from unittest.mock import MagicMock, patch

from amelia.core.orchestrator import create_orchestrator_graph


class TestCreateOrchestratorGraphInterrupt:
    """Test interrupt_before parameter handling."""

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
