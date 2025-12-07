/**
 * Additional TypeScript types for React Router loaders and actions.
 * Re-exports base types from Plan 08.
 * Keep in sync with amelia/server/models/*.py
 */

// Re-export all types from Plan 08 Task 8
export * from './index';

import type { WorkflowSummary, WorkflowDetail } from './index';

// React Router loader/action types (NEW in this plan)
export interface WorkflowsLoaderData {
  workflows: WorkflowSummary[];
}

export interface WorkflowDetailLoaderData {
  workflow: WorkflowDetail;
}

export interface ActionResult {
  success: boolean;
  action: 'approved' | 'rejected' | 'cancelled';
  error?: string;
}
