import { describe, it, expect, vi, beforeEach } from 'vitest';
import { approveAction, rejectAction, cancelAction } from '../workflows';
import { api } from '../../api/client';

vi.mock('../../api/client');

describe('Workflow Actions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('approveAction', () => {
    it('should approve workflow by ID from params', async () => {
      vi.mocked(api.approveWorkflow).mockResolvedValueOnce(undefined);

      const result = await approveAction({
        params: { id: 'wf-1' },
        request: new Request('http://localhost/workflows/wf-1/approve', { method: 'POST' }),
      } as unknown as Parameters<typeof approveAction>[0]);

      expect(api.approveWorkflow).toHaveBeenCalledWith('wf-1');
      expect(result).toEqual({ success: true, action: 'approved' });
    });

    it('should throw 400 if ID is missing', async () => {
      try {
        await approveAction({
          params: {},
          request: new Request('http://localhost/workflows/approve', { method: 'POST' }),
        } as unknown as Parameters<typeof approveAction>[0]);
        expect.fail('Should have thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(Response);
        expect((error as Response).status).toBe(400);
      }
    });

    it('should propagate API errors', async () => {
      vi.mocked(api.approveWorkflow).mockRejectedValueOnce(new Error('Server error'));

      await expect(
        approveAction({
          params: { id: 'wf-1' },
          request: new Request('http://localhost/workflows/wf-1/approve', { method: 'POST' }),
        } as unknown as Parameters<typeof approveAction>[0])
      ).rejects.toThrow('Server error');
    });
  });

  describe('rejectAction', () => {
    it('should reject workflow with feedback from form data', async () => {
      vi.mocked(api.rejectWorkflow).mockResolvedValueOnce(undefined);

      const formData = new FormData();
      formData.append('feedback', 'Plan needs revision');

      const request = new Request('http://localhost/workflows/wf-1/reject', {
        method: 'POST',
        body: formData,
      });

      const result = await rejectAction({
        params: { id: 'wf-1' },
        request,
      } as unknown as Parameters<typeof rejectAction>[0]);

      expect(api.rejectWorkflow).toHaveBeenCalledWith('wf-1', 'Plan needs revision');
      expect(result).toEqual({ success: true, action: 'rejected' });
    });

    it('should throw 400 if ID is missing', async () => {
      const formData = new FormData();
      formData.append('feedback', 'Test');

      const request = new Request('http://localhost/workflows/reject', {
        method: 'POST',
        body: formData,
      });

      try {
        await rejectAction({
          params: {},
          request,
        } as unknown as Parameters<typeof rejectAction>[0]);
        expect.fail('Should have thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(Response);
        expect((error as Response).status).toBe(400);
      }
    });
  });

  describe('cancelAction', () => {
    it('should cancel workflow by ID from params', async () => {
      vi.mocked(api.cancelWorkflow).mockResolvedValueOnce(undefined);

      const result = await cancelAction({
        params: { id: 'wf-1' },
        request: new Request('http://localhost/workflows/wf-1/cancel', { method: 'POST' }),
      } as unknown as Parameters<typeof cancelAction>[0]);

      expect(api.cancelWorkflow).toHaveBeenCalledWith('wf-1');
      expect(result).toEqual({ success: true, action: 'cancelled' });
    });

    it('should throw 400 if ID is missing', async () => {
      try {
        await cancelAction({
          params: {},
          request: new Request('http://localhost/workflows/cancel', { method: 'POST' }),
        } as unknown as Parameters<typeof cancelAction>[0]);
        expect.fail('Should have thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(Response);
        expect((error as Response).status).toBe(400);
      }
    });
  });
});
