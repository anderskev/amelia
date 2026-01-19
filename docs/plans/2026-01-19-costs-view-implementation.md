# Costs View Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a Costs view page that displays usage metrics with date range filtering, trend chart, and model breakdown table.

**Architecture:** Backend `/api/usage` endpoint aggregates token_usage data with date filtering. Frontend CostsPage uses React Router loader pattern with shadcn/ui chart and table components. URL state for date ranges enables shareability.

**Tech Stack:** Python/FastAPI, SQLite, React, TypeScript, React Router v7, shadcn/ui (chart, table), Recharts, Tailwind CSS v4

---

## Task 1: Add UsageResponse Types (Frontend)

**Files:**
- Modify: `dashboard/src/types/index.ts`

**Step 1: Write the types**

Add after line 769 (after PathValidationResponse):

```typescript
// ============================================================================
// Usage API Types
// ============================================================================

/**
 * Summary statistics for the usage endpoint.
 */
export interface UsageSummary {
  /** Total cost in USD for the period. */
  total_cost_usd: number;
  /** Total number of workflows in the period. */
  total_workflows: number;
  /** Total tokens (input + output) in the period. */
  total_tokens: number;
  /** Total duration in milliseconds. */
  total_duration_ms: number;
  /** Cache hit rate (0-1), optional for efficiency metrics. */
  cache_hit_rate?: number;
  /** Savings from caching in USD, optional for efficiency metrics. */
  cache_savings_usd?: number;
}

/**
 * Daily trend data point.
 */
export interface UsageTrendPoint {
  /** ISO date string (YYYY-MM-DD). */
  date: string;
  /** Cost in USD for this date. */
  cost_usd: number;
  /** Number of workflows on this date. */
  workflows: number;
}

/**
 * Usage breakdown by model.
 */
export interface UsageByModel {
  /** Model name (e.g., "claude-sonnet-4"). */
  model: string;
  /** Number of workflows using this model. */
  workflows: number;
  /** Total tokens for this model. */
  tokens: number;
  /** Total cost in USD for this model. */
  cost_usd: number;
  /** Cache hit rate (0-1), optional for efficiency metrics. */
  cache_hit_rate?: number;
  /** Savings from caching in USD, optional for efficiency metrics. */
  cache_savings_usd?: number;
}

/**
 * Response from GET /api/usage endpoint.
 */
export interface UsageResponse {
  /** Aggregated summary statistics. */
  summary: UsageSummary;
  /** Daily trend data points. */
  trend: UsageTrendPoint[];
  /** Breakdown by model. */
  by_model: UsageByModel[];
}
```

**Step 2: Verify types compile**

Run: `cd dashboard && pnpm type-check`
Expected: No errors

**Step 3: Commit**

```bash
git add dashboard/src/types/index.ts
git commit -m "$(cat <<'EOF'
feat(types): add UsageResponse types for costs view

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Add Usage API Endpoint Types (Backend)

**Files:**
- Create: `amelia/server/models/usage.py`

**Step 1: Write the failing test**

Create: `tests/unit/server/models/test_usage.py`

```python
"""Tests for usage response models."""

import pytest
from pydantic import ValidationError

from amelia.server.models.usage import (
    UsageSummary,
    UsageTrendPoint,
    UsageByModel,
    UsageResponse,
)


def test_usage_summary_required_fields():
    """UsageSummary requires core fields."""
    summary = UsageSummary(
        total_cost_usd=127.43,
        total_workflows=24,
        total_tokens=1_200_000,
        total_duration_ms=2_820_000,
    )
    assert summary.total_cost_usd == 127.43
    assert summary.total_workflows == 24
    assert summary.cache_hit_rate is None  # Optional


def test_usage_summary_with_efficiency_metrics():
    """UsageSummary accepts optional efficiency metrics."""
    summary = UsageSummary(
        total_cost_usd=127.43,
        total_workflows=24,
        total_tokens=1_200_000,
        total_duration_ms=2_820_000,
        cache_hit_rate=0.65,
        cache_savings_usd=42.50,
    )
    assert summary.cache_hit_rate == 0.65
    assert summary.cache_savings_usd == 42.50


def test_usage_trend_point():
    """UsageTrendPoint has date, cost, and workflows."""
    point = UsageTrendPoint(
        date="2026-01-15",
        cost_usd=12.34,
        workflows=3,
    )
    assert point.date == "2026-01-15"
    assert point.cost_usd == 12.34
    assert point.workflows == 3


def test_usage_by_model():
    """UsageByModel has model breakdown fields."""
    model = UsageByModel(
        model="claude-sonnet-4",
        workflows=18,
        tokens=892_000,
        cost_usd=42.17,
    )
    assert model.model == "claude-sonnet-4"
    assert model.tokens == 892_000


def test_usage_response_complete():
    """UsageResponse combines all components."""
    response = UsageResponse(
        summary=UsageSummary(
            total_cost_usd=127.43,
            total_workflows=24,
            total_tokens=1_200_000,
            total_duration_ms=2_820_000,
        ),
        trend=[
            UsageTrendPoint(date="2026-01-15", cost_usd=12.34, workflows=3),
        ],
        by_model=[
            UsageByModel(model="claude-sonnet-4", workflows=18, tokens=892_000, cost_usd=42.17),
        ],
    )
    assert len(response.trend) == 1
    assert len(response.by_model) == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/server/models/test_usage.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'amelia.server.models.usage'"

**Step 3: Write minimal implementation**

Create: `amelia/server/models/usage.py`

