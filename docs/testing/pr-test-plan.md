# Dashboard Components Manual Testing Plan

**Branch:** `feature/dashboard-components`
**Feature:** Dashboard UI components for workflow visualization and management

## Overview

This PR introduces the core UI components for Amelia's web dashboard, implementing a hybrid approach:
- **ai-elements components** for queue patterns (JobQueue, ActivityLog)
- **Custom React Flow components** for workflow visualization with aviation theme
- **shadcn/ui primitives** for layout (Sidebar, Progress, Empty states)

Manual testing is needed because:
1. Visual components require human verification of layout, animations, and responsiveness
2. React Flow integration requires browser-based interaction testing
3. Real-time WebSocket event merging cannot be fully automated
4. Keyboard navigation and accessibility need manual validation

---

## Prerequisites

### Environment Setup

```bash
# 1. Navigate to dashboard
cd /Users/ka/github/amelia-langgraph-bridge/dashboard

# 2. Install dependencies
pnpm install

# 3. Start the development server
pnpm run dev

# 4. Verify setup - should open at http://localhost:3000
```

### Backend Server (Optional)

For full integration testing with real data:
```bash
# In a separate terminal
cd /Users/ka/github/amelia-langgraph-bridge
uv run amelia server --reload
```

---

## Test Scenarios

### TC-01: WorkflowCanvas Rendering

**Objective:** Verify React Flow canvas renders workflow nodes correctly with aviation theme

**Steps:**
1. Navigate to a workflow detail page (or create test route with mock pipeline data)
2. Observe the workflow canvas area

**Expected Result:**
- Dot pattern background visible with low opacity
- WorkflowNode components render as map pin icons (not cards)
- Nodes show status colors: green (completed), amber (active), gray (pending), red (blocked)
- Edges connect nodes with time labels
- Stage progress counter appears top-right (e.g., "2/4 stages")
- Canvas is non-interactive (no dragging, zooming, or selection)

**Verification Commands:**
```bash
# Ensure React Flow is properly bundled
pnpm run build
```

---

### TC-02: WorkflowNode Status Variants

**Objective:** Verify node visual states match design spec

**Steps:**
1. View workflow with nodes in different states
2. Check each status variant

**Expected Result:**
- `completed`: Green beacon glow, solid fill, checkmark or success indicator
- `active`: Amber pulsing animation, "breathing" effect
- `pending`: Gray/muted appearance, no glow
- `blocked`: Red indicator, warning styling
- All nodes show label and optional subtitle
- Token count displays when provided

---

### TC-03: WorkflowEdge Styling

**Objective:** Verify edge rendering with time labels and status styling

**Steps:**
1. Observe edges between workflow nodes

**Expected Result:**
- Edges connect source to target nodes smoothly
- Time labels render at edge midpoint (e.g., "12s", "~30s")
- Edge color matches status: green (completed), amber (active), gray (pending)
- Active edges show animated flow indicator (gradient or dash animation)

---

### TC-04: DashboardSidebar Navigation

**Objective:** Verify sidebar component with collapsible sections

**Steps:**
1. Load dashboard layout
2. Click "Workflows" menu item
3. Test keyboard navigation (Tab, Enter, Arrow keys)
4. Resize browser to mobile width (<768px)

**Expected Result:**
- Sidebar displays AMELIA branding with icon
- Workflows section expands/collapses on click
- Sub-items (Active, Completed, Failed) appear when expanded
- ChevronDown icon rotates 180deg when open
- Focus-visible ring appears on keyboard navigation (3px ring)
- Mobile: Sidebar converts to sheet/drawer overlay

---

### TC-05: JobQueue Component

**Objective:** Verify collapsible job queue with workflow list

**Steps:**
1. View JobQueue with multiple workflows
2. Click the collapsible header
3. Select a workflow item

**Expected Result:**
- Header shows "JOB QUEUE" with count badge
- Chevron rotates on collapse/expand
- WorkflowSummary items display: issue ID, worktree name, status, current stage
- Selected item has distinct styling
- Empty state shows "No active workflows" message

---

### TC-06: JobQueueItem Selection

**Objective:** Verify workflow item selection and status display

**Steps:**
1. Click on different JobQueueItem components
2. Observe status badges

**Expected Result:**
- Click triggers onSelect callback with workflow ID
- Selected item has highlight/border styling
- StatusBadge shows correct variant:
  - `pending`: Yellow/amber
  - `running`: Blue with pulse
  - `completed`: Green
  - `failed`: Red
  - `blocked`: Orange/warning

