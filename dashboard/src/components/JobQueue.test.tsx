import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { JobQueue } from './JobQueue';

describe('JobQueue', () => {
  const mockWorkflows = [
    { id: 'wf-001', issue_id: '#8', worktree_name: 'feature-a', status: 'in_progress' as const, current_stage: 'Developer' },
    { id: 'wf-002', issue_id: '#7', worktree_name: 'feature-b', status: 'completed' as const, current_stage: null },
    { id: 'wf-003', issue_id: '#9', worktree_name: 'feature-c', status: 'pending' as const, current_stage: null },
  ];

  it('renders all workflows', () => {
    render(<JobQueue workflows={mockWorkflows} />);
    expect(screen.getByText('#8')).toBeInTheDocument();
    expect(screen.getByText('#7')).toBeInTheDocument();
    expect(screen.getByText('#9')).toBeInTheDocument();
  });

  it('renders section label', () => {
    render(<JobQueue workflows={mockWorkflows} />);
    expect(screen.getByText('JOB QUEUE')).toBeInTheDocument();
  });

  it('highlights selected workflow', () => {
    render(
      <JobQueue workflows={mockWorkflows} selectedId="wf-001" />
    );
    // Find the selected workflow item by its button role and data-selected attribute
    const selectedButton = screen.getByText('#8').closest('[role="button"]');
    expect(selectedButton).toHaveAttribute('data-selected', 'true');
  });

  it('calls onSelect when workflow is clicked', () => {
    const onSelect = vi.fn();
    render(<JobQueue workflows={mockWorkflows} onSelect={onSelect} />);

    const button = screen.getByText('#8').closest('[role="button"]');
    expect(button).not.toBeNull();
    fireEvent.click(button!);
    expect(onSelect).toHaveBeenCalledWith('wf-001');
  });

  it('shows empty state when no workflows', () => {
    render(<JobQueue workflows={[]} />);
    expect(screen.getByText(/No active workflows/)).toBeInTheDocument();
  });

  it('has data-slot attribute', () => {
    render(<JobQueue workflows={mockWorkflows} />);
    // Find the job queue by its heading, then check parent has data-slot
    const heading = screen.getByText('JOB QUEUE');
    const jobQueue = heading.closest('[data-slot="job-queue"]');
    expect(jobQueue).toBeInTheDocument();
  });
});
