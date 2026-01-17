# Pipeline Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the monolithic orchestrator into a pipeline abstraction layer with `ImplementationPipeline` and `ReviewPipeline`.

**Architecture:** Create `amelia/pipelines/` package with protocol definitions in `base.py`, registry in `registry.py`, and pipeline-specific implementations in `implementation/` and `review/` subpackages. The existing orchestrator becomes two pipelines sharing common nodes.

**Tech Stack:** Python 3.12+, Pydantic v2, LangGraph, pytest-asyncio

**Reference:** See `docs/plans/2026-01-10-pipeline-foundation-design.md` for full design context.

---

## Pull Request Structure

This implementation is split into **3 PRs** for risk isolation:

| PR | Tasks | Branch | Description |
|----|-------|--------|-------------|
| **PR 1** | 1-11 | `feat/pipeline-foundation-262` | Create all new pipeline infrastructure (additive, no breaking changes) |
| **PR 2** | 12-19 | `feat/pipeline-migration-262` | Update all callers to use new locations |
| **PR 3** | 20-21 | `feat/pipeline-cleanup-262` | Delete legacy `orchestrator.py` and `state.py` |

**Merge Strategy:**
- PR 1 can be merged independently - purely additive
- PR 2 depends on PR 1 being merged
- PR 3 depends on PR 2 being verified in CI/production

---

# PR 1: Pipeline Foundation (Tasks 1-11)

> **Branch:** `feat/pipeline-foundation-262`
> **Risk:** Low (purely additive - no changes to existing code)
> **Goal:** Create the complete `amelia/pipelines/` package with both pipelines working

---

## Task 1: Create Pipeline Base Types

**Files:**
- Create: `amelia/pipelines/__init__.py`
- Create: `amelia/pipelines/base.py`
- Test: `tests/unit/pipelines/test_base.py`

**Step 1: Create test directory and file**

```bash
mkdir -p tests/unit/pipelines
touch tests/unit/pipelines/__init__.py
```

**Step 2: Write failing tests for base types**

Create `tests/unit/pipelines/test_base.py`:

```python
"""Unit tests for pipeline base types."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from amelia.pipelines.base import (
    BasePipelineState,
    HistoryEntry,
    PipelineMetadata,
)


class TestPipelineMetadata:
    """Tests for PipelineMetadata dataclass."""

    def test_metadata_is_frozen(self) -> None:
        """PipelineMetadata should be immutable."""
        meta = PipelineMetadata(
            name="test",
            display_name="Test",
            description="A test pipeline",
        )
        with pytest.raises(AttributeError):
            meta.name = "changed"  # type: ignore[misc]

    def test_metadata_fields(self) -> None:
        """PipelineMetadata should have required fields."""
        meta = PipelineMetadata(
            name="implementation",
            display_name="Implementation",
            description="Build features",
        )
        assert meta.name == "implementation"
        assert meta.display_name == "Implementation"
        assert meta.description == "Build features"


class TestHistoryEntry:
    """Tests for HistoryEntry dataclass."""

    def test_history_entry_is_frozen(self) -> None:
        """HistoryEntry should be immutable."""
        entry = HistoryEntry(
            timestamp=datetime.now(UTC),
            agent="architect",
            message="Started planning",
        )
        with pytest.raises(AttributeError):
            entry.agent = "developer"  # type: ignore[misc]

    def test_history_entry_fields(self) -> None:
        """HistoryEntry should store timestamp, agent, and message."""
        ts = datetime.now(UTC)
        entry = HistoryEntry(timestamp=ts, agent="reviewer", message="Review complete")
        assert entry.timestamp == ts
        assert entry.agent == "reviewer"
        assert entry.message == "Review complete"


class TestBasePipelineState:
    """Tests for BasePipelineState."""

    def test_required_fields(self) -> None:
        """BasePipelineState should require identity fields."""
        with pytest.raises(ValidationError):
            BasePipelineState()  # type: ignore[call-arg]

    def test_valid_state_creation(self) -> None:
        """BasePipelineState should accept valid identity fields."""
        state = BasePipelineState(
            workflow_id="wf-123",
            pipeline_type="implementation",
            profile_id="default",
            created_at=datetime.now(UTC),
            status="pending",
        )
        assert state.workflow_id == "wf-123"
        assert state.pipeline_type == "implementation"
        assert state.status == "pending"
        assert state.history == []

    def test_status_values(self) -> None:
        """Status should only accept valid literals."""
        for status in ("pending", "running", "paused", "completed", "failed"):
            state = BasePipelineState(
                workflow_id="wf-1",
                pipeline_type="test",
                profile_id="p1",
                created_at=datetime.now(UTC),
                status=status,  # type: ignore[arg-type]
            )
            assert state.status == status

    def test_defaults(self) -> None:
        """BasePipelineState should have sensible defaults."""
        state = BasePipelineState(
            workflow_id="wf-1",
            pipeline_type="test",
            profile_id="p1",
            created_at=datetime.now(UTC),
            status="pending",
        )
        assert state.pending_user_input is False
        assert state.user_message is None
        assert state.driver_session_id is None
        assert state.final_response is None
        assert state.error is None
```

**Step 3: Run tests to verify they fail**

```bash
uv run pytest tests/unit/pipelines/test_base.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'amelia.pipelines'`

**Step 4: Create pipelines package and base module**

Create `amelia/pipelines/__init__.py`:

```python
"""Pipeline abstraction layer for Amelia workflows.

This package provides the foundational types and registry for multiple
workflow pipelines (Implementation, Review, etc.).

Exports:
    Pipeline: Protocol that all pipelines implement.
    PipelineMetadata: Immutable metadata describing a pipeline.
    BasePipelineState: Common state fields shared by all pipelines.
    HistoryEntry: Structured history entry for agent actions.
    get_pipeline: Factory function to get a pipeline by name.
    list_pipelines: List all available pipelines.
"""

from amelia.pipelines.base import (
    BasePipelineState,
    HistoryEntry,
    Pipeline,
    PipelineMetadata,
)

__all__ = [
    "BasePipelineState",
    "HistoryEntry",
    "Pipeline",
    "PipelineMetadata",
]
```