---

### TC-07: ActivityLog Real-time Updates

**Objective:** Verify activity log merges loader data with WebSocket events

**Steps:**
1. Open workflow detail with ActivityLog
2. Connect backend with WebSocket
3. Trigger events (or mock via store)

**Expected Result:**
- Initial events load from server (loader)
- Header shows event count
- Terminal aesthetic: scanlines overlay visible
- Blinking cursor animation at bottom
- New events append without duplicates
- Auto-scroll to bottom on new events
- `aria-live="polite"` announces updates to screen readers

---

### TC-08: ActivityLogItem Formatting

**Objective:** Verify terminal-style log entry rendering

**Steps:**
1. View ActivityLog with various event types

**Expected Result:**
- Monospace font (font-mono)
- Timestamp prefix in muted color
- Event message with appropriate styling
- Different event types may have color coding

---

### TC-09: ApprovalControls Workflow

**Objective:** Verify approval/rejection flow with useFetcher

**Steps:**
1. View ApprovalControls in pending state
2. Click "Approve" button
3. Observe loading state
4. Test "Reject" button similarly

**Expected Result:**
- Pending state: Shows plan summary, Approve (green) and Reject (outline/red) buttons
- Loading: Buttons show Loader spinner, disabled state
- Approved: Shows checkmark with "Plan approved. Implementation starting..."
- Rejected: Shows X with "Plan rejected. Awaiting revision..."
- Form posts to correct action routes (`/workflows/{id}/approve`, `/workflows/{id}/reject`)

---

### TC-10: WorkflowProgress Bar

**Objective:** Verify progress calculation and display

**Steps:**
1. View WorkflowProgress with various completion states

**Expected Result:**
- Progress bar fills proportionally to completed/total stages
- Percentage or stage count displayed
- Animation on progress changes
- Accessible: proper role and aria attributes

---

### TC-11: WorkflowEmptyState Variants

**Objective:** Verify empty state displays for different scenarios

**Steps:**
1. View dashboard with no workflows
2. Check different empty state variants

**Expected Result:**
- `no-workflows`: Generic empty state with create workflow CTA
- `no-active`: "No active workflows" message
- `no-completed`: "No completed workflows yet"
- `error`: Error state with retry option
- Empty component uses shadcn/ui Empty primitive styling

---

### TC-12: Skeleton Loading States

**Objective:** Verify loading skeletons match component dimensions

**Steps:**
1. Slow network or loading state
2. Observe skeleton components

**Expected Result:**
- JobQueueSkeleton: Matches JobQueueItem dimensions
- ActivityLogSkeleton: Matches log entry dimensions
- Pulse animation visible
- Skeletons replaced by real content on load

---

### TC-13: Keyboard Accessibility

**Objective:** Verify full keyboard navigation support

**Steps:**
1. Tab through all interactive elements
2. Test Enter/Space activation
3. Test Escape to close collapsibles/modals

**Expected Result:**
- All buttons, links, and controls are focusable
- Focus-visible ring (3px) appears on Tab navigation
- Enter/Space activates buttons and toggles
- Collapsible sections work with keyboard
- No focus traps (can Tab out of components)

---

### TC-14: Dark Mode / Theme

**Objective:** Verify components render correctly in dark theme

**Steps:**
1. Toggle dark mode (if theme toggle exists)
2. Inspect CSS variable usage

**Expected Result:**
- All components use CSS variables (`var(--color-*)`)
- No hardcoded colors
- Status colors maintain contrast in both themes
- Text remains readable
- Border colors adjust appropriately

---

### TC-15: Component Index Exports

**Objective:** Verify all components are properly exported

**Steps:**
1. Check `dashboard/src/components/index.ts`

**Expected Result:**
- All new components exported:
  - ActivityLog, ActivityLogItem, ActivityLogSkeleton
  - ApprovalControls
  - DashboardSidebar
  - JobQueue, JobQueueItem, JobQueueSkeleton
  - StatusBadge
  - WorkflowCanvas
  - WorkflowEmptyState
  - WorkflowHeader
  - WorkflowProgress
  - flow/WorkflowNode, flow/WorkflowEdge

**Verification Commands:**
```bash
# Type check exports
cd /Users/ka/github/amelia-langgraph-bridge/dashboard
pnpm run type-check
```

---