```python
"""Usage response models for the /api/usage endpoint."""

from pydantic import BaseModel


class UsageSummary(BaseModel):
    """Aggregated usage statistics for a time period."""

    total_cost_usd: float
    total_workflows: int
    total_tokens: int
    total_duration_ms: int
    cache_hit_rate: float | None = None
    cache_savings_usd: float | None = None


class UsageTrendPoint(BaseModel):
    """Single data point for the trend chart."""

    date: str  # ISO date YYYY-MM-DD
    cost_usd: float
    workflows: int


class UsageByModel(BaseModel):
    """Usage breakdown for a single model."""

    model: str
    workflows: int
    tokens: int
    cost_usd: float
    cache_hit_rate: float | None = None
    cache_savings_usd: float | None = None


class UsageResponse(BaseModel):
    """Complete response for GET /api/usage."""

    summary: UsageSummary
    trend: list[UsageTrendPoint]
    by_model: list[UsageByModel]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/models/test_usage.py -v`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add amelia/server/models/usage.py tests/unit/server/models/test_usage.py
git commit -m "$(cat <<'EOF'
feat(models): add usage response models

Pydantic models for UsageSummary, UsageTrendPoint, UsageByModel,
and UsageResponse for the /api/usage endpoint.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Add Usage Repository Methods

**Files:**
- Modify: `amelia/server/database/repository.py`
- Create: `tests/unit/server/database/test_usage_repository.py`

**Step 1: Write the failing test**

Create: `tests/unit/server/database/test_usage_repository.py`

```python
"""Tests for usage repository methods."""

from datetime import date, datetime, UTC
import pytest

from amelia.server.database import WorkflowRepository
from amelia.server.database.connection import Database


@pytest.fixture
async def db():
    """Create in-memory database for testing."""
    database = Database(":memory:")
    await database.connect()
    await database.create_tables()
    yield database
    await database.close()


@pytest.fixture
async def repo(db: Database):
    """Create repository with test database."""
    return WorkflowRepository(db)


@pytest.fixture
async def seed_data(db: Database):
    """Seed test data for usage queries."""
    # Create two workflows
    await db.execute("""
        INSERT INTO workflows (id, issue_id, worktree_path, status, created_at, started_at, state_json)
        VALUES
            ('wf-1', 'ISSUE-1', '/tmp/repo1', 'completed', '2026-01-10T10:00:00Z', '2026-01-10T10:00:00Z', '{}'),
            ('wf-2', 'ISSUE-2', '/tmp/repo2', 'completed', '2026-01-15T10:00:00Z', '2026-01-15T10:00:00Z', '{}')
    """)

    # Create token usage records
    await db.execute("""
        INSERT INTO token_usage (id, workflow_id, agent, model, input_tokens, output_tokens, cache_read_tokens, cost_usd, duration_ms, timestamp)
        VALUES
            ('tu-1', 'wf-1', 'architect', 'claude-sonnet-4', 10000, 2000, 5000, 0.50, 30000, '2026-01-10T10:05:00Z'),
            ('tu-2', 'wf-1', 'developer', 'claude-sonnet-4', 20000, 5000, 8000, 1.20, 60000, '2026-01-10T10:10:00Z'),
            ('tu-3', 'wf-2', 'architect', 'claude-opus-4', 15000, 3000, 0, 2.50, 45000, '2026-01-15T10:05:00Z')
    """)


async def test_get_usage_summary(repo: WorkflowRepository, seed_data):
    """get_usage_summary returns aggregated totals."""
    summary = await repo.get_usage_summary(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    assert summary["total_cost_usd"] == pytest.approx(4.20, rel=0.01)
    assert summary["total_workflows"] == 2
    assert summary["total_tokens"] == 55000  # 10k+2k+20k+5k+15k+3k
    assert summary["total_duration_ms"] == 135000  # 30k+60k+45k


async def test_get_usage_trend(repo: WorkflowRepository, seed_data):
    """get_usage_trend returns daily aggregates."""
    trend = await repo.get_usage_trend(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    # Should have 2 days with data
    assert len(trend) == 2

    # Jan 10 has wf-1 (2 usage records)
    jan10 = next(t for t in trend if t["date"] == "2026-01-10")
    assert jan10["cost_usd"] == pytest.approx(1.70, rel=0.01)
    assert jan10["workflows"] == 1

    # Jan 15 has wf-2 (1 usage record)
    jan15 = next(t for t in trend if t["date"] == "2026-01-15")
    assert jan15["cost_usd"] == pytest.approx(2.50, rel=0.01)
    assert jan15["workflows"] == 1


async def test_get_usage_by_model(repo: WorkflowRepository, seed_data):
    """get_usage_by_model returns model breakdown."""
    by_model = await repo.get_usage_by_model(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    assert len(by_model) == 2

    sonnet = next(m for m in by_model if m["model"] == "claude-sonnet-4")
    assert sonnet["workflows"] == 1  # Only wf-1 used sonnet
    assert sonnet["tokens"] == 37000  # 10k+2k+20k+5k
    assert sonnet["cost_usd"] == pytest.approx(1.70, rel=0.01)

    opus = next(m for m in by_model if m["model"] == "claude-opus-4")
    assert opus["workflows"] == 1
    assert opus["tokens"] == 18000  # 15k+3k


async def test_get_usage_summary_date_filtering(repo: WorkflowRepository, seed_data):
    """Date filtering excludes out-of-range data."""
    summary = await repo.get_usage_summary(
        start_date=date(2026, 1, 14),
        end_date=date(2026, 1, 16),
    )

    # Only wf-2 is in range
    assert summary["total_workflows"] == 1
    assert summary["total_cost_usd"] == pytest.approx(2.50, rel=0.01)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/server/database/test_usage_repository.py -v`
Expected: FAIL with "AttributeError: 'WorkflowRepository' object has no attribute 'get_usage_summary'"

**Step 3: Write minimal implementation**

Add to `amelia/server/database/repository.py` (after the existing methods, around line 500):

