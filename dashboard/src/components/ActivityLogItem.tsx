/**
 * @fileoverview Individual log entry in the activity log.
 */
import { cn, formatTime } from '@/lib/utils';
import { AGENT_STYLES } from '@/lib/constants';
import type { WorkflowEvent } from '@/types';

/**
 * Props for the ActivityLogItem component.
 * @property event - The workflow event to display
 */
interface ActivityLogItemProps {
  event: WorkflowEvent;
}

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
  const agentStyle = AGENT_STYLES[event.agent.toUpperCase()] || {
    text: 'text-muted-foreground',
    bg: '',
  };

  return (
    <div
      data-slot="activity-log-item"
      className={cn(
        'grid grid-cols-[60px_100px_1fr] gap-2 py-1 border-b border-border/30 font-mono text-xs',
        agentStyle.bg
      )}
    >
      <span className="text-muted-foreground tabular-nums">
        {formatTime(event.timestamp)}
      </span>
      <span className={cn('font-semibold', agentStyle.text)}>
        {event.agent.toUpperCase()}
      </span>
      <span className="text-foreground/80 break-words">
        {event.message}
      </span>
    </div>
  );
}
