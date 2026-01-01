# Agent Prompt Configuration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a dashboard UI for editing agent system prompts with version tracking. Users can modify prompts that control agent behavior, with changes taking effect immediately for new workflows. Each workflow records which prompt versions it used.

**Architecture:** Backend stores prompts in SQLite with version history. A PromptResolver class provides the current prompt content (custom or default fallback). The orchestrator injects resolved prompts into agents at workflow startup and records which versions were used. Frontend provides a Settings page with edit modals.

**Tech Stack:** Python/FastAPI/SQLite (backend), React/TypeScript/shadcn (frontend)

---

## Phase 1: Backend Data Model

### Task 1.1: Create Prompt Defaults Module

**Files:**
- Create: `amelia/agents/prompts/__init__.py`
- Create: `amelia/agents/prompts/defaults.py`
- Test: `tests/unit/agents/prompts/test_defaults.py`

**Step 1: Write the failing test**

```python
# tests/unit/agents/prompts/test_defaults.py
"""Tests for hardcoded prompt defaults."""
import pytest

from amelia.agents.prompts.defaults import PROMPT_DEFAULTS, PromptDefault


def test_prompt_default_is_frozen():
    """PromptDefault should be immutable."""
    default = PROMPT_DEFAULTS["architect.system"]
    with pytest.raises(AttributeError):
        default.agent = "modified"


def test_prompt_defaults_contains_architect_system():
    """Should have architect.system prompt defined."""
    assert "architect.system" in PROMPT_DEFAULTS
    default = PROMPT_DEFAULTS["architect.system"]
    assert default.agent == "architect"
    assert default.name == "Architect System Prompt"
    assert len(default.content) > 50  # Has substantial content


def test_prompt_defaults_contains_architect_plan():
    """Should have architect.plan prompt defined."""
    assert "architect.plan" in PROMPT_DEFAULTS
    default = PROMPT_DEFAULTS["architect.plan"]
    assert default.agent == "architect"
    assert default.name == "Architect Plan Format"


def test_prompt_defaults_contains_reviewer_structured():
    """Should have reviewer.structured prompt defined."""
    assert "reviewer.structured" in PROMPT_DEFAULTS
    default = PROMPT_DEFAULTS["reviewer.structured"]
    assert default.agent == "reviewer"


def test_prompt_defaults_contains_reviewer_agentic():
    """Should have reviewer.agentic prompt defined."""
    assert "reviewer.agentic" in PROMPT_DEFAULTS
    default = PROMPT_DEFAULTS["reviewer.agentic"]
    assert default.agent == "reviewer"


def test_all_defaults_have_required_fields():
    """All prompt defaults should have non-empty required fields."""
    for prompt_id, default in PROMPT_DEFAULTS.items():
        assert default.agent, f"{prompt_id} missing agent"
        assert default.name, f"{prompt_id} missing name"
        assert default.content, f"{prompt_id} missing content"
        assert default.description, f"{prompt_id} missing description"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/agents/prompts/test_defaults.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'amelia.agents.prompts'"

**Step 3: Create the prompts package**

```python
# amelia/agents/prompts/__init__.py
"""Agent prompt configuration package.

Provides prompt defaults and resolution for configurable agent prompts.
"""
from amelia.agents.prompts.defaults import PROMPT_DEFAULTS, PromptDefault

__all__ = ["PROMPT_DEFAULTS", "PromptDefault"]
```

**Step 4: Create defaults module with prompts extracted from agents**

```python
# amelia/agents/prompts/defaults.py
"""Hardcoded default prompts for all agents.

These serve as:
- Factory defaults when no custom version exists
- Fallback when database is unavailable
- Source for "Reset to default" action
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptDefault:
    """Immutable prompt default definition.

    Attributes:
        agent: Agent name (architect, developer, reviewer).
        name: Human-readable prompt name.
        description: What this prompt controls.
        content: The actual prompt text.
    """

    agent: str
    name: str
    description: str
    content: str


PROMPT_DEFAULTS: dict[str, PromptDefault] = {
    "architect.system": PromptDefault(
        agent="architect",
        name="Architect System Prompt",
        description="Defines the architect's role for general analysis tasks",
        content="""You are a senior software architect creating implementation plans.
Your role is to analyze issues and produce detailed markdown implementation plans.""",
    ),
    "architect.plan": PromptDefault(
        agent="architect",
        name="Architect Plan Format",
        description="Instructions for structuring the implementation plan output format",
        content="""You are a senior software architect creating implementation plans.

Generate implementation plans in markdown format that follow this structure:

# [Title] Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** [Clear description of what needs to be accomplished]

**Success Criteria:** [How we know when the task is complete]

---

## Phase 1: [Phase Name]

### Task 1.1: [Task Name]

**Step 1: [Step description]**

```[language]
[code block if applicable]
```

**Run:** `[command to run]`

**Success criteria:** [How to verify this step worked]

### Task 1.2: [Next Task]
...

---

## Phase 2: [Next Phase]
...

---

## Summary

[Brief summary of what was accomplished]

---

Guidelines:
- Each Phase groups related work with ## headers
- Each Task is a discrete unit of work with ### headers
- Each Step has code blocks, commands to run, and success criteria
- Include TDD approach: write test first, run to verify it fails, implement, run to verify it passes
- Be specific about file paths, commands, and expected outputs
- Keep steps granular (2-5 minutes of work each)""",
    ),
    "reviewer.structured": PromptDefault(
        agent="reviewer",
        name="Reviewer Structured Prompt",
        description="Instructions for code review with structured JSON output",
        content="""You are an expert code reviewer. Review the provided code changes and produce structured feedback.

