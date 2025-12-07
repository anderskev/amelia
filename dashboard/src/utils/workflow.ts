/**
 * @fileoverview Workflow utility functions.
 */
import type { WorkflowSummary } from '@/types';

/**
 * Determines which workflow to display as the "active" workflow.
 *
 * Priority:
 * 1. Running workflow (status === 'in_progress')
 * 2. Most recently started completed workflow
 *
 * @param workflows - List of workflow summaries
 * @returns The active workflow or null if none exist
 */
export function getActiveWorkflow(workflows: WorkflowSummary[]): WorkflowSummary | null {
  // Priority 1: Running workflow
  const running = workflows.find(w => w.status === 'in_progress');
  if (running) return running;

  // Priority 2: Last completed (most recent by started_at)
  const completed = workflows
    .filter(w => w.status === 'completed')
    .sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime());

  return completed[0] ?? null;
}
