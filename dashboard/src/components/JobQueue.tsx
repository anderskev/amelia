/**
 * @fileoverview Static job queue displaying active workflows.
 *
 * Industrial panel design with compact workflow cards.
 */
import { JobQueueItem } from '@/components/JobQueueItem';
import { cn } from '@/lib/utils';
import type { WorkflowSummary } from '@/types';

/**
 * Props for the JobQueue component.
 * @property workflows - Array of workflow summaries to display
 * @property selectedId - ID of the currently selected workflow
 * @property onSelect - Callback when a workflow is selected
 * @property className - Optional additional CSS classes
 */
interface JobQueueProps {
  workflows?: Pick<WorkflowSummary, 'id' | 'issue_id' | 'worktree_path' | 'status' | 'current_stage'>[];
  selectedId?: string | null;
  onSelect?: (id: string | null) => void;
  className?: string;
}

/**
 * Displays a static list of active workflows.
 *
 * Industrial panel design with:
 * - Sticky header with workflow count
 * - Compact card list with status indicators
 * - Efficient use of horizontal space
 *
 * @param props - Component props
 * @returns The job queue UI
 *
 * @example
 * ```tsx
 * <JobQueue
 *   workflows={workflows}
 *   selectedId={currentId}
 *   onSelect={(id) => navigate(`/workflows/${id}`)}
 * />
 * ```
 */
export function JobQueue({
  workflows = [],
  selectedId = null,
  onSelect = () => {},
  className
}: JobQueueProps) {
  return (
    <div
      data-slot="job-queue"
      className={cn('bg-card/40 border border-border/40 rounded-md flex flex-col', className)}
    >
      {/* Header */}
      <div className="sticky top-0 z-20 bg-card/80 backdrop-blur-sm px-4 py-3 border-b border-border/40">
        <div className="flex items-center justify-between">
          <h3 className="font-heading text-xs font-semibold tracking-widest text-muted-foreground">
            JOB QUEUE
          </h3>
          {workflows.length > 0 && (
            <span className="font-mono text-[10px] text-muted-foreground/60 tabular-nums">
              {workflows.length}
            </span>
          )}
        </div>
      </div>

      {/* Workflow List */}
      {workflows.length === 0 ? (
        <div className="flex-1 flex items-center justify-center py-12">
          <p className="text-sm text-muted-foreground/60">
            No active workflows
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-1.5 p-3">
          {workflows.map((workflow) => (
            <JobQueueItem
              key={workflow.id}
              workflow={workflow}
              selected={workflow.id === selectedId}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}