## Test Environment Cleanup

After testing:
```bash
# Stop dev server (Ctrl+C)

# Stop backend if running
# Ctrl+C in backend terminal

# Optional: Clean build artifacts
rm -rf dist node_modules/.vite
```

---

## Test Result Template

| Test ID | Description | Status | Notes |
|---------|-------------|--------|-------|
| TC-01 | WorkflowCanvas Rendering | [ ] Pass / [ ] Fail | |
| TC-02 | WorkflowNode Status Variants | [ ] Pass / [ ] Fail | |
| TC-03 | WorkflowEdge Styling | [ ] Pass / [ ] Fail | |
| TC-04 | DashboardSidebar Navigation | [ ] Pass / [ ] Fail | |
| TC-05 | JobQueue Component | [ ] Pass / [ ] Fail | |
| TC-06 | JobQueueItem Selection | [ ] Pass / [ ] Fail | |
| TC-07 | ActivityLog Real-time Updates | [ ] Pass / [ ] Fail | |
| TC-08 | ActivityLogItem Formatting | [ ] Pass / [ ] Fail | |
| TC-09 | ApprovalControls Workflow | [ ] Pass / [ ] Fail | |
| TC-10 | WorkflowProgress Bar | [ ] Pass / [ ] Fail | |
| TC-11 | WorkflowEmptyState Variants | [ ] Pass / [ ] Fail | |
| TC-12 | Skeleton Loading States | [ ] Pass / [ ] Fail | |
| TC-13 | Keyboard Accessibility | [ ] Pass / [ ] Fail | |
| TC-14 | Dark Mode / Theme | [ ] Pass / [ ] Fail | |
| TC-15 | Component Index Exports | [ ] Pass / [ ] Fail | |

---

## Agent Execution Notes

### For LLM Agent Executing This Plan:

1. **Use Playwright** for browser automation where possible
2. **Visual tests** (TC-01 through TC-03) require screenshot comparison or human review
3. **Real-time tests** (TC-07) need WebSocket mock or actual backend
4. **Accessibility tests** (TC-13) can use `@axe-core/playwright` for automated checks
5. **Report failures** with exact error messages and screenshots

### Mock Data for Testing

```typescript
// Example pipeline data for WorkflowCanvas
const mockPipeline = {
  nodes: [
    { id: 'plan', label: 'Plan', status: 'completed', tokens: '2.1k' },
    { id: 'develop', label: 'Develop', status: 'active', subtitle: 'Writing code...' },
    { id: 'review', label: 'Review', status: 'pending' },
    { id: 'done', label: 'Done', status: 'pending' },
  ],
  edges: [
    { from: 'plan', to: 'develop', label: '12s', status: 'completed' },
    { from: 'develop', to: 'review', label: '~30s', status: 'active' },
    { from: 'review', to: 'done', label: '~10s', status: 'pending' },
  ],
};

// Example workflows for JobQueue
const mockWorkflows = [
  { id: '1', issue_id: 'PROJ-123', worktree_name: 'feature/auth', status: 'running', current_stage: 'develop' },
  { id: '2', issue_id: 'PROJ-456', worktree_name: 'fix/login-bug', status: 'pending', current_stage: 'plan' },
];
```

---

## Key Changes in This Branch

The following changes should be verified through testing:

1. **WorkflowCanvas** (`dashboard/src/components/WorkflowCanvas.tsx`):
   - Custom React Flow integration
   - Aviation theme with dot background
   - Non-interactive canvas settings

2. **WorkflowNode/WorkflowEdge** (`dashboard/src/components/flow/`):
   - MapPin icon nodes (not Card-based)
   - Status-based beacon animations
   - Time label edges with animated flow

3. **DashboardSidebar** (`dashboard/src/components/DashboardSidebar.tsx`):
   - shadcn/ui Sidebar integration
   - Collapsible navigation sections
   - Mobile responsive behavior

4. **JobQueue/ActivityLog** (`dashboard/src/components/`):
   - Collapsible queue sections
   - Real-time event merging
   - Terminal aesthetic styling

5. **ApprovalControls** (`dashboard/src/components/ApprovalControls.tsx`):
   - useFetcher for form submissions
   - Three-state flow (pending/approved/rejected)
   - Loading indicators

6. **New UI primitives** (`dashboard/src/components/ui/`):
   - Sidebar, Sheet, Separator, Tooltip (extended)
   - Empty state component
   - Input component
