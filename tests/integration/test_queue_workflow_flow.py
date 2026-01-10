"""Integration tests for queue workflow flow.

Tests the complete queue workflow lifecycle:
- Queue workflows without starting
- Start individual queued workflows
- Batch start multiple workflows

Uses real OrchestratorService with real WorkflowRepository (in-memory SQLite).
Only mocks at external boundaries (LangGraph checkpoint/resume).

Mock boundaries:
- AsyncSqliteSaver: Prevents actual graph execution
- create_orchestrator_graph: Returns mock graph

Real components:
- FastAPI route handlers
- OrchestratorService
- WorkflowRepository with in-memory SQLite
- Request/Response model validation
"""

import subprocess
import tempfile
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from amelia.core.state import ExecutionState
from amelia.server.database.connection import Database
from amelia.server.database.repository import WorkflowRepository
from amelia.server.dependencies import get_orchestrator, get_repository
from amelia.server.events.bus import EventBus
from amelia.server.main import create_app
from amelia.server.models.state import ServerExecutionState
from amelia.server.orchestrator.service import OrchestratorService


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def test_db(temp_db_path: Path) -> AsyncGenerator[Database, None]:
    """Create and initialize in-memory SQLite database."""
    db = Database(temp_db_path)
    await db.connect()
    await db.ensure_schema()
    yield db
    await db.close()


@pytest.fixture
def test_repository(test_db: Database) -> WorkflowRepository:
    """Create repository backed by test database."""
    return WorkflowRepository(test_db)


@pytest.fixture
def test_event_bus() -> EventBus:
    """Create event bus for testing."""
    return EventBus()


@pytest.fixture
def temp_checkpoint_db(tmp_path: Path) -> str:
    """Create temporary checkpoint database path."""
    return str(tmp_path / "checkpoints.db")


@pytest.fixture
def test_orchestrator(
    test_event_bus: EventBus,
    test_repository: WorkflowRepository,
    temp_checkpoint_db: str,
) -> OrchestratorService:
    """Create real OrchestratorService with test dependencies."""
    return OrchestratorService(
        event_bus=test_event_bus,
        repository=test_repository,
        checkpoint_path=temp_checkpoint_db,
    )


@pytest.fixture
def test_client(
    test_orchestrator: OrchestratorService,
    test_repository: WorkflowRepository,
) -> TestClient:
    """Create test client with real dependencies."""
    app = create_app()

    # Create a no-op lifespan that doesn't initialize database/orchestrator
    @asynccontextmanager
    async def noop_lifespan(_app: Any) -> AsyncGenerator[None, None]:
        yield

    app.router.lifespan_context = noop_lifespan
    app.dependency_overrides[get_orchestrator] = lambda: test_orchestrator
    app.dependency_overrides[get_repository] = lambda: test_repository

    return TestClient(app)


def init_git_repo(path: Path) -> Path:
    """Initialize a git repo with initial commit for testing.

    Creates a minimal git repository with user config and an initial commit,
    suitable for tests that require git operations.

    Args:
        path: Directory to initialize as git repo.

    Returns:
        Path to the initialized git repository.
    """
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"],
        cwd=path,
        capture_output=True,
        check=True,
    )
    (path / "README.md").write_text("# Test")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial"],
        cwd=path,
        capture_output=True,
        check=True,
    )
    return path


async def create_pending_workflow(
    repository: WorkflowRepository,
    workflow_id: str = "wf-001",
    issue_id: str = "TEST-001",
    worktree_path: str = "/tmp/test-repo",
    profile_id: str = "test",
) -> ServerExecutionState:
    """Create and persist a pending workflow for testing.

    Args:
        repository: Repository to persist to.
        workflow_id: Workflow ID.
        issue_id: Issue ID.
        worktree_path: Worktree path.
        profile_id: Profile ID for execution state.

    Returns:
        Created ServerExecutionState in pending status.
    """
    execution_state = ExecutionState(profile_id=profile_id)
    workflow = ServerExecutionState(
        id=workflow_id,
        issue_id=issue_id,
        worktree_path=worktree_path,
        worktree_name=worktree_path.split("/")[-1],
        workflow_status="pending",
        started_at=datetime.now(UTC),
        execution_state=execution_state,
    )
    await repository.create(workflow)
    return workflow


