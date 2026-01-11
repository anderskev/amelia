/**
 * @fileoverview Indicator for workflows in planning state.
 *
 * Shows when the Architect agent is analyzing the issue and
 * generating an implementation plan.
 */
import { useState, useCallback, useEffect } from 'react';
import { useRevalidator } from 'react-router-dom';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Loader } from '@/components/ai-elements/loader';
import { success, error as toastError } from '@/components/Toast';
import { api } from '@/api/client';
import { cn } from '@/lib/utils';

/**
 * Props for the PlanningIndicator component.
 * @property workflowId - Unique identifier for the workflow
 * @property startedAt - Optional ISO timestamp when planning started
 * @property className - Optional additional CSS classes
 */
interface PlanningIndicatorProps {
  workflowId: string;
  startedAt?: string | null;
  className?: string;
}

/**
 * Formats elapsed time as a human-readable string.
 * @param startedAt - ISO timestamp when planning started
 * @returns Formatted elapsed time string (e.g., "30s", "2m 15s")
 */
function formatElapsedTime(startedAt: string): string {
  const start = new Date(startedAt).getTime();
  const now = Date.now();
  const elapsed = Math.floor((now - start) / 1000);

  if (elapsed < 60) {
    return `${elapsed}s`;
  }

  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;

  if (minutes < 60) {
    return seconds > 0 ? `${minutes}m ${seconds}s` : `${minutes}m`;
  }

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}h ${remainingMinutes}m`;
}

/**
 * Displays a planning indicator for workflows where the Architect
 * is currently generating an implementation plan.
 *
 * Shows:
 * - "PLANNING" heading with animated indicator
 * - Elapsed time since planning started
 * - Cancel button to abort the planning process
 *
 * @param props - Component props
 * @returns The planning indicator UI
 *
 * @example
 * ```tsx
 * <PlanningIndicator
 *   workflowId="wf-123"
 *   startedAt="2025-01-01T10:00:00Z"
 * />
 * ```
 */
export function PlanningIndicator({
  workflowId,
  startedAt,
  className,
}: PlanningIndicatorProps) {
  const revalidator = useRevalidator();
  const [isCancelling, setIsCancelling] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(() =>
    startedAt ? formatElapsedTime(startedAt) : '0s'
  );

  // Update elapsed time every second
  useEffect(() => {
    if (!startedAt) return;

    const updateElapsed = () => {
      setElapsedTime(formatElapsedTime(startedAt));
    };

    // Update immediately
    updateElapsed();

    // Then update every second
    const interval = setInterval(updateElapsed, 1000);
    return () => clearInterval(interval);
  }, [startedAt]);

  const handleCancel = useCallback(async () => {
    setIsCancelling(true);
    try {
      await api.cancelWorkflow(workflowId);
      success('Planning cancelled');
      revalidator.revalidate();
    } catch (err) {
      toastError('Failed to cancel planning');
      console.error('Failed to cancel planning:', err);
    } finally {
      setIsCancelling(false);
    }
  }, [workflowId, revalidator]);

  return (
    <div
      data-slot="planning-indicator"
      className={cn(
        'p-4 border border-status-pending/30 rounded-lg bg-status-pending/5 flex flex-col gap-3',
        className
      )}
    >
      <div className="flex items-center justify-between">
        <h4 className="font-heading text-xs font-semibold tracking-widest text-status-pending">
          PLANNING
        </h4>
        {startedAt && (
          <span className="text-sm font-mono text-muted-foreground">
            {elapsedTime}
          </span>
        )}
      </div>

      <div className="flex items-center gap-3">
        <Loader className="w-4 h-4 text-status-pending" />
        <p className="text-sm text-muted-foreground">
          Architect is analyzing the issue and generating an implementation plan...
        </p>
      </div>

      <div className="flex gap-3">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleCancel}
          disabled={isCancelling}
          className="border-destructive text-destructive hover:bg-destructive hover:text-foreground focus-visible:ring-destructive/50"
        >
          {isCancelling ? (
            <Loader className="w-4 h-4 mr-2" />
          ) : (
            <X className="w-4 h-4 mr-2" />
          )}
          Cancel
        </Button>
      </div>
    </div>
  );
}
