import { useFetcher } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Loader } from '@/components/ai-elements/loader';
import { Check, X } from 'lucide-react';
import { cn } from '@/lib/utils';

type ApprovalStatus = 'pending' | 'approved' | 'rejected';

interface ApprovalControlsProps {
  workflowId: string;
  planSummary: string;
  status?: ApprovalStatus;
  className?: string;
}

export function ApprovalControls({
  workflowId,
  planSummary,
  status = 'pending',
  className,
}: ApprovalControlsProps) {
  const fetcher = useFetcher();
  const isPending = fetcher.state !== 'idle';

  return (
    <div
      data-slot="approval-controls"
      className={cn(
        'p-4 border border-border rounded-lg bg-card',
        className
      )}
    >
      <h3 className="font-heading text-lg font-semibold mb-2">
        {planSummary}
      </h3>

      <p className="text-sm text-muted-foreground mb-4">
        Review and approve this plan to proceed with implementation.
      </p>

      {status === 'pending' && (
        <div className="flex gap-3">
          <fetcher.Form method="post" action={`/workflows/${workflowId}/approve`}>
            <Button
              type="submit"
              disabled={isPending}
              className="bg-status-completed hover:bg-status-completed/90"
            >
              {isPending ? (
                <Loader className="w-4 h-4 mr-2" />
              ) : (
                <Check className="w-4 h-4 mr-2" />
              )}
              Approve
            </Button>
          </fetcher.Form>

          <fetcher.Form method="post" action={`/workflows/${workflowId}/reject`}>
            <input type="hidden" name="feedback" value="Rejected by user" />
            <Button
              type="submit"
              variant="outline"
              disabled={isPending}
              className="border-destructive text-destructive hover:bg-destructive hover:text-foreground"
            >
              {isPending ? (
                <Loader className="w-4 h-4 mr-2" />
              ) : (
                <X className="w-4 h-4 mr-2" />
              )}
              Reject
            </Button>
          </fetcher.Form>
        </div>
      )}

      {status === 'approved' && (
        <div className="flex items-center gap-2 text-status-completed font-semibold">
          <Check className="w-4 h-4" />
          Plan approved. Implementation starting...
        </div>
      )}

      {status === 'rejected' && (
        <div className="flex items-center gap-2 text-destructive font-semibold">
          <X className="w-4 h-4" />
          Plan rejected. Awaiting revision...
        </div>
      )}
    </div>
  );
}
