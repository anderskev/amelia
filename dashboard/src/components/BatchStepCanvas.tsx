/**
 * @fileoverview React Flow canvas for visualizing batch execution plans.
 */
import { useMemo, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  type NodeTypes,
  type Edge,
  type Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { GitBranch, Loader2 } from 'lucide-react';
import { BatchNode, type BatchNodeData } from '@/components/flow/BatchNode';
import { StepNode, type StepNodeData } from '@/components/flow/StepNode';
import { CheckpointMarker, type CheckpointMarkerData } from '@/components/flow/CheckpointMarker';
import { cn } from '@/lib/utils';
import type {
  ExecutionPlan,
  BatchResult,
  BatchApproval,
  StepStatusUI,
  BatchStatusUI,
} from '@/types';

/**
 * Props for the BatchStepCanvas component.
 * @property executionPlan - Execution plan with batches and steps
 * @property batchResults - Optional results from batch execution
 * @property currentBatchIndex - Optional index of currently executing batch
 * @property batchApprovals - Optional batch approval records
 * @property isLoading - Whether the plan is loading
 * @property className - Optional additional CSS classes
 * @property onCancelStep - Optional callback to cancel a step
 */
export interface BatchStepCanvasProps {
  executionPlan?: ExecutionPlan | null;
  batchResults?: BatchResult[];
  currentBatchIndex?: number;
  batchApprovals?: BatchApproval[];
  isLoading?: boolean;
  className?: string;
  onCancelStep?: (stepId: string) => void;
}

/** Custom node types for React Flow. */
const nodeTypes: NodeTypes = {
  batch: BatchNode,
  step: StepNode,
  checkpoint: CheckpointMarker,
};

/** Layout constants for horizontal swimlane layout. */
const LAYOUT = {
  BATCH_WIDTH: 280,
  BATCH_HEIGHT: 160,
  STEP_WIDTH: 240,
  STEP_HEIGHT: 60,
  CHECKPOINT_WIDTH: 80,
  CHECKPOINT_HEIGHT: 80,
  HORIZONTAL_SPACING: 120,
  VERTICAL_SPACING: 80,
  STEP_VERTICAL_SPACING: 20,
  BATCH_START_X: 50,
  BATCH_START_Y: 50,
};

/**
 * Creates nodes and edges for the batch execution plan.
 * Arranges batches horizontally with steps vertically within each batch.
 * Adds checkpoint markers between batches.
 */
function createBatchStepGraph(
  plan: ExecutionPlan,
  batchResults?: BatchResult[],
  currentBatchIndex?: number,
  batchApprovals?: BatchApproval[],
  onCancelStep?: (stepId: string) => void
): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  let currentX = LAYOUT.BATCH_START_X;

  plan.batches.forEach((batch, batchIndex) => {
    const batchId = `batch-${batch.batch_number}`;

    // Determine batch status
    let batchStatus: BatchStatusUI = 'pending';
    if (currentBatchIndex !== undefined) {
      if (batchIndex < currentBatchIndex) {
        batchStatus = 'complete';
      } else if (batchIndex === currentBatchIndex) {
        batchStatus = 'in_progress';
      }
    }

    // Override with actual batch result if available
    const batchResult = batchResults?.find(r => r.batch_number === batch.batch_number);
    if (batchResult) {
      batchStatus = batchResult.status;
    }

    // Create batch node
    const batchNode: Node<BatchNodeData> = {
      id: batchId,
      type: 'batch',
      position: { x: currentX, y: LAYOUT.BATCH_START_Y },
      data: {
        batchNumber: batch.batch_number,
        riskLevel: batch.risk_summary,
        description: batch.description,
        status: batchStatus,
      },
    };
    nodes.push(batchNode);

    // Create step nodes within this batch
    let stepY = LAYOUT.BATCH_START_Y + LAYOUT.BATCH_HEIGHT + LAYOUT.VERTICAL_SPACING;
    const stepX = currentX + (LAYOUT.BATCH_WIDTH - LAYOUT.STEP_WIDTH) / 2;

    batch.steps.forEach((step, stepIndex) => {
      const stepId = step.id;

      // Determine step status
      let stepStatus: StepStatusUI = 'pending';
      const stepResult = batchResult?.completed_steps.find(s => s.step_id === stepId);
      if (stepResult) {
        stepStatus = stepResult.status;
      }

      // Create step node
      const stepNode: Node<StepNodeData> = {
        id: stepId,
        type: 'step',
        position: { x: stepX, y: stepY },
        data: {
          stepId: step.id,
          description: step.description,
          status: stepStatus,
          actionType: step.action_type,
          onCancel: onCancelStep ? () => onCancelStep(stepId) : undefined,
        },
      };
      nodes.push(stepNode);

      // Connect batch to first step
      if (stepIndex === 0) {
        edges.push({
          id: `${batchId}-${stepId}`,
          source: batchId,
          target: stepId,
          type: 'smoothstep',
          style: { stroke: 'var(--border)', strokeWidth: 2 },
        });
      }

      // Connect steps vertically within batch
      if (stepIndex > 0) {
        const prevStep = batch.steps[stepIndex - 1];
        if (prevStep) {
          edges.push({
            id: `${prevStep.id}-${stepId}`,
            source: prevStep.id,
            target: stepId,
            type: 'smoothstep',
            style: { stroke: 'var(--border)', strokeWidth: 2 },
          });
        }
      }

      stepY += LAYOUT.STEP_HEIGHT + LAYOUT.STEP_VERTICAL_SPACING;
    });

    // Add checkpoint marker after this batch (except for the last batch)
    if (batchIndex < plan.batches.length - 1) {
      const checkpointId = `checkpoint-${batch.batch_number}`;
      const checkpointX = currentX + LAYOUT.BATCH_WIDTH + LAYOUT.HORIZONTAL_SPACING / 2 - LAYOUT.CHECKPOINT_WIDTH / 2;
      const checkpointY = LAYOUT.BATCH_START_Y + (LAYOUT.BATCH_HEIGHT - LAYOUT.CHECKPOINT_HEIGHT) / 2;

      // Determine checkpoint status based on approvals
      let checkpointStatus: 'pending' | 'approved' | 'rejected' = 'pending';
      const approval = batchApprovals?.find(a => a.batch_number === batch.batch_number);
      if (approval) {
        checkpointStatus = approval.approved ? 'approved' : 'rejected';
      }

      const checkpointNode: Node<CheckpointMarkerData> = {
        id: checkpointId,
        type: 'checkpoint',
        position: { x: checkpointX, y: checkpointY },
        data: {
          batchNumber: batch.batch_number,
          status: checkpointStatus,
          feedback: approval && !approval.approved ? approval.feedback : null,
          approvedAt: approval && approval.approved ? approval.approved_at : null,
        },
      };
      nodes.push(checkpointNode);

      // Connect batch to checkpoint
      edges.push({
        id: `${batchId}-${checkpointId}`,
        source: batchId,
        target: checkpointId,
        type: 'smoothstep',
        style: { stroke: 'var(--border)', strokeWidth: 2 },
      });

      // Connect checkpoint to next batch
      const nextBatch = plan.batches[batchIndex + 1];
      if (nextBatch) {
        const nextBatchId = `batch-${nextBatch.batch_number}`;
        edges.push({
          id: `${checkpointId}-${nextBatchId}`,
          source: checkpointId,
          target: nextBatchId,
          type: 'smoothstep',
          style: { stroke: 'var(--border)', strokeWidth: 2 },
        });
      }
    }

    // Move to next batch position
    currentX += LAYOUT.BATCH_WIDTH + LAYOUT.HORIZONTAL_SPACING;
  });

  return { nodes, edges };
}

