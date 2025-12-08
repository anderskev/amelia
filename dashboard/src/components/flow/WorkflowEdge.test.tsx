import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { ReactFlowProvider, Position, type EdgeProps } from '@xyflow/react';
import { WorkflowEdge, type WorkflowEdgeType, type WorkflowEdgeData } from './WorkflowEdge';

const baseProps: EdgeProps<WorkflowEdgeType> = {
  id: 'e1-2',
  source: 'node1',
  target: 'node2',
  sourceX: 100,
  sourceY: 100,
  targetX: 200,
  targetY: 100,
  sourcePosition: Position.Right,
  targetPosition: Position.Left,
  data: { label: '0:24', status: 'completed' as const },
};

const renderEdge = (overrides?: Partial<EdgeProps<WorkflowEdgeType>>) => {
  const props = { ...baseProps, ...overrides };
  return render(
    <ReactFlowProvider>
      <svg>
        <WorkflowEdge {...props} />
      </svg>
    </ReactFlowProvider>
  );
};

describe('WorkflowEdge', () => {

  it('renders edge path', () => {
    const { container } = renderEdge();
    // SVG paths don't have semantic roles, querySelector is appropriate here
    const path = container.querySelector('path');
    expect(path).toBeInTheDocument();
  });

  it.each([
    { status: 'completed' as const, hasDash: false },
    { status: 'pending' as const, hasDash: true },
    { status: 'active' as const, hasDash: true },
  ])('applies $status line style (dashed: $hasDash)', ({ status, hasDash }) => {
    const data: WorkflowEdgeData = { label: '0:24', status };
    const { container } = renderEdge({ data });
    const path = container.querySelector('path');
    expect(path).toHaveAttribute('data-status', status);
    if (hasDash) {
      expect(path).toHaveAttribute('stroke-dasharray');
    } else {
      expect(path).not.toHaveAttribute('stroke-dasharray');
    }
  });

});
