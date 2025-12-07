import { useCallback } from 'react';
import { useWorkflowStore } from '../store/workflowStore';
import { api } from '../api/client';
import * as toast from '../components/Toast';
import type { WorkflowStatus } from '../types';

interface UseWorkflowActionsResult {
  approveWorkflow: (workflowId: string, previousStatus: WorkflowStatus) => Promise<void>;
  rejectWorkflow: (workflowId: string, feedback: string, previousStatus: WorkflowStatus) => Promise<void>;
  cancelWorkflow: (workflowId: string, previousStatus: WorkflowStatus) => Promise<void>;
  isActionPending: (workflowId: string) => boolean;
}

export function useWorkflowActions(): UseWorkflowActionsResult {
  const { addPendingAction, removePendingAction, pendingActions } = useWorkflowStore();

  const approveWorkflow = useCallback(
    async (workflowId: string, _previousStatus: WorkflowStatus) => {
      const actionId = `approve-${workflowId}`;
      addPendingAction(actionId);

      try {
        await api.approveWorkflow(workflowId);
        toast.success('Plan approved');
      } catch (error) {
        toast.error(`Approval failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      } finally {
        removePendingAction(actionId);
      }
    },
    [addPendingAction, removePendingAction]
  );

  const rejectWorkflow = useCallback(
    async (workflowId: string, feedback: string, _previousStatus: WorkflowStatus) => {
      const actionId = `reject-${workflowId}`;
      addPendingAction(actionId);

      try {
        await api.rejectWorkflow(workflowId, feedback);
        toast.success('Plan rejected');
      } catch (error) {
        toast.error(`Rejection failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      } finally {
        removePendingAction(actionId);
      }
    },
    [addPendingAction, removePendingAction]
  );

  const cancelWorkflow = useCallback(
    async (workflowId: string, _previousStatus: WorkflowStatus) => {
      const actionId = `cancel-${workflowId}`;
      addPendingAction(actionId);

      try {
        await api.cancelWorkflow(workflowId);
        toast.success('Workflow cancelled');
      } catch (error) {
        toast.error(`Cancellation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      } finally {
        removePendingAction(actionId);
      }
    },
    [addPendingAction, removePendingAction]
  );

  const isActionPending = useCallback(
    (workflowId: string) => {
      return pendingActions.some((id) => id.endsWith(workflowId));
    },
    [pendingActions]
  );

  return {
    approveWorkflow,
    rejectWorkflow,
    cancelWorkflow,
    isActionPending,
  };
}