Create `amelia/pipelines/base.py`:

```python
"""Pipeline protocol and base state types.

This module defines the foundational abstractions for the pipeline system:
- PipelineMetadata: Immutable dataclass describing a pipeline
- HistoryEntry: Structured entry for agent action history
- BasePipelineState: Common fields shared across all pipelines
- Pipeline: Protocol that all workflow types implement
"""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Literal, Protocol, TypeVar

from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, ConfigDict, Field

from amelia.core.agentic_state import add


if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver


@dataclass(frozen=True)
class PipelineMetadata:
    """Immutable metadata describing a pipeline.

    Attributes:
        name: Machine-readable identifier (e.g., "implementation").
        display_name: Human-readable name (e.g., "Implementation").
        description: Brief description of the pipeline's purpose.
    """

    name: str
    display_name: str
    description: str


@dataclass(frozen=True)
class HistoryEntry:
    """Structured history entry for agent actions.

    Attributes:
        timestamp: When the action occurred.
        agent: Which agent performed the action (e.g., "architect", "developer").
        message: Description of the action.
    """

    timestamp: datetime
    agent: str
    message: str


class BasePipelineState(BaseModel):
    """Common state for all pipelines.

    This model is frozen (immutable) to support the stateless reducer pattern.
    Use model_copy(update={...}) to create modified copies.

    Attributes:
        workflow_id: Unique identifier for this workflow instance.
        pipeline_type: Type of pipeline (e.g., "implementation", "review").
        profile_id: ID of the active profile.
        created_at: When the workflow was created.
        status: Current workflow status.
        history: Append-only list of agent actions.
        pending_user_input: Whether waiting for user input.
        user_message: Message from user (e.g., approval feedback).
        driver_session_id: Session ID for driver continuity.
        final_response: Final response when workflow completes.
        error: Error message if status is 'failed'.
    """

    model_config = ConfigDict(frozen=True)

    # Identity (immutable, self-describing for serialization)
    workflow_id: str
    pipeline_type: str
    profile_id: str
    created_at: datetime

    # Lifecycle
    status: Literal["pending", "running", "paused", "completed", "failed"]

    # Observability (append-only via reducer)
    history: Annotated[list[HistoryEntry], add] = Field(default_factory=list)

    # Human interaction
    pending_user_input: bool = False
    user_message: str | None = None

    # Agentic execution
    driver_session_id: str | None = None
    final_response: str | None = None
    error: str | None = None


StateT = TypeVar("StateT", bound=BasePipelineState)


class Pipeline(Protocol[StateT]):
    """Protocol that all pipelines must implement.

    Each pipeline provides:
    - Metadata describing the pipeline
    - A factory method to create the LangGraph state machine
    - A factory method to create initial state
    - Access to the state class for type information
    """

    @property
    def metadata(self) -> PipelineMetadata:
        """Return metadata describing this pipeline."""
        ...

    def create_graph(
        self,
        checkpointer: "BaseCheckpointSaver | None" = None,
    ) -> CompiledStateGraph:
        """Create and compile the LangGraph state machine."""
        ...

    def get_initial_state(self, **kwargs: object) -> StateT:
        """Create initial state for a new workflow."""
        ...

    def get_state_class(self) -> type[StateT]:
        """Return the state class used by this pipeline."""
        ...
```

**Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/unit/pipelines/test_base.py -v
```

**Step 6: Run linting and type checking**

```bash
uv run ruff check amelia/pipelines tests/unit/pipelines
uv run mypy amelia/pipelines
```

**Step 7: Commit**

```bash
git add amelia/pipelines tests/unit/pipelines
git commit -m "feat(pipelines): add base types - PipelineMetadata, HistoryEntry, BasePipelineState, Pipeline protocol"
```

---

## Task 2: Add Design Type to Core Types

**Files:**
- Modify: `amelia/core/types.py`
- Test: `tests/unit/core/test_types.py` (create if needed)

**Step 1: Write failing test for Design type**

Create or update `tests/unit/core/test_types.py`:

```python
"""Tests for Design type."""

from pathlib import Path

import pytest

from amelia.core.types import Design


