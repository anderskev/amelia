/**
 * @fileoverview Custom React Flow node for batch checkpoint markers.
 */
import { memo } from 'react';
import { Handle, Position, type NodeProps, type Node } from '@xyflow/react';
import { Clock, CheckCircle2, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { formatTime } from '@/lib/utils';

/** Possible status values for checkpoint markers. */
type CheckpointStatus = 'pending' | 'approved' | 'rejected';

/**
 * Data payload for checkpoint marker nodes.
 * @property batchNumber - The batch number this checkpoint is AFTER
 * @property status - Current checkpoint status
 * @property feedback - Optional feedback when rejected
 * @property approvedAt - Optional timestamp when approved
 */
export interface CheckpointMarkerData extends Record<string, unknown> {
  batchNumber: number;
  status: CheckpointStatus;
  feedback?: string | null;
  approvedAt?: string | null;
}

/** Type definition for checkpoint marker nodes used in React Flow. */
export type CheckpointMarkerType = Node<CheckpointMarkerData, 'checkpoint'>;

/** Style properties for checkpoint status. */
type StatusStyle = {
  borderClass: string;
  backgroundClass: string;
  iconClass: string;
  textClass: string;
  label: string;
};

/** Style configuration for each checkpoint status. */
const statusStyles: Record<CheckpointStatus, StatusStyle> = {
  pending: {
    borderClass: 'border-border',
    backgroundClass: 'bg-muted/30',
    iconClass: 'text-muted-foreground',
    textClass: 'text-muted-foreground',
    label: 'Awaiting Approval',
  },
  approved: {
    borderClass: 'border-status-completed/40',
    backgroundClass: 'bg-status-completed/5',
    iconClass: 'text-status-completed',
    textClass: 'text-status-completed',
    label: 'Approved',
  },
  rejected: {
    borderClass: 'border-destructive/40',
    backgroundClass: 'bg-destructive/5',
    iconClass: 'text-destructive',
    textClass: 'text-destructive',
    label: 'Rejected',
  },
};

/**
 * Renders the status icon based on checkpoint status.
 */
function StatusIcon({ status, iconClass }: { status: CheckpointStatus; iconClass: string }) {
  const iconProps = {
    className: cn('lucide-icon size-4', iconClass),
    strokeWidth: 2,
  };

  switch (status) {
    case 'pending':
      return (
        <Clock
          data-testid="status-icon-pending"
          className={cn('lucide-clock', iconProps.className)}
          strokeWidth={iconProps.strokeWidth}
        />
      );
    case 'approved':
      return (
        <CheckCircle2
          data-testid="status-icon-approved"
          className={cn('lucide-check-circle-2', iconProps.className)}
          strokeWidth={iconProps.strokeWidth}
        />
      );
    case 'rejected':
      return (
        <XCircle
          data-testid="status-icon-rejected"
          className={cn('lucide-x-circle', iconProps.className)}
          strokeWidth={iconProps.strokeWidth}
        />
      );
  }
}

/**
 * Renders a checkpoint marker showing batch approval status.
 *
 * Displays a compact diamond/lozenge shape between batches with:
 * - Status icon (Clock, CheckCircle2, or XCircle)
 * - Status label (Awaiting Approval, Approved, or Rejected)
 * - Approval timestamp (when approved)
 * - Rejection feedback (when rejected)
 *
 * Visual appearance changes based on approval status.
 *
 * @param props - React Flow node props
 * @returns The checkpoint marker UI
 */
function CheckpointMarkerComponent({ data }: NodeProps<CheckpointMarkerType>) {
  const styles = statusStyles[data.status];
  const ariaLabel = `Checkpoint after Batch ${data.batchNumber}: ${styles.label}`;

  return (
    <div className="relative">
      {/* Outer diamond container for sizing */}
      <div className="w-32 h-32 flex items-center justify-center">
        <Card
          data-testid="checkpoint-marker-card"
          data-slot="checkpoint-marker"
          data-status={data.status}
          role="img"
          aria-label={ariaLabel}
          className={cn(
            'relative rounded-md transition-all duration-200 overflow-visible',
            'border shadow-sm rotate-45 w-full h-full',
            styles.borderClass,
            styles.backgroundClass,
            'p-2'
          )}
        >
          {/* Inner content rotated back to normal */}
          <CardContent className="-rotate-45 flex flex-col items-center justify-center p-0 h-full">
            <div className="flex flex-col items-center gap-1">
              {/* Status Icon */}
              <StatusIcon status={data.status} iconClass={styles.iconClass} />

              {/* Status Label */}
              <span className={cn('font-mono text-[10px] font-medium text-center', styles.textClass)}>
                {styles.label}
              </span>

              {/* Batch number */}
              <span className="font-mono text-[9px] text-muted-foreground">
                Batch {data.batchNumber}
              </span>

              {/* Approval timestamp */}
              {data.status === 'approved' && data.approvedAt && (
                <span
                  data-testid="approval-timestamp"
                  className="font-mono text-[8px] text-muted-foreground mt-0.5"
                >
                  {formatTime(data.approvedAt)}
                </span>
              )}

              {/* Rejection feedback */}
              {data.status === 'rejected' && data.feedback && (
                <p
                  data-testid="rejection-feedback"
                  className="font-body text-[9px] text-destructive text-center mt-1 leading-tight max-w-[80px]"
                >
                  {data.feedback}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Handles positioned relative to the outer container */}
      <Handle type="target" position={Position.Left} className="left-0! top-1/2!" />
      <Handle type="source" position={Position.Right} className="right-0! top-1/2!" />
    </div>
  );
}

/** Memoized checkpoint marker component for React Flow. */
export const CheckpointMarker = memo(CheckpointMarkerComponent);