```python
    # =========================================================================
    # Usage Aggregation
    # =========================================================================

    async def get_usage_summary(
        self,
        start_date: date,
        end_date: date,
    ) -> dict:
        """Get aggregated usage summary for a date range.

        Args:
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).

        Returns:
            Dict with total_cost_usd, total_workflows, total_tokens, total_duration_ms.
        """
        from datetime import date as date_type

        # Format dates for SQL comparison
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()

        row = await self._db.fetch_one(
            """
            SELECT
                COALESCE(SUM(t.cost_usd), 0) as total_cost_usd,
                COUNT(DISTINCT t.workflow_id) as total_workflows,
                COALESCE(SUM(t.input_tokens + t.output_tokens), 0) as total_tokens,
                COALESCE(SUM(t.duration_ms), 0) as total_duration_ms
            FROM token_usage t
            WHERE DATE(t.timestamp) >= ? AND DATE(t.timestamp) <= ?
            """,
            (start_str, end_str),
        )

        return {
            "total_cost_usd": row[0] if row else 0.0,
            "total_workflows": row[1] if row else 0,
            "total_tokens": row[2] if row else 0,
            "total_duration_ms": row[3] if row else 0,
        }

    async def get_usage_trend(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """Get daily usage trend for a date range.

        Args:
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).

        Returns:
            List of dicts with date, cost_usd, workflows.
        """
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()

        rows = await self._db.fetch_all(
            """
            SELECT
                DATE(t.timestamp) as date,
                SUM(t.cost_usd) as cost_usd,
                COUNT(DISTINCT t.workflow_id) as workflows
            FROM token_usage t
            WHERE DATE(t.timestamp) >= ? AND DATE(t.timestamp) <= ?
            GROUP BY DATE(t.timestamp)
            ORDER BY date
            """,
            (start_str, end_str),
        )

        return [
            {
                "date": row[0],
                "cost_usd": row[1],
                "workflows": row[2],
            }
            for row in rows
        ]

    async def get_usage_by_model(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """Get usage breakdown by model for a date range.

        Args:
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).

        Returns:
            List of dicts with model, workflows, tokens, cost_usd.
        """
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()

        rows = await self._db.fetch_all(
            """
            SELECT
                t.model,
                COUNT(DISTINCT t.workflow_id) as workflows,
                SUM(t.input_tokens + t.output_tokens) as tokens,
                SUM(t.cost_usd) as cost_usd
            FROM token_usage t
            WHERE DATE(t.timestamp) >= ? AND DATE(t.timestamp) <= ?
            GROUP BY t.model
            ORDER BY cost_usd DESC
            """,
            (start_str, end_str),
        )

        return [
            {
                "model": row[0],
                "workflows": row[1],
                "tokens": row[2],
                "cost_usd": row[3],
            }
            for row in rows
        ]
```

Also add the import at the top of the file:

```python
from datetime import date
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/database/test_usage_repository.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add amelia/server/database/repository.py tests/unit/server/database/test_usage_repository.py
git commit -m "$(cat <<'EOF'
feat(repository): add usage aggregation methods

- get_usage_summary: total cost, workflows, tokens, duration
- get_usage_trend: daily cost and workflow counts
- get_usage_by_model: breakdown by LLM model

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Add Usage API Route

**Files:**
- Create: `amelia/server/routes/usage.py`
- Modify: `amelia/server/main.py` (add router)
- Create: `tests/unit/server/routes/test_usage.py`

**Step 1: Write the failing test**

Create: `tests/unit/server/routes/test_usage.py`

```python
"""Tests for usage API routes."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient

from amelia.server.main import create_app


@pytest.fixture
def mock_repo():
    """Create mock repository."""
    repo = MagicMock()
    repo.get_usage_summary = AsyncMock(return_value={
        "total_cost_usd": 127.43,
        "total_workflows": 24,
        "total_tokens": 1_200_000,
        "total_duration_ms": 2_820_000,
    })
    repo.get_usage_trend = AsyncMock(return_value=[
        {"date": "2026-01-15", "cost_usd": 12.34, "workflows": 3},
        {"date": "2026-01-16", "cost_usd": 15.67, "workflows": 4},
    ])
    repo.get_usage_by_model = AsyncMock(return_value=[
        {"model": "claude-sonnet-4", "workflows": 18, "tokens": 892_000, "cost_usd": 42.17},
        {"model": "claude-opus-4", "workflows": 6, "tokens": 340_000, "cost_usd": 85.26},
    ])
    return repo


@pytest.fixture
def client(mock_repo):
    """Create test client with mocked dependencies."""
    app = create_app()

    # Override dependencies
    from amelia.server.dependencies import get_repository
    app.dependency_overrides[get_repository] = lambda: mock_repo

    return TestClient(app)


def test_get_usage_with_preset(client, mock_repo):
    """GET /api/usage?preset=30d returns usage data."""
    response = client.get("/api/usage?preset=30d")

    assert response.status_code == 200
    data = response.json()

    assert data["summary"]["total_cost_usd"] == 127.43
    assert data["summary"]["total_workflows"] == 24
    assert len(data["trend"]) == 2
    assert len(data["by_model"]) == 2


def test_get_usage_with_date_range(client, mock_repo):
    """GET /api/usage with start/end dates uses those dates."""
    response = client.get("/api/usage?start=2026-01-01&end=2026-01-15")

    assert response.status_code == 200

    # Verify repo was called with correct dates
    call_args = mock_repo.get_usage_summary.call_args
    assert call_args[1]["start_date"] == date(2026, 1, 1)
    assert call_args[1]["end_date"] == date(2026, 1, 15)


def test_get_usage_preset_7d(client, mock_repo):
    """preset=7d calculates correct date range."""
    response = client.get("/api/usage?preset=7d")

    assert response.status_code == 200

    # Verify dates are within 7 days of today
    call_args = mock_repo.get_usage_summary.call_args
    end_date = call_args[1]["end_date"]
    start_date = call_args[1]["start_date"]
    assert (end_date - start_date).days == 6  # 7 days inclusive


def test_get_usage_invalid_preset(client):
    """Invalid preset returns 400."""
    response = client.get("/api/usage?preset=invalid")

    assert response.status_code == 400


def test_get_usage_missing_params_uses_30d(client, mock_repo):
    """No params defaults to preset=30d."""
    response = client.get("/api/usage")

    assert response.status_code == 200

    # Should use 30 day range
    call_args = mock_repo.get_usage_summary.call_args
    end_date = call_args[1]["end_date"]
    start_date = call_args[1]["start_date"]
    assert (end_date - start_date).days == 29  # 30 days inclusive
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/server/routes/test_usage.py -v`
Expected: FAIL with "404 Not Found" (route doesn't exist)

**Step 3: Write minimal implementation**

Create: `amelia/server/routes/usage.py`

```python
"""Usage metrics routes."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query

