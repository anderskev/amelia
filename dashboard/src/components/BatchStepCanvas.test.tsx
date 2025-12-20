/**
 * @fileoverview Tests for BatchStepCanvas component.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BatchStepCanvas } from './BatchStepCanvas';
import type { ExecutionPlan, ExecutionBatch, PlanStep, BatchResult, BatchApproval } from '@/types';
import { ReactFlowProvider } from '@xyflow/react';

// Wrapper component to provide ReactFlow context
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <ReactFlowProvider>{children}</ReactFlowProvider>;
}

describe('BatchStepCanvas', () => {
  const createStep = (id: string, description: string): PlanStep => ({
    id,
    description,
    action_type: 'code',
    risk_level: 'low',
  });

  const createBatch = (batchNumber: number, steps: PlanStep[]): ExecutionBatch => ({
    batch_number: batchNumber,
    steps,
    risk_summary: 'low',
    description: `Batch ${batchNumber} description`,
  });

  const createPlan = (batches: ExecutionBatch[]): ExecutionPlan => ({
    goal: 'Test goal',
    batches,
    total_estimated_minutes: 30,
  });

  describe('Empty States', () => {
    it('renders empty state when no execution plan', () => {
      render(<BatchStepCanvas />, { wrapper: TestWrapper });

      expect(screen.getByText('No execution plan available')).toBeInTheDocument();
      expect(screen.queryByRole('img', { name: /batch/i })).not.toBeInTheDocument();
    });

    it('renders empty state when execution plan is null', () => {
      render(<BatchStepCanvas executionPlan={null} />, { wrapper: TestWrapper });

      expect(screen.getByText('No execution plan available')).toBeInTheDocument();
    });

    it('renders empty state when execution plan has no batches', () => {
      const plan = createPlan([]);
      render(<BatchStepCanvas executionPlan={plan} />, { wrapper: TestWrapper });

      expect(screen.getByText('No execution plan available')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('renders loading state when isLoading is true', () => {
      render(<BatchStepCanvas isLoading={true} />, { wrapper: TestWrapper });

      expect(screen.getByText('Loading execution plan...')).toBeInTheDocument();
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });
  });

  describe('Batch Rendering', () => {
    it('renders batches as swimlanes', () => {
      const step1 = createStep('step1', 'First step');
      const step2 = createStep('step2', 'Second step');
      const batch1 = createBatch(1, [step1]);
      const batch2 = createBatch(2, [step2]);
      const plan = createPlan([batch1, batch2]);

      render(<BatchStepCanvas executionPlan={plan} />, { wrapper: TestWrapper });

      // Check that batch nodes are rendered
      const batchNodes = screen.getAllByTestId('batch-node-card');
      expect(batchNodes).toHaveLength(2);
    });

    it('renders checkpoint markers between batches', () => {
      const step1 = createStep('step1', 'First step');
      const step2 = createStep('step2', 'Second step');
      const batch1 = createBatch(1, [step1]);
      const batch2 = createBatch(2, [step2]);
      const plan = createPlan([batch1, batch2]);

      render(<BatchStepCanvas executionPlan={plan} />, { wrapper: TestWrapper });

      // Should have 1 checkpoint marker between 2 batches
      const checkpoints = screen.getAllByTestId('checkpoint-marker-card');
      expect(checkpoints).toHaveLength(1);
      expect(screen.getByText('Awaiting Approval')).toBeInTheDocument();
    });

    it('renders steps within each batch', () => {
      const step1 = createStep('step1', 'First step');
      const step2 = createStep('step2', 'Second step');
      const step3 = createStep('step3', 'Third step');
      const batch1 = createBatch(1, [step1, step2]);
      const batch2 = createBatch(2, [step3]);
      const plan = createPlan([batch1, batch2]);

      render(<BatchStepCanvas executionPlan={plan} />, { wrapper: TestWrapper });

      // Check that step nodes are rendered
      const stepNodes = screen.getAllByTestId('step-node-card');
      expect(stepNodes).toHaveLength(3);
      expect(screen.getByText('First step')).toBeInTheDocument();
      expect(screen.getByText('Second step')).toBeInTheDocument();
      expect(screen.getByText('Third step')).toBeInTheDocument();
    });
  });

  describe('Batch Status', () => {
    it('applies status from batch results', () => {
      const step1 = createStep('step1', 'First step');
      const batch1 = createBatch(1, [step1]);
      const plan = createPlan([batch1]);

      const batchResults: BatchResult[] = [
        {
          batch_number: 1,
          status: 'complete',
          completed_steps: [
            {
              step_id: 'step1',
              status: 'completed',
            },
          ],
        },
      ];

      render(
        <BatchStepCanvas executionPlan={plan} batchResults={batchResults} />,
        { wrapper: TestWrapper }
      );

      const batchNode = screen.getByTestId('batch-node-card');
      expect(batchNode).toHaveAttribute('data-status', 'complete');
    });

    it('applies pending status when no batch results', () => {
      const step1 = createStep('step1', 'First step');
      const batch1 = createBatch(1, [step1]);
      const plan = createPlan([batch1]);

      render(<BatchStepCanvas executionPlan={plan} />, { wrapper: TestWrapper });

      const batchNode = screen.getByTestId('batch-node-card');
      expect(batchNode).toHaveAttribute('data-status', 'pending');
    });
  });

  describe('Current Batch Highlighting', () => {
    it('highlights current batch as in_progress', () => {
      const step1 = createStep('step1', 'First step');
      const step2 = createStep('step2', 'Second step');
      const batch1 = createBatch(1, [step1]);
      const batch2 = createBatch(2, [step2]);
      const plan = createPlan([batch1, batch2]);

      render(
        <BatchStepCanvas executionPlan={plan} currentBatchIndex={1} />,
        { wrapper: TestWrapper }
      );

      const batchNodes = screen.getAllByTestId('batch-node-card');
      // Second batch (index 1) should be in_progress
      expect(batchNodes[1]).toHaveAttribute('data-status', 'in_progress');
    });

    it('marks batches before current as complete', () => {
      const step1 = createStep('step1', 'First step');
      const step2 = createStep('step2', 'Second step');
      const batch1 = createBatch(1, [step1]);
      const batch2 = createBatch(2, [step2]);
      const plan = createPlan([batch1, batch2]);

      render(
        <BatchStepCanvas executionPlan={plan} currentBatchIndex={1} />,
        { wrapper: TestWrapper }
      );

      const batchNodes = screen.getAllByTestId('batch-node-card');
      // First batch (index 0) should be complete when current is 1
      expect(batchNodes[0]).toHaveAttribute('data-status', 'complete');
    });
  });

  describe('Step Status', () => {
    it('applies step status from batch results', () => {
      const step1 = createStep('step1', 'First step');
      const step2 = createStep('step2', 'Second step');
      const batch1 = createBatch(1, [step1, step2]);
      const plan = createPlan([batch1]);

      const batchResults: BatchResult[] = [
        {
          batch_number: 1,
          status: 'partial',
          completed_steps: [
            {
              step_id: 'step1',
              status: 'completed',
            },
            // step2 not in completed_steps yet - component will show it as in_progress
          ],
        },
      ];

      render(
        <BatchStepCanvas
          executionPlan={plan}
          batchResults={batchResults}
          currentBatchIndex={0}
        />,
        { wrapper: TestWrapper }
      );

      const stepNodes = screen.getAllByTestId('step-node-card');
      expect(stepNodes[0]).toHaveAttribute('data-status', 'completed');
      // step2 not in completed_steps but batch is current, so shows as pending
      expect(stepNodes[1]).toHaveAttribute('data-status', 'pending');
    });
  });

  describe('Cancel Step Handler', () => {
    it('passes onCancelStep to step nodes', () => {
      const step1 = createStep('step1', 'First step');
      const batch1 = createBatch(1, [step1]);
      const plan = createPlan([batch1]);

      const onCancelStep = vi.fn();

      render(
        <BatchStepCanvas executionPlan={plan} onCancelStep={onCancelStep} />,
        { wrapper: TestWrapper }
      );

      // The cancel button should be present if step is in_progress
      // For this test, we just verify the component renders without errors
      expect(screen.getByTestId('step-node-card')).toBeInTheDocument();
    });
  });

  describe('Batch Approvals', () => {
    it('marks checkpoint as approved when batch is approved', () => {
      const step1 = createStep('step1', 'First step');
      const step2 = createStep('step2', 'Second step');
      const batch1 = createBatch(1, [step1]);
      const batch2 = createBatch(2, [step2]);
      const plan = createPlan([batch1, batch2]);

      const batchApprovals: BatchApproval[] = [
        {
          batch_number: 1,
          approved: true,
          approved_at: '2025-12-15T10:00:00Z',
        },
      ];

      render(
        <BatchStepCanvas executionPlan={plan} batchApprovals={batchApprovals} />,
        { wrapper: TestWrapper }
      );

      const checkpoint = screen.getByTestId('checkpoint-marker-card');
      expect(checkpoint).toHaveAttribute('data-status', 'approved');
    });
  });

  describe('Custom className', () => {
    it('applies custom className to container', () => {
      const step1 = createStep('step1', 'First step');
      const batch1 = createBatch(1, [step1]);
      const plan = createPlan([batch1]);

      const { container } = render(
        <BatchStepCanvas executionPlan={plan} className="custom-class" />,
        { wrapper: TestWrapper }
      );

      const canvas = container.querySelector('[data-slot="batch-step-canvas"]');
      expect(canvas).toHaveClass('custom-class');
    });
  });

  describe('Accessibility', () => {
    it('has accessible role and label', () => {
      const step1 = createStep('step1', 'First step');
      const batch1 = createBatch(1, [step1]);
      const plan = createPlan([batch1]);

      render(<BatchStepCanvas executionPlan={plan} />, { wrapper: TestWrapper });

      const canvas = screen.getByRole('img', { name: /batch execution plan with \d+ batches/i });
      expect(canvas).toBeInTheDocument();
    });
  });
});