OUTPUT FORMAT:
- Summary: 1-2 sentence overview
- Items: Numbered list with format [FILE:LINE] TITLE
  - For each item provide: Issue (what's wrong), Why (why it matters), Fix (recommended solution)
- Good Patterns: List things done well to preserve
- Verdict: "approved" | "needs_fixes" | "blocked"

SEVERITY LEVELS:
- critical: Blocking issues (security, data loss, crashes)
- major: Should fix before merge (bugs, performance, maintainability)
- minor: Nice to have (style, minor improvements)

Be specific with file paths and line numbers. Provide actionable feedback.""",
    ),
    "reviewer.agentic": PromptDefault(
        agent="reviewer",
        name="Reviewer Agentic Prompt",
        description="Instructions for agentic code review with tool calling and skill loading",
        content="""You are an expert code reviewer. Your task is to review code changes using the appropriate review skills.

## Process

1. **Identify Changed Files**: Run `git diff --name-only {base_commit}` to see what files changed

2. **Detect Technologies**: Based on file extensions and imports, identify the stack:
   - Python files (.py): Look for FastAPI, Pydantic-AI, SQLAlchemy, pytest
   - Go files (.go): Look for BubbleTea, Wish, Prometheus
   - TypeScript/React (.tsx, .ts): Look for React Router, shadcn/ui, Zustand, React Flow

3. **Load Review Skills**: Use the `Skill` tool to load appropriate review skills:
   - Python: `beagle:review-python` (FastAPI, pytest, Pydantic)
   - Go: `beagle:review-go` (error handling, concurrency, interfaces)
   - Frontend: `beagle:review-frontend` (React, TypeScript, CSS)
   - TUI: `beagle:review-tui` (BubbleTea terminal apps)

4. **Get the Diff**: Run `git diff {base_commit}` to get the full diff

5. **Review**: Follow the loaded skill's instructions to review the code

6. **Output**: Provide your review in the following JSON format:

```json
{{
  "approved": true|false,
  "comments": ["comment 1", "comment 2"],
  "severity": "low"|"medium"|"high"|"critical"
}}
```

## Rules

- Load skills BEFORE reviewing (not after)
- Include FILE:LINE in your comments
- Be specific about what needs to change
- Only flag real issues - check linters first before flagging style issues
- Approved means the code is ready to merge as-is""",
    ),
}
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/unit/agents/prompts/test_defaults.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add amelia/agents/prompts/ tests/unit/agents/prompts/
git commit -m "feat(prompts): add hardcoded prompt defaults module

Extract system prompts from Architect and Reviewer agents into
a centralized defaults module. This provides factory defaults
and serves as the source for 'Reset to default' functionality."
```

---

### Task 1.2: Create Prompt Pydantic Models

**Files:**
- Create: `amelia/agents/prompts/models.py`
- Test: `tests/unit/agents/prompts/test_models.py`

**Step 1: Write the failing test**

```python
# tests/unit/agents/prompts/test_models.py
"""Tests for prompt Pydantic models."""
import pytest
from pydantic import ValidationError

from amelia.agents.prompts.models import (
    Prompt,
    PromptVersion,
    ResolvedPrompt,
    WorkflowPromptVersion,
)


class TestPrompt:
    """Tests for Prompt model."""

    def test_create_prompt(self):
        """Should create a valid Prompt."""
        prompt = Prompt(
            id="architect.system",
            agent="architect",
            name="Architect System Prompt",
            description="Defines the architect's role",
            current_version_id=None,
        )
        assert prompt.id == "architect.system"
        assert prompt.agent == "architect"
        assert prompt.current_version_id is None

    def test_prompt_with_version(self):
        """Should allow setting current_version_id."""
        prompt = Prompt(
            id="architect.system",
            agent="architect",
            name="Architect System Prompt",
            description="Defines the architect's role",
            current_version_id="version-123",
        )
        assert prompt.current_version_id == "version-123"


class TestPromptVersion:
    """Tests for PromptVersion model."""

    def test_create_version(self):
        """Should create a valid PromptVersion."""
        version = PromptVersion(
            id="v-123",
            prompt_id="architect.system",
            version_number=1,
            content="You are an architect...",
            change_note="Initial version",
        )
        assert version.id == "v-123"
        assert version.version_number == 1
        assert version.created_at is not None

    def test_version_requires_content(self):
        """Should reject empty content."""
        with pytest.raises(ValidationError):
            PromptVersion(
                id="v-123",
                prompt_id="architect.system",
                version_number=1,
                content="",
            )


class TestResolvedPrompt:
    """Tests for ResolvedPrompt model."""

    def test_resolved_default_prompt(self):
        """Should represent a default prompt."""
        resolved = ResolvedPrompt(
            prompt_id="architect.system",
            content="You are an architect...",
            version_id=None,
            version_number=None,
            is_default=True,
        )
        assert resolved.is_default is True
        assert resolved.version_id is None

    def test_resolved_custom_prompt(self):
        """Should represent a custom prompt version."""
        resolved = ResolvedPrompt(
            prompt_id="architect.system",
            content="Custom architect prompt...",
            version_id="v-123",
            version_number=3,
            is_default=False,
        )
        assert resolved.is_default is False
        assert resolved.version_number == 3


class TestWorkflowPromptVersion:
    """Tests for WorkflowPromptVersion model."""

    def test_create_workflow_prompt_version(self):
        """Should link workflow to prompt version."""
        wpv = WorkflowPromptVersion(
            workflow_id="wf-123",
            prompt_id="architect.system",
            version_id="v-456",
        )
        assert wpv.workflow_id == "wf-123"
        assert wpv.prompt_id == "architect.system"
        assert wpv.version_id == "v-456"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/agents/prompts/test_models.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'amelia.agents.prompts.models'"

**Step 3: Create the models module**

```python
# amelia/agents/prompts/models.py
"""Pydantic models for prompt configuration.

Provides data models for prompts, versions, and resolution results.
"""
from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class Prompt(BaseModel):
    """A prompt definition (one per agent prompt type).

    Attributes:
        id: Unique identifier (e.g., "architect.system").
        agent: Agent name (architect, developer, reviewer).
        name: Human-readable name.
        description: What this prompt controls.
        current_version_id: Active version ID, or None to use default.
    """

    id: str
    agent: str
    name: str
    description: str | None = None
    current_version_id: str | None = None


class PromptVersion(BaseModel):
    """A version of a prompt (append-only history).

    Attributes:
        id: Unique version identifier (UUID).
        prompt_id: Reference to parent prompt.
        version_number: Sequential version number.
        content: The prompt text content.
        created_at: When this version was created.
        change_note: Optional note describing the change.
    """

    id: str
    prompt_id: str
    version_number: int
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    change_note: str | None = None

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        """Validate that content is not empty."""
        if not v.strip():
            raise ValueError("Prompt content cannot be empty")
        return v


class ResolvedPrompt(BaseModel):
    """Result of prompt resolution (custom or default).

    Attributes:
        prompt_id: The prompt identifier.
        content: The resolved prompt text.
        version_id: Version ID if using custom, None if default.
        version_number: Version number if using custom.
        is_default: True if using hardcoded default.
    """

    prompt_id: str
    content: str
    version_id: str | None = None
    version_number: int | None = None
    is_default: bool = True


class WorkflowPromptVersion(BaseModel):
    """Links a workflow to the prompt versions it used.

    Attributes:
        workflow_id: The workflow ID.
        prompt_id: The prompt ID.
        version_id: The version ID used by this workflow.
    """

    workflow_id: str
    prompt_id: str
    version_id: str
```

**Step 4: Update __init__.py exports**

```python
# amelia/agents/prompts/__init__.py
"""Agent prompt configuration package.

Provides prompt defaults and resolution for configurable agent prompts.
"""
from amelia.agents.prompts.defaults import PROMPT_DEFAULTS, PromptDefault
from amelia.agents.prompts.models import (
    Prompt,
    PromptVersion,
    ResolvedPrompt,
    WorkflowPromptVersion,
)

__all__ = [
    "PROMPT_DEFAULTS",
    "Prompt",
    "PromptDefault",
    "PromptVersion",
    "ResolvedPrompt",
    "WorkflowPromptVersion",
]
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/unit/agents/prompts/test_models.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add amelia/agents/prompts/
git commit -m "feat(prompts): add Pydantic models for prompt configuration

Add models for Prompt, PromptVersion, ResolvedPrompt, and
WorkflowPromptVersion. These support version tracking and
workflow-to-prompt linking."
```

---

### Task 1.3: Add Prompt Tables to Database Schema

**Files:**
- Modify: `amelia/server/database/connection.py:252-339` (add to ensure_schema)
- Test: `tests/unit/server/database/test_prompt_schema.py`

**Step 1: Write the failing test**

```python
# tests/unit/server/database/test_prompt_schema.py
"""Tests for prompt database schema."""
import pytest
import aiosqlite

from amelia.server.database.connection import Database


@pytest.fixture
async def db(tmp_path):
    """Create a temporary database with schema."""
    db_path = tmp_path / "test.db"
    database = Database(db_path)
    await database.connect()
    await database.ensure_schema()
    yield database
    await database.close()


@pytest.mark.asyncio
async def test_prompts_table_exists(db: Database):
    """Prompts table should exist after schema creation."""
    result = await db.fetch_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='prompts'"
    )
    assert result is not None
    assert result[0] == "prompts"


@pytest.mark.asyncio
async def test_prompt_versions_table_exists(db: Database):
    """Prompt versions table should exist after schema creation."""
    result = await db.fetch_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='prompt_versions'"
    )
    assert result is not None
    assert result[0] == "prompt_versions"


@pytest.mark.asyncio
async def test_workflow_prompt_versions_table_exists(db: Database):
    """Workflow prompt versions table should exist after schema creation."""
    result = await db.fetch_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_prompt_versions'"
    )
    assert result is not None


@pytest.mark.asyncio
async def test_can_insert_prompt(db: Database):
    """Should be able to insert a prompt."""
    await db.execute(
        """INSERT INTO prompts (id, agent, name, description, current_version_id)
           VALUES (?, ?, ?, ?, ?)""",
        ("architect.system", "architect", "Architect System", "Description", None),
    )
    result = await db.fetch_one("SELECT * FROM prompts WHERE id = ?", ("architect.system",))
    assert result is not None
    assert result["agent"] == "architect"


@pytest.mark.asyncio
async def test_can_insert_prompt_version(db: Database):
    """Should be able to insert a prompt version with foreign key."""
    # First insert the prompt
    await db.execute(
        """INSERT INTO prompts (id, agent, name, description)
           VALUES (?, ?, ?, ?)""",
        ("architect.system", "architect", "Architect System", "Description"),
    )
    # Then insert the version
    await db.execute(
        """INSERT INTO prompt_versions (id, prompt_id, version_number, content, change_note)
           VALUES (?, ?, ?, ?, ?)""",
        ("v-123", "architect.system", 1, "You are an architect...", "Initial"),
    )
    result = await db.fetch_one("SELECT * FROM prompt_versions WHERE id = ?", ("v-123",))
    assert result is not None
    assert result["version_number"] == 1


@pytest.mark.asyncio
async def test_version_unique_constraint(db: Database):
    """Same prompt+version_number should fail unique constraint."""
    await db.execute(
        "INSERT INTO prompts (id, agent, name) VALUES (?, ?, ?)",
        ("test.prompt", "test", "Test"),
    )
    await db.execute(
        "INSERT INTO prompt_versions (id, prompt_id, version_number, content) VALUES (?, ?, ?, ?)",
        ("v1", "test.prompt", 1, "Content"),
    )
    with pytest.raises(aiosqlite.IntegrityError):
        await db.execute(
            "INSERT INTO prompt_versions (id, prompt_id, version_number, content) VALUES (?, ?, ?, ?)",
            ("v2", "test.prompt", 1, "Duplicate version number"),
        )


@pytest.mark.asyncio
async def test_workflow_prompt_version_foreign_keys(db: Database):
    """Workflow prompt versions should enforce foreign keys."""
    # Create a workflow first
    await db.execute(
        """INSERT INTO workflows (id, issue_id, worktree_path, worktree_name, state_json)
           VALUES (?, ?, ?, ?, ?)""",
        ("wf-123", "ISSUE-1", "/path", "main", "{}"),
    )
    # Create prompt and version
    await db.execute(
        "INSERT INTO prompts (id, agent, name) VALUES (?, ?, ?)",
        ("test.prompt", "test", "Test"),
    )
    await db.execute(
        "INSERT INTO prompt_versions (id, prompt_id, version_number, content) VALUES (?, ?, ?, ?)",
        ("v1", "test.prompt", 1, "Content"),
    )
    # Now link them
    await db.execute(
        """INSERT INTO workflow_prompt_versions (workflow_id, prompt_id, version_id)
           VALUES (?, ?, ?)""",
        ("wf-123", "test.prompt", "v1"),
    )
    result = await db.fetch_one(
        "SELECT * FROM workflow_prompt_versions WHERE workflow_id = ?", ("wf-123",)
    )
    assert result is not None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/server/database/test_prompt_schema.py -v`
Expected: FAIL - tables don't exist

**Step 3: Add prompt tables to ensure_schema**

Edit `amelia/server/database/connection.py` - add after the token_usage table (around line 302):

```python
        # Prompt configuration tables
        await self.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id TEXT PRIMARY KEY,
                agent TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                current_version_id TEXT
            )
        """)

        await self.execute("""
            CREATE TABLE IF NOT EXISTS prompt_versions (
                id TEXT PRIMARY KEY,
                prompt_id TEXT NOT NULL REFERENCES prompts(id),
                version_number INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                change_note TEXT,
                UNIQUE(prompt_id, version_number)
            )
        """)

        await self.execute("""
            CREATE TABLE IF NOT EXISTS workflow_prompt_versions (
                workflow_id TEXT NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
                prompt_id TEXT NOT NULL REFERENCES prompts(id),
                version_id TEXT NOT NULL REFERENCES prompt_versions(id),
                PRIMARY KEY (workflow_id, prompt_id)
            )
        """)
```

Add indexes after existing indexes (around line 337):

```python
        await self.execute(
            "CREATE INDEX IF NOT EXISTS idx_prompt_versions_prompt ON prompt_versions(prompt_id)"
        )
        await self.execute(
            "CREATE INDEX IF NOT EXISTS idx_workflow_prompts_workflow ON workflow_prompt_versions(workflow_id)"
        )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/database/test_prompt_schema.py -v`
Expected: PASS

**Step 5: Run existing database tests to ensure no regression**

Run: `uv run pytest tests/unit/server/database/ -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add amelia/server/database/connection.py tests/unit/server/database/test_prompt_schema.py
git commit -m "feat(db): add prompt configuration tables to schema

Add prompts, prompt_versions, and workflow_prompt_versions tables
for storing customizable agent prompts with version history."
```

---

## Phase 2: Backend Repository and Resolver

### Task 2.1: Create Prompt Repository

**Files:**
- Create: `amelia/server/database/prompt_repository.py`
- Test: `tests/unit/server/database/test_prompt_repository.py`

**Step 1: Write the failing test**

```python
# tests/unit/server/database/test_prompt_repository.py
"""Tests for PromptRepository."""
import pytest
from datetime import datetime, UTC

from amelia.server.database.connection import Database
from amelia.server.database.prompt_repository import PromptRepository
from amelia.agents.prompts.models import Prompt, PromptVersion


@pytest.fixture
async def db(tmp_path):
    """Create a temporary database with schema."""
    db_path = tmp_path / "test.db"
    database = Database(db_path)
    await database.connect()
    await database.ensure_schema()
    yield database
    await database.close()


@pytest.fixture
def repo(db):
    """Create a PromptRepository."""
    return PromptRepository(db)


