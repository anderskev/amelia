/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { workflowsLoader, workflowDetailLoader, historyLoader } from '../workflows';
import { api } from '../../api/client';
import { getActiveWorkflow } from '../../utils/workflow';
import type { LoaderFunctionArgs } from 'react-router-dom';

vi.mock('../../utils/workflow');

vi.mock('../../api/client');

/**
 * Helper to create LoaderFunctionArgs for testing
 */
function createLoaderArgs(params: Record<string, string>): LoaderFunctionArgs {
  return {
    params,
    request: new Request('http://localhost'),
  } as unknown as LoaderFunctionArgs;
}

/**
 * Mock workflow data fixtures
 */
const mockWorkflowSummary = {
  id: 'wf-1',
  issue_id: 'ISSUE-1',
  worktree_name: 'main',
  status: 'in_progress' as const,
  started_at: '2025-12-01T10:00:00Z',
  current_stage: 'architect',
};

const mockWorkflowDetail = {
  ...mockWorkflowSummary,
  worktree_path: '/path',
  completed_at: null,
  failure_reason: null,
  plan: null,
  token_usage: {},
  recent_events: [],
};

const mockWorkflowHistory = {
  id: 'wf-old',
  issue_id: 'ISSUE-OLD',
  worktree_name: 'old-branch',
  status: 'completed' as const,
  started_at: '2025-11-01T10:00:00Z',
  current_stage: null,
};

describe('Workflow Loaders', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('workflowsLoader', () => {
    it('should return workflows list and activeDetail in response', async () => {
      vi.mocked(api.getWorkflows).mockResolvedValueOnce([mockWorkflowSummary]);
      vi.mocked(getActiveWorkflow).mockReturnValueOnce(mockWorkflowSummary);
      vi.mocked(api.getWorkflow).mockResolvedValueOnce(mockWorkflowDetail);

      const result = await workflowsLoader(createLoaderArgs({}));

      expect(api.getWorkflows).toHaveBeenCalledTimes(1);
      expect(result).toHaveProperty('workflows');
      expect(result).toHaveProperty('activeDetail');
      expect(result.workflows).toEqual([mockWorkflowSummary]);
      expect(result.activeDetail).toEqual(mockWorkflowDetail);
    });

    it('should return null activeDetail when no workflows exist', async () => {
      vi.mocked(api.getWorkflows).mockResolvedValueOnce([]);
      vi.mocked(getActiveWorkflow).mockReturnValueOnce(null);

      const result = await workflowsLoader(createLoaderArgs({}));

      expect(result.workflows).toEqual([]);
      expect(result.activeDetail).toBeNull();
      expect(api.getWorkflow).not.toHaveBeenCalled();
    });

    it('should return null activeDetail when detail API call fails', async () => {
      vi.mocked(api.getWorkflows).mockResolvedValueOnce([mockWorkflowSummary]);
      vi.mocked(getActiveWorkflow).mockReturnValueOnce(mockWorkflowSummary);
      vi.mocked(api.getWorkflow).mockRejectedValueOnce(new Error('Detail fetch failed'));

      const result = await workflowsLoader(createLoaderArgs({}));

      expect(result.workflows).toEqual([mockWorkflowSummary]);
      expect(result.activeDetail).toBeNull();
    });

    it('should include active workflow detail when running workflow exists', async () => {
      const runningWorkflow = { ...mockWorkflowSummary, status: 'in_progress' as const };
      const runningDetail = { ...mockWorkflowDetail, status: 'in_progress' as const };
      vi.mocked(api.getWorkflows).mockResolvedValueOnce([runningWorkflow]);
      vi.mocked(getActiveWorkflow).mockReturnValueOnce(runningWorkflow);
      vi.mocked(api.getWorkflow).mockResolvedValueOnce(runningDetail);

      const result = await workflowsLoader(createLoaderArgs({}));

      expect(getActiveWorkflow).toHaveBeenCalledWith([runningWorkflow]);
      expect(api.getWorkflow).toHaveBeenCalledWith(runningWorkflow.id);
      expect(result.activeDetail).toEqual(runningDetail);
    });

    it('should propagate API errors from getWorkflows', async () => {
      vi.mocked(api.getWorkflows).mockRejectedValueOnce(new Error('Network error'));

      await expect(workflowsLoader(createLoaderArgs({}))).rejects.toThrow('Network error');
    });
  });

  describe('workflowDetailLoader', () => {
    it('should fetch workflow by ID from params', async () => {
      vi.mocked(api.getWorkflow).mockResolvedValueOnce(mockWorkflowDetail);

      const result = await workflowDetailLoader(createLoaderArgs({ id: 'wf-1' }));

      expect(api.getWorkflow).toHaveBeenCalledWith('wf-1');
      expect(result).toEqual({ workflow: mockWorkflowDetail });
    });

    it('should throw 400 if ID is missing', async () => {
      await expect(
        workflowDetailLoader(createLoaderArgs({}))
      ).rejects.toThrowError(
        expect.objectContaining({ status: 400 })
      );
    });
  });

  describe('historyLoader', () => {
    it('should fetch workflow history', async () => {
      vi.mocked(api.getWorkflowHistory).mockResolvedValueOnce([mockWorkflowHistory]);

      const result = await historyLoader(createLoaderArgs({}));

      expect(api.getWorkflowHistory).toHaveBeenCalledTimes(1);
      expect(result).toEqual({ workflows: [mockWorkflowHistory] });
    });
  });
});
