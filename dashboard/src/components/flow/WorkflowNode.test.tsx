import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ReactFlowProvider, Position } from '@xyflow/react';
import { WorkflowNode, type WorkflowNodeData } from './WorkflowNode';

const renderNode = (data: WorkflowNodeData) => {
  return render(
    <ReactFlowProvider>
      <WorkflowNode
        id="test"
        data={data}
        type="workflow"
        selected={false}
        isConnectable={false}
        positionAbsoluteX={0}
        positionAbsoluteY={0}
        zIndex={0}
        dragging={false}
        sourcePosition={Position.Right}
        targetPosition={Position.Left}
      />
    </ReactFlowProvider>
  );
};

describe('WorkflowNode', () => {
  it('renders stage label', () => {
    renderNode({ label: 'Architect', status: 'completed' });
    expect(screen.getByText('Architect')).toBeInTheDocument();
  });

  it('renders subtitle when provided', () => {
    renderNode({ label: 'Architect', subtitle: 'Planning', status: 'completed' });
    expect(screen.getByText('Planning')).toBeInTheDocument();
  });

  it('renders token count when provided', () => {
    renderNode({ label: 'Architect', status: 'completed', tokens: '12.4k' });
    expect(screen.getByText('12.4k tokens')).toBeInTheDocument();
  });

  it('renders MapPin icon', () => {
    const { container } = renderNode({ label: 'Developer', status: 'active' });
    expect(container.querySelector('svg.lucide-map-pin')).toBeInTheDocument();
  });

  it.each([
    { status: 'active' as const, hasAnimation: true },
    { status: 'completed' as const, hasAnimation: false },
    { status: 'pending' as const, hasAnimation: false },
    { status: 'blocked' as const, hasAnimation: false },
  ])('applies $status status (animated: $hasAnimation)', ({ status, hasAnimation }) => {
    const { container } = renderNode({ label: 'Test', status });
    expect(container.querySelector(`[data-status="${status}"]`)).toBeInTheDocument();
    if (hasAnimation) {
      expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
    }
  });

  it('has proper ARIA label', () => {
    renderNode({ label: 'Architect', subtitle: 'Planning', status: 'completed' });
    expect(screen.getByRole('img')).toHaveAttribute(
      'aria-label',
      'Workflow stage: Architect - Planning (completed)'
    );
  });

  it('renders connection handles', () => {
    const { container } = renderNode({ label: 'Test', status: 'pending' });
    expect(container.querySelectorAll('.react-flow__handle')).toHaveLength(2);
  });
});
