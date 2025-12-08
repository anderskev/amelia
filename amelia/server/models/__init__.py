# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Domain models for Amelia server."""

from amelia.server.models.events import EventType, WorkflowEvent
from amelia.server.models.requests import CreateWorkflowRequest, RejectRequest
from amelia.server.models.responses import (
    ActionResponse,
    CreateWorkflowResponse,
    ErrorResponse,
    TokenSummary,
    WorkflowDetailResponse,
    WorkflowListResponse,
    WorkflowSummary,
)
from amelia.server.models.state import (
    VALID_TRANSITIONS,
    InvalidStateTransitionError,
    ServerExecutionState,
    WorkflowStatus,
    validate_transition,
)
from amelia.server.models.tokens import MODEL_PRICING, TokenUsage, calculate_token_cost
from amelia.server.models.websocket import (
    BackfillCompleteMessage,
    BackfillExpiredMessage,
    ClientMessage,
    EventMessage,
    PingMessage,
    PongMessage,
    ServerMessage,
    SubscribeAllMessage,
    SubscribeMessage,
    UnsubscribeMessage,
)


__all__ = [
    # Events
    "EventType",
    "WorkflowEvent",
    # Requests
    "CreateWorkflowRequest",
    "RejectRequest",
    # Responses
    "ActionResponse",
    "CreateWorkflowResponse",
    "ErrorResponse",
    "TokenSummary",
    "WorkflowDetailResponse",
    "WorkflowListResponse",
    "WorkflowSummary",
    # State
    "WorkflowStatus",
    "ServerExecutionState",
    "VALID_TRANSITIONS",
    "InvalidStateTransitionError",
    "validate_transition",
    # Tokens
    "TokenUsage",
    "MODEL_PRICING",
    "calculate_token_cost",
    # WebSocket
    "BackfillCompleteMessage",
    "BackfillExpiredMessage",
    "ClientMessage",
    "EventMessage",
    "PingMessage",
    "PongMessage",
    "ServerMessage",
    "SubscribeAllMessage",
    "SubscribeMessage",
    "UnsubscribeMessage",
]
