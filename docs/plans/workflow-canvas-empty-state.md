# Plan: WorkflowCanvas Always Visible with Empty State

## Problem

Currently, the `WorkflowCanvas` component only renders when:
1. A workflow is selected AND
2. The workflow has a plan (`buildPipeline()` returns non-null)

When no workflow is selected (or click-outside deselects), the canvas disappears entirely, causing a jarring layout shift.

## Goal

The WorkflowCanvas should **always** be visible on the workflows page. When no workflow is selected, display an empty/default state instead of hiding the component.

## Current Flow

```
WorkflowsPage.tsx (line 119):
{pipeline && <WorkflowCanvas pipeline={pipeline} />}
```

This conditional rendering hides the canvas when `pipeline` is null.

## Implementation Plan

### Task 1: Update WorkflowCanvas to Support Empty State

**File:** `dashboard/src/components/WorkflowCanvas.tsx`

**Changes:**
1. Make `pipeline` prop optional: `pipeline?: Pipeline`
2. Add empty state rendering when no pipeline is provided
3. Empty state design:
   - Same container dimensions (h-64)
   - Subtle background with dot pattern (keep consistency)
   - Centered placeholder content:
     - Icon (workflow/diagram icon from Lucide)
     - Text: "Select a workflow to view its pipeline"
   - Muted styling to indicate inactive state

### Task 2: Update WorkflowsPage to Always Render Canvas

**File:** `dashboard/src/pages/WorkflowsPage.tsx`

**Changes:**
1. Remove conditional rendering: `{pipeline && <WorkflowCanvas ... />}`
2. Always render: `<WorkflowCanvas pipeline={pipeline ?? undefined} />`
3. The canvas component handles the empty state internally

### Task 3: Add Loading State (Optional Enhancement)

When a workflow is selected but detail is still loading (`isLoadingDetail` is true), show a loading indicator in the canvas instead of the empty state.

**File:** `dashboard/src/components/WorkflowCanvas.tsx`

**Changes:**
1. Add optional `isLoading?: boolean` prop
2. Show skeleton/spinner when loading
3. Pass `isLoading={isLoadingDetail}` from WorkflowsPage

### Task 4: Write Tests

**File:** `dashboard/src/components/WorkflowCanvas.test.tsx`

**Tests:**
1. Renders empty state when no pipeline provided
2. Renders pipeline visualization when pipeline provided
3. Shows loading state when `isLoading` is true
4. Empty state has correct accessibility attributes

## Visual Design

### Empty State
```
┌─────────────────────────────────────────────────────────────┐
│  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  │
│  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  │
│  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  │
│  ·  ·  ·  ·  ·  ·     [⎔]     ·  ·  ·  ·  ·  ·  ·  ·  ·  │
│  ·  ·  ·  ·  Select a workflow  ·  ·  ·  ·  ·  ·  ·  ·  ·  │
│  ·  ·  ·  ·  to view pipeline   ·  ·  ·  ·  ·  ·  ·  ·  ·  │
│  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  │
│  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  │
└─────────────────────────────────────────────────────────────┘
```

### Loading State
```
┌─────────────────────────────────────────────────────────────┐
│  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  │
│  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  │
│  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  │
│  ·  ·  ·  ·  ·  ·     [◌]     ·  ·  ·  ·  ·  ·  ·  ·  ·  │
│  ·  ·  ·  ·  ·  Loading...  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  │
│  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  │
│  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  │
│  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  │
└─────────────────────────────────────────────────────────────┘
```

## Files to Modify

1. `dashboard/src/components/WorkflowCanvas.tsx` - Add empty/loading states
2. `dashboard/src/pages/WorkflowsPage.tsx` - Remove conditional, pass loading state
3. `dashboard/src/components/WorkflowCanvas.test.tsx` - Add tests (create if needed)

## Acceptance Criteria

- [ ] WorkflowCanvas always renders on the workflows page
- [ ] Empty state shown when no workflow selected
- [ ] Loading state shown when workflow selected but detail loading
- [ ] Normal pipeline view when workflow with plan is selected
- [ ] No layout shift when switching between states
- [ ] Tests pass for all three states