from amelia.server.database import WorkflowRepository
from amelia.server.dependencies import get_repository
from amelia.server.models.usage import (
    UsageByModel,
    UsageResponse,
    UsageSummary,
    UsageTrendPoint,
)

router = APIRouter(prefix="/usage", tags=["usage"])

# Valid preset values
PRESETS = {"7d": 7, "30d": 30, "90d": 90, "all": 365 * 10}  # 'all' = 10 years


@router.get("", response_model=UsageResponse)
async def get_usage(
    start: date | None = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end: date | None = Query(default=None, description="End date (YYYY-MM-DD)"),
    preset: str | None = Query(default=None, description="Preset: 7d, 30d, 90d, all"),
    repository: WorkflowRepository = Depends(get_repository),
) -> UsageResponse:
    """Get usage metrics for a date range.

    Either provide start/end dates or a preset (7d, 30d, 90d, all).
    Defaults to preset=30d if no parameters provided.

    Args:
        start: Start date (inclusive).
        end: End date (inclusive).
        preset: Preset duration.
        repository: Repository dependency.

    Returns:
        UsageResponse with summary, trend, and by_model data.

    Raises:
        HTTPException: 400 if invalid preset or date combination.
    """
    # Determine date range
    if start and end:
        start_date = start
        end_date = end
    elif preset:
        if preset not in PRESETS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid preset '{preset}'. Valid: {', '.join(PRESETS.keys())}",
            )
        days = PRESETS[preset]
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
    else:
        # Default to 30d
        end_date = date.today()
        start_date = end_date - timedelta(days=29)

    # Fetch data in parallel conceptually (SQLite is single-threaded but this is the pattern)
    summary_data = await repository.get_usage_summary(
        start_date=start_date,
        end_date=end_date,
    )
    trend_data = await repository.get_usage_trend(
        start_date=start_date,
        end_date=end_date,
    )
    by_model_data = await repository.get_usage_by_model(
        start_date=start_date,
        end_date=end_date,
    )

    return UsageResponse(
        summary=UsageSummary(**summary_data),
        trend=[UsageTrendPoint(**t) for t in trend_data],
        by_model=[UsageByModel(**m) for m in by_model_data],
    )
```

**Step 4: Register the router**

Modify `amelia/server/main.py` - add import and include_router:

Find the imports section and add:
```python
from amelia.server.routes.usage import router as usage_router
```

Find where other routers are included and add:
```python
app.include_router(usage_router, prefix="/api")
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/unit/server/routes/test_usage.py -v`
Expected: PASS (5 tests)

**Step 6: Commit**

```bash
git add amelia/server/routes/usage.py amelia/server/main.py tests/unit/server/routes/test_usage.py
git commit -m "$(cat <<'EOF'
feat(api): add GET /api/usage endpoint

Returns usage summary, trend, and model breakdown for date ranges.
Supports preset=7d/30d/90d/all or custom start/end dates.
Defaults to 30d if no parameters provided.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Add Usage API Client Method (Frontend)

**Files:**
- Modify: `dashboard/src/api/client.ts`
- Create: `dashboard/src/api/__tests__/client-usage.test.ts`

**Step 1: Write the failing test**

Create: `dashboard/src/api/__tests__/client-usage.test.ts`

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api } from '../client';
import type { UsageResponse } from '@/types';

const mockUsageResponse: UsageResponse = {
  summary: {
    total_cost_usd: 127.43,
    total_workflows: 24,
    total_tokens: 1_200_000,
    total_duration_ms: 2_820_000,
  },
  trend: [
    { date: '2026-01-15', cost_usd: 12.34, workflows: 3 },
  ],
  by_model: [
    { model: 'claude-sonnet-4', workflows: 18, tokens: 892_000, cost_usd: 42.17 },
  ],
};

describe('api.getUsage', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('should fetch usage with preset', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockUsageResponse,
    } as Response);

    const result = await api.getUsage({ preset: '30d' });

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/usage?preset=30d'),
      expect.any(Object)
    );
    expect(result.summary.total_cost_usd).toBe(127.43);
  });

  it('should fetch usage with date range', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockUsageResponse,
    } as Response);

    const result = await api.getUsage({ start: '2026-01-01', end: '2026-01-15' });

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/usage?start=2026-01-01&end=2026-01-15'),
      expect.any(Object)
    );
    expect(result).toEqual(mockUsageResponse);
  });

  it('should default to preset=30d when no params', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockUsageResponse,
    } as Response);

    await api.getUsage({});

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/usage?preset=30d'),
      expect.any(Object)
    );
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && pnpm test -- src/api/__tests__/client-usage.test.ts`
Expected: FAIL with "Property 'getUsage' does not exist on type"

**Step 3: Write minimal implementation**

Add to `dashboard/src/api/client.ts` after the existing methods (around line 658):

First, add the import at the top:
```typescript
import type {
  // ... existing imports ...
  UsageResponse,
} from '../types';
```

Then add the method:
```typescript
  // ==========================================================================
  // Usage API
  // ==========================================================================

  /**
   * Retrieves usage metrics for a date range.
   *
   * @param params - Query parameters (preset or start/end dates).
   * @returns UsageResponse with summary, trend, and by_model.
   * @throws {ApiError} When the API request fails.
   *
   * @example
   * ```typescript
   * // With preset
   * const usage = await api.getUsage({ preset: '30d' });
   *
   * // With date range
   * const usage = await api.getUsage({ start: '2026-01-01', end: '2026-01-15' });
   * ```
   */
  async getUsage(params: {
    start?: string;
    end?: string;
    preset?: string;
  }): Promise<UsageResponse> {
    const searchParams = new URLSearchParams();

    if (params.start && params.end) {
      searchParams.set('start', params.start);
      searchParams.set('end', params.end);
    } else {
      searchParams.set('preset', params.preset ?? '30d');
    }

    const response = await fetchWithTimeout(
      `${API_BASE_URL}/usage?${searchParams.toString()}`
    );
    return handleResponse<UsageResponse>(response);
  },
