/**
 * @fileoverview Pipeline conversion utilities for workflow visualization.
 */
import type { WorkflowDetail } from '@/types';

/** Node in the pipeline visualization. */
export interface PipelineNode {
  id: string;
  label: string;
  subtitle: string;
  status: 'completed' | 'active' | 'blocked' | 'pending';
}

/** Edge connecting pipeline nodes. */
export interface PipelineEdge {
  from: string;
  to: string;
  label: string;
  status: 'completed' | 'active' | 'pending';
}

/** Pipeline data structure for WorkflowCanvas. */
export interface Pipeline {
  nodes: PipelineNode[];
  edges: PipelineEdge[];
}

/**
 * Converts a workflow detail into a pipeline visualization format.
 *
 * Maps task statuses to node statuses:
 * - completed -> completed
 * - in_progress -> active
 * - failed -> blocked
 * - other -> pending
 *
 * @param workflow - The workflow detail containing the plan
 * @returns Pipeline data or null if no plan exists
 */
export function buildPipeline(workflow: WorkflowDetail): Pipeline | null {
  if (!workflow.plan) {
    return null;
  }

  const taskIds = new Set(workflow.plan.tasks.map((t) => t.id));

  const nodes: PipelineNode[] = workflow.plan.tasks.map((task) => ({
    id: task.id,
    label: task.agent,
    subtitle: task.description,
    status: task.status === 'completed'
      ? 'completed'
      : task.status === 'in_progress'
      ? 'active'
      : task.status === 'failed'
      ? 'blocked'
      : 'pending',
  }));

  // Filter edges to only include those where both source and target exist
  const edges: PipelineEdge[] = workflow.plan.tasks.flatMap((task) =>
    task.dependencies
      .filter((depId) => taskIds.has(depId))
      .map((depId) => ({
        from: depId,
        to: task.id,
        label: '',
        status: 'completed' as const,
      }))
  );

  return { nodes, edges };
}