class TestDesign:
    """Tests for Design model."""

    def test_design_creation(self) -> None:
        """Design should store content and source."""
        design = Design(content="# My Design\n\nDetails here.", source="import")
        assert design.content == "# My Design\n\nDetails here."
        assert design.source == "import"

    def test_design_default_source(self) -> None:
        """Design should default source to 'import'."""
        design = Design(content="content")
        assert design.source == "import"

    def test_design_from_file(self, tmp_path: Path) -> None:
        """Design.from_file should load markdown content."""
        design_file = tmp_path / "design.md"
        design_file.write_text("# Design from file\n\nLoaded.", encoding="utf-8")

        design = Design.from_file(design_file)
        assert design.content == "# Design from file\n\nLoaded."
        assert design.source == "file"

    def test_design_from_file_str_path(self, tmp_path: Path) -> None:
        """Design.from_file should accept string paths."""
        design_file = tmp_path / "design.md"
        design_file.write_text("content", encoding="utf-8")

        design = Design.from_file(str(design_file))
        assert design.content == "content"
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/unit/core/test_types.py::TestDesign -v
```

**Step 3: Add Design class to types.py**

Add to `amelia/core/types.py`:

```python
class Design(BaseModel):
    """Design document for implementation.

    Can be user-provided via import or generated by a future Brainstorming pipeline.

    Attributes:
        content: The markdown content of the design document.
        source: Where the design came from ("import", "brainstorming", "file").
    """

    content: str
    source: str = "import"

    @classmethod
    def from_file(cls, path: Path | str) -> "Design":
        """Load design from markdown file."""
        content = Path(path).read_text(encoding="utf-8")
        return cls(content=content, source="file")
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/unit/core/test_types.py::TestDesign -v
```

**Step 5: Commit**

```bash
git add amelia/core/types.py tests/unit/core/test_types.py
git commit -m "feat(core): add Design type for design documents"
```

---

## Task 3: Create ImplementationState

**Files:**
- Create: `amelia/pipelines/implementation/__init__.py`
- Create: `amelia/pipelines/implementation/state.py`
- Test: `tests/unit/pipelines/implementation/test_state.py`

**Step 1: Create test directory**

```bash
mkdir -p tests/unit/pipelines/implementation
touch tests/unit/pipelines/implementation/__init__.py
```

**Step 2: Write failing tests for ImplementationState**

Create `tests/unit/pipelines/implementation/test_state.py`:

```python
"""Unit tests for ImplementationState."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from amelia.core.types import Design, Issue
from amelia.pipelines.base import BasePipelineState
from amelia.pipelines.implementation.state import ImplementationState


class TestImplementationState:
    """Tests for ImplementationState model."""

    def test_inherits_from_base(self) -> None:
        """ImplementationState should inherit from BasePipelineState."""
        assert issubclass(ImplementationState, BasePipelineState)

    def test_pipeline_type_is_implementation(self) -> None:
        """ImplementationState should have pipeline_type='implementation'."""
        state = ImplementationState(
            workflow_id="wf-1",
            profile_id="default",
            created_at=datetime.now(UTC),
            status="pending",
        )
        assert state.pipeline_type == "implementation"

    def test_required_fields_inherited(self) -> None:
        """Should require workflow_id, profile_id, created_at, status."""
        with pytest.raises(ValidationError):
            ImplementationState()  # type: ignore[call-arg]

    def test_optional_domain_fields(self) -> None:
        """Should have optional domain fields with defaults."""
        state = ImplementationState(
            workflow_id="wf-1",
            profile_id="default",
            created_at=datetime.now(UTC),
            status="pending",
        )
        assert state.issue is None
        assert state.design is None
        assert state.goal is None
        assert state.plan_markdown is None
        assert state.key_files == []

    def test_with_issue(self) -> None:
        """Should accept Issue object."""
        issue = Issue(id="ISSUE-123", title="Test", body="Description")
        state = ImplementationState(
            workflow_id="wf-1",
            profile_id="default",
            created_at=datetime.now(UTC),
            status="running",
            issue=issue,
        )
        assert state.issue == issue

    def test_with_design(self) -> None:
        """Should accept Design object."""
        design = Design(content="# Design doc", source="file")
        state = ImplementationState(
            workflow_id="wf-1",
            profile_id="default",
            created_at=datetime.now(UTC),
            status="running",
            design=design,
        )
        assert state.design == design

    def test_task_tracking_fields(self) -> None:
        """Should have multi-task execution tracking fields."""
        state = ImplementationState(
            workflow_id="wf-1",
            profile_id="default",
            created_at=datetime.now(UTC),
            status="running",
            total_tasks=5,
            current_task_index=2,
            task_review_iteration=1,
        )
        assert state.total_tasks == 5
        assert state.current_task_index == 2
        assert state.task_review_iteration == 1

    def test_state_is_frozen(self) -> None:
        """ImplementationState should be immutable."""
        state = ImplementationState(
            workflow_id="wf-1",
            profile_id="default",
            created_at=datetime.now(UTC),
            status="pending",
        )
        with pytest.raises(ValidationError):
            state.status = "running"  # type: ignore[misc]
```

**Step 3: Run tests to verify they fail**

```bash
uv run pytest tests/unit/pipelines/implementation/test_state.py -v
```

**Step 4: Create implementation subpackage**

Create `amelia/pipelines/implementation/__init__.py`:

```python
"""Implementation pipeline for building features from issues.

This pipeline implements the Architect → Developer ↔ Reviewer flow.
"""

from amelia.pipelines.implementation.state import ImplementationState

__all__ = ["ImplementationState"]
```

Create `amelia/pipelines/implementation/state.py`:

```python
"""State model for the Implementation pipeline.