```

**Step 4: Run test to verify it passes**

Run: `cd dashboard && pnpm test -- src/api/__tests__/client-usage.test.ts`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add dashboard/src/api/client.ts dashboard/src/api/__tests__/client-usage.test.ts
git commit -m "$(cat <<'EOF'
feat(api-client): add getUsage method

Fetches usage metrics from /api/usage with preset or date range params.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Add shadcn Chart Component

**Files:**
- Create: `dashboard/src/components/ui/chart.tsx` (via shadcn CLI)
- Verify: `package.json` includes recharts

**Step 1: Install chart component via shadcn CLI**

Run: `cd dashboard && npx shadcn@latest add chart`
Expected: Creates `dashboard/src/components/ui/chart.tsx` and installs recharts

**Step 2: Verify chart component exists**

Run: `ls dashboard/src/components/ui/chart.tsx`
Expected: File exists

**Step 3: Verify recharts is in dependencies**

Run: `grep recharts dashboard/package.json`
Expected: Shows recharts in dependencies

**Step 4: Commit**

```bash
git add dashboard/src/components/ui/chart.tsx dashboard/package.json dashboard/pnpm-lock.yaml
git commit -m "$(cat <<'EOF'
feat(ui): add shadcn chart component

Adds chart primitives from shadcn/ui with recharts dependency.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Create CostsTrendChart Component

**Files:**
- Create: `dashboard/src/components/CostsTrendChart.tsx`
- Create: `dashboard/src/components/CostsTrendChart.test.tsx`

**Step 1: Write the failing test**

Create: `dashboard/src/components/CostsTrendChart.test.tsx`

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CostsTrendChart } from './CostsTrendChart';
import type { UsageTrendPoint } from '@/types';

const mockTrend: UsageTrendPoint[] = [
  { date: '2026-01-15', cost_usd: 12.34, workflows: 3 },
  { date: '2026-01-16', cost_usd: 15.67, workflows: 4 },
  { date: '2026-01-17', cost_usd: 8.90, workflows: 2 },
];

