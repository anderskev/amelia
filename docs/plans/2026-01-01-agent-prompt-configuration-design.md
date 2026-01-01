# Agent Prompt Configuration UI Design

**Date:** 2026-01-01
**Status:** Approved

## Overview

Add a dashboard UI for editing agent system prompts with version tracking. Users can modify prompts that control agent behavior, with changes taking effect immediately for new workflows. Each workflow records which prompt versions it used for auditability.

## Requirements

- Edit system prompts (role/personality text) for Architect, Developer, and Reviewer agents
- Changes take effect immediately for new workflows
- Track version history with change notes
- Link each workflow run to the prompt versions it used
- Provide hardcoded defaults as fallback and reset option
- No access restrictions (single-user/small team use case)

## Data Model

Three new tables in SQLite:

```sql
-- Prompt definitions (one row per agent prompt type)
CREATE TABLE prompts (
    id TEXT PRIMARY KEY,              -- e.g., "architect.system"
    agent TEXT NOT NULL,              -- "architect", "developer", "reviewer"
    name TEXT NOT NULL,               -- "Architect System Prompt"
    description TEXT,                 -- What this prompt controls
    current_version_id TEXT           -- FK to active version (NULL = use default)
);

-- Version history (append-only)
CREATE TABLE prompt_versions (
    id TEXT PRIMARY KEY,              -- UUID
    prompt_id TEXT NOT NULL REFERENCES prompts(id),
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_note TEXT,
    UNIQUE(prompt_id, version_number)
);

-- Junction: which prompt versions were used in each workflow
CREATE TABLE workflow_prompt_versions (
    workflow_id TEXT NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    prompt_id TEXT NOT NULL REFERENCES prompts(id),
    version_id TEXT NOT NULL REFERENCES prompt_versions(id),
    PRIMARY KEY (workflow_id, prompt_id)
);
```

No migrations needed - database can be dropped and recreated.

## Hardcoded Defaults

New file `amelia/agents/prompts/defaults.py`:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class PromptDefault:
    agent: str
    name: str
    description: str
    content: str

PROMPT_DEFAULTS: dict[str, PromptDefault] = {
    "architect.system": PromptDefault(
        agent="architect",
        name="Architect System Prompt",
        description="Defines the architect's role and planning approach",
        content="""\
You are an expert software architect...""",
    ),
    "architect.plan": PromptDefault(
        agent="architect",
        name="Architect Plan Format",
        description="Instructions for structuring the implementation plan",
        content="""\
Create a plan with the following structure...""",
    ),
    "reviewer.structured": PromptDefault(
        agent="reviewer",
        name="Reviewer Structured Prompt",
        description="Instructions for code review with structured output",
        content="""\
You are a senior code reviewer...""",
    ),
    # Additional prompts extracted from current agent files
}
```

Purpose:
- Serves as factory defaults when `current_version_id` is NULL
- Fallback when database is unavailable
- Source for "Reset to default" action

## Prompt Resolution

New file `amelia/agents/prompts/resolver.py`:

```python
class PromptResolver:
    def __init__(self, repository: PromptRepository):
        self.repository = repository

    async def get_prompt(self, prompt_id: str) -> ResolvedPrompt:
        """Returns active version content, or default if none set."""
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
        except DatabaseError:
            pass  # Fall through to default

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
        """Returns all prompts for workflow startup."""
        return {pid: await self.get_prompt(pid) for pid in PROMPT_DEFAULTS}

    async def record_for_workflow(self, workflow_id: str) -> None:
        """Snapshots current versions to workflow_prompt_versions table."""
        prompts = await self.get_all_active()
        for prompt_id, resolved in prompts.items():
            if resolved.version_id:  # Only record if using a DB version
                await self.repository.record_workflow_prompt(
                    workflow_id, prompt_id, resolved.version_id
                )
```

## Backend API

New file `amelia/server/database/prompt_repository.py`:

```python
class PromptRepository:
    # Prompt CRUD
    async def list_prompts(self) -> list[Prompt]
    async def get_prompt(self, prompt_id: str) -> Prompt | None

    # Version management
    async def get_versions(self, prompt_id: str) -> list[PromptVersion]
    async def get_version(self, version_id: str) -> PromptVersion | None
    async def create_version(self, prompt_id: str, content: str, change_note: str | None) -> PromptVersion
    async def set_active_version(self, prompt_id: str, version_id: str) -> None
    async def reset_to_default(self, prompt_id: str) -> None  # Sets current_version_id = NULL

    # Workflow linking
    async def record_workflow_prompt(self, workflow_id: str, prompt_id: str, version_id: str) -> None
    async def get_workflow_prompts(self, workflow_id: str) -> list[WorkflowPromptVersion]