This module defines ImplementationState, which extends BasePipelineState with
fields specific to the implementation workflow (Architect → Developer ↔ Reviewer).
"""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import Field

from amelia.core.types import Design, Issue
from amelia.pipelines.base import BasePipelineState


if TYPE_CHECKING:
    from amelia.agents.evaluator import EvaluationResult
    from amelia.agents.reviewer import StructuredReviewResult
    from amelia.core.state import ReviewResult


class ImplementationState(BasePipelineState):
    """State for the implementation pipeline.

    Extends BasePipelineState with implementation-specific fields for:
    - Domain data (issue, design, plan)
    - Human approval workflow
    - Code review tracking
    - Multi-task execution
    """

    # Override pipeline_type with literal
    pipeline_type: Literal["implementation"] = "implementation"

    # Domain data (from planning phase)
    issue: Issue | None = None
    design: Design | None = None
    goal: str | None = None
    base_commit: str | None = None
    plan_markdown: str | None = None
    raw_architect_output: str | None = None
    plan_path: Path | None = None
    key_files: list[str] = Field(default_factory=list)

    # Human approval (plan review)
    human_approved: bool | None = None
    human_feedback: str | None = None

    # Code review tracking
    last_review: "ReviewResult | None" = None
    code_changes_for_review: str | None = None

    # Review iteration tracking
    review_iteration: int = 0

    # Task-based execution (multi-task plans)
    total_tasks: int | None = None
    current_task_index: int = 0
    task_review_iteration: int = 0

    # Structured review workflow
    structured_review: "StructuredReviewResult | None" = None
    evaluation_result: "EvaluationResult | None" = None
    approved_items: list[int] = Field(default_factory=list)
    auto_approve: bool = False
    review_pass: int = 0
    max_review_passes: int = 3
```

**Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/unit/pipelines/implementation/test_state.py -v
```

**Step 6: Commit**

```bash
git add amelia/pipelines/implementation tests/unit/pipelines/implementation
git commit -m "feat(pipelines): add ImplementationState extending BasePipelineState"
```

---

## Task 4: Create Pipeline Utilities

**Files:**
- Create: `amelia/pipelines/utils.py`
- Test: `tests/unit/pipelines/test_utils.py`

**Step 1: Write failing tests**

Create `tests/unit/pipelines/test_utils.py`:

```python
"""Unit tests for pipeline utilities."""

from unittest.mock import MagicMock

import pytest

from amelia.core.types import Profile
from amelia.pipelines.utils import extract_config_params


class TestExtractConfigParams:
    """Tests for extract_config_params utility."""

    def test_extracts_all_params(self) -> None:
        """Should extract event_bus, workflow_id, and profile from config."""
        mock_event_bus = MagicMock()
        mock_profile = MagicMock(spec=Profile)

        config = {
            "configurable": {
                "event_bus": mock_event_bus,
                "workflow_id": "wf-123",
                "profile": mock_profile,
            }
        }

        event_bus, workflow_id, profile = extract_config_params(config)

        assert event_bus is mock_event_bus
        assert workflow_id == "wf-123"
        assert profile is mock_profile

    def test_event_bus_optional(self) -> None:
        """Event bus should be optional (returns None if missing)."""
        mock_profile = MagicMock(spec=Profile)

        config = {
            "configurable": {
                "workflow_id": "wf-456",
                "profile": mock_profile,
            }
        }

        event_bus, workflow_id, profile = extract_config_params(config)

        assert event_bus is None
        assert workflow_id == "wf-456"

    def test_raises_on_missing_workflow_id(self) -> None:
        """Should raise KeyError if workflow_id is missing."""
        config = {"configurable": {"profile": MagicMock()}}

        with pytest.raises(KeyError):
            extract_config_params(config)

    def test_raises_on_missing_profile(self) -> None:
        """Should raise KeyError if profile is missing."""
        config = {"configurable": {"workflow_id": "wf-1"}}

        with pytest.raises(KeyError):
            extract_config_params(config)
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/pipelines/test_utils.py -v
```

**Step 3: Create utils.py**

Create `amelia/pipelines/utils.py`:

```python
"""Shared utilities for pipeline infrastructure.

This module contains helper functions used across multiple pipelines
for LangGraph configuration handling and token tracking.
"""

from typing import TYPE_CHECKING, Any

from langgraph.types import RunnableConfig

from amelia.core.types import Profile


if TYPE_CHECKING:
    from amelia.server.events.bus import EventBus


def extract_config_params(
    config: RunnableConfig | dict[str, Any],
) -> tuple["EventBus | None", str, Profile]:
    """Extract common parameters from LangGraph config.

    Args:
        config: LangGraph RunnableConfig containing configurable dict.

    Returns:
        Tuple of (event_bus, workflow_id, profile).
        event_bus may be None if not running in server mode.

    Raises:
        KeyError: If workflow_id or profile is missing from config.
    """
    configurable = config.get("configurable", {})

    event_bus = configurable.get("event_bus")
    workflow_id = configurable["workflow_id"]
    profile = configurable["profile"]

    return event_bus, workflow_id, profile
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/unit/pipelines/test_utils.py -v
```

**Step 5: Commit**

```bash
git add amelia/pipelines/utils.py tests/unit/pipelines/test_utils.py
git commit -m "feat(pipelines): add extract_config_params utility"
```

---

## Task 5: Create Core Extraction Utility

**Files:**
- Create: `amelia/core/extraction.py`
- Test: `tests/unit/core/test_extraction.py`

**Step 1: Write failing tests**

Create `tests/unit/core/test_extraction.py`:

```python
"""Unit tests for extraction utilities."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from amelia.core.extraction import extract_structured


class TestSchema(BaseModel):
    """Test schema for extraction."""

    goal: str
    priority: int


class TestExtractStructured:
    """Tests for extract_structured function."""

    @pytest.mark.asyncio
    async def test_extracts_structured_output(self) -> None:
        """Should extract structured data from prompt using LLM."""
        with patch("amelia.core.extraction.DriverFactory") as mock_factory:
            mock_driver = MagicMock()
            mock_driver.extract_structured = AsyncMock(
                return_value=TestSchema(goal="Build feature", priority=1)
            )
            mock_factory.create.return_value = mock_driver

            result = await extract_structured(
                prompt="Extract from this text",
                schema=TestSchema,
                model="gpt-4",
                driver_type="api:openrouter",
            )

            assert result.goal == "Build feature"
            assert result.priority == 1
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/core/test_extraction.py -v
```

**Step 3: Create extraction.py**

Create `amelia/core/extraction.py`:

```python
"""Generic LLM extraction utilities.

This module provides utilities for extracting structured data from text
using LLM calls. These are general-purpose helpers not tied to any
specific pipeline.
"""

from typing import TypeVar

from pydantic import BaseModel

from amelia.drivers.factory import DriverFactory


T = TypeVar("T", bound=BaseModel)


async def extract_structured(
    prompt: str,
    schema: type[T],
    model: str,
    driver_type: str,
) -> T:
    """Extract structured output from text using direct model call.

    Args:
        prompt: The prompt containing text to extract from.
        schema: Pydantic model class defining the expected structure.
        model: Model identifier to use for extraction.
        driver_type: Driver type string (e.g., "api:openrouter").

    Returns:
        Instance of schema populated with extracted data.
    """
    driver = DriverFactory.create(
        driver_type=driver_type,
        model=model,
        working_dir=".",
    )

    return await driver.extract_structured(prompt=prompt, schema=schema)
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/unit/core/test_extraction.py -v
```

**Step 5: Commit**

```bash
git add amelia/core/extraction.py tests/unit/core/test_extraction.py
git commit -m "feat(core): add extract_structured utility for LLM-based extraction"
```

---

## Task 6: Create Pipeline Registry (Stub)

**Files:**
- Create: `amelia/pipelines/registry.py`
- Test: `tests/unit/pipelines/test_registry.py`

**Step 1: Write tests (will pass after Task 11)**

Create `tests/unit/pipelines/test_registry.py`:

```python
"""Unit tests for pipeline registry."""