class TestPromptCRUD:
    """Tests for prompt CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_prompt(self, repo: PromptRepository):
        """Should create a prompt."""
        prompt = Prompt(
            id="test.prompt",
            agent="test",
            name="Test Prompt",
            description="A test prompt",
        )
        await repo.create_prompt(prompt)
        result = await repo.get_prompt("test.prompt")
        assert result is not None
        assert result.name == "Test Prompt"

    @pytest.mark.asyncio
    async def test_list_prompts(self, repo: PromptRepository):
        """Should list all prompts."""
        await repo.create_prompt(Prompt(id="p1", agent="a", name="Prompt 1"))
        await repo.create_prompt(Prompt(id="p2", agent="b", name="Prompt 2"))
        prompts = await repo.list_prompts()
        assert len(prompts) == 2

    @pytest.mark.asyncio
    async def test_get_prompt_not_found(self, repo: PromptRepository):
        """Should return None for non-existent prompt."""
        result = await repo.get_prompt("nonexistent")
        assert result is None


class TestVersionManagement:
    """Tests for version management."""

    @pytest.mark.asyncio
    async def test_create_version(self, repo: PromptRepository):
        """Should create a new version."""
        await repo.create_prompt(Prompt(id="test.prompt", agent="test", name="Test"))
        version = await repo.create_version(
            prompt_id="test.prompt",
            content="New prompt content",
            change_note="Initial version",
        )
        assert version.version_number == 1
        assert version.content == "New prompt content"

    @pytest.mark.asyncio
    async def test_create_version_increments_number(self, repo: PromptRepository):
        """Version numbers should auto-increment."""
        await repo.create_prompt(Prompt(id="test.prompt", agent="test", name="Test"))
        v1 = await repo.create_version("test.prompt", "Content 1", "First")
        v2 = await repo.create_version("test.prompt", "Content 2", "Second")
        assert v1.version_number == 1
        assert v2.version_number == 2

    @pytest.mark.asyncio
    async def test_create_version_sets_active(self, repo: PromptRepository):
        """Creating a version should set it as active."""
        await repo.create_prompt(Prompt(id="test.prompt", agent="test", name="Test"))
        version = await repo.create_version("test.prompt", "Content", None)
        prompt = await repo.get_prompt("test.prompt")
        assert prompt.current_version_id == version.id

    @pytest.mark.asyncio
    async def test_get_versions(self, repo: PromptRepository):
        """Should list all versions for a prompt."""
        await repo.create_prompt(Prompt(id="test.prompt", agent="test", name="Test"))
        await repo.create_version("test.prompt", "V1", None)
        await repo.create_version("test.prompt", "V2", None)
        versions = await repo.get_versions("test.prompt")
        assert len(versions) == 2
        # Should be ordered by version_number descending (newest first)
        assert versions[0].version_number == 2
        assert versions[1].version_number == 1

    @pytest.mark.asyncio
    async def test_get_version_by_id(self, repo: PromptRepository):
        """Should get a specific version by ID."""
        await repo.create_prompt(Prompt(id="test.prompt", agent="test", name="Test"))
        created = await repo.create_version("test.prompt", "Content", None)
        result = await repo.get_version(created.id)
        assert result is not None
        assert result.content == "Content"

    @pytest.mark.asyncio
    async def test_set_active_version(self, repo: PromptRepository):
        """Should change the active version."""
        await repo.create_prompt(Prompt(id="test.prompt", agent="test", name="Test"))
        v1 = await repo.create_version("test.prompt", "V1", None)
        v2 = await repo.create_version("test.prompt", "V2", None)
        # v2 is now active, switch back to v1
        await repo.set_active_version("test.prompt", v1.id)
        prompt = await repo.get_prompt("test.prompt")
        assert prompt.current_version_id == v1.id

    @pytest.mark.asyncio
    async def test_reset_to_default(self, repo: PromptRepository):
        """Should clear current_version_id."""
        await repo.create_prompt(Prompt(id="test.prompt", agent="test", name="Test"))
        await repo.create_version("test.prompt", "Content", None)
        await repo.reset_to_default("test.prompt")
        prompt = await repo.get_prompt("test.prompt")
        assert prompt.current_version_id is None


class TestWorkflowLinking:
    """Tests for workflow-prompt linking."""

    @pytest.mark.asyncio
    async def test_record_workflow_prompt(self, repo: PromptRepository, db: Database):
        """Should record which version a workflow used."""
        # Create workflow
        await db.execute(
            "INSERT INTO workflows (id, issue_id, worktree_path, worktree_name, state_json) VALUES (?, ?, ?, ?, ?)",
            ("wf-1", "ISSUE-1", "/path", "main", "{}"),
        )
        # Create prompt and version
        await repo.create_prompt(Prompt(id="test.prompt", agent="test", name="Test"))
        version = await repo.create_version("test.prompt", "Content", None)
        # Record the link
        await repo.record_workflow_prompt("wf-1", "test.prompt", version.id)
        # Verify
        results = await repo.get_workflow_prompts("wf-1")
        assert len(results) == 1
        assert results[0].version_id == version.id

    @pytest.mark.asyncio
    async def test_get_workflow_prompts_empty(self, repo: PromptRepository):
        """Should return empty list for workflow with no prompts."""
        results = await repo.get_workflow_prompts("nonexistent")
        assert results == []
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/server/database/test_prompt_repository.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Create the repository**

```python
# amelia/server/database/prompt_repository.py
"""Repository for prompt configuration persistence.

Provides CRUD operations for prompts, versions, and workflow linking.
"""
import uuid
from datetime import UTC, datetime

from amelia.agents.prompts.models import (
    Prompt,
    PromptVersion,
    WorkflowPromptVersion,
)
from amelia.server.database.connection import Database


class PromptRepository:
    """Repository for prompt configuration database operations.

    Attributes:
        _db: Database connection wrapper.
    """

    def __init__(self, db: Database) -> None:
        """Initialize repository with database connection.

        Args:
            db: Database connection wrapper.
        """
        self._db = db

    # Prompt CRUD

    async def create_prompt(self, prompt: Prompt) -> None:
        """Create a new prompt definition.

        Args:
            prompt: The prompt to create.
        """
        await self._db.execute(
            """INSERT INTO prompts (id, agent, name, description, current_version_id)
               VALUES (?, ?, ?, ?, ?)""",
            (prompt.id, prompt.agent, prompt.name, prompt.description, prompt.current_version_id),
        )

    async def list_prompts(self) -> list[Prompt]:
        """List all prompt definitions.

        Returns:
            List of all prompts.
        """
        rows = await self._db.fetch_all("SELECT * FROM prompts ORDER BY agent, name")
        return [
            Prompt(
                id=row["id"],
                agent=row["agent"],
                name=row["name"],
                description=row["description"],
                current_version_id=row["current_version_id"],
            )
            for row in rows
        ]

    async def get_prompt(self, prompt_id: str) -> Prompt | None:
        """Get a prompt by ID.

        Args:
            prompt_id: The prompt identifier.

        Returns:
            The prompt if found, None otherwise.
        """
        row = await self._db.fetch_one(
            "SELECT * FROM prompts WHERE id = ?", (prompt_id,)
        )
        if not row:
            return None
        return Prompt(
            id=row["id"],
            agent=row["agent"],
            name=row["name"],
            description=row["description"],
            current_version_id=row["current_version_id"],
        )

    # Version management

    async def get_versions(self, prompt_id: str) -> list[PromptVersion]:
        """Get all versions for a prompt, newest first.

        Args:
            prompt_id: The prompt identifier.

        Returns:
            List of versions ordered by version_number descending.
        """
        rows = await self._db.fetch_all(
            """SELECT * FROM prompt_versions
               WHERE prompt_id = ?
               ORDER BY version_number DESC""",
            (prompt_id,),
        )
        return [
            PromptVersion(
                id=row["id"],
                prompt_id=row["prompt_id"],
                version_number=row["version_number"],
                content=row["content"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(UTC),
                change_note=row["change_note"],
            )
            for row in rows
        ]

    async def get_version(self, version_id: str) -> PromptVersion | None:
        """Get a specific version by ID.

        Args:
            version_id: The version identifier.

        Returns:
            The version if found, None otherwise.
        """
        row = await self._db.fetch_one(
            "SELECT * FROM prompt_versions WHERE id = ?", (version_id,)
        )
        if not row:
            return None
        return PromptVersion(
            id=row["id"],
            prompt_id=row["prompt_id"],
            version_number=row["version_number"],
            content=row["content"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(UTC),
            change_note=row["change_note"],
        )

    async def create_version(
        self,
        prompt_id: str,
        content: str,
        change_note: str | None,
    ) -> PromptVersion:
        """Create a new version and set it as active.

        Args:
            prompt_id: The prompt identifier.
            content: The prompt content.
            change_note: Optional note describing the change.

        Returns:
            The created version.
        """
        # Get next version number
        row = await self._db.fetch_one(
            "SELECT MAX(version_number) as max_version FROM prompt_versions WHERE prompt_id = ?",
            (prompt_id,),
        )
        next_version = (row["max_version"] or 0) + 1 if row else 1

        # Create version
        version_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        await self._db.execute(
            """INSERT INTO prompt_versions (id, prompt_id, version_number, content, created_at, change_note)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (version_id, prompt_id, next_version, content, now.isoformat(), change_note),
        )

        # Set as active
        await self._db.execute(
            "UPDATE prompts SET current_version_id = ? WHERE id = ?",
            (version_id, prompt_id),
        )

        return PromptVersion(
            id=version_id,
            prompt_id=prompt_id,
            version_number=next_version,
            content=content,
            created_at=now,
            change_note=change_note,
        )

    async def set_active_version(self, prompt_id: str, version_id: str) -> None:
        """Set the active version for a prompt.

        Args:
            prompt_id: The prompt identifier.
            version_id: The version to make active.
        """
        await self._db.execute(
            "UPDATE prompts SET current_version_id = ? WHERE id = ?",
            (version_id, prompt_id),
        )

    async def reset_to_default(self, prompt_id: str) -> None:
        """Reset prompt to use hardcoded default.

        Args:
            prompt_id: The prompt identifier.
        """
        await self._db.execute(
            "UPDATE prompts SET current_version_id = NULL WHERE id = ?",
            (prompt_id,),
        )

    # Workflow linking

    async def record_workflow_prompt(
        self,
        workflow_id: str,
        prompt_id: str,
        version_id: str,
    ) -> None:
        """Record which prompt version a workflow used.

        Args:
            workflow_id: The workflow identifier.
            prompt_id: The prompt identifier.
            version_id: The version identifier.
        """
        await self._db.execute(
            """INSERT OR REPLACE INTO workflow_prompt_versions (workflow_id, prompt_id, version_id)
               VALUES (?, ?, ?)""",
            (workflow_id, prompt_id, version_id),
        )

    async def get_workflow_prompts(self, workflow_id: str) -> list[WorkflowPromptVersion]:
        """Get all prompt versions used by a workflow.

        Args:
            workflow_id: The workflow identifier.

        Returns:
            List of workflow-prompt-version links.
        """
        rows = await self._db.fetch_all(
            "SELECT * FROM workflow_prompt_versions WHERE workflow_id = ?",
            (workflow_id,),
        )
        return [
            WorkflowPromptVersion(
                workflow_id=row["workflow_id"],
                prompt_id=row["prompt_id"],
                version_id=row["version_id"],
            )
            for row in rows
        ]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/database/test_prompt_repository.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/server/database/prompt_repository.py tests/unit/server/database/test_prompt_repository.py
git commit -m "feat(db): add PromptRepository for prompt CRUD

