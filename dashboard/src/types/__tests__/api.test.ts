import { describe, it, expect } from 'vitest';
import type {
  WorkflowsLoaderData,
  WorkflowDetailLoaderData,
  ActionResult,
} from '../api';

describe('React Router Type Definitions', () => {
  it('should create valid WorkflowsLoaderData object', () => {
    const loaderData: WorkflowsLoaderData = {
      workflows: [
        {
          id: 'wf-123',
          issue_id: 'ISSUE-456',
          worktree_name: 'feature-branch',
          status: 'in_progress',
          started_at: '2025-12-01T10:00:00Z',
          current_stage: 'architect',
        },
      ],
    };

    expect(loaderData.workflows).toHaveLength(1);
    expect(loaderData.workflows[0]!.id).toBe('wf-123');
  });

  it('should create valid WorkflowDetailLoaderData object', () => {
    const loaderData: WorkflowDetailLoaderData = {
      workflow: {
        id: 'wf-123',
        issue_id: 'ISSUE-456',
        worktree_path: '/path',
        worktree_name: 'feature-branch',
        status: 'in_progress',
        started_at: '2025-12-01T10:00:00Z',
        completed_at: null,
        failure_reason: null,
        current_stage: 'architect',
        plan: null,
        token_usage: {},
        recent_events: [],
      },
    };

    expect(loaderData.workflow.id).toBe('wf-123');
  });

  it('should create valid ActionResult object', () => {
    const result: ActionResult = {
      success: true,
      action: 'approved',
    };

    expect(result.success).toBe(true);
    expect(result.action).toBe('approved');
  });
});
