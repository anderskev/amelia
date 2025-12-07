/**
 * @fileoverview React Flow canvas for visualizing workflow pipelines.
 */
import { useMemo } from 'react';
import {
  ReactFlow,
  Background,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { WorkflowNode, type WorkflowNodeType } from '@/components/flow/WorkflowNode';
import { WorkflowEdge, type WorkflowEdgeType } from '@/components/flow/WorkflowEdge';
import { cn } from '@/lib/utils';

/** Possible status values for pipeline nodes. */
type NodeStatus = 'completed' | 'active' | 'pending' | 'blocked';

/** Possible status values for pipeline edges. */
type EdgeStatus = 'completed' | 'active' | 'pending';

/**
 * Represents a node in the workflow pipeline.
 * @property id - Unique node identifier
 * @property label - Display label for the node
 * @property subtitle - Optional secondary text
 * @property status - Current node status
 * @property tokens - Optional token count display
 */
interface PipelineNode {
  id: string;
  label: string;
  subtitle?: string;
  status: NodeStatus;
  tokens?: string;
}

/**
 * Represents an edge connecting two pipeline nodes.
 * @property from - Source node ID
 * @property to - Target node ID
 * @property label - Edge label text
 * @property status - Current edge status
 */
interface PipelineEdge {
  from: string;
  to: string;
  label: string;
  status: EdgeStatus;
}

/**
 * Complete pipeline data structure for the canvas.
 * @property nodes - Array of pipeline nodes
 * @property edges - Array of pipeline edges
 */
interface Pipeline {
  nodes: PipelineNode[];
  edges: PipelineEdge[];
}

/**
 * Props for the WorkflowCanvas component.
 * @property pipeline - Pipeline data to visualize
 * @property className - Optional additional CSS classes
 */
interface WorkflowCanvasProps {
  pipeline: Pipeline;
  className?: string;
}

/** Custom node types for React Flow. */
const nodeTypes = {
  workflow: WorkflowNode,
};

/** Custom edge types for React Flow. */
const edgeTypes = {
  workflow: WorkflowEdge,
};

/**
 * Visualizes a workflow pipeline using React Flow.
 *
 * Converts pipeline data to React Flow format and renders nodes
 * and edges in a non-interactive view. Shows stage progress indicator.
 *
 * @param props - Component props
 * @returns The workflow canvas visualization
 *
 * @example
 * ```tsx
 * <WorkflowCanvas
 *   pipeline={{
 *     nodes: [{ id: '1', label: 'Plan', status: 'completed' }],
 *     edges: [{ from: '1', to: '2', label: 'approve', status: 'active' }]
 *   }}
 * />
 * ```
 */
export function WorkflowCanvas({ pipeline, className }: WorkflowCanvasProps) {
  // Convert pipeline data to React Flow format
  const nodes: WorkflowNodeType[] = useMemo(
    () =>
      pipeline.nodes.map((node, index) => ({
        id: node.id,
        type: 'workflow' as const,
        position: { x: index * 180, y: 80 },
        data: {
          label: node.label,
          subtitle: node.subtitle,
          status: node.status,
          tokens: node.tokens,
        },
        draggable: false,
        selectable: false,
        connectable: false,
      })),
    [pipeline.nodes]
  );

  const edges: WorkflowEdgeType[] = useMemo(
    () =>
      pipeline.edges.map((edge) => ({
        id: `e-${edge.from}-${edge.to}`,
        source: edge.from,
        target: edge.to,
        type: 'workflow' as const,
        data: {
          label: edge.label,
          status: edge.status,
        },
      })),
    [pipeline.edges]
  );

  const currentStage = pipeline.nodes.find((n) => n.status === 'active')?.label || 'Unknown';
  const completedCount = pipeline.nodes.filter((n) => n.status === 'completed').length;

  return (
    <div
      role="img"
      aria-label={`Workflow pipeline with ${pipeline.nodes.length} stages. Current stage: ${currentStage}`}
      data-slot="workflow-canvas"
      className={cn('h-64 bg-gradient-to-b from-card/40 to-background/40 relative', className)}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        panOnDrag={false}
        zoomOnScroll={false}
        zoomOnPinch={false}
        zoomOnDoubleClick={false}
        preventScrolling={false}
        className="workflow-canvas"
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="var(--muted-foreground)"
          style={{ opacity: 0.1 }}
        />
      </ReactFlow>

      {/* Stage progress info */}
      <div className="absolute top-3 right-3 bg-card/80 border border-border rounded px-3 py-2">
        <span className="font-mono text-sm text-muted-foreground">
          {completedCount}/{pipeline.nodes.length} stages
        </span>
      </div>
    </div>
  );
}
