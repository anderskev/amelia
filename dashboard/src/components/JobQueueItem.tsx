import { StatusBadge } from '@/components/StatusBadge';
import { cn } from '@/lib/utils';
import type { WorkflowSummary } from '@/types';

interface JobQueueItemProps {
  workflow: Pick<WorkflowSummary, 'id' | 'issue_id' | 'worktree_name' | 'status' | 'current_stage'>;
  selected: boolean;
  onSelect: (id: string) => void;
  className?: string;
}

export function JobQueueItem({ workflow, selected, onSelect, className }: JobQueueItemProps) {
  const handleClick = () => onSelect(workflow.id);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(workflow.id);
    }
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      data-slot="job-queue-item"
      data-selected={selected}
      className={cn(
        'flex items-center gap-3 p-3 rounded-lg border transition-all duration-200 cursor-pointer',
        'hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
        selected
          ? 'border-primary bg-primary/10'
          : 'border-border/50 bg-card/50',
        className
      )}
    >
      <StatusBadge status={workflow.status} />

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm font-semibold text-accent">
            {workflow.issue_id}
          </span>
          <span className="font-body text-sm text-foreground truncate">
            {workflow.worktree_name}
          </span>
        </div>

        {workflow.current_stage && (
          <p className="text-xs text-muted-foreground mt-0.5">
            Stage: {workflow.current_stage}
          </p>
        )}
      </div>
    </div>
  );
}