import pytest

from amelia.pipelines.registry import get_pipeline, list_pipelines, PIPELINES


class TestPipelineRegistry:
    """Tests for pipeline registry functions."""

    def test_pipelines_dict_has_implementation(self) -> None:
        """PIPELINES should include 'implementation' key."""
        assert "implementation" in PIPELINES

    def test_pipelines_dict_has_review(self) -> None:
        """PIPELINES should include 'review' key."""
        assert "review" in PIPELINES

    def test_get_pipeline_implementation(self) -> None:
        """get_pipeline should return ImplementationPipeline for 'implementation'."""
        pipeline = get_pipeline("implementation")
        assert pipeline.metadata.name == "implementation"

    def test_get_pipeline_review(self) -> None:
        """get_pipeline should return ReviewPipeline for 'review'."""
        pipeline = get_pipeline("review")
        assert pipeline.metadata.name == "review"

    def test_get_pipeline_unknown_raises(self) -> None:
        """get_pipeline should raise ValueError for unknown pipeline."""
        with pytest.raises(ValueError, match="Unknown pipeline: nonexistent"):
            get_pipeline("nonexistent")

    def test_get_pipeline_returns_fresh_instances(self) -> None:
        """Each get_pipeline call should return a new instance."""
        p1 = get_pipeline("implementation")
        p2 = get_pipeline("implementation")
        assert p1 is not p2

    def test_list_pipelines_returns_list(self) -> None:
        """list_pipelines should return list of pipeline info dicts."""
        pipelines = list_pipelines()
        assert isinstance(pipelines, list)
        assert len(pipelines) >= 2

    def test_list_pipelines_contains_required_fields(self) -> None:
        """Each pipeline info should have name, display_name, description."""
        pipelines = list_pipelines()
        for p in pipelines:
            assert "name" in p
            assert "display_name" in p
            assert "description" in p
```

**Step 2: Create registry stub**

Create `amelia/pipelines/registry.py`:

```python
"""Pipeline registry for routing to pipeline implementations.

This module provides the central registry for all available pipelines
and factory functions to instantiate them.
"""

from amelia.pipelines.base import Pipeline


# Registry mapping pipeline names to their classes
# Will be populated after pipeline implementations exist (Task 11)
PIPELINES: dict[str, type[Pipeline]] = {}


def get_pipeline(name: str) -> Pipeline:
    """Get a pipeline instance by name.

    Creates a fresh instance on each call (stateless factories).

    Args:
        name: Pipeline name (e.g., "implementation", "review").

    Returns:
        Pipeline instance ready for use.

    Raises:
        ValueError: If pipeline name is not registered.
    """
    if name not in PIPELINES:
        raise ValueError(f"Unknown pipeline: {name}")
    return PIPELINES[name]()


def list_pipelines() -> list[dict[str, str]]:
    """List all available pipelines with metadata.

    Returns:
        List of dicts with name, display_name, and description.
    """
    return [
        {
            "name": p.metadata.name,
            "display_name": p.metadata.display_name,
            "description": p.metadata.description,
        }
        for p in (cls() for cls in PIPELINES.values())
    ]
```

**Step 3: Commit stub (tests will pass after Task 11)**

```bash
git add amelia/pipelines/registry.py tests/unit/pipelines/test_registry.py
git commit -m "feat(pipelines): add registry stub (awaiting pipeline implementations)"
```

---

## Task 7: Extract Shared Node Functions

**Files:**
- Create: `amelia/pipelines/nodes.py`
- Test: `tests/unit/pipelines/test_nodes.py`

Extract `call_developer_node` and `call_reviewer_node` from `amelia/core/orchestrator.py`.

**Step 1: Write import tests**

Create `tests/unit/pipelines/test_nodes.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/pipelines/test_nodes.py -v
```

**Step 3: Create nodes.py**

Create `amelia/pipelines/nodes.py` by extracting `call_developer_node` and `call_reviewer_node` from `amelia/core/orchestrator.py` (lines ~580-750). Update imports to use `amelia.pipelines.utils.extract_config_params`.

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/unit/pipelines/test_nodes.py -v
```

**Step 5: Commit**

```bash
git add amelia/pipelines/nodes.py tests/unit/pipelines/test_nodes.py
git commit -m "feat(pipelines): extract shared nodes - call_developer_node, call_reviewer_node"
```

---

## Task 8: Extract Shared Routing Functions

**Files:**
- Create: `amelia/pipelines/routing.py`
- Test: `tests/unit/pipelines/test_routing.py`

Extract `route_after_review_or_task` from `amelia/core/orchestrator.py`.

**Step 1: Write tests**

Create `tests/unit/pipelines/test_routing.py`:

