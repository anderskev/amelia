import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ReactFlowProvider, Position } from '@xyflow/react';
import { CheckpointMarker, type CheckpointMarkerData } from './CheckpointMarker';

const renderNode = (data: CheckpointMarkerData) => {
  return render(
    <ReactFlowProvider>
      <CheckpointMarker
        id="test"
        draggable={false}
        selectable={false}
        deletable={false}
        data={data}
        type="checkpoint"
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

describe('CheckpointMarker', () => {
  it('renders batch number', () => {
    renderNode({
      batchNumber: 1,
      status: 'pending',
    });
    expect(screen.getByText(/Batch 1/)).toBeInTheDocument();
  });

  describe('pending state', () => {
    it('shows pending status with Clock icon', () => {
      renderNode({
        batchNumber: 1,
        status: 'pending',
      });

      const icon = screen.getByTestId('status-icon-pending');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('lucide-clock');
    });

    it('displays "Awaiting Approval" text', () => {
      renderNode({
        batchNumber: 1,
        status: 'pending',
      });

      expect(screen.getByText('Awaiting Approval')).toBeInTheDocument();
    });

    it('applies muted styling to card', () => {
      renderNode({
        batchNumber: 1,
        status: 'pending',
      });

      const card = screen.getByTestId('checkpoint-marker-card');
      expect(card).toHaveClass('border-border');
      expect(card).toHaveClass('bg-muted/30');
    });

    it('has proper ARIA label', () => {
      renderNode({
        batchNumber: 1,
        status: 'pending',
      });

      expect(screen.getByRole('img')).toHaveAttribute(
        'aria-label',
        'Checkpoint after Batch 1: Awaiting Approval'
      );
    });
  });

  describe('approved state', () => {
    it('shows approved status with CheckCircle2 icon', () => {
      renderNode({
        batchNumber: 2,
        status: 'approved',
        approvedAt: '2025-12-15T10:30:45.123Z',
      });

      const icon = screen.getByTestId('status-icon-approved');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('lucide-check-circle-2');
    });

    it('displays "Approved" text', () => {
      renderNode({
        batchNumber: 2,
        status: 'approved',
        approvedAt: '2025-12-15T10:30:45.123Z',
      });

      expect(screen.getByText('Approved')).toBeInTheDocument();
    });

    it('applies green styling to card', () => {
      renderNode({
        batchNumber: 2,
        status: 'approved',
        approvedAt: '2025-12-15T10:30:45.123Z',
      });

      const card = screen.getByTestId('checkpoint-marker-card');
      expect(card).toHaveClass('border-status-completed/40');
      expect(card).toHaveClass('bg-status-completed/5');
    });

    it('shows approval timestamp when provided', () => {
      renderNode({
        batchNumber: 2,
        status: 'approved',
        approvedAt: '2025-12-15T10:30:45.123Z',
      });

      expect(screen.getByTestId('approval-timestamp')).toBeInTheDocument();
      expect(screen.getByTestId('approval-timestamp')).toHaveTextContent('10:30:45.123');
    });

    it('does not show timestamp when not provided', () => {
      renderNode({
        batchNumber: 2,
        status: 'approved',
      });

      expect(screen.queryByTestId('approval-timestamp')).not.toBeInTheDocument();
    });

    it('has proper ARIA label', () => {
      renderNode({
        batchNumber: 2,
        status: 'approved',
        approvedAt: '2025-12-15T10:30:45.123Z',
      });

      expect(screen.getByRole('img')).toHaveAttribute(
        'aria-label',
        'Checkpoint after Batch 2: Approved'
      );
    });
  });

  describe('rejected state', () => {
    it('shows rejected status with XCircle icon', () => {
      renderNode({
        batchNumber: 3,
        status: 'rejected',
        feedback: 'Tests are failing',
      });

      const icon = screen.getByTestId('status-icon-rejected');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('lucide-x-circle');
    });

    it('displays "Rejected" text', () => {
      renderNode({
        batchNumber: 3,
        status: 'rejected',
        feedback: 'Tests are failing',
      });

      expect(screen.getByText('Rejected')).toBeInTheDocument();
    });

    it('applies red/destructive styling to card', () => {
      renderNode({
        batchNumber: 3,
        status: 'rejected',
        feedback: 'Tests are failing',
      });

      const card = screen.getByTestId('checkpoint-marker-card');
      expect(card).toHaveClass('border-destructive/40');
      expect(card).toHaveClass('bg-destructive/5');
    });

    it('shows feedback text when provided', () => {
      renderNode({
        batchNumber: 3,
        status: 'rejected',
        feedback: 'Tests are failing',
      });

      expect(screen.getByText('Tests are failing')).toBeInTheDocument();
    });

    it('does not show feedback when not provided', () => {
      renderNode({
        batchNumber: 3,
        status: 'rejected',
      });

      // Should only see "Rejected" text, not a feedback section
      expect(screen.getByText('Rejected')).toBeInTheDocument();
      expect(screen.queryByTestId('rejection-feedback')).not.toBeInTheDocument();
    });

    it('has proper ARIA label', () => {
      renderNode({
        batchNumber: 3,
        status: 'rejected',
        feedback: 'Tests are failing',
      });

      expect(screen.getByRole('img')).toHaveAttribute(
        'aria-label',
        'Checkpoint after Batch 3: Rejected'
      );
    });
  });

  it('positions handles correctly for horizontal flow', () => {
    renderNode({
      batchNumber: 1,
      status: 'pending',
    });

    const handles = document.querySelectorAll('.react-flow__handle');
    expect(handles.length).toBe(2); // source and target

    const targetHandle = document.querySelector('.react-flow__handle-left');
    const sourceHandle = document.querySelector('.react-flow__handle-right');
    expect(targetHandle).toBeInTheDocument();
    expect(sourceHandle).toBeInTheDocument();
  });

  it('stores data attribute for status', () => {
    renderNode({
      batchNumber: 1,
      status: 'approved',
      approvedAt: '2025-12-15T10:30:45.123Z',
    });

    const card = screen.getByTestId('checkpoint-marker-card');
    expect(card).toHaveAttribute('data-status', 'approved');
  });

  describe('compact design', () => {
    it('uses smaller dimensions than full cards', () => {
      renderNode({
        batchNumber: 1,
        status: 'pending',
      });

      const card = screen.getByTestId('checkpoint-marker-card');
      // Should have more compact padding and sizing
      expect(card).toHaveClass('p-2');
    });

    it('has diamond/lozenge visual shape', () => {
      renderNode({
        batchNumber: 1,
        status: 'pending',
      });

      const card = screen.getByTestId('checkpoint-marker-card');
      // Should use rotate transform for diamond shape
      expect(card).toHaveClass('rotate-45');
    });
  });
});