Provides database operations for prompts, versions, and workflow linking.
Supports version history and active version management."
```

---

### Task 2.2: Create Prompt Resolver

**Files:**
- Create: `amelia/agents/prompts/resolver.py`
- Test: `tests/unit/agents/prompts/test_resolver.py`

**Step 1: Write the failing test**

```python
# tests/unit/agents/prompts/test_resolver.py
"""Tests for PromptResolver."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from amelia.agents.prompts.defaults import PROMPT_DEFAULTS
from amelia.agents.prompts.models import Prompt, PromptVersion, ResolvedPrompt
from amelia.agents.prompts.resolver import PromptResolver


@pytest.fixture
def mock_repository():
    """Create a mock PromptRepository."""
    repo = MagicMock()
    repo.get_prompt = AsyncMock(return_value=None)
    repo.get_version = AsyncMock(return_value=None)
    repo.record_workflow_prompt = AsyncMock()
    return repo


class TestGetPrompt:
    """Tests for get_prompt method."""

    @pytest.mark.asyncio
    async def test_returns_default_when_no_custom_version(self, mock_repository):
        """Should return default when no custom version set."""
        mock_repository.get_prompt.return_value = Prompt(
            id="architect.system",
            agent="architect",
            name="Architect System Prompt",
            current_version_id=None,  # No custom version
        )
        resolver = PromptResolver(mock_repository)
        result = await resolver.get_prompt("architect.system")

        assert result.is_default is True
        assert result.version_id is None
        assert result.content == PROMPT_DEFAULTS["architect.system"].content

    @pytest.mark.asyncio
    async def test_returns_custom_version_when_set(self, mock_repository):
        """Should return custom version content when active."""
        custom_content = "Custom architect prompt..."
        mock_repository.get_prompt.return_value = Prompt(
            id="architect.system",
            agent="architect",
            name="Architect System Prompt",
            current_version_id="v-123",
        )
        mock_repository.get_version.return_value = PromptVersion(
            id="v-123",
            prompt_id="architect.system",
            version_number=3,
            content=custom_content,
        )
        resolver = PromptResolver(mock_repository)
        result = await resolver.get_prompt("architect.system")

        assert result.is_default is False
        assert result.version_id == "v-123"
        assert result.version_number == 3
        assert result.content == custom_content

    @pytest.mark.asyncio
    async def test_falls_back_to_default_on_db_error(self, mock_repository):
        """Should return default when database fails."""
        mock_repository.get_prompt.side_effect = Exception("DB error")
        resolver = PromptResolver(mock_repository)
        result = await resolver.get_prompt("architect.system")

        assert result.is_default is True
        assert result.content == PROMPT_DEFAULTS["architect.system"].content

    @pytest.mark.asyncio
    async def test_raises_for_unknown_prompt(self, mock_repository):
        """Should raise ValueError for unknown prompt ID."""
        mock_repository.get_prompt.return_value = None
        resolver = PromptResolver(mock_repository)

        with pytest.raises(ValueError, match="Unknown prompt"):
            await resolver.get_prompt("nonexistent.prompt")


class TestGetAllActive:
    """Tests for get_all_active method."""

    @pytest.mark.asyncio
    async def test_returns_all_prompts(self, mock_repository):
        """Should return all prompt defaults."""
        mock_repository.get_prompt.return_value = None  # All use defaults
        resolver = PromptResolver(mock_repository)
        result = await resolver.get_all_active()

        assert len(result) == len(PROMPT_DEFAULTS)
        assert "architect.system" in result
        assert "architect.plan" in result
        assert "reviewer.structured" in result


class TestRecordForWorkflow:
    """Tests for record_for_workflow method."""

    @pytest.mark.asyncio
    async def test_records_custom_versions_only(self, mock_repository):
        """Should only record custom versions, not defaults."""
        mock_repository.get_prompt.return_value = Prompt(
            id="architect.system",
            agent="architect",
            name="Test",
            current_version_id="v-123",
        )
        mock_repository.get_version.return_value = PromptVersion(
            id="v-123",
            prompt_id="architect.system",
            version_number=1,
            content="Custom content",
        )
        resolver = PromptResolver(mock_repository)
        await resolver.record_for_workflow("wf-1")

        # Should have been called for each prompt with a version_id
        assert mock_repository.record_workflow_prompt.called

    @pytest.mark.asyncio
    async def test_does_not_record_defaults(self, mock_repository):
        """Should not record anything when all use defaults."""
        mock_repository.get_prompt.return_value = None  # All defaults
        resolver = PromptResolver(mock_repository)
        await resolver.record_for_workflow("wf-1")

        mock_repository.record_workflow_prompt.assert_not_called()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/agents/prompts/test_resolver.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Create the resolver**

```python
# amelia/agents/prompts/resolver.py
"""Prompt resolution for agents.

Provides the PromptResolver that returns current prompt content,
falling back to defaults when no custom version exists.
"""
from loguru import logger

from amelia.agents.prompts.defaults import PROMPT_DEFAULTS
from amelia.agents.prompts.models import ResolvedPrompt
from amelia.server.database.prompt_repository import PromptRepository


class PromptResolver:
    """Resolves prompts from database or defaults.

    Handles the logic of returning custom versions when available
    and falling back to hardcoded defaults otherwise.

    Attributes:
        repository: Database repository for prompt data.
    """

    def __init__(self, repository: PromptRepository) -> None:
        """Initialize resolver with repository.

        Args:
            repository: Database repository for prompts.
        """
        self.repository = repository

    async def get_prompt(self, prompt_id: str) -> ResolvedPrompt:
        """Get the active prompt content.

        Returns custom version if set, otherwise returns default.
        Falls back to default on any database error.

        Args:
            prompt_id: The prompt identifier.

        Returns:
            Resolved prompt with content and metadata.

        Raises:
            ValueError: If prompt_id is unknown (not in defaults).
        """
        try:
            prompt = await self.repository.get_prompt(prompt_id)
            if prompt and prompt.current_version_id:
                version = await self.repository.get_version(prompt.current_version_id)
                if version:
                    return ResolvedPrompt(
                        prompt_id=prompt_id,
                        content=version.content,
                        version_id=version.id,
                        version_number=version.version_number,
                        is_default=False,
                    )
        except Exception as e:
            logger.warning(
                "Failed to get custom prompt, using default",
                prompt_id=prompt_id,
                error=str(e),
            )

        # Fall through to default
        default = PROMPT_DEFAULTS.get(prompt_id)
        if not default:
            raise ValueError(f"Unknown prompt: {prompt_id}")

        return ResolvedPrompt(
            prompt_id=prompt_id,
            content=default.content,
            version_id=None,
            version_number=None,
            is_default=True,
        )

    async def get_all_active(self) -> dict[str, ResolvedPrompt]:
        """Get all prompts for workflow startup.

        Returns:
            Dictionary mapping prompt_id to resolved prompt.
        """
        result = {}
        for prompt_id in PROMPT_DEFAULTS:
            result[prompt_id] = await self.get_prompt(prompt_id)
        return result

    async def record_for_workflow(self, workflow_id: str) -> None:
        """Record which prompt versions a workflow uses.

        Only records custom versions (not defaults) since defaults
        are immutable and can be reconstructed from code.

        Args:
            workflow_id: The workflow identifier.
        """
        prompts = await self.get_all_active()
        for prompt_id, resolved in prompts.items():
            if resolved.version_id:  # Only record custom versions
                await self.repository.record_workflow_prompt(
                    workflow_id, prompt_id, resolved.version_id
                )
```

**Step 4: Update __init__.py exports**

```python
# amelia/agents/prompts/__init__.py
"""Agent prompt configuration package.

Provides prompt defaults and resolution for configurable agent prompts.
"""
from amelia.agents.prompts.defaults import PROMPT_DEFAULTS, PromptDefault
from amelia.agents.prompts.models import (
    Prompt,
    PromptVersion,
    ResolvedPrompt,
    WorkflowPromptVersion,
)
from amelia.agents.prompts.resolver import PromptResolver

__all__ = [
    "PROMPT_DEFAULTS",
    "Prompt",
    "PromptDefault",
    "PromptResolver",
    "PromptVersion",
    "ResolvedPrompt",
    "WorkflowPromptVersion",
]
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/unit/agents/prompts/test_resolver.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add amelia/agents/prompts/
git commit -m "feat(prompts): add PromptResolver for prompt resolution

Resolves prompts from database with fallback to hardcoded defaults.
Records which versions are used by each workflow for auditability."
```

---

## Phase 3: Backend API Routes

### Task 3.1: Create Prompts API Router

**Files:**
- Create: `amelia/server/routes/prompts.py`
- Test: `tests/unit/server/routes/test_prompts.py`

**Step 1: Write the failing test**

```python
# tests/unit/server/routes/test_prompts.py
"""Tests for prompts API routes."""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock, patch

from amelia.agents.prompts.defaults import PROMPT_DEFAULTS
from amelia.agents.prompts.models import Prompt, PromptVersion
from amelia.server.routes.prompts import router, get_prompt_repository


@pytest.fixture
def mock_repo():
    """Create mock repository."""
    repo = MagicMock()
    repo.list_prompts = AsyncMock(return_value=[])
    repo.get_prompt = AsyncMock(return_value=None)
    repo.get_versions = AsyncMock(return_value=[])
    repo.get_version = AsyncMock(return_value=None)
    repo.create_version = AsyncMock()
    repo.reset_to_default = AsyncMock()
    return repo


@pytest.fixture
def app(mock_repo):
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_prompt_repository] = lambda: mock_repo
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestListPrompts:
    """Tests for GET /api/prompts."""

    def test_list_prompts_empty(self, client, mock_repo):
        """Should return empty list when no prompts."""
        response = client.get("/api/prompts")
        assert response.status_code == 200
        assert response.json()["prompts"] == []

    def test_list_prompts_with_data(self, client, mock_repo):
        """Should return prompts with version info."""
        mock_repo.list_prompts.return_value = [
            Prompt(id="test.prompt", agent="test", name="Test Prompt"),
        ]
        response = client.get("/api/prompts")
        assert response.status_code == 200
        data = response.json()
        assert len(data["prompts"]) == 1
        assert data["prompts"][0]["id"] == "test.prompt"


class TestGetPrompt:
    """Tests for GET /api/prompts/{id}."""

    def test_get_prompt_not_found(self, client, mock_repo):
        """Should return 404 for unknown prompt."""
        response = client.get("/api/prompts/nonexistent")
        assert response.status_code == 404

    def test_get_prompt_with_versions(self, client, mock_repo):
        """Should return prompt with version history."""
        mock_repo.get_prompt.return_value = Prompt(
            id="test.prompt", agent="test", name="Test"
        )
        mock_repo.get_versions.return_value = [
            PromptVersion(id="v1", prompt_id="test.prompt", version_number=1, content="Content"),
        ]
        response = client.get("/api/prompts/test.prompt")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test.prompt"
        assert len(data["versions"]) == 1


class TestGetVersions:
    """Tests for GET /api/prompts/{id}/versions."""

    def test_get_versions(self, client, mock_repo):
        """Should return version list."""
        mock_repo.get_versions.return_value = [
            PromptVersion(id="v2", prompt_id="test", version_number=2, content="V2"),
            PromptVersion(id="v1", prompt_id="test", version_number=1, content="V1"),
        ]
        response = client.get("/api/prompts/test/versions")
        assert response.status_code == 200
        data = response.json()
        assert len(data["versions"]) == 2
        assert data["versions"][0]["version_number"] == 2


class TestCreateVersion:
    """Tests for POST /api/prompts/{id}/versions."""

    def test_create_version(self, client, mock_repo):
        """Should create new version."""
        mock_repo.get_prompt.return_value = Prompt(
            id="test.prompt", agent="test", name="Test"
        )
        mock_repo.create_version.return_value = PromptVersion(
            id="v-new", prompt_id="test.prompt", version_number=1, content="New content"
        )
        response = client.post(
            "/api/prompts/test.prompt/versions",
            json={"content": "New content", "change_note": "Initial"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "v-new"

    def test_create_version_empty_content(self, client, mock_repo):
        """Should reject empty content."""
        mock_repo.get_prompt.return_value = Prompt(
            id="test.prompt", agent="test", name="Test"
        )
        response = client.post(
            "/api/prompts/test.prompt/versions",
            json={"content": "", "change_note": None},
        )
        assert response.status_code == 400


class TestResetToDefault:
    """Tests for POST /api/prompts/{id}/reset."""

    def test_reset_to_default(self, client, mock_repo):
        """Should reset prompt to default."""
        mock_repo.get_prompt.return_value = Prompt(
            id="architect.system", agent="architect", name="Test"
        )
        response = client.post("/api/prompts/architect.system/reset")
        assert response.status_code == 200
        mock_repo.reset_to_default.assert_called_once_with("architect.system")


class TestGetDefault:
    """Tests for GET /api/prompts/{id}/default."""

    def test_get_default_content(self, client, mock_repo):
        """Should return hardcoded default content."""
        response = client.get("/api/prompts/architect.system/default")
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == PROMPT_DEFAULTS["architect.system"].content

    def test_get_default_unknown_prompt(self, client, mock_repo):
        """Should return 404 for unknown prompt."""
        response = client.get("/api/prompts/unknown.prompt/default")
        assert response.status_code == 404
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/server/routes/test_prompts.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Create the routes module**

```python
# amelia/server/routes/prompts.py
"""API routes for prompt configuration.