```python
"""Unit tests for shared routing functions."""

from datetime import UTC, datetime

import pytest

from amelia.core.state import ReviewResult
from amelia.pipelines.implementation.state import ImplementationState


class TestRouteAfterReviewOrTask:
    """Tests for route_after_review_or_task function."""

    def _make_state(self, **kwargs) -> ImplementationState:
        """Create test state with defaults."""
        defaults = {
            "workflow_id": "wf-1",
            "profile_id": "default",
            "created_at": datetime.now(UTC),
            "status": "running",
        }
        defaults.update(kwargs)
        return ImplementationState(**defaults)

    def test_legacy_mode_approved_returns_end(self) -> None:
        """In legacy mode (no total_tasks), approved review goes to __end__."""
        from amelia.pipelines.routing import route_after_review_or_task

        state = self._make_state(
            total_tasks=None,
            last_review=ReviewResult(
                reviewer_persona="test",
                approved=True,
                comments=[],
                severity="low",
            ),
        )
        assert route_after_review_or_task(state) == "__end__"

    def test_legacy_mode_rejected_returns_developer(self) -> None:
        """In legacy mode, rejected review loops back to developer."""
        from amelia.pipelines.routing import route_after_review_or_task

        state = self._make_state(
            total_tasks=None,
            last_review=ReviewResult(
                reviewer_persona="test",
                approved=False,
                comments=["Fix this"],
                severity="medium",
            ),
        )
        assert route_after_review_or_task(state) == "developer"

    def test_task_mode_approved_more_tasks_returns_next_task(self) -> None:
        """In task mode with more tasks, approved goes to next_task_node."""
        from amelia.pipelines.routing import route_after_review_or_task

        state = self._make_state(
            total_tasks=3,
            current_task_index=0,
            last_review=ReviewResult(
                reviewer_persona="test",
                approved=True,
                comments=[],
                severity="low",
            ),
        )
        assert route_after_review_or_task(state) == "next_task_node"

    def test_task_mode_approved_last_task_returns_end(self) -> None:
        """In task mode on last task, approved goes to __end__."""
        from amelia.pipelines.routing import route_after_review_or_task

        state = self._make_state(
            total_tasks=3,
            current_task_index=2,
            last_review=ReviewResult(
                reviewer_persona="test",
                approved=True,
                comments=[],
                severity="low",
            ),
        )
        assert route_after_review_or_task(state) == "__end__"
```

**Step 2: Create routing.py**

Create `amelia/pipelines/routing.py` by extracting `route_after_review_or_task` from orchestrator.

**Step 3: Run tests and commit**

```bash
uv run pytest tests/unit/pipelines/test_routing.py -v
git add amelia/pipelines/routing.py tests/unit/pipelines/test_routing.py
git commit -m "feat(pipelines): add shared routing - route_after_review_or_task"
```

---

## Task 9: Create ImplementationPipeline

**Files:**
- Create: `amelia/pipelines/implementation/pipeline.py`
- Create: `amelia/pipelines/implementation/graph.py`
- Create: `amelia/pipelines/implementation/nodes.py`
- Create: `amelia/pipelines/implementation/routing.py`
- Create: `amelia/pipelines/implementation/utils.py`
- Test: `tests/unit/pipelines/implementation/test_pipeline.py`

This is a large task - extract implementation-specific nodes, routing, and create the pipeline class.

**Step 1: Write tests for ImplementationPipeline**

Create `tests/unit/pipelines/implementation/test_pipeline.py`:

```python
"""Unit tests for ImplementationPipeline."""

import pytest

from amelia.pipelines.base import PipelineMetadata
from amelia.pipelines.implementation.pipeline import ImplementationPipeline
from amelia.pipelines.implementation.state import ImplementationState


class TestImplementationPipelineProtocol:
    """Tests that ImplementationPipeline satisfies Pipeline protocol."""

    def test_has_metadata_property(self) -> None:
        """Should have metadata property returning PipelineMetadata."""
        pipeline = ImplementationPipeline()
        meta = pipeline.metadata
        assert isinstance(meta, PipelineMetadata)

    def test_metadata_name_is_implementation(self) -> None:
        """Metadata name should be 'implementation'."""
        pipeline = ImplementationPipeline()
        assert pipeline.metadata.name == "implementation"

    def test_has_create_graph_method(self) -> None:
        """Should have create_graph method."""
        pipeline = ImplementationPipeline()
        assert hasattr(pipeline, "create_graph")
        assert callable(pipeline.create_graph)

    def test_get_state_class_returns_implementation_state(self) -> None:
        """Should return ImplementationState class."""
        pipeline = ImplementationPipeline()
        assert pipeline.get_state_class() is ImplementationState

    def test_creates_valid_initial_state(self) -> None:
        """Should create a valid ImplementationState."""
        pipeline = ImplementationPipeline()
        state = pipeline.get_initial_state(
            workflow_id="wf-test",
            profile_id="default",
        )
        assert isinstance(state, ImplementationState)
        assert state.workflow_id == "wf-test"
        assert state.status == "pending"

    def test_creates_compiled_graph(self) -> None:
        """Should return a compiled LangGraph."""
        pipeline = ImplementationPipeline()
        graph = pipeline.create_graph()
        assert hasattr(graph, "nodes")
```

**Step 2: Extract from orchestrator.py**

Extract the following from `amelia/core/orchestrator.py`:
- `call_architect_node` → `amelia/pipelines/implementation/nodes.py`
- `plan_validator_node` → `amelia/pipelines/implementation/nodes.py`
- `human_approval_node` → `amelia/pipelines/implementation/nodes.py`
- `next_task_node` → `amelia/pipelines/implementation/nodes.py`
- `route_approval` → `amelia/pipelines/implementation/routing.py`
- `extract_task_count`, `extract_task_section`, `commit_task_changes` → `amelia/pipelines/implementation/utils.py`
- `create_orchestrator_graph` → `amelia/pipelines/implementation/graph.py` (renamed to `create_implementation_graph`)

Create `amelia/pipelines/implementation/pipeline.py` with `ImplementationPipeline` class.

**Step 3: Update implementation/__init__.py**

```python
"""Implementation pipeline for building features from issues."""

from amelia.pipelines.implementation.graph import create_implementation_graph
from amelia.pipelines.implementation.pipeline import ImplementationPipeline
from amelia.pipelines.implementation.state import ImplementationState

__all__ = [
    "create_implementation_graph",
    "ImplementationPipeline",
    "ImplementationState",
]
```

**Step 4: Run tests and commit**

```bash
uv run pytest tests/unit/pipelines/implementation -v
git add amelia/pipelines/implementation
git commit -m "feat(pipelines): add ImplementationPipeline with graph, nodes, routing, utils"
```

---

## Task 10: Create ReviewPipeline

**Files:**
- Create: `amelia/pipelines/review/__init__.py`
- Create: `amelia/pipelines/review/pipeline.py`
- Create: `amelia/pipelines/review/graph.py`
- Create: `amelia/pipelines/review/nodes.py`
- Create: `amelia/pipelines/review/routing.py`
- Test: `tests/unit/pipelines/review/test_pipeline.py`

