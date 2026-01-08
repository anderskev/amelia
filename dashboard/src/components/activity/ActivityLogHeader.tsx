import { ChevronRight, ChevronDown, Check, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { StageGroup } from './types';

const AGENT_COLORS: Record<string, string> = {
  architect: 'text-blue-400',
  plan_validator: 'text-purple-400',
  human_approval: 'text-red-400',
  developer: 'text-green-400',
  reviewer: 'text-yellow-400',
};

interface ActivityLogHeaderProps {
  group: StageGroup;
  isCollapsed: boolean;
  onToggle: () => void;
}

export function ActivityLogHeader({
  group,
  isCollapsed,
  onToggle,
}: ActivityLogHeaderProps) {
  const color = AGENT_COLORS[group.stage] || 'text-muted-foreground';

  return (
    <button
      type="button"
      onClick={onToggle}
      className={cn(
        'w-full flex items-center gap-2 px-3 py-2',
        'bg-muted/50 hover:bg-muted/70 transition-colors',
        'border-b border-border/30 font-mono text-sm'
      )}
      aria-expanded={!isCollapsed}
    >
      {isCollapsed ? (
        <ChevronRight className="w-4 h-4 text-muted-foreground" />
      ) : (
        <ChevronDown className="w-4 h-4 text-muted-foreground" />
      )}

      <span className={cn('font-semibold', color)}>{group.label}</span>

      <span className="ml-auto flex items-center gap-2">
        <span className="text-muted-foreground tabular-nums">
          {group.events.length}
        </span>

        {group.isCompleted && (
          <Check
            className="w-4 h-4 text-green-500"
            data-testid="stage-completed"
          />
        )}

        {group.isActive && !group.isCompleted && (
          <Loader2
            className="w-4 h-4 text-primary animate-spin"
            data-testid="stage-active"
          />
        )}
      </span>
    </button>
  );
}
