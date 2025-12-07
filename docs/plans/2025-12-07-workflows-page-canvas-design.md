# WorkflowsPage Canvas Design

**Date:** 2025-12-07
**Status:** Approved

## Overview

Update the WorkflowsPage to match the design mock by displaying a workflow canvas for the active job. Currently, the page only shows the JobQueue list. The new layout will show the full workflow pipeline visualization at the top with the job queue and activity log below.

## Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  WORKFLOW HEADER + CANVAS (full width)                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Issue → Architect → Developer → Reviewer → Done         ││
│  └─────────────────────────────────────────────────────────┘│
├───────────────────┬─────────────────────────────────────────┤
│  JOB QUEUE (1/3)  │  ACTIVITY LOG (2/3)                     │
│  ┌─────────────┐  │  ┌─────────────────────────────────────┐│
│  │ #8 RUNNING  │  │  │ 14:32:07Z [ARCHITECT] Issue #8...   ││
│  │ #7 DONE     │  │  │ 14:32:45Z [ARCHITECT] Plan approved ││
│  │ #9 QUEUED   │  │  │ 14:33:12Z [DEVELOPER] Task received ││
│  └─────────────┘  │  └─────────────────────────────────────┘│
└───────────────────┴─────────────────────────────────────────┘
```

- Canvas at TOP, full width of page
- Below: JobQueue on LEFT (1/3 width), ActivityLog on RIGHT (2/3 width)

## State Selection Logic

Which workflow to display in the canvas/activity area:

```typescript
function getActiveWorkflow(workflows: WorkflowSummary[]): WorkflowSummary | null {
  // Priority 1: Running workflow
  const running = workflows.find(w => w.status === 'in_progress');
  if (running) return running;

  // Priority 2: Last completed (most recent by updated_at)
  const completed = workflows
    .filter(w => w.status === 'completed')
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());

  return completed[0] ?? null;
}
```

### Display States

| State | Canvas Area | Activity Log |
|-------|-------------|--------------|
| Running workflow exists | Show running workflow's pipeline | Live activity stream |
| No running, has completed | Show last completed pipeline | Historical events |
| No workflows at all | `WorkflowEmptyState` (full page) | - |

### Selection Behavior

- User can click any job in the queue to view its details
- This updates the canvas + activity log without page navigation
- A subtle highlight indicates which job is currently displayed

## Data Fetching Strategy

**Pre-fetch active workflow in loader:**
- Route loader fetches both `workflows` list AND detail for the active one
- Instant display for the default view
- Fetch on-demand only when user clicks a different job

```typescript
// loader
export async function loader() {
  const workflows = await fetchWorkflows();
  const active = getActiveWorkflow(workflows);
  const activeDetail = active ? await fetchWorkflowDetail(active.id) : null;
  return { workflows, activeDetail };
}
```

**For user-selected jobs:** Add a `useWorkflowDetail(id)` hook that:
- Returns cached data if available (from loader)
- Fetches if not cached
- Shows skeleton in ActivityLog while loading

## Component Structure

```tsx
export default function WorkflowsPage() {
  const { workflows, activeDetail } = useLoaderData();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // Auto-select active workflow (running or last completed)
  const activeWorkflow = getActiveWorkflow(workflows);
  const displayedId = selectedId ?? activeWorkflow?.id ?? null;

  // Use pre-fetched detail or fetch on demand
  const { detail, isLoading } = useWorkflowDetail(displayedId, activeDetail);

  if (workflows.length === 0) {
    return <WorkflowEmptyState variant="no-workflows" />;
  }

  return (
    <div className="flex flex-col h-full">
      {/* Top: Header + Canvas (full width) */}
      {detail && (
        <>
          <WorkflowHeader workflow={detail} />
          <WorkflowCanvas pipeline={buildPipeline(detail)} className="border-b" />
        </>
      )}

      {/* Bottom: Queue + Activity (split) */}
      <div className="flex-1 grid grid-cols-[1fr_2fr] gap-4 p-4 overflow-hidden">
        <JobQueue
          workflows={workflows}
          selectedId={displayedId}
          onSelect={setSelectedId}
        />
        {detail ? (
          <ActivityLog workflowId={detail.id} initialEvents={detail.recent_events} />
        ) : isLoading ? (
          <ActivityLogSkeleton />
        ) : null}
      </div>
    </div>
  );
}
```

## Implementation Tasks

### 1. New hook: `useWorkflowDetail(id, preloadedDetail?)`
- Fetches workflow detail on demand
- Uses preloaded detail if ID matches
- Caches results to avoid re-fetching
- Returns `{ detail, isLoading, error }`

### 2. Update `WorkflowsPage.tsx`
- Add loader function to pre-fetch active workflow detail
- Implement the two-row layout (canvas top, queue/log bottom)
- Add `selectedId` state for user selection
- Add `getActiveWorkflow()` helper function
- Wire up pipeline building from workflow detail

### 3. Update `JobQueue` component
- Ensure it highlights the selected job (may already work via `selectedId` prop)
- Remove navigation on click (just call `onSelect`, no `navigate()`)

### 4. Styling adjustments
- Canvas area: full width, appropriate height
- Bottom grid: `grid-cols-[1fr_2fr]` for 1/3 + 2/3 split
- Ensure proper overflow/scroll behavior in both panels

### 5. Tests
- Update `WorkflowsPage.test.tsx` for new layout
- Test selection logic (running → completed → none)
- Test loader data fetching
- Test user selection updates display
