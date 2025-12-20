import { describe, it, expect } from 'vitest';
import { buildPipeline } from '../pipeline';
import type { WorkflowDetail, ExecutionPlan } from '@/types';

// Helper to create a minimal workflow detail
function createWorkflowDetail(
  executionPlan: ExecutionPlan | null,
  currentBatchIndex = 0,
  status: WorkflowDetail['status'] = 'in_progress'
): WorkflowDetail {
  return {
    id: 'test-id',
    issue_id: 'TEST-1',
    worktree_name: 'test-worktree',
    worktree_path: '/tmp/test-worktree',
    status,
    current_stage: 'developer',
    started_at: '2025-01-01T00:00:00Z',
    completed_at: null,
    failure_reason: null,
    token_usage: {},
    recent_events: [],
    // Batch execution fields
    execution_plan: executionPlan,
    current_batch_index: currentBatchIndex,
    batch_results: [],
    developer_status: null,
    current_blocker: null,
    batch_approvals: [],
  };
}

function createExecutionPlan(batches: ExecutionPlan['batches']): ExecutionPlan {
  return {
    goal: 'Test goal',
    batches,
    total_estimated_minutes: 60,
    tdd_approach: true,
  };
}

describe('buildPipeline', () => {
  it('should convert workflow detail to pipeline nodes', () => {
    const plan = createExecutionPlan([
      {
        batch_number: 1,
        description: 'First batch',
        risk_summary: 'low',
        steps: [
          { id: 'step-1', description: 'Plan the architecture', action_type: 'code' },
          { id: 'step-2', description: 'Write the code', action_type: 'code' },
        ],
      },
    ]);

    const workflow = createWorkflowDetail(plan, 0);
    const result = buildPipeline(workflow);

    expect(result).not.toBeNull();
    expect(result!.nodes).toHaveLength(2);
    expect(result!.nodes[0]).toEqual({
      id: 'batch-1-step-step-1',
      label: 'Plan the architectu…', // truncated to 20 chars
      subtitle: 'First batch',
      status: 'active',
    });
    expect(result!.nodes[1]).toEqual({
      id: 'batch-1-step-step-2',
      label: 'Write the code', // under 20 chars, no truncation
      subtitle: 'First batch',
      status: 'active',
    });
  });

  it('should create edges between steps in the same batch', () => {
    const plan = createExecutionPlan([
      {
        batch_number: 1,
        description: 'First batch',
        risk_summary: 'low',
        steps: [
          { id: 'step-1', description: 'Step 1', action_type: 'code' },
          { id: 'step-2', description: 'Step 2', action_type: 'code' },
          { id: 'step-3', description: 'Step 3', action_type: 'code' },
        ],
      },
    ]);

    const workflow = createWorkflowDetail(plan);
    const result = buildPipeline(workflow);

    expect(result!.edges).toHaveLength(2);
    expect(result!.edges).toContainEqual({
      from: 'batch-1-step-step-1',
      to: 'batch-1-step-step-2',
      label: '',
      status: 'active',
    });
    expect(result!.edges).toContainEqual({
      from: 'batch-1-step-step-2',
      to: 'batch-1-step-step-3',
      label: '',
      status: 'active',
    });
  });

  it('should create edges between batches', () => {
    const plan = createExecutionPlan([
      {
        batch_number: 1,
        description: 'First batch',
        risk_summary: 'low',
        steps: [{ id: 'step-1', description: 'Step 1', action_type: 'code' }],
      },
      {
        batch_number: 2,
        description: 'Second batch',
        risk_summary: 'medium',
        steps: [{ id: 'step-2', description: 'Step 2', action_type: 'code' }],
      },
    ]);

    const workflow = createWorkflowDetail(plan, 1);
    const result = buildPipeline(workflow);

    // Should have edge from batch 1 last step to batch 2 first step
    expect(result!.edges).toContainEqual({
      from: 'batch-1-step-step-1',
      to: 'batch-2-step-step-2',
      label: 'Batch 2',
      status: 'active',
    });
  });

  it('should mark current batch as active', () => {
    const plan = createExecutionPlan([
      {
        batch_number: 1,
        description: 'First batch',
        risk_summary: 'low',
        steps: [{ id: 'step-1', description: 'Step 1', action_type: 'code' }],
      },
    ]);

    const workflow = createWorkflowDetail(plan, 0);
    const result = buildPipeline(workflow);

    expect(result).not.toBeNull();
    expect(result!.nodes[0]!.status).toBe('active');
  });

  it('should mark completed batches as completed', () => {
    const plan = createExecutionPlan([
      {
        batch_number: 1,
        description: 'First batch',
        risk_summary: 'low',
        steps: [{ id: 'step-1', description: 'Step 1', action_type: 'code' }],
      },
      {
        batch_number: 2,
        description: 'Second batch',
        risk_summary: 'medium',
        steps: [{ id: 'step-2', description: 'Step 2', action_type: 'code' }],
      },
    ]);

    const workflow = createWorkflowDetail(plan, 1); // Currently on batch 2
    const result = buildPipeline(workflow);

    expect(result!.nodes[0]!.status).toBe('completed'); // Batch 1
    expect(result!.nodes[1]!.status).toBe('active'); // Batch 2
  });

  it('should mark pending batches as pending', () => {
    const plan = createExecutionPlan([
      {
        batch_number: 1,
        description: 'First batch',
        risk_summary: 'low',
        steps: [{ id: 'step-1', description: 'Step 1', action_type: 'code' }],
      },
      {
        batch_number: 2,
        description: 'Second batch',
        risk_summary: 'medium',
        steps: [{ id: 'step-2', description: 'Step 2', action_type: 'code' }],
      },
    ]);

    const workflow = createWorkflowDetail(plan, 0); // Currently on batch 1
    const result = buildPipeline(workflow);

    expect(result!.nodes[0]!.status).toBe('active'); // Batch 1
    expect(result!.nodes[1]!.status).toBe('pending'); // Batch 2
  });

  it('should handle empty batches array', () => {
    const plan = createExecutionPlan([]);
    const workflow = createWorkflowDetail(plan);

    const result = buildPipeline(workflow);

    expect(result).not.toBeNull();
    expect(result!.nodes).toHaveLength(0);
    expect(result!.edges).toHaveLength(0);
  });

  it('should handle workflow detail with null execution plan', () => {
    const workflow = createWorkflowDetail(null);

    const result = buildPipeline(workflow);

    expect(result).toBeNull();
  });

  it('should mark blocked workflow batch as blocked', () => {
    const plan = createExecutionPlan([
      {
        batch_number: 1,
        description: 'First batch',
        risk_summary: 'low',
        steps: [{ id: 'step-1', description: 'Step 1', action_type: 'code' }],
      },
    ]);

    const workflow = createWorkflowDetail(plan, 0, 'blocked');
    const result = buildPipeline(workflow);

    expect(result).not.toBeNull();
    expect(result!.nodes[0]!.status).toBe('blocked');
  });

  describe('edge status computation', () => {
    it('marks edges as completed for completed batches', () => {
      const plan = createExecutionPlan([
        {
          batch_number: 1,
          description: 'First batch',
          risk_summary: 'low',
          steps: [
            { id: 'step-1', description: 'Step 1', action_type: 'code' },
            { id: 'step-2', description: 'Step 2', action_type: 'code' },
          ],
        },
      ]);

      const workflow = createWorkflowDetail(plan, 1); // Past batch 1
      const result = buildPipeline(workflow);

      expect(result!.edges).toHaveLength(1);
      expect(result!.edges[0]).toMatchObject({ status: 'completed' });
    });

    it('marks edges as active for active batches', () => {
      const plan = createExecutionPlan([
        {
          batch_number: 1,
          description: 'First batch',
          risk_summary: 'low',
          steps: [
            { id: 'step-1', description: 'Step 1', action_type: 'code' },
            { id: 'step-2', description: 'Step 2', action_type: 'code' },
          ],
        },
      ]);

      const workflow = createWorkflowDetail(plan, 0); // On batch 1
      const result = buildPipeline(workflow);

      expect(result!.edges).toHaveLength(1);
      expect(result!.edges[0]).toMatchObject({ status: 'active' });
    });

    it('marks edges as pending for pending batches', () => {
      const plan = createExecutionPlan([
        {
          batch_number: 1,
          description: 'First batch',
          risk_summary: 'low',
          steps: [{ id: 'step-1', description: 'Step 1', action_type: 'code' }],
        },
        {
          batch_number: 2,
          description: 'Second batch',
          risk_summary: 'medium',
          steps: [
            { id: 'step-2', description: 'Step 2', action_type: 'code' },
            { id: 'step-3', description: 'Step 3', action_type: 'code' },
          ],
        },
      ]);

      const workflow = createWorkflowDetail(plan, 0); // On batch 1, batch 2 is pending
      const result = buildPipeline(workflow);

      // Find edge within batch 2
      const batch2Edge = result!.edges.find(
        e => e.from === 'batch-2-step-step-2' && e.to === 'batch-2-step-step-3'
      );
      expect(batch2Edge).toMatchObject({ status: 'pending' });
    });
  });
});
