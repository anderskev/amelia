/**
 * @fileoverview Header component for workflow detail pages.
 */
import { StatusBadge } from '@/components/StatusBadge';
import { cn } from '@/lib/utils';
import type { WorkflowDetail, WorkflowSummary } from '@/types';

/**
 * Props for the WorkflowHeader component.
 * @property workflow - Workflow data to display
 * @property elapsedTime - Optional formatted elapsed time string
 * @property className - Optional additional CSS classes
 */
interface WorkflowHeaderProps {
  workflow: WorkflowDetail | Pick<WorkflowSummary, 'id' | 'issue_id' | 'worktree_name' | 'status'>;
  elapsedTime?: string;
  className?: string;
}

/**
 * Displays workflow identification and status in the page header.
 *
 * Shows issue ID, worktree name, elapsed time, and status badge
 * with pulsing indicator for running workflows.
 *
 * @param props - Component props
 * @returns The workflow header UI
 */
export function WorkflowHeader({ workflow, elapsedTime, className }: WorkflowHeaderProps) {
  const isRunning = workflow.status === 'in_progress';

  return (
    <header
      role="banner"
      data-slot="workflow-header"
      className={cn(
        'grid grid-cols-3 items-center px-6 py-4 border-b border-border bg-card/50',
        className
      )}
    >
      {/* Left: Workflow info */}
      <div>
        <span className="block font-heading text-xs font-semibold tracking-widest text-muted-foreground mb-1">
          WORKFLOW
        </span>
        <div className="flex items-center gap-3">
          <h2 className="font-display text-3xl font-bold tracking-wider text-foreground">
            {workflow.issue_id}
          </h2>
          <span className="font-mono text-sm text-muted-foreground">
            {workflow.worktree_name}
          </span>
        </div>
      </div>

      {/* Center: Elapsed Time */}
      <div className="text-center">
        <span className="block font-heading text-xs font-semibold tracking-widest text-muted-foreground mb-1">
          ELAPSED
        </span>
        <div className="font-mono text-2xl font-semibold text-primary [text-shadow:0_0_10px_rgba(255,200,87,0.4)]">
          {elapsedTime ?? '--:--'}
        </div>
      </div>

      {/* Right: Status */}
      <div className="flex items-center gap-2 px-4 py-2 bg-primary/10 border border-primary/30 justify-self-end">
        {isRunning && (
          <span className="w-2 h-2 rounded-full bg-primary animate-pulse shadow-[0_0_8px_rgba(255,200,87,0.6)]" />
        )}
        <StatusBadge status={workflow.status} />
      </div>
    </header>
  );
}
