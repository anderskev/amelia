import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useWorkflowActions } from '../useWorkflowActions';
import { useWorkflowStore } from '../../store/workflowStore';
import { api } from '../../api/client';
import * as toast from '../../components/Toast';

vi.mock('../../api/client');
vi.mock('../../components/Toast', () => ({
  success: vi.fn(),
  error: vi.fn(),
  info: vi.fn(),
}));

describe('useWorkflowActions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useWorkflowStore.setState({
      selectedWorkflowId: null,
      eventsByWorkflow: {},
      lastEventId: null,
      isConnected: false,
      connectionError: null,
      pendingActions: [],
    });
  });

  describe('approveWorkflow', () => {
    it('should add pending action during request', async () => {
      vi.mocked(api.approveWorkflow).mockImplementationOnce(
        () => new Promise((resolve) => { setTimeout(resolve, 100); })
      );

      const { result } = renderHook(() => useWorkflowActions());
      result.current.approveWorkflow('wf-1', 'blocked');

      await waitFor(() => {
        expect(useWorkflowStore.getState().pendingActions.includes('approve-wf-1')).toBe(true);
      });

      await waitFor(() => {
        expect(useWorkflowStore.getState().pendingActions.includes('approve-wf-1')).toBe(false);
      });
    });

    it('should show success toast on success', async () => {
      vi.mocked(api.approveWorkflow).mockResolvedValueOnce(undefined);

      const { result } = renderHook(() => useWorkflowActions());
      await result.current.approveWorkflow('wf-1', 'blocked');

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith('Plan approved');
      });
    });

    it('should show error toast on failure', async () => {
      vi.mocked(api.approveWorkflow).mockRejectedValueOnce(new Error('Server error'));

      const { result } = renderHook(() => useWorkflowActions());
      await result.current.approveWorkflow('wf-1', 'blocked');

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Approval failed: Server error');
      });
    });
  });

  describe('rejectWorkflow', () => {
    it('should show success toast on success', async () => {
      vi.mocked(api.rejectWorkflow).mockResolvedValueOnce(undefined);

      const { result } = renderHook(() => useWorkflowActions());
      await result.current.rejectWorkflow('wf-1', 'Needs revision', 'blocked');

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith('Plan rejected');
      });
    });

    it('should show error toast on failure', async () => {
      vi.mocked(api.rejectWorkflow).mockRejectedValueOnce(new Error('Server error'));

      const { result } = renderHook(() => useWorkflowActions());
      await result.current.rejectWorkflow('wf-1', 'Needs revision', 'blocked');

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Rejection failed: Server error');
      });
    });
  });

  describe('cancelWorkflow', () => {
    it('should show success toast on success', async () => {
      vi.mocked(api.cancelWorkflow).mockResolvedValueOnce(undefined);

      const { result } = renderHook(() => useWorkflowActions());
      await result.current.cancelWorkflow('wf-1', 'in_progress');

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith('Workflow cancelled');
      });
    });

    it('should show error toast on failure', async () => {
      vi.mocked(api.cancelWorkflow).mockRejectedValueOnce(new Error('Server error'));

      const { result } = renderHook(() => useWorkflowActions());
      await result.current.cancelWorkflow('wf-1', 'in_progress');

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Cancellation failed: Server error');
      });
    });
  });

  describe('isActionPending', () => {
    it('should return true if action is pending', () => {
      useWorkflowStore.setState({ pendingActions: ['approve-wf-1'] });

      const { result } = renderHook(() => useWorkflowActions());

      expect(result.current.isActionPending('wf-1')).toBe(true);
    });

    it('should return false if no action is pending', () => {
      useWorkflowStore.setState({ pendingActions: [] });

      const { result } = renderHook(() => useWorkflowActions());

      expect(result.current.isActionPending('wf-1')).toBe(false);
    });

    it('should check for any action type for the workflow', () => {
      useWorkflowStore.setState({ pendingActions: ['reject-wf-1'] });

      const { result } = renderHook(() => useWorkflowActions());

      expect(result.current.isActionPending('wf-1')).toBe(true);
    });
  });
});