```

New file `amelia/server/routes/prompts.py`:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/prompts` | List all prompts with current version info |
| GET | `/api/prompts/{id}` | Get prompt with version history |
| GET | `/api/prompts/{id}/versions` | List all versions |
| POST | `/api/prompts/{id}/versions` | Create new version (becomes active) |
| POST | `/api/prompts/{id}/reset` | Reset to hardcoded default |
| GET | `/api/prompts/{id}/default` | Get the hardcoded default content |

## Agent Integration

Agents receive prompts via dependency injection instead of using hardcoded constants:

```python
# amelia/agents/architect.py
class Architect:
    def __init__(self, driver: DriverInterface, prompts: dict[str, str]):
        self.driver = driver
        self.system_prompt = prompts.get("architect.system", FALLBACK_SYSTEM_PROMPT)

    async def plan(self, issue: Issue, ...) -> PlanResult:
        result = await self.driver.generate(
            prompt=user_prompt,
            system_prompt=self.system_prompt,  # Now injected
            schema=MarkdownPlanOutput,
        )
```

Orchestrator resolves prompts once at workflow startup:

```python
# amelia/server/orchestrator/service.py
async def _create_server_graph(self, workflow_id: str, ...):
    resolver = PromptResolver(self.prompt_repository)
    prompts = await resolver.get_all_active()

    # Record which versions this workflow uses
    await resolver.record_for_workflow(workflow_id)

    # Inject into agents
    architect = Architect(driver, prompts)
    reviewer = Reviewer(driver, prompts)
```

## Database Initialization

On startup, seed the `prompts` table from defaults (idempotent):

```python
# amelia/server/database/schema.py
async def initialize_prompts(db: Database):
    """Seeds prompts table from defaults. Idempotent."""
    for prompt_id, default in PROMPT_DEFAULTS.items():
        existing = await db.execute("SELECT 1 FROM prompts WHERE id = ?", [prompt_id])
        if not existing:
            await db.execute(
                "INSERT INTO prompts (id, agent, name, description, current_version_id) VALUES (?, ?, ?, ?, NULL)",
                [prompt_id, default.agent, default.name, default.description]
            )
```

## Frontend UI

New route: `/settings`

### Settings Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Settings                                                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Agent Prompts                                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Architect                                                ││
│  │ ┌─────────────────────────────────────────────────────┐ ││
│  │ │ System Prompt                          v3 (active)  │ ││
│  │ │ Defines the architect's role and planning approach  │ ││
│  │ │                                      [Edit] [Reset] │ ││
│  │ └─────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Reviewer                                                 ││
│  │ ┌─────────────────────────────────────────────────────┐ ││
│  │ │ Structured Review Prompt               v7 (active)  │ ││
│  │ │ ...                                                 │ ││
│  │ └─────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Edit Modal

```
┌─────────────────────────────────────────────────────────────┐
│  Edit: Architect System Prompt                    [Cancel]  │
├─────────────────────────────────────────────────────────────┤
│  Current version: v3                                         │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ (textarea with monospace font)                          ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  Change note (optional):                                     │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Added emphasis on security considerations               ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  [View version history]                    [Save as v4]     │
└─────────────────────────────────────────────────────────────┘
```

### Components

- `dashboard/src/pages/SettingsPage.tsx` - Main settings page
- `dashboard/src/components/settings/PromptCard.tsx` - Card for each prompt
- `dashboard/src/components/settings/PromptEditModal.tsx` - Edit modal with textarea
- `dashboard/src/components/settings/VersionHistory.tsx` - Expandable version list

### Workflow Detail Enhancement

Add "Prompts Used" section to workflow detail page showing which versions were active, with links to view version content.

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Database unavailable | Use hardcoded defaults, log warning |
| Version linked to workflows | Cannot delete (FK constraint) |
| Reset while workflows running | Safe - running workflows captured versions at startup |
| Empty prompt content | Reject with 400 Bad Request |
| Very large prompts | Show character count, soft warning at 10k+ |
| Concurrent edits | Each save creates new version, last wins |

## Files to Create

- `amelia/agents/prompts/__init__.py`
- `amelia/agents/prompts/defaults.py`
- `amelia/agents/prompts/resolver.py`
- `amelia/server/database/prompt_repository.py`
- `amelia/server/routes/prompts.py`
- `dashboard/src/pages/SettingsPage.tsx`
- `dashboard/src/components/settings/PromptCard.tsx`
- `dashboard/src/components/settings/PromptEditModal.tsx`
- `dashboard/src/components/settings/VersionHistory.tsx`

## Files to Modify

- `amelia/server/database/schema.py` - Add new tables and initialization
- `amelia/agents/architect.py` - Accept injected prompts
- `amelia/agents/reviewer.py` - Accept injected prompts
- `amelia/server/orchestrator/service.py` - Resolve and record prompts
- `dashboard/src/App.tsx` or router config - Add /settings route
- Workflow detail component - Add "Prompts Used" section