/**
 * Visualizes a batch execution plan using React Flow.
 *
 * Converts execution plan to React Flow format and renders batches as horizontal
 * swimlanes with steps arranged vertically within each batch. Shows checkpoint
 * markers between batches.
 *
 * Displays three states:
 * 1. Empty state: No execution plan provided
 * 2. Loading state: Plan is loading
 * 3. Active state: Plan data is available
 *
 * @param props - Component props
 * @returns The batch step canvas visualization
 *
 * @example
 * ```tsx
 * <BatchStepCanvas
 *   executionPlan={plan}
 *   currentBatchIndex={1}
 *   onCancelStep={(stepId) => console.log('Cancel:', stepId)}
 * />
 * ```
 */
export function BatchStepCanvas({
  executionPlan,
  batchResults,
  currentBatchIndex,
  batchApprovals,
  isLoading = false,
  className,
  onCancelStep,
}: BatchStepCanvasProps) {
  // Create nodes and edges
  const { nodes, edges } = useMemo(() => {
    if (!executionPlan || executionPlan.batches.length === 0) {
      return { nodes: [], edges: [] };
    }

    return createBatchStepGraph(
      executionPlan,
      batchResults,
      currentBatchIndex,
      batchApprovals,
      onCancelStep
    );
  }, [executionPlan, batchResults, currentBatchIndex, batchApprovals, onCancelStep]);

  /** Memoized nodeColor callback for MiniMap. */
  const getNodeColor = useCallback((node: Node) => {
    if (node.type === 'batch') {
      const status = (node.data as BatchNodeData)?.status;
      if (status === 'complete') return 'var(--status-completed)';
      if (status === 'in_progress') return 'var(--primary)';
      if (status === 'blocked') return 'var(--destructive)';
      return 'var(--muted-foreground)';
    }
    if (node.type === 'step') {
      const status = (node.data as StepNodeData)?.status;
      if (status === 'completed') return 'var(--status-completed)';
      if (status === 'in_progress') return 'var(--primary)';
      if (status === 'failed') return 'var(--destructive)';
      return 'var(--muted-foreground)';
    }
    if (node.type === 'checkpoint') {
      const status = (node.data as CheckpointMarkerData)?.status;
      if (status === 'approved') return 'var(--status-completed)';
      if (status === 'rejected') return 'var(--destructive)';
      return 'var(--muted-foreground)';
    }
    return 'var(--muted-foreground)';
  }, []);

  // Loading state - check first so empty state only shows when truly empty
  if (isLoading) {
    return (
      <div
        data-slot="batch-step-canvas"
        className={cn('h-64 bg-linear-to-b from-card/40 to-background/40 relative overflow-hidden', className)}
      >
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: 'radial-gradient(circle, var(--muted-foreground) 1px, transparent 1px)',
            backgroundSize: '20px 20px',
            backgroundPosition: '0 0',
            opacity: 0.1,
          }}
        />
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
          <Loader2 data-testid="loading-spinner" className="h-8 w-8 text-muted-foreground/60 animate-spin" strokeWidth={2} />
          <p className="text-sm text-muted-foreground">Loading execution plan...</p>
        </div>
      </div>
    );
  }

  // Empty state - no plan
  if (!executionPlan || executionPlan.batches.length === 0) {
    return (
      <div
        data-slot="batch-step-canvas"
        className={cn('h-64 bg-linear-to-b from-card/40 to-background/40 relative overflow-hidden', className)}
      >
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: 'radial-gradient(circle, var(--muted-foreground) 1px, transparent 1px)',
            backgroundSize: '20px 20px',
            backgroundPosition: '0 0',
            opacity: 0.1,
          }}
        />
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
          <GitBranch className="h-12 w-12 text-muted-foreground/40" strokeWidth={1.5} />
          <p className="text-sm text-muted-foreground">No execution plan available</p>
        </div>
      </div>
    );
  }

  // Active state - plan data is available
  const batchCount = executionPlan?.batches.length ?? 0;
  return (
    <div
      role="img"
      aria-label={`Batch execution plan with ${batchCount} batches`}
      data-slot="batch-step-canvas"
      className={cn('h-[600px] py-4 bg-linear-to-b from-card/40 to-background/40 relative', className)}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.15, maxZoom: 1.0, minZoom: 0.1 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        className="batch-step-canvas"
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="var(--muted-foreground)"
          style={{ opacity: 0.1 }}
        />
        <Controls
          showZoom={true}
          showFitView={true}
          showInteractive={false}
          position="bottom-right"
          aria-label="Batch step canvas zoom controls"
        />
        <MiniMap
          nodeColor={getNodeColor}
          maskColor="rgba(0, 0, 0, 0.1)"
          style={{
            backgroundColor: 'var(--background)',
            border: '1px solid var(--border)',
          }}
          pannable
          zoomable
          aria-label="Batch step canvas minimap for navigation"
        />
      </ReactFlow>
    </div>
  );
}
