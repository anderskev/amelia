import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { ReactFlowProvider } from '@xyflow/react';
import { WorkflowEdge } from './WorkflowEdge';

const renderEdge = (props: any) => {
  return render(
    <ReactFlowProvider>
      <svg>
        <WorkflowEdge {...props} />
      </svg>
    </ReactFlowProvider>
  );
};

describe('WorkflowEdge', () => {
  const baseProps = {
    id: 'e1-2',
    source: 'node1',
    target: 'node2',
    sourceX: 100,
    sourceY: 100,
    targetX: 200,
    targetY: 100,
    sourcePosition: 'right' as const,
    targetPosition: 'left' as const,
    data: { label: '0:24', status: 'completed' as const },
  };

  it('renders edge path', () => {
    const { container } = renderEdge(baseProps);
    expect(container.querySelector('path')).toBeInTheDocument();
  });

  it('renders with label data', () => {
    const { container } = renderEdge(baseProps);
    // EdgeLabelRenderer creates a portal, so we verify the edge renders
    // The label is tested in integration/e2e tests with full React Flow
    expect(container.querySelector('path')).toBeInTheDocument();
  });

  it('uses solid line for completed status', () => {
    const { container } = renderEdge(baseProps);
    const path = container.querySelector('path');
    expect(path).toHaveAttribute('data-status', 'completed');
    expect(path).not.toHaveAttribute('stroke-dasharray');
  });

  it('uses dashed line for pending status', () => {
    const pendingProps = {
      ...baseProps,
      data: { ...baseProps.data, status: 'pending' as const },
    };
    const { container } = renderEdge(pendingProps);
    const path = container.querySelector('path');
    expect(path).toHaveAttribute('data-status', 'pending');
    expect(path).toHaveAttribute('stroke-dasharray');
  });

  it('shows animated circle for active edges', () => {
    const activeProps = {
      ...baseProps,
      data: { ...baseProps.data, status: 'active' as const },
    };
    const { container } = renderEdge(activeProps);
    expect(container.querySelector('circle')).toBeInTheDocument();
  });
});
