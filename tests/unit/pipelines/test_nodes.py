"""Unit tests for shared pipeline nodes."""


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
