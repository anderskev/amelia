import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api, ApiError } from './client';

describe('api.createWorkflow', () => {
  const mockFetch = vi.fn();
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = mockFetch;
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.resetAllMocks();
  });

  it('creates workflow with required fields', async () => {
    const mockResponse = {
      id: 'wf-abc123',
      status: 'pending',
      message: 'Workflow created for issue TASK-001',
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await api.createWorkflow({
      issue_id: 'TASK-001',
      worktree_path: '/Users/me/projects/repo',
      task_title: 'Add logout button',
    });

    expect(mockFetch).toHaveBeenCalledWith('/api/workflows', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        issue_id: 'TASK-001',
        worktree_path: '/Users/me/projects/repo',
        task_title: 'Add logout button',
      }),
    });
    expect(result).toEqual(mockResponse);
  });

  it('creates workflow with all fields', async () => {
    const mockResponse = {
      id: 'wf-abc123',
      status: 'pending',
      message: 'Workflow created',
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    await api.createWorkflow({
      issue_id: 'TASK-001',
      worktree_path: '/Users/me/projects/repo',
      profile: 'noop-local',
      task_title: 'Add logout button',
      task_description: 'Add a logout button to the navbar',
    });

    expect(mockFetch).toHaveBeenCalledWith('/api/workflows', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        issue_id: 'TASK-001',
        worktree_path: '/Users/me/projects/repo',
        profile: 'noop-local',
        task_title: 'Add logout button',
        task_description: 'Add a logout button to the navbar',
      }),
    });
  });

  it('throws ApiError on 400 validation error', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: () =>
        Promise.resolve({
          error: 'Invalid worktree path',
          code: 'VALIDATION_ERROR',
        }),
    });

    await expect(
      api.createWorkflow({
        issue_id: 'TASK-001',
        worktree_path: 'not-absolute',
        task_title: 'Test',
      })
    ).rejects.toThrow(ApiError);
  });

  it('throws ApiError on 409 conflict', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 409,
      json: () =>
        Promise.resolve({
          error: 'Worktree already has an active workflow',
          code: 'WORKTREE_IN_USE',
        }),
    });

    await expect(
      api.createWorkflow({
        issue_id: 'TASK-001',
        worktree_path: '/Users/me/projects/repo',
        task_title: 'Test',
      })
    ).rejects.toThrow(ApiError);
  });
});