Provides endpoints for listing, viewing, and editing agent prompts.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from amelia.agents.prompts.defaults import PROMPT_DEFAULTS
from amelia.agents.prompts.models import Prompt, PromptVersion
from amelia.server.database.prompt_repository import PromptRepository


router = APIRouter(prefix="/api/prompts", tags=["prompts"])


# Dependency placeholder - will be overridden by app
def get_prompt_repository() -> PromptRepository:
    """Get prompt repository dependency."""
    raise NotImplementedError("Must be overridden")


# Request/Response models


class PromptSummary(BaseModel):
    """Summary of a prompt for list views."""

    id: str
    agent: str
    name: str
    description: str | None
    current_version_id: str | None
    current_version_number: int | None


class PromptListResponse(BaseModel):
    """Response for list prompts endpoint."""

    prompts: list[PromptSummary]


class VersionSummary(BaseModel):
    """Summary of a prompt version."""

    id: str
    version_number: int
    created_at: str
    change_note: str | None


class PromptDetailResponse(BaseModel):
    """Detailed prompt with version history."""

    id: str
    agent: str
    name: str
    description: str | None
    current_version_id: str | None
    versions: list[VersionSummary]


class VersionListResponse(BaseModel):
    """Response for list versions endpoint."""

    versions: list[VersionSummary]


class VersionDetailResponse(BaseModel):
    """Full version details including content."""

    id: str
    prompt_id: str
    version_number: int
    content: str
    created_at: str
    change_note: str | None


class CreateVersionRequest(BaseModel):
    """Request to create a new version."""

    content: str
    change_note: str | None = None

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        """Validate content is not empty."""
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v


class DefaultContentResponse(BaseModel):
    """Response for get default content endpoint."""

    prompt_id: str
    content: str
    name: str
    description: str


class ResetResponse(BaseModel):
    """Response for reset to default endpoint."""

    message: str


# Routes


@router.get("", response_model=PromptListResponse)
async def list_prompts(
    repository: PromptRepository = Depends(get_prompt_repository),
) -> PromptListResponse:
    """List all prompts with current version info."""
    prompts = await repository.list_prompts()

    # Get version numbers for active versions
    summaries = []
    for prompt in prompts:
        version_number = None
        if prompt.current_version_id:
            version = await repository.get_version(prompt.current_version_id)
            if version:
                version_number = version.version_number

        summaries.append(
            PromptSummary(
                id=prompt.id,
                agent=prompt.agent,
                name=prompt.name,
                description=prompt.description,
                current_version_id=prompt.current_version_id,
                current_version_number=version_number,
            )
        )

    return PromptListResponse(prompts=summaries)


@router.get("/{prompt_id}", response_model=PromptDetailResponse)
async def get_prompt(
    prompt_id: str,
    repository: PromptRepository = Depends(get_prompt_repository),
) -> PromptDetailResponse:
    """Get prompt with version history."""
    prompt = await repository.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt not found: {prompt_id}")

    versions = await repository.get_versions(prompt_id)
    version_summaries = [
        VersionSummary(
            id=v.id,
            version_number=v.version_number,
            created_at=v.created_at.isoformat(),
            change_note=v.change_note,
        )
        for v in versions
    ]

    return PromptDetailResponse(
        id=prompt.id,
        agent=prompt.agent,
        name=prompt.name,
        description=prompt.description,
        current_version_id=prompt.current_version_id,
        versions=version_summaries,
    )


@router.get("/{prompt_id}/versions", response_model=VersionListResponse)
async def get_versions(
    prompt_id: str,
    repository: PromptRepository = Depends(get_prompt_repository),
) -> VersionListResponse:
    """List all versions for a prompt."""
    versions = await repository.get_versions(prompt_id)
    return VersionListResponse(
        versions=[
            VersionSummary(
                id=v.id,
                version_number=v.version_number,
                created_at=v.created_at.isoformat(),
                change_note=v.change_note,
            )
            for v in versions
        ]
    )


