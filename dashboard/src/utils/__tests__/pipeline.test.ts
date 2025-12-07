import { describe, it, expect } from 'vitest';
import { buildPipeline } from '../pipeline';
import type { WorkflowDetail, TaskDAG, TaskNode } from '@/types';

// Helper to create a minimal workflow detail
function createWorkflowDetail(plan: TaskDAG | null): WorkflowDetail {
  return {
    id: 'test-id',
    issue_id: 'TEST-1',
    worktree_name: 'test-worktree',
    worktree_path: '/tmp/test-worktree',
    status: 'in_progress',
    current_stage: 'developer',
    started_at: '2025-01-01T00:00:00Z',
    completed_at: null,
    failure_reason: null,
    plan,
    token_usage: {},
    recent_events: [],
  };
}

function createTask(overrides: Partial<TaskNode> = {}): TaskNode {
  return {
    id: 'task-1',
    agent: 'developer',
    description: 'Test task',
    status: 'pending',
    dependencies: [],
    ...overrides,
  };
}

describe('buildPipeline', () => {
  it('should convert workflow detail to pipeline nodes', () => {
    const workflow = createWorkflowDetail({
      tasks: [
        createTask({ id: 't1', agent: 'architect', description: 'Plan', status: 'completed' }),
        createTask({ id: 't2', agent: 'developer', description: 'Code', status: 'in_progress' }),
      ],
      execution_order: ['t1', 't2'],
    });

    const result = buildPipeline(workflow);

    expect(result).not.toBeNull();
    expect(result!.nodes).toHaveLength(2);
    expect(result!.nodes[0]).toEqual({
      id: 't1',
      label: 'architect',
      subtitle: 'Plan',
      status: 'completed',
    });
    expect(result!.nodes[1]).toEqual({
      id: 't2',
      label: 'developer',
      subtitle: 'Code',
      status: 'active',
    });
  });

  it('should create edges between sequential stages', () => {
    const workflow = createWorkflowDetail({
      tasks: [
        createTask({ id: 't1', dependencies: [] }),
        createTask({ id: 't2', dependencies: ['t1'] }),
        createTask({ id: 't3', dependencies: ['t2'] }),
      ],
      execution_order: ['t1', 't2', 't3'],
    });

    const result = buildPipeline(workflow);

    expect(result!.edges).toHaveLength(2);
    expect(result!.edges).toContainEqual({
      from: 't1',
      to: 't2',
      label: '',
      status: 'completed',
    });
    expect(result!.edges).toContainEqual({
      from: 't2',
      to: 't3',
      label: '',
      status: 'completed',
    });
  });

  it('should mark current stage as active', () => {
    const workflow = createWorkflowDetail({
      tasks: [
        createTask({ id: 't1', status: 'in_progress' }),
      ],
      execution_order: ['t1'],
    });

    const result = buildPipeline(workflow);

    expect(result!.nodes[0].status).toBe('active');
  });

  it('should handle empty stages array', () => {
    const workflow = createWorkflowDetail({ tasks: [], execution_order: [] });

    const result = buildPipeline(workflow);

    expect(result).not.toBeNull();
    expect(result!.nodes).toHaveLength(0);
    expect(result!.edges).toHaveLength(0);
  });

  it('should handle workflow detail with null plan', () => {
    const workflow = createWorkflowDetail(null);

    const result = buildPipeline(workflow);

    expect(result).toBeNull();
  });

  it('should handle stages with no dependencies', () => {
    const workflow = createWorkflowDetail({
      tasks: [
        createTask({ id: 't1', dependencies: [] }),
        createTask({ id: 't2', dependencies: [] }),
      ],
      execution_order: ['t1', 't2'],
    });

    const result = buildPipeline(workflow);

    expect(result!.edges).toHaveLength(0);
  });

  it('should filter out edges referencing non-existent tasks', () => {
    const workflow = createWorkflowDetail({
      tasks: [
        createTask({ id: 't1', dependencies: ['non-existent'] }),
        createTask({ id: 't2', dependencies: ['t1'] }),
      ],
      execution_order: ['t1', 't2'],
    });

    const result = buildPipeline(workflow);

    // Only t1 -> t2 edge should exist, not non-existent -> t1
    expect(result!.edges).toHaveLength(1);
    expect(result!.edges[0]).toEqual({
      from: 't1',
      to: 't2',
      label: '',
      status: 'completed',
    });
  });

  it('should map failed status to blocked', () => {
    const workflow = createWorkflowDetail({
      tasks: [
        createTask({ id: 't1', status: 'failed' }),
      ],
      execution_order: ['t1'],
    });

    const result = buildPipeline(workflow);

    expect(result!.nodes[0].status).toBe('blocked');
  });
});
