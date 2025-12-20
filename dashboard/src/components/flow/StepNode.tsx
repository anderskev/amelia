/**
 * @fileoverview Custom React Flow node for individual execution steps.
 */
import { memo } from 'react';
import { Handle, Position, type NodeProps, type Node } from '@xyflow/react';
import {
  Circle,
  Loader2,
  CheckCircle2,
  MinusCircle,
  XCircle,
  FileCode,
  Terminal,
  CheckSquare,
  Hand,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { StepStatusUI, ActionType } from '@/types';

/**
 * Data payload for step nodes.
 * @property stepId - Unique identifier for the step
 * @property description - Human-readable step description
 * @property status - Current step execution status
 * @property actionType - Type of action this step performs
 * @property elapsedSeconds - Optional elapsed time when step is running
 * @property onCancel - Optional callback to cancel the step
 */
export interface StepNodeData extends Record<string, unknown> {
  stepId: string;
  description: string;
  status: StepStatusUI;
  actionType: ActionType;
  elapsedSeconds?: number;
  onCancel?: () => void;
}

/** Type definition for step nodes used in React Flow. */
export type StepNodeType = Node<StepNodeData, 'step'>;

/**
 * Formats elapsed seconds into human-readable time string.
 * @param seconds - Number of seconds elapsed
 * @returns Formatted time string (e.g., "12s" or "1m 23s")
 */
function formatElapsedTime(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

/**
 * Renders the status icon based on step status.
 */
function StatusIcon({ status }: { status: StepStatusUI }) {
  switch (status) {
    case 'pending':
      return (
        <Circle
          data-testid="status-icon-pending"
          className="lucide-circle size-4 text-muted-foreground"
          strokeWidth={2}
        />
      );
    case 'in_progress':
      return (
        <Loader2
          data-testid="status-icon-in_progress"
          className="lucide-loader-2 size-4 text-primary animate-spin"
          strokeWidth={2}
        />
      );
    case 'completed':
      return (
        <CheckCircle2
          data-testid="status-icon-completed"
          className="lucide-check-circle-2 size-4 text-status-completed"
          strokeWidth={2}
        />
      );
    case 'skipped':
      return (
        <MinusCircle
          data-testid="status-icon-skipped"
          className="lucide-minus-circle size-4 text-muted-foreground"
          strokeWidth={2}
        />
      );
    case 'failed':
      return (
        <XCircle
          data-testid="status-icon-failed"
          className="lucide-x-circle size-4 text-destructive"
          strokeWidth={2}
        />
      );
    case 'cancelled':
      return (
        <XCircle
          data-testid="status-icon-cancelled"
          className="lucide-x-circle size-4 text-amber-500"
          strokeWidth={2}
        />
      );
  }
}

/**
 * Renders the action type icon based on action type.
 */
function ActionTypeIcon({ actionType }: { actionType: ActionType }) {
  const iconClass = 'size-3 text-muted-foreground';

  switch (actionType) {
    case 'code':
      return (
        <FileCode
          data-testid="action-type-icon"
          className={cn('lucide-file-code', iconClass)}
          strokeWidth={2}
        />
      );
    case 'command':
      return (
        <Terminal
          data-testid="action-type-icon"
          className={cn('lucide-terminal', iconClass)}
          strokeWidth={2}
        />
      );
    case 'validation':
      return (
        <CheckSquare
          data-testid="action-type-icon"
          className={cn('lucide-check-square', iconClass)}
          strokeWidth={2}
        />
      );
    case 'manual':
      return (
        <Hand
          data-testid="action-type-icon"
          className={cn('lucide-hand', iconClass)}
          strokeWidth={2}
        />
      );
  }
}

/**
 * Renders a step node showing execution status, description, and controls.
 *
 * Displays status icon, description, elapsed time (when running), and cancel button
 * (when running and cancellable). Visual appearance changes based on status.
 *
 * @param props - React Flow node props
 * @returns The step node UI
 */
function StepNodeComponent({ data }: NodeProps<StepNodeType>) {
  const ariaLabel = `Step: ${data.description} (${data.status})`;
  const showElapsedTime = data.status === 'in_progress' && data.elapsedSeconds !== undefined;
  const showCancelButton = data.status === 'in_progress' && data.onCancel !== undefined;

  return (
    <Card
      data-testid="step-node-card"
      data-slot="step-node"
      data-step-id={data.stepId}
      data-status={data.status}
      role="img"
      aria-label={ariaLabel}
      className={cn(
        'relative rounded-md transition-all duration-200 overflow-hidden',
        'border shadow-sm',
        'min-w-[200px] max-w-[300px]'
      )}
    >
      <CardContent className="flex items-center gap-2 p-2">
        {/* Status Icon */}
        <div className="flex-shrink-0">
          <StatusIcon status={data.status} />
        </div>

        {/* Description and metadata */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <ActionTypeIcon actionType={data.actionType} />
            <span className="font-body text-xs text-foreground truncate">
              {data.description}
            </span>
          </div>

          {/* Elapsed time when running */}
          {showElapsedTime && (
            <div className="mt-0.5">
              <span
                data-testid="elapsed-time"
                className="font-mono text-[10px] text-muted-foreground"
              >
                {formatElapsedTime(data.elapsedSeconds!)}
              </span>
            </div>
          )}
        </div>

        {/* Cancel button when running */}
        {showCancelButton && (
          <Button
            data-testid="cancel-button"
            variant="ghost"
            size="icon-sm"
            onClick={data.onCancel}
            aria-label="Cancel step"
            className="nodrag flex-shrink-0"
          >
            <X className="size-3" strokeWidth={2} />
          </Button>
        )}
      </CardContent>

      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
    </Card>
  );
}

/** Memoized step node component for React Flow. */
export const StepNode = memo(StepNodeComponent);
