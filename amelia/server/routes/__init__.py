# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""API route modules."""
from amelia.server.routes.health import router as health_router
from amelia.server.routes.websocket import router as websocket_router
from amelia.server.routes.workflows import router as workflows_router


__all__ = ["health_router", "websocket_router", "workflows_router"]
