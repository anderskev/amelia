# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Amelia: A local agentic coding system."""

from amelia.config import load_settings
from amelia.core.orchestrator import create_orchestrator_graph
from amelia.core.state import ExecutionState
from amelia.main import app


__version__ = "0.1.0"

__all__ = [
    "app",
    "create_orchestrator_graph",
    "ExecutionState",
    "load_settings",
    "__version__",
]