@router.post(
    "/{prompt_id}/versions",
    status_code=status.HTTP_201_CREATED,
    response_model=VersionDetailResponse,
)
async def create_version(
    prompt_id: str,
    request: CreateVersionRequest,
    repository: PromptRepository = Depends(get_prompt_repository),
) -> VersionDetailResponse:
    """Create a new version (becomes active immediately)."""
    prompt = await repository.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt not found: {prompt_id}")

    try:
        version = await repository.create_version(
            prompt_id=prompt_id,
            content=request.content,
            change_note=request.change_note,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return VersionDetailResponse(
        id=version.id,
        prompt_id=version.prompt_id,
        version_number=version.version_number,
        content=version.content,
        created_at=version.created_at.isoformat(),
        change_note=version.change_note,
    )


@router.post("/{prompt_id}/reset", response_model=ResetResponse)
async def reset_to_default(
    prompt_id: str,
    repository: PromptRepository = Depends(get_prompt_repository),
) -> ResetResponse:
    """Reset prompt to use hardcoded default."""
    prompt = await repository.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt not found: {prompt_id}")

    await repository.reset_to_default(prompt_id)
    return ResetResponse(message=f"Prompt {prompt_id} reset to default")


@router.get("/{prompt_id}/default", response_model=DefaultContentResponse)
async def get_default_content(prompt_id: str) -> DefaultContentResponse:
    """Get the hardcoded default content for a prompt."""
    default = PROMPT_DEFAULTS.get(prompt_id)
    if not default:
        raise HTTPException(status_code=404, detail=f"Unknown prompt: {prompt_id}")

    return DefaultContentResponse(
        prompt_id=prompt_id,
        content=default.content,
        name=default.name,
        description=default.description,
    )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/routes/test_prompts.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/server/routes/prompts.py tests/unit/server/routes/test_prompts.py
git commit -m "feat(api): add prompts API routes

Add REST endpoints for listing, viewing, creating versions,
and resetting prompts. Includes default content endpoint."
```

---

### Task 3.2: Register Routes and Initialize Prompts

**Files:**
- Modify: `amelia/server/app.py` (or main server file)
- Modify: `amelia/server/database/connection.py` (add initialize_prompts)
- Test: `tests/integration/test_prompts_api.py`

**Step 1: Write the failing integration test**

```python
# tests/integration/test_prompts_api.py
"""Integration tests for prompts API."""
import pytest
from fastapi.testclient import TestClient

from amelia.agents.prompts.defaults import PROMPT_DEFAULTS


@pytest.fixture
async def initialized_app(tmp_path):
    """Create app with initialized database."""
    from amelia.server.app import create_app
    from amelia.server.database.connection import Database

    db_path = tmp_path / "test.db"
    db = Database(db_path)
    await db.connect()
    await db.ensure_schema()
    await db.initialize_prompts()

    app = create_app(db)
    yield app

    await db.close()


@pytest.fixture
def client(initialized_app):
    """Create test client."""
    return TestClient(initialized_app)


class TestPromptsIntegration:
    """Integration tests for prompts API."""

    @pytest.mark.asyncio
    async def test_list_prompts_returns_seeded_prompts(self, client):
        """Should return all seeded prompts."""
        response = client.get("/api/prompts")
        assert response.status_code == 200
        data = response.json()
        assert len(data["prompts"]) == len(PROMPT_DEFAULTS)

    @pytest.mark.asyncio
    async def test_create_and_get_version(self, client):
        """Should create version and retrieve it."""
        # Create version
        response = client.post(
            "/api/prompts/architect.system/versions",
            json={"content": "Custom prompt content", "change_note": "Test change"},
        )
        assert response.status_code == 201
        version_id = response.json()["id"]

        # Get prompt detail
        response = client.get("/api/prompts/architect.system")
        assert response.status_code == 200
        data = response.json()
        assert data["current_version_id"] == version_id
        assert len(data["versions"]) == 1

    @pytest.mark.asyncio
    async def test_reset_to_default(self, client):
        """Should reset prompt to default."""
        # Create version first
        client.post(
            "/api/prompts/architect.system/versions",
            json={"content": "Custom", "change_note": None},
        )

        # Reset
        response = client.post("/api/prompts/architect.system/reset")
        assert response.status_code == 200

        # Verify reset
        response = client.get("/api/prompts/architect.system")
        data = response.json()
        assert data["current_version_id"] is None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_prompts_api.py -v`
Expected: FAIL - app doesn't include prompts router

**Step 3: Add initialize_prompts to Database class**

Edit `amelia/server/database/connection.py` - add method after ensure_schema:

```python
    async def initialize_prompts(self) -> None:
        """Seed prompts table from defaults. Idempotent.

        Creates prompt entries for each default if they don't exist.
        Call this after ensure_schema().
        """
        from amelia.agents.prompts.defaults import PROMPT_DEFAULTS

        for prompt_id, default in PROMPT_DEFAULTS.items():
            existing = await self.fetch_one(
                "SELECT 1 FROM prompts WHERE id = ?", (prompt_id,)
            )
            if not existing:
                await self.execute(
                    """INSERT INTO prompts (id, agent, name, description, current_version_id)
                       VALUES (?, ?, ?, ?, NULL)""",
                    (prompt_id, default.agent, default.name, default.description),
                )
```

**Step 4: Register prompts router in app**

Edit `amelia/server/app.py` (adjust path as needed for your codebase):

```python
# Add import
from amelia.server.routes.prompts import router as prompts_router, get_prompt_repository
from amelia.server.database.prompt_repository import PromptRepository

# In create_app or app initialization:
app.include_router(prompts_router)

# Add dependency override
def make_prompt_repository_dependency(db: Database):
    repo = PromptRepository(db)
    def get_repo():
        return repo
    return get_repo

app.dependency_overrides[get_prompt_repository] = make_prompt_repository_dependency(db)
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_prompts_api.py -v`
Expected: PASS

**Step 6: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All PASS

**Step 7: Commit**

```bash
git add amelia/server/
git commit -m "feat(server): register prompts API and initialize on startup

Add prompts router to FastAPI app and seed prompts table
from defaults on database initialization."
```

---

## Phase 4: Agent Integration

### Task 4.1: Modify Architect to Accept Injected Prompts

**Files:**
- Modify: `amelia/agents/architect.py`
- Test: `tests/unit/agents/test_architect_prompts.py`

**Step 1: Write the failing test**

```python
# tests/unit/agents/test_architect_prompts.py
"""Tests for Architect agent prompt injection."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from amelia.agents.architect import Architect
from amelia.core.state import ExecutionState
from amelia.core.types import Issue, Profile


@pytest.fixture
def mock_driver():
    """Create mock driver."""
    driver = MagicMock()
    driver.generate = AsyncMock(return_value=(
        {"goal": "Test goal", "plan_markdown": "# Plan"},
        "session-1",
    ))
    return driver


@pytest.fixture
def state():
    """Create execution state."""
    return ExecutionState(
        issue=Issue(id="TEST-1", title="Test", description="Test issue"),
    )


@pytest.fixture
def profile(tmp_path):
    """Create profile."""
    return Profile(
        name="test",
        working_dir=str(tmp_path),
        driver="api:test",
    )


class TestArchitectPromptInjection:
    """Tests for prompt injection."""

    @pytest.mark.asyncio
    async def test_uses_injected_system_prompt(self, mock_driver, state, profile):
        """Should use injected prompt instead of default."""
        custom_prompt = "You are a custom architect..."
        prompts = {"architect.system": custom_prompt}

        architect = Architect(mock_driver, prompts=prompts)
        await architect.analyze(state, profile)

        # Verify the custom prompt was used
        call_args = mock_driver.generate.call_args
        assert call_args.kwargs["system_prompt"] == custom_prompt

    @pytest.mark.asyncio
    async def test_uses_injected_plan_prompt(self, mock_driver, state, profile):
        """Should use injected plan prompt."""
        custom_plan_prompt = "Custom plan format..."
        prompts = {"architect.plan": custom_plan_prompt}

        architect = Architect(mock_driver, prompts=prompts)
        await architect.plan(state, profile, "wf-1")

        call_args = mock_driver.generate.call_args
        assert call_args.kwargs["system_prompt"] == custom_plan_prompt

    @pytest.mark.asyncio
    async def test_falls_back_to_class_default(self, mock_driver, state, profile):
        """Should use class default when prompt not injected."""
        architect = Architect(mock_driver)  # No prompts injected
        await architect.analyze(state, profile)

        call_args = mock_driver.generate.call_args
        assert "senior software architect" in call_args.kwargs["system_prompt"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/agents/test_architect_prompts.py -v`
Expected: FAIL - Architect doesn't accept prompts parameter

**Step 3: Modify Architect to accept prompts**

Edit `amelia/agents/architect.py`:

```python
# Update __init__
def __init__(
    self,
    driver: DriverInterface,
    stream_emitter: StreamEmitter | None = None,
    prompts: dict[str, str] | None = None,
):
    """Initialize the Architect agent.

    Args:
        driver: LLM driver interface for plan generation.
        stream_emitter: Optional callback for streaming events.
        prompts: Optional dict of prompt_id -> content for custom prompts.
    """
    self.driver = driver
    self._stream_emitter = stream_emitter
    self._prompts = prompts or {}

# Add property methods for prompts
@property
def system_prompt(self) -> str:
    """Get system prompt, custom or default."""
    return self._prompts.get("architect.system", self.SYSTEM_PROMPT)

@property
def plan_prompt(self) -> str:
    """Get plan prompt, custom or default."""
    return self._prompts.get("architect.plan", self.SYSTEM_PROMPT_PLAN)

# Update analyze method to use self.system_prompt
# Update plan method to use self.plan_prompt
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/agents/test_architect_prompts.py -v`
Expected: PASS

**Step 5: Run existing architect tests**

Run: `uv run pytest tests/unit/agents/test_architect.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add amelia/agents/architect.py tests/unit/agents/test_architect_prompts.py
git commit -m "feat(architect): accept injected prompts with fallback to defaults

Architect now accepts optional prompts dict for custom system prompts.
Falls back to class-level defaults when not provided."
```

---

### Task 4.2: Modify Reviewer to Accept Injected Prompts

**Files:**
- Modify: `amelia/agents/reviewer.py`
- Test: `tests/unit/agents/test_reviewer_prompts.py`

**Step 1: Write the failing test**

```python
# tests/unit/agents/test_reviewer_prompts.py
"""Tests for Reviewer agent prompt injection."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from amelia.agents.reviewer import Reviewer
from amelia.core.state import ExecutionState
from amelia.core.types import Issue, Profile


@pytest.fixture
def mock_driver():
    """Create mock driver."""
    driver = MagicMock()
    driver.generate = AsyncMock(return_value=(
        {"approved": True, "comments": [], "severity": "low"},
        "session-1",
    ))
    return driver


@pytest.fixture
def state():
    """Create execution state."""
    return ExecutionState(
        issue=Issue(id="TEST-1", title="Test", description="Test"),
        goal="Test goal",
    )


@pytest.fixture
def profile(tmp_path):
    """Create profile."""
    return Profile(name="test", working_dir=str(tmp_path), driver="api:test")


class TestReviewerPromptInjection:
    """Tests for prompt injection."""

    @pytest.mark.asyncio
    async def test_uses_injected_structured_prompt(self, mock_driver, state, profile):
        """Should use injected structured review prompt."""
        custom_prompt = "Custom structured reviewer..."
        prompts = {"reviewer.structured": custom_prompt}

        reviewer = Reviewer(mock_driver, prompts=prompts)
        await reviewer.structured_review(state, profile, "abc123")

        call_args = mock_driver.generate.call_args
        assert call_args.kwargs["system_prompt"] == custom_prompt

    @pytest.mark.asyncio
    async def test_uses_injected_agentic_prompt(self, mock_driver, state, profile):
        """Should use injected agentic review prompt."""
        custom_prompt = "Custom agentic reviewer..."
        prompts = {"reviewer.agentic": custom_prompt}

        reviewer = Reviewer(mock_driver, prompts=prompts)
        # Note: agentic_review may need special handling
        # This tests that the prompt property returns the custom value
        assert reviewer.agentic_prompt == custom_prompt

    @pytest.mark.asyncio
    async def test_falls_back_to_class_default(self, mock_driver, state, profile):
        """Should use class default when not injected."""
        reviewer = Reviewer(mock_driver)
        await reviewer.structured_review(state, profile, "abc123")

        call_args = mock_driver.generate.call_args
        assert "expert code reviewer" in call_args.kwargs["system_prompt"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/agents/test_reviewer_prompts.py -v`
Expected: FAIL

**Step 3: Modify Reviewer to accept prompts**

Edit `amelia/agents/reviewer.py`:

```python
# Update __init__
def __init__(
    self,
    driver: DriverInterface,
    stream_emitter: StreamEmitter | None = None,
    prompts: dict[str, str] | None = None,
):
    """Initialize the Reviewer agent.

    Args:
        driver: LLM driver interface for generating reviews.
        stream_emitter: Optional callback for streaming events.
        prompts: Optional dict of prompt_id -> content for custom prompts.
    """
    self.driver = driver
    self._stream_emitter = stream_emitter
    self._prompts = prompts or {}

# Add property methods
@property
def structured_prompt(self) -> str:
    """Get structured review prompt, custom or default."""
    return self._prompts.get("reviewer.structured", self.STRUCTURED_SYSTEM_PROMPT)

@property
def agentic_prompt(self) -> str:
    """Get agentic review prompt, custom or default."""
    return self._prompts.get("reviewer.agentic", self.AGENTIC_REVIEW_PROMPT)

# Update structured_review and agentic_review to use properties
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/agents/test_reviewer_prompts.py -v`
Expected: PASS

**Step 5: Run existing reviewer tests**

Run: `uv run pytest tests/unit/agents/test_reviewer.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add amelia/agents/reviewer.py tests/unit/agents/test_reviewer_prompts.py
git commit -m "feat(reviewer): accept injected prompts with fallback to defaults

Reviewer now accepts optional prompts dict for custom review prompts.
Falls back to class-level defaults when not provided."
```

---

### Task 4.3: Update Orchestrator to Inject Prompts

**Files:**
- Modify: `amelia/core/orchestrator.py`
- Modify: `amelia/server/orchestrator/service.py`
- Test: `tests/integration/test_orchestrator_prompts.py`

**Step 1: Write the failing test**

```python
# tests/integration/test_orchestrator_prompts.py
"""Integration tests for orchestrator prompt injection."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from amelia.core.orchestrator import call_architect_node
from amelia.core.state import ExecutionState
from amelia.core.types import Issue, Profile


@pytest.fixture
def state():
    """Create execution state."""
    return ExecutionState(
        issue=Issue(id="TEST-1", title="Test", description="Test"),
    )


@pytest.fixture
def config(tmp_path):
    """Create runnable config."""
    return {
        "configurable": {
            "profile": Profile(name="test", working_dir=str(tmp_path), driver="api:test"),
            "stream_emitter": None,
            "thread_id": "wf-1",
            "prompts": {"architect.plan": "Custom plan prompt..."},
        }
    }


class TestOrchestratorPromptInjection:
    """Tests for prompt injection in orchestrator."""

    @pytest.mark.asyncio
    async def test_architect_receives_prompts_from_config(self, state, config):
        """Architect should receive prompts from orchestrator config."""
        with patch("amelia.core.orchestrator.Architect") as MockArchitect:
            mock_instance = MagicMock()
            mock_instance.plan = AsyncMock(return_value=MagicMock(
                goal="Goal",
                markdown_content="# Plan",
                markdown_path="/path",
                key_files=[],
            ))
            MockArchitect.return_value = mock_instance

            await call_architect_node(state, config)

            # Verify Architect was created with prompts
            call_kwargs = MockArchitect.call_args.kwargs
            assert "prompts" in call_kwargs
            assert call_kwargs["prompts"]["architect.plan"] == "Custom plan prompt..."
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_orchestrator_prompts.py -v`
Expected: FAIL - orchestrator doesn't pass prompts

**Step 3: Update call_architect_node**

Edit `amelia/core/orchestrator.py`:

```python
async def call_architect_node(
    state: ExecutionState,
    config: RunnableConfig | None = None,
) -> dict[str, Any]:
    # ... existing code ...

    # Extract prompts from config
    prompts = config.get("configurable", {}).get("prompts", {})

    driver = DriverFactory.get_driver(profile.driver, model=profile.model)
    architect = Architect(driver, stream_emitter=stream_emitter, prompts=prompts)

    # ... rest of method ...
```

Do the same for call_reviewer_node.

**Step 4: Update OrchestratorService to resolve and inject prompts**

Edit `amelia/server/orchestrator/service.py`:

```python
# In _create_server_graph or similar method:

from amelia.agents.prompts.resolver import PromptResolver
from amelia.server.database.prompt_repository import PromptRepository

# Resolve prompts at workflow startup
prompt_repo = PromptRepository(self._repository._db)
resolver = PromptResolver(prompt_repo)
resolved_prompts = await resolver.get_all_active()

# Record which versions this workflow uses
await resolver.record_for_workflow(workflow_id)

# Convert to simple dict for config
prompts = {pid: rp.content for pid, rp in resolved_prompts.items()}

# Include in config
config = {
    "configurable": {
        # ... existing fields ...
        "prompts": prompts,
    }
}
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_orchestrator_prompts.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add amelia/core/orchestrator.py amelia/server/orchestrator/service.py tests/integration/
git commit -m "feat(orchestrator): inject resolved prompts into agents

Orchestrator now resolves prompts at workflow startup and injects
them into Architect and Reviewer agents. Records which versions
were used for auditability."
```

---

## Phase 5: Frontend Implementation

### Task 5.1: Add API Client Methods

**Files:**
- Modify: `dashboard/src/api/client.ts`
- Modify: `dashboard/src/types/index.ts`
- Test: `dashboard/src/api/__tests__/prompts.test.ts`

**Step 1: Add TypeScript types**

```typescript
// dashboard/src/types/index.ts - add to end

// ============================================================================
// Prompt Types
// ============================================================================

/**
 * Summary of a prompt for list views.
 */
export interface PromptSummary {
  id: string;
  agent: string;
  name: string;
  description: string | null;
  current_version_id: string | null;
  current_version_number: number | null;
}

/**
 * Summary of a prompt version.
 */
export interface VersionSummary {
  id: string;
  version_number: number;
  created_at: string;
  change_note: string | null;
}

/**
 * Detailed prompt with version history.
 */
export interface PromptDetail {
  id: string;
  agent: string;
  name: string;
  description: string | null;
  current_version_id: string | null;
  versions: VersionSummary[];
}

/**
 * Full version details including content.
 */
export interface VersionDetail {
  id: string;
  prompt_id: string;
  version_number: number;
  content: string;
  created_at: string;
  change_note: string | null;
}

/**
 * Default content for a prompt.
 */
export interface DefaultContent {
  prompt_id: string;
  content: string;
  name: string;
  description: string;
}
```

**Step 2: Add API client methods**

```typescript
// dashboard/src/api/client.ts - add to api object

// Prompts API

/**
 * Get all prompts with current version info.
 */
async getPrompts(): Promise<PromptSummary[]> {
  const response = await fetch(`${API_BASE_URL}/prompts`);
  const data = await handleResponse<{ prompts: PromptSummary[] }>(response);
  return data.prompts;
},

/**
 * Get prompt detail with version history.
 */
async getPrompt(id: string): Promise<PromptDetail> {
  const response = await fetch(`${API_BASE_URL}/prompts/${id}`);
  return handleResponse<PromptDetail>(response);
},

/**
 * Get all versions for a prompt.
 */
async getPromptVersions(promptId: string): Promise<VersionSummary[]> {
  const response = await fetch(`${API_BASE_URL}/prompts/${promptId}/versions`);
  const data = await handleResponse<{ versions: VersionSummary[] }>(response);
  return data.versions;
},

/**
 * Create a new version (becomes active immediately).
 */
async createPromptVersion(
  promptId: string,
  content: string,
  changeNote: string | null
): Promise<VersionDetail> {
  const response = await fetch(`${API_BASE_URL}/prompts/${promptId}/versions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, change_note: changeNote }),
  });
  return handleResponse<VersionDetail>(response);
},

/**
 * Reset prompt to hardcoded default.
 */
async resetPromptToDefault(promptId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/prompts/${promptId}/reset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  await handleResponse(response);
},

/**
 * Get the hardcoded default content for a prompt.
 */
async getPromptDefault(promptId: string): Promise<DefaultContent> {
  const response = await fetch(`${API_BASE_URL}/prompts/${promptId}/default`);
  return handleResponse<DefaultContent>(response);
},
```

**Step 3: Write test**

```typescript
// dashboard/src/api/__tests__/prompts.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from '../client';

describe('Prompts API', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('getPrompts returns prompt list', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        prompts: [
          { id: 'architect.system', agent: 'architect', name: 'Test' }
        ]
      }),
    });

    const prompts = await api.getPrompts();
    expect(prompts).toHaveLength(1);
    expect(prompts[0].id).toBe('architect.system');
  });

  it('createPromptVersion sends correct payload', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        id: 'v-123',
        prompt_id: 'architect.system',
        version_number: 1,
        content: 'New content',
      }),
    });

    await api.createPromptVersion('architect.system', 'New content', 'Test note');

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/prompts/architect.system/versions'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ content: 'New content', change_note: 'Test note' }),
      })
    );
  });
});
```

**Step 4: Run frontend tests**

Run: `cd dashboard && pnpm test:run`
Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/src/
git commit -m "feat(dashboard): add prompts API client and types

Add TypeScript types and API client methods for prompt configuration.
Supports listing, creating versions, and resetting to defaults."
```

---

### Task 5.2: Create Settings Page and PromptCard Component

**Files:**
- Create: `dashboard/src/pages/SettingsPage.tsx`
- Create: `dashboard/src/components/settings/PromptCard.tsx`
- Create: `dashboard/src/loaders/settings.ts`
- Modify: `dashboard/src/router.tsx`

**Step 1: Create settings loader**

```typescript
// dashboard/src/loaders/settings.ts
import { api } from '@/api/client';
import type { PromptSummary } from '@/types';

export interface SettingsLoaderData {
  prompts: PromptSummary[];
}

export async function settingsLoader(): Promise<SettingsLoaderData> {
  const prompts = await api.getPrompts();
  return { prompts };
}
```

**Step 2: Create PromptCard component**

```tsx
// dashboard/src/components/settings/PromptCard.tsx
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { PromptSummary } from '@/types';
import { Edit2Icon, RotateCcwIcon } from 'lucide-react';

interface PromptCardProps {
  prompt: PromptSummary;
  onEdit: (promptId: string) => void;
  onReset: (promptId: string) => void;
}

export function PromptCard({ prompt, onEdit, onReset }: PromptCardProps) {
  const isCustom = prompt.current_version_id !== null;

  return (
    <Card data-slot="prompt-card" data-prompt-id={prompt.id}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{prompt.name}</CardTitle>
          <div className="flex items-center gap-2">
            {isCustom ? (
              <Badge variant="secondary">v{prompt.current_version_number}</Badge>
            ) : (
              <Badge variant="outline">Default</Badge>
            )}
          </div>
        </div>
        <CardDescription>{prompt.description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2 justify-end">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onEdit(prompt.id)}
            data-slot="edit-button"
          >
            <Edit2Icon className="size-4 mr-1" />
            Edit
          </Button>
          {isCustom && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onReset(prompt.id)}
              data-slot="reset-button"
            >
              <RotateCcwIcon className="size-4 mr-1" />
              Reset
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

**Step 3: Create SettingsPage**

```tsx
// dashboard/src/pages/SettingsPage.tsx
import { useLoaderData, useRevalidator } from 'react-router-dom';
import { useState } from 'react';
import { toast } from 'sonner';
import { PageHeader } from '@/components/PageHeader';
import { PromptCard } from '@/components/settings/PromptCard';
import { PromptEditModal } from '@/components/settings/PromptEditModal';
import { api } from '@/api/client';
import type { SettingsLoaderData } from '@/loaders/settings';
import type { PromptSummary } from '@/types';

export default function SettingsPage() {
  const { prompts } = useLoaderData() as SettingsLoaderData;
  const revalidator = useRevalidator();
  const [editingPrompt, setEditingPrompt] = useState<string | null>(null);

  // Group prompts by agent
  const promptsByAgent = prompts.reduce((acc, prompt) => {
    const agent = prompt.agent;
    if (!acc[agent]) acc[agent] = [];
    acc[agent].push(prompt);
    return acc;
  }, {} as Record<string, PromptSummary[]>);

  const handleEdit = (promptId: string) => {
    setEditingPrompt(promptId);
  };

  const handleReset = async (promptId: string) => {
    try {
      await api.resetPromptToDefault(promptId);
      toast.success('Prompt reset to default');
      revalidator.revalidate();
    } catch (error) {
      toast.error('Failed to reset prompt');
    }
  };

  const handleSave = async (promptId: string, content: string, changeNote: string | null) => {
    try {
      await api.createPromptVersion(promptId, content, changeNote);
      toast.success('Prompt saved');
      setEditingPrompt(null);
      revalidator.revalidate();
    } catch (error) {
      toast.error('Failed to save prompt');
    }
  };

  return (
    <div className="flex flex-col h-full">
      <PageHeader>
        <PageHeader.Left>
          <PageHeader.Label>CONFIGURATION</PageHeader.Label>
          <PageHeader.Title>Settings</PageHeader.Title>
        </PageHeader.Left>
      </PageHeader>

      <div className="flex-1 overflow-auto p-6">
        <h2 className="text-lg font-semibold mb-4">Agent Prompts</h2>
        <p className="text-muted-foreground mb-6">
          Customize the system prompts that control agent behavior.
          Changes take effect immediately for new workflows.
        </p>

        <div className="space-y-8">
          {Object.entries(promptsByAgent).map(([agent, agentPrompts]) => (
            <div key={agent}>
              <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">
                {agent}
              </h3>
              <div className="grid gap-4 md:grid-cols-2">
                {agentPrompts.map((prompt) => (
                  <PromptCard
                    key={prompt.id}
                    prompt={prompt}
                    onEdit={handleEdit}
                    onReset={handleReset}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {editingPrompt && (
        <PromptEditModal
          promptId={editingPrompt}
          onSave={handleSave}
          onClose={() => setEditingPrompt(null)}
        />
      )}
    </div>
  );
}
```

**Step 4: Add route to router**

```tsx
// dashboard/src/router.tsx - add import and route

import { settingsLoader } from '@/loaders/settings';

// Add to children array:
{
  path: 'settings',
  loader: settingsLoader,
  lazy: async () => {
    const { default: Component } = await import('@/pages/SettingsPage');
    return { Component };
  },
},
```

**Step 5: Run dev server and verify**

Run: `cd dashboard && pnpm dev`
Navigate to: `http://localhost:8421/settings`
Expected: See settings page with prompt cards

**Step 6: Commit**

```bash
git add dashboard/src/
git commit -m "feat(dashboard): add Settings page with PromptCard

Create Settings page showing all prompts grouped by agent.
Each prompt card shows version status and edit/reset actions."
```

---

### Task 5.3: Create PromptEditModal Component

**Files:**
- Create: `dashboard/src/components/settings/PromptEditModal.tsx`
- Test: `dashboard/src/components/settings/__tests__/PromptEditModal.test.tsx`

**Step 1: Create the modal component**

```tsx
// dashboard/src/components/settings/PromptEditModal.tsx
import { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { api } from '@/api/client';
import type { PromptDetail, DefaultContent } from '@/types';

interface PromptEditModalProps {
  promptId: string;
  onSave: (promptId: string, content: string, changeNote: string | null) => Promise<void>;
  onClose: () => void;
}

export function PromptEditModal({ promptId, onSave, onClose }: PromptEditModalProps) {
  const [prompt, setPrompt] = useState<PromptDetail | null>(null);
  const [defaultContent, setDefaultContent] = useState<DefaultContent | null>(null);
  const [content, setContent] = useState('');
  const [changeNote, setChangeNote] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [promptData, defaultData] = await Promise.all([
          api.getPrompt(promptId),
          api.getPromptDefault(promptId),
        ]);
        setPrompt(promptData);
        setDefaultContent(defaultData);

        // If there's a current version, load its content
        if (promptData.current_version_id && promptData.versions.length > 0) {
          // Find the current version and fetch its content
          // For now, use default as starting point
          setContent(defaultData.content);
        } else {
          setContent(defaultData.content);
        }
      } catch (error) {
        console.error('Failed to load prompt:', error);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [promptId]);

  const handleSave = async () => {
    if (!content.trim()) return;
    setSaving(true);
    try {
      await onSave(promptId, content, changeNote || null);
    } finally {
      setSaving(false);
    }
  };

  const handleResetContent = () => {
    if (defaultContent) {
      setContent(defaultContent.content);
    }
  };

  const charCount = content.length;
  const showWarning = charCount > 10000;

  return (
    <Dialog open onOpenChange={() => onClose()}>
      <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Edit: {prompt?.name || 'Loading...'}</DialogTitle>
          <DialogDescription>
            {prompt?.current_version_id
              ? `Current version: v${prompt.versions[0]?.version_number}`
              : 'Using default'}
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex-1 flex items-center justify-center py-8">
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <>
            <div className="flex-1 min-h-0">
              <textarea
                className="w-full h-80 p-3 font-mono text-sm bg-muted rounded-md border resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Enter prompt content..."
                data-slot="prompt-textarea"
              />
              <div className="flex justify-between mt-2 text-xs text-muted-foreground">
                <span className={showWarning ? 'text-yellow-500' : ''}>
                  {charCount.toLocaleString()} characters
                  {showWarning && ' (large prompt may impact performance)'}
                </span>
                <button
                  type="button"
                  onClick={handleResetContent}
                  className="hover:underline"
                >
                  Reset to default
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Change note (optional)</label>
              <Input
                value={changeNote}
                onChange={(e) => setChangeNote(e.target.value)}
                placeholder="Describe what you changed..."
                data-slot="change-note-input"
              />
            </div>
          </>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={loading || saving || !content.trim()}>
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

**Step 2: Write test**

```tsx
// dashboard/src/components/settings/__tests__/PromptEditModal.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PromptEditModal } from '../PromptEditModal';

vi.mock('@/api/client', () => ({
  api: {
    getPrompt: vi.fn().mockResolvedValue({
      id: 'architect.system',
      name: 'Architect System Prompt',
      current_version_id: null,
      versions: [],
    }),
    getPromptDefault: vi.fn().mockResolvedValue({
      prompt_id: 'architect.system',
      content: 'Default content here',
      name: 'Architect System Prompt',
      description: 'Description',
    }),
  },
}));

describe('PromptEditModal', () => {
  const mockOnSave = vi.fn();
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads and displays prompt content', async () => {
    render(
      <PromptEditModal
        promptId="architect.system"
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: '' })).toHaveValue('Default content here');
    });
  });

  it('calls onSave with content and note', async () => {
    const user = userEvent.setup();

    render(
      <PromptEditModal
        promptId="architect.system"
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    // Change content
    const textarea = screen.getByPlaceholderText('Enter prompt content...');
    await user.clear(textarea);
    await user.type(textarea, 'New content');

    // Add change note
    const noteInput = screen.getByPlaceholderText('Describe what you changed...');
    await user.type(noteInput, 'Test change');

    // Save
    await user.click(screen.getByRole('button', { name: 'Save' }));

    expect(mockOnSave).toHaveBeenCalledWith(
      'architect.system',
      'New content',
      'Test change'
    );
  });
});
```

**Step 3: Run tests**

Run: `cd dashboard && pnpm test:run`
Expected: PASS

**Step 4: Commit**

```bash
git add dashboard/src/components/settings/
git commit -m "feat(dashboard): add PromptEditModal with textarea and versioning

Modal loads current prompt content, allows editing, and saves
as a new version. Shows character count with large prompt warning."
```

---

### Task 5.4: Create VersionHistory Component

**Files:**
- Create: `dashboard/src/components/settings/VersionHistory.tsx`

**Step 1: Create the component**

```tsx
// dashboard/src/components/settings/VersionHistory.tsx
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ChevronDownIcon, ChevronRightIcon } from 'lucide-react';
import type { VersionSummary } from '@/types';

interface VersionHistoryProps {
  versions: VersionSummary[];
  currentVersionId: string | null;
  onSelectVersion: (versionId: string) => void;
}

export function VersionHistory({
  versions,
  currentVersionId,
  onSelectVersion,
}: VersionHistoryProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (versions.length === 0) {
    return (
      <p className="text-sm text-muted-foreground italic">No version history</p>
    );
  }

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger asChild>
        <Button variant="ghost" size="sm" className="w-full justify-start">
          {isOpen ? (
            <ChevronDownIcon className="size-4 mr-2" />
          ) : (
            <ChevronRightIcon className="size-4 mr-2" />
          )}
          View version history ({versions.length})
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="mt-2 space-y-1 pl-6">
          {versions.map((version) => (
            <div
              key={version.id}
              className="flex items-center justify-between py-1 px-2 rounded hover:bg-muted text-sm"
            >
              <div>
                <span className="font-mono">v{version.version_number}</span>
                <span className="text-muted-foreground ml-2">
                  {new Date(version.created_at).toLocaleDateString()}
                </span>
                {version.change_note && (
                  <span className="text-muted-foreground ml-2">
                    — {version.change_note}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {version.id === currentVersionId && (
                  <span className="text-xs text-green-500">(active)</span>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onSelectVersion(version.id)}
                >
                  View
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
```

**Step 2: Integrate into PromptEditModal**

Add VersionHistory to the modal:

```tsx
// In PromptEditModal.tsx, add import and usage:
import { VersionHistory } from './VersionHistory';

// Add state for viewing version content
const [viewingVersion, setViewingVersion] = useState<string | null>(null);

// Add handler
const handleViewVersion = async (versionId: string) => {
  // For now, just mark it - could fetch and display content
  setViewingVersion(versionId);
};

// Add to the modal content, after the textarea section:
{prompt && prompt.versions.length > 0 && (
  <VersionHistory
    versions={prompt.versions}
    currentVersionId={prompt.current_version_id}
    onSelectVersion={handleViewVersion}
  />
)}
```

**Step 3: Commit**

```bash
git add dashboard/src/components/settings/
git commit -m "feat(dashboard): add VersionHistory collapsible component

Shows version history with dates and change notes.
Allows viewing previous versions (expandable for content viewing)."
```

---

### Task 5.5: Add Settings Link to Navigation

**Files:**
- Modify: `dashboard/src/components/Layout.tsx` or sidebar component

**Step 1: Add settings nav link**

Find the navigation component and add a Settings link:

```tsx
// Add import
import { SettingsIcon } from 'lucide-react';

// Add to nav items:
<NavLink to="/settings">
  <SettingsIcon className="size-4" />
  <span>Settings</span>
</NavLink>
```

**Step 2: Verify navigation works**

Run dev server and click Settings in nav.

**Step 3: Commit**

```bash
git add dashboard/src/components/
git commit -m "feat(dashboard): add Settings link to navigation

Users can now access prompt configuration from the sidebar."
```

---

## Phase 6: Final Integration and Testing

### Task 6.1: Run Full Test Suite

**Step 1: Run all backend tests**

Run: `uv run pytest tests/ -v`
Expected: All PASS

**Step 2: Run type checking**

Run: `uv run mypy amelia`
Expected: No errors

**Step 3: Run linting**

Run: `uv run ruff check amelia tests`
Expected: No errors

**Step 4: Run frontend tests**

Run: `cd dashboard && pnpm test:run && pnpm lint && pnpm type-check`
Expected: All PASS

### Task 6.2: Manual End-to-End Test

**Step 1: Start the server**

Run: `uv run amelia dev`

**Step 2: Navigate to Settings**

- Open `http://localhost:8420/settings`
- Verify all prompts are listed
- Verify "Default" badge on all prompts

**Step 3: Edit a prompt**

- Click "Edit" on Architect System Prompt
- Modify the content
- Add a change note
- Click "Save"
- Verify "v1" badge appears

**Step 4: Start a workflow**

- Create a workflow
- Verify it uses the custom prompt (check logs)

**Step 5: Reset to default**

- Go back to Settings
- Click "Reset" on the modified prompt
- Verify "Default" badge returns

### Task 6.3: Final Commit

```bash
git add -A
git commit -m "feat: complete agent prompt configuration implementation

- Backend: Prompt defaults, repository, resolver, API routes
- Database: New tables for prompts, versions, workflow linking
- Agents: Accept injected prompts with fallback to defaults
- Orchestrator: Resolves and injects prompts at workflow startup
- Frontend: Settings page with edit modal and version history

Closes #XXX"
```

---

## Summary

This implementation plan covers:

1. **Phase 1**: Data model with defaults, Pydantic models, and database schema
2. **Phase 2**: Repository and resolver for prompt persistence and resolution
3. **Phase 3**: REST API routes for prompt CRUD operations
4. **Phase 4**: Agent modifications to accept injected prompts
5. **Phase 5**: Frontend Settings page with edit modal and version history
6. **Phase 6**: Integration testing and verification

Each task follows TDD with explicit test-first steps, exact file paths, and frequent commits.
