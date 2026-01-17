"""Import verification tests for shared pipeline nodes module.

These tests verify that the amelia.pipelines.nodes module correctly re-exports
node functions. Functional tests for the actual node behavior are in
tests/unit/core/test_developer_node.py and tests/unit/core/test_orchestrator_review.py.
"""


class TestCallDeveloperNodeImport:
    """Tests that call_developer_node can be imported."""

    def test_import_from_nodes(self) -> None:
        """Should be importable from amelia.pipelines.nodes."""
        from amelia.pipelines.nodes import call_developer_node

        assert callable(call_developer_node)


class TestCallReviewerNodeImport:
    """Tests that call_reviewer_node can be imported."""

    def test_import_from_nodes(self) -> None:
        """Should be importable from amelia.pipelines.nodes."""
        from amelia.pipelines.nodes import call_reviewer_node

        assert callable(call_reviewer_node)
