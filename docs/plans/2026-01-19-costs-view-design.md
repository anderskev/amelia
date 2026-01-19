# Costs View Design

**Date:** 2026-01-19
**Status:** Draft

## Overview

Implement a comprehensive Costs view in the Amelia dashboard for monitoring, analyzing, and optimizing LLM usage costs. The view provides flexible date ranges, trend visualization, and model-based cost breakdown.

## Requirements

- **Cost monitoring**: Track spending over time
- **Cost analysis**: Understand where money goes (which models cost most)
- **Cost optimization**: Optional efficiency metrics to identify savings opportunities
- **Flexible time ranges**: User-selectable with sensible defaults (7d, 30d, 90d, All)

## Page Layout

```
┌─────────────────────────────────────────────────────┐
│  PageHeader                                         │
│  COSTS / Usage & Spending    $127.43    [Date Range]│
├─────────────────────────────────────────────────────┤
│  Summary Row                                        │
│  Total: $127.43 · 24 workflows · 1.2M tokens · 47m  │
│                          [Show efficiency metrics]  │
├─────────────────────────────────────────────────────┤
│  Trend Chart (shadcn/ui chart)                      │
│  Daily cost line chart with hover tooltips          │
│                                                     │
├─────────────────────────────────────────────────────┤
│  Model Breakdown (shadcn/ui table)                  │
│  Model            Workflows   Tokens      Cost      │
│  claude-sonnet-4      18      892K      $42.17      │
│  claude-opus-4         6      340K      $85.26      │
│  (clickable rows → filtered History view)           │
└─────────────────────────────────────────────────────┘
```

## Components

### Header
- Uses existing `PageHeader` component
- Left: "COSTS" label, "Usage & Spending" title
- Center: Total spend for selected period
- Right: Date range picker with presets (7d, 30d, 90d, All) and custom range via shadcn `Popover` + `Calendar`

### Summary Row
- Plain text with muted separators (not cards)
- Shows: total cost, workflow count, total tokens, total duration
- Right-aligned toggle for efficiency metrics
- Similar styling to `UsageCard` summary line

### Trend Chart
- Uses shadcn/ui `chart` component (wraps Recharts)
- X-axis: dates in selected range
- Y-axis: cost in USD
- Hover tooltip: date, cost, workflow count
- Granularity auto-adjusts: daily for <60 days, weekly for longer
- When efficiency toggle on: secondary line showing "cost without caching"

### Model Breakdown Table
- Uses shadcn/ui `Table` component
- Columns: Model, Workflows, Tokens, Cost, Share (%)
- Sortable by any column (default: Cost descending)
- Clickable rows → navigate to `/history?model=<model>`
- When efficiency toggle on: add Cache Hit % and Savings columns

## API Design

### `GET /api/usage`

Extensible endpoint for usage metrics (not just costs).

**Request**
```
GET /api/usage?start=2026-01-01&end=2026-01-19
GET /api/usage?preset=30d
```

**Response**
```typescript
interface UsageResponse {
  summary: {
    total_cost_usd: number;
    total_workflows: number;
    total_tokens: number;
    total_duration_ms: number;
    // Optional efficiency metrics
    cache_hit_rate?: number;
    cache_savings_usd?: number;
  };
  trend: Array<{
    date: string;  // ISO date
    cost_usd: number;
    workflows: number;
  }>;
  by_model: Array<{
    model: string;
    workflows: number;
    tokens: number;
    cost_usd: number;
    // Optional efficiency metrics
    cache_hit_rate?: number;
    cache_savings_usd?: number;
  }>;
}
```

## Routing & State

### Route
```
/costs → CostsPage.tsx
```

### URL State
Date range stored in URL for shareability:
```
/costs?start=2026-01-01&end=2026-01-19
/costs?preset=7d
```

Default: `preset=30d`

### Page State
- `showEfficiency: boolean` - toggle state (local useState)

### Data Loading
React Router loader pattern:
```typescript
export async function costsLoader({ request }: LoaderFunctionArgs) {
  const url = new URL(request.url);
  const start = url.searchParams.get('start');
  const end = url.searchParams.get('end');
  const preset = url.searchParams.get('preset') ?? '30d';

  return fetchUsageData({ start, end, preset });
}
```

## States

- **Loading**: Skeleton placeholders for summary, chart, and table
- **Error**: Alert component with retry button
- **Empty**: "No usage data for this period" with suggestion to adjust range

## File Structure

### Frontend (New)
```
dashboard/src/
├── pages/
│   ├── CostsPage.tsx
│   └── CostsPage.test.tsx
├── components/
│   └── CostsTrendChart.tsx
└── components/ui/
    └── chart.tsx  # via npx shadcn@latest add chart
```

### Backend (New)
```
amelia/server/
├── routes/
│   └── usage.py
└── repository/
    └── usage.py  # or extend existing repository
```

### Modifications
- `DashboardSidebar.tsx` - Enable Costs link, remove "Coming Soon" badge
- `router.tsx` - Add `/costs` route and loader
- `dashboard/src/types/index.ts` - Add `UsageResponse` types
- `HistoryPage.tsx` - Support optional `?model=` query param for drill-down

## Dependencies

- Add `recharts` (peer dependency for shadcn chart)
- Run `npx shadcn@latest add chart`

## Future Considerations

The `/api/usage` endpoint is intentionally broad to support future expansion:
- Agent-based breakdown (Architect/Developer/Reviewer)
- Workflow-based breakdown (top N expensive)
- Error rate metrics
- Success/failure rate tracking
- Time-to-completion analytics
