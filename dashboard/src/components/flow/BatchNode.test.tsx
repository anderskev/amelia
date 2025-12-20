import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ReactFlowProvider, Position } from '@xyflow/react';
import { BatchNode, type BatchNodeData } from './BatchNode';

const renderNode = (data: BatchNodeData) => {
  return render(
    <ReactFlowProvider>
      <BatchNode
        id="test"
        draggable={false}
        selectable={false}
        deletable={false}
        data={data}
        type="batch"
        selected={false}
        isConnectable={false}
        positionAbsoluteX={0}
        positionAbsoluteY={0}
        zIndex={0}
        dragging={false}
        sourcePosition={Position.Bottom}
        targetPosition={Position.Top}
      />
    </ReactFlowProvider>
  );
};

describe('BatchNode', () => {
  it('renders batch number', () => {
    renderNode({
      batchNumber: 1,
      riskLevel: 'low',
      status: 'pending'
    });
    expect(screen.getByText('Batch 1')).toBeInTheDocument();
  });

  it('renders description when provided', () => {
    renderNode({
      batchNumber: 2,
      riskLevel: 'medium',
      description: 'Setup database schema',
      status: 'in_progress'
    });
    expect(screen.getByText('Setup database schema')).toBeInTheDocument();
  });

  it('renders without description', () => {
    renderNode({
      batchNumber: 1,
      riskLevel: 'low',
      status: 'pending'
    });
    expect(screen.getByText('Batch 1')).toBeInTheDocument();
    expect(screen.queryByRole('paragraph')).not.toBeInTheDocument();
  });

  it('has proper ARIA label', () => {
    renderNode({
      batchNumber: 1,
      riskLevel: 'low',
      description: 'Initial setup',
      status: 'complete'
    });
    expect(screen.getByRole('img')).toHaveAttribute(
      'aria-label',
      'Batch 1: Initial setup (complete, low risk)'
    );
  });

  it('has proper ARIA label without description', () => {
    renderNode({
      batchNumber: 2,
      riskLevel: 'high',
      status: 'blocked'
    });
    expect(screen.getByRole('img')).toHaveAttribute(
      'aria-label',
      'Batch 2 (blocked, high risk)'
    );
  });

  it('renders node content within a card container', () => {
    renderNode({
      batchNumber: 1,
      riskLevel: 'low',
      status: 'pending'
    });

    const card = screen.getByTestId('batch-node-card');
    expect(card).toBeInTheDocument();
    expect(card).toHaveClass('rounded-md', 'border');
  });

  describe('risk level badge styling', () => {
    it('applies green/teal styling for low risk', () => {
      renderNode({
        batchNumber: 1,
        riskLevel: 'low',
        status: 'pending'
      });

      const badge = screen.getByText('Low Risk');
      expect(badge).toHaveClass('text-status-completed');
      expect(badge).toHaveClass('border-status-completed');
    });

    it('applies amber styling for medium risk', () => {
      renderNode({
        batchNumber: 1,
        riskLevel: 'medium',
        status: 'pending'
      });

      const badge = screen.getByText('Medium Risk');
      expect(badge).toHaveClass('text-amber-600');
      expect(badge).toHaveClass('border-amber-600');
    });

    it('applies red/destructive styling for high risk', () => {
      renderNode({
        batchNumber: 1,
        riskLevel: 'high',
        status: 'pending'
      });

      const badge = screen.getByText('High Risk');
      expect(badge).toHaveClass('text-destructive');
      expect(badge).toHaveClass('border-destructive');
    });
  });

  describe('status-based card styling', () => {
    it.each([
      { status: 'pending' as const, borderClass: 'border-border', bgClass: 'bg-card/60' },
      { status: 'in_progress' as const, borderClass: 'border-primary/60', bgClass: 'bg-primary/10' },
      { status: 'complete' as const, borderClass: 'border-status-completed/40', bgClass: 'bg-status-completed/5' },
      { status: 'blocked' as const, borderClass: 'border-destructive/40', bgClass: 'bg-destructive/5' },
      { status: 'partial' as const, borderClass: 'border-amber-600/40', bgClass: 'bg-amber-600/5' },
    ])('applies correct styling for $status status', ({ status, borderClass, bgClass }) => {
      renderNode({
        batchNumber: 1,
        riskLevel: 'low',
        status
      });

      const card = screen.getByTestId('batch-node-card');
      expect(card).toHaveClass(borderClass);
      expect(card).toHaveClass(bgClass);
    });
  });

  describe('status-based card shadows', () => {
    it('applies elevated shadow with glow for in_progress status', () => {
      renderNode({
        batchNumber: 1,
        riskLevel: 'low',
        status: 'in_progress'
      });

      const card = screen.getByTestId('batch-node-card');
      expect(card).toHaveClass('shadow-lg');
    });

    it('applies medium shadow for complete status', () => {
      renderNode({
        batchNumber: 1,
        riskLevel: 'low',
        status: 'complete'
      });

      const card = screen.getByTestId('batch-node-card');
      expect(card).toHaveClass('shadow-md');
    });

    it('applies small shadow for pending status', () => {
      renderNode({
        batchNumber: 1,
        riskLevel: 'low',
        status: 'pending'
      });

      const card = screen.getByTestId('batch-node-card');
      expect(card).toHaveClass('shadow-sm');
    });

    it('applies medium shadow for blocked status', () => {
      renderNode({
        batchNumber: 1,
        riskLevel: 'low',
        status: 'blocked'
      });

      const card = screen.getByTestId('batch-node-card');
      expect(card).toHaveClass('shadow-md');
    });
  });

  it('positions handles correctly for horizontal flow', () => {
    renderNode({
      batchNumber: 1,
      riskLevel: 'low',
      status: 'pending'
    });

    const handles = document.querySelectorAll('.react-flow__handle');
    expect(handles.length).toBe(2); // source and target

    const targetHandle = document.querySelector('.react-flow__handle-left');
    const sourceHandle = document.querySelector('.react-flow__handle-right');
    expect(targetHandle).toBeInTheDocument();
    expect(sourceHandle).toBeInTheDocument();
  });

  it('stores data attributes for status and risk', () => {
    renderNode({
      batchNumber: 1,
      riskLevel: 'high',
      status: 'in_progress'
    });

    const card = screen.getByTestId('batch-node-card');
    expect(card).toHaveAttribute('data-status', 'in_progress');
    expect(card).toHaveAttribute('data-risk', 'high');
  });

  describe('visual hierarchy', () => {
    it('displays batch number badge prominently', () => {
      renderNode({
        batchNumber: 3,
        riskLevel: 'low',
        status: 'pending'
      });

      const batchBadge = screen.getByText('Batch 3');
      expect(batchBadge).toHaveClass('font-heading', 'font-semibold');
    });

    it('displays risk level badge', () => {
      renderNode({
        batchNumber: 1,
        riskLevel: 'medium',
        status: 'pending'
      });

      const riskBadge = screen.getByText('Medium Risk');
      expect(riskBadge).toBeInTheDocument();
    });
  });
});