# =============================================================================
# Test Classes
# =============================================================================


@pytest.mark.integration
class TestQueueWorkflowCreation:
    """Tests for creating workflows in queued (pending) state."""

    async def test_create_workflow_with_start_false_queues_without_starting(
        self,
        test_client: TestClient,
        test_repository: WorkflowRepository,
    ) -> None:
        """Creating workflow with start=False creates it in pending state."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            resolved_path = str(Path(tmp_dir).resolve())

            response = test_client.post(
                "/api/workflows",
                json={
                    "issue_id": "TEST-QUEUE-001",
                    "worktree_path": resolved_path,
                    "start": False,
                },
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert "id" in data
            workflow_id = data["id"]

            # Verify workflow was created in pending state
            workflow = await test_repository.get(workflow_id)
            assert workflow is not None
            assert workflow.workflow_status == "pending"
            assert workflow.issue_id == "TEST-QUEUE-001"

    async def test_create_workflow_defaults_to_immediate_start(
        self,
        test_client: TestClient,
        test_repository: WorkflowRepository,
        mock_settings: MagicMock,
        langgraph_mock_factory: Any,
        tmp_path: Path,
    ) -> None:
        """Creating workflow without start param defaults to start=True."""
        # Initialize a git repo (required for worktree validation)
        git_dir = tmp_path / "git-repo"
        git_dir.mkdir()
        init_git_repo(git_dir)
        resolved_path = str(git_dir.resolve())

        # Mock LangGraph to prevent actual graph execution
        mocks = langgraph_mock_factory(astream_items=[])
        with (
            patch(
                "amelia.server.orchestrator.service.AsyncSqliteSaver"
            ) as mock_saver_class,
            patch(
                "amelia.server.orchestrator.service.create_orchestrator_graph"
            ) as mock_create_graph,
            patch.object(
                OrchestratorService,
                "_load_settings_for_worktree",
                return_value=mock_settings,
            ),
        ):
            mock_create_graph.return_value = mocks.graph
            mock_saver_class.from_conn_string.return_value = (
                mocks.saver_class.from_conn_string.return_value
            )

            response = test_client.post(
                "/api/workflows",
                json={
                    "issue_id": "TEST-IMMEDIATE-001",
                    "worktree_path": resolved_path,
                    # No start param - defaults to True
                },
            )

        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.integration
class TestStartPendingWorkflow:
    """Tests for POST /api/workflows/{id}/start endpoint."""

    async def test_start_pending_workflow_returns_202(
        self,
        test_client: TestClient,
        test_repository: WorkflowRepository,
        mock_settings: MagicMock,
        langgraph_mock_factory: Any,
    ) -> None:
        """Starting a pending workflow returns 202 Accepted."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            resolved_path = str(Path(tmp_dir).resolve())

            # Create pending workflow
            await create_pending_workflow(
                test_repository,
                workflow_id="wf-pending-start",
                issue_id="TEST-START",
                worktree_path=resolved_path,
            )

            # Mock LangGraph to prevent actual graph execution
            mocks = langgraph_mock_factory(astream_items=[])
            with (
                patch(
                    "amelia.server.orchestrator.service.AsyncSqliteSaver"
                ) as mock_saver_class,
                patch(
                    "amelia.server.orchestrator.service.create_orchestrator_graph"
                ) as mock_create_graph,
                patch.object(
                    OrchestratorService,
                    "_load_settings_for_worktree",
                    return_value=mock_settings,
                ),
            ):
                mock_create_graph.return_value = mocks.graph
                mock_saver_class.from_conn_string.return_value = (
                    mocks.saver_class.from_conn_string.return_value
                )

                response = test_client.post("/api/workflows/wf-pending-start/start")

            assert response.status_code == status.HTTP_202_ACCEPTED
            data = response.json()
            assert data["workflow_id"] == "wf-pending-start"
            assert data["status"] == "started"

    async def test_start_nonexistent_workflow_returns_404(
        self,
        test_client: TestClient,
    ) -> None:
        """Starting a non-existent workflow returns 404."""
        response = test_client.post("/api/workflows/wf-ghost/start")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_start_already_running_workflow_returns_409(
        self,
        test_client: TestClient,
        test_repository: WorkflowRepository,
    ) -> None:
        """Starting a workflow that's not pending returns 409."""
        # Create workflow in in_progress state
        execution_state = ExecutionState(profile_id="test")
        workflow = ServerExecutionState(
            id="wf-running",
            issue_id="TEST-RUNNING",
            worktree_path="/tmp/running",
            worktree_name="running",
            workflow_status="in_progress",
            started_at=datetime.now(UTC),
            execution_state=execution_state,
        )
        await test_repository.create(workflow)

        response = test_client.post("/api/workflows/wf-running/start")

        assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.integration