**Step 1: Create test directory**

```bash
mkdir -p tests/unit/pipelines/review
touch tests/unit/pipelines/review/__init__.py
```

**Step 2: Write tests**

Create `tests/unit/pipelines/review/test_pipeline.py`:

```python
"""Unit tests for ReviewPipeline."""

import pytest

from amelia.pipelines.base import PipelineMetadata
from amelia.pipelines.implementation.state import ImplementationState
from amelia.pipelines.review.pipeline import ReviewPipeline


class TestReviewPipelineProtocol:
    """Tests that ReviewPipeline satisfies Pipeline protocol."""

    def test_metadata_name_is_review(self) -> None:
        """Metadata name should be 'review'."""
        pipeline = ReviewPipeline()
        assert pipeline.metadata.name == "review"

    def test_get_state_class_returns_implementation_state(self) -> None:
        """Should return ImplementationState (shared state)."""
        pipeline = ReviewPipeline()
        assert pipeline.get_state_class() is ImplementationState

    def test_creates_compiled_graph(self) -> None:
        """Should return a compiled LangGraph."""
        pipeline = ReviewPipeline()
        graph = pipeline.create_graph()
        assert hasattr(graph, "nodes")

    def test_graph_has_reviewer_node(self) -> None:
        """Graph should have reviewer node."""
        pipeline = ReviewPipeline()
        graph = pipeline.create_graph()
        assert "reviewer_node" in graph.nodes
```

**Step 3: Extract from orchestrator.py**

Extract the following from `amelia/core/orchestrator.py`:
- `call_evaluation_node` → `amelia/pipelines/review/nodes.py`
- `review_approval_node` → `amelia/pipelines/review/nodes.py`
- `route_after_evaluation`, `route_after_fixes`, `route_after_end_approval` → `amelia/pipelines/review/routing.py`
- `create_review_graph` → `amelia/pipelines/review/graph.py`

Create `amelia/pipelines/review/pipeline.py` with `ReviewPipeline` class.

**Step 4: Run tests and commit**

```bash
uv run pytest tests/unit/pipelines/review -v
git add amelia/pipelines/review tests/unit/pipelines/review
git commit -m "feat(pipelines): add ReviewPipeline with graph, nodes, routing"
```

---

## Task 11: Complete Pipeline Registry

**Files:**
- Modify: `amelia/pipelines/registry.py`
- Modify: `amelia/pipelines/__init__.py`

**Step 1: Update registry with pipeline imports**

Update `amelia/pipelines/registry.py`:

```python
"""Pipeline registry for routing to pipeline implementations."""

from amelia.pipelines.base import Pipeline
from amelia.pipelines.implementation.pipeline import ImplementationPipeline
from amelia.pipelines.review.pipeline import ReviewPipeline


PIPELINES: dict[str, type[Pipeline]] = {
    "implementation": ImplementationPipeline,
    "review": ReviewPipeline,
}


def get_pipeline(name: str) -> Pipeline:
    """Get a pipeline instance by name."""
    if name not in PIPELINES:
        raise ValueError(f"Unknown pipeline: {name}")
    return PIPELINES[name]()


def list_pipelines() -> list[dict[str, str]]:
    """List all available pipelines with metadata."""
    return [
        {
            "name": p.metadata.name,
            "display_name": p.metadata.display_name,
            "description": p.metadata.description,
        }
        for p in (cls() for cls in PIPELINES.values())
    ]
```

**Step 2: Update pipelines __init__.py**

Add `get_pipeline` and `list_pipelines` to exports.

**Step 3: Run registry tests**

```bash
uv run pytest tests/unit/pipelines/test_registry.py -v
```

**Step 4: Commit**

```bash
git add amelia/pipelines/registry.py amelia/pipelines/__init__.py
git commit -m "feat(pipelines): complete registry with Implementation and Review pipelines"
```

---

## PR 1 Completion

**Run full test suite for PR 1:**

```bash
uv run pytest tests/unit/pipelines -v
uv run ruff check amelia/pipelines tests/unit/pipelines
uv run mypy amelia/pipelines
```

**Create PR:**

```bash
git push -u origin feat/pipeline-foundation-262
gh pr create --title "feat(pipelines): add pipeline abstraction layer" --body "$(cat <<'EOF'
## Summary

- Add Pipeline protocol and BasePipelineState base types
- Add PipelineMetadata dataclass and HistoryEntry for observability
- Create ImplementationPipeline with Architect → Developer ↔ Reviewer flow
- Create ReviewPipeline with Reviewer → Evaluator → Developer cycle
- Add pipeline registry with get_pipeline() and list_pipelines()
- Add Design type for future brainstorming pipeline
- Add extract_structured utility for LLM-based extraction

## Test plan

- [ ] All new unit tests pass: `uv run pytest tests/unit/pipelines -v`
- [ ] Type checking passes: `uv run mypy amelia/pipelines`
- [ ] Linting passes: `uv run ruff check amelia/pipelines`
- [ ] Existing tests still pass (no changes to existing code)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

# PR 2: Migration (Tasks 12-19)

> **Branch:** `feat/pipeline-migration-262` (created from main after PR 1 merges)
> **Risk:** Medium (changes imports throughout codebase)
> **Goal:** Update all callers to use new pipeline locations

---

## Task 12: Move Domain Types to Core

**Files:**
- Modify: `amelia/core/types.py`
- Modify: `amelia/core/state.py`

Move `ReviewResult` and `Severity` from `amelia/core/state.py` to `amelia/core/types.py` (domain types used by agents).

**Step 1: Copy types to core/types.py**

**Step 2: Update state.py to import from types**

**Step 3: Update all imports in agents and tests**

**Step 4: Run tests and commit**

```bash
uv run pytest tests -v
git add amelia/core amelia/agents tests
git commit -m "refactor(core): move ReviewResult and Severity to types.py"
```

---

## Task 13: Update Public API Exports

**Files:**
- Modify: `amelia/__init__.py`

Update exports to use new locations:

```python
from amelia.pipelines import get_pipeline
from amelia.pipelines.implementation import (
    ImplementationState,
    create_implementation_graph,
)