describe('CostsTrendChart', () => {
  it('should render chart container', () => {
    render(<CostsTrendChart data={mockTrend} />);

    // Chart container should exist
    expect(screen.getByRole('figure')).toBeInTheDocument();
  });

  it('should show empty state when no data', () => {
    render(<CostsTrendChart data={[]} />);

    expect(screen.getByText(/no data/i)).toBeInTheDocument();
  });

  it('should display chart with data-slot attribute', () => {
    const { container } = render(<CostsTrendChart data={mockTrend} />);

    expect(container.querySelector('[data-slot="costs-trend-chart"]')).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && pnpm test -- src/components/CostsTrendChart.test.tsx`
Expected: FAIL with "Cannot find module './CostsTrendChart'"

**Step 3: Write minimal implementation**

Create: `dashboard/src/components/CostsTrendChart.tsx`

```typescript
/**
 * @fileoverview Trend chart component for costs visualization.
 */
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart';
import { Area, AreaChart, XAxis, YAxis } from 'recharts';
import { formatCost } from '@/utils/workflow';
import type { UsageTrendPoint } from '@/types';

interface CostsTrendChartProps {
  /** Trend data points to display. */
  data: UsageTrendPoint[];
  /** Optional className for styling. */
  className?: string;
}

const chartConfig = {
  cost_usd: {
    label: 'Cost',
    color: 'hsl(var(--primary))',
  },
} satisfies ChartConfig;

/**
 * Formats a date string for chart display.
 * @param dateStr - ISO date string (YYYY-MM-DD)
 * @returns Formatted date (e.g., "Jan 15")
 */
function formatChartDate(dateStr: string): string {
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

/**
 * Displays a line/area chart of daily costs over time.
 *
 * @param props - Component props
 * @returns Chart visualization or empty state
 */
export function CostsTrendChart({ data, className }: CostsTrendChartProps) {
  if (data.length === 0) {
    return (
      <div
        data-slot="costs-trend-chart"
        role="figure"
        className="flex items-center justify-center h-64 text-muted-foreground"
      >
        No data for this period
      </div>
    );
  }

  return (
    <div data-slot="costs-trend-chart" className={className}>
      <ChartContainer config={chartConfig} className="h-64 w-full" role="figure">
        <AreaChart data={data} margin={{ left: 12, right: 12, top: 12, bottom: 12 }}>
          <defs>
            <linearGradient id="fillCost" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
              <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="date"
            tickLine={false}
            axisLine={false}
            tickFormatter={formatChartDate}
            tickMargin={8}
            className="text-xs"
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `$${value}`}
            tickMargin={8}
            width={50}
            className="text-xs"
          />
          <ChartTooltip
            cursor={false}
            content={
              <ChartTooltipContent
                formatter={(value, name) => (
                  <div className="flex flex-col gap-1">
                    <span className="font-medium">{formatCost(Number(value))}</span>
                  </div>
                )}
                labelFormatter={(label) => formatChartDate(String(label))}
              />
            }
          />
          <Area
            dataKey="cost_usd"
            type="monotone"
            fill="url(#fillCost)"
            stroke="hsl(var(--primary))"
            strokeWidth={2}
          />
        </AreaChart>
      </ChartContainer>
    </div>
  );
}
```

**Step 4: Run test to verify it passes**

Run: `cd dashboard && pnpm test -- src/components/CostsTrendChart.test.tsx`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add dashboard/src/components/CostsTrendChart.tsx dashboard/src/components/CostsTrendChart.test.tsx
git commit -m "$(cat <<'EOF'
feat(components): add CostsTrendChart component

Area chart for daily cost visualization using shadcn/ui chart and recharts.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Create Costs Loader

**Files:**
- Create: `dashboard/src/loaders/costs.ts`
- Modify: `dashboard/src/loaders/index.ts`

**Step 1: Write the failing test**

Create: `dashboard/src/loaders/__tests__/costs.test.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { costsLoader } from '../costs';
import { api } from '@/api/client';
import type { UsageResponse } from '@/types';

vi.mock('@/api/client', () => ({
  api: {
    getUsage: vi.fn(),
  },
}));

const mockUsageResponse: UsageResponse = {
  summary: {
    total_cost_usd: 127.43,
    total_workflows: 24,
    total_tokens: 1_200_000,
    total_duration_ms: 2_820_000,
  },
  trend: [
    { date: '2026-01-15', cost_usd: 12.34, workflows: 3 },
  ],
  by_model: [
    { model: 'claude-sonnet-4', workflows: 18, tokens: 892_000, cost_usd: 42.17 },
  ],
};

describe('costsLoader', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getUsage).mockResolvedValue(mockUsageResponse);
  });

  it('should use preset from URL params', async () => {
    const request = new Request('http://localhost/costs?preset=7d');

    const result = await costsLoader({ request, params: {} } as any);

    expect(api.getUsage).toHaveBeenCalledWith({ preset: '7d' });
    expect(result.usage).toEqual(mockUsageResponse);
  });

  it('should use date range from URL params', async () => {
    const request = new Request('http://localhost/costs?start=2026-01-01&end=2026-01-15');

    const result = await costsLoader({ request, params: {} } as any);

    expect(api.getUsage).toHaveBeenCalledWith({
      start: '2026-01-01',
      end: '2026-01-15',
    });
  });

  it('should default to preset=30d when no params', async () => {
    const request = new Request('http://localhost/costs');

    await costsLoader({ request, params: {} } as any);

    expect(api.getUsage).toHaveBeenCalledWith({ preset: '30d' });
  });

  it('should return current params for UI state', async () => {
    const request = new Request('http://localhost/costs?preset=90d');

    const result = await costsLoader({ request, params: {} } as any);

    expect(result.currentPreset).toBe('90d');
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && pnpm test -- src/loaders/__tests__/costs.test.ts`
Expected: FAIL with "Cannot find module '../costs'"

**Step 3: Write minimal implementation**

Create: `dashboard/src/loaders/costs.ts`

```typescript
/**
 * @fileoverview Loader for the Costs page.
 */
import { api } from '@/api/client';
import type { LoaderFunctionArgs } from 'react-router-dom';
import type { UsageResponse } from '@/types';

/**
 * Loader data type for CostsPage.
 */
export interface CostsLoaderData {
  /** Usage data from API. */
  usage: UsageResponse;
  /** Current preset value (for UI state). */
  currentPreset: string | null;
  /** Current start date (for custom range). */
  currentStart: string | null;
  /** Current end date (for custom range). */
  currentEnd: string | null;
}

/**
 * Loader for the Costs page.
 * Fetches usage data based on URL query parameters.
 *
 * @param args - React Router loader arguments.
 * @returns CostsLoaderData with usage metrics and current params.
 *
 * @example
 * // URL: /costs?preset=30d
 * const { usage, currentPreset } = await costsLoader({ request });
 *
 * @example
 * // URL: /costs?start=2026-01-01&end=2026-01-15
 * const { usage, currentStart, currentEnd } = await costsLoader({ request });
 */
export async function costsLoader({
  request,
}: LoaderFunctionArgs): Promise<CostsLoaderData> {
  const url = new URL(request.url);
  const preset = url.searchParams.get('preset');
  const start = url.searchParams.get('start');
  const end = url.searchParams.get('end');

  // Determine API params
  let apiParams: { preset?: string; start?: string; end?: string };
  if (start && end) {
    apiParams = { start, end };
  } else {
    apiParams = { preset: preset ?? '30d' };
  }

  const usage = await api.getUsage(apiParams);

  return {
    usage,
    currentPreset: start && end ? null : (preset ?? '30d'),
    currentStart: start,
    currentEnd: end,
  };
}
```

**Step 4: Update loaders index**

Add export to `dashboard/src/loaders/index.ts`:

```typescript
export { costsLoader } from './costs';
export type { CostsLoaderData } from './costs';
```

**Step 5: Run test to verify it passes**

Run: `cd dashboard && pnpm test -- src/loaders/__tests__/costs.test.ts`
Expected: PASS (4 tests)

**Step 6: Commit**

```bash
git add dashboard/src/loaders/costs.ts dashboard/src/loaders/__tests__/costs.test.ts dashboard/src/loaders/index.ts
git commit -m "$(cat <<'EOF'
feat(loaders): add costsLoader for CostsPage

Fetches usage data based on URL params (preset or date range).
Returns current params for UI state synchronization.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Create CostsPage Component

**Files:**
- Create: `dashboard/src/pages/CostsPage.tsx`
- Create: `dashboard/src/pages/CostsPage.test.tsx`

**Step 1: Write the failing test**

Create: `dashboard/src/pages/CostsPage.test.tsx`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import CostsPage from './CostsPage';
import type { CostsLoaderData } from '@/loaders/costs';

const mockLoaderData: CostsLoaderData = {
  usage: {
    summary: {
      total_cost_usd: 127.43,
      total_workflows: 24,
      total_tokens: 1_200_000,
      total_duration_ms: 2_820_000,
    },
    trend: [
      { date: '2026-01-15', cost_usd: 12.34, workflows: 3 },
      { date: '2026-01-16', cost_usd: 15.67, workflows: 4 },
    ],
    by_model: [
      { model: 'claude-sonnet-4', workflows: 18, tokens: 892_000, cost_usd: 42.17 },
      { model: 'claude-opus-4', workflows: 6, tokens: 340_000, cost_usd: 85.26 },
    ],
  },
  currentPreset: '30d',
  currentStart: null,
  currentEnd: null,
};

vi.mock('react-router-dom', async (importOriginal) => {
  const mod = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...mod,
    useLoaderData: vi.fn(),
    useNavigate: () => vi.fn(),
    useSearchParams: () => [new URLSearchParams('?preset=30d'), vi.fn()],
  };
});

import { useLoaderData } from 'react-router-dom';

describe('CostsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useLoaderData).mockReturnValue(mockLoaderData);
  });

  it('should render page header with title', () => {
    render(
      <MemoryRouter>
        <CostsPage />
      </MemoryRouter>
    );

    expect(screen.getByText('COSTS')).toBeInTheDocument();
    expect(screen.getByText('Usage & Spending')).toBeInTheDocument();
  });

  it('should display total cost in header', () => {
    render(
      <MemoryRouter>
        <CostsPage />
      </MemoryRouter>
    );

    expect(screen.getByText('$127.43')).toBeInTheDocument();
  });

  it('should display summary row with metrics', () => {
    render(
      <MemoryRouter>
        <CostsPage />
      </MemoryRouter>
    );

    expect(screen.getByText('24')).toBeInTheDocument(); // workflows
    expect(screen.getByText(/1\.2M/i)).toBeInTheDocument(); // tokens
  });

  it('should render model breakdown table', () => {
    render(
      <MemoryRouter>
        <CostsPage />
      </MemoryRouter>
    );

    expect(screen.getByText('claude-sonnet-4')).toBeInTheDocument();
    expect(screen.getByText('claude-opus-4')).toBeInTheDocument();
    expect(screen.getByText('$42.17')).toBeInTheDocument();
    expect(screen.getByText('$85.26')).toBeInTheDocument();
  });

  it('should render trend chart', () => {
    const { container } = render(
      <MemoryRouter>
        <CostsPage />
      </MemoryRouter>
    );

    expect(container.querySelector('[data-slot="costs-trend-chart"]')).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && pnpm test -- src/pages/CostsPage.test.tsx`
Expected: FAIL with "Cannot find module './CostsPage'"

**Step 3: Write minimal implementation**

Create: `dashboard/src/pages/CostsPage.tsx`

```typescript
/**
 * @fileoverview Costs page for usage monitoring and analysis.
 */
import { useLoaderData, useNavigate, useSearchParams } from 'react-router-dom';
import { PageHeader } from '@/components/PageHeader';
import { CostsTrendChart } from '@/components/CostsTrendChart';
import { formatTokens, formatCost, formatDuration } from '@/utils/workflow';
import { cn } from '@/lib/utils';
import type { costsLoader } from '@/loaders/costs';

/**
 * Date range preset options.
 */
const PRESETS = [
  { value: '7d', label: '7 days' },
  { value: '30d', label: '30 days' },
  { value: '90d', label: '90 days' },
  { value: 'all', label: 'All time' },
];

/**
 * Costs page displaying usage metrics, trends, and model breakdown.
 *
 * @returns The costs page UI
 */
export default function CostsPage() {
  const { usage, currentPreset } = useLoaderData<typeof costsLoader>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const handlePresetChange = (preset: string) => {
    setSearchParams({ preset });
  };

  const handleModelClick = (model: string) => {
    navigate(`/history?model=${encodeURIComponent(model)}`);
  };

  return (
    <div className="flex flex-col w-full">
      {/* Header */}
      <PageHeader>
        <PageHeader.Left>
          <PageHeader.Label>COSTS</PageHeader.Label>
          <PageHeader.Title>Usage & Spending</PageHeader.Title>
        </PageHeader.Left>
        <PageHeader.Center>
          <PageHeader.Value glow>
            {formatCost(usage.summary.total_cost_usd)}
          </PageHeader.Value>
        </PageHeader.Center>
        <PageHeader.Right>
          {/* Date range selector */}
          <div className="flex gap-1">
            {PRESETS.map((preset) => (
              <button
                key={preset.value}
                onClick={() => handlePresetChange(preset.value)}
                className={cn(
                  'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
                  currentPreset === preset.value
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                )}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </PageHeader.Right>
      </PageHeader>

      <div className="flex flex-col gap-6 p-6">
        {/* Summary row */}
        <div className="flex items-center gap-2 text-sm flex-wrap">
          <span className="text-primary font-semibold">
            {formatCost(usage.summary.total_cost_usd)}
          </span>
          <span className="text-muted-foreground">·</span>
          <span className="text-foreground">{usage.summary.total_workflows} workflows</span>
          <span className="text-muted-foreground">·</span>
          <span className="text-foreground">
            {formatTokens(usage.summary.total_tokens)} tokens
          </span>
          <span className="text-muted-foreground">·</span>
          <span className="text-foreground">
            {formatDuration(usage.summary.total_duration_ms)}
          </span>
        </div>

        {/* Trend chart */}
        <div className="border border-border rounded-lg p-4 bg-card/50">
          <h3 className="font-heading text-xs font-semibold tracking-widest text-muted-foreground mb-4">
            DAILY COSTS
          </h3>
          <CostsTrendChart data={usage.trend} />
        </div>

        {/* Model breakdown table */}
        <div className="border border-border rounded-lg p-4 bg-card/50">
          <h3 className="font-heading text-xs font-semibold tracking-widest text-muted-foreground mb-4">
            BY MODEL
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th scope="col" className="text-left py-2 pr-4 text-muted-foreground font-medium">
                    Model
                  </th>
                  <th scope="col" className="text-right py-2 px-3 text-muted-foreground font-medium">
                    Workflows
                  </th>
                  <th scope="col" className="text-right py-2 px-3 text-muted-foreground font-medium">
                    Tokens
                  </th>
                  <th scope="col" className="text-right py-2 px-3 text-muted-foreground font-medium">
                    Cost
                  </th>
                  <th scope="col" className="text-right py-2 pl-3 text-muted-foreground font-medium">
                    Share
                  </th>
                </tr>
              </thead>
              <tbody>
                {usage.by_model.map((model) => {
                  const share = usage.summary.total_cost_usd > 0
                    ? (model.cost_usd / usage.summary.total_cost_usd) * 100
                    : 0;
                  return (
                    <tr
                      key={model.model}
                      onClick={() => handleModelClick(model.model)}
                      className={cn(
                        'border-b border-border/50 last:border-0 cursor-pointer',
                        'hover:bg-muted/50 transition-colors'
                      )}
                    >
                      <td className="py-2 pr-4 text-foreground font-medium">
                        {model.model}
                      </td>
                      <td className="py-2 px-3 text-right text-muted-foreground tabular-nums">
                        {model.workflows}
                      </td>
                      <td className="py-2 px-3 text-right text-muted-foreground tabular-nums">
                        {formatTokens(model.tokens)}
                      </td>
                      <td className="py-2 px-3 text-right text-primary tabular-nums">
                        {formatCost(model.cost_usd)}
                      </td>
                      <td className="py-2 pl-3 text-right text-muted-foreground tabular-nums">
                        {share.toFixed(1)}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
```

**Step 4: Run test to verify it passes**

Run: `cd dashboard && pnpm test -- src/pages/CostsPage.test.tsx`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add dashboard/src/pages/CostsPage.tsx dashboard/src/pages/CostsPage.test.tsx
git commit -m "$(cat <<'EOF'
feat(pages): add CostsPage component

- PageHeader with total cost and date range selector
- Summary row with workflow count, tokens, duration
- Daily trend chart using CostsTrendChart
- Model breakdown table with clickable rows for drill-down

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Add Route and Enable Sidebar Link

**Files:**
- Modify: `dashboard/src/router.tsx`
- Modify: `dashboard/src/components/DashboardSidebar.tsx`

**Step 1: Add route to router**

Modify `dashboard/src/router.tsx`:

Add import at top:
```typescript
import { costsLoader } from '@/loaders';
```

Add route inside the children array (after 'prompts' route, around line 97):
```typescript
      {
        path: 'costs',
        loader: costsLoader,
        lazy: async () => {
          const { default: Component } = await import('@/pages/CostsPage');
          return { Component };
        },
      },
```

**Step 2: Enable sidebar link**

Modify `dashboard/src/components/DashboardSidebar.tsx`:

Find the Costs SidebarNavLink (around line 308-313) and remove `comingSoon`:

Change from:
```tsx
              <SidebarNavLink
                to="/costs"
                icon={Coins}
                label="Costs"
                comingSoon
              />
```

To:
```tsx
              <SidebarNavLink
                to="/costs"
                icon={Coins}
                label="Costs"
              />
```

**Step 3: Verify type check passes**

Run: `cd dashboard && pnpm type-check`
Expected: No errors

**Step 4: Commit**

```bash
git add dashboard/src/router.tsx dashboard/src/components/DashboardSidebar.tsx
git commit -m "$(cat <<'EOF'
feat(routing): add /costs route and enable sidebar link

- Add costs route with costsLoader and lazy-loaded CostsPage
- Remove "Coming Soon" badge from Costs sidebar link

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Run Full Test Suite and Fix Issues

**Files:** None (verification only)

**Step 1: Run backend tests**

Run: `uv run pytest tests/unit/ -v`
Expected: All tests pass

**Step 2: Run frontend tests**

Run: `cd dashboard && pnpm test:run`
Expected: All tests pass

**Step 3: Run type checks**

Run: `cd dashboard && pnpm type-check && uv run mypy amelia`
Expected: No errors

**Step 4: Run linting**

Run: `cd dashboard && pnpm lint && uv run ruff check amelia`
Expected: No errors (or fix any that appear)

**Step 5: Commit any fixes**

```bash
# If fixes needed:
git add -A
git commit -m "$(cat <<'EOF'
fix: address test and lint issues from full suite

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: Manual Verification

**Files:** None (manual testing)

**Step 1: Start the backend server**

Run: `uv run amelia dev`
Expected: Server starts on localhost:8420

**Step 2: Navigate to Costs page**

Open: `http://localhost:8420/costs`
Expected: Page loads with:
- Header showing "COSTS" / "Usage & Spending"
- Total cost in center
- Date range buttons (7d, 30d, 90d, All)
- Summary row with metrics
- Trend chart (may be empty if no data)
- Model breakdown table (may be empty if no data)

**Step 3: Test date range switching**

Click different preset buttons.
Expected: URL updates with ?preset=Xd and data refreshes

**Step 4: Test model drill-down**

Click a row in the model breakdown table.
Expected: Navigates to /history?model=<model-name>

---

## Summary

This plan implements the Costs view feature in 12 tasks:

1. **Types (Frontend)** - Add UsageResponse types
2. **Models (Backend)** - Add Pydantic usage models
3. **Repository (Backend)** - Add usage aggregation methods
4. **Route (Backend)** - Add GET /api/usage endpoint
5. **API Client (Frontend)** - Add getUsage method
6. **Chart Component (Frontend)** - Install shadcn chart
7. **Trend Chart (Frontend)** - Create CostsTrendChart
8. **Loader (Frontend)** - Create costsLoader
9. **Page (Frontend)** - Create CostsPage
10. **Routing (Frontend)** - Add route and enable sidebar
11. **Verification** - Run full test suite
12. **Manual Testing** - Verify in browser

Each task follows TDD: write failing test, implement, verify pass, commit.
