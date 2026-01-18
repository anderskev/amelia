"""Review pipeline routing functions.

This module contains routing functions specific to the review pipeline
that determine transitions between nodes in the review-fix workflow.
"""

from langgraph.graph import END
from loguru import logger

from amelia.pipelines.implementation.state import ImplementationState


def route_after_evaluation(state: ImplementationState) -> str:
    """Route after evaluation node.

    If auto_approve is set, skip to developer.
    Otherwise, go to human approval.

    Args:
        state: Current execution state with auto_approve flag.

    Returns:
        "developer_node" if auto_approve is set, otherwise "review_approval_node".
    """
    if state.auto_approve:
        return "developer_node"
    return "review_approval_node"


def route_after_fixes(state: ImplementationState) -> str:
    """Route after developer fixes.

    Check if there are still critical/major items to fix.
    If auto_approve, loop back for another review pass.
    Otherwise, go to end approval.

    Args:
        state: Current execution state with review_pass and evaluation_result.

    Returns:
        "reviewer_node" to loop back, "end_approval_node" for human approval, or END.
    """
    max_passes = state.max_review_passes

    if state.review_pass >= max_passes:
        logger.warning(
            "Max review passes reached",
            review_pass=state.review_pass,
            max_passes=max_passes,
        )
        return END

    if state.auto_approve:
        if state.evaluation_result and state.evaluation_result.items_to_implement:
            return "reviewer_node"
        return END

    return "end_approval_node"


def route_after_end_approval(state: ImplementationState) -> str:
    """Route after end approval.

    If human approves, end. Otherwise, loop back to reviewer.

    Args:
        state: Current execution state with human_approved flag.

    Returns:
        END if human approved, otherwise "reviewer_node".
    """
    if state.human_approved:
        return END
    return "reviewer_node"
