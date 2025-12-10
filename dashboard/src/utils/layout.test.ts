// dashboard/src/utils/layout.test.ts
import { describe, it, expect } from 'vitest';
import { getLayoutedElements } from './layout';
import type { WorkflowNodeType } from '@/components/flow/WorkflowNode';
import type { WorkflowEdgeType } from '@/components/flow/WorkflowEdge';

describe('getLayoutedElements', () => {
  const mockNodes: WorkflowNodeType[] = [
    { id: '1', type: 'workflow', position: { x: 0, y: 0 }, data: { label: 'A', status: 'completed' } },
    { id: '2', type: 'workflow', position: { x: 0, y: 0 }, data: { label: 'B', status: 'active' } },
    { id: '3', type: 'workflow', position: { x: 0, y: 0 }, data: { label: 'C', status: 'pending' } },
  ];
  const mockEdges: WorkflowEdgeType[] = [];

  it('positions nodes horizontally with consistent spacing', () => {
    const result = getLayoutedElements(mockNodes, mockEdges);

    // All nodes should be on the same Y coordinate (horizontal layout)
    expect(result[0].position.y).toBe(0);
    expect(result[1].position.y).toBe(0);
    expect(result[2].position.y).toBe(0);

    // X coordinates should increase with spacing
    expect(result[0].position.x).toBe(0);
    expect(result[1].position.x).toBe(200);
    expect(result[2].position.x).toBe(400);
  });

  it('returns empty array for empty input', () => {
    const result = getLayoutedElements([], []);
    expect(result).toEqual([]);
  });

  it('preserves node data and type', () => {
    const result = getLayoutedElements(mockNodes, mockEdges);
    expect(result[0].data.label).toBe('A');
    expect(result[0].type).toBe('workflow');
  });
});
