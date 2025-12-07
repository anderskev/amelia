import { useMemo } from 'react';
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  type Node,
  type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { WorkflowNode, type WorkflowNodeData } from '@/components/flow/WorkflowNode';
import { WorkflowEdge, type WorkflowEdgeData } from '@/components/flow/WorkflowEdge';
import { cn } from '@/lib/utils';

type NodeStatus = 'completed' | 'active' | 'pending' | 'blocked';
type EdgeStatus = 'completed' | 'active' | 'pending';

interface PipelineNode {
  id: string;
  label: string;
  subtitle?: string;
  status: NodeStatus;
  tokens?: string;
}

interface PipelineEdge {
  from: string;
  to: string;
  label: string;
  status: EdgeStatus;
}

interface Pipeline {
  nodes: PipelineNode[];
  edges: PipelineEdge[];
}

interface WorkflowCanvasProps {
  pipeline: Pipeline;
  className?: string;
}

const nodeTypes = {
  workflow: WorkflowNode,
};

const edgeTypes = {
  workflow: WorkflowEdge,
};

export function WorkflowCanvas({ pipeline, className }: WorkflowCanvasProps) {
  // Convert pipeline data to React Flow format
  const nodes: Node<WorkflowNodeData>[] = useMemo(
    () =>
      pipeline.nodes.map((node, index) => ({
        id: node.id,
        type: 'workflow',
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

  const edges: Edge<WorkflowEdgeData>[] = useMemo(
    () =>
      pipeline.edges.map((edge) => ({
        id: `e-${edge.from}-${edge.to}`,
        source: edge.from,
        target: edge.to,
        type: 'workflow',
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
