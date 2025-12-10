/**
 * @fileoverview Tests for WorkflowNode component.
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ReactFlowProvider } from '@xyflow/react';
import { WorkflowNode } from '../WorkflowNode';
import { NODE_WIDTH, NODE_HEIGHT } from '@/utils/layout';

describe('WorkflowNode', () => {
  const defaultProps = {
    id: 'test-node',
    data: {
      label: 'Test Task',
      status: 'pending' as const,
    },
  };

  const renderWithProvider = (props = defaultProps) => {
    return render(
      <ReactFlowProvider>
        <WorkflowNode {...props} />
      </ReactFlowProvider>
    );
  };

  describe('dimensions', () => {
    it('renders with fixed dimensions matching layout constants', () => {
      renderWithProvider();

      const card = screen.getByTestId('workflow-node-card');
      expect(card).toHaveClass(`w-[${NODE_WIDTH}px]`);
      expect(card).toHaveClass(`h-[${NODE_HEIGHT}px]`);
    });
  });

  describe('rendering', () => {
    it('renders the label', () => {
      renderWithProvider();
      expect(screen.getByText('Test Task')).toBeInTheDocument();
    });

    it('renders subtitle when provided', () => {
      renderWithProvider({
        ...defaultProps,
        data: {
          ...defaultProps.data,
          subtitle: 'Task Subtitle',
        },
      });
      expect(screen.getByText('Task Subtitle')).toBeInTheDocument();
    });

    it('renders tokens when provided', () => {
      renderWithProvider({
        ...defaultProps,
        data: {
          ...defaultProps.data,
          tokens: '1.2k',
        },
      });
      expect(screen.getByText('1.2k tokens')).toBeInTheDocument();
    });
  });

  describe('accessibility', () => {
    it('has correct aria-label', () => {
      renderWithProvider();
      const card = screen.getByRole('img');
      expect(card).toHaveAttribute(
        'aria-label',
        'Workflow stage: Test Task (pending)'
      );
    });

    it('includes subtitle in aria-label when provided', () => {
      renderWithProvider({
        ...defaultProps,
        data: {
          ...defaultProps.data,
          subtitle: 'Sub',
        },
      });
      const card = screen.getByRole('img');
      expect(card).toHaveAttribute(
        'aria-label',
        'Workflow stage: Test Task - Sub (pending)'
      );
    });
  });

  describe('status styles', () => {
    it.each([
      ['completed', 'border-status-completed/40'],
      ['active', 'border-primary/60'],
      ['pending', 'border-border'],
      ['blocked', 'border-destructive/40'],
    ])('applies correct border class for %s status', (status, expectedClass) => {
      renderWithProvider({
        ...defaultProps,
        data: {
          ...defaultProps.data,
          status: status as 'completed' | 'active' | 'pending' | 'blocked',
        },
      });
      const card = screen.getByTestId('workflow-node-card');
      expect(card).toHaveClass(expectedClass);
    });
  });
});
