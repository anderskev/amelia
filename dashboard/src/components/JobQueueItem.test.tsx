import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { JobQueueItem } from './JobQueueItem';

describe('JobQueueItem', () => {
  const mockWorkflow = {
    id: 'wf-001',
    issue_id: '#8',
    worktree_name: 'feature-benchmark',
    status: 'in_progress' as const,
    current_stage: 'Developer',
  };

  it('renders issue ID and worktree name', () => {
    render(<JobQueueItem workflow={mockWorkflow} selected={false} onSelect={() => {}} />);
    expect(screen.getByText('#8')).toBeInTheDocument();
    expect(screen.getByText('feature-benchmark')).toBeInTheDocument();
  });

  it('renders status indicator via StatusBadge', () => {
    render(<JobQueueItem workflow={mockWorkflow} selected={false} onSelect={() => {}} />);
    expect(screen.getByRole('status')).toHaveTextContent('RUNNING');
  });

  it('renders estimated time', () => {
    render(<JobQueueItem workflow={mockWorkflow} selected={false} onSelect={() => {}} />);
    // TODO: Update when ETA comes from API
    expect(screen.getByText(/Est: 02:45/)).toBeInTheDocument();
  });

  it('shows selected state with data-selected attribute', () => {
    const { container } = render(
      <JobQueueItem workflow={mockWorkflow} selected={true} onSelect={() => {}} />
    );
    expect(container.querySelector('[data-selected="true"]')).toBeInTheDocument();
  });

  it('calls onSelect when clicked', () => {
    const onSelect = vi.fn();
    render(<JobQueueItem workflow={mockWorkflow} selected={false} onSelect={onSelect} />);

    fireEvent.click(screen.getByRole('button'));
    expect(onSelect).toHaveBeenCalledWith('wf-001');
  });

  it('supports keyboard navigation (Enter)', () => {
    const onSelect = vi.fn();
    render(<JobQueueItem workflow={mockWorkflow} selected={false} onSelect={onSelect} />);

    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' });
    expect(onSelect).toHaveBeenCalledWith('wf-001');
  });

  it('has data-slot attribute', () => {
    const { container } = render(
      <JobQueueItem workflow={mockWorkflow} selected={false} onSelect={() => {}} />
    );
    expect(container.querySelector('[data-slot="job-queue-item"]')).toBeInTheDocument();
  });
});
