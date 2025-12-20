/**
 * @fileoverview Tests for StepNode component.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { ReactFlowProvider, Position } from '@xyflow/react';
import { StepNode, type StepNodeData } from './StepNode';

const renderNode = (data: StepNodeData) => {
  return render(
    <ReactFlowProvider>
      <StepNode
        id="test"
        draggable={false}
        selectable={false}
        deletable={false}
        data={data}
        type="step"
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

describe('StepNode', () => {
  describe('Basic rendering', () => {
    it('renders step description', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Install dependencies',
        status: 'pending',
        actionType: 'command',
      });
      expect(screen.getByText('Install dependencies')).toBeInTheDocument();
    });

    it('renders within a card container', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Write tests',
        status: 'pending',
        actionType: 'code',
      });

      const card = screen.getByTestId('step-node-card');
      expect(card).toBeInTheDocument();
      expect(card).toHaveClass('rounded-md', 'border');
    });

    it('has proper ARIA label', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Run tests',
        status: 'in_progress',
        actionType: 'validation',
      });

      const node = screen.getByRole('img');
      expect(node).toHaveAttribute(
        'aria-label',
        'Step: Run tests (in_progress)'
      );
    });

    it('has data attributes for step ID and status', () => {
      renderNode({
        stepId: 'step-42',
        description: 'Deploy',
        status: 'completed',
        actionType: 'command',
      });

      const card = screen.getByTestId('step-node-card');
      expect(card).toHaveAttribute('data-step-id', 'step-42');
      expect(card).toHaveAttribute('data-status', 'completed');
    });
  });

  describe('Status icons', () => {
    it('renders Circle icon for pending status', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'pending',
        actionType: 'code',
      });

      const icon = screen.getByTestId('status-icon-pending');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('lucide-circle');
    });

    it('renders Loader2 icon for in_progress status', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'in_progress',
        actionType: 'code',
      });

      const icon = screen.getByTestId('status-icon-in_progress');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('lucide-loader-2', 'animate-spin');
    });

    it('renders CheckCircle2 icon for completed status', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'completed',
        actionType: 'code',
      });

      const icon = screen.getByTestId('status-icon-completed');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('lucide-check-circle-2', 'text-status-completed');
    });

    it('renders MinusCircle icon for skipped status', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'skipped',
        actionType: 'code',
      });

      const icon = screen.getByTestId('status-icon-skipped');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('lucide-minus-circle', 'text-muted-foreground');
    });

    it('renders XCircle icon with red color for failed status', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'failed',
        actionType: 'code',
      });

      const icon = screen.getByTestId('status-icon-failed');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('lucide-x-circle', 'text-destructive');
    });

    it('renders XCircle icon with amber color for cancelled status', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'cancelled',
        actionType: 'code',
      });

      const icon = screen.getByTestId('status-icon-cancelled');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('lucide-x-circle', 'text-amber-500');
    });
  });

  describe('Action type indicators', () => {
    it('renders FileCode icon for code action type', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Write code',
        status: 'pending',
        actionType: 'code',
      });

      const icon = screen.getByTestId('action-type-icon');
      expect(icon).toHaveClass('lucide-file-code');
    });

    it('renders Terminal icon for command action type', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Run command',
        status: 'pending',
        actionType: 'command',
      });

      const icon = screen.getByTestId('action-type-icon');
      expect(icon).toHaveClass('lucide-terminal');
    });

    it('renders CheckSquare icon for validation action type', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Validate',
        status: 'pending',
        actionType: 'validation',
      });

      const icon = screen.getByTestId('action-type-icon');
      expect(icon).toHaveClass('lucide-check-square');
    });

    it('renders Hand icon for manual action type', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Manual step',
        status: 'pending',
        actionType: 'manual',
      });

      const icon = screen.getByTestId('action-type-icon');
      expect(icon).toHaveClass('lucide-hand');
    });
  });

  describe('Elapsed time display', () => {
    it('does not display elapsed time when status is not in_progress', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'pending',
        actionType: 'code',
        elapsedSeconds: 10,
      });

      expect(screen.queryByTestId('elapsed-time')).not.toBeInTheDocument();
    });

    it('displays elapsed time when status is in_progress', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'in_progress',
        actionType: 'code',
        elapsedSeconds: 12,
      });

      expect(screen.getByTestId('elapsed-time')).toHaveTextContent('12s');
    });

    it('formats elapsed time under 60 seconds as "Xs"', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'in_progress',
        actionType: 'code',
        elapsedSeconds: 45,
      });

      expect(screen.getByTestId('elapsed-time')).toHaveTextContent('45s');
    });

    it('formats elapsed time over 60 seconds as "Xm Ys"', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'in_progress',
        actionType: 'code',
        elapsedSeconds: 83,
      });

      expect(screen.getByTestId('elapsed-time')).toHaveTextContent('1m 23s');
    });

    it('formats exactly 60 seconds as "1m 0s"', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'in_progress',
        actionType: 'code',
        elapsedSeconds: 60,
      });

      expect(screen.getByTestId('elapsed-time')).toHaveTextContent('1m 0s');
    });

    it('formats large elapsed times correctly', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'in_progress',
        actionType: 'code',
        elapsedSeconds: 125,
      });

      expect(screen.getByTestId('elapsed-time')).toHaveTextContent('2m 5s');
    });

    it('displays "0s" when elapsed time is 0', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'in_progress',
        actionType: 'code',
        elapsedSeconds: 0,
      });

      expect(screen.getByTestId('elapsed-time')).toHaveTextContent('0s');
    });
  });

  describe('Cancel button', () => {
    it('does not show cancel button when status is not in_progress', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'pending',
        actionType: 'code',
        onCancel: vi.fn(),
      });

      expect(screen.queryByTestId('cancel-button')).not.toBeInTheDocument();
    });

    it('does not show cancel button when onCancel is not provided', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'in_progress',
        actionType: 'code',
      });

      expect(screen.queryByTestId('cancel-button')).not.toBeInTheDocument();
    });

    it('shows cancel button when status is in_progress and onCancel is provided', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'in_progress',
        actionType: 'code',
        onCancel: vi.fn(),
      });

      expect(screen.getByTestId('cancel-button')).toBeInTheDocument();
    });

    it('calls onCancel when cancel button is clicked', async () => {
      const user = userEvent.setup();
      const onCancel = vi.fn();

      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'in_progress',
        actionType: 'code',
        onCancel,
      });

      const cancelButton = screen.getByTestId('cancel-button');
      await user.click(cancelButton);

      expect(onCancel).toHaveBeenCalledTimes(1);
    });

    it('cancel button has proper aria-label', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'in_progress',
        actionType: 'code',
        onCancel: vi.fn(),
      });

      const cancelButton = screen.getByTestId('cancel-button');
      expect(cancelButton).toHaveAttribute('aria-label', 'Cancel step');
    });
  });

  describe('React Flow integration', () => {
    it('has handles for connections', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'pending',
        actionType: 'code',
      });

      const handles = document.querySelectorAll('.react-flow__handle');
      expect(handles.length).toBe(2); // source and target
    });

    it('positions handles for vertical flow (top target, bottom source)', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'pending',
        actionType: 'code',
      });

      const targetHandle = document.querySelector('.react-flow__handle-top');
      const sourceHandle = document.querySelector('.react-flow__handle-bottom');
      expect(targetHandle).toBeInTheDocument();
      expect(sourceHandle).toBeInTheDocument();
    });
  });

  describe('Compact design', () => {
    it('has compact padding compared to WorkflowNode', () => {
      renderNode({
        stepId: 'step-1',
        description: 'Test',
        status: 'pending',
        actionType: 'code',
      });

      const card = screen.getByTestId('step-node-card');
      const content = card.querySelector('[data-slot="card-content"]');
      expect(content).toHaveClass('p-2'); // Compact padding
    });
  });

  describe('Description truncation', () => {
    it('truncates very long descriptions', () => {
      const longDescription = 'This is a very long description that should be truncated to prevent the node from becoming too wide and breaking the layout of the flow diagram';

      renderNode({
        stepId: 'step-1',
        description: longDescription,
        status: 'pending',
        actionType: 'code',
      });

      const descriptionElement = screen.getByText(longDescription);
      expect(descriptionElement).toHaveClass('truncate');
    });
  });
});
