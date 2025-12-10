// dashboard/src/utils/layout.ts
/**
 * @fileoverview Simple layout utility for workflow visualization.
 *
 * Uses React Flow's default behavior - nodes are positioned sequentially.
 */
import type { WorkflowNodeType } from '@/components/flow/WorkflowNode';
import type { Edge } from '@xyflow/react';

/** Spacing between nodes. */
const NODE_SPACING = 200;

/**
 * Positions nodes sequentially for React Flow.
 *
 * Places nodes in a horizontal row with consistent spacing.
 * React Flow's fitView will scale and center the result.
 *
 * @param nodes - React Flow nodes to layout
 * @param _edges - Edges (unused, kept for API compatibility)
 * @returns Nodes with updated positions
 */
export function getLayoutedElements(
  nodes: WorkflowNodeType[],
  _edges: Edge[]
): WorkflowNodeType[] {
  return nodes.map((node, index) => ({
    ...node,
    position: { x: index * NODE_SPACING, y: 0 },
  }));
}