# Backward compatibility alias (temporary)
ExecutionState = ImplementationState
```

**Commit:**

```bash
git add amelia/__init__.py
git commit -m "refactor(api): update public exports to pipeline locations"
```

---

## Task 14: Update Server Service

**Files:**
- Modify: `amelia/server/orchestrator/service.py`
- Modify: `amelia/server/models/state.py`

**Step 1: Update imports to use pipelines**

**Step 2: Update _create_server_graph to use get_pipeline**

**Step 3: Fix approve_workflow to use correct graph based on pipeline_type**

**Step 4: Run integration tests**

```bash
uv run pytest tests/integration -v
git add amelia/server
git commit -m "refactor(server): update service to use pipeline abstraction"
```

---

## Task 15: Update Agent Imports

**Files:**
- Modify: `amelia/agents/architect.py`
- Modify: `amelia/agents/developer.py`
- Modify: `amelia/agents/reviewer.py`
- Modify: `amelia/agents/evaluator.py`

Replace `from amelia.core.state import ExecutionState` with `from amelia.pipelines.implementation.state import ImplementationState`.

```bash
uv run pytest tests/unit/agents -v
git add amelia/agents
git commit -m "refactor(agents): update to use ImplementationState from pipelines"
```

---

## Task 16: Update CLI

**Files:**
- Modify: `amelia/client/cli.py`

Update imports.

```bash
uv run pytest tests/unit/client tests/integration/test_cli_agentic.py -v
git add amelia/client
git commit -m "refactor(cli): update to use ImplementationState"
```

---

## Task 17: Update Test Fixtures

**Files:**
- Modify: `tests/conftest.py`
- Modify: `tests/integration/conftest.py`

Update state factory fixtures.

```bash
uv run pytest tests -v
git add tests/conftest.py tests/integration/conftest.py
git commit -m "test: update fixtures to use ImplementationState"
```

---

## Task 18: Update Unit Tests

**Files:**
- Modify: `tests/unit/test_orchestrator_graph.py`
- Modify: `tests/unit/core/test_*.py`

Update imports and patch strings.

```bash
uv run pytest tests/unit -v
git add tests/unit
git commit -m "test: update unit tests for pipeline locations"
```

---

## Task 19: Update Integration Tests

**Files:**
- Modify: `tests/integration/test_*.py`

Update imports and patch strings.

```bash
uv run pytest tests/integration -v
git add tests/integration
git commit -m "test: update integration tests for pipeline locations"
```

---

## PR 2 Completion

**Run full test suite:**

```bash
uv run pytest tests -v
uv run ruff check amelia tests
uv run mypy amelia
```

**Manual CLI verification:**

```bash
uv run amelia --help
uv run amelia start --help
uv run amelia review --help
```

**Create PR:**

```bash
git push -u origin feat/pipeline-migration-262
gh pr create --title "refactor: migrate callers to pipeline abstraction" --body "$(cat <<'EOF'
## Summary

- Move ReviewResult and Severity to core/types.py
- Update public API exports to use pipeline locations
- Update server service to use get_pipeline()
- Update all agents to use ImplementationState
- Update CLI to use new imports
- Update all test imports and patch strings

## Test plan

- [ ] All tests pass: `uv run pytest tests -v`
- [ ] CLI commands work: `uv run amelia --help`
- [ ] Type checking passes: `uv run mypy amelia`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

# PR 3: Cleanup (Tasks 20-21)

> **Branch:** `feat/pipeline-cleanup-262` (created from main after PR 2 merges)
> **Risk:** Low (after verification)
> **Goal:** Delete legacy files

---

## Task 20: Delete Old Files

**Files:**
- Delete: `amelia/core/orchestrator.py`
- Delete: `amelia/core/state.py`

**Step 1: Verify no remaining imports**

```bash
grep -r "from amelia.core.orchestrator" amelia tests
grep -r "from amelia.core.state" amelia tests
```

If any remain, fix them first.

**Step 2: Run full test suite**

```bash
uv run pytest tests -v
```

**Step 3: Delete old files**

```bash
rm amelia/core/orchestrator.py
rm amelia/core/state.py
```

**Step 4: Run tests again**

```bash
uv run pytest tests -v
uv run ruff check amelia tests
uv run mypy amelia
```

**Step 5: Commit**

```bash
git add -A
git commit -m "refactor: remove legacy orchestrator.py and state.py"
```

---

## Task 21: Final Verification

**Step 1: Run full test suite**

```bash
uv run pytest tests -v
```

**Step 2: Run linting and type checking**

```bash
uv run ruff check amelia tests
uv run mypy amelia
```

**Step 3: Manual CLI verification**

```bash
uv run amelia --help
uv run amelia start --help
uv run amelia review --help
```

**Step 4: Create summary commit if needed**

---

## PR 3 Completion

**Create PR:**

```bash
git push -u origin feat/pipeline-cleanup-262
gh pr create --title "refactor: remove legacy orchestrator files" --body "$(cat <<'EOF'
## Summary

- Delete `amelia/core/orchestrator.py` (moved to `amelia/pipelines/`)
- Delete `amelia/core/state.py` (moved to `amelia/pipelines/implementation/state.py`)

## Test plan

- [ ] All tests pass: `uv run pytest tests -v`
- [ ] No remaining imports from deleted files
- [ ] CLI commands work

Closes #262

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Summary

| PR | Tasks | Commits | Risk |
|----|-------|---------|------|
| **PR 1: Foundation** | 1-11 | ~11 commits | Low (additive) |
| **PR 2: Migration** | 12-19 | ~8 commits | Medium (import changes) |
| **PR 3: Cleanup** | 20-21 | ~2 commits | Low (deletion) |

Each PR can be reviewed and merged independently, with PR 2 depending on PR 1 and PR 3 depending on PR 2.
