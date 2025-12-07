import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ActivityLogItem } from './ActivityLogItem';

describe('ActivityLogItem', () => {
  const mockEvent = {
    id: 'evt-001',
    workflow_id: 'wf-001',
    sequence: 1,
    timestamp: '2025-12-01T14:32:07Z',
    agent: 'ARCHITECT',
    event_type: 'stage_started' as const,
    message: 'Issue #8 parsed. Creating task DAG for benchmark framework.',
  };

  it('renders timestamp in HH:MM:SS format', () => {
    render(<ActivityLogItem event={mockEvent} />);
    expect(screen.getByText('14:32:07')).toBeInTheDocument();
  });

  it('renders agent name in brackets', () => {
    render(<ActivityLogItem event={mockEvent} />);
    expect(screen.getByText('[ARCHITECT]')).toBeInTheDocument();
  });

  it('renders message text', () => {
    render(<ActivityLogItem event={mockEvent} />);
    expect(screen.getByText(/Issue #8 parsed/)).toBeInTheDocument();
  });

  it.each([
    { agent: 'ARCHITECT', colorClass: 'text-accent' },
    { agent: 'DEVELOPER', colorClass: 'text-primary' },
    { agent: 'REVIEWER', colorClass: 'text-status-completed' },
    { agent: 'SYSTEM', colorClass: 'text-muted-foreground' },
  ])('applies $colorClass for $agent', ({ agent, colorClass }) => {
    const event = { ...mockEvent, agent };
    render(<ActivityLogItem event={event} />);
    expect(screen.getByText(`[${agent}]`)).toHaveClass(colorClass);
  });

  it('has data-slot attribute', () => {
    const { container } = render(<ActivityLogItem event={mockEvent} />);
    expect(container.querySelector('[data-slot="activity-log-item"]')).toBeInTheDocument();
  });
});
