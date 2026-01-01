/**
 * @fileoverview Individual log entry in the activity log.
 */
import { cn, formatTime } from '@/lib/utils';
import type { WorkflowEvent } from '@/types';

/**
 * Props for the ActivityLogItem component.
 * @property event - The workflow event to display
 */
interface ActivityLogItemProps {
  event: WorkflowEvent;
}

/** Style mapping for different agent types in the log. */
const agentStyles: Record<string, { text: string; bg: string }> = {
  PM: { text: 'text-agent-pm', bg: 'bg-agent-pm-bg' },
  ORCHESTRATOR: { text: 'text-muted-foreground', bg: '' },
  ARCHITECT: { text: 'text-agent-architect', bg: 'bg-agent-architect-bg' },
  DEVELOPER: { text: 'text-agent-developer', bg: 'bg-agent-developer-bg' },
  REVIEWER: { text: 'text-agent-reviewer', bg: 'bg-agent-reviewer-bg' },
  SYSTEM: { text: 'text-muted-foreground', bg: '' },
};

/**
 * Renders a single event entry in the activity log.
 *
 * Displays timestamp, agent name (color-coded), and event message
 * in a terminal-style format.
 *
 * @param props - Component props
 * @returns The log item UI
 */
export function ActivityLogItem({ event }: ActivityLogItemProps) {
  const agentStyle = agentStyles[event.agent.toUpperCase()] || {
    text: 'text-muted-foreground',
    bg: '',
  };

  return (
    <div
      data-slot="activity-log-item"
      className={cn(
        'grid grid-cols-[100px_120px_1fr] gap-3 py-1.5 border-b border-border/30 font-mono text-sm',
        agentStyle.bg
      )}
    >
      <span className="text-muted-foreground tabular-nums">
        {formatTime(event.timestamp)}
      </span>
      <span className={cn('font-semibold', agentStyle.text)}>
        [{event.agent.toUpperCase()}]
      </span>
      <span className="text-foreground/80 break-words">
        {event.message}
      </span>
    </div>
  );
}
