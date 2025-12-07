# PageHeader Compound Component Design

## Overview

Replace `WorkflowHeader` with a flexible `PageHeader` compound component that provides consistent header styling across all dashboard views.

## Requirements

1. Header extends edge-to-edge (full content width)
2. Consistent 3-column grid layout across all pages
3. Slots conditionally render - unused slots collapse
4. Same visual styling/typography as current WorkflowHeader

## Component API

```tsx
<PageHeader>
  <PageHeader.Left>
    <PageHeader.Label>WORKFLOW</PageHeader.Label>
    <PageHeader.Title>ISSUE-123</PageHeader.Title>
    <PageHeader.Subtitle>feature/auth-fix</PageHeader.Subtitle>
  </PageHeader.Left>
  <PageHeader.Center>
    <PageHeader.Label>ELAPSED</PageHeader.Label>
    <PageHeader.Value glow>02:34</PageHeader.Value>
  </PageHeader.Center>
  <PageHeader.Right>
    <StatusBadge status="in_progress" showPulse />
  </PageHeader.Right>
</PageHeader>
```

### Slot Behavior

| Slots Present | Grid Columns |
|---------------|--------------|
| Left + Center + Right | `grid-cols-[1fr_auto_auto]` |
| Left + Center | `grid-cols-[1fr_auto]` |
| Left + Right | `grid-cols-[1fr_auto]` |
| Left only | Single column |

### Typography Helpers

| Component | Styling |
|-----------|---------|
| `Label` | `text-xs font-semibold tracking-widest text-muted-foreground` |
| `Title` | `text-3xl font-bold tracking-wider text-foreground` |
| `Subtitle` | `font-mono text-sm text-muted-foreground` |
| `Value` | `font-mono text-2xl font-semibold text-primary` (optional `glow` prop) |

## Page Usage

### WorkflowsPage & WorkflowDetailPage
- Left: WORKFLOW label, issue ID, worktree name
- Center: ELAPSED label, formatted time with glow
- Right: StatusBadge with pulse indicator

### HistoryPage
- Left: HISTORY label, "Past Runs" title
- Center: TOTAL label, workflow count
- Right: (none - collapses)

### LogsPage
- Left: MONITORING label, "Logs" title
- Center/Right: (none - collapses)

## File Changes

### New
- `dashboard/src/components/PageHeader.tsx`
- `dashboard/src/components/PageHeader.test.tsx`

### Deleted
- `dashboard/src/components/WorkflowHeader.tsx`
- `dashboard/src/components/WorkflowHeader.test.tsx`

### Modified
- `dashboard/src/pages/WorkflowsPage.tsx` - Remove Card wrapper, use PageHeader
- `dashboard/src/pages/WorkflowDetailPage.tsx` - Replace WorkflowHeader
- `dashboard/src/pages/HistoryPage.tsx` - Replace custom header
- `dashboard/src/pages/LogsPage.tsx` - Replace placeholder header
