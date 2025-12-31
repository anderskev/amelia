# Token Usage Tracking Design

## Overview

Persist and surface token usage, cost, and duration data from CLI driver executions. Data is captured per-agent invocation and displayed in the dashboard.

## Goals

- **Short-term**: Cost visibility ($ per workflow) and usage monitoring (token consumption)
- **Long-term**: Per-agent breakdown for self-improvement functionality

## Data Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   CLI Driver    │     │   Orchestrator   │     │    Database     │
│                 │     │                  │     │                 │
│ execute_agentic │────▶│ extract usage    │────▶│ token_usage     │
│ yields messages │     │ from ResultMsg   │     │ (per-agent row) │
│ including       │     │ build TokenUsage │     │                 │
│ ResultMessage   │     │ persist via repo │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                        ┌──────────────────┐              │
                        │   API Routes     │◀─────────────┘
                        │                  │     query & aggregate
                        │ /workflows/{id}  │
                        │ /workflows       │
                        └──────────────────┘
                                 │
                        ┌──────────────────┐
                        │   Dashboard      │
                        │                  │
                        │ History: totals  │
                        │ Detail: breakdown│
                        └──────────────────┘
```

## Display Locations

1. **History page**: Cost, tokens, duration per workflow (3 columns)
2. **Workflow detail page**: Full breakdown (input/output, cache, per-agent, duration)

## Backend Changes

### Model Updates

**TokenUsage** (update existing in `amelia/server/models/tokens.py`):

```python
class TokenUsage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: str = Field(..., description="Workflow ID")
    agent: str = Field(..., description="Agent: architect|developer|reviewer")
    model: str = Field(default="claude-sonnet-4-20250514")
    input_tokens: int = Field(..., ge=0)
    output_tokens: int = Field(..., ge=0)
    cache_read_tokens: int = Field(default=0, ge=0)
    cache_creation_tokens: int = Field(default=0, ge=0)
    cost_usd: float = Field(...)  # Required - calculated before save
    duration_ms: int = Field(..., ge=0)  # NEW
    num_turns: int = Field(default=1, ge=1)  # NEW
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
```

**TokenSummary** (for aggregated display):

```python
class TokenSummary(BaseModel):
    total_input_tokens: int
    total_output_tokens: int
    total_cache_read_tokens: int
    total_cost_usd: float
    total_duration_ms: int
    total_turns: int
    breakdown: list[TokenUsage]  # Per-agent records for detail page
```

### Database Schema

Update `token_usage` table in `connection.py` (no migration - drop dev database):

```sql
CREATE TABLE IF NOT EXISTS token_usage (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    agent TEXT NOT NULL,
    model TEXT NOT NULL DEFAULT 'claude-sonnet-4-20250514',
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cache_read_tokens INTEGER DEFAULT 0,
    cache_creation_tokens INTEGER DEFAULT 0,
    cost_usd REAL NOT NULL,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    num_turns INTEGER NOT NULL DEFAULT 1,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
```

### Repository Methods

Add to `WorkflowRepository`:

```python
async def save_token_usage(self, usage: TokenUsage) -> None:
    """Insert a token usage record."""

async def get_token_usage(self, workflow_id: str) -> list[TokenUsage]:
    """Get all token usage records for a workflow."""

async def get_token_summary(self, workflow_id: str) -> TokenSummary | None:
    """Aggregate tokens/cost across all agents for a workflow."""
```

### Orchestrator Integration

In `call_developer`, `call_architect`, `call_reviewer` nodes - after agent completes:

```python
# After receiving ResultMessage from driver
if result_message.usage:
    usage = TokenUsage(
        workflow_id=state.workflow_id,
        agent="developer",  # or "architect", "reviewer"
        model=result_message.usage.get("model", "unknown"),
        input_tokens=result_message.usage["input_tokens"],
        output_tokens=result_message.usage["output_tokens"],
        cache_read_tokens=result_message.usage.get("cache_read_input_tokens", 0),
        cache_creation_tokens=result_message.usage.get("cache_creation_input_tokens", 0),
        cost_usd=result_message.total_cost_usd or 0.0,
        duration_ms=result_message.duration_ms,
        num_turns=result_message.num_turns,
    )
    await repository.save_token_usage(usage)
```

### API Response Updates

**WorkflowDetailResponse**: Add `token_usage: TokenSummary | None`

**WorkflowSummary** (for history): Add:
- `total_cost_usd: float | None`
- `total_tokens: int | None`
- `total_duration_ms: int | None`

## Frontend Changes

### History Page

Add three columns to workflow history table:

| Issue | Status | Duration | Tokens | Cost | Started |
|-------|--------|----------|--------|------|---------|
| PROJ-123 | completed | 2m 34s | 15.2K | $0.42 | 2h ago |

Formatting:
- Duration: `Xm Ys`
- Tokens: `15.2K` (input + output combined)
- Cost: `$X.XX`

### Workflow Detail Page

Add "USAGE" card below the GOAL section:

```
┌─────────────────────────────────────────────────────────┐
│ USAGE                                                   │
├─────────────────────────────────────────────────────────┤
│ Total: $0.42 · 15.2K tokens · 2m 34s · 12 turns        │
│                                                         │
│ ┌─────────────┬────────┬────────┬──────┬───────┬─────┐ │
│ │ Agent       │ Input  │ Output │ Cache│ Cost  │ Time│ │
│ ├─────────────┼────────┼────────┼──────┼───────┼─────┤ │
│ │ architect   │ 2.1K   │ 0.5K   │ 1.8K │ $0.08 │ 15s │ │
│ │ developer   │ 8.4K   │ 2.1K   │ 6.2K │ $0.28 │ 1m  │ │
│ │ reviewer    │ 3.2K   │ 0.4K   │ 2.9K │ $0.06 │ 22s │ │
│ └─────────────┴────────┴────────┴──────┴───────┴─────┘ │
└─────────────────────────────────────────────────────────┘
```

### TypeScript Types

```typescript
interface TokenUsage {
  id: string;
  workflow_id: string;
  agent: 'architect' | 'developer' | 'reviewer';
  model: string;
  input_tokens: number;
  output_tokens: number;
  cache_read_tokens: number;
  cache_creation_tokens: number;
  cost_usd: number;
  duration_ms: number;
  num_turns: number;
  timestamp: string;
}

interface TokenSummary {
  total_input_tokens: number;
  total_output_tokens: number;
  total_cache_read_tokens: number;
  total_cost_usd: number;
  total_duration_ms: number;
  total_turns: number;
  breakdown: TokenUsage[];
}
```

## Implementation Order (TDD)

### Phase 1: Backend (data layer)
1. Update `TokenUsage` model - add `duration_ms`, `num_turns`, make `cost_usd` required
2. Create `TokenSummary` model
3. Update database schema in `connection.py`
4. Write repository tests → implement `save_token_usage`, `get_token_usage`, `get_token_summary`
5. Write orchestrator tests → implement usage extraction in agent nodes

### Phase 2: API
6. Update response models (`WorkflowDetailResponse`, `WorkflowSummary`)
7. Write route tests → wire up token data in `/workflows/{id}` and `/workflows`

### Phase 3: Frontend
8. Update TypeScript types
9. Write component tests → implement Usage card on detail page
10. Write history table tests → add columns to history page

## Scope Limitations

- CLI driver only (API driver support deferred)
- No budget enforcement or alerts (future feature)
- No analytics page with trends (future feature)

## Notes

- UUIDs stored as strings for consistency with existing codebase
- Per-agent granular storage enables future self-improvement analysis
- Cache token data captured for cost optimization insights
