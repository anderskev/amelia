# Workflow Canvas Simplification with ai-elements

**Date:** 2026-01-06
**Issue:** #218 - Workflow canvas nodes not showing active state during execution
**Branch:** `fix/218-workflow-canvas-active-state`

## Problem

1. **Bug:** Workflow canvas nodes remain in "pending" state even when agents are actively running. The active styling (glow, pulse animation) never appears until the stage completes.

2. **Code complexity:** Custom `WorkflowNode` and `WorkflowCanvas` components duplicate functionality available in the `ai-elements` library.

3. **Hardcoded pipeline:** Current implementation shows fixed 3 nodes (architect, developer, reviewer) instead of dynamically showing all spawned agents with their iterations.

## Solution

Replace custom components with `ai-elements` library components and rebuild the pipeline logic to be event-driven rather than derived from stale loader data.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Integration | npm install `ai-elements` | Published package, maintained separately |
| Status styling | Pass className to Node | Node extends Card props, no wrapper needed |
| Scope | Full (Canvas + Node + pipeline) | Fix bug + simplify + improve UX |
| Data source | Events accumulation | Real-time updates, no loader lag |
| Node granularity | One per agent type, expandable | Clean overview with drill-down |
| Expansion behavior | Inline accordion | Keeps context on canvas |

## Component Architecture

### New Structure

```
dashboard/src/components/
├── WorkflowCanvas.tsx        # Simplified - uses ai-elements Canvas
└── AgentNode.tsx             # New - uses ai-elements Node with status styling

dashboard/src/utils/
└── pipeline.ts               # Rewritten - builds from events, not current_stage
```

### Dependencies

```json
{
  "ai-elements": "^latest"
}
```

## Data Model

### New Types

```typescript
// utils/pipeline.ts

interface AgentIteration {
  id: string;
  startedAt: string;
  completedAt?: string;
  status: 'running' | 'completed' | 'failed';
  message?: string;  // e.g., "Requested changes" or "Approved"
}

interface AgentNodeData {
  agentType: string;           // 'architect', 'developer', 'reviewer'
  status: 'pending' | 'active' | 'completed' | 'blocked';
  iterations: AgentIteration[];
  isExpanded: boolean;
}
```

### Pipeline Builder

```typescript
function buildPipelineFromEvents(events: WorkflowEvent[]): Pipeline {
  // 1. Group stage_started/stage_completed events by agent type
  // 2. Each stage_started creates an iteration
  // 3. Matching stage_completed closes it
  // 4. Order nodes by first appearance
  // 5. Create edges between adjacent agent types
}
```

### Data Flow

1. `WorkflowDetailPage` merges `workflow.recent_events` with real-time WebSocket events
2. Pipeline builder groups events → creates nodes with iterations
3. `WorkflowCanvas` receives dynamic node/edge arrays
4. New WebSocket events → store updates → pipeline rebuilds immediately

## Visual Design

### Status Styling

```typescript
const statusClasses: Record<Status, string> = {
  pending: 'opacity-50 border-border',
  active: 'border-primary bg-primary/10 shadow-lg shadow-primary/20',
  completed: 'border-status-completed/40 bg-status-completed/5',
  blocked: 'border-destructive/40 bg-destructive/5',
};
```

### AgentNode Layout

```
┌─────────────────────────────────┐
│ [Icon] Architect      [2 runs] │  ← NodeHeader with iteration badge
├─────────────────────────────────┤
│ In progress...                  │  ← NodeContent (subtitle when active)
│                                 │
│ ▼ Iteration History (expanded)  │  ← Collapsible trigger
│   ├─ Run 1: Completed 2m ago    │
│   └─ Run 2: Running...          │
└─────────────────────────────────┘
```

### Edge Types

| Status | ai-elements Edge | Visual |
|--------|------------------|--------|
| completed | Default BaseEdge | Solid stroke |
| active | `Edge.Animated` | Moving circle animation |
| pending | `Edge.Temporary` | Dashed line |

## Bug Fix Mechanism

### Why Current Implementation Fails

1. `buildPipeline(workflow)` uses `workflow.current_stage` from loader
2. Even with `useAutoRevalidation`, there's round-trip delay to fetch updated data
3. Fast stage transitions may complete before revalidated data arrives

### Why New Implementation Works

1. Pipeline builds directly from events array, not `current_stage`
2. New events from WebSocket added to store → pipeline rebuilds instantly
3. No loader dependency for active state

```typescript
// WorkflowDetailPage.tsx
const { eventsByWorkflow } = useWorkflowStore();
const allEvents = [
  ...workflow.recent_events,                  // Initial from loader
  ...(eventsByWorkflow[workflow.id] ?? [])    // Real-time additions
];
const pipeline = buildPipelineFromEvents(allEvents);
```

## Implementation Plan

### Files to Modify

| Action | File | Changes |
|--------|------|---------|
| Install | `package.json` | Add `ai-elements` dependency |
| Rewrite | `utils/pipeline.ts` | New `buildPipelineFromEvents()` function |
| Rewrite | `WorkflowCanvas.tsx` | Use ai-elements Canvas, simplified |
| Create | `components/AgentNode.tsx` | New node with ai-elements + status styling |
| Delete | `components/flow/WorkflowNode.tsx` | Replaced by AgentNode |
| Modify | `pages/WorkflowDetailPage.tsx` | Merge loader + real-time events |
| Update | `WorkflowCanvas.test.tsx` | Update tests for new structure |

### Testing

1. **Unit tests** - `buildPipelineFromEvents()` with various event sequences
2. **Component tests** - AgentNode renders correctly for each status
3. **Integration test** - Simulate WebSocket events, verify nodes update
4. **Manual test** - Run real workflow, observe active state updates

### Estimated Impact

- ~150 lines removed (custom node + edge styling)
- ~100 lines added (AgentNode + new pipeline builder)
- Net simplification + bug fix
