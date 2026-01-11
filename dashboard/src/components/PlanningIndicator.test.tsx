import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { PlanningIndicator } from './PlanningIndicator';

// Mock the api client
vi.mock('@/api/client', () => ({
  api: {
    cancelWorkflow: vi.fn().mockResolvedValue(undefined),
  },
}));

const renderWithRouter = (workflowId: string, startedAt?: string) => {
  const router = createMemoryRouter([
    {
      path: '/',
      element: <PlanningIndicator workflowId={workflowId} startedAt={startedAt} />,
    },
  ]);

  return render(<RouterProvider router={router} />);
};

describe('PlanningIndicator', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders planning in progress message', () => {
    renderWithRouter('wf-123');
    expect(screen.getByText('PLANNING')).toBeInTheDocument();
    expect(screen.getByText(/Architect is analyzing/)).toBeInTheDocument();
  });

  it('shows elapsed time', () => {
    const startedAt = new Date(Date.now() - 30000).toISOString(); // 30 seconds ago
    renderWithRouter('wf-123', startedAt);
    expect(screen.getByText(/30s/)).toBeInTheDocument();
  });

  it('has cancel button', () => {
    renderWithRouter('wf-123');
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
  });

  it('calls cancel API when cancel button clicked', async () => {
    const { api } = await import('@/api/client');
    renderWithRouter('wf-123');

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(api.cancelWorkflow).toHaveBeenCalledWith('wf-123');
  });

  it('has data-slot attribute', () => {
    renderWithRouter('wf-123');
    const heading = screen.getByText('PLANNING');
    const indicator = heading.closest('[data-slot="planning-indicator"]');
    expect(indicator).toBeInTheDocument();
  });
});
