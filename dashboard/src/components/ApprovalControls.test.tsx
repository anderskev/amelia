import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { ApprovalControls } from './ApprovalControls';

const renderWithRouter = (workflowId: string, planSummary: string, status?: 'pending' | 'approved' | 'rejected') => {
  const router = createMemoryRouter([
    {
      path: '/',
      element: <ApprovalControls workflowId={workflowId} planSummary={planSummary} status={status} />,
    },
  ]);

  return render(<RouterProvider router={router} />);
};

describe('ApprovalControls', () => {
  it('renders Approve and Reject buttons', () => {
    renderWithRouter('wf-001', 'Add benchmark framework');
    expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reject/i })).toBeInTheDocument();
  });

  it('renders plan summary', () => {
    renderWithRouter('wf-001', 'Add benchmark framework');
    expect(screen.getByText(/Add benchmark framework/)).toBeInTheDocument();
  });

  it('renders description text', () => {
    renderWithRouter('wf-001', 'Add benchmark framework');
    expect(screen.getByText(/Review and approve/)).toBeInTheDocument();
  });

  it('has data-slot attribute', () => {
    const { container } = renderWithRouter('wf-001', 'Test');
    expect(container.querySelector('[data-slot="approval-controls"]')).toBeInTheDocument();
  });

  it('shows approved state when status is approved', () => {
    renderWithRouter('wf-001', 'Test', 'approved');
    expect(screen.getByText(/Plan approved/)).toBeInTheDocument();
  });

  it('shows rejected state when status is rejected', () => {
    renderWithRouter('wf-001', 'Test', 'rejected');
    expect(screen.getByText(/Plan rejected/)).toBeInTheDocument();
  });

  it('hides buttons when not pending', () => {
    renderWithRouter('wf-001', 'Test', 'approved');
    expect(screen.queryByRole('button', { name: /approve/i })).not.toBeInTheDocument();
  });
});
