# Quick Shot Feature Design

## Overview

Add a "Quick Shot" modal to the dashboard for starting noop tracker workflows directly from the UI. Replaces the "Roundtable" placeholder in the sidebar.

## User Flow

1. User clicks "Quick Shot" (lightning icon) in sidebar under TOOLS
2. Modal opens with form fields
3. User fills required fields, clicks "Start Workflow"
4. API creates workflow, modal closes
5. User navigates to `/workflows/{id}` to monitor progress

## UI Layout

```
┌─────────────────────────────────────────────┐
│  ⚡ Quick Shot                          [X] │
├─────────────────────────────────────────────┤
│                                             │
│  Task ID *                                  │
│  ┌─────────────────────────────────────┐   │
│  │ TASK-001                            │   │
│  └─────────────────────────────────────┘   │
│  Unique identifier for this task            │
│                                             │
│  Worktree Path *                            │
│  ┌─────────────────────────────────────┐   │
│  │ /Users/me/projects/my-repo          │   │
│  └─────────────────────────────────────┘   │
│  Absolute path to git worktree              │
│                                             │
│  Profile                                    │
│  ┌─────────────────────────────────────┐   │
│  │ noop-local                          │   │
│  └─────────────────────────────────────┘   │
│  Profile from settings.amelia.yaml          │
│                                             │
│  Title *                                    │
│  ┌─────────────────────────────────────┐   │
│  │ Add logout button to navbar         │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  Description                                │
│  ┌─────────────────────────────────────┐   │
│  │ Add a logout button to the top      │   │
│  │ navigation bar that clears the      │   │
│  │ session and redirects to login...   │   │
│  └─────────────────────────────────────┘   │
│                                             │
│            [Cancel]  [Start Workflow]       │
└─────────────────────────────────────────────┘
```

## Form Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Task ID | Input | Yes | Unique identifier (e.g., TASK-001) |
| Worktree Path | Input | Yes | Absolute path to git worktree |
| Profile | Input | No | Profile name from settings.amelia.yaml |
| Title | Input | Yes | Task title (max 500 chars) |
| Description | Textarea | No | Defaults to title if empty (max 5000 chars) |

## API Integration

**New API client method:**
```typescript
async createWorkflow(request: {
  issue_id: string;
  worktree_path: string;
  profile?: string;
  task_title: string;
  task_description?: string;
}): Promise<{ workflow_id: string }>
```

**Request:** `POST /api/workflows`
```json
{
  "issue_id": "TASK-001",
  "worktree_path": "/Users/me/projects/repo",
  "profile": "noop-local",
  "task_title": "Add logout button",
  "task_description": "Add a logout button..."
}
```

**Response:** `{ "workflow_id": "wf-abc123" }`

## Error Handling

- Validation errors: Shown inline under fields
- API errors: Shown as toast notification
- Loading state: Disables form during submission

## Components

**shadcn/ui components used:**
- Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
- Input, Textarea, Label
- Button

## Files to Change

**New files:**
| File | Purpose |
|------|---------|
| `dashboard/src/components/QuickShotModal.tsx` | Modal dialog with form |

**Modified files:**
| File | Changes |
|------|---------|
| `dashboard/src/components/DashboardSidebar.tsx` | Replace Roundtable with Quick Shot trigger |
| `dashboard/src/api/client.ts` | Add `createWorkflow()` method |
| `dashboard/src/types/index.ts` | Add `task_title`, `task_description` to `StartWorkflowRequest` |

## Testing

- Unit test for QuickShotModal form validation
- Unit test for createWorkflow API method
