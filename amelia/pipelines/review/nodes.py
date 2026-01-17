"""Review pipeline specific node functions.

This module contains node functions specific to the review pipeline
that evaluate review feedback and handle human approval.
"""

from typing import Any

from langchain_core.runnables.config import RunnableConfig
from loguru import logger

from amelia.agents.evaluator import Evaluator
from amelia.core.state import ExecutionState
from amelia.drivers.factory import DriverFactory
from amelia.pipelines.nodes import _save_token_usage
from amelia.pipelines.utils import extract_config_params


async def call_evaluation_node(
    state: ExecutionState,
    config: RunnableConfig | None = None,
) -> dict[str, Any]:
    """Node that evaluates review feedback.

    Calls the Evaluator agent to process review results and
    apply the decision matrix for each item.

    Args:
        state: Current execution state containing the review feedback.
        config: Optional RunnableConfig with stream_emitter in configurable.

    Returns:
        Partial state dict with evaluation_result, approved_items, and driver_session_id.
    """
    event_bus, workflow_id, profile = extract_config_params(config or {})

    config = config or {}
    configurable = config.get("configurable", {})
    prompts = configurable.get("prompts", {})
    repository = configurable.get("repository")

    driver = DriverFactory.get_driver(profile.driver, model=profile.model)
    evaluator = Evaluator(driver=driver, event_bus=event_bus, prompts=prompts)

    evaluation_result, new_session_id = await evaluator.evaluate(
        state, profile, workflow_id=workflow_id
    )

    await _save_token_usage(driver, workflow_id, "evaluator", repository)

    approved_items: list[int] = []
    if state.auto_approve:
        approved_items = [item.number for item in evaluation_result.items_to_implement]

    logger.info(
        "Agent action completed",
        agent="evaluator",
        action="evaluation_completed",
        details={
            "items_to_implement": len(evaluation_result.items_to_implement),
            "items_rejected": len(evaluation_result.items_rejected),
            "items_deferred": len(evaluation_result.items_deferred),
            "auto_approved_count": len(approved_items),
        },
    )

    return {
        "evaluation_result": evaluation_result,
        "approved_items": approved_items,
        "driver_session_id": new_session_id,
    }


async def review_approval_node(
    state: ExecutionState,
    config: RunnableConfig | None = None,
) -> dict[str, Any]:
    """Node for human approval of which review items to fix.

    In server mode, this interrupts for human input via LangGraph interrupt.
    In CLI mode, this currently auto-approves all items (interactive prompts not yet implemented).

    Args:
        state: Current execution state containing the evaluation result.
        config: Optional RunnableConfig with execution_mode in configurable.

    Returns:
        Empty dict (approval handled via LangGraph interrupt in server mode,
        auto-approved in CLI mode).
    """
    config = config or {}
    execution_mode = config.get("configurable", {}).get("execution_mode", "cli")

    if execution_mode == "server":
        return {}

    # CLI mode: auto-approve all items marked for implementation
    # TODO: Implement interactive prompts using typer.confirm
    return {}