class TestBatchStartWorkflows:
    """Tests for POST /api/workflows/start-batch endpoint."""

    async def test_batch_start_all_pending_workflows(
        self,
        test_client: TestClient,
        test_repository: WorkflowRepository,
        mock_settings: MagicMock,
        langgraph_mock_factory: Any,
    ) -> None:
        """Batch start with no filters starts all pending workflows."""
        # Create pending workflows in different temp directories to avoid conflicts
        with tempfile.TemporaryDirectory() as tmp_dir1, \
             tempfile.TemporaryDirectory() as tmp_dir2:
            path1 = str(Path(tmp_dir1).resolve())
            path2 = str(Path(tmp_dir2).resolve())

            await create_pending_workflow(
                test_repository,
                workflow_id="wf-batch-1",
                issue_id="TEST-BATCH-1",
                worktree_path=path1,
            )
            await create_pending_workflow(
                test_repository,
                workflow_id="wf-batch-2",
                issue_id="TEST-BATCH-2",
                worktree_path=path2,
            )

            # Mock LangGraph
            mocks = langgraph_mock_factory(astream_items=[])
            with (
                patch(
                    "amelia.server.orchestrator.service.AsyncSqliteSaver"
                ) as mock_saver_class,
                patch(
                    "amelia.server.orchestrator.service.create_orchestrator_graph"
                ) as mock_create_graph,
                patch.object(
                    OrchestratorService,
                    "_load_settings_for_worktree",
                    return_value=mock_settings,
                ),
            ):
                mock_create_graph.return_value = mocks.graph
                mock_saver_class.from_conn_string.return_value = (
                    mocks.saver_class.from_conn_string.return_value
                )

                response = test_client.post(
                    "/api/workflows/start-batch",
                    json={},
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "started" in data
            assert "errors" in data
            # Both workflows should be started
            assert len(data["started"]) == 2
            assert "wf-batch-1" in data["started"]
            assert "wf-batch-2" in data["started"]
            assert data["errors"] == {}

    async def test_batch_start_specific_workflow_ids(
        self,
        test_client: TestClient,
        test_repository: WorkflowRepository,
        mock_settings: MagicMock,
        langgraph_mock_factory: Any,
    ) -> None:
        """Batch start with workflow_ids only starts specified workflows."""
        with tempfile.TemporaryDirectory() as tmp_dir1, \
             tempfile.TemporaryDirectory() as tmp_dir2, \
             tempfile.TemporaryDirectory() as tmp_dir3:
            path1 = str(Path(tmp_dir1).resolve())
            path2 = str(Path(tmp_dir2).resolve())
            path3 = str(Path(tmp_dir3).resolve())

            await create_pending_workflow(
                test_repository,
                workflow_id="wf-selected-1",
                issue_id="TEST-SEL-1",
                worktree_path=path1,
            )
            await create_pending_workflow(
                test_repository,
                workflow_id="wf-selected-2",
                issue_id="TEST-SEL-2",
                worktree_path=path2,
            )
            await create_pending_workflow(
                test_repository,
                workflow_id="wf-not-selected",
                issue_id="TEST-NOT-SEL",
                worktree_path=path3,
            )

            # Mock LangGraph
            mocks = langgraph_mock_factory(astream_items=[])
            with (
                patch(
                    "amelia.server.orchestrator.service.AsyncSqliteSaver"
                ) as mock_saver_class,
                patch(
                    "amelia.server.orchestrator.service.create_orchestrator_graph"
                ) as mock_create_graph,
                patch.object(
                    OrchestratorService,
                    "_load_settings_for_worktree",
                    return_value=mock_settings,
                ),
            ):
                mock_create_graph.return_value = mocks.graph
                mock_saver_class.from_conn_string.return_value = (
                    mocks.saver_class.from_conn_string.return_value
                )

                response = test_client.post(
                    "/api/workflows/start-batch",
                    json={"workflow_ids": ["wf-selected-1", "wf-selected-2"]},
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            # Only selected workflows should be started
            assert set(data["started"]) == {"wf-selected-1", "wf-selected-2"}

            # Verify wf-not-selected is still pending
            not_selected = await test_repository.get("wf-not-selected")
            assert not_selected is not None
            assert not_selected.workflow_status == "pending"

    async def test_batch_start_empty_result_when_no_pending(
        self,
        test_client: TestClient,
    ) -> None:
        """Batch start returns empty result when no pending workflows."""
        response = test_client.post(
            "/api/workflows/start-batch",
            json={},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["started"] == []
        assert data["errors"] == {}


@pytest.mark.integration
class TestQueueThenStartFlow:
    """Integration tests for complete queue-then-start workflow."""

    async def test_queue_then_start_workflow_flow(
        self,
        test_client: TestClient,
        test_repository: WorkflowRepository,
        mock_settings: MagicMock,
        langgraph_mock_factory: Any,
        tmp_path: Path,
    ) -> None:
        """Complete flow: create queued, verify pending, start, verify in_progress."""
        # Initialize a git repo (required for worktree validation when starting)
        git_dir = tmp_path / "git-repo"
        git_dir.mkdir()
        init_git_repo(git_dir)
        resolved_path = str(git_dir.resolve())

        # Step 1: Create workflow without starting (queue it)
        create_response = test_client.post(
            "/api/workflows",
            json={
                "issue_id": "TEST-FLOW-001",
                "worktree_path": resolved_path,
                "start": False,
            },
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        workflow_id = create_response.json()["id"]

        # Step 2: Verify it's in pending state
        get_response = test_client.get(f"/api/workflows/{workflow_id}")
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["status"] == "pending"

        # Step 3: Start the workflow
        mocks = langgraph_mock_factory(astream_items=[])
        with (
            patch(
                "amelia.server.orchestrator.service.AsyncSqliteSaver"
            ) as mock_saver_class,
            patch(
                "amelia.server.orchestrator.service.create_orchestrator_graph"
            ) as mock_create_graph,
            patch.object(
                OrchestratorService,
                "_load_settings_for_worktree",
                return_value=mock_settings,
            ),
        ):
            mock_create_graph.return_value = mocks.graph
            mock_saver_class.from_conn_string.return_value = (
                mocks.saver_class.from_conn_string.return_value
            )

            start_response = test_client.post(f"/api/workflows/{workflow_id}/start")

        assert start_response.status_code == status.HTTP_202_ACCEPTED

        # Step 4: Verify status changed to in_progress
        get_response = test_client.get(f"/api/workflows/{workflow_id}")
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["status"] == "in_progress"

    async def test_queue_workflow_after_cancelled_succeeds(
        self,
        test_client: TestClient,
        test_repository: WorkflowRepository,
        tmp_path: Path,
    ) -> None:
        """A new workflow can be queued after the previous one is cancelled.

        The system enforces one active workflow per worktree, but completed/cancelled
        workflows don't block new ones.
        """
        # Initialize a git repo
        git_dir = tmp_path / "git-repo"
        git_dir.mkdir()
        init_git_repo(git_dir)
        resolved_path = str(git_dir.resolve())

        # Create first pending workflow
        response1 = test_client.post(
            "/api/workflows",
            json={
                "issue_id": "TEST-FIRST-001",
                "worktree_path": resolved_path,
                "start": False,
            },
        )
        assert response1.status_code == status.HTTP_201_CREATED
        workflow_id = response1.json()["id"]

        # Cancel the first workflow
        cancel_response = test_client.post(f"/api/workflows/{workflow_id}/cancel")
        assert cancel_response.status_code == status.HTTP_200_OK

        # Now create a second pending workflow - should succeed since first is cancelled
        response2 = test_client.post(
            "/api/workflows",
            json={
                "issue_id": "TEST-SECOND-001",
                "worktree_path": resolved_path,
                "start": False,
            },
        )
        assert response2.status_code == status.HTTP_201_CREATED

        # Verify second workflow is pending
        workflow2 = await test_repository.get(response2.json()["id"])
        assert workflow2 is not None
        assert workflow2.workflow_status == "pending"
