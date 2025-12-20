/**
 * @fileoverview Custom React Flow node for execution batch visualization.
 */
import { memo } from 'react';
import { Handle, Position, type NodeProps, type Node } from '@xyflow/react';
import { Package } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { RiskLevel, BatchStatusUI } from '@/types';

/**
 * Data payload for batch nodes.
 * @property batchNumber - Sequential batch number (e.g., 1, 2, 3)
 * @property riskLevel - Risk level of the batch (low, medium, high)
 * @property description - Optional description of what the batch accomplishes
 * @property status - Current batch execution status
 */
export interface BatchNodeData extends Record<string, unknown> {
  batchNumber: number;
  riskLevel: RiskLevel;
  description?: string;
  status: BatchStatusUI;
}

/** Type definition for batch nodes used in React Flow. */
export type BatchNodeType = Node<BatchNodeData, 'batch'>;

/** Style properties for batch status. */
type StatusStyle = {
  containerClass: string;
  borderClass: string;
  backgroundClass: string;
  shadowClass: string;
  glowClass: string;
};

/** Style configuration for each batch status. */
const statusStyles: Record<BatchStatusUI, StatusStyle> = {
  pending: {
    containerClass: 'opacity-50',
    borderClass: 'border-border',
    backgroundClass: 'bg-card/60',
    shadowClass: 'shadow-sm',
    glowClass: '',
  },
  in_progress: {
    containerClass: 'opacity-100',
    borderClass: 'border-primary/60',
    backgroundClass: 'bg-primary/10',
    shadowClass: 'shadow-lg shadow-primary/20',
    glowClass: 'drop-shadow-[0_0_12px_var(--primary)]',
  },
  complete: {
    containerClass: 'opacity-100',
    borderClass: 'border-status-completed/40',
    backgroundClass: 'bg-status-completed/5',
    shadowClass: 'shadow-md',
    glowClass: '',
  },
  blocked: {
    containerClass: 'opacity-100',
    borderClass: 'border-destructive/40',
    backgroundClass: 'bg-destructive/5',
    shadowClass: 'shadow-md',
    glowClass: '',
  },
  partial: {
    containerClass: 'opacity-100',
    borderClass: 'border-amber-600/40',
    backgroundClass: 'bg-amber-600/5',
    shadowClass: 'shadow-md',
    glowClass: '',
  },
};

/** Style configuration for each risk level. */
const riskStyles: Record<RiskLevel, { textClass: string; borderClass: string }> = {
  low: {
    textClass: 'text-status-completed',
    borderClass: 'border-status-completed',
  },
  medium: {
    textClass: 'text-amber-600',
    borderClass: 'border-amber-600',
  },
  high: {
    textClass: 'text-destructive',
    borderClass: 'border-destructive',
  },
};

/** Capitalizes the first letter of a string. */
const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

/**
 * Renders a batch node with status and risk-based styling.
 *
 * Displays batch number, risk level badge, and optional description.
 * Visual appearance changes based on status and risk level.
 *
 * @param props - React Flow node props
 * @returns The batch node UI
 */
function BatchNodeComponent({ data }: NodeProps<BatchNodeType>) {
  const styles = statusStyles[data.status];
  const riskStyle = riskStyles[data.riskLevel];

  const ariaLabel = data.description
    ? `Batch ${data.batchNumber}: ${data.description} (${data.status}, ${data.riskLevel} risk)`
    : `Batch ${data.batchNumber} (${data.status}, ${data.riskLevel} risk)`;

  return (
    <Card
      data-testid="batch-node-card"
      data-slot="batch-node"
      data-status={data.status}
      data-risk={data.riskLevel}
      role="img"
      aria-label={ariaLabel}
      className={cn(
        'relative rounded-md transition-all duration-200 overflow-hidden min-w-64',
        styles.containerClass,
        styles.borderClass,
        styles.backgroundClass,
        styles.shadowClass
      )}
    >
      <CardContent className="flex flex-col p-4 space-y-3">
        {/* Header with batch number and risk badge */}
        <div className="flex items-center justify-between gap-2">
          <div className={cn('flex items-center gap-2', styles.glowClass)}>
            <Package
              className={cn(
                'lucide-package size-5',
                data.status === 'in_progress' ? 'text-primary' : 'text-muted-foreground'
              )}
              strokeWidth={2}
            />
            <span className={cn(
              "font-heading text-sm font-semibold tracking-wider",
              data.status === 'in_progress' ? 'text-primary' : 'text-foreground'
            )}>
              Batch {data.batchNumber}
            </span>
          </div>

          <Badge
            variant="outline"
            className={cn(
              'text-[10px] px-1.5 py-0',
              riskStyle.textClass,
              riskStyle.borderClass
            )}
          >
            {capitalize(data.riskLevel)} Risk
          </Badge>
        </div>

        {/* Description */}
        {data.description && (
          <p className="font-body text-xs text-muted-foreground leading-relaxed">
            {data.description}
          </p>
        )}
      </CardContent>

      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
    </Card>
  );
}

/** Memoized batch node component for React Flow. */
export const BatchNode = memo(BatchNodeComponent);
